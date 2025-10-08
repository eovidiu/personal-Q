## [Init] Lesson: Centralize assistant state
**Situation**: Multiple state file names and locations caused confusion
**Learning**: A single `.ai_state` at repo root avoids ambiguity
**Application**: Read/write `.ai_state` only; deprecate tool-specific variants

## 2025-10-05 Lesson: Indexing rules improves adoption

Situation
- Previous rules were harder to discover and scope.

Learning
- A small `registry.yaml` with front‑matter makes selection and validation straightforward.

Application
- Use the registry pattern in future repos needing AI-assistant rules.
