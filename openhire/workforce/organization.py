"""Organization graph storage, validation, and communication policy."""

from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Iterable, Mapping

from loguru import logger

from openhire.workforce.registry import AgentRegistry

ORGANIZATION_VERSION = 1


def _text(value: Any) -> str:
    return str(value or "").strip()


def _bool(value: Any) -> bool:
    return bool(value) if isinstance(value, bool) else str(value or "").strip().casefold() == "true"


def _number(value: Any) -> int | float | None:
    if value is None or value == "":
        return None
    try:
        parsed = float(value)
    except (TypeError, ValueError):
        return None
    if parsed.is_integer():
        return int(parsed)
    return parsed


def _normalize_employee_ids(employee_ids: Iterable[str] | None) -> set[str] | None:
    if employee_ids is None:
        return None
    return {_text(employee_id) for employee_id in employee_ids if _text(employee_id)}


def _dedupe_preserve_order(items: Iterable[str]) -> list[str]:
    result: list[str] = []
    seen: set[str] = set()
    for item in items:
        text = _text(item)
        if not text or text in seen:
            continue
        seen.add(text)
        result.append(text)
    return result


def normalize_organization_graph(
    data: Mapping[str, Any] | None,
    *,
    employee_ids: Iterable[str] | None = None,
    clean: bool = False,
    default_allow_skip_level_reporting: bool = False,
) -> tuple[dict[str, Any], bool]:
    """Return a normalized organization graph and whether normalization changed it."""

    source = data if isinstance(data, Mapping) else {}
    allowed_ids = _normalize_employee_ids(employee_ids)
    changed = not isinstance(data, Mapping)

    raw_settings = source.get("settings")
    settings_source = raw_settings if isinstance(raw_settings, Mapping) else {}
    settings = {
        "allow_skip_level_reporting": _bool(
            settings_source.get("allow_skip_level_reporting", default_allow_skip_level_reporting)
        )
    }
    if settings_source.get("allow_skip_level_reporting") != settings["allow_skip_level_reporting"]:
        changed = True

    raw_nodes = source.get("nodes")
    node_map: dict[str, dict[str, Any]] = {}
    if isinstance(raw_nodes, list):
        for item in raw_nodes:
            if not isinstance(item, Mapping):
                changed = True
                continue
            employee_id = _text(item.get("employee_id") or item.get("employeeId"))
            if not employee_id:
                changed = True
                continue
            if clean and allowed_ids is not None and employee_id not in allowed_ids:
                changed = True
                continue
            node: dict[str, Any] = {"employee_id": employee_id}
            x = _number(item.get("x"))
            y = _number(item.get("y"))
            if x is not None:
                node["x"] = x
            if y is not None:
                node["y"] = y
            if "allow_skip_level_reporting" in item or "allowSkipLevelReporting" in item:
                node["allow_skip_level_reporting"] = _bool(
                    item.get("allow_skip_level_reporting", item.get("allowSkipLevelReporting"))
                )
            node_map[employee_id] = node
    elif raw_nodes is not None:
        changed = True

    if allowed_ids is not None:
        for employee_id in sorted(allowed_ids):
            node_map.setdefault(employee_id, {"employee_id": employee_id})

    raw_edges = source.get("edges")
    edges: list[dict[str, str]] = []
    seen_edges: set[tuple[str, str]] = set()
    if isinstance(raw_edges, list):
        for item in raw_edges:
            if not isinstance(item, Mapping):
                changed = True
                continue
            reporter_id = _text(item.get("reporter_id") or item.get("reporterId"))
            manager_id = _text(item.get("manager_id") or item.get("managerId"))
            if not reporter_id or not manager_id:
                changed = True
                continue
            if clean and allowed_ids is not None and (reporter_id not in allowed_ids or manager_id not in allowed_ids):
                changed = True
                continue
            key = (reporter_id, manager_id)
            if key in seen_edges:
                changed = True
                continue
            seen_edges.add(key)
            edges.append({"reporter_id": reporter_id, "manager_id": manager_id})
    elif raw_edges is not None:
        changed = True

    graph = {
        "version": ORGANIZATION_VERSION,
        "settings": settings,
        "nodes": list(node_map.values()),
        "edges": edges,
    }
    if source.get("version") != ORGANIZATION_VERSION:
        changed = True
    return graph, changed


