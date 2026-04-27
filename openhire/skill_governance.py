"""Skill catalog discovery and governance helpers for the admin surface."""

from __future__ import annotations

from collections import Counter, defaultdict
from datetime import datetime, timezone
import json
from pathlib import Path
import re
from typing import Any, Mapping

from openhire.skill_catalog import SkillCatalogService, SkillEntry
from openhire.workforce.registry import AgentEntry, AgentRegistry
from openhire.workforce.required_skill import REQUIRED_EMPLOYEE_SKILL_ID


_DEFAULT_GOVERNANCE_STATE = {
    "last_report": None,
    "ignored_issue_ids": [],
    "audit_log": [],
}
_ROLE_QUERY_ALIASES = (
    ("邮箱", "gmail"),
    ("邮件", "gmail"),
    ("message", "slack"),
    ("消息", "slack"),
    ("会议", "calendar"),
    ("日程", "calendar"),
    ("前端", "react"),
    ("frontend", "react"),
    ("后端", "python"),
    ("backend", "python"),
    ("数据", "spreadsheet"),
    ("分析", "spreadsheet"),
    ("运营", "browser"),
    ("巡检", "monitor"),
    ("工单", "jira"),
    ("客服", "zendesk"),
)


def _now() -> str:
    return datetime.now(timezone.utc).isoformat(timespec="seconds")


def _norm(value: Any) -> str:
    return re.sub(r"\s+", " ", str(value or "").strip().casefold())


def _stable_part(value: Any) -> str:
    text = re.sub(r"[^a-z0-9_.:-]+", "-", str(value or "").strip().casefold())
    return text.strip("-") or "unknown"


def _public_employee(entry: AgentEntry) -> dict[str, Any]:
    return {
        "id": entry.agent_id,
        "name": entry.name,
        "role": entry.role,
        "skill_ids": list(entry.skill_ids),
        "skills": list(entry.skills),
    }


def _public_skill(entry: SkillEntry) -> dict[str, Any]:
    return entry.to_public_dict()


