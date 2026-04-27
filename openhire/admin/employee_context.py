"""Employee context helpers for the admin dashboard."""

from __future__ import annotations

import asyncio
import hashlib
import json
import shlex
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from openhire.agent.autocompact import AutoCompact
from openhire.agent.context import ContextBuilder
from openhire.agent.memory import Consolidator, MemoryStore
from openhire.session.manager import Session, SessionManager
from openhire.workforce.registry import AgentEntry
from openhire.workforce.workspace import employee_workspace_path

_INTERNAL_SESSION_CHANNELS = {"cli", "system", "cron", "heartbeat"}
_OPENCLAW_MISSING_SENTINEL = "__OPENHIRE_OPENCLAW_SESSION_MISSING__"
_OPENCLAW_DREAM_STATE_FILE = ".openclaw_dream_state.json"
_OPENCLAW_DREAM_CHUNK_MESSAGES = 20
_OPENCLAW_DREAM_MAX_MESSAGE_CHARS = 12_000


def _status_percent(used_tokens: int, total_tokens: int) -> int:
    if total_tokens <= 0 or used_tokens <= 0:
        return 0
    return max(1, min(100, int((used_tokens / total_tokens) * 100)))


def _is_internal_session_key(key: str) -> bool:
    if ":" not in key:
        return False
    channel, _ = key.split(":", 1)
    return channel in _INTERNAL_SESSION_CHANNELS


def _session_keys(sessions: SessionManager) -> list[str]:
    try:
        infos = list(sessions.list_sessions())
    except Exception:
        return []
    keys: list[str] = []
    for info in infos:
        key = info.get("key") if isinstance(info, dict) else None
        if key:
            keys.append(str(key))
    return keys


def employee_default_session_key(entry: AgentEntry) -> str:
    container_name = str(entry.container_name or "").strip()
    return f"openhire-delegate-{container_name}" if container_name else ""


def _row_value(row: dict[str, Any] | None, *keys: str) -> str:
    if not isinstance(row, dict):
        return ""
    for key in keys:
        value = row.get(key)
        if value:
            return str(value)
    return ""


def _row_container_name(row: dict[str, Any] | None, entry: AgentEntry) -> str:
    return _row_value(row, "containerName", "container_name", "name") or str(entry.container_name or "")


def _row_adapter_name(row: dict[str, Any] | None, entry: AgentEntry) -> str:
    parts = [
        str(entry.agent_type or ""),
        _row_value(row, "agentType", "agent_type", "agentKey", "agent_key"),
        _row_value(row, "image"),
        _row_value(row, "containerName", "container_name", "name"),
    ]
    return " ".join(part.lower() for part in parts if part)


def _is_openclaw_context_row(row: dict[str, Any] | None, entry: AgentEntry) -> bool:
    return "openclaw" in _row_adapter_name(row, entry)


def _openclaw_session_path(session_key: str) -> str:
    return f"/home/node/.openclaw/agents/main/sessions/{session_key}.jsonl"


def _utc_now_iso() -> str:
    return datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")


def resolve_employee_session_key(
    workspace: Path,
    entry: AgentEntry,
    session_key: str | None = None,
) -> str | None:
    sessions = SessionManager(workspace)
    keys = _session_keys(sessions)
    explicit = str(session_key or "").strip()
    if explicit:
        return explicit if explicit in keys else None

    delegate_key = employee_default_session_key(entry)
    if delegate_key and delegate_key in keys:
        return delegate_key

    for key in keys:
        if not _is_internal_session_key(key):
            return key
    return keys[0] if keys else None


def _get_tool_definitions(agent_loop: Any):
    tools = getattr(agent_loop, "tools", None)
    getter = getattr(tools, "get_definitions", None)
    if callable(getter):
        return getter
    return lambda: []


def _max_completion_tokens(agent_loop: Any) -> int:
    provider = getattr(agent_loop, "provider", None)
    generation = getattr(provider, "generation", None)
    value = getattr(generation, "max_tokens", None)
    return int(value) if isinstance(value, int) and value > 0 else 4096


