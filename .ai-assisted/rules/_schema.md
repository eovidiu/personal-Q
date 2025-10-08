Front‑matter and registry schemas for rule documents.

Front‑matter (YAML at top of each rule file):

id: rules.core.assistant
version: 1.0.0
description: Short description
globs: ["**/*"]            # optional; for language/tool scoping
alwaysApply: true           # optional; for core rules
appliesToTools: ["codex"]  # optional; for tool adapters
order: 20                   # optional; relative ordering
tags: ["core", "planning"]

Registry (`.ai-assisted/rules/registry.yaml`):

rules:
  - path: rules/core/assistant-rules.md
    id: rules.core.assistant
    version: 1.0.0
    alwaysApply: true
    tags: ["core"]

See `_schema.frontmatter.json` and `_schema.registry.json` for machine-readable definitions.

