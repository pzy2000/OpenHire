from __future__ import annotations

import asyncio
import json
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import patch

import pytest

try:
    from openhire.channels import feishu

    FEISHU_AVAILABLE = getattr(feishu, "FEISHU_AVAILABLE", False)
except ImportError:
    FEISHU_AVAILABLE = False

if not FEISHU_AVAILABLE:
    pytest.skip("Feishu dependencies not installed (lark-oapi)", allow_module_level=True)

from openhire.agent.loop import AgentLoop
from openhire.bus.queue import MessageBus
from openhire.channels.feishu import FeishuChannel, FeishuConfig
from openhire.config.schema import AgentDefaults, DockerAgentConfig, DockerAgentsConfig, OpenHireConfig
from openhire.providers.base import GenerationSettings, LLMProvider, LLMResponse, ToolCallRequest
from openhire.workforce.registry import AgentEntry, AgentRegistry
from openhire.workforce.store import OpenHireStore
from openhire.workforce.workspace import employee_workspace_path


def _seed_atlas_algo(workspace: Path) -> AgentEntry:
    registry = AgentRegistry(OpenHireStore(workspace))
    return registry.register(AgentEntry(
        agent_id="atlas-algo",
        name="Atlas Algo",
        role="Algorithm Engineer / 算法工程师",
        agent_type="nanobot",
        skills=["Skill Creator"],
        system_prompt="你是算法工程师数字员工，负责设计与实现复杂 AI 能力。",
        status="active",
        container_name="openhire-atlas-algo",
    ))


def _make_feishu_channel(bus: MessageBus) -> FeishuChannel:
    channel = FeishuChannel(
        FeishuConfig(
            enabled=True,
            app_id="app",
            app_secret="secret",
            allow_from=["*"],
            group_policy="open",
            streaming=False,
        ),
        bus,
    )
    channel._client = object()
    return channel


def _make_feishu_event(index: int) -> SimpleNamespace:
    message = SimpleNamespace(
        message_id=f"om_delegate_{index}",
        chat_id="oc_delegate_chat",
        chat_type="group",
        message_type="text",
        content=json.dumps(
            {"text": "请让Atlas Algo写一个自动玩狼人杀的skill@pzy_claw (ou_74170c8d2b3d93f2f0d2118334c9bf39)"}
        ),
        parent_id=None,
        root_id=None,
        thread_id=None,
        mentions=[],
    )
    sender = SimpleNamespace(
        sender_type="user",
        sender_id=SimpleNamespace(open_id="ou_runtime_user"),
    )
    return SimpleNamespace(event=SimpleNamespace(message=message, sender=sender))


_OPC_PROMPT = "请创建一个一人公司OPC，组建一个完整的团队，用来进行电商业务，全自动运行"


