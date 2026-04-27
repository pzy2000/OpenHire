"""Runtime snapshot builders for the admin dashboard."""

from __future__ import annotations

import asyncio
import os
import platform
import re
import shlex
import shutil
import time
from collections import deque
from datetime import datetime, timezone
from typing import Any

from loguru import logger

from openhire.adapters import build_default_registry
from openhire.adapters.base import inspect_container_status
from openhire.utils.helpers import estimate_message_tokens

RUNTIME_HISTORY_WINDOW_SECONDS = 15 * 60
RUNTIME_HISTORY_MAX_SAMPLES = 180
RUNTIME_HISTORY_SAMPLE_INTERVAL_SECONDS = 5
_DOCKER_CPU_RE = re.compile(r"^\s*([0-9]+(?:\.[0-9]+)?)\s*%?\s*$")
_DOCKER_MEMORY_RE = re.compile(r"^\s*([0-9]+(?:\.[0-9]+)?)\s*([kmgt]?i?b)?", re.IGNORECASE)
_DOCKER_RUNNING_STATUSES = {"running", "processing"}
_DOCKER_ISSUE_STATUSES = {"error", "exited", "unknown"}


def _utc_now_iso() -> str:
    return datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")


def _status_percent(used_tokens: int, total_tokens: int) -> int:
    if total_tokens <= 0 or used_tokens <= 0:
        return 0
    return max(1, min(100, int((used_tokens / total_tokens) * 100)))


def _active_task_count(loop: Any) -> int:
    count = 0
    for tasks in getattr(loop, "_active_tasks", {}).values():
        count += sum(1 for task in tasks if not task.done())
    return count


def _dump_cfg(cfg_obj: Any) -> dict[str, Any]:
    if hasattr(cfg_obj, "model_dump"):
        return cfg_obj.model_dump()
    if isinstance(cfg_obj, dict):
        return dict(cfg_obj)
    return dict(vars(cfg_obj))


def _parse_docker_cpu_percent(value: Any) -> float | None:
    if value is None:
        return None
    if isinstance(value, (int, float)):
        return round(max(0.0, float(value)), 2)
    match = _DOCKER_CPU_RE.match(str(value))
    if not match:
        return None
    return round(max(0.0, float(match.group(1))), 2)


def _parse_docker_memory_mib(value: Any) -> float | None:
    if value is None:
        return None
    text = str(value).split("/", 1)[0].strip()
    match = _DOCKER_MEMORY_RE.match(text)
    if not match:
        return None
    amount = max(0.0, float(match.group(1)))
    unit = (match.group(2) or "b").lower()
    multipliers = {
        "b": 1 / (1024 * 1024),
        "kb": 1 / 1024,
        "kib": 1 / 1024,
        "mb": 1,
        "mib": 1,
        "gb": 1024,
        "gib": 1024,
        "tb": 1024 * 1024,
        "tib": 1024 * 1024,
    }
    multiplier = multipliers.get(unit)
    if multiplier is None:
        return None
    return round(amount * multiplier, 2)


def _runtime_history_limit(limit: int | None) -> int:
    try:
        value = int(limit or RUNTIME_HISTORY_MAX_SAMPLES)
    except (TypeError, ValueError):
        value = RUNTIME_HISTORY_MAX_SAMPLES
    return max(1, min(1000, value))