def _make_context_components(agent_loop: Any, workspace: Path) -> tuple[SessionManager, Consolidator, AutoCompact]:
    sessions = SessionManager(workspace)
    context = ContextBuilder(
        workspace,
        timezone=getattr(getattr(agent_loop, "context", None), "timezone", None),
    )
    consolidator = Consolidator(
        store=MemoryStore(workspace),
        provider=getattr(agent_loop, "provider", None),
        model=str(getattr(agent_loop, "model", "") or ""),
        sessions=sessions,
        context_window_tokens=int(getattr(agent_loop, "context_window_tokens", 0) or 0),
        build_messages=context.build_messages,
        get_tool_definitions=_get_tool_definitions(agent_loop),
        max_completion_tokens=_max_completion_tokens(agent_loop),
    )
    return sessions, consolidator, AutoCompact(sessions, consolidator)


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
            if block.get("type") in {"tool_call", "function_call"}:
                continue
            if block.get("type") in {"image", "image_url", "input_image"}:
                parts.append("[image]")
                continue
            if "text" in block:
                parts.append(str(block.get("text") or ""))
                continue
            parts.append(json.dumps(block, ensure_ascii=False))
        return "\n".join(part for part in parts if part)
    if isinstance(content, dict):
        if "text" in content:
            return str(content.get("text") or "")
        return json.dumps(content, ensure_ascii=False)
    return str(content)


def _openclaw_tool_calls(content: Any) -> list[dict[str, Any]]:
    if not isinstance(content, list):
        return []
    calls: list[dict[str, Any]] = []
    for index, block in enumerate(content):
        if not isinstance(block, dict) or block.get("type") not in {"tool_call", "function_call"}:
            continue
        arguments = block.get("arguments") or block.get("input") or {}
        if not isinstance(arguments, str):
            arguments = json.dumps(arguments, ensure_ascii=False)
        calls.append({
            "id": str(block.get("id") or block.get("tool_call_id") or f"call_{index}"),
            "type": "function",
            "function": {
                "name": str(block.get("name") or "tool"),
                "arguments": arguments,
            },
        })
    return calls


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


def _openclaw_row_to_session_message(row: dict[str, Any]) -> dict[str, Any] | None:
    payload = row.get("message")
    if not isinstance(payload, dict):
        return None
    role = str(payload.get("role") or "system")
    if role == "toolResult":
        role = "tool"
    if role not in {"user", "assistant", "tool", "system"}:
        role = "system"

    content = payload.get("content")
    message: dict[str, Any] = {
        "role": role,
        "content": _content_to_text(content),
        "timestamp": str(payload.get("timestamp") or row.get("timestamp") or ""),
        "_openclaw_row": row,
    }
    if payload.get("name") or payload.get("toolName") or payload.get("tool_name"):
        message["name"] = str(payload.get("name") or payload.get("toolName") or payload.get("tool_name"))
    if payload.get("tool_call_id") or payload.get("toolCallId"):
        message["tool_call_id"] = str(payload.get("tool_call_id") or payload.get("toolCallId"))
    tool_calls = payload.get("tool_calls")
    if isinstance(tool_calls, list) and tool_calls:
        message["tool_calls"] = tool_calls
    else:
        content_calls = _openclaw_tool_calls(content)
        if content_calls:
            message["tool_calls"] = content_calls
    return message


def _clean_session_message(message: dict[str, Any]) -> dict[str, Any]:
    return {key: value for key, value in message.items() if not key.startswith("_openclaw_")}


def _openclaw_row_from_message(message: dict[str, Any]) -> dict[str, Any]:
    raw_row = message.get("_openclaw_row")
    if isinstance(raw_row, dict):
        return raw_row
    payload = _clean_session_message(message)
    if payload.get("role") == "tool":
        payload["role"] = "toolResult"
        if payload.get("name") and not payload.get("toolName"):
            payload["toolName"] = payload["name"]
    return {
        "type": "message",
        "timestamp": str(message.get("timestamp") or _utc_now_iso()),
        "message": payload,
    }


def _openclaw_message_signature(message: dict[str, Any]) -> str:
    payload = {
        key: value
        for key, value in _clean_session_message(message).items()
        if key in {"role", "content", "timestamp", "name", "tool_call_id", "tool_calls"}
    }
    encoded = json.dumps(payload, ensure_ascii=False, sort_keys=True, default=str).encode("utf-8")
    return hashlib.sha256(encoded).hexdigest()


def _truncate_text(text: str, limit: int = _OPENCLAW_DREAM_MAX_MESSAGE_CHARS) -> str:
    if len(text) <= limit:
        return text
    return f"{text[:limit]}... [truncated {len(text) - limit} chars]"