class OrganizationStore:
    """Persist organization graph data to ``workspace/openhire/organization.json``."""

    def __init__(self, workspace: Path) -> None:
        self._dir = Path(workspace) / "openhire"
        self._file = self._dir / "organization.json"

    @property
    def path(self) -> Path:
        return self._file

    def load(
        self,
        *,
        employee_ids: Iterable[str] | None = None,
        clean: bool = False,
        default_allow_skip_level_reporting: bool = False,
    ) -> dict[str, Any]:
        data: dict[str, Any] = {}
        if self._file.exists():
            try:
                loaded = json.loads(self._file.read_text(encoding="utf-8"))
                if isinstance(loaded, dict):
                    data = loaded
            except (json.JSONDecodeError, OSError) as exc:
                logger.warning("Failed to load OpenHire organization graph: {}", exc)
        graph, changed = normalize_organization_graph(
            data,
            employee_ids=employee_ids,
            clean=clean,
            default_allow_skip_level_reporting=default_allow_skip_level_reporting,
        )
        if clean and changed and self._file.exists():
            self._write(graph)
        return graph

    def save(
        self,
        graph: Mapping[str, Any],
        *,
        employee_ids: Iterable[str] | None = None,
        default_allow_skip_level_reporting: bool = False,
    ) -> dict[str, Any]:
        normalized, _changed = normalize_organization_graph(
            graph,
            employee_ids=employee_ids,
            clean=False,
            default_allow_skip_level_reporting=default_allow_skip_level_reporting,
        )
        validation = OrganizationValidator.validate(normalized, employee_ids)
        if not validation["valid"]:
            messages = "; ".join(error["message"] for error in validation["errors"])
            raise OrganizationValidationError(messages, validation=validation)
        self._write(normalized)
        return normalized

    def _write(self, graph: Mapping[str, Any]) -> None:
        self._dir.mkdir(parents=True, exist_ok=True)
        tmp = self._file.with_suffix(".tmp")
        tmp.write_text(json.dumps(graph, indent=2, ensure_ascii=False), encoding="utf-8")
        tmp.replace(self._file)


class OrganizationValidationError(ValueError):
    """Raised when an organization graph fails validation."""

    def __init__(self, message: str, *, validation: dict[str, Any]) -> None:
        super().__init__(message)
        self.validation = validation


class OrganizationValidator:
    """Validate OpenHire organization graph invariants."""

    @staticmethod
    def validate(graph: Mapping[str, Any] | None, employee_ids: Iterable[str] | None) -> dict[str, Any]:
        normalized, _changed = normalize_organization_graph(graph, employee_ids=None)
        allowed_ids = _normalize_employee_ids(employee_ids)
        errors: list[dict[str, str]] = []
        warnings: list[dict[str, str]] = []

        node_ids = {_text(node.get("employee_id")) for node in normalized["nodes"] if isinstance(node, Mapping)}
        referenced_ids: set[str] = set()
        manager_by_reporter: dict[str, str] = {}
        children_by_manager: dict[str, list[str]] = {}

        for edge in normalized["edges"]:
            reporter_id = _text(edge.get("reporter_id"))
            manager_id = _text(edge.get("manager_id"))
            referenced_ids.update([reporter_id, manager_id])
            if reporter_id == manager_id:
                errors.append({
                    "code": "self_report",
                    "message": f"Employee '{reporter_id}' cannot report to itself.",
                })
            if allowed_ids is not None:
                for field, employee_id in (("reporter_id", reporter_id), ("manager_id", manager_id)):
                    if employee_id not in allowed_ids:
                        errors.append({
                            "code": "unknown_employee",
                            "message": f"Organization edge references unknown employee '{employee_id}' in {field}.",
                        })
            existing_manager = manager_by_reporter.get(reporter_id)
            if existing_manager and existing_manager != manager_id:
                errors.append({
                    "code": "multiple_managers",
                    "message": f"Employee '{reporter_id}' has multiple managers.",
                })
            manager_by_reporter[reporter_id] = manager_id
            children_by_manager.setdefault(manager_id, []).append(reporter_id)

        if allowed_ids is not None:
            for employee_id in node_ids:
                if employee_id and employee_id not in allowed_ids:
                    errors.append({
                        "code": "unknown_employee",
                        "message": f"Organization node references unknown employee '{employee_id}'.",
                    })

        missing_nodes = sorted(referenced_ids - node_ids)
        for employee_id in missing_nodes:
            warnings.append({
                "code": "missing_node",
                "message": f"Employee '{employee_id}' is referenced by a relationship but has no saved layout node.",
            })

        for reporter_id in sorted(manager_by_reporter):
            seen: set[str] = set()
            current = reporter_id
            while current in manager_by_reporter:
                if current in seen:
                    errors.append({
                        "code": "cycle",
                        "message": f"Organization graph contains a cycle involving employee '{current}'.",
                    })
                    break
                seen.add(current)
                current = manager_by_reporter[current]

        return {
            "valid": not errors,
            "errors": errors,
            "warnings": warnings,
            "summary": {
                "node_count": len(node_ids),
                "edge_count": len(normalized["edges"]),
                "root_count": len(node_ids - set(manager_by_reporter)),
            },
        }


