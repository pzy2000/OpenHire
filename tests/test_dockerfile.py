from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


def test_root_dockerfile_copies_openhire_package_not_legacy_nanobot() -> None:
    dockerfile = (ROOT / "Dockerfile").read_text(encoding="utf-8")

    assert "COPY openhire/ openhire/" in dockerfile
    assert "COPY nanobot/ nanobot/" not in dockerfile
    assert "mkdir -p openhire bridge" in dockerfile


def test_entrypoint_uses_openhire_cli_and_config_dir() -> None:
    entrypoint = (ROOT / "entrypoint.sh").read_text(encoding="utf-8")

    assert 'dir="$HOME/.openhire"' in entrypoint
    assert 'if [ "$1" = "gateway" ] && [ ! -f "$dir/config.json" ]; then' in entrypoint
    assert '"model": "ollama/llama3.2"' in entrypoint
    assert "exec openhire \"$@\"" in entrypoint
    assert "exec nanobot" not in entrypoint


def test_root_dockerfile_starts_long_running_modelscope_gateway() -> None:
    dockerfile = (ROOT / "Dockerfile").read_text(encoding="utf-8")

    assert 'EXPOSE 7860' in dockerfile
    assert 'OPENHIRE_DEPLOY_TARGET=modelscope' in dockerfile
    assert 'CMD ["gateway", "--host", "0.0.0.0", "--port", "7860"]' in dockerfile
    assert 'CMD ["status"]' not in dockerfile
