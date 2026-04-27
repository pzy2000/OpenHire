"""JSON file store for OpenHire digital employee data."""

import json
from pathlib import Path
from typing import Any

from loguru import logger


class OpenHireStore:
    """Persist digital employee data to ``workspace/openhire/agents.json``."""

    def __init__(self, workspace: Path) -> None:
        self._dir = workspace / "openhire"
        self._file = self._dir / "agents.json"

    def version(self) -> tuple[int, int] | None:
        """Return a cheap file version marker for cache invalidation."""
        try:
            stat = self._file.stat()
        except OSError:
            return None
        return stat.st_mtime_ns, stat.st_size

    def load(self) -> dict[str, Any]:
        if not self._file.exists():
            return {"agents": {}}
        try:
            return json.loads(self._file.read_text(encoding="utf-8"))
        except (json.JSONDecodeError, OSError) as e:
            logger.warning("Failed to load OpenHire store: {}", e)
            return {"agents": {}}

    def save(self, data: dict[str, Any]) -> None:
        self._dir.mkdir(parents=True, exist_ok=True)
        tmp = self._file.with_suffix(".tmp")
        tmp.write_text(json.dumps(data, indent=2, ensure_ascii=False), encoding="utf-8")
        tmp.replace(self._file)
