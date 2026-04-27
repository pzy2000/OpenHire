from __future__ import annotations

import asyncio
import time
from datetime import datetime, timedelta
from types import SimpleNamespace

import pytest

from openhire.admin.runtime import (
    DockerAgentRuntimeTracker,
    RuntimeMonitor,
    _parse_docker_cpu_percent,
    _parse_docker_memory_mib,
    build_runtime_history,
    build_admin_snapshot,
    parse_docker_ps_rows,
    probe_docker_daemon,
    repair_docker_daemon,
)
from openhire.config.schema import DockerAgentConfig, DockerAgentsConfig
from openhire.session.manager import SessionManager


class _DoneTask:
    def done(self) -> bool:
        return False


def test_docker_runtime_tracker_tracks_current_command_and_estimates_context() -> None:
    tracker = DockerAgentRuntimeTracker()

    tracker.register_start(
        agent_key="nanobot",
        command=["nanobot", "agent", "--message", "build admin page"],
        prompt_text="build admin page",
        context_window_tokens=1000,
    )

    active = tracker.snapshot("nanobot")
    assert active["currentCommand"].startswith("nanobot agent --message")
    assert active["startedAt"]
    assert active["lastPromptTokensEstimate"] > 0
    assert active["lastPromptContextPercentEstimate"] > 0

    tracker.register_finish("nanobot")

    idle = tracker.snapshot("nanobot")
    assert idle["currentCommand"] is None
    assert idle["startedAt"] is None
    assert idle["lastPromptTokensEstimate"] == active["lastPromptTokensEstimate"]
    assert idle["lastPromptContextPercentEstimate"] == active["lastPromptContextPercentEstimate"]


@pytest.mark.asyncio
async def test_build_admin_snapshot_reports_processing_and_container_status(monkeypatch) -> None:
    async def fake_inspect(_name: str) -> str | None:
        return "running"

    async def fake_probe_docker_daemon(*_args, **_kwargs):
        return {
            "status": "running",
            "ok": True,
            "message": "Docker daemon is reachable.",
            "version": "test",
        }

    monkeypatch.setattr("openhire.admin.runtime.inspect_container_status", fake_inspect)
    monkeypatch.setattr("openhire.admin.runtime.probe_docker_daemon", fake_probe_docker_daemon)

    docker_cfg = DockerAgentsConfig(
        enabled=True,
        agents={
            "nanobot": DockerAgentConfig(
                image="openhire-nanobot:latest",
                persistent=True,
            )
        },
    )
    tracker = DockerAgentRuntimeTracker()
    tracker.register_start(
        agent_key="nanobot",
        command=["nanobot", "agent", "--message", "build admin page"],
        prompt_text="build admin page",
        context_window_tokens=1000,
    )

    loop = SimpleNamespace(
        model="test-model",
        _start_time=time.time() - 120,
        _active_tasks={"cli:test": [_DoneTask()]},
        _last_usage={"prompt_tokens": 100, "completion_tokens": 20, "cached_tokens": 10},
        context_window_tokens=1000,
        _last_admin_session_key="cli:test",
        _last_admin_context_tokens=250,
        _last_admin_context_source="session",
        _last_admin_stop_reason=None,
        _docker_agents_config=docker_cfg,
        docker_runtime_tracker=tracker,
    )

    snapshot = await build_admin_snapshot(loop)

    assert snapshot["mainAgent"]["status"] == "processing"
    assert snapshot["mainAgent"]["context"]["percent"] == 25
    assert snapshot["mainAgent"]["lastSessionKey"] == "cli:test"
    assert snapshot["dockerAgents"][0]["agentKey"] == "nanobot"
    assert snapshot["dockerAgents"][0]["status"] == "processing"
    assert snapshot["dockerAgents"][0]["context"]["source"] == "estimated"
    assert snapshot["dockerDaemon"]["ok"] is True
    assert "env" not in snapshot["dockerAgents"][0]


