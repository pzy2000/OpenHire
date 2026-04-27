"""DockerAgentTool — dispatches tasks to external agents in Docker containers."""

from pathlib import Path
from typing import Any

from openhire.adapters import AdapterRegistry
from openhire.adapters.base import ensure_running, exec_in_container, run_container
from openhire.agent.tools.base import Tool, tool_parameters
from openhire.agent.tools.schema import (
    ArraySchema,
    IntegerSchema,
    StringSchema,
    tool_parameters_schema,
)


@tool_parameters(
    tool_parameters_schema(
        agent=StringSchema(
            "Agent type to dispatch the task to. Must be one of the exact available agent names listed in this tool description.",
        ),
        task=StringSchema("The task description for the agent to execute"),
        role=StringSchema("Role/persona for the agent to adopt", nullable=True),
        tools=ArraySchema(StringSchema(), description="Tools to enable for the agent", nullable=True),
        skills=ArraySchema(StringSchema(), description="Skills to enable for the agent", nullable=True),
        timeout=IntegerSchema(
            300,
            description="Timeout in seconds (default 300, max 1800)",
            minimum=30,
            maximum=1800,
        ),
        required=["agent", "task"],
    )
)
class DockerAgentTool(Tool):
    """Dispatch a task to an external AI agent running in a Docker container."""

    def __init__(
        self,
        workspace: Path,
        agents_config: dict[str, Any],
        adapter_registry: AdapterRegistry,
        runtime_tracker=None,
        context_window_tokens: int = 0,
    ) -> None:
        self._workspace = workspace
        self._config = agents_config
        self._registry = adapter_registry
        self._runtime_tracker = runtime_tracker
        self._context_window_tokens = context_window_tokens

    @property
    def name(self) -> str:
        return "docker_agent"

    @property
    def description(self) -> str:
        available = ", ".join(self._callable_agent_names())
        return (
            "Dispatch a task to an external AI agent running in a Docker container. "
            "You decide the role, tools, and skills for each call. "
            "Use only the exact agent names listed here; do not invent aliases or fallback names. "
            f"Available agents: {available or 'none configured'}"
        )

    def _enabled_configured_agent_names(self) -> list[str]:
        names: list[str] = []
        for name, cfg in self._config.items():
            if cfg.enabled if hasattr(cfg, "enabled") else True:
                names.append(name)
        return names

    def _callable_agent_names(self) -> list[str]:
        return [
            name for name in self._enabled_configured_agent_names()
            if self._registry.get(name) is not None
        ]

    async def execute(
        self,
        agent: str,
        task: str,
        role: str | None = None,
        tools: list[str] | None = None,
        skills: list[str] | None = None,
        timeout: int = 300,
        **kwargs: Any,
    ) -> str:
        # Look up adapter
        adapter = self._registry.get(agent)
        if not adapter:
            available = ", ".join(self._callable_agent_names())
            return f"Error: Unknown agent '{agent}'. Available callable agents: {available or 'none'}"

        # Look up config (key = adapter name)
        cfg_obj = self._config.get(agent)
        if not cfg_obj:
            available = ", ".join(self._callable_agent_names())
            return (
                f"Error: Agent '{agent}' is not configured in dockerAgents.agents. "
                f"Available callable agents: {available or 'none'}"
            )

        cfg = cfg_obj.model_dump() if hasattr(cfg_obj, "model_dump") else dict(cfg_obj)

        if not cfg.get("enabled", True):
            return f"Error: Agent '{agent}' is disabled."

        # Fall back to config defaults for role/tools/skills
        effective_role = role or cfg.get("role") or None
        effective_tools = tools or cfg.get("default_tools") or None
        effective_skills = skills or cfg.get("default_skills") or None

        persistent = cfg.get("persistent", True)
        prompt_text = adapter.build_task_prompt(task, effective_role, effective_skills)

        try:
            if persistent:
                container_name = await ensure_running(
                    adapter, agent, cfg, self._workspace,
                )
                command = adapter.build_command(
                    task, effective_role, effective_tools, effective_skills,
                    instance_id=container_name,
                )
            else:
                instance_id = cfg.get("container_name") or cfg.get("instance_name")
                command = adapter.build_command(
                    task, effective_role, effective_tools, effective_skills,
                    instance_id=instance_id,
                )
            if self._runtime_tracker is not None:
                self._runtime_tracker.register_start(
                    agent_key=agent,
                    command=command,
                    prompt_text=prompt_text,
                    context_window_tokens=self._context_window_tokens,
                )
            if persistent:
                return await exec_in_container(
                    container_name, adapter, task,
                    effective_role, effective_tools, effective_skills,
                    timeout, workspace=self._workspace,
                )
            return await run_container(
                adapter, task, effective_role, effective_tools, effective_skills,
                self._workspace, cfg, timeout,
            )
        finally:
            if self._runtime_tracker is not None:
                self._runtime_tracker.register_finish(agent)
