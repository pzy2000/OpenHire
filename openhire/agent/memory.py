"""Memory system: pure file I/O store, lightweight Consolidator, and Dream processor."""

from __future__ import annotations

import asyncio
import json
import re
import weakref
from datetime import datetime
from pathlib import Path
from typing import TYPE_CHECKING, Any, Callable

from loguru import logger

from openhire.utils.prompt_templates import render_template
from openhire.utils.helpers import ensure_dir, estimate_message_tokens, estimate_prompt_tokens_chain, strip_think

from openhire.agent.runner import AgentRunSpec, AgentRunner
from openhire.agent.tools.base import Tool, tool_parameters
from openhire.agent.tools.registry import ToolRegistry
from openhire.agent.tools.schema import ArraySchema, IntegerSchema, StringSchema, tool_parameters_schema
from openhire.agent_skill_service import AgentSkillService
from openhire.memory_write_service import (
    TRACKED_MEMORY_FILES,
    MemoryWriteError,
    MemoryWriteService,
)
from openhire.utils.gitstore import GitStore

if TYPE_CHECKING:
    from openhire.providers.base import LLMProvider
    from openhire.session.manager import Session, SessionManager


# ---------------------------------------------------------------------------
# MemoryStore — pure file I/O layer
# ---------------------------------------------------------------------------

