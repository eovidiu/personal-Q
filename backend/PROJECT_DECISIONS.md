
## 2025-10-12 Decision: Implement real-time trend calculations

Context
- Dashboard was showing hardcoded mock trend indicators (e.g., "+2 this week")
- Users need actual trend data to understand system performance over time
- Frontend was ready to display trends, but backend was returning mock data

Options Considered
- Continue using mock data
- Implement on-the-fly trend calculations from database
- Pre-aggregate metrics into snapshots table (future optimization)

Choice
- Implemented on-the-fly trend calculations using TrendCalculator service
- Calculate trends for: agents (7-day), tasks (30-day %), success rate (30-day %)
- Added database indexes for performance optimization

Rationale
- Real data provides actionable insights to users
- On-the-fly calculation is simple and works for current scale
- Database indexes ensure queries remain performant
- Can migrate to pre-aggregated snapshots if scale requires it

Implementation
- Created `backend/app/services/trend_calculator.py` with three calculators
- Updated `backend/app/routers/metrics.py` to use real calculations
- Added Alembic migration for database indexes (created_at, completed_at, status+completed_at)
- Wrote 9 comprehensive unit tests covering all edge cases
- All tests pass successfully

Results
- Dashboard now displays real trend data based on historical database queries
- Trends show positive/negative changes with proper formatting
- Handles edge cases: no data, division by zero, new baselines
- Query performance remains fast with proper indexing

## 2025-10-12 Decision: Implement WebSocket real-time updates

Context
- Backend has WebSocket support at `ws://localhost:8000/ws`
- Frontend has WebSocket client in `src/services/api.ts` but wasn't being used
- Users had to manually refresh to see agent status changes and new activities

Options Considered
- Keep manual refresh workflow
- Implement polling (setInterval API calls)
- Implement WebSocket real-time updates

Choice
- Created WebSocket context provider with React Query integration
- WebSocket automatically invalidates/updates cache on server events
- Events: agent_created, agent_updated, agent_deleted, agent_status_changed, task_completed, activity_created

Rationale
- WebSocket provides instant updates without overhead of polling
- React Query cache invalidation ensures UI stays in sync automatically
- Better user experience with immediate feedback on changes
- Backend WebSocket infrastructure already exists
- Clean separation of concerns with context provider pattern

Implementation
- Created `src/contexts/WebSocketContext.tsx` with event handlers
- Updated `src/App.tsx` to wrap app with WebSocketProvider
- WebSocket connects on app load and survives page navigation
- Automatic reconnection handling built into client

Results
- Real-time updates for all agent and task changes
- No manual refresh needed
- Metrics update automatically
- Activities appear instantly
- Clean developer experience with useWebSocket hook
