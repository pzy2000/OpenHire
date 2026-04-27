from __future__ import annotations

from pathlib import Path
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from openhire.agent.loop import AgentLoop
from openhire.bus.events import InboundMessage, OutboundMessage
from openhire.bus.queue import MessageBus
from openhire.config.schema import (
    AgentDefaults,
    Config,
    DockerAgentConfig,
    DockerAgentsConfig,
    OpenHireConfig,
)
from openhire.providers.base import GenerationSettings, LLMProvider, LLMResponse, ToolCallRequest
from openhire.workforce.required_skill import (
    REQUIRED_EMPLOYEE_SKILL_ID,
    REQUIRED_EMPLOYEE_SKILL_NAME,
    REQUIRED_EMPLOYEE_SKILL_PROMPT_START,
)
from openhire.workforce.registry import AgentEntry, AgentRegistry
from openhire.workforce.store import OpenHireStore
from openhire.workforce.tool import OpenHireTool
from openhire.skill_catalog import SkillCatalogService, SkillCatalogStore


def _employee_workspace(workspace: Path, agent_id: str) -> Path:
    return workspace / "openhire" / "employees" / agent_id / "workspace"


def _seed_employee(workspace: Path, **overrides) -> AgentEntry:
    registry = AgentRegistry(OpenHireStore(workspace))
    entry = AgentEntry(
        agent_id="nova-fe",
        name="Nova FE",
        role="前端工程师",
        agent_type="nanobot",
        skills=["react", "typescript"],
        skill_ids=["skill-react", "skill-ts"],
        system_prompt="你是资深前端数字员工，优先处理 Web UI 与交互任务。",
        tools=["figma"],
        status="active",
        container_name="openhire-nova-fe",
    )
    for key, value in overrides.items():
        setattr(entry, key, value)
    return registry.register(entry)


def _docker_enabled_config() -> DockerAgentsConfig:
    return DockerAgentsConfig(
        enabled=True,
        agents={"nanobot": DockerAgentConfig(enabled=True, persistent=True)},
    )


def _tool_names(tools: list[dict[str, object]] | None) -> list[str]:
    names: list[str] = []
    for tool in tools or []:
        fn = tool.get("function") if isinstance(tool, dict) else None
        if isinstance(fn, dict) and isinstance(fn.get("name"), str):
            names.append(fn["name"])
            continue
        if isinstance(tool, dict) and isinstance(tool.get("name"), str):
            names.append(tool["name"])
    return names


def _make_provider() -> MagicMock:
    provider = MagicMock()
    provider.get_default_model.return_value = "test-model"
    provider.generation = GenerationSettings()
    return provider


class _ListEmployeesProvider(LLMProvider):
    def __init__(self) -> None:
        super().__init__(api_key="dummy", api_base="http://dummy")
        self.generation = GenerationSettings()
        self._call_count = 0

    def get_default_model(self) -> str:
        return "test-model"

    async def chat(self, *args, **kwargs) -> LLMResponse:
        raise NotImplementedError

    async def chat_with_retry(self, *, messages, tools=None, **kwargs) -> LLMResponse:
        self._call_count += 1
        if self._call_count == 1:
            assert "openhire" in _tool_names(tools)
            return LLMResponse(
                content="",
                tool_calls=[ToolCallRequest(id="call_1", name="openhire", arguments={"action": "list"})],
                usage={},
            )

        last_tool = next(
            msg for msg in reversed(messages)
            if msg.get("role") == "tool" and msg.get("name") == "openhire"
        )
        return LLMResponse(
            content=f"数字员工清单:\n{last_tool['content']}",
            tool_calls=[],
            usage={},
        )


class _SkillSelectionProvider(LLMProvider):
    def __init__(self, responses: list[str]) -> None:
        super().__init__(api_key="dummy", api_base="http://dummy")
        self.generation = GenerationSettings()
        self.responses = list(responses)
        self.calls: list[dict] = []

    def get_default_model(self) -> str:
        return "test-model"

    async def chat(self, *args, **kwargs) -> LLMResponse:
        raise NotImplementedError

    async def chat_with_retry(self, **kwargs) -> LLMResponse:
        self.calls.append(kwargs)
        return LLMResponse(content=self.responses.pop(0), tool_calls=[], usage={})