class MemoryStore:
    """Pure file I/O for memory files: MEMORY.md, history.jsonl, SOUL.md, USER.md."""

    _DEFAULT_MAX_HISTORY = 1000
    _LEGACY_ENTRY_START_RE = re.compile(r"^\[(\d{4}-\d{2}-\d{2}[^\]]*)\]\s*")
    _LEGACY_TIMESTAMP_RE = re.compile(r"^\[(\d{4}-\d{2}-\d{2} \d{2}:\d{2})\]\s*")
    _LEGACY_RAW_MESSAGE_RE = re.compile(
        r"^\[\d{4}-\d{2}-\d{2}[^\]]*\]\s+[A-Z][A-Z0-9_]*(?:\s+\[tools:\s*[^\]]+\])?:"
    )

    def __init__(self, workspace: Path, max_history_entries: int = _DEFAULT_MAX_HISTORY):
        self.workspace = workspace
        self.max_history_entries = max_history_entries
        self.memory_dir = ensure_dir(workspace / "memory")
        self.memory_file = self.memory_dir / "MEMORY.md"
        self.history_file = self.memory_dir / "history.jsonl"
        self.legacy_history_file = self.memory_dir / "HISTORY.md"
        self.soul_file = workspace / "SOUL.md"
        self.user_file = workspace / "USER.md"
        self._cursor_file = self.memory_dir / ".cursor"
        self._dream_cursor_file = self.memory_dir / ".dream_cursor"
        self._git = GitStore(workspace, tracked_files=[
            "SOUL.md", "USER.md", "memory/MEMORY.md",
        ])
        self._maybe_migrate_legacy_history()

    @property
    def git(self) -> GitStore:
        return self._git

    # -- generic helpers -----------------------------------------------------

    @staticmethod
    def read_file(path: Path) -> str:
        try:
            return path.read_text(encoding="utf-8")
        except FileNotFoundError:
            return ""

    def _maybe_migrate_legacy_history(self) -> None:
        """One-time upgrade from legacy HISTORY.md to history.jsonl.

        The migration is best-effort and prioritizes preserving as much content
        as possible over perfect parsing.
        """
        if not self.legacy_history_file.exists():
            return
        if self.history_file.exists() and self.history_file.stat().st_size > 0:
            return

        try:
            legacy_text = self.legacy_history_file.read_text(
                encoding="utf-8",
                errors="replace",
            )
        except OSError:
            logger.exception("Failed to read legacy HISTORY.md for migration")
            return

        entries = self._parse_legacy_history(legacy_text)
        try:
            if entries:
                self._write_entries(entries)
                last_cursor = entries[-1]["cursor"]
                self._cursor_file.write_text(str(last_cursor), encoding="utf-8")
                # Default to "already processed" so upgrades do not replay the
                # user's entire historical archive into Dream on first start.
                self._dream_cursor_file.write_text(str(last_cursor), encoding="utf-8")

            backup_path = self._next_legacy_backup_path()
            self.legacy_history_file.replace(backup_path)
            logger.info(
                "Migrated legacy HISTORY.md to history.jsonl ({} entries)",
                len(entries),
            )
        except Exception:
            logger.exception("Failed to migrate legacy HISTORY.md")

    def _parse_legacy_history(self, text: str) -> list[dict[str, Any]]:
        normalized = text.replace("\r\n", "\n").replace("\r", "\n").strip()
        if not normalized:
            return []

        fallback_timestamp = self._legacy_fallback_timestamp()
        entries: list[dict[str, Any]] = []
        chunks = self._split_legacy_history_chunks(normalized)

        for cursor, chunk in enumerate(chunks, start=1):
            timestamp = fallback_timestamp
            content = chunk
            match = self._LEGACY_TIMESTAMP_RE.match(chunk)
            if match:
                timestamp = match.group(1)
                remainder = chunk[match.end():].lstrip()
                if remainder:
                    content = remainder

            entries.append({
                "cursor": cursor,
                "timestamp": timestamp,
                "content": content,
            })
        return entries

    def _split_legacy_history_chunks(self, text: str) -> list[str]:
        lines = text.split("\n")
        chunks: list[str] = []
        current: list[str] = []
        saw_blank_separator = False

        for line in lines:
            if saw_blank_separator and line.strip() and current:
                chunks.append("\n".join(current).strip())
                current = [line]
                saw_blank_separator = False
                continue
            if self._should_start_new_legacy_chunk(line, current):
                chunks.append("\n".join(current).strip())
                current = [line]
                saw_blank_separator = False
                continue
            current.append(line)
            saw_blank_separator = not line.strip()

        if current:
            chunks.append("\n".join(current).strip())
        return [chunk for chunk in chunks if chunk]

    def _should_start_new_legacy_chunk(self, line: str, current: list[str]) -> bool:
        if not current:
            return False
        if not self._LEGACY_ENTRY_START_RE.match(line):
            return False
        if self._is_raw_legacy_chunk(current) and self._LEGACY_RAW_MESSAGE_RE.match(line):
            return False
        return True

    def _is_raw_legacy_chunk(self, lines: list[str]) -> bool:
        first_nonempty = next((line for line in lines if line.strip()), "")
        match = self._LEGACY_TIMESTAMP_RE.match(first_nonempty)
        if not match:
            return False
        return first_nonempty[match.end():].lstrip().startswith("[RAW]")

    def _legacy_fallback_timestamp(self) -> str:
        try:
            return datetime.fromtimestamp(
                self.legacy_history_file.stat().st_mtime,
            ).strftime("%Y-%m-%d %H:%M")
        except OSError:
            return datetime.now().strftime("%Y-%m-%d %H:%M")

    def _next_legacy_backup_path(self) -> Path:
        candidate = self.memory_dir / "HISTORY.md.bak"
        suffix = 2
        while candidate.exists():
            candidate = self.memory_dir / f"HISTORY.md.bak.{suffix}"
            suffix += 1
        return candidate

    # -- MEMORY.md (long-term facts) -----------------------------------------

    def read_memory(self) -> str:
        return self.read_file(self.memory_file)

    def write_memory(self, content: str) -> None:
        self.memory_file.write_text(content, encoding="utf-8")

    # -- SOUL.md -------------------------------------------------------------

    def read_soul(self) -> str:
        return self.read_file(self.soul_file)

    def write_soul(self, content: str) -> None:
        self.soul_file.write_text(content, encoding="utf-8")

    # -- USER.md -------------------------------------------------------------

    def read_user(self) -> str:
        return self.read_file(self.user_file)

    def write_user(self, content: str) -> None:
        self.user_file.write_text(content, encoding="utf-8")

    # -- context injection (used by context.py) ------------------------------

    def get_memory_context(self) -> str:
        long_term = self.read_memory()
        return f"## Long-term Memory\n{long_term}" if long_term else ""

    # -- history.jsonl — append-only, JSONL format ---------------------------

    def append_history(self, entry: str) -> int:
        """Append *entry* to history.jsonl and return its auto-incrementing cursor."""
        cursor = self._next_cursor()
        ts = datetime.now().strftime("%Y-%m-%d %H:%M")
        record = {"cursor": cursor, "timestamp": ts, "content": strip_think(entry.rstrip()) or entry.rstrip()}
        with open(self.history_file, "a", encoding="utf-8") as f:
            f.write(json.dumps(record, ensure_ascii=False) + "\n")
        self._cursor_file.write_text(str(cursor), encoding="utf-8")
        return cursor

    def _next_cursor(self) -> int:
        """Read the current cursor counter and return next value."""
        if self._cursor_file.exists():
            try:
                return int(self._cursor_file.read_text(encoding="utf-8").strip()) + 1
            except (ValueError, OSError):
                pass
        # Fallback: read last line's cursor from the JSONL file.
        last = self._read_last_entry()
        if last:
            return last["cursor"] + 1
        return 1

    def read_unprocessed_history(self, since_cursor: int) -> list[dict[str, Any]]:
        """Return history entries with cursor > *since_cursor*."""
        return [e for e in self._read_entries() if e["cursor"] > since_cursor]

    def compact_history(self) -> None:
        """Drop oldest entries if the file exceeds *max_history_entries*."""
        if self.max_history_entries <= 0:
            return
        entries = self._read_entries()
        if len(entries) <= self.max_history_entries:
            return
        kept = entries[-self.max_history_entries:]
        self._write_entries(kept)

    # -- JSONL helpers -------------------------------------------------------

    def _read_entries(self) -> list[dict[str, Any]]:
        """Read all entries from history.jsonl."""
        entries: list[dict[str, Any]] = []
        try:
            with open(self.history_file, "r", encoding="utf-8") as f:
                for line in f:
                    line = line.strip()
                    if line:
                        try:
                            entries.append(json.loads(line))
                        except json.JSONDecodeError:
                            continue
        except FileNotFoundError:
            pass
        return entries

    def _read_last_entry(self) -> dict[str, Any] | None:
        """Read the last entry from the JSONL file efficiently."""
        try:
            with open(self.history_file, "rb") as f:
                f.seek(0, 2)
                size = f.tell()
                if size == 0:
                    return None
                read_size = min(size, 4096)
                f.seek(size - read_size)
                data = f.read().decode("utf-8")
                lines = [l for l in data.split("\n") if l.strip()]
                if not lines:
                    return None
                return json.loads(lines[-1])
        except (FileNotFoundError, json.JSONDecodeError, UnicodeDecodeError):
            return None

    def _write_entries(self, entries: list[dict[str, Any]]) -> None:
        """Overwrite history.jsonl with the given entries."""
        with open(self.history_file, "w", encoding="utf-8") as f:
            for entry in entries:
                f.write(json.dumps(entry, ensure_ascii=False) + "\n")

    # -- dream cursor --------------------------------------------------------

    def get_last_dream_cursor(self) -> int:
        if self._dream_cursor_file.exists():
            try:
                return int(self._dream_cursor_file.read_text(encoding="utf-8").strip())
            except (ValueError, OSError):
                pass
        return 0

    def set_last_dream_cursor(self, cursor: int) -> None:
        self._dream_cursor_file.write_text(str(cursor), encoding="utf-8")

    # -- message formatting utility ------------------------------------------

    @staticmethod
    def _format_messages(messages: list[dict]) -> str:
        lines = []
        for message in messages:
            if not message.get("content"):
                continue
            tools = f" [tools: {', '.join(message['tools_used'])}]" if message.get("tools_used") else ""
            lines.append(
                f"[{message.get('timestamp', '?')[:16]}] {message['role'].upper()}{tools}: {message['content']}"
            )
        return "\n".join(lines)

    def raw_archive(self, messages: list[dict]) -> None:
        """Fallback: dump raw messages to history.jsonl without LLM summarization."""
        self.append_history(
            f"[RAW] {len(messages)} messages\n"
            f"{self._format_messages(messages)}"
        )
        logger.warning(
            "Memory consolidation degraded: raw-archived {} messages", len(messages)
        )



