"""Required digital employee skill contract."""

from __future__ import annotations

import re
from pathlib import Path
from typing import Any

REQUIRED_EMPLOYEE_SKILL_ID = "excellent-employee"
REQUIRED_EMPLOYEE_SKILL_NAME = "优秀员工协议"
REQUIRED_EMPLOYEE_SKILL_SOURCE = "system"
REQUIRED_EMPLOYEE_SKILL_STATUS = "required"
REQUIRED_EMPLOYEE_SKILL_PROMPT_START = "[OpenHire Required Skill: excellent-employee]"
REQUIRED_EMPLOYEE_SKILL_PROMPT_END = "[/OpenHire Required Skill: excellent-employee]"

_SKILL_FILE = Path(__file__).resolve().parent.parent / "skills" / REQUIRED_EMPLOYEE_SKILL_ID / "SKILL.md"
_FRONTMATTER_RE = re.compile(r"^---\s*\r?\n(.*?)\r?\n---\s*\r?\n?", re.DOTALL)
_PROMPT_BLOCK_RE = re.compile(
    re.escape(REQUIRED_EMPLOYEE_SKILL_PROMPT_START)
    + r".*?"
    + re.escape(REQUIRED_EMPLOYEE_SKILL_PROMPT_END),
    re.DOTALL,
)


class RequiredEmployeeSkillError(RuntimeError):
    """Raised when the required employee skill file is missing or invalid."""


def required_employee_skill_path() -> Path:
    return _SKILL_FILE


def _parse_frontmatter(markdown: str) -> tuple[dict[str, str], str]:
    match = _FRONTMATTER_RE.match(markdown)
    if not match:
        raise RequiredEmployeeSkillError(
            f"Required employee skill file '{_SKILL_FILE}' must start with YAML frontmatter."
        )
    metadata: dict[str, str] = {}
    for line in match.group(1).splitlines():
        stripped = line.strip()
        if not stripped or stripped.startswith("#"):
            continue
        if ":" not in stripped:
            raise RequiredEmployeeSkillError(
                f"Required employee skill file '{_SKILL_FILE}' has invalid frontmatter."
            )
        key, value = stripped.split(":", 1)
        metadata[key.strip()] = value.strip().strip('"\'')
    return metadata, markdown[match.end():].strip()


def load_required_employee_skill() -> tuple[dict[str, str], str]:
    markdown = load_required_employee_skill_markdown()
    metadata, body = _parse_frontmatter(markdown)
    if metadata.get("name") != REQUIRED_EMPLOYEE_SKILL_ID:
        raise RequiredEmployeeSkillError(
            f"Required employee skill file '{_SKILL_FILE}' must declare name: {REQUIRED_EMPLOYEE_SKILL_ID}."
        )
    if not metadata.get("description"):
        raise RequiredEmployeeSkillError(
            f"Required employee skill file '{_SKILL_FILE}' must declare description."
        )
    if not body:
        raise RequiredEmployeeSkillError(f"Required employee skill file '{_SKILL_FILE}' must have body content.")
    return metadata, body


def load_required_employee_skill_markdown() -> str:
    if not _SKILL_FILE.is_file():
        raise RequiredEmployeeSkillError(f"Required employee skill file '{_SKILL_FILE}' was not found.")
    try:
        return _SKILL_FILE.read_text(encoding="utf-8")
    except UnicodeDecodeError as exc:
        raise RequiredEmployeeSkillError(
            f"Required employee skill file '{_SKILL_FILE}' must be valid UTF-8."
        ) from exc


def validate_required_employee_skill_markdown(markdown: str) -> tuple[dict[str, str], str]:
    metadata, body = _parse_frontmatter(str(markdown or ""))
    if metadata.get("name") != REQUIRED_EMPLOYEE_SKILL_ID:
        raise RequiredEmployeeSkillError(
            f"Required employee skill markdown must declare name: {REQUIRED_EMPLOYEE_SKILL_ID}."
        )
    if not metadata.get("description"):
        raise RequiredEmployeeSkillError("Required employee skill markdown must declare description.")
    if not body:
        raise RequiredEmployeeSkillError("Required employee skill markdown must have body content.")
    return metadata, body