def _openclaw_tool_call_names(message: dict[str, Any]) -> str:
    calls = message.get("tool_calls")
    if not isinstance(calls, list) or not calls:
        return ""
    names: list[str] = []
    for call in calls:
        if not isinstance(call, dict):
            continue
        function = call.get("function")
        if isinstance(function, dict) and function.get("name"):
            names.append(str(function["name"]))
        elif call.get("name"):
            names.append(str(call["name"]))
    return ", ".join(names)


def _format_openclaw_dream_chunk(session_key: str, messages: list[dict[str, Any]]) -> str:
    lines = [f"OpenClaw session {session_key}: imported {len(messages)} new message(s)."]
    for message in messages:
        role = str(message.get("role") or "system").upper()
        timestamp = str(message.get("timestamp") or "?")[:16]
        content = str(message.get("content") or "").strip()
        tool_names = _openclaw_tool_call_names(message)
        if tool_names:
            content = f"{content}\n[tool calls: {tool_names}]" if content else f"[tool calls: {tool_names}]"
        if not content:
            continue
        lines.append(f"[{timestamp}] {role}: {_truncate_text(content)}")
    return "\n".join(lines)


def _openclaw_dream_state_path(store: MemoryStore) -> Path:
    return store.memory_dir / _OPENCLAW_DREAM_STATE_FILE


def _read_openclaw_dream_state(store: MemoryStore, session_key: str) -> dict[str, Any]:
    path = _openclaw_dream_state_path(store)
    try:
        raw = json.loads(path.read_text(encoding="utf-8"))
    except (FileNotFoundError, json.JSONDecodeError, OSError):
        return {}
    if raw.get("sessionKey") == session_key:
        return raw
    sessions = raw.get("sessions")
    if isinstance(sessions, dict):
        value = sessions.get(session_key)
        return value if isinstance(value, dict) else {}
    return {}


def _write_openclaw_dream_state(store: MemoryStore, session_key: str, messages: list[dict[str, Any]]) -> None:
    state = {
        "sessionKey": session_key,
        "importedCount": len(messages),
        "lastSignature": _openclaw_message_signature(messages[-1]) if messages else "",
        "updatedAt": _utc_now_iso(),
    }
    _openclaw_dream_state_path(store).write_text(
        json.dumps(state, ensure_ascii=False, indent=2, sort_keys=True),
        encoding="utf-8",
    )


def _openclaw_dream_start_index(messages: list[dict[str, Any]], state: dict[str, Any]) -> int:
    if not messages:
        return 0
    last_signature = str(state.get("lastSignature") or "")
    if last_signature:
        for index, message in enumerate(messages):
            if _openclaw_message_signature(message) == last_signature:
                return index + 1
    imported_count = state.get("importedCount")
    if isinstance(imported_count, int) and 0 <= imported_count <= len(messages):
        return imported_count
    return 0


def _openclaw_dream_chunk_count(message_count: int) -> int:
    if message_count <= 0:
        return 0
    return (message_count + _OPENCLAW_DREAM_CHUNK_MESSAGES - 1) // _OPENCLAW_DREAM_CHUNK_MESSAGES


@dataclass
class _OpenClawSession:
    container_name: str
    session_key: str
    path: str
    rows: list[dict[str, Any]]
    messages: list[dict[str, Any]]

    @property
    def header_rows(self) -> list[dict[str, Any]]:
        rows = [row for row in self.rows if row.get("type") != "message"]
        if rows:
            return rows
        return [{"type": "session", "id": self.session_key, "timestamp": _utc_now_iso()}]


async def _docker_exec_text(container_name: str, *args: str, timeout: float = 2.5) -> str:
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
        raise RuntimeError(message or f"docker exec exited with code {proc.returncode}")
    return stdout.decode(errors="replace")


async def _docker_write_text(container_name: str, path: str, content: str, *, timeout: float = 2.5) -> None:
    directory = shlex.quote(str(Path(path).parent))
    quoted_path = shlex.quote(path)
    proc = await asyncio.create_subprocess_exec(
        "docker",
        "exec",
        "-i",
        container_name,
        "sh",
        "-lc",
        f"mkdir -p {directory} && cat > {quoted_path}",
        stdin=asyncio.subprocess.PIPE,
        stdout=asyncio.subprocess.PIPE,
        stderr=asyncio.subprocess.PIPE,
    )
    try:
        _stdout, stderr = await asyncio.wait_for(
            proc.communicate(content.encode("utf-8")),
            timeout=timeout,
        )
    except asyncio.TimeoutError:
        proc.kill()
        await proc.wait()
        raise
    if proc.returncode != 0:
        message = stderr.decode(errors="replace").strip()
        raise RuntimeError(message or f"docker exec exited with code {proc.returncode}")


