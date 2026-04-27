from __future__ import annotations

import json
from pathlib import Path
from unittest.mock import AsyncMock, MagicMock

import pytest
import pytest_asyncio

from openhire.api.server import create_app
from openhire.case_catalog import CaseCatalogService, CaseCatalogStore
from openhire.config.schema import DockerAgentConfig, DockerAgentsConfig
from openhire.workforce.required_skill import (
    REQUIRED_EMPLOYEE_SKILL_ID,
    REQUIRED_EMPLOYEE_SKILL_PROMPT_START,
)

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
    agent.process_direct = AsyncMock(return_value="ok")
    agent._docker_agents_config = None
    agent.get_admin_snapshot = AsyncMock(
        return_value={
            "generatedAt": "2026-04-23T00:00:00Z",
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


def _write_cases(workspace, cases: list[dict]) -> None:
    case_dir = workspace / "openhire"
    case_dir.mkdir(parents=True, exist_ok=True)
    (case_dir / "cases.json").write_text(json.dumps({"cases": cases}, ensure_ascii=False), encoding="utf-8")


def _skill_markdown(name: str, description: str) -> str:
    return f"---\nname: {name}\ndescription: {description}\n---\n\n# {name}\n\n{description}\n"


class _FakeClawHubProvider:
    def __init__(self, markdown_by_url: dict[str, str]) -> None:
        self.markdown_by_url = markdown_by_url
        self.fetch_calls: list[str] = []

    async def fetch_skill_markdown(self, source_url: str) -> str:
        self.fetch_calls.append(source_url)
        return self.markdown_by_url[source_url]


class _FailingPromptSplitProvider:
    def __init__(self) -> None:
        self.calls = 0

    async def chat_with_retry(self, **_kwargs):
        self.calls += 1
        raise AssertionError("case import should not invoke prompt split")


def _case_record(*, config_suffix: str = "v1", second_employee: dict | None = None) -> dict:
    employees = [
        {
            "key": "product-director",
            "name": "产品总监",
            "role": "负责 PRD 范围冻结",
            "agent_type": "nanobot",
            "skill_keys": ["prd"],
            "system_prompt": "你是产品总监。",
            "config_files": {
                "SOUL.md": f"# 产品总监\n\n{config_suffix}",
                "AGENTS.md": "按 MVP、字段、验收口径推进。",
                "HEARTBEAT.md": "汇报待拍板问题。",
                "TOOLS.md": "message, read_file",
                "USER.md": "竞品价格监控看板",
            },
        }
    ]
    if second_employee:
        employees.append(second_employee)
    return {
        "id": "price-watch",
        "title": "竞品价格监控看板",
        "subtitle": "Feishu case",
        "description": "A complete case import package.",
        "skills": [
            {
                "key": "prd",
                "name": "PRD 范围冻结",
                "description": "Freeze MVP scope.",
                "markdown": "---\nname: PRD 范围冻结\ndescription: Freeze MVP scope.\n---\n\n# PRD\n",
            }
        ],
        "employees": employees,
    }


def _export_bundle_case_record() -> dict:
    return {
        "id": "price-watch",
        "title": "竞品价格监控看板",
        "subtitle": "Feishu case",
        "description": "A complete case import package.",
        "skills": [
            {
                "key": "prd",
                "name": "PRD 范围冻结",
                "description": "Freeze MVP scope.",
                "markdown": "---\nname: PRD 范围冻结\ndescription: Freeze MVP scope.\n---\n\n# PRD\n",
            },
            {
                "key": "qa",
                "name": "质量门禁",
                "description": "Ship with quality gates.",
                "markdown": "---\nname: 质量门禁\ndescription: Ship with quality gates.\n---\n\n# QA\n",
            },
        ],
        "employees": [
            {
                "key": "product-director",
                "name": "产品总监",
                "avatar": "coral-wave",
                "role": "负责 PRD 范围冻结",
                "agent_type": "nanobot",
                "skill_keys": ["prd"],
                "system_prompt": "你是产品总监。",
                "agent_config": {"mode": "review"},
                "tools": ["message", "read_file"],
                "config_files": {
                    "SOUL.md": "# 产品总监\n\nv1",
                    "AGENTS.md": "按 MVP、字段、验收口径推进。",
                    "HEARTBEAT.md": "汇报待拍板问题。",
                    "TOOLS.md": "message, read_file",
                    "USER.md": "竞品价格监控看板",
                },
            },
            {
                "key": "qa-director",
                "name": "测试总监",
                "avatar": "violet-signal",
                "role": "负责测试验收与发布门禁",
                "agent_type": "nanobot",
                "skill_keys": ["prd", "qa"],
                "system_prompt": "你是测试总监。",
                "agent_config": {"timezone": "Asia/Shanghai"},
                "tools": ["message", "read_file", "grep"],
                "config_files": {
                    "SOUL.md": "# 测试总监\n\n关注高风险质量点。",
                    "AGENTS.md": "同步验收口径、质量门和阻塞。",
                    "HEARTBEAT.md": "每轮同步质量状态。",
                    "TOOLS.md": "message, read_file, grep",
                    "USER.md": "重点盯导出一致性与告警可信度。",
                },
            },
        ],
    }


def test_repo_cases_json_contains_expected_built_in_case_packages() -> None:
    workspace = Path(__file__).resolve().parents[1]
    service = CaseCatalogService(CaseCatalogStore(workspace))

    cases = service.list_cases()

    assert len(cases) == 6
    ids = {case["id"] for case in cases}
    expected_new_ids = {
        "finance-investment-copilot",
        "software-delivery-command",
        "ecommerce-growth-ops",
        "vertical-consulting-workbench",
        "knowledge-ops-content-matrix",
    }
    assert expected_new_ids.issubset(ids)

    for case in cases:
        if case["id"] not in expected_new_ids:
            continue
        assert len(case["employees"]) >= 1
        employee_keys = [employee["key"] for employee in case["employees"]]
        skill_keys = [skill["key"] for skill in case["skills"]]
        assert len(employee_keys) == len(set(employee_keys))
        assert len(skill_keys) == len(set(skill_keys))
        assert all(skill["source"] == "case" for skill in case["skills"])


@pytest.mark.skipif(not HAS_AIOHTTP, reason="aiohttp not installed")
@pytest.mark.asyncio
async def test_cases_endpoint_seeds_builtin_cases_when_cases_file_missing(aiohttp_client, tmp_path) -> None:
    app = create_app(_make_agent(), model_name="test-model", workspace=tmp_path)
    client = await aiohttp_client(app)

    resp = await client.get("/admin/api/cases")

    assert resp.status == 200
    body = await resp.json()
    assert len(body["cases"]) == 6
    assert body["source"] == str(tmp_path / "openhire" / "cases.json")
    assert (tmp_path / "openhire" / "cases.json").exists()
    assert {case["id"] for case in body["cases"]} >= {
        "competitor-price-monitoring",
        "finance-investment-copilot",
        "software-delivery-command",
    }


@pytest.mark.skipif(not HAS_AIOHTTP, reason="aiohttp not installed")
@pytest.mark.asyncio
async def test_case_ops_uses_seeded_builtin_cases_when_cases_file_missing(aiohttp_client, tmp_path) -> None:
    app = create_app(_make_agent(), model_name="test-model", workspace=tmp_path)
    client = await aiohttp_client(app)

    resp = await client.get("/admin/api/cases/ops")

    assert resp.status == 200
    report = await resp.json()
    assert report["source"] == str(tmp_path / "openhire" / "cases.json")
    assert report["summary"]["totalCaseCount"] == 6
    assert "missing_catalog" not in {issue["type"] for issue in report["issues"]}


@pytest.mark.skipif(not HAS_AIOHTTP, reason="aiohttp not installed")
@pytest.mark.asyncio
async def test_cases_endpoint_rejects_invalid_cases_json(aiohttp_client, tmp_path) -> None:
    case_dir = tmp_path / "openhire"
    case_dir.mkdir(parents=True)
    (case_dir / "cases.json").write_text("{not json", encoding="utf-8")
    app = create_app(_make_agent(), model_name="test-model", workspace=tmp_path)
    client = await aiohttp_client(app)

    resp = await client.get("/admin/api/cases")

    assert resp.status == 400
    body = await resp.json()
    assert "Invalid cases.json" in body["error"]["message"]


@pytest.mark.skipif(not HAS_AIOHTTP, reason="aiohttp not installed")
@pytest.mark.asyncio
async def test_case_ops_scan_persists_issues_and_ignore_state(aiohttp_client, tmp_path) -> None:
    bad_ref_case = _case_record()
    bad_ref_case["id"] = "bad-ref"
    bad_ref_case["skills"] = [
        {
            "key": "defined",
            "source": "case",
            "name": "缺内容技能",
            "description": "No markdown is packaged.",
        }
    ]
    bad_ref_case["employees"][0]["key"] = "bad-ref-owner"
    bad_ref_case["employees"][0]["skill_keys"] = ["missing"]
    _write_cases(
        tmp_path,
        [
            _case_record(),
            {**_case_record(), "title": "duplicate id"},
            {"id": "broken", "title": "Broken", "skills": [], "employees": []},
            bad_ref_case,
        ],
    )
    app = create_app(_make_agent(), model_name="test-model", workspace=tmp_path)
    client = await aiohttp_client(app)

    scan_resp = await client.post("/admin/api/cases/ops/scan")

    assert scan_resp.status == 200
    report = await scan_resp.json()
    issue_types = {issue["type"] for issue in report["issues"]}
    assert {
        "duplicate_case_id",
        "invalid_case",
        "unresolved_skill_ref",
        "missing_skill_content",
    }.issubset(issue_types)
    assert report["summary"]["totalCaseCount"] == 3
    assert report["summary"]["riskIssueCount"] >= 4
    assert (tmp_path / "openhire" / "case_ops.json").exists()

    issue_id = next(issue["id"] for issue in report["issues"] if issue["type"] == "unresolved_skill_ref")
    ignore_resp = await client.post(
        "/admin/api/cases/ops/ignore",
        json={"issue_ids": [issue_id], "ignored": True},
    )

    assert ignore_resp.status == 200
    ignored_report = await ignore_resp.json()
    ignored_issue = next(issue for issue in ignored_report["issues"] if issue["id"] == issue_id)
    assert ignored_issue["ignored"] is True
    assert ignored_report["summary"]["ignoredIssueCount"] == 1

    get_resp = await client.get("/admin/api/cases/ops")
    assert get_resp.status == 200
    persisted = await get_resp.json()
    assert next(issue for issue in persisted["issues"] if issue["id"] == issue_id)["ignored"] is True


@pytest.mark.skipif(not HAS_AIOHTTP, reason="aiohttp not installed")
@pytest.mark.asyncio
async def test_case_ops_reimport_dry_run_and_execute_repairs_drift(aiohttp_client, tmp_path) -> None:
    _write_cases(tmp_path, [_case_record(config_suffix="v1")])
    agent = _make_agent()
    agent.provider = _FailingPromptSplitProvider()
    app = create_app(agent, model_name="test-model", workspace=tmp_path)
    client = await aiohttp_client(app)

    import_resp = await client.post("/admin/api/cases/price-watch/import")
    assert import_resp.status == 201
    imported = await import_resp.json()
    employee_id = imported["employees"][0]["id"]
    soul_file = tmp_path / "openhire" / "employees" / employee_id / "workspace" / "SOUL.md"
    assert soul_file.read_text(encoding="utf-8").endswith("v1")

    _write_cases(tmp_path, [_case_record(config_suffix="v2")])
    scan_resp = await client.post("/admin/api/cases/ops/scan")
    assert scan_resp.status == 200
    report = await scan_resp.json()
    issue_types = {issue["type"] for issue in report["issues"]}
    assert "config_overwrite_risk" in issue_types
    assert "import_drift" in issue_types
    issue_ids = [issue["id"] for issue in report["issues"] if issue["type"] in {"config_overwrite_risk", "import_drift"}]

    dry_run_resp = await client.post(
        "/admin/api/cases/ops/actions",
        json={"action": "reimport_cases", "issue_ids": issue_ids, "dry_run": True},
    )

    assert dry_run_resp.status == 200
    preview = await dry_run_resp.json()
    assert preview["dryRun"] is True
    assert preview["status"] == "ok"
    assert preview["totals"]["employeeUpdates"] == 1
    assert preview["totals"]["configOverwrites"] >= 1
    assert soul_file.read_text(encoding="utf-8").endswith("v1")

    unconfirmed_resp = await client.post(
        "/admin/api/cases/ops/actions",
        json={"action": "reimport_cases", "issue_ids": issue_ids, "dry_run": False},
    )
    assert unconfirmed_resp.status == 400

    execute_resp = await client.post(
        "/admin/api/cases/ops/actions",
        json={"action": "reimport_cases", "issue_ids": issue_ids, "dry_run": False, "confirm": True},
    )

    assert execute_resp.status == 200
    result = await execute_resp.json()
    assert result["dryRun"] is False
    assert result["status"] == "ok"
    assert soul_file.read_text(encoding="utf-8").endswith("v2")

    state = json.loads((tmp_path / "openhire" / "case_ops.json").read_text(encoding="utf-8"))
    assert state["audit_log"][-1]["action"] == "reimport_cases"
    assert state["audit_log"][-1]["status"] == "ok"
    refreshed = await (await client.get("/admin/api/cases/ops")).json()
    refreshed_types = {issue["type"] for issue in refreshed["issues"]}
    assert "import_drift" not in refreshed_types


@pytest.mark.skipif(not HAS_AIOHTTP, reason="aiohttp not installed")
@pytest.mark.asyncio
async def test_case_import_previews_imports_and_reimports_idempotently(aiohttp_client, tmp_path) -> None:
    _write_cases(tmp_path, [_case_record()])
    agent = _make_agent()
    provider = _FailingPromptSplitProvider()
    agent.provider = provider
    app = create_app(agent, model_name="test-model", workspace=tmp_path)
    client = await aiohttp_client(app)

    summary_resp = await client.get("/admin/api/cases")
    assert summary_resp.status == 200
    summary = await summary_resp.json()
    assert summary["cases"][0]["employee_count"] == 1
    assert summary["cases"][0]["skill_count"] == 1
    assert summary["cases"][0]["is_imported"] is False

    detail_resp = await client.get("/admin/api/cases/price-watch")
    assert detail_resp.status == 200
    detail = await detail_resp.json()
    assert detail["employees"][0]["config_files"]["SOUL.md"].endswith("v1")

    preview_resp = await client.post("/admin/api/cases/price-watch/import/preview")
    assert preview_resp.status == 200
    preview = await preview_resp.json()
    assert preview["skills"][0]["action"] == "create"
    assert preview["skills"][0]["source"] == "local"
    assert preview["employees"][0]["action"] == "create"

    import_resp = await client.post("/admin/api/cases/price-watch/import")
    assert import_resp.status == 201
    imported = await import_resp.json()
    assert imported["status"] == "ok"
    employee_id = imported["employees"][0]["id"]

    employees_resp = await client.get("/employees")
    employees = await employees_resp.json()
    assert len(employees) == 1
    assert employees[0]["id"] == employee_id
    assert employees[0]["skill_ids"][0] == REQUIRED_EMPLOYEE_SKILL_ID
    assert len(employees[0]["skill_ids"]) == 2
    assert employees[0]["agent_config"]["case_import"] == {
        "case_id": "price-watch",
        "employee_key": "product-director",
    }
    assert (
        tmp_path
        / "openhire"
        / "employees"
        / employee_id
        / "workspace"
        / "SOUL.md"
    ).read_text(encoding="utf-8").endswith("v1")
    assert REQUIRED_EMPLOYEE_SKILL_PROMPT_START not in (
        tmp_path / "openhire" / "employees" / employee_id / "workspace" / "SOUL.md"
    ).read_text(encoding="utf-8")
    agents_text = (
        tmp_path / "openhire" / "employees" / employee_id / "workspace" / "AGENTS.md"
    ).read_text(encoding="utf-8")
    assert agents_text.startswith("按 MVP、字段、验收口径推进。")
    assert REQUIRED_EMPLOYEE_SKILL_PROMPT_START in agents_text
    assert (tmp_path / "openhire" / "employees" / employee_id / "workspace" / "HEARTBEAT.md").read_text(encoding="utf-8") == "汇报待拍板问题。"
    assert (tmp_path / "openhire" / "employees" / employee_id / "workspace" / "TOOLS.md").read_text(encoding="utf-8") == "message, read_file"
    assert (tmp_path / "openhire" / "employees" / employee_id / "workspace" / "USER.md").read_text(encoding="utf-8") == "竞品价格监控看板"
    assert provider.calls == 0

    _write_cases(tmp_path, [_case_record(config_suffix="v2")])
    preview_again_resp = await client.post("/admin/api/cases/price-watch/import/preview")
    preview_again = await preview_again_resp.json()
    assert preview_again["skills"][0]["action"] == "update"
    assert preview_again["employees"][0]["action"] == "update"
    assert {"name": "SOUL.md", "action": "overwrite"} in preview_again["employees"][0]["config_files"]

    import_again_resp = await client.post("/admin/api/cases/price-watch/import")
    assert import_again_resp.status == 201
    employees_again = await (await client.get("/employees")).json()
    assert len(employees_again) == 1
    assert employees_again[0]["id"] == employee_id
    assert (
        tmp_path
        / "openhire"
        / "employees"
        / employee_id
        / "workspace"
        / "SOUL.md"
    ).read_text(encoding="utf-8").endswith("v2")


@pytest.mark.skipif(not HAS_AIOHTTP, reason="aiohttp not installed")
@pytest.mark.asyncio
async def test_employee_export_returns_case_compatible_bundle_and_roundtrips(aiohttp_client, tmp_path) -> None:
    _write_cases(tmp_path, [_export_bundle_case_record()])
    agent = _make_agent()
    agent.provider = _FailingPromptSplitProvider()
    app = create_app(agent, model_name="test-model", workspace=tmp_path)
    client = await aiohttp_client(app)

    import_resp = await client.post("/admin/api/cases/price-watch/import")
    assert import_resp.status == 201
    imported = await import_resp.json()
    employee_ids = [employee["id"] for employee in imported["employees"]]

    export_resp = await client.post("/admin/api/employees/export", json={"employee_ids": employee_ids})

    assert export_resp.status == 200
    body = await export_resp.json()
    exported_case = body["case"]
    assert exported_case["id"] == "price-watch"
    assert exported_case["title"] == "竞品价格监控看板"
    assert exported_case["input"] == {}
    assert exported_case["output"] == {}
    assert exported_case["workflow"] == []
    assert exported_case["tags"] == []
    assert exported_case["metrics"] == []

    skills_by_key = {skill["key"]: skill for skill in exported_case["skills"]}
    assert set(skills_by_key) == {"prd", "qa"}
    assert all(skill["markdown"] for skill in exported_case["skills"])
    assert all(skill["key"] != REQUIRED_EMPLOYEE_SKILL_ID for skill in exported_case["skills"])

    employees_by_key = {employee["key"]: employee for employee in exported_case["employees"]}
    assert set(employees_by_key) == {"product-director", "qa-director"}
    assert employees_by_key["product-director"]["skill_keys"] == ["prd"]
    assert employees_by_key["qa-director"]["skill_keys"] == ["prd", "qa"]
    assert employees_by_key["product-director"]["tools"] == ["message", "read_file"]
    assert employees_by_key["qa-director"]["tools"] == ["message", "read_file", "grep"]
    assert employees_by_key["product-director"]["config_files"]["SOUL.md"].endswith("v1")
    assert employees_by_key["qa-director"]["config_files"]["USER.md"] == "重点盯导出一致性与告警可信度。"
    assert employees_by_key["product-director"]["agent_config"] == {"mode": "review"}
    assert employees_by_key["qa-director"]["agent_config"] == {"timezone": "Asia/Shanghai"}
    assert all("case_import" not in employee["agent_config"] for employee in exported_case["employees"])
    assert all("id" not in employee for employee in exported_case["employees"])
    assert all("container_name" not in employee for employee in exported_case["employees"])

    roundtrip_workspace = tmp_path / "roundtrip"
    _write_cases(roundtrip_workspace, [exported_case])
    roundtrip_app = create_app(_make_agent(), model_name="test-model", workspace=roundtrip_workspace)
    roundtrip_client = await aiohttp_client(roundtrip_app)

    preview_resp = await roundtrip_client.post("/admin/api/cases/price-watch/import/preview")
    assert preview_resp.status == 200
    preview = await preview_resp.json()
    assert [employee["action"] for employee in preview["employees"]] == ["create", "create"]
    assert {skill["action"] for skill in preview["skills"]} == {"create"}

    roundtrip_import_resp = await roundtrip_client.post("/admin/api/cases/price-watch/import")
    assert roundtrip_import_resp.status == 201
    roundtrip_employees = await (await roundtrip_client.get("/employees")).json()
    assert len(roundtrip_employees) == 2


@pytest.mark.skipif(not HAS_AIOHTTP, reason="aiohttp not installed")
@pytest.mark.asyncio
async def test_case_config_import_endpoints_accept_exported_single_case_json(aiohttp_client, tmp_path) -> None:
    exported_case = _export_bundle_case_record()
    app = create_app(_make_agent(), model_name="test-model", workspace=tmp_path)
    client = await aiohttp_client(app)

    preview_resp = await client.post("/admin/api/cases/import/preview", json=exported_case)

    assert preview_resp.status == 200
    preview_body = await preview_resp.json()
    assert preview_body["case"]["id"] == "price-watch"
    assert [employee["action"] for employee in preview_body["preview"]["employees"]] == ["create", "create"]
    assert {skill["action"] for skill in preview_body["preview"]["skills"]} == {"create"}

    import_resp = await client.post("/admin/api/cases/import", json=exported_case)

    assert import_resp.status == 201
    imported = await import_resp.json()
    assert imported["case"]["id"] == "price-watch"
    assert imported["status"] == "ok"
    employees = await (await client.get("/employees")).json()
    assert len(employees) == 2
    assert all(employee["skill_ids"][0] == REQUIRED_EMPLOYEE_SKILL_ID for employee in employees)


@pytest.mark.skipif(not HAS_AIOHTTP, reason="aiohttp not installed")
@pytest.mark.asyncio
async def test_case_config_import_accepts_exported_json_without_preview(aiohttp_client, tmp_path) -> None:
    exported_case = _export_bundle_case_record()
    app = create_app(_make_agent(), model_name="test-model", workspace=tmp_path)
    client = await aiohttp_client(app)

    import_resp = await client.post("/admin/api/cases/import", json=exported_case)

    assert import_resp.status == 201
    imported = await import_resp.json()
    assert imported["case"]["id"] == "price-watch"
    assert imported["status"] == "ok"
    employees = await (await client.get("/employees")).json()
    assert len(employees) == 2


@pytest.mark.skipif(not HAS_AIOHTTP, reason="aiohttp not installed")
@pytest.mark.asyncio
async def test_case_import_returns_partial_when_one_employee_fails(aiohttp_client, tmp_path) -> None:
    _write_cases(
        tmp_path,
        [
            _case_record(
                second_employee={
                    "key": "bad-runtime",
                    "name": "坏员工",
                    "role": "invalid runtime",
                    "agent_type": "missing-agent",
                    "skill_keys": ["prd"],
                    "system_prompt": "bad",
                    "config_files": {"SOUL.md": "bad"},
                }
            )
        ],
    )
    app = create_app(_make_agent(), model_name="test-model", workspace=tmp_path)
    client = await aiohttp_client(app)

    resp = await client.post("/admin/api/cases/price-watch/import")

    assert resp.status == 207
    body = await resp.json()
    assert body["status"] == "partial"
    assert body["failed_count"] == 1
    assert [item["action"] for item in body["employees"]] == ["created", "failed"]
    employees = await (await client.get("/employees")).json()
    assert len(employees) == 1
    skills = await (await client.get("/skills")).json()
    assert any(skill["source"] == "local" and skill["external_id"] == "price-watch:prd" for skill in skills)


@pytest.mark.skipif(not HAS_AIOHTTP, reason="aiohttp not installed")
@pytest.mark.asyncio
async def test_case_import_can_directly_import_clawhub_skill(aiohttp_client, tmp_path) -> None:
    source_url = "https://clawhub.ai/test/prd-freeze"
    case = _case_record()
    case["skills"][0] = {
        "key": "prd",
        "source": "clawhub",
        "external_id": "prd-freeze",
        "name": "PRD Freeze",
        "description": "Freeze product scope.",
        "source_url": source_url,
    }
    _write_cases(tmp_path, [case])
    provider = _FakeClawHubProvider({source_url: _skill_markdown("prd-freeze", "Freeze product scope.")})
    app = create_app(_make_agent(), model_name="test-model", workspace=tmp_path, skill_provider=provider)
    client = await aiohttp_client(app)

    preview_resp = await client.post("/admin/api/cases/price-watch/import/preview")
    preview = await preview_resp.json()
    assert preview["skills"][0]["source"] == "clawhub"
    assert preview["skills"][0]["action"] == "create"

    resp = await client.post("/admin/api/cases/price-watch/import")

    assert resp.status == 201
    body = await resp.json()
    assert body["skills"][0]["source"] == "clawhub"
    assert provider.fetch_calls == [source_url]
    employees = await (await client.get("/employees")).json()
    assert employees[0]["skill_ids"][0] == REQUIRED_EMPLOYEE_SKILL_ID
    assert employees[0]["skill_ids"][1] == body["skills"][0]["id"]
    skills = await (await client.get("/skills")).json()
    assert any(skill["source"] == "clawhub" and skill["external_id"] == "prd-freeze" for skill in skills)


@pytest.mark.skipif(not HAS_AIOHTTP, reason="aiohttp not installed")
@pytest.mark.asyncio
async def test_case_import_can_directly_import_inline_case_skill(aiohttp_client, tmp_path) -> None:
    case = _case_record()
    case["skills"][0] = {
        "key": "prd",
        "source": "case",
        "name": "PRD 范围冻结",
        "description": "Freeze MVP scope.",
        "markdown": _skill_markdown("PRD 范围冻结", "Freeze MVP scope."),
    }
    _write_cases(tmp_path, [case])
    app = create_app(_make_agent(), model_name="test-model", workspace=tmp_path)
    client = await aiohttp_client(app)

    preview_resp = await client.post("/admin/api/cases/price-watch/import/preview")
    preview = await preview_resp.json()
    assert preview["skills"][0]["source"] == "case"
    assert preview["skills"][0]["action"] == "create"

    resp = await client.post("/admin/api/cases/price-watch/import")

    assert resp.status == 201
    body = await resp.json()
    assert body["skills"][0]["source"] == "case"
    employees = await (await client.get("/employees")).json()
    assert employees[0]["skill_ids"][0] == REQUIRED_EMPLOYEE_SKILL_ID
    assert employees[0]["skill_ids"][1] == body["skills"][0]["id"]
    skills = await (await client.get("/skills")).json()
    assert any(skill["source"] == "case" and skill["external_id"] == "price-watch:prd" for skill in skills)


@pytest.mark.skipif(not HAS_AIOHTTP, reason="aiohttp not installed")
@pytest.mark.asyncio
async def test_case_import_missing_files_fall_back_to_default_bootstrap(aiohttp_client, tmp_path) -> None:
    case = _case_record()
    case["employees"][0]["config_files"] = {
        "SOUL.md": "Only soul from case",
    }
    _write_cases(tmp_path, [case])
    agent = _make_agent()
    agent.provider = _FailingPromptSplitProvider()
    app = create_app(agent, model_name="test-model", workspace=tmp_path)
    client = await aiohttp_client(app)

    resp = await client.post("/admin/api/cases/price-watch/import")

    assert resp.status == 201
    employee_id = (await resp.json())["employees"][0]["id"]
    employee_workspace = tmp_path / "openhire" / "employees" / employee_id / "workspace"
    assert (employee_workspace / "SOUL.md").read_text(encoding="utf-8") == "Only soul from case"
    assert (employee_workspace / "AGENTS.md").read_text(encoding="utf-8").startswith("# Agent Instructions")
    assert REQUIRED_EMPLOYEE_SKILL_PROMPT_START in (employee_workspace / "AGENTS.md").read_text(encoding="utf-8")
    assert (employee_workspace / "HEARTBEAT.md").read_text(encoding="utf-8") == ""
    assert (employee_workspace / "USER.md").read_text(encoding="utf-8") == ""


@pytest.mark.skipif(not HAS_AIOHTTP, reason="aiohttp not installed")
@pytest.mark.asyncio
async def test_case_import_follows_existing_docker_container_creation(
    aiohttp_client,
    tmp_path,
    monkeypatch,
) -> None:
    _write_cases(tmp_path, [_case_record()])
    agent = _make_agent()
    agent._docker_agents_config = DockerAgentsConfig(
        enabled=True,
        agents={"nanobot": DockerAgentConfig(enabled=True, persistent=True)},
    )
    calls: list[dict] = []

    async def fake_ensure_running(adapter, instance_name, agent_cfg, workspace):
        calls.append({
            "agent": adapter.agent_name,
            "instance": instance_name,
            "container": agent_cfg["container_name"],
            "workspace": workspace,
        })
        return agent_cfg["container_name"]

    monkeypatch.setattr("openhire.workforce.lifecycle.ensure_running", fake_ensure_running)
    app = create_app(agent, model_name="test-model", workspace=tmp_path)
    client = await aiohttp_client(app)

    resp = await client.post("/admin/api/cases/price-watch/import")

    assert resp.status == 201
    assert len(calls) == 1
    assert calls[0]["agent"] == "nanobot"
    assert calls[0]["container"].startswith("openhire-")
