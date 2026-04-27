from __future__ import annotations

import asyncio
import json
from types import SimpleNamespace
from unittest.mock import AsyncMock, MagicMock

import pytest
import pytest_asyncio

from openhire.api.server import create_admin_app, create_app
from openhire.agent.memory import MemoryStore
from openhire.admin import employee_context as employee_context_module
from openhire.admin.runtime import RuntimeMonitor
from openhire.session.manager import SessionManager
from openhire.workforce.registry import AgentEntry
from openhire.workforce.workspace import employee_workspace_path

try:
    from aiohttp.test_utils import TestClient, TestServer

    HAS_AIOHTTP = True
except ImportError:
    HAS_AIOHTTP = False


class _FakeProvider:
    generation = SimpleNamespace(max_tokens=128)

    def estimate_prompt_tokens(self, messages, tools, model):
        token_total = sum(len(str(message.get("content", ""))) for message in messages)
        return max(1, token_total), "test_counter"

    async def chat_with_retry(self, **kwargs):
        return SimpleNamespace(content="压缩摘要", tool_calls=[])


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


def _make_admin_agent():
    agent = MagicMock()
    agent.workspace = None
    agent.provider = _FakeProvider()
    agent.model = "test-model"
    agent.context_window_tokens = 1000
    agent.tools = SimpleNamespace(get_definitions=lambda: [])
    agent._docker_agents_config = SimpleNamespace(enabled=False)
    agent._last_admin_session_key = None
    agent._last_admin_context_tokens = 0
    agent._last_admin_context_source = "unknown"
    agent.runtime_monitor = None
    agent.process_direct = AsyncMock(return_value="ok")
    agent.clear_admin_context = AsyncMock(return_value={"sessionKey": "api:default", "clearedMessages": 3})
    agent.compact_admin_context = AsyncMock(
        return_value={"sessionKey": "api:default", "archivedMessages": 4, "keptMessages": 2}
    )
    agent.delete_admin_container = AsyncMock(return_value={"containerName": "nanobot-3", "deleted": True})
    agent.get_admin_snapshot = AsyncMock(
        return_value={
            "generatedAt": "2026-04-15T12:00:00Z",
            "process": {
                "role": "api",
                "pid": 123,
                "workspace": "/workspace",
                "uptimeSeconds": 5,
            },
            "mainAgent": {
                "status": "idle",
                "model": "test-model",
                "uptimeSeconds": 5,
                "activeTaskCount": 0,
                "lastSessionKey": None,
                "context": {
                    "usedTokens": 0,
                    "totalTokens": 1000,
                    "percent": 0,
                    "source": "unknown",
                },
                "lastUsage": {
                    "promptTokens": 0,
                    "completionTokens": 0,
                    "cachedTokens": 0,
                },
            },
            "subagents": [],
            "dockerDaemon": {
                "status": "running",
                "ok": True,
                "message": "Docker daemon is reachable.",
                "version": "test",
            },
            "dockerContainers": [],
            "dockerAgents": [],
        }
    )
    agent._connect_mcp = AsyncMock()
    agent.close_mcp = AsyncMock()
    return agent


@pytest.mark.skipif(not HAS_AIOHTTP, reason="aiohttp not installed")
@pytest.mark.asyncio
async def test_admin_page_contains_mount_points(aiohttp_client) -> None:
    app = create_app(_make_admin_agent(), model_name="test-model")
    client = await aiohttp_client(app)

    resp = await client.get("/admin")

    assert resp.status == 200
    body = await resp.text()
    assert '<html lang="en" data-theme="dark">' in body
    assert 'id="admin-app"' in body
    assert 'id="admin-preferences"' in body
    assert 'id="admin-language-zh"' in body
    assert 'id="admin-language-en"' in body
    assert 'id="admin-theme-toggle"' in body
    assert 'id="admin-github-link"' in body
    assert 'href="https://github.com/pzy2000/openhire"' in body
    assert 'id="hero-command-center"' in body
    assert 'id="hero-runtime-summary"' in body
    assert 'id="alert-strip"' in body
    assert 'id="action-center"' in body
    assert 'id="control-center"' in body
    assert 'id="runtime-timeline"' in body
    assert 'id="employee-studio"' in body
    assert 'id="resource-hub"' in body
    assert 'id="agent-skills-workbench"' in body
    assert 'id="agent-skills-panel"' in body
    assert 'id="infrastructure-shell"' in body
    assert 'id="dream-shell"' in body
    assert 'id="dream-panel"' in body
    assert 'id="process-panel"' in body
    assert 'id="case-carousel"' in body
    assert 'id="case-config-file-input"' in body
    assert 'id="skill-ops-panel"' in body
    assert 'id="employee-list"' in body
    assert 'id="main-agent-panel"' in body
    assert 'id="subagent-list"' not in body
    assert "Background agents spawned by the main loop." not in body
    assert 'id="docker-agent-list"' in body
    assert 'id="soul-library-panel"' in body
    assert 'id="skill-local-list"' in body
    assert 'id="skill-search-panel"' in body
    assert body.count('data-nav-target="') == 7
    assert 'data-nav-target="hero-command-center"' in body
    assert 'data-nav-target="control-center"' in body
    assert 'data-nav-target="employee-studio"' in body
    assert 'data-nav-target="resource-hub"' in body
    assert 'data-nav-target="agent-skills-workbench"' in body
    assert 'data-nav-target="infrastructure-shell"' in body
    assert 'data-nav-target="dream-shell"' in body
    assert 'data-nav-key="hero-command-center"' in body
    assert 'data-nav-key="control-center"' in body
    assert 'data-resource-tab="cases"' in body
    assert 'data-resource-tab="personas"' in body
    assert 'data-resource-tab="skills"' in body
    assert 'role="tablist"' in body
    assert body.index('id="hero-command-center"') < body.index('id="control-center"') < body.index('id="employee-studio"') < body.index('id="resource-hub"') < body.index('id="agent-skills-workbench"') < body.index('id="infrastructure-shell"') < body.index('id="dream-shell"')
    assert "Import From Local Skills" in body
    assert "Import From Web" in body
    assert body.index("Import From Local Skills") < body.index("Import From Web")
    assert "Smart Recommend" in body
    assert "data-smart-skill-recommend-toggle" in body
    assert "role=\"switch\"" in body
    assert 'data-i18n="hero.eyebrow"' in body
    assert 'data-i18n="hero.title"' in body
    assert 'data-i18n="hero.copy"' in body
    assert 'data-i18n="section.control.title"' in body
    assert 'data-i18n="section.resource.title"' in body
    assert 'data-i18n="section.infrastructure.title"' in body
    assert 'data-i18n="preferences.language.label"' in body
    assert 'data-i18n-aria-label="links.github"' in body
    assert "employee-section-actions" in body
    assert "smart-skill-switch" in body
    assert 'id="local-skill-file-input"' in body
    assert "/admin/assets/admin.js" in body


@pytest.mark.skipif(not HAS_AIOHTTP, reason="aiohttp not installed")
@pytest.mark.asyncio
async def test_admin_runtime_endpoint_returns_snapshot(aiohttp_client) -> None:
    agent = _make_admin_agent()
    app = create_app(agent, model_name="test-model")
    client = await aiohttp_client(app)

    resp = await client.get("/admin/api/runtime")

    assert resp.status == 200
    body = await resp.json()
    assert body["generatedAt"] == "2026-04-15T12:00:00Z"
    assert body["process"]["role"] == "api"
    assert "mainAgent" in body
    assert "subagents" in body
    assert body["dockerDaemon"]["ok"] is True
    assert "dockerContainers" in body
    assert "dockerAgents" in body
    assert "env" not in str(body)


@pytest.mark.skipif(not HAS_AIOHTTP, reason="aiohttp not installed")
@pytest.mark.asyncio
async def test_admin_runtime_endpoint_adds_managed_employee_context_to_docker_rows(aiohttp_client, tmp_path) -> None:
    agent = _make_admin_agent()
    app = create_app(agent, model_name="test-model", workspace=tmp_path)
    entry = app["employee_registry"].register(
        AgentEntry(name="Runtime Context", role="Ops", agent_type="nanobot")
    )
    session_key = _create_employee_session(tmp_path, entry, turns=1)
    agent.get_admin_snapshot = AsyncMock(return_value={
        "generatedAt": "2026-04-15T12:00:00Z",
        "process": {"role": "api", "pid": 123, "workspace": str(tmp_path), "uptimeSeconds": 5},
        "mainAgent": {"status": "idle", "context": {"usedTokens": 0, "totalTokens": 1000, "percent": 0}},
        "subagents": [],
        "dockerDaemon": {"status": "running", "ok": True},
        "dockerContainers": [{
            "name": entry.container_name,
            "containerName": entry.container_name,
            "image": "openhire-nanobot:latest",
            "status": "running",
        }],
        "dockerAgents": [],
    })
    client = await aiohttp_client(app)

    resp = await client.get("/admin/api/runtime")

    assert resp.status == 200
    body = await resp.json()
    row = body["dockerContainers"][0]
    assert row["employeeId"] == entry.agent_id
    assert row["employeeName"] == "Runtime Context"
    assert row["sessionKey"] == session_key
    assert row["context"]["available"] is True
    assert row["context"]["sessionKey"] == session_key
    assert row["context"]["source"] == "test_counter"