@pytest.mark.asyncio
async def test_build_admin_snapshot_marks_unknown_when_inspect_fails(monkeypatch) -> None:
    async def broken_inspect(_name: str) -> str | None:
        raise RuntimeError("docker unavailable")

    async def fake_probe_docker_daemon(*_args, **_kwargs):
        return {
            "status": "running",
            "ok": True,
            "message": "Docker daemon is reachable.",
            "version": "test",
        }

    monkeypatch.setattr("openhire.admin.runtime.inspect_container_status", broken_inspect)
    monkeypatch.setattr("openhire.admin.runtime.probe_docker_daemon", fake_probe_docker_daemon)

    loop = SimpleNamespace(
        model="test-model",
        _start_time=time.time() - 30,
        _active_tasks={},
        _last_usage={},
        context_window_tokens=1000,
        _last_admin_session_key=None,
        _last_admin_context_tokens=0,
        _last_admin_context_source="unknown",
        _last_admin_stop_reason=None,
        _docker_agents_config=DockerAgentsConfig(
            enabled=True,
            agents={"aider": DockerAgentConfig(persistent=True)},
        ),
        docker_runtime_tracker=DockerAgentRuntimeTracker(),
    )

    snapshot = await build_admin_snapshot(loop)

    assert snapshot["dockerAgents"][0]["status"] == "unknown"
    assert snapshot["dockerDaemon"]["ok"] is True


@pytest.mark.asyncio
async def test_probe_docker_daemon_reports_unavailable_when_info_fails(monkeypatch) -> None:
    class _FailedDockerInfo:
        returncode = 1

        async def communicate(self):
            return b"", b"Cannot connect to the Docker daemon at unix:///var/run/docker.sock"

    async def fake_create_subprocess_exec(*args, **_kwargs):
        assert args[:4] == ("docker", "info", "--format", "{{.ServerVersion}}")
        return _FailedDockerInfo()

    monkeypatch.setattr(asyncio, "create_subprocess_exec", fake_create_subprocess_exec)

    daemon = await probe_docker_daemon()

    assert daemon["status"] == "unavailable"
    assert daemon["ok"] is False
    assert "Cannot connect to the Docker daemon" in daemon["message"]


@pytest.mark.asyncio
async def test_repair_docker_daemon_launches_docker_desktop_on_macos(monkeypatch) -> None:
    probes = [
        {
            "status": "unavailable",
            "ok": False,
            "message": "Cannot connect to the Docker daemon",
            "version": "",
        },
        {
            "status": "running",
            "ok": True,
            "message": "Docker daemon is reachable.",
            "version": "test",
        },
    ]
    launched: list[tuple[str, ...]] = []

    async def fake_probe(*_args, **_kwargs):
        return probes.pop(0)

    class _StartedDocker:
        returncode = 0

        async def communicate(self):
            return b"", b""

    async def fake_create_subprocess_exec(*args, **_kwargs):
        launched.append(tuple(args))
        return _StartedDocker()

    async def fake_sleep(_seconds: float) -> None:
        return None

    monkeypatch.setattr("openhire.admin.runtime.probe_docker_daemon", fake_probe)
    monkeypatch.setattr("openhire.admin.runtime.platform.system", lambda: "Darwin")
    monkeypatch.setattr("openhire.admin.runtime.shutil.which", lambda name: "/usr/bin/open" if name == "open" else None)
    monkeypatch.setattr(asyncio, "create_subprocess_exec", fake_create_subprocess_exec)
    monkeypatch.setattr(asyncio, "sleep", fake_sleep)

    result = await repair_docker_daemon(wait_timeout=1.0, poll_interval=0.0)

    assert launched == [("open", "-a", "Docker")]
    assert result["attempted"] is True
    assert result["command"] == ["open", "-a", "Docker"]
    assert result["dockerDaemon"]["ok"] is True


