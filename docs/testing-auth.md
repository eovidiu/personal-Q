# Test Authentication Guide

## Overview

This project uses a **test-only authentication endpoint** to enable Playwright E2E tests without requiring Google OAuth. This approach provides fast, reliable automated testing while maintaining production security.

## How It Works

### Triple-Layer Security

The test auth system uses three layers of protection to ensure it's NEVER available in production:

1. **Layer 1 (Import-time)**: `auth_test.py` checks `ENV` at import time and raises `RuntimeError` if `ENV=production`
2. **Layer 2 (Registration)**: `main.py` only includes the router when `settings.env != "production"`
3. **Layer 3 (Runtime)**: Each endpoint validates environment and returns 404 if accessed in production

### Architecture

```
┌─────────────────────────────────────────────────────┐
│  Playwright Test                                    │
│  ┌───────────────────────────────────────────────┐ │
│  │ import { test } from './fixtures/auth'        │ │
│  │                                               │ │
│  │ test('my test', async ({ authenticatedPage }) │ │
│  │   // Page is already authenticated           │ │
│  │ });                                           │ │
│  └───────────────────────────────────────────────┘ │
└─────────────────────────────────────────────────────┘
                         │
                         ↓
┌─────────────────────────────────────────────────────┐
│  Auth Fixture (tests/fixtures/auth.ts)              │
│  ┌───────────────────────────────────────────────┐ │
│  │ POST /api/v1/auth/test-login                  │ │
│  │ { "email": "allowed@example.com" }            │ │
│  │                                               │ │
│  │ → Stores token in localStorage                │ │
│  │ → Returns authenticated page                  │ │
│  └───────────────────────────────────────────────┘ │
└─────────────────────────────────────────────────────┘
                         │
                         ↓
┌─────────────────────────────────────────────────────┐
│  Backend (backend/app/routers/auth_test.py)         │
│  ┌───────────────────────────────────────────────┐ │
│  │ 1. Validate ENV != production                 │ │
│  │ 2. Validate email == ALLOWED_EMAIL            │ │
│  │ 3. Generate real JWT using production logic   │ │
│  │ 4. Return token                               │ │
│  └───────────────────────────────────────────────┘ │
└─────────────────────────────────────────────────────┘
```

## Usage

### Option 1: Using the Auth Fixture (Recommended)

The simplest way to write authenticated tests:

```typescript
// tests/my-test.spec.ts
import { test, expect } from './fixtures/auth';

test('should access protected route', async ({ authenticatedPage }) => {
  // Page is already authenticated - just navigate!
  await authenticatedPage.goto('/agents');
  await expect(authenticatedPage).toHaveURL('/agents');
});
```

### Option 2: Manual Authentication

For more control over authentication:

```typescript
import { test, expect } from '@playwright/test';
import { authenticatePage } from './fixtures/auth';

test('manual auth test', async ({ page }) => {
  // Manually authenticate
  await authenticatePage(page, 'test@example.com');

  // Now page is authenticated
  await page.goto('/agents');
});
```

### Option 3: Using the Token Directly

For API testing:

```typescript
import { test, expect } from './fixtures/auth';

test('API test with token', async ({ testAuthToken }) => {
  const response = await fetch('http://localhost:8000/api/v1/agents', {
    headers: {
      'Authorization': `Bearer ${testAuthToken}`
    }
  });

  expect(response.status).toBe(200);
});
```

## Environment Setup

### Backend Requirements

```bash
# .env file
ENV=development  # MUST be 'development' or 'test', NOT 'production'
ALLOWED_EMAIL=test@example.com  # Email for test authentication
JWT_SECRET_KEY=your-secret-key-min-32-chars
```

### Frontend Requirements

No special configuration needed! The test utilities automatically detect non-production builds.

## Running Tests

```bash
# Run all tests
npm run test

# Run specific test file
npx playwright test tests/agent-update-integration.spec.ts

# Run with UI (for debugging)
npx playwright test --ui

# Run in headed mode
npx playwright test --headed
```

## Security Validation

Run security tests to verify production safety:

```bash
npx playwright test tests/auth-test-endpoint-security.spec.ts
```

These tests verify:
- ✅ Endpoint works in development/test
- ✅ Email validation enforces ALLOWED_EMAIL
- ✅ Tokens are valid and match production format
- ✅ Environment checks are enforced

## Troubleshooting

### "Test authentication failed: Not found"

**Cause**: Backend ENV is set to 'production' or test router not loaded.

**Fix**:
```bash
# Check backend .env file
ENV=development  # NOT production
```

### "Email not authorized"

**Cause**: Test email doesn't match ALLOWED_EMAIL.

**Fix**:
```bash
# Ensure ALLOWED_EMAIL matches your test email
ALLOWED_EMAIL=test@example.com
```

### "Token is expired"

**Cause**: System clock skew or test took > 24 hours.

**Fix**: Tokens expire after 24 hours. Restart the test or check system time.

### Tests still redirecting to OAuth login

**Cause**: Token not being set in localStorage or token invalid.

**Fix**:
```typescript
// Add debugging
test('debug auth', async ({ authenticatedPage, testAuthToken }) => {
  console.log('Token:', testAuthToken);

  const stored = await authenticatedPage.evaluate(() =>
    localStorage.getItem('personal_q_token')
  );
  console.log('Stored token:', stored);
});
```

## Production Safety

### What happens if someone tries to access the test endpoint in production?

1. **Import-time check**: The module raises `RuntimeError` when imported
2. **Registration check**: Router is never included in the FastAPI app
3. **Runtime check**: Even if somehow accessed, returns 404

### How do we verify it's safe?

1. **Automated tests**: `auth-test-endpoint-security.spec.ts` validates all safety measures
2. **Code review**: Triple-layer security is documented and reviewed
3. **Environment validation**: Pydantic validates settings at startup
4. **Audit logs**: All test auth attempts are logged for security monitoring

## Best Practices

### ✅ Do

- Use `authenticatedPage` fixture for most tests
- Set `ENV=development` or `ENV=test` in test environments
- Keep test email in `ALLOWED_EMAIL` environment variable
- Run security validation tests before deployment
- Review backend logs for test auth usage

### ❌ Don't

- Don't set `ENV=production` in test environments
- Don't hardcode test credentials in test files
- Don't use test auth in production
- Don't share JWT_SECRET_KEY between test and production
- Don't skip security validation tests

## Implementation Details

### Files Created

**Backend:**
- `backend/app/routers/auth_test.py` - Test auth endpoint with security checks
- `backend/app/main.py` - Conditionally includes test router

**Frontend:**
- `src/utils/testAuth.ts` - Test auth utilities

**Tests:**
- `tests/fixtures/auth.ts` - Reusable auth fixtures
- `tests/auth-test-endpoint-security.spec.ts` - Security validation tests
- `tests/agent-update-integration.spec.ts` - Updated to use real auth

### Token Format

Test tokens use the same format as production OAuth tokens:

```json
{
  "alg": "HS256",
  "typ": "JWT"
}
{
  "sub": "test@example.com",
  "email": "test@example.com",
  "iat": 1234567890,
  "exp": 1234654290  // +24 hours
}
```

This ensures tests validate against the actual production token format.

## Comparison with Other Approaches

| Approach | Speed | CI/CD Ready | Security | Complexity |
|----------|-------|-------------|----------|------------|
| **Test Endpoint** ✅ | ⚡ <500ms | ✅ Yes | 🔒 High | 📝 Low |
| Google OAuth | 🐌 5-10s | ❌ No | 🔒 High | 📝 High |
| Mocked OAuth | ⚡ Fast | ✅ Yes | ⚠️ Medium | 📝 Medium |
| Debug Bypass | ⚡ Fast | ✅ Yes | ⚠️ **LOW** | 📝 Very Low |

## Further Reading

- [Playwright Authentication Documentation](https://playwright.dev/docs/auth)
- [FastAPI Security Best Practices](https://fastapi.tiangolo.com/tutorial/security/)
- [JWT Best Practices](https://tools.ietf.org/html/rfc8725)
