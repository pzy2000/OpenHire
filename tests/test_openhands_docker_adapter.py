from __future__ import annotations

import asyncio
import importlib
import json
from pathlib import Path
from unittest.mock import AsyncMock, patch

import pytest

from openhire.adapters import build_default_registry
from openhire.adapters.agents.hermes import HermesAdapter
from openhire.adapters.agents.nanobot import NanobotAdapter
from openhire.adapters.agents.openclaw import OpenClawAdapter
from openhire.adapters.base import DockerAgent, ensure_running, exec_in_container, run_container
from openhire.adapters.tool import DockerAgentTool
from openhire.workforce.assignment import (
    default_agent_type_for_role,
    resolve_agent_type,
    valid_agent_types,
)


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


class _EarlyFailMonitorAdapter(_FakeAdapter):
    async def init_exec_monitor(self, container_name: str, workspace: Path | None = None):
        return {"poll_count": 0}

    async def poll_exec_monitor(self, container_name: str, monitor_state):
        monitor_state["poll_count"] += 1
        return "Error: monitor failed before command timeout."


class _NeverEndingProcess:
    def __init__(self) -> None:
        self.stdout = asyncio.StreamReader()
        self.stderr = asyncio.StreamReader()
        self.stdout.feed_eof()
        self.stderr.feed_eof()
        self.returncode: int | None = None
        self.killed = False

    async def wait(self) -> int:
        if self.killed:
            self.returncode = -9
            return -9
        raise asyncio.TimeoutError()

    def kill(self) -> None:
        self.killed = True


def test_openhands_adapter_module_is_disabled_marker_only() -> None:
    module = importlib.import_module("openhire.adapters.agents.openhands")

    assert not hasattr(module, "OpenHandsAdapter")


def test_openhands_adapter_is_not_registered_by_default() -> None:
    registry = build_default_registry()

    assert "openhands" not in registry.names()
    assert registry.names() == ["openclaw", "hermes", "nanobot"]


def test_openhands_is_not_a_valid_assignment_agent_type() -> None:
    assert "openhands" not in valid_agent_types()


def test_frontend_and_design_roles_default_to_nanobot() -> None:
    assert default_agent_type_for_role("Frontend Engineer / 前端工程师") == "nanobot"
    assert default_agent_type_for_role("UI 设计师") == "nanobot"


def test_openhands_recommendation_falls_back_to_nanobot_for_frontend_roles() -> None:
    assert resolve_agent_type("前端工程师", "openhands") == "nanobot"


def test_openhands_default_image_is_not_exposed_by_registered_adapters() -> None:
    registry = build_default_registry()
    images = [registry.get(name).default_image for name in registry.names()]

    assert all("openhands" not in image for image in images)


@pytest.mark.asyncio
async def test_openhands_config_is_not_callable_without_registered_adapter() -> None:
    tool = DockerAgentTool(
        workspace=Path("/tmp/workspace"),
        agents_config={"openhands": {"enabled": True, "image": "disabled:latest"}},
        adapter_registry=build_default_registry(),
    )

    result = await tool.execute(agent="openhands", task="probe")

    assert result == "Error: Unknown agent 'openhands'. Available callable agents: none"


@pytest.mark.asyncio
async def test_exec_in_container_returns_early_monitor_error() -> None:
    proc = _NeverEndingProcess()
    adapter = _EarlyFailMonitorAdapter()
    expected = "Error: monitor failed before command timeout."

    with patch("asyncio.create_subprocess_exec", new_callable=AsyncMock) as mock_exec:
        mock_exec.return_value = proc
        result = await exec_in_container(
            "openhire-fake",
            adapter,
            "probe",
            None,
            None,
            None,
            timeout=300,
            workspace=Path("/tmp/workspace"),
        )

    assert result == expected
    assert proc.killed is True


