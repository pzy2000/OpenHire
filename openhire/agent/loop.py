"""Agent loop: the core processing engine."""

from __future__ import annotations

import asyncio
import dataclasses
import json
import os
import time
from contextlib import AsyncExitStack, nullcontext
from datetime import datetime
from pathlib import Path
from typing import TYPE_CHECKING, Any, Awaitable, Callable

from loguru import logger

from openhire.agent.autocompact import AutoCompact
from openhire.agent.context import ContextBuilder
from openhire.agent.hook import AgentHook, AgentHookContext, CompositeHook
from openhire.agent.memory import Consolidator, Dream
from openhire.agent.runner import _MAX_INJECTIONS_PER_TURN, AgentRunner, AgentRunSpec
from openhire.agent.skill_learning import (
    SkillProposalGenerator,
    detect_skill_learning_trigger_reasons,
)
from openhire.agent.skills import BUILTIN_SKILLS_DIR
from openhire.agent.tools.cron import CronTool
from openhire.agent.tools.filesystem import EditFileTool, ListDirTool, ReadFileTool, WriteFileTool
from openhire.agent.tools.message import MessageTool
from openhire.agent.tools.notebook import NotebookEditTool
from openhire.agent.tools.registry import ToolRegistry
from openhire.agent.tools.search import GlobTool, GrepTool
from openhire.agent.tools.shell import ExecTool
from openhire.agent.tools.web import WebFetchTool, WebSearchTool
from openhire.bus.events import InboundMessage, OutboundMessage
from openhire.bus.queue import MessageBus
from openhire.command import CommandContext, CommandRouter, register_builtin_commands
from openhire.config.schema import AgentDefaults
from openhire.providers.base import LLMProvider
from openhire.session.manager import Session, SessionManager
from openhire.adapters.base import inspect_container_status
from openhire.utils.document import extract_documents
from openhire.utils.helpers import (
    estimate_message_tokens,
    estimate_prompt_tokens_chain,
    image_placeholder_text,
)
from openhire.utils.helpers import truncate_text as truncate_text_fn
from openhire.utils.runtime import EMPTY_FINAL_RESPONSE_MESSAGE

if TYPE_CHECKING:
    from openhire.config.schema import ChannelsConfig, ExecToolConfig, WebToolsConfig
    from openhire.cron.service import CronService


UNIFIED_SESSION_KEY = "unified:default"


class _LoopHook(AgentHook):
    """Core hook for the main loop."""

    def __init__(
        self,
        agent_loop: AgentLoop,
        on_progress: Callable[..., Awaitable[None]] | None = None,
        on_stream: Callable[[str], Awaitable[None]] | None = None,
        on_stream_end: Callable[..., Awaitable[None]] | None = None,
        *,
        channel: str = "cli",
        chat_id: str = "direct",
        message_id: str | None = None,
        requester_agent_id: str | None = None,
    ) -> None:
        super().__init__(reraise=True)
        self._loop = agent_loop
        self._on_progress = on_progress
        self._on_stream = on_stream
        self._on_stream_end = on_stream_end
        self._channel = channel
        self._chat_id = chat_id
        self._message_id = message_id
        self._requester_agent_id = requester_agent_id
        self._stream_buf = ""

    def wants_streaming(self) -> bool:
        return self._on_stream is not None

    async def on_stream(self, context: AgentHookContext, delta: str) -> None:
        from openhire.utils.helpers import strip_think

        prev_clean = strip_think(self._stream_buf)
        self._stream_buf += delta
        new_clean = strip_think(self._stream_buf)
        incremental = new_clean[len(prev_clean) :]
        if incremental and self._on_stream:
            await self._on_stream(incremental)

    async def on_stream_end(self, context: AgentHookContext, *, resuming: bool) -> None:
        if self._on_stream_end:
            await self._on_stream_end(resuming=resuming)
        self._stream_buf = ""

    async def before_execute_tools(self, context: AgentHookContext) -> None:
        self._loop.runtime_monitor.update_tool_calls(
            context.tool_calls,
            iteration=context.iteration,
        )
        if self._on_progress:
            if not self._on_stream:
                thought = self._loop._strip_think(
                    context.response.content if context.response else None
                )
                if thought:
                    await self._on_progress(thought)
            tool_hint = self._loop._strip_think(self._loop._tool_hint(context.tool_calls))
            await self._on_progress(tool_hint, tool_hint=True)
        for tc in context.tool_calls:
            args_str = json.dumps(tc.arguments, ensure_ascii=False)
            logger.info("Tool call: {}({})", tc.name, args_str[:200])
        self._loop._set_tool_context(
            self._channel,
            self._chat_id,
            self._message_id,
            requester_agent_id=self._requester_agent_id,
        )

    async def after_iteration(self, context: AgentHookContext) -> None:
        u = context.usage or {}
        self._loop.runtime_monitor.update_usage(u)
        logger.debug(
            "LLM usage: prompt={} completion={} cached={}",
            u.get("prompt_tokens", 0),
            u.get("completion_tokens", 0),
            u.get("cached_tokens", 0),
        )

    def finalize_content(self, context: AgentHookContext, content: str | None) -> str | None:
        return self._loop._strip_think(content)