def test_runtime_monitor_snapshot_includes_docker_daemon_health() -> None:
    monitor = RuntimeMonitor(
        process_role="gateway",
        workspace="/workspace",
        model="test-model",
        context_window_tokens=1000,
    )

    initial = monitor.snapshot()
    assert initial["dockerDaemon"]["status"] == "unknown"
    assert initial["dockerDaemon"]["ok"] is None

    monitor.update_docker_daemon({
        "status": "unavailable",
        "ok": False,
        "message": "Cannot connect to the Docker daemon",
        "version": "",
    })

    snapshot = monitor.snapshot()
    assert snapshot["dockerDaemon"]["ok"] is False
    assert snapshot["dockerDaemon"]["status"] == "unavailable"
    assert "Cannot connect" in snapshot["dockerDaemon"]["message"]


def test_docker_resource_parsers_accept_common_docker_stats_strings() -> None:
    assert _parse_docker_cpu_percent("12.34%") == 12.34
    assert _parse_docker_cpu_percent("bad") is None
    assert _parse_docker_memory_mib("512KiB / 1GiB") == 0.5
    assert _parse_docker_memory_mib("100MiB / 2GiB") == 100.0
    assert _parse_docker_memory_mib("1.5GiB / 8GiB") == 1536.0
    assert _parse_docker_memory_mib("bad") is None


def test_runtime_monitor_history_records_context_docker_and_resource_metrics() -> None:
    monitor = RuntimeMonitor(
        process_role="gateway",
        workspace="/workspace",
        model="test-model",
        context_window_tokens=1000,
    )

    monitor.update_main_context(used_tokens=250, source="live")
    monitor.update_docker_daemon({
        "status": "running",
        "ok": True,
        "message": "Docker daemon is reachable.",
        "version": "test",
    })
    monitor.update_docker_snapshot([
        {
            "name": "nanobot-1",
            "status": "running",
            "cpuPercent": "12.5%",
            "memoryUsage": "100MiB / 2GiB",
        },
        {
            "name": "nanobot-2",
            "status": "exited",
            "cpuPercent": "bad",
            "memoryUsage": "1GiB / 2GiB",
        },
    ])

    monitor.snapshot()
    history = monitor.history_snapshot()
    sample = history["samples"][-1]

    assert history["windowSeconds"] == 900
    assert history["sampleIntervalSeconds"] == 5
    assert sample["mainStatus"] == "idle"
    assert sample["contextPercent"] == 25
    assert sample["contextUsedTokens"] == 250
    assert sample["dockerDaemonStatus"] == "running"
    assert sample["dockerTotal"] == 2
    assert sample["dockerRunning"] == 1
    assert sample["dockerIssues"] == 1
    assert sample["dockerCpuAvgPercent"] == 12.5
    assert sample["dockerCpuMaxPercent"] == 12.5
    assert sample["dockerMemoryTotalMiB"] == 1124.0


def test_runtime_monitor_history_merges_interval_but_records_state_changes(monkeypatch) -> None:
    now = [1000.0]
    monkeypatch.setattr("openhire.admin.runtime.time.time", lambda: now[0])
    monitor = RuntimeMonitor(
        process_role="gateway",
        workspace="/workspace",
        model="test-model",
        context_window_tokens=1000,
        history_sample_interval_seconds=5,
        history_max_samples=5,
    )

    monitor.snapshot()
    assert len(monitor.history_snapshot()["samples"]) == 1

    now[0] += 1
    monitor.update_main_context(used_tokens=100, source="live")
    monitor.snapshot()
    samples = monitor.history_snapshot()["samples"]
    assert len(samples) == 1
    assert samples[-1]["contextPercent"] == 10

    now[0] += 1
    monitor.start_main_turn(session_key="feishu:chat-1", channel="feishu", chat_id="chat-1")
    monitor.snapshot()
    samples = monitor.history_snapshot()["samples"]
    assert len(samples) == 2
    assert samples[-1]["mainStatus"] == "processing"

    now[0] += 6
    monitor.update_main_context(used_tokens=200, source="live")
    monitor.snapshot()
    samples = monitor.history_snapshot()["samples"]
    assert len(samples) == 3
    assert samples[-1]["contextPercent"] == 20


