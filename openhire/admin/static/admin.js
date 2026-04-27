const POLL_INTERVAL_MS = 2000;
const EMPLOYEE_POLL_INTERVAL_MS = 10000;
const RUNTIME_HISTORY_MAX_SAMPLES = 180;
const RUNTIME_TIMELINE_MINUTE_MS = 60 * 1000;
const RUNTIME_TIMELINE_HOUR_MINUTES = 60;
const RUNTIME_TIMELINE_DAY_MINUTES = 24 * RUNTIME_TIMELINE_HOUR_MINUTES;
const CLAWHUB_SEARCH_MAX_ATTEMPTS = 2;
const CLAWHUB_SEARCH_RETRY_DELAY_MS = 700;
const LOCAL_SKILL_IMPORT_BUTTON_LABEL = "Import From Local Skills";
const SOUL_LIBRARY_LOAD_BUTTON_LABEL = "Load SoulBanner Roles";
const WEB_SKILL_IMPORT_BUTTON_LABEL = "Import From Web";
const LOCAL_SKILL_PREVIEW_TITLE = "Local Import Preview";
const WEB_SKILL_PREVIEW_TITLE = "Web Import Preview";
const WEB_SKILL_URL_PLACEHOLDER = "Paste a public SKILL.md URL";
const CUSTOM_ROLE_TEMPLATE_ID = "custom-role";
const REQUIRED_EMPLOYEE_SKILL_ID = "excellent-employee";
const EMPLOYEE_LIST_COLLAPSED_COUNT = 4;
const SKILL_LIST_COLLAPSED_COUNT = 4;
const DEFAULT_EMPLOYEE_SORT_MODE = "type";
const EMPLOYEE_SORT_STORAGE_KEY = "openhire.admin.employeeSortMode";
const SMART_SKILL_RECOMMEND_STORAGE_KEY = "openhire.admin.smartSkillRecommendEnabled";
const LANGUAGE_STORAGE_KEY = "openhire.admin.language";
const THEME_STORAGE_KEY = "openhire.admin.theme";
const SYSTEM_THEME_QUERY = "(prefers-color-scheme: dark)";
const DEFAULT_THEME = "dark";
const EMPLOYEE_CONFIG_FILES = ["SOUL.md", "AGENTS.md", "HEARTBEAT.md", "TOOLS.md", "USER.md"];
const CREATE_EMPLOYEE_PROGRESS_INTERVAL_MS = 450;
const CREATE_EMPLOYEE_PROGRESS_STAGES = [
  { label: "Invoking LLM to create SOUL.md and AGENTS.md", start: 0, end: 55, durationMs: 18000 },
  { label: "Creating Docker Container", start: 55, end: 92, durationMs: 90000 },
  { label: "Finalizing employee workspace", start: 92, end: 99, durationMs: 15000 },
];
const CASE_IMPORT_PROGRESS_INTERVAL_MS = 450;
const CASE_IMPORT_PROGRESS_STAGES = [
  { label: "Invoking LLM to create SOUL.md and AGENTS.md", start: 0, end: 55, durationMs: 18000 },
  { label: "Creating Docker Container", start: 55, end: 92, durationMs: 90000 },
  { label: "Finalizing case import", start: 92, end: 99, durationMs: 15000 },
];
const EMPLOYEE_SORT_MODES = {
  type: "Type",
  updated: "Last Modified",
  created: "Created",
};

const TRANSLATIONS = {
  en: {
    "document.title": "OpenHire Admin",
    "nav.subtitle": "Digital employee orchestration console",
    "nav.command_center": "Command Center",
    "nav.control_center": "Control Center",
    "nav.organization": "Organization",
    "nav.employee_studio": "Digital Employees",
    "nav.resource_hub": "Resource Hub",
    "nav.agent_skills": "Agent Skills",
    "nav.infrastructure": "Infrastructure",
    "nav.dream": "Dream",
    "nav.snapshot.pending": "Snapshot pending",
    "nav.snapshot.current": "Snapshot {value}",
    "hero.eyebrow": "Digital Employee Orchestration Platform",
    "hero.title": "Command Center",
    "hero.copy": "Operate runtime, employees, skills, and reusable cases from one command surface.",
    "preferences.language.label": "Language",
    "preferences.theme.toggle": "{mode}",
    "preferences.theme.dark": "Dark Mode",
    "preferences.theme.light": "Light Mode",
    "preferences.group.aria_label": "Admin preferences",
    "links.github": "OpenHire on GitHub",
    "companion.action.pat": "Pat",
    "companion.action.feed": "Feed",
    "companion.action.chat": "Chat",
    "companion.action.sound_on": "Sound On",
    "companion.action.sound_off": "Sound Off",
    "companion.action.debug": "Inspect",
    "companion.chat.title": "Talk to the companion",
    "companion.chat.placeholder": "Say something to the companion...",
    "companion.chat.send": "Send",
    "companion.chat.toggle.label": "Chat backend",
    "companion.chat.toggle.side": "Side channel",
    "companion.chat.toggle.main": "Main agent",
    "companion.mood.idle": "Standing by",
    "companion.fallback.body": "Live2D runtime offline; chatting with neon outline mode.",
    "companion.hotspot.aria": "Tap the companion",
    "section.control.title": "Control Center",
    "section.control.copy": "Track live runtime health, context pressure, and primary orchestration actions.",
    "section.organization.title": "Organization",
    "section.organization.copy": "Arrange reporting lines, validate hierarchy, and adjust employee capabilities from one canvas.",
    "section.employees.title": "Digital Employees",
    "section.employees.copy": "Create digital employees backed by Docker workers and preview roles, settings, skills, and tools.",
    "section.resource.title": "Resource Hub",
    "section.resource.copy": "Switch between reusable cases, personas, and skills without leaving the admin workspace.",
    "section.agent_skills.title": "Agent Skills Workbench",
    "section.agent_skills.copy": "Manage the local workspace skills that agents can actually discover, load, and reuse.",
    "section.infrastructure.title": "Infrastructure",
    "section.infrastructure.copy": "Inspect Docker workers, container resources, and runtime source details.",
    "section.dream.title": "Dream",
    "section.dream.copy": "Inspect long-term memory, Dream history, and safe restore points across the main agent and digital employees.",
    "section.soul.title": "Soul Library",
    "section.soul.copy": "Browse SoulBanner personas, import them into the local catalog, and reuse that metadata when creating employees.",
    "section.skills.title": "Skill Catalog",
    "section.skills.copy": "Search public ClawHub skills, import them into the local catalog, and reuse that metadata when creating employees.",
    "resource.tab.cases": "Cases",
    "resource.tab.personas": "Personas",
    "resource.tab.skills": "Skills",
    "button.create_employee": "Create Employee",
    "button.smart_recommend": "Smart Recommend",
    "button.import_local_skills": "Import From Local Skills",
    "button.import_web": "Import From Web",
    "button.select": "Select",
    "button.delete_selected": "Delete Selected",
    "button.export_selected": "Export Selected",
    "button.cancel": "Cancel",
    "button.back": "Back",
    "button.next": "Next",
    "button.confirm_import": "Confirm Import",
    "button.preview_import": "Preview Import",
    "button.search_clawhub": "Search ClawHub",
    "button.preview_from_web": "Preview From Web",
    "button.reload_soulbanner": "Reload SoulBanner Roles",
    "button.load_soulbanner": "Load SoulBanner Roles",
    "button.reload_mbti_sbti": "Reload Mbti/Sbti Roles",
    "button.load_mbti_sbti": "Load Mbti/Sbti",
    "button.import_config": "Import Config",
    "button.clear_context": "Clear Context",
    "button.compact_context": "Compact Context",
    "button.clear_short": "Clear",
    "button.compact_short": "Compact",
    "button.clearing": "Clearing...",
    "button.compacting": "Compacting...",
    "button.close_create_modal": "Close create employee dialog",
    "button.close_case_modal": "Close case dialog",
    "button.close_confirmation_modal": "Close confirmation dialog",
    "button.importing": "Importing...",
    "button.fetching": "Fetching...",
    "button.searching": "Searching...",
    "button.loading": "Loading...",
    "agent_skills.refresh": "Refresh",
    "agent_skills.create": "Create Skill",
    "agent_skills.create_title": "New workspace skill",
    "agent_skills.create_copy": "Create a real workspace skill under workspace/skills.",
    "agent_skills.name": "Skill name",
    "agent_skills.description": "Description",
    "agent_skills.create_submit": "Create Workspace Skill",
    "agent_skills.cancel_create": "Cancel",
    "agent_skills.search": "Search agent skills",
    "agent_skills.filter_all": "All",
    "agent_skills.filter_workspace": "Workspace",
    "agent_skills.filter_builtin": "Built-in",
    "agent_skills.empty": "No agent skills found.",
    "agent_skills.select_empty": "Select a skill to inspect SKILL.md, supporting files, and proposal history.",
    "agent_skills.progressive": "Progressive disclosure: metadata stays visible, SKILL.md loads on selection, and resources stay in scripts/, references/, or assets/.",
    "agent_skills.bound_employees": "bound employees",
    "agent_skills.category_label": "category",
    "agent_skills.uncategorized": "uncategorized",
    "agent_skills.files": "Supporting files",
    "agent_skills.proposals": "Proposals",
    "agent_skills.no_files": "No supporting files.",
    "agent_skills.no_proposals": "No pending proposals.",
    "agent_skills.edit": "Edit",
    "agent_skills.save": "Save",
    "agent_skills.cancel": "Cancel",
    "agent_skills.package": "Package .skill",
    "agent_skills.delete": "Delete",
    "agent_skills.approve": "Approve",
    "agent_skills.discard": "Discard",
    "agent_skills.file_path": "scripts/helper.py",
    "agent_skills.file_content": "File content",
    "agent_skills.write_file": "Write File",
    "agent_skills.install": "Install to Agent Skills",
    "agent_skills.installed": "Installed to Agent Skills.",
    "agent_skills.package_ready": "Package ready: {path}",
    "agent_skills.error": "Agent skill error: {value}",
    "button.cook": "Cook",
    "button.cooking": "Cooking...",
    "button.creating": "Creating...",
    "button.collapse": "Collapse",
    "button.show_more": "Show More (+{count})",
    "organization.refresh": "Refresh",
    "organization.save": "Save Organization",
    "organization.saving": "Saving...",
    "organization.loading": "Loading organization...",
    "organization.empty": "Create digital employees before arranging reporting lines.",
    "organization.canvas": "Reporting Canvas",
    "organization.detail": "Employee Capabilities",
    "organization.no_selection": "Select an employee node to edit reporting and capabilities.",
    "organization.global_skip": "Allow skip-level reporting globally",
    "organization.employee_skip": "Allow this employee to skip levels",
    "organization.manager": "Direct manager",
    "organization.no_manager": "No direct manager",
    "organization.reports": "Direct reports",
    "organization.no_reports": "No direct reports",
    "organization.skills": "Local skills",
    "organization.skills_selected": "{count} selected",
    "organization.skills_empty": "No local skills selected.",
    "organization.tools": "Tools",
    "organization.tools_placeholder": "message, github",
    "organization.start_line": "Start report line",
    "organization.complete_line": "Connect manager",
    "organization.remove_manager": "Remove manager",
    "organization.valid": "Organization graph is valid.",
    "organization.invalid": "{count} issue(s) must be fixed before saving.",
    "organization.dirty": "Unsaved organization changes.",
    "organization.saved": "Organization saved.",
    "organization.connect_hint": "Click a node connector, then click its manager.",
    "button.delete_skill": "Delete skill",
    "button.delete_employee": "Delete Employee",
    "button.delete_docker": "Delete Docker",
    "button.import_selected": "Import Selected ({count})",
    "button.preview_from_web_loading": "Fetching...",
    "button.confirm_import_loading": "Importing...",
    "case.title": "Case Carousel",
    "case.copy": "Pick a complete case to inspect inputs, outputs, employees, skills, and one-click import configuration.",
    "case.loading": "Loading cases...",
    "case.empty": "No cases found. Add workspace/openhire/cases.json to enable one-click imports.",
    "case.ready": "Ready",
    "case.imported": "Imported",
    "case.default_subtitle": "OpenHire case",
    "case.default_body": "Click to inspect this case.",
    "case.metric": "metric",
    "case.employees": "employees",
    "case.skills": "skills",
    "case.ops.title": "Case Ops",
    "case.ops.copy": "Govern reusable case imports, drift, overwrite risk, and recent remediation actions.",
    "case.ops.scan": "Scan Cases",
    "case.ops.loading": "Loading Case Ops...",
    "case.ops.empty": "No case governance issues detected.",
    "case.ops.error": "Case Ops failed: {value}",
    "case.ops.catalog": "Catalog / 案例库",
    "case.ops.issues": "{count} issue(s)",
    "case.ops.selected": "{count} selected",
    "case.ops.ignored": "Ignored",
    "case.ops.ignore": "Ignore",
    "case.ops.unignore": "Unignore",
    "case.ops.reimport": "Preview Reimport",
    "case.ops.confirm": "Confirm Reimport",
    "case.ops.cancel": "Clear Preview",
    "case.ops.preview_title": "Reimport preview",
    "case.ops.preview_body": "{cases} case(s), {employees} employee update(s), {skills} skill update(s), {configs} config overwrite(s).",
    "case.ops.opportunities": "Case Opportunities",
    "case.ops.audit": "Recent Actions",
    "case.ops.open_case": "Open Case",
    "case.ops.import_config": "Import Config",
    "case.ops.export_selected": "Export Selected",
    "case.ops.warning": "Warning: {value}",
    "case.ops.imported": "Imported",
    "case.ops.partial": "Partial",
    "case.ops.risk": "Risks",
    "alert.none": "All systems aligned. No immediate anomalies.",
    "alert.context_pressure": "Context pressure is elevated.",
    "alert.main_idle": "Main agent is idle with no active session.",
    "alert.docker_issue": "Docker workers need attention.",
    "alert.docker_issue_count": "{count} containers impacted.",
    "alert.docker_daemon": "Docker daemon is not reachable.",
    "alert.import_warning": "Recent case import returned warnings.",
    "alert.import_warning_count": "{count} failures detected.",
    "action.title": "Action Center",
    "action.copy": "Prioritized next steps from runtime, employees, skills, and reusable cases.",
    "action.context_pressure.title": "Compact main context",
    "action.context_pressure.body": "Context is at {percent}% for {tokens}. Compact before the next long turn.",
    "action.context_pressure.action": "Compact Context",
    "action.main_idle.title": "Inspect main agent",
    "action.main_idle.body": "The main agent is idle and has no active session. Check the control panel before delegating more work.",
    "action.main_idle.action": "Open Control Center",
    "action.docker_issue.title": "Review Docker workers",
    "action.docker_issue.body": "{count} Docker workers report an error, exited, or unknown state.",
    "action.docker_issue.action": "Open Infrastructure",
    "action.docker_daemon.title": "Start Docker daemon",
    "action.docker_daemon.body": "Docker is unavailable: {message}",
    "action.docker_daemon.action": "Open Infrastructure",
    "action.docker_daemon.repair": "One-click repair",
    "action.case_partial.title": "Resolve case import warnings",
    "action.case_partial.body": "The latest case import has {count} failed items. Review the case result before importing again.",
    "action.case_partial.action": "Open Cases",
    "action.agent_skill_proposals.title": "Review Agent Skills",
    "action.agent_skill_proposals.body": "{count} pending Agent Skill proposal(s). First: {name}.",
    "action.agent_skill_proposals.action": "Open Workbench",
    "action.no_business_skills.title": "Import business skills",
    "action.no_business_skills.body": "Only required skills are available. Import at least one business skill before creating specialized employees.",
    "action.no_business_skills.action": "Review Skills",
    "action.employee_missing_skills.title": "Employees need skills",
    "action.employee_missing_skills.body": "{count} employees have no non-required skill binding. Start with {name}.",
    "action.employee_missing_skills.action": "Open Employee",
    "action.healthy.title": "No urgent action",
    "action.healthy.body": "Runtime, cases, employees, and skills have no immediate blockers.",
    "action.create_employee.title": "Create employee",
    "action.create_employee.body": "Start a new Docker-backed digital employee from a role template.",
    "action.create_employee.action": "Create Employee",
    "action.browse_cases.title": "Browse cases",
    "action.browse_cases.body": "Inspect reusable case packages and import a working team setup.",
    "action.browse_cases.action": "Browse Cases",
    "action.review_skills.title": "Review skills",
    "action.review_skills.body": "Check local skills and import more from web, ClawHub, or persona libraries.",
    "action.review_skills.action": "Review Skills",
    "process.title": "Connected Process",
    "process.pid": "PID",
    "process.uptime": "Uptime",
    "overview.status": "Status",
    "overview.model": "Model",
    "overview.uptime": "Uptime",
    "overview.context": "Context",
    "overview.status_footnote": "Main orchestration loop",
    "overview.model_footnote": "Configured primary model",
    "overview.uptime_footnote": "Process lifetime",
    "main.title": "Main Agent",
    "main.latest_session": "Latest session: {value}",
    "main.active_tasks": "Active Tasks",
    "main.stage": "Stage",
    "main.channel": "Channel",
    "main.prompt_tokens": "Prompt Tokens",
    "main.completion_tokens": "Completion Tokens",
    "main.context_window": "Context Window",
    "runtime.timeline.title": "Runtime Timeline",
    "runtime.timeline.copy": "Recent runtime, context, Docker health, and resource trends from this process.",
    "runtime.timeline.refresh": "Refresh History",
    "runtime.timeline.refreshing": "Refreshing...",
    "runtime.timeline.empty": "Runtime history will appear after the next snapshot.",
    "runtime.timeline.error": "Failed to load runtime history: {message}",
    "runtime.timeline.last_updated": "Last updated {value}",
    "runtime.timeline.ago.hours_minutes": "{hours}h {minutes}m ago",
    "runtime.timeline.ago.days_hours_minutes": "{days}d {hours}h {minutes}m ago",
    "runtime.timeline.window": "{count} samples · {minutes} min window",
    "runtime.timeline.context": "Context",
    "runtime.timeline.main_status": "Main status",
    "runtime.timeline.docker_health": "Docker health",
    "runtime.timeline.resources": "Resources",
    "runtime.timeline.cpu": "CPU avg {avg} · max {max}",
    "runtime.timeline.memory": "Memory {value} MiB",
    "runtime.timeline.docker_counts": "{running}/{total} running · {issues} issues",
    "docker.title": "Docker Agents",
    "docker.copy": "Configured docker workers with current command and estimated context usage.",
    "docker.empty": "No agent-like docker containers found.",
    "docker.daemon_unavailable": "Docker daemon unavailable",
    "docker.daemon_repair": "One-click repair",
    "docker.daemon_repairing": "Repairing...",
    "docker.daemon_repair_hint": "Attempts to launch Docker Desktop or a local Docker service, then refreshes the runtime status.",
    "docker.context": "Context",
    "docker.context_unavailable": "Context unavailable",
    "dream.refresh": "Refresh",
    "dream.refreshing": "Refreshing...",
    "dream.run": "Run Dream",
    "dream.running": "Dreaming...",
    "dream.restore": "Restore Commit",
    "dream.restoring": "Restoring...",
    "dream.loading": "Loading Dream memory...",
    "dream.empty": "No Dream subjects found.",
    "dream.error": "Dream failed: {value}",
    "dream.subjects": "Dream Subjects",
    "dream.files": "Memory Files",
    "dream.commits": "Dream Commits",
    "dream.diff": "Commit Diff",
    "dream.no_commits": "No Dream commits yet.",
    "dream.no_diff": "Select a Dream commit to inspect its diff.",
    "dream.file_empty": "This memory file is empty.",
    "dream.schedule": "Schedule",
    "dream.next_run": "Next Run",
    "dream.last_run": "Last Run",
    "dream.running_subjects": "Running",
    "dream.history": "History",
    "dream.unprocessed": "Unprocessed",
    "dream.latest_commit": "Latest Commit",
    "dream.workspace": "Workspace",
    "dream.versioning": "Versioning",
    "dream.status.completed": "Dream completed.",
    "dream.status.nothing": "Dream has nothing to process.",
    "dream.status.restored": "Dream memory restored.",
    "dream.status.failed": "Dream failed.",
    "dream.confirm.title": "Restore Dream Memory",
    "dream.confirm.subtitle": "This creates a safety commit after restoring tracked memory files.",
    "dream.confirm.message": "Restore Dream subject {subject} to before commit {sha}?",
    "docker.resources": "Resources",
    "docker.current_command": "Current Command",
    "docker.source": "Source",
    "employees.roster": "Employee Roster",
    "employees.counts": "{live} live workers · {saved} saved employees",
    "employees.selected": "{count} selected",
    "employees.sort_by": "Sort by",
    "employees.empty_detail": "Select a digital employee to inspect role settings.",
    "employees.belongs_to": "Belongs to",
    "employees.unassigned": "Unassigned",
    "ops.title": "Employee Ops",
    "ops.copy": "Operational workbench for this employee.",
    "ops.health.healthy": "Healthy",
    "ops.health.healthy.body": "Runtime, skills, config, and automation have no immediate blocker.",
    "ops.health.needs_setup": "Needs setup",
    "ops.health.needs_setup.body": "This employee is not fully connected to a managed runtime yet.",
    "ops.health.runtime_issue": "Runtime issue",
    "ops.health.runtime_issue.body": "The linked runtime reports an error, exited, or unknown state.",
    "ops.health.restart_required": "Restart required",
    "ops.health.restart_required.body": "Config changes are saved and need a runtime restart to take effect.",
    "ops.health.skill_gap": "Skill gap",
    "ops.health.skill_gap.body": "This employee has no non-required business skill binding.",
    "ops.action.edit_config": "Edit Config",
    "ops.action.review_skills": "Review Skills",
    "ops.action.create_cron": "Create Cron",
    "ops.action.view_cron": "View Cron",
    "ops.action.chat_history": "Open Chat History",
    "ops.action.infrastructure": "Review Infrastructure",
    "ops.action.delete_employee": "Delete Employee",
    "ops.action.delete_docker": "Delete Docker",
    "ops.diag.runtime": "Runtime",
    "ops.diag.configuration": "Configuration",
    "ops.diag.skills": "Skill Coverage",
    "ops.diag.automation": "Automation",
    "ops.diag.activity": "Recent Activity",
    "ops.diag.status": "Status",
    "ops.diag.container": "Container",
    "ops.diag.session": "Session",
    "ops.diag.context": "Context",
    "ops.diag.owner": "Owner",
    "ops.diag.file": "File",
    "ops.diag.config_state": "State",
    "ops.diag.files": "Files",
    "ops.diag.business_skills": "Business skills",
    "ops.diag.required_skill": "Required skill",
    "ops.diag.jobs": "Jobs",
    "ops.diag.enabled": "Enabled",
    "ops.diag.next_run": "Next run",
    "ops.diag.last_run": "Last run",
    "ops.diag.history": "History",
    "ops.value.not_assigned": "not assigned",
    "ops.value.not_loaded": "not loaded",
    "ops.value.loading": "loading",
    "ops.value.saved": "Saved",
    "ops.value.editing": "Editing",
    "ops.value.unsaved": "Unsaved changes",
    "ops.value.restart": "Restart required",
    "ops.value.available": "available",
    "ops.value.missing": "missing",
    "ops.value.no_history": "no runtime history",
    "ops.value.ready": "ready",
    "ops.value.none": "none",
    "sort.type": "Type",
    "sort.updated": "Last Modified",
    "sort.created": "Created",
    "skills.local_catalog": "Local Catalog",
    "skills.imported_count": "{count} imported skills",
    "skills.empty": "No local skills yet. Search ClawHub and import metadata first.",
    "skills.search.title": "ClawHub Search",
    "skills.search.copy": "Search public skills and import metadata only.",
    "skills.search.placeholder": "Search ClawHub skills",
    "skills.search.empty_prompt": "Enter a keyword to search ClawHub.",
    "skills.search.empty_none": "No ClawHub skills matched that keyword.",
    "skills.search.loading": "Searching ClawHub...",
    "skills.preview.local": "Local Import Preview",
    "skills.preview.web": "Web Import Preview",
    "skills.preview.empty_label": "SKILL.md",
    "skills.preview.cancel": "Cancel",
    "skills.web.copy": "Fetch a public SKILL.md URL and preview it before importing.",
    "skills.web.placeholder": "Paste a public SKILL.md URL",
    "skills.source_empty_description": "No description available.",
    "skills.source_unknown_version": "unknown version",
    "skills.source_no_external_id": "no external id",
    "skills.required": "Required",
    "skills.recommended": "Recommended",
    "skills.selected": "Selected",
    "skills.optional": "Optional",
    "skills.expand": "Expand",
    "skills.expand_labels": "Expand labels",
    "skills.collapse_labels": "Collapse labels",
    "skill.ops.title": "Skill Ops",
    "skill.ops.copy": "Discover skill opportunities and govern duplicate, unused, missing, or drifting local skills.",
    "skill.ops.scan": "Scan",
    "skill.ops.remote_scan": "Scan + Discover",
    "skill.ops.loading": "Loading Skill Ops...",
    "skill.ops.empty": "No governance issues detected.",
    "skill.ops.error": "Skill Ops failed: {value}",
    "skill.ops.coverage": "{count}% employee coverage",
    "skill.ops.issues": "{count} issue(s)",
    "skill.ops.selected": "{count} selected",
    "skill.ops.ignored": "Ignored",
    "skill.ops.ignore": "Ignore",
    "skill.ops.ignore_selected": "Ignore Selected",
    "skill.ops.select_all": "Select all",
    "skill.ops.collapsed_summary": "{count} hidden, {ignored}/{count} ignored",
    "skill.ops.expanded_summary": "{count} foldable item(s) shown, {ignored}/{count} ignored",
    "skill.ops.show_collapsed": "Show hidden",
    "skill.ops.hide_collapsed": "Hide again",
    "skill.ops.unignore": "Unignore",
    "skill.ops.merge_duplicates": "Merge Duplicates",
    "skill.ops.delete_orphans": "Delete Orphans",
    "skill.ops.repair_employee_bindings": "Repair Bindings",
    "skill.ops.preview": "Preview Cleanup",
    "skill.ops.confirm": "Confirm Cleanup",
    "skill.ops.cancel": "Clear Preview",
    "skill.ops.preview_title": "Cleanup preview",
    "skill.ops.preview_body": "{skills} skill(s), {employees} employee(s) affected.",
    "skill.ops.opportunities": "Discovery Opportunities",
    "skill.ops.audit": "Recent Actions",
    "skill.ops.open_skills": "Review Skills",
    "skill.ops.import_web": "Import Web",
    "skill.ops.browse_personas": "Browse Personas",
    "skill.ops.search_clawhub": "Search",
    "skill.ops.warning": "Warning: {value}",
    "soul.title": "SoulBanner Personas",
    "soul.copy": "Browse role skills from SoulBanner's soulbanner_skills and sovereign_skills.",
    "soul.loading": "Loading SoulBanner roles...",
    "soul.empty.initial": "Load SoulBanner roles to browse personas and import them into the local catalog.",
    "soul.empty.none": "No SoulBanner roles available.",
    "soul.mbti_sbti.title": "Mbti/Sbti Personas",
    "soul.mbti_sbti.copy": "Browse role skills from Sbti-Mbti's mbti_skills and sbti_skills.",
    "soul.mbti_sbti.loading": "Loading Mbti/Sbti roles...",
    "soul.mbti_sbti.empty.initial": "Load Mbti/Sbti to browse personas and import them into the local catalog.",
    "soul.mbti_sbti.empty.none": "No Mbti/Sbti roles available.",
    "modal.create.title": "Create Digital Employee",
    "modal.create.copy": "Choose a role template, fill in a small amount of setup, and create a preview-ready employee configuration.",
    "modal.create.custom_prompt": "Describe the role you want to create in one sentence",
    "modal.create.custom_placeholder": "For example: an operations efficiency expert who understands Feishu automation and can drive hiring workflow setup",
    "modal.create.custom_note": "Cook uses the LLM to fill Employee Name, Role, and System Prompt automatically. The new template is saved after Create Employee succeeds.",
    "modal.create.employee_name": "Employee Name",
    "modal.create.role": "Role",
    "modal.create.avatar": "Avatar",
    "modal.create.avatar_note": "Choose a preset portrait for employee cards and detail views.",
    "modal.create.local_skills": "Local Skills",
    "modal.create.local_skills_empty": "Import skills in the Skill Catalog first, or create the employee without skills.",
    "modal.create.local_skills_required": "The excellent-employee skill is required for every digital employee. {count} selected.",
    "modal.create.local_skills_loading": "Recommending skills...",
    "modal.create.local_skills_warning": "Skill recommendation warning: {value}",
    "modal.create.system_prompt": "System Prompt",
    "modal.create.delete_template": "Delete template",
    "modal.create.avatar_aria": "Employee avatar",
    "modal.create.skills_aria": "Local skills",
    "modal.create.skill_empty": "No local skills yet. Import skills in the Skill Catalog first, or create without skills.",
    "modal.create.wizard.template": "Template",
    "modal.create.wizard.profile": "Profile",
    "modal.create.wizard.skills": "Skills",
    "modal.create.wizard.review": "Review/Create",
    "modal.create.wizard.template_copy": "Pick a role template or cook a custom role before configuring the employee.",
    "modal.create.wizard.profile_copy": "Confirm the employee identity, runtime type, avatar, and operating prompt.",
    "modal.create.wizard.skills_copy": "Bind the required protocol and optional business skills for this employee.",
    "modal.create.wizard.review_copy": "Review the complete setup before creating the employee.",
    "modal.create.validation.profile_required": "Employee name, role, and system prompt are required before continuing.",
    "modal.create.validation.blocked_step": "Complete the earlier wizard steps before opening this step.",
    "modal.create.review_title": "Review employee setup",
    "modal.create.review_template": "Template",
    "modal.create.review_avatar": "Avatar",
    "modal.create.review_agent_type": "Agent type",
    "modal.create.review_skills": "Skills",
    "modal.create.review_recommendation": "Recommendation",
    "modal.create.review_no_skills": "No local skills selected.",
    "modal.create.review_skill_source": "Will use {cloudCount} cloud-installed skill(s) and {localCount} local skill(s).",
  },
  zh: {
    "document.title": "OpenHire 管理页",
    "nav.subtitle": "数字员工编排控制台",
    "nav.command_center": "指挥台",
    "nav.control_center": "控制中心",
    "nav.organization": "组织架构",
    "nav.employee_studio": "数字员工",
    "nav.resource_hub": "资源中心",
    "nav.agent_skills": "技能工作台",
    "nav.infrastructure": "基础设施",
    "nav.dream": "梦境",
    "nav.snapshot.pending": "等待快照",
    "nav.snapshot.current": "快照 {value}",
    "hero.eyebrow": "数字员工编排平台",
    "hero.title": "指挥台",
    "hero.copy": "在一个主控界面里统一处理运行时、员工、技能和可复用案例。",
    "preferences.language.label": "语言",
    "preferences.theme.toggle": "{mode}",
    "preferences.theme.dark": "夜间模式",
    "preferences.theme.light": "浅色模式",
    "preferences.group.aria_label": "管理页偏好设置",
    "links.github": "OpenHire GitHub",
    "companion.action.pat": "摸摸",
    "companion.action.feed": "投喂",
    "companion.action.chat": "对话",
    "companion.action.sound_on": "开声音",
    "companion.action.sound_off": "关声音",
    "companion.action.debug": "检查",
    "companion.chat.title": "和小伙伴聊聊",
    "companion.chat.placeholder": "对小伙伴说点什么...",
    "companion.chat.send": "发送",
    "companion.chat.toggle.label": "对话出口",
    "companion.chat.toggle.side": "侧信道",
    "companion.chat.toggle.main": "主控",
    "companion.mood.idle": "随时待命",
    "companion.fallback.body": "Live2D 引擎未就绪，先用霓虹版陪你聊。",
    "companion.hotspot.aria": "点一下小伙伴",
    "section.control.title": "控制中心",
    "section.control.copy": "集中查看运行态健康、上下文压力和主智能体关键操作。",
    "section.organization.title": "组织架构",
    "section.organization.copy": "通过画布编排汇报关系、自动校验层级，并调整员工能力。",
    "section.employees.title": "数字员工",
    "section.employees.copy": "创建由 Docker worker 驱动的数字员工，并预览角色、设定、技能和工具。",
    "section.resource.title": "资源中心",
    "section.resource.copy": "在一个工作区里切换案例、人格与技能，不再来回滚动寻找入口。",
    "section.agent_skills.title": "Agent Skills Workbench",
    "section.agent_skills.copy": "管理 agent 真正可发现、可读取、可复用的 workspace/skills 本地技能。",
    "section.infrastructure.title": "基础设施",
    "section.infrastructure.copy": "查看 Docker worker、容器资源和运行来源等基础设施信息。",
    "section.dream.title": "梦境",
    "section.dream.copy": "查看主控与数字员工的长期记忆、Dream 历史和可安全回滚的版本。",
    "section.soul.title": "人格库",
    "section.soul.copy": "浏览 SoulBanner 人格角色，导入到本地技能库，并在创建员工时复用这些元数据。",
    "section.skills.title": "技能库",
    "section.skills.copy": "搜索 ClawHub 公共技能，导入到本地技能库，并在创建员工时复用这些元数据。",
    "resource.tab.cases": "案例",
    "resource.tab.personas": "人格",
    "resource.tab.skills": "技能",
    "button.create_employee": "创建员工",
    "button.smart_recommend": "智能推荐",
    "button.import_local_skills": "从本地技能导入",
    "button.import_web": "从网页导入",
    "button.select": "选择",
    "button.delete_selected": "删除已选",
    "button.export_selected": "导出已选",
    "button.cancel": "取消",
    "button.back": "上一步",
    "button.next": "下一步",
    "button.confirm_import": "确认导入",
    "button.preview_import": "预览导入",
    "button.search_clawhub": "搜索 ClawHub",
    "button.preview_from_web": "网页预览",
    "button.reload_soulbanner": "重新加载 SoulBanner 角色",
    "button.load_soulbanner": "加载 SoulBanner 角色",
    "button.reload_mbti_sbti": "重新加载 Mbti/Sbti 角色",
    "button.load_mbti_sbti": "从 Mbti/Sbti 导入",
    "button.import_config": "导入配置",
    "button.clear_context": "清空上下文",
    "button.compact_context": "压缩上下文",
    "button.clear_short": "清空",
    "button.compact_short": "压缩",
    "button.clearing": "清空中...",
    "button.compacting": "压缩中...",
    "button.close_create_modal": "关闭创建员工弹窗",
    "button.close_case_modal": "关闭案例弹窗",
    "button.close_confirmation_modal": "关闭确认弹窗",
    "button.importing": "导入中...",
    "button.fetching": "抓取中...",
    "button.searching": "搜索中...",
    "button.loading": "加载中...",
    "agent_skills.refresh": "刷新",
    "agent_skills.create": "创建技能",
    "agent_skills.create_title": "新建 workspace skill",
    "agent_skills.create_copy": "在 workspace/skills 下创建一个真正会被 agent 读取的技能。",
    "agent_skills.name": "技能名称",
    "agent_skills.description": "描述",
    "agent_skills.create_submit": "创建 Workspace Skill",
    "agent_skills.cancel_create": "取消",
    "agent_skills.search": "搜索 Agent Skills",
    "agent_skills.filter_all": "全部",
    "agent_skills.filter_workspace": "Workspace",
    "agent_skills.filter_builtin": "内置",
    "agent_skills.empty": "暂无 agent skills。",
    "agent_skills.select_empty": "选择一个技能后查看 SKILL.md、资源文件和 proposal 审批记录。",
    "agent_skills.progressive": "Progressive disclosure：metadata 常驻展示，选中后加载 SKILL.md，资源文件放在 scripts/、references/ 或 assets/。",
    "agent_skills.bound_employees": "已绑定员工",
    "agent_skills.category_label": "分类",
    "agent_skills.uncategorized": "未分类",
    "agent_skills.files": "资源文件",
    "agent_skills.proposals": "审批队列",
    "agent_skills.no_files": "暂无资源文件。",
    "agent_skills.no_proposals": "暂无待审批 proposal。",
    "agent_skills.edit": "编辑",
    "agent_skills.save": "保存",
    "agent_skills.cancel": "取消",
    "agent_skills.package": "打包 .skill",
    "agent_skills.delete": "删除",
    "agent_skills.approve": "审批落地",
    "agent_skills.discard": "丢弃",
    "agent_skills.file_path": "scripts/helper.py",
    "agent_skills.file_content": "文件内容",
    "agent_skills.write_file": "写入文件",
    "agent_skills.install": "安装到 Agent Skills",
    "agent_skills.installed": "已安装到 Agent Skills。",
    "agent_skills.package_ready": "打包完成：{path}",
    "agent_skills.error": "Agent skill 错误：{value}",
    "button.cook": "Cook",
    "button.cooking": "Cooking...",
    "button.creating": "创建中...",
    "button.collapse": "收起",
    "button.show_more": "展开 (+{count})",
    "organization.refresh": "刷新",
    "organization.save": "保存组织架构",
    "organization.saving": "保存中...",
    "organization.loading": "正在加载组织架构...",
    "organization.empty": "先创建数字员工，再编排汇报关系。",
    "organization.canvas": "汇报关系画布",
    "organization.detail": "员工能力",
    "organization.no_selection": "选择一个员工节点后编辑汇报关系和能力。",
    "organization.global_skip": "全局允许越级汇报",
    "organization.employee_skip": "允许该员工越级汇报",
    "organization.manager": "直属上级",
    "organization.no_manager": "无直属上级",
    "organization.reports": "直属下级",
    "organization.no_reports": "无直属下级",
    "organization.skills": "本地技能",
    "organization.skills_selected": "已选 {count} 个",
    "organization.skills_empty": "未选择本地技能。",
    "organization.tools": "工具",
    "organization.tools_placeholder": "message, github",
    "organization.start_line": "开始连线",
    "organization.complete_line": "连接上级",
    "organization.remove_manager": "移除上级",
    "organization.valid": "组织架构合法。",
    "organization.invalid": "保存前需修复 {count} 个问题。",
    "organization.dirty": "组织架构有未保存变更。",
    "organization.saved": "组织架构已保存。",
    "organization.connect_hint": "先点击员工节点连接点，再点击直属上级节点。",
    "button.delete_skill": "删除技能",
    "button.delete_employee": "删除员工",
    "button.delete_docker": "删除 Docker",
    "button.import_selected": "导入已选 ({count})",
    "button.preview_from_web_loading": "抓取中...",
    "button.confirm_import_loading": "导入中...",
    "case.title": "案例轮播",
    "case.copy": "选择一个完整案例，查看输入、输出、员工、技能和一键导入配置。",
    "case.loading": "加载案例中...",
    "case.empty": "未找到案例。添加 workspace/openhire/cases.json 后即可启用一键导入。",
    "case.ready": "就绪",
    "case.imported": "已导入",
    "case.default_subtitle": "OpenHire 案例",
    "case.default_body": "点击查看这个案例。",
    "case.metric": "指标",
    "case.employees": "员工",
    "case.skills": "技能",
    "case.ops.title": "案例运维",
    "case.ops.copy": "治理可复用案例的导入风险、漂移、覆盖风险和最近修复动作。",
    "case.ops.scan": "扫描案例",
    "case.ops.loading": "正在加载案例运维...",
    "case.ops.empty": "未发现案例治理问题。",
    "case.ops.error": "案例运维失败：{value}",
    "case.ops.catalog": "Catalog / 案例库",
    "case.ops.issues": "{count} 个问题",
    "case.ops.selected": "已选 {count}",
    "case.ops.ignored": "已忽略",
    "case.ops.ignore": "忽略",
    "case.ops.unignore": "取消忽略",
    "case.ops.reimport": "预览重导入",
    "case.ops.confirm": "确认重导入",
    "case.ops.cancel": "清空预览",
    "case.ops.preview_title": "重导入预览",
    "case.ops.preview_body": "将影响 {cases} 个案例、{employees} 个员工更新、{skills} 个技能更新、{configs} 个配置覆盖。",
    "case.ops.opportunities": "案例机会",
    "case.ops.audit": "最近动作",
    "case.ops.open_case": "打开案例",
    "case.ops.import_config": "导入配置",
    "case.ops.export_selected": "导出已选",
    "case.ops.warning": "警告：{value}",
    "case.ops.imported": "已导入",
    "case.ops.partial": "部分导入",
    "case.ops.risk": "风险",
    "alert.none": "当前没有需要优先处理的异常。",
    "alert.context_pressure": "上下文压力偏高，请优先处理。",
    "alert.main_idle": "主智能体当前空闲，且没有活跃会话。",
    "alert.docker_issue": "存在需要关注的 Docker worker。",
    "alert.docker_issue_count": "发现 {count} 个 worker 异常。",
    "alert.docker_daemon": "Docker daemon 当前不可达。",
    "alert.import_warning": "最近一次案例导入返回了 warning。",
    "alert.import_warning_count": "失败 {count} 项。",
    "action.title": "待办中心",
    "action.copy": "根据运行态、员工、技能和案例自动整理下一步优先动作。",
    "action.context_pressure.title": "压缩主智能体上下文",
    "action.context_pressure.body": "当前上下文已到 {percent}%（{tokens}）。建议在下一轮长任务前压缩。",
    "action.context_pressure.action": "压缩上下文",
    "action.main_idle.title": "检查主智能体",
    "action.main_idle.body": "主智能体当前空闲且没有活跃会话，继续派工前先检查控制面板。",
    "action.main_idle.action": "打开控制中心",
    "action.docker_issue.title": "查看 Docker workers",
    "action.docker_issue.body": "{count} 个 Docker worker 处于 error、exited 或 unknown 状态。",
    "action.docker_issue.action": "打开基础设施",
    "action.docker_daemon.title": "启动 Docker daemon",
    "action.docker_daemon.body": "Docker 当前不可用：{message}",
    "action.docker_daemon.action": "打开基础设施",
    "action.docker_daemon.repair": "一键修复",
    "action.case_partial.title": "处理案例导入 warning",
    "action.case_partial.body": "最近一次案例导入有 {count} 个失败项，再次导入前请先检查结果。",
    "action.case_partial.action": "打开案例",
    "action.agent_skill_proposals.title": "Agent Skills 待审批",
    "action.agent_skill_proposals.body": "当前有 {count} 个待审批 skill proposal，首个：{name}。",
    "action.agent_skill_proposals.action": "打开技能工作台",
    "action.no_business_skills.title": "导入业务技能",
    "action.no_business_skills.body": "当前只有必选技能。创建专业员工前建议至少导入一个业务技能。",
    "action.no_business_skills.action": "查看技能",
    "action.employee_missing_skills.title": "员工缺少业务技能",
    "action.employee_missing_skills.body": "{count} 个员工没有绑定非必选技能。建议先检查 {name}。",
    "action.employee_missing_skills.action": "打开员工",
    "action.healthy.title": "暂无紧急动作",
    "action.healthy.body": "运行态、案例、员工和技能当前没有明显阻塞项。",
    "action.create_employee.title": "创建员工",
    "action.create_employee.body": "从角色模板创建新的 Docker 数字员工。",
    "action.create_employee.action": "创建员工",
    "action.browse_cases.title": "浏览案例",
    "action.browse_cases.body": "查看可复用案例包，并导入完整团队配置。",
    "action.browse_cases.action": "浏览案例",
    "action.review_skills.title": "检查技能",
    "action.review_skills.body": "查看本地技能，或从网页、ClawHub、人格库继续导入。",
    "action.review_skills.action": "查看技能",
    "process.title": "当前连接进程",
    "process.pid": "PID",
    "process.uptime": "运行时长",
    "overview.status": "状态",
    "overview.model": "模型",
    "overview.uptime": "运行时长",
    "overview.context": "上下文",
    "overview.status_footnote": "主编排循环",
    "overview.model_footnote": "当前配置的主模型",
    "overview.uptime_footnote": "进程存活时间",
    "main.title": "主智能体",
    "main.latest_session": "最近会话：{value}",
    "main.active_tasks": "活跃任务",
    "main.stage": "阶段",
    "main.channel": "渠道",
    "main.prompt_tokens": "提示词 Tokens",
    "main.completion_tokens": "输出 Tokens",
    "main.context_window": "上下文窗口",
    "runtime.timeline.title": "运行态时间线",
    "runtime.timeline.copy": "查看当前进程近期运行态、上下文、Docker 健康度和资源趋势。",
    "runtime.timeline.refresh": "刷新历史",
    "runtime.timeline.refreshing": "刷新中...",
    "runtime.timeline.empty": "下一次快照后会显示运行态历史。",
    "runtime.timeline.error": "加载运行态历史失败：{message}",
    "runtime.timeline.last_updated": "最近更新 {value}",
    "runtime.timeline.ago.hours_minutes": "{hours}小时{minutes}分钟前",
    "runtime.timeline.ago.days_hours_minutes": "{days}天{hours}小时{minutes}分钟前",
    "runtime.timeline.window": "{count} 个样本 · {minutes} 分钟窗口",
    "runtime.timeline.context": "上下文",
    "runtime.timeline.main_status": "主状态",
    "runtime.timeline.docker_health": "Docker 健康",
    "runtime.timeline.resources": "资源",
    "runtime.timeline.cpu": "CPU 平均 {avg} · 峰值 {max}",
    "runtime.timeline.memory": "内存 {value} MiB",
    "runtime.timeline.docker_counts": "{running}/{total} 运行 · {issues} 异常",
    "docker.title": "Docker 智能体",
    "docker.copy": "查看已配置 Docker worker 的当前命令和预估上下文占用。",
    "docker.empty": "未发现类智能体 Docker 容器。",
    "docker.daemon_unavailable": "Docker daemon 不可用",
    "docker.daemon_repair": "一键修复",
    "docker.daemon_repairing": "修复中...",
    "docker.daemon_repair_hint": "尝试启动 Docker Desktop 或本机 Docker 服务，然后刷新运行态。",
    "docker.context": "上下文",
    "docker.context_unavailable": "上下文不可用",
    "dream.refresh": "刷新",
    "dream.refreshing": "刷新中...",
    "dream.run": "运行 Dream",
    "dream.running": "梦境处理中...",
    "dream.restore": "回滚 Commit",
    "dream.restoring": "回滚中...",
    "dream.loading": "正在加载梦境记忆...",
    "dream.empty": "暂无 Dream subject。",
    "dream.error": "Dream 失败：{value}",
    "dream.subjects": "梦境对象",
    "dream.files": "记忆文件",
    "dream.commits": "Dream Commits",
    "dream.diff": "Commit Diff",
    "dream.no_commits": "还没有 Dream commit。",
    "dream.no_diff": "选择一个 Dream commit 查看 diff。",
    "dream.file_empty": "这个记忆文件为空。",
    "dream.schedule": "计划",
    "dream.next_run": "下次运行",
    "dream.last_run": "上次运行",
    "dream.running_subjects": "运行中",
    "dream.history": "历史",
    "dream.unprocessed": "未处理",
    "dream.latest_commit": "最新 Commit",
    "dream.workspace": "Workspace",
    "dream.versioning": "版本",
    "dream.status.completed": "Dream 已完成。",
    "dream.status.nothing": "Dream 暂无可处理内容。",
    "dream.status.restored": "Dream 记忆已回滚。",
    "dream.status.failed": "Dream 失败。",
    "dream.confirm.title": "回滚 Dream 记忆",
    "dream.confirm.subtitle": "回滚被追踪的记忆文件后会再创建一个安全 commit。",
    "dream.confirm.message": "将 Dream 对象 {subject} 回滚到 commit {sha} 之前？",
    "docker.resources": "资源",
    "docker.current_command": "当前命令",
    "docker.source": "来源",
    "employees.roster": "员工列表",
    "employees.counts": "{live} 个在线 worker · {saved} 个已保存员工",
    "employees.selected": "已选 {count} 个",
    "employees.sort_by": "排序方式",
    "employees.empty_detail": "选择一个数字员工以查看角色设定。",
    "employees.belongs_to": "所属员工",
    "employees.unassigned": "未分配",
    "ops.title": "员工运维",
    "ops.copy": "这个员工的可运维工作台。",
    "ops.health.healthy": "健康",
    "ops.health.healthy.body": "运行时、技能、配置和自动化当前没有明显阻塞项。",
    "ops.health.needs_setup": "需要配置",
    "ops.health.needs_setup.body": "这个员工还没有完整接入可管理运行时。",
    "ops.health.runtime_issue": "运行时异常",
    "ops.health.runtime_issue.body": "关联运行时处于 error、exited 或 unknown 状态。",
    "ops.health.restart_required": "需要重启",
    "ops.health.restart_required.body": "配置已保存，需要重启运行时后才会生效。",
    "ops.health.skill_gap": "技能缺口",
    "ops.health.skill_gap.body": "这个员工没有绑定非必选业务技能。",
    "ops.action.edit_config": "编辑配置",
    "ops.action.review_skills": "查看技能",
    "ops.action.create_cron": "创建 Cron",
    "ops.action.view_cron": "查看 Cron",
    "ops.action.chat_history": "打开对话历史",
    "ops.action.infrastructure": "查看基础设施",
    "ops.action.delete_employee": "删除员工",
    "ops.action.delete_docker": "删除 Docker",
    "ops.diag.runtime": "运行态",
    "ops.diag.configuration": "配置",
    "ops.diag.skills": "技能覆盖",
    "ops.diag.automation": "自动化",
    "ops.diag.activity": "最近活动",
    "ops.diag.status": "状态",
    "ops.diag.container": "容器",
    "ops.diag.session": "会话",
    "ops.diag.context": "上下文",
    "ops.diag.owner": "所属员工",
    "ops.diag.file": "文件",
    "ops.diag.config_state": "状态",
    "ops.diag.files": "文件数",
    "ops.diag.business_skills": "业务技能",
    "ops.diag.required_skill": "必选技能",
    "ops.diag.jobs": "任务",
    "ops.diag.enabled": "启用",
    "ops.diag.next_run": "下次运行",
    "ops.diag.last_run": "上次运行",
    "ops.diag.history": "历史",
    "ops.value.not_assigned": "未分配",
    "ops.value.not_loaded": "未加载",
    "ops.value.loading": "加载中",
    "ops.value.saved": "已保存",
    "ops.value.editing": "编辑中",
    "ops.value.unsaved": "未保存修改",
    "ops.value.restart": "需要重启",
    "ops.value.available": "可用",
    "ops.value.missing": "缺失",
    "ops.value.no_history": "暂无运行历史",
    "ops.value.ready": "就绪",
    "ops.value.none": "无",
    "sort.type": "类型",
    "sort.updated": "最近修改",
    "sort.created": "创建时间",
    "skills.local_catalog": "本地技能库",
    "skills.imported_count": "已导入 {count} 个技能",
    "skills.empty": "本地还没有技能。先搜索 ClawHub 并导入元数据。",
    "skills.search.title": "ClawHub 搜索",
    "skills.search.copy": "搜索公开技能，只导入元数据。",
    "skills.search.placeholder": "搜索 ClawHub 技能",
    "skills.search.empty_prompt": "输入关键词后搜索 ClawHub。",
    "skills.search.empty_none": "没有匹配这个关键词的 ClawHub 技能。",
    "skills.search.loading": "正在搜索 ClawHub...",
    "skills.preview.local": "本地导入预览",
    "skills.preview.web": "网页导入预览",
    "skills.preview.empty_label": "SKILL.md",
    "skills.preview.cancel": "取消",
    "skills.web.copy": "抓取公开 SKILL.md URL，并在导入前先预览。",
    "skills.web.placeholder": "粘贴公开 SKILL.md URL",
    "skills.source_empty_description": "暂无描述。",
    "skills.source_unknown_version": "未知版本",
    "skills.source_no_external_id": "无外部 ID",
    "skills.required": "必选",
    "skills.recommended": "推荐",
    "skills.selected": "已选",
    "skills.optional": "可选",
    "skills.expand": "展开",
    "skills.expand_labels": "展开标签",
    "skills.collapse_labels": "收起标签",
    "skill.ops.title": "技能运维",
    "skill.ops.copy": "发现可补充技能，并治理重复、闲置、缺内容或绑定漂移的本地技能。",
    "skill.ops.scan": "扫描",
    "skill.ops.remote_scan": "扫描+发现",
    "skill.ops.loading": "正在加载技能运维...",
    "skill.ops.empty": "未发现治理问题。",
    "skill.ops.error": "技能运维失败：{value}",
    "skill.ops.coverage": "员工覆盖 {count}%",
    "skill.ops.issues": "{count} 个问题",
    "skill.ops.selected": "已选 {count}",
    "skill.ops.ignored": "已忽略",
    "skill.ops.ignore": "忽略",
    "skill.ops.ignore_selected": "一键忽略",
    "skill.ops.select_all": "全选",
    "skill.ops.collapsed_summary": "共 {count} 条被折叠，{ignored}/{count} 已忽略",
    "skill.ops.expanded_summary": "已展开 {count} 条折叠项，{ignored}/{count} 已忽略",
    "skill.ops.show_collapsed": "展开折叠项",
    "skill.ops.hide_collapsed": "收起折叠项",
    "skill.ops.unignore": "取消忽略",
    "skill.ops.merge_duplicates": "合并重复",
    "skill.ops.delete_orphans": "删除闲置",
    "skill.ops.repair_employee_bindings": "修复绑定",
    "skill.ops.preview": "预览清理",
    "skill.ops.confirm": "确认清理",
    "skill.ops.cancel": "清空预览",
    "skill.ops.preview_title": "清理预览",
    "skill.ops.preview_body": "将影响 {skills} 个技能、{employees} 个员工。",
    "skill.ops.opportunities": "发现机会",
    "skill.ops.audit": "最近动作",
    "skill.ops.open_skills": "查看技能",
    "skill.ops.import_web": "网页导入",
    "skill.ops.browse_personas": "浏览人格",
    "skill.ops.search_clawhub": "搜索",
    "skill.ops.warning": "警告：{value}",
    "soul.title": "SoulBanner 人格",
    "soul.copy": "浏览 SoulBanner 的 soulbanner_skills 和 sovereign_skills 中的人格角色。",
    "soul.loading": "正在加载 SoulBanner 角色...",
    "soul.empty.initial": "点击加载 SoulBanner 角色后即可浏览人格并导入到本地技能库。",
    "soul.empty.none": "当前没有可用的 SoulBanner 角色。",
    "soul.mbti_sbti.title": "Mbti/Sbti 人格",
    "soul.mbti_sbti.copy": "浏览 Sbti-Mbti 的 mbti_skills 和 sbti_skills 中的人格角色。",
    "soul.mbti_sbti.loading": "正在加载 Mbti/Sbti 角色...",
    "soul.mbti_sbti.empty.initial": "点击从 Mbti/Sbti 导入后即可浏览人格并导入到本地技能库。",
    "soul.mbti_sbti.empty.none": "当前没有可用的 Mbti/Sbti 角色。",
    "modal.create.title": "创建数字员工",
    "modal.create.copy": "选择角色模板，补充少量设定，生成可预览的员工配置。",
    "modal.create.custom_prompt": "一句话描述你想创建的角色",
    "modal.create.custom_placeholder": "例如：一个懂飞书自动化、能推进招聘流程搭建的运营效率专家",
    "modal.create.custom_note": "Cook 会调用 LLM 自动补全 Employee Name、Role 和 System Prompt。创建成功后会自动保存为新模板。",
    "modal.create.employee_name": "员工名称",
    "modal.create.role": "角色",
    "modal.create.avatar": "头像",
    "modal.create.avatar_note": "为员工卡片和详情页选择一个预设头像。",
    "modal.create.local_skills": "本地技能",
    "modal.create.local_skills_empty": "先在技能库导入技能，或者不带技能直接创建员工。",
    "modal.create.local_skills_required": "excellent-employee 技能是每个数字员工的必选项。当前已选 {count} 个。",
    "modal.create.local_skills_loading": "正在推荐技能...",
    "modal.create.local_skills_warning": "技能推荐警告：{value}",
    "modal.create.system_prompt": "系统提示词",
    "modal.create.delete_template": "删除模板",
    "modal.create.avatar_aria": "员工头像",
    "modal.create.skills_aria": "本地技能",
    "modal.create.skill_empty": "本地还没有技能。先在技能库导入技能，或者不带技能直接创建。",
    "modal.create.wizard.template": "模板",
    "modal.create.wizard.profile": "资料",
    "modal.create.wizard.skills": "技能",
    "modal.create.wizard.review": "确认/创建",
    "modal.create.wizard.template_copy": "先选择角色模板，或用 Cook 生成自定义角色。",
    "modal.create.wizard.profile_copy": "确认员工身份、运行时类型、头像和系统提示词。",
    "modal.create.wizard.skills_copy": "绑定必选协议和可选业务技能。",
    "modal.create.wizard.review_copy": "创建前检查完整配置。",
    "modal.create.validation.profile_required": "继续前需要填写员工名称、角色和系统提示词。",
    "modal.create.validation.blocked_step": "请先完成前面的创建步骤。",
    "modal.create.review_title": "确认员工配置",
    "modal.create.review_template": "模板",
    "modal.create.review_avatar": "头像",
    "modal.create.review_agent_type": "Agent type",
    "modal.create.review_skills": "技能",
    "modal.create.review_recommendation": "推荐结果",
    "modal.create.review_no_skills": "未选择本地技能。",
    "modal.create.review_skill_source": "将使用 cloud 下载的 {cloudCount} 个 skill 和 local 导入的 {localCount} 个 skill。",
  },
};

function normalizeLanguage(value) {
  return String(value || "").toLowerCase().startsWith("zh") ? "zh" : "en";
}

function detectDefaultLanguage() {
  try {
    return normalizeLanguage(navigator.language);
  } catch {
    return "en";
  }
}

function readLanguagePreference() {
  try {
    return normalizeLanguage(window.localStorage?.getItem(LANGUAGE_STORAGE_KEY) || detectDefaultLanguage());
  } catch {
    return detectDefaultLanguage();
  }
}

function writeLanguagePreference(language) {
  try {
    window.localStorage?.setItem(LANGUAGE_STORAGE_KEY, normalizeLanguage(language));
  } catch {
    // Ignore storage failures and keep the in-memory preference.
  }
}

function normalizeTheme(value) {
  return String(value || "").toLowerCase() === "dark" ? "dark" : "light";
}

function readStoredThemePreference() {
  try {
    const saved = String(window.localStorage?.getItem(THEME_STORAGE_KEY) || "").toLowerCase();
    return ["dark", "light"].includes(saved) ? saved : "";
  } catch {
    return "";
  }
}

function systemThemeQuery() {
  try {
    return window.matchMedia(SYSTEM_THEME_QUERY);
  } catch {
    return null;
  }
}

function detectDefaultTheme() {
  return systemThemeQuery()?.matches ? "dark" : DEFAULT_THEME;
}

function readThemePreference() {
  return readStoredThemePreference() || detectDefaultTheme();
}

function writeThemePreference(theme) {
  try {
    window.localStorage?.setItem(THEME_STORAGE_KEY, normalizeTheme(theme));
  } catch {
    // Ignore storage failures and keep the in-memory preference.
  }
}

function shouldFollowSystemTheme() {
  return !readStoredThemePreference();
}

function syncSystemThemePreference() {
  if (!shouldFollowSystemTheme()) return;
  applyTheme(detectDefaultTheme(), { persist: false });
}

function initializeSystemThemePreference() {
  const media = systemThemeQuery();
  if (!media) return;
  if (typeof media.addEventListener === "function") {
    media.addEventListener("change", syncSystemThemePreference);
    return;
  }
  if (typeof media.addListener === "function") {
    media.addListener(syncSystemThemePreference);
  }
}

function normalizeResourceHubTab(value) {
  const normalized = String(value || "").toLowerCase();
  return ["cases", "personas", "skills"].includes(normalized) ? normalized : "cases";
}

const NAV_SECTIONS = [
  { key: "hero-command-center", labelKey: "nav.command_center", targetId: "hero-command-center" },
  { key: "control-center", labelKey: "nav.control_center", targetId: "control-center" },
  { key: "organization-shell", labelKey: "nav.organization", targetId: "organization-shell" },
  { key: "employee-studio", labelKey: "nav.employee_studio", targetId: "employee-studio" },
  { key: "resource-hub", labelKey: "nav.resource_hub", targetId: "resource-hub" },
  { key: "agent-skills-workbench", labelKey: "nav.agent_skills", targetId: "agent-skills-workbench" },
  { key: "infrastructure-shell", labelKey: "nav.infrastructure", targetId: "infrastructure-shell" },
  { key: "dream-shell", labelKey: "nav.dream", targetId: "dream-shell" },
];
const NAV_SCROLL_OFFSET = 24;

const uiState = {
  language: readLanguagePreference(),
  theme: readThemePreference(),
  resourceHubTab: "cases",
  activeNavSection: NAV_SECTIONS[0].key,
};

let navSectionObserver = null;
let navScrollTicking = false;

function currentLanguage() {
  return uiState.language;
}

function currentTheme() {
  return uiState.theme;
}

function currentResourceHubTab() {
  return uiState.resourceHubTab;
}

function currentActiveNavSection() {
  return uiState.activeNavSection;
}

function interpolateTranslation(template, replacements = {}) {
  return String(template || "").replace(/\{(\w+)\}/g, (_, key) => (
    Object.prototype.hasOwnProperty.call(replacements, key) ? String(replacements[key]) : `{${key}}`
  ));
}

function t(key, replacements = {}) {
  const language = currentLanguage();
  const template = TRANSLATIONS[language]?.[key] ?? TRANSLATIONS.en[key] ?? key;
  return interpolateTranslation(template, replacements);
}

function defaultSkillRecommendation(overrides = {}) {
  return {
    isLoading: false,
    reason: "",
    warning: "",
    installedSkillIds: [],
    installedSkills: [],
    remoteQueries: [],
    ...overrides,
  };
}

const EMPLOYEE_TEMPLATES = [
  {
    id: "frontend-engineer",
    defaultName: "Nova FE",
    role: "Frontend Engineer / 前端工程师",
    defaultAgentType: "nanobot",
    companyStyle: "ByteDance-style Growth Platform",
    summary: "面向增长、运营后台和复杂交互页面，负责从需求拆解到组件实现、性能优化和端到端验证。",
    docker: {
      image: "openhire/frontend-engineer:demo",
      name: "fe-workbench",
      ports: "5173, 3000",
      resources: "2 CPU / 4 GB RAM",
    },
    settings: {
      model: "gpt-5.4",
      mode: "Feature delivery",
      workspace: "/workspace/web",
      guardrails: "Design system aware, PR-first",
    },
    skills: ["React/Vue UI", "Design System", "Responsive Layout", "Playwright E2E", "Performance Profiling"],
    tools: ["node", "pnpm", "vite", "playwright", "figma-mcp"],
    exampleTasks: ["实现招聘漏斗数据看板", "修复移动端样式回归", "补齐核心表单的 E2E 测试"],
  },
  {
    id: "algorithm-engineer",
    defaultName: "Atlas Algo",
    role: "Algorithm Engineer / 算法工程师",
    defaultAgentType: "nanobot",
    companyStyle: "Baidu-style Search & Recommendation",
    summary: "负责召回、排序、评估和模型实验，把业务目标转成可度量的算法迭代和离线/在线指标。",
    docker: {
      image: "openhire/algorithm-engineer:demo",
      name: "algo-lab",
      ports: "8888, 6006",
      resources: "8 CPU / 24 GB RAM / GPU optional",
    },
    settings: {
      model: "gpt-5.4",
      mode: "Experiment planning",
      workspace: "/workspace/ml",
      guardrails: "Metric-driven, reproducible runs",
    },
    skills: ["Feature Engineering", "Ranking Models", "A/B Metrics", "Vector Search", "Model Evaluation"],
    tools: ["python", "jupyter", "pytorch", "sklearn", "mlflow"],
    exampleTasks: ["设计候选人匹配排序特征", "分析推荐点击率下降原因", "生成离线评估实验报告"],
  },
  {
    id: "backend-engineer",
    defaultName: "Kepler BE",
    role: "Backend Engineer / 后端工程师",
    defaultAgentType: "nanobot",
    companyStyle: "Alibaba-style Commerce Platform",
    summary: "负责高并发 API、领域建模、数据一致性和服务治理，优先保证接口契约稳定和可观测。",
    docker: {
      image: "openhire/backend-engineer:demo",
      name: "backend-core",
      ports: "8080, 5432",
      resources: "4 CPU / 8 GB RAM",
    },
    settings: {
      model: "gpt-5.4",
      mode: "Service implementation",
      workspace: "/workspace/services",
      guardrails: "API contract first, migration aware",
    },
    skills: ["API Design", "Domain Modeling", "SQL Tuning", "Queue Workers", "Integration Tests"],
    tools: ["python", "go", "postgres", "redis", "pytest"],
    exampleTasks: ["设计数字员工配置接口", "排查任务队列积压", "补齐支付回调幂等测试"],
  },
  {
    id: "sre-devops-engineer",
    defaultName: "Pulse SRE",
    role: "SRE/DevOps Engineer / 稳定性工程师",
    defaultAgentType: "openclaw",
    companyStyle: "Tencent-style Cloud Operations",
    summary: "负责部署、监控、告警和容量治理，关注服务稳定性、变更风险和故障恢复速度。",
    docker: {
      image: "openhire/sre-devops-engineer:demo",
      name: "sre-console",
      ports: "9090, 3001",
      resources: "2 CPU / 6 GB RAM",
    },
    settings: {
      model: "gpt-5.4",
      mode: "Operations review",
      workspace: "/workspace/infra",
      guardrails: "Least privilege, rollback ready",
    },
    skills: ["CI/CD", "Kubernetes", "Observability", "Incident Review", "Capacity Planning"],
    tools: ["docker", "kubectl", "helm", "prometheus", "grafana"],
    exampleTasks: ["生成服务发布检查清单", "分析 CPU 异常升高原因", "编写回滚演练步骤"],
  },
  {
    id: "data-product-analyst",
    defaultName: "Mira Data",
    role: "Data/Product Analyst / 数据产品分析师",
    defaultAgentType: "nanobot",
    companyStyle: "Meituan-style Local Services",
    summary: "负责指标体系、漏斗分析、用户分群和业务复盘，把产品问题拆成数据口径和可执行建议。",
    docker: {
      image: "openhire/data-product-analyst:demo",
      name: "data-insight",
      ports: "8501, 5433",
      resources: "2 CPU / 4 GB RAM",
    },
    settings: {
      model: "gpt-5.4",
      mode: "Insight generation",
      workspace: "/workspace/analytics",
      guardrails: "SQL read-only, source cited",
    },
    skills: ["SQL Analysis", "Funnel Metrics", "Cohort Analysis", "Dashboard Spec", "Experiment Review"],
    tools: ["python", "duckdb", "metabase", "notebook", "streamlit"],
    exampleTasks: ["分析投递转化率变化", "定义数字员工活跃指标", "生成周报洞察摘要"],
  },
];

const CUSTOM_ROLE_TEMPLATE = {
  id: CUSTOM_ROLE_TEMPLATE_ID,
  defaultName: "",
  role: "Custom Role / 自定义角色",
  defaultAgentType: "openclaw",
  companyStyle: "一句话描述你想创建的角色，然后用 Cook 自动生成。",
  summary: "",
  isCustomComposer: true,
  docker: {
    image: "custom",
    name: "custom-role",
    ports: "n/a",
    resources: "n/a",
  },
  settings: {
    model: "gpt-5.4",
    mode: "Custom role design",
    workspace: "/workspace",
    guardrails: "Prompt crafted by template cook.",
  },
  skills: [],
  tools: ["cook"],
  exampleTasks: ["描述岗位目标，烘焙成可创建的数字员工模板"],
};

const BUILTIN_TEMPLATE_LOCALIZATIONS = {
  "frontend-engineer": {
    en: {
      role: "Frontend Engineer",
      companyStyle: "ByteDance-style Growth Platform",
      summary: "Build growth-facing dashboards and complex interactive pages, from requirement breakdown to component implementation, performance tuning, and end-to-end validation.",
    },
    zh: {
      role: "前端工程师",
      companyStyle: "字节风格增长平台",
      summary: "面向增长、运营后台和复杂交互页面，负责从需求拆解到组件实现、性能优化和端到端验证。",
    },
  },
  "algorithm-engineer": {
    en: {
      role: "Algorithm Engineer",
      companyStyle: "Baidu-style Search & Recommendation",
      summary: "Own retrieval, ranking, evaluation, and experiment design, turning product goals into measurable algorithm iterations and online/offline metrics.",
    },
    zh: {
      role: "算法工程师",
      companyStyle: "百度风格搜索与推荐",
      summary: "负责召回、排序、评估和模型实验，把业务目标转成可度量的算法迭代和离线/在线指标。",
    },
  },
  "backend-engineer": {
    en: {
      role: "Backend Engineer",
      companyStyle: "Alibaba-style Commerce Platform",
      summary: "Build high-concurrency APIs, domain models, data consistency workflows, and service governance with stable contracts and observability first.",
    },
    zh: {
      role: "后端工程师",
      companyStyle: "阿里风格电商平台",
      summary: "负责高并发 API、领域建模、数据一致性和服务治理，优先保证接口契约稳定和可观测。",
    },
  },
  "sre-devops-engineer": {
    en: {
      role: "SRE / DevOps Engineer",
      companyStyle: "Tencent-style Cloud Operations",
      summary: "Own deployment, monitoring, alerting, and capacity management with a bias toward service stability, safe change management, and fast recovery.",
    },
    zh: {
      role: "SRE / DevOps 工程师",
      companyStyle: "腾讯风格云上运维",
      summary: "负责部署、监控、告警和容量治理，关注服务稳定性、变更风险和故障恢复速度。",
    },
  },
  "data-product-analyst": {
    en: {
      role: "Data / Product Analyst",
      companyStyle: "Meituan-style Local Services",
      summary: "Define metrics, funnels, cohorts, and business reviews, then turn product questions into clear data definitions and actionable recommendations.",
    },
    zh: {
      role: "数据 / 产品分析师",
      companyStyle: "美团风格本地生活",
      summary: "负责指标体系、漏斗分析、用户分群和业务复盘，把产品问题拆成数据口径和可执行建议。",
    },
  },
  [CUSTOM_ROLE_TEMPLATE_ID]: {
    en: {
      role: "Custom Role",
      companyStyle: "Describe the role you want and let Cook generate it automatically.",
      summary: "",
    },
    zh: {
      role: "自定义角色",
      companyStyle: "一句话描述你想创建的角色，然后用 Cook 自动生成。",
      summary: "",
    },
  },
};

function localizeTemplate(template) {
  const localization = BUILTIN_TEMPLATE_LOCALIZATIONS[template?.id]?.[currentLanguage()];
  if (!localization) {
    return template;
  }
  return {
    ...template,
    role: localization.role ?? template.role,
    companyStyle: localization.companyStyle ?? template.companyStyle,
    summary: localization.summary ?? template.summary,
  };
}

const EMPLOYEE_AVATAR_PRESETS = [
  { id: "coral-wave", label: "Coral Wave", background: "#ffe6dc", body: "#ff7a59", skin: "#f3c2a3", hair: "#8f3b2e", accent: "#ffd5c4", accessory: "glasses" },
  { id: "mint-spark", label: "Mint Spark", background: "#dff5ec", body: "#39a87d", skin: "#f0c4a6", hair: "#6e4c34", accent: "#fef4cb", accessory: "pin" },
  { id: "sky-visor", label: "Sky Visor", background: "#dfefff", body: "#4f8cff", skin: "#f2c6a8", hair: "#2c4166", accent: "#ffffff", accessory: "visor" },
  { id: "amber-cap", label: "Amber Cap", background: "#fff0d7", body: "#ff9e3d", skin: "#f1bf98", hair: "#70422c", accent: "#ffdd94", accessory: "cap" },
  { id: "violet-signal", label: "Violet Signal", background: "#efe4ff", body: "#8b67f6", skin: "#f0c0a0", hair: "#55328f", accent: "#d7cbff", accessory: "headset" },
  { id: "rose-pixel", label: "Rose Pixel", background: "#ffe2ef", body: "#ff5c97", skin: "#f4c3aa", hair: "#8f355f", accent: "#ffffff", accessory: "spark" },
  { id: "teal-anchor", label: "Teal Anchor", background: "#ddf3f2", body: "#2f9d95", skin: "#efc29c", hair: "#3e4747", accent: "#c8f0ec", accessory: "glasses" },
  { id: "sandstone", label: "Sandstone", background: "#f5e8db", body: "#c97f4f", skin: "#f0c8a7", hair: "#72503a", accent: "#fff2cf", accessory: "pin" },
];

const EMPLOYEE_AVATARS = EMPLOYEE_AVATAR_PRESETS.map((preset) => ({
  ...preset,
  src: createAvatarSvgDataUri(preset),
}));

const EMPLOYEE_AVATAR_INDEX = Object.fromEntries(
  EMPLOYEE_AVATARS.map((preset) => [preset.id, preset]),
);

const CREATE_WIZARD_STEPS = ["template", "profile", "skills", "review"];
const CREATE_WIZARD_STEP_LABELS = {
  template: "modal.create.wizard.template",
  profile: "modal.create.wizard.profile",
  skills: "modal.create.wizard.skills",
  review: "modal.create.wizard.review",
};
const CREATE_WIZARD_STEP_COPY = {
  template: "modal.create.wizard.template_copy",
  profile: "modal.create.wizard.profile_copy",
  skills: "modal.create.wizard.skills_copy",
  review: "modal.create.wizard.review_copy",
};

const employeeState = {
  employees: [],
  runtimeEmployees: [],
  selectedEmployeeId: null,
  selectedDeleteIds: [],
  isEmployeeListExpanded: false,
  isEmployeeDetailExpanded: false,
  employeeSortMode: readEmployeeSortMode(),
  selectedTemplateId: EMPLOYEE_TEMPLATES[0]?.id,
  selectedAvatarId: EMPLOYEE_AVATARS[0]?.id || "",
  selectedSkillIds: [],
  recommendedSkillIds: [],
  expandedSkillIds: [],
  skillRecommendation: defaultSkillRecommendation(),
  skillRecommendationRequestId: 0,
  lastCreateSkillSummary: "",
  customTemplates: [],
  hiddenTemplateIds: [],
  customRolePrompt: "",
  createDraft: null,
  createWizardStep: "template",
  createWizardError: "",
  completedCreateWizardSteps: [],
  lastSkillRecommendationProfileSignature: "",
  isCreateOpen: false,
  smartSkillRecommendEnabled: readSmartSkillRecommendEnabled(),
};

const organizationState = {
  server: null,
  draft: null,
  selectedEmployeeId: null,
  connectFromId: null,
  isSkillListExpanded: false,
  drag: null,
  validation: { valid: true, errors: [], warnings: [] },
  error: "",
  saveStatus: "",
  isLoading: false,
  isSaving: false,
  isDirty: false,
};

const skillState = {
  localSkills: [],
  selectedDeleteIds: [],
  previewSkill: null,
  previewLabel: "",
  previewSource: "",
  isSoulBannerImportOpen: false,
  isLoadingSoulBanner: false,
  soulBannerResults: [],
  selectedSoulBannerKeys: [],
  isSoulBannerListExpanded: false,
  isMbtiSbtiImportOpen: false,
  isLoadingMbtiSbti: false,
  mbtiSbtiResults: [],
  selectedMbtiSbtiKeys: [],
  isMbtiSbtiListExpanded: false,
  isWebImportOpen: false,
  webImportUrl: "",
  searchQuery: "",
  searchResults: [],
  selectedImportKeys: [],
  isSearching: false,
  isLocalSkillListExpanded: false,
  isSkillSearchResultsExpanded: false,
  expandedLocalSkillLabelIds: [],
  lastImportedSkillIds: [],
  contentModal: {
    isOpen: false,
    skillId: "",
    skill: null,
    markdown: "",
    draft: "",
    isEditing: false,
    isLoading: false,
    error: "",
    contentSource: "",
    canSyncEmployees: false,
    isDirty: false,
    syncedEmployees: 0,
    isSearchPreview: false,
    markdownStatus: "",
    markdownError: "",
  },
};

const SKILL_OPS_DEFAULT_VISIBLE_ACTIVE_ISSUES = 3;

const skillOpsState = {
  report: null,
  selectedIssueIds: [],
  isIssueListExpanded: false,
  isLoading: false,
  isScanning: false,
  isRemoteScanning: false,
  error: "",
  preview: null,
  pendingAction: "",
};

const agentSkillState = {
  skills: [],
  selectedName: "",
  selectedDetail: null,
  proposals: [],
  query: "",
  sourceFilter: "all",
  isLoading: false,
  isDetailLoading: false,
  isEditing: false,
  draft: "",
  error: "",
  packageResult: null,
  isCreateOpen: false,
  createName: "",
  createDescription: "",
  filePath: "",
  fileContent: "",
};

const adminState = {
  mainSessionKey: null,
  mainContextAction: null,
  dockerDaemonAction: null,
  dockerDaemonRepairResult: "",
  mainAgent: {},
  process: {},
  dockerDaemon: {},
  dockerAgents: [],
  demoMode: { enabled: false },
  demoTodos: [],
  employeeContextAction: null,
  generatedAt: "",
  confirmAction: null,
  busyAction: null,
  transcript: {
    isOpen: false,
    title: "",
    subtitle: "",
    endpoint: "",
    isLoading: false,
    error: "",
    payload: null,
  },
};
const employeeConfigState = {
  employeeId: "",
  files: [],
  selectedFile: EMPLOYEE_CONFIG_FILES[0],
  drafts: {},
  isEditing: false,
  isLoading: false,
  error: "",
  restartRequired: false,
  cronJobs: [],
  cronDraft: {
    id: "",
    name: "",
    message: "",
    kind: "every",
    everyMs: "3600000",
    expr: "0 9 * * *",
    tz: "",
    enabled: true,
    deliver: false,
  },
  isCronLoading: false,
  cronError: "",
};
let employeePollTimer = null;
let createEmployeeProgressTimer = null;
let caseImportProgressTimer = null;

const CONTEXT_ACTION_ENDPOINTS = {
  clear: "/admin/api/context/clear",
  compact: "/admin/api/context/compact",
};

const EMPLOYEE_CONTEXT_ENDPOINT = "/admin/api/employees/";

const TRANSCRIPT_ENDPOINTS = {
  main: "/admin/api/transcripts/main",
  docker: "/admin/api/transcripts/docker/",
};

const DOCKER_CONTAINERS_ENDPOINT = "/admin/api/docker-containers/";
const DOCKER_DAEMON_REPAIR_ENDPOINT = "/admin/api/docker-daemon/repair";
const RUNTIME_HISTORY_ENDPOINT = "/admin/api/runtime/history";
const EMPLOYEE_ADMIN_ENDPOINT = "/admin/api/employees/";
const EMPLOYEE_EXPORT_ENDPOINT = "/admin/api/employees/export";
const ORGANIZATION_ENDPOINT = "/admin/api/organization";
const CASES_ENDPOINT = "/admin/api/cases";
const CASE_OPS_ENDPOINT = "/admin/api/cases/ops";
const CASE_OPS_SCAN_ENDPOINT = "/admin/api/cases/ops/scan";
const CASE_OPS_IGNORE_ENDPOINT = "/admin/api/cases/ops/ignore";
const CASE_OPS_ACTION_ENDPOINT = "/admin/api/cases/ops/actions";
const CASE_CONFIG_IMPORT_PREVIEW_ENDPOINT = "/admin/api/cases/import/preview";
const CASE_CONFIG_IMPORT_ENDPOINT = "/admin/api/cases/import";
const LOCAL_SKILL_PREVIEW_ENDPOINT = "/skills/import/local/preview";
const SOULBANNER_SKILL_SEARCH_ENDPOINT = "/skills/search/soulbanner";
const MBTI_SBTI_SKILL_SEARCH_ENDPOINT = "/skills/search/mbti-sbti";
const WEB_SKILL_PREVIEW_ENDPOINT = "/skills/import/web/preview";
const SKILL_GOVERNANCE_ENDPOINT = "/admin/api/skills/governance";
const SKILL_GOVERNANCE_SCAN_ENDPOINT = "/admin/api/skills/governance/scan";
const SKILL_GOVERNANCE_IGNORE_ENDPOINT = "/admin/api/skills/governance/ignore";
const SKILL_GOVERNANCE_ACTION_ENDPOINT = "/admin/api/skills/governance/actions";
const AGENT_SKILLS_ENDPOINT = "/admin/api/agent-skills";
const AGENT_SKILL_PROPOSALS_ENDPOINT = "/admin/api/agent-skills/proposals";
const AGENT_SKILL_PROPOSAL_POLL_INTERVAL_MS = 15000;
const DREAM_ENDPOINT = "/admin/api/dream";
const DREAM_SUBJECT_ENDPOINT = "/admin/api/dream/subjects/";
const DREAM_FILE_TABS = ["SOUL.md", "USER.md", "MEMORY.md", "history.jsonl"];

const caseState = {
  cases: [],
  source: "",
  isLoading: false,
  error: "",
  isDetailOpen: false,
  selectedCaseId: "",
  detail: null,
  preview: null,
  importResult: null,
  detailError: "",
  importedCasePayload: null,
  detailSource: "catalog",
  detailSourceLabel: "",
};

const caseOpsState = {
  report: null,
  isLoading: false,
  isScanning: false,
  error: "",
  selectedIssueIds: [],
  preview: null,
  pendingAction: "",
};

const runtimeHistoryState = {
  samples: [],
  isLoading: false,
  error: "",
  windowSeconds: 900,
  sampleIntervalSeconds: 5,
  lastUpdatedAt: "",
};

const dreamState = {
  subjects: [],
  cron: null,
  runningSubjectIds: [],
  selectedSubjectId: "main",
  selectedFileName: "MEMORY.md",
  selectedCommitSha: "",
  detail: null,
  isLoading: false,
  isDetailLoading: false,
  isRunning: false,
  isRestoring: false,
  error: "",
  actionStatus: "",
};

const employeeExportState = {
  isOpen: false,
  isLoading: false,
  error: "",
  requestId: 0,
  payload: null,
  draft: {
    id: "",
    title: "",
    description: "",
  },
};

const companionRuntimeState = {
  hasSnapshot: false,
  lastMainStatus: "",
  lastBusy: false,
  lastDockerIssueCount: 0,
  lastContextLevel: "ok",
};

function companionPhrase(en, zh) {
  return currentLanguage() === "zh" ? zh : en;
}

function companionReact(options) {
  try {
    window.OpenHireCompanion?.react?.(options);
  } catch (error) {
    console.warn("[companion] reaction skipped", error);
  }
}

function dockerIssueCount(rows = []) {
  return (Array.isArray(rows) ? rows : []).filter((agent) => {
    const status = text(agent?.status, "").toLowerCase();
    return /error|failed|exited|unhealthy|unknown|dead/.test(status);
  }).length;
}

function companionContextLevel(value) {
  const current = percent(value);
  if (current >= 90) return "error";
  if (current >= 75) return "warning";
  return "ok";
}

function publishCompanionContext(payload = {}) {
  const mainAgent = payload.mainAgent || adminState.mainAgent || {};
  const dockerRows = payload.dockerContainers || payload.dockerAgents || adminState.dockerAgents || [];
  const context = mainAgent.context || {};
  try {
    window.OpenHireCompanionContext = {
      generatedAt: text(payload.generatedAt || adminState.generatedAt, ""),
      activeSection: currentActiveNavSection(),
      resourceTab: currentResourceHubTab(),
      mainStatus: text(mainAgent.status, "unknown"),
      mainStage: text(mainAgent.stage, "idle"),
      activeTaskCount: Number(mainAgent.activeTaskCount || 0),
      contextPercent: percent(context.percent),
      contextSource: text(context.source, "unknown"),
      dockerDaemonStatus: text((payload.dockerDaemon || adminState.dockerDaemon || {}).status, "unknown"),
      dockerWorkerCount: Array.isArray(dockerRows) ? dockerRows.length : 0,
      dockerIssueCount: dockerIssueCount(dockerRows),
      employeeCount: employeeState.employees.length,
      runtimeEmployeeCount: employeeState.runtimeEmployees.length,
      localSkillCount: skillState.localSkills.length,
      caseCount: caseState.cases.length,
      lastCaseImportStatus: text(caseState.importResult?.status, ""),
      lastSkillImportCount: skillState.lastImportedSkillIds.length,
      selectedEmployeeId: text(employeeState.selectedEmployeeId, ""),
    };
  } catch (error) {
    console.warn("[companion] context skipped", error);
  }
}

function syncCompanionRuntimeReaction(payload = {}) {
  const mainAgent = payload.mainAgent || {};
  const dockerRows = payload.dockerContainers || payload.dockerAgents || [];
  const status = text(mainAgent.status, "unknown").toLowerCase();
  const busy = /running|busy|working|processing|active/.test(status) || Number(mainAgent.activeTaskCount || 0) > 0;
  const issueCount = dockerIssueCount(dockerRows);
  const contextLevel = companionContextLevel(mainAgent.context?.percent);
  const statusIsError = /error|failed|crash|stuck/.test(status);

  if (!companionRuntimeState.hasSnapshot) {
    companionRuntimeState.hasSnapshot = true;
    companionRuntimeState.lastMainStatus = status;
    companionRuntimeState.lastBusy = busy;
    companionRuntimeState.lastDockerIssueCount = issueCount;
    companionRuntimeState.lastContextLevel = contextLevel;
    if (statusIsError || issueCount > 0) {
      companionReact({
        type: "error",
        bubble: companionPhrase(
          `${issueCount || 1} runtime issue needs attention.`,
          `检测到 ${issueCount || 1} 个运行态异常。`,
        ),
      });
    }
    return;
  }

  if (statusIsError && status !== companionRuntimeState.lastMainStatus) {
    companionReact({
      type: "error",
      bubble: companionPhrase("Main agent reported an error.", "主控状态进入异常。"),
    });
  } else if (issueCount > companionRuntimeState.lastDockerIssueCount) {
    companionReact({
      type: "error",
      bubble: companionPhrase(
        `${issueCount} Docker worker issue(s) visible.`,
        `有 ${issueCount} 个 Docker worker 需要处理。`,
      ),
    });
  } else if (contextLevel !== companionRuntimeState.lastContextLevel && contextLevel !== "ok") {
    companionReact({
      type: contextLevel,
      bubble: companionPhrase(
        `Context pressure is ${percent(mainAgent.context?.percent)}%.`,
        `上下文压力达到 ${percent(mainAgent.context?.percent)}%。`,
      ),
    });
  } else if (busy && !companionRuntimeState.lastBusy) {
    companionReact({
      type: "thinking",
      bubble: companionPhrase("Main agent is working.", "主控开始处理任务。"),
    });
  } else if (!busy && companionRuntimeState.lastBusy) {
    companionReact({
      type: "ready",
      bubble: companionPhrase("Runtime settled back to idle.", "运行态已回到空闲。"),
    });
  }

  companionRuntimeState.lastMainStatus = status;
  companionRuntimeState.lastBusy = busy;
  companionRuntimeState.lastDockerIssueCount = issueCount;
  companionRuntimeState.lastContextLevel = contextLevel;
}

function badgeClass(status) {
  return `badge status-${String(status || "unknown").replace(/[^a-z_]/g, "_")}`;
}

function percent(value) {
  return Math.max(0, Math.min(100, Number(value || 0)));
}

function text(value, fallback = "unknown") {
  return value === null || value === undefined || value === "" ? fallback : String(value);
}

function finiteNumber(value) {
  if (value === null || value === undefined || value === "") return null;
  const numeric = Number(value);
  return Number.isFinite(numeric) ? numeric : null;
}

function sleep(ms) {
  return new Promise((resolve) => window.setTimeout(resolve, ms));
}

function normalizeEmployeeSortMode(value) {
  const mode = text(value, DEFAULT_EMPLOYEE_SORT_MODE);
  return Object.prototype.hasOwnProperty.call(EMPLOYEE_SORT_MODES, mode) ? mode : DEFAULT_EMPLOYEE_SORT_MODE;
}

function readEmployeeSortMode() {
  try {
    return normalizeEmployeeSortMode(window.localStorage?.getItem(EMPLOYEE_SORT_STORAGE_KEY));
  } catch {
    return DEFAULT_EMPLOYEE_SORT_MODE;
  }
}

function writeEmployeeSortMode(mode) {
  try {
    window.localStorage?.setItem(EMPLOYEE_SORT_STORAGE_KEY, normalizeEmployeeSortMode(mode));
  } catch {
    // Ignore storage failures and keep the in-memory preference.
  }
}

function readSmartSkillRecommendEnabled() {
  try {
    return window.localStorage?.getItem(SMART_SKILL_RECOMMEND_STORAGE_KEY) !== "false";
  } catch {
    return true;
  }
}

function writeSmartSkillRecommendEnabled(enabled) {
  try {
    window.localStorage?.setItem(SMART_SKILL_RECOMMEND_STORAGE_KEY, enabled ? "true" : "false");
  } catch {
    // Ignore storage failures and keep the in-memory preference.
  }
}

function employeeSortModeLabel(mode) {
  if (mode === "updated") return t("sort.updated");
  if (mode === "created") return t("sort.created");
  return t("sort.type");
}

function themeToggleLabel() {
  return currentTheme() === "dark" ? t("preferences.theme.light") : t("preferences.theme.dark");
}

function staticTextForKey(key) {
  if (key === "preferences.theme.toggle") {
    return t("preferences.theme.toggle", { mode: themeToggleLabel() });
  }
  return t(key);
}

function syncDocumentPreferences() {
  document.documentElement.lang = currentLanguage() === "zh" ? "zh-CN" : "en";
  document.documentElement.dataset.theme = currentTheme();
  document.title = t("document.title");
}

function renderGeneratedAt() {
  const generatedAt = document.getElementById("generated-at");
  if (!generatedAt) return;
  generatedAt.textContent = adminState.generatedAt
    ? t("nav.snapshot.current", { value: adminState.generatedAt })
    : t("nav.snapshot.pending");
}

function renderPreferenceControls() {
  const zhButton = document.getElementById("admin-language-zh");
  const enButton = document.getElementById("admin-language-en");
  const themeButton = document.getElementById("admin-theme-toggle");
  const themeLabel = document.getElementById("admin-theme-toggle-label");
  if (zhButton) {
    const isActive = currentLanguage() === "zh";
    zhButton.classList.toggle("is-active", isActive);
    zhButton.setAttribute("aria-pressed", isActive ? "true" : "false");
  }
  if (enButton) {
    const isActive = currentLanguage() === "en";
    enButton.classList.toggle("is-active", isActive);
    enButton.setAttribute("aria-pressed", isActive ? "true" : "false");
  }
  if (themeButton) {
    themeButton.classList.toggle("is-dark", currentTheme() === "dark");
    themeButton.dataset.themeTarget = currentTheme() === "dark" ? "light" : "dark";
    themeButton.setAttribute("aria-label", staticTextForKey("preferences.theme.toggle"));
    themeButton.setAttribute("title", staticTextForKey("preferences.theme.toggle"));
  }
  if (themeLabel) {
    themeLabel.textContent = staticTextForKey("preferences.theme.toggle");
  }
}

function findNavSectionConfig(sectionKey) {
  return NAV_SECTIONS.find((section) => section.key === String(sectionKey || "")) || NAV_SECTIONS[0];
}

function renderNavSectionLinks() {
  const activeKey = currentActiveNavSection();
  document.querySelectorAll("[data-nav-target]").forEach((node) => {
    const sectionKey = node.getAttribute("data-nav-key");
    const isActive = sectionKey === activeKey;
    node.classList.toggle("is-active", isActive);
    if (isActive) {
      node.setAttribute("aria-current", "true");
    } else {
      node.removeAttribute("aria-current");
    }
  });
}

function setActiveNavSection(sectionKey) {
  const next = findNavSectionConfig(sectionKey).key;
  if (next === uiState.activeNavSection) {
    renderNavSectionLinks();
    return;
  }
  uiState.activeNavSection = next;
  renderNavSectionLinks();
}

function navTargetElement(targetId) {
  return document.getElementById(String(targetId || ""));
}

function navTargetScrollTop(target) {
  const top = target.getBoundingClientRect().top + window.scrollY - NAV_SCROLL_OFFSET;
  return Math.max(0, top);
}

function scrollToNavSection(targetId) {
  const target = navTargetElement(targetId);
  if (!target) return;
  setActiveNavSection(targetId);
  window.scrollTo({
    top: navTargetScrollTop(target),
    behavior: "smooth",
  });
}

function syncActiveNavSection() {
  const scrollLine = window.scrollY + NAV_SCROLL_OFFSET + 12;
  let activeKey = NAV_SECTIONS[0].key;
  for (const section of NAV_SECTIONS) {
    const target = navTargetElement(section.targetId);
    if (!target) continue;
    if (target.offsetTop <= scrollLine) {
      activeKey = section.key;
    }
  }
  setActiveNavSection(activeKey);
}

function requestNavSectionSync() {
  if (navScrollTicking) return;
  navScrollTicking = true;
  window.requestAnimationFrame(() => {
    navScrollTicking = false;
    syncActiveNavSection();
  });
}

function observeNavSections() {
  navSectionObserver?.disconnect();
  if (typeof window === "undefined" || typeof window.IntersectionObserver !== "function") {
    syncActiveNavSection();
    return;
  }
  navSectionObserver = new IntersectionObserver(
    () => requestNavSectionSync(),
    {
      root: null,
      rootMargin: `-${NAV_SCROLL_OFFSET}px 0px -55% 0px`,
      threshold: [0, 0.2, 0.45, 0.8, 1],
    },
  );
  for (const section of NAV_SECTIONS) {
    const target = navTargetElement(section.targetId);
    if (target) {
      navSectionObserver.observe(target);
    }
  }
  syncActiveNavSection();
}

function renderHeroBar() {
  const heroSummary = document.getElementById("hero-runtime-summary");
  if (!heroSummary) return;
  const processRole = text(adminState.process?.role, "unknown");
  const mainStatus = text(adminState.mainAgent?.status, "unknown");
  const sessionValue = text(
    adminState.mainSessionKey || adminState.mainAgent?.sessionKey || adminState.mainAgent?.lastSessionKey,
    "none",
  );
  const ctxPercent = percent(adminState.mainAgent?.context?.percent);
  heroSummary.innerHTML = `
    <span class="hero-runtime-pill hud-pill"><span class="hud-pill-dot" aria-hidden="true"></span>ROLE · ${html(processRole)}</span>
    <span class="${badgeClass(mainStatus)} hero-runtime-status hud-status"><span class="hud-status-dot" aria-hidden="true"></span>${html(mainStatus)}</span>
    <span class="hero-runtime-pill hud-pill hud-pill-violet">CTX · ${ctxPercent}%</span>
    <span class="hero-runtime-note">${t("main.latest_session", { value: sessionValue })}</span>
  `;
}

function dockerDaemonIssue() {
  if (isDemoMode()) return null;
  const daemon = adminState.dockerDaemon || {};
  if (daemon.ok !== false) return null;
  const status = text(daemon.status, "").toLowerCase();
  if (!status || status === "running") return null;
  return daemon;
}

function isDemoMode() {
  return adminState.demoMode?.enabled === true;
}

function dockerDaemonMessage(daemon) {
  return text(daemon?.message || daemon?.status, "Docker daemon is not reachable.");
}

function collectAlertItems() {
  const items = [];
  const mainAgent = adminState.mainAgent || {};
  const context = mainAgent.context || {};
  const contextPercent = percent(context.percent);
  if (contextPercent >= 70) {
    items.push({
      level: "warning",
      message: `${t("alert.context_pressure")} ${contextPercent}% · ${text(context.usedTokens, "0")} / ${text(context.totalTokens, "0")}`,
    });
  }
  const sessionValue = text(mainAgent.sessionKey || mainAgent.lastSessionKey, "");
  if (text(mainAgent.status, "").toLowerCase() === "idle" && !sessionValue) {
    items.push({
      level: "idle",
      message: `${t("alert.main_idle")} ${t("main.latest_session", { value: "none" })}`,
    });
  }
  const daemonIssue = dockerDaemonIssue();
  if (daemonIssue) {
    items.push({
      level: "danger",
      message: `${t("alert.docker_daemon")} ${dockerDaemonMessage(daemonIssue)}`,
    });
  }
  const dockerIssues = (adminState.dockerAgents || []).filter((agent) => {
    const status = text(agent?.status, "").toLowerCase();
    return ["error", "exited", "unknown"].includes(status);
  });
  if (dockerIssues.length) {
    items.push({
      level: "danger",
      message: `${t("alert.docker_issue")} ${t("alert.docker_issue_count", { count: dockerIssues.length })}`,
    });
  }
  if (caseState.importResult && (caseState.importResult.status === "partial" || Number(caseState.importResult.failed_count || 0) > 0)) {
    items.push({
      level: "warning",
      message: `${t("alert.import_warning")} ${t("alert.import_warning_count", { count: text(caseState.importResult.failed_count, "0") })}`,
    });
  }
  return items;
}

function renderAlertStrip() {
  const root = document.getElementById("alert-strip");
  if (!root) return;
  const alerts = collectAlertItems();
  root.innerHTML = alerts.length
    ? alerts.map((item) => `
      <div class="alert-chip alert-${item.level}">
        <span class="alert-chip-dot" aria-hidden="true"></span>
        <span>${html(item.message)}</span>
      </div>
    `).join("")
    : `<div class="alert-chip alert-ok"><span class="alert-chip-dot" aria-hidden="true"></span><span>${t("alert.none")}</span></div>`;
}

function businessSkillCount() {
  return skillState.localSkills.filter((skill) => !isRequiredLocalSkill(skill)).length;
}

function employeeHasBusinessSkill(employee, businessSkillIds) {
  const skillIds = normalizeSkillIds(employee?.skill_ids);
  if (skillIds.length) {
    return skillIds.some((skillId) => businessSkillIds.has(skillId));
  }
  const names = Array.isArray(employee?.skills) ? employee.skills : [];
  return names.some((name) => {
    const normalized = text(name, "").trim().toLowerCase();
    return normalized && normalized !== REQUIRED_EMPLOYEE_SKILL_ID && normalized !== "优秀员工协议";
  });
}

function employeesMissingBusinessSkills(businessSkillIds) {
  if (!employeeState.employees.length) return [];
  return employeeState.employees.filter((employee) => !employeeHasBusinessSkill(employee, businessSkillIds));
}

function pendingAgentSkillProposals() {
  return agentSkillState.proposals.filter((proposal) => proposal.status === "pending");
}

function collectActionItems() {
  const items = [];
  if (isDemoMode() && Array.isArray(adminState.demoTodos) && adminState.demoTodos.length) {
    items.push(...adminState.demoTodos.map((item) => ({
      key: text(item?.key, "demo-todo"),
      level: text(item?.level, "idle"),
      title: text(item?.title, "Demo task"),
      body: text(item?.body, ""),
      actions: Array.isArray(item?.actions) ? item.actions : [],
      demo: true,
    })));
  }
  const pendingProposals = pendingAgentSkillProposals();
  if (pendingProposals.length) {
    items.push({
      key: "agent-skill-proposals",
      level: "warning",
      title: t("action.agent_skill_proposals.title"),
      body: t("action.agent_skill_proposals.body", {
        count: pendingProposals.length,
        name: text(pendingProposals[0]?.name, "proposal"),
      }),
      actions: [{ kind: "agent-skills", label: t("action.agent_skill_proposals.action") }],
    });
  }
  const mainAgent = adminState.mainAgent || {};
  const context = mainAgent.context || {};
  const contextPercent = percent(context.percent);
  const sessionValue = text(mainAgent.sessionKey || mainAgent.lastSessionKey, "");
  if (contextPercent >= 70) {
    items.push({
      key: "context-pressure",
      level: "warning",
      title: t("action.context_pressure.title"),
      body: t("action.context_pressure.body", {
        percent: contextPercent,
        tokens: `${text(context.usedTokens, "0")} / ${text(context.totalTokens, "0")}`,
      }),
      actions: [{
        kind: "compact",
        label: t("action.context_pressure.action"),
        disabled: !sessionValue || Boolean(adminState.mainContextAction),
      }],
    });
  }
  if (text(mainAgent.status, "").toLowerCase() === "idle" && !sessionValue) {
    items.push({
      key: "main-idle",
      level: "idle",
      title: t("action.main_idle.title"),
      body: t("action.main_idle.body"),
      actions: [{ kind: "control", label: t("action.main_idle.action") }],
    });
  }
  const daemonIssue = dockerDaemonIssue();
  if (daemonIssue) {
    const repairing = adminState.dockerDaemonAction === "repair";
    items.push({
      key: "docker-daemon",
      level: "danger",
      title: t("action.docker_daemon.title"),
      body: t("action.docker_daemon.body", { message: dockerDaemonMessage(daemonIssue) }),
      actions: [
        {
          kind: "docker-repair",
          label: repairing ? t("docker.daemon_repairing") : t("action.docker_daemon.repair"),
          disabled: repairing,
        },
        { kind: "infrastructure", label: t("action.docker_daemon.action") },
      ],
    });
  }
  const dockerIssues = (adminState.dockerAgents || []).filter((agent) => {
    const status = text(agent?.status, "").toLowerCase();
    return ["error", "exited", "unknown"].includes(status);
  });
  if (dockerIssues.length) {
    items.push({
      key: "docker-issue",
      level: "danger",
      title: t("action.docker_issue.title"),
      body: t("action.docker_issue.body", { count: dockerIssues.length }),
      actions: [{ kind: "infrastructure", label: t("action.docker_issue.action") }],
    });
  }
  if (caseState.importResult && (caseState.importResult.status === "partial" || Number(caseState.importResult.failed_count || 0) > 0)) {
    const failedCount = text(caseState.importResult.failed_count, "0");
    items.push({
      key: "case-partial",
      level: "warning",
      title: t("action.case_partial.title"),
      body: t("action.case_partial.body", { count: failedCount }),
      actions: [{ kind: "cases", label: t("action.case_partial.action") }],
    });
  }
  const businessSkillIds = new Set(skillState.localSkills.filter((skill) => !isRequiredLocalSkill(skill)).map((skill) => skill.id));
  const businessSkillTotal = businessSkillCount();
  if (skillState.localSkills.length && businessSkillTotal === 0) {
    items.push({
      key: "no-business-skills",
      level: "warning",
      title: t("action.no_business_skills.title"),
      body: t("action.no_business_skills.body"),
      actions: [{ kind: "skills", label: t("action.no_business_skills.action") }],
    });
  } else if (businessSkillTotal > 0) {
    const missingEmployees = employeesMissingBusinessSkills(businessSkillIds);
    if (missingEmployees.length) {
      items.push({
        key: "employee-missing-skills",
        level: "warning",
        title: t("action.employee_missing_skills.title"),
        body: t("action.employee_missing_skills.body", {
          count: missingEmployees.length,
          name: text(missingEmployees[0]?.name, "employee"),
        }),
        actions: [{
          kind: "employee",
          employeeId: missingEmployees[0]?.id,
          label: t("action.employee_missing_skills.action"),
        }],
      });
    }
  }
  if (items.length) return items;
  return [{
    key: "healthy-actions",
    level: "ok",
    title: t("action.healthy.title"),
    body: t("action.healthy.body"),
    actions: [
      { kind: "create", label: t("action.create_employee.action") },
      { kind: "cases", label: t("action.browse_cases.action") },
      { kind: "skills", label: t("action.review_skills.action") },
    ],
  }];
}

function actionDataAttribute(action) {
  switch (action.kind) {
    case "compact":
      return 'data-action-center-compact="true"';
    case "control":
      return 'data-action-center-control="true"';
    case "infrastructure":
      return 'data-action-center-infrastructure="true"';
    case "docker-repair":
      return 'data-action-center-docker-repair="true"';
    case "cases":
      return 'data-action-center-cases="true"';
    case "skills":
      return 'data-action-center-skills="true"';
    case "agent-skills":
      return 'data-action-center-agent-skills="true"';
    case "employee":
      return `data-action-center-employee="${html(action.employeeId, "")}"`;
    case "create":
      return 'data-action-center-create="true"';
    default:
      return "";
  }
}

function renderActionCenterButton(action) {
  return `
    <button
      class="action-card-button"
      type="button"
      ${actionDataAttribute(action)}
      ${action.disabled ? "disabled" : ""}
    >${html(action.label, "Open")}</button>
  `;
}

function renderActionCenter() {
  const root = document.getElementById("action-center");
  if (!root) return;
  const items = collectActionItems();
  root.innerHTML = `
    <div class="action-center-head">
      <div>
        <div class="agent-section-title">${t("action.title")}</div>
        <p class="section-copy">${t("action.copy")}</p>
      </div>
    </div>
    <div class="action-card-grid">
      ${items.map((item) => `
        <article class="action-card is-${html(item.level, "idle")}">
          <div class="action-card-copy">
            <strong>${html(item.title)}</strong>
            <span>${html(item.body)}</span>
          </div>
          <div class="action-card-actions">
            ${(item.actions || []).map(renderActionCenterButton).join("")}
          </div>
        </article>
      `).join("")}
    </div>
  `;
}

function parseDockerCpuPercent(value) {
  if (value === null || value === undefined || value === "") return null;
  const match = String(value).trim().match(/^([0-9]+(?:\.[0-9]+)?)\s*%?$/);
  return match ? Math.max(0, Number(match[1])) : null;
}

function parseDockerMemoryMiB(value) {
  if (value === null || value === undefined || value === "") return null;
  const textValue = String(value).split("/", 1)[0].trim();
  const match = textValue.match(/^([0-9]+(?:\.[0-9]+)?)\s*([kmgt]?i?b)?/i);
  if (!match) return null;
  const amount = Math.max(0, Number(match[1]));
  const unit = String(match[2] || "b").toLowerCase();
  const multipliers = {
    b: 1 / (1024 * 1024),
    kb: 1 / 1024,
    kib: 1 / 1024,
    mb: 1,
    mib: 1,
    gb: 1024,
    gib: 1024,
    tb: 1024 * 1024,
    tib: 1024 * 1024,
  };
  return Object.prototype.hasOwnProperty.call(multipliers, unit)
    ? Math.round(amount * multipliers[unit] * 100) / 100
    : null;
}

function normalizeRuntimeHistorySample(sample) {
  const generatedAt = text(sample?.generatedAt, new Date().toISOString());
  const parsedEpoch = Date.parse(generatedAt);
  const epochMs = finiteNumber(sample?.epochMs) ?? (Number.isFinite(parsedEpoch) ? parsedEpoch : Date.now());
  const dockerDaemonOk = sample?.dockerDaemonOk === true ? true : (sample?.dockerDaemonOk === false ? false : null);
  return {
    generatedAt,
    epochMs,
    mainStatus: text(sample?.mainStatus, "unknown"),
    mainStage: text(sample?.mainStage, "idle"),
    sessionKey: text(sample?.sessionKey, ""),
    activeTaskCount: Math.max(0, Number(sample?.activeTaskCount || 0)),
    contextPercent: percent(sample?.contextPercent),
    contextUsedTokens: Math.max(0, Number(sample?.contextUsedTokens || 0)),
    contextTotalTokens: Math.max(0, Number(sample?.contextTotalTokens || 0)),
    processUptimeSeconds: Math.max(0, Number(sample?.processUptimeSeconds || 0)),
    dockerDaemonStatus: text(sample?.dockerDaemonStatus, "unknown"),
    dockerDaemonOk,
    dockerTotal: Math.max(0, Number(sample?.dockerTotal || 0)),
    dockerRunning: Math.max(0, Number(sample?.dockerRunning || 0)),
    dockerIssues: Math.max(0, Number(sample?.dockerIssues || 0)),
    dockerCpuAvgPercent: finiteNumber(sample?.dockerCpuAvgPercent),
    dockerCpuMaxPercent: finiteNumber(sample?.dockerCpuMaxPercent),
    dockerMemoryTotalMiB: finiteNumber(sample?.dockerMemoryTotalMiB),
  };
}

function runtimeHistorySampleFromPayload(payload) {
  payload = payload || {};
  const main = payload.mainAgent || {};
  const context = main.context || {};
  const process = payload.process || {};
  const daemon = payload.dockerDaemon || {};
  const containers = Array.isArray(payload.dockerContainers)
    ? payload.dockerContainers
    : (Array.isArray(payload.dockerAgents) ? payload.dockerAgents : []);
  const cpuValues = [];
  const memoryValues = [];
  let running = 0;
  let issues = 0;
  for (const container of containers) {
    const status = text(container?.status, "").toLowerCase();
    if (status === "running" || status === "processing") running += 1;
    if (["error", "exited", "unknown"].includes(status)) issues += 1;
    const cpu = parseDockerCpuPercent(container?.cpuPercent);
    if (cpu !== null) cpuValues.push(cpu);
    const memory = parseDockerMemoryMiB(container?.memoryUsage);
    if (memory !== null) memoryValues.push(memory);
  }
  return normalizeRuntimeHistorySample({
    generatedAt: payload.generatedAt || new Date().toISOString(),
    mainStatus: main.status,
    mainStage: main.stage,
    sessionKey: main.sessionKey || main.lastSessionKey,
    activeTaskCount: main.activeTaskCount,
    contextPercent: context.percent,
    contextUsedTokens: context.usedTokens,
    contextTotalTokens: context.totalTokens,
    processUptimeSeconds: process.uptimeSeconds || main.uptimeSeconds,
    dockerDaemonStatus: daemon.status,
    dockerDaemonOk: daemon.ok,
    dockerTotal: containers.length,
    dockerRunning: running,
    dockerIssues: issues,
    dockerCpuAvgPercent: cpuValues.length ? cpuValues.reduce((sum, value) => sum + value, 0) / cpuValues.length : null,
    dockerCpuMaxPercent: cpuValues.length ? Math.max(...cpuValues) : null,
    dockerMemoryTotalMiB: memoryValues.length ? memoryValues.reduce((sum, value) => sum + value, 0) : null,
  });
}

function appendRuntimeHistorySample(sample) {
  const normalized = normalizeRuntimeHistorySample(sample);
  const previous = runtimeHistoryState.samples[runtimeHistoryState.samples.length - 1];
  if (previous && previous.generatedAt === normalized.generatedAt) {
    runtimeHistoryState.samples = [
      ...runtimeHistoryState.samples.slice(0, -1),
      normalized,
    ];
  } else {
    runtimeHistoryState.samples = [...runtimeHistoryState.samples, normalized].slice(-RUNTIME_HISTORY_MAX_SAMPLES);
  }
  runtimeHistoryState.lastUpdatedAt = normalized.generatedAt;
}

function runtimeSeries(samples, key) {
  return samples
    .map((sample) => finiteNumber(sample?.[key]))
    .filter((value) => value !== null);
}

function compactRuntimeStatusSamples(samples, maxSegments = 96) {
  if (!Array.isArray(samples) || samples.length <= maxSegments) return samples || [];
  const lastIndex = samples.length - 1;
  return Array.from({ length: maxSegments }, (_, index) => {
    const sourceIndex = Math.round((index / Math.max(1, maxSegments - 1)) * lastIndex);
    return samples[sourceIndex];
  });
}

function renderRuntimeSparkline(samples, key, options = {}) {
  const values = runtimeSeries(samples, key);
  if (!values.length) {
    return `<div class="runtime-sparkline is-empty" aria-hidden="true"></div>`;
  }
  const series = values.length === 1 ? [values[0], values[0]] : values;
  const width = 160;
  const height = 48;
  const minValue = finiteNumber(options.min) ?? 0;
  const maxValue = Math.max(finiteNumber(options.max) ?? 0, ...series, minValue + 1);
  const range = Math.max(1, maxValue - minValue);
  const points = series.map((value, index) => {
    const x = series.length === 1 ? 0 : (index / Math.max(1, series.length - 1)) * width;
    const y = height - (((value - minValue) / range) * height);
    return `${Math.round(x * 10) / 10},${Math.round(y * 10) / 10}`;
  }).join(" ");
  const lastX = series.length === 1 ? 0 : width;
  const lastValue = series[series.length - 1];
  const lastY = height - (((lastValue - minValue) / range) * height);
  const areaPoints = `0,${height} ${points} ${lastX},${height}`;
  const gradId = `sparkGrad-${Math.random().toString(36).slice(2, 9)}`;
  const glowId = `sparkGlow-${Math.random().toString(36).slice(2, 9)}`;
  return `
    <svg class="runtime-sparkline" viewBox="0 0 ${width} ${height}" preserveAspectRatio="none" aria-hidden="true">
      <defs>
        <linearGradient id="${gradId}" x1="0" y1="0" x2="1" y2="0">
          <stop offset="0%" stop-color="var(--neon-cyan)" />
          <stop offset="100%" stop-color="var(--neon-violet)" />
        </linearGradient>
        <linearGradient id="${gradId}-area" x1="0" y1="0" x2="0" y2="1">
          <stop offset="0%" stop-color="var(--neon-cyan)" stop-opacity="0.32" />
          <stop offset="100%" stop-color="var(--neon-violet)" stop-opacity="0" />
        </linearGradient>
        <filter id="${glowId}" x="-20%" y="-50%" width="140%" height="200%">
          <feGaussianBlur stdDeviation="1.4" result="coloredBlur" />
          <feMerge>
            <feMergeNode in="coloredBlur" />
            <feMergeNode in="SourceGraphic" />
          </feMerge>
        </filter>
      </defs>
      <polygon class="runtime-sparkline-area" points="${areaPoints}" fill="url(#${gradId}-area)" />
      <polyline points="${points}" stroke="url(#${gradId})" filter="url(#${glowId})" />
      <circle class="runtime-sparkline-head" cx="${Math.round(lastX * 10) / 10}" cy="${Math.round(lastY * 10) / 10}" r="2.4" fill="var(--neon-cyan)" filter="url(#${glowId})" />
    </svg>
  `;
}

function renderRuntimeStatusStrip(samples) {
  if (!samples.length) return `<div class="runtime-status-strip is-empty" aria-hidden="true"></div>`;
  const segments = compactRuntimeStatusSamples(samples);
  return `
    <div class="runtime-status-strip" aria-hidden="true">
      ${segments.map((sample) => `
        <span
          class="runtime-status-segment status-${html(text(sample.mainStatus, "unknown").replace(/[^a-z_]/gi, "_").toLowerCase())}"
          title="${html(`${sample.mainStatus} · ${sample.mainStage}`)}"
        ></span>
      `).join("")}
    </div>
  `;
}

function formatRuntimeNumber(value, suffix = "") {
  const numeric = finiteNumber(value);
  if (numeric === null) return "n/a";
  const rounded = Math.round(numeric * 10) / 10;
  return `${rounded}${suffix}`;
}

function formatRuntimeLastUpdatedAgo(value) {
  const normalized = text(value, "");
  const parsed = Date.parse(normalized);
  if (!Number.isFinite(parsed)) return formatUtcDate(normalized);
  const elapsedMs = Math.max(0, Date.now() - parsed);
  const totalMinutes = Math.floor(elapsedMs / RUNTIME_TIMELINE_MINUTE_MS);
  const days = Math.floor(totalMinutes / RUNTIME_TIMELINE_DAY_MINUTES);
  const hours = Math.floor((totalMinutes % RUNTIME_TIMELINE_DAY_MINUTES) / RUNTIME_TIMELINE_HOUR_MINUTES);
  const minutes = totalMinutes % RUNTIME_TIMELINE_HOUR_MINUTES;
  if (days > 0) {
    return t("runtime.timeline.ago.days_hours_minutes", { days, hours, minutes });
  }
  return t("runtime.timeline.ago.hours_minutes", { hours, minutes });
}

function renderRuntimeTrendCard({ title, value, meta, body }) {
  return `
    <article class="runtime-trend-card">
      <div class="runtime-trend-card-top">
        <span>${html(title)}</span>
        <strong>${html(value)}</strong>
      </div>
      <div class="runtime-trend-meta">${html(meta)}</div>
      ${body}
    </article>
  `;
}

function renderRuntimeTimeline() {
  const root = document.getElementById("runtime-timeline");
  if (!root) return;
  const samples = runtimeHistoryState.samples;
  const latest = samples[samples.length - 1] || null;
  const loading = runtimeHistoryState.isLoading;
  const error = text(runtimeHistoryState.error, "");
  const windowMinutes = Math.round(Number(runtimeHistoryState.windowSeconds || 0) / 60);
  const lastUpdated = runtimeHistoryState.lastUpdatedAt
    ? t("runtime.timeline.last_updated", { value: formatRuntimeLastUpdatedAgo(runtimeHistoryState.lastUpdatedAt) })
    : t("runtime.timeline.empty");
  const contextTokens = latest
    ? `${Math.round(latest.contextUsedTokens)} / ${Math.round(latest.contextTotalTokens)}`
    : "0 / 0";
  const dockerCounts = latest
    ? t("runtime.timeline.docker_counts", {
      running: Math.round(latest.dockerRunning),
      total: Math.round(latest.dockerTotal),
      issues: Math.round(latest.dockerIssues),
    })
    : t("runtime.timeline.docker_counts", { running: 0, total: 0, issues: 0 });
  const cpuMeta = t("runtime.timeline.cpu", {
    avg: formatRuntimeNumber(latest?.dockerCpuAvgPercent, "%"),
    max: formatRuntimeNumber(latest?.dockerCpuMaxPercent, "%"),
  });
  const memoryMeta = t("runtime.timeline.memory", {
    value: formatRuntimeNumber(latest?.dockerMemoryTotalMiB),
  });
  root.innerHTML = `
    <div class="runtime-timeline-head">
      <div>
        <div class="agent-section-title">${t("runtime.timeline.title")}</div>
        <p class="section-copy">${t("runtime.timeline.copy")}</p>
      </div>
      <div class="runtime-timeline-actions">
        <span class="runtime-timeline-meta">${html(lastUpdated)}</span>
        <button class="secondary-button" type="button" data-runtime-history-refresh="true" ${loading ? "disabled" : ""}>
          ${loading ? t("runtime.timeline.refreshing") : t("runtime.timeline.refresh")}
        </button>
      </div>
    </div>
    ${error ? `<div class="runtime-timeline-error">${html(t("runtime.timeline.error", { message: error }))}</div>` : ""}
    <div class="runtime-timeline-meta">${html(t("runtime.timeline.window", { count: samples.length, minutes: windowMinutes }))}</div>
    ${samples.length ? `
      <div class="runtime-trend-grid">
        ${renderRuntimeTrendCard({
          title: t("runtime.timeline.context"),
          value: `${Math.round(latest.contextPercent)}%`,
          meta: contextTokens,
          body: renderRuntimeSparkline(samples, "contextPercent", { min: 0, max: 100 }),
        })}
        ${renderRuntimeTrendCard({
          title: t("runtime.timeline.main_status"),
          value: latest.mainStatus,
          meta: text(latest.mainStage, "idle"),
          body: renderRuntimeStatusStrip(samples),
        })}
        ${renderRuntimeTrendCard({
          title: t("runtime.timeline.docker_health"),
          value: text(latest.dockerDaemonStatus, "unknown"),
          meta: dockerCounts,
          body: renderRuntimeSparkline(samples, "dockerIssues", { min: 0 }),
        })}
        ${renderRuntimeTrendCard({
          title: t("runtime.timeline.resources"),
          value: cpuMeta,
          meta: memoryMeta,
          body: `
            ${renderRuntimeSparkline(samples, "dockerCpuAvgPercent", { min: 0, max: 100 })}
            ${renderRuntimeSparkline(samples, "dockerMemoryTotalMiB", { min: 0 })}
          `,
        })}
      </div>
    ` : `<div class="empty-state">${t("runtime.timeline.empty")}</div>`}
  `;
}

async function loadRuntimeHistory() {
  runtimeHistoryState.isLoading = true;
  runtimeHistoryState.error = "";
  renderRuntimeTimeline();
  try {
    const response = await fetch(`${RUNTIME_HISTORY_ENDPOINT}?limit=${RUNTIME_HISTORY_MAX_SAMPLES}`, { headers: { Accept: "application/json" } });
    if (!response.ok) {
      throw new Error(`HTTP ${response.status}`);
    }
    const payload = await response.json();
    runtimeHistoryState.windowSeconds = Math.max(0, Number(payload.windowSeconds || 900));
    runtimeHistoryState.sampleIntervalSeconds = Math.max(0, Number(payload.sampleIntervalSeconds || 5));
    runtimeHistoryState.samples = Array.isArray(payload.samples)
      ? payload.samples.map(normalizeRuntimeHistorySample).slice(-RUNTIME_HISTORY_MAX_SAMPLES)
      : [];
    runtimeHistoryState.lastUpdatedAt = runtimeHistoryState.samples[runtimeHistoryState.samples.length - 1]?.generatedAt || text(payload.generatedAt, "");
  } catch (error) {
    runtimeHistoryState.error = text(error.message, "Failed to load runtime history");
  } finally {
    runtimeHistoryState.isLoading = false;
    renderRuntimeTimeline();
  }
}

function dreamSubjectEndpoint(subjectId, suffix = "") {
  return `${DREAM_SUBJECT_ENDPOINT}${encodeURIComponent(text(subjectId, "main"))}${suffix}`;
}

function currentDreamSubject() {
  return dreamState.subjects.find((subject) => subject.id === dreamState.selectedSubjectId) || dreamState.subjects[0] || null;
}

function currentDreamFile() {
  const files = Array.isArray(dreamState.detail?.files) ? dreamState.detail.files : [];
  return files.find((file) => file.name === dreamState.selectedFileName) || files[0] || null;
}

function formatDreamTimestampMs(value) {
  const numeric = Number(value || 0);
  if (!Number.isFinite(numeric) || numeric <= 0) return "none";
  return new Date(numeric).toLocaleString();
}

function dreamRunStatusLabel(status) {
  if (status === "completed") return t("dream.status.completed");
  if (status === "nothing_to_process") return t("dream.status.nothing");
  if (status === "restored") return t("dream.status.restored");
  if (status === "failed") return t("dream.status.failed");
  return text(status, "");
}

function renderDreamActions() {
  const refreshButton = document.getElementById("dream-refresh-button");
  const runButton = document.getElementById("dream-run-button");
  if (refreshButton) {
    refreshButton.textContent = dreamState.isLoading ? t("dream.refreshing") : t("dream.refresh");
    refreshButton.disabled = dreamState.isLoading || dreamState.isRunning || dreamState.isRestoring;
  }
  if (runButton) {
    runButton.textContent = dreamState.isRunning ? t("dream.running") : t("dream.run");
    runButton.disabled = !currentDreamSubject() || dreamState.isLoading || dreamState.isRunning || dreamState.isRestoring;
  }
}

function renderDreamMetric(label, value, footnote = "") {
  return `
    <article class="dream-metric">
      <span>${html(label)}</span>
      <strong>${html(value)}</strong>
      ${footnote ? `<small>${html(footnote)}</small>` : ""}
    </article>
  `;
}

function contextActionLabel(action, busy, compactLabel, clearLabel) {
  if (busy && action === "clear") return t("button.clearing");
  if (busy && action === "compact") return t("button.compacting");
  return action === "compact" ? compactLabel : clearLabel;
}

function renderEmployeeContextPanel(context, options = {}) {
  const current = percent(context?.percent);
  const employeeId = text(options.employeeId || context?.employeeId, "");
  const sessionKey = text(options.sessionKey || context?.sessionKey, "");
  const available = Boolean(context?.available);
  const actionable = available && Boolean(employeeId);
  const busy = Boolean(context?.busy) || isEmployeeContextActionBusy(employeeId);
  const clearBusy = isEmployeeContextActionBusy(employeeId, "clear");
  const compactBusy = isEmployeeContextActionBusy(employeeId, "compact");
  const disabled = !actionable || busy;
  const clearLabel = options.shortLabels ? t("button.clear_short") : t("button.clear_context");
  const compactLabel = options.shortLabels ? t("button.compact_short") : t("button.compact_context");
  const actionAttr = options.actionAttr || "data-docker-context-action";
  const showActions = options.showActions !== false;
  const reason = !available
    ? html(context?.reason, t("docker.context_unavailable"))
    : `${current}% · ${html(context?.source, "unknown")}`;
  return `
    <div class="agent-context-panel ${available ? "" : "is-unavailable"}">
      <div class="agent-context-head">
        <div class="agent-section-title">${html(options.title || t("docker.context"))}</div>
        ${showActions ? `<div class="agent-context-actions">
          <button class="secondary-button compact-context-button" type="button"
            ${actionAttr}="clear"
            data-employee-context-id="${html(employeeId)}"
            data-employee-context-session="${html(sessionKey)}"
            ${disabled || clearBusy ? "disabled" : ""}>
            ${contextActionLabel("clear", clearBusy, compactLabel, clearLabel)}
          </button>
          <button class="primary-button compact-context-button" type="button"
            ${actionAttr}="compact"
            data-employee-context-id="${html(employeeId)}"
            data-employee-context-session="${html(sessionKey)}"
            ${disabled || compactBusy ? "disabled" : ""}>
            ${contextActionLabel("compact", compactBusy, compactLabel, clearLabel)}
          </button>
        </div>` : ""}
      </div>
      <div class="progress"><span style="width: ${current}%"></span></div>
      <div class="progress-label">
        <span>${html(context?.usedTokens, "0")} / ${html(context?.totalTokens, "0")}</span>
        <span>${reason}</span>
      </div>
    </div>
  `;
}

function renderDreamSubjectCard(subject) {
  const active = subject.id === dreamState.selectedSubjectId;
  const status = text(subject.dockerStatus || subject.status, "ready");
  const latestCommit = text(subject.latestCommit?.sha, "none");
  const context = subject.context || {};
  const contextLabel = context.available
    ? `${percent(context.percent)}% · ${text(context.usedTokens, "0")} / ${text(context.totalTokens, "0")}`
    : t("docker.context_unavailable");
  return `
    <button class="dream-subject-card ${active ? "is-active" : ""}" type="button" data-dream-subject="${html(subject.id)}">
      <span class="dream-subject-top">
        <strong>${html(subject.name, subject.id)}</strong>
        <span class="${badgeClass(status)}">${html(status)}</span>
      </span>
      <span class="dream-subject-meta">${html(subject.type)} · ${html(subject.agentType)}</span>
      <span class="dream-subject-stats">
        <span>${t("dream.history")}: ${html(subject.historyCount, "0")}</span>
        <span>${t("dream.unprocessed")}: ${html(subject.unprocessedCount, "0")}</span>
      </span>
      <span class="dream-subject-meta">${t("docker.context")}: ${html(contextLabel)}</span>
      <span class="dream-subject-meta">${t("dream.latest_commit")}: ${html(latestCommit)}</span>
    </button>
  `;
}

function renderDreamFileTabs(files) {
  const available = Array.isArray(files) && files.length ? files : DREAM_FILE_TABS.map((name) => ({ name }));
  return `
    <div class="dream-file-tabs" role="tablist" aria-label="${html(t("dream.files"))}">
      ${available.map((file) => {
    const active = file.name === dreamState.selectedFileName;
    return `
        <button class="dream-file-tab ${active ? "is-active" : ""}" type="button" data-dream-file="${html(file.name)}" role="tab" aria-selected="${active ? "true" : "false"}">
          ${html(file.name)}
        </button>
      `;
  }).join("")}
    </div>
  `;
}

function renderDreamFiles() {
  const files = Array.isArray(dreamState.detail?.files) ? dreamState.detail.files : [];
  const selected = currentDreamFile();
  return `
    <section class="dream-card dream-files-card">
      <div class="agent-section-title">${t("dream.files")}</div>
      ${renderDreamFileTabs(files)}
      <pre class="dream-file-preview">${html(selected?.content || t("dream.file_empty"), "")}</pre>
    </section>
  `;
}

function renderDreamCommits() {
  const commits = Array.isArray(dreamState.detail?.commits) ? dreamState.detail.commits : [];
  if (!commits.length) {
    return `<section class="dream-card"><div class="agent-section-title">${t("dream.commits")}</div><div class="empty-state">${t("dream.no_commits")}</div></section>`;
  }
  return `
    <section class="dream-card dream-commits-card">
      <div class="agent-section-title">${t("dream.commits")}</div>
      <div class="dream-commit-list">
        ${commits.map((commit) => {
    const active = commit.sha === dreamState.selectedCommitSha;
    return `
          <button class="dream-commit ${active ? "is-active" : ""}" type="button" data-dream-commit="${html(commit.sha)}">
            <strong>${html(commit.sha)}</strong>
            <span>${html(commit.timestamp)}</span>
            <small>${html(commit.message)}</small>
          </button>
        `;
  }).join("")}
      </div>
      <button class="danger-button dream-restore-button" type="button" data-dream-restore="true" ${dreamState.selectedCommitSha && !dreamState.isRestoring ? "" : "disabled"}>
        ${dreamState.isRestoring ? t("dream.restoring") : t("dream.restore")}
      </button>
    </section>
  `;
}

function renderDreamDiff() {
  const selected = dreamState.detail?.selectedCommit;
  const diff = text(selected?.diff, "");
  return `
    <section class="dream-card dream-diff-card">
      <div class="agent-section-title">${t("dream.diff")}</div>
      ${diff ? `<pre class="dream-diff-preview">${html(diff)}</pre>` : `<div class="empty-state">${t("dream.no_diff")}</div>`}
    </section>
  `;
}

function renderDreamDetail() {
  if (dreamState.isDetailLoading) {
    return `<section class="dream-card"><div class="empty-state">${t("dream.loading")}</div></section>`;
  }
  const subject = dreamState.detail?.subject || currentDreamSubject();
  if (!subject) {
    return `<section class="dream-card"><div class="empty-state">${t("dream.empty")}</div></section>`;
  }
  return `
    <section class="dream-card dream-subject-detail">
      <div class="panel-head">
        <div>
          <h3>${html(subject.name, subject.id)}</h3>
          <div class="panel-meta">${html(subject.workspace, "")}</div>
        </div>
        <span class="${badgeClass(subject.status)}">${html(subject.status, "ready")}</span>
      </div>
      <dl class="key-value dream-key-values">
        <div><dt>${t("dream.workspace")}</dt><dd>${html(subject.workspace, "")}</dd></div>
        <div><dt>${t("dream.history")}</dt><dd>${html(subject.historyCount, "0")}</dd></div>
        <div><dt>${t("dream.unprocessed")}</dt><dd>${html(subject.unprocessedCount, "0")}</dd></div>
        <div><dt>${t("dream.versioning")}</dt><dd>${subject.versioningInitialized ? "git" : "not initialized"}</dd></div>
      </dl>
      ${renderEmployeeContextPanel(subject.context || {}, {
        employeeId: subject.type === "employee" ? subject.id : "",
        sessionKey: subject.context?.sessionKey || "",
        actionAttr: "data-dream-context-action",
        showActions: subject.type === "employee",
      })}
      ${subject.lastRun ? `<div class="dream-action-status">${html(dreamRunStatusLabel(subject.lastRun.status))}</div>` : ""}
    </section>
    <div class="dream-detail-grid">
      <div class="dream-detail-main">
        ${renderDreamFiles()}
        ${renderDreamDiff()}
      </div>
      ${renderDreamCommits()}
    </div>
  `;
}

function renderDreamPanel() {
  renderDreamActions();
  const root = document.getElementById("dream-panel");
  if (!root) return;
  const subjects = Array.isArray(dreamState.subjects) ? dreamState.subjects : [];
  const totalHistory = subjects.reduce((sum, subject) => sum + Number(subject.historyCount || 0), 0);
  const totalUnprocessed = subjects.reduce((sum, subject) => sum + Number(subject.unprocessedCount || 0), 0);
  const cron = dreamState.cron || {};
  const runningCount = Array.isArray(dreamState.runningSubjectIds) ? dreamState.runningSubjectIds.length : 0;
  root.innerHTML = `
    <section class="dream-summary">
      ${renderDreamMetric(t("dream.schedule"), cron.schedule ? formatCronSchedule(cron.schedule) : "none", cron.enabled === false ? "disabled" : "")}
      ${renderDreamMetric(t("dream.next_run"), formatDreamTimestampMs(cron.state?.nextRunAtMs))}
      ${renderDreamMetric(t("dream.history"), String(totalHistory), `${t("dream.unprocessed")}: ${totalUnprocessed}`)}
      ${renderDreamMetric(t("dream.running_subjects"), String(runningCount))}
    </section>
    ${dreamState.error ? `<div class="dream-error">${html(t("dream.error", { value: dreamState.error }))}</div>` : ""}
    ${dreamState.actionStatus ? `<div class="dream-action-status">${html(dreamState.actionStatus)}</div>` : ""}
    <div class="dream-workbench">
      <section class="dream-subjects">
        <div class="agent-section-title">${t("dream.subjects")}</div>
        ${dreamState.isLoading ? `<div class="empty-state">${t("dream.loading")}</div>` : ""}
        ${!dreamState.isLoading && !subjects.length ? `<div class="empty-state">${t("dream.empty")}</div>` : ""}
        ${subjects.map(renderDreamSubjectCard).join("")}
      </section>
      <section class="dream-detail">
        ${renderDreamDetail()}
      </section>
    </div>
  `;
}

async function loadDream({ loadDetail = true } = {}) {
  dreamState.isLoading = true;
  dreamState.error = "";
  renderDreamPanel();
  try {
    const response = await fetch(DREAM_ENDPOINT, { headers: { Accept: "application/json" } });
    if (!response.ok) {
      const error = await response.json().catch(() => ({ error: { message: `HTTP ${response.status}` } }));
      throw new Error(text(error?.error?.message, `HTTP ${response.status}`));
    }
    const payload = await response.json();
    dreamState.subjects = Array.isArray(payload.subjects) ? payload.subjects : [];
    dreamState.cron = payload.cron || null;
    dreamState.runningSubjectIds = Array.isArray(payload.runningSubjectIds) ? payload.runningSubjectIds : [];
    if (!dreamState.subjects.some((subject) => subject.id === dreamState.selectedSubjectId)) {
      dreamState.selectedSubjectId = dreamState.subjects[0]?.id || "main";
    }
  } catch (error) {
    dreamState.error = text(error.message, "Failed to load Dream memory");
  } finally {
    dreamState.isLoading = false;
    renderDreamPanel();
  }
  if (loadDetail && currentDreamSubject()) {
    await loadDreamSubject(dreamState.selectedSubjectId);
  }
}

async function loadDreamSubject(subjectId, sha = "") {
  const normalizedId = text(subjectId, "main");
  dreamState.selectedSubjectId = normalizedId;
  dreamState.isDetailLoading = true;
  dreamState.error = "";
  renderDreamPanel();
  try {
    const query = sha ? `?sha=${encodeURIComponent(sha)}` : "";
    const response = await fetch(`${dreamSubjectEndpoint(normalizedId)}${query}`, { headers: { Accept: "application/json" } });
    if (!response.ok) {
      const error = await response.json().catch(() => ({ error: { message: `HTTP ${response.status}` } }));
      throw new Error(text(error?.error?.message, `HTTP ${response.status}`));
    }
    const payload = await response.json();
    dreamState.detail = payload;
    const files = Array.isArray(payload.files) ? payload.files : [];
    if (!files.some((file) => file.name === dreamState.selectedFileName)) {
      dreamState.selectedFileName = files.some((file) => file.name === "MEMORY.md") ? "MEMORY.md" : (files[0]?.name || "MEMORY.md");
    }
    dreamState.selectedCommitSha = payload.selectedCommit?.commit?.sha || payload.commits?.[0]?.sha || "";
  } catch (error) {
    dreamState.error = text(error.message, "Failed to load Dream subject");
  } finally {
    dreamState.isDetailLoading = false;
    renderDreamPanel();
  }
}

function selectDreamFile(fileName) {
  dreamState.selectedFileName = text(fileName, "MEMORY.md");
  renderDreamPanel();
}

function selectDreamCommit(sha) {
  const normalizedSha = text(sha, "");
  if (!normalizedSha) return;
  loadDreamSubject(dreamState.selectedSubjectId, normalizedSha).catch((error) => {
    dreamState.error = text(error.message, "Failed to load Dream diff");
    renderDreamPanel();
  });
}

async function runSelectedDream() {
  const subject = currentDreamSubject();
  if (!subject || dreamState.isRunning) return;
  dreamState.isRunning = true;
  dreamState.actionStatus = "";
  renderDreamPanel();
  try {
    const response = await fetch(dreamSubjectEndpoint(subject.id, "/run"), {
      method: "POST",
      headers: { Accept: "application/json" },
    });
    const payload = await response.json().catch(() => ({}));
    if (!response.ok) {
      throw new Error(text(payload?.error?.message, `HTTP ${response.status}`));
    }
    dreamState.actionStatus = dreamRunStatusLabel(payload.status);
    await loadDream();
  } finally {
    dreamState.isRunning = false;
    renderDreamPanel();
  }
}

function requestDreamRestore() {
  const subject = currentDreamSubject();
  const sha = dreamState.selectedCommitSha;
  if (!subject || !sha) return;
  openConfirmAction({
    kind: "dream-restore",
    subjectId: subject.id,
    sha,
    title: t("dream.confirm.title"),
    subtitle: t("dream.confirm.subtitle"),
    message: t("dream.confirm.message", { subject: subject.name || subject.id, sha }),
    confirmLabel: t("dream.restore"),
  });
}

async function restoreDreamCommit(subjectId, sha) {
  const normalizedSubjectId = text(subjectId, "main");
  const normalizedSha = text(sha, "");
  if (!normalizedSha) return;
  dreamState.isRestoring = true;
  setBusyAction({ key: "dream-restore", label: t("dream.restoring") });
  try {
    const response = await fetch(dreamSubjectEndpoint(normalizedSubjectId, "/restore"), {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
        Accept: "application/json",
      },
      body: JSON.stringify({ sha: normalizedSha }),
    });
    const payload = await response.json().catch(() => ({}));
    if (!response.ok) {
      throw new Error(text(payload?.error?.message, `HTTP ${response.status}`));
    }
    adminState.confirmAction = null;
    dreamState.actionStatus = dreamRunStatusLabel(payload.status);
    await loadDream();
  } finally {
    dreamState.isRestoring = false;
    clearBusyAction();
    renderDreamPanel();
  }
}

function renderResourceHubTabs() {
  const activeTab = currentResourceHubTab();
  document.querySelectorAll("[data-resource-tab]").forEach((node) => {
    const tab = node.getAttribute("data-resource-tab");
    const isActive = tab === activeTab;
    node.classList.toggle("is-active", isActive);
    node.setAttribute("aria-selected", isActive ? "true" : "false");
    node.setAttribute("tabindex", isActive ? "0" : "-1");
  });
  document.querySelectorAll("[data-resource-panel]").forEach((node) => {
    const panel = node.getAttribute("data-resource-panel");
    node.hidden = panel !== activeTab;
  });
}

function setResourceHubTab(tab) {
  uiState.resourceHubTab = normalizeResourceHubTab(tab);
  renderResourceHubTabs();
}

function renderStaticTranslations() {
  document.querySelectorAll("[data-i18n]").forEach((node) => {
    node.textContent = staticTextForKey(node.getAttribute("data-i18n"));
  });
  document.querySelectorAll("[data-i18n-placeholder]").forEach((node) => {
    node.setAttribute("placeholder", t(node.getAttribute("data-i18n-placeholder")));
  });
  document.querySelectorAll("[data-i18n-aria-label]").forEach((node) => {
    node.setAttribute("aria-label", t(node.getAttribute("data-i18n-aria-label")));
  });
  document.querySelectorAll("[data-i18n-title]").forEach((node) => {
    node.setAttribute("title", t(node.getAttribute("data-i18n-title")));
  });
  renderGeneratedAt();
  renderPreferenceControls();
  renderNavSectionLinks();
  renderHeroBar();
  renderAlertStrip();
  renderActionCenter();
  renderResourceHubTabs();
  renderDreamPanel();
}

function rerenderAdminContent() {
  renderStaticTranslations();
  renderCaseCarousel();
  renderEmployees();
  renderOrganization();
  renderEmployeeModal();
  renderSkillCatalog();
  if (adminState.generatedAt) {
    renderProcess(adminState.process || {});
    renderMainAgent(adminState.mainAgent || {});
    renderDockerAgents(adminState.dockerAgents || []);
  }
  renderHeroBar();
  renderAlertStrip();
  renderActionCenter();
  renderResourceHubTabs();
  renderDreamPanel();
  renderNavSectionLinks();
  requestNavSectionSync();
}

function applyLanguage(language) {
  const next = normalizeLanguage(language);
  if (next === currentLanguage()) {
    renderStaticTranslations();
    window.OpenHireCompanion?.refreshLanguage?.();
    return;
  }
  uiState.language = next;
  writeLanguagePreference(next);
  syncDocumentPreferences();
  rerenderAdminContent();
  window.OpenHireCompanion?.refreshLanguage?.();
}

function applyTheme(theme, options = {}) {
  const persist = options.persist !== false;
  const next = normalizeTheme(theme);
  if (next === currentTheme()) {
    renderStaticTranslations();
    window.OpenHireCompanion?.syncTheme?.(next);
    return;
  }
  uiState.theme = next;
  if (persist) {
    writeThemePreference(next);
  }
  syncDocumentPreferences();
  rerenderAdminContent();
  window.OpenHireCompanion?.syncTheme?.(next);
}

function initializeAdminPreferences() {
  initializeSystemThemePreference();
  syncDocumentPreferences();
  renderStaticTranslations();
}

function html(value, fallback = "unknown") {
  return text(value, fallback)
    .replaceAll("&", "&amp;")
    .replaceAll("<", "&lt;")
    .replaceAll(">", "&gt;")
    .replaceAll('"', "&quot;")
    .replaceAll("'", "&#39;");
}

function createAvatarSvgDataUri(preset) {
  const accessory = renderAvatarAccessory(preset.accessory, preset);
  const svg = `
    <svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 96 96" role="img" aria-label="${preset.label}">
      <defs>
        <clipPath id="clip">
          <circle cx="48" cy="48" r="46" />
        </clipPath>
      </defs>
      <g clip-path="url(#clip)">
        <rect width="96" height="96" rx="48" fill="${preset.background}" />
        <circle cx="48" cy="40" r="18" fill="${preset.skin}" />
        <path d="M28 35c2-13 11-20 20-20s18 6 20 18c-7-4-15-6-24-6-5 0-11 3-16 8Z" fill="${preset.hair}" />
        <path d="M20 97c1-18 12-30 28-30s27 12 28 30" fill="${preset.body}" />
        <circle cx="41" cy="40" r="2.4" fill="#2b211d" />
        <circle cx="55" cy="40" r="2.4" fill="#2b211d" />
        <path d="M42 48c3 2 9 2 12 0" fill="none" stroke="#8c4f40" stroke-width="2.5" stroke-linecap="round" />
        <path d="M31 70c7 6 27 6 34 0" fill="${preset.accent}" opacity="0.9" />
        ${accessory}
      </g>
    </svg>
  `;
  return `data:image/svg+xml;charset=UTF-8,${encodeURIComponent(svg.trim())}`;
}

function renderAvatarAccessory(accessory, preset) {
  if (accessory === "glasses") {
    return `
      <g fill="none" stroke="#1f2a36" stroke-width="2.4" stroke-linecap="round" stroke-linejoin="round">
        <rect x="31" y="34" width="12" height="9" rx="4.5" />
        <rect x="53" y="34" width="12" height="9" rx="4.5" />
        <path d="M43 39h10" />
      </g>
    `;
  }
  if (accessory === "visor") {
    return `
      <g>
        <path d="M26 32c4-8 13-12 22-12 11 0 19 5 23 14" fill="${preset.hair}" />
        <path d="M30 35c4-5 10-8 18-8s15 3 19 8c-4 3-11 5-19 5s-15-2-18-5Z" fill="${preset.accent}" opacity="0.92" />
      </g>
    `;
  }
  if (accessory === "cap") {
    return `
      <g>
        <path d="M26 33c5-7 12-11 22-11 9 0 16 4 22 11-4 1-11 2-22 2s-18-1-22-2Z" fill="${preset.accent}" />
        <path d="M40 34h28c-2 6-9 10-18 10-5 0-9-1-12-3" fill="${preset.hair}" opacity="0.28" />
      </g>
    `;
  }
  if (accessory === "headset") {
    return `
      <g fill="none" stroke="#4a3f76" stroke-width="3" stroke-linecap="round" stroke-linejoin="round">
        <path d="M30 40c0-11 8-20 18-20s18 9 18 20" />
        <path d="M29 41v11" />
        <path d="M67 41v11" />
        <path d="M66 53c-1 4-4 6-8 6" />
      </g>
    `;
  }
  if (accessory === "spark") {
    return `
      <g>
        <path d="M72 21l2 5 5 2-5 2-2 5-2-5-5-2 5-2 2-5Z" fill="${preset.accent}" />
      </g>
    `;
  }
  if (accessory === "pin") {
    return `
      <g>
        <circle cx="62" cy="67" r="5" fill="${preset.accent}" />
        <path d="M62 63v8M58 67h8" stroke="#ffffff" stroke-width="2" stroke-linecap="round" />
      </g>
    `;
  }
  return "";
}

function getAvatarPreset(avatarId) {
  return EMPLOYEE_AVATAR_INDEX[text(avatarId, "")] || null;
}

function renderEmployeeAvatar(employee, extraClass = "") {
  const preset = getAvatarPreset(employee?.avatar);
  const classes = ["employee-avatar"];
  if (extraClass) classes.push(extraClass);
  if (preset) {
    return `
      <span class="${classes.join(" ")} is-image">
        <img src="${preset.src}" alt="${html(preset.label)}" />
      </span>
    `;
  }
  return `
    <span class="${classes.join(" ")}">
      ${html(text(employee?.name, "?").slice(0, 2).toUpperCase())}
    </span>
  `;
}

function slugify(value, fallback = "employee") {
  const slug = text(value, fallback)
    .toLowerCase()
    .replace(/[^a-z0-9]+/g, "-")
    .replace(/^-+|-+$/g, "");
  return slug || fallback;
}

function createEmployeeFromTemplate(template, overrides = {}) {
  const dockerPrefix = slugify(overrides.dockerPrefix || overrides.team || template.id, "employee");
  const team = overrides.team || "Digital Workforce";
  const name = overrides.name || template.defaultName;
  return {
    id: overrides.id || `employee-${template.id}-${Date.now()}`,
    name,
    avatar: text(overrides.avatar, ""),
    role: template.role,
    companyStyle: template.companyStyle,
    summary: template.summary,
    docker: {
      ...template.docker,
      name: `${dockerPrefix}-${template.docker.name}`,
    },
    status: overrides.status || "not_created",
    settings: {
      ...template.settings,
      team,
    },
    skills: [...template.skills],
    tools: [...template.tools],
    exampleTasks: [...template.exampleTasks],
  };
}

function normalizeEmployeeTemplate(template) {
  return {
    id: text(template.id, ""),
    defaultName: text(template.defaultName || template.default_name, ""),
    role: text(template.role, "Custom Role"),
    defaultAgentType: text(template.defaultAgentType || template.default_agent_type, "openclaw"),
    companyStyle: text(template.companyStyle || template.company_style, "Custom role template"),
    summary: text(template.summary, ""),
    isCustomSaved: true,
    isDeletable: true,
    docker: {
      image: "custom",
      name: `custom-${slugify(template.id || template.role || "template", "template")}`,
      ports: "n/a",
      resources: "n/a",
    },
    settings: {
      model: "gpt-5.4",
      mode: "Saved custom role",
      workspace: "/workspace",
      guardrails: "Prompt restored from saved template.",
    },
    skills: [],
    tools: ["cook"],
    exampleTasks: [],
  };
}

function employeeTemplates() {
  return [...EMPLOYEE_TEMPLATES, ...employeeState.customTemplates, CUSTOM_ROLE_TEMPLATE]
    .filter((template) => !employeeState.hiddenTemplateIds.includes(template.id))
    .map((template) => localizeTemplate(template));
}

function selectedEmployeeTemplate() {
  return employeeTemplates().find((item) => item.id === employeeState.selectedTemplateId) || EMPLOYEE_TEMPLATES[0];
}

function createEmployeeDraft(template = selectedEmployeeTemplate()) {
  const isCustomComposer = Boolean(template?.isCustomComposer);
  return {
    name: isCustomComposer ? "" : text(template?.defaultName, ""),
    role: isCustomComposer ? "" : text(template?.role, ""),
    agent_type: text(template?.defaultAgentType, "openclaw"),
    system_prompt: isCustomComposer ? "" : text(template?.summary, ""),
  };
}

function ensureCreateEmployeeDraft() {
  if (!employeeState.createDraft) {
    employeeState.createDraft = createEmployeeDraft();
  }
  return employeeState.createDraft;
}

function invalidateCreateWizardStepsFrom(step) {
  const startIndex = createWizardStepIndex(step);
  if (startIndex < 0) return;
  const invalidated = new Set(CREATE_WIZARD_STEPS.slice(startIndex));
  employeeState.completedCreateWizardSteps = employeeState.completedCreateWizardSteps.filter((item) => !invalidated.has(item));
}

function updateCreateEmployeeDraft(fieldName, value) {
  if (!["name", "role", "agent_type", "system_prompt"].includes(fieldName)) return;
  const draft = ensureCreateEmployeeDraft();
  employeeState.createDraft = {
    ...draft,
    [fieldName]: String(value ?? ""),
  };
  invalidateCreateWizardStepsFrom("profile");
  employeeState.lastSkillRecommendationProfileSignature = "";
}

function resetCreateWizardState() {
  employeeState.createWizardStep = "template";
  employeeState.createWizardError = "";
  employeeState.completedCreateWizardSteps = ["template"];
  employeeState.lastSkillRecommendationProfileSignature = "";
}

function createWizardStepIndex(step) {
  return CREATE_WIZARD_STEPS.indexOf(step);
}

function createWizardProfileSignature() {
  const draft = ensureCreateEmployeeDraft();
  return JSON.stringify({
    name: text(draft.name, "").trim(),
    role: text(draft.role, "").trim(),
    agent_type: text(draft.agent_type, "").trim(),
    system_prompt: text(draft.system_prompt, "").trim(),
  });
}

function markCreateWizardStepComplete(step) {
  if (!CREATE_WIZARD_STEPS.includes(step)) return;
  if (!employeeState.completedCreateWizardSteps.includes(step)) {
    employeeState.completedCreateWizardSteps = [...employeeState.completedCreateWizardSteps, step];
  }
}

function validateCreateWizardStep(step) {
  employeeState.createWizardError = "";
  if (step === "profile") {
    const draft = ensureCreateEmployeeDraft();
    if (!text(draft.name, "").trim() || !text(draft.role, "").trim() || !text(draft.system_prompt, "").trim()) {
      employeeState.createWizardError = t("modal.create.validation.profile_required");
      return false;
    }
  }
  markCreateWizardStepComplete(step);
  return true;
}

function canEnterCreateWizardStep(step) {
  const targetIndex = createWizardStepIndex(step);
  if (targetIndex < 0) return false;
  return CREATE_WIZARD_STEPS.slice(0, targetIndex).every((requiredStep) => (
    employeeState.completedCreateWizardSteps.includes(requiredStep)
  ));
}

function maybeRecommendSkillsForWizardStep() {
  if (employeeState.createWizardStep !== "skills") return;
  if (!employeeState.smartSkillRecommendEnabled || !employeeState.isCreateOpen) return;
  const signature = createWizardProfileSignature();
  if (!signature || signature === employeeState.lastSkillRecommendationProfileSignature) return;
  employeeState.lastSkillRecommendationProfileSignature = signature;
  recommendEmployeeSkills().catch((error) => {
    employeeState.lastSkillRecommendationProfileSignature = "";
    employeeState.skillRecommendation = defaultSkillRecommendation({
      warning: text(error.message, "Failed to recommend skills."),
    });
    renderEmployeeModal();
  });
}

function setCreateWizardStep(step) {
  if (!CREATE_WIZARD_STEPS.includes(step)) return;
  if (!canEnterCreateWizardStep(step)) {
    employeeState.createWizardError = t("modal.create.validation.blocked_step");
    renderEmployeeModal();
    return;
  }
  employeeState.createWizardStep = step;
  employeeState.createWizardError = "";
  maybeRecommendSkillsForWizardStep();
  renderEmployeeModal();
}

function advanceCreateWizardStep() {
  const currentStep = employeeState.createWizardStep || "template";
  if (!validateCreateWizardStep(currentStep)) {
    renderEmployeeModal();
    return;
  }
  const nextStep = CREATE_WIZARD_STEPS[createWizardStepIndex(currentStep) + 1];
  if (nextStep) {
    setCreateWizardStep(nextStep);
  }
}

function retreatCreateWizardStep() {
  const currentIndex = createWizardStepIndex(employeeState.createWizardStep || "template");
  const previousStep = CREATE_WIZARD_STEPS[Math.max(0, currentIndex - 1)];
  setCreateWizardStep(previousStep || "template");
}

function captureEmployeeModalViewState(root) {
  if (!root || !employeeState.isCreateOpen || adminState.confirmAction) {
    return null;
  }
  const modal = root.querySelector(".employee-modal");
  if (!(modal instanceof HTMLElement)) {
    return null;
  }
  const activeElement = document.activeElement instanceof Element
    ? document.activeElement.closest("[data-template-id], [data-avatar-id], [data-local-skill-id], [data-skill-expand-id], [data-modal-close], [name]")
    : null;
  const focus = activeElement instanceof Element
    ? {
      attr: ["data-template-id", "data-avatar-id", "data-local-skill-id", "data-skill-expand-id", "name"].find((attr) => activeElement.hasAttribute(attr)) || "",
      value: text(
        activeElement.getAttribute("data-template-id")
          || activeElement.getAttribute("data-avatar-id")
          || activeElement.getAttribute("data-local-skill-id")
          || activeElement.getAttribute("data-skill-expand-id")
          || activeElement.getAttribute("name"),
        "",
      ),
    }
    : null;
  return {
    scrollTop: modal.scrollTop,
    focus,
  };
}

function restoreEmployeeModalViewState(root, viewState) {
  if (!root || !viewState || !employeeState.isCreateOpen || adminState.confirmAction) {
    return;
  }
  const modal = root.querySelector(".employee-modal");
  if (!(modal instanceof HTMLElement)) {
    return;
  }
  window.requestAnimationFrame(() => {
    modal.scrollTop = viewState.scrollTop;
    const focus = viewState.focus;
    if (!focus?.attr || !focus.value) {
      return;
    }
    const selector = `[${focus.attr}="${CSS.escape(focus.value)}"]`;
    const target = root.querySelector(selector);
    if (!(target instanceof HTMLElement)) {
      return;
    }
    try {
      target.focus({ preventScroll: true });
    } catch {
      target.focus();
      modal.scrollTop = viewState.scrollTop;
    }
  });
}

function parseTagInput(value) {
  return text(value, "")
    .split(/[\n,]/)
    .map((item) => item.trim())
    .filter(Boolean);
}

function normalizePersistedEmployee(employee) {
  return {
    id: text(employee.id, ""),
    name: text(employee.name, "employee"),
    avatar: text(employee.avatar, ""),
    role: text(employee.role, "unknown role"),
    skills: Array.isArray(employee.skills) ? employee.skills : [],
    skill_ids: Array.isArray(employee.skill_ids) ? employee.skill_ids : [],
    system_prompt: text(employee.system_prompt, ""),
    agent_type: text(employee.agent_type, "openclaw"),
    agent_config: employee.agent_config && typeof employee.agent_config === "object" ? employee.agent_config : {},
    tools: Array.isArray(employee.tools) ? employee.tools.map((item) => text(item, "")).filter(Boolean) : [],
    container_name: text(employee.container_name, ""),
    status: text(employee.status, "active"),
    created_at: text(employee.created_at, ""),
    updated_at: text(employee.updated_at, ""),
    demo: employee.demo === true,
    readOnly: employee.readOnly === true || employee.read_only === true,
    persisted: employee.persisted !== false,
  };
}

function normalizeLocalSkill(skill) {
  return {
    id: text(skill.id, ""),
    source: text(skill.source, "clawhub"),
    external_id: text(skill.external_id, ""),
    name: text(skill.name, "unknown skill"),
    description: text(skill.description, ""),
    version: text(skill.version, ""),
    author: text(skill.author, ""),
    license: text(skill.license, ""),
    source_url: text(skill.source_url, ""),
    safety_status: text(skill.safety_status, ""),
    tags: Array.isArray(skill.tags) ? skill.tags.map((item) => text(item, "")).filter(Boolean) : [],
    imported_at: text(skill.imported_at, ""),
    demo: skill.demo === true,
    readOnly: skill.readOnly === true || skill.read_only === true,
  };
}

function normalizeAgentSkill(skill) {
  return {
    name: text(skill?.name, ""),
    description: text(skill?.description, ""),
    source: text(skill?.source, ""),
    category: text(skill?.category, ""),
    path: text(skill?.path, ""),
    available: skill?.available !== false,
    missing_requirements: text(skill?.missing_requirements, ""),
    updated_at: text(skill?.updated_at, ""),
    editable: skill?.editable === true,
    deletable: skill?.deletable === true,
    bound_employee_count: Number.isFinite(Number(skill?.bound_employee_count)) ? Number(skill.bound_employee_count) : 0,
    demo: skill?.demo === true,
    readOnly: skill?.readOnly === true || skill?.read_only === true,
  };
}

function normalizeAgentSkillDetail(payload) {
  const skill = normalizeAgentSkill(payload?.skill || {});
  return {
    skill,
    markdown: text(payload?.markdown, ""),
    files: Array.isArray(payload?.files) ? payload.files.map((item) => ({
      path: text(item?.path, ""),
      type: text(item?.type, "file"),
      size: Number.isFinite(Number(item?.size)) ? Number(item.size) : 0,
    })).filter((item) => item.path) : [],
    metadata: payload?.metadata && typeof payload.metadata === "object" ? payload.metadata : {},
  };
}

function normalizeAgentSkillProposal(proposal) {
  return {
    id: text(proposal?.id, ""),
    action: text(proposal?.action, "create"),
    name: text(proposal?.name, ""),
    reason: text(proposal?.reason, ""),
    content: text(proposal?.content, ""),
    old_string: text(proposal?.old_string, ""),
    new_string: text(proposal?.new_string, ""),
    source: text(proposal?.source, "manual"),
    trigger_reasons: Array.isArray(proposal?.trigger_reasons) ? proposal.trigger_reasons.map((item) => text(item, "")).filter(Boolean) : [],
    evidence: Array.isArray(proposal?.evidence) ? proposal.evidence.map((item) => text(item, "")).filter(Boolean) : [],
    merged_count: Number.isFinite(Number(proposal?.merged_count)) ? Number(proposal.merged_count) : 0,
    status: text(proposal?.status, "pending"),
    created_at: text(proposal?.created_at, ""),
    updated_at: text(proposal?.updated_at, ""),
    applied_at: text(proposal?.applied_at, ""),
    result: proposal?.result && typeof proposal.result === "object" ? proposal.result : null,
  };
}

function normalizeSoulBannerSkillCandidate(skill) {
  return {
    source: text(skill.source, "soulbanner"),
    external_id: text(skill.external_id, ""),
    name: text(skill.name, "unknown skill"),
    description: text(skill.description, ""),
    version: text(skill.version, ""),
    updated_at: text(skill.updated_at, ""),
    author: text(skill.author, ""),
    license: text(skill.license, ""),
    source_url: text(skill.source_url, ""),
    safety_status: text(skill.safety_status, ""),
    tags: Array.isArray(skill.tags) ? skill.tags.map((item) => text(item, "")).filter(Boolean) : [],
    markdown: text(skill.markdown, ""),
  };
}

function normalizeMbtiSbtiSkillCandidate(skill) {
  return {
    source: text(skill.source, "mbti-sbti"),
    external_id: text(skill.external_id, ""),
    name: text(skill.name, "unknown skill"),
    description: text(skill.description, ""),
    version: text(skill.version, ""),
    updated_at: text(skill.updated_at, ""),
    author: text(skill.author, ""),
    license: text(skill.license, ""),
    source_url: text(skill.source_url, ""),
    safety_status: text(skill.safety_status, ""),
    tags: Array.isArray(skill.tags) ? skill.tags.map((item) => text(item, "")).filter(Boolean) : [],
    markdown: text(skill.markdown, ""),
  };
}

function normalizeSkillIds(skillIds) {
  if (!Array.isArray(skillIds)) return [];
  const normalized = [];
  for (const skillId of skillIds) {
    const value = text(skillId, "");
    if (value && !normalized.includes(value)) {
      normalized.push(value);
    }
  }
  return normalized;
}

function mergeInstalledRecommendationSkills(skills) {
  if (!Array.isArray(skills) || skills.length === 0) return;
  const byId = new Map(skillState.localSkills.map((skill) => [skill.id, skill]));
  for (const rawSkill of skills) {
    const skill = normalizeLocalSkill(rawSkill);
    if (!skill.id) continue;
    byId.set(skill.id, { ...(byId.get(skill.id) || {}), ...skill });
  }
  skillState.localSkills = Array.from(byId.values());
}

function isRequiredEmployeeSkillId(skillId) {
  return text(skillId, "") === REQUIRED_EMPLOYEE_SKILL_ID;
}

function isRequiredLocalSkill(skill) {
  return isRequiredEmployeeSkillId(skill?.id);
}

function hasRequiredEmployeeSkill() {
  return skillState.localSkills.some((skill) => isRequiredLocalSkill(skill));
}

function ensureRequiredEmployeeSkillSelected() {
  if (!hasRequiredEmployeeSkill()) return;
  employeeState.selectedSkillIds = [
    REQUIRED_EMPLOYEE_SKILL_ID,
    ...employeeState.selectedSkillIds.filter((skillId) => !isRequiredEmployeeSkillId(skillId)),
  ];
}

function selectedEmployeeSkillIdsForPayload() {
  ensureRequiredEmployeeSkillSelected();
  const availableSkillIds = new Set(skillState.localSkills.map((skill) => skill.id));
  return employeeState.selectedSkillIds.filter((skillId) => availableSkillIds.has(skillId));
}

function employeeCreateSkillSummary(selectedSkillIds) {
  const installedCloudSkillIds = normalizeSkillIds(employeeState.skillRecommendation.installedSkillIds);
  const cloudSkillIds = new Set(installedCloudSkillIds);
  const selected = normalizeSkillIds(selectedSkillIds);
  const cloudCount = installedCloudSkillIds.length;
  const localCount = selected.filter((skillId) => (
    skillId !== REQUIRED_EMPLOYEE_SKILL_ID && !cloudSkillIds.has(skillId)
  )).length;
  if (currentLanguage() === "zh") {
    return `员工创建完成。从 cloud 下载了 ${cloudCount} 个 skill，从 local import 了 ${localCount} 个 skill。`;
  }
  return `Employee created. Imported ${cloudCount} cloud skill(s) and ${localCount} local skill(s).`;
}

function employeeSkillSourceSummary(selectedSkillIds) {
  const installedCloudSkillIds = normalizeSkillIds(employeeState.skillRecommendation.installedSkillIds);
  const cloudSkillIds = new Set(installedCloudSkillIds);
  const selected = normalizeSkillIds(selectedSkillIds);
  const cloudCount = installedCloudSkillIds.length;
  const localCount = selected.filter((skillId) => (
    skillId !== REQUIRED_EMPLOYEE_SKILL_ID && !cloudSkillIds.has(skillId)
  )).length;
  return t("modal.create.review_skill_source", { cloudCount, localCount });
}

function selectRecommendedSkillIds(skillIds) {
  const availableSkillIds = new Set(skillState.localSkills.map((skill) => skill.id));
  const previousRecommendedIds = new Set(employeeState.recommendedSkillIds);
  const recommended = [];
  for (const skillId of skillIds || []) {
    const normalizedId = text(skillId, "");
    if (!normalizedId || normalizedId === REQUIRED_EMPLOYEE_SKILL_ID || !availableSkillIds.has(normalizedId)) {
      continue;
    }
    if (!recommended.includes(normalizedId)) {
      recommended.push(normalizedId);
    }
  }
  employeeState.recommendedSkillIds = recommended;
  employeeState.selectedSkillIds = employeeState.selectedSkillIds.filter((skillId) => !previousRecommendedIds.has(skillId));
  employeeState.selectedSkillIds = [
    ...employeeState.selectedSkillIds,
    ...recommended.filter((skillId) => !employeeState.selectedSkillIds.includes(skillId)),
  ];
  ensureRequiredEmployeeSkillSelected();
}

function resetSkillContentModal() {
  skillState.contentModal = {
    isOpen: false,
    skillId: "",
    skill: null,
    markdown: "",
    draft: "",
    isEditing: false,
    isLoading: false,
    error: "",
    contentSource: "",
    canSyncEmployees: false,
    isDirty: false,
    syncedEmployees: 0,
    isSearchPreview: false,
    isReadOnlyPreview: false,
    markdownStatus: "",
    markdownError: "",
  };
}

function setSkillContentModalPayload(payload) {
  const markdown = text(payload?.markdown, "");
  skillState.contentModal = {
    ...skillState.contentModal,
    skill: payload?.skill || skillState.contentModal.skill,
    markdown,
    draft: markdown,
    isEditing: false,
    isLoading: false,
    error: "",
    contentSource: text(payload?.content_source, ""),
    canSyncEmployees: Boolean(payload?.can_sync_employees),
    isDirty: false,
    syncedEmployees: Number(payload?.synced_employees || 0),
    isReadOnlyPreview: Boolean(payload?.is_read_only_preview),
    markdownStatus: text(payload?.markdown_status, ""),
    markdownError: text(payload?.markdown_error, ""),
  };
}

function skillIdentity(skill) {
  return `${text(skill.source, "clawhub")}::${text(skill.external_id, "")}::${text(skill.source_url, "")}`;
}

function formatUptime(seconds) {
  const total = Math.max(0, Number(seconds || 0));
  const hours = Math.floor(total / 3600);
  const minutes = Math.floor((total % 3600) / 60);
  const secs = total % 60;
  if (hours > 0) return `${hours}h ${minutes}m`;
  if (minutes > 0) return `${minutes}m ${secs}s`;
  return `${secs}s`;
}

function renderMetricCard(label, value, footnote = "") {
  return `
    <article class="metric-card hud-tile">
      <span class="hud-tile-corner hud-tile-corner-tl" aria-hidden="true"></span>
      <span class="hud-tile-corner hud-tile-corner-tr" aria-hidden="true"></span>
      <span class="hud-tile-corner hud-tile-corner-bl" aria-hidden="true"></span>
      <span class="hud-tile-corner hud-tile-corner-br" aria-hidden="true"></span>
      <div class="metric-label">${label}</div>
      <div class="metric-value">${value}</div>
      <div class="metric-footnote">${footnote}</div>
    </article>
  `;
}

function renderTags(items, className = "tag") {
  if (!Array.isArray(items) || items.length === 0) return `<span class="${className}">none</span>`;
  return items.map((item) => `<span class="${className}">${html(item)}</span>`).join("");
}

function isBusy(actionKey) {
  return adminState.busyAction?.key === actionKey;
}

function setBusyAction(action) {
  adminState.busyAction = action;
  renderEmployees();
  renderEmployeeModal();
  renderSkillCatalog();
  renderDreamPanel();
}

function updateBusyActionProgress(update) {
  if (!adminState.busyAction) return;
  adminState.busyAction = {
    ...adminState.busyAction,
    ...update,
  };
  updateBusyOverlay();
}

function updateBusyOverlay() {
  const busyAction = adminState.busyAction;
  if (!busyAction) return;
  const safeKey = String(busyAction.key || "");
  const overlays = document.querySelectorAll(".busy-overlay");
  overlays.forEach((overlay) => {
    if (String(overlay.dataset.busyKey || "") !== safeKey) return;
    const label = overlay.querySelector("[data-busy-label]");
    const percentLabel = overlay.querySelector("[data-busy-percent]");
    const progressBar = overlay.querySelector("[data-busy-progress]");
    const progressFill = overlay.querySelector("[data-busy-progress-fill]");
    const current = percent(busyAction.progress);
    if (label) {
      label.textContent = busyAction.label || "Working...";
    }
    if (percentLabel) {
      percentLabel.textContent = `${Math.round(current)}%`;
    }
    if (progressBar) {
      progressBar.setAttribute("aria-valuenow", String(Math.round(current)));
      progressBar.setAttribute("aria-label", busyAction.label || "Working");
    }
    if (progressFill) {
      progressFill.style.width = `${current}%`;
    }
  });
}

function clearBusyAction() {
  adminState.busyAction = null;
  renderEmployees();
  renderEmployeeModal();
  renderSkillCatalog();
  renderDreamPanel();
}

function setMainContextAction(action) {
  adminState.mainContextAction = action;
  renderMainAgent(adminState.mainAgent || {});
  renderActionCenter();
}

function clearMainContextAction() {
  adminState.mainContextAction = null;
  renderMainAgent(adminState.mainAgent || {});
  renderActionCenter();
}

function employeeContextActionKey(employeeId, action) {
  return `${text(employeeId, "")}:${text(action, "")}`;
}

function isEmployeeContextActionBusy(employeeId, action = "") {
  const current = adminState.employeeContextAction;
  if (!current) return false;
  if (action) return current.key === employeeContextActionKey(employeeId, action);
  return text(current.employeeId, "") === text(employeeId, "");
}

function setEmployeeContextAction(employeeId, action, surface = "") {
  adminState.employeeContextAction = {
    employeeId: text(employeeId, ""),
    action: text(action, ""),
    key: employeeContextActionKey(employeeId, action),
    surface: text(surface, ""),
  };
  renderDockerAgents(adminState.dockerAgents || []);
  renderDreamPanel();
  renderEmployees();
}

function clearEmployeeContextAction() {
  adminState.employeeContextAction = null;
  renderDockerAgents(adminState.dockerAgents || []);
  renderDreamPanel();
  renderEmployees();
}

function defaultTranscriptState() {
  return {
    isOpen: false,
    title: "",
    subtitle: "",
    endpoint: "",
    isLoading: false,
    error: "",
    payload: null,
  };
}

function renderChatHistoryIcon() {
  return `
    <svg class="chat-history-icon" viewBox="0 0 24 24" aria-hidden="true" focusable="false">
      <path d="M6.5 5h11A2.5 2.5 0 0 1 20 7.5v6A2.5 2.5 0 0 1 17.5 16H12l-4.5 3v-3h-1A2.5 2.5 0 0 1 4 13.5v-6A2.5 2.5 0 0 1 6.5 5Z" />
      <path d="M8 8h8M8 11h5" />
    </svg>
  `;
}

function openTranscriptModal({ title, subtitle, endpoint }) {
  adminState.transcript = {
    isOpen: true,
    title,
    subtitle,
    endpoint,
    isLoading: true,
    error: "",
    payload: null,
  };
  renderEmployeeModal();
  loadTranscript(endpoint).catch((error) => {
    adminState.transcript = {
      ...adminState.transcript,
      isLoading: false,
      error: text(error.message, "Failed to load chat history"),
    };
    renderEmployeeModal();
  });
}

function closeTranscriptModal() {
  adminState.transcript = defaultTranscriptState();
  renderEmployeeModal();
}

function openMainAgentTranscript() {
  const endpoint = adminState.mainSessionKey
    ? `${TRANSCRIPT_ENDPOINTS.main}?session_key=${encodeURIComponent(adminState.mainSessionKey)}`
    : TRANSCRIPT_ENDPOINTS.main;
  openTranscriptModal({
    title: "Main Agent Chat History",
    subtitle: text(adminState.mainSessionKey, "latest session"),
    endpoint,
  });
}

function openDockerAgentTranscript(containerName) {
  if (!containerName) return;
  openTranscriptModal({
    title: "Docker Agent Chat History",
    subtitle: containerName,
    endpoint: `${TRANSCRIPT_ENDPOINTS.docker}${encodeURIComponent(containerName)}`,
  });
}

async function loadTranscript(endpoint) {
  const response = await fetch(endpoint, { headers: { Accept: "application/json" } });
  if (!response.ok) {
    const error = await response.json().catch(() => ({ error: { message: `HTTP ${response.status}` } }));
    throw new Error(text(error?.error?.message, `HTTP ${response.status}`));
  }
  const payload = await response.json();
  adminState.transcript = {
    ...adminState.transcript,
    isLoading: false,
    error: "",
    payload,
  };
  renderEmployeeModal();
}

function openConfirmAction(action) {
  if (adminState.busyAction) return;
  adminState.confirmAction = action;
  renderEmployeeModal();
}

function closeConfirmAction() {
  if (adminState.busyAction) return;
  adminState.confirmAction = null;
  renderEmployeeModal();
}

function employeeItems() {
  return [...employeeState.runtimeEmployees, ...employeeState.employees];
}

function selectableEmployees() {
  return employeeState.employees.filter((employee) => !employee.readOnly && employee.persisted !== false);
}

function selectableEmployeeIds() {
  return selectableEmployees().map((employee) => employee.id).filter(Boolean);
}

function selectableSkills() {
  return skillState.localSkills.filter((skill) => !isRequiredLocalSkill(skill) && !skill.readOnly);
}

function selectableSkillIds() {
  return selectableSkills().map((skill) => skill.id).filter(Boolean);
}

function employeeDisplayItems() {
  return [...employeeItems()].sort(compareEmployees);
}

function findEmployeeByContainerName(containerName) {
  const normalized = text(containerName, "");
  if (!normalized) return null;
  return employeeState.employees.find((employee) => text(employee.container_name, "") === normalized) || null;
}

function employeeConfigTarget(employee) {
  if (!employee) return null;
  if (!employee.runtime) return employee;
  if (employee.runtime.kind !== "docker") return null;
  return findEmployeeByContainerName(employee.docker?.name);
}

function employeeConfigEndpoint(employeeId, suffix = "") {
  return `${EMPLOYEE_ADMIN_ENDPOINT}${encodeURIComponent(employeeId)}${suffix}`;
}

function selectedEmployeeIndex() {
  return employeeDisplayItems().findIndex((item) => item.id === employeeState.selectedEmployeeId);
}

function revealSelectedEmployeeInList() {
  if (selectedEmployeeIndex() >= EMPLOYEE_LIST_COLLAPSED_COUNT) {
    employeeState.isEmployeeListExpanded = true;
  }
}

function ensureSelectedEmployee() {
  const items = employeeDisplayItems();
  if (!items.some((item) => item.id === employeeState.selectedEmployeeId)) {
    const previousEmployeeId = employeeState.selectedEmployeeId;
    employeeState.selectedEmployeeId = items[0]?.id;
    if (employeeState.selectedEmployeeId !== previousEmployeeId) {
      employeeState.isEmployeeDetailExpanded = false;
    }
  }
}

function normalizeOrganizationNode(rawNode, employee, index) {
  const employeeId = text(rawNode?.employee_id || rawNode?.employeeId || employee?.id, "");
  const hasX = Number.isFinite(Number(rawNode?.x));
  const hasY = Number.isFinite(Number(rawNode?.y));
  const column = index % 3;
  const row = Math.floor(index / 3);
  return {
    employee_id: employeeId,
    x: hasX ? Number(rawNode.x) : 40 + column * 260,
    y: hasY ? Number(rawNode.y) : 40 + row * 180,
    allow_skip_level_reporting: Boolean(rawNode?.allow_skip_level_reporting || rawNode?.allowSkipLevelReporting),
    skill_ids: normalizeSkillIds(employee?.skill_ids || []),
    tools: Array.isArray(employee?.tools) ? employee.tools.map((item) => text(item, "")).filter(Boolean) : [],
  };
}

function normalizeOrganizationPayload(payload) {
  const employees = Array.isArray(payload?.employees)
    ? payload.employees.map(normalizePersistedEmployee)
    : [...employeeState.employees];
  const employeeById = new Map(employees.map((employee) => [employee.id, employee]));
  const rawNodesById = new Map((Array.isArray(payload?.nodes) ? payload.nodes : [])
    .map((node) => [text(node?.employee_id || node?.employeeId, ""), node])
    .filter(([employeeId]) => Boolean(employeeId)));
  const nodes = employees.map((employee, index) => normalizeOrganizationNode(rawNodesById.get(employee.id), employee, index));
  const edges = (Array.isArray(payload?.edges) ? payload.edges : [])
    .map((edge) => ({
      reporter_id: text(edge?.reporter_id || edge?.reporterId, ""),
      manager_id: text(edge?.manager_id || edge?.managerId, ""),
    }))
    .filter((edge) => edge.reporter_id && edge.manager_id && employeeById.has(edge.reporter_id) && employeeById.has(edge.manager_id));
  return {
    settings: {
      allow_skip_level_reporting: Boolean(payload?.settings?.allow_skip_level_reporting),
    },
    nodes,
    edges,
    validation: payload?.validation || { valid: true, errors: [], warnings: [] },
  };
}

function cloneOrganizationDraft(draft) {
  return {
    settings: { ...(draft?.settings || { allow_skip_level_reporting: false }) },
    nodes: (draft?.nodes || []).map((node) => ({
      ...node,
      skill_ids: normalizeSkillIds(node.skill_ids),
      tools: Array.isArray(node.tools) ? [...node.tools] : [],
    })),
    edges: (draft?.edges || []).map((edge) => ({ ...edge })),
  };
}

function organizationNodeMap() {
  return new Map((organizationState.draft?.nodes || []).map((node) => [node.employee_id, node]));
}

function organizationEmployeeMap() {
  return new Map(employeeState.employees.map((employee) => [employee.id, employee]));
}

function organizationNode(employeeId) {
  return organizationNodeMap().get(text(employeeId, ""));
}

function organizationEmployee(employeeId) {
  return organizationEmployeeMap().get(text(employeeId, ""));
}

function organizationManagerId(employeeId, edges = organizationState.draft?.edges || []) {
  const edge = edges.find((item) => item.reporter_id === employeeId);
  return edge?.manager_id || "";
}

function organizationReports(employeeId, edges = organizationState.draft?.edges || []) {
  return edges.filter((edge) => edge.manager_id === employeeId).map((edge) => edge.reporter_id);
}

function organizationWouldCreateCycle(reporterId, managerId, edges) {
  let current = managerId;
  const seen = new Set([reporterId]);
  const managerByReporter = new Map(edges.map((edge) => [edge.reporter_id, edge.manager_id]));
  while (current) {
    if (seen.has(current)) return true;
    seen.add(current);
    current = managerByReporter.get(current) || "";
  }
  return false;
}

function validateOrganizationDraft() {
  const draft = organizationState.draft;
  const errors = [];
  if (!draft) {
    organizationState.validation = { valid: true, errors: [], warnings: [] };
    return organizationState.validation;
  }
  const employeeIds = new Set(employeeState.employees.map((employee) => employee.id));
  const managerByReporter = new Map();
  for (const edge of draft.edges) {
    if (!employeeIds.has(edge.reporter_id) || !employeeIds.has(edge.manager_id)) {
      errors.push({ code: "unknown_employee", message: "Organization relationship references an unknown employee." });
    }
    if (edge.reporter_id === edge.manager_id) {
      errors.push({ code: "self_report", message: "An employee cannot report to itself." });
    }
    const existingManager = managerByReporter.get(edge.reporter_id);
    if (existingManager && existingManager !== edge.manager_id) {
      errors.push({ code: "multiple_managers", message: "An employee cannot have multiple direct managers." });
    }
    managerByReporter.set(edge.reporter_id, edge.manager_id);
  }
  for (const edge of draft.edges) {
    if (organizationWouldCreateCycle(edge.reporter_id, edge.manager_id, draft.edges)) {
      errors.push({ code: "cycle", message: "Reporting lines cannot form a cycle." });
      break;
    }
  }
  organizationState.validation = { valid: errors.length === 0, errors, warnings: [] };
  return organizationState.validation;
}

function markOrganizationDirty(message = "") {
  organizationState.isDirty = true;
  organizationState.saveStatus = message || t("organization.dirty");
  validateOrganizationDraft();
  const saveButton = document.getElementById("organization-save-button");
  if (saveButton) {
    saveButton.textContent = organizationState.isSaving ? t("organization.saving") : t("organization.save");
    saveButton.disabled = organizationState.isSaving || !organizationState.isDirty || !organizationState.validation.valid;
  }
}

function selectOrganizationEmployee(employeeId) {
  const nextEmployeeId = text(employeeId, "");
  if (organizationState.selectedEmployeeId !== nextEmployeeId) {
    organizationState.isSkillListExpanded = false;
  }
  organizationState.selectedEmployeeId = nextEmployeeId;
  organizationState.saveStatus = "";
  renderOrganization();
}

function updateOrganizationNode(employeeId, updates) {
  const node = organizationNode(employeeId);
  if (!node) return;
  Object.assign(node, updates);
  markOrganizationDirty();
  renderOrganization();
}

function setOrganizationManager(employeeId, managerId) {
  const reporterId = text(employeeId, "");
  const nextManagerId = text(managerId, "");
  if (!organizationState.draft || !reporterId) return;
  const nextEdges = organizationState.draft.edges.filter((edge) => edge.reporter_id !== reporterId);
  if (nextManagerId) {
    if (reporterId === nextManagerId) {
      organizationState.error = "An employee cannot report to itself.";
      renderOrganization();
      return;
    }
    if (organizationWouldCreateCycle(reporterId, nextManagerId, [...nextEdges, { reporter_id: reporterId, manager_id: nextManagerId }])) {
      organizationState.error = "Reporting lines cannot form a cycle.";
      renderOrganization();
      return;
    }
    nextEdges.push({ reporter_id: reporterId, manager_id: nextManagerId });
  }
  organizationState.draft.edges = nextEdges;
  organizationState.error = "";
  markOrganizationDirty();
  renderOrganization();
}

function startOrganizationConnection(employeeId) {
  const normalized = text(employeeId, "");
  if (!normalized) return;
  if (!organizationState.connectFromId) {
    organizationState.connectFromId = normalized;
    organizationState.saveStatus = t("organization.connect_hint");
    renderOrganization();
    return;
  }
  const reporterId = organizationState.connectFromId;
  organizationState.connectFromId = null;
  setOrganizationManager(reporterId, normalized);
}

function toggleOrganizationSkill(employeeId, skillId, checked) {
  const node = organizationNode(employeeId);
  if (!node) return;
  const normalizedSkillId = text(skillId, "");
  if (!normalizedSkillId || normalizedSkillId === REQUIRED_EMPLOYEE_SKILL_ID) return;
  const next = new Set(normalizeSkillIds(node.skill_ids));
  if (checked) {
    next.add(normalizedSkillId);
  } else {
    next.delete(normalizedSkillId);
  }
  node.skill_ids = [REQUIRED_EMPLOYEE_SKILL_ID, ...[...next].filter((item) => item !== REQUIRED_EMPLOYEE_SKILL_ID)];
  markOrganizationDirty();
  renderOrganization();
}

function updateOrganizationTools(employeeId, value) {
  const node = organizationNode(employeeId);
  if (!node) return;
  node.tools = parseTagInput(value);
  markOrganizationDirty();
}

function organizationCanvasBounds() {
  const nodes = organizationState.draft?.nodes || [];
  const maxX = Math.max(900, ...nodes.map((node) => Number(node.x || 0) + 240));
  const maxY = Math.max(520, ...nodes.map((node) => Number(node.y || 0) + 150));
  return { width: maxX + 80, height: maxY + 80 };
}

function renderOrganizationStatus() {
  const validation = validateOrganizationDraft();
  const status = validation.valid
    ? t("organization.valid")
    : t("organization.invalid", { count: validation.errors.length });
  const statusClass = validation.valid ? "status-ok" : "status-error";
  const extra = organizationState.error || organizationState.saveStatus;
  return `
    <div class="organization-status">
      <span class="badge ${statusClass}">${html(status)}</span>
      ${extra ? `<span>${html(extra)}</span>` : ""}
    </div>
  `;
}

function renderOrganizationCanvas() {
  const draft = organizationState.draft;
  if (!draft || draft.nodes.length === 0) {
    return `<section class="panel organization-empty"><div class="empty-state">${html(t("organization.empty"))}</div></section>`;
  }
  const bounds = organizationCanvasBounds();
  const nodeById = organizationNodeMap();
  const edges = draft.edges.map((edge) => {
    const reporter = nodeById.get(edge.reporter_id);
    const manager = nodeById.get(edge.manager_id);
    if (!reporter || !manager) return "";
    const x1 = Number(reporter.x || 0) + 220;
    const y1 = Number(reporter.y || 0) + 54;
    const x2 = Number(manager.x || 0) + 20;
    const y2 = Number(manager.y || 0) + 54;
    const mid = Math.max(x1 + 24, (x1 + x2) / 2);
    return `<path class="organization-edge" d="M ${x1} ${y1} C ${mid} ${y1}, ${mid} ${y2}, ${x2} ${y2}" marker-end="url(#organization-arrow)" />`;
  }).join("");
  const nodes = draft.nodes.map((node) => {
    const employee = organizationEmployee(node.employee_id);
    const selected = organizationState.selectedEmployeeId === node.employee_id;
    const connecting = organizationState.connectFromId === node.employee_id;
    const manager = organizationEmployee(organizationManagerId(node.employee_id));
    return `
      <article
        class="organization-node ${selected ? "is-selected" : ""} ${connecting ? "is-connecting" : ""}"
        style="transform: translate(${Number(node.x || 0)}px, ${Number(node.y || 0)}px)"
        data-organization-node="${html(node.employee_id)}"
      >
        <button class="organization-node-body" type="button" data-organization-select="${html(node.employee_id)}">
          <span>${renderEmployeeAvatar(employee || { avatar: "", name: "employee" })}</span>
          <span>
            <strong>${html(employee?.name, node.employee_id)}</strong>
            <small>${html(employee?.role, "role")}</small>
            <em>${html(manager?.name || t("organization.no_manager"))}</em>
          </span>
        </button>
        <button
          class="organization-connector"
          type="button"
          data-organization-connect="${html(node.employee_id)}"
          title="${html(organizationState.connectFromId ? t("organization.complete_line") : t("organization.start_line"))}"
          aria-label="${html(organizationState.connectFromId ? t("organization.complete_line") : t("organization.start_line"))}"
        >→</button>
      </article>
    `;
  }).join("");
  return `
    <section class="organization-canvas-wrap panel">
      <div class="panel-head">
        <div>
          <h3>${html(t("organization.canvas"))}</h3>
          <div class="panel-meta">${html(t("organization.connect_hint"))}</div>
        </div>
        <label class="organization-toggle">
          <input type="checkbox" data-organization-global-skip="true" ${draft.settings.allow_skip_level_reporting ? "checked" : ""}>
          <span>${html(t("organization.global_skip"))}</span>
        </label>
      </div>
      ${renderOrganizationStatus()}
      <div class="organization-canvas" style="min-width:${bounds.width}px; min-height:${bounds.height}px" data-organization-canvas="true">
        <svg class="organization-edge-layer" viewBox="0 0 ${bounds.width} ${bounds.height}" aria-hidden="true" focusable="false">
          <defs>
            <marker id="organization-arrow" markerWidth="10" markerHeight="8" refX="9" refY="4" orient="auto">
              <path d="M0,0 L10,4 L0,8 Z"></path>
            </marker>
          </defs>
          ${edges}
        </svg>
        <div class="organization-node-layer">${nodes}</div>
      </div>
    </section>
  `;
}

function renderOrganizationDetail() {
  const draft = organizationState.draft;
  const selectedId = organizationState.selectedEmployeeId;
  const node = selectedId ? organizationNode(selectedId) : null;
  const employee = selectedId ? organizationEmployee(selectedId) : null;
  if (!draft || !node || !employee) {
    return `<section class="panel organization-detail"><div class="empty-state">${html(t("organization.no_selection"))}</div></section>`;
  }
  const managerId = organizationManagerId(selectedId);
  const reports = organizationReports(selectedId).map((employeeId) => organizationEmployee(employeeId)?.name || employeeId);
  const selectedSkills = new Set(normalizeSkillIds(node.skill_ids));
  const localSkills = skillState.localSkills || [];
  const selectedLocalSkills = localSkills.filter((skill) => isRequiredLocalSkill(skill) || selectedSkills.has(skill.id));
  const isSkillListExpanded = organizationState.isSkillListExpanded;
  return `
    <section class="panel organization-detail" data-organization-detail="true">
      <div class="panel-head">
        <div>
          <h3>${html(t("organization.detail"))}</h3>
          <div class="panel-meta">${html(employee.name)} · ${html(employee.agent_type)}</div>
        </div>
        <span class="${badgeClass(employee.status)}">${html(employee.status)}</span>
      </div>
      <label class="organization-field">
        <span>${html(t("organization.manager"))}</span>
        <select data-organization-manager="${html(selectedId)}">
          <option value="">${html(t("organization.no_manager"))}</option>
          ${employeeState.employees.filter((item) => item.id !== selectedId).map((item) => `
            <option value="${html(item.id)}" ${item.id === managerId ? "selected" : ""}>${html(item.name)} · ${html(item.role)}</option>
          `).join("")}
        </select>
      </label>
      <button class="secondary-button organization-remove-manager" type="button" data-organization-remove-manager="${html(selectedId)}" ${managerId ? "" : "disabled"}>${html(t("organization.remove_manager"))}</button>
      <label class="organization-toggle">
        <input type="checkbox" data-organization-employee-skip="${html(selectedId)}" ${node.allow_skip_level_reporting ? "checked" : ""}>
        <span>${html(t("organization.employee_skip"))}</span>
      </label>
      <div class="organization-report-list">
        <div class="agent-section-title">${html(t("organization.reports"))}</div>
        <div>${reports.length ? reports.map((name) => `<span class="tag">${html(name)}</span>`).join("") : `<span class="tag">${html(t("organization.no_reports"))}</span>`}</div>
      </div>
      <div class="organization-skill-list">
        <div class="organization-skill-head">
          <div>
            <div class="agent-section-title">${html(t("organization.skills"))}</div>
            <div class="organization-skill-summary">${html(t("organization.skills_selected", { count: selectedLocalSkills.length }))}</div>
          </div>
          ${localSkills.length ? `
            <button class="secondary-button organization-skill-toggle" type="button" data-organization-skill-toggle="true">
              ${html(isSkillListExpanded ? t("button.collapse") : t("button.show_more", { count: localSkills.length }))}
            </button>
          ` : ""}
        </div>
        ${selectedLocalSkills.length ? `
          <div class="organization-skill-tags">
            ${selectedLocalSkills.slice(0, 4).map((skill) => `<span class="tag">${html(skill.name)}</span>`).join("")}
            ${selectedLocalSkills.length > 4 ? `<span class="tag">+${html(String(selectedLocalSkills.length - 4))}</span>` : ""}
          </div>
        ` : `<span class="tag">${html(t("organization.skills_empty"))}</span>`}
        ${isSkillListExpanded ? `
          <div class="organization-skill-options">
            ${localSkills.map((skill) => {
              const required = isRequiredLocalSkill(skill);
              const checked = required || selectedSkills.has(skill.id);
              return `
                <label class="organization-skill-option">
                  <input
                    type="checkbox"
                    data-organization-skill="${html(selectedId)}"
                    data-skill-id="${html(skill.id)}"
                    ${checked ? "checked" : ""}
                    ${required ? "disabled" : ""}
                  >
                  <span>${html(skill.name)}</span>
                </label>
              `;
            }).join("") || `<span class="tag">none</span>`}
          </div>
        ` : ""}
      </div>
      <label class="organization-field">
        <span>${html(t("organization.tools"))}</span>
        <input type="text" data-organization-tools="${html(selectedId)}" value="${html((node.tools || []).join(", "))}" placeholder="${html(t("organization.tools_placeholder"))}">
      </label>
    </section>
  `;
}

function renderOrganization() {
  const panel = document.getElementById("organization-panel");
  if (!panel) return;
  if (organizationState.isLoading) {
    panel.innerHTML = `<section class="panel"><div class="empty-state">${html(t("organization.loading"))}</div></section>`;
    return;
  }
  panel.innerHTML = `
    <div class="organization-workbench">
      ${renderOrganizationCanvas()}
      ${renderOrganizationDetail()}
    </div>
  `;
  const saveButton = document.getElementById("organization-save-button");
  if (saveButton) {
    saveButton.textContent = organizationState.isSaving ? t("organization.saving") : t("organization.save");
    saveButton.disabled = organizationState.isSaving || !organizationState.isDirty || !validateOrganizationDraft().valid;
  }
}

async function loadOrganization() {
  organizationState.isLoading = true;
  organizationState.error = "";
  renderOrganization();
  const response = await fetch(ORGANIZATION_ENDPOINT, { headers: { Accept: "application/json" } });
  if (!response.ok) {
    throw new Error(`Failed to load organization: HTTP ${response.status}`);
  }
  const payload = await response.json();
  if (Array.isArray(payload.employees)) {
    employeeState.employees = payload.employees.map(normalizePersistedEmployee);
  }
  organizationState.server = normalizeOrganizationPayload(payload);
  organizationState.draft = cloneOrganizationDraft(organizationState.server);
  organizationState.selectedEmployeeId = organizationState.selectedEmployeeId || organizationState.draft.nodes[0]?.employee_id || null;
  organizationState.connectFromId = null;
  organizationState.validation = payload.validation || { valid: true, errors: [], warnings: [] };
  organizationState.isDirty = false;
  organizationState.isLoading = false;
  organizationState.saveStatus = "";
  renderEmployees();
  renderOrganization();
}

async function saveOrganization() {
  if (!organizationState.draft || organizationState.isSaving) return;
  const validation = validateOrganizationDraft();
  if (!validation.valid) {
    organizationState.error = t("organization.invalid", { count: validation.errors.length });
    renderOrganization();
    return;
  }
  organizationState.isSaving = true;
  renderOrganization();
  try {
    const payload = {
      settings: organizationState.draft.settings,
      nodes: organizationState.draft.nodes.map((node) => ({
        employee_id: node.employee_id,
        x: Number(node.x || 0),
        y: Number(node.y || 0),
        allow_skip_level_reporting: Boolean(node.allow_skip_level_reporting),
      })),
      edges: organizationState.draft.edges.map((edge) => ({ ...edge })),
      capabilities: organizationState.draft.nodes.map((node) => ({
        employee_id: node.employee_id,
        skill_ids: normalizeSkillIds(node.skill_ids),
        tools: Array.isArray(node.tools) ? node.tools : [],
      })),
    };
    const response = await fetch(ORGANIZATION_ENDPOINT, {
      method: "PUT",
      headers: { "Content-Type": "application/json", Accept: "application/json" },
      body: JSON.stringify(payload),
    });
    const body = await response.json().catch(() => ({}));
    if (!response.ok) {
      throw new Error(text(body?.error?.message, `HTTP ${response.status}`));
    }
    if (Array.isArray(body.employees)) {
      employeeState.employees = body.employees.map(normalizePersistedEmployee);
    }
    organizationState.server = normalizeOrganizationPayload(body);
    organizationState.draft = cloneOrganizationDraft(organizationState.server);
    organizationState.isDirty = false;
    organizationState.error = "";
    organizationState.saveStatus = t("organization.saved");
    renderEmployees();
  } finally {
    organizationState.isSaving = false;
    renderOrganization();
  }
}

function startOrganizationDrag(event, nodeElement) {
  const employeeId = nodeElement.getAttribute("data-organization-node");
  const node = organizationNode(employeeId);
  if (!node) return;
  organizationState.drag = {
    employeeId,
    startX: event.clientX,
    startY: event.clientY,
    x: Number(node.x || 0),
    y: Number(node.y || 0),
  };
  nodeElement.setPointerCapture?.(event.pointerId);
}

function moveOrganizationDrag(event) {
  if (!organizationState.drag) return;
  const drag = organizationState.drag;
  const node = organizationNode(drag.employeeId);
  if (!node) return;
  node.x = Math.max(0, drag.x + event.clientX - drag.startX);
  node.y = Math.max(0, drag.y + event.clientY - drag.startY);
  markOrganizationDirty();
  renderOrganization();
}

function endOrganizationDrag() {
  organizationState.drag = null;
}

function employeeTimeCandidate(employee, mode) {
  if (employee.runtime) {
    return text(employee.runtime.startedAt, "");
  }
  if (mode === "created") {
    return text(employee.created_at, "");
  }
  return text(employee.updated_at || employee.created_at, "");
}

function parseEmployeeTimestamp(value) {
  const raw = text(value, "").trim();
  if (!raw || ["unknown", "not tracked", "not available", "not finished"].includes(raw.toLowerCase())) {
    return null;
  }
  const parsed = Date.parse(raw);
  return Number.isNaN(parsed) ? null : parsed;
}

function compareNullableDesc(left, right) {
  if (left === right) return 0;
  if (left === null) return 1;
  if (right === null) return -1;
  return right - left;
}

function compareTextAsc(left, right) {
  return text(left, "").localeCompare(text(right, ""), undefined, { sensitivity: "base" });
}

function compareEmployeeStable(left, right) {
  const nameCmp = compareTextAsc(left.name, right.name);
  if (nameCmp !== 0) return nameCmp;
  return compareTextAsc(left.id, right.id);
}

function compareEmployeesByTime(left, right, mode) {
  const timeCmp = compareNullableDesc(
    parseEmployeeTimestamp(employeeTimeCandidate(left, mode)),
    parseEmployeeTimestamp(employeeTimeCandidate(right, mode)),
  );
  if (timeCmp !== 0) return timeCmp;
  return compareEmployeeStable(left, right);
}

function compareEmployees(left, right) {
  const mode = normalizeEmployeeSortMode(employeeState.employeeSortMode);
  if (mode === "type") {
    const typeCmp = Number(Boolean(left.runtime)) - Number(Boolean(right.runtime));
    if (typeCmp !== 0) return typeCmp;
    return compareEmployeesByTime(left, right, "updated");
  }
  return compareEmployeesByTime(left, right, mode);
}

function runtimeName(agent) {
  return text(agent.name || agent.containerName || agent.agentKey || agent.id, "runtime-worker");
}

function createEmployeeFromDocker(agent) {
  const name = runtimeName(agent);
  const cpu = text(agent.cpuPercent, "n/a");
  const memory = text(agent.memoryUsage, "n/a");
  const command = text(agent.currentCommand, "idle");
  return {
    id: `runtime-docker-${slugify(name, "docker")}`,
    name,
    avatar: "",
    role: "Docker Worker / 容器运行时",
    companyStyle: text(agent.source, "docker"),
    summary: `Live Docker container sampled from runtime monitor. Current command: ${command}`,
    docker: {
      image: text(agent.image, "unknown"),
      name,
      ports: text(agent.ports, "no ports"),
      resources: `CPU ${cpu} · Memory ${memory}`,
    },
    status: text(agent.status, "unknown"),
    settings: {
      model: text(agent.agentKey, "runtime"),
      mode: command,
      team: text(agent.source, "docker"),
      workspace: text(agent.uptime, "unknown uptime"),
      guardrails: "Runtime state is sampled from Docker and tracker snapshots.",
    },
    skills: ["Docker runtime", text(agent.source, "docker")],
    tools: Array.isArray(agent.processes) && agent.processes.length ? agent.processes : [command],
    exampleTasks: [text(agent.ports, "no exposed ports")],
    demo: agent.demo === true,
    readOnly: agent.demo === true || agent.readOnly === true || agent.read_only === true,
    runtime: {
      kind: "docker",
      source: text(agent.source, "docker"),
      sessionKey: text(agent.sessionKey, "no session"),
      command,
      startedAt: text(agent.startedAt, "not tracked"),
      taskPreview: text(agent.lastTaskSummary, "not available"),
      context: agent.context || null,
    },
  };
}

function createEmployeeFromSubagent(agent) {
  const name = text(agent.label || agent.id, "subagent");
  return {
    id: `runtime-subagent-${slugify(agent.id || name, "subagent")}`,
    name,
    avatar: "",
    role: "Subagent / 后台执行代理",
    companyStyle: "runtime session",
    summary: text(agent.taskPreview, "Background subagent task"),
    docker: {
      image: "n/a",
      name: text(agent.id, name),
      ports: "n/a",
      resources: text(agent.duration, "running"),
    },
    status: text(agent.status, "unknown"),
    settings: {
      model: "runtime",
      mode: "spawned task",
      team: text(agent.sessionKey, "no session"),
      workspace: text(agent.startedAt, "not tracked"),
      guardrails: "Subagent state is reported by RuntimeMonitor.",
    },
    skills: ["Subagent runtime"],
    tools: ["spawn_agent"],
    exampleTasks: [text(agent.taskPreview, "unknown task")],
    runtime: {
      kind: "subagent",
      source: "runtime",
      sessionKey: text(agent.sessionKey, "no session"),
      command: text(agent.taskPreview, "unknown task"),
      startedAt: text(agent.startedAt, "not tracked"),
      finishedAt: text(agent.finishedAt, "not finished"),
      taskPreview: text(agent.taskPreview, "unknown task"),
    },
  };
}

function syncEmployeesFromRuntime(payload) {
  const dockerRows = Array.isArray(payload.dockerContainers)
    ? payload.dockerContainers
    : (Array.isArray(payload.dockerAgents) ? payload.dockerAgents : []);
  const subagents = Array.isArray(payload.subagents) ? payload.subagents : [];
  employeeState.runtimeEmployees = [
    ...subagents.map(createEmployeeFromSubagent),
    ...dockerRows.map(createEmployeeFromDocker),
  ];
  ensureSelectedEmployee();
  revealSelectedEmployeeInList();
}

function renderEmployeeList() {
  const list = document.getElementById("employee-list");
  if (!list) return;
  ensureSelectedEmployee();
  const items = employeeDisplayItems();
  const persistedIds = selectableEmployeeIds();
  const selectedDeleteCount = employeeState.selectedDeleteIds.length;
  const allEmployeesSelected = persistedIds.length > 0 && persistedIds.every((id) => employeeState.selectedDeleteIds.includes(id));
  const hiddenCount = Math.max(0, items.length - EMPLOYEE_LIST_COLLAPSED_COUNT);
  const visibleItems = employeeState.isEmployeeListExpanded
    ? items
    : items.slice(0, EMPLOYEE_LIST_COLLAPSED_COUNT);
  const createSummary = text(employeeState.lastCreateSkillSummary, "");
  list.innerHTML = `
    <div class="employee-list-head">
      <div>
        <div class="agent-section-title">${t("employees.roster")}</div>
        <div class="panel-meta">${t("employees.counts", { live: employeeState.runtimeEmployees.length, saved: employeeState.employees.length })}</div>
        ${createSummary ? `<div class="employee-create-status">${html(createSummary)}</div>` : ""}
      </div>
      <div class="employee-list-controls">
        <div class="batch-select-controls">
          <label class="batch-checkbox" data-toggle-all-employees="true">
            <input type="checkbox" ${allEmployeesSelected ? "checked" : ""} ${persistedIds.length ? "" : "disabled"}>
            <span>${t("button.select")}</span>
          </label>
          <span class="panel-meta">${t("employees.selected", { count: html(selectedDeleteCount, "0") })}</span>
          <button class="secondary-button batch-export-button" type="button" data-export-selected-employees="true" ${selectedDeleteCount ? "" : "disabled"}>${t("button.export_selected")}</button>
          <button class="danger-button batch-delete-button" type="button" data-delete-selected-employees="true" ${selectedDeleteCount ? "" : "disabled"}>${t("button.delete_selected")}</button>
        </div>
        <label class="employee-sort-control">
          <span>${t("employees.sort_by")}</span>
          <select data-employee-sort="true" aria-label="${html(t("employees.sort_by"))}">
            ${Object.keys(EMPLOYEE_SORT_MODES).map((mode) => `
              <option value="${mode}" ${mode === employeeState.employeeSortMode ? "selected" : ""}>${employeeSortModeLabel(mode)}</option>
            `).join("")}
          </select>
        </label>
      </div>
    </div>
    <div class="employee-card-list">
      ${visibleItems.map((employee) => {
        const owner = employeeConfigTarget(employee);
        const sourceLabel = employee.runtime?.kind === "docker"
          ? `${t("employees.belongs_to")}: ${text(owner?.name, t("employees.unassigned"))}`
          : (employee.demo ? "demo" : (employee.runtime?.source || employee.agent_type || "persisted"));
        const canBatchDelete = !employee.runtime && !employee.readOnly && employee.persisted !== false;
        const deleteChecked = employeeState.selectedDeleteIds.includes(employee.id);
        return `
        <article
          class="employee-card ${employee.id === employeeState.selectedEmployeeId ? "is-selected" : ""}"
          data-employee-id="${html(employee.id)}"
          tabindex="0"
          role="button"
        >
          ${employee.runtime?.kind === "docker" && !employee.demo ? `
            <span class="employee-card-controls">
              <span
                class="mini-icon-button ${isBusy(`delete-docker:${employee.docker.name}`) ? "is-busy" : ""}"
                role="button"
                tabindex="0"
                data-delete-docker-card="${html(employee.docker.name)}"
                aria-label="${html(t("button.delete_docker"))}"
                title="${html(t("button.delete_docker"))}"
              >${isBusy(`delete-docker:${employee.docker.name}`) ? "..." : "×"}</span>
            </span>
          ` : (!employee.runtime && !employee.readOnly ? `
            <span class="employee-card-controls">
              ${canBatchDelete ? `
                <label class="batch-checkbox compact-batch-checkbox" data-employee-delete-toggle="${html(employee.id)}">
                  <input type="checkbox" ${deleteChecked ? "checked" : ""}>
                  <span class="visually-hidden">${html(`${t("button.select")} ${employee.name}`)}</span>
                </label>
              ` : ""}
              <span
                class="mini-icon-button ${isBusy(`delete-employee:${employee.id}`) ? "is-busy" : ""}"
                role="button"
                tabindex="0"
                data-delete-employee-card="${html(employee.id)}"
                aria-label="${html(t("button.delete_employee"))}"
                title="${html(t("button.delete_employee"))}"
              >${isBusy(`delete-employee:${employee.id}`) ? "..." : "×"}</span>
            </span>
          ` : "")}
          <span class="employee-card-main">
            ${renderEmployeeAvatar(employee)}
            <span>
              <strong>${html(employee.name)}</strong>
              <span>${html(employee.role)}</span>
            </span>
          </span>
          <span class="employee-card-foot">
              <span>${html(sourceLabel)}</span>
            ${employee.demo || employee.readOnly ? `<span class="tag demo-badge" data-demo-badge="true">Demo</span>` : ""}
            <span class="${badgeClass(employee.status)}">${html(employee.status)}</span>
          </span>
        </article>
      `;
      }).join("")}
    </div>
    ${hiddenCount > 0 ? `
      <button
        class="employee-list-toggle"
        type="button"
        data-toggle-employee-list="true"
        aria-expanded="${employeeState.isEmployeeListExpanded ? "true" : "false"}"
      >${employeeState.isEmployeeListExpanded ? t("button.collapse") : t("button.show_more", { count: hiddenCount })}</button>
    ` : ""}
  `;
}

function renderEmployeeDetail() {
  const detail = document.getElementById("employee-detail");
  if (!detail) return;
  ensureSelectedEmployee();
  const employee = employeeDisplayItems().find((item) => item.id === employeeState.selectedEmployeeId);
  if (!employee) {
    detail.innerHTML = `<section class="panel"><div class="empty-state">${html(t("employees.empty_detail"))}</div></section>`;
    return;
  }
  if (employee.runtime) {
    renderEmployeeRuntimeDetail(detail, employee);
    return;
  }
  renderPersistedEmployeeDetail(detail, employee);
}

function renderEmployeeDetailToggle(hiddenCount) {
  if (hiddenCount <= 0) return "";
  return `
    <button
      class="employee-detail-toggle"
      type="button"
      data-toggle-employee-detail="true"
      aria-expanded="${employeeState.isEmployeeDetailExpanded ? "true" : "false"}"
    >${employeeState.isEmployeeDetailExpanded ? t("button.collapse") : t("button.show_more", { count: hiddenCount })}</button>
  `;
}

function employeeOpsOwner(employee) {
  return employee?.runtime ? employeeConfigTarget(employee) : employee;
}

function employeeOpsConfigApplies(owner, configState = employeeConfigState) {
  return Boolean(owner?.id && configState?.employeeId === owner.id);
}

function employeeOpsBusinessSkillIds(skills = skillState.localSkills) {
  return new Set((Array.isArray(skills) ? skills : [])
    .filter((skill) => !isRequiredLocalSkill(skill))
    .map((skill) => text(skill.id, ""))
    .filter(Boolean));
}

function employeeOpsBusinessSkillLabels(employee, skills = skillState.localSkills) {
  if (!employee) return [];
  const skillById = new Map((Array.isArray(skills) ? skills : [])
    .map((skill) => [text(skill.id, ""), skill])
    .filter(([id]) => Boolean(id)));
  const labels = [];
  for (const skillId of normalizeSkillIds(employee.skill_ids)) {
    if (isRequiredEmployeeSkillId(skillId)) continue;
    labels.push(text(skillById.get(skillId)?.name || skillId, skillId));
  }
  for (const name of Array.isArray(employee.skills) ? employee.skills : []) {
    const normalized = text(name, "").trim();
    if (!normalized || normalized === REQUIRED_EMPLOYEE_SKILL_ID || normalized === "优秀员工协议") continue;
    labels.push(normalized);
  }
  return [...new Set(labels)];
}

function employeeOpsHasRequiredSkill(employee) {
  if (!employee) return false;
  if (normalizeSkillIds(employee.skill_ids).includes(REQUIRED_EMPLOYEE_SKILL_ID)) return true;
  return (Array.isArray(employee.skills) ? employee.skills : []).some((name) => (
    text(name, "").trim().toLowerCase() === REQUIRED_EMPLOYEE_SKILL_ID || text(name, "").trim() === "优秀员工协议"
  ));
}

function employeeOpsHealthMeta(code) {
  const meta = {
    healthy: { badgeStatus: "ok", level: "ok" },
    needs_setup: { badgeStatus: "warning", level: "warning" },
    runtime_issue: { badgeStatus: "error", level: "danger" },
    restart_required: { badgeStatus: "warning", level: "warning" },
    skill_gap: { badgeStatus: "warning", level: "warning" },
  };
  return meta[code] || meta.healthy;
}

function computeEmployeeOpsHealth(employee, runtime = employee?.runtime, skills = skillState.localSkills, configState = employeeConfigState, cronState = employeeConfigState) {
  const owner = employeeOpsOwner(employee);
  const status = text(employee?.status, "").toLowerCase();
  const runtimeKind = text(runtime?.kind, "");
  let code = "healthy";
  if (runtime && ["error", "exited", "unknown"].includes(status)) {
    code = "runtime_issue";
  } else if (owner && employeeOpsConfigApplies(owner, configState) && configState.restartRequired) {
    code = "restart_required";
  } else if ((owner || !runtime) && !employeeHasBusinessSkill(owner || employee, employeeOpsBusinessSkillIds(skills))) {
    code = "skill_gap";
  } else if ((!runtime && !text(employee?.container_name, "")) || (runtimeKind === "docker" && !owner)) {
    code = "needs_setup";
  }
  const meta = employeeOpsHealthMeta(code);
  return {
    code,
    status: t(`ops.health.${code}`),
    body: t(`ops.health.${code}.body`),
    badgeStatus: meta.badgeStatus,
    level: meta.level,
    cronJobCount: Array.isArray(cronState?.cronJobs) ? cronState.cronJobs.length : 0,
  };
}

function employeeOpsActionButton(action) {
  const attributes = [
    `data-employee-ops-action="${html(action.kind)}"`,
    action.employeeId ? `data-employee-ops-employee-id="${html(action.employeeId)}"` : "",
    action.containerName ? `data-employee-ops-container="${html(action.containerName)}"` : "",
    action.section ? `data-employee-ops-target="${html(action.section)}"` : "",
  ].filter(Boolean).join(" ");
  return `
    <button
      class="employee-ops-action ${action.danger ? "is-danger" : ""}"
      type="button"
      ${attributes}
      ${action.disabled ? "disabled" : ""}
    >${html(action.label)}</button>
  `;
}

function employeeOpsChatContainer(employee, owner) {
  if (employee?.runtime?.kind === "docker") return text(employee?.docker?.name, "");
  return text(owner?.container_name || employee?.container_name, "");
}

function renderEmployeeOpsActions(employee, owner) {
  const configReady = Boolean(owner?.id);
  const configApplies = employeeOpsConfigApplies(owner);
  const cronJobs = configApplies ? employeeConfigState.cronJobs || [] : [];
  const containerName = employeeOpsChatContainer(employee, owner);
  const actions = [
    { kind: "config", label: t("ops.action.edit_config"), section: "config", disabled: !configReady },
    { kind: "cron", label: t(cronJobs.length ? "ops.action.view_cron" : "ops.action.create_cron"), section: "cron", disabled: !configReady },
    { kind: "skills", label: t("ops.action.review_skills") },
    { kind: "transcript", label: t("ops.action.chat_history"), containerName, disabled: !containerName },
    { kind: "infrastructure", label: t("ops.action.infrastructure") },
  ];
  if (employee?.runtime?.kind === "docker") {
    actions.push({ kind: "delete-docker", label: t("ops.action.delete_docker"), containerName: employee.docker?.name, danger: true, disabled: !employee.docker?.name });
  } else if (!employee?.runtime) {
    actions.push({ kind: "delete-employee", label: t("ops.action.delete_employee"), employeeId: employee?.id, danger: true, disabled: !employee?.id });
  }
  return `<div class="employee-ops-actions">${actions.map(employeeOpsActionButton).join("")}</div>`;
}

function employeeOpsTimestamp(value) {
  const numeric = Number(value || 0);
  if (!numeric) return t("ops.value.none");
  const date = new Date(numeric);
  if (Number.isNaN(date.getTime())) return t("ops.value.none");
  return date.toLocaleString();
}

function employeeOpsCronTimestamp(jobs, field, pick) {
  const values = (Array.isArray(jobs) ? jobs : [])
    .map((job) => Number(job?.state?.[field] || 0))
    .filter((value) => value > 0);
  if (!values.length) return t("ops.value.none");
  return employeeOpsTimestamp(pick(...values));
}

function renderEmployeeOpsMetric(label, value) {
  return `
    <div class="employee-ops-metric">
      <span>${html(label)}</span>
      <strong>${html(value, t("ops.value.none"))}</strong>
    </div>
  `;
}

function renderEmployeeOpsDiagnosticCard(key, title, metrics) {
  return `
    <article class="employee-ops-diagnostic" data-employee-ops-diagnostic="${html(key)}">
      <div class="employee-ops-diagnostic-title">${html(title)}</div>
      <div class="employee-ops-metrics">${metrics.map((item) => renderEmployeeOpsMetric(item.label, item.value)).join("")}</div>
    </article>
  `;
}

function renderEmployeeOpsDiagnostics(employee, options = {}) {
  const owner = options.owner || employeeOpsOwner(employee);
  const runtime = options.runtime || employee?.runtime || null;
  const context = runtime?.context || null;
  const configApplies = employeeOpsConfigApplies(owner);
  const configSelected = selectedEmployeeConfigFile();
  const configStateLabel = !owner
    ? t("ops.value.not_assigned")
    : employeeConfigState.isLoading || !configApplies
      ? t("ops.value.loading")
      : employeeConfigState.error
        ? employeeConfigState.error
        : employeeConfigState.restartRequired
          ? t("ops.value.restart")
          : employeeConfigState.isEditing
            ? t("ops.value.editing")
            : t("ops.value.saved");
  const cronJobs = configApplies ? employeeConfigState.cronJobs || [] : [];
  const enabledCronJobs = cronJobs.filter((job) => job.enabled);
  const skillTarget = owner || (!runtime ? employee : null);
  const businessSkills = employeeOpsBusinessSkillLabels(skillTarget, skillState.localSkills);
  const containerName = employeeOpsChatContainer(employee, owner);
  const cards = [
    renderEmployeeOpsDiagnosticCard("runtime", t("ops.diag.runtime"), [
      { label: t("ops.diag.status"), value: text(employee?.status, "unknown") },
      { label: t("ops.diag.container"), value: text(employee?.docker?.name || employee?.container_name, t("ops.value.not_assigned")) },
      { label: t("ops.diag.session"), value: text(runtime?.sessionKey, t("ops.value.none")) },
      { label: t("ops.diag.context"), value: context ? `${percent(context.percent)}% · ${text(context.usedTokens, "0")} / ${text(context.totalTokens, "0")}` : t("ops.value.none") },
      { label: t("ops.diag.owner"), value: text(owner?.name, t("employees.unassigned")) },
    ]),
    renderEmployeeOpsDiagnosticCard("config", t("ops.diag.configuration"), [
      { label: t("ops.diag.file"), value: configApplies ? configSelected.name : t("ops.value.not_loaded") },
      { label: t("ops.diag.config_state"), value: configStateLabel },
      { label: t("ops.diag.files"), value: configApplies ? String(employeeConfigState.files.length) : "0" },
    ]),
    renderEmployeeOpsDiagnosticCard("skills", t("ops.diag.skills"), [
      { label: t("ops.diag.business_skills"), value: businessSkills.length ? businessSkills.join(", ") : t("ops.value.missing") },
      { label: t("ops.diag.required_skill"), value: employeeOpsHasRequiredSkill(skillTarget) ? t("ops.value.available") : t("ops.value.missing") },
    ]),
    renderEmployeeOpsDiagnosticCard("cron", t("ops.diag.automation"), [
      { label: t("ops.diag.jobs"), value: String(cronJobs.length) },
      { label: t("ops.diag.enabled"), value: String(enabledCronJobs.length) },
      { label: t("ops.diag.next_run"), value: employeeOpsCronTimestamp(cronJobs, "nextRunAtMs", Math.min) },
      { label: t("ops.diag.last_run"), value: employeeOpsCronTimestamp(cronJobs, "lastRunAtMs", Math.max) },
    ]),
    renderEmployeeOpsDiagnosticCard("activity", t("ops.diag.activity"), [
      { label: t("ops.diag.history"), value: containerName ? t("ops.value.available") : t("ops.value.no_history") },
      { label: t("ops.diag.session"), value: text(runtime?.sessionKey, t("ops.value.none")) },
    ]),
  ];
  return `<div class="employee-ops-diagnostics">${cards.join("")}</div>`;
}

function renderEmployeeOpsWorkbench(employee, options = {}) {
  const owner = options.owner || employeeOpsOwner(employee);
  if (owner?.id) {
    ensureEmployeeConfigLoaded(owner.id);
  }
  const runtime = options.runtime || employee?.runtime || null;
  const health = computeEmployeeOpsHealth(employee, runtime, skillState.localSkills, employeeConfigState, employeeConfigState);
  return `
    <div class="employee-ops-workbench employee-ops-${health.level}" data-employee-ops="true">
      <div class="employee-ops-summary">
        <div>
          <div class="agent-section-title">${t("ops.title")}</div>
          <p>${html(health.body)}</p>
        </div>
        <span class="${badgeClass(health.badgeStatus)}">${html(health.status)}</span>
      </div>
      ${renderEmployeeOpsActions(employee, owner)}
      ${renderEmployeeOpsDiagnostics(employee, { owner, runtime, health })}
    </div>
  `;
}

function revealEmployeeOpsSection(section) {
  if (section === "config" || section === "cron") {
    employeeState.isEmployeeDetailExpanded = true;
    renderEmployeeDetail();
  }
  window.requestAnimationFrame(() => {
    const target = document.querySelector(`[data-employee-ops-section="${section}"]`);
    if (target) {
      target.scrollIntoView({ behavior: "smooth", block: "start" });
    }
  });
}

function handleEmployeeOpsAction(event) {
  const button = event.target instanceof Element ? event.target.closest("[data-employee-ops-action]") : null;
  if (!button) return false;
  const action = button.getAttribute("data-employee-ops-action");
  if (action === "config" || action === "cron") {
    revealEmployeeOpsSection(action);
    return true;
  }
  if (action === "skills") {
    setResourceHubTab("skills");
    scrollToNavSection("resource-hub");
    return true;
  }
  if (action === "transcript") {
    const containerName = button.getAttribute("data-employee-ops-container");
    if (containerName) openDockerAgentTranscript(containerName);
    return true;
  }
  if (action === "infrastructure") {
    scrollToNavSection("infrastructure-shell");
    return true;
  }
  if (action === "delete-docker") {
    const containerName = button.getAttribute("data-employee-ops-container");
    openConfirmAction({
      kind: "delete-docker",
      containerName,
      title: "Delete Docker Container",
      subtitle: "This will force remove the running container.",
      message: `Delete Docker container ${containerName}? Running workloads will be interrupted immediately.`,
      confirmLabel: "Delete Docker",
    });
    return true;
  }
  if (action === "delete-employee") {
    const employeeId = button.getAttribute("data-employee-ops-employee-id");
    const employee = employeeItems().find((item) => item.id === employeeId);
    openConfirmAction({
      kind: "delete-employee",
      employeeId,
      title: "Delete Employee",
      subtitle: "This will remove the persisted employee.",
      message: `Delete employee ${text(employee?.name, employeeId)}? This action cannot be undone.`,
      confirmLabel: "Delete Employee",
    });
    return true;
  }
  return false;
}

function renderPersistedEmployeeDetail(detail, employee) {
  const detailSections = [
    () => `
      <div class="agent-section">
        <div class="agent-section-title">System Prompt</div>
        <div class="code-block">${html(employee.system_prompt)}</div>
      </div>
    `,
    () => renderEmployeeConfigEditor(employee),
  ];
  const expandedDetail = employeeState.isEmployeeDetailExpanded
    ? detailSections.map((renderSection) => renderSection()).join("")
    : "";
  detail.innerHTML = `
    <section class="panel employee-detail-panel">
      <div class="panel-head">
        <div class="employee-identity">
          ${renderEmployeeAvatar(employee, "employee-avatar-large")}
          <div>
          <h3>${html(employee.name)}</h3>
          <div class="panel-meta">${html(employee.role)} · ${html(employee.agent_type)}</div>
          </div>
        </div>
        <div class="employee-actions">
          <span class="${badgeClass(employee.status)}">${html(employee.status)}</span>
          <button class="danger-button" type="button" data-delete-employee="${html(employee.id)}">Delete Employee</button>
        </div>
      </div>
      ${renderEmployeeOpsWorkbench(employee, { owner: employee })}
      <p class="employee-summary ${employeeState.isEmployeeDetailExpanded ? "" : "is-collapsed"}">${html(employee.system_prompt || "Persistent digital employee configuration.")}</p>
      <dl class="key-value employee-key-value">
        <div><dt>ID</dt><dd>${html(employee.id)}</dd></div>
        <div><dt>Avatar</dt><dd>${html(getAvatarPreset(employee.avatar)?.label || employee.avatar || "default")}</dd></div>
        <div><dt>Agent Type</dt><dd>${html(employee.agent_type)}</dd></div>
        <div><dt>Container</dt><dd>${html(employee.container_name, "not assigned")}</dd></div>
        <div><dt>Role</dt><dd>${html(employee.role)}</dd></div>
        <div><dt>Created At</dt><dd>${html(employee.created_at, "unknown")}</dd></div>
      </dl>
      <div class="employee-detail-grid">
        <div class="agent-section">
          <div class="agent-section-title">Skills / Tags</div>
          <div class="tag-cloud">${renderTags(employee.skills)}</div>
        </div>
        <div class="agent-section">
          <div class="agent-section-title">Agent Config</div>
          <div class="code-block">${html(JSON.stringify(employee.agent_config || {}, null, 2), "{}")}</div>
        </div>
      </div>
      ${expandedDetail}
      ${renderEmployeeDetailToggle(detailSections.length)}
    </section>
  `;
}

function renderEmployeeRuntimeDetail(detail, employee) {
  const context = employee.runtime.context || {};
  const current = percent(context.percent);
  const owner = employeeConfigTarget(employee);
  const deleteActionKey = `delete-docker:${employee.docker.name}`;
  const dockerDeleteButton = employee.runtime.kind === "docker"
    ? `<button class="danger-button" type="button" data-delete-docker="${html(employee.docker.name)}" ${isBusy(deleteActionKey) ? "disabled" : ""}>${isBusy(deleteActionKey) ? "Deleting..." : "Delete Docker"}</button>`
    : "";
  const detailSections = [
    () => `
      <div class="agent-section">
        <div class="agent-section-title">Task Preview</div>
        <div class="code-block">${html(employee.runtime.taskPreview)}</div>
      </div>
    `,
    () => renderEmployeeConfigEditor(owner),
  ];
  const taskPreviewSection = employeeState.isEmployeeDetailExpanded ? detailSections[0]() : "";
  const configSection = employeeState.isEmployeeDetailExpanded ? detailSections[1]() : "";
  detail.innerHTML = `
    <section class="panel employee-detail-panel">
      <div class="panel-head">
        <div class="employee-identity">
          ${renderEmployeeAvatar(employee, "employee-avatar-large")}
          <div>
          <h3>${html(employee.name)}</h3>
          <div class="panel-meta">${html(employee.role)} · ${html(employee.runtime.kind)}</div>
          </div>
        </div>
        <div class="employee-actions">
          <span class="${badgeClass(employee.status)}">${html(employee.status)}</span>
          ${dockerDeleteButton}
        </div>
      </div>
      ${renderEmployeeOpsWorkbench(employee, { owner, runtime: employee.runtime })}
      <p class="employee-summary ${employeeState.isEmployeeDetailExpanded ? "" : "is-collapsed"}">${html(employee.summary)}</p>
      <dl class="key-value employee-key-value">
        <div><dt>Source</dt><dd>${html(employee.runtime.source)}</dd></div>
        <div><dt>Session</dt><dd>${html(employee.runtime.sessionKey)}</dd></div>
        <div><dt>Docker Image</dt><dd>${html(employee.docker.image)}</dd></div>
        <div><dt>Runtime Name</dt><dd>${html(employee.docker.name)}</dd></div>
        <div><dt>Belongs to / 所属员工</dt><dd>${html(owner?.name, "Unassigned")}</dd></div>
        <div><dt>Ports</dt><dd>${html(employee.docker.ports)}</dd></div>
        <div><dt>Resources</dt><dd>${html(employee.docker.resources)}</dd></div>
        <div><dt>Started</dt><dd>${html(employee.runtime.startedAt)}</dd></div>
        <div><dt>Workspace / Uptime</dt><dd>${html(employee.settings.workspace)}</dd></div>
      </dl>
      <div class="agent-section">
        <div class="agent-section-title">Current Task</div>
        <div class="command-line">${html(employee.runtime.command)}</div>
      </div>
      ${taskPreviewSection}
      ${employee.runtime.context ? `
        <div class="agent-section">
          <div class="agent-section-title">Context Estimate</div>
          <div class="progress"><span style="width: ${current}%"></span></div>
          <div class="progress-label">
            <span>${html(context.usedTokens, "0")} / ${html(context.totalTokens, "0")}</span>
            <span>${current}% · ${html(context.source, "unknown")}</span>
          </div>
        </div>
      ` : ""}
      <div class="agent-section">
        <div class="agent-section-title">Processes / Tools</div>
        <div class="tag-cloud">${renderTags(employee.tools, "tag tool-tag")}</div>
      </div>
      ${configSection}
      ${renderEmployeeDetailToggle(detailSections.length)}
    </section>
  `;
}

function resetEmployeeConfigState(employeeId = "") {
  employeeConfigState.employeeId = employeeId;
  employeeConfigState.files = [];
  employeeConfigState.selectedFile = EMPLOYEE_CONFIG_FILES[0];
  employeeConfigState.drafts = {};
  employeeConfigState.isEditing = false;
  employeeConfigState.isLoading = false;
  employeeConfigState.error = "";
  employeeConfigState.restartRequired = false;
  employeeConfigState.cronJobs = [];
  employeeConfigState.cronDraft = defaultEmployeeCronDraft();
  employeeConfigState.isCronLoading = false;
  employeeConfigState.cronError = "";
}

function defaultEmployeeCronDraft(overrides = {}) {
  return {
    id: "",
    name: "",
    message: "",
    kind: "every",
    everyMs: "3600000",
    expr: "0 9 * * *",
    tz: "",
    enabled: true,
    deliver: false,
    ...overrides,
  };
}

function ensureEmployeeConfigLoaded(employeeId) {
  const normalizedId = text(employeeId, "");
  if (!normalizedId) return;
  if (employeeConfigState.employeeId === normalizedId && (employeeConfigState.files.length || employeeConfigState.isLoading || employeeConfigState.error)) {
    return;
  }
  resetEmployeeConfigState(normalizedId);
  employeeConfigState.isLoading = true;
  loadEmployeeConfig(normalizedId).catch((error) => {
    employeeConfigState.isLoading = false;
    employeeConfigState.error = text(error.message, "Failed to load employee config.");
    renderEmployees();
  });
}

function selectedEmployeeConfigFile() {
  return employeeConfigState.files.find((file) => file.name === employeeConfigState.selectedFile)
    || employeeConfigState.files[0]
    || { name: employeeConfigState.selectedFile, content: "" };
}

function renderEmployeeConfigEditor(employee) {
  if (!employee) {
    return `
      <div class="agent-section employee-config-panel" data-employee-ops-section="config">
        <div class="agent-section-title">Employee Runtime Config</div>
        <div class="empty-state">Belongs to / 所属员工: Unassigned</div>
      </div>
    `;
  }
  ensureEmployeeConfigLoaded(employee.id);
  if (employeeConfigState.employeeId !== employee.id || employeeConfigState.isLoading) {
    return `
      <div class="agent-section employee-config-panel" data-employee-ops-section="config">
        <div class="agent-section-title">Employee Runtime Config</div>
        <div class="empty-state">Loading employee config...</div>
      </div>
    `;
  }
  if (employeeConfigState.error) {
    return `
      <div class="agent-section employee-config-panel" data-employee-ops-section="config">
        <div class="agent-section-title">Employee Runtime Config</div>
        <div class="empty-state">${html(employeeConfigState.error)}</div>
      </div>
    `;
  }
  const selected = selectedEmployeeConfigFile();
  const draft = Object.prototype.hasOwnProperty.call(employeeConfigState.drafts, selected.name)
    ? employeeConfigState.drafts[selected.name]
    : text(selected.content, "");
  const isDirty = draft !== text(selected.content, "");
  return `
    <div class="agent-section employee-config-panel" data-employee-ops-section="config">
      <div class="panel-head employee-config-head">
        <div>
          <div class="agent-section-title">Employee Runtime Config</div>
          <div class="panel-meta">Belongs to / 所属员工: ${html(employee.name)} · ${html(employee.container_name, "no container")}</div>
        </div>
        ${employeeConfigState.restartRequired ? `<span class="badge status-warning">Restart required</span>` : ""}
      </div>
      <div class="employee-config-tabs">
        ${EMPLOYEE_CONFIG_FILES.map((filename) => `
          <button
            class="secondary-button ${selected.name === filename ? "is-selected" : ""}"
            type="button"
            data-employee-config-file="${html(filename)}"
          >${html(filename)}</button>
        `).join("")}
      </div>
      <div class="employee-config-toolbar">
        <strong>${html(selected.name)}</strong>
        <span>${isDirty ? "Unsaved changes" : "Saved"}</span>
        ${employeeConfigState.isEditing ? `
          <button class="secondary-button" type="button" data-employee-config-cancel="true">Cancel</button>
          <button class="primary-button" type="button" data-employee-config-save="true" ${isDirty ? "" : "disabled"}>Save</button>
        ` : `
          <button class="secondary-button" type="button" data-employee-config-edit="true">Edit</button>
        `}
      </div>
      ${employeeConfigState.isEditing ? `
        <textarea class="employee-config-editor" data-employee-config-draft="true" spellcheck="false">${html(draft, "")}</textarea>
      ` : `
        <pre class="employee-config-preview">${html(selected.content, "")}</pre>
      `}
      ${renderEmployeeCronEditor(employee)}
    </div>
  `;
}

function formatCronSchedule(schedule) {
  if (!schedule) return "unknown";
  if (schedule.kind === "every" && schedule.everyMs) {
    const ms = Number(schedule.everyMs);
    if (ms % 3600000 === 0) return `every ${ms / 3600000}h`;
    if (ms % 60000 === 0) return `every ${ms / 60000}m`;
    if (ms % 1000 === 0) return `every ${ms / 1000}s`;
    return `every ${ms}ms`;
  }
  if (schedule.kind === "cron") {
    return `cron ${text(schedule.expr, "")}${schedule.tz ? ` (${schedule.tz})` : ""}`;
  }
  if (schedule.kind === "at") {
    return `at ${text(schedule.atMs, "")}`;
  }
  return text(schedule.kind, "unknown");
}

function renderEmployeeCronEditor(employee) {
  const draft = employeeConfigState.cronDraft;
  const jobs = employeeConfigState.cronJobs || [];
  return `
    <div class="agent-section employee-cron-panel" data-employee-ops-section="cron">
      <div class="agent-section-title">Employee Cron</div>
      ${employeeConfigState.cronError ? `<div class="empty-state">${html(employeeConfigState.cronError)}</div>` : ""}
      <div class="employee-cron-list">
        ${jobs.length ? jobs.map((job) => `
          <div class="employee-cron-row">
            <div>
              <strong>${html(job.name)}</strong>
              <span>${html(formatCronSchedule(job.schedule))} · ${job.enabled ? "enabled" : "disabled"}</span>
              <span>${html(job.payload?.message, "")}</span>
            </div>
            <div class="employee-cron-actions">
              <button class="secondary-button" type="button" data-employee-cron-edit="${html(job.id)}">Modify</button>
              <button class="danger-button" type="button" data-employee-cron-delete="${html(job.id)}">Delete</button>
            </div>
          </div>
        `).join("") : `<div class="empty-state">No employee-owned cron jobs.</div>`}
      </div>
      <div class="employee-cron-form">
        <input data-employee-cron-name="true" type="text" value="${html(draft.name, "")}" placeholder="Cron name" aria-label="Cron name">
        <select data-employee-cron-kind="true" aria-label="Cron schedule type">
          <option value="every" ${draft.kind === "every" ? "selected" : ""}>Every</option>
          <option value="cron" ${draft.kind === "cron" ? "selected" : ""}>Cron</option>
        </select>
        ${draft.kind === "cron" ? `
          <input data-employee-cron-expr="true" type="text" value="${html(draft.expr, "")}" placeholder="0 9 * * *" aria-label="Cron expression">
          <input data-employee-cron-tz="true" type="text" value="${html(draft.tz, "")}" placeholder="Asia/Shanghai" aria-label="Cron timezone">
        ` : `
          <input data-employee-cron-every-ms="true" type="number" min="1000" step="1000" value="${html(draft.everyMs, "3600000")}" aria-label="Every milliseconds">
        `}
        <textarea data-employee-cron-message="true" placeholder="Scheduled instruction" aria-label="Cron message">${html(draft.message, "")}</textarea>
        <label class="employee-cron-checkbox"><input data-employee-cron-enabled="true" type="checkbox" ${draft.enabled ? "checked" : ""}> Enabled</label>
        <button class="primary-button" type="button" data-employee-cron-save="true">${draft.id ? "Save Cron" : "Create Cron"}</button>
        ${draft.id ? `<button class="secondary-button" type="button" data-employee-cron-new="true">New Cron</button>` : ""}
      </div>
    </div>
  `;
}

function formatTranscriptTimestamp(value) {
  const normalized = text(value, "").trim();
  if (!normalized) return "";
  let parsed = null;
  if (/^\d+(\.\d+)?$/.test(normalized)) {
    const numeric = Number(normalized);
    if (Number.isFinite(numeric)) {
      parsed = new Date(numeric > 1000000000000 ? numeric : numeric * 1000);
    }
  }
  if (!parsed) {
    parsed = new Date(normalized);
  }
  if (Number.isNaN(parsed.getTime())) return normalized;
  const pad = (part) => String(part).padStart(2, "0");
  return `${parsed.getFullYear()}-${pad(parsed.getMonth() + 1)}-${pad(parsed.getDate())} ${pad(parsed.getHours())}:${pad(parsed.getMinutes())}:${pad(parsed.getSeconds())}`;
}

function renderTranscriptItem(item) {
  const role = text(item.role, "system");
  const roleClass = role.replace(/[^a-z_-]/gi, "_").toLowerCase();
  const summary = text(item.summary || item.content || role, role);
  const detail = text(item.detail || item.content || summary, "");
  const rawTimestamp = text(item.timestamp, "");
  const timestamp = formatTranscriptTimestamp(rawTimestamp);
  const hasDetail = detail && detail !== summary;
  return `
    <article class="transcript-item transcript-role-${roleClass}">
      <div class="transcript-item-head">
        <span class="transcript-role-label">${html(role)}</span>
        ${timestamp ? `<span class="transcript-time" title="${html(rawTimestamp)}">${html(timestamp)}</span>` : ""}
      </div>
      <div class="transcript-summary">${html(summary)}</div>
      ${hasDetail ? `
        <details class="transcript-detail">
          <summary>Details</summary>
          <pre>${html(detail)}</pre>
        </details>
      ` : ""}
    </article>
  `;
}

function renderTranscriptModal() {
  const transcript = adminState.transcript || defaultTranscriptState();
  const payload = transcript.payload || {};
  const items = Array.isArray(payload.items) ? payload.items : [];
  const warning = transcript.error || payload.warning || "";
  const body = transcript.isLoading
    ? `<div class="empty-state transcript-empty">Loading chat history...</div>`
    : transcript.error
      ? `<div class="empty-state transcript-empty">${html(transcript.error)}</div>`
      : items.length === 0
        ? `<div class="empty-state transcript-empty">${html(warning || "No chat history available.")}</div>`
        : `<div class="transcript-timeline">${items.map(renderTranscriptItem).join("")}</div>`;
  return `
    <div class="modal-backdrop transcript-modal-backdrop">
      <div class="transcript-modal-shell">
        <section class="employee-modal transcript-modal" role="dialog" aria-modal="true" aria-labelledby="transcript-modal-title">
          <div class="panel-head">
            <div>
              <h3 id="transcript-modal-title">${html(transcript.title || "Chat History")}</h3>
              <div class="panel-meta">
                ${html(payload.sessionId || transcript.subtitle || "no session")}
                ${payload.source ? ` · ${html(payload.source)}` : ""}
              </div>
            </div>
          </div>
          ${warning && !transcript.error && items.length > 0 ? `<div class="transcript-warning">${html(warning)}</div>` : ""}
          ${body}
        </section>
        <button class="icon-button transcript-modal-close" type="button" data-modal-close="true" aria-label="Close chat history dialog">×</button>
      </div>
    </div>
  `;
}

function renderSkillContentModal() {
  const modal = skillState.contentModal;
  const skill = modal.skill || skillState.localSkills.find((item) => item.id === modal.skillId) || {};
  const title = text(skill.name, modal.skillId || "Skill");
  const isSaveBusy = isBusy(`save-skill-content:${modal.skillId}`);
  const canSave = modal.isEditing && modal.isDirty && !modal.isLoading && !isSaveBusy;
  const canImportPreview = modal.isSearchPreview && !modal.isLoading && modal.skill;
  const readOnlyPreview = Boolean(modal.isReadOnlyPreview);
  const importPreviewBusy = isBusy(`import-search-skill:${modal.skillId}`);
  const body = modal.isLoading
    ? `<div class="empty-state">Loading skill content...</div>`
    : (modal.error || modal.markdownStatus === "error")
      ? `
        <div class="empty-state">
          ${html(modal.error || modal.markdownError || "Failed to load full SKILL.md.")}
          ${skill.source_url ? `<div class="panel-meta">${html(skill.source_url)}</div>` : ""}
          ${skill.description ? `<p class="employee-summary">${html(skill.description)}</p>` : ""}
        </div>
      `
      : modal.isEditing
        ? `
          <textarea
            id="skill-content-editor"
            class="skill-content-editor"
            data-skill-content-editor="true"
            spellcheck="false"
          >${html(modal.draft, "")}</textarea>
        `
        : `<pre class="skill-content-preview">${html(modal.markdown || "No SKILL.md content available.")}</pre>`;
  const skillContentBusy = isSaveBusy || importPreviewBusy;
  return `
    <div class="modal-backdrop skill-content-modal-backdrop">
      <div class="skill-content-modal-shell">
        <section class="employee-modal skill-content-modal" role="dialog" aria-modal="true" aria-labelledby="skill-content-title">
          <div class="panel-head">
            <div>
              <h3 id="skill-content-title">${html(title)}</h3>
              <div class="panel-meta">
                ${html(modal.contentSource || skill.source || "skill")}
                ${modal.syncedEmployees ? ` · synced ${html(modal.syncedEmployees)} employees` : ""}
              </div>
            </div>
            ${(modal.isSearchPreview || readOnlyPreview) ? "" : `
              <div class="skill-content-toolbar">
                <button
                  class="icon-button"
                  type="button"
                  data-skill-content-edit="true"
                  aria-label="Edit skill markdown"
                  title="Edit"
                  ${modal.isLoading || modal.isEditing ? "disabled" : ""}
                >✎</button>
                <button
                  class="icon-button"
                  type="button"
                  data-skill-content-save="true"
                  aria-label="Save skill markdown"
                  title="Save"
                  ${canSave ? "" : "disabled"}
                >💾</button>
              </div>
            `}
          </div>
          ${body}
          ${canImportPreview ? `
            <div class="modal-actions">
              <button
                class="primary-button"
                type="button"
                data-import-search-skill="true"
                ${importPreviewBusy ? "disabled" : ""}
              >${importPreviewBusy ? "Importing..." : "Import This Skill"}</button>
            </div>
          ` : ""}
        </section>
        <button class="icon-button skill-content-modal-close" type="button" data-modal-close="true" aria-label="Close skill content dialog" ${skillContentBusy ? "disabled" : ""}>×</button>
      </div>
    </div>
    ${skillContentBusy ? renderBusyMask() : ""}
  `;
}

function renderCreateWizardStepper() {
  const currentStep = employeeState.createWizardStep || "template";
  return `
    <div class="create-wizard-stepper" role="tablist" aria-label="Create employee wizard">
      ${CREATE_WIZARD_STEPS.map((step, index) => {
        const isActive = step === currentStep;
        const isComplete = employeeState.completedCreateWizardSteps.includes(step);
        const canEnter = canEnterCreateWizardStep(step);
        return `
          <button
            class="create-wizard-step ${isActive ? "is-active" : ""} ${isComplete ? "is-complete" : ""}"
            type="button"
            data-create-wizard-step="${html(step)}"
            data-create-wizard-go="${html(step)}"
            role="tab"
            aria-selected="${isActive ? "true" : "false"}"
            ${canEnter ? "" : "disabled"}
          >
            <span class="create-wizard-step-index">${index + 1}</span>
            <span class="create-wizard-step-label">${t(CREATE_WIZARD_STEP_LABELS[step])}</span>
          </button>
        `;
      }).join("")}
    </div>
  `;
}

function renderCreateWizardTemplateStep({ allTemplates, selectedTemplate, isCustomRoleSelected, cookBusy }) {
  return `
    <section class="create-wizard-body" data-create-wizard-panel="template">
      <div class="create-wizard-intro">
        <strong>${t("modal.create.wizard.template")}</strong>
        <span>${t("modal.create.wizard.template_copy")}</span>
      </div>
      <div class="template-grid">
        ${allTemplates.map((template) => `
          <div class="template-card-shell">
            <button
              class="template-card ${template.id === selectedTemplate.id ? "is-selected" : ""} ${template.isCustomComposer ? "is-custom-composer" : ""}"
              type="button"
              data-template-id="${html(template.id)}"
            >
              <span class="template-title">${html(template.role)}</span>
              <span class="template-meta">${html(template.companyStyle)}</span>
            </button>
            ${allTemplates.length > 1 && template.id !== CUSTOM_ROLE_TEMPLATE_ID ? `
              <button
                class="template-delete-button"
                type="button"
                data-delete-template-id="${html(template.id)}"
                aria-label="${html(t("modal.create.delete_template"))}"
                title="${html(t("modal.create.delete_template"))}"
              >×</button>
            ` : ""}
          </div>
        `).join("")}
      </div>
      ${isCustomRoleSelected ? `
        <div class="custom-role-panel">
          <label class="custom-role-input">
            <span>${t("modal.create.custom_prompt")}</span>
            <input
              name="custom_role_prompt"
              type="text"
              value="${html(employeeState.customRolePrompt, "")}"
              placeholder="${html(t("modal.create.custom_placeholder"))}"
              autocomplete="off"
            />
          </label>
          <div class="custom-role-actions">
            <button class="primary-button" type="button" data-cook-template="true" ${cookBusy ? "disabled" : ""}>
              ${cookBusy ? t("button.cooking") : t("button.cook")}
            </button>
            <span class="field-note">${t("modal.create.custom_note")}</span>
          </div>
        </div>
      ` : ""}
    </section>
  `;
}

function renderCreateWizardProfileStep({ draft, avatarOptions }) {
  return `
    <section class="create-wizard-body" data-create-wizard-panel="profile">
      <div class="create-wizard-intro">
        <strong>${t("modal.create.wizard.profile")}</strong>
        <span>${t("modal.create.wizard.profile_copy")}</span>
      </div>
      <div class="form-grid">
        <label>
          <span>${t("modal.create.employee_name")}</span>
          <input name="name" type="text" value="${html(draft.name, "")}" autocomplete="off" />
        </label>
        <label>
          <span>${t("modal.create.role")}</span>
          <input name="role" type="text" value="${html(draft.role, "")}" autocomplete="off" />
        </label>
        <label>
          <span>agent_type</span>
          <select name="agent_type">
            ${["openclaw", "nanobot", "hermes"].map((agentType) => `
              <option value="${agentType}" ${agentType === draft.agent_type ? "selected" : ""}>${agentType}</option>
            `).join("")}
          </select>
        </label>
        <label class="form-span-3">
          <span>${t("modal.create.avatar")}</span>
          <div class="avatar-picker" role="radiogroup" aria-label="${html(t("modal.create.avatar_aria"))}">
            ${avatarOptions}
          </div>
          <span class="field-note">${t("modal.create.avatar_note")}</span>
        </label>
        <label class="form-span-3">
          <span>${t("modal.create.system_prompt")}</span>
          <textarea name="system_prompt" rows="7">${html(draft.system_prompt, "")}</textarea>
        </label>
      </div>
    </section>
  `;
}

function renderCreateWizardSkillsStep({ localSkillCards }) {
  return `
    <section class="create-wizard-body" data-create-wizard-panel="skills">
      <div class="create-wizard-intro">
        <strong>${t("modal.create.wizard.skills")}</strong>
        <span>${t("modal.create.wizard.skills_copy")}</span>
      </div>
      <label class="create-wizard-block">
        <span>${t("modal.create.local_skills")}</span>
        <div class="skill-picker" role="group" aria-label="${html(t("modal.create.skills_aria"))}">
          ${localSkillCards}
        </div>
        <span class="field-note">
          ${skillState.localSkills.length
            ? t("modal.create.local_skills_required", { count: employeeState.selectedSkillIds.length })
            : t("modal.create.local_skills_empty")}
          ${employeeState.skillRecommendation.isLoading ? ` ${t("modal.create.local_skills_loading")}` : ""}
          ${employeeState.skillRecommendation.warning ? ` ${t("modal.create.local_skills_warning", { value: html(employeeState.skillRecommendation.warning) })}` : ""}
          ${employeeState.skillRecommendation.reason ? ` ${html(employeeState.skillRecommendation.reason)}` : ""}
        </span>
      </label>
    </section>
  `;
}

function selectedCreateWizardSkillNames() {
  const selectedIds = selectedEmployeeSkillIdsForPayload();
  return selectedIds.map((skillId) => (
    skillState.localSkills.find((skill) => skill.id === skillId)?.name || skillId
  ));
}

function renderCreateWizardReviewStep({ selectedTemplate, draft, selectedAvatarId }) {
  const avatar = getAvatarPreset(selectedAvatarId);
  const skillNames = selectedCreateWizardSkillNames();
  const recommendation = employeeState.skillRecommendation || defaultSkillRecommendation();
  const recommendationText = [
    recommendation.warning ? t("modal.create.local_skills_warning", { value: recommendation.warning }) : "",
    recommendation.reason,
    employeeSkillSourceSummary(selectedEmployeeSkillIdsForPayload()),
  ].filter(Boolean).join(" ");
  return `
    <section class="create-wizard-body" data-create-wizard-panel="review">
      <div class="create-wizard-intro">
        <strong>${t("modal.create.review_title")}</strong>
        <span>${t("modal.create.wizard.review_copy")}</span>
      </div>
      <dl class="employee-review-grid">
        <div><dt>${t("modal.create.review_template")}</dt><dd>${html(selectedTemplate.role)}</dd></div>
        <div><dt>${t("modal.create.employee_name")}</dt><dd>${html(draft.name, "n/a")}</dd></div>
        <div><dt>${t("modal.create.role")}</dt><dd>${html(draft.role, "n/a")}</dd></div>
        <div><dt>${t("modal.create.review_agent_type")}</dt><dd>${html(draft.agent_type, "openclaw")}</dd></div>
        <div><dt>${t("modal.create.review_avatar")}</dt><dd>${html(avatar?.label || selectedAvatarId || "n/a")}</dd></div>
        <div><dt>${t("modal.create.review_skills")}</dt><dd>${skillNames.length ? renderTags(skillNames) : t("modal.create.review_no_skills")}</dd></div>
        <div class="employee-review-wide"><dt>${t("modal.create.system_prompt")}</dt><dd>${html(draft.system_prompt, "n/a")}</dd></div>
        <div class="employee-review-wide"><dt>${t("modal.create.review_recommendation")}</dt><dd>${html(recommendationText || "n/a")}</dd></div>
      </dl>
    </section>
  `;
}

function renderCreateWizardBody(context) {
  switch (employeeState.createWizardStep || "template") {
    case "profile":
      return renderCreateWizardProfileStep(context);
    case "skills":
      return renderCreateWizardSkillsStep(context);
    case "review":
      return renderCreateWizardReviewStep(context);
    case "template":
    default:
      return renderCreateWizardTemplateStep(context);
  }
}

function renderCreateWizardFooter() {
  const currentStep = employeeState.createWizardStep || "template";
  const currentIndex = createWizardStepIndex(currentStep);
  const isReview = currentStep === "review";
  const busyAction = adminState.busyAction;
  return `
    <div class="create-wizard-footer">
      ${employeeState.createWizardError ? `<div class="create-wizard-error" data-create-wizard-error="true">${html(employeeState.createWizardError)}</div>` : ""}
      <div class="modal-actions">
        <button class="secondary-button" type="button" data-modal-close="true" ${busyAction ? "disabled" : ""}>${t("button.cancel")}</button>
        ${currentIndex > 0 ? `<button class="secondary-button" type="button" data-create-wizard-back="true" ${busyAction ? "disabled" : ""}>${t("button.back")}</button>` : ""}
        ${isReview
          ? `<button class="primary-button" type="submit" ${busyAction ? "disabled" : ""}>${busyAction?.key === "create-employee" ? t("button.creating") : t("button.create_employee")}</button>`
          : `<button class="primary-button" type="button" data-create-wizard-next="true" ${busyAction ? "disabled" : ""}>${t("button.next")}</button>`}
      </div>
    </div>
  `;
}

function renderEmployeeModal() {
  const root = document.getElementById("employee-modal-root");
  if (!root) return;
  const viewState = captureEmployeeModalViewState(root);
  const confirmAction = adminState.confirmAction;
  const busyAction = adminState.busyAction;
  const transcript = adminState.transcript || defaultTranscriptState();
  const skillContentModal = skillState.contentModal || {};
  if (!employeeState.isCreateOpen && !confirmAction && !transcript.isOpen && !skillContentModal.isOpen && !employeeExportState.isOpen && !caseState.isDetailOpen) {
    root.innerHTML = busyAction ? renderBusyMask() : "";
    return;
  }
  if (confirmAction) {
    root.innerHTML = `
      <div class="modal-backdrop">
        <section class="employee-modal confirm-modal" role="dialog" aria-modal="true" aria-labelledby="confirm-modal-title">
          <div class="panel-head">
            <div>
              <h3 id="confirm-modal-title">${html(confirmAction.title)}</h3>
              <div class="panel-meta">${html(confirmAction.subtitle || "This action cannot be undone.")}</div>
            </div>
            <button class="icon-button" type="button" data-modal-close="true" aria-label="Close confirmation dialog" ${busyAction ? "disabled" : ""}>×</button>
          </div>
          <p class="employee-summary">${html(confirmAction.message)}</p>
          <div class="modal-actions">
            <button class="secondary-button" type="button" data-modal-close="true" ${busyAction ? "disabled" : ""}>Cancel</button>
            ${confirmAction.secondaryConfirmLabel ? `
              <button class="secondary-button" type="button" data-confirm-secondary-action="true" ${busyAction ? "disabled" : ""}>${html(confirmAction.secondaryConfirmLabel)}</button>
            ` : ""}
            <button class="danger-button" type="button" data-confirm-action="true" ${busyAction ? "disabled" : ""}>${busyAction ? html(busyAction.label, "Working...") : html(confirmAction.confirmLabel || "Confirm")}</button>
          </div>
        </section>
      </div>
      ${busyAction ? renderBusyMask() : ""}
    `;
    return;
  }
  if (transcript.isOpen) {
    root.innerHTML = renderTranscriptModal();
    return;
  }
  if (skillContentModal.isOpen) {
    root.innerHTML = renderSkillContentModal();
    return;
  }
  if (employeeExportState.isOpen) {
    root.innerHTML = renderEmployeeExportModal();
    return;
  }
  if (caseState.isDetailOpen) {
    root.innerHTML = renderCaseDetailModal();
    requestCaseDetailViewportSync();
    return;
  }
  const selectedTemplate = selectedEmployeeTemplate();
  const draft = ensureCreateEmployeeDraft();
  const allTemplates = employeeTemplates();
  const isCustomRoleSelected = selectedTemplate.id === CUSTOM_ROLE_TEMPLATE_ID;
  const cookBusy = isBusy("cook-custom-template");
  const selectedAvatarId = getAvatarPreset(employeeState.selectedAvatarId)?.id || EMPLOYEE_AVATARS[0]?.id || "";
  const avatarOptions = EMPLOYEE_AVATARS.map((avatar) => `
    <button
      class="avatar-option ${avatar.id === selectedAvatarId ? "is-selected" : ""}"
      type="button"
      data-avatar-id="${html(avatar.id)}"
      aria-pressed="${avatar.id === selectedAvatarId ? "true" : "false"}"
      title="${html(avatar.label)}"
    >
      <span class="avatar-option-media">
        <img src="${avatar.src}" alt="${html(avatar.label)}" />
      </span>
      <span class="avatar-option-label">${html(avatar.label)}</span>
    </button>
  `).join("");
  const localSkillCards = skillState.localSkills.length === 0
    ? `<div class="skill-option-empty">${t("modal.create.skill_empty")}</div>`
    : skillState.localSkills.map((skill) => {
      const isSelected = employeeState.selectedSkillIds.includes(skill.id);
      const isRequired = isRequiredLocalSkill(skill);
      const isRecommended = employeeState.recommendedSkillIds.includes(skill.id);
      const description = text(skill.description, t("skills.source_empty_description"));
      const isExpanded = employeeState.expandedSkillIds.includes(skill.id);
      const canExpand = description.length > 120;
      return `
        <article
          class="skill-option ${isSelected ? "is-selected" : ""} ${isRequired ? "is-required" : ""}"
          data-local-skill-id="${html(skill.id)}"
          role="button"
          tabindex="0"
          aria-pressed="${isSelected ? "true" : "false"}"
          ${isRequired ? 'aria-disabled="true"' : ""}
          title="${html(skill.name)}"
        >
          <span class="skill-option-top">
            <strong class="skill-option-name">${html(skill.name)}</strong>
            <span class="skill-option-state">${isRequired ? t("skills.required") : (isRecommended ? t("skills.recommended") : (isSelected ? t("skills.selected") : t("skills.optional")))}</span>
          </span>
          <span class="panel-meta">${html(skill.author || "community")} · ${html(skill.version || t("skills.source_unknown_version"))}</span>
          <span class="skill-summary skill-option-summary skill-option-description ${isExpanded ? "is-expanded" : "is-collapsed"}">${html(description)}</span>
          ${canExpand ? `
            <button
              class="skill-expand-button"
              type="button"
              data-skill-expand-id="${html(skill.id)}"
              aria-expanded="${isExpanded ? "true" : "false"}"
            >${isExpanded ? t("button.collapse") : t("skills.expand")}</button>
          ` : ""}
          <span class="tag-cloud">
            <span class="tag">${html(skill.source)}</span>
            <span class="tag tool-tag">${html(skill.external_id || t("skills.source_no_external_id"))}</span>
          </span>
        </article>
      `;
    }).join("");
  const wizardContext = {
    allTemplates,
    selectedTemplate,
    isCustomRoleSelected,
    cookBusy,
    draft,
    selectedAvatarId,
    avatarOptions,
    localSkillCards,
  };
  root.innerHTML = `
    <div class="modal-backdrop">
      <section class="employee-modal" role="dialog" aria-modal="true" aria-labelledby="employee-modal-title">
        <div class="panel-head">
          <div>
            <h3 id="employee-modal-title">${t("modal.create.title")}</h3>
            <div class="panel-meta">${t("modal.create.copy")}</div>
          </div>
          <button class="icon-button" type="button" data-modal-close="true" aria-label="${html(t("button.close_create_modal"))}">×</button>
        </div>
        <form id="employee-create-form" class="employee-form">
          ${renderCreateWizardStepper()}
          ${renderCreateWizardBody(wizardContext)}
          ${renderCreateWizardFooter()}
        </form>
      </section>
    </div>
    ${busyAction ? renderBusyMask() : ""}
  `;
  restoreEmployeeModalViewState(root, viewState);
}

function renderSkillCatalog() {
  renderSkillOpsPanel();
  renderSoulLibraryPanel();
  renderLocalSkillList();
  renderSkillSearchPanel();
  renderResourceHubTabs();
  renderAlertStrip();
  renderActionCenter();
  requestNavSectionSync();
}

function normalizeSkillGovernance(report) {
  if (!report || typeof report !== "object") return null;
  return {
    generatedAt: text(report.generatedAt, ""),
    summary: report.summary && typeof report.summary === "object" ? report.summary : {},
    issues: Array.isArray(report.issues) ? report.issues.map((issue) => ({
      ...issue,
      id: text(issue?.id, ""),
      type: text(issue?.type, ""),
      title: text(issue?.title, ""),
      body: text(issue?.body, ""),
      severity: text(issue?.severity, "info"),
      ignored: issue?.ignored === true,
      skillIds: Array.isArray(issue?.skillIds) ? issue.skillIds.map((item) => text(item, "")).filter(Boolean) : [],
      employeeIds: Array.isArray(issue?.employeeIds) ? issue.employeeIds.map((item) => text(item, "")).filter(Boolean) : [],
      skills: Array.isArray(issue?.skills) ? issue.skills.map(normalizeLocalSkill) : [],
      employees: Array.isArray(issue?.employees) ? issue.employees : [],
    })).filter((issue) => issue.id) : [],
    opportunities: Array.isArray(report.opportunities) ? report.opportunities.map((item) => ({
      ...item,
      id: text(item?.id, ""),
      type: text(item?.type, ""),
      source: text(item?.source, ""),
      title: text(item?.title, ""),
      body: text(item?.body, ""),
      query: text(item?.query, ""),
      candidateCount: item?.candidateCount,
      candidates: Array.isArray(item?.candidates) ? item.candidates : [],
    })).filter((item) => item.id) : [],
    warnings: Array.isArray(report.warnings) ? report.warnings.map((item) => text(item, "")).filter(Boolean) : [],
    auditLog: Array.isArray(report.auditLog) ? report.auditLog.filter((item) => item && typeof item === "object") : [],
  };
}

function skillOpsSelectedIssues() {
  const report = skillOpsState.report;
  if (!report) return [];
  return report.issues.filter((issue) => skillOpsState.selectedIssueIds.includes(issue.id));
}

function skillOpsIssueDisplayGroups(issues) {
  const normalized = Array.isArray(issues) ? issues : [];
  const activeIssues = normalized.filter((issue) => issue.ignored !== true);
  const ignoredIssues = normalized.filter((issue) => issue.ignored === true);
  const foldableIssues = [
    ...activeIssues.slice(SKILL_OPS_DEFAULT_VISIBLE_ACTIVE_ISSUES),
    ...ignoredIssues,
  ];
  return {
    displayedIssues: skillOpsState.isIssueListExpanded
      ? normalized
      : activeIssues.slice(0, SKILL_OPS_DEFAULT_VISIBLE_ACTIVE_ISSUES),
    foldableIssues,
    foldedIgnoredCount: foldableIssues.filter((issue) => issue.ignored === true).length,
  };
}

function skillOpsVisibleIssueIds() {
  return skillOpsIssueDisplayGroups(skillOpsState.report?.issues || [])
    .displayedIssues
    .map((issue) => issue.id)
    .filter(Boolean);
}

function skillOpsActionEnabled(action) {
  const selected = skillOpsSelectedIssues();
  if (action === "merge_duplicates") {
    return selected.some((issue) => ["duplicate_exact", "duplicate_name"].includes(issue.type));
  }
  if (action === "delete_orphans") {
    return selected.some((issue) => issue.type === "orphan_skill");
  }
  if (action === "repair_employee_bindings") {
    return selected.some((issue) => issue.type === "stale_employee_binding");
  }
  return false;
}

function skillOpsIssueIdsForAction(action) {
  const allowed = {
    merge_duplicates: ["duplicate_exact", "duplicate_name"],
    delete_orphans: ["orphan_skill"],
    repair_employee_bindings: ["stale_employee_binding"],
  }[action] || [];
  return skillOpsSelectedIssues()
    .filter((issue) => allowed.includes(issue.type))
    .map((issue) => issue.id);
}

function renderSkillOpsMetric(label, value) {
  return `
    <span class="skill-ops-metric">
      <strong>${html(value, "0")}</strong>
      <span>${html(label)}</span>
    </span>
  `;
}

function renderSkillOpsIssue(issue) {
  const checked = skillOpsState.selectedIssueIds.includes(issue.id);
  const title = issue.title || issue.type;
  const affected = [
    ...issue.skills.map((skill) => skill.name || skill.id),
    ...issue.employees.map((employee) => employee.name || employee.id),
  ].filter(Boolean).slice(0, 4);
  return `
    <article class="skill-ops-issue ${issue.ignored ? "is-ignored" : ""}">
      <label class="batch-checkbox">
        <input type="checkbox" data-skill-ops-issue="${html(issue.id)}" ${checked ? "checked" : ""}>
        <span class="visually-hidden">${html(`${t("button.select")} ${title}`)}</span>
      </label>
      <div class="skill-ops-issue-body">
        <div class="skill-ops-issue-top">
          <strong>${html(title)}</strong>
          <span class="tag">${html(issue.type)}</span>
          ${issue.ignored ? `<span class="tag">${t("skill.ops.ignored")}</span>` : ""}
        </div>
        <p>${html(issue.body)}</p>
        ${affected.length ? `<div class="tag-cloud">${affected.map((item) => `<span class="tag">${html(item)}</span>`).join("")}</div>` : ""}
      </div>
      <button
        class="secondary-button skill-ops-inline-action"
        type="button"
        data-skill-ops-ignore="${html(issue.id)}"
        data-skill-ops-ignore-value="${issue.ignored ? "false" : "true"}"
      >${issue.ignored ? t("skill.ops.unignore") : t("skill.ops.ignore")}</button>
    </article>
  `;
}

function renderSkillOpsOpportunity(item) {
  const count = Number.isFinite(Number(item.candidateCount)) ? ` · ${Number(item.candidateCount)}` : "";
  const label = item.type === "clawhub_query"
    ? t("skill.ops.search_clawhub")
    : item.type === "persona_source"
      ? t("skill.ops.browse_personas")
      : t("skill.ops.import_web");
  return `
    <article class="skill-ops-opportunity">
      <span>
        <strong>${html(item.title || item.source)}</strong>
        <span>${html(item.body)}${html(count)}</span>
      </span>
      <button class="secondary-button" type="button" data-skill-ops-opportunity="${html(item.id)}">${label}</button>
    </article>
  `;
}

function renderSkillOpsPreview() {
  const preview = skillOpsState.preview;
  if (!preview) return "";
  const plan = preview.plan || {};
  return `
    <section class="skill-ops-preview">
      <div>
        <strong>${t("skill.ops.preview_title")}</strong>
        <p>${t("skill.ops.preview_body", {
          skills: html(plan.skillCount ?? (plan.skillsDeleted || []).length, "0"),
          employees: html(plan.employeeCount ?? (plan.employeesUpdated || []).length, "0"),
        })}</p>
      </div>
      <div class="skill-ops-actions">
        <button class="secondary-button" type="button" data-skill-ops-cancel-preview="true">${t("skill.ops.cancel")}</button>
        <button class="danger-button" type="button" data-skill-ops-confirm="true">${t("skill.ops.confirm")}</button>
      </div>
    </section>
  `;
}

function renderSkillOpsPanel() {
  const root = document.getElementById("skill-ops-panel");
  if (!root) return;
  const report = skillOpsState.report;
  const summary = report?.summary || {};
  const allIssues = report?.issues || [];
  const issueGroups = skillOpsIssueDisplayGroups(allIssues);
  const visibleIssues = issueGroups.displayedIssues;
  const foldableCount = issueGroups.foldableIssues.length;
  const foldableIgnoredCount = issueGroups.foldedIgnoredCount;
  const visibleIssueIds = visibleIssues.map((issue) => issue.id).filter(Boolean);
  const selectedCount = skillOpsState.selectedIssueIds.length;
  const allIssuesSelected = visibleIssueIds.length > 0 && visibleIssueIds.every((issueId) => skillOpsState.selectedIssueIds.includes(issueId));
  const someIssuesSelected = visibleIssueIds.some((issueId) => skillOpsState.selectedIssueIds.includes(issueId));
  const busy = skillOpsState.isLoading || skillOpsState.isScanning || skillOpsState.isRemoteScanning;
  root.innerHTML = `
    <div class="skill-ops-head">
      <div>
        <div class="agent-section-title">${t("skill.ops.title")}</div>
        <div class="panel-meta">${t("skill.ops.copy")}</div>
      </div>
      <div class="skill-ops-actions">
        <button class="secondary-button" type="button" data-skill-ops-scan="true" ${busy ? "disabled" : ""}>
          ${skillOpsState.isScanning ? t("button.loading") : t("skill.ops.scan")}
        </button>
        <button class="primary-button" type="button" data-skill-ops-remote="true" ${busy ? "disabled" : ""}>
          ${skillOpsState.isRemoteScanning ? t("button.loading") : t("skill.ops.remote_scan")}
        </button>
      </div>
    </div>
    ${skillOpsState.error ? `<div class="skill-ops-error">${t("skill.ops.error", { value: html(skillOpsState.error) })}</div>` : ""}
    ${skillOpsState.isLoading && !report ? `<div class="empty-state">${t("skill.ops.loading")}</div>` : ""}
    ${report ? `
      <div class="skill-ops-summary">
        <div class="skill-ops-metrics">
          ${renderSkillOpsMetric(t("skills.local_catalog"), summary.businessSkillCount ?? 0)}
          ${renderSkillOpsMetric(t("skill.ops.coverage", { count: html(summary.employeeCoveragePercent ?? 0) }), `${summary.employeesWithBusinessSkills ?? 0}/${summary.employeeCount ?? 0}`)}
          ${renderSkillOpsMetric(t("skill.ops.issues", { count: allIssues.length }), allIssues.length)}
          ${renderSkillOpsMetric(t("skill.ops.ignored"), summary.ignoredIssueCount ?? 0)}
        </div>
        <span class="panel-meta">${formatUtcDate(report.generatedAt) || html(report.generatedAt)}</span>
      </div>
      ${report.warnings.length ? report.warnings.map((warning) => `<div class="skill-ops-warning">${t("skill.ops.warning", { value: html(warning) })}</div>`).join("") : ""}
      <div class="skill-ops-grid">
        <section>
          <div class="skill-ops-section-head">
            <strong>${t("skill.ops.issues", { count: allIssues.length })}</strong>
            <span class="panel-meta">${t("skill.ops.selected", { count: selectedCount })}</span>
          </div>
          <div class="skill-ops-actions skill-ops-bulk-actions">
            <label class="batch-checkbox skill-ops-select-all">
              <input
                type="checkbox"
                data-skill-ops-select-all="true"
                ${allIssuesSelected ? "checked" : ""}
                ${visibleIssueIds.length ? "" : "disabled"}
              >
              <span>${t("skill.ops.select_all")}</span>
            </label>
            <button class="secondary-button" type="button" data-skill-ops-ignore-selected="true" ${selectedCount ? "" : "disabled"}>${t("skill.ops.ignore_selected")}</button>
            <button class="secondary-button" type="button" data-skill-ops-action="merge_duplicates" ${skillOpsActionEnabled("merge_duplicates") ? "" : "disabled"}>${t("skill.ops.merge_duplicates")}</button>
            <button class="secondary-button" type="button" data-skill-ops-action="delete_orphans" ${skillOpsActionEnabled("delete_orphans") ? "" : "disabled"}>${t("skill.ops.delete_orphans")}</button>
            <button class="secondary-button" type="button" data-skill-ops-action="repair_employee_bindings" ${skillOpsActionEnabled("repair_employee_bindings") ? "" : "disabled"}>${t("skill.ops.repair_employee_bindings")}</button>
          </div>
          ${renderSkillOpsPreview()}
          <div class="skill-ops-issue-list">
            ${visibleIssues.length ? visibleIssues.map(renderSkillOpsIssue).join("") : (foldableCount ? "" : `<div class="empty-state">${t("skill.ops.empty")}</div>`)}
            ${foldableCount ? `
              <div class="skill-ops-fold-summary">
                <span>${t(skillOpsState.isIssueListExpanded ? "skill.ops.expanded_summary" : "skill.ops.collapsed_summary", {
                  count: foldableCount,
                  ignored: foldableIgnoredCount,
                })}</span>
                <button
                  class="secondary-button skill-ops-fold-toggle"
                  type="button"
                  data-skill-ops-toggle-fold="${skillOpsState.isIssueListExpanded ? "false" : "true"}"
                  aria-expanded="${skillOpsState.isIssueListExpanded ? "true" : "false"}"
                >${skillOpsState.isIssueListExpanded ? t("skill.ops.hide_collapsed") : t("skill.ops.show_collapsed")}</button>
              </div>
            ` : ""}
          </div>
        </section>
        <section>
          <div class="skill-ops-section-head">
            <strong>${t("skill.ops.opportunities")}</strong>
          </div>
          <div class="skill-ops-opportunities">
            ${(report.opportunities || []).map(renderSkillOpsOpportunity).join("")}
          </div>
          <div class="skill-ops-section-head">
            <strong>${t("skill.ops.audit")}</strong>
          </div>
          <div class="skill-ops-audit">
            ${(report.auditLog || []).slice(-3).reverse().map((item) => `
              <div class="skill-ops-audit-item">
                <strong>${html(item.action || "action")}</strong>
                <span>${html(item.at || "")}</span>
              </div>
            `).join("") || `<div class="empty-state">${t("skill.ops.empty")}</div>`}
          </div>
        </section>
      </div>
    ` : ""}
  `;
  const selectAll = root.querySelector("[data-skill-ops-select-all]");
  if (selectAll) {
    selectAll.indeterminate = someIssuesSelected && !allIssuesSelected;
  }
}

async function loadSkillGovernance() {
  skillOpsState.isLoading = true;
  skillOpsState.error = "";
  renderSkillOpsPanel();
  try {
    const response = await fetch(SKILL_GOVERNANCE_ENDPOINT, { headers: { Accept: "application/json" } });
    if (!response.ok) {
      const error = await response.json().catch(() => ({ error: { message: `HTTP ${response.status}` } }));
      throw new Error(text(error?.error?.message, `HTTP ${response.status}`));
    }
    skillOpsState.report = normalizeSkillGovernance(await response.json());
    skillOpsState.isIssueListExpanded = false;
    skillOpsState.selectedIssueIds = skillOpsState.selectedIssueIds.filter((issueId) => (
      skillOpsState.report?.issues.some((issue) => issue.id === issueId)
    ));
  } catch (error) {
    skillOpsState.error = text(error.message, "Failed to load skill governance.");
  } finally {
    skillOpsState.isLoading = false;
    renderSkillOpsPanel();
  }
}

async function scanSkillGovernance({ includeRemote = false } = {}) {
  skillOpsState.isScanning = !includeRemote;
  skillOpsState.isRemoteScanning = includeRemote;
  skillOpsState.error = "";
  skillOpsState.preview = null;
  renderSkillOpsPanel();
  try {
    const response = await fetch(SKILL_GOVERNANCE_SCAN_ENDPOINT, {
      method: "POST",
      headers: { "Content-Type": "application/json", Accept: "application/json" },
      body: JSON.stringify({ include_remote: includeRemote }),
    });
    if (!response.ok) {
      const error = await response.json().catch(() => ({ error: { message: `HTTP ${response.status}` } }));
      throw new Error(text(error?.error?.message, `HTTP ${response.status}`));
    }
    skillOpsState.report = normalizeSkillGovernance(await response.json());
    skillOpsState.selectedIssueIds = [];
    skillOpsState.isIssueListExpanded = false;
  } catch (error) {
    skillOpsState.error = text(error.message, "Failed to scan skill governance.");
  } finally {
    skillOpsState.isScanning = false;
    skillOpsState.isRemoteScanning = false;
    renderSkillOpsPanel();
  }
}

function toggleSkillOpsIssueSelection(issueId) {
  const normalized = text(issueId, "");
  if (!normalized) return;
  if (skillOpsState.selectedIssueIds.includes(normalized)) {
    skillOpsState.selectedIssueIds = skillOpsState.selectedIssueIds.filter((item) => item !== normalized);
  } else {
    skillOpsState.selectedIssueIds = [...skillOpsState.selectedIssueIds, normalized];
  }
  skillOpsState.preview = null;
  renderSkillOpsPanel();
}

function toggleSkillOpsAllIssuesSelection(selected) {
  const issueIds = skillOpsVisibleIssueIds();
  skillOpsState.selectedIssueIds = selected ? issueIds : [];
  skillOpsState.preview = null;
  renderSkillOpsPanel();
}

function setSkillOpsIssueListExpanded(expanded) {
  skillOpsState.isIssueListExpanded = expanded === true;
  if (!skillOpsState.isIssueListExpanded) {
    const visibleIssueIds = new Set(skillOpsVisibleIssueIds());
    skillOpsState.selectedIssueIds = skillOpsState.selectedIssueIds.filter((issueId) => visibleIssueIds.has(issueId));
  }
  skillOpsState.preview = null;
  renderSkillOpsPanel();
}

async function setSkillOpsIssuesIgnored(issueIds, ignored) {
  const normalized = Array.from(new Set((issueIds || []).map((issueId) => text(issueId, "")).filter(Boolean)));
  if (!normalized.length) return;
  const response = await fetch(SKILL_GOVERNANCE_IGNORE_ENDPOINT, {
    method: "POST",
    headers: { "Content-Type": "application/json", Accept: "application/json" },
    body: JSON.stringify({ issue_ids: normalized, ignored: ignored === true }),
  });
  if (!response.ok) {
    const error = await response.json().catch(() => ({ error: { message: `HTTP ${response.status}` } }));
    throw new Error(text(error?.error?.message, `HTTP ${response.status}`));
  }
  skillOpsState.report = normalizeSkillGovernance(await response.json());
  if (ignored === true) {
    skillOpsState.selectedIssueIds = skillOpsState.selectedIssueIds.filter((issueId) => !normalized.includes(issueId));
  }
  renderSkillOpsPanel();
}

async function setSkillOpsIssueIgnored(issueId, ignored) {
  await setSkillOpsIssuesIgnored([issueId], ignored);
}

async function ignoreSelectedSkillOpsIssues() {
  const issueIds = skillOpsSelectedIssues().map((issue) => issue.id);
  if (!issueIds.length) return;
  await setSkillOpsIssuesIgnored(issueIds, true);
  skillOpsState.selectedIssueIds = [];
  skillOpsState.preview = null;
  renderSkillOpsPanel();
}

async function runSkillOpsAction(action, { dryRun = true, confirm = false } = {}) {
  const issueIds = skillOpsIssueIdsForAction(action);
  if (!issueIds.length) return;
  skillOpsState.pendingAction = action;
  const response = await fetch(SKILL_GOVERNANCE_ACTION_ENDPOINT, {
    method: "POST",
    headers: { "Content-Type": "application/json", Accept: "application/json" },
    body: JSON.stringify({
      action,
      issue_ids: issueIds,
      dry_run: dryRun,
      confirm,
    }),
  });
  if (!response.ok) {
    const error = await response.json().catch(() => ({ error: { message: `HTTP ${response.status}` } }));
    throw new Error(text(error?.error?.message, `HTTP ${response.status}`));
  }
  const payload = await response.json();
  if (dryRun) {
    skillOpsState.preview = payload;
    renderSkillOpsPanel();
    return;
  }
  skillOpsState.preview = null;
  skillOpsState.selectedIssueIds = [];
  adminState.confirmAction = null;
  await loadSkills();
  await loadEmployees();
  await loadSkillGovernance();
}

function requestSkillOpsAction(action) {
  runSkillOpsAction(action, { dryRun: true }).catch((error) => {
    skillOpsState.error = text(error.message, "Failed to preview cleanup.");
    renderSkillOpsPanel();
  });
}

function confirmSkillOpsAction() {
  const preview = skillOpsState.preview;
  if (!preview?.action) return;
  const plan = preview.plan || {};
  openConfirmAction({
    kind: "skill-ops-action",
    action: preview.action,
    title: t("skill.ops.confirm"),
    subtitle: t("skill.ops.preview_title"),
    message: t("skill.ops.preview_body", {
      skills: plan.skillCount ?? (plan.skillsDeleted || []).length,
      employees: plan.employeeCount ?? (plan.employeesUpdated || []).length,
    }),
    confirmLabel: t("skill.ops.confirm"),
  });
}

function handleSkillOpsOpportunity(opportunityId) {
  const item = skillOpsState.report?.opportunities.find((opportunity) => opportunity.id === opportunityId);
  if (!item) return;
  if (item.type === "clawhub_query") {
    skillState.searchQuery = item.query || "";
    setResourceHubTab("skills");
    renderSkillCatalog();
    if (skillState.searchQuery) {
      searchSkills().catch((error) => {
        window.alert(text(error.message, "Failed to search skills"));
      });
    }
    return;
  }
  if (item.type === "persona_source") {
    setResourceHubTab("personas");
    return;
  }
  if (item.type === "web_import") {
    skillState.isWebImportOpen = true;
    setResourceHubTab("skills");
    renderSkillCatalog();
  }
}

function renderSkillListToggle({ hiddenCount, isExpanded, dataAttribute, label }) {
  if (hiddenCount <= 0) return "";
  return `
    <button
      class="skill-list-toggle"
      type="button"
      ${dataAttribute}="true"
      aria-expanded="${isExpanded ? "true" : "false"}"
      aria-label="${html(label)}"
    >${isExpanded ? t("button.collapse") : t("button.show_more", { count: hiddenCount })}</button>
  `;
}

function importedSkillIdsFromPayload(payload) {
  if (!Array.isArray(payload)) return [];
  return payload.map((skill) => text(skill?.id, "")).filter(Boolean);
}

function formatUtcDate(value) {
  const normalized = text(value, "");
  if (!normalized) return "";
  const parsed = new Date(normalized);
  if (Number.isNaN(parsed.getTime())) {
    return "";
  }
  return parsed.toISOString().slice(0, 10);
}

function remotePersonaMetaLabel(skill) {
  const author = html(skill.author || "community");
  const updatedAt = formatUtcDate(skill.updated_at);
  if (updatedAt) {
    return `${author} · ${html(updatedAt)}`;
  }
  return `${author} · ${html(skill.version || t("skills.source_unknown_version"))}`;
}

function revealImportedLocalSkillsInList() {
  const importedIds = skillState.lastImportedSkillIds;
  if (!importedIds.length) return;
  const shouldExpand = importedIds.some((skillId) => (
    skillState.localSkills.findIndex((skill) => skill.id === skillId) >= SKILL_LIST_COLLAPSED_COUNT
  ));
  if (shouldExpand) {
    skillState.isLocalSkillListExpanded = true;
  }
  skillState.lastImportedSkillIds = [];
}

function selectedSkillSearchResultIndex() {
  return skillState.searchResults.findIndex((skill) => (
    skillState.selectedImportKeys.includes(skillIdentity(skill))
  ));
}

function findSearchSkillByIdentity(identity) {
  return skillState.searchResults.find((skill) => skillIdentity(skill) === identity) || null;
}

function findSoulBannerSkillByIdentity(identity) {
  return skillState.soulBannerResults.find((skill) => skillIdentity(skill) === identity) || null;
}

function findMbtiSbtiSkillByIdentity(identity) {
  return skillState.mbtiSbtiResults.find((skill) => skillIdentity(skill) === identity) || null;
}

function findCaseSkillByIdentity(identity) {
  const skills = Array.isArray(caseState.detail?.skills) ? caseState.detail.skills : [];
  return skills.find((skill) => skillIdentity(skill) === identity) || null;
}

function findLocalSkillByIdentity(identity) {
  return skillState.localSkills.find((skill) => skillIdentity(skill) === identity) || null;
}

function revealSelectedSkillSearchResults() {
  if (selectedSkillSearchResultIndex() >= SKILL_LIST_COLLAPSED_COUNT) {
    skillState.isSkillSearchResultsExpanded = true;
  }
}

function localSkillLabelsExpanded(skillId) {
  return skillState.expandedLocalSkillLabelIds.includes(text(skillId, ""));
}

function localSkillLabelCloudOverflows(cloud) {
  if (!(cloud instanceof HTMLElement)) return false;
  const wasExpanded = cloud.classList.contains("is-expanded");
  if (wasExpanded) {
    cloud.classList.remove("is-expanded");
    cloud.classList.add("is-collapsed");
  }
  const overflows = cloud.scrollHeight > cloud.clientHeight + 1;
  if (wasExpanded) {
    cloud.classList.remove("is-collapsed");
    cloud.classList.add("is-expanded");
  }
  return overflows;
}

function refreshLocalSkillLabelToggles() {
  const clouds = document.querySelectorAll("[data-skill-label-cloud]");
  for (const cloud of clouds) {
    const skillId = text(cloud.getAttribute("data-skill-label-cloud"), "");
    const card = cloud.closest("[data-skill-card-id]");
    const toggle = card?.querySelector("[data-skill-label-toggle]");
    if (!(toggle instanceof HTMLButtonElement)) continue;
    const isExpanded = localSkillLabelsExpanded(skillId);
    toggle.hidden = !localSkillLabelCloudOverflows(cloud);
    toggle.setAttribute("aria-expanded", isExpanded ? "true" : "false");
    toggle.textContent = isExpanded ? t("skills.collapse_labels") : t("skills.expand_labels");
  }
}

function renderCatalogSkillCard(skill) {
  const isRequired = isRequiredLocalSkill(skill);
  const deleteChecked = skillState.selectedDeleteIds.includes(skill.id);
  const labelsExpanded = localSkillLabelsExpanded(skill.id);
  const readOnlyDemo = skill.demo || skill.readOnly;
  return `
    <article class="skill-card ${isRequired ? "is-required" : ""} ${readOnlyDemo ? "is-demo" : ""}" data-skill-card-id="${html(skill.id)}" tabindex="0" role="button">
      ${(isRequired || readOnlyDemo) ? "" : `
        <label class="batch-checkbox compact-batch-checkbox skill-batch-checkbox" data-skill-delete-toggle="${html(skill.id)}">
          <input type="checkbox" ${deleteChecked ? "checked" : ""}>
          <span class="visually-hidden">${html(`${t("button.select")} ${skill.name}`)}</span>
        </label>
        <button
          class="skill-card-delete-button"
          type="button"
          data-delete-skill-id="${html(skill.id)}"
          aria-label="${html(t("button.delete_skill"))}"
          title="${html(t("button.delete_skill"))}"
        >×</button>
      `}
      <div class="skill-card-top">
        <div>
          <strong>${html(skill.name)}</strong>
          <div class="panel-meta">${html(skill.author || "community")} · ${html(skill.version || t("skills.source_unknown_version"))}</div>
        </div>
        ${readOnlyDemo ? `<span class="tag demo-badge" data-demo-badge="true">Demo</span>` : (isRequired ? `<span class="tag">${t("skills.required")}</span>` : (skill.safety_status ? `<span class="tag">${html(skill.safety_status)}</span>` : ""))}
      </div>
      <p class="skill-summary">${html(skill.description || t("skills.source_empty_description"))}</p>
      <div
        class="tag-cloud skill-card-label-cloud ${labelsExpanded ? "is-expanded" : "is-collapsed"}"
        data-skill-label-cloud="${html(skill.id)}"
      >
        <span class="tag">${html(skill.source)}</span>
        <span class="tag tool-tag">${html(skill.external_id || t("skills.source_no_external_id"))}</span>
        ${skill.tags.map((tag) => `<span class="tag">${html(tag)}</span>`).join("")}
      </div>
      <button
        class="skill-card-label-toggle"
        type="button"
        data-skill-label-toggle="${html(skill.id)}"
        aria-expanded="${labelsExpanded ? "true" : "false"}"
        hidden
      >${labelsExpanded ? t("skills.collapse_labels") : t("skills.expand_labels")}</button>
      ${skill.id ? `<div class="skill-card-actions">
        <button
          class="secondary-button"
          type="button"
          data-install-agent-skill="${html(skill.id)}"
        >${t("agent_skills.install")}</button>
      </div>` : ""}
    </article>
  `;
}

function renderLocalSkillList() {
  const root = document.getElementById("skill-local-list");
  if (!root) return;
  const skills = [...skillState.localSkills];
  const deletableSkillIds = selectableSkillIds();
  const selectedDeleteCount = skillState.selectedDeleteIds.length;
  const allSkillsSelected = deletableSkillIds.length > 0 && deletableSkillIds.every((id) => skillState.selectedDeleteIds.includes(id));
  const hiddenCount = Math.max(0, skills.length - SKILL_LIST_COLLAPSED_COUNT);
  const visibleSkills = skillState.isLocalSkillListExpanded
    ? skills
    : skills.slice(0, SKILL_LIST_COLLAPSED_COUNT);
  root.innerHTML = `
    <div class="skill-panel-head">
      <div>
        <div class="agent-section-title">${t("skills.local_catalog")}</div>
        <div class="panel-meta">${t("skills.imported_count", { count: skills.length })}</div>
      </div>
      <div class="batch-select-controls">
        <label class="batch-checkbox" data-toggle-all-skills="true">
          <input type="checkbox" ${allSkillsSelected ? "checked" : ""} ${deletableSkillIds.length ? "" : "disabled"}>
          <span>${t("button.select")}</span>
        </label>
        <span class="panel-meta">${t("employees.selected", { count: html(selectedDeleteCount, "0") })}</span>
        <button class="danger-button batch-delete-button" type="button" data-delete-selected-skills="true" ${selectedDeleteCount ? "" : "disabled"}>${t("button.delete_selected")}</button>
      </div>
    </div>
    ${skills.length === 0 ? `
      <div class="empty-state">${t("skills.empty")}</div>
    ` : `
      <div class="skill-card-list">
        ${visibleSkills.map((skill) => renderCatalogSkillCard(skill)).join("")}
      </div>
      ${renderSkillListToggle({
        hiddenCount,
        isExpanded: skillState.isLocalSkillListExpanded,
        dataAttribute: "data-toggle-local-skill-list",
        label: "Toggle local skill list",
      })}
    `}
  `;
  if (typeof window.requestAnimationFrame === "function") {
    window.requestAnimationFrame(refreshLocalSkillLabelToggles);
  } else {
    refreshLocalSkillLabelToggles();
  }
}

function skillPreviewTitle() {
  return skillState.previewSource === "web" ? WEB_SKILL_PREVIEW_TITLE : LOCAL_SKILL_PREVIEW_TITLE;
}

function renderSoulBannerSkillCard(skill) {
  const identity = skillIdentity(skill);
  const isSelected = skillState.selectedSoulBannerKeys.includes(identity);
  return `
    <article
      class="skill-option ${isSelected ? "is-selected" : ""}"
      data-soulbanner-skill-toggle="${html(identity)}"
      role="button"
      tabindex="0"
      aria-pressed="${isSelected ? "true" : "false"}"
      title="${html(skill.name)}"
    >
      <span class="skill-option-top">
        <strong class="skill-option-name">${html(skill.name)}</strong>
        <span class="skill-option-state">${isSelected ? t("skills.selected") : t("skills.optional")}</span>
      </span>
      <span class="panel-meta">${remotePersonaMetaLabel(skill)}</span>
      <span class="skill-summary skill-option-summary skill-option-description">${html(skill.description || t("skills.source_empty_description"))}</span>
      <span class="tag-cloud">
        <span class="tag">${html(skill.source)}</span>
        <span class="tag tool-tag">${html(skill.external_id || t("skills.source_no_external_id"))}</span>
        ${skill.tags.map((tag) => `<span class="tag">${html(tag)}</span>`).join("")}
      </span>
    </article>
  `;
}

function renderMbtiSbtiSkillCard(skill) {
  const identity = skillIdentity(skill);
  const isSelected = skillState.selectedMbtiSbtiKeys.includes(identity);
  return `
    <article
      class="skill-option ${isSelected ? "is-selected" : ""}"
      data-mbti-sbti-skill-toggle="${html(identity)}"
      role="button"
      tabindex="0"
      aria-pressed="${isSelected ? "true" : "false"}"
      title="${html(skill.name)}"
    >
      <span class="skill-option-top">
        <strong class="skill-option-name">${html(skill.name)}</strong>
        <span class="skill-option-state">${isSelected ? t("skills.selected") : t("skills.optional")}</span>
      </span>
      <span class="panel-meta">${remotePersonaMetaLabel(skill)}</span>
      <span class="skill-summary skill-option-summary skill-option-description">${html(skill.description || t("skills.source_empty_description"))}</span>
      <span class="tag-cloud">
        <span class="tag">${html(skill.source)}</span>
        <span class="tag tool-tag">${html(skill.external_id || t("skills.source_no_external_id"))}</span>
        ${skill.tags.map((tag) => `<span class="tag">${html(tag)}</span>`).join("")}
      </span>
    </article>
  `;
}

function toggleSoulBannerListExpansion() {
  skillState.isSoulBannerListExpanded = !skillState.isSoulBannerListExpanded;
  renderSkillCatalog();
}

function toggleMbtiSbtiListExpansion() {
  skillState.isMbtiSbtiListExpanded = !skillState.isMbtiSbtiListExpanded;
  renderSkillCatalog();
}

function renderSoulLibraryPanel() {
  const root = document.getElementById("soul-library-panel");
  if (!root) return;
  const isLoaded = skillState.isSoulBannerImportOpen;
  const selectedCount = skillState.selectedSoulBannerKeys.length;
  const importBusy = isBusy("import-soulbanner-skills");
  const canImport = selectedCount > 0 && !importBusy && !skillState.isLoadingSoulBanner;
  const loadLabel = skillState.isLoadingSoulBanner
    ? t("button.loading")
    : (isLoaded ? t("button.reload_soulbanner") : t("button.load_soulbanner"));
  const isMbtiSbtiLoaded = skillState.isMbtiSbtiImportOpen;
  const mbtiSbtiSelectedCount = skillState.selectedMbtiSbtiKeys.length;
  const mbtiSbtiImportBusy = isBusy("import-mbti-sbti-skills");
  const canImportMbtiSbti = mbtiSbtiSelectedCount > 0 && !mbtiSbtiImportBusy && !skillState.isLoadingMbtiSbti;
  const mbtiSbtiLoadLabel = skillState.isLoadingMbtiSbti
    ? t("button.loading")
    : (isMbtiSbtiLoaded ? t("button.reload_mbti_sbti") : t("button.load_mbti_sbti"));
  const soulBannerHiddenCount = Math.max(0, skillState.soulBannerResults.length - SKILL_LIST_COLLAPSED_COUNT);
  const visibleSoulBannerResults = skillState.isSoulBannerListExpanded
    ? skillState.soulBannerResults
    : skillState.soulBannerResults.slice(0, SKILL_LIST_COLLAPSED_COUNT);
  const mbtiSbtiHiddenCount = Math.max(0, skillState.mbtiSbtiResults.length - SKILL_LIST_COLLAPSED_COUNT);
  const visibleMbtiSbtiResults = skillState.isMbtiSbtiListExpanded
    ? skillState.mbtiSbtiResults
    : skillState.mbtiSbtiResults.slice(0, SKILL_LIST_COLLAPSED_COUNT);
  root.innerHTML = `
    <div class="soul-source-panel">
      <div class="skill-panel-head">
        <div>
          <div class="agent-section-title">${t("soul.title")}</div>
          <div class="panel-meta">${t("soul.copy")}</div>
        </div>
      </div>
      <div class="skill-search-actions">
        <button
          class="secondary-button"
          type="button"
          data-load-soul-library="true"
          ${skillState.isLoadingSoulBanner ? "disabled" : ""}
        >${loadLabel}</button>
        <button class="primary-button" type="button" data-import-soulbanner-skills="true" ${canImport ? "" : "disabled"}>
          ${importBusy ? t("button.importing") : t("button.import_selected", { count: selectedCount })}
        </button>
      </div>
      ${skillState.isLoadingSoulBanner ? `
        <div class="empty-state">${t("soul.loading")}</div>
      ` : !isLoaded ? `
        <div class="empty-state">${t("soul.empty.initial")}</div>
      ` : skillState.soulBannerResults.length === 0 ? `
        <div class="empty-state">${t("soul.empty.none")}</div>
      ` : `
        <div class="skill-picker" role="group" aria-label="${html(t("soul.title"))}">
          ${visibleSoulBannerResults.map((skill) => renderSoulBannerSkillCard(skill)).join("")}
        </div>
        ${renderSkillListToggle({
          hiddenCount: soulBannerHiddenCount,
          isExpanded: skillState.isSoulBannerListExpanded,
          dataAttribute: "data-toggle-soulbanner-list",
          label: "Toggle SoulBanner list",
        })}
      `}
    </div>
    <div class="soul-source-panel">
      <div class="skill-panel-head">
        <div>
          <div class="agent-section-title">${t("soul.mbti_sbti.title")}</div>
          <div class="panel-meta">${t("soul.mbti_sbti.copy")}</div>
        </div>
      </div>
      <div class="skill-search-actions">
        <button
          class="secondary-button"
          type="button"
          data-load-mbti-sbti-library="true"
          ${skillState.isLoadingMbtiSbti ? "disabled" : ""}
        >${mbtiSbtiLoadLabel}</button>
        <button class="primary-button" type="button" data-import-mbti-sbti-skills="true" ${canImportMbtiSbti ? "" : "disabled"}>
          ${mbtiSbtiImportBusy ? t("button.importing") : t("button.import_selected", { count: mbtiSbtiSelectedCount })}
        </button>
      </div>
      ${skillState.isLoadingMbtiSbti ? `
        <div class="empty-state">${t("soul.mbti_sbti.loading")}</div>
      ` : !isMbtiSbtiLoaded ? `
        <div class="empty-state">${t("soul.mbti_sbti.empty.initial")}</div>
      ` : skillState.mbtiSbtiResults.length === 0 ? `
        <div class="empty-state">${t("soul.mbti_sbti.empty.none")}</div>
      ` : `
        <div class="skill-picker" role="group" aria-label="${html(t("soul.mbti_sbti.title"))}">
          ${visibleMbtiSbtiResults.map((skill) => renderMbtiSbtiSkillCard(skill)).join("")}
        </div>
        ${renderSkillListToggle({
          hiddenCount: mbtiSbtiHiddenCount,
          isExpanded: skillState.isMbtiSbtiListExpanded,
          dataAttribute: "data-toggle-mbti-sbti-list",
          label: "Toggle Mbti Sbti list",
        })}
      `}
    </div>
  `;
}

function renderWebSkillImportPanel() {
  if (!skillState.isWebImportOpen) {
    return "";
  }
  const previewWebBusy = isBusy("preview-web-skill");
  return `
    <section class="skill-inline-import-panel">
      <div class="skill-panel-head">
        <div>
          <div class="agent-section-title">${t("button.import_web")}</div>
          <div class="panel-meta">${t("skills.web.copy")}</div>
        </div>
      </div>
      <form id="skill-web-import-form" class="skill-search-form">
        <input
          name="url"
          type="url"
          value="${html(skillState.webImportUrl, "")}"
          placeholder="${t("skills.web.placeholder")}"
          autocomplete="off"
        />
        <div class="skill-search-actions">
          <button class="secondary-button" type="submit" ${previewWebBusy ? "disabled" : ""}>
            ${previewWebBusy ? t("button.fetching") : t("button.preview_from_web")}
          </button>
        </div>
      </form>
    </section>
  `;
}

function renderSkillPreview() {
  if (!skillState.previewSkill) {
    return "";
  }
  const importPreviewBusy = isBusy("import-preview-skill");
  return `
    <section class="skill-preview-panel">
      <div class="skill-panel-head">
        <div>
          <div class="agent-section-title">${skillState.previewSource === "web" ? t("skills.preview.web") : t("skills.preview.local")}</div>
          <div class="panel-meta">${html(skillState.previewLabel || t("skills.preview.empty_label"))}</div>
        </div>
      </div>
      <div class="skill-card-list">
        ${renderCatalogSkillCard(skillState.previewSkill)}
      </div>
      <div class="skill-search-actions">
        <button class="secondary-button" type="button" data-cancel-skill-preview="true" ${importPreviewBusy ? "disabled" : ""}>${t("skills.preview.cancel")}</button>
        <button class="primary-button" type="button" data-confirm-skill-import="true" ${importPreviewBusy ? "disabled" : ""}>
          ${importPreviewBusy ? t("button.importing") : t("button.confirm_import")}
        </button>
      </div>
    </section>
  `;
}

function renderSkillSearchPanel() {
  const root = document.getElementById("skill-search-panel");
  if (!root) return;
  const selectedCount = skillState.selectedImportKeys.length;
  const canImport = selectedCount > 0 && !isBusy("import-skills");
  root.innerHTML = `
    ${renderWebSkillImportPanel()}
    ${renderSkillPreview()}
    <div class="skill-panel-head">
      <div>
        <div class="agent-section-title">${t("skills.search.title")}</div>
        <div class="panel-meta">${t("skills.search.copy")}</div>
      </div>
    </div>
    <form id="skill-search-form" class="skill-search-form">
      <input
        name="q"
        type="text"
        value="${html(skillState.searchQuery, "")}"
        placeholder="${t("skills.search.placeholder")}"
        autocomplete="off"
      />
      <div class="skill-search-actions">
        <button class="secondary-button" type="submit" ${skillState.isSearching ? "disabled" : ""}>
          ${skillState.isSearching ? t("button.searching") : t("button.search_clawhub")}
        </button>
        <button class="primary-button" type="button" data-import-skills="true" ${canImport ? "" : "disabled"}>
          ${isBusy("import-skills") ? t("button.importing") : t("button.import_selected", { count: selectedCount })}
        </button>
      </div>
    </form>
    <div class="skill-search-results">
      ${renderSkillSearchResults()}
    </div>
  `;
}

function renderSkillSearchResults() {
  if (!skillState.searchQuery) {
    return `<div class="empty-state">${t("skills.search.empty_prompt")}</div>`;
  }
  if (skillState.isSearching) {
    return `<div class="empty-state">${t("skills.search.loading")}</div>`;
  }
  if (skillState.searchResults.length === 0) {
    return `<div class="empty-state">${t("skills.search.empty_none")}</div>`;
  }
  const hiddenCount = Math.max(0, skillState.searchResults.length - SKILL_LIST_COLLAPSED_COUNT);
  const visibleResults = skillState.isSkillSearchResultsExpanded
    ? skillState.searchResults
    : skillState.searchResults.slice(0, SKILL_LIST_COLLAPSED_COUNT);
  return `
    ${visibleResults.map((skill) => {
    const identity = skillIdentity(skill);
    const checked = skillState.selectedImportKeys.includes(identity);
    return `
      <article
        class="skill-search-item"
        data-search-skill-preview="${html(identity)}"
        tabindex="0"
      >
        <input
          type="checkbox"
          data-skill-toggle="${html(identity)}"
          aria-label="${html(`${t("button.select")} ${skill.name}`)}"
          ${checked ? "checked" : ""}
        />
        <span class="skill-search-main">
          <span class="skill-search-title-row">
            <strong>${html(skill.name)}</strong>
            <span class="panel-meta">${html(skill.version || t("skills.source_unknown_version"))}</span>
          </span>
          <span class="panel-meta">${html(skill.author || "community")} · ${html(skill.external_id || t("skills.source_no_external_id"))}</span>
          <span class="skill-summary">${html(skill.description || t("skills.source_empty_description"))}</span>
        </span>
      </article>
    `;
  }).join("")}
    ${renderSkillListToggle({
      hiddenCount,
      isExpanded: skillState.isSkillSearchResultsExpanded,
      dataAttribute: "data-toggle-skill-search-results",
      label: "Toggle skill search results",
    })}
  `;
}

function agentSkillFilteredRows() {
  const query = text(agentSkillState.query, "").toLowerCase();
  return agentSkillState.skills.filter((skill) => {
    if (agentSkillState.sourceFilter !== "all" && skill.source !== agentSkillState.sourceFilter) {
      return false;
    }
    if (!query) return true;
    return [skill.name, skill.description, skill.path].some((value) => text(value, "").toLowerCase().includes(query));
  });
}

function renderAgentSkillCreatePanel() {
  if (!agentSkillState.isCreateOpen) return "";
  return `
    <section class="agent-skill-create-panel">
      <div>
        <strong>${t("agent_skills.create_title")}</strong>
        <p>${t("agent_skills.create_copy")}</p>
      </div>
      <div class="agent-skill-create-grid">
        <label>
          <span>${t("agent_skills.name")}</span>
          <input type="text" data-agent-skill-create-name="true" value="${html(agentSkillState.createName, "")}" placeholder="repo-workflow" />
        </label>
        <label>
          <span>${t("agent_skills.description")}</span>
          <input type="text" data-agent-skill-create-description="true" value="${html(agentSkillState.createDescription, "")}" placeholder="Use when..." />
        </label>
      </div>
      <div class="agent-skills-actions">
        <button class="secondary-button" type="button" data-agent-skill-create-cancel="true">${t("agent_skills.cancel_create")}</button>
        <button class="primary-button" type="button" data-agent-skill-create-submit="true">${t("agent_skills.create_submit")}</button>
      </div>
    </section>
  `;
}

function renderAgentSkillListItem(skill) {
  const selected = skill.name === agentSkillState.selectedName;
  const status = skill.available ? "available" : "blocked";
  return `
    <button
      class="agent-skill-row ${selected ? "is-selected" : ""}"
      type="button"
      data-agent-skill-select="${html(skill.name)}"
      aria-pressed="${selected ? "true" : "false"}"
    >
      <span>
        <strong>${html(skill.name)}</strong>
        <span>${html(skill.description || skill.path)}</span>
      </span>
      <span class="agent-skill-row-meta">
        ${skill.demo || skill.readOnly ? `<span class="tag demo-badge" data-demo-badge="true">Demo</span>` : ""}
        <span class="tag">${html(skill.source)}</span>
        <span class="tag">${html(status)}</span>
      </span>
    </button>
  `;
}

function renderAgentSkillsList() {
  const rows = agentSkillFilteredRows();
  return `
    <section class="agent-skills-list-panel">
      <div class="agent-skill-filter-row">
        <input
          type="search"
          data-agent-skill-query="true"
          value="${html(agentSkillState.query, "")}"
          placeholder="${t("agent_skills.search")}"
        />
      </div>
      <div class="segmented-control agent-skill-source-filter" role="group" aria-label="Agent skill source filter">
        ${["all", "workspace", "builtin"].map((source) => `
          <button
            class="${agentSkillState.sourceFilter === source ? "is-active" : ""}"
            type="button"
            data-agent-skill-source-filter="${source}"
          >${t(`agent_skills.filter_${source}`)}</button>
        `).join("")}
      </div>
      ${agentSkillState.isLoading ? `
        <div class="empty-state">${t("button.loading")}</div>
      ` : rows.length ? `
        <div class="agent-skill-list" role="list">
          ${rows.map(renderAgentSkillListItem).join("")}
        </div>
      ` : `
        <div class="empty-state">${t("agent_skills.empty")}</div>
      `}
    </section>
  `;
}

function renderAgentSkillDetail() {
  const detail = agentSkillState.selectedDetail;
  if (agentSkillState.isDetailLoading) {
    return `<section class="agent-skill-detail-panel"><div class="empty-state">${t("button.loading")}</div></section>`;
  }
  if (!detail) {
    return `
      <section class="agent-skill-detail-panel">
        <div class="empty-state">${t("agent_skills.select_empty")}</div>
      </section>
    `;
  }
  const skill = detail.skill;
  const draft = agentSkillState.isEditing ? agentSkillState.draft : detail.markdown;
  const canEdit = skill.editable && !agentSkillState.isEditing;
  const canSave = skill.editable && agentSkillState.isEditing && agentSkillState.draft !== detail.markdown;
  const readOnlyDemo = skill.demo || skill.readOnly;
  return `
    <section class="agent-skill-detail-panel">
      <div class="agent-skill-detail-head">
        <div>
          <div class="agent-section-title">${html(skill.name)}</div>
          <div class="panel-meta">${html(skill.source)} · ${html(skill.path)}</div>
        </div>
        <div class="agent-skills-actions">
          ${readOnlyDemo ? `<span class="tag demo-badge" data-demo-badge="true">Demo</span>` : `<button class="secondary-button" type="button" data-agent-skill-package="${html(skill.name)}">${t("agent_skills.package")}</button>`}
          ${canEdit ? `<button class="secondary-button" type="button" data-agent-skill-edit="true">${t("agent_skills.edit")}</button>` : ""}
          ${agentSkillState.isEditing ? `<button class="secondary-button" type="button" data-agent-skill-cancel-edit="true">${t("agent_skills.cancel")}</button>` : ""}
          ${agentSkillState.isEditing ? `<button class="primary-button" type="button" data-agent-skill-save="true" ${canSave ? "" : "disabled"}>${t("agent_skills.save")}</button>` : ""}
          ${skill.deletable ? `<button class="danger-button" type="button" data-agent-skill-delete="${html(skill.name)}">${t("agent_skills.delete")}</button>` : ""}
        </div>
      </div>
      <div class="agent-skill-meta-grid">
        <span><strong>${html(skill.available ? "available" : "blocked")}</strong><small>${html(skill.missing_requirements || skill.updated_at)}</small></span>
        <span><strong>${html(skill.bound_employee_count, "0")}</strong><small>${t("agent_skills.bound_employees")}</small></span>
        <span><strong>${html(skill.category || t("agent_skills.uncategorized"))}</strong><small>${t("agent_skills.category_label")}</small></span>
      </div>
      <div class="agent-skill-progressive-note">${t("agent_skills.progressive")}</div>
      <textarea
        class="agent-skill-editor"
        data-agent-skill-draft="true"
        ${agentSkillState.isEditing ? "" : "readonly"}
        spellcheck="false"
      >${html(draft, "")}</textarea>
    </section>
  `;
}

function renderAgentSkillFiles() {
  const detail = agentSkillState.selectedDetail;
  if (!detail) return "";
  const files = detail.files || [];
  return `
    <section class="agent-skill-files-panel">
      <div class="agent-skill-side-head">
        <strong>${t("agent_skills.files")}</strong>
      </div>
      ${files.length ? `
        <div class="agent-skill-file-list">
          ${files.map((file) => `
            <div class="agent-skill-file-row">
              <span>
                <strong>${html(file.path)}</strong>
                <small>${html(file.type)} · ${html(file.size, "0")} bytes</small>
              </span>
              ${detail.skill.editable && file.type !== "directory" ? `<button class="secondary-button" type="button" data-agent-skill-delete-file="${html(file.path)}">×</button>` : ""}
            </div>
          `).join("")}
        </div>
      ` : `<div class="empty-state">${t("agent_skills.no_files")}</div>`}
      ${detail.skill.editable ? `
        <div class="agent-skill-file-form">
          <input type="text" data-agent-skill-file-path="true" value="${html(agentSkillState.filePath, "")}" placeholder="${t("agent_skills.file_path")}" />
          <textarea data-agent-skill-file-content="true" placeholder="${t("agent_skills.file_content")}">${html(agentSkillState.fileContent, "")}</textarea>
          <button class="secondary-button" type="button" data-agent-skill-write-file="true">${t("agent_skills.write_file")}</button>
        </div>
      ` : ""}
    </section>
  `;
}

function renderAgentSkillProposals() {
  const proposals = agentSkillState.proposals.filter((proposal) => proposal.status === "pending");
  return `
    <section class="agent-skill-proposals-panel">
      <div class="agent-skill-side-head">
        <strong>${t("agent_skills.proposals")}</strong>
      </div>
      ${proposals.length ? proposals.map((proposal) => `
        <article class="agent-skill-proposal-card">
          <div>
            <strong>${html(proposal.action)} · ${html(proposal.name)}</strong>
            <small>${html(proposal.source)}${proposal.merged_count ? ` · merged ${html(proposal.merged_count)}` : ""}${proposal.trigger_reasons.length ? ` · ${html(proposal.trigger_reasons.join(", "))}` : ""}</small>
            <p>${html(proposal.reason || proposal.created_at)}</p>
          </div>
          ${proposal.evidence.length ? `<p>${html(proposal.evidence.slice(0, 2).join(" · "))}</p>` : ""}
          <pre>${html(proposal.action === "patch" ? proposal.new_string : proposal.content).slice(0, 700)}</pre>
          <div class="agent-skills-actions">
            <button class="secondary-button" type="button" data-agent-skill-proposal-discard="${html(proposal.id)}">${t("agent_skills.discard")}</button>
            <button class="primary-button" type="button" data-agent-skill-proposal-approve="${html(proposal.id)}">${t("agent_skills.approve")}</button>
          </div>
        </article>
      `).join("") : `<div class="empty-state">${t("agent_skills.no_proposals")}</div>`}
    </section>
  `;
}

function renderAgentSkillsWorkbench() {
  const root = document.getElementById("agent-skills-panel");
  if (!root) return;
  root.innerHTML = `
    ${agentSkillState.error ? `<div class="skill-ops-error">${t("agent_skills.error", { value: html(agentSkillState.error) })}</div>` : ""}
    ${agentSkillState.packageResult ? `<div class="skill-ops-warning">${t("agent_skills.package_ready", { path: html(agentSkillState.packageResult.package_path || "") })}</div>` : ""}
    ${renderAgentSkillCreatePanel()}
    <div class="agent-skills-grid">
      ${renderAgentSkillsList()}
      ${renderAgentSkillDetail()}
      <div class="agent-skill-side-column">
        ${renderAgentSkillFiles()}
        ${renderAgentSkillProposals()}
      </div>
    </div>
  `;
}

function renderBusyMask() {
  if (!adminState.busyAction) return "";
  const busyAction = adminState.busyAction;
  const progressValue = Number(busyAction.progress);
  const hasProgress = Number.isFinite(progressValue);
  const current = percent(progressValue);
  const label = busyAction.label || "Working...";
  return `
    <div class="busy-overlay" aria-live="polite" data-busy-key="${html(busyAction.key || "")}">
      <div class="busy-card">
        <span class="busy-spinner" aria-hidden="true"></span>
        <span class="busy-content">
          <strong data-busy-label="true">${html(label)}</strong>
          ${hasProgress ? `
            <span class="busy-progress-meta" data-busy-percent="true">${Math.round(current)}%</span>
            <span
              class="busy-progress"
              role="progressbar"
              aria-label="${html(label)}"
              aria-valuemin="0"
              aria-valuemax="100"
              aria-valuenow="${Math.round(current)}"
              data-busy-progress="true"
            >
              <span data-busy-progress-fill="true" style="width: ${current}%"></span>
            </span>
          ` : ""}
        </span>
      </div>
    </div>
  `;
}

function renderCaseMetric(metric) {
  if (metric && typeof metric === "object") {
    return `<span class="case-metric"><strong>${html(metric.value, "")}</strong><span>${html(metric.label, "")}</span></span>`;
  }
  return `<span class="case-metric"><strong>${html(metric, "")}</strong><span>${t("case.metric")}</span></span>`;
}

function normalizeCaseOpsReport(report) {
  if (!report || typeof report !== "object") return null;
  return {
    generatedAt: text(report.generatedAt, ""),
    source: text(report.source, ""),
    summary: report.summary && typeof report.summary === "object" ? report.summary : {},
    issues: Array.isArray(report.issues) ? report.issues.map((issue) => ({
      ...issue,
      id: text(issue?.id, ""),
      type: text(issue?.type, ""),
      title: text(issue?.title, ""),
      body: text(issue?.body, ""),
      severity: text(issue?.severity, "info"),
      ignored: issue?.ignored === true,
      caseId: text(issue?.caseId, ""),
      caseIds: Array.isArray(issue?.caseIds) ? issue.caseIds.map((item) => text(item, "")).filter(Boolean) : [],
      drift: Array.isArray(issue?.drift) ? issue.drift : [],
      skills: Array.isArray(issue?.skills) ? issue.skills : [],
      employees: Array.isArray(issue?.employees) ? issue.employees : [],
    })).filter((issue) => issue.id) : [],
    opportunities: Array.isArray(report.opportunities) ? report.opportunities.map((item) => ({
      ...item,
      id: text(item?.id, ""),
      type: text(item?.type, ""),
      title: text(item?.title, ""),
      body: text(item?.body, ""),
      caseId: text(item?.caseId, ""),
    })).filter((item) => item.id) : [],
    warnings: Array.isArray(report.warnings) ? report.warnings.map((item) => text(item, "")).filter(Boolean) : [],
    auditLog: Array.isArray(report.auditLog) ? report.auditLog.filter((item) => item && typeof item === "object") : [],
  };
}

function caseOpsSelectedIssues() {
  const report = caseOpsState.report;
  if (!report) return [];
  return report.issues.filter((issue) => caseOpsState.selectedIssueIds.includes(issue.id));
}

function caseOpsIssueIdsForAction() {
  return caseOpsSelectedIssues()
    .filter((issue) => [
      "partial_import",
      "import_drift",
      "config_overwrite_risk",
      "recent_import_failed",
    ].includes(issue.type))
    .map((issue) => issue.id);
}

function caseOpsActionEnabled() {
  return caseOpsIssueIdsForAction().length > 0;
}

function renderCaseOpsMetric(label, value) {
  return `
    <span class="case-ops-metric">
      <strong>${html(value, "0")}</strong>
      <span>${html(label)}</span>
    </span>
  `;
}

function renderCaseOpsIssue(issue) {
  const checked = caseOpsState.selectedIssueIds.includes(issue.id);
  const caseTags = [...new Set([issue.caseId, ...(issue.caseIds || [])].filter(Boolean))];
  const details = [
    ...caseTags,
    ...(issue.drift || []).map((item) => `${item.kind || "item"}:${item.key || item.id || ""}`),
    ...(issue.skills || []).map((item) => item.name || item.key || ""),
  ].filter(Boolean).slice(0, 5);
  const canReimport = ["partial_import", "import_drift", "config_overwrite_risk", "recent_import_failed"].includes(issue.type);
  return `
    <article class="case-ops-issue ${issue.ignored ? "is-ignored" : ""}">
      <label class="batch-checkbox">
        <input type="checkbox" data-case-ops-issue="${html(issue.id)}" ${checked ? "checked" : ""} ${canReimport ? "" : "disabled"}>
        <span class="visually-hidden">${html(`${t("button.select")} ${issue.title || issue.type}`)}</span>
      </label>
      <div class="case-ops-issue-body">
        <div class="case-ops-issue-top">
          <strong>${html(issue.title || issue.type)}</strong>
          <span class="tag">${html(issue.type)}</span>
          ${issue.ignored ? `<span class="tag">${t("case.ops.ignored")}</span>` : ""}
        </div>
        <p>${html(issue.body)}</p>
        ${details.length ? `<div class="tag-cloud">${details.map((item) => `<span class="tag">${html(item)}</span>`).join("")}</div>` : ""}
      </div>
      <div class="case-ops-issue-actions">
        ${issue.caseId ? `<button class="secondary-button case-ops-inline-action" type="button" data-case-ops-open-case="${html(issue.caseId)}">${t("case.ops.open_case")}</button>` : ""}
        <button
          class="secondary-button case-ops-inline-action"
          type="button"
          data-case-ops-ignore="${html(issue.id)}"
          data-case-ops-ignore-value="${issue.ignored ? "false" : "true"}"
        >${issue.ignored ? t("case.ops.unignore") : t("case.ops.ignore")}</button>
      </div>
    </article>
  `;
}

function renderCaseOpsOpportunity(item) {
  const label = item.type === "import_config"
    ? t("case.ops.import_config")
    : item.type === "export_selected"
      ? t("case.ops.export_selected")
      : item.type === "reimport_cases"
        ? t("case.ops.reimport")
        : t("case.ops.open_case");
  return `
    <article class="case-ops-opportunity">
      <span>
        <strong>${html(item.title)}</strong>
        <span>${html(item.body)}</span>
      </span>
      <button class="secondary-button" type="button" data-case-ops-opportunity="${html(item.id)}">${label}</button>
    </article>
  `;
}

function renderCaseOpsPreview() {
  const preview = caseOpsState.preview;
  if (!preview) return "";
  const totals = preview.totals || {};
  const caseCount = Array.isArray(preview.cases) ? preview.cases.length : 0;
  const employees = Number(totals.employeeCreates || 0) + Number(totals.employeeUpdates || 0);
  const skills = Number(totals.skillCreates || 0) + Number(totals.skillUpdates || 0);
  const configs = Number(totals.configOverwrites || 0);
  return `
    <section class="case-ops-preview">
      <div>
        <strong>${t("case.ops.preview_title")}</strong>
        <p>${t("case.ops.preview_body", {
          cases: caseCount,
          employees,
          skills,
          configs,
        })}</p>
        ${(preview.cases || []).map((item) => `
          <span class="tag ${item.status === "failed" ? "warning-tag" : ""}">${html(item.title || item.caseId)} · ${html(item.status || "ok")}</span>
        `).join("")}
      </div>
      <div class="case-ops-actions">
        <button class="secondary-button" type="button" data-case-ops-cancel-preview="true">${t("case.ops.cancel")}</button>
        <button class="danger-button" type="button" data-case-ops-confirm="true" ${caseCount ? "" : "disabled"}>${t("case.ops.confirm")}</button>
      </div>
    </section>
  `;
}

function renderCaseOpsPanel() {
  const report = caseOpsState.report;
  const summary = report?.summary || {};
  const visibleIssues = report?.issues || [];
  const selectedCount = caseOpsState.selectedIssueIds.length;
  const busy = caseOpsState.isLoading || caseOpsState.isScanning;
  return `
    <section class="case-ops-panel">
      <div class="case-ops-head">
        <div>
          <div class="agent-section-title">${t("case.ops.title")}</div>
          <div class="panel-meta">${t("case.ops.copy")}</div>
        </div>
        <div class="case-ops-actions">
          <button class="secondary-button" type="button" data-case-ops-scan="true" ${busy ? "disabled" : ""}>
            ${caseOpsState.isScanning ? t("button.loading") : t("case.ops.scan")}
          </button>
          <button class="secondary-button" type="button" data-case-ops-import-config="true">${t("case.ops.import_config")}</button>
        </div>
      </div>
      ${caseOpsState.error ? `<div class="case-ops-error">${t("case.ops.error", { value: html(caseOpsState.error) })}</div>` : ""}
      ${caseOpsState.isLoading && !report ? `<div class="empty-state">${t("case.ops.loading")}</div>` : ""}
      ${report ? `
        <div class="case-ops-summary">
          <div class="case-ops-metrics">
            ${renderCaseOpsMetric(t("case.ops.catalog"), `${summary.fullyImportedCaseCount ?? 0}/${summary.totalCaseCount ?? 0}`)}
            ${renderCaseOpsMetric(t("case.ops.partial"), summary.partialImportCount ?? 0)}
            ${renderCaseOpsMetric(t("case.ops.risk"), summary.riskIssueCount ?? 0)}
            ${renderCaseOpsMetric(t("case.ops.ignored"), summary.ignoredIssueCount ?? 0)}
          </div>
          <span class="panel-meta">${formatUtcDate(report.generatedAt) || html(report.generatedAt)}</span>
        </div>
        ${report.warnings.length ? report.warnings.map((warning) => `<div class="case-ops-warning">${t("case.ops.warning", { value: html(warning) })}</div>`).join("") : ""}
        <div class="case-ops-grid">
          <section>
            <div class="case-ops-section-head">
              <strong>${t("case.ops.issues", { count: visibleIssues.length })}</strong>
              <span class="panel-meta">${t("case.ops.selected", { count: selectedCount })}</span>
            </div>
            <div class="case-ops-actions">
              <button class="secondary-button" type="button" data-case-ops-action="reimport_cases" ${caseOpsActionEnabled() ? "" : "disabled"}>${t("case.ops.reimport")}</button>
            </div>
            ${renderCaseOpsPreview()}
            <div class="case-ops-issue-list">
              ${visibleIssues.length ? visibleIssues.map(renderCaseOpsIssue).join("") : `<div class="empty-state">${t("case.ops.empty")}</div>`}
            </div>
          </section>
          <section>
            <div class="case-ops-section-head">
              <strong>${t("case.ops.opportunities")}</strong>
            </div>
            <div class="case-ops-opportunities">
              ${(report.opportunities || []).map(renderCaseOpsOpportunity).join("")}
            </div>
            <div class="case-ops-section-head">
              <strong>${t("case.ops.audit")}</strong>
            </div>
            <div class="case-ops-audit">
              ${(report.auditLog || []).slice(-3).reverse().map((item) => `
                <div class="case-ops-audit-item">
                  <strong>${html(item.action || "action")}</strong>
                  <span>${html(item.status || "")} · ${html(item.at || "")}</span>
                </div>
              `).join("") || `<div class="empty-state">${t("case.ops.empty")}</div>`}
            </div>
          </section>
        </div>
      ` : ""}
    </section>
  `;
}

function renderCaseCarouselActions() {
  return `
    <div class="section-head-actions case-section-actions">
      <button class="secondary-button" type="button" data-import-case-config="true">${t("button.import_config")}</button>
      <span class="panel-meta">${html(caseState.source || "workspace/openhire/cases.json")}</span>
    </div>
  `;
}

function renderCaseCarousel() {
  const root = document.getElementById("case-carousel");
  if (!root) return;
  const caseOpsPanel = renderCaseOpsPanel();
  const catalogHead = `
    <div class="section-head case-section-head">
      <div>
        <h3>${t("case.title")}</h3>
        <p class="section-copy">${t("case.copy")}</p>
      </div>
      ${renderCaseCarouselActions()}
    </div>
  `;
  let content = "";
  if (caseState.isLoading) {
    content = `<div class="resource-panel-shell case-panel">${caseOpsPanel}${catalogHead}<div class="empty-state">${t("case.loading")}</div></div>`;
  } else if (caseState.error) {
    content = `<div class="resource-panel-shell case-panel">${caseOpsPanel}${catalogHead}<div class="empty-state">${html(caseState.error)}</div></div>`;
  } else if (!caseState.cases.length) {
    content = `<div class="resource-panel-shell case-panel">${caseOpsPanel}${catalogHead}<div class="empty-state">${t("case.empty")}</div></div>`;
  } else {
    content = `
      <div class="resource-panel-shell case-panel">
        ${caseOpsPanel}
        ${catalogHead}
        <div class="case-card-track case-catalog-grid">
          ${caseState.cases.map((item) => `
            <button class="case-card" type="button" data-case-id="${html(item.id)}">
              <span class="case-card-head">
                <span>
                  <strong>${html(item.title)}</strong>
                  <span>${html(item.subtitle || item.description || t("case.default_subtitle"))}</span>
                </span>
                <span class="${item.is_imported ? "badge status-ok" : "badge status-idle"}">${item.demo ? "Demo" : (item.is_imported ? t("case.imported") : t("case.ready"))}</span>
              </span>
              <span class="case-card-body">${html(item.description || t("case.default_body"))}</span>
              <span class="case-metrics">
                ${(item.metrics || []).slice(0, 3).map(renderCaseMetric).join("")}
                <span class="case-metric"><strong>${html(item.employee_count, "0")}</strong><span>${t("case.employees")}</span></span>
                <span class="case-metric"><strong>${html(item.skill_count, "0")}</strong><span>${t("case.skills")}</span></span>
              </span>
              <span class="tag-cloud">${item.demo ? `<span class="tag demo-badge" data-demo-badge="true">Demo</span>` : ""}${(item.tags || []).slice(0, 5).map((tag) => `<span class="tag">${html(tag)}</span>`).join("")}</span>
            </button>
          `).join("")}
        </div>
      </div>
    `;
  }
  root.innerHTML = content;
  renderAlertStrip();
  renderActionCenter();
  renderResourceHubTabs();
  requestNavSectionSync();
}

async function loadCases() {
  caseState.isLoading = true;
  caseState.error = "";
  renderCaseCarousel();
  try {
    const response = await fetch(CASES_ENDPOINT, { headers: { Accept: "application/json" } });
    if (!response.ok) {
      const error = await response.json().catch(() => ({ error: { message: `HTTP ${response.status}` } }));
      throw new Error(text(error?.error?.message, `HTTP ${response.status}`));
    }
    const payload = await response.json();
    caseState.cases = Array.isArray(payload?.cases) ? payload.cases : [];
    caseState.source = text(payload?.source, "");
  } catch (error) {
    caseState.error = text(error.message, "Failed to load cases.");
  } finally {
    caseState.isLoading = false;
    renderCaseCarousel();
  }
}

async function loadCaseOps() {
  caseOpsState.isLoading = true;
  caseOpsState.error = "";
  renderCaseCarousel();
  try {
    const response = await fetch(CASE_OPS_ENDPOINT, { headers: { Accept: "application/json" } });
    if (!response.ok) {
      const error = await response.json().catch(() => ({ error: { message: `HTTP ${response.status}` } }));
      throw new Error(text(error?.error?.message, `HTTP ${response.status}`));
    }
    caseOpsState.report = normalizeCaseOpsReport(await response.json());
    caseOpsState.selectedIssueIds = caseOpsState.selectedIssueIds.filter((issueId) => (
      caseOpsState.report?.issues.some((issue) => issue.id === issueId)
    ));
  } catch (error) {
    caseOpsState.error = text(error.message, "Failed to load case ops.");
  } finally {
    caseOpsState.isLoading = false;
    renderCaseCarousel();
  }
}

async function scanCaseOps() {
  caseOpsState.isScanning = true;
  caseOpsState.error = "";
  caseOpsState.preview = null;
  renderCaseCarousel();
  try {
    const response = await fetch(CASE_OPS_SCAN_ENDPOINT, {
      method: "POST",
      headers: { Accept: "application/json" },
    });
    if (!response.ok) {
      const error = await response.json().catch(() => ({ error: { message: `HTTP ${response.status}` } }));
      throw new Error(text(error?.error?.message, `HTTP ${response.status}`));
    }
    caseOpsState.report = normalizeCaseOpsReport(await response.json());
    caseOpsState.selectedIssueIds = [];
  } catch (error) {
    caseOpsState.error = text(error.message, "Failed to scan cases.");
  } finally {
    caseOpsState.isScanning = false;
    renderCaseCarousel();
  }
}

function toggleCaseOpsIssueSelection(issueId) {
  const normalized = text(issueId, "");
  if (!normalized) return;
  if (caseOpsState.selectedIssueIds.includes(normalized)) {
    caseOpsState.selectedIssueIds = caseOpsState.selectedIssueIds.filter((item) => item !== normalized);
  } else {
    caseOpsState.selectedIssueIds = [...caseOpsState.selectedIssueIds, normalized];
  }
  caseOpsState.preview = null;
  renderCaseCarousel();
}

async function setCaseOpsIssueIgnored(issueId, ignored) {
  const normalized = text(issueId, "");
  if (!normalized) return;
  const response = await fetch(CASE_OPS_IGNORE_ENDPOINT, {
    method: "POST",
    headers: { "Content-Type": "application/json", Accept: "application/json" },
    body: JSON.stringify({ issue_ids: [normalized], ignored: ignored === true }),
  });
  if (!response.ok) {
    const error = await response.json().catch(() => ({ error: { message: `HTTP ${response.status}` } }));
    throw new Error(text(error?.error?.message, `HTTP ${response.status}`));
  }
  caseOpsState.report = normalizeCaseOpsReport(await response.json());
  renderCaseCarousel();
}

async function runCaseOpsAction(action, { dryRun = true, confirm = false, caseIds = [] } = {}) {
  const issueIds = caseIds.length ? [] : caseOpsIssueIdsForAction(action);
  if (!caseIds.length && !issueIds.length) return;
  caseOpsState.pendingAction = action;
  const response = await fetch(CASE_OPS_ACTION_ENDPOINT, {
    method: "POST",
    headers: { "Content-Type": "application/json", Accept: "application/json" },
    body: JSON.stringify({
      action,
      issue_ids: issueIds,
      case_ids: caseIds,
      dry_run: dryRun,
      confirm,
    }),
  });
  if (!response.ok) {
    const error = await response.json().catch(() => ({ error: { message: `HTTP ${response.status}` } }));
    throw new Error(text(error?.error?.message, `HTTP ${response.status}`));
  }
  const payload = await response.json();
  if (dryRun) {
    caseOpsState.preview = payload;
    renderCaseCarousel();
    return;
  }
  caseOpsState.preview = null;
  caseOpsState.selectedIssueIds = [];
  adminState.confirmAction = null;
  await loadSkills();
  await loadEmployees();
  await loadCases();
  await loadCaseOps();
}

function requestCaseOpsAction(action) {
  runCaseOpsAction(action, { dryRun: true }).catch((error) => {
    caseOpsState.error = text(error.message, "Failed to preview case action.");
    renderCaseCarousel();
  });
}

function confirmCaseOpsAction() {
  const preview = caseOpsState.preview;
  if (!preview?.action) return;
  const totals = preview.totals || {};
  openConfirmAction({
    kind: "case-ops-action",
    action: preview.action,
    title: t("case.ops.confirm"),
    subtitle: t("case.ops.preview_title"),
    message: t("case.ops.preview_body", {
      cases: Array.isArray(preview.cases) ? preview.cases.length : 0,
      employees: Number(totals.employeeCreates || 0) + Number(totals.employeeUpdates || 0),
      skills: Number(totals.skillCreates || 0) + Number(totals.skillUpdates || 0),
      configs: Number(totals.configOverwrites || 0),
    }),
    confirmLabel: t("case.ops.confirm"),
  });
}

function handleCaseOpsOpportunity(opportunityId) {
  const item = caseOpsState.report?.opportunities.find((opportunity) => opportunity.id === opportunityId);
  if (!item) return;
  if (item.type === "import_config") {
    openCaseConfigFilePicker().catch((error) => {
      window.alert(text(error.message, "Failed to import case config"));
    });
    return;
  }
  if (item.type === "export_selected") {
    if (employeeState.selectedDeleteIds.length) {
      openEmployeeExportModal().catch((error) => {
        window.alert(text(error.message, "Failed to export selected employees"));
      });
      return;
    }
    scrollToNavSection("employee-studio");
    return;
  }
  if (item.type === "reimport_cases" && item.caseId) {
    runCaseOpsAction("reimport_cases", { dryRun: true, caseIds: [item.caseId] }).catch((error) => {
      caseOpsState.error = text(error.message, "Failed to preview case action.");
      renderCaseCarousel();
    });
    return;
  }
  if (item.type === "open_case" && item.caseId) {
    openCaseDetail(item.caseId);
  }
}

function openCaseDetail(caseId) {
  caseState.isDetailOpen = true;
  caseState.selectedCaseId = text(caseId, "");
  caseState.detail = null;
  caseState.preview = null;
  caseState.importResult = null;
  caseState.detailError = "";
  caseState.importedCasePayload = null;
  caseState.detailSource = "catalog";
  caseState.detailSourceLabel = "";
  renderEmployeeModal();
  loadCaseDetail(caseState.selectedCaseId).catch((error) => {
    caseState.detailError = text(error.message, "Failed to load case.");
    renderEmployeeModal();
  });
}

function closeCaseDetail() {
  if (adminState.busyAction) return;
  caseState.isDetailOpen = false;
  caseState.selectedCaseId = "";
  caseState.detail = null;
  caseState.preview = null;
  caseState.importResult = null;
  caseState.detailError = "";
  caseState.importedCasePayload = null;
  caseState.detailSource = "catalog";
  caseState.detailSourceLabel = "";
  renderEmployeeModal();
}

function defaultEmployeeExportDraft(overrides = {}) {
  return {
    id: "",
    title: "",
    description: "",
    ...overrides,
  };
}

function resetEmployeeExportState() {
  employeeExportState.isOpen = false;
  employeeExportState.isLoading = false;
  employeeExportState.error = "";
  employeeExportState.payload = null;
  employeeExportState.draft = defaultEmployeeExportDraft();
}

function currentEmployeeExportCase() {
  if (!employeeExportState.payload) return null;
  return {
    ...employeeExportState.payload,
    id: String(employeeExportState.draft.id ?? ""),
    title: String(employeeExportState.draft.title ?? ""),
    description: String(employeeExportState.draft.description ?? ""),
  };
}

function updateEmployeeExportPreview() {
  const preview = document.querySelector("[data-employee-export-preview]");
  if (preview) {
    const exportedCase = currentEmployeeExportCase();
    preview.textContent = exportedCase ? JSON.stringify(exportedCase, null, 2) : "";
  }
}

const CASE_DETAIL_MODAL_MIN_HEIGHT = 360;
const CASE_DETAIL_MODAL_MAX_HEIGHT = 860;

function syncCaseDetailViewport() {
  if (!caseState.isDetailOpen) return;
  const backdrop = document.querySelector(".case-modal-backdrop");
  const modal = document.querySelector(".case-detail-modal");
  if (!(backdrop instanceof HTMLElement) || !(modal instanceof HTMLElement)) return;
  const viewport = window.visualViewport;
  const viewportHeight = Number(viewport?.height) || window.innerHeight || document.documentElement.clientHeight || CASE_DETAIL_MODAL_MAX_HEIGHT;
  const viewportOffsetTop = Number(viewport?.offsetTop) || 0;
  const modalTop = Math.max(0, modal.getBoundingClientRect().top - viewportOffsetTop);
  const bottomGap = viewportHeight <= 820 ? 10 : 16;
  const availableHeight = Math.floor(viewportHeight - modalTop - bottomGap);
  if (!Number.isFinite(availableHeight) || availableHeight <= 0) return;
  const minimumHeight = Math.min(CASE_DETAIL_MODAL_MIN_HEIGHT, availableHeight);
  const height = Math.min(CASE_DETAIL_MODAL_MAX_HEIGHT, Math.max(minimumHeight, availableHeight));
  backdrop.style.setProperty("--case-modal-height", `${height}px`);
}

function requestCaseDetailViewportSync() {
  if (!caseState.isDetailOpen) return;
  syncCaseDetailViewport();
  if (typeof window.requestAnimationFrame !== "function") return;
  window.requestAnimationFrame(() => {
    syncCaseDetailViewport();
    window.requestAnimationFrame(syncCaseDetailViewport);
  });
}

async function openEmployeeExportModal() {
  const employeeIds = [...employeeState.selectedDeleteIds];
  if (!employeeIds.length) return;
  employeeExportState.requestId += 1;
  const requestId = employeeExportState.requestId;
  employeeExportState.isOpen = true;
  employeeExportState.isLoading = true;
  employeeExportState.error = "";
  employeeExportState.payload = null;
  employeeExportState.draft = defaultEmployeeExportDraft();
  renderEmployeeModal();
  try {
    const response = await fetch(EMPLOYEE_EXPORT_ENDPOINT, {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
        Accept: "application/json",
      },
      body: JSON.stringify({ employee_ids: employeeIds }),
    });
    if (!response.ok) {
      const error = await response.json().catch(() => ({ error: { message: `HTTP ${response.status}` } }));
      throw new Error(text(error?.error?.message, `HTTP ${response.status}`));
    }
    const payload = await response.json();
    if (employeeExportState.requestId !== requestId || !employeeExportState.isOpen) return;
    const exportedCase = payload?.case && typeof payload.case === "object" ? payload.case : null;
    if (!exportedCase) {
      throw new Error("Missing exported case payload.");
    }
    employeeExportState.payload = exportedCase;
    employeeExportState.draft = defaultEmployeeExportDraft({
      id: text(exportedCase.id, ""),
      title: text(exportedCase.title, ""),
      description: text(exportedCase.description, ""),
    });
    employeeExportState.isLoading = false;
    employeeExportState.error = "";
  } catch (error) {
    if (employeeExportState.requestId !== requestId || !employeeExportState.isOpen) return;
    employeeExportState.isLoading = false;
    employeeExportState.error = text(error.message, "Failed to export selected employees.");
  }
  renderEmployeeModal();
}

function closeEmployeeExportModal() {
  employeeExportState.requestId += 1;
  resetEmployeeExportState();
  renderEmployeeModal();
}

function updateEmployeeExportDraft(fieldName, value) {
  if (!["id", "title", "description"].includes(fieldName)) return;
  employeeExportState.draft = {
    ...employeeExportState.draft,
    [fieldName]: String(value ?? ""),
  };
  updateEmployeeExportPreview();
}

async function downloadEmployeeExportCase() {
  const exportedCase = currentEmployeeExportCase();
  if (!exportedCase) return;
  const fileName = `${slugify(exportedCase.id || exportedCase.title || "employee-export", "employee-export")}.json`;
  const content = `${JSON.stringify(exportedCase, null, 2)}\n`;
  if (typeof window.showSaveFilePicker === "function") {
    try {
      const handle = await window.showSaveFilePicker({
        suggestedName: fileName,
        types: [
          {
            description: "JSON Files",
            accept: { "application/json": [".json"] },
          },
        ],
      });
      const writable = await handle.createWritable();
      await writable.write(content);
      await writable.close();
      return;
    } catch (error) {
      if (error?.name === "AbortError") {
        return;
      }
      throw error;
    }
  }
  const blob = new Blob([content], { type: "application/json;charset=utf-8" });
  const objectUrl = window.URL.createObjectURL(blob);
  const link = document.createElement("a");
  link.href = objectUrl;
  link.download = fileName;
  document.body.appendChild(link);
  link.click();
  link.remove();
  window.setTimeout(() => window.URL.revokeObjectURL(objectUrl), 0);
}

async function loadCaseDetail(caseId) {
  const response = await fetch(`${CASES_ENDPOINT}/${encodeURIComponent(caseId)}`, { headers: { Accept: "application/json" } });
  if (!response.ok) {
    const error = await response.json().catch(() => ({ error: { message: `HTTP ${response.status}` } }));
    throw new Error(text(error?.error?.message, `HTTP ${response.status}`));
  }
  caseState.detail = await response.json();
  renderEmployeeModal();
}

async function openCaseConfigFilePicker() {
  if (typeof window.showOpenFilePicker === "function") {
    try {
      const [handle] = await window.showOpenFilePicker({
        multiple: false,
        types: [
          {
            description: "JSON Files",
            accept: { "application/json": [".json"] },
          },
        ],
      });
      if (!handle) return;
      const file = await handle.getFile();
      if (!file) return;
      await previewCaseConfigFile(file);
      return;
    } catch (error) {
      if (error?.name === "AbortError") {
        return;
      }
      throw error;
    }
  }
  const input = document.getElementById("case-config-file-input");
  if (!(input instanceof HTMLInputElement)) return;
  input.click();
}

async function previewCaseConfigFile(file) {
  const actionKey = `preview-case-file:${text(file?.name, "import")}`;
  setBusyAction({ key: actionKey, label: "Previewing case config..." });
  try {
    const raw = await file.text();
    let parsed;
    try {
      parsed = JSON.parse(raw);
    } catch (error) {
      throw new Error(`Invalid JSON in ${text(file?.name, "selected file")}: ${text(error?.message, "parse error")}`);
    }
    const response = await fetch(CASE_CONFIG_IMPORT_PREVIEW_ENDPOINT, {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
        Accept: "application/json",
      },
      body: JSON.stringify(parsed),
    });
    if (!response.ok) {
      const error = await response.json().catch(() => ({ error: { message: `HTTP ${response.status}` } }));
      throw new Error(text(error?.error?.message, `HTTP ${response.status}`));
    }
    const payload = await response.json();
    caseState.isDetailOpen = true;
    caseState.selectedCaseId = text(payload?.case?.id, slugify(file.name.replace(/\.json$/i, ""), "case"));
    caseState.detail = payload?.case || null;
    caseState.preview = payload?.preview || null;
    caseState.importResult = null;
    caseState.detailError = "";
    caseState.importedCasePayload = payload?.case || null;
    caseState.detailSource = "upload";
    caseState.detailSourceLabel = text(file?.name, "Imported JSON");
    renderEmployeeModal();
    companionReact({
      type: "ready",
      bubble: companionPhrase("Case config preview is ready.", "案例配置预览已就绪。"),
    });
  } catch (error) {
    companionReact({
      type: "error",
      bubble: companionPhrase("Case config preview failed.", "案例配置预览失败。"),
    });
    throw error;
  } finally {
    clearBusyAction();
  }
}

async function previewCaseImport(caseId) {
  const actionKey = `preview-case:${caseId}`;
  setBusyAction({ key: actionKey, label: "Previewing case import..." });
  try {
    const response = caseState.importedCasePayload
      ? await fetch(CASE_CONFIG_IMPORT_PREVIEW_ENDPOINT, {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
          Accept: "application/json",
        },
        body: JSON.stringify({ case: caseState.importedCasePayload }),
      })
      : await fetch(`${CASES_ENDPOINT}/${encodeURIComponent(caseId)}/import/preview`, {
        method: "POST",
        headers: { Accept: "application/json" },
      });
    if (!response.ok) {
      const error = await response.json().catch(() => ({ error: { message: `HTTP ${response.status}` } }));
      throw new Error(text(error?.error?.message, `HTTP ${response.status}`));
    }
    const payload = await response.json();
    if (caseState.importedCasePayload) {
      caseState.detail = payload?.case || caseState.detail;
      caseState.importedCasePayload = payload?.case || caseState.importedCasePayload;
      caseState.selectedCaseId = text(payload?.case?.id, caseState.selectedCaseId || "case");
      caseState.preview = payload?.preview || null;
    } else {
      caseState.preview = payload;
    }
    caseState.importResult = null;
    renderEmployeeModal();
  } finally {
    clearBusyAction();
  }
}

function caseImportProgressSnapshot(elapsedMs) {
  let elapsed = Math.max(0, Number(elapsedMs || 0));
  for (const stage of CASE_IMPORT_PROGRESS_STAGES) {
    if (elapsed <= stage.durationMs) {
      const ratio = stage.durationMs > 0 ? elapsed / stage.durationMs : 1;
      return {
        label: stage.label,
        progress: Math.round(stage.start + ((stage.end - stage.start) * ratio)),
      };
    }
    elapsed -= stage.durationMs;
  }
  const finalEstimate = CASE_IMPORT_PROGRESS_STAGES[CASE_IMPORT_PROGRESS_STAGES.length - 1];
  return {
    label: finalEstimate.label,
    progress: finalEstimate.end,
  };
}

function startCaseImportProgress(actionKey) {
  stopCaseImportProgress();
  const startedAt = Date.now();
  setBusyAction({
    key: actionKey,
    label: CASE_IMPORT_PROGRESS_STAGES[0].label,
    progress: 0,
  });
  caseImportProgressTimer = window.setInterval(() => {
    updateBusyActionProgress(caseImportProgressSnapshot(Date.now() - startedAt));
  }, CASE_IMPORT_PROGRESS_INTERVAL_MS);
}

function completeCaseImportProgress() {
  updateBusyActionProgress({
    label: "Case imported",
    progress: 100,
  });
}

function stopCaseImportProgress() {
  if (!caseImportProgressTimer) return;
  window.clearInterval(caseImportProgressTimer);
  caseImportProgressTimer = null;
}

async function confirmCaseImport(caseId) {
  const actionKey = `import-case:${caseId}`;
  startCaseImportProgress(actionKey);
  try {
    const response = caseState.importedCasePayload
      ? await fetch(CASE_CONFIG_IMPORT_ENDPOINT, {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
          Accept: "application/json",
        },
        body: JSON.stringify({ case: caseState.importedCasePayload }),
      })
      : await fetch(`${CASES_ENDPOINT}/${encodeURIComponent(caseId)}/import`, {
        method: "POST",
        headers: { Accept: "application/json" },
      });
    if (!response.ok && response.status !== 207) {
      const error = await response.json().catch(() => ({ error: { message: `HTTP ${response.status}` } }));
      throw new Error(text(error?.error?.message, `HTTP ${response.status}`));
    }
    caseState.importResult = await response.json();
    const failedCount = Number(caseState.importResult?.failed_count || 0);
    companionReact({
      type: failedCount > 0 || caseState.importResult?.status === "partial" ? "warning" : "ready",
      bubble: failedCount > 0
        ? companionPhrase(`Case import completed with ${failedCount} warning(s).`, `案例导入完成，但有 ${failedCount} 个告警。`)
        : companionPhrase("Case imported and team setup refreshed.", "案例已导入，团队配置已刷新。"),
    });
    completeCaseImportProgress();
    await sleep(250);
    caseState.preview = null;
    await loadSkills();
    await loadEmployees();
    await loadCases();
    await loadCaseOps();
    const importedEmployee = (caseState.importResult.employees || []).find((employee) => employee.id);
    if (importedEmployee) {
      employeeState.selectedEmployeeId = importedEmployee.id;
      employeeState.isEmployeeDetailExpanded = true;
      resetEmployeeConfigState(importedEmployee.id);
      renderEmployees();
    }
    if (caseState.importResult?.status !== "partial") {
      caseState.isDetailOpen = false;
      caseState.selectedCaseId = "";
      caseState.detail = null;
      caseState.preview = null;
      caseState.importResult = null;
      caseState.detailError = "";
      caseState.importedCasePayload = null;
      caseState.detailSource = "catalog";
      caseState.detailSourceLabel = "";
      return;
    }
    renderEmployeeModal();
  } catch (error) {
    companionReact({
      type: "error",
      bubble: companionPhrase("Case import failed.", "案例导入失败。"),
    });
    throw error;
  } finally {
    stopCaseImportProgress();
    clearBusyAction();
  }
}

function renderCaseDossierHero(detail, metaLabel) {
  const employees = Array.isArray(detail?.employees) ? detail.employees : [];
  const skills = Array.isArray(detail?.skills) ? detail.skills : [];
  const workflow = Array.isArray(detail?.workflow) ? detail.workflow : [];
  const tags = Array.isArray(detail?.tags) ? detail.tags : [];
  const title = detail?.title || "Case Detail";
  const summary = detail?.description || detail?.subtitle || "Review the reusable case package before importing.";
  const statusLabel = caseState.importResult
    ? (caseState.importResult.status === "partial" ? "Partial import" : "Imported")
    : (caseState.preview ? "Preview ready" : "Ready to import");
  return `
    <div class="case-dossier-hero">
      <div class="case-dossier-copy">
        <div class="case-dossier-eyebrow">Case Dossier / 案例档案</div>
        <h3 id="case-detail-title">${html(title)}</h3>
        <p class="case-dossier-summary">${html(summary)}</p>
        <div class="case-dossier-meta">
          <span>${html(metaLabel)}</span>
          <span>${html(statusLabel)}</span>
        </div>
        ${tags.length ? `<div class="tag-cloud case-dossier-tags">${tags.slice(0, 6).map((tag) => `<span class="tag">${html(tag)}</span>`).join("")}</div>` : ""}
      </div>
      <div class="case-dossier-stats" aria-label="Case package summary">
        <div><strong>${employees.length}</strong><span>Employees / 员工</span></div>
        <div><strong>${skills.length}</strong><span>Skills / 技能</span></div>
        <div><strong>${workflow.length}</strong><span>Workflow / 流程</span></div>
      </div>
    </div>
  `;
}

function renderCaseSectionTitle(title, note = "") {
  return `
    <div class="case-section-title">
      <span>${html(title)}</span>
      ${note ? `<small>${html(note)}</small>` : ""}
    </div>
  `;
}

function renderCaseInputOutput(detail) {
  const input = detail.input || {};
  const output = detail.output || {};
  const highlights = Array.isArray(output.highlights) ? output.highlights : [];
  return `
    <div class="case-detail-grid case-io-grid">
      <section class="case-detail-block case-io-block">
        ${renderCaseSectionTitle("Input / 输入", "Source request")}
        <div class="case-input-card">
          <div class="code-block case-code-block">${html(input.request || JSON.stringify(input, null, 2), "")}</div>
        </div>
      </section>
      <section class="case-detail-block case-io-block case-output-block">
        ${renderCaseSectionTitle("Output / 输出", "Expected result")}
        <details class="case-output-details">
          <summary aria-label="Toggle output details">
            <span>Result details / 输出详情</span>
          </summary>
          <div class="case-output-detail-body">
            <div class="case-output-summary">${html(output.summary || "No output summary.")}</div>
            ${highlights.length ? `<ul class="case-highlight-list">${highlights.map((item) => `<li>${html(item)}</li>`).join("")}</ul>` : ""}
            ${output.final_response ? `
              <div class="case-final-response">
                <strong>Final response</strong>
                <div class="code-block case-code-block">${html(output.final_response)}</div>
              </div>
            ` : ""}
          </div>
        </details>
      </section>
    </div>
  `;
}

function renderCaseWorkflow(detail) {
  const steps = Array.isArray(detail.workflow) ? detail.workflow : [];
  if (!steps.length) return "";
  return `
    <div class="agent-section">
      ${renderCaseSectionTitle("Workflow / 协作流程", `${steps.length} stages`)}
      <div class="case-step-list">
        ${steps.map((step, index) => `
          <article class="case-step">
            <span class="case-step-index">${index + 1}</span>
            <div class="case-step-content">
              <strong>${html(step?.title || `Step ${index + 1}`)}</strong>
              <p>${html(step?.body || step || "")}</p>
            </div>
          </article>
        `).join("")}
      </div>
    </div>
  `;
}

function renderCaseEmployees(detail) {
  const employees = Array.isArray(detail.employees) ? detail.employees : [];
  return `
    <div class="agent-section">
      ${renderCaseSectionTitle("Employees / 数字员工", `${employees.length} ready`)}
      <div class="case-employee-grid">
        ${employees.map((employee) => `
          <article class="case-employee-card">
            <div class="case-entity-head">
              <strong>${html(employee.name)}</strong>
              <span>${html(employee.agent_type)}</span>
            </div>
            <p>${html(employee.role || "Digital employee")}</p>
            <div class="tag-cloud">${(employee.skill_keys || []).map((skill) => `<span class="tag">${html(skill)}</span>`).join("")}</div>
            <details>
              <summary>Config files</summary>
              <div class="case-config-list">
                ${Object.entries(employee.config_files || {}).map(([filename, content]) => `
                  <div>
                    <strong>${html(filename)}</strong>
                    <pre>${html(content, "")}</pre>
                  </div>
                `).join("")}
              </div>
            </details>
          </article>
        `).join("")}
      </div>
    </div>
  `;
}

function renderCaseSkills(detail) {
  const skills = Array.isArray(detail.skills) ? detail.skills : [];
  return `
    <div class="agent-section">
      ${renderCaseSectionTitle("Skills / 技能", `${skills.length} package skills`)}
      <div class="case-skill-grid">
        ${skills.map((skill) => {
          const identity = skillIdentity(skill);
          return `
          <article class="case-skill-card" data-case-skill-preview="${html(identity)}" tabindex="0" role="button">
            <div class="case-entity-head">
              <strong>${html(skill.name)}</strong>
              <span>${html(skill.source || "case")}</span>
            </div>
            <p>${html(skill.description || "No description.")}</p>
            <div class="tag-cloud">${(skill.tags || []).slice(0, 5).map((tag) => `<span class="tag">${html(tag)}</span>`).join("")}</div>
          </article>
        `;
        }).join("")}
      </div>
    </div>
  `;
}

function renderCaseImportPreview() {
  const preview = caseState.preview;
  if (!preview) return "";
  return `
    <div class="case-import-preview">
      <div class="agent-section-title">Import Preview / 导入预览</div>
      <div class="case-import-summary">
        <span>${preview.skills?.filter((item) => item.action === "create").length || 0} skills to create</span>
        <span>${preview.skills?.filter((item) => item.action === "update").length || 0} skills to update</span>
        <span>${preview.employees?.filter((item) => item.action === "create").length || 0} employees to create</span>
        <span>${preview.employees?.filter((item) => item.action === "update").length || 0} employees to update</span>
        <span>${html(preview.overwrite_count, "0")} config files to overwrite</span>
      </div>
      <div class="case-preview-list">
        ${(preview.employees || []).map((employee) => `
          <article>
            <strong>${html(employee.name)} · ${html(employee.action)}</strong>
            <div class="panel-meta">${html(employee.agent_type)} · ${html(employee.existing_id || "new employee")}</div>
            <div class="tag-cloud">${(employee.config_files || []).map((file) => `<span class="tag ${file.action === "overwrite" ? "warning-tag" : ""}">${html(file.name)}: ${html(file.action)}</span>`).join("")}</div>
          </article>
        `).join("")}
      </div>
    </div>
  `;
}

function renderCaseImportResult() {
  const result = caseState.importResult;
  if (!result) return "";
  return `
    <div class="case-import-result ${result.status === "partial" ? "is-partial" : ""}">
      <strong>${result.status === "partial" ? "Partial import completed" : "Case imported"}</strong>
      <span>${html(result.failed_count || 0)} failed · ${(result.employees || []).filter((item) => item.id).length} employees ready</span>
      ${(result.employees || []).some((item) => item.error) ? `
        <div class="case-preview-list">
          ${(result.employees || []).filter((item) => item.error).map((item) => `
            <article><strong>${html(item.name)}</strong><p>${html(item.error)}</p></article>
          `).join("")}
        </div>
      ` : ""}
    </div>
  `;
}

function renderCaseDetailModal() {
  const detail = caseState.detail;
  const title = detail?.title || "Case Detail";
  const busy = adminState.busyAction;
  const isImportBusy = busy?.key === `import-case:${caseState.selectedCaseId}`;
  const isPreviewBusy = busy?.key === `preview-case:${caseState.selectedCaseId}`;
  const metaLabel = caseState.detailSource === "upload"
    ? `${text(caseState.selectedCaseId, "case")} · ${text(caseState.detailSourceLabel, "Imported JSON")}`
    : text(caseState.selectedCaseId, "case");
  const body = caseState.detailError
    ? `<div class="empty-state">${html(caseState.detailError)}</div>`
    : !detail
      ? `<div class="empty-state">Loading case detail...</div>`
      : `
        ${renderCaseInputOutput(detail)}
        ${renderCaseWorkflow(detail)}
        ${renderCaseEmployees(detail)}
        ${renderCaseSkills(detail)}
        ${renderCaseImportPreview()}
        ${renderCaseImportResult()}
      `;
  return `
    <div class="modal-backdrop case-modal-backdrop">
      <section class="employee-modal case-detail-modal" role="dialog" aria-modal="true" aria-labelledby="case-detail-title">
        <div class="panel-head case-detail-head">
          ${detail ? renderCaseDossierHero(detail, metaLabel) : `
            <div class="case-detail-title-shell">
              <div class="case-dossier-eyebrow">Case Dossier / 案例档案</div>
              <h3 id="case-detail-title">${html(title)}</h3>
              <div class="panel-meta">${html(metaLabel)}</div>
            </div>
          `}
          <button class="icon-button" type="button" data-modal-close="true" aria-label="Close case dialog" ${busy ? "disabled" : ""}>×</button>
        </div>
        <div class="case-detail-scroll">
          ${body}
        </div>
        <div class="modal-actions">
          <button class="secondary-button" type="button" data-case-preview-import="${html(caseState.selectedCaseId)}" ${!detail || busy ? "disabled" : ""}>${isPreviewBusy ? "Previewing..." : "Preview Import"}</button>
          <button class="primary-button" type="button" data-case-confirm-import="${html(caseState.selectedCaseId)}" ${!detail || busy ? "disabled" : ""}>${isImportBusy ? "Importing..." : "Confirm Import"}</button>
        </div>
      </section>
    </div>
    ${busy ? renderBusyMask() : ""}
  `;
}

function renderEmployeeExportModal() {
  const exportedCase = currentEmployeeExportCase();
  const employeeCount = Array.isArray(exportedCase?.employees) ? exportedCase.employees.length : 0;
  const skillCount = Array.isArray(exportedCase?.skills) ? exportedCase.skills.length : 0;
  const body = employeeExportState.isLoading
    ? `<div class="empty-state">Building export preview...</div>`
    : employeeExportState.error
      ? `<div class="empty-state">${html(employeeExportState.error)}</div>`
      : !exportedCase
        ? `<div class="empty-state">No export data available.</div>`
        : `
          <p class="employee-summary">Export the selected persisted employees as a single case record compatible with Case Carousel / 案例轮播 import.</p>
          <form class="employee-export-form" id="employee-export-form">
            <label>
              <span>Case ID</span>
              <input
                type="text"
                name="id"
                value="${html(employeeExportState.draft.id, "")}"
                data-employee-export-field="id"
                spellcheck="false"
              >
            </label>
            <label>
              <span>Title</span>
              <input
                type="text"
                name="title"
                value="${html(employeeExportState.draft.title, "")}"
                data-employee-export-field="title"
              >
            </label>
            <label>
              <span>Description</span>
              <textarea
                name="description"
                data-employee-export-field="description"
                spellcheck="false"
              >${html(employeeExportState.draft.description, "")}</textarea>
            </label>
          </form>
          <div class="employee-export-summary">
            <span class="tag">${html(employeeCount, "0")} employees</span>
            <span class="tag">${html(skillCount, "0")} skills</span>
          </div>
          <div class="agent-section">
            <div class="agent-section-title">Export Preview / 导出预览</div>
            <pre class="skill-content-preview employee-export-preview" data-employee-export-preview="true">${html(JSON.stringify(exportedCase, null, 2), "")}</pre>
          </div>
        `;
  return `
    <div class="modal-backdrop employee-export-modal-backdrop">
      <section class="employee-modal employee-export-modal" role="dialog" aria-modal="true" aria-labelledby="employee-export-title">
        <div class="panel-head">
          <div>
            <h3 id="employee-export-title">Export Selected Employees</h3>
            <div class="panel-meta">Preview and download a case-compatible export bundle.</div>
          </div>
          <button class="icon-button" type="button" data-modal-close="true" aria-label="Close export dialog">×</button>
        </div>
        ${body}
        <div class="modal-actions">
          <button class="secondary-button" type="button" data-modal-close="true">Cancel</button>
          <button class="primary-button" type="button" data-download-export-case="true" ${exportedCase && !employeeExportState.isLoading && !employeeExportState.error ? "" : "disabled"}>Download JSON</button>
        </div>
      </section>
    </div>
  `;
}

function renderEmployees() {
  renderEmployeeList();
  renderEmployeeDetail();
  renderActionCenter();
}

function openCreateEmployee() {
  employeeState.selectedTemplateId = EMPLOYEE_TEMPLATES[0]?.id;
  employeeState.selectedAvatarId = EMPLOYEE_AVATARS[0]?.id || "";
  employeeState.selectedSkillIds = [REQUIRED_EMPLOYEE_SKILL_ID];
  employeeState.recommendedSkillIds = [];
  employeeState.expandedSkillIds = [];
  employeeState.skillRecommendation = defaultSkillRecommendation();
  employeeState.skillRecommendationRequestId += 1;
  employeeState.customRolePrompt = "";
  employeeState.createDraft = createEmployeeDraft(selectedEmployeeTemplate());
  resetCreateWizardState();
  employeeState.isCreateOpen = true;
  renderEmployeeModal();
}

function closeCreateEmployee() {
  if (adminState.busyAction) return;
  employeeState.isCreateOpen = false;
  employeeState.customRolePrompt = "";
  employeeState.createDraft = null;
  resetCreateWizardState();
  employeeState.recommendedSkillIds = [];
  employeeState.skillRecommendation = defaultSkillRecommendation();
  employeeState.skillRecommendationRequestId += 1;
  renderEmployeeModal();
}

function selectEmployee(employeeId) {
  employeeState.selectedEmployeeId = employeeId;
  employeeState.isEmployeeDetailExpanded = false;
  revealSelectedEmployeeInList();
  renderEmployeeList();
  renderEmployeeDetail();
  renderActionCenter();
}

async function actionCenterCompactMainContext() {
  await runMainAgentContextAction("compact");
  renderActionCenter();
}

function actionCenterOpenControl() {
  scrollToNavSection("control-center");
}

function actionCenterScrollToInfrastructure() {
  scrollToNavSection("infrastructure-shell");
}

function actionCenterOpenCases() {
  setResourceHubTab("cases");
  scrollToNavSection("resource-hub");
}

function actionCenterOpenSkills() {
  setResourceHubTab("skills");
  scrollToNavSection("resource-hub");
}

function actionCenterOpenAgentSkills() {
  scrollToNavSection("agent-skills-workbench");
}

function actionCenterOpenEmployee(employeeId) {
  selectEmployee(employeeId);
  scrollToNavSection("employee-studio");
}

function setEmployeeSortMode(mode) {
  const nextMode = normalizeEmployeeSortMode(mode);
  if (nextMode === employeeState.employeeSortMode) return;
  employeeState.employeeSortMode = nextMode;
  writeEmployeeSortMode(nextMode);
  ensureSelectedEmployee();
  revealSelectedEmployeeInList();
  renderEmployees();
  renderOrganization();
}

function renderSmartSkillRecommendToggle() {
  const enabled = Boolean(employeeState.smartSkillRecommendEnabled);
  const button = document.getElementById("smart-skill-recommend-toggle");
  if (!button) return;
  button.classList.toggle("is-on", enabled);
  button.setAttribute("aria-checked", enabled ? "true" : "false");
  const label = button.querySelector(".smart-skill-switch-label");
  if (label) {
    label.textContent = t("button.smart_recommend");
  }
}

function maybeAutoRecommendEmployeeSkills() {
  maybeRecommendSkillsForWizardStep();
}

async function recommendEmployeeSkills() {
  if (!employeeState.isCreateOpen) return;
  const requestId = employeeState.skillRecommendationRequestId + 1;
  employeeState.skillRecommendationRequestId = requestId;
  const draft = ensureCreateEmployeeDraft();
  if (!text(draft.role, "").trim() && !text(draft.system_prompt, "").trim()) return;
  employeeState.skillRecommendation = {
    ...employeeState.skillRecommendation,
    isLoading: true,
    warning: "",
  };
  renderEmployeeModal();
  try {
    const selectedSkills = skillState.localSkills
      .filter((skill) => employeeState.selectedSkillIds.includes(skill.id))
      .map((skill) => skill.name);
    const response = await fetch("/admin/api/employee-skills/recommend", {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
        Accept: "application/json",
      },
      body: JSON.stringify({
        name: text(draft.name, ""),
        role: text(draft.role, ""),
        system_prompt: text(draft.system_prompt, ""),
        skills: selectedSkills,
      }),
    });
    if (!response.ok) {
      const error = await response.json().catch(() => ({ error: { message: `HTTP ${response.status}` } }));
      throw new Error(text(error?.error?.message, `HTTP ${response.status}`));
    }
    const payload = await response.json();
    if (requestId !== employeeState.skillRecommendationRequestId || !employeeState.isCreateOpen) {
      return;
    }
    mergeInstalledRecommendationSkills(Array.isArray(payload?.installed_skills) ? payload.installed_skills : []);
    selectRecommendedSkillIds(Array.isArray(payload?.skill_ids) ? payload.skill_ids : []);
    employeeState.skillRecommendation = {
      isLoading: false,
      reason: text(payload?.reason, ""),
      warning: text(payload?.warning, ""),
      installedSkillIds: normalizeSkillIds(payload?.installed_skill_ids),
      installedSkills: Array.isArray(payload?.installed_skills) ? payload.installed_skills.map(normalizeLocalSkill) : [],
      remoteQueries: normalizeSkillIds(payload?.remote_queries),
    };
  } finally {
    if (requestId === employeeState.skillRecommendationRequestId && employeeState.skillRecommendation.isLoading) {
      employeeState.skillRecommendation = {
        ...employeeState.skillRecommendation,
        isLoading: false,
      };
    }
    renderEmployeeModal();
  }
}

function setSmartSkillRecommendEnabled(enabled) {
  employeeState.smartSkillRecommendEnabled = Boolean(enabled);
  writeSmartSkillRecommendEnabled(employeeState.smartSkillRecommendEnabled);
  renderSmartSkillRecommendToggle();
  if (employeeState.smartSkillRecommendEnabled) {
    maybeAutoRecommendEmployeeSkills();
  }
}

function toggleSmartSkillRecommend() {
  setSmartSkillRecommendEnabled(!employeeState.smartSkillRecommendEnabled);
}

function toggleEmployeeListExpansion() {
  if (employeeItems().length <= EMPLOYEE_LIST_COLLAPSED_COUNT) return;
  employeeState.isEmployeeListExpanded = !employeeState.isEmployeeListExpanded;
  renderEmployeeList();
}

function toggleEmployeeDeleteSelection(employeeId) {
  const normalizedId = text(employeeId, "");
  if (!normalizedId) return;
  if (employeeState.selectedDeleteIds.includes(normalizedId)) {
    employeeState.selectedDeleteIds = employeeState.selectedDeleteIds.filter((id) => id !== normalizedId);
  } else {
    employeeState.selectedDeleteIds = [...employeeState.selectedDeleteIds, normalizedId];
  }
  renderEmployeeList();
}

function toggleAllEmployeeDeleteSelections() {
  const ids = selectableEmployeeIds();
  if (ids.length === 0) return;
  const allSelected = ids.every((id) => employeeState.selectedDeleteIds.includes(id));
  employeeState.selectedDeleteIds = allSelected ? [] : ids;
  renderEmployeeList();
}

function toggleSkillDeleteSelection(skillId) {
  const normalizedId = text(skillId, "");
  if (!normalizedId) return;
  if (skillState.selectedDeleteIds.includes(normalizedId)) {
    skillState.selectedDeleteIds = skillState.selectedDeleteIds.filter((id) => id !== normalizedId);
  } else {
    skillState.selectedDeleteIds = [...skillState.selectedDeleteIds, normalizedId];
  }
  renderLocalSkillList();
}

function toggleAllSkillDeleteSelections() {
  const ids = selectableSkillIds();
  if (ids.length === 0) return;
  const allSelected = ids.every((id) => skillState.selectedDeleteIds.includes(id));
  skillState.selectedDeleteIds = allSelected ? [] : ids;
  renderLocalSkillList();
}

function toggleEmployeeDetailExpansion() {
  employeeState.isEmployeeDetailExpanded = !employeeState.isEmployeeDetailExpanded;
  renderEmployeeDetail();
}

function toggleLocalSkillListExpansion() {
  if (skillState.localSkills.length <= SKILL_LIST_COLLAPSED_COUNT) return;
  skillState.isLocalSkillListExpanded = !skillState.isLocalSkillListExpanded;
  renderLocalSkillList();
}

function toggleLocalSkillLabels(skillId) {
  const normalizedId = text(skillId, "");
  if (!normalizedId) return;
  if (skillState.expandedLocalSkillLabelIds.includes(normalizedId)) {
    skillState.expandedLocalSkillLabelIds = skillState.expandedLocalSkillLabelIds.filter((id) => id !== normalizedId);
  } else {
    skillState.expandedLocalSkillLabelIds = [...skillState.expandedLocalSkillLabelIds, normalizedId];
  }
  renderLocalSkillList();
}

function toggleSkillSearchResultsExpansion() {
  if (skillState.searchResults.length <= SKILL_LIST_COLLAPSED_COUNT) return;
  skillState.isSkillSearchResultsExpanded = !skillState.isSkillSearchResultsExpanded;
  renderSkillSearchPanel();
}

function selectTemplate(templateId) {
  employeeState.selectedTemplateId = templateId;
  employeeState.customRolePrompt = templateId === CUSTOM_ROLE_TEMPLATE_ID ? "" : employeeState.customRolePrompt;
  employeeState.selectedAvatarId = EMPLOYEE_AVATARS[0]?.id || "";
  employeeState.selectedSkillIds = [REQUIRED_EMPLOYEE_SKILL_ID];
  employeeState.recommendedSkillIds = [];
  employeeState.skillRecommendation = defaultSkillRecommendation();
  employeeState.skillRecommendationRequestId += 1;
  employeeState.createDraft = createEmployeeDraft(selectedEmployeeTemplate());
  employeeState.completedCreateWizardSteps = ["template"];
  employeeState.lastSkillRecommendationProfileSignature = "";
  employeeState.createWizardError = "";
  renderEmployeeModal();
}

function selectAvatar(avatarId) {
  if (!getAvatarPreset(avatarId)) return;
  employeeState.selectedAvatarId = avatarId;
  renderEmployeeModal();
}

function toggleLocalSkill(skillId) {
  const normalizedId = text(skillId, "");
  if (!normalizedId) return;
  if (!skillState.localSkills.some((skill) => skill.id === normalizedId)) return;
  if (isRequiredEmployeeSkillId(normalizedId)) {
    ensureRequiredEmployeeSkillSelected();
    renderEmployeeModal();
    return;
  }
  if (employeeState.selectedSkillIds.includes(normalizedId)) {
    employeeState.selectedSkillIds = employeeState.selectedSkillIds.filter((id) => id !== normalizedId);
    employeeState.recommendedSkillIds = employeeState.recommendedSkillIds.filter((id) => id !== normalizedId);
  } else {
    employeeState.selectedSkillIds = [...employeeState.selectedSkillIds, normalizedId];
  }
  renderEmployeeModal();
}

function toggleSkillExpansion(skillId) {
  const normalizedId = text(skillId, "");
  if (!normalizedId) return;
  if (employeeState.expandedSkillIds.includes(normalizedId)) {
    employeeState.expandedSkillIds = employeeState.expandedSkillIds.filter((id) => id !== normalizedId);
  } else {
    employeeState.expandedSkillIds = [...employeeState.expandedSkillIds, normalizedId];
  }
  renderEmployeeModal();
}

function setAgentSkillCreateOpen(open) {
  agentSkillState.isCreateOpen = Boolean(open);
  if (!agentSkillState.isCreateOpen) {
    agentSkillState.createName = "";
    agentSkillState.createDescription = "";
  }
  renderAgentSkillsWorkbench();
}

function setAgentSkillSourceFilter(source) {
  agentSkillState.sourceFilter = ["all", "workspace", "builtin"].includes(source) ? source : "all";
  renderAgentSkillsWorkbench();
}

async function loadAgentSkills() {
  agentSkillState.isLoading = true;
  agentSkillState.error = "";
  renderAgentSkillsWorkbench();
  try {
    const [skillsResponse, proposalsResponse] = await Promise.all([
      fetch(AGENT_SKILLS_ENDPOINT, { headers: { Accept: "application/json" } }),
      fetch(AGENT_SKILL_PROPOSALS_ENDPOINT, { headers: { Accept: "application/json" } }),
    ]);
    if (!skillsResponse.ok) {
      const error = await skillsResponse.json().catch(() => ({ error: { message: `HTTP ${skillsResponse.status}` } }));
      throw new Error(text(error?.error?.message, `HTTP ${skillsResponse.status}`));
    }
    if (!proposalsResponse.ok) {
      const error = await proposalsResponse.json().catch(() => ({ error: { message: `HTTP ${proposalsResponse.status}` } }));
      throw new Error(text(error?.error?.message, `HTTP ${proposalsResponse.status}`));
    }
    const skillsPayload = await skillsResponse.json();
    const proposalsPayload = await proposalsResponse.json();
    agentSkillState.skills = Array.isArray(skillsPayload) ? skillsPayload.map(normalizeAgentSkill) : [];
    agentSkillState.proposals = Array.isArray(proposalsPayload) ? proposalsPayload.map(normalizeAgentSkillProposal) : [];
    if (agentSkillState.selectedName && !agentSkillState.skills.some((skill) => skill.name === agentSkillState.selectedName)) {
      agentSkillState.selectedName = "";
      agentSkillState.selectedDetail = null;
      agentSkillState.isEditing = false;
    }
  } catch (error) {
    agentSkillState.error = text(error.message, "Failed to load agent skills.");
  } finally {
    agentSkillState.isLoading = false;
    renderAgentSkillsWorkbench();
    renderActionCenter();
  }
}

async function refreshAgentSkillProposals() {
  const response = await fetch(AGENT_SKILL_PROPOSALS_ENDPOINT, { headers: { Accept: "application/json" } });
  if (!response.ok) return;
  const payload = await response.json();
  agentSkillState.proposals = Array.isArray(payload) ? payload.map(normalizeAgentSkillProposal) : [];
  renderActionCenter();
  renderAgentSkillsWorkbench();
}

async function selectAgentSkill(name) {
  const normalizedName = text(name, "");
  if (!normalizedName) return;
  agentSkillState.selectedName = normalizedName;
  agentSkillState.isDetailLoading = true;
  agentSkillState.isEditing = false;
  agentSkillState.packageResult = null;
  agentSkillState.error = "";
  renderAgentSkillsWorkbench();
  try {
    const response = await fetch(`${AGENT_SKILLS_ENDPOINT}/${encodeURIComponent(normalizedName)}`, {
      headers: { Accept: "application/json" },
    });
    if (!response.ok) {
      const error = await response.json().catch(() => ({ error: { message: `HTTP ${response.status}` } }));
      throw new Error(text(error?.error?.message, `HTTP ${response.status}`));
    }
    agentSkillState.selectedDetail = normalizeAgentSkillDetail(await response.json());
    agentSkillState.draft = agentSkillState.selectedDetail.markdown;
  } catch (error) {
    agentSkillState.error = text(error.message, "Failed to load agent skill.");
  } finally {
    agentSkillState.isDetailLoading = false;
    renderAgentSkillsWorkbench();
  }
}

async function createAgentSkillFromDraft() {
  const name = text(agentSkillState.createName, "").trim();
  const description = text(agentSkillState.createDescription, "").trim();
  if (!name || !description) {
    throw new Error("Skill name and description are required.");
  }
  setBusyAction({ key: "agent-skill-create", label: "Creating agent skill..." });
  try {
    const response = await fetch(AGENT_SKILLS_ENDPOINT, {
      method: "POST",
      headers: { "Content-Type": "application/json", Accept: "application/json" },
      body: JSON.stringify({ name, description }),
    });
    if (!response.ok) {
      const error = await response.json().catch(() => ({ error: { message: `HTTP ${response.status}` } }));
      throw new Error(text(error?.error?.message, `HTTP ${response.status}`));
    }
    const detail = normalizeAgentSkillDetail(await response.json());
    agentSkillState.selectedName = detail.skill.name;
    agentSkillState.selectedDetail = detail;
    agentSkillState.draft = detail.markdown;
    setAgentSkillCreateOpen(false);
    await loadAgentSkills();
    await selectAgentSkill(detail.skill.name);
  } finally {
    clearBusyAction();
  }
}

function startAgentSkillEdit() {
  if (!agentSkillState.selectedDetail?.skill?.editable) return;
  agentSkillState.isEditing = true;
  agentSkillState.draft = agentSkillState.selectedDetail.markdown;
  renderAgentSkillsWorkbench();
}

function cancelAgentSkillEdit() {
  agentSkillState.isEditing = false;
  agentSkillState.draft = agentSkillState.selectedDetail?.markdown || "";
  renderAgentSkillsWorkbench();
}

async function saveAgentSkill() {
  const name = agentSkillState.selectedDetail?.skill?.name;
  if (!name) return;
  setBusyAction({ key: `agent-skill-save:${name}`, label: "Saving agent skill..." });
  try {
    const response = await fetch(`${AGENT_SKILLS_ENDPOINT}/${encodeURIComponent(name)}`, {
      method: "PUT",
      headers: { "Content-Type": "application/json", Accept: "application/json" },
      body: JSON.stringify({ content: agentSkillState.draft }),
    });
    if (!response.ok) {
      const error = await response.json().catch(() => ({ error: { message: `HTTP ${response.status}` } }));
      throw new Error(text(error?.error?.message, `HTTP ${response.status}`));
    }
    agentSkillState.selectedDetail = normalizeAgentSkillDetail(await response.json());
    agentSkillState.draft = agentSkillState.selectedDetail.markdown;
    agentSkillState.isEditing = false;
    await loadAgentSkills();
    agentSkillState.selectedName = name;
  } finally {
    clearBusyAction();
    renderAgentSkillsWorkbench();
  }
}

async function deleteAgentSkill(name) {
  const normalizedName = text(name, "");
  if (!normalizedName) return;
  if (!window.confirm(`Delete workspace agent skill ${normalizedName}?`)) return;
  setBusyAction({ key: `agent-skill-delete:${normalizedName}`, label: "Deleting agent skill..." });
  try {
    const response = await fetch(`${AGENT_SKILLS_ENDPOINT}/${encodeURIComponent(normalizedName)}`, {
      method: "DELETE",
      headers: { Accept: "application/json" },
    });
    if (!response.ok) {
      const error = await response.json().catch(() => ({ error: { message: `HTTP ${response.status}` } }));
      throw new Error(text(error?.error?.message, `HTTP ${response.status}`));
    }
    agentSkillState.selectedName = "";
    agentSkillState.selectedDetail = null;
    await loadAgentSkills();
  } finally {
    clearBusyAction();
  }
}

async function packageAgentSkill(name) {
  const normalizedName = text(name, "");
  if (!normalizedName) return;
  setBusyAction({ key: `agent-skill-package:${normalizedName}`, label: "Packaging agent skill..." });
  try {
    const response = await fetch(`${AGENT_SKILLS_ENDPOINT}/${encodeURIComponent(normalizedName)}/package`, {
      method: "POST",
      headers: { Accept: "application/json" },
    });
    if (!response.ok) {
      const error = await response.json().catch(() => ({ error: { message: `HTTP ${response.status}` } }));
      throw new Error(text(error?.error?.message, `HTTP ${response.status}`));
    }
    agentSkillState.packageResult = await response.json();
    renderAgentSkillsWorkbench();
  } finally {
    clearBusyAction();
  }
}

async function writeAgentSkillFile() {
  const name = agentSkillState.selectedDetail?.skill?.name;
  if (!name) return;
  setBusyAction({ key: `agent-skill-file:${name}`, label: "Writing agent skill file..." });
  try {
    const response = await fetch(`${AGENT_SKILLS_ENDPOINT}/${encodeURIComponent(name)}/files`, {
      method: "POST",
      headers: { "Content-Type": "application/json", Accept: "application/json" },
      body: JSON.stringify({
        file_path: agentSkillState.filePath,
        content: agentSkillState.fileContent,
      }),
    });
    if (!response.ok) {
      const error = await response.json().catch(() => ({ error: { message: `HTTP ${response.status}` } }));
      throw new Error(text(error?.error?.message, `HTTP ${response.status}`));
    }
    agentSkillState.selectedDetail = normalizeAgentSkillDetail(await response.json());
    agentSkillState.filePath = "";
    agentSkillState.fileContent = "";
  } finally {
    clearBusyAction();
    renderAgentSkillsWorkbench();
  }
}

async function deleteAgentSkillFile(filePath) {
  const name = agentSkillState.selectedDetail?.skill?.name;
  const normalizedPath = text(filePath, "");
  if (!name || !normalizedPath) return;
  const response = await fetch(`${AGENT_SKILLS_ENDPOINT}/${encodeURIComponent(name)}/files?file_path=${encodeURIComponent(normalizedPath)}`, {
    method: "DELETE",
    headers: { Accept: "application/json" },
  });
  if (!response.ok) {
    const error = await response.json().catch(() => ({ error: { message: `HTTP ${response.status}` } }));
    throw new Error(text(error?.error?.message, `HTTP ${response.status}`));
  }
  agentSkillState.selectedDetail = normalizeAgentSkillDetail(await response.json());
  renderAgentSkillsWorkbench();
}

async function approveAgentSkillProposal(proposalId) {
  const normalizedId = text(proposalId, "");
  if (!normalizedId) return;
  const response = await fetch(`${AGENT_SKILL_PROPOSALS_ENDPOINT}/${encodeURIComponent(normalizedId)}/approve`, {
    method: "POST",
    headers: { Accept: "application/json" },
  });
  if (!response.ok) {
    const error = await response.json().catch(() => ({ error: { message: `HTTP ${response.status}` } }));
    throw new Error(text(error?.error?.message, `HTTP ${response.status}`));
  }
  await loadAgentSkills();
}

async function discardAgentSkillProposal(proposalId) {
  const normalizedId = text(proposalId, "");
  if (!normalizedId) return;
  const response = await fetch(`${AGENT_SKILL_PROPOSALS_ENDPOINT}/${encodeURIComponent(normalizedId)}`, {
    method: "DELETE",
    headers: { Accept: "application/json" },
  });
  if (!response.ok) {
    const error = await response.json().catch(() => ({ error: { message: `HTTP ${response.status}` } }));
    throw new Error(text(error?.error?.message, `HTTP ${response.status}`));
  }
  await loadAgentSkills();
}

async function installCatalogSkillToAgentSkills(skillId) {
  const normalizedId = text(skillId, "");
  if (!normalizedId) return;
  setBusyAction({ key: `install-agent-skill:${normalizedId}`, label: "Installing to Agent Skills..." });
  try {
    const response = await fetch(AGENT_SKILLS_ENDPOINT, {
      method: "POST",
      headers: { "Content-Type": "application/json", Accept: "application/json" },
      body: JSON.stringify({ catalog_skill_id: normalizedId }),
    });
    if (!response.ok) {
      const error = await response.json().catch(() => ({ error: { message: `HTTP ${response.status}` } }));
      throw new Error(text(error?.error?.message, `HTTP ${response.status}`));
    }
    const detail = normalizeAgentSkillDetail(await response.json());
    agentSkillState.selectedName = detail.skill.name;
    agentSkillState.selectedDetail = detail;
    agentSkillState.draft = detail.markdown;
    agentSkillState.packageResult = null;
    await loadAgentSkills();
    scrollToNavSection("agent-skills-workbench");
  } finally {
    clearBusyAction();
    renderAgentSkillsWorkbench();
  }
}

async function loadEmployees() {
  const response = await fetch("/employees", { headers: { Accept: "application/json" } });
  if (!response.ok) {
    throw new Error(`Failed to load employees: HTTP ${response.status}`);
  }
  const payload = await response.json();
  employeeState.employees = Array.isArray(payload) ? payload.map(normalizePersistedEmployee) : [];
  const availableEmployeeIds = new Set(selectableEmployeeIds());
  employeeState.selectedDeleteIds = employeeState.selectedDeleteIds.filter((employeeId) => availableEmployeeIds.has(employeeId));
  ensureSelectedEmployee();
  revealSelectedEmployeeInList();
  renderEmployees();
}

async function loadEmployeeConfig(employeeId) {
  const [configResponse, cronResponse] = await Promise.all([
    fetch(employeeConfigEndpoint(employeeId, "/runtime-config"), { headers: { Accept: "application/json" } }),
    fetch(employeeConfigEndpoint(employeeId, "/cron"), { headers: { Accept: "application/json" } }),
  ]);
  if (!configResponse.ok) {
    const error = await configResponse.json().catch(() => ({ error: { message: `HTTP ${configResponse.status}` } }));
    throw new Error(text(error?.error?.message, `HTTP ${configResponse.status}`));
  }
  if (!cronResponse.ok) {
    const error = await cronResponse.json().catch(() => ({ error: { message: `HTTP ${cronResponse.status}` } }));
    throw new Error(text(error?.error?.message, `HTTP ${cronResponse.status}`));
  }
  const config = await configResponse.json();
  const cronJobs = await cronResponse.json();
  employeeConfigState.employeeId = employeeId;
  employeeConfigState.files = Array.isArray(config.files) ? config.files : [];
  employeeConfigState.selectedFile = employeeConfigState.files.some((file) => file.name === employeeConfigState.selectedFile)
    ? employeeConfigState.selectedFile
    : (employeeConfigState.files[0]?.name || EMPLOYEE_CONFIG_FILES[0]);
  employeeConfigState.drafts = {};
  employeeConfigState.isEditing = false;
  employeeConfigState.isLoading = false;
  employeeConfigState.error = "";
  employeeConfigState.restartRequired = Boolean(config.restart_required);
  employeeConfigState.cronJobs = Array.isArray(cronJobs) ? cronJobs : [];
  employeeConfigState.isCronLoading = false;
  employeeConfigState.cronError = "";
  renderEmployees();
}

function selectEmployeeConfigFile(filename) {
  const normalized = text(filename, "");
  if (!EMPLOYEE_CONFIG_FILES.includes(normalized)) return;
  employeeConfigState.selectedFile = normalized;
  employeeConfigState.isEditing = false;
  renderEmployeeDetail();
}

function startEmployeeConfigEdit() {
  const selected = selectedEmployeeConfigFile();
  employeeConfigState.drafts[selected.name] = text(selected.content, "");
  employeeConfigState.isEditing = true;
  renderEmployeeDetail();
}

function cancelEmployeeConfigEdit() {
  const selected = selectedEmployeeConfigFile();
  delete employeeConfigState.drafts[selected.name];
  employeeConfigState.isEditing = false;
  renderEmployeeDetail();
}

function updateEmployeeConfigDraft(value) {
  const selected = selectedEmployeeConfigFile();
  employeeConfigState.drafts[selected.name] = String(value ?? "");
}

async function saveEmployeeConfigFile() {
  const employeeId = employeeConfigState.employeeId;
  const selected = selectedEmployeeConfigFile();
  const content = Object.prototype.hasOwnProperty.call(employeeConfigState.drafts, selected.name)
    ? employeeConfigState.drafts[selected.name]
    : text(selected.content, "");
  const response = await fetch(employeeConfigEndpoint(employeeId, `/runtime-config/${encodeURIComponent(selected.name)}`), {
    method: "PUT",
    headers: {
      "Content-Type": "application/json",
      Accept: "application/json",
    },
    body: JSON.stringify({ content }),
  });
  if (!response.ok) {
    const error = await response.json().catch(() => ({ error: { message: `HTTP ${response.status}` } }));
    throw new Error(text(error?.error?.message, `HTTP ${response.status}`));
  }
  const payload = await response.json();
  employeeConfigState.files = employeeConfigState.files.map((file) => (
    file.name === payload.file?.name ? payload.file : file
  ));
  employeeConfigState.drafts = {};
  employeeConfigState.isEditing = false;
  employeeConfigState.restartRequired = Boolean(payload.restart_required);
  if (payload.employee) {
    const updated = normalizePersistedEmployee(payload.employee);
    employeeState.employees = employeeState.employees.map((employee) => (
      employee.id === updated.id ? updated : employee
    ));
  }
  renderEmployees();
}

function updateEmployeeCronDraft(field, value) {
  employeeConfigState.cronDraft = {
    ...employeeConfigState.cronDraft,
    [field]: value,
  };
}

function editEmployeeCron(jobId) {
  const job = employeeConfigState.cronJobs.find((item) => item.id === jobId);
  if (!job) return;
  employeeConfigState.cronDraft = defaultEmployeeCronDraft({
    id: job.id,
    name: text(job.name, ""),
    message: text(job.payload?.message, ""),
    kind: text(job.schedule?.kind, "every"),
    everyMs: text(job.schedule?.everyMs, "3600000"),
    expr: text(job.schedule?.expr, "0 9 * * *"),
    tz: text(job.schedule?.tz, ""),
    enabled: Boolean(job.enabled),
    deliver: Boolean(job.payload?.deliver),
  });
  renderEmployeeDetail();
}

function employeeCronPayloadFromDraft() {
  const draft = employeeConfigState.cronDraft;
  const schedule = draft.kind === "cron"
    ? { kind: "cron", expr: draft.expr, tz: draft.tz }
    : { kind: "every", everyMs: Number(draft.everyMs || 0) };
  return {
    name: draft.name,
    message: draft.message,
    schedule,
    enabled: Boolean(draft.enabled),
    deliver: Boolean(draft.deliver),
  };
}

async function saveEmployeeCron() {
  const employeeId = employeeConfigState.employeeId;
  const draft = employeeConfigState.cronDraft;
  const isUpdate = Boolean(draft.id);
  const endpoint = employeeConfigEndpoint(employeeId, isUpdate ? `/cron/${encodeURIComponent(draft.id)}` : "/cron");
  const response = await fetch(endpoint, {
    method: isUpdate ? "PUT" : "POST",
    headers: {
      "Content-Type": "application/json",
      Accept: "application/json",
    },
    body: JSON.stringify(employeeCronPayloadFromDraft()),
  });
  if (!response.ok) {
    const error = await response.json().catch(() => ({ error: { message: `HTTP ${response.status}` } }));
    throw new Error(text(error?.error?.message, `HTTP ${response.status}`));
  }
  const saved = await response.json();
  employeeConfigState.cronJobs = [
    saved,
    ...employeeConfigState.cronJobs.filter((job) => job.id !== saved.id),
  ];
  employeeConfigState.cronDraft = defaultEmployeeCronDraft();
  employeeConfigState.cronError = "";
  renderEmployeeDetail();
}

async function deleteEmployeeCron(jobId) {
  const employeeId = employeeConfigState.employeeId;
  const response = await fetch(employeeConfigEndpoint(employeeId, `/cron/${encodeURIComponent(jobId)}`), {
    method: "DELETE",
    headers: { Accept: "application/json" },
  });
  if (!response.ok) {
    const error = await response.json().catch(() => ({ error: { message: `HTTP ${response.status}` } }));
    throw new Error(text(error?.error?.message, `HTTP ${response.status}`));
  }
  employeeConfigState.cronJobs = employeeConfigState.cronJobs.filter((job) => job.id !== jobId);
  if (employeeConfigState.cronDraft.id === jobId) {
    employeeConfigState.cronDraft = defaultEmployeeCronDraft();
  }
  renderEmployeeDetail();
}

function startEmployeePolling() {
  if (employeePollTimer) return;
  employeePollTimer = window.setInterval(async () => {
    try {
      await loadEmployees();
    } catch (error) {
      console.warn("Failed to refresh employees", error);
    }
  }, EMPLOYEE_POLL_INTERVAL_MS);
}

async function loadEmployeeTemplates() {
  const response = await fetch("/employee-templates", { headers: { Accept: "application/json" } });
  if (!response.ok) {
    throw new Error(`Failed to load employee templates: HTTP ${response.status}`);
  }
  const payload = await response.json();
  employeeState.customTemplates = Array.isArray(payload?.templates) ? payload.templates.map(normalizeEmployeeTemplate) : [];
  employeeState.hiddenTemplateIds = Array.isArray(payload?.hiddenTemplateIds)
    ? payload.hiddenTemplateIds.map((item) => text(item, "")).filter(Boolean)
    : [];
  if (!employeeTemplates().some((template) => template.id === employeeState.selectedTemplateId)) {
    employeeState.selectedTemplateId = EMPLOYEE_TEMPLATES[0]?.id;
    employeeState.createDraft = createEmployeeDraft(selectedEmployeeTemplate());
  }
  renderEmployeeModal();
}

async function loadSkills() {
  const response = await fetch("/skills", { headers: { Accept: "application/json" } });
  if (!response.ok) {
    throw new Error(`Failed to load skills: HTTP ${response.status}`);
  }
  const payload = await response.json();
  skillState.localSkills = Array.isArray(payload) ? payload.map(normalizeLocalSkill) : [];
  const availableSkillIds = new Set(skillState.localSkills.map((skill) => skill.id));
  const deletableSkillIds = new Set(selectableSkillIds());
  skillState.selectedDeleteIds = skillState.selectedDeleteIds.filter((skillId) => deletableSkillIds.has(skillId));
  skillState.expandedLocalSkillLabelIds = skillState.expandedLocalSkillLabelIds.filter((skillId) => availableSkillIds.has(skillId));
  employeeState.selectedSkillIds = employeeState.selectedSkillIds.filter((skillId) => availableSkillIds.has(skillId));
  employeeState.recommendedSkillIds = employeeState.recommendedSkillIds.filter((skillId) => availableSkillIds.has(skillId));
  employeeState.expandedSkillIds = employeeState.expandedSkillIds.filter((skillId) => availableSkillIds.has(skillId));
  ensureRequiredEmployeeSkillSelected();
  revealImportedLocalSkillsInList();
  renderSkillCatalog();
  renderEmployeeModal();
}

async function openSkillContent(skillId) {
  const normalizedId = text(skillId, "");
  if (!normalizedId) return;
  const skill = skillState.localSkills.find((item) => item.id === normalizedId) || null;
  skillState.contentModal = {
    ...skillState.contentModal,
    isOpen: true,
    skillId: normalizedId,
    skill,
    markdown: "",
    draft: "",
    isEditing: false,
    isLoading: true,
    error: "",
    contentSource: "",
    canSyncEmployees: false,
    isDirty: false,
    syncedEmployees: 0,
  };
  renderEmployeeModal();
  try {
    const response = await fetch(`/skills/${encodeURIComponent(normalizedId)}/content`, {
      headers: { Accept: "application/json" },
    });
    if (!response.ok) {
      const error = await response.json().catch(() => ({ error: { message: `HTTP ${response.status}` } }));
      throw new Error(text(error?.error?.message, `HTTP ${response.status}`));
    }
    setSkillContentModalPayload(await response.json());
  } catch (error) {
    skillState.contentModal = {
      ...skillState.contentModal,
      isLoading: false,
      error: text(error.message, "Failed to load skill content."),
    };
  }
  renderEmployeeModal();
}

async function openSearchSkillContent(identity) {
  const skill = findSearchSkillByIdentity(identity);
  if (!skill?.source_url) return;
  skillState.contentModal = {
    ...skillState.contentModal,
    isOpen: true,
    skillId: identity,
    skill,
    markdown: "",
    draft: "",
    isEditing: false,
    isLoading: true,
    error: "",
    contentSource: "clawhub",
    canSyncEmployees: false,
    isDirty: false,
    syncedEmployees: 0,
    isSearchPreview: true,
    markdownStatus: "",
    markdownError: "",
  };
  renderEmployeeModal();
  try {
    const response = await fetch(`/skills/search/clawhub/content?source_url=${encodeURIComponent(skill.source_url)}`, {
      headers: { Accept: "application/json" },
    });
    if (!response.ok) {
      const error = await response.json().catch(() => ({ error: { message: `HTTP ${response.status}` } }));
      throw new Error(text(error?.error?.message, `HTTP ${response.status}`));
    }
    const payload = await response.json();
    setSkillContentModalPayload({
      ...payload,
      skill: {
        ...skill,
        ...(payload.skill || {}),
      },
    });
    skillState.contentModal = {
      ...skillState.contentModal,
      isSearchPreview: true,
    };
  } catch (error) {
    skillState.contentModal = {
      ...skillState.contentModal,
      isLoading: false,
      error: text(error.message, "Failed to load skill content."),
      markdownStatus: "error",
    };
  }
  renderEmployeeModal();
}

async function openCaseSkillContent(identity) {
  const skill = findCaseSkillByIdentity(identity);
  if (!skill) return;
  const localSkill = findLocalSkillByIdentity(identity);
  if (localSkill?.id) {
    await openSkillContent(localSkill.id);
    return;
  }
  if (text(skill.markdown, "")) {
    skillState.contentModal = {
      ...skillState.contentModal,
      isOpen: true,
      skillId: identity,
      skill,
      markdown: "",
      draft: "",
      isEditing: false,
      isLoading: false,
      error: "",
      contentSource: "case",
      canSyncEmployees: false,
      isDirty: false,
      syncedEmployees: 0,
      isSearchPreview: false,
      isReadOnlyPreview: true,
      markdownStatus: "ok",
      markdownError: "",
    };
    setSkillContentModalPayload({
      skill,
      markdown: text(skill.markdown, ""),
      content_source: "case",
      can_sync_employees: false,
      synced_employees: 0,
      is_read_only_preview: true,
      markdown_status: "ok",
      markdown_error: "",
    });
    renderEmployeeModal();
    return;
  }
  if (!skill.source_url) return;
  skillState.contentModal = {
    ...skillState.contentModal,
    isOpen: true,
    skillId: identity,
    skill,
    markdown: "",
    draft: "",
    isEditing: false,
    isLoading: true,
    error: "",
    contentSource: text(skill.source || "skill", ""),
    canSyncEmployees: false,
    isDirty: false,
    syncedEmployees: 0,
    isSearchPreview: false,
    isReadOnlyPreview: true,
    markdownStatus: "",
    markdownError: "",
  };
  renderEmployeeModal();
  try {
    const response = await fetch(`/skills/search/clawhub/content?source_url=${encodeURIComponent(skill.source_url)}`, {
      headers: { Accept: "application/json" },
    });
    if (!response.ok) {
      const error = await response.json().catch(() => ({ error: { message: `HTTP ${response.status}` } }));
      throw new Error(text(error?.error?.message, `HTTP ${response.status}`));
    }
    const payload = await response.json();
    setSkillContentModalPayload({
      ...payload,
      skill: {
        ...skill,
        ...(payload.skill || {}),
      },
      is_read_only_preview: true,
    });
    skillState.contentModal = {
      ...skillState.contentModal,
      isSearchPreview: false,
      isReadOnlyPreview: true,
    };
  } catch (error) {
    skillState.contentModal = {
      ...skillState.contentModal,
      isLoading: false,
      error: text(error.message, "Failed to load skill content."),
      markdownStatus: "error",
    };
  }
  renderEmployeeModal();
}

function closeSkillContentModal() {
  if (adminState.busyAction) return;
  resetSkillContentModal();
  renderEmployeeModal();
}

function startSkillContentEdit() {
  if (!skillState.contentModal.isOpen || skillState.contentModal.isLoading) return;
  skillState.contentModal = {
    ...skillState.contentModal,
    isEditing: true,
    draft: skillState.contentModal.markdown,
    isDirty: false,
  };
  renderEmployeeModal();
}

function updateSkillContentDraft(value) {
  if (!skillState.contentModal.isOpen) return;
  const draft = String(value ?? "");
  skillState.contentModal = {
    ...skillState.contentModal,
    draft,
    isDirty: draft !== skillState.contentModal.markdown,
  };
}

function requestSaveSkillContent() {
  const modal = skillState.contentModal;
  if (!modal.isOpen || !modal.isEditing || !modal.isDirty) return;
  if (modal.canSyncEmployees && isRequiredEmployeeSkillId(modal.skillId)) {
    openConfirmAction({
      kind: "save-skill-content",
      title: "Save Required Skill",
      subtitle: "Choose how to apply the updated excellent-employee SKILL.md.",
      message: "Save Only updates the SKILL.md file. Save + Sync Employees also replaces existing employee prompt blocks that already contain this required skill marker.",
      secondaryConfirmLabel: "Save Only",
      confirmLabel: "Save + Sync Employees",
    });
    return;
  }
  saveSkillContent({ syncEmployeePrompts: false }).catch((error) => {
    window.alert(text(error.message, "Failed to save skill content"));
  });
}

async function saveSkillContent({ syncEmployeePrompts = false } = {}) {
  const modal = skillState.contentModal;
  if (!modal.isOpen || !modal.skillId) return;
  const actionKey = `save-skill-content:${modal.skillId}`;
  setBusyAction({ key: actionKey, label: "Saving skill..." });
  try {
    const response = await fetch(`/skills/${encodeURIComponent(modal.skillId)}/content`, {
      method: "PUT",
      headers: {
        "Content-Type": "application/json",
        Accept: "application/json",
      },
      body: JSON.stringify({
        markdown: modal.draft,
        sync_employee_prompts: Boolean(syncEmployeePrompts),
      }),
    });
    if (!response.ok) {
      const error = await response.json().catch(() => ({ error: { message: `HTTP ${response.status}` } }));
      throw new Error(text(error?.error?.message, `HTTP ${response.status}`));
    }
    adminState.confirmAction = null;
    setSkillContentModalPayload(await response.json());
    await loadSkills();
    if (syncEmployeePrompts) {
      await loadEmployees();
    }
  } finally {
    clearBusyAction();
  }
}

async function importSearchSkillFromModal() {
  const modal = skillState.contentModal;
  if (!modal.isOpen || !modal.isSearchPreview || !modal.skill) return;
  const skill = {
    ...modal.skill,
    markdown: modal.markdownStatus === "ok" ? modal.markdown : "",
  };
  const actionKey = `import-search-skill:${modal.skillId}`;
  setBusyAction({ key: actionKey, label: "Importing skill..." });
  try {
    const response = await fetch("/skills/import", {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
        Accept: "application/json",
      },
      body: JSON.stringify({ skills: [skill] }),
    });
    if (!response.ok) {
      const error = await response.json().catch(() => ({ error: { message: `HTTP ${response.status}` } }));
      throw new Error(text(error?.error?.message, `HTTP ${response.status}`));
    }
    skillState.lastImportedSkillIds = importedSkillIdsFromPayload(await response.json());
    resetSkillContentModal();
    await loadSkills();
    companionReact({
      type: "ready",
      bubble: companionPhrase("Skill imported into the local catalog.", "技能已导入本地技能库。"),
    });
  } catch (error) {
    companionReact({
      type: "error",
      bubble: companionPhrase("Skill import failed.", "技能导入失败。"),
    });
    throw error;
  } finally {
    clearBusyAction();
  }
}

function clearSkillPreview({ resetFileInput = false, clearWebUrl = false } = {}) {
  skillState.previewSkill = null;
  skillState.previewLabel = "";
  skillState.previewSource = "";
  if (clearWebUrl) {
    skillState.webImportUrl = "";
  }
  if (resetFileInput) {
    const input = document.getElementById("local-skill-file-input");
    if (input instanceof HTMLInputElement) {
      input.value = "";
    }
  }
  renderSkillCatalog();
}

function openLocalSkillFilePicker() {
  const input = document.getElementById("local-skill-file-input");
  if (!(input instanceof HTMLInputElement)) return;
  input.click();
}

function resetWebSkillPreviewIfNeeded() {
  if (skillState.previewSource !== "web") {
    return;
  }
  skillState.previewSkill = null;
  skillState.previewLabel = "";
  skillState.previewSource = "";
}

function toggleWebSkillImport() {
  if (skillState.isWebImportOpen) {
    skillState.isWebImportOpen = false;
    skillState.webImportUrl = "";
    resetWebSkillPreviewIfNeeded();
    renderSkillCatalog();
    return;
  }
  skillState.isWebImportOpen = true;
  skillState.webImportUrl = "";
  resetWebSkillPreviewIfNeeded();
  const input = document.getElementById("local-skill-file-input");
  if (input instanceof HTMLInputElement) {
    input.value = "";
  }
  renderSkillCatalog();
}

async function cookCustomTemplate() {
  const description = text(employeeState.customRolePrompt, "").trim();
  if (!description) {
    throw new Error("一句话描述你想创建的角色后，再点击 Cook。");
  }
  const draft = ensureCreateEmployeeDraft();
  setBusyAction({ key: "cook-custom-template", label: "Cooking custom role..." });
  try {
    const response = await fetch("/admin/api/employee-templates/cook", {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
        Accept: "application/json",
      },
      body: JSON.stringify({
        description,
        agent_type: text(draft.agent_type, "openclaw"),
      }),
    });
    if (!response.ok) {
      const error = await response.json().catch(() => ({ error: { message: `HTTP ${response.status}` } }));
      throw new Error(text(error?.error?.message, `HTTP ${response.status}`));
    }
    const payload = await response.json();
    employeeState.createDraft = {
      ...draft,
      name: text(payload.name, draft.name),
      role: text(payload.role, draft.role),
      system_prompt: text(payload.system_prompt, draft.system_prompt),
    };
    invalidateCreateWizardStepsFrom("profile");
    employeeState.lastSkillRecommendationProfileSignature = "";
    renderEmployeeModal();
  } finally {
    clearBusyAction();
  }
}

async function saveCustomEmployeeTemplate() {
  const draft = ensureCreateEmployeeDraft();
  const response = await fetch("/employee-templates", {
    method: "POST",
    headers: {
      "Content-Type": "application/json",
      Accept: "application/json",
    },
    body: JSON.stringify({
      defaultName: text(draft.name, ""),
      role: text(draft.role, ""),
      defaultAgentType: text(draft.agent_type, "openclaw"),
      companyStyle: text(employeeState.customRolePrompt, "Custom role template"),
      summary: text(draft.system_prompt, ""),
    }),
  });
  if (!response.ok) {
    const error = await response.json().catch(() => ({ error: { message: `HTTP ${response.status}` } }));
    throw new Error(text(error?.error?.message, `HTTP ${response.status}`));
  }
  const saved = normalizeEmployeeTemplate(await response.json());
  employeeState.customTemplates = [
    saved,
    ...employeeState.customTemplates.filter((template) => template.id !== saved.id),
  ];
  return saved;
}

async function deleteEmployeeTemplate(templateId) {
  const normalizedId = text(templateId, "");
  if (!normalizedId) {
    throw new Error("Template id is required.");
  }
  const actionKey = `delete-template:${normalizedId}`;
  setBusyAction({ key: actionKey, label: "Deleting template..." });
  try {
    const response = await fetch(`/employee-templates/${encodeURIComponent(normalizedId)}`, {
      method: "DELETE",
      headers: { Accept: "application/json" },
    });
    if (!response.ok) {
      const error = await response.json().catch(() => ({ error: { message: `HTTP ${response.status}` } }));
      throw new Error(text(error?.error?.message, `HTTP ${response.status}`));
    }
    adminState.confirmAction = null;
    await loadEmployeeTemplates();
  } finally {
    clearBusyAction();
  }
}

async function loadSoulBannerSkills() {
  const hasExistingResults = skillState.isSoulBannerImportOpen && skillState.soulBannerResults.length > 0;
  skillState.isSoulBannerImportOpen = true;
  skillState.isLoadingSoulBanner = true;
  skillState.isSoulBannerListExpanded = false;
  if (!hasExistingResults) {
    skillState.soulBannerResults = [];
  }
  skillState.selectedSoulBannerKeys = [];
  renderSkillCatalog();
  try {
    const response = await fetch(SOULBANNER_SKILL_SEARCH_ENDPOINT, {
      headers: { Accept: "application/json" },
    });
    if (!response.ok) {
      const error = await response.json().catch(() => ({ error: { message: `HTTP ${response.status}` } }));
      throw new Error(text(error?.error?.message, `HTTP ${response.status}`));
    }
    const payload = await response.json();
    skillState.soulBannerResults = Array.isArray(payload) ? payload.map(normalizeSoulBannerSkillCandidate) : [];
    skillState.selectedSoulBannerKeys = [];
  } finally {
    skillState.isLoadingSoulBanner = false;
    renderSkillCatalog();
  }
}

function toggleSoulBannerSkill(identity) {
  const normalizedIdentity = text(identity, "");
  if (!normalizedIdentity || !findSoulBannerSkillByIdentity(normalizedIdentity)) return;
  if (skillState.selectedSoulBannerKeys.includes(normalizedIdentity)) {
    skillState.selectedSoulBannerKeys = skillState.selectedSoulBannerKeys.filter((item) => item !== normalizedIdentity);
  } else {
    skillState.selectedSoulBannerKeys = [...skillState.selectedSoulBannerKeys, normalizedIdentity];
  }
  renderSkillCatalog();
}

async function importSelectedSoulBannerSkills() {
  const selected = skillState.soulBannerResults.filter((skill) => skillState.selectedSoulBannerKeys.includes(skillIdentity(skill)));
  if (selected.length === 0) return;
  setBusyAction({ key: "import-soulbanner-skills", label: "Importing SoulBanner skills..." });
  try {
    const response = await fetch("/skills/import", {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
        Accept: "application/json",
      },
      body: JSON.stringify({ skills: selected }),
    });
    if (!response.ok) {
      const error = await response.json().catch(() => ({ error: { message: `HTTP ${response.status}` } }));
      throw new Error(text(error?.error?.message, `HTTP ${response.status}`));
    }
    skillState.lastImportedSkillIds = importedSkillIdsFromPayload(await response.json());
    skillState.selectedSoulBannerKeys = [];
    await loadSkills();
    companionReact({
      type: "ready",
      bubble: companionPhrase(`${selected.length} persona skill(s) imported.`, `已导入 ${selected.length} 个人格技能。`),
    });
  } catch (error) {
    companionReact({
      type: "error",
      bubble: companionPhrase("SoulBanner import failed.", "SoulBanner 导入失败。"),
    });
    throw error;
  } finally {
    clearBusyAction();
  }
}

async function loadMbtiSbtiSkills() {
  const hasExistingResults = skillState.isMbtiSbtiImportOpen && skillState.mbtiSbtiResults.length > 0;
  skillState.isMbtiSbtiImportOpen = true;
  skillState.isLoadingMbtiSbti = true;
  skillState.isMbtiSbtiListExpanded = false;
  if (!hasExistingResults) {
    skillState.mbtiSbtiResults = [];
  }
  skillState.selectedMbtiSbtiKeys = [];
  renderSkillCatalog();
  try {
    const response = await fetch(MBTI_SBTI_SKILL_SEARCH_ENDPOINT, {
      headers: { Accept: "application/json" },
    });
    if (!response.ok) {
      const error = await response.json().catch(() => ({ error: { message: `HTTP ${response.status}` } }));
      throw new Error(text(error?.error?.message, `HTTP ${response.status}`));
    }
    const payload = await response.json();
    skillState.mbtiSbtiResults = Array.isArray(payload) ? payload.map(normalizeMbtiSbtiSkillCandidate) : [];
    skillState.selectedMbtiSbtiKeys = [];
  } finally {
    skillState.isLoadingMbtiSbti = false;
    renderSkillCatalog();
  }
}

function toggleMbtiSbtiSkill(identity) {
  const normalizedIdentity = text(identity, "");
  if (!normalizedIdentity || !findMbtiSbtiSkillByIdentity(normalizedIdentity)) return;
  if (skillState.selectedMbtiSbtiKeys.includes(normalizedIdentity)) {
    skillState.selectedMbtiSbtiKeys = skillState.selectedMbtiSbtiKeys.filter((item) => item !== normalizedIdentity);
  } else {
    skillState.selectedMbtiSbtiKeys = [...skillState.selectedMbtiSbtiKeys, normalizedIdentity];
  }
  renderSkillCatalog();
}

async function importSelectedMbtiSbtiSkills() {
  const selected = skillState.mbtiSbtiResults.filter((skill) => skillState.selectedMbtiSbtiKeys.includes(skillIdentity(skill)));
  if (selected.length === 0) return;
  setBusyAction({ key: "import-mbti-sbti-skills", label: "Importing Mbti/Sbti skills..." });
  try {
    const response = await fetch("/skills/import", {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
        Accept: "application/json",
      },
      body: JSON.stringify({ skills: selected }),
    });
    if (!response.ok) {
      const error = await response.json().catch(() => ({ error: { message: `HTTP ${response.status}` } }));
      throw new Error(text(error?.error?.message, `HTTP ${response.status}`));
    }
    skillState.lastImportedSkillIds = importedSkillIdsFromPayload(await response.json());
    skillState.selectedMbtiSbtiKeys = [];
    await loadSkills();
    companionReact({
      type: "ready",
      bubble: companionPhrase(`${selected.length} Mbti/Sbti skill(s) imported.`, `已导入 ${selected.length} 个 Mbti/Sbti 技能。`),
    });
  } catch (error) {
    companionReact({
      type: "error",
      bubble: companionPhrase("Mbti/Sbti import failed.", "Mbti/Sbti 导入失败。"),
    });
    throw error;
  } finally {
    clearBusyAction();
  }
}

async function searchClawHubSkills(query) {
  skillState.searchQuery = text(query, "");
  skillState.isSearching = true;
  skillState.selectedImportKeys = [];
  skillState.isSkillSearchResultsExpanded = false;
  renderSkillCatalog();
  try {
    for (let attempt = 1; attempt <= CLAWHUB_SEARCH_MAX_ATTEMPTS; attempt += 1) {
      let response;
      try {
        response = await fetch(`/skills/search/clawhub?q=${encodeURIComponent(skillState.searchQuery)}`, {
          headers: { Accept: "application/json" },
        });
      } catch (error) {
        if (attempt >= CLAWHUB_SEARCH_MAX_ATTEMPTS) {
          throw error;
        }
        await sleep(CLAWHUB_SEARCH_RETRY_DELAY_MS * attempt);
        continue;
      }
      if (!response.ok) {
        const error = await response.json().catch(() => ({ error: { message: `HTTP ${response.status}` } }));
        const message = text(error?.error?.message, `HTTP ${response.status}`);
        const retryable = response.status === 502 || response.status === 503 || response.status === 504;
        if (retryable && attempt < CLAWHUB_SEARCH_MAX_ATTEMPTS) {
          await sleep(CLAWHUB_SEARCH_RETRY_DELAY_MS * attempt);
          continue;
        }
        throw new Error(message);
      }
      const payload = await response.json();
      skillState.searchResults = Array.isArray(payload) ? payload : [];
      return;
    }
    throw new Error("ClawHub search failed after retries.");
  } finally {
    skillState.isSearching = false;
    renderSkillCatalog();
  }
}

async function importSelectedSkills() {
  const selected = skillState.searchResults.filter((skill) => skillState.selectedImportKeys.includes(skillIdentity(skill)));
  if (selected.length === 0) return;
  setBusyAction({ key: "import-skills", label: "Importing skills..." });
  try {
    const response = await fetch("/skills/import", {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
        Accept: "application/json",
      },
      body: JSON.stringify({ skills: selected }),
    });
    if (!response.ok) {
      const error = await response.json().catch(() => ({ error: { message: `HTTP ${response.status}` } }));
      throw new Error(text(error?.error?.message, `HTTP ${response.status}`));
    }
    skillState.lastImportedSkillIds = importedSkillIdsFromPayload(await response.json());
    skillState.selectedImportKeys = [];
    await loadSkills();
    companionReact({
      type: "ready",
      bubble: companionPhrase(`${selected.length} ClawHub skill(s) imported.`, `已导入 ${selected.length} 个 ClawHub 技能。`),
    });
  } catch (error) {
    companionReact({
      type: "error",
      bubble: companionPhrase("ClawHub skill import failed.", "ClawHub 技能导入失败。"),
    });
    throw error;
  } finally {
    clearBusyAction();
  }
}

async function previewLocalSkillFile(file) {
  if (!(file instanceof File)) return;
  const data = new FormData();
  data.set("file", file, file.name || "SKILL.md");
  skillState.isWebImportOpen = false;
  skillState.webImportUrl = "";
  skillState.previewSkill = null;
  skillState.previewLabel = "";
  skillState.previewSource = "";
  setBusyAction({ key: "preview-local-skill", label: "Analyzing local skill..." });
  try {
    const response = await fetch(LOCAL_SKILL_PREVIEW_ENDPOINT, {
      method: "POST",
      headers: { Accept: "application/json" },
      body: data,
    });
    if (!response.ok) {
      const error = await response.json().catch(() => ({ error: { message: `HTTP ${response.status}` } }));
      throw new Error(text(error?.error?.message, `HTTP ${response.status}`));
    }
    const payload = await response.json();
    if (!payload?.skill || typeof payload.skill !== "object") {
      throw new Error("Local skill preview response is invalid.");
    }
    skillState.previewSkill = normalizeLocalSkill(payload.skill);
    skillState.previewLabel = text(file.name, "SKILL.md");
    skillState.previewSource = "local";
  } finally {
    clearBusyAction();
  }
}

async function previewWebSkillUrl(url) {
  const normalizedUrl = text(url, "").trim();
  if (!normalizedUrl) {
    throw new Error("Enter a public SKILL.md URL.");
  }
  skillState.isWebImportOpen = true;
  skillState.webImportUrl = normalizedUrl;
  skillState.previewSkill = null;
  skillState.previewLabel = "";
  skillState.previewSource = "";
  setBusyAction({ key: "preview-web-skill", label: "Fetching web skill..." });
  try {
    const response = await fetch(WEB_SKILL_PREVIEW_ENDPOINT, {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
        Accept: "application/json",
      },
      body: JSON.stringify({ url: normalizedUrl }),
    });
    if (!response.ok) {
      const error = await response.json().catch(() => ({ error: { message: `HTTP ${response.status}` } }));
      throw new Error(text(error?.error?.message, `HTTP ${response.status}`));
    }
    const payload = await response.json();
    if (!payload?.skill || typeof payload.skill !== "object") {
      throw new Error("Web skill preview response is invalid.");
    }
    skillState.previewSkill = normalizeLocalSkill(payload.skill);
    skillState.previewLabel = normalizedUrl;
    skillState.previewSource = "web";
  } finally {
    clearBusyAction();
  }
}

async function importPreviewedSkill() {
  if (!skillState.previewSkill) return;
  const previewSource = skillState.previewSource;
  setBusyAction({ key: "import-preview-skill", label: "Importing skill..." });
  try {
    const response = await fetch("/skills/import", {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
        Accept: "application/json",
      },
      body: JSON.stringify({ skills: [skillState.previewSkill] }),
    });
    if (!response.ok) {
      const error = await response.json().catch(() => ({ error: { message: `HTTP ${response.status}` } }));
      throw new Error(text(error?.error?.message, `HTTP ${response.status}`));
    }
    skillState.lastImportedSkillIds = importedSkillIdsFromPayload(await response.json());
    clearSkillPreview({ resetFileInput: true, clearWebUrl: previewSource === "web" });
    await loadSkills();
    companionReact({
      type: "ready",
      bubble: companionPhrase("Previewed skill imported.", "预览技能已导入。"),
    });
  } catch (error) {
    companionReact({
      type: "error",
      bubble: companionPhrase("Previewed skill import failed.", "预览技能导入失败。"),
    });
    throw error;
  } finally {
    clearBusyAction();
  }
}

function createEmployeeProgressSnapshot(elapsedMs) {
  let elapsed = Math.max(0, Number(elapsedMs || 0));
  for (const stage of CREATE_EMPLOYEE_PROGRESS_STAGES) {
    if (elapsed <= stage.durationMs) {
      const ratio = stage.durationMs > 0 ? elapsed / stage.durationMs : 1;
      return {
        label: stage.label,
        progress: Math.round(stage.start + ((stage.end - stage.start) * ratio)),
      };
    }
    elapsed -= stage.durationMs;
  }
  const finalEstimate = CREATE_EMPLOYEE_PROGRESS_STAGES[CREATE_EMPLOYEE_PROGRESS_STAGES.length - 1];
  return {
    label: finalEstimate.label,
    progress: finalEstimate.end,
  };
}

function startCreateEmployeeProgress() {
  stopCreateEmployeeProgress();
  const startedAt = Date.now();
  setBusyAction({
    key: "create-employee",
    label: CREATE_EMPLOYEE_PROGRESS_STAGES[0].label,
    progress: 0,
  });
  createEmployeeProgressTimer = window.setInterval(() => {
    updateBusyActionProgress(createEmployeeProgressSnapshot(Date.now() - startedAt));
  }, CREATE_EMPLOYEE_PROGRESS_INTERVAL_MS);
}

function completeCreateEmployeeProgress() {
  updateBusyActionProgress({
    label: "Employee created",
    progress: 100,
  });
}

function stopCreateEmployeeProgress() {
  if (!createEmployeeProgressTimer) return;
  window.clearInterval(createEmployeeProgressTimer);
  createEmployeeProgressTimer = null;
}

async function createEmployeeFromForm(form) {
  const draft = ensureCreateEmployeeDraft();
  if (!validateCreateWizardStep("profile")) {
    employeeState.createWizardStep = "profile";
    renderEmployeeModal();
    return;
  }
  markCreateWizardStepComplete("skills");
  markCreateWizardStepComplete("review");
  const shouldSaveCustomTemplate = employeeState.selectedTemplateId === CUSTOM_ROLE_TEMPLATE_ID;
  const skillIds = selectedEmployeeSkillIdsForPayload();
  const payload = {
    name: text(draft.name, ""),
    avatar: getAvatarPreset(employeeState.selectedAvatarId)?.id || "",
    role: text(draft.role, ""),
    skill_ids: skillIds,
    system_prompt: text(draft.system_prompt, ""),
    agent_type: text(draft.agent_type, ""),
    agent_config: {},
  };
  startCreateEmployeeProgress();
  try {
    const response = await fetch("/employees", {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
        Accept: "application/json",
      },
      body: JSON.stringify(payload),
    });
    if (!response.ok) {
      const error = await response.json().catch(() => ({ error: { message: `HTTP ${response.status}` } }));
      throw new Error(text(error?.error?.message, `HTTP ${response.status}`));
    }
    const created = normalizePersistedEmployee(await response.json());
    completeCreateEmployeeProgress();
    await sleep(250);
    if (shouldSaveCustomTemplate) {
      try {
        await saveCustomEmployeeTemplate();
      } catch (error) {
        window.alert(`Employee created, but failed to save custom template: ${text(error.message)}`);
      }
    }
    employeeState.isCreateOpen = false;
    employeeState.customRolePrompt = "";
    employeeState.createDraft = null;
    employeeState.lastCreateSkillSummary = employeeCreateSkillSummary(skillIds);
    await loadEmployees();
    await loadOrganization();
    employeeState.selectedEmployeeId = created.id;
    organizationState.selectedEmployeeId = created.id;
    revealSelectedEmployeeInList();
    renderEmployees();
    renderOrganization();
    companionReact({
      type: "ready",
      bubble: companionPhrase(
        `${text(created.name, "Employee")} is ready.`,
        `${text(created.name, "数字员工")} 已就绪。`,
      ),
    });
  } catch (error) {
    companionReact({
      type: "error",
      bubble: companionPhrase("Employee creation failed.", "数字员工创建失败。"),
    });
    throw error;
  } finally {
    stopCreateEmployeeProgress();
    clearBusyAction();
  }
}

async function deleteEmployee(employeeId) {
  const actionKey = `delete-employee:${employeeId}`;
  setBusyAction({ key: actionKey, label: "Deleting employee..." });
  try {
    await requestDeleteEmployee(employeeId);
    adminState.confirmAction = null;
    if (employeeState.selectedEmployeeId === employeeId) {
      employeeState.selectedEmployeeId = null;
    }
    employeeState.selectedDeleteIds = employeeState.selectedDeleteIds.filter((id) => id !== employeeId);
    await loadEmployees();
    await loadOrganization();
  } finally {
    clearBusyAction();
  }
}

async function requestDeleteEmployee(employeeId) {
  const response = await fetch(`/employees/${encodeURIComponent(employeeId)}`, {
    method: "DELETE",
    headers: { Accept: "application/json" },
  });
  if (!response.ok) {
    const error = await response.json().catch(() => ({ error: { message: `HTTP ${response.status}` } }));
    throw new Error(text(error?.error?.message, `HTTP ${response.status}`));
  }
}

async function batchDeleteEmployees(employeeIds) {
  const targets = employeeIds.map((id) => text(id, "")).filter(Boolean);
  if (targets.length === 0) return;
  setBusyAction({ key: "delete-employees-batch", label: "Deleting employees..." });
  try {
    for (const employeeId of targets) {
      await requestDeleteEmployee(employeeId);
      employeeState.selectedDeleteIds = employeeState.selectedDeleteIds.filter((id) => id !== employeeId);
      if (employeeState.selectedEmployeeId === employeeId) {
        employeeState.selectedEmployeeId = null;
      }
    }
    adminState.confirmAction = null;
    await loadEmployees();
  } finally {
    clearBusyAction();
  }
}

async function deleteSkill(skillId) {
  if (isRequiredEmployeeSkillId(skillId)) {
    throw new Error("The required employee skill cannot be deleted.");
  }
  const actionKey = `delete-skill:${skillId}`;
  setBusyAction({ key: actionKey, label: "Deleting skill..." });
  try {
    await requestDeleteSkill(skillId);
    adminState.confirmAction = null;
    employeeState.selectedSkillIds = employeeState.selectedSkillIds.filter((id) => id !== skillId);
    employeeState.expandedSkillIds = employeeState.expandedSkillIds.filter((id) => id !== skillId);
    skillState.selectedDeleteIds = skillState.selectedDeleteIds.filter((id) => id !== skillId);
    await loadSkills();
  } finally {
    clearBusyAction();
  }
}

async function requestDeleteSkill(skillId) {
  const response = await fetch(`/skills/${encodeURIComponent(skillId)}`, {
    method: "DELETE",
    headers: { Accept: "application/json" },
  });
  if (!response.ok) {
    const error = await response.json().catch(() => ({ error: { message: `HTTP ${response.status}` } }));
    throw new Error(text(error?.error?.message, `HTTP ${response.status}`));
  }
}

async function batchDeleteSkills(skillIds) {
  const targets = skillIds
    .map((id) => text(id, ""))
    .filter(Boolean)
    .filter((id) => !isRequiredEmployeeSkillId(id));
  if (targets.length === 0) return;
  setBusyAction({ key: "delete-skills-batch", label: "Deleting skills..." });
  try {
    for (const skillId of targets) {
      await requestDeleteSkill(skillId);
      employeeState.selectedSkillIds = employeeState.selectedSkillIds.filter((id) => id !== skillId);
      employeeState.expandedSkillIds = employeeState.expandedSkillIds.filter((id) => id !== skillId);
      skillState.selectedDeleteIds = skillState.selectedDeleteIds.filter((id) => id !== skillId);
    }
    adminState.confirmAction = null;
    await loadSkills();
  } finally {
    clearBusyAction();
  }
}

async function runMainAgentContextAction(action) {
  if (adminState.mainContextAction) return;
  const endpoint = CONTEXT_ACTION_ENDPOINTS[action];
  if (!endpoint) {
    throw new Error("Unsupported context action.");
  }
  const sessionKey = adminState.mainSessionKey;
  if (!sessionKey) {
    throw new Error("No active main-agent session available.");
  }
  setMainContextAction(action);
  try {
    const response = await fetch(endpoint, {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
        Accept: "application/json",
      },
      body: JSON.stringify({ session_key: sessionKey }),
    });
    if (!response.ok) {
      const error = await response.json().catch(() => ({ error: { message: `HTTP ${response.status}` } }));
      throw new Error(text(error?.error?.message, `HTTP ${response.status}`));
    }
    await refreshDashboard();
  } finally {
    clearMainContextAction();
  }
}

async function runEmployeeContextAction(employeeId, action, sessionKey = "", surface = "") {
  const normalizedEmployeeId = text(employeeId, "");
  const normalizedAction = text(action, "");
  if (!normalizedEmployeeId || !["clear", "compact"].includes(normalizedAction)) {
    throw new Error("Unsupported employee context action.");
  }
  if (isEmployeeContextActionBusy(normalizedEmployeeId)) return;
  setEmployeeContextAction(normalizedEmployeeId, normalizedAction, surface);
  try {
    const response = await fetch(`${EMPLOYEE_CONTEXT_ENDPOINT}${encodeURIComponent(normalizedEmployeeId)}/context/${normalizedAction}`, {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
        Accept: "application/json",
      },
      body: JSON.stringify(sessionKey ? { session_key: sessionKey } : {}),
    });
    if (!response.ok) {
      const error = await response.json().catch(() => ({ error: { message: `HTTP ${response.status}` } }));
      throw new Error(text(error?.error?.message, `HTTP ${response.status}`));
    }
    await refreshDashboard();
    if (surface === "dream") {
      await loadDream();
    }
  } finally {
    clearEmployeeContextAction();
  }
}

function renderDockerDaemonSurfaces() {
  renderAlertStrip();
  renderActionCenter();
  renderDockerAgents(adminState.dockerAgents || []);
}

async function repairDockerDaemon() {
  if (adminState.dockerDaemonAction) return;
  adminState.dockerDaemonAction = "repair";
  adminState.dockerDaemonRepairResult = "";
  renderDockerDaemonSurfaces();
  try {
    const response = await fetch(DOCKER_DAEMON_REPAIR_ENDPOINT, {
      method: "POST",
      headers: { Accept: "application/json" },
    });
    const payload = await response.json().catch(() => ({}));
    if (!response.ok) {
      throw new Error(text(payload?.error?.message, `HTTP ${response.status}`));
    }
    if (payload?.dockerDaemon) {
      adminState.dockerDaemon = payload.dockerDaemon;
    }
    adminState.dockerDaemonRepairResult = text(payload?.message, "");
    await refreshDashboard();
  } finally {
    adminState.dockerDaemonAction = null;
    renderDockerDaemonSurfaces();
  }
}

async function deleteRuntimeDocker(containerName) {
  const actionKey = `delete-docker:${containerName}`;
  setBusyAction({ key: actionKey, label: `Deleting Docker ${containerName}...` });
  try {
    const response = await fetch(`${DOCKER_CONTAINERS_ENDPOINT}${encodeURIComponent(containerName)}`, {
      method: "DELETE",
      headers: { Accept: "application/json" },
    });
    if (!response.ok) {
      const error = await response.json().catch(() => ({ error: { message: `HTTP ${response.status}` } }));
      throw new Error(text(error?.error?.message, `HTTP ${response.status}`));
    }
    adminState.confirmAction = null;
    await refreshDashboard();
  } finally {
    clearBusyAction();
  }
}

function initEmployeeInteractions() {
  renderHeroBar();
  renderAlertStrip();
  renderActionCenter();
  renderResourceHubTabs();
  renderNavSectionLinks();
  renderCaseCarousel();
  renderEmployees();
  renderEmployeeModal();
  renderSkillCatalog();
  renderAgentSkillsWorkbench();
  renderSmartSkillRecommendToggle();
  renderDreamPanel();
  document.getElementById("create-employee-button")?.addEventListener("click", openCreateEmployee);
  document.getElementById("smart-skill-recommend-toggle")?.addEventListener("click", toggleSmartSkillRecommend);
  document.querySelector("[data-organization-refresh]")?.addEventListener("click", () => {
    loadOrganization().catch((error) => {
      organizationState.error = text(error.message, "Failed to refresh organization");
      organizationState.isLoading = false;
      renderOrganization();
    });
  });
  document.querySelector("[data-organization-save]")?.addEventListener("click", () => {
    saveOrganization().catch((error) => {
      organizationState.error = text(error.message, "Failed to save organization");
      organizationState.isSaving = false;
      renderOrganization();
    });
  });
  document.getElementById("admin-language-zh")?.addEventListener("click", () => applyLanguage("zh"));
  document.getElementById("admin-language-en")?.addEventListener("click", () => applyLanguage("en"));
  document.getElementById("admin-theme-toggle")?.addEventListener("click", () => applyTheme(currentTheme() === "dark" ? "light" : "dark"));
  window.addEventListener("scroll", requestNavSectionSync, { passive: true });
  window.addEventListener("resize", () => {
    requestNavSectionSync();
    requestCaseDetailViewportSync();
  });
  if (window.visualViewport) {
    window.visualViewport.addEventListener("resize", requestCaseDetailViewportSync);
    window.visualViewport.addEventListener("scroll", requestCaseDetailViewportSync, { passive: true });
  }
  observeNavSections();
  document.addEventListener("click", (event) => {
    if (!(event.target instanceof Element)) return;
    const navSectionLink = event.target.closest("[data-nav-target]");
    if (navSectionLink) {
      event.preventDefault();
      scrollToNavSection(navSectionLink.getAttribute("data-nav-target"));
      return;
    }
    const mainTranscriptButton = event.target.closest("[data-transcript-main]");
    if (mainTranscriptButton) {
      openMainAgentTranscript();
      return;
    }
    const resourceTabButton = event.target.closest("[data-resource-tab]");
    if (resourceTabButton) {
      setResourceHubTab(resourceTabButton.getAttribute("data-resource-tab"));
      return;
    }
    const runtimeHistoryRefreshButton = event.target.closest("[data-runtime-history-refresh]");
    if (runtimeHistoryRefreshButton) {
      loadRuntimeHistory();
      return;
    }
    const organizationSelectButton = event.target.closest("[data-organization-select]");
    if (organizationSelectButton) {
      selectOrganizationEmployee(organizationSelectButton.getAttribute("data-organization-select"));
      return;
    }
    const organizationConnectButton = event.target.closest("[data-organization-connect]");
    if (organizationConnectButton) {
      startOrganizationConnection(organizationConnectButton.getAttribute("data-organization-connect"));
      return;
    }
    const organizationRemoveManagerButton = event.target.closest("[data-organization-remove-manager]");
    if (organizationRemoveManagerButton) {
      setOrganizationManager(organizationRemoveManagerButton.getAttribute("data-organization-remove-manager"), "");
      return;
    }
    const organizationSkillToggleButton = event.target.closest("[data-organization-skill-toggle]");
    if (organizationSkillToggleButton) {
      organizationState.isSkillListExpanded = !organizationState.isSkillListExpanded;
      renderOrganization();
      return;
    }
    const dreamRefreshButton = event.target.closest("[data-dream-refresh]");
    if (dreamRefreshButton) {
      loadDream().catch((error) => {
        dreamState.error = text(error.message, "Failed to refresh Dream");
        renderDreamPanel();
      });
      return;
    }
    const dreamRunButton = event.target.closest("[data-dream-run]");
    if (dreamRunButton) {
      runSelectedDream().catch((error) => {
        dreamState.error = text(error.message, "Failed to run Dream");
        renderDreamPanel();
      });
      return;
    }
    const dreamSubjectButton = event.target.closest("[data-dream-subject]");
    if (dreamSubjectButton) {
      loadDreamSubject(dreamSubjectButton.getAttribute("data-dream-subject")).catch((error) => {
        dreamState.error = text(error.message, "Failed to open Dream subject");
        renderDreamPanel();
      });
      return;
    }
    const dreamFileButton = event.target.closest("[data-dream-file]");
    if (dreamFileButton) {
      selectDreamFile(dreamFileButton.getAttribute("data-dream-file"));
      return;
    }
    const dreamCommitButton = event.target.closest("[data-dream-commit]");
    if (dreamCommitButton) {
      selectDreamCommit(dreamCommitButton.getAttribute("data-dream-commit"));
      return;
    }
    const dreamRestoreButton = event.target.closest("[data-dream-restore]");
    if (dreamRestoreButton) {
      requestDreamRestore();
      return;
    }
    const dreamContextButton = event.target.closest("[data-dream-context-action]");
    if (dreamContextButton) {
      runEmployeeContextAction(
        dreamContextButton.getAttribute("data-employee-context-id"),
        dreamContextButton.getAttribute("data-dream-context-action"),
        dreamContextButton.getAttribute("data-employee-context-session"),
        "dream",
      ).catch((error) => {
        dreamState.error = text(error.message, "Failed to update employee context");
        renderDreamPanel();
      });
      return;
    }
    if (handleEmployeeOpsAction(event)) {
      return;
    }
    const createWizardNextButton = event.target.closest("[data-create-wizard-next]");
    if (createWizardNextButton) {
      event.preventDefault();
      advanceCreateWizardStep();
      return;
    }
    const createWizardBackButton = event.target.closest("[data-create-wizard-back]");
    if (createWizardBackButton) {
      event.preventDefault();
      retreatCreateWizardStep();
      return;
    }
    const createWizardStepButton = event.target.closest("[data-create-wizard-go]");
    if (createWizardStepButton) {
      event.preventDefault();
      setCreateWizardStep(createWizardStepButton.getAttribute("data-create-wizard-go"));
      return;
    }
    const actionCenterCompactButton = event.target.closest("[data-action-center-compact]");
    if (actionCenterCompactButton) {
      actionCenterCompactMainContext().catch((error) => {
        window.alert(text(error.message, "Failed to compact context"));
      });
      return;
    }
    const actionCenterControlButton = event.target.closest("[data-action-center-control]");
    if (actionCenterControlButton) {
      actionCenterOpenControl();
      return;
    }
    const actionCenterInfrastructureButton = event.target.closest("[data-action-center-infrastructure]");
    if (actionCenterInfrastructureButton) {
      actionCenterScrollToInfrastructure();
      return;
    }
    const actionCenterDockerRepairButton = event.target.closest("[data-action-center-docker-repair]");
    if (actionCenterDockerRepairButton) {
      repairDockerDaemon().catch((error) => {
        window.alert(text(error.message, "Failed to repair Docker daemon"));
      });
      return;
    }
    const actionCenterCasesButton = event.target.closest("[data-action-center-cases]");
    if (actionCenterCasesButton) {
      actionCenterOpenCases();
      return;
    }
    const actionCenterSkillsButton = event.target.closest("[data-action-center-skills]");
    if (actionCenterSkillsButton) {
      actionCenterOpenSkills();
      return;
    }
    const actionCenterAgentSkillsButton = event.target.closest("[data-action-center-agent-skills]");
    if (actionCenterAgentSkillsButton) {
      actionCenterOpenAgentSkills();
      return;
    }
    const actionCenterEmployeeButton = event.target.closest("[data-action-center-employee]");
    if (actionCenterEmployeeButton) {
      actionCenterOpenEmployee(actionCenterEmployeeButton.getAttribute("data-action-center-employee"));
      return;
    }
    const actionCenterCreateButton = event.target.closest("[data-action-center-create]");
    if (actionCenterCreateButton) {
      openCreateEmployee();
      return;
    }
    const dockerTranscriptButton = event.target.closest("[data-transcript-docker]");
    if (dockerTranscriptButton) {
      openDockerAgentTranscript(dockerTranscriptButton.getAttribute("data-transcript-docker"));
      return;
    }
    const dockerContextButton = event.target.closest("[data-docker-context-action]");
    if (dockerContextButton) {
      runEmployeeContextAction(
        dockerContextButton.getAttribute("data-employee-context-id"),
        dockerContextButton.getAttribute("data-docker-context-action"),
        dockerContextButton.getAttribute("data-employee-context-session"),
        "infrastructure",
      ).catch((error) => {
        window.alert(text(error.message, "Failed to update Docker agent context"));
      });
      return;
    }
    const dockerDaemonRepairButton = event.target.closest("[data-docker-daemon-repair]");
    if (dockerDaemonRepairButton) {
      repairDockerDaemon().catch((error) => {
        window.alert(text(error.message, "Failed to repair Docker daemon"));
      });
      return;
    }
    const caseOpsScanButton = event.target.closest("[data-case-ops-scan]");
    if (caseOpsScanButton) {
      scanCaseOps().catch((error) => {
        caseOpsState.error = text(error.message, "Failed to scan cases.");
        renderCaseCarousel();
      });
      return;
    }
    const caseOpsIssueToggle = event.target.closest("[data-case-ops-issue]");
    if (caseOpsIssueToggle) {
      toggleCaseOpsIssueSelection(caseOpsIssueToggle.getAttribute("data-case-ops-issue"));
      return;
    }
    const caseOpsIgnoreButton = event.target.closest("[data-case-ops-ignore]");
    if (caseOpsIgnoreButton) {
      setCaseOpsIssueIgnored(
        caseOpsIgnoreButton.getAttribute("data-case-ops-ignore"),
        caseOpsIgnoreButton.getAttribute("data-case-ops-ignore-value") === "true",
      ).catch((error) => {
        caseOpsState.error = text(error.message, "Failed to update case issue.");
        renderCaseCarousel();
      });
      return;
    }
    const caseOpsActionButton = event.target.closest("[data-case-ops-action]");
    if (caseOpsActionButton) {
      requestCaseOpsAction(caseOpsActionButton.getAttribute("data-case-ops-action"));
      return;
    }
    const caseOpsCancelPreviewButton = event.target.closest("[data-case-ops-cancel-preview]");
    if (caseOpsCancelPreviewButton) {
      caseOpsState.preview = null;
      renderCaseCarousel();
      return;
    }
    const caseOpsConfirmButton = event.target.closest("[data-case-ops-confirm]");
    if (caseOpsConfirmButton) {
      confirmCaseOpsAction();
      return;
    }
    const caseOpsOpportunityButton = event.target.closest("[data-case-ops-opportunity]");
    if (caseOpsOpportunityButton) {
      handleCaseOpsOpportunity(caseOpsOpportunityButton.getAttribute("data-case-ops-opportunity"));
      return;
    }
    const caseOpsOpenCaseButton = event.target.closest("[data-case-ops-open-case]");
    if (caseOpsOpenCaseButton) {
      openCaseDetail(caseOpsOpenCaseButton.getAttribute("data-case-ops-open-case"));
      return;
    }
    const caseOpsImportConfigButton = event.target.closest("[data-case-ops-import-config]");
    if (caseOpsImportConfigButton) {
      openCaseConfigFilePicker().catch((error) => {
        window.alert(text(error.message, "Failed to import case config"));
      });
      return;
    }
    const caseCardButton = event.target.closest("[data-case-id]");
    if (caseCardButton) {
      openCaseDetail(caseCardButton.getAttribute("data-case-id"));
      return;
    }
    const importCaseConfigButton = event.target.closest("[data-import-case-config]");
    if (importCaseConfigButton) {
      openCaseConfigFilePicker().catch((error) => {
        window.alert(text(error.message, "Failed to import case config"));
      });
      return;
    }
    const casePreviewButton = event.target.closest("[data-case-preview-import]");
    if (casePreviewButton) {
      previewCaseImport(casePreviewButton.getAttribute("data-case-preview-import")).catch((error) => {
        window.alert(text(error.message, "Failed to preview case import"));
      });
      return;
    }
    const caseImportButton = event.target.closest("[data-case-confirm-import]");
    if (caseImportButton) {
      confirmCaseImport(caseImportButton.getAttribute("data-case-confirm-import")).catch((error) => {
        window.alert(text(error.message, "Failed to import case"));
      });
      return;
    }
    const contextActionButton = event.target.closest("[data-main-context-action]");
    if (contextActionButton) {
      runMainAgentContextAction(contextActionButton.getAttribute("data-main-context-action")).catch((error) => {
        window.alert(text(error.message, "Failed to update context"));
      });
      return;
    }
    const dockerDeleteButton = event.target.closest("[data-delete-docker]");
    if (dockerDeleteButton) {
      const containerName = dockerDeleteButton.getAttribute("data-delete-docker");
      openConfirmAction({
        kind: "delete-docker",
        containerName,
        title: "Delete Docker Container",
        subtitle: "This will force remove the running container.",
        message: `Delete Docker container ${containerName}? Running workloads will be interrupted immediately.`,
        confirmLabel: "Delete Docker",
      });
      return;
    }
    const dockerDeleteCardButton = event.target.closest("[data-delete-docker-card]");
    if (dockerDeleteCardButton) {
      const containerName = dockerDeleteCardButton.getAttribute("data-delete-docker-card");
      openConfirmAction({
        kind: "delete-docker",
        containerName,
        title: "Delete Docker Container",
        subtitle: "This will force remove the running container.",
        message: `Delete Docker container ${containerName}? Running workloads will be interrupted immediately.`,
        confirmLabel: "Delete Docker",
      });
      return;
    }
    const employeeDeleteCardButton = event.target.closest("[data-delete-employee-card]");
    if (employeeDeleteCardButton) {
      const employeeId = employeeDeleteCardButton.getAttribute("data-delete-employee-card");
      const employee = employeeItems().find((item) => item.id === employeeId);
      openConfirmAction({
        kind: "delete-employee",
        employeeId,
        title: "Delete Employee",
        subtitle: "This will remove the persisted employee.",
        message: `Delete employee ${text(employee?.name, employeeId)}? This action cannot be undone.`,
        confirmLabel: "Delete Employee",
      });
      return;
    }
    const employeeBatchToggle = event.target.closest("[data-employee-delete-toggle]");
    if (employeeBatchToggle) {
      toggleEmployeeDeleteSelection(employeeBatchToggle.getAttribute("data-employee-delete-toggle"));
      return;
    }
    const toggleAllEmployeesButton = event.target.closest("[data-toggle-all-employees]");
    if (toggleAllEmployeesButton) {
      toggleAllEmployeeDeleteSelections();
      return;
    }
    const deleteSelectedEmployeesButton = event.target.closest("[data-delete-selected-employees]");
    if (deleteSelectedEmployeesButton) {
      openConfirmAction({
        kind: "delete-employees",
        employeeIds: [...employeeState.selectedDeleteIds],
        title: "Delete Selected Employees",
        subtitle: "This will remove the selected persisted employees.",
        message: `Delete ${employeeState.selectedDeleteIds.length} employees? This action cannot be undone.`,
        confirmLabel: "Delete Employees",
      });
      return;
    }
    const exportSelectedEmployeesButton = event.target.closest("[data-export-selected-employees]");
    if (exportSelectedEmployeesButton) {
      openEmployeeExportModal().catch((error) => {
        window.alert(text(error.message, "Failed to export selected employees"));
      });
      return;
    }
    const employeeListToggle = event.target.closest("[data-toggle-employee-list]");
    if (employeeListToggle) {
      toggleEmployeeListExpansion();
      return;
    }
    const employeeDetailToggle = event.target.closest("[data-toggle-employee-detail]");
    if (employeeDetailToggle) {
      toggleEmployeeDetailExpansion();
      return;
    }
    const configFileButton = event.target.closest("[data-employee-config-file]");
    if (configFileButton) {
      selectEmployeeConfigFile(configFileButton.getAttribute("data-employee-config-file"));
      return;
    }
    const configEditButton = event.target.closest("[data-employee-config-edit]");
    if (configEditButton) {
      startEmployeeConfigEdit();
      return;
    }
    const configCancelButton = event.target.closest("[data-employee-config-cancel]");
    if (configCancelButton) {
      cancelEmployeeConfigEdit();
      return;
    }
    const configSaveButton = event.target.closest("[data-employee-config-save]");
    if (configSaveButton) {
      saveEmployeeConfigFile().catch((error) => {
        window.alert(text(error.message, "Failed to save employee config"));
      });
      return;
    }
    const cronSaveButton = event.target.closest("[data-employee-cron-save]");
    if (cronSaveButton) {
      saveEmployeeCron().catch((error) => {
        employeeConfigState.cronError = text(error.message, "Failed to save employee cron");
        renderEmployeeDetail();
      });
      return;
    }
    const cronNewButton = event.target.closest("[data-employee-cron-new]");
    if (cronNewButton) {
      employeeConfigState.cronDraft = defaultEmployeeCronDraft();
      renderEmployeeDetail();
      return;
    }
    const cronEditButton = event.target.closest("[data-employee-cron-edit]");
    if (cronEditButton) {
      editEmployeeCron(cronEditButton.getAttribute("data-employee-cron-edit"));
      return;
    }
    const cronDeleteButton = event.target.closest("[data-employee-cron-delete]");
    if (cronDeleteButton) {
      deleteEmployeeCron(cronDeleteButton.getAttribute("data-employee-cron-delete")).catch((error) => {
        employeeConfigState.cronError = text(error.message, "Failed to delete employee cron");
        renderEmployeeDetail();
      });
      return;
    }
    const localSkillListToggle = event.target.closest("[data-toggle-local-skill-list]");
    if (localSkillListToggle) {
      toggleLocalSkillListExpansion();
      return;
    }
    const skillSearchResultsToggle = event.target.closest("[data-toggle-skill-search-results]");
    if (skillSearchResultsToggle) {
      toggleSkillSearchResultsExpansion();
      return;
    }
    const skillOpsScanButton = event.target.closest("[data-skill-ops-scan]");
    if (skillOpsScanButton) {
      scanSkillGovernance({ includeRemote: false }).catch((error) => {
        skillOpsState.error = text(error.message, "Failed to scan skill governance.");
        renderSkillOpsPanel();
      });
      return;
    }
    const skillOpsRemoteButton = event.target.closest("[data-skill-ops-remote]");
    if (skillOpsRemoteButton) {
      scanSkillGovernance({ includeRemote: true }).catch((error) => {
        skillOpsState.error = text(error.message, "Failed to scan skill governance.");
        renderSkillOpsPanel();
      });
      return;
    }
    const skillOpsFoldToggle = event.target.closest("[data-skill-ops-toggle-fold]");
    if (skillOpsFoldToggle) {
      setSkillOpsIssueListExpanded(skillOpsFoldToggle.getAttribute("data-skill-ops-toggle-fold") === "true");
      return;
    }
    const skillOpsSelectAll = event.target.closest("[data-skill-ops-select-all]");
    if (skillOpsSelectAll) {
      toggleSkillOpsAllIssuesSelection(skillOpsSelectAll.checked);
      return;
    }
    const skillOpsIssueToggle = event.target.closest("[data-skill-ops-issue]");
    if (skillOpsIssueToggle) {
      toggleSkillOpsIssueSelection(skillOpsIssueToggle.getAttribute("data-skill-ops-issue"));
      return;
    }
    const skillOpsIgnoreSelectedButton = event.target.closest("[data-skill-ops-ignore-selected]");
    if (skillOpsIgnoreSelectedButton) {
      ignoreSelectedSkillOpsIssues().catch((error) => {
        skillOpsState.error = text(error.message, "Failed to update issues.");
        renderSkillOpsPanel();
      });
      return;
    }
    const skillOpsIgnoreButton = event.target.closest("[data-skill-ops-ignore]");
    if (skillOpsIgnoreButton) {
      setSkillOpsIssueIgnored(
        skillOpsIgnoreButton.getAttribute("data-skill-ops-ignore"),
        skillOpsIgnoreButton.getAttribute("data-skill-ops-ignore-value") === "true",
      ).catch((error) => {
        skillOpsState.error = text(error.message, "Failed to update issue.");
        renderSkillOpsPanel();
      });
      return;
    }
    const skillOpsActionButton = event.target.closest("[data-skill-ops-action]");
    if (skillOpsActionButton) {
      requestSkillOpsAction(skillOpsActionButton.getAttribute("data-skill-ops-action"));
      return;
    }
    const skillOpsCancelPreviewButton = event.target.closest("[data-skill-ops-cancel-preview]");
    if (skillOpsCancelPreviewButton) {
      skillOpsState.preview = null;
      renderSkillOpsPanel();
      return;
    }
    const skillOpsConfirmButton = event.target.closest("[data-skill-ops-confirm]");
    if (skillOpsConfirmButton) {
      confirmSkillOpsAction();
      return;
    }
    const skillOpsOpportunityButton = event.target.closest("[data-skill-ops-opportunity]");
    if (skillOpsOpportunityButton) {
      handleSkillOpsOpportunity(skillOpsOpportunityButton.getAttribute("data-skill-ops-opportunity"));
      return;
    }
    const agentSkillsRefreshButton = event.target.closest("[data-agent-skills-refresh]");
    if (agentSkillsRefreshButton) {
      loadAgentSkills().catch((error) => {
        agentSkillState.error = text(error.message, "Failed to refresh agent skills.");
        renderAgentSkillsWorkbench();
      });
      return;
    }
    const agentSkillCreateButton = event.target.closest("[data-agent-skill-create]");
    if (agentSkillCreateButton) {
      setAgentSkillCreateOpen(true);
      scrollToNavSection("agent-skills-workbench");
      return;
    }
    const agentSkillCreateCancelButton = event.target.closest("[data-agent-skill-create-cancel]");
    if (agentSkillCreateCancelButton) {
      setAgentSkillCreateOpen(false);
      return;
    }
    const agentSkillCreateSubmitButton = event.target.closest("[data-agent-skill-create-submit]");
    if (agentSkillCreateSubmitButton) {
      createAgentSkillFromDraft().catch((error) => {
        agentSkillState.error = text(error.message, "Failed to create agent skill.");
        renderAgentSkillsWorkbench();
      });
      return;
    }
    const agentSkillFilterButton = event.target.closest("[data-agent-skill-source-filter]");
    if (agentSkillFilterButton) {
      setAgentSkillSourceFilter(agentSkillFilterButton.getAttribute("data-agent-skill-source-filter"));
      return;
    }
    const agentSkillSelectButton = event.target.closest("[data-agent-skill-select]");
    if (agentSkillSelectButton) {
      selectAgentSkill(agentSkillSelectButton.getAttribute("data-agent-skill-select"));
      return;
    }
    const agentSkillEditButton = event.target.closest("[data-agent-skill-edit]");
    if (agentSkillEditButton) {
      startAgentSkillEdit();
      return;
    }
    const agentSkillCancelEditButton = event.target.closest("[data-agent-skill-cancel-edit]");
    if (agentSkillCancelEditButton) {
      cancelAgentSkillEdit();
      return;
    }
    const agentSkillSaveButton = event.target.closest("[data-agent-skill-save]");
    if (agentSkillSaveButton) {
      saveAgentSkill().catch((error) => {
        agentSkillState.error = text(error.message, "Failed to save agent skill.");
        renderAgentSkillsWorkbench();
      });
      return;
    }
    const agentSkillDeleteButton = event.target.closest("[data-agent-skill-delete]");
    if (agentSkillDeleteButton) {
      deleteAgentSkill(agentSkillDeleteButton.getAttribute("data-agent-skill-delete")).catch((error) => {
        agentSkillState.error = text(error.message, "Failed to delete agent skill.");
        renderAgentSkillsWorkbench();
      });
      return;
    }
    const agentSkillPackageButton = event.target.closest("[data-agent-skill-package]");
    if (agentSkillPackageButton) {
      packageAgentSkill(agentSkillPackageButton.getAttribute("data-agent-skill-package")).catch((error) => {
        agentSkillState.error = text(error.message, "Failed to package agent skill.");
        renderAgentSkillsWorkbench();
      });
      return;
    }
    const agentSkillWriteFileButton = event.target.closest("[data-agent-skill-write-file]");
    if (agentSkillWriteFileButton) {
      writeAgentSkillFile().catch((error) => {
        agentSkillState.error = text(error.message, "Failed to write agent skill file.");
        renderAgentSkillsWorkbench();
      });
      return;
    }
    const agentSkillDeleteFileButton = event.target.closest("[data-agent-skill-delete-file]");
    if (agentSkillDeleteFileButton) {
      deleteAgentSkillFile(agentSkillDeleteFileButton.getAttribute("data-agent-skill-delete-file")).catch((error) => {
        agentSkillState.error = text(error.message, "Failed to delete agent skill file.");
        renderAgentSkillsWorkbench();
      });
      return;
    }
    const agentSkillProposalApproveButton = event.target.closest("[data-agent-skill-proposal-approve]");
    if (agentSkillProposalApproveButton) {
      approveAgentSkillProposal(agentSkillProposalApproveButton.getAttribute("data-agent-skill-proposal-approve")).catch((error) => {
        agentSkillState.error = text(error.message, "Failed to approve proposal.");
        renderAgentSkillsWorkbench();
      });
      return;
    }
    const agentSkillProposalDiscardButton = event.target.closest("[data-agent-skill-proposal-discard]");
    if (agentSkillProposalDiscardButton) {
      discardAgentSkillProposal(agentSkillProposalDiscardButton.getAttribute("data-agent-skill-proposal-discard")).catch((error) => {
        agentSkillState.error = text(error.message, "Failed to discard proposal.");
        renderAgentSkillsWorkbench();
      });
      return;
    }
    const employeeButton = event.target.closest("[data-employee-id]");
    if (employeeButton) {
      selectEmployee(employeeButton.getAttribute("data-employee-id"));
      return;
    }
    const deleteButton = event.target.closest("[data-delete-employee]");
    if (deleteButton) {
      deleteEmployee(deleteButton.getAttribute("data-delete-employee")).catch((error) => {
        window.alert(text(error.message, "Failed to delete employee"));
      });
      return;
    }
    const deleteSkillButton = event.target.closest("[data-delete-skill-id]");
    if (deleteSkillButton) {
      const skillId = deleteSkillButton.getAttribute("data-delete-skill-id");
      const skill = skillState.localSkills.find((item) => item.id === skillId);
      openConfirmAction({
        kind: "delete-skill",
        skillId,
        title: "Delete Skill",
        subtitle: "This will remove the skill from the local catalog.",
        message: `Delete skill ${text(skill?.name, skillId)}? Employees already using this skill will keep their current text tags.`,
        confirmLabel: "Delete Skill",
      });
      return;
    }
    const skillDeleteToggle = event.target.closest("[data-skill-delete-toggle]");
    if (skillDeleteToggle) {
      toggleSkillDeleteSelection(skillDeleteToggle.getAttribute("data-skill-delete-toggle"));
      return;
    }
    const toggleAllSkillsButton = event.target.closest("[data-toggle-all-skills]");
    if (toggleAllSkillsButton) {
      toggleAllSkillDeleteSelections();
      return;
    }
    const skillLabelToggle = event.target.closest("[data-skill-label-toggle]");
    if (skillLabelToggle) {
      toggleLocalSkillLabels(skillLabelToggle.getAttribute("data-skill-label-toggle"));
      return;
    }
    const deleteSelectedSkillsButton = event.target.closest("[data-delete-selected-skills]");
    if (deleteSelectedSkillsButton) {
      openConfirmAction({
        kind: "delete-skills",
        skillIds: [...skillState.selectedDeleteIds],
        title: "Delete Selected Skills",
        subtitle: "This will remove the selected local skills.",
        message: `Delete ${skillState.selectedDeleteIds.length} skills? Employees already using them will keep their current text tags.`,
        confirmLabel: "Delete Skills",
      });
      return;
    }
    const installAgentSkillButton = event.target.closest("[data-install-agent-skill]");
    if (installAgentSkillButton) {
      installCatalogSkillToAgentSkills(installAgentSkillButton.getAttribute("data-install-agent-skill")).catch((error) => {
        agentSkillState.error = text(error.message, "Failed to install catalog skill.");
        renderAgentSkillsWorkbench();
        window.alert(agentSkillState.error);
      });
      return;
    }
    const skillCardButton = event.target.closest("[data-skill-card-id]");
    if (skillCardButton) {
      openSkillContent(skillCardButton.getAttribute("data-skill-card-id")).catch((error) => {
        window.alert(text(error.message, "Failed to open skill"));
      });
      return;
    }
    const caseSkillPreview = event.target.closest("[data-case-skill-preview]");
    if (caseSkillPreview) {
      openCaseSkillContent(caseSkillPreview.getAttribute("data-case-skill-preview")).catch((error) => {
        window.alert(text(error.message, "Failed to open skill"));
      });
      return;
    }
    const searchSkillPreview = event.target.closest("[data-search-skill-preview]");
    if (searchSkillPreview && !event.target.closest("[data-skill-toggle]")) {
      openSearchSkillContent(searchSkillPreview.getAttribute("data-search-skill-preview")).catch((error) => {
        window.alert(text(error.message, "Failed to open skill"));
      });
      return;
    }
    const importSkillsButton = event.target.closest("[data-import-skills]");
    if (importSkillsButton) {
      importSelectedSkills().catch((error) => {
        window.alert(text(error.message, "Failed to import skills"));
      });
      return;
    }
    const toggleSoulBannerListButton = event.target.closest("[data-toggle-soulbanner-list]");
    if (toggleSoulBannerListButton) {
      toggleSoulBannerListExpansion();
      return;
    }
    const toggleMbtiSbtiListButton = event.target.closest("[data-toggle-mbti-sbti-list]");
    if (toggleMbtiSbtiListButton) {
      toggleMbtiSbtiListExpansion();
      return;
    }
    const importLocalSkillButton = event.target.closest("[data-import-local-skill]");
    if (importLocalSkillButton) {
      openLocalSkillFilePicker();
      return;
    }
    const loadSoulLibraryButton = event.target.closest("[data-load-soul-library]");
    if (loadSoulLibraryButton) {
      loadSoulBannerSkills().catch((error) => {
        window.alert(text(error.message, "Failed to load SoulBanner skills"));
      });
      return;
    }
    const importSoulBannerSkillsButton = event.target.closest("[data-import-soulbanner-skills]");
    if (importSoulBannerSkillsButton) {
      importSelectedSoulBannerSkills().catch((error) => {
        window.alert(text(error.message, "Failed to import SoulBanner skills"));
      });
      return;
    }
    const loadMbtiSbtiLibraryButton = event.target.closest("[data-load-mbti-sbti-library]");
    if (loadMbtiSbtiLibraryButton) {
      loadMbtiSbtiSkills().catch((error) => {
        window.alert(text(error.message, "Failed to load Mbti/Sbti skills"));
      });
      return;
    }
    const importMbtiSbtiSkillsButton = event.target.closest("[data-import-mbti-sbti-skills]");
    if (importMbtiSbtiSkillsButton) {
      importSelectedMbtiSbtiSkills().catch((error) => {
        window.alert(text(error.message, "Failed to import Mbti/Sbti skills"));
      });
      return;
    }
    const soulBannerSkillButton = event.target.closest("[data-soulbanner-skill-toggle]");
    if (soulBannerSkillButton) {
      toggleSoulBannerSkill(soulBannerSkillButton.getAttribute("data-soulbanner-skill-toggle"));
      return;
    }
    const mbtiSbtiSkillButton = event.target.closest("[data-mbti-sbti-skill-toggle]");
    if (mbtiSbtiSkillButton) {
      toggleMbtiSbtiSkill(mbtiSbtiSkillButton.getAttribute("data-mbti-sbti-skill-toggle"));
      return;
    }
    const toggleWebSkillImportButton = event.target.closest("[data-toggle-web-skill-import]");
    if (toggleWebSkillImportButton) {
      toggleWebSkillImport();
      return;
    }
    const confirmSkillImportButton = event.target.closest("[data-confirm-skill-import]");
    if (confirmSkillImportButton) {
      importPreviewedSkill().catch((error) => {
        window.alert(text(error.message, "Failed to import skill"));
      });
      return;
    }
    const cancelSkillPreviewButton = event.target.closest("[data-cancel-skill-preview]");
    if (cancelSkillPreviewButton) {
      clearSkillPreview({ resetFileInput: true, clearWebUrl: skillState.previewSource === "web" });
      return;
    }
    const editSkillContentButton = event.target.closest("[data-skill-content-edit]");
    if (editSkillContentButton) {
      startSkillContentEdit();
      return;
    }
    const saveSkillContentButton = event.target.closest("[data-skill-content-save]");
    if (saveSkillContentButton) {
      requestSaveSkillContent();
      return;
    }
    const importSearchSkillButton = event.target.closest("[data-import-search-skill]");
    if (importSearchSkillButton) {
      importSearchSkillFromModal().catch((error) => {
        window.alert(text(error.message, "Failed to import skill"));
      });
      return;
    }
    const cookTemplateButton = event.target.closest("[data-cook-template]");
    if (cookTemplateButton) {
      cookCustomTemplate().catch((error) => {
        window.alert(text(error.message, "Failed to cook template"));
      });
      return;
    }
    const deleteTemplateButton = event.target.closest("[data-delete-template-id]");
    if (deleteTemplateButton) {
      const templateId = deleteTemplateButton.getAttribute("data-delete-template-id");
      const template = employeeTemplates().find((item) => item.id === templateId);
      openConfirmAction({
        kind: "delete-template",
        templateId,
        title: "Delete Role Template",
        subtitle: "This will remove the template from the role picker.",
        message: `Delete role template ${text(template?.role, templateId)}? This action cannot be undone.`,
        confirmLabel: "Delete Template",
      });
      return;
    }
    const templateButton = event.target.closest("[data-template-id]");
    if (templateButton) {
      selectTemplate(templateButton.getAttribute("data-template-id"));
      return;
    }
    const avatarButton = event.target.closest("[data-avatar-id]");
    if (avatarButton) {
      selectAvatar(avatarButton.getAttribute("data-avatar-id"));
      return;
    }
    const skillExpandButton = event.target.closest("[data-skill-expand-id]");
    if (skillExpandButton) {
      toggleSkillExpansion(skillExpandButton.getAttribute("data-skill-expand-id"));
      return;
    }
    const localSkillButton = event.target.closest("[data-local-skill-id]");
    if (localSkillButton) {
      toggleLocalSkill(localSkillButton.getAttribute("data-local-skill-id"));
      return;
    }
    const downloadExportButton = event.target.closest("[data-download-export-case]");
    if (downloadExportButton) {
      downloadEmployeeExportCase().catch((error) => {
        window.alert(text(error.message, "Failed to save export JSON"));
      });
      return;
    }
    const closeButton = event.target.closest("[data-modal-close]");
    if (closeButton || event.target.classList.contains("modal-backdrop")) {
      if (adminState.confirmAction) {
        closeConfirmAction();
      } else if (adminState.transcript?.isOpen) {
        closeTranscriptModal();
      } else if (skillState.contentModal?.isOpen) {
        closeSkillContentModal();
      } else if (employeeExportState.isOpen) {
        closeEmployeeExportModal();
      } else if (caseState.isDetailOpen) {
        closeCaseDetail();
      } else {
        closeCreateEmployee();
      }
      return;
    }
    const confirmButton = event.target.closest("[data-confirm-action]");
    if (confirmButton && adminState.confirmAction?.kind === "delete-docker") {
      deleteRuntimeDocker(adminState.confirmAction.containerName).catch((error) => {
        window.alert(text(error.message, "Failed to delete docker"));
      });
      return;
    }
    if (confirmButton && adminState.confirmAction?.kind === "delete-template") {
      deleteEmployeeTemplate(adminState.confirmAction.templateId).catch((error) => {
        window.alert(text(error.message, "Failed to delete template"));
      });
      return;
    }
    if (confirmButton && adminState.confirmAction?.kind === "delete-employee") {
      deleteEmployee(adminState.confirmAction.employeeId).catch((error) => {
        window.alert(text(error.message, "Failed to delete employee"));
      });
      return;
    }
    if (confirmButton && adminState.confirmAction?.kind === "delete-employees") {
      batchDeleteEmployees(adminState.confirmAction.employeeIds || []).catch((error) => {
        window.alert(text(error.message, "Failed to delete employees"));
      });
      return;
    }
    if (confirmButton && adminState.confirmAction?.kind === "delete-skill") {
      deleteSkill(adminState.confirmAction.skillId).catch((error) => {
        window.alert(text(error.message, "Failed to delete skill"));
      });
      return;
    }
    if (confirmButton && adminState.confirmAction?.kind === "delete-skills") {
      batchDeleteSkills(adminState.confirmAction.skillIds || []).catch((error) => {
        window.alert(text(error.message, "Failed to delete skills"));
      });
      return;
    }
    if (confirmButton && adminState.confirmAction?.kind === "skill-ops-action") {
      runSkillOpsAction(adminState.confirmAction.action, { dryRun: false, confirm: true }).catch((error) => {
        window.alert(text(error.message, "Failed to run skill cleanup"));
      });
      return;
    }
    if (confirmButton && adminState.confirmAction?.kind === "case-ops-action") {
      runCaseOpsAction(adminState.confirmAction.action, { dryRun: false, confirm: true }).catch((error) => {
        window.alert(text(error.message, "Failed to run case action"));
      });
      return;
    }
    if (confirmButton && adminState.confirmAction?.kind === "dream-restore") {
      restoreDreamCommit(adminState.confirmAction.subjectId, adminState.confirmAction.sha).catch((error) => {
        window.alert(text(error.message, "Failed to restore Dream memory"));
      });
      return;
    }
    const secondaryConfirmButton = event.target.closest("[data-confirm-secondary-action]");
    if (secondaryConfirmButton && adminState.confirmAction?.kind === "save-skill-content") {
      saveSkillContent({ syncEmployeePrompts: false }).catch((error) => {
        window.alert(text(error.message, "Failed to save skill"));
      });
      return;
    }
    if (confirmButton && adminState.confirmAction?.kind === "save-skill-content") {
      saveSkillContent({ syncEmployeePrompts: true }).catch((error) => {
        window.alert(text(error.message, "Failed to save skill"));
      });
      return;
    }
  });
  document.addEventListener("input", (event) => {
    const target = event.target;
    if (!(target instanceof HTMLInputElement || target instanceof HTMLTextAreaElement)) return;
    if (target.form?.id === "skill-web-import-form" && target.name === "url") {
      skillState.webImportUrl = target.value;
      return;
    }
    if (target.matches("[data-skill-content-editor]")) {
      updateSkillContentDraft(target.value);
      renderEmployeeModal();
      return;
    }
    if (target.matches("[data-agent-skill-query]")) {
      agentSkillState.query = target.value;
      renderAgentSkillsWorkbench();
      return;
    }
    if (target.matches("[data-agent-skill-draft]")) {
      agentSkillState.draft = target.value;
      return;
    }
    if (target.matches("[data-agent-skill-create-name]")) {
      agentSkillState.createName = target.value;
      return;
    }
    if (target.matches("[data-agent-skill-create-description]")) {
      agentSkillState.createDescription = target.value;
      return;
    }
    if (target.matches("[data-agent-skill-file-path]")) {
      agentSkillState.filePath = target.value;
      return;
    }
    if (target.matches("[data-agent-skill-file-content]")) {
      agentSkillState.fileContent = target.value;
      return;
    }
    if (target.matches("[data-employee-config-draft]")) {
      updateEmployeeConfigDraft(target.value);
      renderEmployeeDetail();
      return;
    }
    if (target.matches("[data-employee-export-field]")) {
      updateEmployeeExportDraft(target.getAttribute("data-employee-export-field"), target.value);
      return;
    }
    if (target.matches("[data-organization-tools]")) {
      updateOrganizationTools(target.getAttribute("data-organization-tools"), target.value);
      return;
    }
    if (target.matches("[data-employee-cron-name]")) {
      updateEmployeeCronDraft("name", target.value);
      return;
    }
    if (target.matches("[data-employee-cron-message]")) {
      updateEmployeeCronDraft("message", target.value);
      return;
    }
    if (target.matches("[data-employee-cron-every-ms]")) {
      updateEmployeeCronDraft("everyMs", target.value);
      return;
    }
    if (target.matches("[data-employee-cron-expr]")) {
      updateEmployeeCronDraft("expr", target.value);
      return;
    }
    if (target.matches("[data-employee-cron-tz]")) {
      updateEmployeeCronDraft("tz", target.value);
      return;
    }
    if (target.form?.id !== "employee-create-form") return;
    if (target.name === "custom_role_prompt") {
      employeeState.customRolePrompt = target.value;
      return;
    }
    updateCreateEmployeeDraft(target.name, target.value);
  });
  document.addEventListener("change", (event) => {
    const target = event.target;
    if (target instanceof HTMLInputElement && target.id === "local-skill-file-input") {
      const [file] = Array.from(target.files || []);
      target.value = "";
      if (!file) return;
      previewLocalSkillFile(file).catch((error) => {
        window.alert(text(error.message, "Failed to import from local skills"));
      });
      return;
    }
    if (target instanceof HTMLInputElement && target.id === "case-config-file-input") {
      const [file] = Array.from(target.files || []);
      target.value = "";
      if (!file) return;
      previewCaseConfigFile(file).catch((error) => {
        window.alert(text(error.message, "Failed to import case config"));
      });
      return;
    }
    if (target instanceof HTMLSelectElement && target.matches("[data-employee-sort]")) {
      setEmployeeSortMode(target.value);
      return;
    }
    if (target instanceof HTMLSelectElement && target.matches("[data-organization-manager]")) {
      setOrganizationManager(target.getAttribute("data-organization-manager"), target.value);
      return;
    }
    if (target instanceof HTMLInputElement && target.matches("[data-organization-global-skip]")) {
      organizationState.draft.settings.allow_skip_level_reporting = target.checked;
      markOrganizationDirty();
      renderOrganization();
      return;
    }
    if (target instanceof HTMLInputElement && target.matches("[data-organization-employee-skip]")) {
      updateOrganizationNode(target.getAttribute("data-organization-employee-skip"), { allow_skip_level_reporting: target.checked });
      return;
    }
    if (target instanceof HTMLInputElement && target.matches("[data-organization-skill]")) {
      toggleOrganizationSkill(
        target.getAttribute("data-organization-skill"),
        target.getAttribute("data-skill-id"),
        target.checked,
      );
      return;
    }
    if (target instanceof HTMLSelectElement && target.matches("[data-employee-cron-kind]")) {
      updateEmployeeCronDraft("kind", target.value);
      renderEmployeeDetail();
      return;
    }
    if (target instanceof HTMLInputElement && target.matches("[data-employee-cron-enabled]")) {
      updateEmployeeCronDraft("enabled", target.checked);
      return;
    }
    if (target instanceof HTMLSelectElement && target.form?.id === "employee-create-form") {
      updateCreateEmployeeDraft(target.name, target.value);
    }
    if (!(target instanceof HTMLInputElement)) return;
    if (!target.matches("[data-skill-toggle]")) return;
    const identity = target.getAttribute("data-skill-toggle");
    if (!identity) return;
    if (target.checked) {
      if (!skillState.selectedImportKeys.includes(identity)) {
        skillState.selectedImportKeys = [...skillState.selectedImportKeys, identity];
      }
    } else {
      skillState.selectedImportKeys = skillState.selectedImportKeys.filter((item) => item !== identity);
    }
    revealSelectedSkillSearchResults();
    renderSkillCatalog();
  });
  document.addEventListener("pointerdown", (event) => {
    if (!(event.target instanceof Element)) return;
    if (event.target.closest("[data-organization-connect]")) return;
    const node = event.target.closest("[data-organization-node]");
    if (!node) return;
    event.preventDefault();
    selectOrganizationEmployee(node.getAttribute("data-organization-node"));
    startOrganizationDrag(event, node);
  });
  document.addEventListener("pointermove", (event) => {
    moveOrganizationDrag(event);
  });
  document.addEventListener("pointerup", () => {
    endOrganizationDrag();
  });
  document.addEventListener("keydown", (event) => {
    if (!(event.target instanceof Element)) return;
    const soulBannerSkillCard = event.target.closest("[data-soulbanner-skill-toggle]");
    if (soulBannerSkillCard) {
      if (event.key !== "Enter" && event.key !== " ") return;
      event.preventDefault();
      toggleSoulBannerSkill(soulBannerSkillCard.getAttribute("data-soulbanner-skill-toggle"));
      return;
    }
    const mbtiSbtiSkillCard = event.target.closest("[data-mbti-sbti-skill-toggle]");
    if (mbtiSbtiSkillCard) {
      if (event.key !== "Enter" && event.key !== " ") return;
      event.preventDefault();
      toggleMbtiSbtiSkill(mbtiSbtiSkillCard.getAttribute("data-mbti-sbti-skill-toggle"));
      return;
    }
    const searchSkillCard = event.target.closest("[data-search-skill-preview]");
    if (searchSkillCard && !event.target.closest("[data-skill-toggle]")) {
      if (event.key !== "Enter" && event.key !== " ") return;
      event.preventDefault();
      openSearchSkillContent(searchSkillCard.getAttribute("data-search-skill-preview")).catch((error) => {
        window.alert(text(error.message, "Failed to open skill"));
      });
      return;
    }
    const catalogSkillCard = event.target.closest("[data-skill-card-id]");
    if (
      catalogSkillCard
      && !event.target.closest("[data-delete-skill-id]")
      && !event.target.closest("[data-skill-delete-toggle]")
      && !event.target.closest("[data-skill-label-toggle]")
      && !event.target.closest("[data-install-agent-skill]")
    ) {
      if (event.key !== "Enter" && event.key !== " ") return;
      event.preventDefault();
      openSkillContent(catalogSkillCard.getAttribute("data-skill-card-id")).catch((error) => {
        window.alert(text(error.message, "Failed to open skill"));
      });
      return;
    }
    const employeeCard = event.target.closest("[data-employee-id]");
    if (employeeCard && !event.target.closest("[data-delete-employee-card]") && !event.target.closest("[data-employee-delete-toggle]")) {
      if (event.key !== "Enter" && event.key !== " ") return;
      event.preventDefault();
      selectEmployee(employeeCard.getAttribute("data-employee-id"));
      return;
    }
    const caseSkillCard = event.target.closest("[data-case-skill-preview]");
    if (caseSkillCard) {
      if (event.key !== "Enter" && event.key !== " ") return;
      event.preventDefault();
      openCaseSkillContent(caseSkillCard.getAttribute("data-case-skill-preview")).catch((error) => {
        window.alert(text(error.message, "Failed to open skill"));
      });
      return;
    }
    const skillCard = event.target.closest("[data-local-skill-id]");
    if (!skillCard) return;
    if (event.target.closest("[data-skill-expand-id]")) return;
    if (event.key !== "Enter" && event.key !== " ") return;
    event.preventDefault();
    toggleLocalSkill(skillCard.getAttribute("data-local-skill-id"));
  });
  document.addEventListener("submit", (event) => {
    if (event.target?.id === "skill-web-import-form") {
      event.preventDefault();
      const formData = new FormData(event.target);
      previewWebSkillUrl(formData.get("url")).catch((error) => {
        window.alert(text(error.message, "Failed to import from web"));
      });
      return;
    }
    if (event.target?.id === "skill-search-form") {
      event.preventDefault();
      const formData = new FormData(event.target);
      searchClawHubSkills(formData.get("q")).catch((error) => {
        window.alert(text(error.message, "Failed to search ClawHub"));
      });
      return;
    }
    if (event.target?.id !== "employee-create-form") return;
    event.preventDefault();
    createEmployeeFromForm(event.target).catch((error) => {
      window.alert(text(error.message, "Failed to create employee"));
    });
  });
}

function renderMainAgent(mainAgent) {
  adminState.mainAgent = mainAgent || {};
  const currentMainAgent = adminState.mainAgent;
  const status = text(currentMainAgent.status, "unknown");
  const context = currentMainAgent.context || {};
  const usage = currentMainAgent.lastUsage || {};
  const current = percent(context.percent);
  const sessionKey = text(currentMainAgent.sessionKey || currentMainAgent.lastSessionKey, "");
  adminState.mainSessionKey = sessionKey || null;
  const mainContextAction = text(adminState.mainContextAction, "");
  const contextActionBusy = mainContextAction === "clear" || mainContextAction === "compact";
  const contextButtonDisabled = !sessionKey || contextActionBusy;
  const clearContextLabel = mainContextAction === "clear" ? t("button.clearing") : t("button.clear_context");
  const compactContextLabel = mainContextAction === "compact" ? t("button.compacting") : t("button.compact_context");

  document.getElementById("main-agent-panel").innerHTML = `
    <section class="panel control-panel control-main-panel">
      <div class="panel-head">
        <div>
          <h3>${t("main.title")}</h3>
          <div class="panel-meta">${t("main.latest_session", { value: text(currentMainAgent.sessionKey || currentMainAgent.lastSessionKey, "none") })}</div>
        </div>
        <div class="employee-actions">
          <span class="${badgeClass(status)}">${status}</span>
          <button class="icon-button chat-history-button" type="button" data-transcript-main="true" title="Chat history" aria-label="Open Main Agent chat history">${renderChatHistoryIcon()}</button>
          <button class="secondary-button" type="button" data-main-context-action="clear" ${contextButtonDisabled ? "disabled" : ""}>${clearContextLabel}</button>
          <button class="primary-button" type="button" data-main-context-action="compact" ${contextButtonDisabled ? "disabled" : ""}>${compactContextLabel}</button>
        </div>
      </div>
      <dl class="key-value">
        <div><dt>${t("overview.model")}</dt><dd>${text(currentMainAgent.model)}</dd></div>
        <div><dt>${t("main.active_tasks")}</dt><dd>${text(currentMainAgent.activeTaskCount, "0")}</dd></div>
        <div><dt>${t("main.stage")}</dt><dd>${text(currentMainAgent.stage, "idle")}</dd></div>
        <div><dt>${t("main.channel")}</dt><dd>${text(currentMainAgent.channel, "none")}</dd></div>
        <div><dt>${t("main.prompt_tokens")}</dt><dd>${text(usage.promptTokens, "0")}</dd></div>
        <div><dt>${t("main.completion_tokens")}</dt><dd>${text(usage.completionTokens, "0")}</dd></div>
      </dl>
      <div class="agent-section">
        <div class="agent-section-title">${t("main.context_window")}</div>
        <div class="progress"><span style="width: ${current}%"></span></div>
        <div class="progress-label">
          <span>${text(context.usedTokens, "0")} / ${text(context.totalTokens, "0")}</span>
          <span>${current}% · ${text(context.source, "unknown")}</span>
        </div>
      </div>
    </section>
  `;

  document.getElementById("overview-cards").innerHTML = [
    renderMetricCard(t("overview.status"), status.toUpperCase(), t("overview.status_footnote")),
    renderMetricCard(t("overview.model"), text(currentMainAgent.model), t("overview.model_footnote")),
    renderMetricCard(t("overview.uptime"), formatUptime(currentMainAgent.uptimeSeconds), t("overview.uptime_footnote")),
    renderMetricCard(t("overview.context"), `${current}%`, `${text(context.usedTokens, "0")} / ${text(context.totalTokens, "0")}`),
  ].join("");
}

function renderProcess(process) {
  adminState.process = process || {};
  const connectedProcesses = Array.isArray(process.connectedProcesses) ? process.connectedProcesses : [];
  document.getElementById("process-panel").innerHTML = `
    <section class="panel control-panel control-process-panel">
      <div class="panel-head">
        <div>
          <h3>${t("process.title")}</h3>
          <div class="panel-meta">${text(process.workspace, "unknown workspace")}</div>
        </div>
        <span class="badge status-running">${text(process.role, "unknown")}</span>
      </div>
      <dl class="key-value">
        <div><dt>${t("process.pid")}</dt><dd>${text(process.pid)}</dd></div>
        <div><dt>${t("process.uptime")}</dt><dd>${formatUptime(process.uptimeSeconds)}</dd></div>
      </dl>
      ${connectedProcesses.length ? `
        <div class="agent-section demo-connected-processes" data-demo-connected-processes="true">
          <div class="agent-section-title">Connected Processes</div>
          <div class="tag-cloud">
            ${connectedProcesses.map((item) => `
              <span class="tag">${html(text(item.role, "process"))} · ${html(text(item.status, "connected"))}</span>
            `).join("")}
          </div>
        </div>
      ` : ""}
    </section>
  `;
}

function renderSubagents(agents) {
  const list = document.getElementById("subagent-list");
  if (!list) return;
  if (!Array.isArray(agents) || agents.length === 0) {
    list.innerHTML = `<section class="panel"><div class="empty-state">No active or recent subagents.</div></section>`;
    return;
  }
  list.innerHTML = agents.map((agent) => `
    <article class="agent-card">
      <div class="agent-card-top">
        <div>
          <h4>${text(agent.label || agent.id)}</h4>
          <div class="agent-meta">${text(agent.sessionKey, "no session")}</div>
        </div>
        <span class="${badgeClass(agent.status)}">${text(agent.status)}</span>
      </div>
      <div class="agent-section">
        <div class="agent-section-title">Task</div>
        <div class="command-line">${text(agent.taskPreview, "unknown")}</div>
      </div>
    </article>
  `).join("");
}

function dockerAgentSourceLabel(agent) {
  const employeeName = text(agent?.employeeName, "");
  const employeeId = text(agent?.employeeId, "");
  if (employeeName && employeeId) return `${employeeName} · ${employeeId}`;
  if (employeeName) return employeeName;
  if (employeeId) return employeeId;
  return text(agent?.source, "docker");
}

function renderDockerAgents(agents) {
  adminState.dockerAgents = Array.isArray(agents) ? agents : [];
  const list = document.getElementById("docker-agent-list");
  const daemonIssue = dockerDaemonIssue();
  const repairing = adminState.dockerDaemonAction === "repair";
  const repairResult = text(adminState.dockerDaemonRepairResult, "");
  const daemonPanel = daemonIssue ? `
    <section class="panel docker-daemon-alert">
      <div class="panel-head">
        <div>
          <h3>${t("docker.daemon_unavailable")}</h3>
          <div class="panel-meta">${html(dockerDaemonMessage(daemonIssue))}</div>
        </div>
        <span class="badge status-error">${html(text(daemonIssue.status, "unavailable"))}</span>
      </div>
      <div class="docker-daemon-alert-actions">
        <button class="primary-button docker-daemon-repair-button" type="button" data-docker-daemon-repair="true" ${repairing ? "disabled" : ""}>
          ${repairing ? t("docker.daemon_repairing") : t("docker.daemon_repair")}
        </button>
        <span class="panel-meta">${t("docker.daemon_repair_hint")}</span>
      </div>
      ${repairResult ? `<div class="docker-daemon-repair-result">${html(repairResult)}</div>` : ""}
    </section>
  ` : "";
  if (!Array.isArray(agents) || agents.length === 0) {
    list.innerHTML = `${daemonPanel}<section class="panel"><div class="empty-state">${t("docker.empty")}</div></section>`;
    return;
  }

  list.innerHTML = daemonPanel + agents.map((agent) => {
    const context = agent.context || {};
    const current = percent(context.percent);
    const dockerName = text(agent.name || agent.containerName || agent.agentKey, "");
    const sourceLabel = dockerAgentSourceLabel(agent);
    const readOnlyDemo = agent.demo === true || agent.readOnly === true || agent.read_only === true;
    return `
      <article class="agent-card ${readOnlyDemo ? "is-demo" : ""}">
        <div class="agent-card-top docker-agent-card-top">
          <div class="docker-agent-head">
            <h4>${html(dockerName, "docker")}</h4>
            <div class="agent-meta">${text(agent.image)} · ${text(agent.ports, "no ports")}</div>
          </div>
          <div class="agent-card-actions docker-agent-card-actions">
            ${readOnlyDemo ? `<span class="tag demo-badge" data-demo-badge="true">Demo</span>` : ""}
            <span class="${badgeClass(agent.status)}">${text(agent.status)}</span>
            ${readOnlyDemo ? "" : `<button class="icon-button chat-history-button" type="button" data-transcript-docker="${html(dockerName)}" title="Chat history" aria-label="Open Docker Agent chat history">${renderChatHistoryIcon()}</button>`}
          </div>
        </div>
        <div class="agent-section">
          <div class="agent-section-title">${t("docker.resources")}</div>
          <div class="code-block">CPU ${text(agent.cpuPercent, "n/a")} · Memory ${text(agent.memoryUsage, "n/a")}</div>
        </div>
        <div class="agent-section">
          <div class="agent-section-title">${t("docker.current_command")}</div>
          <div class="command-line">${text(agent.currentCommand, "idle")}</div>
        </div>
        <div class="agent-section">
          ${renderEmployeeContextPanel(context, {
            employeeId: agent.employeeId || "",
            sessionKey: context.sessionKey || agent.sessionKey || "",
            shortLabels: true,
            actionAttr: "data-docker-context-action",
          })}
        </div>
        <div class="agent-section">
          <div class="agent-section-title">${t("docker.source")}</div>
          <div class="code-block">${html(sourceLabel, "docker")}</div>
        </div>
      </article>
    `;
  }).join("");
}

async function refreshDashboard() {
  const response = await fetch("/admin/api/runtime", { headers: { Accept: "application/json" } });
  if (!response.ok) {
    throw new Error(`HTTP ${response.status}`);
  }
  renderPayload(await response.json());
}

function renderPayload(payload) {
  payload = payload || {};
  adminState.generatedAt = text(payload.generatedAt, "");
  adminState.dockerDaemon = payload.dockerDaemon || {};
  adminState.demoMode = payload.demoMode || { enabled: false };
  adminState.demoTodos = Array.isArray(payload.demoTodos) ? payload.demoTodos : [];
  appendRuntimeHistorySample(runtimeHistorySampleFromPayload(payload));
  syncEmployeesFromRuntime(payload);
  renderEmployees();
  renderProcess(payload.process || {});
  renderMainAgent(payload.mainAgent || {});
  renderRuntimeTimeline();
  renderDockerAgents(payload.dockerContainers || payload.dockerAgents || []);
  renderGeneratedAt();
  renderHeroBar();
  renderAlertStrip();
  renderActionCenter();
  renderResourceHubTabs();
  renderDreamPanel();
  publishCompanionContext(payload);
  syncCompanionRuntimeReaction(payload);
  requestNavSectionSync();
}

async function tick() {
  try {
    await refreshDashboard();
  } catch (error) {
    document.getElementById("docker-agent-list").innerHTML = `
      <section class="panel"><div class="empty-state">Failed to load runtime snapshot: ${text(error.message)}</div></section>
    `;
  }
}

function startSse() {
  if (!window.EventSource) return false;
  const events = new EventSource("/admin/api/events");
  events.addEventListener("runtime", (event) => {
    renderPayload(JSON.parse(event.data));
  });
  events.onerror = () => {
    events.close();
    tick();
    window.setInterval(tick, POLL_INTERVAL_MS);
  };
  return true;
}

window.addEventListener("DOMContentLoaded", async () => {
  initializeAdminPreferences();
  initEmployeeInteractions();
  try {
    window.OpenHireCompanion?.mount?.({
      lang: () => currentLanguage(),
      modelName: "openhire",
    });
  } catch (companionError) {
    console.warn("[companion] mount skipped", companionError);
  }
  try {
    await loadCases();
    await loadEmployeeTemplates();
    await loadSkills();
    await loadAgentSkills();
    await loadEmployees();
    await loadOrganization();
    await loadCaseOps();
    await loadSkillGovernance();
    await loadDream();
    startEmployeePolling();
    window.setInterval(() => {
      refreshAgentSkillProposals().catch(() => {});
    }, AGENT_SKILL_PROPOSAL_POLL_INTERVAL_MS);
  } catch (error) {
    document.getElementById("employee-detail").innerHTML = `
      <section class="panel"><div class="empty-state">Failed to load admin data: ${text(error.message)}</div></section>
    `;
  }
  await loadRuntimeHistory();
  if (!startSse()) {
    tick();
    window.setInterval(tick, POLL_INTERVAL_MS);
  }
});
