from __future__ import annotations

import json
import time
from types import SimpleNamespace
from unittest.mock import AsyncMock, MagicMock

import pytest
import pytest_asyncio

from openhire.admin.demo_mode import demo_mode_status
from openhire.admin.runtime import RuntimeMonitor, build_admin_snapshot
from openhire.api.server import create_app as _create_app
from openhire.config.schema import DockerAgentConfig, DockerAgentsConfig
from openhire.workforce.organization import OrganizationStore
from openhire.workforce.registry import AgentEntry, AgentRegistry
from openhire.workforce.required_skill import REQUIRED_EMPLOYEE_SKILL_ID
from openhire.workforce.store import OpenHireStore

try:
    from aiohttp.test_utils import TestClient, TestServer

    HAS_AIOHTTP = True
except ImportError:
    HAS_AIOHTTP = False


def create_app(*args, **kwargs):
    kwargs.setdefault("admin_auth_required", False)
    return _create_app(*args, **kwargs)


@pytest_asyncio.fixture
async def aiohttp_client():
    clients: list[TestClient] = []

    async def _make_client(app):
        client = TestClient(TestServer(app))
        await client.start_server()
        clients.append(client)
        return client

    try:
        yield _make_client
    finally:
        for client in clients:
            await client.close()


def _make_agent() -> MagicMock:
    agent = MagicMock()
    agent.workspace = None
    agent.provider = None
    agent.model = "test-model"
    agent.context_window_tokens = 10000
    agent.process_direct = AsyncMock(return_value="ok")
    agent._docker_agents_config = None
    agent.get_admin_snapshot = AsyncMock(
        return_value={
            "generatedAt": "2026-04-27T00:00:00Z",
            "process": {"role": "api", "pid": 1, "workspace": "/workspace", "uptimeSeconds": 1},
            "mainAgent": {"status": "idle", "model": "test-model", "context": {}, "lastUsage": {}},
            "subagents": [],
            "dockerContainers": [],
            "dockerAgents": [],
        }
    )
    agent._connect_mcp = AsyncMock()
    agent.close_mcp = AsyncMock()
    return agent


def test_demo_mode_env_detection_and_explicit_disable() -> None:
    assert demo_mode_status(environ={"OPENHIRE_DEMO_MODE": "1"})["enabled"] is True
    assert demo_mode_status(environ={"OPENHIRE_DEPLOY_TARGET": "modelscope"})["enabled"] is True
    assert demo_mode_status(environ={"MODELSCOPE_STUDIO_ID": "studio-1"})["enabled"] is True
    assert demo_mode_status(
        environ={"OPENHIRE_DEMO_MODE": "0", "OPENHIRE_DEPLOY_TARGET": "modelscope"}
    )["enabled"] is False


@pytest.mark.asyncio
async def test_demo_runtime_snapshot_does_not_probe_docker(monkeypatch) -> None:
    monkeypatch.setenv("OPENHIRE_DEMO_MODE", "1")

    async def fail_probe(*_args, **_kwargs):
        raise AssertionError("demo mode must not probe Docker")

    monkeypatch.setattr("openhire.admin.runtime.probe_docker_daemon", fail_probe)
    loop = SimpleNamespace(
        model="test-model",
        workspace="/demo/workspace",
        _start_time=time.time() - 120,
        _active_tasks={},
        _last_usage={},
        context_window_tokens=10000,
        _last_admin_session_key=None,
        _last_admin_context_tokens=0,
        _last_admin_context_source="unknown",
        _last_admin_stop_reason=None,
        _docker_agents_config=DockerAgentsConfig(
            enabled=True,
            agents={"nanobot": DockerAgentConfig(image="openhire/nanobot:test")},
        ),
        docker_runtime_tracker=None,
    )

    snapshot = await build_admin_snapshot(loop)

    assert snapshot["demoMode"]["enabled"] is True
    assert snapshot["dockerDaemon"]["demo"] is True
    assert snapshot["dockerContainers"]
    assert snapshot["dockerContainers"][0]["demo"] is True