@pytest.mark.skipif(not HAS_AIOHTTP, reason="aiohttp not installed")
@pytest.mark.asyncio
async def test_admin_runtime_endpoint_reads_openclaw_container_context(
    aiohttp_client,
    tmp_path,
    monkeypatch,
) -> None:
    agent = _make_admin_agent()
    app = create_app(agent, model_name="test-model", workspace=tmp_path)
    entry = app["employee_registry"].register(
        AgentEntry(name="OpenClaw Runtime", role="Ops", agent_type="openclaw")
    )
    raw = _openclaw_session_jsonl(entry.container_name, turns=2)

    async def fake_docker_exec(container_name: str, *args, timeout: float = 2.5) -> str:
        assert container_name == entry.container_name
        return raw

    monkeypatch.setattr(employee_context_module, "_docker_exec_text", fake_docker_exec)
    agent.get_admin_snapshot = AsyncMock(return_value={
        "generatedAt": "2026-04-15T12:00:00Z",
        "process": {"role": "api", "pid": 123, "workspace": str(tmp_path), "uptimeSeconds": 5},
        "mainAgent": {"status": "idle", "context": {"usedTokens": 0, "totalTokens": 1000, "percent": 0}},
        "subagents": [],
        "dockerDaemon": {"status": "running", "ok": True},
        "dockerContainers": [{
            "name": entry.container_name,
            "containerName": entry.container_name,
            "image": "openhire-openclaw:latest",
            "status": "running",
        }],
        "dockerAgents": [],
    })
    client = await aiohttp_client(app)

    resp = await client.get("/admin/api/runtime")

    assert resp.status == 200
    body = await resp.json()
    context = body["dockerContainers"][0]["context"]
    assert context["available"] is True
    assert context["sessionKey"] == f"openhire-delegate-{entry.container_name}"
    assert context["source"] == "openclaw_container"
    assert context["messageCount"] == 4
    assert context["usedTokens"] > 0


@pytest.mark.skipif(not HAS_AIOHTTP, reason="aiohttp not installed")
@pytest.mark.asyncio
async def test_admin_dream_endpoint_lists_main_and_employee_subjects(aiohttp_client, tmp_path) -> None:
    app = create_app(_make_admin_agent(), model_name="test-model", workspace=tmp_path)
    entry = app["employee_registry"].register(
        AgentEntry(name="Nova Memory", role="Ops", agent_type="nanobot", system_prompt="Remember ops.")
    )
    main_store = MemoryStore(tmp_path)
    main_store.append_history("Main event")
    employee_store = MemoryStore(employee_workspace_path(tmp_path, entry))
    employee_store.append_history("Employee event")
    employee_store.set_last_dream_cursor(1)
    session_key = _create_employee_session(tmp_path, entry, turns=1)
    client = await aiohttp_client(app)

    resp = await client.get("/admin/api/dream")

    assert resp.status == 200
    body = await resp.json()
    subjects = {item["id"]: item for item in body["subjects"]}
    assert subjects["main"]["historyCount"] == 1
    assert subjects["main"]["unprocessedCount"] == 1
    assert subjects[entry.agent_id]["name"] == "Nova Memory"
    assert subjects[entry.agent_id]["agentType"] == "nanobot"
    assert subjects[entry.agent_id]["unprocessedCount"] == 0
    assert subjects[entry.agent_id]["context"]["available"] is True
    assert subjects[entry.agent_id]["context"]["sessionKey"] == session_key
    assert "cron" in body


@pytest.mark.skipif(not HAS_AIOHTTP, reason="aiohttp not installed")
@pytest.mark.asyncio
async def test_admin_dream_endpoint_reads_openclaw_container_context(
    aiohttp_client,
    tmp_path,
    monkeypatch,
) -> None:
    agent = _make_admin_agent()
    app = create_app(agent, model_name="test-model", workspace=tmp_path)
    entry = app["employee_registry"].register(
        AgentEntry(name="OpenClaw Dream", role="Ops", agent_type="openclaw")
    )
    raw = _openclaw_session_jsonl(entry.container_name, turns=1)

    async def fake_docker_exec(container_name: str, *args, timeout: float = 2.5) -> str:
        assert container_name == entry.container_name
        return raw

    monkeypatch.setattr(employee_context_module, "_docker_exec_text", fake_docker_exec)
    agent.get_admin_snapshot = AsyncMock(return_value={
        "generatedAt": "2026-04-15T12:00:00Z",
        "process": {"role": "api", "pid": 123, "workspace": str(tmp_path), "uptimeSeconds": 5},
        "mainAgent": {"status": "idle", "context": {"usedTokens": 0, "totalTokens": 1000, "percent": 0}},
        "subagents": [],
        "dockerDaemon": {"status": "running", "ok": True},
        "dockerContainers": [{
            "name": entry.container_name,
            "containerName": entry.container_name,
            "image": "openhire-openclaw:latest",
            "status": "running",
        }],
        "dockerAgents": [],
    })
    client = await aiohttp_client(app)

    resp = await client.get("/admin/api/dream")

    assert resp.status == 200
    body = await resp.json()
    subjects = {item["id"]: item for item in body["subjects"]}
    context = subjects[entry.agent_id]["context"]
    assert context["available"] is True
    assert context["source"] == "openclaw_container"
    assert context["messageCount"] == 2
    assert subjects[entry.agent_id]["workspaceUnprocessedCount"] == 0
    assert subjects[entry.agent_id]["unprocessedCount"] == 1
    assert subjects[entry.agent_id]["externalHistory"]["pendingMessages"] == 2


@pytest.mark.skipif(not HAS_AIOHTTP, reason="aiohttp not installed")
@pytest.mark.asyncio
async def test_admin_dream_subject_returns_files_history_and_diff(aiohttp_client, tmp_path) -> None:
    app = create_app(_make_admin_agent(), model_name="test-model", workspace=tmp_path)
    store = MemoryStore(tmp_path)
    store.git.init()
    store.write_memory("# Memory\n- Dream fact")
    sha = store.git.auto_commit("dream: test update")
    store.append_history("History item")
    client = await aiohttp_client(app)

    resp = await client.get("/admin/api/dream/subjects/main")

    assert resp.status == 200
    body = await resp.json()
    files = {item["name"]: item for item in body["files"]}
    assert files["MEMORY.md"]["content"] == "# Memory\n- Dream fact"
    assert files["history.jsonl"]["entries"][0]["content"] == "History item"
    assert body["commits"][0]["sha"] == sha
    assert "Dream fact" in body["selectedCommit"]["diff"]


@pytest.mark.skipif(not HAS_AIOHTTP, reason="aiohttp not installed")
@pytest.mark.asyncio
async def test_admin_dream_employee_subject_returns_context(aiohttp_client, tmp_path) -> None:
    app = create_app(_make_admin_agent(), model_name="test-model", workspace=tmp_path)
    entry = app["employee_registry"].register(
        AgentEntry(name="Dream Context", role="Ops", agent_type="nanobot")
    )
    session_key = _create_employee_session(tmp_path, entry, turns=1)
    client = await aiohttp_client(app)

    resp = await client.get(f"/admin/api/dream/subjects/{entry.agent_id}")

    assert resp.status == 200
    body = await resp.json()
    assert body["subject"]["context"]["available"] is True
    assert body["subject"]["context"]["sessionKey"] == session_key


@pytest.mark.skipif(not HAS_AIOHTTP, reason="aiohttp not installed")
@pytest.mark.asyncio
async def test_admin_dream_run_reports_nothing_to_process(aiohttp_client, tmp_path) -> None:
    app = create_app(_make_admin_agent(), model_name="test-model", workspace=tmp_path)
    client = await aiohttp_client(app)

    resp = await client.post("/admin/api/dream/subjects/main/run")

    assert resp.status == 200
    body = await resp.json()
    assert body["status"] == "nothing_to_process"
    assert body["didWork"] is False


