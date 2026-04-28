"""Governed writes to long-term memory files."""

from __future__ import annotations

from dataclasses import asdict, dataclass, field
from datetime import datetime, timezone
import json
from pathlib import Path
from typing import Any, Mapping
import uuid

from openhire.utils.gitstore import GitStore


TRACKED_MEMORY_FILES = ("SOUL.md", "USER.md", "memory/MEMORY.md")
AUTO_APPLY_CATEGORIES = {"user_preference", "project_fact", "workflow_experience"}
SKIP_CATEGORIES = {"temporary_status", "one_time_event"}
HIGH_IMPACT_CATEGORIES = {
    "organization_relation",
    "employee_permission",
    "default_behavior",
    "security_policy",
    "required_skill",
    "runtime_default",
    "adapter_default",
}
VALID_ACTIONS = {"append", "patch", "delete"}
VALID_IMPACTS = {"low", "medium", "high"}


def _now() -> str:
    return datetime.now(timezone.utc).isoformat(timespec="seconds")


def _coerce_string_list(raw: Any) -> list[str]:
    values = raw if isinstance(raw, list) else [raw]
    result: list[str] = []
    for item in values:
        if item is None:
            continue
        text = str(item).strip()
        if text and text not in result:
            result.append(text)
    return result


def _coerce_ttl(raw: Any) -> int | None:
    if raw in ("", None):
        return None
    try:
        value = int(raw)
    except (TypeError, ValueError) as exc:
        raise MemoryWriteValidationError("ttl_days must be an integer.") from exc
    if value < 0:
        raise MemoryWriteValidationError("ttl_days must be greater than or equal to 0.")
    return value


def normalize_memory_target(raw: str) -> str:
    target = str(raw or "").strip().replace("\\", "/")
    if target == "MEMORY.md":
        target = "memory/MEMORY.md"
    if target not in TRACKED_MEMORY_FILES:
        allowed = ", ".join(TRACKED_MEMORY_FILES)
        raise MemoryWriteValidationError(f"target_file must be one of: {allowed}.")
    return target


@dataclass
class MemoryWriteProposal:
    id: str
    target_file: str
    action: str
    old_text: str = ""
    new_text: str = ""
    category: str = "other"
    impact: str = "medium"
    reason: str = ""
    ttl_days: int | None = None
    evidence: list[str] = field(default_factory=list)
    metadata: dict[str, Any] = field(default_factory=dict)
    status: str = "pending"
    created_at: str = field(default_factory=_now)
    updated_at: str = ""
    applied_at: str = ""
    result: dict[str, Any] | None = None

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)

    @classmethod
    def from_dict(cls, payload: Mapping[str, Any]) -> MemoryWriteProposal:
        return cls(
            id=str(payload.get("id") or ""),
            target_file=normalize_memory_target(str(payload.get("target_file") or "")),
            action=str(payload.get("action") or "append"),
            old_text=str(payload.get("old_text") or ""),
            new_text=str(payload.get("new_text") or ""),
            category=str(payload.get("category") or "other"),
            impact=str(payload.get("impact") or "medium"),
            reason=str(payload.get("reason") or ""),
            ttl_days=_coerce_ttl(payload.get("ttl_days")),
            evidence=_coerce_string_list(payload.get("evidence") or []),
            metadata=payload.get("metadata") if isinstance(payload.get("metadata"), dict) else {},
            status=str(payload.get("status") or "pending"),
            created_at=str(payload.get("created_at") or _now()),
            updated_at=str(payload.get("updated_at") or ""),
            applied_at=str(payload.get("applied_at") or ""),
            result=payload.get("result") if isinstance(payload.get("result"), dict) else None,
        )


