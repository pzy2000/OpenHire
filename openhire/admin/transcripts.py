"""Read-only transcript builders for the admin dashboard."""

from __future__ import annotations

import asyncio
import json
import shlex
from typing import Any

from openhire.utils.helpers import safe_filename

DEFAULT_TRANSCRIPT_LIMIT = 200
MAX_TRANSCRIPT_LIMIT = 1000
MAX_CONTENT_CHARS = 12000
SUMMARY_CHARS = 180


class DockerTranscriptTimeout(RuntimeError):
    """Raised when a Docker transcript read exceeds its timeout."""


class DockerTranscriptReadError(RuntimeError):
    """Raised when Docker transcript extraction fails."""


def clamp_limit(value: Any, default: int = DEFAULT_TRANSCRIPT_LIMIT) -> int:
    try:
        limit = int(value)
    except (TypeError, ValueError):
        return default
    return max(1, min(MAX_TRANSCRIPT_LIMIT, limit))


def _truncate(text: str, limit: int = MAX_CONTENT_CHARS) -> str:
    if len(text) <= limit:
        return text
    return f"{text[:limit]}... [truncated {len(text) - limit} chars]"


def _preview(text: str, limit: int = SUMMARY_CHARS) -> str:
    text = " ".join(str(text or "").split())
    if len(text) <= limit:
        return text
    return f"{text[:limit - 1]}..."


def _json_preview(value: Any) -> str:
    try:
        return json.dumps(value, ensure_ascii=False, indent=2, sort_keys=True)
    except TypeError:
        return str(value)


def _content_to_text(content: Any) -> str:
    if content is None:
        return ""
    if isinstance(content, str):
        return content
    if isinstance(content, list):
        parts: list[str] = []
        for block in content:
            if isinstance(block, str):
                parts.append(block)
                continue
            if not isinstance(block, dict):
                parts.append(str(block))
                continue
            if "text" in block:
                parts.append(str(block.get("text") or ""))
                continue
            if block.get("type") in {"image", "image_url", "input_image"}:
                parts.append("[image]")
                continue
            if block.get("type") in {"tool_call", "function_call"} or "name" in block:
                continue
            parts.append(_json_preview(block))
        return "\n".join(part for part in parts if part)
    if isinstance(content, dict):
        if "text" in content:
            return str(content.get("text") or "")
        return _json_preview(content)
    return str(content)


def _normalize_role(role: Any) -> str:
    value = str(role or "system")
    if value == "toolResult":
        return "tool"
    if value in {"user", "assistant", "tool", "system"}:
        return value
    return "system"


def _tool_name_from_call(call: Any) -> str:
    if not isinstance(call, dict):
        return "tool"
    function = call.get("function")
    if isinstance(function, dict) and function.get("name"):
        return str(function["name"])
    if call.get("name"):
        return str(call["name"])
    return "tool"


def _tool_detail_from_call(call: Any) -> Any:
    if not isinstance(call, dict):
        return call
    function = call.get("function")
    if isinstance(function, dict):
        return {
            "name": function.get("name") or call.get("name") or "tool",
            "arguments": function.get("arguments") or {},
        }
    return {
        "name": call.get("name") or "tool",
        "arguments": call.get("arguments") or call.get("input") or {},
    }


def _extract_tool_calls(message: dict[str, Any]) -> list[dict[str, Any]]:
    raw_calls = message.get("tool_calls")
    calls: list[dict[str, Any]] = []
    if isinstance(raw_calls, list):
        calls.extend(call for call in raw_calls if isinstance(call, dict))
    content = message.get("content")
    if isinstance(content, list):
        for block in content:
            if not isinstance(block, dict):
                continue
            if block.get("type") in {"tool_call", "function_call"} or (
                block.get("name") and ("arguments" in block or "input" in block)
            ):
                calls.append(block)
    return calls


def _tool_call_summary(calls: list[dict[str, Any]]) -> str:
    names = [_tool_name_from_call(call) for call in calls]
    if not names:
        return ""
    label = "tool call" if len(names) == 1 else "tool calls"
    return f"{len(names)} {label}: {', '.join(names)}"


def normalize_messages(messages: list[dict[str, Any]], *, limit: int) -> list[dict[str, Any]]:
    items: list[dict[str, Any]] = []
    for index, message in enumerate(messages[-limit:]):
        if not isinstance(message, dict):
            continue
        role = _normalize_role(message.get("role"))
        content = _truncate(_content_to_text(message.get("content")))
        calls = _extract_tool_calls(message)
        detail_parts: list[str] = []
        if content:
            detail_parts.append(content)
        if calls:
            detail_parts.append(_json_preview([_tool_detail_from_call(call) for call in calls]))

        summary = _preview(content) or role
        if calls:
            summary = _tool_call_summary(calls)
        elif role == "tool":
            tool_name = str(
                message.get("name")
                or message.get("toolName")
                or message.get("tool_name")
                or "tool"
            )
            summary = f"{tool_name} result"

        items.append({
            "id": str(message.get("id") or message.get("tool_call_id") or message.get("toolCallId") or index),
            "role": role,
            "title": role if role != "tool" else str(message.get("name") or message.get("toolName") or "tool"),
            "timestamp": message.get("timestamp"),
            "content": content,
            "summary": summary,
            "detail": _truncate("\n\n".join(detail_parts)),
        })
    return items


