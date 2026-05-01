from __future__ import annotations

from pathlib import Path
from unittest.mock import AsyncMock, MagicMock

import pytest
import pytest_asyncio

from openhire.agent.loop import AgentLoop
from openhire.agent.tools.message import MessageTool
from openhire.api.server import create_app as _create_app
from openhire.bus.queue import MessageBus
from openhire.config.schema import DockerAgentsConfig, OpenHireConfig
from openhire.providers.base import GenerationSettings, LLMProvider, LLMResponse, ToolCallRequest
from openhire.skill_catalog import SkillCatalogService, SkillCatalogStore
from openhire.workforce.organization import OrganizationPolicy, OrganizationStore, OrganizationValidator
from openhire.workforce.registry import AgentEntry, AgentRegistry
from openhire.workforce.required_skill import REQUIRED_EMPLOYEE_SKILL_ID, REQUIRED_EMPLOYEE_SKILL_NAME
from openhire.workforce.store import OpenHireStore
from openhire.workforce.tool import OpenHireTool

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


class _OrganizationToolCallProvider(LLMProvider):
    def __init__(self) -> None:
        super().__init__(api_key="dummy", api_base="http://dummy")
        self.generation = GenerationSettings()
        self.calls: list[list[dict]] = []

    def get_default_model(self) -> str:
        return "test-model"

    async def chat(self, *args, **kwargs) -> LLMResponse:
        raise NotImplementedError

    async def chat_with_retry(self, *, messages, tools=None, **kwargs) -> LLMResponse:
        self.calls.append(messages)
        if len(self.calls) == 1:
            return LLMResponse(
                content="",
                tool_calls=[
                    ToolCallRequest(
                        id="call_delegate",
                        name="openhire",
                        arguments={"action": "delegate", "agent_id": "c", "task": "review"},
                    )
                ],
                usage={},
            )
        tool_content = next(
            msg["content"]
            for msg in reversed(messages)
            if msg.get("role") == "tool" and msg.get("name") == "openhire"
        )
        return LLMResponse(content=f"tool said: {tool_content}", tool_calls=[], usage={})


def _registry(workspace: Path) -> AgentRegistry:
    return AgentRegistry(OpenHireStore(workspace))


def _seed_employee(workspace: Path, agent_id: str, name: str, **overrides) -> AgentEntry:
    entry = AgentEntry(
        agent_id=agent_id,
        name=name,
        role=f"{name} role",
        agent_type="nanobot",
        skills=[REQUIRED_EMPLOYEE_SKILL_NAME],
        skill_ids=[REQUIRED_EMPLOYEE_SKILL_ID],
        tools=[],
        status="active",
    )
    for key, value in overrides.items():
        setattr(entry, key, value)
    return _registry(workspace).register(entry)


def _graph(*, edges: list[dict[str, str]], nodes: list[dict] | None = None, allow_skip: bool = False) -> dict:
    return {
        "version": 1,
        "settings": {"allow_skip_level_reporting": allow_skip},
        "nodes": nodes
        or [
            {"employee_id": "a", "x": 10, "y": 20},
            {"employee_id": "b", "x": 250, "y": 20},
            {"employee_id": "c", "x": 490, "y": 20},
        ],
        "edges": edges,
    }


def test_organization_validator_accepts_single_manager_forest_and_store_roundtrip(tmp_path: Path) -> None:
    graph = _graph(edges=[{"reporter_id": "a", "manager_id": "b"}, {"reporter_id": "b", "manager_id": "c"}])

    validation = OrganizationValidator.validate(graph, {"a", "b", "c"})
    assert validation["valid"] is True
    assert validation["errors"] == []

    store = OrganizationStore(tmp_path)
    saved = store.save(graph, employee_ids={"a", "b", "c"})
    loaded = store.load(employee_ids={"a", "b", "c"})

    assert saved["nodes"][0]["x"] == 10
    assert loaded["edges"] == graph["edges"]
    assert loaded["settings"]["allow_skip_level_reporting"] is False


@pytest.mark.parametrize(
    ("edges", "message"),
    [
        ([{"reporter_id": "a", "manager_id": "a"}], "cannot report to itself"),
        ([{"reporter_id": "a", "manager_id": "b"}, {"reporter_id": "a", "manager_id": "c"}], "multiple managers"),
        ([{"reporter_id": "a", "manager_id": "b"}, {"reporter_id": "b", "manager_id": "a"}], "cycle"),
        ([{"reporter_id": "a", "manager_id": "missing"}], "unknown employee"),
    ],
)
def test_organization_validator_rejects_invalid_relationships(edges: list[dict[str, str]], message: str) -> None:
    validation = OrganizationValidator.validate(_graph(edges=edges), {"a", "b", "c"})

    assert validation["valid"] is False
    assert any(message in error["message"] for error in validation["errors"])


