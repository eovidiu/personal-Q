## [Init] Suggestion: Keep logs at repo root
**Situation**: Assistants need predictable locations for shared context
**Future suggestions**:
- Add lightweight validation to `.ai_state` updates
- Periodically prune or summarize long logs
- Add a script to append templated entries via CLI

## 2025-10-05 Suggestion: Add optional TruffleHog integration

Situation
- Pre-commit uses gitleaks with regex fallback.

Future suggestions
- Provide optional TruffleHog deep scan script for CI usage.
