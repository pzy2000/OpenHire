"""Message router — route group messages to the appropriate digital employee."""

from __future__ import annotations

import json
import re
from dataclasses import dataclass, field
from typing import TYPE_CHECKING, Any

from loguru import logger

from openhire.workforce.registry import AgentEntry, AgentRegistry

if TYPE_CHECKING:
    from openhire.providers.base import LLMProvider


@dataclass
class RoutingDecision:
    """Result of message routing."""

    target_agents: list[str] = field(default_factory=list)  # agent_id list
    reason: str = ""
    strategy: str = ""  # "mention" / "skill_match" / "llm_classify" / "broadcast" / "none"


# Skill keyword mapping — maps common terms to skill tags
_SKILL_KEYWORDS: dict[str, list[str]] = {
    "前端": ["frontend", "react", "vue", "css", "html", "typescript", "javascript", "ui"],
    "后端": ["backend", "api", "server", "database", "python", "java", "go", "node"],
    "算法": ["algorithm", "ml", "ai", "model", "training", "data", "pytorch", "tensorflow"],
    "设计": ["design", "figma", "ui", "ux", "sketch", "prototype"],
    "运维": ["devops", "deploy", "docker", "k8s", "kubernetes", "ci", "cd", "infra"],
    "测试": ["test", "qa", "testing", "automation", "selenium", "cypress"],
    "产品": ["product", "prd", "requirement", "需求", "feature"],
    "数据": ["data", "sql", "etl", "analytics", "dashboard", "bi"],
    "frontend": ["frontend", "react", "vue", "css", "html", "typescript", "javascript"],
    "backend": ["backend", "api", "server", "database", "python", "java", "go"],
    "github": ["github", "git", "pr", "pull request", "commit", "branch", "merge"],
    "figma": ["figma", "design", "mockup", "prototype"],
}


class MessageRouter:
    """Route group chat messages to the appropriate digital employee(s)."""

    def __init__(
        self,
        registry: AgentRegistry,
        provider: "LLMProvider | None" = None,
        model: str | None = None,
        llm_threshold: float = 0.7,
    ) -> None:
        self._registry = registry
        self._provider = provider
        self._model = model
        self._llm_threshold = llm_threshold

    async def route(
        self,
        content: str,
        sender_id: str,
        group_id: str,
        mentions: list[str] | None = None,
        metadata: dict[str, Any] | None = None,
    ) -> RoutingDecision:
        """Determine which agent(s) should handle this message.

        Routing priority:
        1. Explicit @ mention of a person → their digital employee
        2. Skill/keyword matching against group roster
        3. LLM-based intent classification (if provider available)
        4. Fallback: no routing (main agent handles it)
        """
        roster = self._registry.get_group_roster(group_id)
        if not roster:
            return RoutingDecision(strategy="none", reason="no agents in this group")

        # 1. Mention-based routing
        if mentions:
            decision = self._route_by_mention(mentions, roster)
            if decision.target_agents:
                return decision

        # 2. Skill/keyword matching
        decision = self._route_by_skill(content, roster)
        if decision.target_agents:
            return decision

        # 3. LLM classification
        if self._provider:
            decision = await self._route_by_llm(content, roster)
            if decision.target_agents:
                return decision

        return RoutingDecision(strategy="none", reason="no matching agent found")

    def _route_by_mention(
        self, mentions: list[str], roster: list[AgentEntry],
    ) -> RoutingDecision:
        """Route by @ mention — find the digital employee of the mentioned person."""
        owner_map = {e.owner_id: e for e in roster}
        targets = [owner_map[m].agent_id for m in mentions if m in owner_map]
        if targets:
            return RoutingDecision(
                target_agents=targets,
                reason=f"mentioned user(s) matched to agent(s)",
                strategy="mention",
            )
        return RoutingDecision(strategy="mention")

    def _route_by_skill(
        self, content: str, roster: list[AgentEntry],
    ) -> RoutingDecision:
        """Route by keyword/skill matching against agent skills."""
        content_lower = content.lower()
        scores: dict[str, int] = {}

        for agent in roster:
            score = 0
            # Direct skill match
            for skill in agent.skills:
                if skill.lower() in content_lower:
                    score += 2
            # Tool match
            for tool in agent.tools:
                if tool.lower() in content_lower:
                    score += 2
            # Keyword expansion match
            for keyword, related_skills in _SKILL_KEYWORDS.items():
                if keyword in content_lower:
                    for skill in agent.skills:
                        if skill.lower() in related_skills:
                            score += 1
            if score > 0:
                scores[agent.agent_id] = score

        if not scores:
            return RoutingDecision(strategy="skill_match")

        max_score = max(scores.values())
        # Return all agents with the top score (may be multiple for cross-cutting tasks)
        targets = [aid for aid, s in scores.items() if s == max_score]
        return RoutingDecision(
            target_agents=targets,
            reason=f"skill match (score={max_score})",
            strategy="skill_match",
        )

    async def _route_by_llm(
        self, content: str, roster: list[AgentEntry],
    ) -> RoutingDecision:
        """Use LLM to classify which agent should handle the message."""
        if not self._provider:
            return RoutingDecision(strategy="llm_classify")

        roster_desc = "\n".join(
            f"- {a.agent_id}: {a.name} | role={a.role} | skills={','.join(a.skills)} | tools={','.join(a.tools)}"
            for a in roster
        )
        prompt = (
            "You are a message router. Given a user message and a list of available agents, "
            "decide which agent(s) should handle the message.\n\n"
            f"Available agents:\n{roster_desc}\n\n"
            f"User message: {content}\n\n"
            "Respond in JSON: {\"agents\": [\"agent_id\", ...], \"reason\": \"...\", \"confidence\": 0.0-1.0}\n"
            "If no agent is a good fit, return {\"agents\": [], \"reason\": \"...\", \"confidence\": 0.0}"
        )

        try:
            messages = [{"role": "user", "content": prompt}]
            response = await self._provider.chat(
                messages=messages,
                model=self._model,
                max_tokens=200,
                temperature=0.0,
            )
            text = response.get("content", "") if isinstance(response, dict) else str(response)
            # Extract JSON from response
            match = re.search(r"\{[^}]+\}", text)
            if match:
                result = json.loads(match.group())
                agents = result.get("agents", [])
                confidence = result.get("confidence", 0.0)
                reason = result.get("reason", "")
                if agents and confidence >= self._llm_threshold:
                    # Validate agent IDs exist in roster
                    valid_ids = {a.agent_id for a in roster}
                    targets = [a for a in agents if a in valid_ids]
                    if targets:
                        return RoutingDecision(
                            target_agents=targets,
                            reason=f"LLM: {reason} (confidence={confidence:.2f})",
                            strategy="llm_classify",
                        )
        except Exception as e:
            logger.warning("LLM routing failed: {}", e)

        return RoutingDecision(strategy="llm_classify")
