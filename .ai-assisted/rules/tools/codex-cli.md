id: rules.tool.codex
version: 1.0.0
description: Codex CLI adapter — planning, patching, validation, approvals
appliesToTools: ["codex"]
tags: ["tooling"]
---

# Codex CLI Adapter

Plan discipline:
- Keep plans 3–7 steps, 5–7 words each.
- Exactly one `in_progress` step at all times.
- Update before long actions and after completing steps.

Preambles before tool calls:
- One or two sentences max; group related actions.
- Skip trivial reads unless part of grouped action.

Edits and patches:
- Use `apply_patch` for all file modifications.
- Make minimal, focused changes; avoid unrelated fixes.
- Obey any `AGENTS.md` constraints in affected scope.

Sandbox/approvals:
- `on-request`: escalate only for network or privileged writes.
- Avoid destructive commands unless explicitly requested.

Validation philosophy:
- Proactively run tests/lint in non-interactive modes.
- In interactive modes, propose validation commands and wait for approval unless test-related.

State and logging:
- Mirror plan state into `.ai_state.next_steps` and `.ai_state.completed` at milestones.
- Append decisions and lessons while working; don’t defer to the end.

