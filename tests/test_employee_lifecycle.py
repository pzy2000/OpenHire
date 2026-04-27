from __future__ import annotations

import asyncio

import pytest

from openhire.config.schema import DockerAgentConfig, DockerAgentsConfig
from openhire.providers.base import LLMResponse
from openhire.workforce.lifecycle import AgentLifecycle
from openhire.workforce.required_skill import (
    REQUIRED_EMPLOYEE_SKILL_ID,
    REQUIRED_EMPLOYEE_SKILL_NAME,
    REQUIRED_EMPLOYEE_SKILL_PROMPT_START,
    build_required_employee_skill_prompt_block,
)
from openhire.workforce.registry import AgentEntry, AgentRegistry
from openhire.workforce.store import OpenHireStore


def _employee_workspace(workspace, agent_id: str):
    return workspace / "openhire" / "employees" / agent_id / "workspace"


def _docker_config() -> DockerAgentsConfig:
    return DockerAgentsConfig(
        enabled=True,
        agents={"nanobot": DockerAgentConfig(enabled=True, persistent=True)},
    )


class _PromptSplitProvider:
    def __init__(self, responses: list[str]) -> None:
        self.responses = list(responses)
        self.calls: list[dict] = []

    async def chat_with_retry(self, **kwargs) -> LLMResponse:
        self.calls.append(kwargs)
        return LLMResponse(content=self.responses.pop(0), tool_calls=[], usage={})


@pytest.mark.asyncio
async def test_create_agent_splits_employee_bootstrap_prompts(tmp_path) -> None:
    registry = AgentRegistry(OpenHireStore(tmp_path))
    provider = _PromptSplitProvider([
        '{"soul":"用直接、工程化的语气处理前端任务。","agents":"负责前端实现、性能优化和端到端验证。"}'
    ])
    lifecycle = AgentLifecycle(registry, tmp_path, llm_provider=provider)

    entry = await lifecycle.create_agent(
        name="Nova FE",
        role="前端工程师",
        skills=["react"],
        system_prompt="你负责前端。",
        agent_type="nanobot",
    )

    assert entry.skill_ids == [REQUIRED_EMPLOYEE_SKILL_ID]
    assert entry.skills == [REQUIRED_EMPLOYEE_SKILL_NAME, "react"]
    assert entry.system_prompt.startswith("你负责前端。")
    assert REQUIRED_EMPLOYEE_SKILL_PROMPT_START in entry.system_prompt
    assert entry.system_prompt.count(REQUIRED_EMPLOYEE_SKILL_PROMPT_START) == 1

    employee_workspace = _employee_workspace(tmp_path, entry.agent_id)
    soul = (employee_workspace / "SOUL.md").read_text(encoding="utf-8")
    agents = (employee_workspace / "AGENTS.md").read_text(encoding="utf-8")
    assert soul.startswith("# Soul")
    assert agents.startswith("# Agent Instructions")
    assert "用直接、工程化的语气处理前端任务。" in soul
    assert "负责前端实现、性能优化和端到端验证。" in agents
    assert REQUIRED_EMPLOYEE_SKILL_PROMPT_START not in soul
    assert REQUIRED_EMPLOYEE_SKILL_PROMPT_START in agents
    assert len(provider.calls) == 1
    assert (employee_workspace / "TOOLS.md").exists()
    assert (employee_workspace / "USER.md").read_text(encoding="utf-8") == ""
    assert (employee_workspace / "HEARTBEAT.md").read_text(encoding="utf-8") == ""


@pytest.mark.asyncio
async def test_create_agent_preserves_container_runtime_templates_before_openhire_blocks(
    tmp_path,
    monkeypatch,
) -> None:
    registry = AgentRegistry(OpenHireStore(tmp_path))
    provider = _PromptSplitProvider([
        '{"soul":"Nova keeps replies crisp.","agents":"Nova checks UI regressions before handoff."}'
    ])

    async def fake_ensure_running(adapter, instance_name, agent_cfg, workspace):
        assert adapter.agent_name == "nanobot"
        assert workspace == _employee_workspace(tmp_path, instance_name)
        return agent_cfg["container_name"]

    async def fake_read_container_bootstrap_file(container_name, adapter, filename):
        assert container_name.startswith("openhire-")
        assert adapter.agent_name == "nanobot"
        return {
            "SOUL.md": "# Runtime Soul\nI am nanobot from the image.",
            "AGENTS.md": "# Runtime Agents\nUse the image runbook.",
        }[filename]

    monkeypatch.setattr("openhire.workforce.lifecycle.ensure_running", fake_ensure_running)
    monkeypatch.setattr(
        "openhire.workforce.lifecycle.read_container_bootstrap_file",
        fake_read_container_bootstrap_file,
    )

    lifecycle = AgentLifecycle(
        registry,
        tmp_path,
        docker_agents_config=_docker_config(),
        llm_provider=provider,
    )
    entry = await lifecycle.create_agent(
        name="Nova FE",
        role="前端工程师",
        system_prompt="你负责前端。",
        agent_type="nanobot",
    )

    employee_workspace = _employee_workspace(tmp_path, entry.agent_id)
    soul = (employee_workspace / "SOUL.md").read_text(encoding="utf-8")
    agents = (employee_workspace / "AGENTS.md").read_text(encoding="utf-8")
    assert soul.startswith("# Runtime Soul\nI am nanobot from the image.")
    assert agents.startswith("# Runtime Agents\nUse the image runbook.")
    assert "Nova keeps replies crisp." in soul
    assert "Nova checks UI regressions before handoff." in agents


