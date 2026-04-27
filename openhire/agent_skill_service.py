"""Agent-readable skill directory management for the admin workbench."""

from __future__ import annotations

from dataclasses import asdict, dataclass, field
from datetime import datetime, timezone
import importlib.util
import json
from pathlib import Path
import re
import shutil
import subprocess
import sys
import tempfile
from typing import Any, Mapping
import uuid

from openhire.agent.skills import BUILTIN_SKILLS_DIR, SkillsLoader
from openhire.skill_catalog import SkillPreviewParseError, _load_skill_frontmatter

_SKILL_NAME_RE = re.compile(r"[a-z0-9]+(?:-[a-z0-9]+)*")
_ALLOWED_RESOURCE_DIRS = {"scripts", "references", "assets"}
_MAX_SKILL_NAME_LENGTH = 64
_SKILL_CREATOR_SCRIPTS_DIR = BUILTIN_SKILLS_DIR / "skill-creator" / "scripts"
_QUICK_VALIDATE_PATH = _SKILL_CREATOR_SCRIPTS_DIR / "quick_validate.py"
_PACKAGE_SKILL_PATH = _SKILL_CREATOR_SCRIPTS_DIR / "package_skill.py"


def _now() -> str:
    return datetime.now(timezone.utc).isoformat(timespec="seconds")


def normalize_agent_skill_name(raw: str) -> str:
    """Normalize user-provided names using the skill-creator naming rule."""

    normalized = str(raw or "").strip().lower()
    normalized = re.sub(r"[^a-z0-9]+", "-", normalized)
    normalized = re.sub(r"-{2,}", "-", normalized).strip("-")
    if not normalized:
        raise AgentSkillValidationError("Skill name must include at least one letter or digit.")
    if len(normalized) > _MAX_SKILL_NAME_LENGTH:
        raise AgentSkillValidationError(
            f"Skill name '{normalized}' is too long ({len(normalized)} characters)."
        )
    if not _SKILL_NAME_RE.fullmatch(normalized):
        raise AgentSkillValidationError(
            "Skill name must use lowercase letters, digits, and single hyphens."
        )
    return normalized


def _title_case_skill_name(name: str) -> str:
    return " ".join(part.capitalize() for part in name.split("-"))


def _load_quick_validate_module() -> Any:
    spec = importlib.util.spec_from_file_location("openhire_skill_quick_validate", _QUICK_VALIDATE_PATH)
    if spec is None or spec.loader is None:
        raise AgentSkillValidationError("Skill validator is unavailable.")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def _validate_skill_dir(skill_dir: Path) -> None:
    module = _load_quick_validate_module()
    valid, message = module.validate_skill(skill_dir)
    if not valid:
        raise AgentSkillValidationError(str(message))


def _parse_skill_metadata(markdown: str) -> dict[str, Any]:
    try:
        frontmatter = _load_skill_frontmatter(markdown)
    except SkillPreviewParseError as exc:
        raise AgentSkillValidationError(str(exc)) from exc
    return {
        "name": str(frontmatter.get("name") or "").strip(),
        "description": str(frontmatter.get("description") or "").strip(),
        "license": str(frontmatter.get("license") or "").strip(),
        "homepage": str(frontmatter.get("homepage") or "").strip(),
        "version": str(frontmatter.get("version") or "").strip(),
        "author": str(frontmatter.get("author") or "").strip(),
        "category": str(frontmatter.get("category") or "").strip(),
    }


def _default_skill_markdown(name: str, description: str) -> str:
    title = _title_case_skill_name(name)
    return (
        "---\n"
        f"name: {name}\n"
        f"description: {description.strip()}\n"
        "---\n\n"
        f"# {title}\n\n"
        f"{description.strip()}\n\n"
        "## Procedure\n\n"
        "1. Read the user's request and identify the reusable workflow this skill supports.\n"
        "2. Use this skill's resources only when they directly help the task.\n\n"
        "## Verification\n\n"
        "- Confirm the result matches the user's requested workflow.\n"
    )


