"""Demo-mode helpers for hosted OpenHire admin deployments."""

from __future__ import annotations

import os
import time
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Any, Mapping

_TRUE_VALUES = {"1", "true", "yes", "on", "enabled", "force"}
_FALSE_VALUES = {"0", "false", "no", "off", "disabled"}
_AUTO_VALUES = {"", "auto", "detect"}
_MODELSCOPE_ENV_KEYS = {
    "EAS_SERVICE_NAME",
    "EAS_SERVICE_VERSION",
    "MODEL_SCOPE_ENV",
    "MODELSCOPE_ENV",
    "MODELSCOPE_STUDIO_ID",
    "MODELSCOPE_STUDIO_NAME",
    "MODELSCOPE_SPACE_ID",
    "MODELSCOPE_SPACE_NAME",
    "PAI_SERVICE_NAME",
    "PAI_SERVICE_VERSION",
    "SPACE_ID",
    "STUDIO_ID",
}
_PATH_MARKERS = (
    "modelscope-studios",
    "/eas_mount_tmp/",
    "studio_askor305_openhire",
)
MODELSCOPE_DEMO_MODEL = "deepseek-ai/DeepSeek-V4-Flash"
MODELSCOPE_DEMO_API_BASE = "https://api-inference.modelscope.cn/v1"
MODELSCOPE_DEMO_API_KEY_ENV_KEYS = (
    "OPENHIRE_MODELSCOPE_API_KEY",
    "MODELSCOPE_API_TOKEN",
    "MODELSCOPE_TOKEN",
    "MODEL_SCOPE_TOKEN",
)


def _now_iso(now: float | None = None) -> str:
    return datetime.fromtimestamp(now or time.time(), timezone.utc).isoformat(timespec="seconds").replace("+00:00", "Z")


def _minutes_ago(minutes: int, *, now: float | None = None) -> str:
    base = datetime.fromtimestamp(now or time.time(), timezone.utc)
    return (base - timedelta(minutes=minutes)).isoformat(timespec="seconds").replace("+00:00", "Z")


def _env_text(environ: Mapping[str, str], key: str) -> str:
    return str(environ.get(key) or "").strip()


def _modelscope_deploy_reason(
    environ: Mapping[str, str],
    *,
    workspace: str | Path | None = None,
    include_token_env: bool = True,
) -> str | None:
    target = _env_text(environ, "OPENHIRE_DEPLOY_TARGET").lower()
    if target and any(marker in target for marker in ("modelscope", "studio", "创空间")):
        return "OPENHIRE_DEPLOY_TARGET"

    for key in _MODELSCOPE_ENV_KEYS:
        if _env_text(environ, key):
            return key
    for key, value in environ.items():
        normalized_key = str(key).upper()
        if (
            normalized_key.startswith("MODELSCOPE_")
            and (include_token_env or normalized_key not in MODELSCOPE_DEMO_API_KEY_ENV_KEYS)
            and str(value or "").strip()
        ):
            return normalized_key

    path_candidates = [
        str(workspace or ""),
        _env_text(environ, "PWD"),
        _env_text(environ, "WORK_SPACE"),
        _env_text(environ, "PROJECT_DIR"),
    ]
    for candidate in path_candidates:
        normalized = candidate.lower()
        if normalized and any(marker in normalized for marker in _PATH_MARKERS):
            return "modelscope_path"

    return None


def demo_mode_status(
    *,
    environ: Mapping[str, str] | None = None,
    workspace: str | Path | None = None,
) -> dict[str, Any]:
    """Resolve whether demo mode should be active."""

    env = environ or os.environ
    raw = _env_text(env, "OPENHIRE_DEMO_MODE").lower()
    if raw in _TRUE_VALUES:
        return {"enabled": True, "mode": "forced", "reason": "OPENHIRE_DEMO_MODE"}
    if raw in _FALSE_VALUES:
        return {"enabled": False, "mode": "disabled", "reason": "OPENHIRE_DEMO_MODE"}
    if raw not in _AUTO_VALUES:
        return {"enabled": False, "mode": "disabled", "reason": "OPENHIRE_DEMO_MODE"}

    reason = _modelscope_deploy_reason(env, workspace=workspace)
    if reason:
        return {"enabled": True, "mode": "auto", "reason": reason}

    return {"enabled": False, "mode": "auto", "reason": "no_hosted_deploy_marker"}


