"""Persisted custom employee template primitives for the admin UI."""

from __future__ import annotations

import json
import uuid
from collections.abc import Mapping
from dataclasses import asdict, dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from loguru import logger

PROTECTED_TEMPLATE_IDS = {"custom-role"}


def _now() -> str:
    return datetime.now(timezone.utc).isoformat(timespec="seconds")


@dataclass
class EmployeeTemplateEntry:
    """Persisted custom employee template."""

    id: str = ""
    default_name: str = ""
    role: str = ""
    default_agent_type: str = "openclaw"
    company_style: str = ""
    summary: str = ""
    created_at: str = field(default_factory=_now)
    updated_at: str = field(default_factory=_now)

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)

    def to_public_dict(self) -> dict[str, str]:
        return {
            "id": self.id,
            "defaultName": self.default_name,
            "role": self.role,
            "defaultAgentType": self.default_agent_type,
            "companyStyle": self.company_style,
            "summary": self.summary,
            "createdAt": self.created_at,
            "updatedAt": self.updated_at,
        }

    @classmethod
    def from_dict(cls, data: Mapping[str, Any]) -> EmployeeTemplateEntry:
        known = {f.name for f in cls.__dataclass_fields__.values()}
        return cls(**{k: v for k, v in data.items() if k in known})


class EmployeeTemplateStore:
    """Persist custom employee templates to ``workspace/openhire/employee_templates.json``."""

    def __init__(self, workspace: Path) -> None:
        self._dir = workspace / "openhire"
        self._file = self._dir / "employee_templates.json"

    def load(self) -> dict[str, Any]:
        if not self._file.exists():
            return {"templates": {}}
        try:
            return json.loads(self._file.read_text(encoding="utf-8"))
        except (json.JSONDecodeError, OSError) as exc:
            logger.warning("Failed to load employee template store: {}", exc)
            return {"templates": {}}

    def save(self, data: dict[str, Any]) -> None:
        self._dir.mkdir(parents=True, exist_ok=True)
        tmp = self._file.with_suffix(".tmp")
        tmp.write_text(json.dumps(data, indent=2, ensure_ascii=False), encoding="utf-8")
        tmp.replace(self._file)


class EmployeeTemplateService:
    """Manage persisted custom employee templates."""

    def __init__(self, store: EmployeeTemplateStore) -> None:
        self._store = store
        self._cache: dict[str, EmployeeTemplateEntry] | None = None
        self._hidden_template_ids: set[str] | None = None

    def _load(self) -> dict[str, EmployeeTemplateEntry]:
        if self._cache is None:
            data = self._store.load()
            self._cache = {
                key: EmployeeTemplateEntry.from_dict(value)
                for key, value in data.get("templates", {}).items()
                if isinstance(value, Mapping)
            }
            self._hidden_template_ids = {
                str(item or "").strip()
                for item in data.get("hidden_template_ids", [])
                if str(item or "").strip() and str(item or "").strip() not in PROTECTED_TEMPLATE_IDS
            }
        return self._cache

    def _hidden_ids(self) -> set[str]:
        self._load()
        if self._hidden_template_ids is None:
            self._hidden_template_ids = set()
        return self._hidden_template_ids

    def _save(self) -> None:
        entries = self._load()
        self._store.save(
            {
                "templates": {key: value.to_dict() for key, value in entries.items()},
                "hidden_template_ids": sorted(self._hidden_ids()),
            }
        )

    def list(self) -> list[EmployeeTemplateEntry]:
        return list(self._load().values())

    def hidden_template_ids(self) -> list[str]:
        return sorted(self._hidden_ids())

    def is_protected(self, template_id: str) -> bool:
        return str(template_id or "").strip() in PROTECTED_TEMPLATE_IDS

    def upsert(self, record: Mapping[str, Any]) -> EmployeeTemplateEntry:
        normalized = self._normalize_record(record)
        entries = self._load()
        entry_id = normalized["id"]
        existing = entries.get(entry_id) if entry_id else None
        if existing is None:
            existing = self._find_matching_entry(
                role=normalized["role"],
                default_agent_type=normalized["default_agent_type"],
                summary=normalized["summary"],
            )
        if existing is None:
            existing = EmployeeTemplateEntry(id=entry_id or str(uuid.uuid4())[:8])
            entries[existing.id] = existing
            existing.created_at = _now()
        existing.default_name = normalized["default_name"]
        existing.role = normalized["role"]
        existing.default_agent_type = normalized["default_agent_type"]
        existing.company_style = normalized["company_style"]
        existing.summary = normalized["summary"]
        existing.updated_at = _now()
        self._hidden_ids().discard(existing.id)
        self._save()
        return existing

    def delete(self, template_id: str) -> bool:
        normalized_id = str(template_id or "").strip()
        if not normalized_id:
            return False
        if self.is_protected(normalized_id):
            return False
        entries = self._load()
        removed = False
        if normalized_id in entries:
            del entries[normalized_id]
            removed = True
        else:
            self._hidden_ids().add(normalized_id)
            removed = True
        if removed:
            self._save()
        return removed

    def _find_matching_entry(
        self,
        *,
        role: str,
        default_agent_type: str,
        summary: str,
    ) -> EmployeeTemplateEntry | None:
        for entry in self._load().values():
            if (
                entry.role == role
                and entry.default_agent_type == default_agent_type
                and entry.summary == summary
            ):
                return entry
        return None

    @staticmethod
    def _normalize_record(record: Mapping[str, Any]) -> dict[str, str]:
        def text(value: Any) -> str:
            return str(value or "").strip()

        return {
            "id": text(record.get("id")),
            "default_name": text(record.get("defaultName") or record.get("default_name")),
            "role": text(record.get("role")),
            "default_agent_type": text(record.get("defaultAgentType") or record.get("default_agent_type") or "openclaw"),
            "company_style": text(record.get("companyStyle") or record.get("company_style")),
            "summary": text(record.get("summary")),
        }