def _seed_catalog(workspace: Path) -> dict[str, str]:
    service = SkillCatalogService(SkillCatalogStore(workspace))
    imported = service.upsert_many(
        [
            {
                "source": "clawhub",
                "external_id": "gmail",
                "name": "Gmail",
                "description": "Read and send Gmail.",
                "source_url": "https://clawhub.ai/byungkyu/gmail",
                "tags": ["scenario:邮箱与消息分诊"],
                "markdown": "---\nname: gmail\ndescription: Read and send Gmail.\n---\n\n# Gmail\n",
            },
            {
                "source": "clawhub",
                "external_id": "slack",
                "name": "Slack",
                "description": "Manage Slack messages.",
                "source_url": "https://clawhub.ai/steipete/slack",
                "tags": ["scenario:邮箱与消息分诊"],
                "markdown": "---\nname: slack\ndescription: Manage Slack messages.\n---\n\n# Slack\n",
            },
            {
                "source": "clawhub",
                "external_id": "jira",
                "name": "JIRA",
                "description": "Manage tickets.",
                "source_url": "https://clawhub.ai/jdrhyne/jira",
                "tags": ["scenario:工单分派"],
                "markdown": "---\nname: jira\ndescription: Manage tickets.\n---\n\n# JIRA\n",
            },
        ]
    )
    return {entry.external_id: entry.id for entry in imported}


def test_openhire_config_enabled_by_default() -> None:
    assert Config().openhire.enabled is True


def test_agent_loop_can_disable_openhire_tool_explicitly(tmp_path: Path) -> None:
    defaults = AgentDefaults()
    config = Config()

    enabled_loop = AgentLoop(
        bus=MessageBus(),
        provider=_make_provider(),
        workspace=tmp_path,
        model="test-model",
        context_window_tokens=defaults.context_window_tokens,
        openhire_config=config.openhire,
        docker_agents_config=config.tools.docker_agents,
    )
    disabled_loop = AgentLoop(
        bus=MessageBus(),
        provider=_make_provider(),
        workspace=tmp_path,
        model="test-model",
        context_window_tokens=defaults.context_window_tokens,
        openhire_config=OpenHireConfig(enabled=False),
        docker_agents_config=config.tools.docker_agents,
    )

    assert "openhire" in enabled_loop.tools.tool_names
    assert "openhire" not in disabled_loop.tools.tool_names


@pytest.mark.asyncio
async def test_agent_loop_can_query_employees_with_default_openhire_config(tmp_path: Path) -> None:
    entry = _seed_employee(tmp_path)
    config = Config()
    loop = AgentLoop(
        bus=MessageBus(),
        provider=_ListEmployeesProvider(),
        workspace=tmp_path,
        model="test-model",
        context_window_tokens=AgentDefaults().context_window_tokens,
        openhire_config=config.openhire,
        docker_agents_config=config.tools.docker_agents,
    )

    response = await loop.process_direct(
        "请告诉我现在有哪些数字员工，以及他们对应的 skill。",
        session_key="api:test-openhire",
        channel="api",
        chat_id="default",
    )

    assert response is not None
    assert entry.name in response.content
    assert entry.role in response.content
    assert "skills=react,typescript" in response.content


@pytest.mark.asyncio
async def test_openhire_get_accepts_employee_name(tmp_path: Path) -> None:
    entry = _seed_employee(tmp_path)
    tool = OpenHireTool(
        workspace=tmp_path,
        openhire_config=OpenHireConfig(enabled=True),
        docker_agents_config=DockerAgentsConfig(enabled=True),
    )

    result = await tool.execute(action="get", name="nova fe")

    assert f'"agent_id": "{entry.agent_id}"' in result
    assert f'"name": "{entry.name}"' in result


@pytest.mark.asyncio
async def test_openhire_register_adds_required_employee_skill(tmp_path: Path) -> None:
    tool = OpenHireTool(
        workspace=tmp_path,
        openhire_config=OpenHireConfig(enabled=True),
        docker_agents_config=DockerAgentsConfig(enabled=False),
    )

    result = await tool.execute(
        action="register",
        name="Ops",
        owner_id="user-ops",
        role="运营效率专家",
        skills=["feishu"],
    )

    assert "Registered: Ops" in result
    entry = tool.registry.all()[0]
    assert entry.skill_ids == [REQUIRED_EMPLOYEE_SKILL_ID]
    assert entry.skills == [REQUIRED_EMPLOYEE_SKILL_NAME, "feishu"]
    assert REQUIRED_EMPLOYEE_SKILL_PROMPT_START in entry.system_prompt