@pytest.mark.skipif(not HAS_AIOHTTP, reason="aiohttp not installed")
@pytest.mark.asyncio
async def test_admin_dream_run_ingests_openclaw_container_history(
    aiohttp_client,
    tmp_path,
    monkeypatch,
) -> None:
    agent = _make_admin_agent()
    app = create_app(agent, model_name="test-model", workspace=tmp_path)
    entry = app["employee_registry"].register(
        AgentEntry(name="OpenClaw Dream Run", role="Ops", agent_type="openclaw")
    )
    raw = _openclaw_session_jsonl(entry.container_name, turns=2)

    async def fake_docker_exec(container_name: str, *args, timeout: float = 2.5) -> str:
        assert container_name == entry.container_name
        return raw

    async def fake_dream_run(self):
        assert self.agent_skill_workspace == tmp_path
        entries = self.store.read_unprocessed_history(since_cursor=0)
        assert entries
        assert "OpenClaw session" in entries[0]["content"]
        assert "openclaw request 0" in entries[0]["content"]
        self.store.set_last_dream_cursor(entries[-1]["cursor"])
        return True

    monkeypatch.setattr(employee_context_module, "_docker_exec_text", fake_docker_exec)
    monkeypatch.setattr("openhire.api.server.Dream.run", fake_dream_run)
    agent.get_admin_snapshot = AsyncMock(return_value={
        "generatedAt": "2026-04-15T12:00:00Z",
        "process": {"role": "api", "pid": 123, "workspace": str(tmp_path), "uptimeSeconds": 5},
        "mainAgent": {"status": "idle", "context": {"usedTokens": 0, "totalTokens": 1000, "percent": 0}},
        "subagents": [],
        "dockerDaemon": {"status": "running", "ok": True},
        "dockerContainers": [{
            "name": entry.container_name,
            "containerName": entry.container_name,
            "image": "openhire-openclaw:latest",
            "status": "running",
        }],
        "dockerAgents": [],
    })
    client = await aiohttp_client(app)

    resp = await client.post(f"/admin/api/dream/subjects/{entry.agent_id}/run")

    assert resp.status == 200
    body = await resp.json()
    assert body["status"] == "completed"
    assert body["ingestedHistory"]["ingestedMessages"] == 4
    assert body["ingestedHistory"]["ingestedEntries"] == 1
    store = MemoryStore(employee_workspace_path(tmp_path, entry))
    entries = store.read_unprocessed_history(since_cursor=0)
    assert len(entries) == 1

    second = await client.post(f"/admin/api/dream/subjects/{entry.agent_id}/run")
    second_body = await second.json()
    assert second_body["status"] == "nothing_to_process"
    assert second_body["ingestedHistory"]["ingestedMessages"] == 0


@pytest.mark.skipif(not HAS_AIOHTTP, reason="aiohttp not installed")
@pytest.mark.asyncio
async def test_admin_dream_run_executes_and_blocks_parallel_run(aiohttp_client, tmp_path, monkeypatch) -> None:
    agent = _make_admin_agent()
    agent.provider = MagicMock()
    agent.model = "test-model"
    app = create_app(agent, model_name="test-model", workspace=tmp_path)
    store = MemoryStore(tmp_path)
    store.append_history("Run Dream")
    started = asyncio.Event()
    release = asyncio.Event()

    async def fake_run(self):
        started.set()
        await release.wait()
        self.store.write_memory("Dream changed")
        self.store.set_last_dream_cursor(1)
        self.store.git.auto_commit("dream: fake update")
        return True

    monkeypatch.setattr("openhire.api.server.Dream.run", fake_run)
    client = await aiohttp_client(app)

    first = asyncio.create_task(client.post("/admin/api/dream/subjects/main/run"))
    await asyncio.wait_for(started.wait(), timeout=2)
    conflict = await client.post("/admin/api/dream/subjects/main/run")
    release.set()
    first_resp = await first

    assert conflict.status == 409
    assert first_resp.status == 200
    body = await first_resp.json()
    assert body["status"] == "completed"
    assert MemoryStore(tmp_path).read_memory() == "Dream changed"


@pytest.mark.skipif(not HAS_AIOHTTP, reason="aiohttp not installed")
@pytest.mark.asyncio
async def test_admin_dream_restore_validates_and_restores_commit(aiohttp_client, tmp_path) -> None:
    app = create_app(_make_admin_agent(), model_name="test-model", workspace=tmp_path)
    store = MemoryStore(tmp_path)
    store.git.init()
    store.write_memory("updated memory")
    sha = store.git.auto_commit("dream: update memory")
    client = await aiohttp_client(app)

    missing_sha = await client.post("/admin/api/dream/subjects/main/restore", json={})
    unknown_subject = await client.get("/admin/api/dream/subjects/missing")
    restore = await client.post("/admin/api/dream/subjects/main/restore", json={"sha": sha})

    assert missing_sha.status == 400
    assert unknown_subject.status == 404
    assert restore.status == 200
    body = await restore.json()
    assert body["status"] == "restored"
    assert body["newCommit"]["sha"]
    assert "memory/MEMORY.md" in body["restoredFiles"]
    assert MemoryStore(tmp_path).read_memory() == ""


@pytest.mark.skipif(not HAS_AIOHTTP, reason="aiohttp not installed")
@pytest.mark.asyncio
async def test_admin_runtime_history_endpoint_returns_fallback_sample(aiohttp_client) -> None:
    agent = _make_admin_agent()
    app = create_app(agent, model_name="test-model")
    client = await aiohttp_client(app)

    resp = await client.get("/admin/api/runtime/history?limit=1")

    assert resp.status == 200
    body = await resp.json()
    assert body["windowSeconds"] == 900
    assert body["sampleIntervalSeconds"] == 5
    assert len(body["samples"]) == 1
    sample = body["samples"][0]
    assert sample["mainStatus"] == "idle"
    assert sample["contextPercent"] == 0
    assert sample["dockerDaemonStatus"] == "running"
    assert sample["dockerTotal"] == 0


@pytest.mark.skipif(not HAS_AIOHTTP, reason="aiohttp not installed")
@pytest.mark.asyncio
async def test_admin_runtime_history_endpoint_uses_monitor_history_and_limit(aiohttp_client) -> None:
    agent = _make_admin_agent()
    monitor = RuntimeMonitor(
        process_role="gateway",
        workspace="/workspace",
        model="test-model",
        context_window_tokens=1000,
        history_sample_interval_seconds=0,
    )
    monitor.update_main_context(used_tokens=100, source="live")
    monitor.snapshot()
    monitor.start_main_turn(session_key="feishu:chat-1", channel="feishu", chat_id="chat-1")
    monitor.update_main_context(used_tokens=400, source="live")
    monitor.snapshot()
    agent.runtime_monitor = monitor
    app = create_app(agent, model_name="test-model")
    client = await aiohttp_client(app)

    resp = await client.get("/admin/api/runtime/history?limit=1")

    assert resp.status == 200
    body = await resp.json()
    assert len(body["samples"]) == 1
    assert body["samples"][0]["mainStatus"] == "processing"
    assert body["samples"][0]["contextPercent"] == 40


@pytest.mark.skipif(not HAS_AIOHTTP, reason="aiohttp not installed")
@pytest.mark.asyncio
async def test_create_app_schedules_and_cleans_employee_restore(aiohttp_client, monkeypatch) -> None:
    started = asyncio.Event()
    cancelled = asyncio.Event()
    never_finish = asyncio.Event()

    async def fake_restore_active_agents(_self):
        started.set()
        try:
            await never_finish.wait()
        finally:
            cancelled.set()
        return {"restored": 0, "failed": 0, "skipped": 0}

    monkeypatch.setattr(
        "openhire.workforce.lifecycle.AgentLifecycle.restore_active_agents",
        fake_restore_active_agents,
    )
    app = create_app(_make_admin_agent(), model_name="test-model")
    client = await aiohttp_client(app)

    await asyncio.wait_for(started.wait(), timeout=2)
    task = app["employee_restore_task"]
    assert isinstance(task, asyncio.Task)
    assert not task.done()

    await client.close()
    await asyncio.wait_for(cancelled.wait(), timeout=2)
    assert task.done()


@pytest.mark.skipif(not HAS_AIOHTTP, reason="aiohttp not installed")
@pytest.mark.asyncio
async def test_create_admin_app_schedules_employee_restore(aiohttp_client, monkeypatch) -> None:
    started = asyncio.Event()

    async def fake_restore_active_agents(_self):
        started.set()
        return {"restored": 1, "failed": 0, "skipped": 0}

    monkeypatch.setattr(
        "openhire.workforce.lifecycle.AgentLifecycle.restore_active_agents",
        fake_restore_active_agents,
    )
    app = create_admin_app(_make_admin_agent(), process_role="gateway")
    client = await aiohttp_client(app)

    await asyncio.wait_for(started.wait(), timeout=2)
    assert isinstance(app["employee_restore_task"], asyncio.Task)
    await client.close()


@pytest.mark.skipif(not HAS_AIOHTTP, reason="aiohttp not installed")
@pytest.mark.asyncio
async def test_employees_endpoint_exposes_updated_at(aiohttp_client, tmp_path) -> None:
    app = create_app(_make_admin_agent(), model_name="test-model", workspace=tmp_path)
    app["employee_registry"].register(
        AgentEntry(
            name="Nova FE",
            role="Frontend Engineer",
            system_prompt="Build admin UI",
            agent_type="nanobot",
        )
    )
    client = await aiohttp_client(app)

    resp = await client.get("/employees")

    assert resp.status == 200
    body = await resp.json()
    assert len(body) == 1
    assert body[0]["created_at"]
    assert body[0]["updated_at"]