def test_organization_store_cleans_deleted_employee_references_on_load(tmp_path: Path) -> None:
    store = OrganizationStore(tmp_path)
    store.save(_graph(edges=[{"reporter_id": "a", "manager_id": "b"}]), employee_ids={"a", "b", "c"})

    cleaned = store.load(employee_ids={"a", "c"}, clean=True)

    assert [node["employee_id"] for node in cleaned["nodes"]] == ["a", "c"]
    assert cleaned["edges"] == []


def test_organization_policy_blocks_skip_level_by_default_and_allows_overrides(tmp_path: Path) -> None:
    _seed_employee(tmp_path, "a", "Analyst")
    _seed_employee(tmp_path, "b", "Manager")
    _seed_employee(tmp_path, "c", "Director")
    OrganizationStore(tmp_path).save(
        _graph(
            edges=[{"reporter_id": "a", "manager_id": "b"}, {"reporter_id": "b", "manager_id": "c"}],
            nodes=[
                {"employee_id": "a", "allow_skip_level_reporting": False},
                {"employee_id": "b"},
                {"employee_id": "c"},
            ],
        ),
        employee_ids={"a", "b", "c"},
    )
    policy = OrganizationPolicy(_registry(tmp_path), OrganizationStore(tmp_path))

    assert policy.can_communicate("a", "b").allowed is True
    denied = policy.can_communicate("a", "c")
    assert denied.allowed is False
    assert "skip-level" in denied.reason

    OrganizationStore(tmp_path).save(
        _graph(
            edges=[{"reporter_id": "a", "manager_id": "b"}, {"reporter_id": "b", "manager_id": "c"}],
            nodes=[
                {"employee_id": "a", "allow_skip_level_reporting": True},
                {"employee_id": "b"},
                {"employee_id": "c"},
            ],
        ),
        employee_ids={"a", "b", "c"},
    )

    assert policy.can_communicate("a", "c").allowed is True
    assert policy.can_communicate("", "c").allowed is True


def test_organization_policy_allows_global_skip_level_override(tmp_path: Path) -> None:
    _seed_employee(tmp_path, "a", "Analyst")
    _seed_employee(tmp_path, "b", "Manager")
    _seed_employee(tmp_path, "c", "Director")
    OrganizationStore(tmp_path).save(
        _graph(
            edges=[{"reporter_id": "a", "manager_id": "b"}, {"reporter_id": "b", "manager_id": "c"}],
            allow_skip=True,
        ),
        employee_ids={"a", "b", "c"},
    )

    policy = OrganizationPolicy(_registry(tmp_path), OrganizationStore(tmp_path))

    decision = policy.can_communicate("a", "c")
    assert decision.allowed is True
    assert "global skip-level" in decision.reason


@pytest.mark.skipif(not HAS_AIOHTTP, reason="aiohttp not installed")
@pytest.mark.asyncio
async def test_admin_organization_api_saves_graph_and_employee_capabilities(aiohttp_client, tmp_path: Path) -> None:
    app = create_app(_make_agent(), model_name="test-model", workspace=tmp_path)
    _seed_employee(tmp_path, "a", "Analyst")
    _seed_employee(tmp_path, "b", "Manager")
    [skill] = SkillCatalogService(SkillCatalogStore(tmp_path)).upsert_many(
        [
            {
                "source": "clawhub",
                "external_id": "jira",
                "name": "JIRA",
                "description": "Manage tickets.",
                "source_url": "https://clawhub.ai/example/jira",
                "markdown": "---\nname: jira\ndescription: Manage tickets.\n---\n\n# JIRA\n",
            }
        ]
    )
    client = await aiohttp_client(app)

    put_resp = await client.put(
        "/admin/api/organization",
        json={
            "settings": {"allow_skip_level_reporting": False},
            "nodes": [
                {"employee_id": "a", "x": 10, "y": 20, "allow_skip_level_reporting": True},
                {"employee_id": "b", "x": 260, "y": 20},
            ],
            "edges": [{"reporter_id": "a", "manager_id": "b"}],
            "capabilities": [{"employee_id": "a", "skill_ids": [skill.id], "tools": ["message", "github"]}],
        },
    )

    assert put_resp.status == 200
    body = await put_resp.json()
    assert body["validation"]["valid"] is True
    assert body["edges"] == [{"reporter_id": "a", "manager_id": "b"}]
    updated = app["employee_registry"].get("a")
    assert updated is not None
    assert updated.skill_ids == [REQUIRED_EMPLOYEE_SKILL_ID, skill.id]
    assert updated.skills == [REQUIRED_EMPLOYEE_SKILL_NAME, "JIRA"]
    assert updated.tools == ["message", "github"]

    get_resp = await client.get("/admin/api/organization")
    assert get_resp.status == 200
    loaded = await get_resp.json()
    assert loaded["employees"][0]["tools"] == ["message", "github"]
    assert loaded["nodes"][0]["allow_skip_level_reporting"] is True