@pytest.mark.asyncio
async def test_openhire_register_in_feishu_group_auto_joins_current_group(tmp_path: Path) -> None:
    tool = OpenHireTool(
        workspace=tmp_path,
        openhire_config=OpenHireConfig(enabled=True),
        docker_agents_config=DockerAgentsConfig(enabled=False),
    )
    tool.set_context("feishu", "oc_group")

    result = await tool.execute(
        action="register",
        name="市场总监",
        owner_id="user-market",
        role="负责市场调研",
        agent_type="nanobot",
        tools=["message"],
    )

    assert "Registered: 市场总监" in result
    entry = tool.registry.all()[0]
    assert entry.group_ids == ["oc_group"]


@pytest.mark.asyncio
async def test_openhire_register_does_not_auto_join_without_message_tool(tmp_path: Path) -> None:
    tool = OpenHireTool(
        workspace=tmp_path,
        openhire_config=OpenHireConfig(enabled=True),
        docker_agents_config=DockerAgentsConfig(enabled=False),
    )
    tool.set_context("feishu", "oc_group")

    await tool.execute(
        action="register",
        name="无消息员工",
        owner_id="user-no-message",
        role="只做内部任务",
        agent_type="nanobot",
        tools=["read_file"],
    )

    entry = tool.registry.all()[0]
    assert entry.group_ids == []


@pytest.mark.asyncio
async def test_openhire_register_does_not_auto_join_feishu_dm(tmp_path: Path) -> None:
    tool = OpenHireTool(
        workspace=tmp_path,
        openhire_config=OpenHireConfig(enabled=True),
        docker_agents_config=DockerAgentsConfig(enabled=False),
    )
    tool.set_context("feishu", "ou_user")

    await tool.execute(
        action="register",
        name="私聊员工",
        owner_id="user-dm",
        role="私聊上下文创建",
        agent_type="nanobot",
        tools=["message"],
    )

    entry = tool.registry.all()[0]
    assert entry.group_ids == []


@pytest.mark.asyncio
async def test_openhire_register_without_provider_keeps_legacy_response_shape(tmp_path: Path) -> None:
    _seed_catalog(tmp_path)
    tool = OpenHireTool(
        workspace=tmp_path,
        openhire_config=OpenHireConfig(enabled=True),
        docker_agents_config=DockerAgentsConfig(enabled=False),
    )

    result = await tool.execute(
        action="register",
        name="Legacy",
        owner_id="user-legacy",
        role="邮箱与消息分诊员",
    )

    assert "Registered: Legacy" in result
    assert "Skill selection warning" not in result
    entry = tool.registry.all()[0]
    assert entry.skill_ids == [REQUIRED_EMPLOYEE_SKILL_ID]


@pytest.mark.asyncio
async def test_openhire_register_auto_selects_catalog_skills_and_preserves_explicit(tmp_path: Path) -> None:
    ids = _seed_catalog(tmp_path)
    provider = _SkillSelectionProvider([
        f'{{"skill_ids":["{ids["gmail"]}","{ids["slack"]}"],"reason":"message triage"}}',
        '{"soul":"Inbox Ops answers like a focused operations specialist.","agents":"Inbox Ops triages messages and keeps evidence links."}',
    ])
    tool = OpenHireTool(
        workspace=tmp_path,
        openhire_config=OpenHireConfig(enabled=True),
        docker_agents_config=DockerAgentsConfig(enabled=False),
        provider=provider,
    )

    result = await tool.execute(
        action="register",
        name="Inbox Ops",
        owner_id="user-inbox",
        role="邮箱与消息分诊员",
        skills=["triage"],
    )

    assert "Registered: Inbox Ops" in result
    entry = tool.registry.all()[0]
    assert entry.skill_ids == [REQUIRED_EMPLOYEE_SKILL_ID, ids["gmail"], ids["slack"]]
    assert entry.skills == [REQUIRED_EMPLOYEE_SKILL_NAME, "triage", "Gmail", "Slack"]
    employee_workspace = _employee_workspace(tmp_path, entry.agent_id)
    assert "Inbox Ops answers like a focused operations specialist." in (
        employee_workspace / "SOUL.md"
    ).read_text(encoding="utf-8")
    assert "Inbox Ops triages messages and keeps evidence links." in (
        employee_workspace / "AGENTS.md"
    ).read_text(encoding="utf-8")
    assert len(provider.calls) == 2


