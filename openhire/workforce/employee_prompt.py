"""Split and compose per-employee bootstrap prompt files."""

from __future__ import annotations

import asyncio
import inspect
import json
import re
from dataclasses import dataclass
from typing import Any

from loguru import logger

from openhire.workforce.required_skill import (
    REQUIRED_EMPLOYEE_SKILL_PROMPT_END,
    REQUIRED_EMPLOYEE_SKILL_PROMPT_START,
    build_required_employee_skill_prompt_block,
)
from openhire.workforce.workspace import EMPLOYEE_CONFIG_FILES, default_employee_config_text

SOUL_BLOCK_START = "<!-- OpenHire Employee SOUL: begin -->"
SOUL_BLOCK_END = "<!-- OpenHire Employee SOUL: end -->"
AGENTS_BLOCK_START = "<!-- OpenHire Employee AGENTS: begin -->"
AGENTS_BLOCK_END = "<!-- OpenHire Employee AGENTS: end -->"

_JSON_BLOCK_RE = re.compile(r"```(?:json)?\s*(.*?)```", re.DOTALL | re.IGNORECASE)
_REQUIRED_BLOCK_RE = re.compile(
    re.escape(REQUIRED_EMPLOYEE_SKILL_PROMPT_START)
    + r".*?"
    + re.escape(REQUIRED_EMPLOYEE_SKILL_PROMPT_END),
    re.DOTALL,
)


@dataclass(slots=True)
class EmployeePromptFragments:
    soul: str
    agents: str
    used_fallback: bool = False


async def compose_employee_bootstrap_files(
    entry: Any,
    *,
    base_files: dict[str, str] | None = None,
    llm_provider: Any | None = None,
    retries: int = 3,
) -> dict[str, str]:
    """Return split SOUL.md and AGENTS.md content for a newly-created employee."""
    fragments = await split_employee_prompt(entry, llm_provider=llm_provider, retries=retries)
    base_files = base_files or {}
    soul_base = base_files.get("SOUL.md") or default_employee_config_text("SOUL.md")
    agents_base = base_files.get("AGENTS.md") or default_employee_config_text("AGENTS.md")

    soul_body = _remove_required_skill_block(fragments.soul)
    agents_body = _remove_required_skill_block(fragments.agents)
    required_block = build_required_employee_skill_prompt_block()
    if required_block not in agents_body:
        agents_body = f"{agents_body.rstrip()}\n\n{required_block}".strip()

    return {
        "SOUL.md": _append_managed_block(
            soul_base,
            SOUL_BLOCK_START,
            SOUL_BLOCK_END,
            soul_body,
        ),
        "AGENTS.md": _append_managed_block(
            agents_base,
            AGENTS_BLOCK_START,
            AGENTS_BLOCK_END,
            agents_body,
        ),
    }


async def split_employee_prompt(
    entry: Any,
    *,
    llm_provider: Any | None = None,
    retries: int = 3,
) -> EmployeePromptFragments:
    chat_with_retry = _chat_with_retry(llm_provider)
    last_error = "no LLM provider available"
    if chat_with_retry is not None:
        for _attempt in range(max(1, retries)):
            try:
                response = await chat_with_retry(
                    messages=[
                        {
                            "role": "system",
                            "content": (
                                "Split a digital employee bootstrap prompt into append-only markdown fragments. "
                                "SOUL.md is for identity, voice, tone, personality, and communication style. "
                                "AGENTS.md is for work methods, operating rules, responsibilities, workflows, "
                                "evidence, escalation, reporting, and collaboration protocol. "
                                "Return JSON only: {\"soul\":\"...\",\"agents\":\"...\"}. "
                                "Do not include markdown fences. Do not reproduce the required-skill marker block; "
                                "OpenHire appends that canonical block separately."
                            ),
                        },
                        {
                            "role": "user",
                            "content": json.dumps(
                                {
                                    "employee": {
                                        "name": getattr(entry, "name", ""),
                                        "role": getattr(entry, "role", ""),
                                        "skills": list(getattr(entry, "skills", []) or []),
                                        "agent_type": getattr(entry, "agent_type", ""),
                                        "system_prompt": getattr(entry, "system_prompt", ""),
                                    }
                                },
                                ensure_ascii=False,
                            ),
                        },
                    ],
                    max_tokens=1200,
                    temperature=0,
                )
                return _parse_llm_fragments(str(getattr(response, "content", "") or ""))
            except Exception as exc:
                last_error = str(exc)

    logger.warning(
        "Employee prompt split failed for {} ({}); using deterministic fallback: {}",
        getattr(entry, "name", ""),
        getattr(entry, "agent_id", ""),
        last_error,
    )
    return _deterministic_fragments(entry)


async def read_container_bootstrap_file(container_name: str, adapter: Any, filename: str) -> str:
    template_paths = getattr(adapter, "bootstrap_template_paths", {}) or {}
    template_path = str(template_paths.get(filename) or "").strip()
    if not template_path:
        return ""

    proc = await asyncio.create_subprocess_exec(
        "docker",
        "exec",
        container_name,
        "cat",
        template_path,
        stdout=asyncio.subprocess.PIPE,
        stderr=asyncio.subprocess.PIPE,
    )
    stdout, stderr = await proc.communicate()
    if proc.returncode != 0:
        logger.warning(
            "Failed to read {} template from {} at {}: {}",
            filename,
            container_name,
            template_path,
            stderr.decode(errors="replace")[:500],
        )
        return ""
    return stdout.decode(errors="replace").strip()


