# Testing & Validation Documentation

This document provides comprehensive testing and validation procedures for the Personal-Q AI Agent Manager application.

## Table of Contents

- [Overview](#overview)
- [Testing Strategy](#testing-strategy)
- [Backend Testing](#backend-testing)
- [Frontend Testing](#frontend-testing)
- [Manual Testing](#manual-testing)
- [Performance Testing](#performance-testing)
- [Security Testing](#security-testing)

---

## Overview

The Personal-Q application uses a multi-layered testing approach:

1. **Backend Unit Tests** - Test individual functions and services
2. **Backend Integration Tests** - Test API endpoints and database operations
3. **Frontend E2E Tests** - Test user workflows with Playwright
4. **Manual Testing** - Verify real-world scenarios and edge cases

**Test Coverage Goals:**
- Backend: 95% code coverage
- Frontend: Critical user paths covered
- Zero console errors in production

---

## Testing Strategy

### Automated Testing

```
┌─────────────────────────────────────────┐
│         Playwright E2E Tests            │
│   (UI workflows, user scenarios)        │
└─────────────────────────────────────────┘
                  │
                  ▼
┌─────────────────────────────────────────┐
│      Backend Integration Tests          │
│    (API endpoints, database ops)        │
└─────────────────────────────────────────┘
                  │
                  ▼
┌─────────────────────────────────────────┐
│         Backend Unit Tests              │
│  (Services, utilities, calculators)     │
└─────────────────────────────────────────┘
```

### Test Environments

- **Unit Tests**: In-memory SQLite database
- **Integration Tests**: Separate test database
- **E2E Tests**: Vite preview build (production-like)
- **Manual Tests**: Docker Compose full stack

---

## Backend Testing

### Running Backend Tests

```bash
cd backend

# Run all tests
pytest

# Run with coverage report
pytest --cov=app --cov-report=html

# Run specific test file
pytest tests/unit/test_trend_calculator.py

# Run tests matching pattern
pytest -k "test_agent"

# Run with verbose output
pytest -v

# Run without coverage requirements
pytest --no-cov
```

### Backend Test Structure

```
backend/tests/
├── conftest.py              # Shared fixtures
├── unit/                    # Unit tests
│   ├── test_trend_calculator.py
│   ├── test_agent_service.py
│   └── test_cache_service.py
└── integration/             # Integration tests
    ├── test_agents_api.py
    ├── test_tasks_api.py
    └── test_metrics_api.py
```

### Writing Backend Unit Tests

```python
"""Example unit test for TrendCalculator."""

import pytest
from datetime import timedelta
from app.services.trend_calculator import TrendCalculator
from app.models.agent import Agent, AgentStatus, AgentType
from app.utils.datetime_utils import utcnow

@pytest.mark.asyncio
async def test_calculate_agent_trend_with_growth(test_session):
    """Test agent trend showing growth."""
    now = utcnow()

    # Create test data
    for i in range(3):
        agent = Agent(
            id=f"agent-{i}",
            name=f"Test Agent {i}",
            agent_type=AgentType.CONVERSATIONAL,
            status=AgentStatus.ACTIVE,
            model="claude-3-5-sonnet-20241022",
            system_prompt="Test",
            created_at=now - timedelta(days=i),
            updated_at=now,
        )
        test_session.add(agent)

    await test_session.commit()

    # Test calculation
    trend = await TrendCalculator.calculate_agent_trend(test_session)
    assert trend == "+3 this week"
```

### Backend Test Fixtures

The `conftest.py` provides shared fixtures:

```python
@pytest.fixture
async def test_engine():
    """In-memory SQLite database for tests."""
    # Creates fresh database for each test

@pytest.fixture
async def test_session(test_engine):
    """Database session with automatic rollback."""
    # Provides clean session, rolls back after test
```

### Backend Integration Tests

Integration tests verify API endpoints:

```python
@pytest.mark.asyncio
async def test_create_agent(client, test_session):
    """Test agent creation endpoint."""
    response = await client.post(
        "/api/v1/agents",
        json={
            "name": "Test Agent",
            "description": "Integration test",
            "agent_type": "CONVERSATIONAL",
            "model": "claude-3-5-sonnet-20241022",
            "system_prompt": "Test"
        }
    )

    assert response.status_code == 201
    data = response.json()
    assert data["name"] == "Test Agent"
```

---

## Frontend Testing

### Running Frontend Tests

```bash
# Run all Playwright tests
npm run test:e2e

# Run in headed mode (watch browser)
npm run test:e2e:headed

# Run specific test file
npx playwright test tests/agents.spec.ts

# Run tests matching title
npx playwright test -g "create agent"

# Debug mode (step through tests)
npx playwright test --debug

# View test report
npx playwright show-report
```

### Frontend Test Structure

```
tests/
├── agents.spec.ts           # Agent CRUD operations
├── tasks.spec.ts            # Task management
├── authentication.spec.ts   # Login/logout flows
├── navigation.spec.ts       # Navigation and routing
├── search.spec.ts           # Search functionality
└── trends.spec.ts          # Trend calculations display
```

### Test Configuration

**Key Settings** (`playwright.config.ts`):

```typescript
{
  testDir: './tests',
  fullyParallel: false,         // Sequential for stability
  workers: 1,                   // Single worker
  webServer: {
    command: 'npm run build && npm run preview',
    port: 4173,
    reuseExistingServer: true,
  }
}
```

**Why Vite Preview?**
- Production-like build
- Consistent module resolution
- No HMR issues during long test runs
- 100% deterministic results

### Writing Frontend E2E Tests

```typescript
import { test, expect } from '@playwright/test';

test.describe('Agent Management', () => {
  test('should create a new agent', async ({ page }) => {
    await page.goto('/');

    // Wait for page load
    await expect(page.locator('h1')).toContainText('AI Agents');

    // Open create dialog
    await page.click('button:has-text("New Agent")');

    // Fill form
    await page.fill('[data-testid="agent-name"]', 'Test Agent');
    await page.fill('[data-testid="agent-description"]', 'Test Description');
    await page.selectOption('[data-testid="agent-type"]', 'CONVERSATIONAL');

    // Submit
    await page.click('button:has-text("Create")');

    // Verify success
    await expect(page.locator('.agent-card')).toContainText('Test Agent');
  });
});
```

### Test Data Attributes

Always use data-testid for stable selectors:

```tsx
// Good - stable selector
<input data-testid="agent-name" />

// Bad - brittle, changes with styling
<input className="mt-2 px-4 py-2 border" />
```

### Frontend Test Best Practices

1. **Use explicit waits**: `await expect(locator).toBeVisible()`
2. **Avoid hardcoded timeouts**: `setTimeout` is flaky
3. **Test isolation**: Each test should be independent
4. **Descriptive names**: "should show error when name is empty"
5. **Clean test data**: Reset state between tests

---

## Manual Testing

### Environment Setup

#### Start Full Stack

```bash
# Start all services
docker-compose up -d

# Verify services are running
docker-compose ps

# Check logs
docker logs personal-q-backend
docker logs personal-q-frontend
```

**Expected Services:**
- Backend: http://localhost:8000
- Frontend: http://localhost:5173
- Redis: localhost:6379
- Celery Worker: Running
- Celery Beat: Running

#### Verify Backend Health

```bash
# Health check
curl http://localhost:8000/health

# API docs
open http://localhost:8000/docs

# Database exists
ls -lh backend/data/personal_q.db
```

### Manual Testing Checklist

#### 1. Dashboard/AgentsPage

- [ ] Navigate to http://localhost:5173
- [ ] Verify page loads without errors
- [ ] Check console for errors (F12 → Console)
- [ ] Verify dashboard metrics display real numbers
- [ ] Check agent list loads from backend
- [ ] Verify React Query DevTools appear (bottom-left)
- [ ] Test search bar (type "test", verify filtering)
- [ ] Test status filter dropdown
- [ ] Test type filter dropdown
- [ ] Verify "Create New Agent" button is visible

#### 2. Agent Creation

- [ ] Click "New Agent" button
- [ ] Verify dialog opens
- [ ] Fill in all required fields:
  - Name: "Manual Test Agent"
  - Description: "Testing manual workflow"
  - Type: Select "Conversational"
  - Model: "claude-3-5-sonnet-20241022"
  - Temperature: 0.7
  - Max Tokens: 2048
  - System Prompt: "You are a helpful assistant"
- [ ] Submit form
- [ ] Verify success toast appears
- [ ] Verify agent appears in list immediately
- [ ] Verify dashboard metrics increment
- [ ] Check database: `sqlite3 backend/data/personal_q.db "SELECT name FROM agents;"`

#### 3. Agent Detail Page

- [ ] Click on an agent card
- [ ] Verify navigation to `/agent/:id`
- [ ] Verify agent details load correctly
- [ ] Check metrics section (tasks completed, success rate)
- [ ] Verify activities tab loads
- [ ] Verify configuration tab shows settings
- [ ] Test "Edit" button functionality
- [ ] Test "Back" navigation

#### 4. Agent Updates

- [ ] On agent detail page, click "Configure" or "Edit"
- [ ] Modify agent description
- [ ] Submit changes
- [ ] Verify success toast
- [ ] Verify changes reflect immediately on page
- [ ] Navigate back to agents list
- [ ] Verify changes persist

#### 5. Agent Status Toggle

- [ ] Click "Pause" or "Activate" button on agent card
- [ ] Verify loading spinner appears briefly
- [ ] Verify status badge updates (Active ↔ Paused)
- [ ] Check backend: `sqlite3 backend/data/personal_q.db "SELECT name, status FROM agents;"`
- [ ] Verify change persists after page refresh

#### 6. Real-time Trend Display

- [ ] Navigate to dashboard
- [ ] Check trend indicators show real calculations:
  - "Agent count: +X this week" (not mock "+2 this week")
  - "Tasks: +X.X% from last month" (actual percentage)
  - "Success rate: +X.X% from last month" (actual rate)
- [ ] Create a new agent
- [ ] Verify dashboard metrics update
- [ ] Verify trends recalculate

#### 7. WebSocket Real-time Updates

- [ ] Open app in two browser tabs (Tab A, Tab B)
- [ ] In Tab A: Create a new agent
- [ ] Verify Tab B updates automatically (no refresh needed)
- [ ] In Tab A: Change agent status
- [ ] Verify Tab B reflects status change immediately
- [ ] Check browser console for WebSocket connection messages

#### 8. Tasks Page

- [ ] Navigate to `/tasks`
- [ ] Verify task list loads
- [ ] Test filter by status (Pending, Running, Completed)
- [ ] Test filter by priority
- [ ] Test search functionality
- [ ] Click "Create Task" button
- [ ] Fill task form and submit
- [ ] Verify task appears in list

#### 9. Authentication Flow

- [ ] Logout (if logged in)
- [ ] Verify redirect to `/login`
- [ ] Try accessing `/agents` while logged out
- [ ] Verify redirect back to login
- [ ] Enter credentials (check backend for default user)
- [ ] Verify successful login
- [ ] Verify redirect to dashboard
- [ ] Check localStorage for auth token: `localStorage.getItem('auth_token')`
- [ ] Verify API calls include Authorization header (Network tab)

#### 10. Error Handling

- [ ] Stop backend: `docker-compose stop backend`
- [ ] Refresh frontend
- [ ] Verify error toast/message displays
- [ ] Verify UI doesn't crash (no white screen)
- [ ] Restart backend: `docker-compose start backend`
- [ ] Verify app recovers automatically
- [ ] Test network error handling:
  - Open DevTools → Network tab
  - Throttle to "Offline"
  - Attempt action
  - Verify error handling

---

## Performance Testing

### Metrics to Monitor

```bash
# Lighthouse CI (Chrome DevTools)
npm run lighthouse

# Bundle size analysis
npm run build
npm run analyze

# Backend performance
ab -n 1000 -c 10 http://localhost:8000/api/v1/agents
```

### Performance Benchmarks

- **Page Load Time**: < 3 seconds (initial load)
- **API Response Time**: < 200ms (p95)
- **Database Query Time**: < 50ms (with indexes)
- **WebSocket Reconnect**: < 1 second
- **Bundle Size**: < 500KB (gzipped)

### Frontend Performance Checklist

- [ ] No layout shift (CLS < 0.1)
- [ ] First Contentful Paint < 1.5s
- [ ] Time to Interactive < 3s
- [ ] Loading skeletons display during data fetch
- [ ] No UI blocking during API calls
- [ ] Optimistic updates feel instant
- [ ] Smooth scrolling on agent list

### Backend Performance Checklist

- [ ] Database queries use indexes
- [ ] N+1 query problems resolved
- [ ] Trend calculations < 100ms
- [ ] Redis cache hit rate > 80%
- [ ] No memory leaks in long-running services

---

## Security Testing

### Authentication Tests

- [ ] JWT token expires correctly
- [ ] Expired token returns 401
- [ ] Refresh token flow works
- [ ] Logout clears all tokens
- [ ] Protected routes redirect to login
- [ ] Authorization header required on API calls

### Input Validation Tests

- [ ] SQL injection attempts blocked
- [ ] XSS attempts sanitized
- [ ] LLM prompt injection attempts detected
- [ ] File upload size limits enforced
- [ ] CORS policy correctly configured

### Security Headers Check

```bash
curl -I http://localhost:8000/api/v1/agents

# Should include:
# X-Content-Type-Options: nosniff
# X-Frame-Options: DENY
# X-XSS-Protection: 1; mode=block
```

---

## Browser Console Checks

### Expected Console Output

**Good** ✅:
```
React Query: Fetching ['agents', {...}]
WebSocket: Connected to ws://localhost:8000/ws
Cache invalidated: ['metrics', 'dashboard']
```

**Bad** ❌:
```
ERROR: Uncaught TypeError: Cannot read property 'id' of undefined
401 Unauthorized - /api/v1/agents
CORS policy: Access blocked from 'http://localhost:5173'
```

### React Query DevTools Inspection

Open DevTools (click flower icon bottom-left):

1. **Check Query Keys**:
   - `['agents', {status: 'active', search: ''}]`
   - `['agent', 'agent-123']`
   - `['metrics', 'dashboard']`
   - `['activities', {limit: 10}]`

2. **Verify Query Status**:
   - Green = success, fresh data
   - Yellow = stale (will refetch on next mount)
   - Red = error

3. **Check Cache Behavior**:
   - Mutations invalidate correct queries
   - Stale time configured appropriately
   - No unnecessary refetches

---

## Database Verification

### Inspect Database Directly

```bash
# Open SQLite database
sqlite3 backend/data/personal_q.db

# Check agents
SELECT id, name, status, created_at FROM agents;

# Check recent activities
SELECT activity_type, title, created_at
FROM activities
ORDER BY created_at DESC
LIMIT 10;

# Check tasks
SELECT id, title, status, priority
FROM tasks
WHERE status = 'COMPLETED';

# Verify indexes exist
.schema agents
-- Should show: CREATE INDEX ix_agents_created_at...

# Check trend data
SELECT COUNT(*) FROM agents WHERE created_at >= date('now', '-7 days');
```

### Backend API Tests (curl)

```bash
# Get all agents
curl http://localhost:8000/api/v1/agents | jq

# Get specific agent
curl http://localhost:8000/api/v1/agents/agent-123 | jq

# Get dashboard metrics (requires auth)
curl -H "Authorization: Bearer $TOKEN" \
  http://localhost:8000/api/v1/metrics/dashboard | jq

# Test trend calculations
curl -H "Authorization: Bearer $TOKEN" \
  http://localhost:8000/api/v1/metrics/dashboard | jq '.trends'

# Get activities
curl http://localhost:8000/api/v1/activities?limit=5 | jq
```

---

## Common Issues & Solutions

### Issue: 401 Unauthorized Errors

**Symptoms**: All API calls return 401
**Solution**:
1. Verify authentication is implemented (Issue #35)
2. Check token in localStorage: `localStorage.getItem('auth_token')`
3. Verify token expiration: `jwt.io` (paste token)
4. Re-login if token expired

### Issue: CORS Errors

**Symptoms**: `Access to XMLHttpRequest blocked by CORS policy`
**Solution**:
1. Check `backend/app/main.py` CORS configuration
2. Verify `http://localhost:5173` is in `allow_origins`
3. Restart backend after config change

### Issue: Connection Refused

**Symptoms**: `ERR_CONNECTION_REFUSED` on API calls
**Solution**:
1. Verify backend is running: `docker-compose ps`
2. Check backend logs: `docker logs personal-q-backend`
3. Verify port 8000 is not in use: `lsof -i :8000`
4. Restart backend: `docker-compose restart backend`

### Issue: Data Not Updating

**Symptoms**: UI shows stale data after mutations
**Solution**:
1. Open React Query DevTools
2. Check if mutation invalidates correct queries
3. Verify `queryClient.invalidateQueries({ queryKey: [...] })`
4. Check network tab for refetch requests
5. Try manual refetch in DevTools

### Issue: WebSocket Not Connecting

**Symptoms**: Real-time updates not working
**Solution**:
1. Check browser console for WebSocket errors
2. Verify WebSocket URL: `ws://localhost:8000/ws`
3. Check backend WebSocket endpoint is running
4. Verify CORS allows WebSocket upgrade
5. Check firewall/proxy settings

### Issue: Tests Failing Intermittently

**Symptoms**: Playwright tests pass/fail randomly
**Solution**:
1. Switch to Vite preview build (already done)
2. Reduce workers to 1 in `playwright.config.ts`
3. Add explicit waits: `await expect(locator).toBeVisible()`
4. Check for race conditions in async operations
5. Verify test data cleanup between tests

### Issue: Trends Show Mock Data

**Symptoms**: Dashboard shows "+2 this week" (hardcoded)
**Solution**:
1. Verify backend updated to use TrendCalculator
2. Check migration ran: `alembic current`
3. Verify indexes exist: `.schema agents` in SQLite
4. Check backend logs for trend calculation errors
5. Restart backend after code changes

---

## Test Coverage Reports

### Backend Coverage

```bash
cd backend
pytest --cov=app --cov-report=html

# Open report
open htmlcov/index.html
```

**Current Coverage**: ~25% (needs improvement)
**Goal**: 95% coverage on critical paths

### Frontend Coverage (Future)

```bash
# Add to package.json
npm run test:coverage

# Configure in vitest.config.ts
coverage: {
  provider: 'v8',
  reporter: ['text', 'html'],
  exclude: ['node_modules/', 'tests/']
}
```

---

## Continuous Integration

### GitHub Actions Workflow

```yaml
name: Tests

on: [push, pull_request]

jobs:
  backend-tests:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3
      - name: Run backend tests
        run: |
          cd backend
          pip install -r requirements.txt
          pytest --cov=app

  frontend-tests:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3
      - name: Install dependencies
        run: npm ci
      - name: Run Playwright tests
        run: npx playwright test
```

---

## Summary

### Test Status

- ✅ Backend Unit Tests: 9/9 passing (TrendCalculator)
- ⚠️ Backend Integration Tests: Limited coverage
- ⚠️ Frontend E2E Tests: 41/57 passing (72%)
- ✅ Manual Testing: Comprehensive checklist provided
- ✅ Performance: Benchmarks defined
- ✅ Security: Checklist provided

### Next Steps

1. **Improve Backend Coverage**: Add more unit tests for services
2. **Fix Frontend Tests**: Address 16 failing Playwright tests
3. **Add CI/CD**: Automate test runs on PR
4. **Performance Monitoring**: Add Lighthouse CI
5. **Security Scans**: Integrate SAST tools

### Resources

- [Pytest Documentation](https://docs.pytest.org/)
- [Playwright Documentation](https://playwright.dev/)
- [React Query Testing](https://tanstack.com/query/latest/docs/framework/react/guides/testing)
- [FastAPI Testing](https://fastapi.tiangolo.com/tutorial/testing/)