def _split_session_key(key: str | None) -> tuple[str | None, str | None]:
    if not key or ":" not in key:
        return None, None
    return key.split(":", 1)


def _latest_session_key(loop: Any) -> str | None:
    explicit = getattr(loop, "_last_admin_session_key", None)
    if explicit:
        return str(explicit)
    sessions = getattr(loop, "sessions", None)
    if sessions is None or not hasattr(sessions, "list_sessions"):
        return None
    try:
        session_infos = list(sessions.list_sessions())
    except Exception:
        return None

    def _is_internal(key: str) -> bool:
        channel, _chat_id = _split_session_key(key)
        return channel in {"cli", "system", "cron", "heartbeat"}

    for info in session_infos:
        key = info.get("key") if isinstance(info, dict) else None
        if key and not _is_internal(str(key)):
            return str(key)
    if session_infos:
        key = session_infos[0].get("key") if isinstance(session_infos[0], dict) else None
        return str(key) if key else None
    return None


async def build_main_transcript(
    loop: Any,
    *,
    session_key: str | None = None,
    limit: int = DEFAULT_TRANSCRIPT_LIMIT,
) -> dict[str, Any]:
    limit = clamp_limit(limit)
    resolved_key = session_key or _latest_session_key(loop)
    if not resolved_key:
        return {
            "agent": "Main Agent",
            "source": "openhire-session",
            "sessionId": None,
            "status": "empty",
            "items": [],
            "warning": "No active main-agent session found.",
        }

    sessions = getattr(loop, "sessions", None)
    if sessions is None or not hasattr(sessions, "get_or_create"):
        return {
            "agent": "Main Agent",
            "source": "openhire-session",
            "sessionId": resolved_key,
            "status": "unavailable",
            "items": [],
            "warning": "Session manager is unavailable.",
        }
    session = sessions.get_or_create(str(resolved_key))
    items = normalize_messages(list(getattr(session, "messages", []) or []), limit=limit)
    return {
        "agent": "Main Agent",
        "source": "openhire-session",
        "sessionId": str(resolved_key),
        "status": "ok" if items else "empty",
        "items": items,
        "warning": None if items else "No messages stored for this session.",
    }


async def _docker_exec_text(container_name: str, *args: str, timeout: float = 2.0) -> str:
    proc = await asyncio.create_subprocess_exec(
        "docker",
        "exec",
        container_name,
        *args,
        stdout=asyncio.subprocess.PIPE,
        stderr=asyncio.subprocess.PIPE,
    )
    try:
        stdout, stderr = await asyncio.wait_for(proc.communicate(), timeout=timeout)
    except asyncio.TimeoutError:
        proc.kill()
        await proc.wait()
        raise
    if proc.returncode != 0:
        message = stderr.decode(errors="replace").strip() or stdout.decode(errors="replace").strip()
        raise DockerTranscriptReadError(message or f"docker exec exited with code {proc.returncode}")
    return stdout.decode(errors="replace")


def _infer_adapter(row: dict[str, Any]) -> str:
    agent_key = str(row.get("agentKey") or row.get("agent_key") or "").lower()
    image = str(row.get("image") or "").lower()
    name = str(row.get("containerName") or row.get("name") or "").lower()
    combined = " ".join([agent_key, image, name])
    if "openclaw" in combined:
        return "openclaw"
    if "nanobot" in combined:
        return "nanobot"
    if "hermes" in combined:
        return "hermes"
    return agent_key or "unknown"


def _container_name(row: dict[str, Any]) -> str:
    return str(row.get("containerName") or row.get("name") or "")


def _empty_docker_payload(
    *,
    container_name: str,
    source: str,
    session_id: str | None,
    status: str,
    warning: str,
) -> dict[str, Any]:
    return {
        "agent": container_name,
        "source": source,
        "sessionId": session_id,
        "status": status,
        "items": [],
        "warning": warning,
    }


def _parse_jsonl(raw: str) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for line in raw.splitlines():
        line = line.strip()
        if not line:
            continue
        try:
            item = json.loads(line)
        except json.JSONDecodeError:
            continue
        if isinstance(item, dict):
            rows.append(item)
    return rows