@pytest.mark.asyncio
async def test_openhire_setup_group_auto_selects_skills_per_member(tmp_path: Path) -> None:
    ids = _seed_catalog(tmp_path)
    provider = _SkillSelectionProvider([
        f'{{"skill_ids":["{ids["gmail"]}"],"reason":"mail"}}',
        f'{{"skill_ids":["{ids["jira"]}"],"reason":"tickets"}}',
        '{"soul":"Mail Bot keeps a calm inbox voice.","agents":"Mail Bot follows inbox triage steps."}',
        '{"soul":"Ticket Bot is direct about queue ownership.","agents":"Ticket Bot follows ticket routing steps."}',
    ])
    tool = OpenHireTool(
        workspace=tmp_path,
        openhire_config=OpenHireConfig(enabled=True),
        docker_agents_config=DockerAgentsConfig(enabled=False),
        provider=provider,
    )

    result = await tool.execute(
        action="setup_group",
        group_id="ops-group",
        members=[
            {"owner_id": "mail", "name": "Mail Bot", "role": "邮箱与消息分诊员"},
            {"owner_id": "ticket", "name": "Ticket Bot", "role": "工单分派员"},
        ],
    )

    assert "Group ops-group set up with 2 agents" in result
    entries = sorted(tool.registry.all(), key=lambda item: item.name)
    assert entries[0].skill_ids == [REQUIRED_EMPLOYEE_SKILL_ID, ids["gmail"]]
    assert entries[1].skill_ids == [REQUIRED_EMPLOYEE_SKILL_ID, ids["jira"]]
    assert len(provider.calls) == 4


@pytest.mark.asyncio
async def test_openhire_register_continues_when_skill_selection_fails(tmp_path: Path) -> None:
    _seed_catalog(tmp_path)
    provider = _SkillSelectionProvider(["not json"] * 8)
    tool = OpenHireTool(
        workspace=tmp_path,
        openhire_config=OpenHireConfig(enabled=True),
        docker_agents_config=DockerAgentsConfig(enabled=False),
        provider=provider,
    )

    result = await tool.execute(
        action="register",
        name="Fallback",
        owner_id="user-fallback",
        role="未知角色",
    )

    assert "Registered: Fallback" in result
    assert "Skill selection warning" in result
    entry = tool.registry.all()[0]
    assert entry.skill_ids == [REQUIRED_EMPLOYEE_SKILL_ID]
    employee_workspace = _employee_workspace(tmp_path, entry.agent_id)
    assert "未知角色" in (employee_workspace / "SOUL.md").read_text(encoding="utf-8")
    assert REQUIRED_EMPLOYEE_SKILL_PROMPT_START in (
        employee_workspace / "AGENTS.md"
    ).read_text(encoding="utf-8")
    assert len(provider.calls) == 8