@pytest.mark.skipif(not HAS_AIOHTTP, reason="aiohttp not installed")
@pytest.mark.asyncio
async def test_admin_js_asset_matches_main_polling_and_sse(aiohttp_client) -> None:
    app = create_app(_make_admin_agent(), model_name="test-model")
    client = await aiohttp_client(app)

    resp = await client.get("/admin/assets/admin.js")

    assert resp.status == 200
    body = await resp.text()
    assert "2000" in body
    assert "EMPLOYEE_POLL_INTERVAL_MS = 10000" in body
    assert "EventSource" in body
    assert "/admin/api/events" in body
    assert 'const RUNTIME_HISTORY_ENDPOINT = "/admin/api/runtime/history"' in body
    assert "renderRuntimeTimeline" in body
    assert "normalizeRuntimeHistorySample" in body
    assert "appendRuntimeHistorySample" in body
    assert "renderRuntimeSparkline" in body
    assert "formatRuntimeLastUpdatedAgo" in body
    assert "RUNTIME_TIMELINE_DAY_MINUTES" in body
    assert "data-runtime-history-refresh" in body
    assert "runtime.timeline.title" in body
    assert "runtime.timeline.refresh" in body
    assert "runtime.timeline.ago.hours_minutes" in body
    assert "runtime.timeline.ago.days_hours_minutes" in body
    assert "formatUtcDate(runtimeHistoryState.lastUpdatedAt)" not in body
    assert "syncEmployeesFromRuntime" in body
    assert "renderEmployeeRuntimeDetail" in body
    assert "dockerAgentSourceLabel" in body
    assert "agent?.employeeName" in body
    assert 'fetch("/employees"' in body
    assert "Delete Employee" in body
    assert "data-delete-employee-card" in body
    assert "data-employee-delete-toggle" in body
    assert "data-delete-selected-employees" in body
    assert "data-export-selected-employees" in body
    assert 'const SOULBANNER_SKILL_SEARCH_ENDPOINT = "/skills/search/soulbanner"' in body
    assert 'const MBTI_SBTI_SKILL_SEARCH_ENDPOINT = "/skills/search/mbti-sbti"' in body
    assert 'const SKILL_GOVERNANCE_ENDPOINT = "/admin/api/skills/governance"' in body
    assert 'const SKILL_GOVERNANCE_SCAN_ENDPOINT = "/admin/api/skills/governance/scan"' in body
    assert 'const SKILL_GOVERNANCE_ACTION_ENDPOINT = "/admin/api/skills/governance/actions"' in body
    assert 'const AGENT_SKILLS_ENDPOINT = "/admin/api/agent-skills"' in body
    assert 'const AGENT_SKILL_PROPOSALS_ENDPOINT = "/admin/api/agent-skills/proposals"' in body
    assert "agentSkillState" in body
    assert "renderAgentSkillsWorkbench" in body
    assert "loadAgentSkills" in body
    assert "refreshAgentSkillProposals" in body
    assert "AGENT_SKILL_PROPOSAL_POLL_INTERVAL_MS" in body
    assert "selectAgentSkill" in body
    assert "createAgentSkillFromDraft" in body
    assert "saveAgentSkill" in body
    assert "writeAgentSkillFile" in body
    assert "approveAgentSkillProposal" in body
    assert "installCatalogSkillToAgentSkills" in body
    assert "data-agent-skill-select" in body
    assert "data-agent-skill-draft" in body
    assert "data-agent-skill-write-file" in body
    assert "data-agent-skill-proposal-approve" in body
    assert "data-install-agent-skill" in body
    assert "Agent Skills Workbench" in body
    assert "Progressive disclosure" in body
    assert "agent_skills.bound_employees" in body
    assert "agent_skills.uncategorized" in body
    assert "action.agent_skill_proposals.title" in body
    assert "data-action-center-agent-skills" in body
    assert 'const DREAM_ENDPOINT = "/admin/api/dream"' in body
    assert 'const DREAM_SUBJECT_ENDPOINT = "/admin/api/dream/subjects/"' in body
    assert "dreamState" in body
    assert "renderDreamPanel" in body
    assert "loadDream" in body
    assert "runSelectedDream" in body
    assert "restoreDreamCommit" in body
    assert "data-dream-refresh" in body
    assert "data-dream-run" in body
    assert "data-dream-subject" in body
    assert "data-dream-file" in body
    assert "data-dream-commit" in body
    assert "data-dream-restore" in body
    assert "data-dream-context-action" in body
    assert "dream.confirm.title" in body
    assert "skillOpsState" in body
    assert "renderSkillOpsPanel" in body
    assert "renderSkillOpsIssue" in body
    assert "loadSkillGovernance" in body
    assert "scanSkillGovernance" in body
    assert "runSkillOpsAction" in body
    assert "confirmSkillOpsAction" in body
    assert "toggleSkillOpsIssueSelection" in body
    assert "toggleSkillOpsAllIssuesSelection" in body
    assert "setSkillOpsIssueListExpanded" in body
    assert "ignoreSelectedSkillOpsIssues" in body
    assert "data-skill-ops-scan" in body
    assert "data-skill-ops-remote" in body
    assert "data-skill-ops-select-all" in body
    assert "data-skill-ops-issue" in body
    assert "data-skill-ops-ignore-selected" in body
    assert "data-skill-ops-ignore" in body
    assert "data-skill-ops-toggle-fold" in body
    assert "data-skill-ops-action" in body
    assert "data-skill-ops-confirm" in body
    assert "data-skill-ops-opportunity" in body
    assert "skill.ops.title" in body
    assert "skill.ops.ignore_selected" in body
    assert "skill.ops.collapsed_summary" in body
    assert "skill.ops.merge_duplicates" in body
    assert "skill.ops.delete_orphans" in body
    assert "skill.ops.repair_employee_bindings" in body
    assert "renderSoulLibraryPanel" in body
    assert "Load SoulBanner Roles" in body
    assert "Load Mbti/Sbti" in body
    assert "loadSoulBannerSkills" in body
    assert "loadMbtiSbtiSkills" in body
    assert "importSelectedSoulBannerSkills" in body
    assert "importSelectedMbtiSbtiSkills" in body
    assert "toggleMbtiSbtiSkill" in body
    assert "normalizeMbtiSbtiSkillCandidate" in body
    assert "data-load-soul-library" in body
    assert "data-load-mbti-sbti-library" in body
    assert "data-import-soulbanner-skills" in body
    assert "data-import-mbti-sbti-skills" in body
    assert "data-toggle-soulbanner-list" in body
    assert "data-toggle-mbti-sbti-list" in body
    assert "toggleSoulBannerListExpansion" in body
    assert "toggleMbtiSbtiListExpansion" in body
    assert "isSoulBannerListExpanded" in body
    assert "isMbtiSbtiListExpanded" in body
    assert "data-mbti-sbti-skill-toggle" in body
    assert 'class="skill-option ${isSelected ? "is-selected" : ""}"' in body
    assert "import-soulbanner-skill-button" not in body
    assert "data-import-case-config" in body
    assert "toggleAllEmployeeDeleteSelections" in body
    assert "batchDeleteEmployees" in body
    assert "EMPLOYEE_EXPORT_ENDPOINT" in body
    assert "/admin/api/employees/export" in body
    assert "CASE_CONFIG_IMPORT_PREVIEW_ENDPOINT" in body
    assert "CASE_CONFIG_IMPORT_ENDPOINT" in body
    assert "/admin/api/cases/import/preview" in body
    assert "/admin/api/cases/import" in body
    assert "openEmployeeExportModal" in body
    assert "renderEmployeeExportModal" in body
    assert "openCaseConfigFilePicker" in body
    assert "previewCaseConfigFile" in body
    assert "showOpenFilePicker" in body
    assert "showSaveFilePicker" in body
    assert "case-config-file-input" in body
    assert "data-employee-export-field" in body
    assert "data-download-export-case" in body
    assert "Export Preview / 导出预览" in body
    assert "adminState.confirmAction = null;" in body
    assert "data-delete-skill-id" in body
    assert "Delete Skill" in body
    assert "data-skill-delete-toggle" in body
    assert "data-delete-selected-skills" in body
    assert "toggleAllSkillDeleteSelections" in body
    assert "batchDeleteSkills" in body
    assert "agent_type" in body
    assert "Custom Role / 自定义角色" in body
    assert "data-cook-template" in body
    assert "data-delete-template-id" in body
    assert "template.id !== CUSTOM_ROLE_TEMPLATE_ID" in body
    assert "Delete Role Template" in body
    assert "custom_role_prompt" in body
    assert "/employee-templates" in body
    assert "/admin/api/employee-templates/cook" in body
    assert "selectedAvatarId" in body
    assert "data-avatar-id" in body
    assert "Choose a preset portrait" in body
    assert "createWizardStep" in body
    assert "createWizardError" in body
    assert "completedCreateWizardSteps" in body
    assert "lastSkillRecommendationProfileSignature" in body
    assert "setCreateWizardStep" in body
    assert "validateCreateWizardStep" in body
    assert "canEnterCreateWizardStep" in body
    assert "renderCreateWizardStepper" in body
    assert "renderCreateWizardBody" in body
    assert "maybeRecommendSkillsForWizardStep" in body
    assert "create-wizard-stepper" in body
    assert 'CREATE_WIZARD_STEPS = ["template", "profile", "skills", "review"]' in body
    assert "data-create-wizard-step" in body
    assert "data-create-wizard-next" in body
    assert "data-create-wizard-back" in body
    assert "data-create-wizard-go" in body
    assert "data-create-wizard-error" in body
    assert "createWizardProfileSignature" in body
    assert "employeeSkillSourceSummary" in body
    assert "modal.create.wizard.template" in body
    assert "modal.create.wizard.profile" in body
    assert "modal.create.wizard.skills" in body
    assert "modal.create.wizard.review" in body
    assert "modal.create.validation.profile_required" in body
    assert "modal.create.review_skill_source" in body
    assert "modal.create.review_title" in body
    assert "modal.create.review_skills" in body
    assert "selectedSkillIds" in body
    assert "smartSkillRecommendEnabled" in body
    assert "openhire.admin.smartSkillRecommendEnabled" in body
    assert "/admin/api/employee-skills/recommend" in body
    assert "recommendedSkillIds" in body
    assert "recommendEmployeeSkills" in body
    assert "Skill recommendation warning" in body
    assert 'const LANGUAGE_STORAGE_KEY = "openhire.admin.language"' in body
    assert 'const THEME_STORAGE_KEY = "openhire.admin.theme"' in body
    assert 'const DEFAULT_THEME = "dark"' in body
    assert "formatUtcDate" in body
    assert "remotePersonaMetaLabel" in body
    assert "navigator.language" in body
    assert 'const SYSTEM_THEME_QUERY = "(prefers-color-scheme: dark)"' in body
    assert "window.matchMedia(SYSTEM_THEME_QUERY)" in body
    assert 'systemThemeQuery()?.matches ? "dark" : DEFAULT_THEME' in body
    assert 'media.addEventListener("change", syncSystemThemePreference)' in body
    assert "applyTheme(detectDefaultTheme(), { persist: false })" in body
    assert "function t(" in body
    assert "function applyLanguage(" in body
    assert "function applyTheme(" in body
    assert "function renderStaticTranslations(" in body
    assert "document.documentElement.lang" in body
    assert "document.documentElement.dataset.theme" in body
    assert "admin-language-zh" in body
    assert "admin-language-en" in body
    assert "admin-theme-toggle" in body
    assert 'resourceHubTab: "cases"' in body
    assert "activeNavSection: NAV_SECTIONS[0].key" in body
    assert "const NAV_SECTIONS = [" in body
    assert "const NAV_SCROLL_OFFSET = 24" in body
    assert "currentActiveNavSection" in body
    assert "renderNavSectionLinks" in body
    assert "setActiveNavSection" in body
    assert "scrollToNavSection" in body
    assert "requestNavSectionSync" in body
    assert "observeNavSections" in body
    assert "IntersectionObserver" in body
    assert "aria-current" in body
    assert "data-nav-target" in body
    assert "normalizeResourceHubTab" in body
    assert "currentResourceHubTab" in body
    assert "setResourceHubTab" in body
    assert "renderResourceHubTabs" in body
    assert "renderHeroBar" in body
    assert "renderAlertStrip" in body
    assert "renderActionCenter" in body
    assert "collectActionItems" in body
    assert "contextPercent >= 70" in body
    assert "dockerDaemonIssue" in body
    assert "dockerDaemonMessage" in body
    assert "alert.docker_daemon" in body
    assert "action.docker_daemon.title" in body
    assert "action.docker_daemon.repair" in body
    assert "DOCKER_DAEMON_REPAIR_ENDPOINT" in body
    assert "repairDockerDaemon" in body
    assert "docker-daemon" in body
    assert "docker.daemon_unavailable" in body
    assert "data-docker-daemon-repair" in body
    assert "data-action-center-docker-repair" in body
    assert "adminState.dockerDaemon = payload.dockerDaemon || {}" in body
    assert "dockerIssues.length" in body
    assert "caseState.importResult" in body
    assert "healthy-actions" in body
    assert "employeesMissingBusinessSkills" in body
    assert "businessSkillCount" in body
    assert "actionCenterCompactMainContext" in body
    assert "actionCenterOpenSkills" in body
    assert "actionCenterOpenCases" in body
    assert "actionCenterOpenEmployee" in body
    assert "actionCenterScrollToInfrastructure" in body
    assert "data-action-center-compact" in body
    assert "data-action-center-control" in body
    assert "data-action-center-infrastructure" in body
    assert "data-action-center-cases" in body
    assert "data-action-center-skills" in body
    assert "data-action-center-employee" in body
    assert "data-action-center-create" in body
    assert "action.context_pressure.title" in body
    assert "action.docker_issue.title" in body
    assert "action.case_partial.title" in body
    assert "action.healthy.title" in body
    assert "runMainAgentContextAction(\"compact\")" in body
    assert "computeEmployeeOpsHealth" in body
    assert "renderEmployeeOpsWorkbench" in body
    assert "renderEmployeeOpsDiagnostics" in body
    assert "handleEmployeeOpsAction" in body
    assert "employee-ops-workbench" in body
    assert "data-employee-ops=\"true\"" in body
    assert "data-employee-ops-action" in body
    assert "data-employee-ops-section=\"config\"" in body
    assert "data-employee-ops-section=\"cron\"" in body
    assert "ops.health.healthy" in body
    assert "ops.health.needs_setup" in body
    assert "ops.health.runtime_issue" in body
    assert "ops.health.restart_required" in body
    assert "ops.health.skill_gap" in body
    assert "Restart required" in body
    assert "employeeHasBusinessSkill(owner || employee" in body
    assert "[\"error\", \"exited\", \"unknown\"].includes(status)" in body
    assert "setResourceHubTab(\"skills\")" in body
    assert "scrollToNavSection(\"infrastructure-shell\")" in body
    assert "openDockerAgentTranscript(containerName)" in body
    assert "alert.none" in body
    assert "alert.import_warning" in body
    assert "updated_at: text(skill.updated_at, \"\")" in body
    assert "remotePersonaMetaLabel(skill)" in body
    assert "themeButton.dataset.themeTarget" in body
    assert "installed_skill_ids" in body
    assert "installed_skills" in body
    assert "mergeInstalledRecommendationSkills" in body
    assert "skillRecommendationRequestId" in body
    assert "lastCreateSkillSummary" in body
    assert "cloud 下载" in body
    assert "local import" in body
    assert "smart-skill-recommend-toggle" in body
    assert "toggleSmartSkillRecommend" in body
    assert "/admin/api/employee-skills/recommend" in body
    assert "recommendedSkillIds" in body
    assert "recommended" in body
    assert "recommendEmployeeSkills" in body
    assert "Skill recommendation warning" in body
    assert "setCreateWizardStep(createWizardStepButton.getAttribute" in body
    assert "REQUIRED_EMPLOYEE_SKILL_ID" in body
    assert "excellent-employee" in body
    assert "Required" in body
    assert "isRequiredLocalSkill" in body
    assert "data-local-skill-id" in body
    assert "expandedSkillIds" in body
    assert "data-skill-expand-id" in body
    assert "EMPLOYEE_LIST_COLLAPSED_COUNT" in body
    assert "isEmployeeDetailExpanded" in body
    assert "EMPLOYEE_SORT_STORAGE_KEY" in body
    assert "window.localStorage" in body
    assert "startEmployeePolling" in body
    assert 'fetch("/employees"' in body
    assert "Failed to refresh employees" in body
    assert "data-employee-sort" in body
    assert "Last Modified" in body
    assert "Created" in body
    assert "Type" in body
    assert "data-toggle-employee-list" in body
    assert "data-toggle-employee-detail" in body
    assert "employee-detail-toggle" in body
    assert "SKILL_LIST_COLLAPSED_COUNT" in body
    assert "data-toggle-local-skill-list" in body
    assert "data-toggle-skill-search-results" in body
    assert "isLocalSkillListExpanded" in body
    assert "isSkillSearchResultsExpanded" in body
    assert "isSoulBannerListExpanded" in body
    assert "isMbtiSbtiListExpanded" in body
    assert "lastImportedSkillIds" in body
    assert "Show More" in body
    assert "createDraft" in body
    assert "scrollTop" in body
    assert "requestAnimationFrame" in body
    assert "Collapse" in body
    assert "CREATE_EMPLOYEE_PROGRESS_STAGES" in body
    assert "startCreateEmployeeProgress" in body
    assert "stopCreateEmployeeProgress" in body
    assert "updateBusyActionProgress" in body
    assert "Invoking LLM to create SOUL.md and AGENTS.md" in body
    assert "Creating Docker Container" in body
    assert "Finalizing employee workspace" in body
    assert "Employee created" in body
    assert "busy-progress" in body
    assert "role=\"progressbar\"" in body
    assert "aria-valuenow" in body
    assert "stopCreateEmployeeProgress();" in body
    assert "The excellent-employee skill is required for every digital employee." in body
    assert "Import From Local Skills" in body
    assert "Import From Web" in body
    assert "local-skill-file-input" in body
    assert "/skills/import/local/preview" in body
    assert "/skills/import/web/preview" in body
    assert "Paste a public SKILL.md URL" in body
    assert "Web Import Preview" in body
    assert "Confirm Import" in body
    assert "data-skill-card-id" in body
    assert "expandedLocalSkillLabelIds" in body
    assert "data-skill-label-cloud" in body
    assert "data-skill-label-toggle" in body
    assert "refreshLocalSkillLabelToggles" in body
    assert "toggleLocalSkillLabels" in body
    assert "skills.expand_labels" in body
    assert "skills.collapse_labels" in body
    assert "skill.tags" in body
    assert "skill-content-modal" in body
    assert "skill-content-modal-shell" in body
    assert "skill-content-modal-close" in body
    assert "data-skill-content-edit" in body
    assert "data-skill-content-save" in body
    assert "data-search-skill-preview" in body
    assert "Import This Skill" in body
    assert "/skills/search/clawhub/content" in body
    assert "markdownStatus" in body
    assert "markdownError" in body
    assert "data-import-search-skill" in body
    assert "Save Only" in body
    assert "Save + Sync Employees" in body
    assert "/skills/" in body
    assert "/content" in body
    assert "sync_employee_prompts" in body
    assert "skill-content-editor" in body
    assert "isDirty" in body
    assert "CLAWHUB_SEARCH_MAX_ATTEMPTS" in body
    assert "CLAWHUB_SEARCH_RETRY_DELAY_MS" in body
    assert "Clear Context" in body
    assert "Compact Context" in body
    assert "Clearing..." in body
    assert "Compacting..." in body
    assert "mainContextAction" in body
    assert "employeeContextAction" in body
    assert "/admin/api/context/clear" in body
    assert "/admin/api/context/compact" in body
    assert "/admin/api/employees/" in body
    assert "data-docker-context-action" in body
    assert "button.clear_short" in body
    assert "button.compact_short" in body
    assert "Delete Docker" in body
    assert "/admin/api/docker-containers/" in body
    assert "docker-daemon-alert" in body
    assert "docker-agent-card-top" in body
    assert "docker-agent-card-actions" in body
    assert "TRANSCRIPT_ENDPOINTS" in body
    assert "/admin/api/transcripts/main" in body
    assert "/admin/api/transcripts/docker/" in body
    assert "data-transcript-main" in body
    assert "data-transcript-docker" in body
    assert "formatTranscriptTimestamp" in body
    assert "numeric > 1000000000000 ? numeric : numeric * 1000" in body
    assert "renderTranscriptModal" in body
    assert "Chat history" in body
    assert "transcript-modal-shell" in body
    assert "transcript-modal-close" in body
    assert "Belongs to / 所属员工" in body
    assert "Unassigned" in body
    assert "runtime-config" in body
    assert "employeeConfigState" in body
    assert "Restart required" in body
    assert "data-employee-config-file" in body
    assert "data-employee-cron-save" in body
    assert "/admin/api/employees/" in body
    assert "/cron" in body
    assert "CASES_ENDPOINT" in body
    assert "/admin/api/cases" in body
    assert 'const CASE_OPS_ENDPOINT = "/admin/api/cases/ops"' in body
    assert 'const CASE_OPS_SCAN_ENDPOINT = "/admin/api/cases/ops/scan"' in body
    assert 'const CASE_OPS_ACTION_ENDPOINT = "/admin/api/cases/ops/actions"' in body
    assert "caseOpsState" in body
    assert "renderCaseOpsPanel" in body
    assert "renderCaseOpsIssue" in body
    assert "renderCaseOpsPreview" in body
    assert "loadCaseOps" in body
    assert "scanCaseOps" in body
    assert "runCaseOpsAction" in body
    assert "confirmCaseOpsAction" in body
    assert "toggleCaseOpsIssueSelection" in body
    assert "data-case-ops-scan" in body
    assert "data-case-ops-issue" in body
    assert "data-case-ops-ignore" in body
    assert "data-case-ops-action" in body
    assert "data-case-ops-confirm" in body
    assert "data-case-ops-open-case" in body
    assert "data-case-ops-import-config" in body
    assert "data-case-ops-opportunity" in body
    assert "case.ops.title" in body
    assert "case.ops.reimport" in body
    assert "renderCaseCarousel" in body
    assert "openCaseDetail" in body
    assert "renderCaseDossierHero" in body
    assert "renderCaseSectionTitle" in body
    assert "case-dossier-hero" in body
    assert "case-dossier-stats" in body
    assert "case-detail-head" in body
    assert '<details class="case-output-details">' in body
    assert '<details class="case-output-details" open' not in body
    assert "case-output-detail-body" in body
    assert "case-output-summary" in body
    assert "case-step-index" in body
    assert "case-entity-head" in body
    assert "case-detail-scroll" in body
    assert "syncCaseDetailViewport" in body
    assert "requestCaseDetailViewportSync" in body
    assert "visualViewport" in body
    assert "Preview Import" in body
    assert "Confirm Import" in body
    assert 'data-case-confirm-import="${html(caseState.selectedCaseId)}" ${!detail || busy ? "disabled" : ""}' in body
    assert '!detail || !caseState.preview || busy ? "disabled" : ""' not in body
    assert "caseState.isDetailOpen = false;" in body
    assert "data-case-skill-preview" in body
    assert "openCaseSkillContent" in body
    assert "data-case-id" in body
    assert "data-case-preview-import" in body
    assert "data-case-confirm-import" in body
    assert "Case Carousel / 案例轮播" in body
    assert "Import Preview / 导入预览" in body
    assert "CASE_IMPORT_PROGRESS_STAGES" in body
    assert "startCaseImportProgress" in body
    assert "stopCaseImportProgress" in body
    assert "updateBusyActionProgress" in body
    assert "Invoking LLM to create SOUL.md and AGENTS.md" in body
    assert "Creating Docker Container" in body
    assert "Finalizing case import" in body
    assert "Case imported" in body
    assert "busy-progress" in body
    assert "role=\"progressbar\"" in body
    assert "aria-valuenow" in body
    assert "stopCaseImportProgress();" in body
    assert 't("button.show_more"' in body
    assert "renderEmployeeDetailToggle(detailSections.length)" in body
    assert "frontend only" not in body


