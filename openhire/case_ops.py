"""Case operations governance for the admin UI."""

from __future__ import annotations

import json
import re
from collections import Counter, defaultdict
from collections.abc import Mapping
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from openhire.case_catalog import (
    CaseCatalogError,
    CaseCatalogService,
    CaseImportService,
    _find_case_employee,
    _find_case_skill,
)
from openhire.skill_catalog import SkillCatalogService
from openhire.workforce.registry import AgentEntry, AgentRegistry
from openhire.workforce.workspace import employee_workspace_path


_DEFAULT_CASE_OPS_STATE = {
    "last_report": None,
    "ignored_issue_ids": [],
    "audit_log": [],
}


def _now() -> str:
    return datetime.now(timezone.utc).isoformat(timespec="seconds")


def _text(value: Any, fallback: str = "") -> str:
    if value is None:
        return fallback
    value = str(value)
    return value if value else fallback


def _slug_part(value: Any) -> str:
    return re.sub(r"[^a-z0-9_-]+", "-", _text(value, "item").lower()).strip("-")[:80] or "item"


def _string_list(value: Any) -> list[str]:
    if not isinstance(value, list):
        return []
    return [_text(item) for item in value if _text(item)]


def _public_employee(entry: AgentEntry) -> dict[str, Any]:
    return entry.to_public_dict()


class CaseOpsStore:
    """Persist case ops reports, ignored issue IDs, and audit entries."""

    def __init__(self, workspace: Path) -> None:
        self._dir = workspace / "openhire"
        self._file = self._dir / "case_ops.json"

    def load(self) -> dict[str, Any]:
        if not self._file.exists():
            return dict(_DEFAULT_CASE_OPS_STATE)
        try:
            data = json.loads(self._file.read_text(encoding="utf-8"))
        except (json.JSONDecodeError, OSError):
            return dict(_DEFAULT_CASE_OPS_STATE)
        if not isinstance(data, dict):
            return dict(_DEFAULT_CASE_OPS_STATE)
        return {
            "last_report": data.get("last_report") if isinstance(data.get("last_report"), dict) else None,
            "ignored_issue_ids": [
                str(item) for item in data.get("ignored_issue_ids", []) if str(item or "").strip()
            ],
            "audit_log": [
                item for item in data.get("audit_log", []) if isinstance(item, dict)
            ][-50:],
        }

    def save(self, data: dict[str, Any]) -> None:
        self._dir.mkdir(parents=True, exist_ok=True)
        tmp = self._file.with_suffix(".tmp")
        tmp.write_text(json.dumps(data, indent=2, ensure_ascii=False), encoding="utf-8")
        tmp.replace(self._file)

    def save_report(self, report: dict[str, Any]) -> dict[str, Any]:
        state = self.load()
        state["last_report"] = report
        self.save(state)
        return state

    def set_ignored(self, issue_ids: list[str], ignored: bool) -> dict[str, Any]:
        state = self.load()
        current = {str(item) for item in state.get("ignored_issue_ids", [])}
        for issue_id in issue_ids:
            if ignored:
                current.add(str(issue_id))
            else:
                current.discard(str(issue_id))
        state["ignored_issue_ids"] = sorted(current)
        if isinstance(state.get("last_report"), dict):
            state["last_report"] = CaseOpsService.apply_ignored(
                state["last_report"],
                state["ignored_issue_ids"],
            )
        self.save(state)
        return state

    def append_audit(self, entry: dict[str, Any]) -> dict[str, Any]:
        state = self.load()
        audit_log = [item for item in state.get("audit_log", []) if isinstance(item, dict)]
        audit_log.append({"at": _now(), **entry})
        state["audit_log"] = audit_log[-50:]
        self.save(state)
        return state