@pytest.mark.asyncio
async def test_generic_agents_keep_workspace_bind_mounts() -> None:
    workspace = Path("/tmp/generic-workspace")
    proc = AsyncMock()
    proc.communicate.return_value = (b"ok", b"")
    proc.returncode = 0

    with (
        patch("openhire.adapters.base._ensure_image", new=AsyncMock()),
        patch("asyncio.create_subprocess_exec", new_callable=AsyncMock) as mock_exec,
    ):
        mock_exec.return_value = proc

        await run_container(
            _FakeAdapter(),
            "build admin",
            None,
            None,
            None,
            workspace,
            {"image": "fake:latest"},
        )

    args = mock_exec.call_args.args
    assert f"{workspace}:/workspace" in args
    assert "-w" in args
    assert "/workspace" in args


def test_git_build_context_urls_use_repo_remotes_not_html_pages() -> None:
    assert OpenClawAdapter().build_context_url.endswith(".git")
    assert HermesAdapter().build_context_url.endswith(".git")
    assert NanobotAdapter().build_context_url.endswith(".git")


@pytest.mark.asyncio
async def test_nanobot_persistent_container_overrides_entrypoint_for_keepalive() -> None:
    workspace = Path("/tmp/nanobot-workspace")
    create_proc = AsyncMock()
    create_proc.communicate.return_value = (b"container-id", b"")
    create_proc.returncode = 0
    start_proc = AsyncMock()
    start_proc.communicate.return_value = (b"", b"")
    start_proc.returncode = 0

    with (
        patch("openhire.adapters.base._ensure_image", new=AsyncMock()),
        patch("openhire.adapters.base._inspect_container", new=AsyncMock(return_value=None)),
        patch("asyncio.create_subprocess_exec", new_callable=AsyncMock) as mock_exec,
    ):
        mock_exec.side_effect = [create_proc, start_proc]

        await ensure_running(
            NanobotAdapter(),
            "nanobot",
            {"image": "openhire-nanobot:latest"},
            workspace,
        )

    create_args = mock_exec.call_args_list[0].args
    assert "--entrypoint" in create_args
    assert "sh" in create_args
    assert create_args[-2:] == ("-lc", "tail -f /dev/null")


def test_nanobot_build_command_uses_nanobot_cli() -> None:
    adapter = NanobotAdapter()

    command = adapter.build_command(
        "design a skill",
        role="algo",
        skills=["reasoning"],
        instance_id="openhire-nano",
    )

    assert command[:3] == ["nanobot", "agent", "--session"]
    assert command[3] == "openhire-delegate-openhire-nano"
    assert command[4:6] == ["--workspace", "/workspace"]
    assert command[6] == "--message"
    assert "design a skill" in command[7]


def test_hermes_build_command_uses_stable_openhire_source() -> None:
    adapter = HermesAdapter()

    command = adapter.build_command("run task", role="dev", instance_id="openhire-hermes")

    assert command[:4] == ["hermes", "chat", "--quiet", "--source"]
    assert command[4] == "openhire-openhire-hermes"
    assert command[5:7] == ["-q", "[Role: dev]\nrun task"]


def test_openclaw_build_command_uses_openclaw_cli() -> None:
    adapter = OpenClawAdapter()

    command = adapter.build_command(
        "run task",
        role="dev",
        skills=["coding"],
        instance_id="openhire-abc",
    )

    assert command[:4] == [
        "openclaw",
        "agent",
        "--session-id",
        "openhire-delegate-openhire-abc",
    ]
    assert command[4] == "--message"
    assert "run task" in command[5]


def test_openclaw_environment_rewrites_localhost_llm_base_url_on_desktop() -> None:
    adapter = OpenClawAdapter()
    source = {"LLM_BASE_URL": "http://localhost:16666/v1", "LLM_MODEL": "openai/gpt-5.4"}

    with patch(
        "openhire.adapters.agents.openclaw._should_rewrite_localhost_base_url",
        return_value=True,
    ):
        env = adapter.environment(source)

    assert env["LLM_BASE_URL"] == "http://host.docker.internal:16666/v1"
    assert env["LLM_MODEL"] == "openai/gpt-5.4"
    assert env["OPENHIRE_OPENCLAW_CONFIG_VERSION"] == "2"