@dataclass(frozen=True)
class OrganizationPolicyDecision:
    allowed: bool
    reason: str = ""


class OrganizationPolicy:
    """Evaluate whether employees may communicate under the organization graph."""

    def __init__(
        self,
        registry: AgentRegistry,
        store: OrganizationStore,
        *,
        default_allow_skip_level_reporting: bool = False,
    ) -> None:
        self._registry = registry
        self._store = store
        self._default_allow_skip_level_reporting = default_allow_skip_level_reporting

    def can_communicate(self, requester_agent_id: str | None, target_agent_id: str | None) -> OrganizationPolicyDecision:
        requester_id = _text(requester_agent_id)
        target_id = _text(target_agent_id)
        if not requester_id or not target_id:
            return OrganizationPolicyDecision(True, "main/admin context bypasses organization policy")
        if requester_id == target_id:
            return OrganizationPolicyDecision(True, "same employee")
        if self._registry.get(requester_id) is None:
            return OrganizationPolicyDecision(False, f"requester employee '{requester_id}' was not found")
        if self._registry.get(target_id) is None:
            return OrganizationPolicyDecision(False, f"target employee '{target_id}' was not found")

        graph = self._store.load(
            employee_ids=[entry.agent_id for entry in self._registry.all()],
            clean=True,
            default_allow_skip_level_reporting=self._default_allow_skip_level_reporting,
        )
        if _bool(graph.get("settings", {}).get("allow_skip_level_reporting")):
            return OrganizationPolicyDecision(True, "global skip-level reporting is enabled")

        nodes = {
            _text(node.get("employee_id")): node
            for node in graph.get("nodes", [])
            if isinstance(node, Mapping) and _text(node.get("employee_id"))
        }
        requester_node = nodes.get(requester_id, {})
        if _bool(requester_node.get("allow_skip_level_reporting")):
            return OrganizationPolicyDecision(True, "requester skip-level reporting override is enabled")

        direct_pairs = {
            (_text(edge.get("reporter_id")), _text(edge.get("manager_id")))
            for edge in graph.get("edges", [])
            if isinstance(edge, Mapping)
        }
        if (requester_id, target_id) in direct_pairs:
            return OrganizationPolicyDecision(True, "target is requester direct manager")
        if (target_id, requester_id) in direct_pairs:
            return OrganizationPolicyDecision(True, "target is requester direct report")
        return OrganizationPolicyDecision(
            False,
            f"skip-level communication from '{requester_id}' to '{target_id}' is disabled",
        )


__all__ = [
    "ORGANIZATION_VERSION",
    "OrganizationPolicy",
    "OrganizationPolicyDecision",
    "OrganizationStore",
    "OrganizationValidationError",
    "OrganizationValidator",
    "normalize_organization_graph",
    "_dedupe_preserve_order",
]