async def _read_openclaw_session(
    entry: AgentEntry,
    row: dict[str, Any] | None,
    *,
    session_key: str | None = None,
) -> _OpenClawSession | None:
    container_name = _row_container_name(row, entry)
    if not container_name:
        return None
    resolved_key = str(session_key or employee_default_session_key(entry) or f"openhire-delegate-{container_name}").strip()
    if not resolved_key:
        return None
    path = _openclaw_session_path(resolved_key)
    quoted_path = shlex.quote(path)
    quoted_missing = shlex.quote(_OPENCLAW_MISSING_SENTINEL)
    raw = await _docker_exec_text(
        container_name,
        "sh",
        "-lc",
        f"if [ -f {quoted_path} ]; then cat {quoted_path}; else printf %s {quoted_missing}; fi",
    )
    if raw.strip() == _OPENCLAW_MISSING_SENTINEL:
        return None
    rows = _parse_jsonl(raw)
    messages = [
        message
        for row_item in rows
        if row_item.get("type") == "message"
        for message in [_openclaw_row_to_session_message(row_item)]
        if message is not None
    ]
    return _OpenClawSession(
        container_name=container_name,
        session_key=resolved_key,
        path=path,
        rows=rows,
        messages=messages,
    )


def _serialize_openclaw_session(session: _OpenClawSession, messages: list[dict[str, Any]]) -> str:
    rows = session.header_rows + [_openclaw_row_from_message(message) for message in messages]
    return "\n".join(json.dumps(row, ensure_ascii=False) for row in rows) + "\n"


def _estimate_openclaw_context(
    agent_loop: Any,
    root_workspace: Path,
    entry: AgentEntry,
    session: _OpenClawSession,
    *,
    busy: bool = False,
) -> dict[str, Any]:
    total_tokens = int(getattr(agent_loop, "context_window_tokens", 0) or 0)
    if not session.messages:
        return {
            "available": True,
            "busy": bool(busy),
            "sessionKey": session.session_key,
            "usedTokens": 0,
            "totalTokens": total_tokens,
            "percent": 0,
            "source": "openclaw_container",
            "reason": "",
            "messageCount": 0,
        }

    workspace = employee_workspace_path(root_workspace, entry)
    _sessions, consolidator, _auto_compact = _make_context_components(agent_loop, workspace)
    synthetic = Session(key=session.session_key, messages=[_clean_session_message(message) for message in session.messages])
    try:
        used_tokens, _source = consolidator.estimate_session_prompt_tokens(synthetic)
    except Exception as exc:
        return {
            "available": True,
            "busy": bool(busy),
            "sessionKey": session.session_key,
            "usedTokens": 0,
            "totalTokens": total_tokens,
            "percent": 0,
            "source": "openclaw_container_error",
            "reason": str(exc),
            "messageCount": len(session.messages),
        }
    return {
        "available": True,
        "busy": bool(busy),
        "sessionKey": session.session_key,
        "usedTokens": max(0, int(used_tokens or 0)),
        "totalTokens": total_tokens,
        "percent": _status_percent(int(used_tokens or 0), total_tokens),
        "source": "openclaw_container",
        "reason": "",
        "messageCount": len(session.messages),
    }


async def openclaw_dream_pending_summary(
    root_workspace: Path,
    entry: AgentEntry,
    *,
    row: dict[str, Any] | None = None,
    store: MemoryStore | None = None,
    session_key: str | None = None,
) -> dict[str, Any]:
    if not _is_openclaw_context_row(row, entry):
        return {"pendingEntries": 0, "pendingMessages": 0, "sessionKey": None}
    resolved_store = store or MemoryStore(employee_workspace_path(root_workspace, entry))
    try:
        session = await _read_openclaw_session(entry, row, session_key=session_key)
    except Exception:
        return {"pendingEntries": 0, "pendingMessages": 0, "sessionKey": None}
    if session is None:
        return {"pendingEntries": 0, "pendingMessages": 0, "sessionKey": None}
    state = _read_openclaw_dream_state(resolved_store, session.session_key)
    start = _openclaw_dream_start_index(session.messages, state)
    pending_messages = max(0, len(session.messages) - start)
    return {
        "pendingEntries": _openclaw_dream_chunk_count(pending_messages),
        "pendingMessages": pending_messages,
        "sessionKey": session.session_key,
    }