class CaseOpsService:
    """Compute case import governance issues and bounded remediation plans."""

    def __init__(
        self,
        *,
        store: CaseOpsStore,
        case_catalog: CaseCatalogService,
        case_importer: CaseImportService,
        employee_registry: AgentRegistry,
        skill_catalog: SkillCatalogService,
        workspace: Path,
    ) -> None:
        self._store = store
        self._case_catalog = case_catalog
        self._case_importer = case_importer
        self._employee_registry = employee_registry
        self._skill_catalog = skill_catalog
        self._workspace = workspace

    @staticmethod
    def apply_ignored(report: dict[str, Any], ignored_issue_ids: list[str]) -> dict[str, Any]:
        ignored = set(ignored_issue_ids)
        next_report = dict(report)
        issues = []
        for issue in report.get("issues", []):
            if not isinstance(issue, dict):
                continue
            issue = dict(issue)
            issue["ignored"] = str(issue.get("id") or "") in ignored
            issues.append(issue)
        next_report["issues"] = issues
        summary = dict(next_report.get("summary") or {})
        summary["ignoredIssueCount"] = sum(1 for issue in issues if issue.get("ignored"))
        next_report["summary"] = summary
        next_report["ignoredIssueIds"] = sorted(ignored)
        return next_report

    def get_report(self) -> dict[str, Any]:
        state = self._store.load()
        report = state.get("last_report")
        if not isinstance(report, dict):
            report = self.build_report()
        return self.apply_ignored(report, state.get("ignored_issue_ids", []))

    def scan(self) -> dict[str, Any]:
        report = self.build_report()
        state = self._store.save_report(self.apply_ignored(report, self._store.load().get("ignored_issue_ids", [])))
        return self.apply_ignored(state["last_report"], state.get("ignored_issue_ids", []))

    def update_ignored(self, issue_ids: list[str], ignored: bool) -> dict[str, Any]:
        state = self._store.set_ignored(issue_ids, ignored)
        report = state.get("last_report") if isinstance(state.get("last_report"), dict) else self.build_report()
        return self.apply_ignored(report, state.get("ignored_issue_ids", []))

    def build_report(self) -> dict[str, Any]:
        raw_records, missing_catalog, load_error = self._load_case_records()
        valid_items: list[dict[str, Any]] = []
        issues: list[dict[str, Any]] = []
        if missing_catalog or (not raw_records and not load_error):
            issues.append(
                {
                    "id": "missing_catalog:cases",
                    "type": "missing_catalog",
                    "severity": "warning",
                    "title": "Case catalog missing",
                    "body": "No reusable case records are available in workspace/openhire/cases.json.",
                    "caseIds": [],
                    "ignored": False,
                }
            )
        if load_error:
            issues.append(
                {
                    "id": "invalid_case:catalog",
                    "type": "invalid_case",
                    "severity": "critical",
                    "title": "Case catalog cannot be parsed",
                    "body": load_error,
                    "caseIds": [],
                    "ignored": False,
                }
            )
        for index, record in enumerate(raw_records):
            try:
                case = self._case_catalog.normalize_import_payload(record)
            except CaseCatalogError as exc:
                issues.append(
                    {
                        "id": f"invalid_case:{index}",
                        "type": "invalid_case",
                        "severity": "critical",
                        "title": "Case package invalid",
                        "body": str(exc),
                        "caseIds": [],
                        "index": index,
                        "ignored": False,
                    }
                )
                continue
            valid_items.append({"case": case, "raw": record, "index": index})

        issues.extend(self._duplicate_case_issues(valid_items))
        import_summaries = []
        for item in valid_items:
            case = item["case"]
            import_summary = self._case_import_summary(case)
            import_summaries.append(import_summary)
            issues.extend(self._case_static_issues(case, item["raw"]))
            issues.extend(self._case_import_issues(case, import_summary))
        issues.extend(self._recent_import_issues())
        issues = self._dedupe_issues(issues)
        summary = self._summary(valid_items, import_summaries, issues)
        report = {
            "generatedAt": _now(),
            "source": str(self._case_catalog.source_file),
            "summary": summary,
            "issues": issues,
            "opportunities": self._opportunities(valid_items, import_summaries),
            "warnings": [],
            "auditLog": self._store.load().get("audit_log", []),
        }
        return self.apply_ignored(report, self._store.load().get("ignored_issue_ids", []))

    @staticmethod
    def _dedupe_issues(issues: list[dict[str, Any]]) -> list[dict[str, Any]]:
        result = []
        seen = set()
        for issue in issues:
            issue_id = str(issue.get("id") or "")
            if issue_id and issue_id in seen:
                continue
            if issue_id:
                seen.add(issue_id)
            result.append(issue)
        return result

    def _load_case_records(self) -> tuple[list[Any], bool, str]:
        source = self._case_catalog.source_file
        if not source.exists():
            return [], True, ""
        try:
            payload = json.loads(source.read_text(encoding="utf-8"))
        except json.JSONDecodeError as exc:
            return [], False, f"Invalid cases.json: {exc.msg}"
        except OSError as exc:
            return [], False, f"Failed to read cases.json: {exc}"
        if isinstance(payload, list):
            return payload, False, ""
        if isinstance(payload, Mapping):
            records = payload.get("cases", [])
            if not isinstance(records, list):
                return [], False, "cases.json field 'cases' must be an array."
            return records, False, ""
        return [], False, "cases.json must be an object or an array."

    def _duplicate_case_issues(self, valid_items: list[dict[str, Any]]) -> list[dict[str, Any]]:
        by_id: dict[str, list[dict[str, Any]]] = defaultdict(list)
        for item in valid_items:
            by_id[item["case"]["id"]].append(item)
        issues = []
        for case_id, group in by_id.items():
            if len(group) < 2:
                continue
            issues.append(
                {
                    "id": f"duplicate_case_id:{case_id}",
                    "type": "duplicate_case_id",
                    "severity": "critical",
                    "title": "Duplicate case id",
                    "body": f"{len(group)} case records normalize to '{case_id}'.",
                    "caseIds": [case_id],
                    "indexes": [item["index"] for item in group],
                    "ignored": False,
                }
            )
        return issues

    def _case_static_issues(self, case: dict[str, Any], raw_record: Any) -> list[dict[str, Any]]:
        issues: list[dict[str, Any]] = []
        skill_keys = {skill["key"] for skill in case["skills"]}
        unresolved = []
        for employee in case["employees"]:
            missing = [key for key in employee["skill_keys"] if key not in skill_keys]
            if missing:
                unresolved.append({"employeeKey": employee["key"], "missingSkillKeys": missing})
        if unresolved:
            issues.append(
                {
                    "id": f"unresolved_skill_ref:{case['id']}",
                    "type": "unresolved_skill_ref",
                    "severity": "critical",
                    "title": "Case employee references missing skills",
                    "body": f"{len(unresolved)} employee(s) reference skill_keys not defined by the case.",
                    "caseIds": [case["id"]],
                    "caseId": case["id"],
                    "employees": unresolved,
                    "ignored": False,
                }
            )
        missing_content = self._missing_content_skills(case, raw_record)
        if missing_content:
            issues.append(
                {
                    "id": f"missing_skill_content:{case['id']}",
                    "type": "missing_skill_content",
                    "severity": "warning",
                    "title": "Case skill content missing",
                    "body": f"{len(missing_content)} local or inline skill(s) do not include SKILL.md markdown.",
                    "caseIds": [case["id"]],
                    "caseId": case["id"],
                    "skills": missing_content,
                    "ignored": False,
                }
            )
        return issues

    def _missing_content_skills(self, case: dict[str, Any], raw_record: Any) -> list[dict[str, Any]]:
        if not isinstance(raw_record, Mapping):
            return []
        raw_skills = raw_record.get("skills")
        if not isinstance(raw_skills, list):
            return []
        normalized_by_index = list(case.get("skills") or [])
        missing = []
        for index, raw_skill in enumerate(raw_skills):
            if not isinstance(raw_skill, Mapping):
                continue
            source = _text(raw_skill.get("source"), "local").lower()
            if source not in {"local", "case"}:
                continue
            if _text(raw_skill.get("markdown")).strip():
                continue
            normalized = normalized_by_index[index] if index < len(normalized_by_index) else {}
            missing.append(
                {
                    "key": _text(normalized.get("key"), _slug_part(raw_skill.get("name") or index)),
                    "name": _text(normalized.get("name"), _text(raw_skill.get("name"), "skill")),
                    "source": source,
                }
            )
        return missing

    def _case_import_summary(self, case: dict[str, Any]) -> dict[str, Any]:
        employees = list(case.get("employees") or [])
        skills = list(case.get("skills") or [])
        imported_employees = [
            employee for employee in employees
            if _find_case_employee(self._employee_registry, case["id"], employee["key"]) is not None
        ]
        imported_skills = [
            skill for skill in skills
            if _find_case_skill(self._skill_catalog, skill) is not None
        ]
        preview = None
        preview_error = ""
        try:
            preview = self._case_importer.preview(case)
        except Exception as exc:  # pragma: no cover - defensive against runtime storage failures.
            preview_error = str(exc)
        return {
            "caseId": case["id"],
            "title": case["title"],
            "employeeCount": len(employees),
            "skillCount": len(skills),
            "importedEmployeeCount": len(imported_employees),
            "importedSkillCount": len(imported_skills),
            "isFullyImported": bool(employees) and len(imported_employees) == len(employees) and len(imported_skills) == len(skills),
            "isPartiallyImported": (len(imported_employees) + len(imported_skills)) > 0
            and not (bool(employees) and len(imported_employees) == len(employees) and len(imported_skills) == len(skills)),
            "preview": preview,
            "previewError": preview_error,
        }

    def _case_import_issues(self, case: dict[str, Any], summary: dict[str, Any]) -> list[dict[str, Any]]:
        issues: list[dict[str, Any]] = []
        if summary.get("previewError"):
            issues.append(
                {
                    "id": f"invalid_case:preview:{case['id']}",
                    "type": "invalid_case",
                    "severity": "critical",
                    "title": "Case preview failed",
                    "body": summary["previewError"],
                    "caseIds": [case["id"]],
                    "caseId": case["id"],
                    "ignored": False,
                }
            )
        if summary.get("isPartiallyImported"):
            issues.append(
                {
                    "id": f"partial_import:{case['id']}",
                    "type": "partial_import",
                    "severity": "warning",
                    "title": "Case partially imported",
                    "body": (
                        f"{summary['importedEmployeeCount']}/{summary['employeeCount']} employees and "
                        f"{summary['importedSkillCount']}/{summary['skillCount']} skills are present."
                    ),
                    "caseIds": [case["id"]],
                    "caseId": case["id"],
                    "ignored": False,
                }
            )
        preview = summary.get("preview") if isinstance(summary.get("preview"), Mapping) else {}
        overwrite_count = int(preview.get("overwrite_count") or 0) if isinstance(preview, Mapping) else 0
        if overwrite_count > 0:
            issues.append(
                {
                    "id": f"config_overwrite_risk:{case['id']}",
                    "type": "config_overwrite_risk",
                    "severity": "warning",
                    "title": "Case import would overwrite config",
                    "body": f"Preview found {overwrite_count} config file(s) that would be overwritten.",
                    "caseIds": [case["id"]],
                    "caseId": case["id"],
                    "overwriteCount": overwrite_count,
                    "ignored": False,
                }
            )
        drift = self._case_drift(case)
        if drift:
            issues.append(
                {
                    "id": f"import_drift:{case['id']}",
                    "type": "import_drift",
                    "severity": "warning",
                    "title": "Imported case drift detected",
                    "body": f"{len(drift)} imported employee or skill item(s) differ from the case package.",
                    "caseIds": [case["id"]],
                    "caseId": case["id"],
                    "drift": drift[:10],
                    "ignored": False,
                }
            )
        return issues

    def _case_drift(self, case: dict[str, Any]) -> list[dict[str, Any]]:
        drift: list[dict[str, Any]] = []
        skills_by_key = {skill["key"]: skill for skill in case.get("skills", [])}
        for skill in case.get("skills", []):
            existing = _find_case_skill(self._skill_catalog, skill)
            if not existing:
                continue
            fields = []
            for field in ("name", "description"):
                if _text(getattr(existing, field, "")) != _text(skill.get(field)):
                    fields.append(field)
            if _text(skill.get("markdown")).strip() and _text(existing.markdown).strip() and _text(existing.markdown).strip() != _text(skill.get("markdown")).strip():
                fields.append("markdown")
            if fields:
                drift.append({"kind": "skill", "key": skill["key"], "id": existing.id, "fields": fields})
        for employee in case.get("employees", []):
            existing = _find_case_employee(self._employee_registry, case["id"], employee["key"])
            if not existing:
                continue
            fields = []
            for field in ("name", "role", "agent_type"):
                if _text(getattr(existing, field, "")) != _text(employee.get(field)):
                    fields.append(field)
            expected_skill_names = [
                skills_by_key[key]["name"] for key in employee.get("skill_keys", []) if key in skills_by_key
            ] or list(employee.get("skills") or [])
            if expected_skill_names and not all(name in existing.skills for name in expected_skill_names):
                fields.append("skills")
            if list(existing.tools) != list(employee.get("tools") or []):
                fields.append("tools")
            config_drift = self._employee_config_drift(existing, employee)
            fields.extend(config_drift)
            if fields:
                drift.append({"kind": "employee", "key": employee["key"], "id": existing.agent_id, "fields": fields})
        return drift

    def _employee_config_drift(self, existing: AgentEntry, employee: Mapping[str, Any]) -> list[str]:
        drift = []
        resolver = getattr(self._case_importer, "_resolved_employee_config_files", None)
        config_files = resolver(employee) if callable(resolver) else employee.get("config_files")
        if not isinstance(config_files, Mapping):
            return drift
        base = employee_workspace_path(self._workspace, existing)
        for filename, expected in config_files.items():
            path = base / str(filename)
            try:
                current = path.read_text(encoding="utf-8")
            except OSError:
                current = ""
            if current != _text(expected):
                drift.append(f"config:{filename}")
        return drift

    def _recent_import_issues(self) -> list[dict[str, Any]]:
        issues = []
        for entry in self._store.load().get("audit_log", [])[-5:]:
            if entry.get("action") != "reimport_cases" or entry.get("status") not in {"partial", "failed"}:
                continue
            issues.append(
                {
                    "id": f"recent_import_failed:{_slug_part(entry.get('at'))}",
                    "type": "recent_import_failed",
                    "severity": "warning",
                    "title": "Recent case action needs review",
                    "body": f"Recent reimport finished with status {entry.get('status')}.",
                    "caseIds": _string_list(entry.get("caseIds")),
                    "ignored": False,
                }
            )
        return issues

    def _summary(
        self,
        valid_items: list[dict[str, Any]],
        import_summaries: list[dict[str, Any]],
        issues: list[dict[str, Any]],
    ) -> dict[str, Any]:
        counts = Counter(issue.get("type") for issue in issues)
        risk_types = {
            "invalid_case",
            "duplicate_case_id",
            "unresolved_skill_ref",
            "missing_skill_content",
            "partial_import",
            "import_drift",
            "config_overwrite_risk",
            "recent_import_failed",
        }
        return {
            "totalCaseCount": len(valid_items),
            "importableCaseCount": len(valid_items),
            "fullyImportedCaseCount": sum(1 for item in import_summaries if item.get("isFullyImported")),
            "partialImportCount": counts.get("partial_import", 0),
            "issueCount": len(issues),
            "riskIssueCount": sum(1 for issue in issues if issue.get("type") in risk_types),
            "configOverwriteRiskCount": counts.get("config_overwrite_risk", 0),
            "driftIssueCount": counts.get("import_drift", 0),
            "recentFailedImportCount": counts.get("recent_import_failed", 0),
            "ignoredIssueCount": 0,
        }

    def _opportunities(self, valid_items: list[dict[str, Any]], import_summaries: list[dict[str, Any]]) -> list[dict[str, Any]]:
        opportunities = [
            {
                "id": "case:import-config",
                "type": "import_config",
                "title": "Import external case config",
                "body": "Preview a case JSON before importing employees, skills, and config files.",
            },
            {
                "id": "case:export-selected",
                "type": "export_selected",
                "title": "Export selected employees",
                "body": "Build a reusable case JSON from selected persisted employees.",
            },
        ]
        summary_by_id = {item["caseId"]: item for item in import_summaries}
        for item in valid_items[:4]:
            case = item["case"]
            summary = summary_by_id.get(case["id"], {})
            opportunities.append(
                {
                    "id": f"case:open:{case['id']}",
                    "type": "open_case",
                    "title": f"Open {case['title']}",
                    "body": "Inspect the full case package and one-click import controls.",
                    "caseId": case["id"],
                }
            )
            if not summary.get("isFullyImported"):
                opportunities.append(
                    {
                        "id": f"case:reimport:{case['id']}",
                        "type": "reimport_cases",
                        "title": f"Preview reimport for {case['title']}",
                        "body": "Dry-run the case import before applying changes.",
                        "caseId": case["id"],
                    }
                )
        return opportunities[:8]

    def plan_action(
        self,
        *,
        action: str,
        issue_ids: list[str] | None = None,
        case_ids: list[str] | None = None,
    ) -> dict[str, Any]:
        if action != "reimport_cases":
            raise ValueError(f"Unsupported case ops action '{action}'.")
        selected_case_ids = self._selected_case_ids(issue_ids or [], case_ids or [])
        cases_by_id = self._valid_cases_by_id()
        rows = []
        totals = {
            "employeeCreates": 0,
            "employeeUpdates": 0,
            "skillCreates": 0,
            "skillUpdates": 0,
            "configOverwrites": 0,
        }
        for case_id in selected_case_ids:
            case = cases_by_id.get(case_id)
            if not case:
                rows.append({"caseId": case_id, "status": "failed", "error": "Case not found or invalid."})
                continue
            try:
                preview = self._case_importer.preview(case)
            except Exception as exc:
                rows.append({"caseId": case_id, "title": case.get("title", case_id), "status": "failed", "error": str(exc)})
                continue
            row = self._preview_row(case, preview)
            rows.append(row)
            for key in totals:
                totals[key] += int(row.get(key) or 0)
        status = "ok"
        if not rows:
            status = "empty"
        elif any(row.get("status") == "failed" for row in rows):
            status = "partial" if any(row.get("status") != "failed" for row in rows) else "failed"
        return {
            "action": action,
            "dryRun": True,
            "status": status,
            "caseIds": selected_case_ids,
            "cases": rows,
            "totals": totals,
        }

    async def execute_action(
        self,
        *,
        action: str,
        issue_ids: list[str] | None = None,
        case_ids: list[str] | None = None,
    ) -> dict[str, Any]:
        plan = self.plan_action(action=action, issue_ids=issue_ids, case_ids=case_ids)
        cases_by_id = self._valid_cases_by_id()
        results = []
        for case_id in plan.get("caseIds", []):
            case = cases_by_id.get(case_id)
            if not case:
                results.append({"caseId": case_id, "status": "failed", "error": "Case not found or invalid."})
                continue
            try:
                result = await self._case_importer.import_case(case)
            except Exception as exc:
                results.append({"caseId": case_id, "title": case.get("title", case_id), "status": "failed", "error": str(exc)})
                continue
            results.append({"caseId": case_id, "title": case.get("title", case_id), **result})
        status = self._result_status(results)
        state = self._store.append_audit(
            {
                "action": action,
                "status": status,
                "caseIds": plan.get("caseIds", []),
                "resultCount": len(results),
                "failedCount": sum(1 for item in results if item.get("status") in {"failed", "partial"}),
                "results": results,
            }
        )
        report = self.build_report()
        self._store.save_report(self.apply_ignored(report, state.get("ignored_issue_ids", [])))
        return {
            "action": action,
            "dryRun": False,
            "status": status,
            "caseIds": plan.get("caseIds", []),
            "cases": results,
        }

    def _selected_case_ids(self, issue_ids: list[str], case_ids: list[str]) -> list[str]:
        selected = [_text(case_id) for case_id in case_ids if _text(case_id)]
        if not selected and issue_ids:
            report = self.build_report()
            wanted = set(issue_ids)
            for issue in report.get("issues", []):
                if issue.get("id") not in wanted:
                    continue
                selected.extend(_string_list(issue.get("caseIds")))
                if issue.get("caseId"):
                    selected.append(_text(issue.get("caseId")))
        result = []
        seen = set()
        for case_id in selected:
            if not case_id or case_id in seen:
                continue
            seen.add(case_id)
            result.append(case_id)
        return result

    def _valid_cases_by_id(self) -> dict[str, dict[str, Any]]:
        records, _, _ = self._load_case_records()
        result = {}
        for record in records:
            try:
                case = self._case_catalog.normalize_import_payload(record)
            except CaseCatalogError:
                continue
            result.setdefault(case["id"], case)
        return result

    @staticmethod
    def _preview_row(case: dict[str, Any], preview: Mapping[str, Any]) -> dict[str, Any]:
        employees = preview.get("employees") if isinstance(preview, Mapping) else []
        skills = preview.get("skills") if isinstance(preview, Mapping) else []
        employees = employees if isinstance(employees, list) else []
        skills = skills if isinstance(skills, list) else []
        return {
            "caseId": case["id"],
            "title": case["title"],
            "status": "ok",
            "employeeCreates": sum(1 for item in employees if item.get("action") == "create"),
            "employeeUpdates": sum(1 for item in employees if item.get("action") == "update"),
            "skillCreates": sum(1 for item in skills if item.get("action") == "create"),
            "skillUpdates": sum(1 for item in skills if item.get("action") == "update"),
            "configOverwrites": int(preview.get("overwrite_count") or 0),
            "preview": preview,
        }

    @staticmethod
    def _result_status(results: list[dict[str, Any]]) -> str:
        if not results:
            return "empty"
        if any(item.get("status") == "partial" for item in results):
            return "partial"
        failed = [item for item in results if item.get("status") == "failed"]
        if not failed:
            return "ok"
        return "failed" if len(failed) == len(results) else "partial"