@pytest.mark.asyncio
async def test_demo_runtime_monitor_sampler_uses_virtual_docker(monkeypatch) -> None:
    monkeypatch.setenv("OPENHIRE_DEMO_MODE", "1")

    async def fail_probe(*_args, **_kwargs):
        raise AssertionError("demo sampler must not probe Docker")

    monkeypatch.setattr("openhire.admin.runtime.probe_docker_daemon", fail_probe)
    monitor = RuntimeMonitor(
        process_role="gateway",
        workspace="/demo/workspace",
        model="test-model",
        context_window_tokens=10000,
    )
    monitor.start_docker_sampler(interval_s=0.01)
    try:
        await asyncio_sleep()
        snapshot = monitor.snapshot()
    finally:
        await monitor.stop_docker_sampler()

    assert snapshot["dockerDaemon"]["demo"] is True
    assert snapshot["dockerContainers"][0]["source"] == "demo"


async def asyncio_sleep() -> None:
    import asyncio

    await asyncio.sleep(0.03)


@pytest.mark.skipif(not HAS_AIOHTTP, reason="aiohttp not installed")
@pytest.mark.asyncio
async def test_demo_mode_skips_employee_container_restore(aiohttp_client, monkeypatch, tmp_path) -> None:
    monkeypatch.setenv("OPENHIRE_DEMO_MODE", "1")

    async def fail_restore(_self):
        raise AssertionError("demo mode should not restore real Docker employees")

    monkeypatch.setattr("openhire.workforce.lifecycle.AgentLifecycle.restore_active_agents", fail_restore)
    app = create_app(_make_agent(), model_name="test-model", workspace=tmp_path)
    client = await aiohttp_client(app)

    assert "employee_restore_task" not in app
    await client.close()


@pytest.mark.skipif(not HAS_AIOHTTP, reason="aiohttp not installed")
@pytest.mark.asyncio
async def test_demo_mode_materializes_employees_and_skills_for_empty_admin_data(
    aiohttp_client,
    monkeypatch,
    tmp_path,
) -> None:
    monkeypatch.setenv("OPENHIRE_DEMO_MODE", "1")

    async def fail_create(_self, *_args, **_kwargs):
        raise AssertionError("demo bootstrap must not create real employee containers")

    monkeypatch.setattr("openhire.workforce.lifecycle.AgentLifecycle.create_agent", fail_create)
    app = create_app(_make_agent(), model_name="test-model", workspace=tmp_path)
    (tmp_path / "openhire" / "cases.json").write_text(json.dumps({"cases": []}), encoding="utf-8")
    client = await aiohttp_client(app)

    employees = await (await client.get("/employees")).json()
    skills = await (await client.get("/skills")).json()
    cases = await (await client.get("/admin/api/cases")).json()
    agent_skills = await (await client.get("/admin/api/agent-skills")).json()
    runtime = await (await client.get("/admin/api/runtime")).json()

    assert len(employees) == 5
    assert {item["id"] for item in employees} == {
        "demo-market",
        "demo-product",
        "demo-architect",
        "demo-qa-ops",
        "demo-finance",
    }
    assert all(item["agent_config"]["demo"] is True for item in employees)
    assert all("demo" not in item and "readOnly" not in item for item in employees)
    assert {item["id"] for item in skills} >= {
        REQUIRED_EMPLOYEE_SKILL_ID,
        "market-research",
        "product-brief",
        "system-design",
        "release-checklist",
        "risk-review",
    }
    assert any(item["source"] == "demo" for item in skills)
    assert cases["cases"] and cases["cases"][0]["demo"] is True
    assert any(item.get("demo") is True for item in agent_skills)
    assert runtime["demoMode"]["enabled"] is True
    assert runtime["demoTodos"]
    assert (tmp_path / "openhire" / "agents.json").exists()
    assert (tmp_path / "openhire" / "skills.json").exists()
    assert "employee_restore_task" not in app


