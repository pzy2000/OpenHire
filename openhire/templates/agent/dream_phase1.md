Compare conversation history against current memory files. Also scan memory files for stale content — even if not mentioned in history.

Output one line per finding:
[FILE] atomic fact (not already in memory)
[FILE-REMOVE] reason for removal
[SKILL] kebab-case-name: one-line description of the reusable pattern

Files: USER (identity, preferences), SOUL (bot behavior, tone), MEMORY (knowledge, project context)

Rules:
- Atomic facts: "has a cat named Luna" not "discussed pet care"
- Corrections: [USER] location is Tokyo, not Osaka
- Capture confirmed approaches the user validated

Staleness — flag for [FILE-REMOVE]:
- Time-sensitive data older than 14 days: weather, daily status, one-time meetings, passed events
- Completed one-time tasks: triage, one-time reviews, finished research, resolved incidents
- Resolved tracking: merged/closed PRs, fixed issues, completed migrations
- Detailed incident info after 14 days — reduce to one-line summary
- Superseded: approaches replaced by newer solutions, deprecated dependencies

Skill discovery — flag [SKILL] when ANY of these indicate a reusable pattern:
- The agent successfully completed a complex task with 5+ tool calls
- The agent hit errors or a dead end, then found a working path
- The user corrected the agent's approach and the corrected approach should be remembered
- A non-trivial reusable workflow appeared, especially if it has clear repeatable steps
- Prefer reusable workflows over one-off facts; do not flag trivial actions like "read a file"
- Do not worry about duplicates — the next phase will check and update similar existing skills

Do not add: current weather, transient status, temporary errors, conversational filler.

[SKIP] if nothing needs updating.
