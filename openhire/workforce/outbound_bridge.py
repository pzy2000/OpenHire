"""Parse Docker employee outbound bridge directives."""

from __future__ import annotations

import json
import re
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

OUTBOUND_PREFIX = "OPENHIRE_OUTBOUND_JSON:"
_JSON_OBJECT_RE = re.compile(r"\{.*\}", re.DOTALL)


@dataclass
class DockerOutboundMessage:
    """A validated message requested by a Docker employee."""

    content: str
    media: list[str] = field(default_factory=list)


@dataclass
class DockerOutboundParseResult:
    """Result of stripping and parsing outbound bridge directives."""

    cleaned_output: str
    messages: list[DockerOutboundMessage] = field(default_factory=list)
    errors: list[str] = field(default_factory=list)


def parse_docker_outbound_output(output: str, *, workspace: Path) -> DockerOutboundParseResult:
    """Parse ``OPENHIRE_OUTBOUND_JSON`` lines from Docker stdout.

    The Docker process is untrusted for routing. It may request content/media
    only; the host decides channel and chat based on the current OpenHire turn.
    """
    messages: list[DockerOutboundMessage] = []
    errors: list[str] = []
    kept_lines: list[str] = []
    directive_index = 0

    for line in str(output or "").splitlines():
        stripped = line.strip()
        if not stripped.startswith(OUTBOUND_PREFIX):
            kept_lines.append(line)
            continue

        directive_index += 1
        raw = stripped[len(OUTBOUND_PREFIX):].strip()
        try:
            payload = json.loads(raw)
        except json.JSONDecodeError as exc:
            errors.append(f"outbound message {directive_index} invalid JSON: {exc.msg}")
            continue

        message = _parse_payload(payload, directive_index, workspace=workspace, errors=errors)
        if message is not None:
            messages.append(message)

    return DockerOutboundParseResult(
        cleaned_output="\n".join(kept_lines).strip(),
        messages=messages,
        errors=errors,
    )


def clean_docker_agent_output(output: str) -> str:
    """Return user-sendable text from a Docker agent result."""
    lines: list[str] = []
    for line in str(output or "").splitlines():
        stripped = line.strip()
        if not stripped:
            continue
        if stripped == "🐈 nanobot":
            continue
        if stripped.startswith(OUTBOUND_PREFIX):
            stripped = stripped[len(OUTBOUND_PREFIX):].strip()
            if not stripped:
                continue
        if stripped.startswith("Outbound bridge error:"):
            continue
        lines.append(stripped)

    text = "\n".join(lines).strip()
    if not text:
        return ""

    json_text = text
    match = _JSON_OBJECT_RE.search(text)
    if match:
        json_text = match.group(0)
    try:
        payload = json.loads(json_text)
    except json.JSONDecodeError:
        return text
    if isinstance(payload, dict) and isinstance(payload.get("content"), str):
        return payload["content"].strip()
    return text


def _parse_payload(
    payload: Any,
    index: int,
    *,
    workspace: Path,
    errors: list[str],
) -> DockerOutboundMessage | None:
    if not isinstance(payload, dict):
        errors.append(f"outbound message {index} must be a JSON object")
        return None
    if "channel" in payload or "chat_id" in payload:
        errors.append(f"outbound message {index} must not specify channel or chat_id")
        return None

    content = str(payload.get("content") or "").strip()
    if not content:
        errors.append(f"outbound message {index} content is required")
        return None

    raw_media = payload.get("media") or []
    if not isinstance(raw_media, list):
        errors.append(f"outbound message {index} media must be a list")
        return None

    media: list[str] = []
    for item in raw_media:
        mapped = _map_media_path(item, index, workspace=workspace, errors=errors)
        if mapped is None:
            return None
        media.append(mapped)

    return DockerOutboundMessage(content=content, media=media)


def _map_media_path(
    value: Any,
    index: int,
    *,
    workspace: Path,
    errors: list[str],
) -> str | None:
    if not isinstance(value, str) or not value.strip():
        errors.append(f"outbound message {index} media paths must be non-empty strings")
        return None

    raw = value.strip()
    path = Path(raw)
    if path.is_absolute():
        try:
            relative = path.relative_to("/workspace")
        except ValueError:
            errors.append(f"outbound message {index} media path '{raw}' escapes workspace")
            return None
    else:
        relative = path

    workspace_root = workspace.resolve(strict=False)
    candidate = (workspace_root / relative).resolve(strict=False)
    try:
        candidate.relative_to(workspace_root)
    except ValueError:
        errors.append(f"outbound message {index} media path '{raw}' escapes workspace")
        return None
    return str(candidate)