class AgentLoop:
    """
    The agent loop is the core processing engine.

    It:
    1. Receives messages from the bus
    2. Builds context with history, memory, skills
    3. Calls the LLM
    4. Executes tool calls
    5. Sends responses back
    """

    _RUNTIME_CHECKPOINT_KEY = "runtime_checkpoint"
    _PENDING_USER_TURN_KEY = "pending_user_turn"

    def __init__(
        self,
        bus: MessageBus,
        provider: LLMProvider,
        workspace: Path,
        model: str | None = None,
        max_iterations: int | None = None,
        context_window_tokens: int | None = None,
        context_block_limit: int | None = None,
        max_tool_result_chars: int | None = None,
        provider_retry_mode: str = "standard",
        web_config: WebToolsConfig | None = None,
        exec_config: ExecToolConfig | None = None,
        cron_service: CronService | None = None,
        restrict_to_workspace: bool = False,
        session_manager: SessionManager | None = None,
        mcp_servers: dict | None = None,
        channels_config: ChannelsConfig | None = None,
        timezone: str | None = None,
        session_ttl_minutes: int = 0,
        hooks: list[AgentHook] | None = None,
        unified_session: bool = False,
        disabled_skills: list[str] | None = None,
        docker_agents_config: "DockerAgentsConfig | None" = None,
        openhire_config: "OpenHireConfig | None" = None,
    ):
        from openhire.config.schema import DockerAgentsConfig, ExecToolConfig, OpenHireConfig, WebToolsConfig

        defaults = AgentDefaults()
        self.bus = bus
        self.channels_config = channels_config
        self.provider = provider
        self.workspace = workspace
        self.model = model or provider.get_default_model()
        self.max_iterations = (
            max_iterations if max_iterations is not None else defaults.max_tool_iterations
        )
        self.context_window_tokens = (
            context_window_tokens
            if context_window_tokens is not None
            else defaults.context_window_tokens
        )
        self.context_block_limit = context_block_limit
        self.max_tool_result_chars = (
            max_tool_result_chars
            if max_tool_result_chars is not None
            else defaults.max_tool_result_chars
        )
        self.provider_retry_mode = provider_retry_mode
        self.web_config = web_config or WebToolsConfig()
        self.exec_config = exec_config or ExecToolConfig()
        self.cron_service = cron_service
        self.restrict_to_workspace = restrict_to_workspace
        self._docker_agents_config = docker_agents_config
        self._openhire_config = openhire_config
        self._start_time = time.time()
        self._last_usage: dict[str, int] = {}
        self._last_admin_session_key: str | None = None
        self._last_admin_context_tokens = 0
        self._last_admin_context_source = "unknown"
        self._last_admin_stop_reason: str | None = None
        self._extra_hooks: list[AgentHook] = hooks or []
        from openhire.admin.runtime import RuntimeMonitor

        self.runtime_monitor = RuntimeMonitor(
            process_role="agent",
            workspace=str(workspace),
            model=self.model,
            context_window_tokens=self.context_window_tokens,
        )

        self.context = ContextBuilder(workspace, timezone=timezone, disabled_skills=disabled_skills)
        self.sessions = session_manager or SessionManager(workspace)
        self.tools = ToolRegistry()
        self.runner = AgentRunner(provider)
        self._unified_session = unified_session
        self._running = False
        self._mcp_servers = mcp_servers or {}
        self._mcp_stacks: dict[str, AsyncExitStack] = {}
        self._mcp_connected = False
        self._mcp_connecting = False
        self._mcp_connect_task: asyncio.Task | None = None
        self._active_tasks: dict[str, list[asyncio.Task]] = {}  # session_key -> tasks
        self._background_tasks: list[asyncio.Task] = []
        self._session_locks: dict[str, asyncio.Lock] = {}
        self.docker_runtime_tracker = None
        # Per-session pending queues for mid-turn message injection.
        # When a session has an active task, new messages for that session
        # are routed here instead of creating a new task.
        self._pending_queues: dict[str, asyncio.Queue] = {}
        # OPENHIRE_MAX_CONCURRENT_REQUESTS: <=0 means unlimited; default 3.
        _max = int(os.environ.get("OPENHIRE_MAX_CONCURRENT_REQUESTS", "3"))
        self._concurrency_gate: asyncio.Semaphore | None = (
            asyncio.Semaphore(_max) if _max > 0 else None
        )
        self.consolidator = Consolidator(
            store=self.context.memory,
            provider=provider,
            model=self.model,
            sessions=self.sessions,
            context_window_tokens=context_window_tokens,
            build_messages=self.context.build_messages,
            get_tool_definitions=self.tools.get_definitions,
            max_completion_tokens=provider.generation.max_tokens,
        )
        self.auto_compact = AutoCompact(
            sessions=self.sessions,
            consolidator=self.consolidator,
            session_ttl_minutes=session_ttl_minutes,
        )
        self.dream = Dream(
            store=self.context.memory,
            provider=provider,
            model=self.model,
        )
        self._skill_proposal_generator = SkillProposalGenerator(
            workspace=self.workspace,
            provider=provider,
            model=self.model,
        )
        self._register_default_tools()
        self.commands = CommandRouter()
        register_builtin_commands(self.commands)

    def _register_default_tools(self) -> None:
        """Register the default set of tools."""
        allowed_dir = (
            self.workspace if (self.restrict_to_workspace or self.exec_config.sandbox) else None
        )
        extra_read = [BUILTIN_SKILLS_DIR] if allowed_dir else None
        self.tools.register(
            ReadFileTool(
                workspace=self.workspace, allowed_dir=allowed_dir, extra_allowed_dirs=extra_read
            )
        )
        for cls in (WriteFileTool, EditFileTool, ListDirTool):
            self.tools.register(cls(workspace=self.workspace, allowed_dir=allowed_dir))
        for cls in (GlobTool, GrepTool):
            self.tools.register(cls(workspace=self.workspace, allowed_dir=allowed_dir))
        self.tools.register(NotebookEditTool(workspace=self.workspace, allowed_dir=allowed_dir))
        if self.exec_config.enable:
            self.tools.register(
                ExecTool(
                    working_dir=str(self.workspace),
                    timeout=self.exec_config.timeout,
                    restrict_to_workspace=self.restrict_to_workspace,
                    sandbox=self.exec_config.sandbox,
                    path_append=self.exec_config.path_append,
                    allowed_env_keys=self.exec_config.allowed_env_keys,
                )
            )
        if self.web_config.enable:
            self.tools.register(
                WebSearchTool(config=self.web_config.search, proxy=self.web_config.proxy)
            )
            self.tools.register(WebFetchTool(proxy=self.web_config.proxy))
        organization_policy = None
        if self._openhire_config and self._openhire_config.enabled:
            from openhire.workforce.organization import OrganizationPolicy, OrganizationStore
            from openhire.workforce.registry import AgentRegistry
            from openhire.workforce.store import OpenHireStore

            organization_policy = OrganizationPolicy(
                AgentRegistry(OpenHireStore(self.workspace)),
                OrganizationStore(self.workspace),
                default_allow_skip_level_reporting=bool(
                    getattr(self._openhire_config, "allow_skip_level_reporting", False)
                ),
            )
        self.tools.register(MessageTool(
            send_callback=self.bus.publish_outbound,
            organization_policy=organization_policy,
        ))
        if self.cron_service:
            self.tools.register(
                CronTool(self.cron_service, default_timezone=self.context.timezone or "UTC")
            )
        if self._docker_agents_config and self._docker_agents_config.enabled:
            from openhire.adapters import build_default_registry
            from openhire.adapters.tool import DockerAgentTool

            self.docker_runtime_tracker = self.runtime_monitor.docker_agent_tracker
            self.tools.register(DockerAgentTool(
                workspace=self.workspace,
                agents_config=self._docker_agents_config.agents,
                adapter_registry=build_default_registry(),
                runtime_tracker=self.docker_runtime_tracker,
                context_window_tokens=self.context_window_tokens,
            ))
        if self._openhire_config and self._openhire_config.enabled:
            from openhire.workforce.tool import OpenHireTool

            self.tools.register(OpenHireTool(
                workspace=self.workspace,
                openhire_config=self._openhire_config,
                docker_agents_config=self._docker_agents_config,
                provider=self.provider,
                send_callback=self.bus.publish_outbound,
            ))

    async def _connect_mcp(self) -> None:
        """Connect to configured MCP servers (one-time, lazy)."""
        if self._mcp_connected or self._mcp_connecting or not self._mcp_servers:
            return
        self._mcp_connecting = True
        from openhire.agent.tools.mcp import connect_mcp_servers

        try:
            self._mcp_stacks = await connect_mcp_servers(self._mcp_servers, self.tools)
            if self._mcp_stacks:
                self._mcp_connected = True
            else:
                logger.warning("No MCP servers connected successfully (will retry next message)")
        except asyncio.CancelledError:
            logger.warning("MCP connection cancelled (will retry next message)")
            self._mcp_stacks.clear()
        except BaseException as e:
            logger.error("Failed to connect MCP servers (will retry next message): {}", e)
            self._mcp_stacks.clear()
        finally:
            self._mcp_connecting = False

    def _set_tool_context(
        self,
        channel: str,
        chat_id: str,
        message_id: str | None = None,
        *,
        requester_agent_id: str | None = None,
    ) -> None:
        """Update context for all tools that need routing info."""
        for name in ("message", "cron", "openhire"):
            if tool := self.tools.get(name):
                if hasattr(tool, "set_context"):
                    with_message_id = name in {"message", "openhire"}
                    tool.set_context(channel, chat_id, *([message_id] if with_message_id else []))
                if hasattr(tool, "set_requester_agent_id"):
                    tool.set_requester_agent_id(requester_agent_id)

    @staticmethod
    def _organization_requester_agent_id(msg: InboundMessage) -> str:
        """Return explicit employee requester metadata, if this inbound turn has one."""
        metadata = msg.metadata or {}
        for key in ("requester_agent_id", "requesterAgentId", "employee_id", "employeeId"):
            value = metadata.get(key)
            if value:
                return str(value).strip()
        return ""

    @staticmethod
    def _strip_think(text: str | None) -> str | None:
        """Remove <think>…</think> blocks that some models embed in content."""
        if not text:
            return None
        from openhire.utils.helpers import strip_think

        return strip_think(text) or None

    @staticmethod
    def _tool_hint(tool_calls: list) -> str:
        """Format tool calls as concise hints with smart abbreviation."""
        from openhire.utils.tool_hints import format_tool_hints

        return format_tool_hints(tool_calls)

    def _effective_session_key(self, msg: InboundMessage) -> str:
        """Return the session key used for task routing and mid-turn injections."""
        if self._unified_session and not msg.session_key_override:
            return UNIFIED_SESSION_KEY
        return msg.session_key

    async def _run_agent_loop(
        self,
        initial_messages: list[dict],
        on_progress: Callable[..., Awaitable[None]] | None = None,
        on_stream: Callable[[str], Awaitable[None]] | None = None,
        on_stream_end: Callable[..., Awaitable[None]] | None = None,
        *,
        session: Session | None = None,
        channel: str = "cli",
        chat_id: str = "direct",
        message_id: str | None = None,
        requester_agent_id: str | None = None,
        pending_queue: asyncio.Queue | None = None,
    ) -> tuple[str | None, list[str], list[dict], str, bool]:
        """Run the agent iteration loop.

        *on_stream*: called with each content delta during streaming.
        *on_stream_end(resuming)*: called when a streaming session finishes.
        ``resuming=True`` means tool calls follow (spinner should restart);
        ``resuming=False`` means this is the final response.

        Returns (final_content, tools_used, messages, stop_reason, had_injections).
        """
        loop_hook = _LoopHook(
            self,
            on_progress=on_progress,
            on_stream=on_stream,
            on_stream_end=on_stream_end,
            channel=channel,
            chat_id=chat_id,
            message_id=message_id,
            requester_agent_id=requester_agent_id,
        )
        hook: AgentHook = (
            CompositeHook([loop_hook] + self._extra_hooks) if self._extra_hooks else loop_hook
        )

        async def _checkpoint(payload: dict[str, Any]) -> None:
            if session is None:
                return
            self._set_runtime_checkpoint(session, payload)

        async def _drain_pending(*, limit: int = _MAX_INJECTIONS_PER_TURN) -> list[dict[str, Any]]:
            """Non-blocking drain of follow-up messages from the pending queue."""
            if pending_queue is None:
                return []
            items: list[dict[str, Any]] = []
            while len(items) < limit:
                try:
                    pending_msg = pending_queue.get_nowait()
                except asyncio.QueueEmpty:
                    break
                content = pending_msg.content
                media = pending_msg.media if pending_msg.media else None
                if media:
                    content, media = extract_documents(content, media)
                    media = media or None
                user_content = self.context._build_user_content(content, media)
                runtime_ctx = self.context._build_runtime_context(
                    pending_msg.channel,
                    pending_msg.chat_id,
                    self.context.timezone,
                )
                if isinstance(user_content, str):
                    merged: str | list[dict[str, Any]] = f"{runtime_ctx}\n\n{user_content}"
                else:
                    merged = [{"type": "text", "text": runtime_ctx}] + user_content
                items.append({"role": "user", "content": merged})
            return items

        result = await self.runner.run(AgentRunSpec(
            initial_messages=initial_messages,
            tools=self.tools,
            model=self.model,
            max_iterations=self.max_iterations,
            max_tool_result_chars=self.max_tool_result_chars,
            hook=hook,
            error_message="Sorry, I encountered an error calling the AI model.",
            concurrent_tools=True,
            workspace=self.workspace,
            session_key=session.key if session else None,
            context_window_tokens=self.context_window_tokens,
            context_block_limit=self.context_block_limit,
            provider_retry_mode=self.provider_retry_mode,
            progress_callback=on_progress,
            checkpoint_callback=_checkpoint,
            injection_callback=_drain_pending,
        ))
        self._last_usage = result.usage
        if result.stop_reason == "max_iterations":
            logger.warning("Max iterations ({}) reached", self.max_iterations)
        elif result.stop_reason == "error":
            logger.error("LLM returned error: {}", (result.final_content or "")[:200])
        return result.final_content, result.tools_used, result.messages, result.stop_reason, result.had_injections

    async def run(self) -> None:
        """Run the agent loop, dispatching messages as tasks to stay responsive to /stop."""
        self._running = True
        # Connect MCP servers in the background. A slow or broken MCP server
        # must never block message consumption: we start draining the inbound
        # queue immediately and let MCP tools register as they become ready.
        if self._mcp_servers and self._mcp_connect_task is None:
            self._mcp_connect_task = asyncio.create_task(self._connect_mcp())
        logger.info("Agent loop started")

        while self._running:
            try:
                msg = await asyncio.wait_for(self.bus.consume_inbound(), timeout=1.0)
            except asyncio.TimeoutError:
                self.auto_compact.check_expired(
                    self._schedule_background,
                    active_session_keys=self._pending_queues.keys(),
                )
                continue
            except asyncio.CancelledError:
                # Preserve real task cancellation so shutdown can complete cleanly.
                # Only ignore non-task CancelledError signals that may leak from integrations.
                if not self._running or asyncio.current_task().cancelling():
                    raise
                continue
            except Exception as e:
                logger.warning("Error consuming inbound message: {}, continuing...", e)
                continue

            raw = msg.content.strip()
            if self.commands.is_priority(raw):
                ctx = CommandContext(msg=msg, session=None, key=msg.session_key, raw=raw, loop=self)
                result = await self.commands.dispatch_priority(ctx)
                if result:
                    await self.bus.publish_outbound(result)
                continue
            effective_key = self._effective_session_key(msg)
            # If this session already has an active pending queue (i.e. a task
            # is processing this session), route the message there for mid-turn
            # injection instead of creating a competing task.
            if effective_key in self._pending_queues:
                pending_msg = msg
                if effective_key != msg.session_key:
                    pending_msg = dataclasses.replace(
                        msg,
                        session_key_override=effective_key,
                    )
                try:
                    self._pending_queues[effective_key].put_nowait(pending_msg)
                except asyncio.QueueFull:
                    logger.warning(
                        "Pending queue full for session {}, falling back to queued task",
                        effective_key,
                    )
                else:
                    logger.info(
                        "Routed follow-up message to pending queue for session {}",
                        effective_key,
                    )
                    continue
            # Compute the effective session key before dispatching
            # This ensures /stop command can find tasks correctly when unified session is enabled
            task = asyncio.create_task(self._dispatch(msg))
            self._active_tasks.setdefault(effective_key, []).append(task)
            task.add_done_callback(
                lambda t, k=effective_key: self._active_tasks.get(k, [])
                and self._active_tasks[k].remove(t)
                if t in self._active_tasks.get(k, [])
                else None
            )

    async def _dispatch(self, msg: InboundMessage) -> None:
        """Process a message: per-session serial, cross-session concurrent."""
        session_key = self._effective_session_key(msg)
        if session_key != msg.session_key:
            msg = dataclasses.replace(msg, session_key_override=session_key)
        lock = self._session_locks.setdefault(session_key, asyncio.Lock())
        gate = self._concurrency_gate or nullcontext()

        # Register a pending queue so follow-up messages for this session are
        # routed here (mid-turn injection) instead of spawning a new task.
        pending = asyncio.Queue(maxsize=20)
        self._pending_queues[session_key] = pending

        try:
            async with lock, gate:
                try:
                    on_stream = on_stream_end = None
                    if msg.metadata.get("_wants_stream"):
                        # Split one answer into distinct stream segments.
                        stream_base_id = f"{msg.session_key}:{time.time_ns()}"
                        stream_segment = 0

                        def _current_stream_id() -> str:
                            return f"{stream_base_id}:{stream_segment}"

                        async def on_stream(delta: str) -> None:
                            meta = dict(msg.metadata or {})
                            meta["_stream_delta"] = True
                            meta["_stream_id"] = _current_stream_id()
                            await self.bus.publish_outbound(OutboundMessage(
                                channel=msg.channel, chat_id=msg.chat_id,
                                content=delta,
                                metadata=meta,
                            ))

                        async def on_stream_end(*, resuming: bool = False) -> None:
                            nonlocal stream_segment
                            meta = dict(msg.metadata or {})
                            meta["_stream_end"] = True
                            meta["_resuming"] = resuming
                            meta["_stream_id"] = _current_stream_id()
                            await self.bus.publish_outbound(OutboundMessage(
                                channel=msg.channel, chat_id=msg.chat_id,
                                content="",
                                metadata=meta,
                            ))
                            stream_segment += 1

                    response = await self._process_message(
                        msg, on_stream=on_stream, on_stream_end=on_stream_end,
                        pending_queue=pending,
                    )
                    if response is not None:
                        await self.bus.publish_outbound(response)
                    elif msg.channel == "cli":
                        await self.bus.publish_outbound(OutboundMessage(
                            channel=msg.channel, chat_id=msg.chat_id,
                            content="", metadata=msg.metadata or {},
                        ))
                except asyncio.CancelledError:
                    logger.info("Task cancelled for session {}", session_key)
                    raise
                except Exception:
                    logger.exception("Error processing message for session {}", session_key)
                    await self.bus.publish_outbound(OutboundMessage(
                        channel=msg.channel, chat_id=msg.chat_id,
                        content="Sorry, I encountered an error.",
                    ))
        finally:
            # Drain any messages still in the pending queue and re-publish
            # them to the bus so they are processed as fresh inbound messages
            # rather than silently lost.
            queue = self._pending_queues.pop(session_key, None)
            if queue is not None:
                leftover = 0
                while True:
                    try:
                        item = queue.get_nowait()
                    except asyncio.QueueEmpty:
                        break
                    await self.bus.publish_inbound(item)
                    leftover += 1
                if leftover:
                    logger.info(
                        "Re-published {} leftover message(s) to bus for session {}",
                        leftover, session_key,
                    )

    async def close_mcp(self) -> None:
        """Drain pending background archives, then close MCP connections."""
        if self._background_tasks:
            await asyncio.gather(*self._background_tasks, return_exceptions=True)
            self._background_tasks.clear()
        # Cancel any in-flight MCP connect task so shutdown is not blocked
        # waiting on a non-responsive MCP server.
        if self._mcp_connect_task is not None and not self._mcp_connect_task.done():
            self._mcp_connect_task.cancel()
            try:
                await self._mcp_connect_task
            except (asyncio.CancelledError, Exception):
                pass
        self._mcp_connect_task = None
        for name, stack in self._mcp_stacks.items():
            try:
                await stack.aclose()
            except (RuntimeError, BaseExceptionGroup):
                logger.debug("MCP server '{}' cleanup error (can be ignored)", name)
        self._mcp_stacks.clear()

    def _schedule_background(self, coro) -> None:
        """Schedule a coroutine as a tracked background task (drained on shutdown)."""
        task = asyncio.create_task(coro)
        self._background_tasks.append(task)
        task.add_done_callback(self._background_tasks.remove)

    def stop(self) -> None:
        """Stop the agent loop."""
        self._running = False
        logger.info("Agent loop stopping")

    async def _process_message(
        self,
        msg: InboundMessage,
        session_key: str | None = None,
        on_progress: Callable[[str], Awaitable[None]] | None = None,
        on_stream: Callable[[str], Awaitable[None]] | None = None,
        on_stream_end: Callable[..., Awaitable[None]] | None = None,
        pending_queue: asyncio.Queue | None = None,
    ) -> OutboundMessage | None:
        """Process a single inbound message and return the response."""
        # System messages: parse origin from chat_id ("channel:chat_id")
        if msg.channel == "system":
            channel, chat_id = (
                msg.chat_id.split(":", 1) if ":" in msg.chat_id else ("cli", msg.chat_id)
            )
            logger.info("Processing system message from {}", msg.sender_id)
            key = f"{channel}:{chat_id}"
            self.runtime_monitor.start_main_turn(
                session_key=key,
                channel=channel,
                chat_id=chat_id,
            )
            session = self.sessions.get_or_create(key)
            if self._restore_runtime_checkpoint(session):
                self.sessions.save(session)
            if self._restore_pending_user_turn(session):
                self.sessions.save(session)

            session, pending = self.auto_compact.prepare_session(session, key)

            await self.consolidator.maybe_consolidate_by_tokens(session)
            self._set_tool_context(channel, chat_id, msg.metadata.get("message_id"))
            history = session.get_history(max_messages=0)
            current_role = "user"

            messages = self.context.build_messages(
                history=history,
                current_message=msg.content, channel=channel, chat_id=chat_id,
                session_summary=pending,
                current_role=current_role,
            )
            self._update_admin_live_context(messages)
            try:
                final_content, _, all_msgs, _, _ = await self._run_agent_loop(
                    messages, session=session, channel=channel, chat_id=chat_id,
                    message_id=msg.metadata.get("message_id"),
                    requester_agent_id=self._organization_requester_agent_id(msg),
                )
            except Exception as exc:
                self.runtime_monitor.finish_main_turn(stop_reason="error", error=str(exc))
                raise
            self._save_turn(session, all_msgs, 1 + len(history))
            self._clear_runtime_checkpoint(session)
            self.sessions.save(session)
            self._update_admin_session_snapshot(session, key, stop_reason=None)
            self.runtime_monitor.finish_main_turn(stop_reason="completed")
            self._schedule_background(self.consolidator.maybe_consolidate_by_tokens(session))
            return OutboundMessage(
                channel=channel,
                chat_id=chat_id,
                content=final_content or "Background task completed.",
            )

        # Extract document text from media at the processing boundary so all
        # channels benefit without format-specific logic in ContextBuilder.
        if msg.media:
            new_content, image_only = extract_documents(msg.content, msg.media)
            msg = dataclasses.replace(msg, content=new_content, media=image_only)

        preview = msg.content[:80] + "..." if len(msg.content) > 80 else msg.content
        logger.info("Processing message from {}:{}: {}", msg.channel, msg.sender_id, preview)

        key = session_key or msg.session_key
        self.runtime_monitor.start_main_turn(
            session_key=key,
            channel=msg.channel,
            chat_id=msg.chat_id,
        )
        session = self.sessions.get_or_create(key)
        if self._restore_runtime_checkpoint(session):
            self.sessions.save(session)
        if self._restore_pending_user_turn(session):
            self.sessions.save(session)

        session, pending = self.auto_compact.prepare_session(session, key)

        # Slash commands
        raw = msg.content.strip()
        ctx = CommandContext(msg=msg, session=session, key=key, raw=raw, loop=self)
        if result := await self.commands.dispatch(ctx):
            self.runtime_monitor.finish_main_turn(stop_reason="command")
            return result

        await self.consolidator.maybe_consolidate_by_tokens(session)

        requester_agent_id = self._organization_requester_agent_id(msg)
        self._set_tool_context(
            msg.channel,
            msg.chat_id,
            msg.metadata.get("message_id"),
            requester_agent_id=requester_agent_id,
        )
        for tool_name in ("message", "openhire"):
            if tool := self.tools.get(tool_name):
                if hasattr(tool, "start_turn"):
                    tool.start_turn()

        history = session.get_history(max_messages=0)

        initial_messages = self.context.build_messages(
            history=history,
            current_message=msg.content,
            session_summary=pending,
            media=msg.media if msg.media else None,
            channel=msg.channel,
            chat_id=msg.chat_id,
        )
        self._update_admin_live_context(initial_messages)

        async def _bus_progress(content: str, *, tool_hint: bool = False) -> None:
            meta = dict(msg.metadata or {})
            meta["_progress"] = True
            meta["_tool_hint"] = tool_hint
            await self.bus.publish_outbound(
                OutboundMessage(
                    channel=msg.channel,
                    chat_id=msg.chat_id,
                    content=content,
                    metadata=meta,
                )
            )

        # Persist the triggering user message immediately, before running the
        # agent loop. If the process is killed mid-turn (OOM, SIGKILL, self-
        # restart, etc.), the existing runtime_checkpoint preserves the
        # in-flight assistant/tool state but NOT the user message itself, so
        # the user's prompt is silently lost on recovery. Saving it up front
        # makes recovery possible from the session log alone.
        user_persisted_early = False
        if isinstance(msg.content, str) and msg.content.strip():
            session.add_message("user", msg.content)
            self._mark_pending_user_turn(session)
            self.sessions.save(session)
            user_persisted_early = True

        try:
            final_content, _, all_msgs, stop_reason, had_injections = await self._run_agent_loop(
                initial_messages,
                on_progress=on_progress or _bus_progress,
                on_stream=on_stream,
                on_stream_end=on_stream_end,
                session=session,
                channel=msg.channel,
                chat_id=msg.chat_id,
                message_id=msg.metadata.get("message_id"),
                requester_agent_id=requester_agent_id,
                pending_queue=pending_queue,
            )
        except Exception as exc:
            self.runtime_monitor.finish_main_turn(stop_reason="error", error=str(exc))
            raise

        if final_content is None or not final_content.strip():
            final_content = EMPTY_FINAL_RESPONSE_MESSAGE

        # Skip the already-persisted user message when saving the turn
        save_skip = 1 + len(history) + (1 if user_persisted_early else 0)
        self._save_turn(session, all_msgs, save_skip)
        self._clear_pending_user_turn(session)
        self._clear_runtime_checkpoint(session)
        self.sessions.save(session)
        self._update_admin_session_snapshot(session, key, stop_reason=stop_reason)
        self.runtime_monitor.finish_main_turn(stop_reason=stop_reason)
        self._schedule_background(self.consolidator.maybe_consolidate_by_tokens(session))
        turn_start = max(0, 1 + len(history))
        self._maybe_schedule_skill_learning(
            messages=all_msgs[turn_start:],
            final_content=final_content,
            stop_reason=stop_reason,
            session_key=key,
        )

        openhire_sent = bool(getattr(self.tools.get("openhire"), "_sent_in_turn", False))
        if openhire_sent:
            return None

        # When follow-up messages were injected mid-turn, a later natural
        # language reply may address those follow-ups and should not be
        # suppressed just because MessageTool was used earlier in the turn.
        # However, if the turn falls back to the empty-final-response
        # placeholder, suppress it when the real user-visible output already
        # came from MessageTool.
        message_sent = bool(getattr(self.tools.get("message"), "_sent_in_turn", False))
        if message_sent:
            if not had_injections or stop_reason == "empty_final_response":
                return None

        preview = final_content[:120] + "..." if len(final_content) > 120 else final_content
        logger.info("Response to {}:{}: {}", msg.channel, msg.sender_id, preview)

        meta = dict(msg.metadata or {})
        if on_stream is not None and stop_reason != "error":
            meta["_streamed"] = True
        return OutboundMessage(
            channel=msg.channel,
            chat_id=msg.chat_id,
            content=final_content,
            metadata=meta,
        )

    @staticmethod
    def _strip_runtime_context_from_text(content: str) -> str:
        if not content.startswith(ContextBuilder._RUNTIME_CONTEXT_TAG):
            return content
        end_marker = ContextBuilder._RUNTIME_CONTEXT_END
        end_pos = content.find(end_marker)
        if end_pos >= 0:
            return content[end_pos + len(end_marker):].lstrip("\n")
        return content[len(ContextBuilder._RUNTIME_CONTEXT_TAG):].lstrip("\n")

    @classmethod
    def _clean_skill_learning_messages(cls, messages: list[dict[str, Any]]) -> list[dict[str, Any]]:
        cleaned: list[dict[str, Any]] = []
        for message in messages:
            entry = dict(message)
            if entry.get("role") == "user":
                content = entry.get("content")
                if isinstance(content, str):
                    entry["content"] = cls._strip_runtime_context_from_text(content)
                elif isinstance(content, list):
                    blocks: list[Any] = []
                    for block in content:
                        if isinstance(block, dict) and isinstance(block.get("text"), str):
                            text = cls._strip_runtime_context_from_text(block["text"])
                            if text.strip():
                                blocks.append({**block, "text": text})
                        else:
                            blocks.append(block)
                    entry["content"] = blocks
            cleaned.append(entry)
        return cleaned

    def _maybe_schedule_skill_learning(
        self,
        *,
        messages: list[dict[str, Any]],
        final_content: str,
        stop_reason: str,
        session_key: str,
    ) -> None:
        cleaned = self._clean_skill_learning_messages(messages)
        trigger_reasons = detect_skill_learning_trigger_reasons(cleaned, stop_reason=stop_reason)
        if not trigger_reasons:
            return

        async def _submit() -> None:
            generator = getattr(self, "_skill_proposal_generator", None)
            if generator is None:
                return
            await generator.submit_turn(
                messages=cleaned,
                final_content=final_content,
                trigger_reasons=trigger_reasons,
                session_key=session_key,
            )

        self._schedule_background(_submit())

    def _update_admin_session_snapshot(
        self,
        session: Session,
        session_key: str,
        *,
        stop_reason: str | None,
    ) -> None:
        """Cache the latest session context estimate for the admin dashboard."""
        context_tokens = 0
        source = "unknown"
        try:
            context_tokens, source = self.consolidator.estimate_session_prompt_tokens(session)
        except Exception:
            context_tokens = 0
        if context_tokens <= 0:
            context_tokens = int(self._last_usage.get("prompt_tokens", 0) or 0)
            if context_tokens > 0:
                source = "last_usage"
        self._last_admin_session_key = session_key
        self._last_admin_context_tokens = max(0, int(context_tokens))
        self._last_admin_context_source = source
        self._last_admin_stop_reason = "error" if stop_reason == "error" else None
        self.runtime_monitor.update_main_context(used_tokens=self._last_admin_context_tokens, source=source)
        self.runtime_monitor.update_usage(self._last_usage)

    def _update_admin_live_context(self, messages: list[dict[str, Any]]) -> None:
        context_tokens = 0
        source = "unknown"
        try:
            context_tokens, source = estimate_prompt_tokens_chain(
                self.provider,
                self.model,
                messages,
                self.tools.get_definitions(),
            )
        except Exception:
            context_tokens = sum(estimate_message_tokens(message) for message in messages)
            source = "tiktoken"
        self.runtime_monitor.update_main_context(used_tokens=context_tokens, source=source)

    async def get_admin_snapshot(self, process_role: str | None = None) -> dict[str, Any]:
        """Return a structured runtime snapshot for the admin dashboard."""
        from openhire.admin.runtime import build_admin_snapshot

        if process_role:
            self.runtime_monitor.set_process_role(process_role)
        return await build_admin_snapshot(self)

    def _resolve_admin_session_key(self, session_key: str | None = None) -> str | None:
        if session_key:
            return session_key

        explicit = getattr(self, "_last_admin_session_key", None)
        if explicit:
            return explicit

        try:
            session_infos = list(self.sessions.list_sessions())
        except Exception:
            return None

        def _is_internal(key: str) -> bool:
            if ":" not in key:
                return False
            channel, _ = key.split(":", 1)
            return channel in {"cli", "system", "cron", "heartbeat"}

        for info in session_infos:
            key = info.get("key") if isinstance(info, dict) else None
            if key and not _is_internal(str(key)):
                return str(key)
        if session_infos:
            key = session_infos[0].get("key") if isinstance(session_infos[0], dict) else None
            return str(key) if key else None
        return None

    def _has_active_session_task(self, session_key: str) -> bool:
        return any(not task.done() for task in self._active_tasks.get(session_key, []))

    async def clear_admin_context(self, session_key: str | None = None) -> dict[str, Any]:
        resolved_key = self._resolve_admin_session_key(session_key)
        if not resolved_key:
            raise ValueError("No active session context found.")
        if self._has_active_session_task(resolved_key):
            raise RuntimeError(f"Session '{resolved_key}' is currently busy.")

        lock = self._session_locks.setdefault(resolved_key, asyncio.Lock())
        async with lock:
            session = self.sessions.get_or_create(resolved_key)
            cleared_messages = len(session.messages)
            session.clear()
            session.metadata.clear()
            self.sessions.save(session)
            self.sessions.invalidate(resolved_key)
            self.auto_compact._summaries.pop(resolved_key, None)
            self._last_admin_session_key = resolved_key
            self._last_admin_context_tokens = 0
            self._last_admin_context_source = "cleared"
            self._last_admin_stop_reason = None
            self.runtime_monitor.update_main_context(used_tokens=0, source="cleared")
            return {
                "sessionKey": resolved_key,
                "clearedMessages": cleared_messages,
            }

    async def compact_admin_context(self, session_key: str | None = None) -> dict[str, Any]:
        resolved_key = self._resolve_admin_session_key(session_key)
        if not resolved_key:
            raise ValueError("No active session context found.")
        if self._has_active_session_task(resolved_key):
            raise RuntimeError(f"Session '{resolved_key}' is currently busy.")

        lock = self._session_locks.setdefault(resolved_key, asyncio.Lock())
        async with lock:
            self.sessions.invalidate(resolved_key)
            session = self.sessions.get_or_create(resolved_key)
            archive_msgs, kept_msgs = self.auto_compact._split_unconsolidated(session)
            if not archive_msgs:
                context_tokens, source = self.consolidator.estimate_session_prompt_tokens(session)
                self._last_admin_session_key = resolved_key
                self._last_admin_context_tokens = max(0, int(context_tokens))
                self._last_admin_context_source = source
                self.runtime_monitor.update_main_context(used_tokens=self._last_admin_context_tokens, source=source)
                return {
                    "sessionKey": resolved_key,
                    "archivedMessages": 0,
                    "keptMessages": len(session.messages),
                    "summaryCreated": False,
                }

            last_active = session.updated_at
            summary = await self.consolidator.archive(archive_msgs) or ""
            if summary and summary != "(nothing)":
                self.auto_compact._summaries[resolved_key] = (summary, last_active)
                session.metadata["_last_summary"] = {
                    "text": summary,
                    "last_active": last_active.isoformat(),
                }
            session.messages = kept_msgs
            session.last_consolidated = 0
            session.updated_at = datetime.now()
            self.sessions.save(session)
            context_tokens, source = self.consolidator.estimate_session_prompt_tokens(session)
            self._last_admin_session_key = resolved_key
            self._last_admin_context_tokens = max(0, int(context_tokens))
            self._last_admin_context_source = source
            self._last_admin_stop_reason = None
            self.runtime_monitor.update_main_context(used_tokens=self._last_admin_context_tokens, source=source)
            return {
                "sessionKey": resolved_key,
                "archivedMessages": len(archive_msgs),
                "keptMessages": len(kept_msgs),
                "summaryCreated": bool(summary),
            }

    async def delete_admin_container(self, container_name: str) -> dict[str, Any]:
        name = str(container_name or "").strip()
        if not name:
            raise ValueError("Container name is required.")

        status = await inspect_container_status(name)
        if status is None:
            raise ValueError(f"Container '{name}' not found.")

        proc = await asyncio.create_subprocess_exec(
            "docker", "rm", "-f", name,
            stdout=asyncio.subprocess.DEVNULL,
            stderr=asyncio.subprocess.PIPE,
        )
        _, err = await proc.communicate()
        if proc.returncode != 0:
            raise RuntimeError(f"docker rm failed: {err.decode(errors='replace')[:2000]}")
        return {"containerName": name, "deleted": True}

    def _sanitize_persisted_blocks(
        self,
        content: list[dict[str, Any]],
        *,
        should_truncate_text: bool = False,
        drop_runtime: bool = False,
    ) -> list[dict[str, Any]]:
        """Strip volatile multimodal payloads before writing session history."""
        filtered: list[dict[str, Any]] = []
        for block in content:
            if not isinstance(block, dict):
                filtered.append(block)
                continue

            if (
                drop_runtime
                and block.get("type") == "text"
                and isinstance(block.get("text"), str)
                and block["text"].startswith(ContextBuilder._RUNTIME_CONTEXT_TAG)
            ):
                continue

            if block.get("type") == "image_url" and block.get("image_url", {}).get(
                "url", ""
            ).startswith("data:image/"):
                path = (block.get("_meta") or {}).get("path", "")
                filtered.append({"type": "text", "text": image_placeholder_text(path)})
                continue

            if block.get("type") == "text" and isinstance(block.get("text"), str):
                text = block["text"]
                if should_truncate_text and len(text) > self.max_tool_result_chars:
                    text = truncate_text_fn(text, self.max_tool_result_chars)
                filtered.append({**block, "text": text})
                continue

            filtered.append(block)

        return filtered

    def _save_turn(self, session: Session, messages: list[dict], skip: int) -> None:
        """Save new-turn messages into session, truncating large tool results."""
        from datetime import datetime

        for m in messages[skip:]:
            entry = dict(m)
            role, content = entry.get("role"), entry.get("content")
            if role == "assistant" and not content and not entry.get("tool_calls"):
                continue  # skip empty assistant messages — they poison session context
            if role == "tool":
                if isinstance(content, str) and len(content) > self.max_tool_result_chars:
                    entry["content"] = truncate_text_fn(content, self.max_tool_result_chars)
                elif isinstance(content, list):
                    filtered = self._sanitize_persisted_blocks(content, should_truncate_text=True)
                    if not filtered:
                        continue
                    entry["content"] = filtered
            elif role == "user":
                if isinstance(content, str) and content.startswith(ContextBuilder._RUNTIME_CONTEXT_TAG):
                    # Strip the entire runtime-context block (including any session summary).
                    # The block is bounded by _RUNTIME_CONTEXT_TAG and _RUNTIME_CONTEXT_END.
                    end_marker = ContextBuilder._RUNTIME_CONTEXT_END
                    end_pos = content.find(end_marker)
                    if end_pos >= 0:
                        after = content[end_pos + len(end_marker):].lstrip("\n")
                        if after:
                            entry["content"] = after
                        else:
                            continue
                    else:
                        # Fallback: no end marker found, strip the tag prefix
                        after_tag = content[len(ContextBuilder._RUNTIME_CONTEXT_TAG):].lstrip("\n")
                        if after_tag.strip():
                            entry["content"] = after_tag
                        else:
                            continue
                if isinstance(content, list):
                    filtered = self._sanitize_persisted_blocks(content, drop_runtime=True)
                    if not filtered:
                        continue
                    entry["content"] = filtered
            entry.setdefault("timestamp", datetime.now().isoformat())
            session.messages.append(entry)
        session.updated_at = datetime.now()

    def _set_runtime_checkpoint(self, session: Session, payload: dict[str, Any]) -> None:
        """Persist the latest in-flight turn state into session metadata."""
        session.metadata[self._RUNTIME_CHECKPOINT_KEY] = payload
        self.sessions.save(session)

    def _mark_pending_user_turn(self, session: Session) -> None:
        session.metadata[self._PENDING_USER_TURN_KEY] = True

    def _clear_pending_user_turn(self, session: Session) -> None:
        session.metadata.pop(self._PENDING_USER_TURN_KEY, None)

    def _clear_runtime_checkpoint(self, session: Session) -> None:
        if self._RUNTIME_CHECKPOINT_KEY in session.metadata:
            session.metadata.pop(self._RUNTIME_CHECKPOINT_KEY, None)

    @staticmethod
    def _checkpoint_message_key(message: dict[str, Any]) -> tuple[Any, ...]:
        return (
            message.get("role"),
            message.get("content"),
            message.get("tool_call_id"),
            message.get("name"),
            message.get("tool_calls"),
            message.get("reasoning_content"),
            message.get("thinking_blocks"),
        )

    def _restore_runtime_checkpoint(self, session: Session) -> bool:
        """Materialize an unfinished turn into session history before a new request."""
        from datetime import datetime

        checkpoint = session.metadata.get(self._RUNTIME_CHECKPOINT_KEY)
        if not isinstance(checkpoint, dict):
            return False

        assistant_message = checkpoint.get("assistant_message")
        completed_tool_results = checkpoint.get("completed_tool_results") or []
        pending_tool_calls = checkpoint.get("pending_tool_calls") or []

        restored_messages: list[dict[str, Any]] = []
        if isinstance(assistant_message, dict):
            restored = dict(assistant_message)
            restored.setdefault("timestamp", datetime.now().isoformat())
            restored_messages.append(restored)
        for message in completed_tool_results:
            if isinstance(message, dict):
                restored = dict(message)
                restored.setdefault("timestamp", datetime.now().isoformat())
                restored_messages.append(restored)
        for tool_call in pending_tool_calls:
            if not isinstance(tool_call, dict):
                continue
            tool_id = tool_call.get("id")
            name = ((tool_call.get("function") or {}).get("name")) or "tool"
            restored_messages.append(
                {
                    "role": "tool",
                    "tool_call_id": tool_id,
                    "name": name,
                    "content": "Error: Task interrupted before this tool finished.",
                    "timestamp": datetime.now().isoformat(),
                }
            )

        overlap = 0
        max_overlap = min(len(session.messages), len(restored_messages))
        for size in range(max_overlap, 0, -1):
            existing = session.messages[-size:]
            restored = restored_messages[:size]
            if all(
                self._checkpoint_message_key(left) == self._checkpoint_message_key(right)
                for left, right in zip(existing, restored)
            ):
                overlap = size
                break
        session.messages.extend(restored_messages[overlap:])

        self._clear_pending_user_turn(session)
        self._clear_runtime_checkpoint(session)
        return True

    def _restore_pending_user_turn(self, session: Session) -> bool:
        """Close a turn that only persisted the user message before crashing."""
        from datetime import datetime

        if not session.metadata.get(self._PENDING_USER_TURN_KEY):
            return False

        if session.messages and session.messages[-1].get("role") == "user":
            session.messages.append(
                {
                    "role": "assistant",
                    "content": "Error: Task interrupted before a response was generated.",
                    "timestamp": datetime.now().isoformat(),
                }
            )
            session.updated_at = datetime.now()

        self._clear_pending_user_turn(session)
        return True

    async def process_direct(
        self,
        content: str,
        session_key: str = "cli:direct",
        channel: str = "cli",
        chat_id: str = "direct",
        media: list[str] | None = None,
        requester_agent_id: str | None = None,
        on_progress: Callable[[str], Awaitable[None]] | None = None,
        on_stream: Callable[[str], Awaitable[None]] | None = None,
        on_stream_end: Callable[..., Awaitable[None]] | None = None,
    ) -> OutboundMessage | None:
        """Process a message directly and return the outbound payload."""
        await self._connect_mcp()
        msg = InboundMessage(
            channel=channel, sender_id="user", chat_id=chat_id,
            content=content, media=media or [],
            metadata={"requester_agent_id": requester_agent_id} if requester_agent_id else {},
        )
        return await self._process_message(
            msg,
            session_key=session_key,
            on_progress=on_progress,
            on_stream=on_stream,
            on_stream_end=on_stream_end,
        )