def test_runtime_monitor_history_respects_max_samples(monkeypatch) -> None:
    now = [2000.0]
    monkeypatch.setattr("openhire.admin.runtime.time.time", lambda: now[0])
    monitor = RuntimeMonitor(
        process_role="gateway",
        workspace="/workspace",
        model="test-model",
        context_window_tokens=1000,
        history_sample_interval_seconds=0,
        history_max_samples=3,
    )

    for used_tokens in [10, 20, 30, 40, 50]:
        now[0] += 1
        monitor.update_main_context(used_tokens=used_tokens, source="live")
        monitor.snapshot()

    samples = monitor.history_snapshot()["samples"]
    assert len(samples) == 3
    assert [sample["contextUsedTokens"] for sample in samples] == [30, 40, 50]


@pytest.mark.asyncio
async def test_build_runtime_history_falls_back_to_current_snapshot_without_monitor() -> None:
    loop = SimpleNamespace(
        model="test-model",
        _start_time=time.time() - 30,
        _active_tasks={},
        _last_usage={},
        context_window_tokens=1000,
        _last_admin_session_key="api:default",
        _last_admin_context_tokens=400,
        _last_admin_context_source="session",
        _last_admin_stop_reason=None,
        _docker_agents_config=None,
    )

    history = await build_runtime_history(loop, limit=5)

    assert len(history["samples"]) == 1
    assert history["samples"][0]["mainStatus"] == "idle"
    assert history["samples"][0]["contextPercent"] == 40
    assert history["samples"][0]["dockerDaemonStatus"] == "unknown"


def test_runtime_monitor_reports_live_processing_context() -> None:
    monitor = RuntimeMonitor(
        process_role="gateway",
        workspace="/workspace",
        model="test-model",
        context_window_tokens=1000,
    )

    monitor.start_main_turn(
        session_key="feishu:chat-1",
        channel="feishu",
        chat_id="chat-1",
    )
    monitor.update_main_context(used_tokens=250, source="live")

    snapshot = monitor.snapshot()

    assert snapshot["process"]["role"] == "gateway"
    assert snapshot["mainAgent"]["status"] == "processing"
    assert snapshot["mainAgent"]["sessionKey"] == "feishu:chat-1"
    assert snapshot["mainAgent"]["lastSessionKey"] == "feishu:chat-1"
    assert snapshot["mainAgent"]["context"]["percent"] == 25

    monitor.finish_main_turn(stop_reason="completed")
    snapshot = monitor.snapshot()
    assert snapshot["mainAgent"]["status"] == "idle"
    assert snapshot["mainAgent"]["context"]["usedTokens"] == 250


def test_runtime_monitor_tracks_subagents_and_waiting_status() -> None:
    monitor = RuntimeMonitor(
        process_role="gateway",
        workspace="/workspace",
        model="test-model",
        context_window_tokens=1000,
    )

    monitor.start_subagent(
        task_id="abc123",
        label="frontend",
        task="build the frontend",
        session_key="feishu:chat-1",
    )

    snapshot = monitor.snapshot()
    assert snapshot["mainAgent"]["status"] == "waiting_on_subagents"
    assert snapshot["subagents"][0]["id"] == "abc123"
    assert snapshot["subagents"][0]["sessionKey"] == "feishu:chat-1"
    assert snapshot["subagents"][0]["status"] == "running"

    monitor.finish_subagent("abc123", status="ok")
    snapshot = monitor.snapshot()
    assert snapshot["subagents"][0]["status"] == "ok"