def is_demo_mode(*, environ: Mapping[str, str] | None = None, workspace: str | Path | None = None) -> bool:
    return bool(demo_mode_status(environ=environ, workspace=workspace).get("enabled"))


def _modelscope_demo_api_key(environ: Mapping[str, str]) -> str:
    for key in MODELSCOPE_DEMO_API_KEY_ENV_KEYS:
        value = _env_text(environ, key)
        if value:
            return value
    return ""


def apply_modelscope_demo_config_overlay(
    config: Any,
    *,
    environ: Mapping[str, str] | None = None,
    workspace: str | Path | None = None,
) -> bool:
    """Point hosted ModelScope demo deployments at ModelScope DeepSeek."""

    env = environ or os.environ
    resolved_workspace = workspace
    if resolved_workspace is None:
        resolved_workspace = getattr(config, "workspace_path", None)
    status = demo_mode_status(environ=env, workspace=resolved_workspace)
    if not status.get("enabled"):
        return False
    if not _modelscope_deploy_reason(env, workspace=resolved_workspace, include_token_env=False):
        return False

    api_key = _modelscope_demo_api_key(env)
    if not api_key:
        env_names = ", ".join(MODELSCOPE_DEMO_API_KEY_ENV_KEYS)
        raise ValueError(
            "ModelScope demo mode requires a ModelScope Inference token. "
            f"Set one of: {env_names}."
        )

    config.agents.defaults.provider = "deepseek"
    config.agents.defaults.model = MODELSCOPE_DEMO_MODEL
    config.providers.deepseek.api_key = api_key
    config.providers.deepseek.api_base = MODELSCOPE_DEMO_API_BASE
    return True


def demo_employee_rows(*, now: float | None = None) -> list[dict[str, Any]]:
    records = [
        ("demo-market", "Mira Market", "市场洞察员工 / Market Insight", ["market-research", "competitor-intel"], ["browser", "search", "spreadsheet"]),
        ("demo-product", "Nova PM", "产品经理员工 / Product Manager", ["product-brief", "user-story"], ["docs", "figma", "jira"]),
        ("demo-architect", "Kepler Architect", "架构研发员工 / Architecture Engineer", ["system-design", "repo-navigation"], ["git", "pytest", "docker"]),
        ("demo-qa-ops", "Pulse QA/Ops", "质量与运维员工 / QA & Ops", ["release-checklist", "incident-review"], ["playwright", "logs", "grafana"]),
        ("demo-finance", "Atlas Finance", "财务风控员工 / Finance Risk", ["risk-review", "forecasting"], ["spreadsheet", "notebook", "pdf"]),
    ]
    rows: list[dict[str, Any]] = []
    for index, (employee_id, name, role, skill_ids, tools) in enumerate(records):
        rows.append({
            "id": employee_id,
            "name": name,
            "avatar": "",
            "role": role,
            "skills": [item.replace("-", " ").title() for item in skill_ids],
            "skill_ids": skill_ids,
            "system_prompt": f"You are {name}, a demo digital employee for {role}.",
            "agent_type": "nanobot" if index != 3 else "openclaw",
            "agent_config": {"demo": True, "workspace": f"/demo/workspace/{employee_id}"},
            "tools": tools,
            "container_name": f"openhire-{employee_id}",
            "status": "active",
            "created_at": _minutes_ago(180 - index * 17, now=now),
            "updated_at": _minutes_ago(8 + index, now=now),
            "demo": True,
            "persisted": False,
            "readOnly": True,
        })
    return rows


