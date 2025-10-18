# Playwright Test Suite

This directory contains E2E tests for the Personal-Q application.

## Test Files

### `agent-update-integration.spec.ts`
Integration tests for the Update Agent functionality. Tests the complete flow from opening the edit dialog, updating fields, and verifying the changes are saved correctly.

**Key scenarios tested:**
- Field name transformation (camelCase → snake_case): `maxTokens` → `max_tokens`, `systemPrompt` → `system_prompt`, `type` → `agent_type`
- Dialog open/close behavior
- Form field updates (name, description, temperature, max tokens, system prompt)
- API request validation
- UI update verification

### `agent-update.spec.ts`
Unit-style tests with comprehensive API mocking. Currently has mocking issues - use `agent-update-integration.spec.ts` instead for reliable testing.

### `oauth-callback.spec.ts`
Tests for OAuth callback flow and CSRF protection.

### `oauth-google-integration.spec.ts`
Integration tests for Google OAuth authentication.

## Running Tests

### Prerequisites

1. **Start the backend:**
   ```bash
   docker-compose up -d backend redis db
   ```

2. **Start the frontend:**
   ```bash
   npm run dev
   ```

3. **Ensure you have test data:**
   - At least one agent should exist in the database
   - A test user account should be available

### Run All Tests
```bash
npx playwright test
```

### Run Specific Test File
```bash
npx playwright test tests/agent-update-integration.spec.ts
```

### Run Tests in UI Mode (Recommended for debugging)
```bash
npx playwright test --ui
```

### Run Tests in Headed Mode (See browser)
```bash
npx playwright test --headed
```

### Run Single Test
```bash
npx playwright test -g "should successfully update agent name and description"
```

## Test Configuration

Configuration is in `playwright.config.ts`. Key settings:

- **Base URL**: `http://localhost:5173`
- **API URL**: `http://localhost:8000`
- **Timeout**: 30 seconds per test
- **Retries**: 2 on CI, 0 locally

## Authentication in Tests

The integration tests assume you're already authenticated. For automated testing:

1. **Option 1 - Manual login first:**
   - Open browser manually
   - Login via Google OAuth
   - Browser state will be saved
   - Tests will use the saved session

2. **Option 2 - Mock authentication:**
   - Set up test user with email/password
   - Use direct token endpoint instead of OAuth

3. **Option 3 - Use Playwright storage state:**
   ```typescript
   // In playwright.config.ts
   use: {
     storageState: 'tests/.auth/user.json'
   }
   ```

## Debugging Failed Tests

### View test report
```bash
npx playwright show-report
```

### Enable debug mode
```bash
PWDEBUG=1 npx playwright test
```

### Take screenshots on failure
Already enabled in config:
```typescript
screenshot: 'only-on-failure'
```

### Record video
```bash
npx playwright test --video=on
```

## Common Issues

### 1. "Configure button not found"
**Cause**: Page not fully loaded or agent data not available
**Solution**: Check that backend is running and has test data

### 2. "Dialog did not close"
**Cause**: API error or validation failure
**Solution**: Check browser console and backend logs for errors

### 3. "Request body verification failed"
**Cause**: Field name transformation not working
**Solution**: Verify AgentForm.tsx has the transformation logic in handleSubmit

### 4. Authentication timeout
**Cause**: Not logged in or session expired
**Solution**: Login manually first, or set up test auth

## Best Practices

1. **Use integration tests** for critical user flows (like `agent-update-integration.spec.ts`)
2. **Mock only when necessary** - real backend testing catches more bugs
3. **Clean up after tests** - restore original values to avoid test pollution
4. **Use data-testid** for reliable element selection
5. **Wait for network idle** before interactions
6. **Verify both UI and API** - check visual changes AND request payloads

## Adding New Tests

When adding new test files:

1. Use descriptive names: `feature-name.spec.ts`
2. Add test documentation at the top of the file
3. Include setup instructions in beforeEach
4. Clean up test data in afterEach
5. Add to this README with key scenarios tested
