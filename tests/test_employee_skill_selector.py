from __future__ import annotations

from openhire.providers.base import LLMResponse
from openhire.skill_catalog import SkillEntry
from openhire.workforce.required_skill import REQUIRED_EMPLOYEE_SKILL_ID
from openhire.workforce.skill_selection import EmployeeSkillSelector


class _ScriptedProvider:
    def __init__(self, responses: list[str]) -> None:
        self.responses = list(responses)
        self.calls: list[dict] = []

    async def chat_with_retry(self, **kwargs) -> LLMResponse:
        self.calls.append(kwargs)
        if not self.responses:
            return LLMResponse(content='{"skill_ids":[],"reason":"none"}')
        return LLMResponse(content=self.responses.pop(0))


def _skill(skill_id: str, name: str, description: str = "") -> SkillEntry:
    return SkillEntry(
        id=skill_id,
        source="clawhub",
        external_id=name.lower(),
        name=name,
        description=description or f"{name} skill",
        tags=[f"tool:{name.lower()}"],
    )


async def test_selector_returns_valid_skill_ids_and_reason() -> None:
    provider = _ScriptedProvider(['{"skill_ids":["gmail","slack"],"reason":"message triage"}'])
    selector = EmployeeSkillSelector(provider=provider)

    result = await selector.select(
        name="Inbox Ops",
        role="邮箱与消息分诊员",
        system_prompt="处理邮件和 Slack 消息。",
        explicit_skills=[],
        catalog_skills=[_skill("gmail", "Gmail"), _skill("slack", "Slack")],
    )

    assert result.skill_ids == ["gmail", "slack"]
    assert result.skill_names == ["Gmail", "Slack"]
    assert result.reason == "message triage"
    assert result.warning == ""
    assert len(provider.calls) == 1


async def test_selector_retries_invalid_json_then_succeeds() -> None:
    provider = _ScriptedProvider([
        "not json",
        '{"skill_ids":["jira"],"reason":"ticket routing"}',
    ])
    selector = EmployeeSkillSelector(provider=provider, retries=5)

    result = await selector.select(
        name="Ticket Ops",
        role="工单分派员",
        system_prompt="收集用户问题并创建工单。",
        explicit_skills=[],
        catalog_skills=[_skill("jira", "JIRA")],
    )

    assert result.skill_ids == ["jira"]
    assert len(provider.calls) == 2


async def test_selector_retries_unknown_skill_id_then_succeeds() -> None:
    provider = _ScriptedProvider([
        '{"skill_ids":["missing"],"reason":"bad"}',
        '{"skill_ids":["zendesk"],"reason":"support tickets"}',
    ])
    selector = EmployeeSkillSelector(provider=provider, retries=5)

    result = await selector.select(
        name="Support",
        role="工单分派员",
        system_prompt="管理 Zendesk tickets。",
        explicit_skills=[],
        catalog_skills=[_skill("zendesk", "Zendesk")],
    )

    assert result.skill_ids == ["zendesk"]
    assert len(provider.calls) == 2


async def test_selector_excludes_required_skill_and_limits_to_max() -> None:
    provider = _ScriptedProvider([
        '{"skill_ids":["excellent-employee","a","b","c","d","e","f"],"reason":"many"}'
    ])
    selector = EmployeeSkillSelector(provider=provider, max_skills=5)
    skills = [_skill(letter, letter.upper()) for letter in "abcdef"]
    skills.append(_skill(REQUIRED_EMPLOYEE_SKILL_ID, "优秀员工协议"))

    result = await selector.select(
        name="Ops",
        role="运营巡检员",
        system_prompt="检查后台页面和活动链接。",
        explicit_skills=[],
        catalog_skills=skills,
    )

    assert result.skill_ids == ["a", "b", "c", "d", "e"]
    assert REQUIRED_EMPLOYEE_SKILL_ID not in result.skill_ids
    assert "limited to 5" in result.warning


async def test_selector_returns_warning_after_five_failures() -> None:
    provider = _ScriptedProvider(["not json"] * 5)
    selector = EmployeeSkillSelector(provider=provider, retries=5)

    result = await selector.select(
        name="Broken",
        role="未知角色",
        system_prompt="",
        explicit_skills=[],
        catalog_skills=[_skill("gmail", "Gmail")],
    )

    assert result.skill_ids == []
    assert result.skill_names == []
    assert "failed after 5 attempts" in result.warning
    assert len(provider.calls) == 5


async def test_selector_without_provider_returns_warning() -> None:
    selector = EmployeeSkillSelector(provider=None)

    result = await selector.select(
        name="No Provider",
        role="邮箱与消息分诊员",
        system_prompt="",
        explicit_skills=[],
        catalog_skills=[_skill("gmail", "Gmail")],
    )

    assert result.skill_ids == []
    assert "provider" in result.warning
