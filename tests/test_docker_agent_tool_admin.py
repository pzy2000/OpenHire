from __future__ import annotations

from pathlib import Path

import pytest

from openhire.adapters import AdapterRegistry
from openhire.adapters.base import DockerAgent
from openhire.adapters.tool import DockerAgentTool
from openhire.admin.runtime import DockerAgentRuntimeTracker
from openhire.config.schema import DockerAgentConfig


class _FakeAdapter(DockerAgent):
    @property
    def agent_name(self) -> str:
        return "fake"

    @property
    def default_image(self) -> str:
        return "fake:latest"

    def build_command(
        self,
        task: str,
        role: str | None = None,
        tools: list[str] | None = None,
        skills: list[str] | None = None,
        *,
        instance_id: str | None = None,
    ) -> list[str]:
        return ["run", self.build_task_prompt(task, role, skills)]


@pytest.mark.asyncio
async def test_docker_agent_tool_tracks_current_command_during_execution(monkeypatch, tmp_path: Path) -> None:
    tracker = DockerAgentRuntimeTracker()
    registry = AdapterRegistry()
    registry.register(_FakeAdapter())

    async def fake_ensure_running(*_args, **_kwargs):
        return "openhire-fake"

    async def fake_exec(*_args, **_kwargs):
        snapshot = tracker.snapshot("fake")
        assert snapshot["currentCommand"].startswith("run ")
        return "ok"

    monkeypatch.setattr("openhire.adapters.tool.ensure_running", fake_ensure_running)
    monkeypatch.setattr("openhire.adapters.tool.exec_in_container", fake_exec)

    tool = DockerAgentTool(
        workspace=tmp_path,
        agents_config={"fake": DockerAgentConfig(persistent=True)},
        adapter_registry=registry,
        runtime_tracker=tracker,
        context_window_tokens=1000,
    )

    result = await tool.execute(agent="fake", task="build admin")

    assert result == "ok"
    snapshot = tracker.snapshot("fake")
    assert snapshot["currentCommand"] is None
    assert snapshot["lastPromptTokensEstimate"] > 0


def test_docker_agent_tool_description_only_lists_callable_agents(tmp_path: Path) -> None:
    registry = AdapterRegistry()
    registry.register(_FakeAdapter())

    tool = DockerAgentTool(
        workspace=tmp_path,
        agents_config={
            "fake": DockerAgentConfig(persistent=True),
            "claude-code": DockerAgentConfig(persistent=False),
        },
        adapter_registry=registry,
    )

    description = tool.description
    assert "Available agents: fake" in description
    assert "claude-code" not in description


@pytest.mark.asyncio
async def test_docker_agent_tool_unknown_agent_error_lists_callable_agents(tmp_path: Path) -> None:
    registry = AdapterRegistry()
    registry.register(_FakeAdapter())

    tool = DockerAgentTool(
        workspace=tmp_path,
        agents_config={
            "fake": DockerAgentConfig(persistent=True),
            "claude-code": DockerAgentConfig(persistent=False),
        },
        adapter_registry=registry,
    )

    result = await tool.execute(agent="claude-code", task="build admin")

    assert "Unknown agent 'claude-code'" in result
    assert "Available callable agents: fake" in result