@pytest.mark.asyncio
async def test_create_agent_invokes_prompt_splitter_only_after_container_creation(
    tmp_path,
    monkeypatch,
) -> None:
    registry = AgentRegistry(OpenHireStore(tmp_path))
    provider = _PromptSplitProvider([
        '{"soul":"should not be used","agents":"should not be used"}'
    ])

    async def fake_ensure_running(*_args, **_kwargs):
        raise RuntimeError("docker create failed")

    monkeypatch.setattr("openhire.workforce.lifecycle.ensure_running", fake_ensure_running)

    lifecycle = AgentLifecycle(
        registry,
        tmp_path,
        docker_agents_config=_docker_config(),
        llm_provider=provider,
    )
    with pytest.raises(RuntimeError, match="docker create failed"):
        await lifecycle.create_agent(
            name="Nova FE",
            role="前端工程师",
            system_prompt="你负责前端。",
            agent_type="nanobot",
        )

    assert provider.calls == []


@pytest.mark.asyncio
async def test_create_agent_retries_prompt_split_then_uses_deterministic_fallback(
    tmp_path,
    monkeypatch,
) -> None:
    registry = AgentRegistry(OpenHireStore(tmp_path))
    provider = _PromptSplitProvider(["not json", '{"soul":""}', '{"agents":""}'])
    warnings: list[str] = []

    def fake_warning(message, *args):
        warnings.append(message.format(*args))

    monkeypatch.setattr("openhire.workforce.employee_prompt.logger.warning", fake_warning)

    lifecycle = AgentLifecycle(registry, tmp_path, llm_provider=provider)
    entry = await lifecycle.create_agent(
        name="API Owner",
        role="后端工程师",
        skills=["python"],
        system_prompt="你负责后端 API。",
        agent_type="nanobot",
    )

    employee_workspace = _employee_workspace(tmp_path, entry.agent_id)
    soul = (employee_workspace / "SOUL.md").read_text(encoding="utf-8")
    agents = (employee_workspace / "AGENTS.md").read_text(encoding="utf-8")
    assert len(provider.calls) == 3
    assert "你负责后端 API。" in soul
    assert REQUIRED_EMPLOYEE_SKILL_PROMPT_START not in soul
    assert REQUIRED_EMPLOYEE_SKILL_PROMPT_START in agents
    assert any("deterministic fallback" in warning for warning in warnings)


