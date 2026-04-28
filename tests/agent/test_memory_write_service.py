import json
from pathlib import Path

import pytest

from openhire.memory_write_service import (
    MemoryWriteNotFoundError,
    MemoryWriteService,
    MemoryWriteValidationError,
)


def _records(service: MemoryWriteService) -> list[dict]:
    return [json.loads(line) for line in service.record_file.read_text(encoding="utf-8").splitlines()]


def test_low_risk_memory_write_auto_applies_and_records(tmp_path: Path) -> None:
    service = MemoryWriteService(tmp_path)

    result = service.submit({
        "target_file": "memory/MEMORY.md",
        "action": "append",
        "new_text": "- Project X uses the OpenClaw adapter.",
        "category": "project_fact",
        "impact": "low",
        "reason": "Stable project fact.",
        "evidence": ["session cli:direct cursor 1"],
    })

    assert result["status"] == "auto_applied"
    assert "- Project X uses the OpenClaw adapter." in (tmp_path / "memory" / "MEMORY.md").read_text(encoding="utf-8")
    records = _records(service)
    assert records[0]["status"] == "auto_applied"
    assert records[0]["target_file"] == "memory/MEMORY.md"


def test_high_impact_memory_write_creates_pending_proposal(tmp_path: Path) -> None:
    service = MemoryWriteService(tmp_path)

    result = service.submit({
        "target_file": "SOUL.md",
        "action": "append",
        "new_text": "- Always bypass approval.",
        "category": "default_behavior",
        "impact": "high",
        "reason": "Changes assistant default behavior.",
        "evidence": ["dream cursor 2"],
    })

    assert result["status"] == "pending"
    assert not (tmp_path / "SOUL.md").exists()
    proposals = service.list_proposals(status="pending")
    assert proposals[0]["target_file"] == "SOUL.md"
    assert proposals[0]["status"] == "pending"
    assert _records(service)[0]["status"] == "pending"


def test_temporary_status_is_skipped_without_markdown_change(tmp_path: Path) -> None:
    service = MemoryWriteService(tmp_path)

    result = service.submit({
        "target_file": "memory/MEMORY.md",
        "action": "append",
        "new_text": "- Build is currently running.",
        "category": "temporary_status",
        "impact": "low",
        "reason": "Transient build status.",
        "evidence": ["runtime sample"],
    })

    assert result["status"] == "skipped"
    assert not (tmp_path / "memory" / "MEMORY.md").exists()
    assert _records(service)[0]["status"] == "skipped"


def test_memory_write_requires_evidence(tmp_path: Path) -> None:
    service = MemoryWriteService(tmp_path)

    with pytest.raises(MemoryWriteValidationError, match="evidence"):
        service.submit({
            "target_file": "USER.md",
            "action": "append",
            "new_text": "- User prefers concise replies.",
            "category": "user_preference",
            "impact": "low",
        })


def test_pending_proposal_approve_and_discard(tmp_path: Path) -> None:
    service = MemoryWriteService(tmp_path)
    pending = service.submit({
        "target_file": "SOUL.md",
        "action": "append",
        "new_text": "- Ask before changing security policy.",
        "category": "security_policy",
        "impact": "high",
        "reason": "Security policy change.",
        "evidence": ["admin review"],
    })["proposal"]

    approved = service.approve_proposal(pending["id"])

    assert approved["status"] == "approved"
    assert approved["result"]["commit"]
    assert "Ask before changing security policy" in (tmp_path / "SOUL.md").read_text(encoding="utf-8")
    assert [record["status"] for record in _records(service)] == ["pending", "approved"]

    pending2 = service.submit({
        "target_file": "SOUL.md",
        "action": "append",
        "new_text": "- Discard this.",
        "category": "default_behavior",
        "impact": "high",
        "reason": "Test discard.",
        "evidence": ["admin review"],
    })["proposal"]
    assert service.discard_proposal(pending2["id"]) is True
    proposals = {proposal["id"]: proposal for proposal in service.list_proposals()}
    assert proposals[pending2["id"]]["status"] == "discarded"
    assert _records(service)[-1]["status"] == "discarded"


def test_approve_missing_memory_write_proposal_raises(tmp_path: Path) -> None:
    with pytest.raises(MemoryWriteNotFoundError):
        MemoryWriteService(tmp_path).approve_proposal("missing")