@pytest.mark.skipif(not HAS_AIOHTTP, reason="aiohttp not installed")
@pytest.mark.asyncio
async def test_admin_organization_api_rejects_invalid_graph(aiohttp_client, tmp_path: Path) -> None:
    app = create_app(_make_agent(), model_name="test-model", workspace=tmp_path)
    _seed_employee(tmp_path, "a", "Analyst")
    client = await aiohttp_client(app)

    resp = await client.put(
        "/admin/api/organization",
        json={"nodes": [{"employee_id": "a"}], "edges": [{"reporter_id": "a", "manager_id": "a"}]},
    )

    assert resp.status == 400
    body = await resp.json()
    assert any("cannot report to itself" in error["message"] for error in body["validation"]["errors"])


@pytest.mark.skipif(not HAS_AIOHTTP, reason="aiohttp not installed")
@pytest.mark.asyncio
async def test_admin_organization_api_rejects_invalid_capabilities_without_saving_graph(aiohttp_client, tmp_path: Path) -> None:
    app = create_app(_make_agent(), model_name="test-model", workspace=tmp_path)
    _seed_employee(tmp_path, "a", "Analyst")
    _seed_employee(tmp_path, "b", "Manager")
    client = await aiohttp_client(app)

    resp = await client.put(
        "/admin/api/organization",
        json={
            "nodes": [{"employee_id": "a"}, {"employee_id": "b"}],
            "edges": [{"reporter_id": "a", "manager_id": "b"}],
            "capabilities": [{"employee_id": "a", "skill_ids": ["missing-skill"]}],
        },
    )

    assert resp.status == 400
    body = await resp.json()
    assert "Invalid skill_ids" in body["error"]["message"]
    get_resp = await client.get("/admin/api/organization")
    loaded = await get_resp.json()
    assert loaded["edges"] == []


@pytest.mark.asyncio
async def test_openhire_delegate_blocks_skip_level_requester_before_container_execution(tmp_path: Path) -> None:
    _seed_employee(tmp_path, "a", "Analyst")
    _seed_employee(tmp_path, "b", "Manager")
    _seed_employee(tmp_path, "c", "Director")
    OrganizationStore(tmp_path).save(
        _graph(edges=[{"reporter_id": "a", "manager_id": "b"}, {"reporter_id": "b", "manager_id": "c"}]),
        employee_ids={"a", "b", "c"},
    )
    tool = OpenHireTool(
        workspace=tmp_path,
        openhire_config=OpenHireConfig(enabled=True),
        docker_agents_config=DockerAgentsConfig(enabled=True),
    )

    result = await tool.execute(action="delegate", requester_agent_id="a", agent_id="c", task="review")

    assert "Organization policy blocked delegate" in result
    assert "skip-level" in result


@pytest.mark.asyncio
async def test_openhire_delegate_uses_default_requester_context(tmp_path: Path) -> None:
    _seed_employee(tmp_path, "a", "Analyst")
    _seed_employee(tmp_path, "b", "Manager")
    _seed_employee(tmp_path, "c", "Director")
    OrganizationStore(tmp_path).save(
        _graph(edges=[{"reporter_id": "a", "manager_id": "b"}, {"reporter_id": "b", "manager_id": "c"}]),
        employee_ids={"a", "b", "c"},
    )
    tool = OpenHireTool(
        workspace=tmp_path,
        openhire_config=OpenHireConfig(enabled=True),
        docker_agents_config=DockerAgentsConfig(enabled=True),
    )
    tool.set_requester_agent_id("a")

    result = await tool.execute(action="delegate", agent_id="c", task="review")

    assert "Organization policy blocked delegate" in result
    assert "skip-level" in result


