"""Automatic Agent Skill proposal generation from completed turns."""

from __future__ import annotations

import asyncio
import json
import re
from pathlib import Path
from typing import Any, Mapping

from loguru import logger

from openhire.agent_skill_service import AgentSkillService
from openhire.providers.base import LLMProvider

_CORRECTION_MARKERS = (
    "不是",
    "不对",
    "错了",
    "纠正",
    "我不是这个意思",
    "你应该",
    "请改成",
    "按之前",
    "actually",
    "not that",
    "wrong",
    "i meant",
    "you should",
)
_WORKFLOW_MARKERS = (
    "workflow",
    "流程",
    "步骤",
    "复用",
    "可复用",
    "repeatable",
    "reusable",
    "playbook",
)
_JSON_OBJECT_RE = re.compile(r"\{.*\}", re.DOTALL)


def _content_text(content: Any) -> str:
    if isinstance(content, str):
        return content
    if isinstance(content, list):
        parts: list[str] = []
        for item in content:
            if isinstance(item, dict):
                if isinstance(item.get("text"), str):
                    parts.append(item["text"])
                elif item.get("type") == "image_url":
                    parts.append("[image]")
            elif item is not None:
                parts.append(str(item))
        return "\n".join(parts)
    return "" if content is None else str(content)


def _tool_call_names(message: Mapping[str, Any]) -> list[str]:
    names: list[str] = []
    for tool_call in message.get("tool_calls") or []:
        if not isinstance(tool_call, Mapping):
            continue
        function = tool_call.get("function")
        if isinstance(function, Mapping):
            name = str(function.get("name") or "").strip()
        else:
            name = str(tool_call.get("name") or "").strip()
        if name:
            names.append(name)
    return names


def _tool_call_count(messages: list[dict[str, Any]]) -> int:
    return sum(len(_tool_call_names(message)) for message in messages)


def _has_tool_error(messages: list[dict[str, Any]]) -> bool:
    for message in messages:
        if message.get("role") != "tool":
            continue
        content = _content_text(message.get("content")).strip().lower()
        if content.startswith("error") or "analyze the error above" in content:
            return True
    return False


def _has_user_correction(messages: list[dict[str, Any]]) -> bool:
    for message in messages:
        if message.get("role") != "user":
            continue
        text = _content_text(message.get("content")).lower()
        if any(marker in text for marker in _CORRECTION_MARKERS):
            return True
    return False


def _looks_like_reusable_workflow(messages: list[dict[str, Any]]) -> bool:
    text = "\n".join(_content_text(message.get("content")) for message in messages).lower()
    return _tool_call_count(messages) >= 3 or any(marker in text for marker in _WORKFLOW_MARKERS)


def detect_skill_learning_trigger_reasons(
    messages: list[dict[str, Any]],
    *,
    stop_reason: str,
) -> list[str]:
    """Return ordered trigger reasons for auto skill proposal consideration."""

    if stop_reason != "completed":
        return []
    reasons: list[str] = []
    if _tool_call_count(messages) >= 5:
        reasons.append("complex_task_5_tool_calls")
    if _has_tool_error(messages):
        reasons.append("error_recovered")
    if _has_user_correction(messages):
        reasons.append("user_correction")
    if not reasons and _looks_like_reusable_workflow(messages):
        reasons.append("nontrivial_reusable_workflow")
    return reasons


def _extract_json_object(text: str) -> dict[str, Any]:
    raw = str(text or "").strip()
    if raw.startswith("```"):
        raw = re.sub(r"^```(?:json)?\s*", "", raw, flags=re.IGNORECASE)
        raw = re.sub(r"\s*```$", "", raw)
    match = _JSON_OBJECT_RE.search(raw)
    if not match:
        raise ValueError("Model did not return a JSON object.")
    payload = json.loads(match.group(0))
    if not isinstance(payload, dict):
        raise ValueError("Model JSON must be an object.")
    return payload


