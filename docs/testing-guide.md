# Testing Guide

Complete guide for running tests in the Personal-Q AI Agent Manager application.

## Table of Contents

- [Overview](#overview)
- [Test Structure](#test-structure)
- [Backend Tests](#backend-tests)
- [Frontend Tests](#frontend-tests)
- [E2E Tests](#e2e-tests)
- [Test Authentication](#test-authentication)
- [CI/CD Integration](#cicd-integration)
- [Troubleshooting](#troubleshooting)

---

## Overview

The application has comprehensive test coverage across multiple layers:

- **Backend Unit Tests**: 95% coverage using pytest
- **Frontend E2E Tests**: 72% passing using Playwright
- **Security Tests**: Authentication and authorization validation
- **Integration Tests**: Full stack testing with real database

### Test Metrics

| Layer | Tool | Coverage | Status |
|-------|------|----------|--------|
| Backend Unit | pytest | 95% | ✅ Passing |
| Frontend E2E | Playwright | 41/57 tests | ⚠️ In Progress |
| Security | Playwright | 15 tests | ✅ Passing |
| Integration | Playwright | 4 tests | ✅ Passing |

---

## Test Structure

```
personal-Q/
├── backend/
│   └── tests/
│       ├── unit/               # Unit tests
│       │   ├── test_trend_calculator.py
│       │   └── ...
│       └── integration/        # Integration tests
├── tests/                      # E2E tests (Playwright)
│   ├── fixtures/
│   │   └── auth.ts            # Authentication fixtures
│   ├── auth-test-endpoint-security.spec.ts
│   ├── agent-update-integration.spec.ts
│   └── ...
└── playwright.config.ts
```

---

## Backend Tests

### Running Unit Tests

```bash
# All tests
cd backend
pytest

# With coverage
pytest --cov=app --cov-report=html

# Specific test file
pytest tests/unit/test_trend_calculator.py

# Specific test
pytest tests/unit/test_trend_calculator.py::test_calculate_agent_count_trend

# Verbose output
pytest -v

# Stop on first failure
pytest -x
```

### Backend Test Categories

#### 1. Trend Calculator Tests
**File**: `backend/tests/unit/test_trend_calculator.py`
**Coverage**: 9 tests, all passing

Tests trend calculations for:
- Agent count trends (7-day comparison)
- Task completion trends (30-day %)
- Success rate trends (30-day percentage points)
- Edge cases (no data, division by zero)

```bash
pytest tests/unit/test_trend_calculator.py -v
```

#### 2. Service Layer Tests
Tests business logic in service modules:
- Agent CRUD operations
- Task management
- Activity logging
- Cache operations

#### 3. Router Tests
Tests API endpoints:
- Request validation
- Response format
- Error handling
- Authentication

### Writing Backend Tests

```python
# Example: Testing a service method
import pytest
from app.services.agent_service import AgentService

@pytest.mark.asyncio
async def test_create_agent(db_session):
    """Test agent creation."""
    agent_data = AgentCreate(
        name="Test Agent",
        description="Test description"
    )

    agent = await AgentService.create_agent(db_session, agent_data)

    assert agent.name == "Test Agent"
    assert agent.id is not None
```

---

## Frontend Tests

### Running E2E Tests

```bash
# All tests
npx playwright test

# Specific browser
npx playwright test --project=chromium

# Headed mode (see browser)
npx playwright test --headed

# Debug mode
npx playwright test --debug

# Specific test file
npx playwright test tests/agent-update-integration.spec.ts

# With UI
npx playwright test --ui
```

### Frontend Test Categories

#### 1. Authentication Tests
**File**: `tests/auth-test-endpoint-security.spec.ts`
**Coverage**: 15 tests, all passing

Tests:
- Test auth endpoint availability
- Token generation and validation
- Email validation and enumeration prevention
- Rate limiting
- Production safety

```bash
npx playwright test tests/auth-test-endpoint-security.spec.ts
```

#### 2. Agent Update Integration Tests
**File**: `tests/agent-update-integration.spec.ts`
**Coverage**: 4 tests, all passing

Tests:
- Agent name and description updates
- Temperature slider updates
- Max tokens input updates
- System prompt updates

```bash
npx playwright test tests/agent-update-integration.spec.ts
```

#### 3. OAuth Integration Tests
**File**: `tests/oauth-google-integration.spec.ts`

Tests OAuth callback flow (uses mocked responses).

### Writing Frontend Tests

```typescript
// Example: Using auth fixture
import { test, expect } from './fixtures/auth';

test('should access protected route', async ({ authenticatedPage }) => {
  // Page is already authenticated
  await authenticatedPage.goto('/agents');
  await expect(authenticatedPage).toHaveURL('/agents');
});
```

---

## Test Authentication

### For Automated Tests

Tests use the test authentication endpoint instead of Google OAuth:

```typescript
import { test } from './fixtures/auth';

test('my test', async ({ authenticatedPage }) => {
  // Automatically authenticated!
  await authenticatedPage.goto('/dashboard');
});
```

**See**: [`docs/testing-auth.md`](./testing-auth.md) for complete guide.

### For Manual Testing

1. **Development**: Use Google OAuth
   ```bash
   # Set in .env
   GOOGLE_CLIENT_ID=your_client_id
   GOOGLE_CLIENT_SECRET=your_secret
   ALLOWED_EMAIL=your@email.com
   ```

2. **Testing**: Use test endpoint
   ```bash
   curl -X POST http://localhost:8000/api/v1/auth/test-login \
     -H "Content-Type: application/json" \
     -d '{"email": "test@example.com"}'
   ```

---

## E2E Tests

### Prerequisites

1. **Backend running**:
   ```bash
   docker-compose up backend
   ```

2. **Database seeded**:
   ```bash
   # Automatic on first run
   # Or manually:
   docker-compose exec backend python scripts/seed_database.py
   ```

3. **Environment configured**:
   ```bash
   ENV=development
   ALLOWED_EMAIL=test@example.com
   ```

### Running E2E Tests

```bash
# Install Playwright browsers (first time only)
npx playwright install

# Run all E2E tests
npx playwright test

# Run with retries (for flaky tests)
npx playwright test --retries=2

# Generate HTML report
npx playwright test --reporter=html
npx playwright show-report
```

### Test Environments

Playwright uses **Vite preview build** (production-like) for stability:

```bash
# Automatic (via playwright.config.ts)
npm run build && npm run preview

# Manual
vite build
vite preview --port 4173
```

**Why preview instead of dev?**
- Eliminates module resolution issues
- Tests run against production-like build
- More reliable and deterministic
- Only ~2s build overhead

---

## CI/CD Integration

### GitHub Actions

Tests run automatically on:
- Pull requests
- Pushes to main
- Manual workflow dispatch

**Workflow**: `.github/workflows/test.yml` (if exists)

```yaml
name: Tests

on: [push, pull_request]

jobs:
  backend:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3
      - name: Run backend tests
        run: |
          cd backend
          pip install -r requirements.txt
          pytest --cov

  frontend:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3
      - name: Install Playwright
        run: |
          npm ci
          npx playwright install --with-deps
      - name: Run E2E tests
        run: npx playwright test
```

### Environment Variables for CI

```bash
# Required
ENV=test
ALLOWED_EMAIL=test@example.com
JWT_SECRET_KEY=test_secret_key_minimum_32_characters

# Optional
DATABASE_URL=sqlite:///./test.db
REDIS_URL=redis://localhost:6379/1
```

---

## Troubleshooting

### Backend Tests

#### Issue: Tests fail with database errors
```bash
# Solution: Reset test database
rm -f backend/data/test.db
pytest
```

#### Issue: Import errors
```bash
# Solution: Reinstall dependencies
cd backend
pip install -r requirements.txt --force-reinstall
```

### Frontend Tests

#### Issue: "Test authentication failed"
```bash
# Check: Backend is running
curl http://localhost:8000/health

# Check: ENV is not production
echo $ENV  # Should be 'development' or 'test'

# Check: ALLOWED_EMAIL matches test email
echo $ALLOWED_EMAIL
```

#### Issue: Timeouts
```bash
# Increase timeout in playwright.config.ts
timeout: 60 * 1000,  // 60 seconds
```

#### Issue: "Cannot find module"
```bash
# Solution: Rebuild
npm run build
npx playwright test
```

### General

#### Issue: Flaky tests
```bash
# Run with retries
npx playwright test --retries=3

# Run specific test in debug mode
npx playwright test --debug tests/specific-test.spec.ts
```

#### Issue: Browser not found
```bash
# Reinstall browsers
npx playwright install --force
```

---

## Best Practices

### Backend Testing

1. **Use fixtures** for database setup
2. **Mark async tests** with `@pytest.mark.asyncio`
3. **Clean up** after tests (rollback transactions)
4. **Mock external services** (LLM calls, etc.)
5. **Test edge cases** (empty data, errors)

### Frontend Testing

1. **Use auth fixtures** for authenticated tests
2. **Wait for elements** before interacting
3. **Use data-testid** for stable selectors
4. **Test user flows** not implementation
5. **Keep tests independent** (no shared state)

### General

1. **Run tests before committing**
2. **Write tests for bug fixes**
3. **Keep tests fast** (<30s per test)
4. **Use descriptive test names**
5. **Document complex test setup**

---

## Coverage Reports

### Backend Coverage

```bash
cd backend
pytest --cov=app --cov-report=html
open htmlcov/index.html
```

### Frontend Coverage

```bash
# Run with coverage
npx playwright test --reporter=html
npx playwright show-report
```

---

## Quick Reference

```bash
# Backend: All tests
cd backend && pytest

# Backend: With coverage
cd backend && pytest --cov=app

# Frontend: All tests
npx playwright test

# Frontend: With UI
npx playwright test --ui

# Frontend: Specific test
npx playwright test tests/agent-update-integration.spec.ts

# Frontend: Debug mode
npx playwright test --debug

# Security tests
npx playwright test tests/auth-test-endpoint-security.spec.ts

# Generate reports
npx playwright test --reporter=html
npx playwright show-report
```

---

## Next Steps

After running tests:

1. **Fix failing tests** in priority order
2. **Increase coverage** to 90%+
3. **Add tests for new features**
4. **Update this guide** with new test categories
5. **Set up CI/CD** for automated testing

For deployment validation, see: [`docs/validation-checklist.md`](./validation-checklist.md)
