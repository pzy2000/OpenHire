"""Agent registry — digital employee identity and membership management."""

from __future__ import annotations

import uuid
from dataclasses import asdict, dataclass, field
from datetime import datetime, timezone
from typing import Any

from openhire.workforce.store import OpenHireStore


def _now() -> str:
    return datetime.now(timezone.utc).isoformat(timespec="seconds")


@dataclass
class AgentEntry:
    """A registered digital employee."""

    agent_id: str = ""
    name: str = ""                     # display name, e.g. "前端小王的数字员工"
    avatar: str = ""                   # selected preset avatar id
    owner_id: str = ""                 # bound human ID (feishu user_id)
    role: str = ""                     # role description
    agent_type: str = "openclaw"       # adapter type: openclaw / hermes / nanobot
    skills: list[str] = field(default_factory=list)   # e.g. ["react", "typescript"]
    skill_ids: list[str] = field(default_factory=list)  # local skill catalog IDs
    system_prompt: str = ""            # persistent role/system prompt
    agent_config: dict[str, Any] = field(default_factory=dict)  # reserved runtime config
    tools: list[str] = field(default_factory=list)    # e.g. ["github", "figma"]
    acp_agent: str = "claude"          # ACP backend agent (openclaw only)
    group_ids: list[str] = field(default_factory=list)
    container_name: str = ""           # Docker container name
    memory_namespace: str = ""         # for cross-project memory reuse
    status: str = "active"             # active / suspended / archived
    created_at: str = field(default_factory=_now)
    updated_at: str = field(default_factory=_now)

    @property
    def id(self) -> str:
        return self.agent_id

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)

    def to_public_dict(self) -> dict[str, Any]:
        return {
            "id": self.agent_id,
            "name": self.name,
            "avatar": self.avatar,
            "role": self.role,
            "skills": list(self.skills),
            "skill_ids": list(self.skill_ids),
            "system_prompt": self.system_prompt,
            "agent_type": self.agent_type,
            "agent_config": dict(self.agent_config),
            "tools": list(self.tools),
            "container_name": self.container_name,
            "status": self.status,
            "created_at": self.created_at,
            "updated_at": self.updated_at,
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> AgentEntry:
        known = {f.name for f in cls.__dataclass_fields__.values()}
        return cls(**{k: v for k, v in data.items() if k in known})


class AgentRegistry:
    """Manage digital employee registration, lookup, and group membership."""

    def __init__(self, store: OpenHireStore) -> None:
        self._store = store
        self._cache: dict[str, AgentEntry] | None = None
        self._cache_version: tuple[int, int] | None = None

    def _load(self) -> dict[str, AgentEntry]:
        version = self._store.version()
        if self._cache is None or version != self._cache_version:
            data = self._store.load()
            self._cache = {
                k: AgentEntry.from_dict(v)
                for k, v in data.get("agents", {}).items()
            }
            self._cache_version = version
        return self._cache

    def _save(self) -> None:
        entries = self._load()
        self._store.save({"agents": {k: v.to_dict() for k, v in entries.items()}})
        self._cache_version = self._store.version()

    # ---- CRUD ----

    def register(self, entry: AgentEntry) -> AgentEntry:
        entries = self._load()
        if not entry.agent_id:
            entry.agent_id = str(uuid.uuid4())[:8]
        if not entry.container_name:
            entry.container_name = f"openhire-{entry.agent_id}"
        if not entry.memory_namespace:
            entry.memory_namespace = entry.agent_id
        entry.created_at = _now()
        entry.updated_at = _now()
        entries[entry.agent_id] = entry
        self._save()
        return entry

    def get(self, agent_id: str) -> AgentEntry | None:
        return self._load().get(agent_id)

    def update(self, agent_id: str, **fields: Any) -> AgentEntry | None:
        entries = self._load()
        entry = entries.get(agent_id)
        if not entry:
            return None
        for k, v in fields.items():
            if hasattr(entry, k):
                setattr(entry, k, v)
        entry.updated_at = _now()
        self._save()
        return entry

    def remove(self, agent_id: str) -> bool:
        entries = self._load()
        if agent_id not in entries:
            return False
        del entries[agent_id]
        self._save()
        return True

    def all(self) -> list[AgentEntry]:
        return list(self._load().values())

    # ---- Queries ----

    def by_owner(self, owner_id: str) -> list[AgentEntry]:
        return [e for e in self._load().values() if e.owner_id == owner_id]

    def by_group(self, group_id: str) -> list[AgentEntry]:
        return [e for e in self._load().values()
                if group_id in e.group_ids and e.status == "active"]

    def by_skill(self, skill: str) -> list[AgentEntry]:
        skill_lower = skill.lower()
        return [e for e in self._load().values()
                if any(skill_lower in s.lower() for s in e.skills) and e.status == "active"]

    # ---- Group membership ----

    def join_group(self, agent_id: str, group_id: str) -> bool:
        entry = self.get(agent_id)
        if not entry:
            return False
        if group_id not in entry.group_ids:
            entry.group_ids.append(group_id)
            entry.updated_at = _now()
            self._save()
        return True

    def leave_group(self, agent_id: str, group_id: str) -> bool:
        entry = self.get(agent_id)
        if not entry or group_id not in entry.group_ids:
            return False
        entry.group_ids.remove(group_id)
        entry.updated_at = _now()
        self._save()
        return True

    def get_group_roster(self, group_id: str) -> list[AgentEntry]:
        return self.by_group(group_id)