@pytest.mark.skipif(not HAS_AIOHTTP, reason="aiohttp not installed")
@pytest.mark.asyncio
async def test_admin_css_keeps_scrolled_modal_close_buttons_outside_scroll(aiohttp_client) -> None:
    app = create_app(_make_admin_agent(), model_name="test-model")
    client = await aiohttp_client(app)

    resp = await client.get("/admin/assets/admin.css")

    assert resp.status == 200
    body = await resp.text()
    assert ".case-card-track" in body
    assert ".case-detail-modal" in body
    assert ".case-modal-backdrop" in body
    assert ".case-detail-head" in body
    assert ".case-dossier-hero" in body
    assert ".case-dossier-stats" in body
    assert ".case-section-title" in body
    assert ".case-io-grid" in body
    assert ".case-output-details" in body
    assert ".case-output-detail-body" in body
    assert ".case-output-summary" in body
    assert ".case-step-index" in body
    assert ".case-entity-head" in body
    assert ".case-detail-scroll" in body
    assert ".case-import-preview" in body
    assert ".batch-checkbox" in body
    assert ".batch-delete-button" in body
    assert ".batch-export-button" in body
    assert ".employee-export-form" in body
    assert ".employee-export-preview" in body
    assert ".docker-agent-card-top" in body
    assert ".docker-agent-card-actions" in body
    assert ".docker-daemon-alert" in body
    assert ".docker-daemon-alert-actions" in body
    assert ".docker-daemon-repair-button" in body
    assert ".create-wizard-stepper" in body
    assert ".create-wizard-step" in body
    assert ".create-wizard-body" in body
    assert ".create-wizard-footer" in body
    assert ".create-wizard-error" in body
    assert ".employee-review-grid" in body
    assert ".employee-ops-workbench" in body
    assert ".employee-ops-summary" in body
    assert ".employee-ops-actions" in body
    assert ".employee-ops-action" in body
    assert ".employee-ops-diagnostics" in body
    assert ".employee-ops-diagnostic" in body
    assert ".employee-ops-metric" in body
    assert ".transcript-modal-shell" in body
    assert ".transcript-modal-close" in body
    assert ".skill-content-modal-shell" in body
    assert ".skill-content-modal-close" in body
    assert ".case-ops-panel" in body
    assert ".case-ops-summary" in body
    assert ".case-ops-issue-list" in body
    assert ".case-ops-preview" in body
    assert ".case-ops-audit" in body
    assert ".case-catalog-grid" in body
    assert ".skill-ops-panel" in body
    assert ".skill-ops-head" in body
    assert ".skill-ops-summary" in body
    assert ".skill-ops-metrics" in body
    assert ".skill-ops-grid" in body
    assert ".skill-ops-issue" in body
    assert "grid-template-columns: auto minmax(0, 1fr) auto" in body
    assert ".skill-ops-bulk-actions" in body
    assert ".skill-ops-select-all" in body
    assert ".skill-ops-fold-summary" in body
    assert ".skill-ops-fold-toggle" in body
    assert ".skill-ops-actions" in body
    assert ".skill-ops-preview" in body
    assert ".skill-ops-opportunity" in body
    assert ".agent-skills-grid" in body
    assert ".agent-skill-detail-panel" in body
    assert ".agent-skill-editor" in body
    assert ".agent-skill-proposal-card" in body
    assert ".agent-skill-file-form" in body
    assert ".dream-panel" in body
    assert ".dream-summary" in body
    assert ".dream-workbench" in body
    assert ".dream-subject-card" in body
    assert ".dream-detail-grid" in body
    assert ".dream-file-preview" in body
    assert ".dream-diff-preview" in body
    assert ".skill-card-label-cloud" in body
    assert ".skill-card-label-cloud.is-collapsed" in body
    assert ".skill-card-label-cloud.is-expanded" in body
    assert ".skill-card-label-toggle" in body
    assert ".admin-preferences" in body
    assert ".hero-command-bar" in body
    assert ".hero-runtime-summary" in body
    assert ".runtime-timeline-panel" in body
    assert ".runtime-timeline-head" in body
    assert ".runtime-trend-grid" in body
    assert ".runtime-trend-card" in body
    assert ".runtime-sparkline" in body
    assert ".runtime-status-strip" in body
    assert ".section-shell" in body
    assert ".nav-anchor-section" in body
    assert ".control-center-grid" in body
    assert ".employee-studio-head" in body
    assert ".resource-hub-tabs" in body
    assert ".resource-hub-tab" in body
    assert ".resource-hub-panel[hidden]" in body
    assert ".resource-panel-shell" in body
    assert ".alert-strip" in body
    assert ".alert-chip" in body
    assert ".action-center" in body
    assert ".action-center-head" in body
    assert ".action-card-grid" in body
    assert ".action-card" in body
    assert ".action-card.is-warning" in body
    assert ".action-card.is-danger" in body
    assert ".action-card-actions" in body
    assert ".action-card-button" in body
    assert ".nav-section-link" in body
    assert ".nav-section-link.is-active" in body
    assert '.nav-section-link[aria-current="true"]' in body
    assert "grid-template-columns: 264px minmax(0, 1fr)" in body
    assert ".admin-brand {\n  margin: 0;" in body
    assert "font-size: 24px" in body
    assert ".admin-nav-note {\n  margin-top: auto" in body
    assert "border-radius: 8px" in body
    assert "background: var(--surface-soft)" in body
    assert 'html[data-theme="light"] .nav-section-link.is-active' in body
    assert "grid-template-columns: repeat(auto-fit, minmax(150px, 1fr))" in body
    assert "@media (max-width: 560px)" in body
    assert ".nav-icon-button" in body
    assert ".nav-icon-link" in body
    assert ".language-button-group" in body
    assert ".preference-button" in body
    assert "color-scheme: light" in body
    assert "color-scheme: dark" in body
    assert 'html[data-theme="dark"]' in body
    assert 'html[data-theme="dark"] .case-detail-block' in body
    assert "100dvh" in body
    assert "100dvw" in body
    assert "--case-modal-height" in body
    assert "height: var(--case-modal-height" in body
    assert "flex: 1 1 auto" in body
    assert ".case-detail-modal > .modal-actions" in body
    assert "@media (max-height: 820px), (max-width: 900px)" in body
    assert "overscroll-behavior: contain" in body
    assert "width: clamp(260px, 46vw, 520px)" in body
    assert "scroll-behavior: smooth" in body
    assert "scroll-margin-top" in body
    assert "position: sticky" in body
    assert "height: 100vh" in body
    assert "overflow-y: auto" in body
    assert "@media (max-width: 980px)" in body
    assert "right: -52px" in body
    assert "pointer-events: none" in body
    assert "position: static" in body
    assert "height: auto" in body
    assert "overflow: visible" in body