def _chat_with_retry(provider: Any | None) -> Any | None:
    chat_with_retry = getattr(provider, "chat_with_retry", None) if provider else None
    if not chat_with_retry or not inspect.iscoroutinefunction(chat_with_retry):
        return None
    return chat_with_retry


def _parse_llm_fragments(content: str) -> EmployeePromptFragments:
    payload = _extract_json(content)
    soul = _text(
        payload.get("soul")
        or payload.get("soul_md")
        or payload.get("SOUL.md")
        or payload.get("SOUL")
    )
    agents = _text(
        payload.get("agents")
        or payload.get("agents_md")
        or payload.get("AGENTS.md")
        or payload.get("AGENTS")
    )
    soul = _remove_required_skill_block(soul)
    agents = _remove_required_skill_block(agents)
    if not soul:
        raise ValueError("Prompt split response must include non-empty soul.")
    if not agents:
        raise ValueError("Prompt split response must include non-empty agents.")
    return EmployeePromptFragments(soul=soul, agents=agents)


def _extract_json(content: str) -> dict[str, Any]:
    match = _JSON_BLOCK_RE.search(content)
    raw = match.group(1) if match else content
    payload = json.loads(raw.strip())
    if not isinstance(payload, dict):
        raise ValueError("Prompt split response must be a JSON object.")
    return payload


def _deterministic_fragments(entry: Any) -> EmployeePromptFragments:
    name = _text(getattr(entry, "name", ""))
    role = _text(getattr(entry, "role", ""))
    agent_type = _text(getattr(entry, "agent_type", ""))
    source_prompt = _remove_required_skill_block(_text(getattr(entry, "system_prompt", "")))
    skills = [
        _text(skill)
        for skill in list(getattr(entry, "skills", []) or [])
        if _text(skill)
    ]

    soul_lines = [
        "## OpenHire Employee Identity",
        f"- Name: {name or 'Digital Employee'}",
        f"- Role: {role or 'General digital employee'}",
    ]
    if agent_type:
        soul_lines.append(f"- Runtime: {agent_type}")
    soul_lines.extend([
        "",
        "## Voice",
        "Be direct, grounded, and specific to this role. Keep responses concise unless the task requires depth.",
    ])
    if source_prompt:
        soul_lines.extend(["", "## Role Prompt", source_prompt])
    elif role:
        soul_lines.extend(["", "## Role Prompt", f"你是{role}，负责该角色的核心交付。"])

    agents_lines = [
        "## OpenHire Employee Operating Instructions",
        f"- Role: {role or 'General digital employee'}",
    ]
    if skills:
        agents_lines.append(f"- Skills: {', '.join(skills)}")
    agents_lines.extend([
        "- Work from verifiable evidence and cite files, logs, links, or tests when decisions depend on them.",
        "- Escalate permission, cost, safety, production-risk, or unresolved requirement conflicts to the human owner.",
        "- Keep handoff state current: background, goal, progress, attempted paths, blockers, links, and next step.",
    ])

    return EmployeePromptFragments(
        soul="\n".join(soul_lines).strip(),
        agents="\n".join(agents_lines).strip(),
        used_fallback=True,
    )


def compose_case_bootstrap_files(files: dict[str, str] | None) -> dict[str, str]:
    """Normalize case-provided bootstrap files without invoking any LLM."""
    provided = files if isinstance(files, dict) else {}
    normalized: dict[str, str] = {}
    for filename in EMPLOYEE_CONFIG_FILES:
        if filename in provided:
            content = str(provided.get(filename) or "")
        elif filename in {"SOUL.md", "AGENTS.md", "TOOLS.md"}:
            content = default_employee_config_text(filename)
        else:
            content = ""
        if filename == "SOUL.md":
            normalized[filename] = _remove_required_skill_block(content)
            continue
        if filename == "AGENTS.md":
            agents_body = _remove_required_skill_block(content)
            required_block = build_required_employee_skill_prompt_block()
            normalized[filename] = f"{agents_body.rstrip()}\n\n{required_block}".strip() if agents_body else required_block
            continue
        normalized[filename] = content
    return normalized


def _append_managed_block(base: str, start: str, end: str, body: str) -> str:
    block_pattern = re.compile(re.escape(start) + r".*?" + re.escape(end), re.DOTALL)
    clean_base = block_pattern.sub("", str(base or "")).rstrip()
    clean_body = str(body or "").strip()
    block = f"{start}\n{clean_body}\n{end}".strip()
    return f"{clean_base}\n\n{block}\n" if clean_base else f"{block}\n"


def _remove_required_skill_block(value: str) -> str:
    return _REQUIRED_BLOCK_RE.sub("", str(value or "")).strip()


def _text(value: Any) -> str:
    return str(value or "").strip()
