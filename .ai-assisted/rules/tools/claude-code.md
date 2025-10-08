id: rules.tool.claude
version: 1.0.0
description: Claude Code adapter — pinning, context, safe ~/.claude usage
appliesToTools: ["claude"]
tags: ["tooling"]
---

# Claude Code Adapter

Pin these files:
- `.ai_state`, `PROJECT_DECISIONS.md`, `LESSONS_LEARNED.md`, `FUTURE_CONSIDERATIONS.md`, `AGENTS.md`.

Workspace and context:
- Use project search guided by language `globs` from the registry.
- Summarize large files; pin only the sections you need.

Checkpointing:
- Update `.ai_state` after milestones and escalations.
- Append decision/lesson/future entries in real time.

Safe `~/.claude` usage:
- Version only prompts and templates; never sessions, transcripts, or secrets.
- Optional symlink: `.ai-assisted/rules/templates/prompts/claude/*` → `~/.claude/prompts/`.

Risk protocol:
- For HIGH/CRITICAL risks, pause, checkpoint `.ai_state`, and ask for input.

See also: `Claude.md` (root quickstart).

