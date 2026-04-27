"""Case carousel catalog and import helpers for the admin UI."""

from __future__ import annotations

import json
import re
from collections.abc import Mapping
from pathlib import Path
from typing import Any

from loguru import logger

from openhire.adapters import build_default_registry
from openhire.skill_catalog import SkillCatalogService, ensure_skill_frontmatter
from openhire.workforce.employee_prompt import compose_case_bootstrap_files
from openhire.workforce.lifecycle import AgentLifecycle
from openhire.workforce.registry import AgentEntry, AgentRegistry
from openhire.workforce.required_skill import REQUIRED_EMPLOYEE_SKILL_ID, apply_required_employee_skill_contract
from openhire.workforce.workspace import (
    EMPLOYEE_CONFIG_FILES,
    employee_workspace_path,
    read_employee_config_file,
    write_employee_config_file,
)

_CASE_KEY_RE = re.compile(r"[^a-z0-9_-]+")
_BUILTIN_CASES_FILE = Path(__file__).with_name("cases.json")


class CaseCatalogError(ValueError):
    """Raised when ``cases.json`` cannot be loaded or normalized."""


class CaseNotFoundError(CaseCatalogError):
    """Raised when a requested case id is missing."""


class CaseCatalogStore:
    """Persist admin case catalog data to ``workspace/openhire/cases.json``."""

    def __init__(self, workspace: Path) -> None:
        self._dir = workspace / "openhire"
        self._file = self._dir / "cases.json"
        self._seed_builtin_cases()

    @property
    def file(self) -> Path:
        return self._file

    def _seed_builtin_cases(self) -> None:
        if self._file.exists() or not _BUILTIN_CASES_FILE.is_file():
            return
        try:
            self._dir.mkdir(parents=True, exist_ok=True)
            self._file.write_bytes(_BUILTIN_CASES_FILE.read_bytes())
            logger.info("Seeded case catalog from {} to {}", _BUILTIN_CASES_FILE, self._file)
        except OSError as exc:
            logger.warning("Failed to seed case catalog from {} to {}: {}", _BUILTIN_CASES_FILE, self._file, exc)

    def load(self) -> dict[str, Any]:
        if not self._file.exists():
            return {"cases": [], "missing": True}
        try:
            payload = json.loads(self._file.read_text(encoding="utf-8"))
        except json.JSONDecodeError as exc:
            raise CaseCatalogError(f"Invalid cases.json: {exc.msg}") from exc
        except OSError as exc:
            raise CaseCatalogError(f"Failed to read cases.json: {exc}") from exc

        if isinstance(payload, list):
            payload = {"cases": payload}
        if not isinstance(payload, dict):
            raise CaseCatalogError("cases.json must be an object or an array.")
        return payload


