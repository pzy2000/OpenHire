from __future__ import annotations

from unittest.mock import AsyncMock, MagicMock

import pytest
import pytest_asyncio

from openhire.api.server import create_app
from openhire.workforce.required_skill import REQUIRED_EMPLOYEE_SKILL_ID, REQUIRED_EMPLOYEE_SKILL_NAME

try:
    from aiohttp.test_utils import TestClient, TestServer

    HAS_AIOHTTP = True
except ImportError:
    HAS_AIOHTTP = False


class _FakeClawHubProvider:
    def __init__(self) -> None:
        self.markdown_by_url = {
            "https://clawhub.ai/steipete/github": (
                "---\nname: github\ndescription: Use the gh CLI.\n---\n\n"
                "# Github\n\nFull GitHub instructions.\n"
            ),
            "https://clawhub.ai/icework/nano-gpt-cli": (
                "---\nname: nano-gpt-cli\ndescription: Use nano-gpt locally.\n---\n\n"
                "# Nano Gpt\n\nFull nano-gpt instructions.\n"
            ),
        }

    async def search(self, query: str, *, limit: int = 10) -> list[dict[str, str]]:
        assert query == "github"
        assert limit == 10
        return [
            {
                "source": "clawhub",
                "external_id": "github",
                "name": "Github",
                "description": "Use the gh CLI.",
                "version": "1.0.0",
                "author": "steipete",
                "license": "",
                "source_url": "https://clawhub.ai/steipete/github",
                "safety_status": "",
            },
            {
                "source": "clawhub",
                "external_id": "nano-gpt-cli",
                "name": "Nano Gpt",
                "description": "Use nano-gpt locally.",
                "version": "0.1.2",
                "author": "icework",
                "license": "",
                "source_url": "https://clawhub.ai/icework/nano-gpt-cli",
                "safety_status": "",
            },
        ]

    async def fetch_skill_markdown(self, source_url: str) -> str:
        return self.markdown_by_url[source_url]

    async def fetch_package_details(self, source_url: str) -> dict[str, object]:
        return {"downloads": 1000, "stars": 5, "risk": "unknown", "download_url": source_url}


def _make_agent() -> MagicMock:
    agent = MagicMock()
    agent.process_direct = AsyncMock(return_value="ok")
    agent._docker_agents_config = None
    agent.get_admin_snapshot = AsyncMock(return_value={})
    agent._connect_mcp = AsyncMock()
    agent.close_mcp = AsyncMock()
    return agent


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


@pytest.mark.skipif(not HAS_AIOHTTP, reason="aiohttp not installed")
@pytest.mark.asyncio
async def test_skill_catalog_e2e_search_import_and_bind_to_employee(
    aiohttp_client,
    tmp_path,
) -> None:
    app = create_app(
        _make_agent(),
        model_name="test-model",
        workspace=tmp_path,
        skill_provider=_FakeClawHubProvider(),
    )
    client = await aiohttp_client(app)

    search_resp = await client.get("/skills/search/clawhub?q=github")

    assert search_resp.status == 200
    searched = await search_resp.json()
    assert len(searched) == 2

    import_resp = await client.post("/skills/import", json={"skills": searched})

    assert import_resp.status == 201
    imported = await import_resp.json()
    assert len(imported) == 2
    github_content = await client.get(f"/skills/{imported[0]['id']}/content")
    assert github_content.status == 200
    github_payload = await github_content.json()
    assert "Full GitHub instructions." in github_payload["markdown"]

    create_resp = await client.post(
        "/employees",
        json={
            "name": "Tooling",
            "role": "平台工程师",
            "skill_ids": [imported[0]["id"], imported[1]["id"]],
            "system_prompt": "你负责技能和工具集成。",
            "agent_type": "openclaw",
        },
    )

    assert create_resp.status == 201
    employee = await create_resp.json()
    assert employee["skill_ids"] == [REQUIRED_EMPLOYEE_SKILL_ID, imported[0]["id"], imported[1]["id"]]
    assert employee["skills"] == [REQUIRED_EMPLOYEE_SKILL_NAME, "Github", "Nano Gpt"]
