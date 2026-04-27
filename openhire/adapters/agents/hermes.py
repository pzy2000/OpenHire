"""Hermes agent adapter — runs NousResearch Hermes in Docker."""

from typing import Any

from openhire.adapters.base import DockerAgent


class HermesAdapter(DockerAgent):

    @property
    def agent_name(self) -> str:
        return "hermes"

    @property
    def default_image(self) -> str:
        return "openhire-hermes:latest"

    @property
    def needs_build(self) -> bool:
        return True

    @property
    def build_context_url(self) -> str:
        return "https://github.com/NousResearch/hermes-agent.git"

    def build_command(
        self,
        task: str,
        role: str | None = None,
        tools: list[str] | None = None,
        skills: list[str] | None = None,
        *,
        instance_id: str | None = None,
    ) -> list[str]:
        prompt = self._build_task_prompt(task, role, skills)
        source = f"openhire-{instance_id}" if instance_id else "openhire-ephemeral"
        return ["hermes", "chat", "--quiet", "--source", source, "-q", prompt]

    def build_init_commands(self, agent_cfg: dict[str, Any]) -> list[list[str]]:
        """Configure model inside the container after first creation."""
        return [
            ["hermes", "config", "set", "model.provider", "custom"],
            ["hermes", "config", "set", "model.base_url",
             "https://dashscope.aliyuncs.com/compatible-mode/v1"],
            ["hermes", "config", "set", "model.default", "qwen3.6-plus"],
            ["sh", "-c", "hermes config set model.api_key $DASHSCOPE_API_KEY"],
        ]
