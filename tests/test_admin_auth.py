from __future__ import annotations

from datetime import timedelta
from types import SimpleNamespace
from unittest.mock import AsyncMock, MagicMock

import pytest
import pytest_asyncio

from openhire.admin.auth import AdminAuthStore, AuthError
from openhire.api.server import create_app

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


def _make_agent() -> MagicMock:
    agent = MagicMock()
    agent.workspace = None
    agent.provider = SimpleNamespace(generation=SimpleNamespace(max_tokens=128))
    agent.model = "test-model"
    agent.context_window_tokens = 1000
    agent.tools = SimpleNamespace(get_definitions=lambda: [])
    agent._docker_agents_config = SimpleNamespace(enabled=False)
    agent._last_admin_session_key = None
    agent._last_admin_context_tokens = 0
    agent._last_admin_context_source = "unknown"
    agent.runtime_monitor = None
    agent.process_direct = AsyncMock(return_value="ok")
    agent.clear_admin_context = AsyncMock(return_value={"sessionKey": "api:default"})
    agent.get_admin_snapshot = AsyncMock(
        return_value={
            "generatedAt": "2026-05-01T00:00:00Z",
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


def test_auth_store_creates_users_and_verifies_password(tmp_path) -> None:
    store = AdminAuthStore(tmp_path)
    user = store.create_user("admin", "password123", bootstrap_only=True)

    assert user["username"] == "admin"
    assert store.needs_bootstrap() is False
    assert store.authenticate("admin", "wrong-password") is None
    assert store.authenticate("admin", "password123")["id"] == user["id"]
    with pytest.raises(AuthError):
        store.create_user("admin", "another-password")


def test_auth_store_session_expiry_and_delete_guards(tmp_path) -> None:
    store = AdminAuthStore(tmp_path)
    admin = store.create_user("admin", "password123", bootstrap_only=True)
    other = store.create_user("operator", "password456")
    expired_token, _ = store.create_session(admin["id"], lifetime=timedelta(seconds=-1))

    assert store.session_for_token(expired_token) is None
    with pytest.raises(AuthError):
        store.delete_user(admin["id"], current_user_id=admin["id"])
    assert store.delete_user(other["id"], current_user_id=admin["id"])["deleted"] is True
    with pytest.raises(AuthError):
        store.delete_user(admin["id"], current_user_id="someone-else")


@pytest.mark.skipif(not HAS_AIOHTTP, reason="aiohttp not installed")
@pytest.mark.asyncio
async def test_admin_requires_login_but_v1_stays_open(aiohttp_client, tmp_path) -> None:
    app = create_app(_make_agent(), model_name="test-model", workspace=tmp_path)
    client = await aiohttp_client(app)

    login_resp = await client.get("/admin/login")
    admin_resp = await client.get("/admin", allow_redirects=False)
    runtime_resp = await client.get("/admin/api/runtime")
    employees_resp = await client.get("/employees")
    api_resp = await client.post(
        "/v1/chat/completions",
        json={"messages": [{"role": "user", "content": "hello"}]},
    )

    assert login_resp.status == 200
    login_body = await login_resp.text()
    assert "data-auth-login-root" in login_body
    assert "/admin/api/auth/register" in login_body
    assert "/admin/api/auth/login" in login_body
    assert admin_resp.status == 302
    assert admin_resp.headers["Location"] == "/admin/login"
    assert runtime_resp.status == 401
    assert employees_resp.status == 401
    assert api_resp.status == 200


@pytest.mark.skipif(not HAS_AIOHTTP, reason="aiohttp not installed")
@pytest.mark.asyncio
async def test_bootstrap_login_logout_and_csrf(aiohttp_client, tmp_path) -> None:
    app = create_app(_make_agent(), model_name="test-model", workspace=tmp_path)
    client = await aiohttp_client(app)

    session = await client.get("/admin/api/auth/session")
    assert (await session.json())["needsBootstrap"] is True

    register = await client.post(
        "/admin/api/auth/register",
        json={"username": "admin", "password": "password123"},
    )
    assert register.status == 201
    registered = await register.json()
    csrf = registered["csrfToken"]
    assert registered["authenticated"] is True

    runtime = await client.get("/admin/api/runtime")
    assert runtime.status == 200

    missing_csrf = await client.post("/admin/api/context/clear", json={"session_key": "api:default"})
    assert missing_csrf.status == 403

    ok_csrf = await client.post(
        "/admin/api/context/clear",
        json={"session_key": "api:default"},
        headers={"X-OpenHire-CSRF": csrf},
    )
    assert ok_csrf.status == 200

    logout = await client.post("/admin/api/auth/logout")
    assert logout.status == 200
    after = await client.get("/admin/api/runtime")
    assert after.status == 401


@pytest.mark.skipif(not HAS_AIOHTTP, reason="aiohttp not installed")
@pytest.mark.asyncio
async def test_logged_in_admin_can_manage_users(aiohttp_client, tmp_path) -> None:
    app = create_app(_make_agent(), model_name="test-model", workspace=tmp_path)
    client = await aiohttp_client(app)
    register = await client.post(
        "/admin/api/auth/register",
        json={"username": "admin", "password": "password123"},
    )
    csrf = (await register.json())["csrfToken"]

    created = await client.post(
        "/admin/api/auth/users",
        json={"username": "operator", "password": "password456"},
        headers={"X-OpenHire-CSRF": csrf},
    )
    assert created.status == 201
    user_id = (await created.json())["user"]["id"]

    users = await client.get("/admin/api/auth/users")
    assert [item["username"] for item in (await users.json())["users"]] == ["admin", "operator"]

    deleted = await client.delete(
        f"/admin/api/auth/users/{user_id}",
        headers={"X-OpenHire-CSRF": csrf},
    )
    assert deleted.status == 200


@pytest.mark.skipif(not HAS_AIOHTTP, reason="aiohttp not installed")
@pytest.mark.asyncio
async def test_demo_mode_bypasses_admin_auth(aiohttp_client, tmp_path, monkeypatch) -> None:
    monkeypatch.setenv("OPENHIRE_DEMO_MODE", "true")
    app = create_app(_make_agent(), model_name="test-model", workspace=tmp_path)
    client = await aiohttp_client(app)

    admin = await client.get("/admin")
    runtime = await client.get("/admin/api/runtime")
    employees = await client.get("/employees")
    session = await client.get("/admin/api/auth/session")

    assert admin.status == 200
    assert runtime.status == 200
    assert employees.status == 200
    assert (await session.json())["demoMode"]["enabled"] is True
