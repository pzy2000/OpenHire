from __future__ import annotations

from unittest.mock import AsyncMock, MagicMock

import pytest

from openhire.agent.loop import AgentLoop
from openhire.bus.queue import MessageBus
from openhire.providers.base import GenerationSettings, LLMResponse


def _make_provider() -> MagicMock:
    provider = MagicMock()
    provider.get_default_model.return_value = "test-model"
    provider.generation = GenerationSettings(max_tokens=0)
    provider.estimate_prompt_tokens.return_value = (320, "test-counter")
    provider.chat_with_retry = AsyncMock(return_value=LLMResponse(content="压缩摘要", tool_calls=[]))
    provider.chat_stream_with_retry = MagicMock()
    return provider


@pytest.mark.asyncio
async def test_clear_admin_context_removes_all_session_messages(tmp_path) -> None:
    loop = AgentLoop(
        bus=MessageBus(),
        provider=_make_provider(),
        workspace=tmp_path,
        model="test-model",
        context_window_tokens=1000,
    )
    session = loop.sessions.get_or_create("api:test")
    session.add_message("user", "hello")
    session.add_message("assistant", "world")
    loop.sessions.save(session)

    result = await loop.clear_admin_context("api:test")
    refreshed = loop.sessions.get_or_create("api:test")

    assert result["sessionKey"] == "api:test"
    assert result["clearedMessages"] == 2
    assert refreshed.messages == []
    assert refreshed.last_consolidated == 0


@pytest.mark.asyncio
async def test_compact_admin_context_archives_prefix_and_keeps_recent_suffix(tmp_path) -> None:
    provider = _make_provider()
    loop = AgentLoop(
        bus=MessageBus(),
        provider=provider,
        workspace=tmp_path,
        model="test-model",
        context_window_tokens=1000,
    )
    session = loop.sessions.get_or_create("api:test")
    for idx in range(12):
        session.add_message("user", f"user-{idx}")
        session.add_message("assistant", f"assistant-{idx}")
    loop.sessions.save(session)

    result = await loop.compact_admin_context("api:test")
    refreshed = loop.sessions.get_or_create("api:test")

    assert result["sessionKey"] == "api:test"
    assert result["archivedMessages"] > 0
    assert result["keptMessages"] > 0
    assert len(refreshed.messages) == result["keptMessages"]
    assert len(refreshed.messages) < 24
    assert refreshed.metadata["_last_summary"]["text"] == "压缩摘要"


@pytest.mark.asyncio
async def test_delete_admin_container_removes_existing_container(tmp_path, monkeypatch) -> None:
    loop = AgentLoop(
        bus=MessageBus(),
        provider=_make_provider(),
        workspace=tmp_path,
        model="test-model",
        context_window_tokens=1000,
    )

    proc = AsyncMock()
    proc.communicate.return_value = (b"", b"")
    proc.returncode = 0

    monkeypatch.setattr("openhire.agent.loop.inspect_container_status", AsyncMock(return_value="running"))
    monkeypatch.setattr("asyncio.create_subprocess_exec", AsyncMock(return_value=proc))

    result = await loop.delete_admin_container("nanobot-3")

    assert result == {"containerName": "nanobot-3", "deleted": True}


@pytest.mark.asyncio
async def test_delete_admin_container_rejects_missing_container(tmp_path, monkeypatch) -> None:
    loop = AgentLoop(
        bus=MessageBus(),
        provider=_make_provider(),
        workspace=tmp_path,
        model="test-model",
        context_window_tokens=1000,
    )

    monkeypatch.setattr("openhire.agent.loop.inspect_container_status", AsyncMock(return_value=None))

    with pytest.raises(ValueError, match="not found"):
        await loop.delete_admin_container("missing")