# ---------------------------------------------------------------------------
# Consolidator — lightweight token-budget triggered consolidation
# ---------------------------------------------------------------------------


class Consolidator:
    """Lightweight consolidation: summarizes evicted messages into history.jsonl."""

    _MAX_CONSOLIDATION_ROUNDS = 5
    _MAX_CHUNK_MESSAGES = 60  # hard cap per consolidation round

    _SAFETY_BUFFER = 1024  # extra headroom for tokenizer estimation drift

    def __init__(
        self,
        store: MemoryStore,
        provider: LLMProvider,
        model: str,
        sessions: SessionManager,
        context_window_tokens: int,
        build_messages: Callable[..., list[dict[str, Any]]],
        get_tool_definitions: Callable[[], list[dict[str, Any]]],
        max_completion_tokens: int = 4096,
    ):
        self.store = store
        self.provider = provider
        self.model = model
        self.sessions = sessions
        self.context_window_tokens = context_window_tokens
        self.max_completion_tokens = max_completion_tokens
        self._build_messages = build_messages
        self._get_tool_definitions = get_tool_definitions
        self._locks: weakref.WeakValueDictionary[str, asyncio.Lock] = (
            weakref.WeakValueDictionary()
        )

    def get_lock(self, session_key: str) -> asyncio.Lock:
        """Return the shared consolidation lock for one session."""
        return self._locks.setdefault(session_key, asyncio.Lock())

    def pick_consolidation_boundary(
        self,
        session: Session,
        tokens_to_remove: int,
    ) -> tuple[int, int] | None:
        """Pick a user-turn boundary that removes enough old prompt tokens."""
        start = session.last_consolidated
        if start >= len(session.messages) or tokens_to_remove <= 0:
            return None

        removed_tokens = 0
        last_boundary: tuple[int, int] | None = None
        for idx in range(start, len(session.messages)):
            message = session.messages[idx]
            if idx > start and message.get("role") == "user":
                last_boundary = (idx, removed_tokens)
                if removed_tokens >= tokens_to_remove:
                    return last_boundary
            removed_tokens += estimate_message_tokens(message)

        return last_boundary

    def _cap_consolidation_boundary(
        self,
        session: Session,
        end_idx: int,
    ) -> int | None:
        """Clamp the chunk size without breaking the user-turn boundary."""
        start = session.last_consolidated
        if end_idx - start <= self._MAX_CHUNK_MESSAGES:
            return end_idx

        capped_end = start + self._MAX_CHUNK_MESSAGES
        for idx in range(capped_end, start, -1):
            if session.messages[idx].get("role") == "user":
                return idx
        return None

    def estimate_session_prompt_tokens(self, session: Session) -> tuple[int, str]:
        """Estimate current prompt size for the normal session history view."""
        history = session.get_history(max_messages=0)
        channel, chat_id = (session.key.split(":", 1) if ":" in session.key else (None, None))
        probe_messages = self._build_messages(
            history=history,
            current_message="[token-probe]",
            channel=channel,
            chat_id=chat_id,
        )
        return estimate_prompt_tokens_chain(
            self.provider,
            self.model,
            probe_messages,
            self._get_tool_definitions(),
        )

    async def archive(self, messages: list[dict]) -> str | None:
        """Summarize messages via LLM and append to history.jsonl.

        Returns the summary text on success, None if nothing to archive.
        """
        if not messages:
            return None
        try:
            formatted = MemoryStore._format_messages(messages)
            response = await self.provider.chat_with_retry(
                model=self.model,
                messages=[
                    {
                        "role": "system",
                        "content": render_template(
                            "agent/consolidator_archive.md",
                            strip=True,
                        ),
                    },
                    {"role": "user", "content": formatted},
                ],
                tools=None,
                tool_choice=None,
            )
            summary = response.content or "[no summary]"
            self.store.append_history(summary)
            return summary
        except Exception:
            logger.warning("Consolidation LLM call failed, raw-dumping to history")
            self.store.raw_archive(messages)
            return None

    async def maybe_consolidate_by_tokens(self, session: Session) -> None:
        """Loop: archive old messages until prompt fits within safe budget.

        The budget reserves space for completion tokens and a safety buffer
        so the LLM request never exceeds the context window.
        """
        if not session.messages or self.context_window_tokens <= 0:
            return

        lock = self.get_lock(session.key)
        async with lock:
            budget = self.context_window_tokens - self.max_completion_tokens - self._SAFETY_BUFFER
            target = budget // 2
            try:
                estimated, source = self.estimate_session_prompt_tokens(session)
            except Exception:
                logger.exception("Token estimation failed for {}", session.key)
                estimated, source = 0, "error"
            if estimated <= 0:
                return
            if estimated < budget:
                unconsolidated_count = len(session.messages) - session.last_consolidated
                logger.debug(
                    "Token consolidation idle {}: {}/{} via {}, msgs={}",
                    session.key,
                    estimated,
                    self.context_window_tokens,
                    source,
                    unconsolidated_count,
                )
                return

            for round_num in range(self._MAX_CONSOLIDATION_ROUNDS):
                if estimated <= target:
                    return

                boundary = self.pick_consolidation_boundary(session, max(1, estimated - target))
                if boundary is None:
                    logger.debug(
                        "Token consolidation: no safe boundary for {} (round {})",
                        session.key,
                        round_num,
                    )
                    return

                end_idx = boundary[0]
                end_idx = self._cap_consolidation_boundary(session, end_idx)
                if end_idx is None:
                    logger.debug(
                        "Token consolidation: no capped boundary for {} (round {})",
                        session.key,
                        round_num,
                    )
                    return

                chunk = session.messages[session.last_consolidated:end_idx]
                if not chunk:
                    return

                logger.info(
                    "Token consolidation round {} for {}: {}/{} via {}, chunk={} msgs",
                    round_num,
                    session.key,
                    estimated,
                    self.context_window_tokens,
                    source,
                    len(chunk),
                )
                if not await self.archive(chunk):
                    return
                session.last_consolidated = end_idx
                self.sessions.save(session)

                try:
                    estimated, source = self.estimate_session_prompt_tokens(session)
                except Exception:
                    logger.exception("Token estimation failed for {}", session.key)
                    estimated, source = 0, "error"
                if estimated <= 0:
                    return


