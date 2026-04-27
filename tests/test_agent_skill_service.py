from __future__ import annotations

import json
import zipfile
from pathlib import Path
from unittest.mock import AsyncMock, MagicMock

import pytest
import pytest_asyncio

from openhire.agent.skills import SkillsLoader
from openhire.agent_skill_service import (
    AgentSkillProtectedError,
    AgentSkillService,
    AgentSkillValidationError,
)
from openhire.api.server import create_app
from openhire.workforce.registry import AgentEntry
from openhire.workforce.required_skill import REQUIRED_EMPLOYEE_SKILL_ID

try:
    from aiohttp.test_utils import TestClient, TestServer

    HAS_AIOHTTP = True
except ImportError:
    HAS_AIOHTTP = False


def _skill_markdown(name: str, description: str = "Use this skill for tests.") -> str:
    return f"---\nname: {name}\ndescription: {description}\n---\n\n# {name}\n\n{description}\n"


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


def test_agent_skill_service_create_patch_file_package_and_loader_summary(tmp_path: Path) -> None:
    service = AgentSkillService(tmp_path, builtin_skills_dir=tmp_path / "builtin")

    created = service.create(
        name="Repo Workflow",
        description="Use this skill for repository release workflows.",
        resources=["scripts"],
    )

    assert created["skill"]["name"] == "repo-workflow"
    assert (tmp_path / "skills" / "repo-workflow" / "SKILL.md").exists()
    assert "repo-workflow" in SkillsLoader(tmp_path, builtin_skills_dir=tmp_path / "builtin").build_skills_summary()

    patched = service.patch(
        "repo-workflow",
        old_string="repository release workflows",
        new_string="repository verification workflows",
    )
    assert "verification workflows" in patched["markdown"]

    with pytest.raises(AgentSkillValidationError):
        service.write_file("repo-workflow", file_path="../outside.py", content="x")

    with pytest.raises(AgentSkillValidationError):
        service.write_file("repo-workflow", file_path="README.md", content="x")

    with_file = service.write_file(
        "repo-workflow",
        file_path="scripts/check.py",
        content="print('ok')\n",
    )
    assert {"path": "scripts/check.py", "type": "file", "size": 12} in with_file["files"]

    packaged = service.package("repo-workflow")
    package_path = Path(packaged["package_path"])
    assert package_path.exists()
    with zipfile.ZipFile(package_path, "r") as archive:
        assert "repo-workflow/SKILL.md" in archive.namelist()
        assert "repo-workflow/scripts/check.py" in archive.namelist()


def test_agent_skill_service_proposal_requires_approval_before_writing(tmp_path: Path) -> None:
    service = AgentSkillService(tmp_path, builtin_skills_dir=tmp_path / "builtin")

    proposal = service.create_proposal(
        {
            "action": "create",
            "name": "approved-workflow",
            "reason": "Agent completed a complex workflow.",
            "content": _skill_markdown("approved-workflow"),
        }
    )

    assert proposal["status"] == "pending"
    assert not (tmp_path / "skills" / "approved-workflow").exists()

    approved = service.approve_proposal(proposal["id"])

    assert approved["status"] == "approved"
    assert (tmp_path / "skills" / "approved-workflow" / "SKILL.md").exists()


def test_agent_skill_service_merges_duplicate_pending_auto_proposals(tmp_path: Path) -> None:
    service = AgentSkillService(tmp_path, builtin_skills_dir=tmp_path / "builtin")

    first = service.create_proposal(
        {
            "action": "create",
            "source": "turn",
            "name": "repeatable-flow",
            "reason": "The agent completed a complex workflow.",
            "trigger_reasons": ["complex_task_5_tool_calls"],
            "evidence": ["read_file -> edit_file -> pytest"],
            "content": _skill_markdown("repeatable-flow", "Use this repeatable flow."),
        }
    )
    second = service.create_proposal(
        {
            "action": "create",
            "source": "dream",
            "name": "repeatable-flow",
            "reason": "Dream saw the same workflow later.",
            "trigger_reasons": ["nontrivial_reusable_workflow"],
            "evidence": ["user reused the same release checklist"],
            "content": _skill_markdown("repeatable-flow", "Use this updated repeatable flow."),
        }
    )

    proposals = service.list_proposals()
    assert first["id"] == second["id"]
    assert len(proposals) == 1
    assert proposals[0]["source"] == "auto"
    assert proposals[0]["merged_count"] == 1
    assert proposals[0]["trigger_reasons"] == [
        "complex_task_5_tool_calls",
        "nontrivial_reusable_workflow",
    ]
    assert "Dream saw the same workflow later." in proposals[0]["reason"]
    assert proposals[0]["evidence"] == [
        "read_file -> edit_file -> pytest",
        "user reused the same release checklist",
    ]
    assert "updated repeatable flow" in proposals[0]["content"]


def test_agent_skill_service_does_not_merge_manual_or_approved_proposals(tmp_path: Path) -> None:
    service = AgentSkillService(tmp_path, builtin_skills_dir=tmp_path / "builtin")

    manual = service.create_proposal(
        {
            "action": "create",
            "name": "manual-flow",
            "reason": "Admin draft.",
            "content": _skill_markdown("manual-flow", "Manual proposal."),
        }
    )
    automatic = service.create_proposal(
        {
            "action": "create",
            "source": "turn",
            "name": "manual-flow",
            "reason": "Automatic proposal.",
            "content": _skill_markdown("manual-flow", "Automatic proposal."),
        }
    )

    assert manual["id"] != automatic["id"]
    assert len(service.list_proposals()) == 2

    approved = service.approve_proposal(automatic["id"])
    followup = service.create_proposal(
        {
            "action": "create",
            "source": "dream",
            "name": "manual-flow",
            "reason": "New automatic proposal after approval.",
            "content": _skill_markdown("manual-flow", "Follow-up proposal."),
        }
    )

    assert approved["status"] == "approved"
    assert followup["id"] != automatic["id"]
    assert len(service.list_proposals()) == 3


