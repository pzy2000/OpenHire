"""Per-employee workspace helpers."""

from __future__ import annotations

from importlib.resources import files as pkg_files
from pathlib import Path
from typing import Any

EMPLOYEE_CONFIG_FILES = ("SOUL.md", "AGENTS.md", "HEARTBEAT.md", "TOOLS.md", "USER.md")
_TEMPLATE_FILES = {"SOUL.md", "AGENTS.md", "TOOLS.md"}
_EMPTY_FILES = {"HEARTBEAT.md", "USER.md"}


def employee_workspace_path(workspace: Path, employee: Any | str) -> Path:
    """Return the isolated workspace path for a digital employee."""
    employee_id = str(getattr(employee, "agent_id", employee) or "").strip()
    return workspace / "openhire" / "employees" / employee_id / "workspace"


def is_employee_config_file(filename: str) -> bool:
    return filename in EMPLOYEE_CONFIG_FILES


def _template_text(filename: str) -> str:
    try:
        template = pkg_files("openhire") / "templates" / filename
        return template.read_text(encoding="utf-8")
    except Exception:
        return ""


def default_employee_config_text(filename: str) -> str:
    if filename in _TEMPLATE_FILES:
        return _template_text(filename)
    return ""


def ensure_employee_workspace_dir(workspace: Path, entry: Any) -> Path:
    employee_workspace = employee_workspace_path(workspace, entry)
    employee_workspace.mkdir(parents=True, exist_ok=True)
    return employee_workspace


def initialize_employee_workspace(workspace: Path, entry: Any) -> Path:
    """Create missing per-employee bootstrap files without overwriting edits."""
    employee_workspace = ensure_employee_workspace_dir(workspace, entry)

    for filename in EMPLOYEE_CONFIG_FILES:
        path = employee_workspace / filename
        if path.exists():
            continue
        if filename in _EMPTY_FILES:
            content = ""
        else:
            content = default_employee_config_text(filename)
        path.write_text(content, encoding="utf-8")

    return employee_workspace


def write_employee_bootstrap_files(
    workspace: Path,
    entry: Any,
    files: dict[str, str],
) -> Path:
    """Write initial bootstrap files for a newly-created employee workspace."""
    employee_workspace = ensure_employee_workspace_dir(workspace, entry)
    for filename in EMPLOYEE_CONFIG_FILES:
        path = employee_workspace / filename
        if filename in files:
            path.write_text(str(files[filename] or ""), encoding="utf-8")
            continue
        if path.exists():
            continue
        if filename in _EMPTY_FILES:
            content = ""
        else:
            content = default_employee_config_text(filename)
        path.write_text(str(content or ""), encoding="utf-8")
    return employee_workspace


def read_employee_config_file(workspace: Path, entry: Any, filename: str) -> dict[str, str | bool]:
    if not is_employee_config_file(filename):
        raise ValueError(f"Unsupported employee config file '{filename}'.")
    employee_workspace = initialize_employee_workspace(workspace, entry)
    path = employee_workspace / filename
    return {
        "name": filename,
        "content": path.read_text(encoding="utf-8") if path.exists() else "",
        "exists": path.exists(),
    }


def write_employee_config_file(workspace: Path, entry: Any, filename: str, content: str) -> dict[str, str | bool]:
    if not is_employee_config_file(filename):
        raise ValueError(f"Unsupported employee config file '{filename}'.")
    employee_workspace = initialize_employee_workspace(workspace, entry)
    path = employee_workspace / filename
    path.write_text(content, encoding="utf-8")
    return {
        "name": filename,
        "content": content,
        "exists": True,
    }
