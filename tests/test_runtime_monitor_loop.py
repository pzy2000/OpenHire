from __future__ import annotations

import asyncio
import json
from types import SimpleNamespace
from unittest.mock import AsyncMock, MagicMock

import pytest

from openhire.agent.loop import AgentLoop
from openhire.bus.queue import MessageBus
from openhire.channels.feishu import FEISHU_AVAILABLE, FeishuChannel, FeishuConfig
from openhire.providers.base import GenerationSettings, LLMResponse


@pytest.mark.asyncio
async def test_process_direct_reports_processing_and_live_context(tmp_path) -> None:
    provider = MagicMock()
    provider.get_default_model.return_value = "test-model"
    provider.generation = GenerationSettings(max_tokens=0)
    provider.estimate_prompt_tokens.return_value = (320, "test-counter")
    started = asyncio.Event()
    release = asyncio.Event()

    async def slow_chat_with_retry(**_kwargs):
        started.set()
        await release.wait()
        return LLMResponse(
            content="ok",
            tool_calls=[],
            usage={"prompt_tokens": 320, "completion_tokens": 5},
        )

    provider.chat_with_retry = slow_chat_with_retry
    provider.chat_stream_with_retry = AsyncMock()

    loop = AgentLoop(
        bus=MessageBus(),
        provider=provider,
        workspace=tmp_path,
        model="test-model",
        context_window_tokens=1000,
    )

    task = asyncio.create_task(
        loop.process_direct("hello", session_key="api:test", channel="api", chat_id="default")
    )
    await asyncio.wait_for(started.wait(), timeout=2)

    snapshot = await loop.get_admin_snapshot(process_role="api")
    assert snapshot["mainAgent"]["status"] == "processing"
    assert snapshot["mainAgent"]["sessionKey"] == "api:test"
    assert snapshot["mainAgent"]["context"]["usedTokens"] == 320
    assert snapshot["mainAgent"]["context"]["percent"] == 32

    release.set()
    await task
    snapshot = await loop.get_admin_snapshot(process_role="api")
    assert snapshot["mainAgent"]["status"] == "idle"
    assert snapshot["mainAgent"]["context"]["usedTokens"] == 320


def _make_provider(started: asyncio.Event, release: asyncio.Event):
    provider = MagicMock()
    provider.get_default_model.return_value = "test-model"
    provider.generation = GenerationSettings(max_tokens=0)
    provider.estimate_prompt_tokens.return_value = (280, "test-counter")

    async def slow_chat_with_retry(**_kwargs):
        started.set()
        await release.wait()
        return LLMResponse(
            content="feishu ok",
            tool_calls=[],
            usage={"prompt_tokens": 280, "completion_tokens": 9},
        )

    provider.chat_with_retry = slow_chat_with_retry
    provider.chat_stream_with_retry = AsyncMock()
    return provider


def _make_feishu_event() -> SimpleNamespace:
    message = SimpleNamespace(
        message_id="om_runtime_001",
        chat_id="oc_runtime_chat",
        chat_type="group",
        message_type="text",
        content=json.dumps({"text": "请检查实时监控"}),
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


@pytest.mark.skipif(not FEISHU_AVAILABLE, reason="Feishu dependencies not installed")
@pytest.mark.asyncio
async def test_feishu_message_updates_main_agent_runtime_monitor(tmp_path) -> None:
    bus = MessageBus()
    started = asyncio.Event()
    release = asyncio.Event()
    loop = AgentLoop(
        bus=bus,
        provider=_make_provider(started, release),
        workspace=tmp_path,
        model="test-model",
        context_window_tokens=1000,
    )
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
    channel._client = None

    runner = asyncio.create_task(loop.run())
    try:
        await channel._on_message(_make_feishu_event())
        await asyncio.wait_for(started.wait(), timeout=2)

        snapshot = await loop.get_admin_snapshot(process_role="gateway")
        assert snapshot["mainAgent"]["status"] == "processing"
        assert snapshot["mainAgent"]["sessionKey"] == "feishu:oc_runtime_chat"
        assert snapshot["mainAgent"]["channel"] == "feishu"
        assert snapshot["mainAgent"]["chatId"] == "oc_runtime_chat"
        assert snapshot["mainAgent"]["context"]["usedTokens"] == 280

        release.set()
        outbound = await asyncio.wait_for(bus.consume_outbound(), timeout=2)
        assert outbound.channel == "feishu"
        assert outbound.chat_id == "oc_runtime_chat"
        assert outbound.content == "feishu ok"

        snapshot = await loop.get_admin_snapshot(process_role="gateway")
        assert snapshot["mainAgent"]["status"] == "idle"
        assert snapshot["mainAgent"]["lastSessionKey"] == "feishu:oc_runtime_chat"
        assert snapshot["mainAgent"]["context"]["usedTokens"] == 280
    finally:
        loop.stop()
        runner.cancel()
        with pytest.raises(asyncio.CancelledError):
            await runner