@pytest.mark.skipif(not HAS_AIOHTTP, reason="aiohttp not installed")
@pytest.mark.asyncio
async def test_admin_css_collapses_employee_detail_long_sections(aiohttp_client) -> None:
    app = create_app(_make_admin_agent(), model_name="test-model")
    client = await aiohttp_client(app)

    resp = await client.get("/admin/assets/admin.css")

    assert resp.status == 200
    body = await resp.text()
    assert ".employee-detail-toggle" in body
    assert ".employee-summary.is-collapsed" in body
    assert "-webkit-line-clamp: 3" in body


class _FakeRuntimeMonitor:
    def __init__(self) -> None:
        self.version = 0
        self._changes_sent = 0
        self._block_forever = asyncio.Event()

    async def wait_for_change(self, version: int, timeout: float = 15.0) -> int:
        if self._changes_sent == 0:
            self._changes_sent += 1
            self.version = version + 1
            return self.version
        await self._block_forever.wait()
        return self.version


@pytest.mark.skipif(not HAS_AIOHTTP, reason="aiohttp not installed")
@pytest.mark.asyncio
async def test_admin_events_streams_subsequent_runtime_changes(aiohttp_client) -> None:
    agent = _make_admin_agent()
    agent.runtime_monitor = _FakeRuntimeMonitor()
    counter = 0

    async def snapshot(*, process_role: str = "api"):
        nonlocal counter
        counter += 1
        return {
            "generatedAt": f"snapshot-{counter}",
            "process": {"role": process_role, "pid": 123, "workspace": "/workspace", "uptimeSeconds": 5},
            "mainAgent": {"status": "idle", "model": "test-model", "context": {}, "lastUsage": {}},
            "subagents": [],
            "dockerDaemon": {
                "status": "running",
                "ok": True,
                "message": "Docker daemon is reachable.",
                "version": "test",
            },
            "dockerContainers": [],
            "dockerAgents": [],
        }

    agent.get_admin_snapshot = AsyncMock(side_effect=snapshot)
    app = create_app(agent, model_name="test-model")
    client = await aiohttp_client(app)

    resp = await client.get("/admin/api/events")

    assert resp.status == 200
    lines = []
    for _ in range(6):
        lines.append((await asyncio.wait_for(resp.content.readline(), timeout=2)).decode("utf-8"))
    resp.close()
    body = "".join(lines)
    assert body.count("event: runtime") == 2
    assert '"generatedAt": "snapshot-1"' in body
    assert '"generatedAt": "snapshot-2"' in body


