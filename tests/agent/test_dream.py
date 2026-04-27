"""Tests for the Dream class — two-phase memory consolidation via AgentRunner."""

import json

import pytest

from unittest.mock import AsyncMock, MagicMock

from openhire.agent.memory import Dream, MemoryStore
from openhire.agent.runner import AgentRunResult
from openhire.agent.skills import BUILTIN_SKILLS_DIR


@pytest.fixture
def store(tmp_path):
    s = MemoryStore(tmp_path)
    s.write_soul("# Soul\n- Helpful")
    s.write_user("# User\n- Developer")
    s.write_memory("# Memory\n- Project X active")
    return s


@pytest.fixture
def mock_provider():
    p = MagicMock()
    p.chat_with_retry = AsyncMock()
    return p


@pytest.fixture
def mock_runner():
    return MagicMock()


@pytest.fixture
def dream(store, mock_provider, mock_runner):
    d = Dream(store=store, provider=mock_provider, model="test-model", max_batch_size=5)
    d._runner = mock_runner
    return d


def _make_run_result(
    stop_reason="completed",
    final_content=None,
    tool_events=None,
    usage=None,
):
    return AgentRunResult(
        final_content=final_content or stop_reason,
        stop_reason=stop_reason,
        messages=[],
        tools_used=[],
        usage={},
        tool_events=tool_events or [],
    )


class TestDreamRun:
    async def test_noop_when_no_unprocessed_history(self, dream, mock_provider, mock_runner, store):
        """Dream should not call LLM when there's nothing to process."""
        result = await dream.run()
        assert result is False
        mock_provider.chat_with_retry.assert_not_called()
        mock_runner.run.assert_not_called()

    async def test_calls_runner_for_unprocessed_entries(self, dream, mock_provider, mock_runner, store):
        """Dream should call AgentRunner when there are unprocessed history entries."""
        store.append_history("User prefers dark mode")
        mock_provider.chat_with_retry.return_value = MagicMock(content="New fact")
        mock_runner.run = AsyncMock(return_value=_make_run_result(
            tool_events=[{"name": "edit_file", "status": "ok", "detail": "memory/MEMORY.md"}],
        ))
        result = await dream.run()
        assert result is True
        mock_runner.run.assert_called_once()
        spec = mock_runner.run.call_args[0][0]
        assert spec.max_iterations == 10
        assert spec.fail_on_tool_error is False

    async def test_advances_dream_cursor(self, dream, mock_provider, mock_runner, store):
        """Dream should advance the cursor after processing."""
        store.append_history("event 1")
        store.append_history("event 2")
        mock_provider.chat_with_retry.return_value = MagicMock(content="Nothing new")
        mock_runner.run = AsyncMock(return_value=_make_run_result())
        await dream.run()
        assert store.get_last_dream_cursor() == 2

    async def test_compacts_processed_history(self, dream, mock_provider, mock_runner, store):
        """Dream should compact history after processing."""
        store.append_history("event 1")
        store.append_history("event 2")
        store.append_history("event 3")
        mock_provider.chat_with_retry.return_value = MagicMock(content="Nothing new")
        mock_runner.run = AsyncMock(return_value=_make_run_result())
        await dream.run()
        # After Dream, cursor is advanced and 3, compact keeps last max_history_entries
        entries = store.read_unprocessed_history(since_cursor=0)
        assert all(e["cursor"] > 0 for e in entries)

    async def test_skill_phase_uses_builtin_skill_creator_path(self, dream, mock_provider, mock_runner, store):
        """Dream should point skill proposals at the builtin skill-creator template."""
        store.append_history("Repeated workflow one")
        store.append_history("Repeated workflow two")
        mock_provider.chat_with_retry.return_value = MagicMock(content="[SKILL] test-skill: test description")
        mock_runner.run = AsyncMock(return_value=_make_run_result())

        await dream.run()

        spec = mock_runner.run.call_args[0][0]
        system_prompt = spec.initial_messages[0]["content"]
        expected = str(BUILTIN_SKILLS_DIR / "skill-creator" / "SKILL.md")
        assert expected in system_prompt
        assert "propose_agent_skill" in system_prompt
        assert "Do NOT use write_file or edit_file for skills/<name>/SKILL.md" in system_prompt
        assert "5+ tool calls" in system_prompt
        assert "user corrected" in system_prompt
        assert "prefer patch or edit proposals for similar existing skills" in system_prompt

    async def test_dream_does_not_register_write_file_for_skill_creation(self, dream):
        """Dream must not have a direct write_file path into workspace/skills."""
        assert dream._tools.get("write_file") is None

    async def test_dream_edit_file_rejects_workspace_skill_paths(self, dream, store):
        """Dream edit_file should not create or mutate skills directly."""
        edit_tool = dream._tools.get("edit_file")
        assert edit_tool is not None

        result = await edit_tool.execute(
            path="skills/test-skill/SKILL.md",
            old_text="",
            new_text="---\nname: test-skill\ndescription: Test\n---\n",
        )

        assert "Dream cannot write workspace/skills directly" in result
        assert not (store.workspace / "skills" / "test-skill" / "SKILL.md").exists()

    async def test_propose_agent_skill_tool_writes_proposal_not_skill(self, dream, store):
        """Dream-created skills should enter the Workbench proposal queue."""
        propose_tool = dream._tools.get("propose_agent_skill")
        assert propose_tool is not None

        result = await propose_tool.execute(
            name="test-skill",
            reason="Repeated workflow appeared in history.",
            content="---\nname: test-skill\ndescription: Use this skill for tests.\n---\n\n# Test Skill\n",
            source="dream",
            trigger_reasons=["nontrivial_reusable_workflow"],
            evidence=["Dream saw the workflow twice."],
        )

        assert "Created pending agent skill proposal" in result
        assert not (store.workspace / "skills" / "test-skill" / "SKILL.md").exists()
        proposal_state = json.loads(
            (store.workspace / "openhire" / "agent_skill_proposals.json").read_text(encoding="utf-8")
        )
        assert proposal_state["proposals"][0]["name"] == "test-skill"
        assert proposal_state["proposals"][0]["status"] == "pending"
        assert proposal_state["proposals"][0]["source"] == "dream"
        assert proposal_state["proposals"][0]["trigger_reasons"] == ["nontrivial_reusable_workflow"]

    async def test_propose_agent_skill_tool_supports_patch_proposals(self, dream, store):
        """Dream can propose updates without mutating the skill directly."""
        propose_tool = dream._tools.get("propose_agent_skill")
        assert propose_tool is not None

        result = await propose_tool.execute(
            action="patch",
            name="existing-skill",
            reason="Recovered path should be added.",
            old_string="Old workflow",
            new_string="Recovered workflow",
            source="dream",
            trigger_reasons=["error_recovered"],
            evidence=["An earlier command failed, then a fallback worked."],
        )

        assert "Created pending agent skill proposal" in result
        proposal_state = json.loads(
            (store.workspace / "openhire" / "agent_skill_proposals.json").read_text(encoding="utf-8")
        )
        proposal = proposal_state["proposals"][0]
        assert proposal["action"] == "patch"
        assert proposal["name"] == "existing-skill"
        assert proposal["old_string"] == "Old workflow"
        assert proposal["new_string"] == "Recovered workflow"
        assert proposal["source"] == "dream"
