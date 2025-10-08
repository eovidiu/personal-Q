## [Init] Decision: Create canonical logs
**Context**: Initialize root-level decision log per assistant-rules
**Options Considered**: Use context folder vs root
**Choice**: Use root-level PROJECT_DECISIONS.md
**Rationale**: Tool-agnostic, consistent location across assistants

## 2025-10-05 Decision: Adopt modular rules structure

Context
- Needed a reusable, assistant-agnostic rules layout with tool adapters and templates.

Options Considered
- Keep monolithic `assistant-rules.md` with language files
- Modularize into core/profiles/tools with registry and bootstrap

Choice
- Modularize under `.ai-assisted/rules` with `registry.yaml`, tool adapters, templates, and bootstrap scripts.

Rationale
- Easier reuse across projects, clearer scoping, and leverage Codex/Claude strengths.

## 2025-10-05 Decision: Prefer copy-in over submodule

Context
- We want the simplest installation and contributor workflow.

Options Considered
- Git submodule for centralized updates
- Copy-in with a local sync script

Choice
- Copy-in. Provide `scripts/sync-rules.sh` for easy updates.

Rationale
- Removes submodule complexity while still allowing periodic updates.