def _opc_team_members(owner_id: str) -> list[dict[str, object]]:
    tools = ["web_search", "web_fetch", "read_file", "write_file", "edit_file", "message"]
    return [
        {
            "owner_id": owner_id,
            "name": "一人公司OPC",
            "role": "电商业务全自动运营总控，负责目标拆解、团队编排、跨岗位协同、异常升级与经营复盘。",
            "skills": ["ecommerce", "operations", "automation", "analysis", "coordination"],
            "tools": [
                "web_search",
                "web_fetch",
                "exec",
                "read_file",
                "write_file",
                "edit_file",
                "glob",
                "grep",
                "openhire",
                "cron",
                "message",
            ],
        },
        {
            "owner_id": owner_id,
            "name": "品牌与战略负责人",
            "role": "负责品牌定位、经营目标制定、类目策略、竞争分析和中长期增长规划。",
            "skills": ["strategy", "branding", "market-research", "business-planning"],
            "tools": tools,
        },
        {
            "owner_id": owner_id,
            "name": "选品与采购经理",
            "role": "负责市场机会挖掘、选品评估、供应商开发、打样、采购与成本谈判。",
            "skills": ["product-sourcing", "vendor-management", "pricing", "negotiation"],
            "tools": tools,
        },
        {
            "owner_id": owner_id,
            "name": "供应链与库存经理",
            "role": "负责生产排期、补货计划、库存周转、物流协调和缺货预警。",
            "skills": ["supply-chain", "inventory", "forecasting", "logistics"],
            "tools": ["read_file", "write_file", "edit_file", "grep", "message", "cron"],
        },
        {
            "owner_id": owner_id,
            "name": "店铺运营经理",
            "role": "负责店铺日常运营、活动提报、商品上下架、页面优化和平台规则执行。",
            "skills": ["store-operations", "marketplace-rules", "campaigns", "merchandising"],
            "tools": [*tools, "cron"],
        },
        {
            "owner_id": owner_id,
            "name": "内容与设计主管",
            "role": "负责商品详情页、主图、短视频脚本、直播素材和品牌视觉一致性。",
            "skills": ["copywriting", "creative-direction", "visual-design", "content-production"],
            "tools": tools,
        },
        {
            "owner_id": owner_id,
            "name": "广告投放优化师",
            "role": "负责站内外广告投放、预算分配、创意测试、ROI优化和流量增长。",
            "skills": ["performance-marketing", "ads-optimization", "attribution", "growth"],
            "tools": tools,
        },
        {
            "owner_id": owner_id,
            "name": "数据分析师",
            "role": "负责经营看板、转化漏斗、利润分析、归因分析和异常监控。",
            "skills": ["analytics", "reporting", "sql-thinking", "forecasting"],
            "tools": ["read_file", "write_file", "edit_file", "grep", "exec", "message", "cron"],
        },
        {
            "owner_id": owner_id,
            "name": "客服与售后主管",
            "role": "负责售前咨询、售后处理、评价管理、退款纠纷和用户声音汇总。",
            "skills": ["customer-support", "after-sales", "review-management", "crm"],
            "tools": ["read_file", "write_file", "edit_file", "message", "cron"],
        },
        {
            "owner_id": owner_id,
            "name": "财务与风控经理",
            "role": "负责利润核算、现金流管理、预算控制、税务配合和风险预警。",
            "skills": ["finance", "cashflow", "risk-control", "budgeting"],
            "tools": ["read_file", "write_file", "edit_file", "grep", "message", "cron"],
        },
        {
            "owner_id": owner_id,
            "name": "自动化与系统工程师",
            "role": "负责搭建自动化流程、数据同步、任务编排、告警机制与系统集成。",
            "skills": ["automation", "integrations", "scripting", "monitoring"],
            "tools": ["exec", "read_file", "write_file", "edit_file", "glob", "grep", "cron", "message", "openhire"],
        },
    ]


def _make_opc_feishu_event(index: int, chat_id: str) -> SimpleNamespace:
    message = SimpleNamespace(
        message_id=f"om_opc_team_{index}",
        chat_id=chat_id,
        chat_type="group",
        message_type="text",
        content=json.dumps({"text": _OPC_PROMPT}, ensure_ascii=False),
        parent_id=None,
        root_id=None,
        thread_id=None,
        mentions=[],
    )
    sender = SimpleNamespace(
        sender_type="user",
        sender_id=SimpleNamespace(open_id="ou_runtime_user"),
    )
    return SimpleNamespace(event=SimpleNamespace(message=message, sender=sender))


class _DelegateProvider(LLMProvider):
    def __init__(self) -> None:
        super().__init__(api_key="dummy", api_base="http://dummy")
        self.generation = GenerationSettings()

    def get_default_model(self) -> str:
        return "test-model"

    async def chat(self, *args, **kwargs) -> LLMResponse:
        raise NotImplementedError

    async def chat_with_retry(self, *, messages, tools=None, **kwargs) -> LLMResponse:
        history = [msg for msg in messages if msg.get("role") != "system"]
        last = history[-1]
        if last.get("role") == "user":
            return LLMResponse(
                content="",
                tool_calls=[ToolCallRequest(
                    id="call_delegate",
                    name="openhire",
                    arguments={
                        "action": "delegate",
                        "name": "Atlas Algo",
                        "task": "请设计一个自动玩狼人杀的 skill",
                        "timeout": 900,
                    },
                )],
                usage={},
            )

        assert last.get("role") == "tool"
        return LLMResponse(
            content=f"Atlas Algo 结果：\n{last['content']}",
            tool_calls=[],
            usage={},
        )