def _runtime_history_sample_from_snapshot(
    snapshot: dict[str, Any],
    *,
    epoch_ms: int | None = None,
) -> dict[str, Any]:
    generated_at = str(snapshot.get("generatedAt") or _utc_now_iso())
    main = snapshot.get("mainAgent") if isinstance(snapshot.get("mainAgent"), dict) else {}
    process = snapshot.get("process") if isinstance(snapshot.get("process"), dict) else {}
    context = main.get("context") if isinstance(main.get("context"), dict) else {}
    daemon = snapshot.get("dockerDaemon") if isinstance(snapshot.get("dockerDaemon"), dict) else default_docker_daemon_snapshot()
    containers = snapshot.get("dockerContainers")
    if not isinstance(containers, list):
        containers = snapshot.get("dockerAgents")
    containers = [item for item in containers or [] if isinstance(item, dict)]

    cpu_values: list[float] = []
    memory_values: list[float] = []
    running = 0
    issues = 0
    for container in containers:
        status = str(container.get("status") or "").strip().lower()
        if status in _DOCKER_RUNNING_STATUSES:
            running += 1
        if status in _DOCKER_ISSUE_STATUSES:
            issues += 1
        cpu = _parse_docker_cpu_percent(container.get("cpuPercent"))
        if cpu is not None:
            cpu_values.append(cpu)
        memory = _parse_docker_memory_mib(container.get("memoryUsage"))
        if memory is not None:
            memory_values.append(memory)

    return {
        "generatedAt": generated_at,
        "epochMs": int(epoch_ms if epoch_ms is not None else time.time() * 1000),
        "mainStatus": str(main.get("status") or "unknown"),
        "mainStage": str(main.get("stage") or "idle"),
        "sessionKey": main.get("sessionKey") or main.get("lastSessionKey"),
        "activeTaskCount": int(main.get("activeTaskCount", 0) or 0),
        "contextPercent": _status_percent(
            int(context.get("usedTokens", 0) or 0),
            int(context.get("totalTokens", 0) or 0),
        ) if "percent" not in context else max(0, min(100, int(context.get("percent", 0) or 0))),
        "contextUsedTokens": int(context.get("usedTokens", 0) or 0),
        "contextTotalTokens": int(context.get("totalTokens", 0) or 0),
        "processUptimeSeconds": int(process.get("uptimeSeconds", main.get("uptimeSeconds", 0)) or 0),
        "dockerDaemonStatus": str(daemon.get("status") or "unknown"),
        "dockerDaemonOk": daemon.get("ok"),
        "dockerTotal": len(containers),
        "dockerRunning": running,
        "dockerIssues": issues,
        "dockerCpuAvgPercent": round(sum(cpu_values) / len(cpu_values), 2) if cpu_values else None,
        "dockerCpuMaxPercent": round(max(cpu_values), 2) if cpu_values else None,
        "dockerMemoryTotalMiB": round(sum(memory_values), 2) if memory_values else None,
    }


def _runtime_history_signature(sample: dict[str, Any]) -> tuple[Any, ...]:
    return (
        sample.get("mainStatus"),
        sample.get("mainStage"),
        sample.get("sessionKey"),
        sample.get("activeTaskCount"),
        sample.get("dockerDaemonStatus"),
        sample.get("dockerDaemonOk"),
        sample.get("dockerTotal"),
        sample.get("dockerRunning"),
        sample.get("dockerIssues"),
    )


def _runtime_history_payload(
    samples: list[dict[str, Any]],
    *,
    limit: int | None = None,
    window_seconds: int = RUNTIME_HISTORY_WINDOW_SECONDS,
    sample_interval_seconds: float = RUNTIME_HISTORY_SAMPLE_INTERVAL_SECONDS,
) -> dict[str, Any]:
    normalized_limit = _runtime_history_limit(limit)
    return {
        "generatedAt": _utc_now_iso(),
        "windowSeconds": window_seconds,
        "sampleIntervalSeconds": sample_interval_seconds,
        "samples": samples[-normalized_limit:],
    }


class DockerAgentRuntimeTracker:
    """Track current docker-agent execution metadata for the admin dashboard."""

    def __init__(self, on_change=None) -> None:
        self._entries: dict[str, dict[str, Any]] = {}
        self._on_change = on_change

    def register_start(
        self,
        *,
        agent_key: str,
        command: list[str],
        prompt_text: str,
        context_window_tokens: int,
    ) -> None:
        prompt_tokens = estimate_message_tokens({"role": "user", "content": prompt_text}) if prompt_text else 0
        self._entries[agent_key] = {
            **self._entries.get(agent_key, {}),
            "currentCommand": shlex.join(command),
            "startedAt": _utc_now_iso(),
            "lastPromptTokensEstimate": prompt_tokens,
            "lastPromptContextPercentEstimate": _status_percent(prompt_tokens, context_window_tokens),
            "lastTaskSummary": prompt_text[:240],
        }
        if self._on_change:
            self._on_change()

    def register_finish(self, agent_key: str) -> None:
        entry = self._entries.setdefault(agent_key, {})
        entry["currentCommand"] = None
        entry["startedAt"] = None
        if self._on_change:
            self._on_change()

    def snapshot(self, agent_key: str) -> dict[str, Any]:
        entry = self._entries.get(agent_key, {})
        return {
            "currentCommand": entry.get("currentCommand"),
            "startedAt": entry.get("startedAt"),
            "lastPromptTokensEstimate": int(entry.get("lastPromptTokensEstimate") or 0),
            "lastPromptContextPercentEstimate": int(entry.get("lastPromptContextPercentEstimate") or 0),
            "lastTaskSummary": entry.get("lastTaskSummary"),
        }

    def all_snapshots(self) -> dict[str, dict[str, Any]]:
        return {key: self.snapshot(key) for key in self._entries}