def test_parse_docker_ps_rows_detects_nanobot_and_openhire_containers() -> None:
    raw = (
        # Disabled OpenHands-specific containers should be ignored.
        "openhands-1\\tghcr.io/all-hands-ai/openhands:0.55\\trunning\\tUp 4 hours\\t0.0.0.0:3000->3000/tcp\\n"
        "nanobot-1\\topenhire-nanobot:latest\\trunning\\tUp 4 hours\\t3000/tcp\\n"
        "openhire-nanobot\\topenhire/agent:latest\\trunning\\tUp 8 minutes\\t3000/tcp\\n"
        "postgres\\tpostgres:16\\trunning\\tUp 4 hours\\t5432/tcp\\n"
    )

    rows = parse_docker_ps_rows(raw)

    assert [row["name"] for row in rows] == ["nanobot-1", "openhire-nanobot"]
    assert rows[0]["currentCommand"] == "server/idle"
    assert rows[1]["source"] == "docker"


@pytest.mark.asyncio
async def test_build_admin_snapshot_hydrates_idle_monitor_from_latest_feishu_session(tmp_path) -> None:
    sessions = SessionManager(tmp_path)
    old = sessions.get_or_create("cli:direct")
    old.updated_at = datetime.now() - timedelta(hours=1)
    old.add_message("user", "old cli message")
    sessions.save(old)

    feishu = sessions.get_or_create("feishu:oc_real_chat")
    feishu.add_message("user", "飞书里真实发生过的消息")
    feishu.add_message("assistant", "真实回复")
    sessions.save(feishu)

    class _Consolidator:
        def estimate_session_prompt_tokens(self, session):
            assert session.key == "feishu:oc_real_chat"
            return 456, "session"

    loop = SimpleNamespace(
        model="test-model",
        context_window_tokens=1000,
        runtime_monitor=RuntimeMonitor(
            process_role="gateway",
            workspace=str(tmp_path),
            model="test-model",
            context_window_tokens=1000,
        ),
        sessions=sessions,
        consolidator=_Consolidator(),
        _last_usage={"prompt_tokens": 12, "completion_tokens": 3, "cached_tokens": 1},
        _last_admin_session_key=None,
        _last_admin_context_tokens=0,
        _last_admin_context_source="unknown",
        _last_admin_stop_reason=None,
    )

    snapshot = await build_admin_snapshot(loop)

    assert snapshot["mainAgent"]["status"] == "idle"
    assert snapshot["mainAgent"]["lastSessionKey"] == "feishu:oc_real_chat"
    assert snapshot["mainAgent"]["channel"] == "feishu"
    assert snapshot["mainAgent"]["chatId"] == "oc_real_chat"
    assert snapshot["mainAgent"]["context"]["usedTokens"] == 456
    assert snapshot["mainAgent"]["context"]["percent"] == 45
    assert snapshot["mainAgent"]["context"]["source"] == "session"


@pytest.mark.asyncio
async def test_build_admin_snapshot_preserves_cleared_context_on_idle_monitor(tmp_path) -> None:
    sessions = SessionManager(tmp_path)
    sessions.get_or_create("api:clear")

    class _Consolidator:
        def estimate_session_prompt_tokens(self, session):
            assert session.key == "api:clear"
            return 321, "session"

    monitor = RuntimeMonitor(
        process_role="gateway",
        workspace=str(tmp_path),
        model="test-model",
        context_window_tokens=1000,
    )
    monitor.start_main_turn(session_key="api:clear", channel="api", chat_id="clear")
    monitor.update_main_context(used_tokens=0, source="cleared")
    monitor.finish_main_turn(stop_reason="completed")

    loop = SimpleNamespace(
        model="test-model",
        context_window_tokens=1000,
        runtime_monitor=monitor,
        sessions=sessions,
        consolidator=_Consolidator(),
        _last_usage={},
        _last_admin_session_key="api:clear",
        _last_admin_context_tokens=0,
        _last_admin_context_source="cleared",
        _last_admin_stop_reason=None,
    )

    snapshot = await build_admin_snapshot(loop)
    context = snapshot["mainAgent"]["context"]

    assert snapshot["mainAgent"]["status"] == "idle"
    assert snapshot["mainAgent"]["lastSessionKey"] == "api:clear"
    assert context["usedTokens"] == 0
    assert context["percent"] == 0
    assert context["source"] == "cleared"