@pytest.mark.asyncio
async def test_create_agent_with_bootstrap_files_skips_prompt_split_and_runtime_templates(
    tmp_path,
    monkeypatch,
) -> None:
    registry = AgentRegistry(OpenHireStore(tmp_path))
    provider = _PromptSplitProvider([
        '{"soul":"should not be used","agents":"should not be used"}'
    ])
    required_block = build_required_employee_skill_prompt_block()
    read_calls: list[tuple[str, str]] = []

    async def fake_ensure_running(adapter, instance_name, agent_cfg, workspace):
        assert adapter.agent_name == "nanobot"
        assert workspace == _employee_workspace(tmp_path, instance_name)
        return agent_cfg["container_name"]

    async def fake_read_container_bootstrap_file(container_name, adapter, filename):
        read_calls.append((container_name, filename))
        return "should not be read"

    monkeypatch.setattr("openhire.workforce.lifecycle.ensure_running", fake_ensure_running)
    monkeypatch.setattr(
        "openhire.workforce.lifecycle.read_container_bootstrap_file",
        fake_read_container_bootstrap_file,
    )

    lifecycle = AgentLifecycle(
        registry,
        tmp_path,
        docker_agents_config=_docker_config(),
        llm_provider=provider,
    )
    entry = await lifecycle.create_agent(
        name="Case PM",
        role="产品总监",
        system_prompt="你负责产品推进。",
        agent_type="nanobot",
        bootstrap_files={
            "SOUL.md": f"Case soul\n\n{required_block}",
            "AGENTS.md": "Case agents",
            "HEARTBEAT.md": "Heartbeat",
            "TOOLS.md": "Tools",
            "USER.md": "User",
        },
    )

    employee_workspace = _employee_workspace(tmp_path, entry.agent_id)
    soul = (employee_workspace / "SOUL.md").read_text(encoding="utf-8")
    agents = (employee_workspace / "AGENTS.md").read_text(encoding="utf-8")
    assert provider.calls == []
    assert read_calls == []
    assert soul == "Case soul"
    assert REQUIRED_EMPLOYEE_SKILL_PROMPT_START not in soul
    assert agents.startswith("Case agents")
    assert REQUIRED_EMPLOYEE_SKILL_PROMPT_START in agents
    assert agents.count(REQUIRED_EMPLOYEE_SKILL_PROMPT_START) == 1
    assert (employee_workspace / "HEARTBEAT.md").read_text(encoding="utf-8") == "Heartbeat"
    assert (employee_workspace / "TOOLS.md").read_text(encoding="utf-8") == "Tools"
    assert (employee_workspace / "USER.md").read_text(encoding="utf-8") == "User"


@pytest.mark.asyncio
async def test_create_agent_with_partial_bootstrap_files_falls_back_to_defaults(tmp_path) -> None:
    registry = AgentRegistry(OpenHireStore(tmp_path))
    provider = _PromptSplitProvider([
        '{"soul":"should not be used","agents":"should not be used"}'
    ])

    lifecycle = AgentLifecycle(registry, tmp_path, llm_provider=provider)
    entry = await lifecycle.create_agent(
        name="Case PM",
        role="产品总监",
        system_prompt="你负责产品推进。",
        agent_type="nanobot",
        bootstrap_files={
            "SOUL.md": "Case soul only",
        },
    )

    employee_workspace = _employee_workspace(tmp_path, entry.agent_id)
    assert provider.calls == []
    assert (employee_workspace / "SOUL.md").read_text(encoding="utf-8") == "Case soul only"
    assert (employee_workspace / "AGENTS.md").read_text(encoding="utf-8").startswith("# Agent Instructions")
    assert REQUIRED_EMPLOYEE_SKILL_PROMPT_START not in (employee_workspace / "SOUL.md").read_text(encoding="utf-8")
    assert REQUIRED_EMPLOYEE_SKILL_PROMPT_START in (employee_workspace / "AGENTS.md").read_text(encoding="utf-8")
    assert (employee_workspace / "TOOLS.md").read_text(encoding="utf-8").startswith("# Tool Usage Notes")
    assert (employee_workspace / "USER.md").read_text(encoding="utf-8") == ""
    assert (employee_workspace / "HEARTBEAT.md").read_text(encoding="utf-8") == ""


@pytest.mark.asyncio
async def test_restore_active_agents_only_restores_active_entries(tmp_path, monkeypatch) -> None:
    registry = AgentRegistry(OpenHireStore(tmp_path))
    active = registry.register(AgentEntry(name="Active", agent_type="nanobot", status="active"))
    registry.register(AgentEntry(name="Suspended", agent_type="nanobot", status="suspended"))
    registry.register(AgentEntry(name="Archived", agent_type="nanobot", status="archived"))
    calls: list[str] = []

    async def fake_ensure_running(adapter, instance_name, agent_cfg, workspace):
        calls.append(instance_name)
        assert adapter.agent_name == "nanobot"
        assert workspace == _employee_workspace(tmp_path, instance_name)
        return agent_cfg["container_name"]

    monkeypatch.setattr("openhire.workforce.lifecycle.ensure_running", fake_ensure_running)

    lifecycle = AgentLifecycle(registry, tmp_path, docker_agents_config=_docker_config())
    stats = await lifecycle.restore_active_agents()

    assert calls == [active.agent_id]
    assert stats == {"restored": 1, "failed": 0, "skipped": 2}


