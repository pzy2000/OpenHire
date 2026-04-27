from __future__ import annotations

import asyncio
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import AsyncMock, MagicMock

import pytest
import pytest_asyncio

from openhire.admin import transcripts
from openhire.session.manager import SessionManager

try:
    from aiohttp.test_utils import TestClient, TestServer

    HAS_AIOHTTP = True
except ImportError:
    HAS_AIOHTTP = False


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


def _make_loop(tmp_path: Path):
    sessions = SessionManager(tmp_path)
    return SimpleNamespace(
        sessions=sessions,
        _last_admin_session_key=None,
    )


@pytest.mark.asyncio
async def test_main_transcript_reads_persisted_session_messages(tmp_path: Path) -> None:
    loop = _make_loop(tmp_path)
    session = loop.sessions.get_or_create("feishu:chat")
    session.add_message("user", "hello")
    session.messages.append(
        {
            "role": "assistant",
            "content": "",
            "tool_calls": [
                {
                    "id": "call_1",
                    "type": "function",
                    "function": {"name": "read_file", "arguments": '{"path":"README.md"}'},
                }
            ],
            "timestamp": "2026-04-21T12:00:00",
        }
    )
    session.messages.append(
        {
            "role": "tool",
            "name": "read_file",
            "tool_call_id": "call_1",
            "content": "file contents",
            "timestamp": "2026-04-21T12:00:01",
        }
    )
    loop.sessions.save(session)
    loop._last_admin_session_key = "feishu:chat"

    payload = await transcripts.build_main_transcript(loop, limit=10)

    assert payload["agent"] == "Main Agent"
    assert payload["source"] == "openhire-session"
    assert payload["sessionId"] == "feishu:chat"
    assert [item["role"] for item in payload["items"]] == ["user", "assistant", "tool"]
    assert payload["items"][1]["summary"] == "1 tool call: read_file"
    assert "README.md" in payload["items"][1]["detail"]
    assert payload["items"][2]["summary"] == "read_file result"


@pytest.mark.asyncio
async def test_main_transcript_returns_empty_when_no_session(tmp_path: Path) -> None:
    loop = _make_loop(tmp_path)

    payload = await transcripts.build_main_transcript(loop, limit=10)

    assert payload["status"] == "empty"
    assert payload["sessionId"] is None
    assert payload["items"] == []


@pytest.mark.asyncio
async def test_openclaw_docker_transcript_parses_container_jsonl(monkeypatch) -> None:
    raw = "\n".join(
        [
            '{"type":"session","id":"openhire-delegate-openhire-abc","timestamp":"2026-04-21T12:00:00Z"}',
            '{"type":"message","timestamp":"2026-04-21T12:00:01Z","message":{"role":"user","content":[{"type":"text","text":"run task"}]}}',
            '{"type":"message","timestamp":"2026-04-21T12:00:02Z","message":{"role":"assistant","content":[{"type":"tool_call","id":"tool1","name":"terminal","arguments":{"cmd":"pytest"}}]}}',
            '{"type":"message","timestamp":"2026-04-21T12:00:03Z","message":{"role":"toolResult","toolName":"terminal","content":[{"type":"text","text":"passed"}]}}',
        ]
    )
    calls: list[tuple[str, tuple[str, ...]]] = []

    async def fake_docker_exec(container_name: str, *args: str, timeout: float = 2.0) -> str:
        calls.append((container_name, args))
        return raw

    monkeypatch.setattr(transcripts, "_docker_exec_text", fake_docker_exec)

    payload = await transcripts.build_docker_transcript(
        {"name": "openhire-abc", "image": "openhire-openclaw:latest"},
        limit=20,
    )

    assert calls[0][0] == "openhire-abc"
    assert "/home/node/.openclaw/agents/main/sessions/openhire-delegate-openhire-abc.jsonl" in " ".join(calls[0][1])
    assert payload["agent"] == "openhire-abc"
    assert payload["source"] == "openclaw-container"
    assert payload["sessionId"] == "openhire-delegate-openhire-abc"
    assert [item["role"] for item in payload["items"]] == ["user", "assistant", "tool"]
    assert payload["items"][1]["summary"] == "1 tool call: terminal"


@pytest.mark.asyncio
async def test_docker_transcript_timeout_is_typed(monkeypatch) -> None:
    async def fake_docker_exec(*_args, **_kwargs) -> str:
        raise asyncio.TimeoutError

    monkeypatch.setattr(transcripts, "_docker_exec_text", fake_docker_exec)

    with pytest.raises(transcripts.DockerTranscriptTimeout):
        await transcripts.build_docker_transcript(
            {"name": "openhire-abc", "image": "openhire-openclaw:latest"},
            limit=20,
        )


@pytest.mark.skipif(not HAS_AIOHTTP, reason="aiohttp not installed")
@pytest.mark.asyncio
async def test_admin_transcript_routes_return_main_and_unknown_docker(aiohttp_client, tmp_path: Path) -> None:
    from openhire.api.server import create_app

    agent = MagicMock()
    agent.runtime_monitor = None
    agent.process_direct = AsyncMock(return_value="ok")
    agent.clear_admin_context = AsyncMock()
    agent.compact_admin_context = AsyncMock()
    agent.delete_admin_container = AsyncMock()
    agent.get_admin_snapshot = AsyncMock(
        return_value={
            "generatedAt": "now",
            "process": {"role": "api", "pid": 1, "workspace": str(tmp_path), "uptimeSeconds": 1},
            "mainAgent": {"status": "idle", "context": {}, "lastUsage": {}},
            "subagents": [],
            "dockerContainers": [{"name": "openhire-known", "image": "openhire-openclaw:latest"}],
            "dockerAgents": [],
        }
    )
    agent.sessions = SessionManager(tmp_path)
    session = agent.sessions.get_or_create("api:default")
    session.add_message("user", "hi")
    agent.sessions.save(session)
    agent._last_admin_session_key = "api:default"
    agent._connect_mcp = AsyncMock()
    agent.close_mcp = AsyncMock()

    app = create_app(agent, model_name="test-model", workspace=tmp_path)
    client = await aiohttp_client(app)

    main_resp = await client.get("/admin/api/transcripts/main")
    assert main_resp.status == 200
    main_body = await main_resp.json()
    assert main_body["sessionId"] == "api:default"
    assert main_body["items"][0]["content"] == "hi"

    missing_resp = await client.get("/admin/api/transcripts/docker/openhire-missing")
    assert missing_resp.status == 404
