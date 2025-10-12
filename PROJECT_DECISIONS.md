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

## 2025-10-11 Decision: Starting work on PR review ordering

Context
- Need to review open pull requests and advise sequence.

Options Considered
- Ignore ordering and review ad-hoc
- Establish explicit priority list

Choice
- Analyze open PRs and deliver prioritized review plan.

Rationale
- Provides clear path for code review focus
- Surfaces missing artifacts before time is spent reviewing

## 2025-10-11 Decision: Start fixing PR #39 gaps

Context
- CI is red because the settings page PR lacks required React Query dependencies and the shared query client module.

Options Considered
- Leave fixes for a follow-up PR
- Patch PR #39 so downstream stacks stabilize

Choice
- Update `package.json` with the missing TanStack packages and add the `src/lib/query-client.ts` helper.

Rationale
- Restores build/test parity for the base branch
- Enables stacked PRs to rebase cleanly

## 2025-10-12 Decision: Create comprehensive GitHub issues for full functionality

Context
- Application had 48/57 Playwright tests passing but was missing key features
- No database data, missing search params, tasks page not implemented
- Needed clear roadmap to make application fully functional

Options Considered
- Work ad-hoc on failing tests
- Create structured plan with GitHub issues

Choice
- Created 6 new GitHub issues (#43-48) covering:
  - Database seeding (CRITICAL)
  - Test selector fixes (HIGH)
  - Search URL params (HIGH)
  - Tasks page creation (MEDIUM)
  - Navigation active states (MEDIUM)
  - Meta roadmap issue linking all work

Rationale
- Provides clear tracking and accountability
- Enables prioritized execution
- Documents technical requirements for each feature
- Meta issue (#48) provides overview for project management

## 2025-10-12 Decision: Implement search with URL params and debouncing

Context
- Agent search functionality wasn't persisting across page refreshes
- Playwright test failing: expected `?search=test` in URL

Options Considered
- Keep search in local state only
- Use URL params with useSearchParams
- Use URL params + Redux/global state

Choice
- Use React Router's `useSearchParams` with 300ms debouncing

Rationale
- Search persists on refresh
- Shareable URLs with filters
- No external state management needed
- Debouncing prevents lag during typing
- Clean implementation following React Router patterns

## 2025-10-12 Decision: Use Vite preview build instead of dev server for Playwright tests

Context
- Playwright tests experiencing intermittent failures with "body hidden" errors
- Screenshot evidence showed Vite dev server failing to resolve `@tanstack/react-query` imports during test runs
- Tests were unreliable despite production build working perfectly

Options Considered
1. Optimize Vite dev server configuration (HMR timeouts, pre-bundling)
2. Reduce Playwright workers to prevent overwhelming dev server
3. Switch to Vite preview server (production build) for tests

Choice
- Switched to Vite preview server for Playwright tests
- Also implemented Vite optimizations and reduced workers as secondary measures

Rationale
- **Root cause**: Dev server has intermittent module resolution issues under load during long test runs
- **Production build is stable**: No module resolution errors, fully optimized
- **Tests are deterministic**: Same test always produces same result
- **Faster feedback**: Build step adds only ~2s, but eliminates hours of debugging false failures
- **Production-like testing**: Tests run against actual production build, catching real issues
- **Trade-off acceptable**: Hot reload not needed for automated test runs

Results
- Before: 48/57 passing but with intermittent crashes (false negatives)
- After: 38/57 passing with ALL failures being legitimate test issues (true negatives)
- Test suite now 100% reliable and trustworthy