@pytest.mark.asyncio
async def test_openhire_delegate_uses_employee_container_and_prompt(tmp_path: Path) -> None:
    entry = _seed_employee(tmp_path)
    tool = OpenHireTool(
        workspace=tmp_path,
        openhire_config=OpenHireConfig(enabled=True),
        docker_agents_config=_docker_enabled_config(),
    )
    captured: dict[str, object] = {}

    async def fake_ensure_running(adapter, instance_name, agent_cfg, workspace):
        captured["ensure"] = {
            "agent_name": adapter.agent_name,
            "instance_name": instance_name,
            "container_name": agent_cfg["container_name"],
            "workspace": workspace,
        }
        return agent_cfg["container_name"]

    async def fake_exec(container_name, adapter, task, role, tools, skills, timeout=300, workspace=None):
        captured["exec"] = {
            "container_name": container_name,
            "agent_name": adapter.agent_name,
            "task": task,
            "role": role,
            "tools": tools,
            "skills": skills,
            "timeout": timeout,
            "workspace": workspace,
        }
        return "EXEC_OK"

    with patch("openhire.workforce.tool.ensure_running", fake_ensure_running), patch(
        "openhire.workforce.tool.exec_in_container", fake_exec,
    ):
        result = await tool.execute(action="delegate", name="Nova FE", task="实现登录页")

    assert captured["ensure"] == {
        "agent_name": "nanobot",
        "instance_name": entry.agent_id,
        "container_name": entry.container_name,
        "workspace": _employee_workspace(tmp_path, entry.agent_id),
    }
    assert captured["exec"] == {
        "container_name": entry.container_name,
        "agent_name": "nanobot",
        "task": (
            "Follow the employee system prompt while completing the task.\n\n"
            f"[Employee System Prompt]\n{entry.system_prompt}\n[/Employee System Prompt]\n\n"
            "[Task]\n实现登录页\n[/Task]"
        ),
        "role": entry.role,
        "tools": entry.tools,
        "skills": entry.skills,
        "timeout": 300,
        "workspace": _employee_workspace(tmp_path, entry.agent_id),
    }
    assert entry.name in result
    assert entry.agent_id in result
    assert "EXEC_OK" in result


@pytest.mark.asyncio
async def test_openhire_delegate_sends_employee_outbound_to_current_group(tmp_path: Path) -> None:
    entry = _seed_employee(
        tmp_path,
        name="废人员工",
        tools=["message"],
        group_ids=["oc_group"],
    )
    sent: list[OutboundMessage] = []
    tool = OpenHireTool(
        workspace=tmp_path,
        openhire_config=OpenHireConfig(enabled=True),
        docker_agents_config=_docker_enabled_config(),
        send_callback=lambda msg: sent.append(msg),
    )
    tool.set_context("feishu", "oc_group", "om_parent")

    async def fake_ensure_running(adapter, instance_name, agent_cfg, workspace):
        return agent_cfg["container_name"]

    async def fake_exec(container_name, adapter, task, role, tools, skills, timeout=300, workspace=None):
        assert "OPENHIRE_OUTBOUND_JSON" in task
        return 'thinking\nOPENHIRE_OUTBOUND_JSON: {"content":"我先废为敬"}\ndone'

    with patch("openhire.workforce.tool.ensure_running", fake_ensure_running), patch(
        "openhire.workforce.tool.exec_in_container", fake_exec,
    ):
        result = await tool.execute(action="delegate", agent_id=entry.agent_id, task="开始发癫")

    assert len(sent) == 1
    assert sent[0] == OutboundMessage(
        channel="feishu",
        chat_id="oc_group",
        content="【废人员工】我先废为敬",
        media=[],
        metadata={"message_id": "om_parent"},
    )
    assert tool._sent_in_turn is True
    assert "OPENHIRE_OUTBOUND_JSON" not in result
    assert "Outbound bridge: sent 1 message(s)." in result


@pytest.mark.asyncio
async def test_openhire_delegate_sends_plain_employee_output_to_current_group(tmp_path: Path) -> None:
    entry = _seed_employee(tmp_path, name="废人员工", tools=["message"], group_ids=["oc_group"])
    sent: list[OutboundMessage] = []
    tool = OpenHireTool(
        workspace=tmp_path,
        openhire_config=OpenHireConfig(enabled=True),
        docker_agents_config=_docker_enabled_config(),
        send_callback=lambda msg: sent.append(msg),
    )
    tool.set_context("feishu", "oc_group")

    async def fake_ensure_running(adapter, instance_name, agent_cfg, workspace):
        return agent_cfg["container_name"]

    async def fake_exec(container_name, adapter, task, role, tools, skills, timeout=300, workspace=None):
        assert "final response will be sent" in task
        return "大家好，我来上班了，精神状态还在路上。"

    with patch("openhire.workforce.tool.ensure_running", fake_ensure_running), patch(
        "openhire.workforce.tool.exec_in_container", fake_exec,
    ):
        result = await tool.execute(action="delegate", agent_id=entry.agent_id, task="说一句")

    assert sent[0].content == "【废人员工】大家好，我来上班了，精神状态还在路上。"
    assert tool._sent_in_turn is True
    assert "Outbound bridge: sent 1 message(s)." in result