def _coerce_resources(raw: Any) -> list[str]:
    values = raw if isinstance(raw, list) else []
    resources: list[str] = []
    for item in values:
        normalized = str(item or "").strip()
        if not normalized:
            continue
        if normalized not in _ALLOWED_RESOURCE_DIRS:
            allowed = ", ".join(sorted(_ALLOWED_RESOURCE_DIRS))
            raise AgentSkillValidationError(f"Unknown resource directory '{normalized}'. Allowed: {allowed}.")
        if normalized not in resources:
            resources.append(normalized)
    return resources


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


def _merge_reason(existing: str, incoming: str) -> str:
    existing = str(existing or "").strip()
    incoming = str(incoming or "").strip()
    if not incoming:
        return existing
    if not existing:
        return incoming
    if incoming in existing:
        return existing
    return f"{existing}\n\n{incoming}"


def _is_relative_safe_path(path: str) -> bool:
    candidate = Path(path)
    return not candidate.is_absolute() and ".." not in candidate.parts


def _safe_resource_path(skill_dir: Path, relative_path: str) -> Path:
    normalized = str(relative_path or "").strip().replace("\\", "/")
    if not normalized or not _is_relative_safe_path(normalized):
        raise AgentSkillValidationError("Resource file path must be relative and stay inside the skill.")
    parts = Path(normalized).parts
    if not parts or parts[0] not in _ALLOWED_RESOURCE_DIRS:
        allowed = ", ".join(sorted(_ALLOWED_RESOURCE_DIRS))
        raise AgentSkillValidationError(f"Resource files must live under one of: {allowed}.")
    target = (skill_dir / normalized).resolve()
    root = skill_dir.resolve()
    try:
        target.relative_to(root)
    except ValueError as exc:
        raise AgentSkillValidationError("Resource file path escapes the skill directory.") from exc
    return target


def _reject_symlink_path(path: Path, root: Path) -> None:
    current = root.resolve()
    for part in path.resolve().relative_to(current).parts:
        current = current / part
        if current.is_symlink():
            raise AgentSkillValidationError("Symlinks are not allowed in agent skills.")


@dataclass
class AgentSkillProposal:
    id: str
    action: str
    name: str
    reason: str = ""
    content: str = ""
    old_string: str = ""
    new_string: str = ""
    source: str = "manual"
    trigger_reasons: list[str] = field(default_factory=list)
    evidence: list[str] = field(default_factory=list)
    merged_count: int = 0
    status: str = "pending"
    created_at: str = field(default_factory=_now)
    updated_at: str = ""
    applied_at: str = ""
    result: dict[str, Any] | None = None

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)

    @classmethod
    def from_dict(cls, payload: Mapping[str, Any]) -> AgentSkillProposal:
        return cls(
            id=str(payload.get("id") or ""),
            action=str(payload.get("action") or "create"),
            name=str(payload.get("name") or ""),
            reason=str(payload.get("reason") or ""),
            content=str(payload.get("content") or ""),
            old_string=str(payload.get("old_string") or ""),
            new_string=str(payload.get("new_string") or ""),
            source=str(payload.get("source") or "manual"),
            trigger_reasons=_coerce_string_list(payload.get("trigger_reasons") or []),
            evidence=_coerce_string_list(payload.get("evidence") or []),
            merged_count=int(payload.get("merged_count") or 0),
            status=str(payload.get("status") or "pending"),
            created_at=str(payload.get("created_at") or _now()),
            updated_at=str(payload.get("updated_at") or ""),
            applied_at=str(payload.get("applied_at") or ""),
            result=payload.get("result") if isinstance(payload.get("result"), dict) else None,
        )