def test_agent_skill_service_protects_builtin_delete_and_deletes_workspace_shadow(tmp_path: Path) -> None:
    builtin = tmp_path / "builtin"
    (builtin / "shared").mkdir(parents=True)
    (builtin / "shared" / "SKILL.md").write_text(_skill_markdown("shared", "Built-in skill."), encoding="utf-8")
    service = AgentSkillService(tmp_path, builtin_skills_dir=builtin)

    with pytest.raises(AgentSkillProtectedError):
        service.delete("shared")

    service.create(name="shared", content=_skill_markdown("shared", "Workspace shadow."), overwrite=False)
    assert service.get("shared")["skill"]["source"] == "workspace"

    service.delete("shared")

    assert service.get("shared")["skill"]["source"] == "builtin"


@pytest.mark.skipif(not HAS_AIOHTTP, reason="aiohttp not installed")
@pytest.mark.asyncio
async def test_agent_skill_api_installs_catalog_skill_and_approves_proposal(
    aiohttp_client,
    tmp_path: Path,
) -> None:
    app = create_app(_make_agent(), model_name="test-model", workspace=tmp_path)
    client = await aiohttp_client(app)

    import_resp = await client.post(
        "/skills/import",
        json={
            "skills": [
                {
                    "source": "local",
                    "external_id": "catalog-tooling",
                    "name": "catalog-tooling",
                    "description": "Use catalog tooling.",
                    "markdown": _skill_markdown("catalog-tooling", "Use catalog tooling."),
                }
            ]
        },
    )
    assert import_resp.status == 201
    imported = await import_resp.json()

    install_resp = await client.post(
        "/admin/api/agent-skills",
        json={"catalog_skill_id": imported[0]["id"]},
    )
    assert install_resp.status == 201
    install_body = await install_resp.json()
    assert install_body["skill"]["name"] == "catalog-tooling"
    assert (tmp_path / "skills" / "catalog-tooling" / "SKILL.md").exists()

    list_resp = await client.get("/admin/api/agent-skills")
    assert list_resp.status == 200
    listed = await list_resp.json()
    assert any(item["name"] == "catalog-tooling" and item["source"] == "workspace" for item in listed)

    proposal_resp = await client.post(
        "/admin/api/agent-skills/proposals",
        json={
            "action": "create",
            "name": "approval-only",
            "reason": "agent generated candidate",
            "content": _skill_markdown("approval-only"),
        },
    )
    assert proposal_resp.status == 201
    proposal = await proposal_resp.json()
    assert not (tmp_path / "skills" / "approval-only").exists()

    approve_resp = await client.post(f"/admin/api/agent-skills/proposals/{proposal['id']}/approve")
    assert approve_resp.status == 200
    assert (await approve_resp.json())["status"] == "approved"
    assert (tmp_path / "skills" / "approval-only" / "SKILL.md").exists()

    state = json.loads((tmp_path / "openhire" / "agent_skill_proposals.json").read_text(encoding="utf-8"))
    assert state["proposals"][0]["status"] == "approved"


@pytest.mark.skipif(not HAS_AIOHTTP, reason="aiohttp not installed")
@pytest.mark.asyncio
async def test_agent_skill_bound_employee_counts_use_catalog_skill_ids(
    aiohttp_client,
    tmp_path: Path,
) -> None:
    app = create_app(_make_agent(), model_name="test-model", workspace=tmp_path)
    client = await aiohttp_client(app)

    import_resp = await client.post(
        "/skills/import",
        json={
            "skills": [
                {
                    "source": "local",
                    "external_id": "catalog-tooling",
                    "name": "Display Tooling",
                    "description": "Use catalog tooling.",
                    "markdown": _skill_markdown("catalog-tooling", "Use catalog tooling."),
                }
            ]
        },
    )
    assert import_resp.status == 201
    imported = await import_resp.json()
    catalog_skill_id = imported[0]["id"]

    install_resp = await client.post(
        "/admin/api/agent-skills",
        json={"catalog_skill_id": catalog_skill_id},
    )
    assert install_resp.status == 201

    app["employee_registry"].register(
        AgentEntry(
            name="Catalog Bound",
            role="Ops",
            skills=["Display name should not be the source of truth"],
            skill_ids=[catalog_skill_id],
        )
    )
    app["employee_registry"].register(
        AgentEntry(
            name="Required Bound",
            role="Ops",
            skills=["优秀员工协议"],
            skill_ids=[REQUIRED_EMPLOYEE_SKILL_ID],
        )
    )
    app["employee_registry"].register(
        AgentEntry(
            name="Legacy Bound",
            role="Ops",
            skills=["catalog-tooling"],
            skill_ids=[],
        )
    )
    app["employee_registry"].register(
        AgentEntry(
            name="Duplicate Bound",
            role="Ops",
            skills=["catalog-tooling"],
            skill_ids=[catalog_skill_id],
        )
    )

    list_resp = await client.get("/admin/api/agent-skills")
    assert list_resp.status == 200
    rows = {item["name"]: item for item in await list_resp.json()}

    assert rows["catalog-tooling"]["bound_employee_count"] == 3
    assert rows["excellent-employee"]["bound_employee_count"] == 1

    detail_resp = await client.get("/admin/api/agent-skills/catalog-tooling")
    assert detail_resp.status == 200
    detail = await detail_resp.json()
    assert detail["skill"]["bound_employee_count"] == 3
