"""
OpenHire - Digital Employee Orchestration Platform
"""

from importlib.metadata import PackageNotFoundError, version as _pkg_version
from pathlib import Path
import tomllib


def _read_pyproject_version() -> str | None:
    """Read the source-tree version when package metadata is unavailable."""
    pyproject = Path(__file__).resolve().parent.parent / "pyproject.toml"
    if not pyproject.exists():
        return None
    data = tomllib.loads(pyproject.read_text(encoding="utf-8"))
    return data.get("project", {}).get("version")


def _resolve_version() -> str:
    try:
        return _pkg_version("openhire")
    except PackageNotFoundError:
        return _read_pyproject_version() or "0.1.5"


__version__ = _resolve_version()
__logo__ = "🚀"
__brand__ = "OpenHire"

from openhire.facade import OpenHire, RunResult

__all__ = ["OpenHire", "RunResult"]