class AgentSkillService:
    """Manage skills that are actually loaded by ``SkillsLoader``."""

    _AUTO_PROPOSAL_SOURCES = {"turn", "dream", "auto"}

    def __init__(self, workspace: Path, builtin_skills_dir: Path | None = None) -> None:
        self.workspace = Path(workspace)
        self.workspace_skills = self.workspace / "skills"
        self.builtin_skills = builtin_skills_dir or BUILTIN_SKILLS_DIR
        self._proposal_file = self.workspace / "openhire" / "agent_skill_proposals.json"
        self._package_dir = self.workspace / "openhire" / "agent_skill_packages"

    def list(self, *, bound_counts: Mapping[str, int] | None = None) -> list[dict[str, Any]]:
        loader = SkillsLoader(self.workspace, builtin_skills_dir=self.builtin_skills)
        rows: list[dict[str, Any]] = []
        for entry in sorted(loader.list_skills(filter_unavailable=False), key=lambda item: item["name"]):
            name = entry["name"]
            markdown = Path(entry["path"]).read_text(encoding="utf-8")
            metadata = _parse_skill_metadata(markdown)
            skill_meta = loader._get_skill_meta(name)
            available = loader._check_requirements(skill_meta)
            rows.append(
                {
                    "name": name,
                    "description": metadata.get("description", ""),
                    "source": entry["source"],
                    "category": metadata.get("category", ""),
                    "path": entry["path"],
                    "available": available,
                    "missing_requirements": "" if available else loader._get_missing_requirements(skill_meta),
                    "updated_at": self._mtime(Path(entry["path"])),
                    "editable": entry["source"] == "workspace",
                    "deletable": entry["source"] == "workspace",
                    "bound_employee_count": int((bound_counts or {}).get(name, 0)),
                }
            )
        return rows

    def get(self, name: str) -> dict[str, Any]:
        entry = self._find_skill(name)
        if entry is None:
            raise AgentSkillNotFoundError(f"Agent skill '{name}' not found.")
        skill_file = Path(entry["path"])
        markdown = skill_file.read_text(encoding="utf-8")
        loader = SkillsLoader(self.workspace, builtin_skills_dir=self.builtin_skills)
        skill_meta = loader._get_skill_meta(entry["name"])
        available = loader._check_requirements(skill_meta)
        return {
            "skill": {
                "name": entry["name"],
                "source": entry["source"],
                "path": str(skill_file),
                "available": available,
                "missing_requirements": "" if available else loader._get_missing_requirements(skill_meta),
                "editable": entry["source"] == "workspace",
                "deletable": entry["source"] == "workspace",
                "updated_at": self._mtime(skill_file),
                **_parse_skill_metadata(markdown),
            },
            "markdown": markdown,
            "files": self._file_tree(skill_file.parent),
            "metadata": _parse_skill_metadata(markdown),
        }

    def create(
        self,
        *,
        name: str,
        description: str = "",
        content: str = "",
        resources: list[str] | None = None,
        overwrite: bool = False,
    ) -> dict[str, Any]:
        normalized_name = normalize_agent_skill_name(name)
        skill_dir = self.workspace_skills / normalized_name
        if skill_dir.exists() and not overwrite:
            raise AgentSkillConflictError(f"Workspace skill '{normalized_name}' already exists.")

        markdown = content.strip() if content.strip() else _default_skill_markdown(normalized_name, description)
        metadata = _parse_skill_metadata(markdown)
        frontmatter_name = normalize_agent_skill_name(str(metadata.get("name") or normalized_name))
        if frontmatter_name != normalized_name:
            raise AgentSkillValidationError(
                f"SKILL.md name '{frontmatter_name}' must match directory name '{normalized_name}'."
            )
        self._validate_payload(normalized_name, markdown, resources=resources or [])

        if skill_dir.exists():
            shutil.rmtree(skill_dir)
        skill_dir.mkdir(parents=True, exist_ok=False)
        (skill_dir / "SKILL.md").write_text(markdown + ("\n" if not markdown.endswith("\n") else ""), encoding="utf-8")
        for resource in _coerce_resources(resources or []):
            (skill_dir / resource).mkdir(exist_ok=True)
        _validate_skill_dir(skill_dir)
        return self.get(normalized_name)

    def patch(self, name: str, *, old_string: str, new_string: str) -> dict[str, Any]:
        normalized_name = normalize_agent_skill_name(name)
        skill_dir = self._workspace_skill_dir(normalized_name)
        markdown_path = skill_dir / "SKILL.md"
        markdown = markdown_path.read_text(encoding="utf-8")
        if not old_string:
            raise AgentSkillValidationError("old_string is required.")
        if old_string not in markdown:
            raise AgentSkillValidationError("old_string was not found in SKILL.md.")
        updated = markdown.replace(old_string, new_string, 1)
        self._validate_payload(normalized_name, updated)
        markdown_path.write_text(updated, encoding="utf-8")
        _validate_skill_dir(skill_dir)
        return self.get(normalized_name)

    def update(self, name: str, *, content: str) -> dict[str, Any]:
        normalized_name = normalize_agent_skill_name(name)
        skill_dir = self._workspace_skill_dir(normalized_name)
        markdown = content.strip()
        if not markdown:
            raise AgentSkillValidationError("SKILL.md content is required.")
        metadata = _parse_skill_metadata(markdown)
        frontmatter_name = normalize_agent_skill_name(str(metadata.get("name") or normalized_name))
        if frontmatter_name != normalized_name:
            raise AgentSkillValidationError(
                f"SKILL.md name '{frontmatter_name}' must match directory name '{normalized_name}'."
            )
        self._validate_payload(normalized_name, markdown)
        (skill_dir / "SKILL.md").write_text(markdown + ("\n" if not markdown.endswith("\n") else ""), encoding="utf-8")
        _validate_skill_dir(skill_dir)
        return self.get(normalized_name)

    def write_file(self, name: str, *, file_path: str, content: str) -> dict[str, Any]:
        normalized_name = normalize_agent_skill_name(name)
        skill_dir = self._workspace_skill_dir(normalized_name)
        target = _safe_resource_path(skill_dir, file_path)
        _reject_symlink_path(target.parent, skill_dir)
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_text(str(content), encoding="utf-8")
        _validate_skill_dir(skill_dir)
        return self.get(normalized_name)

    def remove_file(self, name: str, *, file_path: str) -> dict[str, Any]:
        normalized_name = normalize_agent_skill_name(name)
        skill_dir = self._workspace_skill_dir(normalized_name)
        target = _safe_resource_path(skill_dir, file_path)
        if not target.exists():
            raise AgentSkillNotFoundError(f"Resource file '{file_path}' not found.")
        _reject_symlink_path(target, skill_dir)
        if target.is_dir():
            shutil.rmtree(target)
        else:
            target.unlink()
        _validate_skill_dir(skill_dir)
        return self.get(normalized_name)

    def delete(self, name: str) -> None:
        normalized_name = normalize_agent_skill_name(name)
        skill_dir = self.workspace_skills / normalized_name
        if not skill_dir.exists():
            if (self.builtin_skills / normalized_name / "SKILL.md").exists():
                raise AgentSkillProtectedError("Built-in agent skills cannot be deleted from the workbench.")
            raise AgentSkillNotFoundError(f"Workspace skill '{normalized_name}' not found.")
        _reject_symlink_path(skill_dir, self.workspace_skills)
        shutil.rmtree(skill_dir)

    def package(self, name: str) -> dict[str, Any]:
        normalized_name = normalize_agent_skill_name(name)
        entry = self._find_skill(normalized_name)
        if entry is None:
            raise AgentSkillNotFoundError(f"Agent skill '{normalized_name}' not found.")
        skill_dir = Path(entry["path"]).parent
        _validate_skill_dir(skill_dir)
        self._package_dir.mkdir(parents=True, exist_ok=True)
        completed = subprocess.run(
            [sys.executable, str(_PACKAGE_SKILL_PATH), str(skill_dir), str(self._package_dir)],
            check=False,
            capture_output=True,
            text=True,
        )
        if completed.returncode != 0:
            message = (completed.stderr or completed.stdout or "Skill packaging failed.").strip()
            raise AgentSkillValidationError(message)
        package_path = self._package_dir / f"{normalized_name}.skill"
        return {
            "name": normalized_name,
            "package_path": str(package_path),
            "size": package_path.stat().st_size if package_path.exists() else 0,
            "output": completed.stdout,
        }

    def list_proposals(self) -> list[dict[str, Any]]:
        return [proposal.to_dict() for proposal in self._load_proposals()]

    def create_proposal(self, payload: Mapping[str, Any]) -> dict[str, Any]:
        action = str(payload.get("action") or "create").strip() or "create"
        if action not in {"create", "patch", "edit"}:
            raise AgentSkillValidationError("Proposal action must be create, patch, or edit.")
        name = normalize_agent_skill_name(str(payload.get("name") or ""))
        source = str(payload.get("source") or "manual").strip().lower() or "manual"
        if source not in {"manual", *self._AUTO_PROPOSAL_SOURCES}:
            source = "manual"
        proposal = AgentSkillProposal(
            id=str(uuid.uuid4())[:8],
            action=action,
            name=name,
            reason=str(payload.get("reason") or ""),
            content=str(payload.get("content") or ""),
            old_string=str(payload.get("old_string") or ""),
            new_string=str(payload.get("new_string") or ""),
            source=source,
            trigger_reasons=_coerce_string_list(payload.get("trigger_reasons") or []),
            evidence=_coerce_string_list(payload.get("evidence") or []),
        )
        if action in {"create", "edit"}:
            if not proposal.content.strip():
                raise AgentSkillValidationError("Proposal content is required.")
            self._validate_payload(name, proposal.content)
        if action == "patch" and not proposal.old_string:
            raise AgentSkillValidationError("Patch proposals require old_string.")
        proposals = self._load_proposals()
        if proposal.source in self._AUTO_PROPOSAL_SOURCES:
            existing = self._find_pending_auto_proposal(proposals, proposal.name)
            if existing is not None:
                self._merge_auto_proposal(existing, proposal)
                self._save_proposals(proposals)
                return existing.to_dict()
        proposals.append(proposal)
        self._save_proposals(proposals)
        return proposal.to_dict()

    def _find_pending_auto_proposal(
        self,
        proposals: list[AgentSkillProposal],
        name: str,
    ) -> AgentSkillProposal | None:
        return next(
            (
                proposal
                for proposal in proposals
                if proposal.status == "pending"
                and proposal.name == name
                and proposal.source in self._AUTO_PROPOSAL_SOURCES
            ),
            None,
        )

    def _merge_auto_proposal(self, existing: AgentSkillProposal, incoming: AgentSkillProposal) -> None:
        existing.action = incoming.action
        existing.reason = _merge_reason(existing.reason, incoming.reason)
        existing.content = incoming.content or existing.content
        existing.old_string = incoming.old_string or existing.old_string
        existing.new_string = incoming.new_string or existing.new_string
        existing.source = existing.source if existing.source == incoming.source else "auto"
        for reason in incoming.trigger_reasons:
            if reason not in existing.trigger_reasons:
                existing.trigger_reasons.append(reason)
        for item in incoming.evidence:
            if item not in existing.evidence:
                existing.evidence.append(item)
        existing.evidence = existing.evidence[-10:]
        existing.merged_count += 1
        existing.updated_at = _now()

    def approve_proposal(self, proposal_id: str) -> dict[str, Any]:
        proposals = self._load_proposals()
        proposal = next((item for item in proposals if item.id == proposal_id), None)
        if proposal is None:
            raise AgentSkillNotFoundError(f"Proposal '{proposal_id}' not found.")
        if proposal.status != "pending":
            raise AgentSkillValidationError("Only pending proposals can be approved.")

        if proposal.action == "create":
            result = self.create(name=proposal.name, content=proposal.content, overwrite=False)
        elif proposal.action == "edit":
            result = self.update(proposal.name, content=proposal.content)
        else:
            result = self.patch(
                proposal.name,
                old_string=proposal.old_string,
                new_string=proposal.new_string,
            )
        proposal.status = "approved"
        proposal.applied_at = _now()
        proposal.result = {"skill": result.get("skill", {})}
        self._save_proposals(proposals)
        return proposal.to_dict()

    def discard_proposal(self, proposal_id: str) -> bool:
        proposals = self._load_proposals()
        remaining = [item for item in proposals if item.id != proposal_id]
        if len(remaining) == len(proposals):
            return False
        self._save_proposals(remaining)
        return True

    def _validate_payload(self, name: str, markdown: str, *, resources: list[str] | None = None) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            skill_dir = Path(tmp) / name
            skill_dir.mkdir()
            (skill_dir / "SKILL.md").write_text(
                markdown + ("\n" if not markdown.endswith("\n") else ""),
                encoding="utf-8",
            )
            for resource in _coerce_resources(resources or []):
                (skill_dir / resource).mkdir()
            _validate_skill_dir(skill_dir)

    def _find_skill(self, name: str) -> dict[str, str] | None:
        normalized_name = normalize_agent_skill_name(name)
        loader = SkillsLoader(self.workspace, builtin_skills_dir=self.builtin_skills)
        return next(
            (entry for entry in loader.list_skills(filter_unavailable=False) if entry["name"] == normalized_name),
            None,
        )

    def _workspace_skill_dir(self, name: str) -> Path:
        normalized_name = normalize_agent_skill_name(name)
        skill_dir = self.workspace_skills / normalized_name
        if not (skill_dir / "SKILL.md").exists():
            if (self.builtin_skills / normalized_name / "SKILL.md").exists():
                raise AgentSkillProtectedError("Built-in agent skills must be copied into the workspace before editing.")
            raise AgentSkillNotFoundError(f"Workspace skill '{normalized_name}' not found.")
        return skill_dir

    def _file_tree(self, skill_dir: Path) -> list[dict[str, Any]]:
        files: list[dict[str, Any]] = []
        for path in sorted(skill_dir.rglob("*")):
            if path == skill_dir / "SKILL.md":
                continue
            if path.is_symlink():
                files.append({"path": str(path.relative_to(skill_dir)), "type": "symlink", "size": 0})
                continue
            if path.is_dir() and path.name in {".git", "__pycache__", "node_modules"}:
                continue
            rel = str(path.relative_to(skill_dir))
            if not rel:
                continue
            files.append(
                {
                    "path": rel,
                    "type": "directory" if path.is_dir() else "file",
                    "size": path.stat().st_size if path.is_file() else 0,
                }
            )
        return files

    def _load_proposals(self) -> list[AgentSkillProposal]:
        if not self._proposal_file.exists():
            return []
        try:
            payload = json.loads(self._proposal_file.read_text(encoding="utf-8"))
        except (json.JSONDecodeError, OSError):
            return []
        proposals = payload.get("proposals") if isinstance(payload, dict) else []
        if not isinstance(proposals, list):
            return []
        return [AgentSkillProposal.from_dict(item) for item in proposals if isinstance(item, Mapping)]

    def _save_proposals(self, proposals: list[AgentSkillProposal]) -> None:
        self._proposal_file.parent.mkdir(parents=True, exist_ok=True)
        tmp = self._proposal_file.with_suffix(".tmp")
        tmp.write_text(
            json.dumps({"proposals": [proposal.to_dict() for proposal in proposals]}, indent=2, ensure_ascii=False),
            encoding="utf-8",
        )
        tmp.replace(self._proposal_file)

    @staticmethod
    def _mtime(path: Path) -> str:
        try:
            return datetime.fromtimestamp(path.stat().st_mtime, tz=timezone.utc).isoformat(timespec="seconds")
        except OSError:
            return ""


class AgentSkillError(RuntimeError):
    """Base error for agent skill workbench operations."""


class AgentSkillValidationError(AgentSkillError, ValueError):
    """Raised when a skill request violates validation or safety rules."""


class AgentSkillConflictError(AgentSkillError):
    """Raised when a create request conflicts with an existing workspace skill."""


class AgentSkillNotFoundError(AgentSkillError):
    """Raised when a requested skill or proposal is missing."""


class AgentSkillProtectedError(AgentSkillError):
    """Raised when callers try to mutate protected built-in skills."""