@pytest.mark.asyncio
async def test_openhire_delegate_cleans_nanobot_banner_before_sending(tmp_path: Path) -> None:
    entry = _seed_employee(tmp_path, name="废人员工", tools=["message"], group_ids=["oc_group"])
    sent: list[OutboundMessage] = []
    tool = OpenHireTool(
        workspace=tmp_path,
        openhire_config=OpenHireConfig(enabled=True),
        docker_agents_config=_docker_enabled_config(),
        send_callback=lambda msg: sent.append(msg),
    )
    tool.set_context("feishu", "oc_group")

    async def fake_ensure_running(adapter, instance_name, agent_cfg, workspace):
        return agent_cfg["container_name"]

    async def fake_exec(container_name, adapter, task, role, tools, skills, timeout=300, workspace=None):
        return "🐈 nanobot\n我已进入工作状态，具体表现为：打开了电脑，也打开了发呆模式。"

    with patch("openhire.workforce.tool.ensure_running", fake_ensure_running), patch(
        "openhire.workforce.tool.exec_in_container", fake_exec,
    ):
        await tool.execute(action="delegate", agent_id=entry.agent_id, task="再说一句")

    assert sent[0].content == "【废人员工】我已进入工作状态，具体表现为：打开了电脑，也打开了发呆模式。"


@pytest.mark.asyncio
async def test_openhire_delegate_falls_back_when_protocol_json_is_split(tmp_path: Path) -> None:
    entry = _seed_employee(tmp_path, name="废人员工", tools=["message"], group_ids=["oc_group"])
    sent: list[OutboundMessage] = []
    tool = OpenHireTool(
        workspace=tmp_path,
        openhire_config=OpenHireConfig(enabled=True),
        docker_agents_config=_docker_enabled_config(),
        send_callback=lambda msg: sent.append(msg),
    )
    tool.set_context("feishu", "oc_group")

    async def fake_ensure_running(adapter, instance_name, agent_cfg, workspace):
        return agent_cfg["container_name"]

    async def fake_exec(container_name, adapter, task, role, tools, skills, timeout=300, workspace=None):
        return '🐈 nanobot\nOPENHIRE_OUTBOUND_JSON:\n{"content":"拆行也要发出去"}'

    with patch("openhire.workforce.tool.ensure_running", fake_ensure_running), patch(
        "openhire.workforce.tool.exec_in_container", fake_exec,
    ):
        result = await tool.execute(action="delegate", agent_id=entry.agent_id, task="说一句")

    assert sent[0].content == "【废人员工】拆行也要发出去"
    assert "invalid JSON" not in result


@pytest.mark.asyncio
async def test_openhire_delegate_rejects_outbound_without_message_tool(tmp_path: Path) -> None:
    entry = _seed_employee(tmp_path, tools=[], group_ids=["oc_group"])
    sent: list[OutboundMessage] = []
    tool = OpenHireTool(
        workspace=tmp_path,
        openhire_config=OpenHireConfig(enabled=True),
        docker_agents_config=_docker_enabled_config(),
        send_callback=lambda msg: sent.append(msg),
    )
    tool.set_context("feishu", "oc_group")

    async def fake_ensure_running(adapter, instance_name, agent_cfg, workspace):
        return agent_cfg["container_name"]

    async def fake_exec(container_name, adapter, task, role, tools, skills, timeout=300, workspace=None):
        return 'OPENHIRE_OUTBOUND_JSON: {"content":"should not send"}'

    with patch("openhire.workforce.tool.ensure_running", fake_ensure_running), patch(
        "openhire.workforce.tool.exec_in_container", fake_exec,
    ):
        result = await tool.execute(action="delegate", agent_id=entry.agent_id, task="发消息")

    assert sent == []
    assert "Outbound bridge error: Agent 'nova-fe' does not have message tool permission." in result