def _format_duration(started_at: str | None) -> float | None:
    if not started_at:
        return None
    try:
        started = datetime.fromisoformat(started_at.replace("Z", "+00:00"))
    except ValueError:
        return None
    return max(0.0, (datetime.now(timezone.utc) - started).total_seconds())


def _tool_call_snapshot(tool_calls: list[Any]) -> list[dict[str, Any]]:
    out: list[dict[str, Any]] = []
    for call in tool_calls:
        name = getattr(call, "name", None) or (call.get("name") if isinstance(call, dict) else "")
        arguments = getattr(call, "arguments", None) or (call.get("arguments") if isinstance(call, dict) else {})
        out.append({
            "name": name,
            "arguments": arguments if isinstance(arguments, dict) else {},
        })
    return out


def _split_session_key(key: str | None) -> tuple[str | None, str | None]:
    if not key or ":" not in key:
        return None, None
    channel, chat_id = key.split(":", 1)
    return channel, chat_id


def _latest_session_key(loop: Any) -> str | None:
    explicit = getattr(loop, "_last_admin_session_key", None)
    if explicit:
        return explicit

    sessions = getattr(loop, "sessions", None)
    if sessions is None or not hasattr(sessions, "list_sessions"):
        return None

    try:
        session_infos = list(sessions.list_sessions())
    except Exception:
        return None

    if not session_infos:
        return None

    def _is_internal(key: str) -> bool:
        channel, _ = _split_session_key(key)
        return channel in {"cli", "system", "cron", "heartbeat"}

    for info in session_infos:
        key = info.get("key") if isinstance(info, dict) else None
        if key and not _is_internal(str(key)):
            return str(key)

    key = session_infos[0].get("key") if isinstance(session_infos[0], dict) else None
    return str(key) if key else None


def _estimate_session_context(loop: Any, session_key: str, total_tokens: int) -> dict[str, Any]:
    used_tokens = 0
    source = "unknown"
    sessions = getattr(loop, "sessions", None)
    session = None
    try:
        if sessions is not None and hasattr(sessions, "get_or_create"):
            session = sessions.get_or_create(session_key)
    except Exception:
        session = None

    if session is not None:
        consolidator = getattr(loop, "consolidator", None)
        if consolidator is not None and hasattr(consolidator, "estimate_session_prompt_tokens"):
            try:
                used_tokens, source = consolidator.estimate_session_prompt_tokens(session)
            except Exception:
                used_tokens, source = 0, "unknown"

        if used_tokens <= 0:
            try:
                history = session.get_history(max_messages=0)
                used_tokens = sum(estimate_message_tokens(message) for message in history)
                source = "session_history"
            except Exception:
                used_tokens, source = 0, "unknown"

    if used_tokens <= 0:
        used_tokens = int(getattr(loop, "_last_admin_context_tokens", 0) or 0)
        source = getattr(loop, "_last_admin_context_source", source) or source

    used_tokens = max(0, int(used_tokens or 0))
    return {
        "usedTokens": used_tokens,
        "totalTokens": total_tokens,
        "percent": _status_percent(used_tokens, total_tokens),
        "source": source,
    }


def _should_hydrate_idle_context(context: dict[str, Any]) -> bool:
    used_tokens = int(context.get("usedTokens", 0) or 0)
    if used_tokens > 0:
        return False
    source = str(context.get("source") or "").strip().lower()
    return source in {"", "unknown", "unavailable", "empty"}


def _hydrate_main_from_sessions(snapshot: dict[str, Any], loop: Any) -> None:
    main = snapshot.get("mainAgent")
    if not isinstance(main, dict):
        return
    if main.get("status") == "processing":
        return

    session_key = main.get("sessionKey") or main.get("lastSessionKey") or _latest_session_key(loop)
    if not session_key:
        return

    channel, chat_id = _split_session_key(str(session_key))
    total_tokens = int(
        (main.get("context") or {}).get("totalTokens")
        or getattr(loop, "context_window_tokens", 0)
        or 0
    )
    context = main.get("context") or {}
    if _should_hydrate_idle_context(context):
        context = _estimate_session_context(loop, str(session_key), total_tokens)
        main["context"] = context

    last_usage = dict(getattr(loop, "_last_usage", {}) or {})
    if last_usage and not any((main.get("lastUsage") or {}).values()):
        main["lastUsage"] = {
            "promptTokens": int(last_usage.get("prompt_tokens", 0) or 0),
            "completionTokens": int(last_usage.get("completion_tokens", 0) or 0),
            "cachedTokens": int(last_usage.get("cached_tokens", 0) or 0),
        }

    main["lastSessionKey"] = str(session_key)
    main.setdefault("sessionKey", None)
    if channel and not main.get("channel"):
        main["channel"] = channel
    if chat_id and not main.get("chatId"):
        main["chatId"] = chat_id
    try:
        setattr(loop, "_last_admin_session_key", str(session_key))
        setattr(loop, "_last_admin_context_tokens", int(context.get("usedTokens", 0) or 0))
        setattr(loop, "_last_admin_context_source", context.get("source", "unknown"))
    except Exception:
        pass