@pytest.mark.skipif(not HAS_AIOHTTP, reason="aiohttp not installed")
@pytest.mark.asyncio
async def test_demo_mode_materializes_default_organization(aiohttp_client, monkeypatch, tmp_path) -> None:
    monkeypatch.setenv("OPENHIRE_DEMO_MODE", "1")
    app = create_app(_make_agent(), model_name="test-model", workspace=tmp_path)
    client = await aiohttp_client(app)

    resp = await client.get("/admin/api/organization")

    assert resp.status == 200
    body = await resp.json()
    assert {item["id"] for item in body["employees"]} == {
        "demo-market",
        "demo-product",
        "demo-architect",
        "demo-qa-ops",
        "demo-finance",
    }
    assert body["validation"]["valid"] is True
    assert body["settings"]["allow_skip_level_reporting"] is False
    assert body["edges"] == [
        {"reporter_id": "demo-market", "manager_id": "demo-product"},
        {"reporter_id": "demo-architect", "manager_id": "demo-product"},
        {"reporter_id": "demo-finance", "manager_id": "demo-product"},
        {"reporter_id": "demo-qa-ops", "manager_id": "demo-architect"},
    ]
    assert (tmp_path / "openhire" / "agents.json").exists()
    assert (tmp_path / "openhire" / "organization.json").exists()


@pytest.mark.skipif(not HAS_AIOHTTP, reason="aiohttp not installed")
@pytest.mark.asyncio
async def test_demo_materialized_organization_can_save_capabilities(
    aiohttp_client,
    monkeypatch,
    tmp_path,
) -> None:
    monkeypatch.setenv("OPENHIRE_DEMO_MODE", "1")
    app = create_app(_make_agent(), model_name="test-model", workspace=tmp_path)
    client = await aiohttp_client(app)
    initial = await (await client.get("/admin/api/organization")).json()

    resp = await client.put(
        "/admin/api/organization",
        json={
            "settings": initial["settings"],
            "nodes": initial["nodes"],
            "edges": [
                {"reporter_id": "demo-market", "manager_id": "demo-architect"},
                {"reporter_id": "demo-architect", "manager_id": "demo-product"},
                {"reporter_id": "demo-finance", "manager_id": "demo-product"},
                {"reporter_id": "demo-qa-ops", "manager_id": "demo-architect"},
            ],
            "capabilities": [
                {
                    "employee_id": "demo-market",
                    "skill_ids": ["market-research"],
                    "tools": ["browser", "search", "message"],
                }
            ],
        },
    )

    assert resp.status == 200
    body = await resp.json()
    assert body["validation"]["valid"] is True
    assert {"reporter_id": "demo-market", "manager_id": "demo-architect"} in body["edges"]
    updated = app["employee_registry"].get("demo-market")
    assert updated is not None
    assert updated.skill_ids == [REQUIRED_EMPLOYEE_SKILL_ID, "market-research"]
    assert updated.tools == ["browser", "search", "message"]


@pytest.mark.skipif(not HAS_AIOHTTP, reason="aiohttp not installed")
@pytest.mark.asyncio
async def test_demo_mode_does_not_override_real_employees(aiohttp_client, monkeypatch, tmp_path) -> None:
    monkeypatch.setenv("OPENHIRE_DEMO_MODE", "1")
    registry = AgentRegistry(OpenHireStore(tmp_path))
    entry = registry.register(AgentEntry(name="Real Employee", role="Backend Engineer"))
    OrganizationStore(tmp_path).save(
        {
            "settings": {"allow_skip_level_reporting": True},
            "nodes": [{"employee_id": entry.agent_id, "x": 99, "y": 101}],
            "edges": [],
        },
        employee_ids={entry.agent_id},
    )
    app = create_app(_make_agent(), model_name="test-model", workspace=tmp_path)
    client = await aiohttp_client(app)

    employees = await (await client.get("/employees")).json()
    organization = await (await client.get("/admin/api/organization")).json()

    assert [item["id"] for item in employees] == [entry.agent_id]
    assert "demo" not in employees[0]
    assert [item["id"] for item in organization["employees"]] == [entry.agent_id]
    assert organization["nodes"][0]["x"] == 99
    assert organization["settings"]["allow_skip_level_reporting"] is True


def test_admin_static_contains_demo_mode_guards() -> None:
    from pathlib import Path

    body = (Path(__file__).resolve().parents[1] / "openhire" / "admin" / "static" / "admin.js").read_text(
        encoding="utf-8"
    )

    assert "data-demo-badge" in body
    assert "demoTodos" in body
    assert "data-demo-connected-processes" in body
    assert "return employeeState.employees.filter((employee) => !employee.readOnly" in body
