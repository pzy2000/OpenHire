"""Agent lifecycle — create, destroy, suspend, resume, merge digital employees."""

from __future__ import annotations

import asyncio
from typing import TYPE_CHECKING, Any

from loguru import logger

from openhire.adapters import build_default_registry
from openhire.adapters.base import ensure_running, inspect_container_status
from openhire.workforce.employee_prompt import (
    compose_case_bootstrap_files,
    compose_employee_bootstrap_files,
    read_container_bootstrap_file,
)
from openhire.workforce.required_skill import apply_required_employee_skill_contract
from openhire.workforce.registry import AgentEntry, AgentRegistry
from openhire.workforce.workspace import (
    default_employee_config_text,
    ensure_employee_workspace_dir,
    write_employee_bootstrap_files,
)

if TYPE_CHECKING:
    from pathlib import Path


class AgentLifecycle:
    """Manage the full lifecycle of digital employees and their containers."""

    def __init__(
        self,
        registry: AgentRegistry,
        workspace: "Path",
        docker_agents_config: Any | None = None,
        llm_provider: Any | None = None,
    ) -> None:
        self._registry = registry
        self._workspace = workspace
        self._docker_agents_config = docker_agents_config
        self._llm_provider = llm_provider
        self._adapter_registry = build_default_registry()

    async def create_agent(
        self,
        name: str,
        avatar: str = "",
        owner_id: str = "",
        role: str = "",
        agent_type: str = "openclaw",
        skills: list[str] | None = None,
        skill_ids: list[str] | None = None,
        system_prompt: str = "",
        agent_config: dict[str, Any] | None = None,
        tools: list[str] | None = None,
        bootstrap_files: dict[str, str] | None = None,
        acp_agent: str = "claude",
        group_id: str | None = None,
    ) -> AgentEntry:
        """Register a new digital employee and ensure its container is ready."""
        required_skills, required_skill_ids, required_system_prompt = apply_required_employee_skill_contract(
            skills=skills,
            skill_ids=skill_ids,
            system_prompt=system_prompt,
        )
        entry = self._registry.register(AgentEntry(
            name=name,
            avatar=avatar,
            owner_id=owner_id,
            role=role,
            agent_type=agent_type,
            skills=required_skills,
            skill_ids=required_skill_ids,
            system_prompt=required_system_prompt,
            agent_config=agent_config or {},
            tools=tools or [],
            acp_agent=acp_agent,
            group_ids=[group_id] if group_id else [],
        ))
        ensure_employee_workspace_dir(self._workspace, entry)
        try:
            container_name = await self._ensure_agent_container(entry)
            await self._initialize_agent_bootstrap_files(
                entry,
                container_name,
                bootstrap_files=bootstrap_files,
            )
        except Exception:
            self._registry.remove(entry.agent_id)
            raise
        logger.info("Created digital employee: {} ({})", entry.name, entry.agent_id)
        return entry

    async def _ensure_agent_container(self, entry: AgentEntry) -> str | None:
        docker_cfg = self._docker_agents_config
        if not docker_cfg or not getattr(docker_cfg, "enabled", False):
            return None

        adapter = self._adapter_registry.get(entry.agent_type)
        if not adapter:
            raise RuntimeError(f"Unsupported agent_type '{entry.agent_type}' for container creation.")

        cfg_obj = getattr(docker_cfg, "agents", {}).get(entry.agent_type)
        if cfg_obj and not getattr(cfg_obj, "enabled", True):
            raise RuntimeError(f"Agent type '{entry.agent_type}' is disabled in dockerAgents configuration.")

        cfg = cfg_obj.model_dump() if hasattr(cfg_obj, "model_dump") else dict(entry.agent_config or {})
        if cfg_obj is None:
            cfg = {}
        merged_cfg = {
            **cfg,
            **dict(entry.agent_config or {}),
            "container_name": entry.container_name,
        }
        employee_workspace = ensure_employee_workspace_dir(self._workspace, entry)
        container_name = await ensure_running(
            adapter=adapter,
            instance_name=entry.agent_id,
            agent_cfg=merged_cfg,
            workspace=employee_workspace,
        )
        self._registry.update(
            entry.agent_id,
            container_name=container_name,
            status="active",
            agent_config=dict(entry.agent_config or {}),
        )
        return container_name

    async def _initialize_agent_bootstrap_files(
        self,
        entry: AgentEntry,
        container_name: str | None,
        *,
        bootstrap_files: dict[str, str] | None = None,
    ) -> None:
        if bootstrap_files is not None:
            write_employee_bootstrap_files(
                self._workspace,
                entry,
                compose_case_bootstrap_files(bootstrap_files),
            )
            return
        base_files = await self._load_runtime_bootstrap_templates(entry, container_name)
        files = await compose_employee_bootstrap_files(
            entry,
            base_files=base_files,
            llm_provider=self._llm_provider,
            retries=3,
        )
        write_employee_bootstrap_files(self._workspace, entry, files)

    async def _load_runtime_bootstrap_templates(
        self,
        entry: AgentEntry,
        container_name: str | None,
    ) -> dict[str, str]:
        adapter = self._adapter_registry.get(entry.agent_type) if container_name else None
        templates: dict[str, str] = {}
        for filename in ("SOUL.md", "AGENTS.md"):
            content = ""
            if adapter is not None and container_name:
                content = await read_container_bootstrap_file(container_name, adapter, filename)
                if not content:
                    logger.warning(
                        "Falling back to OpenHire {} template for employee {} ({})",
                        filename,
                        entry.name,
                        entry.agent_id,
                    )
            templates[filename] = content or default_employee_config_text(filename)
        return templates

    async def restore_active_agents(self) -> dict[str, int]:
        """Ensure all active registered employees have running containers."""
        entries = self._registry.all()
        if not self._docker_agents_config or not getattr(self._docker_agents_config, "enabled", False):
            return {
                "restored": 0,
                "failed": 0,
                "skipped": len(entries),
            }
        active_entries = [entry for entry in entries if entry.status == "active"]
        stats = {
            "restored": 0,
            "failed": 0,
            "skipped": len(entries) - len(active_entries),
        }
        if not active_entries:
            return stats

        async def restore_one(entry: AgentEntry) -> None:
            try:
                await self._ensure_agent_container(entry)
            except Exception as exc:
                stats["failed"] += 1
                logger.warning(
                    "Failed to restore digital employee container {} ({}): {}",
                    entry.name,
                    entry.agent_id,
                    exc,
                )
                return
            stats["restored"] += 1

        await asyncio.gather(*(restore_one(entry) for entry in active_entries))
        logger.info(
            "Digital employee container restore complete: restored={} failed={} skipped={}",
            stats["restored"],
            stats["failed"],
            stats["skipped"],
        )
        return stats

    async def destroy_agent(self, agent_id: str, archive_memory: bool = True) -> bool:
        """Stop container, optionally archive memory, and remove registration."""
        entry = self._registry.get(agent_id)
        if not entry:
            return False

        # Stop and remove container
        await self._stop_container(entry.container_name)
        await self._remove_container(entry.container_name)

        # Archive status before removal
        if archive_memory:
            self._registry.update(agent_id, status="archived")
            logger.info("Archived digital employee: {} ({})", entry.name, agent_id)
        else:
            self._registry.remove(agent_id)
            logger.info("Destroyed digital employee: {} ({})", entry.name, agent_id)

        return True

    async def suspend_agent(self, agent_id: str) -> bool:
        """Stop container but keep registration (can be resumed later)."""
        entry = self._registry.get(agent_id)
        if not entry or entry.status != "active":
            return False

        await self._stop_container(entry.container_name)
        self._registry.update(agent_id, status="suspended")
        logger.info("Suspended digital employee: {} ({})", entry.name, agent_id)
        return True

    async def resume_agent(self, agent_id: str) -> bool:
        """Resume a suspended agent by restarting its container."""
        entry = self._registry.get(agent_id)
        if not entry or entry.status != "suspended":
            return False

        self._registry.update(agent_id, status="active")
        logger.info("Resumed digital employee: {} ({})", entry.name, agent_id)
        return True

    async def merge_agents(self, source_id: str, target_id: str) -> bool:
        """Merge source agent's skills and group memberships into target, then archive source."""
        source = self._registry.get(source_id)
        target = self._registry.get(target_id)
        if not source or not target:
            return False

        # Merge skills (deduplicate)
        merged_skills = list(dict.fromkeys(target.skills + source.skills))
        # Merge local skill bindings (deduplicate)
        merged_skill_ids = list(dict.fromkeys(target.skill_ids + source.skill_ids))
        # Merge tools (deduplicate)
        merged_tools = list(dict.fromkeys(target.tools + source.tools))
        # Merge group memberships
        merged_groups = list(dict.fromkeys(target.group_ids + source.group_ids))

        self._registry.update(
            target_id,
            skills=merged_skills,
            skill_ids=merged_skill_ids,
            tools=merged_tools,
            group_ids=merged_groups,
        )

        # Archive source
        await self._stop_container(source.container_name)
        self._registry.update(source_id, status="archived")

        logger.info("Merged {} into {}", source.name, target.name)
        return True

    @staticmethod
    def _normalize_match_text(value: Any) -> str:
        return "".join(str(value or "").casefold().split())

    def _find_reusable_group_agent(
        self,
        *,
        owner_id: str,
        group_id: str,
        member: dict[str, Any],
    ) -> AgentEntry | None:
        member_name = self._normalize_match_text(member.get("name"))
        member_role = self._normalize_match_text(member.get("role"))
        matches: list[AgentEntry] = []
        for entry in self._registry.by_owner(owner_id):
            if entry.status != "active":
                continue
            if member_name and self._normalize_match_text(entry.name) == member_name:
                matches.append(entry)
                continue
            if member_role and self._normalize_match_text(entry.role) == member_role:
                matches.append(entry)

        if not matches:
            return None
        for entry in matches:
            if group_id in entry.group_ids:
                return entry
        return matches[0]

    async def setup_group(
        self, group_id: str, members: list[dict[str, Any]],
    ) -> list[AgentEntry]:
        """Set up digital employees for a new group/project.

        Each member dict should have: owner_id, name, role, skills, tools.
        The same owner may have multiple role-specific digital employees; reuse
        only when an active employee for that owner already matches the member
        by name or role.
        """
        result_slots: list[AgentEntry | asyncio.Task[AgentEntry]] = []
        creation_tasks: list[asyncio.Task[AgentEntry]] = []
        pending_creations: list[tuple[str, str, str, asyncio.Task[AgentEntry]]] = []
        for member in members:
            owner_id = member.get("owner_id", "")
            if not owner_id:
                continue

            agent = self._find_reusable_group_agent(
                owner_id=owner_id,
                group_id=group_id,
                member=member,
            )

            if agent:
                self._registry.join_group(agent.agent_id, group_id)
                result_slots.append(agent)
                continue

            member_name = self._normalize_match_text(member.get("name"))
            member_role = self._normalize_match_text(member.get("role"))
            pending_task: asyncio.Task[AgentEntry] | None = None
            for pending_owner_id, pending_name, pending_role, task in pending_creations:
                if pending_owner_id != owner_id:
                    continue
                if member_name and member_name == pending_name:
                    pending_task = task
                    break
                if member_role and member_role == pending_role:
                    pending_task = task
                    break

            if pending_task is not None:
                result_slots.append(pending_task)
                continue

            task = asyncio.create_task(
                self.create_agent(
                    name=member.get("name", f"{owner_id}的数字员工"),
                    avatar=member.get("avatar", ""),
                    owner_id=owner_id,
                    role=member.get("role", ""),
                    agent_type=member.get("agent_type", "openclaw"),
                    skills=member.get("skills", []),
                    skill_ids=member.get("skill_ids", []),
                    system_prompt=member.get("system_prompt", ""),
                    agent_config=member.get("agent_config", {}),
                    tools=member.get("tools", []),
                    acp_agent=member.get("acp_agent", "claude"),
                    group_id=group_id,
                )
            )
            creation_tasks.append(task)
            pending_creations.append((owner_id, member_name, member_role, task))
            result_slots.append(task)

        if creation_tasks:
            task_results = await asyncio.gather(*creation_tasks, return_exceptions=True)
            first_error = next(
                (result for result in task_results if isinstance(result, BaseException)),
                None,
            )
            if first_error is not None:
                raise first_error

        results = [
            slot.result() if isinstance(slot, asyncio.Task) else slot
            for slot in result_slots
        ]

        logger.info("Set up group {} with {} agents", group_id, len(results))
        return results

    async def close_group(self, group_id: str, archive: bool = True) -> int:
        """Remove all agents from a group. Suspend agents with no remaining groups."""
        roster = self._registry.get_group_roster(group_id)
        count = 0
        for agent in roster:
            self._registry.leave_group(agent.agent_id, group_id)
            count += 1
            # If agent has no remaining groups, suspend it
            refreshed = self._registry.get(agent.agent_id)
            if refreshed and not refreshed.group_ids:
                if archive:
                    await self.suspend_agent(agent.agent_id)

        logger.info("Closed group {}: {} agents removed", group_id, count)
        return count

    # ---- Container helpers ----

    async def _stop_container(self, container_name: str) -> None:
        try:
            status = await inspect_container_status(container_name)
            if status == "running":
                proc = await asyncio.create_subprocess_exec(
                    "docker", "stop", container_name,
                    stdout=asyncio.subprocess.DEVNULL,
                    stderr=asyncio.subprocess.DEVNULL,
                )
                await proc.wait()
        except Exception as exc:
            logger.warning("Failed to stop container {}: {}", container_name, exc)

    async def _remove_container(self, container_name: str) -> None:
        try:
            status = await inspect_container_status(container_name)
            if status is not None:
                proc = await asyncio.create_subprocess_exec(
                    "docker", "rm", "-f", container_name,
                    stdout=asyncio.subprocess.DEVNULL,
                    stderr=asyncio.subprocess.DEVNULL,
                )
                await proc.wait()
        except Exception as exc:
            logger.warning("Failed to remove container {}: {}", container_name, exc)