@pytest.mark.asyncio
async def test_openhire_route_filters_skip_level_targets(tmp_path: Path) -> None:
    _seed_employee(tmp_path, "a", "Analyst", owner_id="owner-a", group_ids=["group"])
    _seed_employee(tmp_path, "b", "Manager", owner_id="owner-b", group_ids=["group"])
    _seed_employee(tmp_path, "c", "Director", owner_id="owner-c", group_ids=["group"])
    OrganizationStore(tmp_path).save(
        _graph(edges=[{"reporter_id": "a", "manager_id": "b"}, {"reporter_id": "b", "manager_id": "c"}]),
        employee_ids={"a", "b", "c"},
    )
    tool = OpenHireTool(
        workspace=tmp_path,
        openhire_config=OpenHireConfig(enabled=True),
        docker_agents_config=DockerAgentsConfig(enabled=True),
    )

    result = await tool.execute(
        action="route",
        group_id="group",
        message="please review",
        mentions=["owner-b", "owner-c"],
        requester_agent_id="a",
    )

    assert "Route to: b" in result
    assert "c" not in result.split("Route to:", 1)[1].split("|", 1)[0]


@pytest.mark.asyncio
async def test_message_tool_blocks_explicit_skip_level_target(tmp_path: Path) -> None:
    _seed_employee(tmp_path, "a", "Analyst")
    _seed_employee(tmp_path, "b", "Manager")
    _seed_employee(tmp_path, "c", "Director")
    OrganizationStore(tmp_path).save(
        _graph(edges=[{"reporter_id": "a", "manager_id": "b"}, {"reporter_id": "b", "manager_id": "c"}]),
        employee_ids={"a", "b", "c"},
    )
    sent = []
    tool = MessageTool(
        send_callback=lambda msg: sent.append(msg),
        default_channel="feishu",
        default_chat_id="oc_group",
        organization_policy=OrganizationPolicy(_registry(tmp_path), OrganizationStore(tmp_path)),
    )

    result = await tool.execute(content="hello", requester_agent_id="a", target_agent_id="c")

    assert sent == []
    assert "Organization policy blocked message" in result


@pytest.mark.asyncio
async def test_message_tool_uses_default_requester_context(tmp_path: Path) -> None:
    _seed_employee(tmp_path, "a", "Analyst")
    _seed_employee(tmp_path, "b", "Manager")
    _seed_employee(tmp_path, "c", "Director")
    OrganizationStore(tmp_path).save(
        _graph(edges=[{"reporter_id": "a", "manager_id": "b"}, {"reporter_id": "b", "manager_id": "c"}]),
        employee_ids={"a", "b", "c"},
    )
    sent = []
    tool = MessageTool(
        send_callback=lambda msg: sent.append(msg),
        default_channel="feishu",
        default_chat_id="oc_group",
        organization_policy=OrganizationPolicy(_registry(tmp_path), OrganizationStore(tmp_path)),
    )
    tool.set_requester_agent_id("a")

    result = await tool.execute(content="hello", target_agent_id="c")

    assert sent == []
    assert "Organization policy blocked message" in result


@pytest.mark.asyncio
async def test_agent_loop_injects_requester_agent_id_from_inbound_metadata(tmp_path: Path) -> None:
    _seed_employee(tmp_path, "a", "Analyst")
    _seed_employee(tmp_path, "b", "Manager")
    _seed_employee(tmp_path, "c", "Director")
    OrganizationStore(tmp_path).save(
        _graph(edges=[{"reporter_id": "a", "manager_id": "b"}, {"reporter_id": "b", "manager_id": "c"}]),
        employee_ids={"a", "b", "c"},
    )
    provider = _OrganizationToolCallProvider()
    loop = AgentLoop(
        bus=MessageBus(),
        provider=provider,
        workspace=tmp_path,
        model="test-model",
        openhire_config=OpenHireConfig(enabled=True),
        docker_agents_config=DockerAgentsConfig(enabled=True),
    )

    response = await loop.process_direct(
        "delegate as employee",
        session_key="test:organization-requester",
        requester_agent_id="a",
    )

    assert response is not None
    assert "Organization policy blocked delegate" in response.content
    assert "skip-level" in response.content