def demo_skill_rows(*, now: float | None = None) -> list[dict[str, Any]]:
    skills = [
        ("market-research", "Market Research", "快速收集市场、竞品和客户信号。", ["research", "market", "demo"]),
        ("product-brief", "Product Brief", "把业务目标整理成产品方案、范围和验收标准。", ["product", "planning", "demo"]),
        ("system-design", "System Design", "拆解架构、接口、数据流和风险点。", ["engineering", "architecture", "demo"]),
        ("release-checklist", "Release Checklist", "生成上线前检查、回滚和监控清单。", ["qa", "ops", "demo"]),
        ("risk-review", "Risk Review", "评估财务、合同和交付风险。", ["finance", "risk", "demo"]),
    ]
    return [
        {
            "id": skill_id,
            "source": "demo",
            "external_id": skill_id,
            "name": name,
            "description": description,
            "version": "1.0.0-demo",
            "author": "OpenHire Demo",
            "license": "MIT",
            "source_url": "",
            "safety_status": "demo",
            "tags": tags,
            "imported_at": _minutes_ago(240 - index * 13, now=now),
            "demo": True,
            "readOnly": True,
        }
        for index, (skill_id, name, description, tags) in enumerate(skills)
    ]


def demo_case_records() -> list[dict[str, Any]]:
    return [
        {
            "id": "demo-growth-review",
            "title": "20% Revenue Growth Review",
            "subtitle": "数字员工协作拆解增长、风险和执行计划",
            "description": "市场、产品、研发、财务和运维员工并行产出 CEO review action plan。",
            "tags": ["demo", "growth", "collaboration"],
            "metrics": [{"label": "employees", "value": "5"}, {"label": "workflow", "value": "6 steps"}],
            "input": {"goal": "Grow revenue 20% next quarter with controlled collection risk."},
            "output": {"format": "CEO review plan", "sections": ["Market", "Pipeline", "Risk", "Delivery"]},
            "workflow": [
                "市场洞察员工收集行业和竞品信号",
                "产品经理员工整理增长杠杆和路线图",
                "研发员工评估交付依赖和技术风险",
                "财务风控员工校验收入、毛利和回款节奏",
                "主智能体汇总为行动计划",
            ],
            "skills": [
                {"key": "market-research", "source": "local", "name": "Market Research", "description": "市场和竞品研究"},
                {"key": "product-brief", "source": "local", "name": "Product Brief", "description": "产品方案和验收标准"},
                {"key": "risk-review", "source": "local", "name": "Risk Review", "description": "收入和合同风险评估"},
            ],
            "employees": [
                {"key": "market", "name": "Mira Market", "role": "Market Insight", "skill_keys": ["market-research"], "tools": ["browser", "search"]},
                {"key": "product", "name": "Nova PM", "role": "Product Manager", "skill_keys": ["product-brief"], "tools": ["docs", "figma"]},
                {"key": "finance", "name": "Atlas Finance", "role": "Finance Risk", "skill_keys": ["risk-review"], "tools": ["spreadsheet"]},
            ],
            "demo": True,
            "readOnly": True,
        },
        {
            "id": "demo-release-war-room",
            "title": "Release War Room",
            "subtitle": "上线前检查、灰度、监控和回滚演练",
            "description": "研发、QA 和 SRE 员工协作完成一次可审计的发布准备流程。",
            "tags": ["demo", "release", "ops"],
            "metrics": [{"label": "checks", "value": "12"}, {"label": "risk", "value": "low"}],
            "skills": [
                {"key": "system-design", "source": "local", "name": "System Design", "description": "接口与依赖分析"},
                {"key": "release-checklist", "source": "local", "name": "Release Checklist", "description": "上线检查和回滚清单"},
            ],
            "employees": [
                {"key": "architect", "name": "Kepler Architect", "role": "Architecture Engineer", "skill_keys": ["system-design"], "tools": ["git", "pytest"]},
                {"key": "qaops", "name": "Pulse QA/Ops", "role": "QA & Ops", "skill_keys": ["release-checklist"], "tools": ["playwright", "grafana"]},
            ],
            "demo": True,
            "readOnly": True,
        },
    ]