async def ingest_openclaw_dream_history(
    root_workspace: Path,
    entry: AgentEntry,
    *,
    row: dict[str, Any] | None = None,
    store: MemoryStore | None = None,
    session_key: str | None = None,
) -> dict[str, Any]:
    if not _is_openclaw_context_row(row, entry):
        return {"ingestedEntries": 0, "ingestedMessages": 0, "sessionKey": None}
    resolved_store = store or MemoryStore(employee_workspace_path(root_workspace, entry))
    session = await _read_openclaw_session(entry, row, session_key=session_key)
    if session is None:
        return {"ingestedEntries": 0, "ingestedMessages": 0, "sessionKey": None}

    state = _read_openclaw_dream_state(resolved_store, session.session_key)
    start = _openclaw_dream_start_index(session.messages, state)
    pending = session.messages[start:]
    if not pending:
        return {
            "ingestedEntries": 0,
            "ingestedMessages": 0,
            "sessionKey": session.session_key,
        }

    ingested_entries = 0
    for offset in range(0, len(pending), _OPENCLAW_DREAM_CHUNK_MESSAGES):
        chunk = pending[offset: offset + _OPENCLAW_DREAM_CHUNK_MESSAGES]
        resolved_store.append_history(_format_openclaw_dream_chunk(session.session_key, chunk))
        ingested_entries += 1
    _write_openclaw_dream_state(resolved_store, session.session_key, session.messages)
    return {
        "ingestedEntries": ingested_entries,
        "ingestedMessages": len(pending),
        "sessionKey": session.session_key,
    }


def unavailable_employee_context(
    agent_loop: Any,
    *,
    reason: str = "No employee session found.",
    busy: bool = False,
) -> dict[str, Any]:
    total_tokens = int(getattr(agent_loop, "context_window_tokens", 0) or 0)
    return {
        "available": False,
        "busy": bool(busy),
        "sessionKey": None,
        "usedTokens": 0,
        "totalTokens": total_tokens,
        "percent": 0,
        "source": "no_session",
        "reason": reason,
    }


def employee_context_snapshot(
    agent_loop: Any,
    root_workspace: Path,
    entry: AgentEntry,
    *,
    busy: bool = False,
    session_key: str | None = None,
) -> dict[str, Any]:
    workspace = employee_workspace_path(root_workspace, entry)
    resolved_key = resolve_employee_session_key(workspace, entry, session_key=session_key)
    if not resolved_key:
        return unavailable_employee_context(agent_loop, busy=busy)

    sessions, consolidator, _auto_compact = _make_context_components(agent_loop, workspace)
    session = sessions.get_or_create(resolved_key)
    total_tokens = int(getattr(agent_loop, "context_window_tokens", 0) or 0)
    if not session.messages and session.metadata.get("_admin_context_source") == "cleared":
        return {
            "available": True,
            "busy": bool(busy),
            "sessionKey": resolved_key,
            "usedTokens": 0,
            "totalTokens": total_tokens,
            "percent": 0,
            "source": "cleared",
            "reason": "",
        }

    try:
        used_tokens, source = consolidator.estimate_session_prompt_tokens(session)
    except Exception as exc:
        return {
            "available": True,
            "busy": bool(busy),
            "sessionKey": resolved_key,
            "usedTokens": 0,
            "totalTokens": total_tokens,
            "percent": 0,
            "source": "estimate_error",
            "reason": str(exc),
        }

    return {
        "available": True,
        "busy": bool(busy),
        "sessionKey": resolved_key,
        "usedTokens": max(0, int(used_tokens or 0)),
        "totalTokens": total_tokens,
        "percent": _status_percent(int(used_tokens or 0), total_tokens),
        "source": str(source or "unknown"),
        "reason": "",
    }