class CaseCatalogService:
    """Read and normalize case packages for carousel display."""

    def __init__(self, store: CaseCatalogStore) -> None:
        self._store = store

    @property
    def source_file(self) -> Path:
        return self._store.file

    def list_cases(self) -> list[dict[str, Any]]:
        payload = self._store.load()
        records = payload.get("cases", [])
        if not isinstance(records, list):
            raise CaseCatalogError("cases.json field 'cases' must be an array.")
        return [self._normalize_case(record, index) for index, record in enumerate(records)]

    def get_case(self, case_id: str) -> dict[str, Any]:
        normalized_id = _text(case_id)
        for case in self.list_cases():
            if case["id"] == normalized_id:
                return case
        raise CaseNotFoundError(f"Case '{normalized_id}' not found.")

    def normalize_import_payload(self, payload: Any) -> dict[str, Any]:
        record = payload
        if isinstance(payload, Mapping):
            if "case" in payload:
                record = payload.get("case")
            elif "cases" in payload:
                cases = payload.get("cases")
                if not isinstance(cases, list) or len(cases) != 1:
                    raise CaseCatalogError("Imported config must contain exactly one case.")
                record = cases[0]
        elif isinstance(payload, list):
            if len(payload) != 1:
                raise CaseCatalogError("Imported config must contain exactly one case.")
            record = payload[0]
        return self._normalize_case(record, 0)

    def list_summaries(
        self,
        registry: AgentRegistry,
        skill_catalog: SkillCatalogService,
    ) -> list[dict[str, Any]]:
        return [
            self._case_summary(case, registry=registry, skill_catalog=skill_catalog)
            for case in self.list_cases()
        ]

    def _case_summary(
        self,
        case: dict[str, Any],
        *,
        registry: AgentRegistry,
        skill_catalog: SkillCatalogService,
    ) -> dict[str, Any]:
        imported_employee_count = sum(
            1
            for employee in case["employees"]
            if _find_case_employee(registry, case["id"], employee["key"]) is not None
        )
        imported_skill_count = sum(1 for skill in case["skills"] if _find_case_skill(skill_catalog, skill) is not None)
        return {
            "id": case["id"],
            "title": case["title"],
            "subtitle": case["subtitle"],
            "description": case["description"],
            "tags": list(case["tags"]),
            "metrics": list(case["metrics"]),
            "employee_count": len(case["employees"]),
            "skill_count": len(case["skills"]),
            "imported_employee_count": imported_employee_count,
            "imported_skill_count": imported_skill_count,
            "is_imported": (
                bool(case["employees"])
                and imported_employee_count == len(case["employees"])
                and imported_skill_count == len(case["skills"])
            ),
        }

    def _normalize_case(self, record: Any, index: int) -> dict[str, Any]:
        if not isinstance(record, Mapping):
            raise CaseCatalogError(f"Case at index {index} must be an object.")
        case_id = _slug(record.get("id") or record.get("key") or record.get("title"), f"case-{index + 1}")
        title = _text(record.get("title") or record.get("name"), f"Case {index + 1}")
        skills = [
            self._normalize_skill(case_id, item, skill_index)
            for skill_index, item in enumerate(_list(record.get("skills")))
        ]
        employees = [
            self._normalize_employee(item, employee_index)
            for employee_index, item in enumerate(_list(record.get("employees")))
        ]
        if not employees:
            raise CaseCatalogError(f"Case '{case_id}' must include at least one employee.")
        return {
            "id": case_id,
            "title": title,
            "subtitle": _text(record.get("subtitle"), ""),
            "description": _text(record.get("description"), ""),
            "tags": _string_list(record.get("tags")),
            "metrics": _list(record.get("metrics")),
            "input": record.get("input") if isinstance(record.get("input"), Mapping) else {},
            "output": record.get("output") if isinstance(record.get("output"), Mapping) else {},
            "workflow": _list(record.get("workflow")),
            "skills": skills,
            "employees": employees,
        }

    def _normalize_skill(self, case_id: str, record: Any, index: int) -> dict[str, Any]:
        if not isinstance(record, Mapping):
            raise CaseCatalogError(f"Skill at index {index} in case '{case_id}' must be an object.")
        key = _slug(record.get("key") or record.get("id") or record.get("external_id") or record.get("name"), f"skill-{index + 1}")
        name = _text(record.get("name"), key)
        source = _text(record.get("source"), "local").lower()
        external_id = _text(
            record.get("external_id"),
            f"{case_id}:{key}" if source in {"local", "case"} else "",
        )
        return {
            "key": key,
            "source": source,
            "external_id": external_id,
            "name": name,
            "description": _text(record.get("description"), ""),
            "version": _text(record.get("version"), "1.0.0"),
            "author": _text(record.get("author"), "OpenHire"),
            "license": _text(record.get("license"), ""),
            "source_url": _text(record.get("source_url"), ""),
            "safety_status": _text(record.get("safety_status"), ""),
            "markdown": _text(
                record.get("markdown"),
                "" if source == "clawhub" else _default_skill_markdown(name),
            ),
            "tags": ["case", f"case:{case_id}", *_string_list(record.get("tags"))],
        }

    def _normalize_employee(self, record: Any, index: int) -> dict[str, Any]:
        if not isinstance(record, Mapping):
            raise CaseCatalogError(f"Employee at index {index} must be an object.")
        key = _slug(record.get("key") or record.get("id") or record.get("name"), f"employee-{index + 1}")
        name = _text(record.get("name"), key)
        config_files = _config_files(record.get("config_files") or record.get("configFiles"))
        return {
            "key": key,
            "name": name,
            "avatar": _text(record.get("avatar"), ""),
            "role": _text(record.get("role"), ""),
            "agent_type": _text(record.get("agent_type") or record.get("agentType"), "nanobot"),
            "skills": _string_list(record.get("skills")),
            "skill_keys": [
                _slug(item, f"skill-{skill_index + 1}")
                for skill_index, item in enumerate(_string_list(record.get("skill_keys") or record.get("skillKeys")))
            ],
            "system_prompt": _text(record.get("system_prompt") or record.get("systemPrompt"), ""),
            "agent_config": dict(record.get("agent_config") or record.get("agentConfig") or {}),
            "tools": _string_list(record.get("tools")),
            "config_files": config_files,
        }