def parse_docker_ps_rows(raw: str) -> list[dict[str, Any]]:
    """Parse `docker ps` tab-separated rows for agent-like containers."""
    rows: list[dict[str, Any]] = []
    raw = raw.replace("\\n", "\n")
    for line in raw.splitlines():
        line = line.replace("\\t", "\t")
        parts = line.split("\t")
        if len(parts) < 5:
            continue
        name, image, state, status_text, ports = parts[:5]
        # OpenHands-specific containers are no longer first-class runtime targets.
        # if name.startswith("openhands-"):
        #     continue
        if not (name.startswith("nanobot-") or name.startswith("openhire-")):
            continue
        rows.append({
            "name": name,
            "image": image,
            "status": state or "unknown",
            "uptime": status_text,
            "ports": ports,
            "cpuPercent": None,
            "memoryUsage": None,
            "currentCommand": "server/idle" if state == "running" else "unknown",
            "processes": [],
            "source": "docker",
        })
    return rows


async def _docker_output(*args: str, timeout: float = 2.0) -> str:
    try:
        proc = await asyncio.create_subprocess_exec(
            "docker",
            *args,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.DEVNULL,
        )
    except OSError:
        return ""
    try:
        stdout, _ = await asyncio.wait_for(proc.communicate(), timeout=timeout)
    except asyncio.TimeoutError:
        proc.kill()
        await proc.wait()
        return ""
    if proc.returncode != 0:
        return ""
    return stdout.decode(errors="replace")


def _docker_daemon_snapshot(
    status: str,
    *,
    message: str = "",
    version: str = "",
    ok: bool | None = None,
) -> dict[str, Any]:
    return {
        "status": status,
        "ok": status == "running" if ok is None and status != "unknown" else ok,
        "message": message,
        "version": version,
    }


def default_docker_daemon_snapshot() -> dict[str, Any]:
    return _docker_daemon_snapshot(
        "unknown",
        message="Docker daemon has not been checked yet.",
        ok=None,
    )


async def probe_docker_daemon(timeout: float = 2.0) -> dict[str, Any]:
    """Return whether the Docker CLI can reach the daemon."""
    try:
        proc = await asyncio.create_subprocess_exec(
            "docker",
            "info",
            "--format",
            "{{.ServerVersion}}",
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE,
        )
    except FileNotFoundError:
        return _docker_daemon_snapshot("unavailable", message="docker CLI was not found.")
    except OSError as exc:
        return _docker_daemon_snapshot("unavailable", message=str(exc))
    try:
        stdout, stderr = await asyncio.wait_for(proc.communicate(), timeout=timeout)
    except asyncio.TimeoutError:
        proc.kill()
        await proc.wait()
        return _docker_daemon_snapshot("unknown", message="docker info timed out.", ok=False)
    if proc.returncode != 0:
        message = stderr.decode(errors="replace").strip() or stdout.decode(errors="replace").strip()
        return _docker_daemon_snapshot(
            "unavailable",
            message=(message or "Docker daemon is not reachable.")[:500],
        )
    version = stdout.decode(errors="replace").strip()
    return _docker_daemon_snapshot("running", message="Docker daemon is reachable.", version=version)


def docker_daemon_start_command() -> tuple[str, ...] | None:
    """Return the safest local command to ask an existing Docker daemon to start."""
    system = platform.system().lower()
    if system == "darwin" and shutil.which("open"):
        return ("open", "-a", "Docker")
    if shutil.which("colima"):
        return ("colima", "start")
    if system == "linux" and hasattr(os, "geteuid") and os.geteuid() == 0:
        if shutil.which("systemctl"):
            return ("systemctl", "start", "docker")
        if shutil.which("service"):
            return ("service", "docker", "start")
    return None


