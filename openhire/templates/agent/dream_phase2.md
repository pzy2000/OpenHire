Update memory files based on the analysis below.
- [FILE] entries: submit the described content with `memory_write`
- [FILE-REMOVE] entries: submit the removal with `memory_write`
- [SKILL] entries: submit a pending Agent Skills Workbench proposal using propose_agent_skill

## File paths (relative to workspace root)
- SOUL.md
- USER.md
- memory/MEMORY.md

Do NOT guess paths.

## Memory write rules
- Use `memory_write` for every change to SOUL.md, USER.md, or memory/MEMORY.md.
- Do NOT call `edit_file` for SOUL.md, USER.md, or memory/MEMORY.md.
- Include evidence for every `memory_write`: quote the source finding and/or history line that justifies it.
- Use action=append for new low-risk facts; action=patch for precise corrections; action=delete only for stale/superseded content.
- Use category=user_preference, project_fact, or workflow_experience only for stable long-term facts.
- Use category=temporary_status or one_time_event for transient status, meetings, one-off errors, or passed events; these are recorded but not written to long-term Markdown.
- Mark impact=high for SOUL.md changes, org/permission/default/security/required-skill/runtime/adapter changes, or broad deletions/replacements.
- If nothing should update, stop without calling tools.

## Skill creation rules (for [SKILL] entries)
- Trigger on reusable patterns from complex completed tasks (5+ tool calls), recovered errors/dead ends, user corrected approaches, or non-trivial reusable workflows
- Compare against the Existing Skills list first; prefer patch or edit proposals for similar existing skills instead of creating duplicates
- Use propose_agent_skill with action=create, name, reason, source=dream, trigger_reasons, evidence, and full SKILL.md content
- For existing workspace skills, use propose_agent_skill with action=patch and exact old_string/new_string when reliable; use action=edit with full content when patching is not reliable
- Do NOT use write_file or edit_file for skills/<name>/SKILL.md; skills must be approved in Agent Skills Workbench before writing
- Before proposing, read_file `{{ skill_creator_path }}` for format reference (frontmatter structure, naming conventions, quality standards)
- **Dedup check**: read existing skills listed below to verify the new skill is not functionally redundant. Skip creation if an existing skill already covers the same workflow.
- Include YAML frontmatter with name and description fields
- Keep SKILL.md under 2000 words — concise and actionable
- Include: when to use, steps, output format, at least one example
- Do NOT overwrite existing skills — skip if the skill directory already exists
- Reference specific tools the agent has access to (read_file, write_file, exec, web_search, etc.)
- Skills are instruction sets, not code — do not include implementation code

## Quality
- Every line must carry standalone value
- Concise bullets under clear headers
- When reducing (not deleting): keep essential facts, drop verbose details
- If uncertain whether to delete, keep but add "(verify currency)"