class CaseImportService:
    """Preview and import a normalized case into OpenHire employees and skills."""

    def __init__(
        self,
        *,
        workspace: Path,
        registry: AgentRegistry,
        lifecycle: AgentLifecycle,
        skill_catalog: SkillCatalogService,
        skill_provider: Any | None = None,
        case_catalog: CaseCatalogService | None = None,
    ) -> None:
        self._workspace = workspace
        self._registry = registry
        self._lifecycle = lifecycle
        self._skill_catalog = skill_catalog
        self._skill_provider = skill_provider
        self._case_catalog = case_catalog
        self._valid_agent_types = set(build_default_registry().names())

    def preview(self, case: dict[str, Any]) -> dict[str, Any]:
        skill_preview = [self._preview_skill(case["id"], skill) for skill in case["skills"]]
        employee_preview = [
            self._preview_employee(case, employee)
            for employee in case["employees"]
        ]
        return {
            "case": {
                "id": case["id"],
                "title": case["title"],
                "employee_count": len(case["employees"]),
                "skill_count": len(case["skills"]),
            },
            "skills": skill_preview,
            "employees": employee_preview,
            "overwrite_count": sum(
                1
                for employee in employee_preview
                for file in employee["config_files"]
                if file["action"] == "overwrite"
            ),
        }

    def export_case_for_employees(self, employee_ids: list[str]) -> dict[str, Any]:
        entries = self._resolve_export_entries(employee_ids)
        skill_rows, skill_keys_by_id = self._export_skills(entries)
        employee_rows = self._export_employees(entries, skill_keys_by_id)
        return {
            **self._default_export_case(entries),
            "skills": skill_rows,
            "employees": employee_rows,
        }

    async def import_case(self, case: dict[str, Any]) -> dict[str, Any]:
        skill_records = await self._prepare_skill_records(case["skills"])
        skill_entries = self._skill_catalog.upsert_many(skill_records)
        skill_ids_by_key = {
            skill["key"]: entry.id
            for skill, entry in zip(skill_records, skill_entries, strict=False)
        }
        skill_names_by_key = {skill["key"]: skill["name"] for skill in skill_records}
        employee_results: list[dict[str, Any]] = []

        for employee in case["employees"]:
            try:
                result = await self._import_employee(
                    case,
                    employee,
                    skill_ids_by_key=skill_ids_by_key,
                    skill_names_by_key=skill_names_by_key,
                )
            except Exception as exc:
                logger.exception("Failed to import case employee {} from {}", employee["key"], case["id"])
                result = {
                    "key": employee["key"],
                    "name": employee["name"],
                    "action": "failed",
                    "error": str(exc),
                }
            employee_results.append(result)

        failed = [item for item in employee_results if item["action"] == "failed"]
        return {
            "case": {"id": case["id"], "title": case["title"]},
            "status": "partial" if failed else "ok",
            "skills": [
                {
                    "key": skill["key"],
                    "id": skill_ids_by_key.get(skill["key"], ""),
                    "name": skill["name"],
                    "source": skill["source"],
                }
                for skill in skill_records
            ],
            "employees": employee_results,
            "failed_count": len(failed),
        }

    def _preview_skill(self, case_id: str, skill: dict[str, Any]) -> dict[str, Any]:
        existing = _find_case_skill(self._skill_catalog, skill)
        return {
            "key": skill["key"],
            "name": skill["name"],
            "source": skill["source"],
            "action": "update" if existing else "create",
            "existing_id": existing.id if existing else "",
        }

    async def _prepare_skill_records(self, skills: list[dict[str, Any]]) -> list[dict[str, Any]]:
        records: list[dict[str, Any]] = []
        for skill in skills:
            record = dict(skill)
            if (
                record.get("source") == "clawhub"
                and record.get("source_url")
                and not record.get("markdown")
            ):
                fetch = getattr(self._skill_provider, "fetch_skill_markdown", None)
                if fetch:
                    record["markdown"] = await fetch(str(record["source_url"]))
            # Some packaged SKILL.md files ship without YAML frontmatter;
            # synthesize one from the case metadata so downstream upsert paths
            # can still extract name/description reliably.
            if record.get("markdown"):
                record["markdown"] = ensure_skill_frontmatter(str(record["markdown"]), record)
            records.append(record)
        return records

    def _resolve_export_entries(self, employee_ids: list[str]) -> list[AgentEntry]:
        entries: list[AgentEntry] = []
        seen: set[str] = set()
        for employee_id in employee_ids:
            normalized_id = _text(employee_id)
            if not normalized_id or normalized_id in seen:
                continue
            seen.add(normalized_id)
            entry = self._registry.get(normalized_id)
            if entry is None:
                raise CaseCatalogError(f"Employee '{normalized_id}' not found.")
            entries.append(entry)
        if not entries:
            raise CaseCatalogError("At least one persisted employee is required for export.")
        return entries

    def _default_export_case(self, entries: list[AgentEntry]) -> dict[str, Any]:
        referenced_case = self._shared_export_case(entries)
        entry_names = [_text(entry.name, "employee") for entry in entries]
        if referenced_case is not None:
            case_id = referenced_case["id"]
            title = referenced_case["title"]
            subtitle = referenced_case["subtitle"]
            description = referenced_case["description"]
        else:
            default_case_id = self._default_export_case_id(entries)
            case_id = default_case_id
            title = self._default_export_case_title(entries)
            subtitle = "Exported employee bundle"
            description = f"Exported from {len(entries)} selected employees: {', '.join(entry_names[:3])}"
            if len(entry_names) > 3:
                description = f"{description}, and {len(entry_names) - 3} more."
            else:
                description = f"{description}."
        return {
            "id": case_id,
            "title": title,
            "subtitle": subtitle,
            "description": description,
            "tags": [],
            "metrics": [],
            "input": {},
            "output": {},
            "workflow": [],
        }

    def _shared_export_case(self, entries: list[AgentEntry]) -> dict[str, Any] | None:
        if not self._case_catalog:
            return None
        shared_case_id = self._shared_export_case_id(entries)
        if not shared_case_id:
            return None
        try:
            case = self._case_catalog.get_case(shared_case_id)
        except CaseCatalogError:
            return {
                "id": shared_case_id,
                "title": _humanize_slug(shared_case_id),
                "subtitle": "",
                "description": "",
            }
        return {
            "id": case["id"],
            "title": case["title"],
            "subtitle": case["subtitle"],
            "description": case["description"],
        }

    def _shared_export_case_id(self, entries: list[AgentEntry]) -> str:
        case_ids: list[str] = []
        for entry in entries:
            marker = _case_import_marker(entry)
            case_id = _text(marker.get("case_id"))
            if not case_id:
                return ""
            case_ids.append(case_id)
        if not case_ids:
            return ""
        first_case_id = case_ids[0]
        return first_case_id if all(case_id == first_case_id for case_id in case_ids) else ""

    def _default_export_case_id(self, entries: list[AgentEntry]) -> str:
        shared_case_id = self._shared_export_case_id(entries)
        if shared_case_id:
            return shared_case_id
        first_key = self._default_export_employee_key(entries[0])
        if len(entries) == 1:
            return _slug(first_key, "employee-export")
        return _slug(f"{first_key}-bundle", "employee-export")

    def _default_export_case_title(self, entries: list[AgentEntry]) -> str:
        if len(entries) == 1:
            return f"{_text(entries[0].name, 'Employee')} Export"
        return f"{_text(entries[0].name, 'Employee')} 等 {len(entries)} 位员工"

    def _export_skills(self, entries: list[AgentEntry]) -> tuple[list[dict[str, Any]], dict[str, str]]:
        ordered_skill_ids = self._ordered_export_skill_ids(entries)
        if not ordered_skill_ids:
            return [], {}
        skill_entries = self._skill_catalog.get_by_ids(ordered_skill_ids)
        used_keys: set[str] = set()
        skill_rows: list[dict[str, Any]] = []
        skill_keys_by_id: dict[str, str] = {}
        for skill in skill_entries:
            if skill.id == REQUIRED_EMPLOYEE_SKILL_ID:
                continue
            key = _unique_slug(_export_skill_key(skill.to_public_dict()), used_keys, "skill")
            used_keys.add(key)
            content = self._skill_catalog.get_content(skill.id) or {}
            public = skill.to_public_dict()
            skill_rows.append({
                "key": key,
                "source": public["source"],
                "external_id": public["external_id"],
                "name": public["name"],
                "description": public["description"],
                "version": public["version"],
                "author": public["author"],
                "license": public["license"],
                "source_url": public["source_url"],
                "safety_status": public["safety_status"],
                "markdown": _text(content.get("markdown")),
                "tags": list(public.get("tags") or []),
            })
            skill_keys_by_id[skill.id] = key
        return skill_rows, skill_keys_by_id

    def _ordered_export_skill_ids(self, entries: list[AgentEntry]) -> list[str]:
        skill_ids: list[str] = []
        seen: set[str] = set()
        for entry in entries:
            for skill_id in list(entry.skill_ids or []):
                normalized_id = _text(skill_id)
                if (
                    not normalized_id
                    or normalized_id == REQUIRED_EMPLOYEE_SKILL_ID
                    or normalized_id in seen
                ):
                    continue
                seen.add(normalized_id)
                skill_ids.append(normalized_id)
        return skill_ids

    def _export_employees(
        self,
        entries: list[AgentEntry],
        skill_keys_by_id: dict[str, str],
    ) -> list[dict[str, Any]]:
        used_keys: set[str] = set()
        rows: list[dict[str, Any]] = []
        for entry in entries:
            employee_key = _unique_slug(self._default_export_employee_key(entry), used_keys, "employee")
            used_keys.add(employee_key)
            rows.append({
                "key": employee_key,
                "name": entry.name,
                "avatar": entry.avatar,
                "role": entry.role,
                "agent_type": entry.agent_type,
                "skill_keys": [
                    skill_keys_by_id[skill_id]
                    for skill_id in list(entry.skill_ids or [])
                    if skill_id in skill_keys_by_id
                ],
                "system_prompt": entry.system_prompt,
                "agent_config": _clean_export_agent_config(entry.agent_config),
                "tools": _string_list(list(entry.tools or [])),
                "config_files": {
                    filename: _text(read_employee_config_file(self._workspace, entry, filename).get("content"))
                    for filename in EMPLOYEE_CONFIG_FILES
                },
            })
        return rows

    @staticmethod
    def _default_export_employee_key(entry: AgentEntry) -> str:
        marker = _case_import_marker(entry)
        return _text(marker.get("employee_key"), _slug(entry.name or entry.agent_id, "employee"))

    def _preview_employee(self, case: dict[str, Any], employee: dict[str, Any]) -> dict[str, Any]:
        existing = _find_case_employee(self._registry, case["id"], employee["key"])
        return {
            "key": employee["key"],
            "name": employee["name"],
            "agent_type": employee["agent_type"],
            "action": "update" if existing else "create",
            "existing_id": existing.agent_id if existing else "",
            "skill_keys": list(employee["skill_keys"]),
            "config_files": self._preview_config_files(existing, employee),
        }

    def _preview_config_files(
        self,
        existing: AgentEntry | None,
        employee: dict[str, Any],
    ) -> list[dict[str, str]]:
        rows: list[dict[str, str]] = []
        for filename, content in self._resolved_employee_config_files(employee).items():
            action = "create"
            if existing is not None:
                path = employee_workspace_path(self._workspace, existing) / filename
                if path.exists():
                    try:
                        current = path.read_text(encoding="utf-8")
                    except OSError:
                        current = ""
                    action = "unchanged" if current == content else "overwrite"
            rows.append({"name": filename, "action": action})
        return rows

    async def _import_employee(
        self,
        case: dict[str, Any],
        employee: dict[str, Any],
        *,
        skill_ids_by_key: dict[str, str],
        skill_names_by_key: dict[str, str],
    ) -> dict[str, Any]:
        if employee["agent_type"] not in self._valid_agent_types:
            raise ValueError(
                f"Invalid agent_type '{employee['agent_type']}'. Allowed: {', '.join(sorted(self._valid_agent_types))}"
            )

        skill_ids = [
            skill_ids_by_key[key]
            for key in employee["skill_keys"]
            if key in skill_ids_by_key
        ]
        skill_names = [
            skill_names_by_key[key]
            for key in employee["skill_keys"]
            if key in skill_names_by_key
        ] or list(employee["skills"])
        resolved_files = self._resolved_employee_config_files(employee)
        system_prompt = employee["system_prompt"] or _text(resolved_files.get("SOUL.md"), employee["role"])
        agent_config = {
            **dict(employee["agent_config"]),
            "case_import": {
                "case_id": case["id"],
                "employee_key": employee["key"],
            },
        }
        existing = _find_case_employee(self._registry, case["id"], employee["key"])
        action = "created"
        if existing is None:
            entry = await self._lifecycle.create_agent(
                name=employee["name"],
                avatar=employee["avatar"],
                role=employee["role"],
                agent_type=employee["agent_type"],
                skills=skill_names,
                skill_ids=skill_ids,
                system_prompt=system_prompt,
                agent_config=agent_config,
                tools=employee["tools"],
                bootstrap_files=resolved_files,
            )
        else:
            updated_skills, updated_skill_ids, updated_prompt = apply_required_employee_skill_contract(
                skills=skill_names,
                skill_ids=skill_ids,
                system_prompt=system_prompt,
            )
            entry = self._registry.update(
                existing.agent_id,
                name=employee["name"],
                avatar=employee["avatar"],
                role=employee["role"],
                agent_type=employee["agent_type"],
                skills=updated_skills,
                skill_ids=updated_skill_ids,
                system_prompt=updated_prompt,
                agent_config=agent_config,
                tools=employee["tools"],
            )
            if entry is None:
                raise ValueError(f"Employee '{existing.agent_id}' disappeared during import.")
            action = "updated"

        written_files = [
            write_employee_config_file(self._workspace, entry, filename, content)
            for filename, content in resolved_files.items()
        ]
        return {
            "key": employee["key"],
            "id": entry.agent_id,
            "name": entry.name,
            "action": action,
            "config_files": [file["name"] for file in written_files],
        }

    @staticmethod
    def _resolved_employee_config_files(employee: dict[str, Any]) -> dict[str, str]:
        return compose_case_bootstrap_files(employee.get("config_files"))