async def repair_docker_daemon(
    *,
    wait_timeout: float = 18.0,
    poll_interval: float = 1.0,
) -> dict[str, Any]:
    """Best-effort one-click repair for a stopped local Docker daemon."""
    before = await probe_docker_daemon()
    if before.get("ok") is True:
        return {
            "attempted": False,
            "command": [],
            "message": "Docker daemon is already reachable.",
            "dockerDaemon": before,
        }

    command = docker_daemon_start_command()
    if command is None:
        return {
            "attempted": False,
            "command": [],
            "message": "No supported automatic Docker daemon starter is available on this host.",
            "dockerDaemon": before,
        }

    try:
        proc = await asyncio.create_subprocess_exec(
            *command,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE,
        )
        stdout, stderr = await asyncio.wait_for(proc.communicate(), timeout=10.0)
    except asyncio.TimeoutError:
        proc.kill()
        await proc.wait()
        daemon = await probe_docker_daemon()
        return {
            "attempted": True,
            "command": list(command),
            "message": f"Timed out while running {shlex.join(command)}.",
            "dockerDaemon": daemon,
        }
    except OSError as exc:
        daemon = await probe_docker_daemon()
        return {
            "attempted": True,
            "command": list(command),
            "message": str(exc),
            "dockerDaemon": daemon,
        }

    if proc.returncode != 0:
        output = stderr.decode(errors="replace").strip() or stdout.decode(errors="replace").strip()
        daemon = await probe_docker_daemon()
        return {
            "attempted": True,
            "command": list(command),
            "message": (output or f"Failed to run {shlex.join(command)}.")[:500],
            "dockerDaemon": daemon,
        }

    deadline = time.monotonic() + max(0.0, wait_timeout)
    daemon = await probe_docker_daemon()
    while daemon.get("ok") is not True and time.monotonic() < deadline:
        await asyncio.sleep(max(0.0, poll_interval))
        daemon = await probe_docker_daemon()

    message = (
        "Docker daemon is reachable."
        if daemon.get("ok") is True
        else "Docker start was requested, but the daemon is still not reachable."
    )
    return {
        "attempted": True,
        "command": list(command),
        "message": message,
        "dockerDaemon": daemon,
    }


async def sample_docker_containers(
    tracker: DockerAgentRuntimeTracker | None = None,
) -> list[dict[str, Any]]:
    """Best-effort Docker sampler used by the admin runtime monitor."""
    raw = await _docker_output(
        "ps",
        "-a",
        "--format",
        "{{.Names}}\t{{.Image}}\t{{.State}}\t{{.Status}}\t{{.Ports}}",
    )
    rows = parse_docker_ps_rows(raw)
    if not rows:
        return []

    stats_raw = await _docker_output(
        "stats",
        "--no-stream",
        "--format",
        "{{.Name}}\t{{.CPUPerc}}\t{{.MemUsage}}",
        timeout=3.0,
    )
    stats: dict[str, tuple[str, str]] = {}
    for line in stats_raw.splitlines():
        parts = line.split("\t")
        if len(parts) >= 3:
            stats[parts[0]] = (parts[1], parts[2])

    tracker_rows = tracker.all_snapshots() if tracker else {}
    for row in rows:
        if row["name"] in stats:
            row["cpuPercent"], row["memoryUsage"] = stats[row["name"]]
        top_raw = await _docker_output("top", row["name"], timeout=1.5)
        processes = [
            " ".join(line.split()[1:])
            for line in top_raw.splitlines()[1:4]
            if line.strip()
        ]
        if processes:
            row["processes"] = processes
            row["currentCommand"] = processes[0] or row["currentCommand"]
        # Prefer exact container name, then agent-key snapshots.
        for key, entry in tracker_rows.items():
            if key == row["name"] or row["name"].startswith(f"{key}-"):
                if entry.get("currentCommand"):
                    row["currentCommand"] = entry["currentCommand"]
                    row["source"] = "tracker"
                break
    return rows


