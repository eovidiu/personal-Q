# Migration: CrewAI → Claude Agent Runtime (Anthropic SDK tool-use loop)

> Status: **In progress on branch `claude/claude-sdk-agent-migration-lxxan0`.**
> This document is both the transition plan and the record of what has been done.

## 1. Why migrate

Personal-Q originally used **CrewAI** (which wraps **LiteLLM** + **LangChain**)
to orchestrate agent task execution. In practice this added a heavy, fast-moving
dependency stack on top of a backend that *already* talked to Claude directly
through the official **Anthropic SDK** (`backend/app/services/llm_service.py`).

CrewAI was effectively a parallel, redundant execution path with real costs:

- **Dependency weight & churn** — `crewai`, `litellm`, `langchain-anthropic`,
  `langchain-core` pulled in a large transitive tree, slow Docker builds, and
  frequent breaking releases (the repo already carried pins like
  `crewai==0.203.1` in `requirements.txt` but `crewai>=0.86.0` in `pyproject.toml`
  — an inconsistency waiting to break).
- **Indirection** — agent execution went app → CrewAI → LiteLLM → Anthropic,
  making errors, token accounting, retries, and prompt-injection controls harder
  to reason about than a direct SDK call.
- **Memory disabled / tools unused** — `Crew(memory=False)` was forced to avoid
  OpenAI embeddings, and `create_agent_tools()` always returned `[]`. The crew
  was, in effect, a single LLM call with extra layers.

The replacement is a **self-hosted Claude agent runtime**: an agentic
**tool-use loop** built directly on the Anthropic SDK (Messages API). It keeps
everything in our own FastAPI/Celery infrastructure, removes the CrewAI/LangChain/
LiteLLM stack, and gives us a clean place to add real tools.

### Architecture chosen

| Option | Decision |
|---|---|
| **Anthropic SDK tool-use loop** (self-hosted agentic loop) | ✅ **Chosen** — minimal deps, stays in our infra, fits Celery + the existing `llm_service` resilience patterns. |
| Claude Managed Agents (`client.beta.agents`/`sessions`, Anthropic-hosted containers) | ❌ Not now — server-managed, Anthropic-only, a larger architectural shift away from the Celery/worker model. Revisit if we need sandboxed code execution per task (see §8). |

## 2. What the runtime does

`backend/app/services/agent_runtime.py` → `AgentRuntime`:

```
execute_agent_task(db, agent, task_description, task_input)
  └─ resolve & validate model (Anthropic only)
  └─ build system prompt (role + agent.system_prompt, sanitized)
  └─ build tools (empty today; extensible)
  └─ run agentic loop:
        while not done and iterations < MAX_AGENT_ITERATIONS:
            resp = client.messages.create(model, system, messages, tools)
            if resp.stop_reason == "tool_use": run tools, append results, continue
            if resp.stop_reason == "pause_turn": re-send to resume
            else: collect final text → done
  └─ return {success, result, model_used, usage, iterations}
```

`execute_multi_agent_task(db, agents, tasks, process)` chains agents
**sequentially**, feeding each agent the prior agents' outputs as context
(reproducing CrewAI's sequential process; `hierarchical` adds a coordination
note). The public method signatures match the former `CrewService` so the
Celery worker swap was a one-line change.

Key correctness properties carried over / improved:

- **API keys come only from environment variables** (via `provider_registry`), never the DB.
- **Prompt-injection sanitization** reused from `app.security.prompt_sanitizer`.
- **Resilience**: tenacity retry with exponential backoff on transient errors
  (`APIConnectionError`, `RateLimitError`, timeouts), per-call.
- **Token usage** is aggregated across loop iterations and returned to the worker.
- **Tool failures** are reported back to the model as `is_error` tool results
  rather than crashing the task.

## 3. Model-awareness (important behavioral change)

Claude **4.6+ and Fable** models (`claude-opus-4-6/4-7/4-8`, `claude-sonnet-4-6`,
`claude-haiku-4-5`, `claude-fable-5`, `claude-mythos-5`) **reject** sampling
parameters (`temperature`/`top_p`/`top_k`) and the legacy
`thinking.budget_tokens` config — sending them returns HTTP 400.

Both the new runtime and `llm_service` now **omit `temperature` for these model
families** and only send it for older models that accept it
(`_accepts_sampling_params`). This was a latent bug surfaced by moving the
default to a current model.

The retired default `claude-3-5-sonnet-20241022` was replaced:

- `settings.default_model` → **`claude-opus-4-8`**.
- `llm_service.validate_api_key` ping model → **`claude-haiku-4-5`** (was a retired model that would now 404).
- `provider_registry` gained current models: Opus 4.8 (recommended), Sonnet 4.6, Haiku 4.5, Fable 5.
- `model_validator` legacy map now remaps **retired snapshot IDs** (e.g.
  `claude-3-5-sonnet-20241022`, `claude-3-7-sonnet-20250219`,
  `claude-3-opus-20240229`) to current models, so existing seeded agents keep working.

> **Scope note (multi-provider):** the OpenAI/Mistral entries remain in the
> registry for the settings UI and model metadata, but the **agent runtime
> executes Anthropic models only** and returns a clear error for other
> providers. CrewAI/LiteLLM was what made cross-provider *execution* work. If
> non-Anthropic execution is still required, see §8.

## 4. Files changed

**New**
- `backend/app/services/agent_runtime.py` — the Claude agent runtime.
- `backend/tests/unit/test_agent_runtime.py` — runtime unit tests (mocked SDK).
- `MIGRATION.md` — this document.