class MemoryWriteService:
    """Apply low-risk memory writes and queue high-impact writes for review."""

    def __init__(self, workspace: Path) -> None:
        self.workspace = Path(workspace)
        self._proposal_file = self.workspace / "openhire" / "memory_write_proposals.json"
        self._record_file = self.workspace / "openhire" / "memory_records.jsonl"
        self._git = GitStore(self.workspace, tracked_files=list(TRACKED_MEMORY_FILES))

    @property
    def proposal_file(self) -> Path:
        return self._proposal_file

    @property
    def record_file(self) -> Path:
        return self._record_file

    def list_proposals(self, *, status: str | None = None) -> list[dict[str, Any]]:
        proposals = [proposal.to_dict() for proposal in self._load_proposals()]
        if status:
            proposals = [proposal for proposal in proposals if proposal.get("status") == status]
        return proposals

    def pending_count(self) -> int:
        return len(self.list_proposals(status="pending"))

    def list_records(self, *, limit: int = 50) -> list[dict[str, Any]]:
        try:
            limit_value = max(0, int(50 if limit is None else limit))
        except (TypeError, ValueError):
            limit_value = 50
        if limit_value == 0:
            return []
        records: list[dict[str, Any]] = []
        try:
            with open(self._record_file, encoding="utf-8") as fh:
                for line in fh:
                    line = line.strip()
                    if not line:
                        continue
                    try:
                        item = json.loads(line)
                    except json.JSONDecodeError:
                        continue
                    if isinstance(item, dict):
                        records.append(item)
        except FileNotFoundError:
            return []
        return records[-limit_value:]

    def submit(self, payload: Mapping[str, Any], *, metadata: Mapping[str, Any] | None = None) -> dict[str, Any]:
        proposal = self._proposal_from_payload(payload, metadata=metadata)
        if proposal.category in SKIP_CATEGORIES:
            record = self._append_record("skipped", proposal)
            return {"status": "skipped", "record": record}

        if self._requires_review(proposal):
            proposals = self._load_proposals()
            proposals.append(proposal)
            self._save_proposals(proposals)
            record = self._append_record("pending", proposal)
            return {"status": "pending", "proposal": proposal.to_dict(), "record": record}

        result = self._apply(proposal)
        record = self._append_record("auto_applied", proposal, result=result)
        return {"status": "auto_applied", "record": record, "result": result}

    def approve_proposal(self, proposal_id: str) -> dict[str, Any]:
        proposals = self._load_proposals()
        proposal = next((item for item in proposals if item.id == proposal_id), None)
        if proposal is None:
            raise MemoryWriteNotFoundError(f"Memory write proposal '{proposal_id}' not found.")
        if proposal.status != "pending":
            raise MemoryWriteValidationError("Only pending memory write proposals can be approved.")

        self._git.init()
        result = self._apply(proposal)
        proposal.status = "approved"
        proposal.applied_at = _now()
        proposal.updated_at = proposal.applied_at
        proposal.result = result
        self._save_proposals(proposals)

        sha = self._git.auto_commit(f"memory: approve {proposal.id} {proposal.target_file}")
        if sha:
            result["commit"] = sha
            proposal.result = result
            self._save_proposals(proposals)
        self._append_record("approved", proposal, result=result)
        return proposal.to_dict()

    def discard_proposal(self, proposal_id: str) -> bool:
        proposals = self._load_proposals()
        proposal = next((item for item in proposals if item.id == proposal_id), None)
        if proposal is None:
            return False
        if proposal.status == "pending":
            proposal.status = "discarded"
            proposal.updated_at = _now()
            self._save_proposals(proposals)
            self._append_record("discarded", proposal)
        return True

    def _proposal_from_payload(
        self,
        payload: Mapping[str, Any],
        *,
        metadata: Mapping[str, Any] | None = None,
    ) -> MemoryWriteProposal:
        target_file = normalize_memory_target(str(payload.get("target_file") or ""))
        action = str(payload.get("action") or "append").strip().lower() or "append"
        if action not in VALID_ACTIONS:
            raise MemoryWriteValidationError("action must be append, patch, or delete.")
        category = str(payload.get("category") or "other").strip().lower() or "other"
        impact = str(payload.get("impact") or "medium").strip().lower() or "medium"
        if impact not in VALID_IMPACTS:
            raise MemoryWriteValidationError("impact must be low, medium, or high.")
        reason = str(payload.get("reason") or "").strip()
        evidence = _coerce_string_list(payload.get("evidence") or [])
        if metadata:
            auto_evidence = _coerce_string_list(metadata.get("evidence") or [])
            for item in auto_evidence:
                if item not in evidence:
                    evidence.append(item)
        if not evidence:
            raise MemoryWriteValidationError("evidence is required for memory writes.")

        old_text = str(payload.get("old_text") or "")
        new_text = str(payload.get("new_text") or "")
        if action == "append" and not new_text.strip():
            raise MemoryWriteValidationError("new_text is required for append.")
        if action in {"patch", "delete"} and not old_text:
            raise MemoryWriteValidationError("old_text is required for patch/delete.")
        if action == "patch" and not new_text:
            raise MemoryWriteValidationError("new_text is required for patch.")

        return MemoryWriteProposal(
            id=str(uuid.uuid4())[:8],
            target_file=target_file,
            action=action,
            old_text=old_text,
            new_text=new_text,
            category=category,
            impact=impact,
            reason=reason,
            ttl_days=_coerce_ttl(payload.get("ttl_days")),
            evidence=evidence,
            metadata=dict(metadata or {}),
        )

    def _requires_review(self, proposal: MemoryWriteProposal) -> bool:
        if proposal.impact == "high":
            return True
        if proposal.target_file == "SOUL.md":
            return True
        if proposal.category in HIGH_IMPACT_CATEGORIES:
            return True
        if proposal.category not in AUTO_APPLY_CATEGORIES:
            return True
        if proposal.action == "delete":
            return True
        if proposal.action == "patch" and (len(proposal.old_text) > 1200 or len(proposal.new_text) > 2000):
            return True
        return not (proposal.impact == "low" and proposal.target_file in {"USER.md", "memory/MEMORY.md"})

    def _apply(self, proposal: MemoryWriteProposal) -> dict[str, Any]:
        path = self.workspace / proposal.target_file
        path.parent.mkdir(parents=True, exist_ok=True)
        before = path.read_text(encoding="utf-8") if path.exists() else ""

        if proposal.action == "append":
            addition = proposal.new_text.strip()
            after = f"{before.rstrip()}\n\n{addition}\n" if before.strip() else f"{addition}\n"
        elif proposal.action == "patch":
            if proposal.old_text not in before:
                raise MemoryWriteValidationError(f"old_text was not found in {proposal.target_file}.")
            after = before.replace(proposal.old_text, proposal.new_text, 1)
        else:
            if proposal.old_text not in before:
                raise MemoryWriteValidationError(f"old_text was not found in {proposal.target_file}.")
            after = before.replace(proposal.old_text, "", 1)

        path.write_text(after, encoding="utf-8")
        return {
            "target_file": proposal.target_file,
            "changed": before != after,
            "before_chars": len(before),
            "after_chars": len(after),
        }

    def _append_record(
        self,
        status: str,
        proposal: MemoryWriteProposal,
        *,
        result: Mapping[str, Any] | None = None,
    ) -> dict[str, Any]:
        record = {
            "id": str(uuid.uuid4())[:8],
            "proposal_id": proposal.id,
            "status": status,
            "target_file": proposal.target_file,
            "action": proposal.action,
            "category": proposal.category,
            "impact": proposal.impact,
            "reason": proposal.reason,
            "ttl_days": proposal.ttl_days,
            "evidence": list(proposal.evidence),
            "metadata": dict(proposal.metadata or {}),
            "result": dict(result or {}),
            "created_at": _now(),
        }
        self._record_file.parent.mkdir(parents=True, exist_ok=True)
        with open(self._record_file, "a", encoding="utf-8") as fh:
            fh.write(json.dumps(record, ensure_ascii=False) + "\n")
        return record

    def _load_proposals(self) -> list[MemoryWriteProposal]:
        if not self._proposal_file.exists():
            return []
        try:
            payload = json.loads(self._proposal_file.read_text(encoding="utf-8"))
        except (json.JSONDecodeError, OSError):
            return []
        proposals = payload.get("proposals") if isinstance(payload, dict) else []
        if not isinstance(proposals, list):
            return []
        loaded: list[MemoryWriteProposal] = []
        for item in proposals:
            if isinstance(item, Mapping):
                try:
                    loaded.append(MemoryWriteProposal.from_dict(item))
                except MemoryWriteValidationError:
                    continue
        return loaded

    def _save_proposals(self, proposals: list[MemoryWriteProposal]) -> None:
        self._proposal_file.parent.mkdir(parents=True, exist_ok=True)
        tmp = self._proposal_file.with_suffix(".tmp")
        tmp.write_text(
            json.dumps({"proposals": [proposal.to_dict() for proposal in proposals]}, indent=2, ensure_ascii=False),
            encoding="utf-8",
        )
        tmp.replace(self._proposal_file)


class MemoryWriteError(RuntimeError):
    """Base error for governed memory writes."""


class MemoryWriteValidationError(MemoryWriteError, ValueError):
    """Raised when a memory write violates policy or patch constraints."""


class MemoryWriteNotFoundError(MemoryWriteError):
    """Raised when a requested memory write proposal is missing."""