def _find_case_skill(skill_catalog: SkillCatalogService, expected: Mapping[str, Any]) -> Any | None:
    expected_identity = _skill_identity(expected)
    for skill in skill_catalog.list():
        if _skill_identity(skill.to_public_dict()) == expected_identity:
            return skill
    return None


def _find_case_employee(
    registry: AgentRegistry,
    case_id: str,
    employee_key: str,
) -> AgentEntry | None:
    for entry in registry.all():
        agent_config = entry.agent_config if isinstance(entry.agent_config, Mapping) else {}
        marker = agent_config.get("case_import")
        if not isinstance(marker, Mapping):
            continue
        if marker.get("case_id") == case_id and marker.get("employee_key") == employee_key:
            return entry
    return None


def _config_files(value: Any) -> dict[str, str]:
    if not isinstance(value, Mapping):
        return {}
    files: dict[str, str] = {}
    for filename in EMPLOYEE_CONFIG_FILES:
        if filename in value:
            files[filename] = str(value.get(filename) or "")
    return files


def _skill_identity(record: Mapping[str, Any]) -> tuple[str, str]:
    source = _text(record.get("source"))
    external_id = _text(record.get("external_id"))
    source_url = _text(record.get("source_url"))
    if source == "web":
        return source, source_url or external_id
    return source, external_id or source_url