# ---------------------------------------------------------------------------
# Dream — heavyweight cron-scheduled memory consolidation
# ---------------------------------------------------------------------------


@tool_parameters(
    tool_parameters_schema(
        action=StringSchema(
            "Proposal action: create for a new skill, patch/edit for an existing workspace skill",
            enum=["create", "patch", "edit"],
        ),
        name=StringSchema("Kebab-case skill name, e.g. repo-release-workflow"),
        reason=StringSchema("Why Dream proposes this skill"),
        content=StringSchema("Complete SKILL.md markdown including YAML frontmatter for create/edit proposals"),
        old_string=StringSchema("Exact existing SKILL.md substring for patch proposals"),
        new_string=StringSchema("Replacement text for patch proposals"),
        source=StringSchema("Proposal source", enum=["dream", "turn", "manual", "auto"]),
        trigger_reasons=ArraySchema(StringSchema("Trigger reason"), description="Why this proposal was triggered"),
        evidence=ArraySchema(StringSchema("Evidence line"), description="Short evidence snippets for the admin reviewer"),
        required=["name"],
    )
)
class ProposeAgentSkillTool(Tool):
    """Submit Dream-discovered skill candidates to the admin approval queue."""

    def __init__(self, workspace: Path) -> None:
        self._service = AgentSkillService(workspace)

    @property
    def name(self) -> str:
        return "propose_agent_skill"

    @property
    def description(self) -> str:
        return (
            "Create a pending Agent Skills Workbench proposal for a new SKILL.md. "
            "This does not write workspace/skills; an admin must approve the proposal first."
        )

    async def execute(
        self,
        action: str | None = None,
        name: str | None = None,
        content: str | None = None,
        reason: str | None = None,
        old_string: str | None = None,
        new_string: str | None = None,
        source: str | None = None,
        trigger_reasons: list[str] | None = None,
        evidence: list[str] | None = None,
        **kwargs: Any,
    ) -> str:
        if not name:
            return "Error: name is required."
        normalized_action = (action or "create").strip() or "create"
        if normalized_action in {"create", "edit"} and not content:
            return "Error: content is required for create/edit proposals."
        if normalized_action == "patch" and not old_string:
            return "Error: old_string is required for patch proposals."
        try:
            proposal = self._service.create_proposal(
                {
                    "action": normalized_action,
                    "name": name,
                    "reason": reason or "Dream discovered a repeatable workflow.",
                    "content": content or "",
                    "old_string": old_string or "",
                    "new_string": new_string or "",
                    "source": source or "dream",
                    "trigger_reasons": trigger_reasons or ["nontrivial_reusable_workflow"],
                    "evidence": evidence or [],
                }
            )
        except Exception as exc:
            return f"Error: {exc}"
        return (
            f"Created pending agent skill proposal {proposal['id']} for {proposal['name']}. "
            "Review it in Agent Skills Workbench before it can write workspace/skills."
        )