@pytest.mark.skipif(not HAS_AIOHTTP, reason="aiohttp not installed")
@pytest.mark.asyncio
async def test_admin_events_once_returns_sse_runtime_event(aiohttp_client) -> None:
    app = create_app(_make_admin_agent(), model_name="test-model")
    client = await aiohttp_client(app)

    resp = await client.get("/admin/api/events?once=1")

    assert resp.status == 200
    body = await resp.text()
    assert "event: runtime" in body
    assert "data:" in body


@pytest.mark.skipif(not HAS_AIOHTTP, reason="aiohttp not installed")
@pytest.mark.asyncio
async def test_admin_clear_context_endpoint_calls_agent(aiohttp_client) -> None:
    agent = _make_admin_agent()
    app = create_app(agent, model_name="test-model")
    client = await aiohttp_client(app)

    resp = await client.post("/admin/api/context/clear", json={"session_key": "api:default"})

    assert resp.status == 200
    body = await resp.json()
    assert body["sessionKey"] == "api:default"
    assert body["clearedMessages"] == 3
    agent.clear_admin_context.assert_awaited_once_with("api:default")


@pytest.mark.skipif(not HAS_AIOHTTP, reason="aiohttp not installed")
@pytest.mark.asyncio
async def test_admin_compact_context_endpoint_calls_agent(aiohttp_client) -> None:
    agent = _make_admin_agent()
    app = create_app(agent, model_name="test-model")
    client = await aiohttp_client(app)

    resp = await client.post("/admin/api/context/compact", json={"session_key": "api:default"})

    assert resp.status == 200
    body = await resp.json()
    assert body["sessionKey"] == "api:default"
    assert body["archivedMessages"] == 4
    agent.compact_admin_context.assert_awaited_once_with("api:default")


