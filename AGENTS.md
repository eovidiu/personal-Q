# AGENTS

This file provides guidance for AI assistants working in this repository.

- Scope: Entire repository.
- Audience: Gemini CLI, Claude Code, Cursor, Codex CLI, and similar tools.

## Canonical Context Files (repo root)
- `.ai_state` — Session state (JSON). Single source of truth.
- `PROJECT_DECISIONS.md` — Decision log (what/why).
- `LESSONS_LEARNED.md` — Accumulated insights.
- `FUTURE_CONSIDERATIONS.md` — Ideas and future improvements.

See `README.md` for example schemas and entry templates.

## Required Assistant Routine
- Startup
  - Read `.ai_state` and scan the three Markdown logs.
  - If filesystem writes are blocked, emit patches or log entries in the response for manual application.
- During work
  - Update `.ai_state` after milestones, escalations, and context switches.
  - Append decisions, lessons, and future considerations as they occur.
  - On HIGH/CRITICAL risks, pause, checkpoint to `.ai_state`, and ask for user input.
- Constraints
  - Do not create tool-specific state files; use only the canonical files above.
  - Do not `git commit` or perform destructive actions without explicit user instruction.

## Rules Reference
- Rules live under `.ai-assisted/rules` and are indexed by `.ai-assisted/rules/registry.yaml`.
- Core contract: `.ai-assisted/rules/core/assistant-rules.md` (applies repo-wide).
- Tool adapters: `.ai-assisted/rules/tools/` for Codex CLI and Claude Code specifics.