def demo_case_summaries() -> list[dict[str, Any]]:
    summaries: list[dict[str, Any]] = []
    for case in demo_case_records():
        summaries.append({
            "id": case["id"],
            "title": case["title"],
            "subtitle": case.get("subtitle", ""),
            "description": case.get("description", ""),
            "tags": list(case.get("tags", [])),
            "metrics": list(case.get("metrics", [])),
            "employee_count": len(case.get("employees", [])),
            "skill_count": len(case.get("skills", [])),
            "imported_employee_count": 0,
            "imported_skill_count": 0,
            "is_imported": False,
            "demo": True,
            "readOnly": True,
        })
    return summaries


def demo_case_by_id(case_id: str) -> dict[str, Any] | None:
    normalized = str(case_id or "").strip()
    return next((case for case in demo_case_records() if case["id"] == normalized), None)


def demo_agent_skill_rows(*, now: float | None = None) -> list[dict[str, Any]]:
    rows = [
        ("demo-runbook-review", "Review release runbooks and produce rollback-ready checks.", "operations"),
        ("demo-market-brief", "Turn market signals into a concise opportunity brief.", "research"),
        ("demo-hiring-scorecard", "Create structured interview scorecards for role-based hiring.", "recruiting"),
    ]
    return [
        {
            "name": name,
            "description": description,
            "source": "demo",
            "category": category,
            "path": f"demo://skills/{name}/SKILL.md",
            "available": True,
            "missing_requirements": "",
            "updated_at": _minutes_ago(70 - index * 9, now=now),
            "editable": False,
            "deletable": False,
            "bound_employee_count": index + 1,
            "demo": True,
            "readOnly": True,
        }
        for index, (name, description, category) in enumerate(rows)
    ]


def demo_agent_skill_detail(name: str) -> dict[str, Any] | None:
    row = next((item for item in demo_agent_skill_rows() if item["name"] == str(name or "").strip()), None)
    if row is None:
        return None
    title = row["name"].replace("-", " ").title()
    return {
        "skill": row,
        "markdown": (
            f"---\nname: {row['name']}\ndescription: {row['description']}\ncategory: {row['category']}\n---\n\n"
            f"# {title}\n\n"
            "This is a read-only demo skill used by OpenHire demo mode.\n\n"
            "## Procedure\n\n"
            "1. Inspect the current request and relevant workspace context.\n"
            "2. Produce a concise, reusable work product.\n"
            "3. Record assumptions and follow-up risks.\n"
        ),
        "files": [{"path": "SKILL.md", "type": "file", "size": 320}],
        "metadata": {"name": row["name"], "description": row["description"], "category": row["category"]},
    }


def demo_persona_records(source: str) -> list[dict[str, Any]]:
    personas = [
        ("demo-ceo-strategist", "CEO Strategist", "擅长把业务目标拆成组织协作路径。", ["strategy", "demo"]),
        ("demo-interviewer", "Structured Interviewer", "擅长结构化面试、追问和候选人评估。", ["hiring", "demo"]),
        ("demo-operator", "Operations Commander", "擅长运营巡检、SOP 和风险升级。", ["ops", "demo"]),
    ]
    return [
        {
            "id": slug,
            "source": source,
            "external_id": slug,
            "name": name,
            "description": description,
            "version": "demo",
            "author": "OpenHire Demo",
            "license": "MIT",
            "source_url": "",
            "safety_status": "demo",
            "tags": tags,
            "updated_at": _now_iso(),
            "demo": True,
            "readOnly": True,
        }
        for slug, name, description, tags in personas
    ]