@tool_parameters(
    tool_parameters_schema(
        target_file=StringSchema(
            "Memory file to update",
            enum=["SOUL.md", "USER.md", "memory/MEMORY.md", "MEMORY.md"],
        ),
        action=StringSchema("Write action", enum=["append", "patch", "delete"]),
        old_text=StringSchema("Exact existing text for patch/delete actions"),
        new_text=StringSchema("Text to append or replacement text for patch actions"),
        category=StringSchema(
            "Memory category",
            enum=[
                "user_preference",
                "project_fact",
                "workflow_experience",
                "organization_relation",
                "employee_permission",
                "default_behavior",
                "security_policy",
                "required_skill",
                "runtime_default",
                "adapter_default",
                "temporary_status",
                "one_time_event",
                "other",
            ],
        ),
        impact=StringSchema("Impact level", enum=["low", "medium", "high"]),
        reason=StringSchema("Why this memory write should happen"),
        ttl_days=IntegerSchema(
            description="Optional TTL in days for time-limited facts; omit for stable facts",
            minimum=0,
            nullable=True,
        ),
        evidence=ArraySchema(
            StringSchema("Evidence pointer or excerpt"),
            description="Evidence from the processed session/history",
        ),
        required=["target_file", "action", "category", "impact", "reason", "evidence"],
    )
)
class MemoryWriteTool(Tool):
    """Govern long-term memory writes from Dream."""

    def __init__(self, store: MemoryStore, subject_id: str = "main") -> None:
        self._store = store
        self._service = MemoryWriteService(store.workspace)
        self._subject_id = subject_id
        self._run_context: dict[str, Any] = {}

    @property
    def name(self) -> str:
        return "memory_write"

    @property
    def description(self) -> str:
        return (
            "Submit a governed write to SOUL.md, USER.md, or memory/MEMORY.md. "
            "Low-risk long-term facts may be applied automatically; high-impact "
            "changes create an Admin review proposal."
        )

    def set_run_context(
        self,
        *,
        subject_id: str,
        cursor_start: int,
        cursor_end: int,
        source_excerpt: str,
    ) -> None:
        evidence = [
            (
                f"Dream subject={subject_id} workspace={self._store.workspace} "
                f"history_cursor={cursor_start}-{cursor_end}"
            )
        ]
        excerpt = source_excerpt.strip()
        if excerpt:
            evidence.append(f"Source excerpt: {excerpt[:1000]}")
        self._run_context = {
            "subject_id": subject_id,
            "workspace": str(self._store.workspace),
            "cursor_start": cursor_start,
            "cursor_end": cursor_end,
            "source_excerpt": excerpt[:1000],
            "evidence": evidence,
        }

    async def execute(
        self,
        target_file: str | None = None,
        action: str | None = None,
        old_text: str | None = None,
        new_text: str | None = None,
        category: str | None = None,
        impact: str | None = None,
        reason: str | None = None,
        ttl_days: int | None = None,
        evidence: list[str] | None = None,
        **kwargs: Any,
    ) -> str:
        try:
            result = self._service.submit(
                {
                    "target_file": target_file or "",
                    "action": action or "append",
                    "old_text": old_text or "",
                    "new_text": new_text or "",
                    "category": category or "other",
                    "impact": impact or "medium",
                    "reason": reason or "",
                    "ttl_days": ttl_days,
                    "evidence": evidence or [],
                },
                metadata=self._run_context,
            )
        except MemoryWriteError as exc:
            return f"Error: {exc}"
        status = result.get("status")
        if status == "auto_applied":
            record = result.get("record", {})
            return f"Applied governed memory write {record.get('id', '')} to {target_file}."
        if status == "pending":
            proposal = result.get("proposal", {})
            return (
                f"Created pending memory write proposal {proposal.get('id', '')} "
                f"for {proposal.get('target_file', target_file)}."
            )
        if status == "skipped":
            record = result.get("record", {})
            return f"Skipped transient memory write {record.get('id', '')}; recorded audit entry only."
        return f"Memory write result: {status}"