def _format_turn_transcript(messages: list[dict[str, Any]], *, max_chars: int = 14_000) -> str:
    lines: list[str] = []
    for message in messages:
        role = str(message.get("role") or "unknown")
        if names := _tool_call_names(message):
            lines.append(f"{role.upper()} tool_calls: {', '.join(names)}")
        elif role == "tool":
            name = str(message.get("name") or "tool")
            content = _content_text(message.get("content")).replace("\n", " ").strip()
            lines.append(f"TOOL {name}: {content[:800]}")
        else:
            content = _content_text(message.get("content")).strip()
            if content:
                lines.append(f"{role.upper()}: {content[:1200]}")
    transcript = "\n".join(lines)
    if len(transcript) > max_chars:
        return transcript[-max_chars:]
    return transcript


def _proposal_evidence(
    messages: list[dict[str, Any]],
    *,
    trigger_reasons: list[str],
    final_content: str,
    session_key: str,
) -> list[str]:
    tool_names: list[str] = []
    for message in messages:
        tool_names.extend(_tool_call_names(message))
    evidence = [
        f"session={session_key}",
        f"triggers={', '.join(trigger_reasons)}",
    ]
    if tool_names:
        evidence.append(f"tools={', '.join(tool_names[:12])}")
    if final_content:
        evidence.append(f"final={final_content[:240]}")
    return evidence


