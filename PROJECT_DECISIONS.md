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

## 2025-10-08 Decision: Use SQLite for all structured data storage

Context
- Need embedded database for agent config, tasks, and activity logs
- Initially considered both SQLite and ChromaDB for different purposes

Options Considered
- Use both SQLite (structured data) and ChromaDB (vector storage)
- Use only ChromaDB for everything
- Use only SQLite for everything

Choice
- Use SQLite for structured data (agents, tasks, activities, API keys, schedules)
- Use ChromaDB exclusively for vector embeddings and semantic search

Rationale
- SQLite excels at relational data with ACID compliance
- ChromaDB optimized for vector similarity search
- Each database serves its specific strength
- Both are embedded and require no external services
- No internet connection required for either

## 2025-10-08 Decision: Async SQLAlchemy with aiosqlite

Context
- FastAPI is async-first framework
- Need database operations that don't block event loop

Options Considered
- Synchronous SQLAlchemy with thread pool
- Async SQLAlchemy with aiosqlite

Choice
- Async SQLAlchemy 2.0 with aiosqlite driver

Rationale
- Better performance with async/await patterns
- Non-blocking database operations
- Consistent with FastAPI async architecture
- Modern SQLAlchemy 2.0 patterns

## 2025-10-08 Decision: Alembic for database migrations

Context
- Need version-controlled database schema changes
- Want to track database evolution over time

Options Considered
- Manual SQL migrations
- Alembic with autogenerate
- SQLAlchemy create_all() only

Choice
- Alembic with manual migrations (autogenerate as helper)

Rationale
- Professional database version control
- Rollback capability
- Team collaboration support
- Industry standard for SQLAlchemy projects