class RuntimeMonitor:
    """Single source of truth for the admin runtime dashboard."""

    def __init__(
        self,
        *,
        process_role: str,
        workspace: str,
        model: str,
        context_window_tokens: int,
        history_window_seconds: int = RUNTIME_HISTORY_WINDOW_SECONDS,
        history_max_samples: int = RUNTIME_HISTORY_MAX_SAMPLES,
        history_sample_interval_seconds: float = RUNTIME_HISTORY_SAMPLE_INTERVAL_SECONDS,
    ) -> None:
        self.process_role = process_role
        self.workspace = workspace
        self.model = model
        self.context_window_tokens = context_window_tokens
        self.history_window_seconds = max(1, int(history_window_seconds))
        self.history_max_samples = max(1, int(history_max_samples))
        self.history_sample_interval_seconds = max(0.0, float(history_sample_interval_seconds))
        self.started_at = time.time()
        self.docker_agent_tracker = DockerAgentRuntimeTracker(on_change=self._mark_changed)
        self._change_event = asyncio.Event()
        self._version = 0
        self._docker_sampler_task: asyncio.Task | None = None
        self._history_samples: deque[dict[str, Any]] = deque(maxlen=self.history_max_samples)
        self._main: dict[str, Any] = {
            "status": "idle",
            "sessionKey": None,
            "channel": None,
            "chatId": None,
            "startedAt": None,
            "stage": "idle",
            "currentToolCalls": [],
            "context": {
                "usedTokens": 0,
                "totalTokens": context_window_tokens,
                "percent": 0,
                "source": "unknown",
            },
            "lastUsage": {
                "promptTokens": 0,
                "completionTokens": 0,
                "cachedTokens": 0,
            },
            "lastError": None,
        }
        self._subagents: dict[str, dict[str, Any]] = {}
        self._docker_containers: list[dict[str, Any]] = []
        self._docker_daemon: dict[str, Any] = default_docker_daemon_snapshot()

    @property
    def version(self) -> int:
        return self._version

    def set_process_role(self, role: str) -> None:
        if role and role != self.process_role:
            self.process_role = role
            self._mark_changed()

    def _mark_changed(self) -> None:
        self._version += 1
        self._change_event.set()
        self._change_event = asyncio.Event()

    async def wait_for_change(self, version: int, timeout: float = 15.0) -> int:
        if version != self._version:
            return self._version
        try:
            await asyncio.wait_for(self._change_event.wait(), timeout=timeout)
        except asyncio.TimeoutError:
            pass
        return self._version

    def start_main_turn(self, *, session_key: str, channel: str, chat_id: str) -> None:
        now = _utc_now_iso()
        self._main.update({
            "status": "processing",
            "sessionKey": session_key,
            "channel": channel,
            "chatId": chat_id,
            "startedAt": now,
            "stage": "building_context",
            "currentToolCalls": [],
            "lastError": None,
        })
        self._mark_changed()

    def update_main_context(self, *, used_tokens: int, source: str) -> None:
        self._main["context"] = {
            "usedTokens": max(0, int(used_tokens)),
            "totalTokens": self.context_window_tokens,
            "percent": _status_percent(int(used_tokens), self.context_window_tokens),
            "source": source,
        }
        self._mark_changed()

    def update_tool_calls(
        self,
        tool_calls: list[Any],
        *,
        iteration: int | None = None,
        stage: str = "executing_tools",
    ) -> None:
        self._main["stage"] = stage if iteration is None else f"{stage}:{iteration}"
        self._main["currentToolCalls"] = _tool_call_snapshot(tool_calls)
        self._mark_changed()

    def update_usage(self, usage: dict[str, int] | None) -> None:
        usage = usage or {}
        self._main["lastUsage"] = {
            "promptTokens": int(usage.get("prompt_tokens", 0) or 0),
            "completionTokens": int(usage.get("completion_tokens", 0) or 0),
            "cachedTokens": int(usage.get("cached_tokens", 0) or 0),
        }
        self._mark_changed()

    def finish_main_turn(self, *, stop_reason: str | None = None, error: str | None = None) -> None:
        self._main["status"] = "error" if stop_reason == "error" or error else "idle"
        self._main["stage"] = stop_reason or "idle"
        self._main["currentToolCalls"] = []
        self._main["lastError"] = error
        self._mark_changed()

    def start_subagent(
        self,
        *,
        task_id: str,
        label: str,
        task: str,
        session_key: str | None,
    ) -> None:
        self._subagents[task_id] = {
            "id": task_id,
            "label": label,
            "status": "running",
            "startedAt": _utc_now_iso(),
            "finishedAt": None,
            "duration": None,
            "taskPreview": task[:240],
            "sessionKey": session_key,
        }
        self._mark_changed()

    def finish_subagent(self, task_id: str, *, status: str) -> None:
        entry = self._subagents.setdefault(
            task_id,
            {
                "id": task_id,
                "label": task_id,
                "startedAt": None,
                "taskPreview": "",
                "sessionKey": None,
            },
        )
        entry["status"] = status
        entry["finishedAt"] = _utc_now_iso()
        entry["duration"] = _format_duration(entry.get("startedAt"))
        self._mark_changed()

    def update_docker_snapshot(self, containers: list[dict[str, Any]]) -> None:
        self._docker_containers = list(containers)
        self._mark_changed()

    def update_docker_daemon(self, daemon: dict[str, Any]) -> None:
        self._docker_daemon = dict(daemon or default_docker_daemon_snapshot())
        self._mark_changed()

    def start_docker_sampler(self, *, interval_s: float = 1.0) -> None:
        if self._docker_sampler_task and not self._docker_sampler_task.done():
            return

        async def _run() -> None:
            while True:
                try:
                    daemon = await probe_docker_daemon()
                    self.update_docker_daemon(daemon)
                    if daemon.get("ok") is True:
                        self.update_docker_snapshot(
                            await sample_docker_containers(self.docker_agent_tracker)
                        )
                    else:
                        self.update_docker_snapshot([])
                except asyncio.CancelledError:
                    raise
                except Exception as exc:
                    logger.debug("Docker sampler failed: {}", exc)
                await asyncio.sleep(interval_s)

        self._docker_sampler_task = asyncio.create_task(_run())

    async def stop_docker_sampler(self) -> None:
        task = self._docker_sampler_task
        if not task:
            return
        task.cancel()
        try:
            await task
        except asyncio.CancelledError:
            pass
        self._docker_sampler_task = None

    def _prune_history(self, newest_epoch_ms: int) -> None:
        oldest_allowed = newest_epoch_ms - (self.history_window_seconds * 1000)
        while self._history_samples and int(self._history_samples[0].get("epochMs", 0) or 0) < oldest_allowed:
            self._history_samples.popleft()

    def _record_history_sample(self, snapshot: dict[str, Any]) -> None:
        epoch_ms = int(time.time() * 1000)
        sample = _runtime_history_sample_from_snapshot(snapshot, epoch_ms=epoch_ms)
        self._prune_history(epoch_ms)
        if not self._history_samples:
            self._history_samples.append(sample)
            return

        previous = self._history_samples[-1]
        elapsed_ms = epoch_ms - int(previous.get("epochMs", 0) or 0)
        state_changed = _runtime_history_signature(previous) != _runtime_history_signature(sample)
        interval_elapsed = elapsed_ms >= int(self.history_sample_interval_seconds * 1000)
        if state_changed or interval_elapsed:
            self._history_samples.append(sample)
        else:
            self._history_samples[-1] = sample

    def history_snapshot(self, *, limit: int | None = None) -> dict[str, Any]:
        if not self._history_samples:
            self.snapshot()
        return _runtime_history_payload(
            list(self._history_samples),
            limit=limit,
            window_seconds=self.history_window_seconds,
            sample_interval_seconds=self.history_sample_interval_seconds,
        )

    def snapshot(self, *, record_history: bool = True) -> dict[str, Any]:
        main = dict(self._main)
        active_subagents = [
            item for item in self._subagents.values()
            if item.get("status") == "running"
        ]
        if main["status"] == "idle" and active_subagents:
            main["status"] = "waiting_on_subagents"
            main["stage"] = "subagents_running"
        main["activeTaskCount"] = 1 if main["status"] == "processing" else 0
        main["lastSessionKey"] = main.get("sessionKey")
        main["model"] = self.model
        main["uptimeSeconds"] = max(0, int(time.time() - self.started_at))

        docker_containers = [dict(item) for item in self._docker_containers]
        snapshot = {
            "generatedAt": _utc_now_iso(),
            "process": {
                "role": self.process_role,
                "pid": os.getpid(),
                "workspace": self.workspace,
                "uptimeSeconds": max(0, int(time.time() - self.started_at)),
            },
            "mainAgent": main,
            "subagents": list(self._subagents.values()),
            "dockerDaemon": dict(self._docker_daemon),
            "dockerContainers": docker_containers,
            "dockerAgents": docker_containers,
        }
        if record_history:
            self._record_history_sample(snapshot)
        return snapshot


