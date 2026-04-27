import json

import pytest

from openhire.config.loader import (
    _resolve_env_vars,
    load_config,
    resolve_config_env_vars,
    save_config,
)


class TestResolveEnvVars:
    def test_replaces_string_value(self, monkeypatch):
        monkeypatch.setenv("MY_SECRET", "hunter2")
        assert _resolve_env_vars("${MY_SECRET}") == "hunter2"

    def test_partial_replacement(self, monkeypatch):
        monkeypatch.setenv("HOST", "example.com")
        assert _resolve_env_vars("https://${HOST}/api") == "https://example.com/api"

    def test_multiple_vars_in_one_string(self, monkeypatch):
        monkeypatch.setenv("USER", "alice")
        monkeypatch.setenv("PASS", "secret")
        assert _resolve_env_vars("${USER}:${PASS}") == "alice:secret"

    def test_nested_dicts(self, monkeypatch):
        monkeypatch.setenv("TOKEN", "abc123")
        data = {"channels": {"telegram": {"token": "${TOKEN}"}}}
        result = _resolve_env_vars(data)
        assert result["channels"]["telegram"]["token"] == "abc123"

    def test_lists(self, monkeypatch):
        monkeypatch.setenv("VAL", "x")
        assert _resolve_env_vars(["${VAL}", "plain"]) == ["x", "plain"]

    def test_ignores_non_strings(self):
        assert _resolve_env_vars(42) == 42
        assert _resolve_env_vars(True) is True
        assert _resolve_env_vars(None) is None
        assert _resolve_env_vars(3.14) == 3.14

    def test_plain_strings_unchanged(self):
        assert _resolve_env_vars("no vars here") == "no vars here"

    def test_missing_var_raises(self):
        with pytest.raises(ValueError, match="DOES_NOT_EXIST"):
            _resolve_env_vars("${DOES_NOT_EXIST}")


class TestResolveConfig:
    def test_resolves_env_vars_in_config(self, tmp_path, monkeypatch):
        monkeypatch.setenv("TEST_API_KEY", "resolved-key")
        config_path = tmp_path / "config.json"
        config_path.write_text(
            json.dumps(
                {"providers": {"groq": {"apiKey": "${TEST_API_KEY}"}}}
            ),
            encoding="utf-8",
        )

        raw = load_config(config_path)
        assert raw.providers.groq.api_key == "${TEST_API_KEY}"

        resolved = resolve_config_env_vars(raw)
        assert resolved.providers.groq.api_key == "resolved-key"

    def test_save_preserves_templates(self, tmp_path, monkeypatch):
        monkeypatch.setenv("MY_TOKEN", "real-token")
        config_path = tmp_path / "config.json"
        config_path.write_text(
            json.dumps(
                {"channels": {"telegram": {"token": "${MY_TOKEN}"}}}
            ),
            encoding="utf-8",
        )

        raw = load_config(config_path)
        save_config(raw, config_path)

        saved = json.loads(config_path.read_text(encoding="utf-8"))
        assert saved["channels"]["telegram"]["token"] == "${MY_TOKEN}"

    def test_resolve_config_backfills_nanobot_docker_agent_from_provider_defaults(self, tmp_path):
        config_path = tmp_path / "config.json"
        config_path.write_text(
            json.dumps(
                {
                    "agents": {
                        "defaults": {
                            "model": "gpt-5.4",
                            "provider": "openai",
                        }
                    },
                    "providers": {
                        "openai": {
                            "apiKey": "dummy",
                            "apiBase": "http://localhost:16666/v1",
                        }
                    },
                    "tools": {
                        "dockerAgents": {
                            "enabled": True,
                            "agents": {
                                "openclaw": {
                                    "persistent": True,
                                    "env": {
                                        "LLM_MODEL": "openai/gpt-5.4",
                                        "LLM_API_KEY": "dummy",
                                        "LLM_BASE_URL": "http://localhost:16666/v1",
                                    },
                                }
                            },
                        }
                    },
                }
            ),
            encoding="utf-8",
        )

        resolved = resolve_config_env_vars(load_config(config_path))

        nanobot = resolved.tools.docker_agents.agents["nanobot"]
        assert nanobot.persistent is True
        assert nanobot.image == "openhire-nanobot:latest"
        assert nanobot.env == {
            "LLM_MODEL": "gpt-5.4",
            "LLM_API_KEY": "dummy",
            "LLM_PROVIDER": "openai",
            "LLM_BASE_URL": "http://localhost:16666/v1",
        }

    def test_resolve_config_backfills_openclaw_docker_agent_from_provider_defaults(self, tmp_path):
        config_path = tmp_path / "config.json"
        config_path.write_text(
            json.dumps(
                {
                    "agents": {
                        "defaults": {
                            "model": "gpt-5.4",
                            "provider": "openai",
                        }
                    },
                    "providers": {
                        "openai": {
                            "apiKey": "dummy",
                            "apiBase": "http://localhost:16666/v1",
                        }
                    },
                    "tools": {
                        "dockerAgents": {
                            "enabled": True,
                            "agents": {},
                        }
                    },
                }
            ),
            encoding="utf-8",
        )

        resolved = resolve_config_env_vars(load_config(config_path))

        openclaw = resolved.tools.docker_agents.agents["openclaw"]
        assert openclaw.persistent is True
        assert openclaw.image == "openhire-openclaw:latest"
        assert openclaw.env == {
            "LLM_MODEL": "gpt-5.4",
            "LLM_API_KEY": "dummy",
            "LLM_PROVIDER": "openai",
            "LLM_BASE_URL": "http://localhost:16666/v1",
        }

    def test_resolve_config_merges_openclaw_defaults_without_overriding_explicit_env(self, tmp_path):
        config_path = tmp_path / "config.json"
        config_path.write_text(
            json.dumps(
                {
                    "agents": {
                        "defaults": {
                            "model": "gpt-5.4",
                            "provider": "openai",
                        }
                    },
                    "providers": {
                        "openai": {
                            "apiKey": "dummy",
                            "apiBase": "http://localhost:16666/v1",
                        }
                    },
                    "tools": {
                        "dockerAgents": {
                            "enabled": True,
                            "agents": {
                                "openclaw": {
                                    "persistent": False,
                                    "env": {
                                        "LLM_MODEL": "custom/model",
                                        "LLM_API_KEY": "explicit-key",
                                        "LLM_PROVIDER": "custom",
                                        "EXTRA_FLAG": "kept",
                                    },
                                }
                            },
                        }
                    },
                }
            ),
            encoding="utf-8",
        )

        resolved = resolve_config_env_vars(load_config(config_path))

        openclaw = resolved.tools.docker_agents.agents["openclaw"]
        assert openclaw.persistent is False
        assert openclaw.env == {
            "LLM_MODEL": "custom/model",
            "LLM_API_KEY": "explicit-key",
            "LLM_PROVIDER": "custom",
            "LLM_BASE_URL": "http://localhost:16666/v1",
            "EXTRA_FLAG": "kept",
        }