class Dream:
    """Two-phase memory processor: analyze history.jsonl, then edit files via AgentRunner.

    Phase 1 produces an analysis summary (plain LLM call).
    Phase 2 delegates to AgentRunner with read_file / edit_file tools for
    memory edits and propose_agent_skill for admin-approved skill candidates.
    """

    def __init__(
        self,
        store: MemoryStore,
        provider: LLMProvider,
        model: str,
        max_batch_size: int = 20,
        max_iterations: int = 10,
        max_tool_result_chars: int = 16_000,
        agent_skill_workspace: Path | None = None,
        subject_id: str = "main",
    ):
        self.store = store
        self.provider = provider
        self.model = model
        self.max_batch_size = max_batch_size
        self.max_iterations = max_iterations
        self.max_tool_result_chars = max_tool_result_chars
        self._runner = AgentRunner(provider)
        self.agent_skill_workspace = agent_skill_workspace or store.workspace
        self.subject_id = subject_id
        self._tools = self._build_tools()

    # -- tool registry -------------------------------------------------------

    def _build_tools(self) -> ToolRegistry:
        """Build a minimal tool registry for the Dream agent."""
        from openhire.agent.skills import BUILTIN_SKILLS_DIR
        from openhire.agent.tools.filesystem import EditFileTool, ReadFileTool

        tools = ToolRegistry()
        workspace = self.store.workspace
        skills_dir = workspace / "skills"
        tracked_memory_paths = {
            (workspace / rel).resolve()
            for rel in TRACKED_MEMORY_FILES
        }
        tracked_memory_paths.add((workspace / "MEMORY.md").resolve())

        class DreamEditFileTool(EditFileTool):
            async def execute(self, path: str | None = None, **kwargs: Any) -> str:
                if path:
                    try:
                        fp = self._resolve(path)
                        if fp.resolve() in tracked_memory_paths:
                            return (
                                "Error: Dream cannot edit long-term memory files directly. "
                                "Use memory_write so policy, evidence, and Admin review can be enforced."
                            )
                        fp.relative_to(skills_dir.resolve())
                        return (
                            "Error: Dream cannot write workspace/skills directly. "
                            "Use propose_agent_skill so an admin can approve it in Agent Skills Workbench."
                        )
                    except ValueError:
                        pass
                    except PermissionError as exc:
                        return f"Error: {exc}"
                return await super().execute(path=path, **kwargs)

        # Allow reading builtin skills for reference during skill creation
        extra_read = [BUILTIN_SKILLS_DIR] if BUILTIN_SKILLS_DIR.exists() else None
        tools.register(ReadFileTool(
            workspace=workspace,
            allowed_dir=workspace,
            extra_allowed_dirs=extra_read,
        ))
        tools.register(DreamEditFileTool(workspace=workspace, allowed_dir=workspace))
        tools.register(MemoryWriteTool(self.store, subject_id=self.subject_id))
        tools.register(ProposeAgentSkillTool(self.agent_skill_workspace))
        return tools

    # -- skill listing --------------------------------------------------------

    def _list_existing_skills(self) -> list[str]:
        """List existing skills as 'name — description' for dedup context."""
        import re as _re

        from openhire.agent.skills import BUILTIN_SKILLS_DIR

        _DESC_RE = _re.compile(r"^description:\s*(.+)$", _re.MULTILINE | _re.IGNORECASE)
        entries: dict[str, str] = {}
        for base in (self.store.workspace / "skills", BUILTIN_SKILLS_DIR):
            if not base.exists():
                continue
            for d in base.iterdir():
                if not d.is_dir():
                    continue
                skill_md = d / "SKILL.md"
                if not skill_md.exists():
                    continue
                # Prefer workspace skills over builtin (same name)
                if d.name in entries and base == BUILTIN_SKILLS_DIR:
                    continue
                content = skill_md.read_text(encoding="utf-8")[:500]
                m = _DESC_RE.search(content)
                desc = m.group(1).strip() if m else "(no description)"
                entries[d.name] = desc
        return [f"{name} — {desc}" for name, desc in sorted(entries.items())]

    # -- main entry ----------------------------------------------------------

    async def run(self) -> bool:
        """Process unprocessed history entries. Returns True if work was done."""
        from openhire.agent.skills import BUILTIN_SKILLS_DIR

        last_cursor = self.store.get_last_dream_cursor()
        entries = self.store.read_unprocessed_history(since_cursor=last_cursor)
        if not entries:
            return False

        batch = entries[: self.max_batch_size]
        logger.info(
            "Dream: processing {} entries (cursor {}→{}), batch={}",
            len(entries), last_cursor, batch[-1]["cursor"], len(batch),
        )

        # Build history text for LLM
        history_text = "\n".join(
            f"[{e['timestamp']}] {e['content']}" for e in batch
        )
        cursor_start = int(batch[0]["cursor"])
        cursor_end = int(batch[-1]["cursor"])

        # Current file contents
        current_date = datetime.now().strftime("%Y-%m-%d")
        current_memory = self.store.read_memory() or "(empty)"
        current_soul = self.store.read_soul() or "(empty)"
        current_user = self.store.read_user() or "(empty)"

        file_context = (
            f"## Current Date\n{current_date}\n\n"
            f"## Current MEMORY.md ({len(current_memory)} chars)\n{current_memory}\n\n"
            f"## Current SOUL.md ({len(current_soul)} chars)\n{current_soul}\n\n"
            f"## Current USER.md ({len(current_user)} chars)\n{current_user}"
        )

        # Phase 1: Analyze (no skills list — dedup is Phase 2's job)
        phase1_prompt = (
            f"## Conversation History\n{history_text}\n\n{file_context}"
        )

        try:
            phase1_response = await self.provider.chat_with_retry(
                model=self.model,
                messages=[
                    {
                        "role": "system",
                        "content": render_template("agent/dream_phase1.md", strip=True),
                    },
                    {"role": "user", "content": phase1_prompt},
                ],
                tools=None,
                tool_choice=None,
            )
            analysis = phase1_response.content or ""
            logger.debug("Dream Phase 1 analysis ({} chars): {}", len(analysis), analysis[:500])
        except Exception:
            logger.exception("Dream Phase 1 failed")
            return False

        # Phase 2: Delegate to AgentRunner with read_file / edit_file
        existing_skills = self._list_existing_skills()
        skills_section = ""
        if existing_skills:
            skills_section = (
                "\n\n## Existing Skills\n"
                + "\n".join(f"- {s}" for s in existing_skills)
            )
        phase2_prompt = f"## Analysis Result\n{analysis}\n\n{file_context}{skills_section}"

        tools = self._tools
        memory_write_tool = tools.get("memory_write")
        if hasattr(memory_write_tool, "set_run_context"):
            memory_write_tool.set_run_context(
                subject_id=self.subject_id,
                cursor_start=cursor_start,
                cursor_end=cursor_end,
                source_excerpt=history_text,
            )
        skill_creator_path = BUILTIN_SKILLS_DIR / "skill-creator" / "SKILL.md"
        messages: list[dict[str, Any]] = [
            {
                "role": "system",
                "content": render_template(
                    "agent/dream_phase2.md",
                    strip=True,
                    skill_creator_path=str(skill_creator_path),
                ),
            },
            {"role": "user", "content": phase2_prompt},
        ]

        try:
            result = await self._runner.run(AgentRunSpec(
                initial_messages=messages,
                tools=tools,
                model=self.model,
                max_iterations=self.max_iterations,
                max_tool_result_chars=self.max_tool_result_chars,
                fail_on_tool_error=False,
            ))
            logger.debug(
                "Dream Phase 2 complete: stop_reason={}, tool_events={}",
                result.stop_reason, len(result.tool_events),
            )
            for ev in (result.tool_events or []):
                logger.info("Dream tool_event: name={}, status={}, detail={}", ev.get("name"), ev.get("status"), ev.get("detail", "")[:200])
        except Exception:
            logger.exception("Dream Phase 2 failed")
            result = None

        # Build changelog from tool events
        changelog: list[str] = []
        if result and result.tool_events:
            for event in result.tool_events:
                if event["status"] == "ok":
                    changelog.append(f"{event['name']}: {event['detail']}")

        # Advance cursor — always, to avoid re-processing Phase 1
        new_cursor = batch[-1]["cursor"]
        self.store.set_last_dream_cursor(new_cursor)
        self.store.compact_history()

        if result and result.stop_reason == "completed":
            logger.info(
                "Dream done: {} change(s), cursor advanced to {}",
                len(changelog), new_cursor,
            )
        else:
            reason = result.stop_reason if result else "exception"
            logger.warning(
                "Dream incomplete ({}): cursor advanced to {}",
                reason, new_cursor,
            )

        # Git auto-commit (only when there are actual changes)
        if changelog and self.store.git.is_initialized():
            ts = batch[-1]["timestamp"]
            sha = self.store.git.auto_commit(f"dream: {ts}, {len(changelog)} change(s)")
            if sha:
                logger.info("Dream commit: {}", sha)

        return True