@pytest.mark.asyncio
async def test_openhire_delegate_rejects_outbound_to_group_employee_has_not_joined(tmp_path: Path) -> None:
    entry = _seed_employee(tmp_path, tools=["message"], group_ids=["oc_allowed"])
    sent: list[OutboundMessage] = []
    tool = OpenHireTool(
        workspace=tmp_path,
        openhire_config=OpenHireConfig(enabled=True),
        docker_agents_config=_docker_enabled_config(),
        send_callback=lambda msg: sent.append(msg),
    )
    tool.set_context("feishu", "oc_other")

    async def fake_ensure_running(adapter, instance_name, agent_cfg, workspace):
        return agent_cfg["container_name"]

    async def fake_exec(container_name, adapter, task, role, tools, skills, timeout=300, workspace=None):
        return 'OPENHIRE_OUTBOUND_JSON: {"content":"should not send"}'

    with patch("openhire.workforce.tool.ensure_running", fake_ensure_running), patch(
        "openhire.workforce.tool.exec_in_container", fake_exec,
    ):
        result = await tool.execute(action="delegate", agent_id=entry.agent_id, task="发消息")

    assert sent == []
    assert "Outbound bridge error: Agent 'nova-fe' is not a member of chat 'oc_other'." in result


@pytest.mark.asyncio
async def test_openhire_delegate_rejects_outbound_without_context(tmp_path: Path) -> None:
    entry = _seed_employee(tmp_path, tools=["message"], group_ids=["oc_group"])
    sent: list[OutboundMessage] = []
    tool = OpenHireTool(
        workspace=tmp_path,
        openhire_config=OpenHireConfig(enabled=True),
        docker_agents_config=_docker_enabled_config(),
        send_callback=lambda msg: sent.append(msg),
    )

    async def fake_ensure_running(adapter, instance_name, agent_cfg, workspace):
        return agent_cfg["container_name"]

    async def fake_exec(container_name, adapter, task, role, tools, skills, timeout=300, workspace=None):
        return 'OPENHIRE_OUTBOUND_JSON: {"content":"should not send"}'

    with patch("openhire.workforce.tool.ensure_running", fake_ensure_running), patch(
        "openhire.workforce.tool.exec_in_container", fake_exec,
    ):
        result = await tool.execute(action="delegate", agent_id=entry.agent_id, task="发消息")

    assert sent == []
    assert "Outbound bridge error: No current channel/chat context is available." in result


@pytest.mark.asyncio
async def test_agent_loop_suppresses_final_reply_when_openhire_employee_sent_to_group(
    tmp_path: Path,
) -> None:
    entry = _seed_employee(tmp_path, tools=["message"], group_ids=["oc_group"])
    loop = AgentLoop(
        bus=MessageBus(),
        provider=_make_provider(),
        workspace=tmp_path,
        model="test-model",
        context_window_tokens=AgentDefaults().context_window_tokens,
        openhire_config=OpenHireConfig(enabled=True),
        docker_agents_config=_docker_enabled_config(),
    )
    calls = iter([
        LLMResponse(
            content="",
            tool_calls=[
                ToolCallRequest(
                    id="call_openhire",
                    name="openhire",
                    arguments={"action": "delegate", "agent_id": entry.agent_id, "task": "发一条开场白"},
                )
            ],
        ),
        LLMResponse(content="已让废人员工发言。", tool_calls=[]),
    ])
    loop.provider.chat_with_retry = AsyncMock(side_effect=lambda *a, **kw: next(calls))

    async def fake_ensure_running(adapter, instance_name, agent_cfg, workspace):
        return agent_cfg["container_name"]

    async def fake_exec(container_name, adapter, task, role, tools, skills, timeout=300, workspace=None):
        return 'OPENHIRE_OUTBOUND_JSON: {"content":"开摆"}'

    with patch("openhire.workforce.tool.ensure_running", fake_ensure_running), patch(
        "openhire.workforce.tool.exec_in_container", fake_exec,
    ):
        result = await loop._process_message(
            InboundMessage(
                channel="feishu",
                sender_id="user",
                chat_id="oc_group",
                content="让废人员工发言",
                metadata={"message_id": "om_parent"},
            )
        )

    assert result is None
    sent = await loop.bus.consume_outbound()
    while sent.metadata.get("_tool_hint") or sent.metadata.get("_progress"):
        sent = await loop.bus.consume_outbound()
    assert sent.content == "【Nova FE】开摆"
    assert sent.channel == "feishu"
    assert sent.chat_id == "oc_group"
