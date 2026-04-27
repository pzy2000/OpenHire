"""Nanobot adapter — runs HKUDS/nanobot as a Docker subagent."""

from __future__ import annotations

import json
import sys
from urllib.parse import urlsplit, urlunsplit

from openhire.adapters.base import DockerAgent

_RUNTIME_CONFIG_PATH = "/home/nanobot/.nanobot/config.json"
_CONFIG_WRITE_SCRIPT = (
    "from pathlib import Path; import sys; "
    f"path = Path('{_RUNTIME_CONFIG_PATH}'); "
    "path.parent.mkdir(parents=True, exist_ok=True); "
    "path.write_text(sys.argv[1], encoding='utf-8')"
)
_KNOWN_PROVIDER_KEYS = {
    "custom",
    "azure_openai",
    "anthropic",
    "openai",
    "openrouter",
    "deepseek",
    "groq",
    "zhipu",
    "dashscope",
    "vllm",
    "ollama",
    "ovms",
    "gemini",
    "moonshot",
    "minimax",
    "mistral",
    "stepfun",
    "xiaomi_mimo",
    "aihubmix",
    "siliconflow",
    "volcengine",
    "volcengine_coding_plan",
    "byteplus",
    "byteplus_coding_plan",
    "qianfan",
}


class NanobotAdapter(DockerAgent):
    """Adapter for HKUDS/nanobot ultra-lightweight AI agent."""

    @property
    def agent_name(self) -> str:
        return "nanobot"

    @property
    def default_image(self) -> str:
        return "openhire-nanobot:latest"

    @property
    def needs_build(self) -> bool:
        return True

    @property
    def build_context_url(self) -> str:
        return "https://github.com/HKUDS/nanobot.git"

    @property
    def bootstrap_template_paths(self) -> dict[str, str]:
        return {
            "SOUL.md": "/app/nanobot/templates/SOUL.md",
            "AGENTS.md": "/app/nanobot/templates/AGENTS.md",
        }

    @property
    def persistent_entrypoint(self) -> str | None:
        return "sh"

    def persistent_command(self) -> list[str]:
        return ["-lc", "tail -f /dev/null"]

    def environment(self, env_config: dict[str, str]) -> dict[str, str]:
        env = super().environment(env_config)
        base_url = env.get("LLM_BASE_URL")
        if not base_url or not _should_rewrite_localhost_base_url():
            return env
        env["LLM_BASE_URL"] = _rewrite_localhost_base_url(base_url)
        return env

    def build_init_commands(self, agent_cfg: dict[str, object]) -> list[list[str]]:
        env_cfg = agent_cfg.get("env", {})
        if not isinstance(env_cfg, dict):
            return []
        env = self.environment({str(k): str(v) for k, v in env_cfg.items()})
        runtime_config = _build_runtime_config(env)
        if runtime_config is None:
            return []
        return [[
            "python",
            "-c",
            _CONFIG_WRITE_SCRIPT,
            json.dumps(runtime_config, ensure_ascii=False),
        ]]

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
        session = f"openhire-delegate-{instance_id}" if instance_id else "openhire-delegate-ephemeral"
        return [
            "nanobot",
            "agent",
            "--session",
            session,
            "--workspace",
            "/workspace",
            "--message",
            prompt,
        ]


def _build_runtime_config(env: dict[str, str]) -> dict[str, object] | None:
    raw_model = str(env.get("LLM_MODEL") or "").strip()
    api_key = str(env.get("LLM_API_KEY") or "").strip()
    if not raw_model or not api_key:
        return None

    provider_hint = str(env.get("LLM_PROVIDER") or "").strip()
    model, provider = _runtime_model_and_provider(raw_model, provider_hint=provider_hint)
    provider_cfg: dict[str, str] = {"apiKey": api_key}
    api_base = str(env.get("LLM_BASE_URL") or "").strip()
    if api_base:
        provider_cfg["apiBase"] = api_base

    return {
        "agents": {
            "defaults": {
                "workspace": "/workspace",
                "model": model,
                "provider": provider,
            }
        },
        "providers": {
            provider: provider_cfg,
        },
    }


def _runtime_model_and_provider(model: str, provider_hint: str = "") -> tuple[str, str]:
    normalized_hint = _normalize_provider_key(provider_hint)
    if normalized_hint:
        if "/" in model:
            prefix, suffix = model.split("/", 1)
            if _normalize_provider_key(prefix) == normalized_hint:
                return suffix.strip(), normalized_hint
        return model, normalized_hint
    if "/" in model:
        prefix, suffix = model.split("/", 1)
        provider = _provider_key_for_model(prefix)
        return suffix.strip(), provider
    return model, _provider_key_for_model(model)


def _provider_key_for_model(model: str) -> str:
    prefix = model.strip().lower()
    normalized = _normalize_provider_key(prefix)
    if normalized in _KNOWN_PROVIDER_KEYS:
        return normalized
    if prefix.startswith(("gpt-", "o1", "o3", "o4")):
        return "openai"
    return "openai" if not prefix else "custom"


def _normalize_provider_key(value: str) -> str:
    return value.strip().lower().replace("-", "_")


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