def test_openclaw_build_init_commands_write_runtime_model_config() -> None:
    adapter = OpenClawAdapter()

    with patch(
        "openhire.adapters.agents.openclaw._should_rewrite_localhost_base_url",
        return_value=True,
    ):
        commands = adapter.build_init_commands({
            "env": {
                "LLM_MODEL": "gpt-5.4",
                "LLM_API_KEY": "dummy",
                "LLM_PROVIDER": "openai",
                "LLM_BASE_URL": "http://localhost:16666/v1",
            },
            "acp": {
                "backend": "acpx",
                "default_agent": "codex",
                "allowed_agents": ["codex"],
            },
        })

    runtime_command = commands[0]
    assert runtime_command[:4] == ["openclaw", "config", "set", "--batch-json"]
    runtime_updates = json.loads(runtime_command[4])
    assert runtime_updates == [
        {"path": "agents.defaults.model", "value": "openai/gpt-5.4"},
        {
            "path": "models.providers.openai",
            "value": {
                "baseUrl": "http://host.docker.internal:16666/v1",
                "apiKey": "dummy",
                "api": "openai-completions",
                "models": [],
                "request": {"allowPrivateNetwork": True},
            },
        },
    ]
    flattened = "\n".join(" ".join(command) for command in commands)
    assert "agent.model" not in flattened
    assert "qwen3.6-plus" not in flattened
    assert "dashscope.aliyuncs.com" not in flattened
    assert ["openclaw", "config", "set", "acp.defaultAgent", "codex"] in commands


def test_openclaw_build_init_commands_keep_acp_when_llm_config_missing() -> None:
    adapter = OpenClawAdapter()

    commands = adapter.build_init_commands({
        "env": {
            "LLM_MODEL": "openai/gpt-5.4",
        },
        "acp": {
            "default_agent": "codex",
        },
    })

    flattened = "\n".join(" ".join(command) for command in commands)
    assert "models.providers.openai.apiKey" not in flattened
    assert ["openclaw", "config", "set", "acp.defaultAgent", "codex"] in commands


def test_nanobot_environment_rewrites_localhost_llm_base_url_on_desktop() -> None:
    adapter = NanobotAdapter()
    source = {"LLM_BASE_URL": "http://localhost:16666/v1", "LLM_MODEL": "openai/gpt-5.4"}

    with patch(
        "openhire.adapters.agents.nanobot._should_rewrite_localhost_base_url",
        return_value=True,
    ):
        env = adapter.environment(source)

    assert env["LLM_BASE_URL"] == "http://host.docker.internal:16666/v1"
    assert env["LLM_MODEL"] == "openai/gpt-5.4"


def test_nanobot_build_init_commands_write_runtime_config() -> None:
    adapter = NanobotAdapter()

    with patch(
        "openhire.adapters.agents.nanobot._should_rewrite_localhost_base_url",
        return_value=True,
    ):
        commands = adapter.build_init_commands({
            "env": {
                "LLM_MODEL": "openai/gpt-5.4",
                "LLM_API_KEY": "dummy",
                "LLM_PROVIDER": "openai",
                "LLM_BASE_URL": "http://localhost:16666/v1",
            }
        })

    assert len(commands) == 1
    command = commands[0]
    assert command[:2] == ["python", "-c"]
    runtime_config = json.loads(command[3])
    assert runtime_config["agents"]["defaults"] == {
        "workspace": "/workspace",
        "model": "gpt-5.4",
        "provider": "openai",
    }
    assert runtime_config["providers"]["openai"]["apiKey"] == "dummy"
    assert runtime_config["providers"]["openai"]["apiBase"] == "http://host.docker.internal:16666/v1"


def test_nanobot_build_init_commands_skip_when_llm_config_missing() -> None:
    adapter = NanobotAdapter()

    commands = adapter.build_init_commands({"env": {"LLM_MODEL": "openai/gpt-5.4"}})

    assert commands == []


def test_nanobot_build_init_commands_use_provider_hint_for_prefixed_model() -> None:
    adapter = NanobotAdapter()

    commands = adapter.build_init_commands({
        "env": {
            "LLM_MODEL": "gpt-5.4",
            "LLM_API_KEY": "dummy",
            "LLM_PROVIDER": "openai",
        }
    })

    runtime_config = json.loads(commands[0][3])
    assert runtime_config["agents"]["defaults"]["provider"] == "openai"
    assert runtime_config["agents"]["defaults"]["model"] == "gpt-5.4"