async def build_admin_snapshot(loop: Any) -> dict[str, Any]:
    """Build the full admin runtime snapshot."""
    monitor = getattr(loop, "runtime_monitor", None)
    if monitor is not None:
        snapshot = monitor.snapshot(record_history=False)
        _hydrate_main_from_sessions(snapshot, loop)
        if hasattr(monitor, "_record_history_sample"):
            monitor._record_history_sample(snapshot)
        return snapshot
    active_task_count = _active_task_count(loop)
    main_status = "processing" if active_task_count > 0 else "idle"
    if main_status == "idle" and getattr(loop, "_last_admin_stop_reason", None) == "error":
        main_status = "error"

    total_context_tokens = int(getattr(loop, "context_window_tokens", 0) or 0)
    used_context_tokens = int(getattr(loop, "_last_admin_context_tokens", 0) or 0)
    main_context_source = getattr(loop, "_last_admin_context_source", "unknown") or "unknown"
    last_usage = dict(getattr(loop, "_last_usage", {}) or {})

    snapshot = {
        "generatedAt": _utc_now_iso(),
        "mainAgent": {
            "status": main_status,
            "model": getattr(loop, "model", ""),
            "uptimeSeconds": max(0, int(time.time() - float(getattr(loop, "_start_time", time.time())))),
            "activeTaskCount": active_task_count,
            "lastSessionKey": getattr(loop, "_last_admin_session_key", None),
            "context": {
                "usedTokens": used_context_tokens,
                "totalTokens": total_context_tokens,
                "percent": _status_percent(used_context_tokens, total_context_tokens),
                "source": main_context_source,
            },
            "lastUsage": {
                "promptTokens": int(last_usage.get("prompt_tokens", 0) or 0),
                "completionTokens": int(last_usage.get("completion_tokens", 0) or 0),
                "cachedTokens": int(last_usage.get("cached_tokens", 0) or 0),
            },
        },
        "dockerAgents": [],
    }

    docker_cfg = getattr(loop, "_docker_agents_config", None)
    if not docker_cfg or not getattr(docker_cfg, "enabled", False):
        snapshot["dockerDaemon"] = default_docker_daemon_snapshot()
        return snapshot

    registry = build_default_registry()
    tracker = getattr(loop, "docker_runtime_tracker", None)
    snapshot["dockerDaemon"] = await probe_docker_daemon()

    for agent_key, cfg_obj in getattr(docker_cfg, "agents", {}).items():
        cfg = _dump_cfg(cfg_obj)
        runtime = tracker.snapshot(agent_key) if tracker else {
            "currentCommand": None,
            "startedAt": None,
            "lastPromptTokensEstimate": 0,
            "lastPromptContextPercentEstimate": 0,
            "lastTaskSummary": None,
        }
        adapter = registry.get(agent_key)
        image = cfg.get("image") or (adapter.default_image if adapter else "")
        persistent = bool(cfg.get("persistent", True))
        container_name = cfg.get("container_name") or f"openhire-{agent_key}"

        status = "not_created"
        try:
            inspect_status = await inspect_container_status(container_name)
            status = inspect_status or "not_created"
        except Exception as exc:
            logger.warning("Failed to inspect docker container {}: {}", container_name, exc)
            status = "unknown"

        if runtime["currentCommand"]:
            status = "processing" if status != "unknown" else "unknown"

        estimated_tokens = runtime["lastPromptTokensEstimate"]
        snapshot["dockerAgents"].append({
            "agentKey": agent_key,
            "containerName": container_name,
            "image": image,
            "persistent": persistent,
            "status": status,
            "currentCommand": runtime["currentCommand"],
            "startedAt": runtime["startedAt"],
            "context": {
                "usedTokens": estimated_tokens,
                "totalTokens": total_context_tokens,
                "percent": runtime["lastPromptContextPercentEstimate"],
                "source": "estimated" if estimated_tokens > 0 else "unavailable",
            },
        })

    return snapshot


async def build_runtime_history(
    loop: Any,
    *,
    limit: int | None = None,
    process_role: str = "api",
) -> dict[str, Any]:
    """Return recent in-memory runtime history for the admin dashboard."""
    monitor = getattr(loop, "runtime_monitor", None)
    if monitor is not None and hasattr(monitor, "history_snapshot"):
        await build_admin_snapshot(loop)
        return monitor.history_snapshot(limit=limit)

    snapshot_getter = getattr(loop, "get_admin_snapshot", None)
    if callable(snapshot_getter):
        snapshot = await snapshot_getter(process_role=process_role)
    else:
        snapshot = await build_admin_snapshot(loop)
    sample = _runtime_history_sample_from_snapshot(snapshot)
    return _runtime_history_payload([sample], limit=limit)
