# Docker Adapter 框架

## 概述

Docker Adapter 是 OpenHire 的执行层，负责在独立 Docker 容器中运行外部 AI agent。每个 agent 可以是持久化容器（长期存在）或临时容器（用完即销毁）。

## 支持的 Agent

| Agent | 类型 | Docker Image | 说明 |
|-------|------|-------------|------|
| OpenClaw | 需 build | `openhire-openclaw:latest` | 通过 ACP 统一调度 Claude Code/Codex/OpenCode 等 |
| Hermes | 需 build | `openhire-hermes:latest` | NousResearch 通用 agent |
| OpenHire (subagent) | 复用 | `openhire:latest` | 再启一个 OpenHire 实例作为 subagent |

> OpenHands 已禁用：不再注册为可用 Docker Adapter。

## 文件结构

```
openhire/adapters/
├── __init__.py          # AdapterRegistry 注册表
├── base.py              # DockerAgent ABC + 容器生命周期函数
├── tool.py              # DockerAgentTool (LLM 可调用)
└── agents/
    ├── openclaw.py      # OpenClaw + ACP 支持
    ├── openhands.py     # OpenHands 已禁用（不注册、不调用）
    ├── hermes.py        # Hermes
    └── openhire_subagent.py  # OpenHire 自身（容器内 subagent）
```

## 容器生命周期

### 持久化模式 (persistent: true)

```
ensure_running()
  ├── 容器存在且运行中 → 直接返回
  ├── 容器存在但停止 → docker start
  └── 容器不存在 → docker create + docker start + init commands
      └── 主进程: tail -f /dev/null (保持存活)

exec_in_container()
  └── docker exec <container> <command>
```

### 临时模式 (persistent: false)

```
run_container()
  └── docker run --rm <image> <command>
      └── 执行完自动销毁
```

## ACP (Agent Client Protocol)

OpenClaw 通过 ACP 协议统一管理多种 coding CLI：

```
OpenClaw 容器
  └── ACP Backend (acpx)
      ├── claude (Claude Code)
      ├── codex (OpenAI Codex CLI)
      ├── opencode
      ├── gemini (Gemini CLI)
      ├── copilot
      ├── cursor
      ├── kiro
      └── ...
```

容器首次创建后，自动通过 `openclaw config set` 写入 ACP 配置。

## 配置示例

```json
{
  "tools": {
    "dockerAgents": {
      "enabled": true,
      "agents": {
        "openclaw": {
          "persistent": true,
          "containerName": "openclaw-main",
          "role": "资深全栈工程师",
          "acp": {
            "defaultAgent": "claude",
            "allowedAgents": ["claude", "codex", "opencode", "gemini"],
            "permissionMode": "approve-all"
          },
          "env": {
            "ANTHROPIC_API_KEY": "${ANTHROPIC_API_KEY}"
          }
        }
      }
    }
  }
}
```

## DockerAgentConfig 字段

| 字段 | 类型 | 默认值 | 说明 |
|------|------|--------|------|
| enabled | bool | true | 是否启用 |
| image | string | "" | 覆盖默认镜像 |
| env | dict | {} | 环境变量，支持 `${VAR}` |
| timeout | int | 300 | 超时秒数 |
| memory_limit | string | "2g" | 内存限制 |
| cpus | string | "2" | CPU 限制 |
| persistent | bool | true | 持久化容器 |
| container_name | string | "" | 自定义容器名 |
| role | string | "" | 默认角色 |
| default_tools | list | [] | 默认工具 |
| default_skills | list | [] | 默认技能 |
| acp | ACPConfig | {} | ACP 配置 |