def _case_import_marker(entry: AgentEntry) -> Mapping[str, Any]:
    marker = entry.agent_config.get("case_import") if isinstance(entry.agent_config, Mapping) else {}
    return marker if isinstance(marker, Mapping) else {}


def _clean_export_agent_config(value: Any) -> dict[str, Any]:
    if not isinstance(value, Mapping):
        return {}
    result = dict(value)
    result.pop("case_import", None)
    return result


def _export_skill_key(record: Mapping[str, Any]) -> str:
    source = _text(record.get("source"))
    external_id = _text(record.get("external_id"))
    if source in {"local", "case"} and ":" in external_id:
        external_id = external_id.rsplit(":", 1)[-1]
    if external_id:
        return _slug(external_id, "skill")
    return _slug(record.get("name") or record.get("source_url"), "skill")


def _unique_slug(value: Any, seen: set[str], fallback: str) -> str:
    base = _slug(value, fallback)
    if base not in seen:
        return base
    index = 2
    while f"{base}-{index}" in seen:
        index += 1
    return f"{base}-{index}"


def _humanize_slug(value: str) -> str:
    parts = [part for part in re.split(r"[-_]+", _text(value)) if part]
    if not parts:
        return "Exported Case"
    return " ".join(part.capitalize() for part in parts)


def _default_skill_markdown(name: str) -> str:
    return f"---\nname: {name}\ndescription: Case-imported OpenHire skill.\n---\n\n# {name}\n"


def _text(value: Any, fallback: str = "") -> str:
    if value is None:
        return fallback
    text = str(value).strip()
    return text if text else fallback


def _list(value: Any) -> list[Any]:
    return value if isinstance(value, list) else []


def _string_list(value: Any) -> list[str]:
    if isinstance(value, str):
        raw_items = value.split(",")
    elif isinstance(value, list):
        raw_items = value
    else:
        raw_items = []
    result: list[str] = []
    seen: set[str] = set()
    for item in raw_items:
        normalized = _text(item)
        lowered = normalized.lower()
        if not normalized or lowered in seen:
            continue
        seen.add(lowered)
        result.append(normalized)
    return result


def _slug(value: Any, fallback: str = "case") -> str:
    raw = _text(value, fallback).lower().replace(" ", "-")
    slug = _CASE_KEY_RE.sub("-", raw).strip("-_")
    return slug or fallback
