"""Employee assignment service for digital employee pool reuse and auto-creation."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Protocol

from openhire.adapters import build_default_registry
from openhire.workforce.required_skill import (
    ensure_required_employee_skill_ids,
    ensure_required_employee_skill_names,
    inject_required_employee_skill_prompt,
)
from openhire.workforce.registry import AgentEntry, AgentRegistry


def _normalize_role(value: str) -> str:
    return "".join(str(value or "").lower().split())


def _normalize_skills(skills: list[str] | None) -> list[str]:
    seen: set[str] = set()
    normalized: list[str] = []
    for skill in skills or []:
        text = str(skill or "").strip()
        if not text:
            continue
        lowered = text.lower()
        if lowered in seen:
            continue
        seen.add(lowered)
        normalized.append(text)
    return normalized


def valid_agent_types() -> set[str]:
    return set(build_default_registry().names())


def default_agent_type_for_role(role: str) -> str:
    role_lower = str(role or "").lower()
    if any(token in role_lower for token in ("frontend", "前端", "design", "设计", "美术", "art", "ui", "ux")):
        return "nanobot"
    if any(token in role_lower for token in ("backend", "后端", "data", "数据", "algorithm", "算法")):
        return "nanobot"
    if any(token in role_lower for token in ("test", "测试", "qa", "sre", "devops", "运维")):
        return "openclaw"
    return "openclaw"


def resolve_agent_type(role: str, recommended_agent_type: str | None) -> str:
    allowed = valid_agent_types()
    if recommended_agent_type in allowed:
        return str(recommended_agent_type)
    fallback = default_agent_type_for_role(role)
    return fallback if fallback in allowed else "openclaw"


def build_auto_system_prompt(role: str, skills: list[str], planned_prompt: str = "") -> str:
    prompt = str(planned_prompt or "").strip()
    if prompt:
        return prompt
    if skills:
        return f"你是{role}，负责相关工作，重点关注：{', '.join(skills)}。"
    return f"你是{role}，负责该角色的核心交付。"


@dataclass(slots=True)
class PlannedRole:
    role: str
    skills: list[str] = field(default_factory=list)
    system_prompt: str = ""
    recommended_agent_type: str | None = None

    def normalized_skills(self) -> list[str]:
        return _normalize_skills(self.skills)


@dataclass(slots=True)
class AssignmentResult:
    employee: AgentEntry
    created: bool
    planned_role: PlannedRole


class Planner(Protocol):
    async def plan(self, task_or_context: str) -> list[PlannedRole]:
        ...


class AssignmentService:
    """Select existing employees or create minimal missing ones from planned roles."""

    def __init__(self, registry: AgentRegistry, planner: Planner) -> None:
        self._registry = registry
        self._planner = planner

    async def assign(self, task_or_context: str) -> list[AssignmentResult]:
        planned_roles = await self._planner.plan(task_or_context)
        results: list[AssignmentResult] = []
        for planned in planned_roles:
            employee = self._match_existing(planned)
            if employee is not None:
                results.append(AssignmentResult(employee=employee, created=False, planned_role=planned))
                continue
            created = self._create_employee(planned)
            results.append(AssignmentResult(employee=created, created=True, planned_role=planned))
        return results

    def _match_existing(self, planned: PlannedRole) -> AgentEntry | None:
        best: tuple[int, AgentEntry] | None = None
        for employee in self._registry.all():
            if employee.status != "active":
                continue
            score = self._score_match(employee, planned)
            if score < 70:
                continue
            if best is None or score > best[0]:
                best = (score, employee)
        return best[1] if best else None

    def _score_match(self, employee: AgentEntry, planned: PlannedRole) -> int:
        employee_role = _normalize_role(employee.role)
        planned_role = _normalize_role(planned.role)
        employee_skills = {skill.lower() for skill in employee.skills}
        planned_skills = {skill.lower() for skill in planned.normalized_skills()}

        role_score = 0
        if employee_role and employee_role == planned_role:
            role_score = 100
        elif employee_role and planned_role and (
            employee_role in planned_role or planned_role in employee_role
        ):
            role_score = 80

        overlap = len(employee_skills & planned_skills)
        skill_score = min(15, overlap * 5)
        type_score = 5 if (
            planned.recommended_agent_type
            and employee.agent_type == planned.recommended_agent_type
        ) else 0
        return role_score + skill_score + type_score

    def _create_employee(self, planned: PlannedRole) -> AgentEntry:
        skills = planned.normalized_skills()
        agent_type = resolve_agent_type(planned.role, planned.recommended_agent_type)
        system_prompt = inject_required_employee_skill_prompt(
            build_auto_system_prompt(
                planned.role,
                skills,
                planned.system_prompt,
            )
        )
        return self._registry.register(
            AgentEntry(
                name=planned.role,
                role=planned.role,
                skills=ensure_required_employee_skill_names(skills),
                skill_ids=ensure_required_employee_skill_ids([]),
                system_prompt=system_prompt,
                agent_type=agent_type,
                agent_config={},
                status="active",
            )
        )