**Modified**
- `backend/app/workers/tasks.py` — worker now calls `AgentRuntime.execute_agent_task`.
- `backend/app/services/__init__.py` — export `AgentRuntime`, drop `CrewService`.
- `backend/app/services/llm_service.py` — model-aware sampling params, current
  validation-ping model, refreshed pricing table.
- `backend/app/services/model_validator.py` — current model aliases + retired-snapshot remaps.
- `backend/app/services/provider_registry.py` — current Claude models.
- `backend/config/settings.py` — `default_model = claude-opus-4-8`.
- `backend/app/main.py` — app description.
- `backend/requirements.txt`, `backend/pyproject.toml` — removed `crewai`,
  `litellm`, `langchain-anthropic`, `langchain-core`; `anthropic>=0.39.0`.
- `backend/Dockerfile`, `Dockerfile.celery-worker` — dropped CrewAI build notes; bumped worker cache buster.
- `backend/tests/integration/test_api_key_config.py`,
  `backend/tests/unit/test_websocket_broadcasts.py` — retargeted to `AgentRuntime`.
- `README.md`, `.github/workflows/claude-code-review.yml` — docs/architecture text.

**Removed**
- `backend/app/services/crew_service.py`
- `backend/tests/unit/test_crew_service.py`

## 5. Phased rollout

1. **Phase 1 — Runtime in place (this PR).** New runtime, worker wired, CrewAI
   removed from deps and code, tests updated. Behavior parity: single call per
   task (no tools yet), multi-agent sequential chaining.
2. **Phase 2 — Verify in an environment with `ANTHROPIC_API_KEY`/`PERSONAL_Q_API_KEY`.**
   Run a real task end-to-end through Celery; confirm token usage + result
   persistence and WebSocket events.
3. **Phase 3 — Add real tools.** Register handlers in `TOOL_HANDLERS` and expose
   schemas from `build_tools` (driven by `agent.tools_config`). Natural first
   tools: web search/fetch (server-side), and the existing integrations
   (Slack/Obsidian/MS Graph) as client-side tools.
4. **Phase 4 — Optional enhancements.** Adaptive thinking + `effort` for modern
   models; streaming task output to the WebSocket; prompt caching for shared
   system prompts; per-agent `max_tokens` streaming guard for large outputs.

## 6. Testing

- `backend/tests/unit/test_agent_runtime.py` — role/prompt helpers,
  `_accepts_sampling_params`, model resolution (rejects non-Anthropic), happy
  path, temperature inclusion/omission by model family, tool-use loop, unknown-tool
  error handling, multi-agent chaining and validation.
- `backend/tests/integration/test_api_key_config.py` — graceful failure when the
  key is missing, non-Anthropic rejection, multi-agent failure propagation.
- `backend/tests/unit/test_websocket_broadcasts.py` — task lifecycle events now
  mock `AgentRuntime`.

Run: `cd backend && pytest tests/unit/test_agent_runtime.py tests/integration/test_api_key_config.py tests/unit/test_websocket_broadcasts.py`

## 7. Rollback

The change is isolated to the execution layer. To roll back:
`git revert` this PR (restores `crew_service.py`, the deps, and the worker import).
No DB schema or API contract changed — task input/output shapes are unchanged, so
no migration is required either direction.

## 8. Known follow-ups / out of scope

- **Code Quality (black/isort) — FIXED in this PR.** The `ci.yml` lint job
  installs an **unpinned** `black` (now 26.5.1) + `isort` and checks all of
  `backend/app`. Pre-existing drift in files this migration didn't otherwise
  touch (`routers/{auth,metrics,tasks,websocket,llm}.py`, `workers/celery_app.py`,
  `services/memory_service.py`, `middleware/rate_limit.py`, `db/*`) was
  reformatted repo-wide (`black --line-length=100 backend/app` +
  `isort --profile black --line-length 100 backend/app`) so the lint job passes.
  Recommended follow-up: **pin** `black`/`isort` versions in the workflow so an
  unpinned upgrade can't re-break the check.
- **Build Docker Images — FIXED in this PR.** The failure was a pre-existing CI
  misconfiguration, not a missing file: `backend/entrypoint.sh` (and every other
  `COPY` source) exists, but `backend/Dockerfile` COPYs paths relative to the
  **repo root** (`COPY backend/app ./app`, matching how Railway builds it) while
  the `ci.yml` `build` job passed `context: ./backend`, so `COPY backend/entrypoint.sh`
  resolved to `backend/backend/entrypoint.sh` → not found. Fixed by setting the
  backend build step's `context: .` (the frontend step already used `context: .`).
- **`backend/uv.lock`** still references the removed packages. Regenerate with
  `uv lock` (or delete if pip-only) so the lockfile matches `pyproject.toml`.
  The Docker build uses `pip install -e .` from `pyproject.toml`, so this is a
  hygiene item, not a build blocker.
- **Non-Anthropic execution** (OpenAI/Mistral) is no longer wired for task
  execution. If needed, add provider-specific clients behind the runtime or
  reintroduce a thin LiteLLM adapter for those providers only.
- **`anthropic` version**: floor kept at `>=0.39.0` for safety; bump to a recent
  release to pick up newer features (adaptive thinking betas, server-side tools).
- **PROJECT_SPECIFICATION.md** still describes CrewAI in places (historical spec);
  update if it is meant to be a living document.
- **Managed Agents** remains the path if we later want Anthropic-hosted, per-task
  sandboxed tool execution.