def save_required_employee_skill_markdown(markdown: str) -> None:
    validate_required_employee_skill_markdown(markdown)
    _SKILL_FILE.parent.mkdir(parents=True, exist_ok=True)
    _SKILL_FILE.write_text(str(markdown), encoding="utf-8")


def required_employee_skill_record() -> dict[str, str]:
    metadata, _body = load_required_employee_skill()
    return {
        "id": REQUIRED_EMPLOYEE_SKILL_ID,
        "source": REQUIRED_EMPLOYEE_SKILL_SOURCE,
        "external_id": REQUIRED_EMPLOYEE_SKILL_ID,
        "name": metadata.get("display_name") or REQUIRED_EMPLOYEE_SKILL_NAME,
        "description": metadata["description"],
        "version": "",
        "author": "OpenHire",
        "license": "",
        "source_url": str(_SKILL_FILE),
        "safety_status": REQUIRED_EMPLOYEE_SKILL_STATUS,
        "tags": ["system", REQUIRED_EMPLOYEE_SKILL_ID],
        "imported_at": "",
    }


def required_employee_skill_name() -> str:
    return required_employee_skill_record()["name"]


def _normalize_text(value: Any) -> str:
    return str(value or "").strip()


def _prepend_unique(required: str, items: list[str] | None, *, aliases: set[str] | None = None) -> list[str]:
    required_text = _normalize_text(required)
    alias_keys = {required_text.casefold(), *(alias.casefold() for alias in aliases or set())}
    result = [required_text]
    seen = {required_text.casefold()}
    for item in items or []:
        text = _normalize_text(item)
        if not text:
            continue
        key = text.casefold()
        if key in seen or key in alias_keys:
            continue
        seen.add(key)
        result.append(text)
    return result


def ensure_required_employee_skill_ids(skill_ids: list[str] | None) -> list[str]:
    return _prepend_unique(REQUIRED_EMPLOYEE_SKILL_ID, skill_ids)


def ensure_required_employee_skill_names(skills: list[str] | None) -> list[str]:
    required_name = required_employee_skill_name()
    return _prepend_unique(
        required_name,
        skills,
        aliases={REQUIRED_EMPLOYEE_SKILL_ID, REQUIRED_EMPLOYEE_SKILL_NAME},
    )


def inject_required_employee_skill_prompt(system_prompt: str) -> str:
    prompt = _normalize_text(system_prompt)
    if REQUIRED_EMPLOYEE_SKILL_PROMPT_START in prompt:
        return prompt
    block = build_required_employee_skill_prompt_block()
    return f"{prompt}\n\n{block}".strip() if prompt else block


def build_required_employee_skill_prompt_block() -> str:
    _metadata, body = load_required_employee_skill()
    return f"{REQUIRED_EMPLOYEE_SKILL_PROMPT_START}\n{body}\n{REQUIRED_EMPLOYEE_SKILL_PROMPT_END}"


def replace_required_employee_skill_prompt_block(system_prompt: str) -> tuple[str, bool]:
    prompt = str(system_prompt or "")
    if REQUIRED_EMPLOYEE_SKILL_PROMPT_START not in prompt:
        return prompt, False
    updated, count = _PROMPT_BLOCK_RE.subn(build_required_employee_skill_prompt_block(), prompt, count=1)
    return updated, count > 0


def apply_required_employee_skill_contract(
    *,
    skills: list[str] | None,
    skill_ids: list[str] | None,
    system_prompt: str,
) -> tuple[list[str], list[str], str]:
    return (
        ensure_required_employee_skill_names(skills),
        ensure_required_employee_skill_ids(skill_ids),
        inject_required_employee_skill_prompt(system_prompt),
    )