def _create_employee_session(tmp_path, entry, *, turns: int = 2, session_key: str | None = None) -> str:
    employee_workspace = employee_workspace_path(tmp_path, entry)
    sessions = SessionManager(employee_workspace)
    key = session_key or f"openhire-delegate-{entry.container_name}"
    session = sessions.get_or_create(key)
    for idx in range(turns):
        session.add_message("user", f"employee request {idx}")
        session.add_message("assistant", f"employee response {idx}")
    sessions.save(session)
    return key


def _openclaw_session_jsonl(container_name: str, *, turns: int = 2) -> str:
    session_key = f"openhire-delegate-{container_name}"
    rows = [
        {
            "type": "session",
            "id": session_key,
            "timestamp": "2026-04-21T12:00:00Z",
        }
    ]
    for index in range(turns):
        rows.append({
            "type": "message",
            "timestamp": f"2026-04-21T12:00:{index * 2 + 1:02d}Z",
            "message": {
                "role": "user",
                "content": [{"type": "text", "text": f"openclaw request {index}"}],
            },
        })
        rows.append({
            "type": "message",
            "timestamp": f"2026-04-21T12:00:{index * 2 + 2:02d}Z",
            "message": {
                "role": "assistant",
                "content": [{"type": "text", "text": f"openclaw response {index}"}],
            },
        })
    return "\n".join(json.dumps(row, ensure_ascii=False) for row in rows) + "\n"


@pytest.mark.skipif(not HAS_AIOHTTP, reason="aiohttp not installed")
@pytest.mark.asyncio
async def test_admin_employee_context_clear_endpoint_clears_employee_workspace_session(aiohttp_client, tmp_path) -> None:
    app = create_app(_make_admin_agent(), model_name="test-model", workspace=tmp_path)
    entry = app["employee_registry"].register(
        AgentEntry(name="Context Worker", role="Ops", agent_type="nanobot")
    )
    session_key = _create_employee_session(tmp_path, entry, turns=2)
    client = await aiohttp_client(app)

    resp = await client.post(f"/admin/api/employees/{entry.agent_id}/context/clear")

    assert resp.status == 200
    body = await resp.json()
    assert body["employeeId"] == entry.agent_id
    assert body["sessionKey"] == session_key
    assert body["clearedMessages"] == 4
    assert body["context"]["usedTokens"] == 0
    assert body["context"]["source"] == "cleared"
    refreshed = SessionManager(employee_workspace_path(tmp_path, entry)).get_or_create(session_key)
    assert refreshed.messages == []


@pytest.mark.skipif(not HAS_AIOHTTP, reason="aiohttp not installed")
@pytest.mark.asyncio
async def test_admin_employee_context_clear_endpoint_clears_openclaw_container_session(
    aiohttp_client,
    tmp_path,
    monkeypatch,
) -> None:
    agent = _make_admin_agent()
    monitor = RuntimeMonitor(
        process_role="gateway",
        workspace=str(tmp_path),
        model="test-model",
        context_window_tokens=1000,
    )
    agent.runtime_monitor = monitor
    app = create_app(agent, model_name="test-model", workspace=tmp_path)
    entry = app["employee_registry"].register(
        AgentEntry(name="OpenClaw Clear", role="Ops", agent_type="openclaw")
    )
    monitor.update_docker_snapshot([
        {
            "name": entry.container_name,
            "containerName": entry.container_name,
            "image": "openhire-openclaw:latest",
            "status": "running",
        }
    ])
    stored = {"raw": _openclaw_session_jsonl(entry.container_name, turns=2)}

    async def fake_docker_exec(container_name: str, *args, timeout: float = 2.5) -> str:
        assert container_name == entry.container_name
        return stored["raw"]

    async def fake_docker_write(container_name: str, path: str, content: str, timeout: float = 2.5) -> None:
        assert container_name == entry.container_name
        assert path.endswith(f"openhire-delegate-{entry.container_name}.jsonl")
        stored["raw"] = content

    monkeypatch.setattr(employee_context_module, "_docker_exec_text", fake_docker_exec)
    monkeypatch.setattr(employee_context_module, "_docker_write_text", fake_docker_write)
    client = await aiohttp_client(app)

    resp = await client.post(f"/admin/api/employees/{entry.agent_id}/context/clear")

    assert resp.status == 200
    body = await resp.json()
    assert body["sessionKey"] == f"openhire-delegate-{entry.container_name}"
    assert body["clearedMessages"] == 4
    assert body["context"]["source"] == "cleared"
    assert '"type": "session"' in stored["raw"]
    assert '"type": "message"' not in stored["raw"]


@pytest.mark.skipif(not HAS_AIOHTTP, reason="aiohttp not installed")
@pytest.mark.asyncio
async def test_admin_employee_context_compact_endpoint_archives_employee_history(aiohttp_client, tmp_path) -> None:
    app = create_app(_make_admin_agent(), model_name="test-model", workspace=tmp_path)
    entry = app["employee_registry"].register(
        AgentEntry(name="Compact Worker", role="Ops", agent_type="nanobot")
    )
    session_key = _create_employee_session(tmp_path, entry, turns=6)
    client = await aiohttp_client(app)

    resp = await client.post(f"/admin/api/employees/{entry.agent_id}/context/compact")

    assert resp.status == 200
    body = await resp.json()
    assert body["employeeId"] == entry.agent_id
    assert body["sessionKey"] == session_key
    assert body["archivedMessages"] > 0
    assert body["keptMessages"] >= 1
    assert body["summaryCreated"] is True
    store = MemoryStore(employee_workspace_path(tmp_path, entry))
    entries = store.read_unprocessed_history(since_cursor=0)
    assert entries
    assert "压缩摘要" in entries[-1]["content"]


@pytest.mark.skipif(not HAS_AIOHTTP, reason="aiohttp not installed")
@pytest.mark.asyncio
async def test_admin_employee_context_endpoint_validates_missing_and_busy(aiohttp_client, tmp_path) -> None:
    agent = _make_admin_agent()
    monitor = RuntimeMonitor(
        process_role="gateway",
        workspace=str(tmp_path),
        model="test-model",
        context_window_tokens=1000,
    )
    agent.runtime_monitor = monitor
    app = create_app(agent, model_name="test-model", workspace=tmp_path)
    entry = app["employee_registry"].register(
        AgentEntry(name="Busy Worker", role="Ops", agent_type="nanobot")
    )
    _create_employee_session(tmp_path, entry, turns=1)
    monitor.update_docker_snapshot([
        {"name": entry.container_name, "containerName": entry.container_name, "status": "processing"}
    ])
    client = await aiohttp_client(app)

    unknown = await client.post("/admin/api/employees/missing/context/clear")
    busy = await client.post(f"/admin/api/employees/{entry.agent_id}/context/clear")

    assert unknown.status == 404
    assert busy.status == 409


@pytest.mark.skipif(not HAS_AIOHTTP, reason="aiohttp not installed")
@pytest.mark.asyncio
async def test_admin_employee_context_endpoint_requires_existing_session(aiohttp_client, tmp_path) -> None:
    app = create_app(_make_admin_agent(), model_name="test-model", workspace=tmp_path)
    entry = app["employee_registry"].register(
        AgentEntry(name="No Session Worker", role="Ops", agent_type="nanobot")
    )
    client = await aiohttp_client(app)

    resp = await client.post(f"/admin/api/employees/{entry.agent_id}/context/compact")

    assert resp.status == 400


@pytest.mark.skipif(not HAS_AIOHTTP, reason="aiohttp not installed")
@pytest.mark.asyncio
async def test_admin_repair_docker_daemon_endpoint_calls_repair(aiohttp_client, monkeypatch) -> None:
    async def fake_repair_docker_daemon():
        return {
            "attempted": True,
            "command": ["open", "-a", "Docker"],
            "message": "Docker daemon is reachable.",
            "dockerDaemon": {
                "status": "running",
                "ok": True,
                "message": "Docker daemon is reachable.",
                "version": "test",
            },
        }

    monkeypatch.setattr("openhire.api.server.repair_docker_daemon", fake_repair_docker_daemon)

    app = create_app(_make_admin_agent(), model_name="test-model")
    client = await aiohttp_client(app)

    resp = await client.post("/admin/api/docker-daemon/repair")

    assert resp.status == 200
    body = await resp.json()
    assert body["attempted"] is True
    assert body["command"] == ["open", "-a", "Docker"]
    assert body["dockerDaemon"]["ok"] is True


@pytest.mark.skipif(not HAS_AIOHTTP, reason="aiohttp not installed")
@pytest.mark.asyncio
async def test_admin_delete_docker_endpoint_calls_agent(aiohttp_client) -> None:
    agent = _make_admin_agent()
    app = create_app(agent, model_name="test-model")
    client = await aiohttp_client(app)

    resp = await client.delete("/admin/api/docker-containers/nanobot-3")

    assert resp.status == 200
    body = await resp.json()
    assert body["containerName"] == "nanobot-3"
    assert body["deleted"] is True
    agent.delete_admin_container.assert_awaited_once_with("nanobot-3")
