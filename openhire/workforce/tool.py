"""OpenHireTool — manage digital employees from within the agent loop."""

import inspect
import json
from pathlib import Path
from typing import Any, Awaitable, Callable

from openhire.adapters import build_default_registry
from openhire.adapters.base import ensure_running, exec_in_container
from openhire.agent.tools.base import Tool, tool_parameters
from openhire.agent.tools.schema import (
    ArraySchema,
    IntegerSchema,
    ObjectSchema,
    StringSchema,
    tool_parameters_schema,
)
from openhire.bus.events import OutboundMessage
from openhire.skill_catalog import SkillCatalogService, SkillCatalogStore
from openhire.workforce.outbound_bridge import (
    OUTBOUND_PREFIX,
    DockerOutboundMessage,
    DockerOutboundParseResult,
    clean_docker_agent_output,
    parse_docker_outbound_output,
)
from openhire.workforce.organization import OrganizationPolicy, OrganizationStore
from openhire.workforce.skill_selection import EmployeeSkillSelector, EmployeeSkillSelection
from openhire.workforce.workspace import initialize_employee_workspace


@tool_parameters(
    tool_parameters_schema(
        action=StringSchema(
            "Action to perform",
            enum=[
                "register", "list", "get", "update", "destroy",
                "suspend", "resume", "merge",
                "setup_group", "close_group", "group_roster",
                "route", "delegate",
            ],
        ),
        agent_id=StringSchema(
            "Agent ID (for get/update/destroy/suspend/resume/merge/delegate)",
            nullable=True,
        ),
        target_id=StringSchema("Target agent ID (for merge)", nullable=True),
        group_id=StringSchema("Group/chat ID (for setup_group/close_group/group_roster/route)", nullable=True),
        requester_agent_id=StringSchema("Requester employee ID for organization policy checks", nullable=True),
        target_agent_id=StringSchema("Explicit target employee ID for organization policy checks", nullable=True),
        name=StringSchema("Display name (for register/get/delegate)", nullable=True),
        owner_id=StringSchema("Owner's user ID (for register)", nullable=True),
        role=StringSchema("Role description (for register/update)", nullable=True),
        agent_type=StringSchema("Adapter type: openclaw/hermes/nanobot (for register)", nullable=True),
        skills=ArraySchema(StringSchema(), description="Skill tags (for register/update)", nullable=True),
        tools=ArraySchema(StringSchema(), description="Tool names (for register/update)", nullable=True),
        acp_agent=StringSchema("ACP backend agent for openclaw (for register)", nullable=True),
        message=StringSchema("Message content (for route)", nullable=True),
        task=StringSchema("Task content (for delegate)", nullable=True),
        timeout=IntegerSchema(
            300,
            description="Timeout in seconds for delegate (default 300, max 1800)",
            minimum=30,
            maximum=1800,
            nullable=True,
        ),
        mentions=ArraySchema(StringSchema(), description="Mentioned user IDs (for route)", nullable=True),
        members=ArraySchema(
            ObjectSchema(
                description=(
                    "Member definition with owner_id, name, role, skills, tools. "
                    "For a virtual company/team, pass one member per role; members may share "
                    "the same owner_id, and setup_group only reuses same-owner employees when "
                    "name or role matches."
                )
            ),
            description="Members list (for setup_group); use this to create multi-role teams.",
            nullable=True,
        ),
        required=["action"],
    )
)
class OpenHireTool(Tool):
    """Manage digital employees: register, assign, query, route, and lifecycle operations."""

    def __init__(
        self,
        workspace: Path,
        openhire_config: Any,
        docker_agents_config: Any | None = None,
        provider: Any | None = None,
        send_callback: Callable[[OutboundMessage], Awaitable[None] | None] | None = None,
    ) -> None:
        from openhire.workforce.lifecycle import AgentLifecycle
        from openhire.workforce.registry import AgentRegistry
        from openhire.workforce.router import MessageRouter
        from openhire.workforce.store import OpenHireStore

        self._workspace = workspace
        self._docker_agents_config = docker_agents_config
        self._adapter_registry = build_default_registry()
        store = OpenHireStore(workspace)
        self._registry = AgentRegistry(store)
        self._skill_catalog = SkillCatalogService(SkillCatalogStore(workspace))
        self._skill_selector = EmployeeSkillSelector(
            provider=provider,
            max_skills=getattr(openhire_config, "skill_selection_max", 5) if openhire_config else 5,
            retries=getattr(openhire_config, "skill_selection_retries", 5) if openhire_config else 5,
        )
        self._lifecycle = AgentLifecycle(
            self._registry,
            workspace,
            docker_agents_config=docker_agents_config,
            llm_provider=provider,
        )
        self._router = MessageRouter(
            self._registry,
            llm_threshold=openhire_config.llm_route_threshold if openhire_config else 0.7,
        )
        self._organization_policy = OrganizationPolicy(
            self._registry,
            OrganizationStore(workspace),
            default_allow_skip_level_reporting=bool(
                getattr(openhire_config, "allow_skip_level_reporting", False)
            ),
        )
        self._config = openhire_config
        self._send_callback = send_callback
        self._channel = ""
        self._chat_id = ""
        self._message_id: str | None = None
        self._sent_in_turn = False

    def set_context(self, channel: str, chat_id: str, message_id: str | None = None) -> None:
        """Set the current channel context for employee outbound bridge sends."""
        self._channel = channel
        self._chat_id = chat_id
        self._message_id = message_id

    def set_send_callback(
        self,
        callback: Callable[[OutboundMessage], Awaitable[None] | None],
    ) -> None:
        """Set the callback used to publish employee outbound messages."""
        self._send_callback = callback

    def start_turn(self) -> None:
        """Reset per-turn send tracking."""
        self._sent_in_turn = False

    async def _select_skills_for_employee(
        self,
        *,
        name: str,
        role: str,
        system_prompt: str = "",
        explicit_skills: list | None = None,
    ) -> EmployeeSkillSelection:
        if self._config and getattr(self._config, "auto_select_skills", True) is False:
            return EmployeeSkillSelection(warning="Skill selection skipped: disabled in OpenHire config.")
        return await self._skill_selector.select(
            name=name,
            role=role,
            system_prompt=system_prompt,
            explicit_skills=[str(item) for item in explicit_skills or []],
            catalog_skills=self._skill_catalog.list(),
        )

    @staticmethod
    def _merge_skill_names(explicit_skills: list | None, selected_names: list[str]) -> list[str]:
        result: list[str] = []
        seen: set[str] = set()
        for item in [*(explicit_skills or []), *selected_names]:
            text = str(item or "").strip()
            if not text:
                continue
            key = text.casefold()
            if key in seen:
                continue
            seen.add(key)
            result.append(text)
        return result

    @staticmethod
    def _output_warning(selection: EmployeeSkillSelection) -> str:
        if not selection.warning or selection.warning.startswith("Skill selection skipped:"):
            return ""
        return selection.warning

    @property
    def name(self) -> str:
        return "openhire"

    @property
    def description(self) -> str:
        return (
            "Manage digital employees (数字员工). Actions: "
            "register (create new), list (all agents), get (by ID or name), update, "
            "destroy, suspend, resume, merge (two agents), "
            "setup_group (assign agents to a group; for a company/team, create one member per role), close_group, "
            "group_roster (list agents in group), route (determine which agent handles a message), "
            "delegate (run a task as a named digital employee). New employees automatically receive "
            "the required excellent-employee skill."
        )

    @property
    def registry(self) -> Any:
        return self._registry

    @property
    def router(self) -> Any:
        return self._router

    @property
    def lifecycle(self) -> Any:
        return self._lifecycle

    async def execute(self, action: str, **kwargs: Any) -> str:
        try:
            handler = getattr(self, f"_action_{action}", None)
            if not handler:
                return f"Error: Unknown action '{action}'."
            return await handler(**{k: v for k, v in kwargs.items() if v is not None})
        except Exception as e:
            return f"Error: {e}"

    # ---- Actions ----

    async def _action_register(
        self, name: str = "", owner_id: str = "", role: str = "",
        agent_type: str = "openclaw", skills: list | None = None,
        tools: list | None = None, acp_agent: str = "claude",
        group_id: str | None = None, **kw,
    ) -> str:
        if not name or not owner_id:
            return "Error: 'name' and 'owner_id' are required for register."
        selection = await self._select_skills_for_employee(
            name=name,
            role=role,
            explicit_skills=skills or [],
        )
        effective_tools = tools or []
        effective_group_id = group_id or self._default_registration_group_id(effective_tools)
        entry = await self._lifecycle.create_agent(
            name=name, owner_id=owner_id, role=role,
            agent_type=agent_type,
            skills=self._merge_skill_names(skills or [], selection.skill_names),
            skill_ids=selection.skill_ids,
            tools=effective_tools,
            acp_agent=acp_agent, group_id=effective_group_id,
        )
        warning = self._output_warning(selection)
        suffix = f"\nSkill selection warning: {warning}" if warning else ""
        return f"Registered: {entry.name} (id={entry.agent_id}, container={entry.container_name}){suffix}"

    async def _action_list(self, **kw) -> str:
        agents = self._registry.all()
        if not agents:
            return "No digital employees registered."
        lines = []
        for a in agents:
            lines.append(
                f"- {a.agent_id}: {a.name} | role={a.role} | type={a.agent_type} | "
                f"status={a.status} | skills={','.join(a.skills)} | groups={','.join(a.group_ids)}"
            )
        return "\n".join(lines)

    async def _action_get(self, agent_id: str = "", **kw) -> str:
        entry, error = self._resolve_entry(agent_id=agent_id, name=kw.get("name", ""))
        if error:
            return error
        assert entry is not None
        return json.dumps(entry.to_dict(), indent=2, ensure_ascii=False)

    async def _action_update(self, agent_id: str = "", **kw) -> str:
        if not agent_id:
            return "Error: 'agent_id' is required."
        fields = {k: v for k, v in kw.items() if k in ("role", "skills", "tools", "name")}
        if not fields:
            return "Error: No fields to update."
        entry = self._registry.update(agent_id, **fields)
        if not entry:
            return f"Agent '{agent_id}' not found."
        return f"Updated: {entry.name} ({agent_id})"

    async def _action_destroy(self, agent_id: str = "", **kw) -> str:
        if not agent_id:
            return "Error: 'agent_id' is required."
        ok = await self._lifecycle.destroy_agent(agent_id)
        return f"Destroyed: {agent_id}" if ok else f"Agent '{agent_id}' not found."

    async def _action_suspend(self, agent_id: str = "", **kw) -> str:
        if not agent_id:
            return "Error: 'agent_id' is required."
        ok = await self._lifecycle.suspend_agent(agent_id)
        return f"Suspended: {agent_id}" if ok else f"Cannot suspend '{agent_id}'."

    async def _action_resume(self, agent_id: str = "", **kw) -> str:
        if not agent_id:
            return "Error: 'agent_id' is required."
        ok = await self._lifecycle.resume_agent(agent_id)
        return f"Resumed: {agent_id}" if ok else f"Cannot resume '{agent_id}'."

    async def _action_merge(self, agent_id: str = "", target_id: str = "", **kw) -> str:
        if not agent_id or not target_id:
            return "Error: 'agent_id' (source) and 'target_id' are required."
        ok = await self._lifecycle.merge_agents(agent_id, target_id)
        return f"Merged {agent_id} into {target_id}" if ok else "Merge failed."

    async def _action_setup_group(
        self, group_id: str = "", members: list | None = None, **kw,
    ) -> str:
        if not group_id or not members:
            return "Error: 'group_id' and 'members' are required."
        enriched_members: list[dict[str, Any]] = []
        warnings: list[str] = []
        for member in members:
            if not isinstance(member, dict):
                continue
            next_member = dict(member)
            selection = await self._select_skills_for_employee(
                name=str(next_member.get("name") or ""),
                role=str(next_member.get("role") or ""),
                system_prompt=str(next_member.get("system_prompt") or ""),
                explicit_skills=next_member.get("skills") or [],
            )
            next_member["skills"] = self._merge_skill_names(next_member.get("skills") or [], selection.skill_names)
            next_member["skill_ids"] = selection.skill_ids
            if warning := self._output_warning(selection):
                warnings.append(f"{next_member.get('name') or next_member.get('role')}: {warning}")
            enriched_members.append(next_member)
        agents = await self._lifecycle.setup_group(group_id, enriched_members)
        names = [f"{a.name} ({a.agent_id})" for a in agents]
        suffix = f"\nSkill selection warning: {'; '.join(warnings)}" if warnings else ""
        return f"Group {group_id} set up with {len(agents)} agents: {', '.join(names)}{suffix}"

    async def _action_close_group(self, group_id: str = "", **kw) -> str:
        if not group_id:
            return "Error: 'group_id' is required."
        count = await self._lifecycle.close_group(group_id)
        return f"Closed group {group_id}: {count} agents removed."

    async def _action_group_roster(self, group_id: str = "", **kw) -> str:
        if not group_id:
            return "Error: 'group_id' is required."
        roster = self._registry.get_group_roster(group_id)
        if not roster:
            return f"No agents in group {group_id}."
        lines = [f"- {a.agent_id}: {a.name} (role={a.role}, skills={','.join(a.skills)})" for a in roster]
        return "\n".join(lines)

    async def _action_route(
        self, group_id: str = "", message: str = "",
        mentions: list | None = None, requester_agent_id: str = "", **kw,
    ) -> str:
        if not group_id or not message:
            return "Error: 'group_id' and 'message' are required."
        decision = await self._router.route(
            content=message, sender_id="", group_id=group_id, mentions=mentions,
        )
        if not decision.target_agents:
            return f"No agent matched. Strategy: {decision.strategy}. Reason: {decision.reason}"
        if requester_agent_id:
            allowed_targets: list[str] = []
            blocked_reasons: list[str] = []
            for target_agent_id in decision.target_agents:
                policy_decision = self._organization_policy.can_communicate(requester_agent_id, target_agent_id)
                if policy_decision.allowed:
                    allowed_targets.append(target_agent_id)
                else:
                    blocked_reasons.append(policy_decision.reason)
            if not allowed_targets:
                return (
                    "No agent matched. Strategy: organization_policy. "
                    f"Reason: {'; '.join(blocked_reasons) or 'all targets were blocked'}"
                )
            decision.target_agents = allowed_targets
        agents_str = ", ".join(decision.target_agents)
        return f"Route to: {agents_str} | Strategy: {decision.strategy} | Reason: {decision.reason}"

    async def _action_delegate(
        self,
        agent_id: str = "",
        name: str = "",
        task: str = "",
        timeout: int = 300,
        requester_agent_id: str = "",
        **kw,
    ) -> str:
        normalized_task = str(task or "").strip()
        if not normalized_task:
            return "Error: 'task' is required."

        entry, error = self._resolve_entry(agent_id=agent_id, name=name)
        if error:
            return error
        assert entry is not None
        if entry.status != "active":
            return f"Agent '{entry.agent_id}' is not active."

        policy_decision = self._organization_policy.can_communicate(requester_agent_id, entry.agent_id)
        if not policy_decision.allowed:
            return f"Organization policy blocked delegate: {policy_decision.reason}"

        adapter = self._adapter_registry.get(entry.agent_type)
        if not adapter:
            return f"Error: Unsupported agent_type '{entry.agent_type}' for delegate."

        merged_cfg = self._delegate_agent_config(entry)
        delegated_task = self._compose_delegate_task(
            entry,
            self._with_outbound_bridge_instruction(entry, normalized_task),
        )
        workspace = initialize_employee_workspace(self._workspace, entry)
        container_name = await ensure_running(
            adapter=adapter,
            instance_name=entry.agent_id,
            agent_cfg=merged_cfg,
            workspace=workspace,
        )
        result = await exec_in_container(
            container_name=container_name,
            adapter=adapter,
            task=delegated_task,
            role=entry.role or None,
            tools=entry.tools or None,
            skills=entry.skills or None,
            timeout=timeout,
            workspace=workspace,
        )
        result = await self._process_delegate_outbound(entry, result)
        return (
            f"Delegated to {entry.name} (id={entry.agent_id}, type={entry.agent_type}).\n"
            f"Result:\n{result}"
        )

    def _resolve_entry(self, agent_id: str = "", name: str = "") -> tuple[Any | None, str | None]:
        normalized_id = str(agent_id or "").strip()
        if normalized_id:
            entry = self._registry.get(normalized_id)
            if entry is None:
                return None, f"Agent '{normalized_id}' not found."
            return entry, None

        normalized_name = str(name or "").strip()
        if not normalized_name:
            return None, "Error: 'agent_id' or 'name' is required."

        matches = [
            entry for entry in self._registry.all()
            if entry.name.casefold() == normalized_name.casefold()
        ]
        if not matches:
            return None, f"Agent '{normalized_name}' not found."
        if len(matches) > 1:
            return None, (
                f"Multiple agents named '{normalized_name}' found. "
                "Use 'agent_id' instead."
            )
        return matches[0], None

    def _delegate_agent_config(self, entry: Any) -> dict[str, Any]:
        docker_cfg = self._docker_agents_config
        if docker_cfg is None or not getattr(docker_cfg, "enabled", False):
            raise RuntimeError("Digital employee delegation requires dockerAgents to be enabled.")

        cfg_obj = getattr(docker_cfg, "agents", {}).get(entry.agent_type)
        if cfg_obj and not getattr(cfg_obj, "enabled", True):
            raise RuntimeError(
                f"Agent type '{entry.agent_type}' is disabled in dockerAgents configuration."
            )
        cfg = cfg_obj.model_dump() if hasattr(cfg_obj, "model_dump") else dict(cfg_obj or {})
        return {
            **cfg,
            **dict(entry.agent_config or {}),
            "container_name": entry.container_name,
        }

    @staticmethod
    def _compose_delegate_task(entry: Any, task: str) -> str:
        system_prompt = str(entry.system_prompt or "").strip()
        if not system_prompt:
            return task
        return (
            "Follow the employee system prompt while completing the task.\n\n"
            f"[Employee System Prompt]\n{system_prompt}\n[/Employee System Prompt]\n\n"
            f"[Task]\n{task}\n[/Task]"
        )

    def _with_outbound_bridge_instruction(self, entry: Any, task: str) -> str:
        if not self._can_offer_outbound_bridge(entry):
            return task
        return (
            "[OpenHire Outbound Bridge]\n"
            "Your final response will be sent to the current group by OpenHire. "
            "Write only the message content that should appear in the group. "
            "Do not include explanations, code fences, channel, or chat_id. "
            "If you must attach files, optionally output exactly one line like:\n"
            f"{OUTBOUND_PREFIX} {{\"content\":\"message text\",\"media\":[\"relative/or/workspace/file\"]}}\n"
            "[/OpenHire Outbound Bridge]\n\n"
            f"{task}"
        )

    def _can_offer_outbound_bridge(self, entry: Any) -> bool:
        return (
            self._send_callback is not None
            and bool(self._channel)
            and bool(self._chat_id)
            and self._has_message_tool(entry)
            and self._chat_id in set(getattr(entry, "group_ids", []) or [])
        )

    async def _process_delegate_outbound(self, entry: Any, output: str) -> str:
        parsed = parse_docker_outbound_output(output, workspace=self._workspace)
        if not parsed.messages and not parsed.errors and not self._can_offer_outbound_bridge(entry):
            return output

        if not parsed.messages and self._can_offer_outbound_bridge(entry):
            fallback = clean_docker_agent_output(parsed.cleaned_output or output)
            if fallback:
                parsed.messages.append(DockerOutboundMessage(content=fallback, media=[]))

        sent_count, delivery_errors = await self._deliver_outbound_messages(entry, parsed)
        lines: list[str] = []
        if parsed.cleaned_output and not sent_count:
            lines.append(parsed.cleaned_output)
        if sent_count:
            lines.append(f"Outbound bridge: sent {sent_count} message(s).")
        errors = delivery_errors if sent_count else [*parsed.errors, *delivery_errors]
        for error in errors:
            lines.append(f"Outbound bridge error: {error}")
        return "\n".join(lines) or "(no output)"

    async def _deliver_outbound_messages(
        self,
        entry: Any,
        parsed: DockerOutboundParseResult,
    ) -> tuple[int, list[str]]:
        if not parsed.messages:
            return 0, []

        validation_error = self._outbound_delivery_error(entry)
        if validation_error:
            return 0, [validation_error]

        assert self._send_callback is not None
        sent = 0
        metadata = {"message_id": self._message_id} if self._message_id else {}
        for message in parsed.messages:
            outbound = OutboundMessage(
                channel=self._channel,
                chat_id=self._chat_id,
                content=f"【{entry.name}】{message.content}",
                media=message.media,
                metadata=metadata,
            )
            result = self._send_callback(outbound)
            if inspect.isawaitable(result):
                await result
            sent += 1
        if sent:
            self._sent_in_turn = True
        return sent, []

    def _outbound_delivery_error(self, entry: Any) -> str | None:
        if not self._has_message_tool(entry):
            return f"Agent '{entry.agent_id}' does not have message tool permission."
        if not self._channel or not self._chat_id:
            return "No current channel/chat context is available."
        if self._chat_id not in set(getattr(entry, "group_ids", []) or []):
            return f"Agent '{entry.agent_id}' is not a member of chat '{self._chat_id}'."
        if self._send_callback is None:
            return "Outbound message sending is not configured."
        return None

    @staticmethod
    def _has_message_tool(entry: Any) -> bool:
        return any(str(tool).casefold() == "message" for tool in getattr(entry, "tools", []) or [])

    def _default_registration_group_id(self, tools: list | None) -> str | None:
        if self._channel != "feishu" or not self._chat_id.startswith("oc_"):
            return None
        if not any(str(tool).casefold() == "message" for tool in tools or []):
            return None
        return self._chat_id