@pytest.mark.asyncio
async def test_restore_active_agents_continues_after_failure(tmp_path, monkeypatch) -> None:
    registry = AgentRegistry(OpenHireStore(tmp_path))
    broken = registry.register(AgentEntry(name="Broken", agent_type="nanobot", status="active"))
    healthy = registry.register(AgentEntry(name="Healthy", agent_type="nanobot", status="active"))
    calls: list[str] = []

    async def fake_ensure_running(adapter, instance_name, agent_cfg, workspace):
        calls.append(instance_name)
        assert adapter.agent_name == "nanobot"
        assert workspace == _employee_workspace(tmp_path, instance_name)
        if instance_name == broken.agent_id:
            raise RuntimeError("docker start failed")
        return agent_cfg["container_name"]

    monkeypatch.setattr("openhire.workforce.lifecycle.ensure_running", fake_ensure_running)

    lifecycle = AgentLifecycle(registry, tmp_path, docker_agents_config=_docker_config())
    stats = await lifecycle.restore_active_agents()

    assert set(calls) == {broken.agent_id, healthy.agent_id}
    assert stats == {"restored": 1, "failed": 1, "skipped": 0}


@pytest.mark.asyncio
async def test_restore_active_agents_skips_when_docker_agents_disabled(tmp_path, monkeypatch) -> None:
    registry = AgentRegistry(OpenHireStore(tmp_path))
    registry.register(AgentEntry(name="Active", agent_type="nanobot", status="active"))
    calls: list[str] = []

    async def fake_ensure_running(*_args, **_kwargs):
        calls.append("called")
        return "container"

    monkeypatch.setattr("openhire.workforce.lifecycle.ensure_running", fake_ensure_running)

    lifecycle = AgentLifecycle(
        registry,
        tmp_path,
        docker_agents_config=DockerAgentsConfig(enabled=False),
    )
    stats = await lifecycle.restore_active_agents()

    assert calls == []
    assert stats == {"restored": 0, "failed": 0, "skipped": 1}


@pytest.mark.asyncio
async def test_setup_group_allows_same_owner_to_create_distinct_role_employees(tmp_path) -> None:
    registry = AgentRegistry(OpenHireStore(tmp_path))
    owner_id = "oc_opc_chat"
    existing = registry.register(
        AgentEntry(
            name="一人公司OPC",
            owner_id=owner_id,
            role="电商业务全自动运营总控，负责目标拆解、团队编排、跨岗位协同、异常升级与经营复盘。",
            agent_type="nanobot",
            skills=["ecommerce", "coordination"],
            status="active",
        )
    )
    lifecycle = AgentLifecycle(registry, tmp_path)

    results = await lifecycle.setup_group(
        owner_id,
        [
            {
                "owner_id": owner_id,
                "name": "一人公司OPC",
                "role": "电商业务全自动运营总控",
                "skills": ["ecommerce", "coordination"],
                "agent_type": "nanobot",
            },
            {
                "owner_id": owner_id,
                "name": "品牌与战略负责人",
                "role": "负责品牌定位、经营目标制定、类目策略、竞争分析和中长期增长规划。",
                "skills": ["strategy", "branding"],
                "agent_type": "nanobot",
            },
            {
                "owner_id": owner_id,
                "name": "选品与采购经理",
                "role": "负责市场机会挖掘、选品评估、供应商开发、打样、采购与成本谈判。",
                "skills": ["product-sourcing", "vendor-management"],
                "agent_type": "nanobot",
            },
        ],
    )

    assert len(results) == 3
    assert results[0].agent_id == existing.agent_id
    assert len({entry.agent_id for entry in results}) == 3
    assert results[1].skill_ids == [REQUIRED_EMPLOYEE_SKILL_ID]
    assert results[1].skills[0] == REQUIRED_EMPLOYEE_SKILL_NAME
    assert REQUIRED_EMPLOYEE_SKILL_PROMPT_START in results[1].system_prompt
    assert {entry.name for entry in registry.get_group_roster(owner_id)} == {
        "一人公司OPC",
        "品牌与战略负责人",
        "选品与采购经理",
    }
    assert len(registry.all()) == 3


@pytest.mark.asyncio
async def test_setup_group_creates_missing_docker_employees_in_parallel(tmp_path, monkeypatch) -> None:
    registry = AgentRegistry(OpenHireStore(tmp_path))
    all_started = asyncio.Event()
    started: list[str] = []

    async def fake_ensure_running(adapter, instance_name, agent_cfg, workspace):
        assert adapter.agent_name == "nanobot"
        assert workspace == _employee_workspace(tmp_path, instance_name)
        started.append(instance_name)
        if len(started) == 3:
            all_started.set()
        await asyncio.wait_for(all_started.wait(), timeout=1)
        return agent_cfg["container_name"]

    monkeypatch.setattr("openhire.workforce.lifecycle.ensure_running", fake_ensure_running)

    lifecycle = AgentLifecycle(registry, tmp_path, docker_agents_config=_docker_config())
    results = await lifecycle.setup_group(
        "oc_launch",
        [
            {"owner_id": "ou_company", "name": "品牌负责人", "role": "品牌策略", "agent_type": "nanobot"},
            {"owner_id": "ou_company", "name": "选品经理", "role": "选品采购", "agent_type": "nanobot"},
            {"owner_id": "ou_company", "name": "投放优化师", "role": "广告投放", "agent_type": "nanobot"},
        ],
    )

    assert [entry.name for entry in results] == ["品牌负责人", "选品经理", "投放优化师"]
    assert len(started) == 3
    assert len(registry.all()) == 3