class SkillGovernanceStore:
    """Persist skill governance report and operator decisions."""

    def __init__(self, workspace: Path) -> None:
        self._dir = workspace / "openhire"
        self._file = self._dir / "skill_governance.json"

    def load(self) -> dict[str, Any]:
        if not self._file.exists():
            return dict(_DEFAULT_GOVERNANCE_STATE)
        try:
            data = json.loads(self._file.read_text(encoding="utf-8"))
        except (json.JSONDecodeError, OSError):
            return dict(_DEFAULT_GOVERNANCE_STATE)
        if not isinstance(data, dict):
            return dict(_DEFAULT_GOVERNANCE_STATE)
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
            state["last_report"] = SkillGovernanceService.apply_ignored(
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


class SkillGovernanceService:
    """Compute governance issues and apply bounded cleanup actions."""

    def __init__(
        self,
        *,
        store: SkillGovernanceStore,
        skill_catalog: SkillCatalogService,
        employee_registry: AgentRegistry,
    ) -> None:
        self._store = store
        self._skill_catalog = skill_catalog
        self._employee_registry = employee_registry

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

    async def scan(self, *, include_remote: bool = False, skill_provider: Any | None = None) -> dict[str, Any]:
        report = self.build_report()
        if include_remote:
            await self._augment_remote_opportunities(report, skill_provider)
        state = self._store.save_report(self.apply_ignored(report, self._store.load().get("ignored_issue_ids", [])))
        return self.apply_ignored(state["last_report"], state.get("ignored_issue_ids", []))

    def build_report(self) -> dict[str, Any]:
        skills = self._skill_catalog.list()
        business_skills = [skill for skill in skills if skill.id != REQUIRED_EMPLOYEE_SKILL_ID]
        employees = self._employee_registry.all()
        skill_by_id = {skill.id: skill for skill in skills if skill.id}
        business_skill_ids = {skill.id for skill in business_skills}
        bound_counts = Counter(
            skill_id
            for employee in employees
            for skill_id in employee.skill_ids
            if skill_id in business_skill_ids
        )
        issues: list[dict[str, Any]] = []
        issues.extend(self._duplicate_issues(business_skills, bound_counts))
        issues.extend(self._orphan_issues(business_skills, bound_counts))
        issues.extend(self._missing_content_issues(business_skills))
        issues.extend(self._employee_binding_issues(employees, skill_by_id, business_skill_ids))
        opportunities = self._opportunities(employees, business_skills)
        summary = self._summary(skills, business_skills, employees, issues)
        report = {
            "generatedAt": _now(),
            "summary": summary,
            "issues": issues,
            "opportunities": opportunities,
            "warnings": [],
            "auditLog": self._store.load().get("audit_log", []),
        }
        return self.apply_ignored(report, self._store.load().get("ignored_issue_ids", []))

    def _duplicate_issues(self, skills: list[SkillEntry], bound_counts: Counter[str]) -> list[dict[str, Any]]:
        issues: list[dict[str, Any]] = []
        exact_groups: dict[tuple[str, str], list[SkillEntry]] = defaultdict(list)
        name_groups: dict[str, list[SkillEntry]] = defaultdict(list)
        for skill in skills:
            if not _norm(skill.name):
                continue
            exact_groups[(_norm(skill.name), _norm(skill.description))].append(skill)
            name_groups[_norm(skill.name)].append(skill)
        for key, group in exact_groups.items():
            if len(group) < 2:
                continue
            issue_id = self._group_issue_id("duplicate_exact", group)
            issues.append(self._duplicate_issue(issue_id, "duplicate_exact", group, bound_counts))
        for key, group in name_groups.items():
            if len(group) < 2:
                continue
            issue_id = self._group_issue_id("duplicate_name", group)
            issues.append(self._duplicate_issue(issue_id, "duplicate_name", group, bound_counts))
        return issues

    def _duplicate_issue(
        self,
        issue_id: str,
        issue_type: str,
        group: list[SkillEntry],
        bound_counts: Counter[str],
    ) -> dict[str, Any]:
        canonical = self._canonical_skill(group, bound_counts)
        return {
            "id": issue_id,
            "type": issue_type,
            "severity": "warning",
            "title": "Duplicate skill candidates",
            "body": f"{len(group)} skills share the same name or metadata.",
            "skillIds": [skill.id for skill in group],
            "canonicalSkillId": canonical.id if canonical else "",
            "skills": [_public_skill(skill) for skill in group],
            "employeeCount": sum(bound_counts.get(skill.id, 0) for skill in group),
            "ignored": False,
        }

    @staticmethod
    def _group_issue_id(prefix: str, group: list[SkillEntry]) -> str:
        return f"{prefix}:{'-'.join(sorted(skill.id for skill in group if skill.id))}"

    def _canonical_skill(self, group: list[SkillEntry], bound_counts: Counter[str]) -> SkillEntry | None:
        if not group:
            return None
        return sorted(
            group,
            key=lambda skill: (
                bound_counts.get(skill.id, 0),
                str(skill.imported_at or ""),
                str(skill.id or ""),
            ),
            reverse=True,
        )[0]

    def _orphan_issues(self, skills: list[SkillEntry], bound_counts: Counter[str]) -> list[dict[str, Any]]:
        return [
            {
                "id": f"orphan_skill:{skill.id}",
                "type": "orphan_skill",
                "severity": "info",
                "title": "Unused skill",
                "body": f"{skill.name or skill.id} is not bound to any employee.",
                "skillIds": [skill.id],
                "skills": [_public_skill(skill)],
                "ignored": False,
            }
            for skill in skills
            if skill.id and bound_counts.get(skill.id, 0) == 0
        ]

    def _missing_content_issues(self, skills: list[SkillEntry]) -> list[dict[str, Any]]:
        issues = []
        for skill in skills:
            if not skill.id or str(skill.markdown or "").strip():
                continue
            issues.append(
                {
                    "id": f"missing_content:{skill.id}",
                    "type": "missing_content",
                    "severity": "warning",
                    "title": "Skill content missing",
                    "body": f"{skill.name or skill.id} has generated metadata but no stored SKILL.md content.",
                    "skillIds": [skill.id],
                    "skills": [_public_skill(skill)],
                    "ignored": False,
                }
            )
        return issues

    def _employee_binding_issues(
        self,
        employees: list[AgentEntry],
        skill_by_id: dict[str, SkillEntry],
        business_skill_ids: set[str],
    ) -> list[dict[str, Any]]:
        issues: list[dict[str, Any]] = []
        for employee in employees:
            if employee.skill_ids:
                missing = [skill_id for skill_id in employee.skill_ids if skill_id not in skill_by_id]
                expected_names = [skill_by_id[skill_id].name for skill_id in employee.skill_ids if skill_id in skill_by_id]
                stale_names = bool(expected_names and list(employee.skills) != expected_names)
                if missing or stale_names or employee.skill_ids[0] != REQUIRED_EMPLOYEE_SKILL_ID:
                    suffix = "-".join(sorted(missing)) or "names"
                    issues.append(
                        {
                            "id": f"stale_employee_binding:{employee.agent_id}:{_stable_part(suffix)}",
                            "type": "stale_employee_binding",
                            "severity": "warning",
                            "title": "Employee skill binding drift",
                            "body": f"{employee.name or employee.agent_id} has missing or stale skill bindings.",
                            "employeeIds": [employee.agent_id],
                            "employees": [_public_employee(employee)],
                            "missingSkillIds": missing,
                            "ignored": False,
                        }
                    )
                continue
            legacy_business_skills = [
                skill for skill in employee.skills
                if _norm(skill) and _norm(skill) != _norm("优秀员工协议")
            ]
            if legacy_business_skills or not (set(employee.skill_ids) & business_skill_ids):
                issues.append(
                    {
                        "id": f"legacy_unbound_employee:{employee.agent_id}",
                        "type": "legacy_unbound_employee",
                        "severity": "info",
                        "title": "Employee has no local skill id binding",
                        "body": f"{employee.name or employee.agent_id} uses legacy skill names without local skill IDs.",
                        "employeeIds": [employee.agent_id],
                        "employees": [_public_employee(employee)],
                        "ignored": False,
                    }
                )
        return issues

    def _summary(
        self,
        skills: list[SkillEntry],
        business_skills: list[SkillEntry],
        employees: list[AgentEntry],
        issues: list[dict[str, Any]],
    ) -> dict[str, Any]:
        employees_with_business = 0
        business_ids = {skill.id for skill in business_skills}
        for employee in employees:
            if any(skill_id in business_ids for skill_id in employee.skill_ids):
                employees_with_business += 1
        coverage = 100 if not employees else round((employees_with_business / len(employees)) * 100)
        counts = Counter(issue.get("type") for issue in issues)
        return {
            "totalSkillCount": len(skills),
            "businessSkillCount": len(business_skills),
            "employeeCount": len(employees),
            "employeesWithBusinessSkills": employees_with_business,
            "employeeCoveragePercent": coverage,
            "duplicateGroupCount": counts.get("duplicate_name", 0),
            "orphanSkillCount": counts.get("orphan_skill", 0),
            "missingContentCount": counts.get("missing_content", 0),
            "staleEmployeeBindingCount": counts.get("stale_employee_binding", 0),
            "legacyUnboundEmployeeCount": counts.get("legacy_unbound_employee", 0),
            "ignoredIssueCount": 0,
        }

    def _opportunities(self, employees: list[AgentEntry], business_skills: list[SkillEntry]) -> list[dict[str, Any]]:
        opportunities: list[dict[str, Any]] = []
        queries: list[str] = []
        for employee in employees:
            query = self._query_for_employee(employee)
            if query and query not in queries:
                queries.append(query)
        if not queries:
            queries = ["github", "calendar", "browser"]
        for query in queries[:3]:
            opportunities.append(
                {
                    "id": f"clawhub:{query}",
                    "type": "clawhub_query",
                    "source": "clawhub",
                    "title": f"Search ClawHub for {query}",
                    "body": "Find public agent skills that match current employee roles.",
                    "query": query,
                    "candidateCount": None,
                    "candidates": [],
                }
            )
        opportunities.append(
            {
                "id": "persona:soulbanner",
                "type": "persona_source",
                "source": "soulbanner",
                "title": "Browse SoulBanner personas",
                "body": "Import persona skills for role coverage and employee specialization.",
                "query": "",
                "candidateCount": None,
                "candidates": [],
            }
        )
        opportunities.append(
            {
                "id": "web:skill-md",
                "type": "web_import",
                "source": "web",
                "title": "Import a SKILL.md URL",
                "body": "Preview and import a trusted public SKILL.md file.",
                "query": "",
                "candidateCount": None,
                "candidates": [],
            }
        )
        return opportunities

    @staticmethod
    def _query_for_employee(employee: AgentEntry) -> str:
        text = " ".join([employee.name, employee.role, employee.system_prompt, *employee.skills]).casefold()
        for token, query in _ROLE_QUERY_ALIASES:
            if token.casefold() in text:
                return query
        return ""

    async def _augment_remote_opportunities(self, report: dict[str, Any], skill_provider: Any | None) -> None:
        search = getattr(skill_provider, "search", None) if skill_provider else None
        if not callable(search):
            report.setdefault("warnings", []).append("Remote discovery skipped: no ClawHub provider available.")
            return
        for opportunity in report.get("opportunities", []):
            if opportunity.get("type") != "clawhub_query":
                continue
            query = str(opportunity.get("query") or "").strip()
            if not query:
                continue
            try:
                candidates = await search(query, limit=3)
            except Exception as exc:
                report.setdefault("warnings", []).append(f"Remote discovery skipped for {query}: {exc}")
                continue
            public_candidates = [dict(item) for item in candidates if isinstance(item, Mapping)]
            opportunity["candidateCount"] = len(public_candidates)
            opportunity["candidates"] = public_candidates

    def update_ignored(self, issue_ids: list[str], ignored: bool) -> dict[str, Any]:
        state = self._store.set_ignored(issue_ids, ignored)
        report = state.get("last_report") if isinstance(state.get("last_report"), dict) else self.build_report()
        return self.apply_ignored(report, state.get("ignored_issue_ids", []))

    def plan_action(
        self,
        *,
        action: str,
        issue_ids: list[str] | None = None,
        skill_ids: list[str] | None = None,
        employee_ids: list[str] | None = None,
    ) -> dict[str, Any]:
        if action == "merge_duplicates":
            return self._plan_merge_duplicates(issue_ids or [])
        if action == "delete_orphans":
            return self._plan_delete_orphans(skill_ids or [], issue_ids or [])
        if action == "repair_employee_bindings":
            return self._plan_repair_employee_bindings(employee_ids or [], issue_ids or [])
        raise ValueError(f"Unsupported skill governance action '{action}'.")

    def execute_action(
        self,
        *,
        action: str,
        issue_ids: list[str] | None = None,
        skill_ids: list[str] | None = None,
        employee_ids: list[str] | None = None,
    ) -> dict[str, Any]:
        plan = self.plan_action(
            action=action,
            issue_ids=issue_ids,
            skill_ids=skill_ids,
            employee_ids=employee_ids,
        )
        if action == "merge_duplicates":
            self._execute_merge(plan)
        elif action == "delete_orphans":
            self._execute_delete(plan)
        elif action == "repair_employee_bindings":
            self._execute_repair(plan)
        state = self._store.append_audit(
            {
                "action": action,
                "issueIds": issue_ids or [],
                "skillIds": skill_ids or [],
                "employeeIds": employee_ids or [],
                "plan": plan,
            }
        )
        report = self.build_report()
        self._store.save_report(self.apply_ignored(report, state.get("ignored_issue_ids", [])))
        return plan

    def _plan_merge_duplicates(self, issue_ids: list[str]) -> dict[str, Any]:
        report = self.build_report()
        issues = [
            issue for issue in report["issues"]
            if issue["id"] in issue_ids and issue["type"] in {"duplicate_exact", "duplicate_name"}
        ]
        mapping: dict[str, str] = {}
        canonical_groups = []
        for issue in issues:
            canonical_id = str(issue.get("canonicalSkillId") or "")
            if not canonical_id:
                continue
            duplicates = [skill_id for skill_id in issue.get("skillIds", []) if skill_id != canonical_id]
            for duplicate_id in duplicates:
                mapping[str(duplicate_id)] = canonical_id
            canonical_groups.append({"issueId": issue["id"], "canonicalSkillId": canonical_id, "duplicateSkillIds": duplicates})
        return self._plan_for_mapping(mapping, canonical_groups=canonical_groups)

    def _plan_for_mapping(self, mapping: dict[str, str], *, canonical_groups: list[dict[str, Any]]) -> dict[str, Any]:
        employees_updated = []
        for employee in self._employee_registry.all():
            if not employee.skill_ids:
                continue
            next_ids = self._replace_skill_ids(employee.skill_ids, mapping)
            if next_ids != employee.skill_ids:
                employees_updated.append({"employeeId": employee.agent_id, "from": employee.skill_ids, "to": next_ids})
        return {
            "canonicalSkills": canonical_groups,
            "skillsDeleted": sorted(mapping.keys()),
            "employeesUpdated": employees_updated,
            "employeeCount": len(employees_updated),
            "skillCount": len(mapping),
        }

    @staticmethod
    def _replace_skill_ids(skill_ids: list[str], mapping: dict[str, str]) -> list[str]:
        result: list[str] = []
        seen: set[str] = set()
        for skill_id in skill_ids:
            next_id = mapping.get(skill_id, skill_id)
            if next_id in seen:
                continue
            seen.add(next_id)
            result.append(next_id)
        return result

    def _plan_delete_orphans(self, skill_ids: list[str], issue_ids: list[str]) -> dict[str, Any]:
        report = self.build_report()
        orphan_ids = {
            skill_id
            for issue in report["issues"]
            if issue["type"] == "orphan_skill" and (not issue_ids or issue["id"] in issue_ids)
            for skill_id in issue.get("skillIds", [])
        }
        requested = set(skill_ids) if skill_ids else orphan_ids
        deletable = sorted(skill_id for skill_id in requested if skill_id in orphan_ids and skill_id != REQUIRED_EMPLOYEE_SKILL_ID)
        return {
            "skillsDeleted": deletable,
            "employeesUpdated": [],
            "employeeCount": 0,
            "skillCount": len(deletable),
        }

    def _plan_repair_employee_bindings(self, employee_ids: list[str], issue_ids: list[str]) -> dict[str, Any]:
        report = self.build_report()
        issue_employee_ids = {
            employee_id
            for issue in report["issues"]
            if issue["type"] == "stale_employee_binding" and (not issue_ids or issue["id"] in issue_ids)
            for employee_id in issue.get("employeeIds", [])
        }
        requested = set(employee_ids) if employee_ids else issue_employee_ids
        skill_by_id = {skill.id: skill for skill in self._skill_catalog.list() if skill.id}
        employees_updated = []
        for employee in self._employee_registry.all():
            if employee.agent_id not in requested or not employee.skill_ids:
                continue
            next_ids = []
            for skill_id in [REQUIRED_EMPLOYEE_SKILL_ID, *employee.skill_ids]:
                if skill_id not in skill_by_id or skill_id in next_ids:
                    continue
                next_ids.append(skill_id)
            next_names = [skill_by_id[skill_id].name for skill_id in next_ids]
            if next_ids != employee.skill_ids or next_names != employee.skills:
                employees_updated.append(
                    {
                        "employeeId": employee.agent_id,
                        "from": employee.skill_ids,
                        "to": next_ids,
                        "skills": next_names,
                    }
                )
        return {
            "skillsDeleted": [],
            "employeesUpdated": employees_updated,
            "employeeCount": len(employees_updated),
            "skillCount": 0,
        }

    def _execute_merge(self, plan: dict[str, Any]) -> None:
        mapping = {
            duplicate_id: group["canonicalSkillId"]
            for group in plan.get("canonicalSkills", [])
            for duplicate_id in group.get("duplicateSkillIds", [])
        }
        skill_by_id = {skill.id: skill for skill in self._skill_catalog.list() if skill.id}
        for employee in self._employee_registry.all():
            if not employee.skill_ids:
                continue
            next_ids = self._replace_skill_ids(employee.skill_ids, mapping)
            if next_ids == employee.skill_ids:
                continue
            next_names = [skill_by_id[skill_id].name for skill_id in next_ids if skill_id in skill_by_id]
            self._employee_registry.update(employee.agent_id, skill_ids=next_ids, skills=next_names or employee.skills)
        for skill_id in plan.get("skillsDeleted", []):
            self._skill_catalog.remove(str(skill_id))

    def _execute_delete(self, plan: dict[str, Any]) -> None:
        for skill_id in plan.get("skillsDeleted", []):
            self._skill_catalog.remove(str(skill_id))

    def _execute_repair(self, plan: dict[str, Any]) -> None:
        for item in plan.get("employeesUpdated", []):
            employee_id = str(item.get("employeeId") or "")
            if not employee_id:
                continue
            self._employee_registry.update(
                employee_id,
                skill_ids=list(item.get("to") or []),
                skills=list(item.get("skills") or []),
            )