def demo_docker_daemon() -> dict[str, Any]:
    return {
        "status": "demo",
        "ok": True,
        "message": "Demo mode is supplying virtual Docker workers; no Docker daemon is required.",
        "version": "demo",
        "demo": True,
    }


def demo_docker_containers(*, now: float | None = None) -> list[dict[str, Any]]:
    current = now or time.time()
    bucket = int(current // 6)
    statuses = ["running", "processing", "healthy", "syncing"]
    commands = [
        "openhire worker --role market --task insight-refresh",
        "openhire worker --role product --task roadmap-sync",
        "openhire worker --role qaops --task release-check",
        "openhire worker --role finance --task risk-forecast",
    ]
    names = ["openhire-demo-market", "openhire-demo-product", "openhire-demo-qaops", "openhire-demo-finance"]
    rows: list[dict[str, Any]] = []
    for index, name in enumerate(names):
        status = statuses[(bucket + index) % len(statuses)]
        cpu = round(4.5 + ((bucket + index * 3) % 18) * 1.7, 1)
        memory = 180 + ((bucket + index * 71) % 420)
        rows.append({
            "name": name,
            "containerName": name,
            "agentKey": name.replace("openhire-demo-", ""),
            "image": f"openhire/{name.replace('openhire-demo-', '')}:demo",
            "status": status,
            "uptime": f"Up {20 + index * 9 + bucket % 8} minutes",
            "ports": f"78{60 + index}->7860/tcp",
            "cpuPercent": f"{cpu}%",
            "memoryUsage": f"{memory}MiB / 2GiB",
            "currentCommand": commands[index],
            "processes": [commands[index], "python -m openhire.agent.worker", "tail -f /demo/events.jsonl"],
            "source": "demo",
            "demo": True,
            "readOnly": True,
            "startedAt": _minutes_ago(20 + index * 9, now=current),
            "sessionKey": f"demo:{name}",
            "lastTaskSummary": commands[index],
            "context": {
                "usedTokens": 1300 + ((bucket + index * 333) % 4200),
                "totalTokens": 10000,
                "percent": 13 + ((bucket + index * 11) % 42),
                "source": "demo",
                "sessionKey": f"demo:{name}",
                "demo": True,
            },
        })
    return rows


def demo_subagents(*, now: float | None = None) -> list[dict[str, Any]]:
    current = now or time.time()
    bucket = int(current // 8)
    labels = ["Market Scan", "Release Review", "Risk Check"]
    statuses = ["running", "completed", "running"]
    return [
        {
            "id": f"demo-subagent-{index + 1}",
            "label": label,
            "status": statuses[(bucket + index) % len(statuses)],
            "startedAt": _minutes_ago(3 + index * 4, now=current),
            "finishedAt": None,
            "duration": None,
            "taskPreview": f"Demo {label.lower()} is updating the admin cockpit.",
            "sessionKey": f"demo:subagent:{index + 1}",
            "demo": True,
        }
        for index, label in enumerate(labels)
    ]


def demo_todos() -> list[dict[str, Any]]:
    return [
        {"key": "demo-import-case", "level": "warning", "title": "导入可复用案例", "body": "从资源中心选择一个 demo case，把员工、技能和配置变成真实工作流。", "actions": [{"kind": "cases", "label": "查看案例"}]},
        {"key": "demo-compose-team", "level": "idle", "title": "组建数字员工团队", "body": "用内置员工类型验证市场、产品、研发、运维和财务的协作分工。", "actions": [{"kind": "create", "label": "创建员工"}]},
        {"key": "demo-review-infra", "level": "ok", "title": "检查虚拟基础设施", "body": "Demo Docker worker 会自动变化，适合展示无 Docker daemon 的托管部署。", "actions": [{"kind": "infrastructure", "label": "查看基础设施"}]},
        {"key": "demo-agent-skills", "level": "idle", "title": "沉淀 Agent Skill", "body": "进入技能工作台查看可复用的 demo skill、提案和打包流程。", "actions": [{"kind": "agent-skills", "label": "打开技能工作台"}]},
        {"key": "demo-provider", "level": "warning", "title": "连接真实 Provider/IM", "body": "演示模式不需要真实模型和 Docker；接入生产前再配置 Provider、Feishu 或 Gateway。", "actions": [{"kind": "control", "label": "查看运行态"}]},
    ]


def _context_tokens(total_tokens: int, *, bucket: int) -> dict[str, Any]:
    total = max(1, int(total_tokens or 10000))
    used = min(total - 1, 1800 + (bucket % 9) * 540)
    return {"usedTokens": used, "totalTokens": total, "percent": int((used / total) * 100), "source": "demo", "demo": True}


def apply_demo_runtime_overlay(
    snapshot: dict[str, Any],
    *,
    demo_mode: Mapping[str, Any] | None = None,
    workspace: str | Path | None = None,
    model: str = "openhire-demo",
    process_role: str = "gateway",
    context_window_tokens: int = 10000,
    now: float | None = None,
) -> dict[str, Any]:
    status = dict(demo_mode or demo_mode_status(workspace=workspace))
    snapshot = dict(snapshot or {})
    snapshot["demoMode"] = status
    if not status.get("enabled"):
        return snapshot

    current = now or time.time()
    bucket = int(current // 6)
    snapshot["generatedAt"] = _now_iso(current)
    process = dict(snapshot.get("process") or {})
    process.setdefault("role", process_role or "gateway")
    process.setdefault("pid", "demo")
    process.setdefault("workspace", str(workspace or process.get("workspace") or "/demo/workspace"))
    process.setdefault("uptimeSeconds", 1800 + bucket * 6)
    if not process.get("connectedProcesses"):
        process["connectedProcesses"] = [
            {"pid": "demo-main", "role": "gateway", "status": "connected", "command": "openhire gateway --demo", "uptimeSeconds": process.get("uptimeSeconds", 0)},
            {"pid": "demo-sse", "role": "events", "status": "streaming", "command": "GET /admin/api/events", "uptimeSeconds": 90 + bucket},
            {"pid": "demo-worker", "role": "virtual-docker", "status": "running", "command": "demo docker sampler", "uptimeSeconds": 240 + bucket},
        ]
    process["demo"] = True
    snapshot["process"] = process

    main = dict(snapshot.get("mainAgent") or {})
    main_status = str(main.get("status") or "").lower()
    main_context = main.get("context") if isinstance(main.get("context"), dict) else {}
    if not main or (main_status in {"", "idle", "unknown"} and not main.get("lastSessionKey") and int(main_context.get("usedTokens", 0) or 0) <= 0):
        stage_cycle = ["planning", "delegating", "reviewing", "summarizing"]
        main = {
            "status": "processing" if bucket % 3 else "idle",
            "model": model or "openhire-demo",
            "uptimeSeconds": int(process.get("uptimeSeconds") or 0),
            "activeTaskCount": 1 if bucket % 3 else 0,
            "sessionKey": "demo:command-center",
            "lastSessionKey": "demo:command-center",
            "channel": "demo",
            "chatId": "command-center",
            "stage": stage_cycle[bucket % len(stage_cycle)],
            "currentToolCalls": [{"name": "demo_refresh", "arguments": {"panel": "admin"}}] if bucket % 3 else [],
            "context": _context_tokens(context_window_tokens, bucket=bucket),
            "lastUsage": {
                "promptTokens": 1300 + bucket % 500,
                "completionTokens": 320 + bucket % 120,
                "cachedTokens": 800 + bucket % 300,
            },
            "demo": True,
        }
    else:
        main.setdefault("demo", True)
    snapshot["mainAgent"] = main

    containers = snapshot.get("dockerContainers")
    if not isinstance(containers, list):
        containers = snapshot.get("dockerAgents")
    if not isinstance(containers, list) or not containers:
        containers = demo_docker_containers(now=current)
        snapshot["dockerDaemon"] = demo_docker_daemon()
    else:
        daemon = snapshot.get("dockerDaemon") if isinstance(snapshot.get("dockerDaemon"), dict) else {}
        if daemon.get("ok") is not True:
            snapshot["dockerDaemon"] = demo_docker_daemon()
    snapshot["dockerContainers"] = containers
    snapshot["dockerAgents"] = containers

    subagents = snapshot.get("subagents")
    if not isinstance(subagents, list) or not subagents:
        snapshot["subagents"] = demo_subagents(now=current)
    snapshot["demoTodos"] = demo_todos()
    return snapshot


def demo_runtime_history_samples(*, limit: int = 12, workspace: str | Path | None = None, model: str = "openhire-demo") -> list[dict[str, Any]]:
    count = max(1, min(60, int(limit or 12)))
    now = time.time()
    samples: list[dict[str, Any]] = []
    for offset in range(count - 1, -1, -1):
        sample_time = now - offset * 12
        snapshot = apply_demo_runtime_overlay(
            {},
            demo_mode={"enabled": True, "mode": "auto", "reason": "history"},
            workspace=workspace,
            model=model,
            now=sample_time,
        )
        main = snapshot["mainAgent"]
        context = main["context"]
        containers = snapshot["dockerContainers"]
        cpu_values = [float(str(item["cpuPercent"]).rstrip("%")) for item in containers]
        memory_values = [float(str(item["memoryUsage"]).split("MiB", 1)[0]) for item in containers]
        samples.append({
            "generatedAt": snapshot["generatedAt"],
            "epochMs": int(sample_time * 1000),
            "mainStatus": main["status"],
            "mainStage": main["stage"],
            "sessionKey": main["sessionKey"],
            "activeTaskCount": main["activeTaskCount"],
            "contextPercent": context["percent"],
            "contextUsedTokens": context["usedTokens"],
            "contextTotalTokens": context["totalTokens"],
            "processUptimeSeconds": snapshot["process"]["uptimeSeconds"],
            "dockerDaemonStatus": snapshot["dockerDaemon"]["status"],
            "dockerDaemonOk": True,
            "dockerTotal": len(containers),
            "dockerRunning": sum(1 for item in containers if str(item.get("status")).lower() in {"running", "processing", "healthy", "syncing"}),
            "dockerIssues": 0,
            "dockerCpuAvgPercent": round(sum(cpu_values) / len(cpu_values), 2),
            "dockerCpuMaxPercent": round(max(cpu_values), 2),
            "dockerMemoryTotalMiB": round(sum(memory_values), 2),
            "demo": True,
        })
    return samples


def apply_demo_runtime_history_overlay(
    payload: dict[str, Any],
    *,
    demo_mode: Mapping[str, Any] | None = None,
    workspace: str | Path | None = None,
    model: str = "openhire-demo",
    limit: int | None = None,
) -> dict[str, Any]:
    status = dict(demo_mode or demo_mode_status(workspace=workspace))
    payload = dict(payload or {})
    payload["demoMode"] = status
    if not status.get("enabled"):
        return payload
    samples = payload.get("samples") if isinstance(payload.get("samples"), list) else []
    should_replace = not samples or all(
        int(sample.get("dockerTotal", 0) or 0) == 0 and int(sample.get("contextUsedTokens", 0) or 0) == 0
        for sample in samples
        if isinstance(sample, dict)
    )
    if should_replace or len(samples) < 4:
        payload["samples"] = demo_runtime_history_samples(limit=max(limit or 12, 8), workspace=workspace, model=model)
        payload["generatedAt"] = _now_iso()
        payload.setdefault("windowSeconds", 15 * 60)
        payload.setdefault("sampleIntervalSeconds", 5)
    return payload
