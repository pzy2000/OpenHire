from __future__ import annotations

import os
from unittest.mock import AsyncMock, MagicMock, patch

import pytest
import pytest_asyncio
import typer

from openhire.admin.demo_mode import (
    MODELSCOPE_DEMO_API_BASE,
    MODELSCOPE_DEMO_API_KEY_ENV_KEYS,
    MODELSCOPE_DEMO_MODEL,
    apply_modelscope_demo_config_overlay,
)
from openhire.api.server import create_app as _create_app
from openhire.cli.commands import _load_runtime_config, _make_provider
from openhire.config.schema import Config

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


def _base_config() -> Config:
    config = Config()
    config.agents.defaults.provider = "ollama"
    config.agents.defaults.model = "ollama/llama3.2"
    return config


def _clear_modelscope_env(monkeypatch: pytest.MonkeyPatch) -> None:
    for key in list(os.environ):
        if key.startswith("MODELSCOPE_") or key in {
            "OPENHIRE_DEMO_MODE",
            "OPENHIRE_DEPLOY_TARGET",
            "OPENHIRE_MODELSCOPE_API_KEY",
            "MODEL_SCOPE_ENV",
            "MODEL_SCOPE_TOKEN",
            "SPACE_ID",
            "STUDIO_ID",
            "WORK_SPACE",
            "PROJECT_DIR",
        }:
            monkeypatch.delenv(key, raising=False)


def test_modelscope_demo_overlay_uses_modelscope_deepseek() -> None:
    config = _base_config()

    applied = apply_modelscope_demo_config_overlay(
        config,
        environ={
            "OPENHIRE_DEPLOY_TARGET": "modelscope",
            "OPENHIRE_MODELSCOPE_API_KEY": "test-ms-token",
        },
    )

    assert applied is True
    assert config.agents.defaults.provider == "deepseek"
    assert config.agents.defaults.model == MODELSCOPE_DEMO_MODEL
    assert config.providers.deepseek.api_key == "test-ms-token"
    assert config.providers.deepseek.api_base == MODELSCOPE_DEMO_API_BASE
    assert config.get_provider_name() == "deepseek"
    assert config.get_api_base() == MODELSCOPE_DEMO_API_BASE


def test_modelscope_demo_overlay_respects_explicit_demo_disable() -> None:
    config = _base_config()

    applied = apply_modelscope_demo_config_overlay(
        config,
        environ={
            "OPENHIRE_DEMO_MODE": "0",
            "OPENHIRE_DEPLOY_TARGET": "modelscope",
            "OPENHIRE_MODELSCOPE_API_KEY": "test-ms-token",
        },
    )

    assert applied is False
    assert config.agents.defaults.provider == "ollama"
    assert config.agents.defaults.model == "ollama/llama3.2"


def test_modelscope_demo_overlay_skips_local_forced_demo_without_deploy_marker() -> None:
    config = _base_config()

    applied = apply_modelscope_demo_config_overlay(
        config,
        environ={
            "OPENHIRE_DEMO_MODE": "1",
            "OPENHIRE_MODELSCOPE_API_KEY": "test-ms-token",
        },
    )

    assert applied is False
    assert config.agents.defaults.provider == "ollama"
    assert config.agents.defaults.model == "ollama/llama3.2"


def test_modelscope_demo_overlay_requires_token_for_hosted_demo() -> None:
    config = _base_config()

    with pytest.raises(ValueError) as exc_info:
        apply_modelscope_demo_config_overlay(
            config,
            environ={"OPENHIRE_DEPLOY_TARGET": "modelscope"},
        )

    message = str(exc_info.value)
    for key in MODELSCOPE_DEMO_API_KEY_ENV_KEYS:
        assert key in message
    assert config.agents.defaults.provider == "ollama"
    assert config.agents.defaults.model == "ollama/llama3.2"


def test_load_runtime_config_applies_modelscope_demo_overlay(monkeypatch) -> None:
    _clear_modelscope_env(monkeypatch)
    monkeypatch.setenv("OPENHIRE_DEPLOY_TARGET", "modelscope")
    monkeypatch.setenv("OPENHIRE_MODELSCOPE_API_KEY", "test-ms-token")
    config = _base_config()

    with patch("openhire.config.loader.load_config", return_value=config), patch(
        "openhire.config.loader.resolve_config_env_vars",
        side_effect=lambda loaded: loaded,
    ):
        loaded = _load_runtime_config()

    assert loaded.agents.defaults.provider == "deepseek"
    assert loaded.agents.defaults.model == MODELSCOPE_DEMO_MODEL
    assert loaded.providers.deepseek.api_key == "test-ms-token"
    assert loaded.providers.deepseek.api_base == MODELSCOPE_DEMO_API_BASE


def test_load_runtime_config_reports_missing_modelscope_token(monkeypatch) -> None:
    _clear_modelscope_env(monkeypatch)
    monkeypatch.setenv("OPENHIRE_DEPLOY_TARGET", "modelscope")
    config = _base_config()

    with patch("openhire.config.loader.load_config", return_value=config), patch(
        "openhire.config.loader.resolve_config_env_vars",
        side_effect=lambda loaded: loaded,
    ), pytest.raises(typer.Exit) as exc_info:
        _load_runtime_config()

    assert exc_info.value.exit_code == 1
    assert config.agents.defaults.provider == "ollama"
    assert config.agents.defaults.model == "ollama/llama3.2"


def test_make_provider_uses_modelscope_demo_deepseek_base() -> None:
    config = _base_config()
    apply_modelscope_demo_config_overlay(
        config,
        environ={
            "OPENHIRE_DEPLOY_TARGET": "modelscope",
            "OPENHIRE_MODELSCOPE_API_KEY": "test-ms-token",
        },
    )

    with patch("openhire.providers.openai_compat_provider.AsyncOpenAI") as mock_async_openai:
        provider = _make_provider(config)

    assert provider.get_default_model() == MODELSCOPE_DEMO_MODEL
    kwargs = mock_async_openai.call_args.kwargs
    assert kwargs["api_key"] == "test-ms-token"
    assert kwargs["base_url"] == MODELSCOPE_DEMO_API_BASE


@pytest.mark.skipif(not HAS_AIOHTTP, reason="aiohttp not installed")
@pytest.mark.asyncio
async def test_demo_runtime_payload_shows_modelscope_deepseek_model(aiohttp_client, monkeypatch) -> None:
    monkeypatch.setenv("OPENHIRE_DEMO_MODE", "1")
    agent = MagicMock()
    agent.workspace = None
    agent.provider = None
    agent.model = MODELSCOPE_DEMO_MODEL
    agent.context_window_tokens = 10000
    agent.process_direct = AsyncMock(return_value="ok")
    agent._docker_agents_config = None
    agent.get_admin_snapshot = AsyncMock(
        return_value={
            "generatedAt": "2026-04-27T00:00:00Z",
            "process": {"role": "api", "pid": 1, "workspace": "/workspace", "uptimeSeconds": 1},
            "mainAgent": {"status": "idle", "context": {}, "lastUsage": {}},
            "subagents": [],
            "dockerContainers": [],
            "dockerAgents": [],
        }
    )
    agent._connect_mcp = AsyncMock()
    agent.close_mcp = AsyncMock()
    app = create_app(agent, model_name=MODELSCOPE_DEMO_MODEL)
    client = await aiohttp_client(app)

    runtime = await (await client.get("/admin/api/runtime")).json()

    assert runtime["demoMode"]["enabled"] is True
    assert runtime["mainAgent"]["model"] == MODELSCOPE_DEMO_MODEL
    await client.close()
