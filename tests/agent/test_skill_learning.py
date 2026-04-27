from __future__ import annotations

import json
from pathlib import Path
from unittest.mock import AsyncMock, MagicMock

import pytest

from openhire.agent.skill_learning import (
    SkillProposalGenerator,
    detect_skill_learning_trigger_reasons,
)
from openhire.agent_skill_service import AgentSkillService
from openhire.providers.base import LLMResponse


def _assistant_tool_call(index: int, name: str = "read_file") -> dict:
    return {
        "role": "assistant",
        "content": "",
        "tool_calls": [
            {
                "id": f"call_{index}",
                "type": "function",
                "function": {"name": name, "arguments": "{}"},
            }
        ],
    }


def _tool_result(index: int, name: str = "read_file", content: str = "ok") -> dict:
    return {
        "role": "tool",
        "tool_call_id": f"call_{index}",
        "name": name,
        "content": content,
    }


def _skill_markdown(name: str, description: str = "Use this skill for tests.") -> str:
    return f"---\nname: {name}\ndescription: {description}\n---\n\n# {name}\n\n{description}\n"


def test_detect_skill_learning_trigger_reasons_for_complex_error_and_correction() -> None:
    complex_messages = [{"role": "user", "content": "ship the release"}]
    for idx in range(5):
        complex_messages += [_assistant_tool_call(idx), _tool_result(idx)]
    complex_messages.append({"role": "assistant", "content": "done"})

    assert "complex_task_5_tool_calls" in detect_skill_learning_trigger_reasons(
        complex_messages,
        stop_reason="completed",
    )

    recovered_messages = [
        {"role": "user", "content": "debug this"},
        _assistant_tool_call(1, "exec"),
        _tool_result(1, "exec", "Error: command failed\n\n[Analyze the error above and try a different approach.]"),
        _assistant_tool_call(2, "exec"),
        _tool_result(2, "exec", "ok"),
        {"role": "assistant", "content": "fixed"},
    ]
    assert "error_recovered" in detect_skill_learning_trigger_reasons(
        recovered_messages,
        stop_reason="completed",
    )

    correction_messages = [
        {"role": "user", "content": "不是这个做法，请按之前的导入流程修"},
        {"role": "assistant", "content": "已修正"},
    ]
    assert "user_correction" in detect_skill_learning_trigger_reasons(
        correction_messages,
        stop_reason="completed",
    )


@pytest.mark.asyncio
async def test_skill_proposal_generator_creates_pending_proposal_for_complex_turn(tmp_path: Path) -> None:
    provider = MagicMock()
    provider.chat_with_retry = AsyncMock(
        side_effect=[
            LLMResponse(
                content=json.dumps(
                    {
                        "decision": "create",
                        "name": "release-verification-flow",
                        "reason": "The turn used a repeatable release verification workflow.",
                    }
                )
            ),
            LLMResponse(
                content=json.dumps(
                    {
                        "content": _skill_markdown(
                            "release-verification-flow",
                            "Use this skill after complex release verification.",
                        )
                    }
                )
            ),
        ]
    )
    generator = SkillProposalGenerator(workspace=tmp_path, provider=provider, model="test-model")

    proposal = await generator.submit_turn(
        messages=[
            {"role": "user", "content": "verify and ship"},
            *[_assistant_tool_call(idx) for idx in range(5)],
            {"role": "assistant", "content": "Release verified."},
        ],
        final_content="Release verified.",
        trigger_reasons=["complex_task_5_tool_calls"],
        session_key="cli:test",
    )

    assert proposal is not None
    assert proposal["source"] == "turn"
    assert proposal["name"] == "release-verification-flow"
    assert proposal["trigger_reasons"] == ["complex_task_5_tool_calls"]
    assert proposal["status"] == "pending"
    assert not (tmp_path / "skills" / "release-verification-flow" / "SKILL.md").exists()


@pytest.mark.asyncio
async def test_skill_proposal_generator_updates_similar_existing_skill(tmp_path: Path) -> None:
    service = AgentSkillService(tmp_path, builtin_skills_dir=tmp_path / "builtin")
    service.create(
        name="release-verification-flow",
        content=_skill_markdown("release-verification-flow", "Use old flow."),
    )
    provider = MagicMock()
    provider.chat_with_retry = AsyncMock(
        side_effect=[
            LLMResponse(
                content=json.dumps(
                    {
                        "decision": "update",
                        "name": "release-verification-flow",
                        "reason": "The existing release skill should mention the successful fix.",
                    }
                )
            ),
            LLMResponse(
                content=json.dumps(
                    {
                        "action": "patch",
                        "old_string": "Use old flow.",
                        "new_string": "Use the recovered release verification flow.",
                    }
                )
            ),
        ]
    )
    generator = SkillProposalGenerator(workspace=tmp_path, provider=provider, model="test-model")

    proposal = await generator.submit_turn(
        messages=[
            {"role": "user", "content": "release failed; try another path"},
            _assistant_tool_call(1, "exec"),
            _tool_result(1, "exec", "Error: failed"),
            _assistant_tool_call(2, "exec"),
            _tool_result(2, "exec", "ok"),
            {"role": "assistant", "content": "Recovered with a new verification step."},
        ],
        final_content="Recovered with a new verification step.",
        trigger_reasons=["error_recovered"],
        session_key="cli:test",
    )

    assert proposal is not None
    assert proposal["action"] == "patch"
    assert proposal["name"] == "release-verification-flow"
    assert proposal["old_string"] == "Use old flow."
    assert proposal["new_string"] == "Use the recovered release verification flow."
    assert not proposal.get("applied_at")
    assert "Use old flow." in service.get("release-verification-flow")["markdown"]


@pytest.mark.asyncio
async def test_skill_proposal_generator_invalid_json_is_non_blocking(tmp_path: Path) -> None:
    provider = MagicMock()
    provider.chat_with_retry = AsyncMock(return_value=LLMResponse(content="not json"))
    generator = SkillProposalGenerator(workspace=tmp_path, provider=provider, model="test-model")

    proposal = await generator.submit_turn(
        messages=[{"role": "user", "content": "please build a reusable workflow"}],
        final_content="done",
        trigger_reasons=["nontrivial_reusable_workflow"],
        session_key="cli:test",
    )

    assert proposal is None
    assert not (tmp_path / "openhire" / "agent_skill_proposals.json").exists()