class SkillProposalGenerator:
    """Generate pending Agent Skills Workbench proposals from completed turns."""

    def __init__(
        self,
        *,
        workspace: Path,
        provider: LLMProvider,
        model: str,
        timeout_s: float = 45.0,
        service: AgentSkillService | None = None,
    ) -> None:
        self.workspace = Path(workspace)
        self.provider = provider
        self.model = model
        self.timeout_s = timeout_s
        self.service = service or AgentSkillService(self.workspace)

    async def submit_turn(
        self,
        *,
        messages: list[dict[str, Any]],
        final_content: str,
        trigger_reasons: list[str],
        session_key: str,
    ) -> dict[str, Any] | None:
        """Classify a completed turn and create or update a pending proposal."""

        if not trigger_reasons:
            return None
        transcript = _format_turn_transcript(messages)
        evidence = _proposal_evidence(
            messages,
            trigger_reasons=trigger_reasons,
            final_content=final_content,
            session_key=session_key,
        )
        try:
            decision = await self._classify(transcript, trigger_reasons)
            kind = str(decision.get("decision") or decision.get("action") or "skip").strip().lower()
            if kind not in {"create", "update"}:
                return None
            name = str(decision.get("name") or "").strip()
            reason = str(decision.get("reason") or "OpenHire detected a reusable workflow.").strip()
            if kind == "update":
                return await self._submit_update(
                    name=name,
                    reason=reason,
                    transcript=transcript,
                    trigger_reasons=trigger_reasons,
                    evidence=evidence,
                )
            return await self._submit_create(
                name=name,
                reason=reason,
                transcript=transcript,
                trigger_reasons=trigger_reasons,
                evidence=evidence,
            )
        except Exception as exc:
            logger.warning("Skill proposal generation skipped: {}", exc)
            return None

    async def _chat_json(self, system: str, user: str, *, max_tokens: int = 2048) -> dict[str, Any]:
        response = await asyncio.wait_for(
            self.provider.chat_with_retry(
                model=self.model,
                messages=[
                    {"role": "system", "content": system},
                    {"role": "user", "content": user},
                ],
                tools=None,
                tool_choice=None,
                temperature=0.2,
                max_tokens=max_tokens,
            ),
            timeout=self.timeout_s,
        )
        return _extract_json_object(response.content or "")

    async def _classify(self, transcript: str, trigger_reasons: list[str]) -> dict[str, Any]:
        skills = self.service.list()
        summaries = "\n".join(
            f"- {item['name']} ({item.get('source', 'unknown')}): {item.get('description', '')}"
            for item in skills
        ) or "(none)"
        return await self._chat_json(
            "You classify whether an OpenHire turn should create or update an Agent Skill. "
            "Return JSON only: {\"decision\":\"skip|create|update\",\"name\":\"kebab-case-skill-name\",\"reason\":\"...\"}. "
            "Choose update when an existing skill summary is functionally similar; otherwise create. "
            "Choose skip when the workflow is trivial, one-off, or already fully covered.",
            (
                f"Trigger reasons: {', '.join(trigger_reasons)}\n\n"
                f"Existing skills:\n{summaries}\n\n"
                f"Turn transcript:\n{transcript}"
            ),
            max_tokens=1200,
        )

    async def _submit_create(
        self,
        *,
        name: str,
        reason: str,
        transcript: str,
        trigger_reasons: list[str],
        evidence: list[str],
    ) -> dict[str, Any] | None:
        payload = await self._chat_json(
            "You write concise Agent Skill proposals for OpenHire. Return JSON only: "
            "{\"content\":\"complete SKILL.md markdown\"}. The markdown must include YAML frontmatter "
            "with name and description, then actionable instructions under 2000 words.",
            f"Skill name: {name}\nReason: {reason}\nTurn transcript:\n{transcript}",
            max_tokens=3200,
        )
        content = str(payload.get("content") or "").strip()
        if not content:
            return None
        return self.service.create_proposal(
            {
                "action": "create",
                "source": "turn",
                "name": name,
                "reason": reason,
                "content": content,
                "trigger_reasons": trigger_reasons,
                "evidence": evidence,
            }
        )

    async def _submit_update(
        self,
        *,
        name: str,
        reason: str,
        transcript: str,
        trigger_reasons: list[str],
        evidence: list[str],
    ) -> dict[str, Any] | None:
        try:
            detail = self.service.get(name)
        except Exception:
            return await self._submit_create(
                name=name,
                reason=reason,
                transcript=transcript,
                trigger_reasons=trigger_reasons,
                evidence=evidence,
            )
        source = str(detail.get("skill", {}).get("source") or "")
        current = str(detail.get("markdown") or "")
        if source != "workspace":
            payload = await self._chat_json(
                "You update a built-in Agent Skill by proposing a workspace shadow copy. Return JSON only: "
                "{\"content\":\"complete updated SKILL.md markdown\"}. Preserve the same frontmatter name.",
                f"Skill name: {name}\nReason: {reason}\nCurrent SKILL.md:\n{current}\n\nTurn transcript:\n{transcript}",
                max_tokens=3600,
            )
            content = str(payload.get("content") or "").strip()
            if not content:
                return None
            return self.service.create_proposal(
                {
                    "action": "create",
                    "source": "turn",
                    "name": name,
                    "reason": reason,
                    "content": content,
                    "trigger_reasons": trigger_reasons,
                    "evidence": evidence,
                }
            )
        payload = await self._chat_json(
            "You update an existing workspace Agent Skill. Return JSON only in one of these shapes: "
            "{\"action\":\"patch\",\"old_string\":\"exact existing substring\",\"new_string\":\"replacement\"} "
            "or {\"action\":\"edit\",\"content\":\"complete updated SKILL.md markdown\"}. Prefer patch when reliable.",
            f"Skill name: {name}\nReason: {reason}\nCurrent SKILL.md:\n{current}\n\nTurn transcript:\n{transcript}",
            max_tokens=3600,
        )
        action = str(payload.get("action") or "patch").strip().lower()
        if action == "edit":
            content = str(payload.get("content") or "").strip()
            if not content:
                return None
            return self.service.create_proposal(
                {
                    "action": "edit",
                    "source": "turn",
                    "name": name,
                    "reason": reason,
                    "content": content,
                    "trigger_reasons": trigger_reasons,
                    "evidence": evidence,
                }
            )
        return self.service.create_proposal(
            {
                "action": "patch",
                "source": "turn",
                "name": name,
                "reason": reason,
                "old_string": str(payload.get("old_string") or ""),
                "new_string": str(payload.get("new_string") or ""),
                "trigger_reasons": trigger_reasons,
                "evidence": evidence,
            }
        )
