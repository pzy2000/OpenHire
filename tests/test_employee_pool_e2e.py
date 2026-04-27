from __future__ import annotations

from openhire.workforce.assignment import AssignmentService, PlannedRole
from openhire.workforce.registry import AgentEntry, AgentRegistry
from openhire.workforce.store import OpenHireStore


class _SnakeGamePlanner:
    async def plan(self, task_or_context: str) -> list[PlannedRole]:
        assert task_or_context == "帮我做一个贪吃蛇游戏"
        return [
            # Disabled OpenHands recommendations should fall back without failing assignment.
            PlannedRole(role="前端工程师", skills=["react", "game-ui"], recommended_agent_type="openhands"),
            PlannedRole(role="测试工程师", skills=["qa", "e2e"], recommended_agent_type="openclaw"),
            PlannedRole(role="游戏美术设计师", skills=["art", "ui"], recommended_agent_type=None),
            PlannedRole(role="后端工程师", skills=["python", "api"], recommended_agent_type="nanobot"),
        ]


async def test_employee_pool_assignment_e2e_snake_game(tmp_path) -> None:
    registry = AgentRegistry(OpenHireStore(tmp_path))
    existing_frontend = registry.register(
        AgentEntry(
            name="前端工程师",
            role="前端工程师",
            skills=["react", "typescript"],
            system_prompt="你负责前端。",
            agent_type="nanobot",
        )
    )
    existing_tester = registry.register(
        AgentEntry(
            name="测试工程师",
            role="测试工程师",
            skills=["qa", "automation"],
            system_prompt="你负责测试。",
            agent_type="openclaw",
        )
    )
    service = AssignmentService(registry=registry, planner=_SnakeGamePlanner())

    result = await service.assign("帮我做一个贪吃蛇游戏")

    assert len(result) == 4
    assert result[0].employee.id == existing_frontend.agent_id
    assert result[0].created is False
    assert result[1].employee.id == existing_tester.agent_id
    assert result[1].created is False
    assert result[2].employee.role == "游戏美术设计师"
    assert result[2].created is True
    assert result[2].employee.agent_type == "nanobot"
    assert result[3].employee.role == "后端工程师"
    assert result[3].created is True
    assert result[3].employee.agent_type == "nanobot"
    assert all(item.employee.agent_type for item in result)
    assert len(registry.all()) == 4