async def employee_context_snapshot_for_row(
    agent_loop: Any,
    root_workspace: Path,
    entry: AgentEntry,
    *,
    row: dict[str, Any] | None = None,
    busy: bool = False,
    session_key: str | None = None,
) -> dict[str, Any]:
    workspace_context = employee_context_snapshot(
        agent_loop,
        root_workspace,
        entry,
        busy=busy,
        session_key=session_key,
    )
    if workspace_context.get("available") or not _is_openclaw_context_row(row, entry):
        return workspace_context

    try:
        openclaw_session = await _read_openclaw_session(entry, row, session_key=session_key)
    except asyncio.TimeoutError:
        return unavailable_employee_context(
            agent_loop,
            reason="Timed out reading OpenClaw session from container.",
            busy=busy,
        )
    except Exception as exc:
        return unavailable_employee_context(
            agent_loop,
            reason=f"Failed to read OpenClaw session from container: {exc}",
            busy=busy,
        )
    if openclaw_session is None:
        return unavailable_employee_context(
            agent_loop,
            reason="No OpenClaw session transcript found in container.",
            busy=busy,
        )
    return _estimate_openclaw_context(agent_loop, root_workspace, entry, openclaw_session, busy=busy)


def clear_employee_context(
    agent_loop: Any,
    root_workspace: Path,
    entry: AgentEntry,
    *,
    session_key: str | None = None,
    busy: bool = False,
) -> dict[str, Any]:
    if busy:
        raise RuntimeError(f"Employee '{entry.agent_id}' is currently busy.")

    workspace = employee_workspace_path(root_workspace, entry)
    resolved_key = resolve_employee_session_key(workspace, entry, session_key=session_key)
    if not resolved_key:
        raise ValueError("No employee session context found.")

    sessions = SessionManager(workspace)
    session = sessions.get_or_create(resolved_key)
    cleared_messages = len(session.messages)
    session.clear()
    session.metadata.clear()
    session.metadata["_admin_context_source"] = "cleared"
    sessions.save(session)
    sessions.invalidate(resolved_key)

    total_tokens = int(getattr(agent_loop, "context_window_tokens", 0) or 0)
    return {
        "employeeId": entry.agent_id,
        "sessionKey": resolved_key,
        "clearedMessages": cleared_messages,
        "context": {
            "available": True,
            "busy": False,
            "sessionKey": resolved_key,
            "usedTokens": 0,
            "totalTokens": total_tokens,
            "percent": 0,
            "source": "cleared",
            "reason": "",
        },
    }


async def clear_employee_context_for_row(
    agent_loop: Any,
    root_workspace: Path,
    entry: AgentEntry,
    *,
    row: dict[str, Any] | None = None,
    session_key: str | None = None,
    busy: bool = False,
) -> dict[str, Any]:
    if busy:
        raise RuntimeError(f"Employee '{entry.agent_id}' is currently busy.")
    workspace_context = employee_context_snapshot(
        agent_loop,
        root_workspace,
        entry,
        busy=False,
        session_key=session_key,
    )
    if workspace_context.get("available"):
        return clear_employee_context(
            agent_loop,
            root_workspace,
            entry,
            session_key=str(workspace_context.get("sessionKey") or session_key or ""),
            busy=False,
        )
    if not _is_openclaw_context_row(row, entry):
        raise ValueError("No employee session context found.")
    openclaw_session = await _read_openclaw_session(entry, row, session_key=session_key)
    if openclaw_session is None:
        raise ValueError("No employee session context found.")
    cleared_messages = len(openclaw_session.messages)
    await _docker_write_text(
        openclaw_session.container_name,
        openclaw_session.path,
        _serialize_openclaw_session(openclaw_session, []),
    )
    total_tokens = int(getattr(agent_loop, "context_window_tokens", 0) or 0)
    return {
        "employeeId": entry.agent_id,
        "sessionKey": openclaw_session.session_key,
        "clearedMessages": cleared_messages,
        "context": {
            "available": True,
            "busy": False,
            "sessionKey": openclaw_session.session_key,
            "usedTokens": 0,
            "totalTokens": total_tokens,
            "percent": 0,
            "source": "cleared",
            "reason": "",
            "messageCount": 0,
        },
    }