class _OPCTeamProvider(LLMProvider):
    def __init__(self, owner_id: str) -> None:
        super().__init__(api_key="dummy", api_base="http://dummy")
        self.generation = GenerationSettings()
        self.owner_id = owner_id

    def get_default_model(self) -> str:
        return "test-model"

    async def chat(self, *args, **kwargs) -> LLMResponse:
        raise NotImplementedError

    async def chat_with_retry(self, *, messages, tools=None, **kwargs) -> LLMResponse:
        history = [msg for msg in messages if msg.get("role") != "system"]
        last = history[-1]
        if last.get("role") == "user":
            assert _OPC_PROMPT in str(last.get("content") or "")
            return LLMResponse(
                content="",
                tool_calls=[
                    ToolCallRequest(
                        id="call_register_opc",
                        name="openhire",
                        arguments={
                            "action": "register",
                            "owner_id": self.owner_id,
                            "name": "一人公司OPC",
                            "role": (
                                "电商业务全自动运营总控，负责目标拆解、团队编排、跨岗位协同、"
                                "异常升级与经营复盘。面向中国电商场景，统筹选品、供应链、内容、"
                                "投放、客服、财务与数据分析。"
                            ),
                            "agent_type": "nanobot",
                            "skills": ["ecommerce", "operations", "automation", "analysis", "coordination"],
                            "tools": [
                                "web_search",
                                "web_fetch",
                                "exec",
                                "read_file",
                                "write_file",
                                "edit_file",
                                "glob",
                                "grep",
                                "openhire",
                                "cron",
                                "message",
                            ],
                        },
                    )
                ],
                usage={},
            )

        assert last.get("role") == "tool"
        content = str(last.get("content") or "")
        if content.startswith("Registered: 一人公司OPC"):
            return LLMResponse(
                content="",
                tool_calls=[
                    ToolCallRequest(
                        id="call_setup_opc_team",
                        name="openhire",
                        arguments={
                            "action": "setup_group",
                            "group_id": self.owner_id,
                            "members": _opc_team_members(self.owner_id),
                        },
                    )
                ],
                usage={},
            )
        assert content.startswith(f"Group {self.owner_id} set up with 11 agents:")
        return LLMResponse(content=f"已创建完成。\n{content}", tool_calls=[], usage={})


async def _run_opc_team_feishu_trial(tmp_path: Path, index: int) -> None:
    workspace = tmp_path / f"opc-trial-{index}"
    chat_id = f"oc_opc_team_{index}"
    bus = MessageBus()
    channel = _make_feishu_channel(bus)
    loop = AgentLoop(
        bus=bus,
        provider=_OPCTeamProvider(owner_id=chat_id),
        workspace=workspace,
        model="test-model",
        context_window_tokens=AgentDefaults().context_window_tokens,
        docker_agents_config=DockerAgentsConfig(
            enabled=True,
            agents={
                "nanobot": DockerAgentConfig(enabled=True, persistent=True),
                "openclaw": DockerAgentConfig(enabled=True, persistent=True),
            },
        ),
        openhire_config=OpenHireConfig(enabled=True),
    )
    ensure_calls: list[tuple[str, str, str, Path]] = []

    async def fake_add_reaction(*_args, **_kwargs):
        return None

    async def fake_ensure_running(adapter, instance_name, agent_cfg, workspace):
        ensure_calls.append((
            adapter.agent_name,
            instance_name,
            agent_cfg["container_name"],
            workspace,
        ))
        return agent_cfg["container_name"]

    runner = asyncio.create_task(loop.run())
    try:
        with (
            patch.object(channel, "_add_reaction", fake_add_reaction),
            patch("openhire.workforce.lifecycle.ensure_running", fake_ensure_running),
        ):
            await channel._on_message(_make_opc_feishu_event(index, chat_id))
            while True:
                outbound = await asyncio.wait_for(bus.consume_outbound(), timeout=5)
                if not outbound.metadata.get("_progress"):
                    break

        assert outbound.channel == "feishu"
        assert outbound.chat_id == chat_id
        assert "已创建完成" in outbound.content

        registry = AgentRegistry(OpenHireStore(workspace))
        all_agents = registry.all()
        roster = registry.get_group_roster(chat_id)
        assert len(all_agents) == 11
        assert len(roster) == 11
        assert len({agent.agent_id for agent in roster}) == 11
        assert {agent.name for agent in roster} == {str(member["name"]) for member in _opc_team_members(chat_id)}
        assert len(ensure_calls) == 11
        assert len({instance_name for _agent, instance_name, _container, _workspace in ensure_calls}) == 11
    finally:
        loop.stop()
        runner.cancel()
        with pytest.raises(asyncio.CancelledError):
            await runner


