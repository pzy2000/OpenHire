"""OpenClaw adapter — runs OpenClaw with ACP support for coding agents.

OpenClaw natively supports ACP (Agent Client Protocol), which can run
Claude Code, Codex, OpenCode, Gemini CLI, Copilot, Cursor, Kiro, and
other coding harnesses through a unified interface.
"""

import json
import ipaddress
import sys
from typing import Any
from urllib.parse import urlsplit, urlunsplit

from openhire.adapters.base import DockerAgent

_OPENCLAW_CONFIG_VERSION = "2"


class OpenClawAdapter(DockerAgent):

    @property
    def agent_name(self) -> str:
        return "openclaw"

    @property
    def default_image(self) -> str:
        return "openhire-openclaw:latest"

    @property
    def needs_build(self) -> bool:
        return True

    @property
    def build_context_url(self) -> str:
        return "https://github.com/openclaw/openclaw.git"

    @property
    def bootstrap_template_paths(self) -> dict[str, str]:
        return {
            "SOUL.md": "/app/docs/reference/templates/SOUL.md",
            "AGENTS.md": "/app/docs/reference/templates/AGENTS.md",
        }

    def build_command(
        self,
        task: str,
        role: str | None = None,
        tools: list[str] | None = None,
        skills: list[str] | None = None,
        *,
        instance_id: str | None = None,
    ) -> list[str]:
        prompt = self._build_task_prompt(task, role, skills)
        # `openclaw agent` requires a session route: --session-id (or --to / --agent).
        # Delegate runs are headless; scope one session per container/worker instance.
        session = (
            f"openhire-delegate-{instance_id}"
            if instance_id
            else "openhire-delegate-ephemeral"
        )
        return [
            "openclaw",
            "agent",
            "--session-id",
            session,
            "--message",
            prompt,
        ]

    def build_acp_config(self, acp_cfg: dict[str, Any]) -> dict[str, Any]:
        """Build the ACP section for openclaw.json from adapter config."""
        return {
            "acp": {
                "enabled": acp_cfg.get("enabled", True),
                "backend": acp_cfg.get("backend", "acpx"),
                "defaultAgent": acp_cfg.get("default_agent", "claude"),
                "allowedAgents": acp_cfg.get("allowed_agents", ["claude", "codex", "opencode"]),
                "maxConcurrentSessions": acp_cfg.get("max_concurrent_sessions", 4),
                "dispatch": {"enabled": True},
            }
        }

    def environment(self, env_config: dict[str, str]) -> dict[str, str]:
        env = super().environment(env_config)
        env["OPENHIRE_OPENCLAW_CONFIG_VERSION"] = _OPENCLAW_CONFIG_VERSION
        base_url = env.get("LLM_BASE_URL")
        if not base_url or not _should_rewrite_localhost_base_url():
            return env
        env["LLM_BASE_URL"] = _rewrite_localhost_base_url(base_url)
        return env

    def build_init_commands(self, agent_cfg: dict[str, Any]) -> list[list[str]]:
        """Configure OpenClaw runtime and ACP settings after first creation."""
        cmds: list[list[str]] = []
        env_cfg = agent_cfg.get("env", {})
        if isinstance(env_cfg, dict):
            env = self.environment({str(k): str(v) for k, v in env_cfg.items()})
            cmds.extend(_build_runtime_config_commands(env))

        acp_cfg = agent_cfg.get("acp", {})
        if not acp_cfg.get("enabled", True):
            return cmds

        permission_mode = acp_cfg.get("permission_mode", "approve-all")

        # Enable ACP
        cmds.append(["openclaw", "config", "set", "acp.enabled", "true"])
        cmds.append(["openclaw", "config", "set", "acp.backend", acp_cfg.get("backend", "acpx")])
        cmds.append(["openclaw", "config", "set", "acp.dispatch.enabled", "true"])

        # Set default agent
        default_agent = acp_cfg.get("default_agent", "claude")
        cmds.append(["openclaw", "config", "set", "acp.defaultAgent", default_agent])

        # Set allowed agents
        allowed = acp_cfg.get("allowed_agents", ["claude", "codex", "opencode"])
        cmds.append(["openclaw", "config", "set", "acp.allowedAgents", json.dumps(allowed)])

        # Set max concurrent sessions
        max_sessions = str(acp_cfg.get("max_concurrent_sessions", 4))
        cmds.append(["openclaw", "config", "set", "acp.maxConcurrentSessions", max_sessions])

        # Set permission mode
        cmds.append([
            "openclaw", "config", "set",
            "plugins.entries.acpx.config.permissionMode", permission_mode,
        ])

        return cmds