async def compact_employee_context(
    agent_loop: Any,
    root_workspace: Path,
    entry: AgentEntry,
    *,
    session_key: str | None = None,
    busy: bool = False,
) -> dict[str, Any]:
    if busy:
        raise RuntimeError(f"Employee '{entry.agent_id}' is currently busy.")

    workspace = employee_workspace_path(root_workspace, entry)
    resolved_key = resolve_employee_session_key(workspace, entry, session_key=session_key)
    if not resolved_key:
        raise ValueError("No employee session context found.")

    sessions, consolidator, auto_compact = _make_context_components(agent_loop, workspace)
    sessions.invalidate(resolved_key)
    session = sessions.get_or_create(resolved_key)
    archive_msgs, kept_msgs = auto_compact._split_unconsolidated(session)
    if not archive_msgs:
        context = employee_context_snapshot(
            agent_loop,
            root_workspace,
            entry,
            session_key=resolved_key,
        )
        return {
            "employeeId": entry.agent_id,
            "sessionKey": resolved_key,
            "archivedMessages": 0,
            "keptMessages": len(session.messages),
            "summaryCreated": False,
            "context": context,
        }

    last_active = session.updated_at
    summary = await consolidator.archive(archive_msgs) or ""
    if summary and summary != "(nothing)":
        session.metadata["_last_summary"] = {
            "text": summary,
            "last_active": last_active.isoformat(),
        }
    session.metadata.pop("_admin_context_source", None)
    session.messages = kept_msgs
    session.last_consolidated = 0
    sessions.save(session)
    sessions.invalidate(resolved_key)

    return {
        "employeeId": entry.agent_id,
        "sessionKey": resolved_key,
        "archivedMessages": len(archive_msgs),
        "keptMessages": len(kept_msgs),
        "summaryCreated": bool(summary),
        "context": employee_context_snapshot(
            agent_loop,
            root_workspace,
            entry,
            session_key=resolved_key,
        ),
    }


async def compact_employee_context_for_row(
    agent_loop: Any,
    root_workspace: Path,
    entry: AgentEntry,
    *,
    row: dict[str, Any] | None = None,
    session_key: str | None = None,
    busy: bool = False,
) -> dict[str, Any]:
    if busy:
        raise RuntimeError(f"Employee '{entry.agent_id}' is currently busy.")
    workspace_context = employee_context_snapshot(
        agent_loop,
        root_workspace,
        entry,
        busy=False,
        session_key=session_key,
    )
    if workspace_context.get("available"):
        return await compact_employee_context(
            agent_loop,
            root_workspace,
            entry,
            session_key=str(workspace_context.get("sessionKey") or session_key or ""),
            busy=False,
        )
    if not _is_openclaw_context_row(row, entry):
        raise ValueError("No employee session context found.")
    openclaw_session = await _read_openclaw_session(entry, row, session_key=session_key)
    if openclaw_session is None:
        raise ValueError("No employee session context found.")

    workspace = employee_workspace_path(root_workspace, entry)
    _sessions, consolidator, auto_compact = _make_context_components(agent_loop, workspace)
    synthetic = Session(
        key=openclaw_session.session_key,
        messages=openclaw_session.messages,
    )
    archive_msgs, kept_msgs = auto_compact._split_unconsolidated(synthetic)
    if not archive_msgs:
        return {
            "employeeId": entry.agent_id,
            "sessionKey": openclaw_session.session_key,
            "archivedMessages": 0,
            "keptMessages": len(openclaw_session.messages),
            "summaryCreated": False,
            "context": _estimate_openclaw_context(
                agent_loop,
                root_workspace,
                entry,
                openclaw_session,
                busy=False,
            ),
        }

    cleaned_archive = [_clean_session_message(message) for message in archive_msgs]
    summary = await consolidator.archive(cleaned_archive) or ""
    await _docker_write_text(
        openclaw_session.container_name,
        openclaw_session.path,
        _serialize_openclaw_session(openclaw_session, kept_msgs),
    )
    refreshed = _OpenClawSession(
        container_name=openclaw_session.container_name,
        session_key=openclaw_session.session_key,
        path=openclaw_session.path,
        rows=openclaw_session.header_rows + [_openclaw_row_from_message(message) for message in kept_msgs],
        messages=kept_msgs,
    )
    return {
        "employeeId": entry.agent_id,
        "sessionKey": openclaw_session.session_key,
        "archivedMessages": len(archive_msgs),
        "keptMessages": len(kept_msgs),
        "summaryCreated": bool(summary),
        "context": _estimate_openclaw_context(
            agent_loop,
            root_workspace,
            entry,
            refreshed,
            busy=False,
        ),
    }