@pytest.mark.asyncio
async def test_feishu_opc_team_creation_prompt_repeats_five_times(tmp_path: Path) -> None:
    for index in range(5):
        await _run_opc_team_feishu_trial(tmp_path, index)


@pytest.mark.asyncio
async def test_feishu_openhire_delegate_nanobot_e2e_repeats_five_times(tmp_path: Path) -> None:
    employee = _seed_atlas_algo(tmp_path)
    bus = MessageBus()
    channel = _make_feishu_channel(bus)
    loop = AgentLoop(
        bus=bus,
        provider=_DelegateProvider(),
        workspace=tmp_path,
        model="test-model",
        context_window_tokens=AgentDefaults().context_window_tokens,
        docker_agents_config=DockerAgentsConfig(
            enabled=True,
            agents={"nanobot": DockerAgentConfig(enabled=True, persistent=True)},
        ),
        openhire_config=OpenHireConfig(enabled=True),
    )

    sent_messages: list[str] = []
    outbound_contents: list[str] = []

    async def fake_add_reaction(*_args, **_kwargs):
        return None

    def fake_send_message_sync(receive_id_type: str, receive_id: str, msg_type: str, content: str) -> None:
        payload = json.loads(content)
        if msg_type == "text":
            sent_messages.append(payload["text"])
            return
        sent_messages.append(json.dumps(payload, ensure_ascii=False))

    async def fake_ensure_running(adapter, instance_name, agent_cfg, workspace):
        assert adapter.agent_name == "nanobot"
        assert instance_name == employee.agent_id
        assert agent_cfg["container_name"] == employee.container_name
        assert workspace == employee_workspace_path(tmp_path, employee)
        return employee.container_name

    async def fake_exec_in_container(
        container_name,
        adapter,
        task,
        role,
        tools,
        skills,
        timeout=300,
        workspace=None,
    ):
        assert workspace == employee_workspace_path(tmp_path, employee)
        command = adapter.build_command(
            task, role, tools, skills, instance_id=container_name,
        )
        if command[:3] != ["nanobot", "agent", "--session"] or "--message" not in command:
            return (
                "OCI runtime exec failed: exec failed: unable to start container process: "
                f"exec: \"{command[0]}\": executable file not found in $PATH"
            )
        return f"OK container={container_name} command={' '.join(command[:7])}"

    runner = asyncio.create_task(loop.run())
    try:
        with (
            patch.object(channel, "_add_reaction", fake_add_reaction),
            patch.object(channel, "_send_message_sync", fake_send_message_sync),
            patch("openhire.workforce.tool.ensure_running", fake_ensure_running),
            patch("openhire.workforce.tool.exec_in_container", fake_exec_in_container),
            ):
                for index in range(5):
                    await channel._on_message(_make_feishu_event(index))
                    while True:
                        outbound = await asyncio.wait_for(bus.consume_outbound(), timeout=2)
                        if not outbound.metadata.get("_progress"):
                            break
                    assert outbound.channel == "feishu"
                    assert outbound.chat_id == "oc_delegate_chat"
                    outbound_contents.append(outbound.content)
                    await channel.send(outbound)

        assert len(sent_messages) == 5
        assert len(outbound_contents) == 5
        assert all("Atlas Algo 结果：" in item for item in outbound_contents)
        assert all(
            "OK container=openhire-atlas-algo command=nanobot agent --session" in item
            and "--message" in item
            for item in outbound_contents
        )
    finally:
        loop.stop()
        runner.cancel()
        with pytest.raises(asyncio.CancelledError):
            await runner
