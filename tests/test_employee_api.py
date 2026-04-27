from __future__ import annotations

from unittest.mock import AsyncMock, MagicMock

import aiohttp
import pytest
import pytest_asyncio

from openhire.api.server import create_app
from openhire.config.schema import DockerAgentConfig, DockerAgentsConfig
from openhire.providers.base import LLMResponse
from openhire.skill_catalog import ClawHubProviderError, SkillCatalogService, SkillCatalogStore
from openhire.workforce.required_skill import (
    REQUIRED_EMPLOYEE_SKILL_ID,
    REQUIRED_EMPLOYEE_SKILL_NAME,
    REQUIRED_EMPLOYEE_SKILL_PROMPT_START,
)
from openhire.workforce.registry import AgentEntry, AgentRegistry
from openhire.workforce.store import OpenHireStore

try:
    from aiohttp.test_utils import TestClient, TestServer

    HAS_AIOHTTP = True
except ImportError:
    HAS_AIOHTTP = False


def _make_agent() -> MagicMock:
    agent = MagicMock()
    agent.process_direct = AsyncMock(return_value="ok")
    agent._docker_agents_config = None
    agent.get_admin_snapshot = AsyncMock(
        return_value={
            "generatedAt": "2026-04-16T00:00:00Z",
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


def _local_skill_upload() -> aiohttp.FormData:
    data = aiohttp.FormData()
    data.add_field(
        "file",
        (
            "---\n"
            "name: interview-calibration\n"
            "description: Standardize interviewer feedback.\n"
            "---\n\n"
            "# Interview Calibration\n"
        ).encode("utf-8"),
        filename="SKILL.md",
        content_type="text/markdown",
    )
    return data


def _skill_markdown(name: str, description: str) -> str:
    return f"---\nname: {name}\ndescription: {description}\n---\n\n# {name}\n\n{description}\n"


def _assert_required_employee_skill(body: dict) -> None:
    assert body["skill_ids"][0] == REQUIRED_EMPLOYEE_SKILL_ID
    assert body["skills"][0] == REQUIRED_EMPLOYEE_SKILL_NAME
    assert REQUIRED_EMPLOYEE_SKILL_PROMPT_START in body["system_prompt"]
    assert body["system_prompt"].count(REQUIRED_EMPLOYEE_SKILL_PROMPT_START) == 1


def _employee_workspace(workspace, agent_id: str):
    return workspace / "openhire" / "employees" / agent_id / "workspace"


def _seed_recommendation_skill(workspace, *, external_id: str = "gmail", name: str = "Gmail") -> str:
    service = SkillCatalogService(SkillCatalogStore(workspace))
    [entry] = service.upsert_many(
        [
            {
                "source": "clawhub",
                "external_id": external_id,
                "name": name,
                "description": f"{name} skill.",
                "source_url": f"https://clawhub.ai/test/{external_id}",
                "markdown": f"---\nname: {external_id}\ndescription: {name} skill.\n---\n\n# {name}\n",
            }
        ]
    )
    return entry.id


def _clawhub_skill_record(external_id: str, name: str, description: str | None = None) -> dict[str, str]:
    return {
        "source": "clawhub",
        "external_id": external_id,
        "name": name,
        "description": description or f"{name} skill.",
        "version": "1.0.0",
        "author": "test",
        "license": "",
        "source_url": f"https://clawhub.ai/test/{external_id}",
        "safety_status": "",
    }


class _FakeRecommendationClawHubProvider:
    def __init__(
        self,
        *,
        search_results: dict[str, list[dict[str, str]]] | None = None,
        markdown_by_url: dict[str, str] | None = None,
        fail_search: bool = False,
    ) -> None:
        self.search_results = search_results or {}
        self.markdown_by_url = markdown_by_url or {}
        self.fail_search = fail_search
        self.search_calls: list[tuple[str, int]] = []
        self.fetch_calls: list[str] = []

    async def search(self, query: str, *, limit: int = 10) -> list[dict[str, str]]:
        self.search_calls.append((query, limit))
        if self.fail_search:
            raise ClawHubProviderError("ClawHub unavailable")
        return list(self.search_results.get(query, []))[:limit]

    async def fetch_skill_markdown(self, source_url: str) -> str:
        self.fetch_calls.append(source_url)
        return self.markdown_by_url[source_url]

    async def fetch_package_details(self, source_url: str) -> dict[str, object]:
        return {}


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
async def test_employee_crud_api_persists_and_lists_entries(aiohttp_client, tmp_path) -> None:
    app = create_app(_make_agent(), model_name="test-model", workspace=tmp_path)
    client = await aiohttp_client(app)

    create_resp = await client.post(
        "/employees",
        json={
            "name": "Nova FE",
            "avatar": "coral-wave",
            "role": "前端工程师",
            "skills": ["react", "typescript"],
            "system_prompt": "你是资深前端工程师。",
            "agent_type": "nanobot",
        },
    )

    assert create_resp.status == 201
    created = await create_resp.json()
    assert created["name"] == "Nova FE"
    assert created["id"]
    assert created["avatar"] == "coral-wave"
    assert created["agent_type"] == "nanobot"
    assert created["skills"] == [REQUIRED_EMPLOYEE_SKILL_NAME, "react", "typescript"]
    assert created["system_prompt"].startswith("你是资深前端工程师。")
    _assert_required_employee_skill(created)
    assert created["agent_config"] == {}
    assert created["container_name"] == f"openhire-{created['id']}"
    assert created["status"] == "active"
    assert "created_at" in created
    assert "updated_at" in created

    list_resp = await client.get("/employees")

    assert list_resp.status == 200
    payload = await list_resp.json()
    assert [item["id"] for item in payload] == [created["id"]]
    assert payload[0]["name"] == "Nova FE"
    assert payload[0]["avatar"] == "coral-wave"
    assert payload[0]["updated_at"] == created["updated_at"]
    assert payload[0]["container_name"] == created["container_name"]

    delete_resp = await client.delete(f"/employees/{created['id']}")
    assert delete_resp.status == 204

    final_list = await client.get("/employees")
    assert final_list.status == 200
    assert await final_list.json() == []


@pytest.mark.skipif(not HAS_AIOHTTP, reason="aiohttp not installed")
@pytest.mark.asyncio
async def test_employee_runtime_config_files_are_whitelisted_and_save_soul_updates_prompt(
    aiohttp_client,
    tmp_path,
) -> None:
    app = create_app(_make_agent(), model_name="test-model", workspace=tmp_path)
    client = await aiohttp_client(app)
    create_resp = await client.post(
        "/employees",
        json={
            "name": "Nova FE",
            "role": "前端工程师",
            "skills": ["react"],
            "system_prompt": "你负责前端。",
            "agent_type": "nanobot",
        },
    )
    created = await create_resp.json()

    list_resp = await client.get(f"/admin/api/employees/{created['id']}/runtime-config")

    assert list_resp.status == 200
    config = await list_resp.json()
    assert [item["name"] for item in config["files"]] == [
        "SOUL.md",
        "AGENTS.md",
        "HEARTBEAT.md",
        "TOOLS.md",
        "USER.md",
    ]
    soul = next(item for item in config["files"] if item["name"] == "SOUL.md")
    agents = next(item for item in config["files"] if item["name"] == "AGENTS.md")
    assert created["system_prompt"].startswith("你负责前端。")
    _assert_required_employee_skill(created)
    assert soul["content"] != created["system_prompt"]
    assert "你负责前端。" in soul["content"]
    assert REQUIRED_EMPLOYEE_SKILL_PROMPT_START not in soul["content"]
    assert REQUIRED_EMPLOYEE_SKILL_PROMPT_START in agents["content"]

    rejected = await client.put(
        f"/admin/api/employees/{created['id']}/runtime-config/README.md",
        json={"content": "unsafe"},
    )
    assert rejected.status == 400

    save_resp = await client.put(
        f"/admin/api/employees/{created['id']}/runtime-config/SOUL.md",
        json={"content": "Updated employee soul."},
    )

    assert save_resp.status == 200
    saved = await save_resp.json()
    assert saved["file"]["name"] == "SOUL.md"
    assert saved["file"]["content"] == "Updated employee soul."
    assert saved["restart_required"] is True
    assert (_employee_workspace(tmp_path, created["id"]) / "SOUL.md").read_text(encoding="utf-8") == "Updated employee soul."

    employees = await (await client.get("/employees")).json()
    assert employees[0]["system_prompt"] == created["system_prompt"]


@pytest.mark.skipif(not HAS_AIOHTTP, reason="aiohttp not installed")
@pytest.mark.asyncio
async def test_employee_cron_admin_endpoints_filter_by_employee(
    aiohttp_client,
    tmp_path,
) -> None:
    app = create_app(_make_agent(), model_name="test-model", workspace=tmp_path)
    client = await aiohttp_client(app)
    registry = app["employee_registry"]
    first = registry.register(AgentEntry(name="Nova FE", role="前端", agent_type="nanobot"))
    second = registry.register(AgentEntry(name="QA", role="测试", agent_type="nanobot"))

    create_resp = await client.post(
        f"/admin/api/employees/{first.agent_id}/cron",
        json={
            "name": "daily check",
            "message": "检查项目状态",
            "schedule": {"kind": "every", "everyMs": 60000},
            "deliver": False,
        },
    )

    assert create_resp.status == 201
    created = await create_resp.json()
    assert created["payload"]["employee_id"] == first.agent_id

    first_jobs = await (await client.get(f"/admin/api/employees/{first.agent_id}/cron")).json()
    second_jobs = await (await client.get(f"/admin/api/employees/{second.agent_id}/cron")).json()
    assert [job["id"] for job in first_jobs] == [created["id"]]
    assert second_jobs == []

    update_resp = await client.put(
        f"/admin/api/employees/{first.agent_id}/cron/{created['id']}",
        json={"message": "更新后的检查", "enabled": False},
    )
    assert update_resp.status == 200
    updated = await update_resp.json()
    assert updated["payload"]["message"] == "更新后的检查"
    assert updated["enabled"] is False
    assert updated["payload"]["employee_id"] == first.agent_id

    delete_resp = await client.delete(f"/admin/api/employees/{first.agent_id}/cron/{created['id']}")
    assert delete_resp.status == 204
    assert await (await client.get(f"/admin/api/employees/{first.agent_id}/cron")).json() == []


@pytest.mark.skipif(not HAS_AIOHTTP, reason="aiohttp not installed")
@pytest.mark.asyncio
async def test_employee_list_sees_external_registry_creates_without_restart(
    aiohttp_client,
    tmp_path,
) -> None:
    app = create_app(_make_agent(), model_name="test-model", workspace=tmp_path)
    client = await aiohttp_client(app)

    initial_resp = await client.get("/employees")
    assert initial_resp.status == 200
    assert await initial_resp.json() == []

    external_registry = AgentRegistry(OpenHireStore(tmp_path))
    created = external_registry.register(AgentEntry(
        name="Pixel Figma",
        role="Figma Frontend Designer",
        skills=["figma", "frontend"],
        system_prompt="Design from Figma.",
        agent_type="nanobot",
    ))

    list_resp = await client.get("/employees")
    assert list_resp.status == 200
    body = await list_resp.json()
    assert [item["id"] for item in body] == [created.agent_id]
    assert body[0]["skills"] == ["figma", "frontend"]
    assert app["employee_registry"].get(created.agent_id).name == "Pixel Figma"


@pytest.mark.skipif(not HAS_AIOHTTP, reason="aiohttp not installed")
@pytest.mark.asyncio
async def test_employee_create_accepts_tags_alias_for_skills(aiohttp_client, tmp_path) -> None:
    app = create_app(_make_agent(), model_name="test-model", workspace=tmp_path)
    client = await aiohttp_client(app)

    resp = await client.post(
        "/employees",
        json={
            "name": "QA",
            "role": "测试工程师",
            "tags": ["qa", "automation"],
            "system_prompt": "你负责测试。",
            "agent_type": "openclaw",
        },
    )

    assert resp.status == 201
    body = await resp.json()
    assert body["skills"] == [REQUIRED_EMPLOYEE_SKILL_NAME, "qa", "automation"]
    _assert_required_employee_skill(body)


@pytest.mark.skipif(not HAS_AIOHTTP, reason="aiohttp not installed")
@pytest.mark.asyncio
async def test_employee_create_accepts_local_skill_ids(aiohttp_client, tmp_path) -> None:
    app = create_app(_make_agent(), model_name="test-model", workspace=tmp_path)
    client = await aiohttp_client(app)

    import_resp = await client.post(
        "/skills/import",
        json={
            "skills": [
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
                    "markdown": _skill_markdown("github", "Use the gh CLI."),
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
                    "markdown": _skill_markdown("nano-gpt-cli", "Use nano-gpt locally."),
                },
            ]
        },
    )
    imported = await import_resp.json()

    resp = await client.post(
        "/employees",
        json={
            "name": "Tools",
            "role": "工程师",
            "skill_ids": [imported[0]["id"], imported[1]["id"]],
            "system_prompt": "你负责工具集成。",
            "agent_type": "openclaw",
        },
    )

    assert resp.status == 201
    body = await resp.json()
    assert body["skill_ids"] == [REQUIRED_EMPLOYEE_SKILL_ID, imported[0]["id"], imported[1]["id"]]
    assert body["skills"] == [REQUIRED_EMPLOYEE_SKILL_NAME, "Github", "Nano Gpt"]
    _assert_required_employee_skill(body)


@pytest.mark.skipif(not HAS_AIOHTTP, reason="aiohttp not installed")
@pytest.mark.asyncio
async def test_employee_create_accepts_local_uploaded_skill_ids(aiohttp_client, tmp_path) -> None:
    app = create_app(_make_agent(), model_name="test-model", workspace=tmp_path)
    client = await aiohttp_client(app)

    preview_resp = await client.post(
        "/skills/import/local/preview",
        data=_local_skill_upload(),
    )
    preview_body = await preview_resp.json()

    import_resp = await client.post(
        "/skills/import",
        json={"skills": [preview_body["skill"]]},
    )
    imported = await import_resp.json()

    resp = await client.post(
        "/employees",
        json={
            "name": "Interviewer",
            "role": "面试官",
            "skill_ids": [imported[0]["id"]],
            "system_prompt": "你负责标准化面试反馈。",
            "agent_type": "openclaw",
        },
    )

    assert resp.status == 201
    body = await resp.json()
    assert body["skill_ids"] == [REQUIRED_EMPLOYEE_SKILL_ID, imported[0]["id"]]
    assert body["skills"] == [REQUIRED_EMPLOYEE_SKILL_NAME, "interview-calibration"]
    _assert_required_employee_skill(body)


@pytest.mark.skipif(not HAS_AIOHTTP, reason="aiohttp not installed")
@pytest.mark.asyncio
async def test_employee_create_rejects_unknown_skill_ids(aiohttp_client, tmp_path) -> None:
    app = create_app(_make_agent(), model_name="test-model", workspace=tmp_path)
    client = await aiohttp_client(app)

    resp = await client.post(
        "/employees",
        json={
            "name": "Tools",
            "role": "工程师",
            "skill_ids": ["missing-skill"],
            "system_prompt": "你负责工具集成。",
            "agent_type": "openclaw",
        },
    )

    assert resp.status == 400
    body = await resp.json()
    assert "skill_ids" in body["error"]["message"]


@pytest.mark.skipif(not HAS_AIOHTTP, reason="aiohttp not installed")
@pytest.mark.asyncio
async def test_employee_create_allows_missing_skills(aiohttp_client, tmp_path) -> None:
    app = create_app(_make_agent(), model_name="test-model", workspace=tmp_path)
    client = await aiohttp_client(app)

    resp = await client.post(
        "/employees",
        json={
            "name": "Incomplete",
            "role": "前端工程师",
            "system_prompt": "你是前端。",
            "agent_type": "nanobot",
        },
    )

    assert resp.status == 201
    body = await resp.json()
    assert body["skills"] == [REQUIRED_EMPLOYEE_SKILL_NAME]
    assert body["skill_ids"] == [REQUIRED_EMPLOYEE_SKILL_ID]
    _assert_required_employee_skill(body)


@pytest.mark.skipif(not HAS_AIOHTTP, reason="aiohttp not installed")
@pytest.mark.asyncio
async def test_employee_create_validates_other_required_fields(aiohttp_client, tmp_path) -> None:
    app = create_app(_make_agent(), model_name="test-model", workspace=tmp_path)
    client = await aiohttp_client(app)

    resp = await client.post(
        "/employees",
        json={
            "name": "Incomplete",
            "role": "前端工程师",
            "agent_type": "nanobot",
        },
    )

    assert resp.status == 400
    body = await resp.json()
    assert "system_prompt" in body["error"]["message"]


@pytest.mark.skipif(not HAS_AIOHTTP, reason="aiohttp not installed")
@pytest.mark.asyncio
async def test_employee_create_validates_agent_type(aiohttp_client, tmp_path) -> None:
    app = create_app(_make_agent(), model_name="test-model", workspace=tmp_path)
    client = await aiohttp_client(app)

    # OpenHands is disabled and should be rejected like an unknown agent type.
    for agent_type in ("invalid-agent", "openhands"):
        resp = await client.post(
            "/employees",
            json={
                "name": "Nova FE",
                "role": "前端工程师",
                "skills": ["react"],
                "system_prompt": "你是前端。",
                "agent_type": agent_type,
            },
        )

        assert resp.status == 400
        body = await resp.json()
        assert "agent_type" in body["error"]["message"]


@pytest.mark.skipif(not HAS_AIOHTTP, reason="aiohttp not installed")
@pytest.mark.asyncio
async def test_employee_create_validates_avatar_id(aiohttp_client, tmp_path) -> None:
    app = create_app(_make_agent(), model_name="test-model", workspace=tmp_path)
    client = await aiohttp_client(app)

    resp = await client.post(
        "/employees",
        json={
            "name": "Nova FE",
            "avatar": "Coral Wave",
            "role": "前端工程师",
            "skills": ["react"],
            "system_prompt": "你是前端。",
            "agent_type": "nanobot",
        },
    )

    assert resp.status == 400
    body = await resp.json()
    assert "avatar" in body["error"]["message"]


@pytest.mark.skipif(not HAS_AIOHTTP, reason="aiohttp not installed")
@pytest.mark.asyncio
async def test_employee_template_api_saves_lists_and_cooks(aiohttp_client, tmp_path) -> None:
    agent = _make_agent()
    agent.process_direct = AsyncMock(
        return_value='```json\n{"name":"Ops Weaver","role":"Operations Automation Specialist","system_prompt":"你是一个擅长自动化流程设计与执行的运营效率专家。"}\n```'
    )
    app = create_app(agent, model_name="test-model", workspace=tmp_path)
    client = await aiohttp_client(app)

    initial_resp = await client.get("/employee-templates")
    assert initial_resp.status == 200
    assert await initial_resp.json() == {"templates": [], "hiddenTemplateIds": []}

    cook_resp = await client.post(
        "/admin/api/employee-templates/cook",
        json={
            "description": "一个擅长飞书自动化和招聘流程搭建的运营效率专家",
            "agent_type": "openclaw",
        },
    )

    assert cook_resp.status == 200
    cooked = await cook_resp.json()
    assert cooked["name"] == "Ops Weaver"
    assert cooked["role"] == "Operations Automation Specialist"
    assert "运营效率专家" in cooked["system_prompt"]

    save_resp = await client.post(
        "/employee-templates",
        json={
            "defaultName": cooked["name"],
            "role": cooked["role"],
            "defaultAgentType": "openclaw",
            "companyStyle": "一个擅长飞书自动化和招聘流程搭建的运营效率专家",
            "summary": cooked["system_prompt"],
        },
    )

    assert save_resp.status == 201
    saved = await save_resp.json()
    assert saved["id"]
    assert saved["defaultName"] == "Ops Weaver"
    assert saved["defaultAgentType"] == "openclaw"

    list_resp = await client.get("/employee-templates")
    assert list_resp.status == 200
    payload = await list_resp.json()
    assert len(payload["templates"]) == 1
    assert payload["templates"][0]["id"] == saved["id"]
    assert payload["hiddenTemplateIds"] == []

    delete_resp = await client.delete(f"/employee-templates/{saved['id']}")
    assert delete_resp.status == 204

    final_resp = await client.get("/employee-templates")
    assert final_resp.status == 200
    assert await final_resp.json() == {"templates": [], "hiddenTemplateIds": []}

    protected_delete_resp = await client.delete("/employee-templates/custom-role")
    assert protected_delete_resp.status == 400
    protected_body = await protected_delete_resp.json()
    assert "cannot be deleted" in protected_body["error"]["message"]


@pytest.mark.skipif(not HAS_AIOHTTP, reason="aiohttp not installed")
@pytest.mark.asyncio
async def test_employee_skill_recommendation_api_returns_selected_skills(aiohttp_client, tmp_path) -> None:
    skill_id = _seed_recommendation_skill(tmp_path)
    skill_provider = _FakeRecommendationClawHubProvider(search_results={"gmail": []})
    agent = _make_agent()
    agent.provider = MagicMock()
    agent.provider.chat_with_retry = AsyncMock(
        side_effect=[
            LLMResponse(content='{"queries":["gmail"]}'),
            LLMResponse(content=f'{{"skill_ids":["{skill_id}"],"reason":"inbox triage"}}'),
        ]
    )
    app = create_app(agent, model_name="test-model", workspace=tmp_path, skill_provider=skill_provider)
    client = await aiohttp_client(app)

    resp = await client.post(
        "/admin/api/employee-skills/recommend",
        json={
            "name": "Inbox Ops",
            "role": "邮箱与消息分诊员",
            "system_prompt": "处理邮件。",
            "skills": ["triage"],
        },
    )

    assert resp.status == 200
    body = await resp.json()
    assert body["skill_ids"] == [skill_id]
    assert body["skills"] == ["Gmail"]
    assert body["reason"] == "inbox triage"
    assert body["warning"] == ""
    assert body["installed_skill_ids"] == []
    assert body["installed_skills"] == []
    assert body["remote_queries"] == ["gmail"]


@pytest.mark.skipif(not HAS_AIOHTTP, reason="aiohttp not installed")
@pytest.mark.asyncio
async def test_employee_skill_recommendation_installs_clawhub_skill_when_local_catalog_empty(
    aiohttp_client,
    tmp_path,
) -> None:
    remote = _clawhub_skill_record("gmail", "Gmail", "Handle inbox triage.")
    provider = _FakeRecommendationClawHubProvider(
        search_results={"gmail": [remote]},
        markdown_by_url={remote["source_url"]: _skill_markdown("gmail", "Handle inbox triage.")},
    )
    agent = _make_agent()
    agent.provider = MagicMock()
    agent.provider.chat_with_retry = AsyncMock(
        side_effect=[
            LLMResponse(content='{"queries":["gmail"]}'),
            LLMResponse(content='{"skill_ids":["clawhub:0"],"reason":"needs inbox automation"}'),
        ]
    )
    app = create_app(agent, model_name="test-model", workspace=tmp_path, skill_provider=provider)
    client = await aiohttp_client(app)

    resp = await client.post(
        "/admin/api/employee-skills/recommend",
        json={"name": "Inbox Ops", "role": "邮箱与消息分诊员", "system_prompt": "处理邮件。"},
    )

    assert resp.status == 200
    body = await resp.json()
    assert len(body["skill_ids"]) == 1
    assert body["skill_ids"] == body["installed_skill_ids"]
    assert body["skills"] == ["Gmail"]
    assert body["installed_skills"][0]["source"] == "clawhub"
    assert body["installed_skills"][0]["external_id"] == "gmail"
    assert body["remote_queries"] == ["gmail"]
    assert body["warning"] == ""
    assert provider.search_calls == [("gmail", 6)]
    assert provider.fetch_calls == [remote["source_url"]]

    skills_resp = await client.get("/skills")
    assert skills_resp.status == 200
    skill_names = [item["name"] for item in await skills_resp.json()]
    assert "Gmail" in skill_names


@pytest.mark.skipif(not HAS_AIOHTTP, reason="aiohttp not installed")
@pytest.mark.asyncio
async def test_employee_skill_recommendation_falls_back_to_compact_clawhub_queries(
    aiohttp_client,
    tmp_path,
) -> None:
    remote = _clawhub_skill_record("publish-api", "Publish Api", "Publish and verify API changes.")
    provider = _FakeRecommendationClawHubProvider(
        search_results={"api": [remote]},
        markdown_by_url={remote["source_url"]: _skill_markdown("publish-api", "Publish APIs.")},
    )
    agent = _make_agent()
    agent.provider = MagicMock()
    agent.provider.chat_with_retry = AsyncMock(
        side_effect=[
            LLMResponse(content='{"queries":["high-concurrency API","domain modeling"]}'),
            LLMResponse(content='{"skill_ids":["clawhub:0"],"reason":"api support"}'),
        ]
    )
    app = create_app(agent, model_name="test-model", workspace=tmp_path, skill_provider=provider)
    client = await aiohttp_client(app)

    resp = await client.post(
        "/admin/api/employee-skills/recommend",
        json={"name": "Kepler BE", "role": "Backend Engineer / 后端工程师", "system_prompt": "负责高并发 API。"},
    )

    assert resp.status == 200
    body = await resp.json()
    assert body["skills"] == ["Publish Api"]
    assert body["installed_skill_ids"] == body["skill_ids"]
    assert body["remote_queries"] == ["high-concurrency API", "domain modeling", "python", "api"]
    assert provider.search_calls == [
        ("high-concurrency API", 6),
        ("domain modeling", 6),
        ("python", 6),
        ("api", 6),
    ]


@pytest.mark.skipif(not HAS_AIOHTTP, reason="aiohttp not installed")
@pytest.mark.asyncio
async def test_employee_skill_recommendation_can_mix_local_and_clawhub_skills(
    aiohttp_client,
    tmp_path,
) -> None:
    local_skill_id = _seed_recommendation_skill(tmp_path, external_id="slack", name="Slack")
    remote = _clawhub_skill_record("calendar", "Calendar", "Coordinate meetings.")
    provider = _FakeRecommendationClawHubProvider(
        search_results={"calendar": [remote]},
        markdown_by_url={remote["source_url"]: _skill_markdown("calendar", "Coordinate meetings.")},
    )
    agent = _make_agent()
    agent.provider = MagicMock()
    agent.provider.chat_with_retry = AsyncMock(
        side_effect=[
            LLMResponse(content='{"queries":["calendar"]}'),
            LLMResponse(
                content=f'{{"skill_ids":["{local_skill_id}","clawhub:0"],"reason":"messages and meetings"}}'
            ),
        ]
    )
    app = create_app(agent, model_name="test-model", workspace=tmp_path, skill_provider=provider)
    client = await aiohttp_client(app)

    resp = await client.post(
        "/admin/api/employee-skills/recommend",
        json={"name": "Ops", "role": "行政协同", "system_prompt": "处理消息和会议。"},
    )

    assert resp.status == 200
    body = await resp.json()
    assert body["skill_ids"][0] == local_skill_id
    assert len(body["skill_ids"]) == 2
    assert body["skills"] == ["Slack", "Calendar"]
    assert body["installed_skill_ids"] == [body["skill_ids"][1]]
    assert body["installed_skills"][0]["external_id"] == "calendar"
    assert body["reason"] == "messages and meetings"
    assert body["warning"] == ""


@pytest.mark.skipif(not HAS_AIOHTTP, reason="aiohttp not installed")
@pytest.mark.asyncio
async def test_employee_skill_recommendation_falls_back_to_local_when_clawhub_search_fails(
    aiohttp_client,
    tmp_path,
) -> None:
    local_skill_id = _seed_recommendation_skill(tmp_path)
    provider = _FakeRecommendationClawHubProvider(fail_search=True)
    agent = _make_agent()
    agent.provider = MagicMock()
    agent.provider.chat_with_retry = AsyncMock(
        side_effect=[
            LLMResponse(content='{"queries":["gmail"]}'),
            LLMResponse(content=f'{{"skill_ids":["{local_skill_id}"],"reason":"local fallback"}}'),
        ]
    )
    app = create_app(agent, model_name="test-model", workspace=tmp_path, skill_provider=provider)
    client = await aiohttp_client(app)

    resp = await client.post(
        "/admin/api/employee-skills/recommend",
        json={"name": "Inbox Ops", "role": "邮箱与消息分诊员", "system_prompt": "处理邮件。"},
    )

    assert resp.status == 200
    body = await resp.json()
    assert body["skill_ids"] == [local_skill_id]
    assert body["installed_skill_ids"] == []
    assert body["installed_skills"] == []
    assert body["remote_queries"] == ["gmail"]
    assert "ClawHub" in body["warning"]
    assert "local fallback" == body["reason"]
    assert provider.fetch_calls == []


@pytest.mark.skipif(not HAS_AIOHTTP, reason="aiohttp not installed")
@pytest.mark.asyncio
async def test_employee_skill_recommendation_reuses_existing_clawhub_skill_without_fetch(
    aiohttp_client,
    tmp_path,
) -> None:
    existing_skill_id = _seed_recommendation_skill(tmp_path, external_id="calendar", name="Calendar")
    remote = _clawhub_skill_record("calendar", "Calendar", "Coordinate meetings.")
    provider = _FakeRecommendationClawHubProvider(search_results={"calendar": [remote]})
    agent = _make_agent()
    agent.provider = MagicMock()
    agent.provider.chat_with_retry = AsyncMock(
        side_effect=[
            LLMResponse(content='{"queries":["calendar"]}'),
            LLMResponse(content='{"skill_ids":["clawhub:0"],"reason":"already available"}'),
        ]
    )
    app = create_app(agent, model_name="test-model", workspace=tmp_path, skill_provider=provider)
    client = await aiohttp_client(app)

    resp = await client.post(
        "/admin/api/employee-skills/recommend",
        json={"name": "Calendar Ops", "role": "日程助理", "system_prompt": "安排会议。"},
    )

    assert resp.status == 200
    body = await resp.json()
    assert body["skill_ids"] == [existing_skill_id]
    assert body["skills"] == ["Calendar"]
    assert body["installed_skill_ids"] == []
    assert body["installed_skills"] == []
    assert provider.fetch_calls == []


@pytest.mark.skipif(not HAS_AIOHTTP, reason="aiohttp not installed")
@pytest.mark.asyncio
async def test_employee_skill_recommendation_api_without_provider_returns_warning(aiohttp_client, tmp_path) -> None:
    _seed_recommendation_skill(tmp_path)
    app = create_app(_make_agent(), model_name="test-model", workspace=tmp_path)
    client = await aiohttp_client(app)

    resp = await client.post(
        "/admin/api/employee-skills/recommend",
        json={"name": "Inbox Ops", "role": "邮箱与消息分诊员", "system_prompt": ""},
    )

    assert resp.status == 200
    body = await resp.json()
    assert body["skill_ids"] == []
    assert "provider" in body["warning"]


@pytest.mark.skipif(not HAS_AIOHTTP, reason="aiohttp not installed")
@pytest.mark.asyncio
async def test_delete_missing_employee_returns_404(aiohttp_client, tmp_path) -> None:
    app = create_app(_make_agent(), model_name="test-model", workspace=tmp_path)
    client = await aiohttp_client(app)

    resp = await client.delete("/employees/missing")

    assert resp.status == 404
    body = await resp.json()
    assert "not found" in body["error"]["message"].lower()


@pytest.mark.skipif(not HAS_AIOHTTP, reason="aiohttp not installed")
@pytest.mark.asyncio
async def test_employee_create_starts_docker_container_when_enabled(
    aiohttp_client,
    tmp_path,
    monkeypatch,
) -> None:
    agent = _make_agent()
    agent._docker_agents_config = DockerAgentsConfig(
        enabled=True,
        agents={"nanobot": DockerAgentConfig(enabled=True, persistent=True)},
    )

    async def fake_ensure_running(adapter, instance_name, agent_cfg, workspace):
        assert adapter.agent_name == "nanobot"
        assert instance_name
        assert agent_cfg["container_name"].startswith("openhire-")
        assert workspace == _employee_workspace(tmp_path, instance_name)
        return agent_cfg["container_name"]

    monkeypatch.setattr("openhire.workforce.lifecycle.ensure_running", fake_ensure_running)

    app = create_app(agent, model_name="test-model", workspace=tmp_path)
    client = await aiohttp_client(app)

    resp = await client.post(
        "/employees",
        json={
            "name": "Nova FE",
            "role": "前端工程师",
            "skills": ["react"],
            "system_prompt": "你是前端。",
            "agent_type": "nanobot",
        },
    )

    assert resp.status == 201
    body = await resp.json()
    assert body["status"] == "active"


@pytest.mark.skipif(not HAS_AIOHTTP, reason="aiohttp not installed")
@pytest.mark.asyncio
async def test_employee_create_rolls_back_when_container_creation_fails(
    aiohttp_client,
    tmp_path,
    monkeypatch,
) -> None:
    agent = _make_agent()
    agent._docker_agents_config = DockerAgentsConfig(
        enabled=True,
        agents={"nanobot": DockerAgentConfig(enabled=True, persistent=True)},
    )

    async def broken_ensure_running(*_args, **_kwargs):
        raise RuntimeError("docker create failed")

    monkeypatch.setattr("openhire.workforce.lifecycle.ensure_running", broken_ensure_running)

    app = create_app(agent, model_name="test-model", workspace=tmp_path)
    client = await aiohttp_client(app)

    resp = await client.post(
        "/employees",
        json={
            "name": "Nova FE",
            "role": "前端工程师",
            "skills": ["react"],
            "system_prompt": "你是前端。",
            "agent_type": "nanobot",
        },
    )

    assert resp.status == 500

    list_resp = await client.get("/employees")
    assert list_resp.status == 200
    assert await list_resp.json() == []