@pytest.mark.asyncio
async def test_setup_group_keeps_successful_parallel_creations_when_one_fails(
    tmp_path,
    monkeypatch,
) -> None:
    registry = AgentRegistry(OpenHireStore(tmp_path))
    completed: list[str] = []

    async def fake_ensure_running(adapter, instance_name, agent_cfg, workspace):
        assert adapter.agent_name == "nanobot"
        assert workspace == _employee_workspace(tmp_path, instance_name)
        entry = registry.get(instance_name)
        assert entry is not None
        await asyncio.sleep(0)
        if entry.name == "Broken":
            raise RuntimeError("docker start failed")
        completed.append(entry.name)
        return agent_cfg["container_name"]

    monkeypatch.setattr("openhire.workforce.lifecycle.ensure_running", fake_ensure_running)

    lifecycle = AgentLifecycle(registry, tmp_path, docker_agents_config=_docker_config())
    with pytest.raises(RuntimeError, match="docker start failed"):
        await lifecycle.setup_group(
            "oc_launch",
            [
                {"owner_id": "ou_company", "name": "Broken", "role": "坏容器", "agent_type": "nanobot"},
                {"owner_id": "ou_company", "name": "Healthy", "role": "正常容器", "agent_type": "nanobot"},
            ],
        )

    assert completed == ["Healthy"]
    assert [entry.name for entry in registry.all()] == ["Healthy"]


@pytest.mark.asyncio
async def test_setup_group_reuses_pending_same_owner_creation(tmp_path, monkeypatch) -> None:
    registry = AgentRegistry(OpenHireStore(tmp_path))
    calls: list[str] = []

    async def fake_ensure_running(adapter, instance_name, agent_cfg, workspace):
        assert adapter.agent_name == "nanobot"
        assert workspace == _employee_workspace(tmp_path, instance_name)
        calls.append(instance_name)
        return agent_cfg["container_name"]

    monkeypatch.setattr("openhire.workforce.lifecycle.ensure_running", fake_ensure_running)

    lifecycle = AgentLifecycle(registry, tmp_path, docker_agents_config=_docker_config())
    results = await lifecycle.setup_group(
        "oc_launch",
        [
            {"owner_id": "ou_company", "name": "店铺运营经理", "role": "店铺运营", "agent_type": "nanobot"},
            {"owner_id": "ou_company", "name": "店铺运营经理", "role": "同名复用", "agent_type": "nanobot"},
            {"owner_id": "ou_company", "name": "运营别名", "role": "店铺运营", "agent_type": "nanobot"},
        ],
    )

    assert len(calls) == 1
    assert len({entry.agent_id for entry in results}) == 1
    assert len(registry.all()) == 1


@pytest.mark.asyncio
async def test_setup_group_reuses_same_owner_when_name_or_role_matches(tmp_path) -> None:
    registry = AgentRegistry(OpenHireStore(tmp_path))
    owner_id = "ou_user"
    existing_by_name = registry.register(
        AgentEntry(
            name="店铺运营经理",
            owner_id=owner_id,
            role="负责店铺日常运营。",
            agent_type="nanobot",
            status="active",
        )
    )
    existing_by_role = registry.register(
        AgentEntry(
            name="广告增长负责人",
            owner_id=owner_id,
            role="广告投放优化师",
            agent_type="nanobot",
            status="active",
        )
    )
    lifecycle = AgentLifecycle(registry, tmp_path)

    results = await lifecycle.setup_group(
        "oc_store_ops",
        [
            {"owner_id": owner_id, "name": "店铺运营经理", "role": "不同但同名应复用"},
            {"owner_id": owner_id, "name": "另一个名字", "role": "广告投放优化师"},
        ],
    )

    assert [entry.agent_id for entry in results] == [
        existing_by_name.agent_id,
        existing_by_role.agent_id,
    ]
    assert len(registry.all()) == 2