def _build_runtime_config_commands(env: dict[str, str]) -> list[list[str]]:
    raw_model = str(env.get("LLM_MODEL") or "").strip()
    api_key = str(env.get("LLM_API_KEY") or "").strip()
    if not raw_model or not api_key:
        return []

    provider_hint = str(env.get("LLM_PROVIDER") or "").strip()
    model, provider = _runtime_model_and_provider(raw_model, provider_hint=provider_hint)
    if not model or not provider:
        return []

    updates: list[dict[str, object]] = [
        {"path": "agents.defaults.model", "value": f"{provider}/{model}"},
    ]
    api_base = str(env.get("LLM_BASE_URL") or "").strip()
    provider_config = _runtime_provider_config(api_key=api_key, api_base=api_base)
    if provider_config:
        updates.append({"path": f"models.providers.{provider}", "value": provider_config})
    return [["openclaw", "config", "set", "--batch-json", json.dumps(updates)]]


def _runtime_provider_config(api_key: str, api_base: str) -> dict[str, object] | None:
    if not api_base:
        return None
    config: dict[str, object] = {
        "baseUrl": api_base,
        "apiKey": api_key,
        "api": "openai-completions",
        "models": [],
    }
    if _base_url_targets_private_network(api_base):
        config["request"] = {"allowPrivateNetwork": True}
    return config


def _runtime_model_and_provider(model: str, provider_hint: str = "") -> tuple[str, str]:
    provider = provider_hint.strip()
    raw_model = model.strip()
    if provider and "/" in raw_model:
        prefix, suffix = raw_model.split("/", 1)
        if prefix.strip() == provider:
            return suffix.strip(), provider
    if provider:
        return raw_model, provider
    if "/" in raw_model:
        prefix, suffix = raw_model.split("/", 1)
        return suffix.strip(), prefix.strip()
    return raw_model, "openai"


def _should_rewrite_localhost_base_url() -> bool:
    return sys.platform in {"darwin", "win32"}


def _rewrite_localhost_base_url(base_url: str) -> str:
    try:
        parts = urlsplit(base_url)
    except ValueError:
        return base_url

    host = parts.hostname
    if host not in {"localhost", "127.0.0.1", "::1"} or not parts.scheme:
        return base_url

    userinfo = ""
    if parts.username:
        userinfo = parts.username
        if parts.password:
            userinfo += f":{parts.password}"
        userinfo += "@"
    port = f":{parts.port}" if parts.port else ""
    netloc = f"{userinfo}host.docker.internal{port}"
    return urlunsplit((parts.scheme, netloc, parts.path, parts.query, parts.fragment))


def _base_url_targets_private_network(base_url: str) -> bool:
    try:
        parts = urlsplit(base_url)
    except ValueError:
        return False
    host = (parts.hostname or "").strip().lower()
    if host in {"localhost", "host.docker.internal", "gateway.docker.internal", "docker.for.mac.localhost"}:
        return True
    try:
        addr = ipaddress.ip_address(host)
    except ValueError:
        return False
    return (
        addr.is_private
        or addr.is_loopback
        or addr.is_link_local
        or addr.is_reserved
        or addr.is_unspecified
    )