def _normalize_openclaw_jsonl(raw: str, *, limit: int) -> list[dict[str, Any]]:
    messages: list[dict[str, Any]] = []
    for row in _parse_jsonl(raw):
        if row.get("type") != "message":
            continue
        message = row.get("message")
        if not isinstance(message, dict):
            continue
        entry = dict(message)
        entry.setdefault("timestamp", row.get("timestamp"))
        entry.setdefault("id", row.get("id"))
        messages.append(entry)
    return normalize_messages(messages, limit=limit)


def _normalize_hermes_export(raw: str, *, limit: int) -> tuple[str | None, list[dict[str, Any]]]:
    session_id: str | None = None
    messages: list[dict[str, Any]] = []
    for row in _parse_jsonl(raw):
        if row.get("id") and session_id is None:
            session_id = str(row["id"])
        raw_messages = row.get("messages")
        if isinstance(raw_messages, list):
            for message in raw_messages:
                if isinstance(message, dict):
                    messages.append(message)
            continue
        if row.get("role"):
            messages.append(row)
    return session_id, normalize_messages(messages, limit=limit)


async def _build_openclaw_transcript(container_name: str, *, limit: int) -> dict[str, Any]:
    session_id = f"openhire-delegate-{container_name}"
    path = f"/home/node/.openclaw/agents/main/sessions/{session_id}.jsonl"
    raw = await _docker_exec_text(
        container_name,
        "sh",
        "-lc",
        f"cat {shlex.quote(path)} 2>/dev/null || true",
        timeout=2.5,
    )
    items = _normalize_openclaw_jsonl(raw, limit=limit)
    return {
        "agent": container_name,
        "source": "openclaw-container",
        "sessionId": session_id,
        "status": "ok" if items else "empty",
        "items": items,
        "warning": None if items else f"No OpenClaw session transcript found at {path}.",
    }


async def _build_nanobot_transcript(container_name: str, *, limit: int) -> dict[str, Any]:
    session_id = f"openhire-delegate-{container_name}"
    filename = safe_filename(session_id.replace(":", "_"))
    path = f"/workspace/sessions/{filename}.jsonl"
    raw = await _docker_exec_text(
        container_name,
        "sh",
        "-lc",
        f"cat {shlex.quote(path)} 2>/dev/null || true",
        timeout=2.5,
    )
    rows = _parse_jsonl(raw)
    messages = [row for row in rows if row.get("_type") != "metadata"]
    items = normalize_messages(messages, limit=limit)
    return {
        "agent": container_name,
        "source": "nanobot-container",
        "sessionId": session_id,
        "status": "ok" if items else "empty",
        "items": items,
        "warning": None if items else f"No nanobot session transcript found at {path}.",
    }


async def _build_hermes_transcript(container_name: str, *, limit: int) -> dict[str, Any]:
    source = f"openhire-{container_name}"
    script = (
        "tmp=$(mktemp); "
        f"if hermes sessions export \"$tmp\" --source {shlex.quote(source)} >/dev/null 2>/tmp/openhire-transcript.err; then "
        "cat \"$tmp\"; rm -f \"$tmp\"; "
        "else cat /tmp/openhire-transcript.err >&2; rm -f \"$tmp\"; exit 1; fi"
    )
    raw = await _docker_exec_text(container_name, "sh", "-lc", script, timeout=5.0)
    session_id, items = _normalize_hermes_export(raw, limit=limit)
    return {
        "agent": container_name,
        "source": "hermes-container",
        "sessionId": session_id or source,
        "status": "ok" if items else "empty",
        "items": items,
        "warning": None if items else f"No Hermes sessions found for source {source}.",
    }


async def build_docker_transcript(row: dict[str, Any], *, limit: int = DEFAULT_TRANSCRIPT_LIMIT) -> dict[str, Any]:
    limit = clamp_limit(limit)
    container_name = _container_name(row)
    adapter = _infer_adapter(row)
    try:
        if adapter == "openclaw":
            return await _build_openclaw_transcript(container_name, limit=limit)
        if adapter == "nanobot":
            return await _build_nanobot_transcript(container_name, limit=limit)
        if adapter == "hermes":
            return await _build_hermes_transcript(container_name, limit=limit)
    except asyncio.TimeoutError as exc:
        raise DockerTranscriptTimeout(f"Timed out reading transcript for {container_name}.") from exc
    except DockerTranscriptReadError as exc:
        return _empty_docker_payload(
            container_name=container_name,
            source=f"{adapter}-container",
            session_id=None,
            status="unavailable",
            warning=str(exc),
        )
    return _empty_docker_payload(
        container_name=container_name,
        source="docker-container",
        session_id=None,
        status="unsupported",
        warning=f"No transcript reader is available for adapter '{adapter}'.",
    )
