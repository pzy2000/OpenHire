from __future__ import annotations

from openhire.workforce.assignment import AssignmentService, PlannedRole
from openhire.workforce.required_skill import (
    REQUIRED_EMPLOYEE_SKILL_ID,
    REQUIRED_EMPLOYEE_SKILL_NAME,
    REQUIRED_EMPLOYEE_SKILL_PROMPT_START,
)
from openhire.workforce.registry import AgentEntry, AgentRegistry
from openhire.workforce.store import OpenHireStore


class _StubPlanner:
    def __init__(self, planned_roles: list[PlannedRole]) -> None:
        self._planned_roles = planned_roles

    async def plan(self, task_or_context: str) -> list[PlannedRole]:
        assert task_or_context
        return list(self._planned_roles)


async def test_assignment_service_reuses_existing_role(tmp_path) -> None:
    registry = AgentRegistry(OpenHireStore(tmp_path))
    existing = registry.register(
        AgentEntry(
            name="Nova FE",
            role="前端工程师",
            skills=["react", "typescript"],
            system_prompt="你负责前端开发。",
            agent_type="nanobot",
        )
    )
    service = AssignmentService(
        registry=registry,
        planner=_StubPlanner(
            [
                PlannedRole(
                    role="前端工程师",
                    skills=["react"],
                    system_prompt="你负责前端开发。",
                    # Disabled OpenHands recommendations should not block role reuse.
                    recommended_agent_type="openhands",
                )
            ]
        ),
    )

    result = await service.assign("帮我做一个前端页面")

    assert len(result) == 1
    assert result[0].employee.id == existing.agent_id
    assert result[0].created is False
    assert result[0].employee.agent_type == "nanobot"
    assert len(registry.all()) == 1


async def test_assignment_service_auto_creates_missing_role(tmp_path) -> None:
    registry = AgentRegistry(OpenHireStore(tmp_path))
    service = AssignmentService(
        registry=registry,
        planner=_StubPlanner(
            [
                PlannedRole(
                    role="后端工程师",
                    skills=["python", "api"],
                    system_prompt="你负责后端开发。",
                    recommended_agent_type="nanobot",
                )
            ]
        ),
    )

    result = await service.assign("实现接口")

    assert len(result) == 1
    assert result[0].created is True
    assert result[0].employee.role == "后端工程师"
    assert result[0].employee.agent_type == "nanobot"
    assert result[0].employee.skill_ids == [REQUIRED_EMPLOYEE_SKILL_ID]
    assert result[0].employee.skills == [REQUIRED_EMPLOYEE_SKILL_NAME, "python", "api"]
    assert REQUIRED_EMPLOYEE_SKILL_PROMPT_START in result[0].employee.system_prompt
    assert len(registry.all()) == 1


async def test_assignment_service_returns_agent_type_for_all_assignments(tmp_path) -> None:
    registry = AgentRegistry(OpenHireStore(tmp_path))
    registry.register(
        AgentEntry(
            name="QA",
            role="测试工程师",
            skills=["qa"],
            system_prompt="你负责测试。",
            agent_type="openclaw",
        )
    )
    service = AssignmentService(
        registry=registry,
        planner=_StubPlanner(
            [
                PlannedRole(role="测试工程师", skills=["qa"], recommended_agent_type="openclaw"),
                PlannedRole(role="游戏美术设计师", skills=["art", "ui"], recommended_agent_type=None),
            ]
        ),
    )

    result = await service.assign("帮我做一个贪吃蛇游戏")

    assert len(result) == 2
    assert [item.employee.agent_type for item in result] == ["openclaw", "nanobot"]
