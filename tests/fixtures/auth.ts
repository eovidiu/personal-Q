/**
 * Playwright Authentication Fixtures
 *
 * Provides reusable authentication fixtures for E2E tests using the test-only
 * authentication endpoint instead of Google OAuth.
 *
 * Usage:
 * ```typescript
 * import { test } from './fixtures/auth';
 *
 * test('my test', async ({ authenticatedPage }) => {
 *   // Page is already authenticated
 *   await authenticatedPage.goto('/agents');
 * });
 * ```
 */

import { test as base, Page } from '@playwright/test';

const API_BASE_URL = process.env.VITE_API_BASE_URL || 'http://localhost:8000';
const TOKEN_STORAGE_KEY = 'personal_q_token';
const DEFAULT_TEST_EMAIL = process.env.ALLOWED_EMAIL || 'test@example.com';

/**
 * Get JWT token from test authentication endpoint.
 *
 * @param email - Email to authenticate (must match backend ALLOWED_EMAIL)
 * @returns JWT access token
 */
async function getTestAuthToken(email: string = DEFAULT_TEST_EMAIL): Promise<string> {
  const response = await fetch(`${API_BASE_URL}/api/v1/auth/test-login`, {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
    },
    body: JSON.stringify({ email }),
  });

  if (!response.ok) {
    const error = await response.json().catch(() => ({ detail: 'Unknown error' }));
    throw new Error(
      `Test authentication failed: ${error.detail || response.statusText}. ` +
      `Make sure backend is running and ALLOWED_EMAIL is set to '${email}'.`
    );
  }

  const data = await response.json();
  return data.access_token;
}

/**
 * Extended test fixtures with authentication support.
 */
type AuthFixtures = {
  /**
   * Authenticated page fixture.
   *
   * Automatically authenticates the page before each test by:
   * 1. Calling the test auth endpoint to get a real JWT token
   * 2. Storing the token in localStorage
   * 3. Returning the authenticated page
   *
   * Example:
   * ```typescript
   * test('should access protected route', async ({ authenticatedPage }) => {
   *   await authenticatedPage.goto('/agents');
   *   await expect(authenticatedPage).toHaveURL('/agents');
   * });
   * ```
   */
  authenticatedPage: Page;

  /**
   * Test authentication token.
   *
   * Provides the JWT token without setting up the page.
   * Useful for API testing or manual token management.
   *
   * Example:
   * ```typescript
   * test('should call API with token', async ({ testAuthToken }) => {
   *   const response = await fetch('/api/v1/agents', {
   *     headers: { 'Authorization': `Bearer ${testAuthToken}` }
   *   });
   * });
   * ```
   */
  testAuthToken: string;
};

/**
 * Export test with authentication fixtures.
 *
 * Import this instead of @playwright/test to get auth fixtures:
 * ```typescript
 * import { test, expect } from './fixtures/auth';
 * ```
 */
export const test = base.extend<AuthFixtures>({
  // Fixture: testAuthToken
  testAuthToken: async ({}, use) => {
    const token = await getTestAuthToken();
    await use(token);
    // No cleanup needed - token will expire naturally
  },

  // Fixture: authenticatedPage
  authenticatedPage: async ({ page, testAuthToken }, use) => {
    // Set up authentication before test runs
    await page.goto('/');
    await page.evaluate(
      ({ token, storageKey }) => {
        localStorage.setItem(storageKey, token);
      },
      { token: testAuthToken, storageKey: TOKEN_STORAGE_KEY }
    );

    // Page is now authenticated - pass to test
    await use(page);

    // Cleanup after test
    await page.evaluate((storageKey) => {
      localStorage.removeItem(storageKey);
    }, TOKEN_STORAGE_KEY);
  },
});

/**
 * Re-export expect from Playwright for convenience.
 */
export { expect } from '@playwright/test';

/**
 * Helper function to manually authenticate a page.
 *
 * Use this if you need to authenticate an existing page or
 * if you don't want to use the fixture.
 *
 * @param page - Playwright Page object
 * @param email - Email to authenticate (optional)
 */
export async function authenticatePage(
  page: Page,
  email: string = DEFAULT_TEST_EMAIL
): Promise<void> {
  const token = await getTestAuthToken(email);

  await page.goto('/');
  await page.evaluate(
    ({ token, storageKey }) => {
      localStorage.setItem(storageKey, token);
    },
    { token, storageKey: TOKEN_STORAGE_KEY }
  );
}

/**
 * Helper function to clear authentication from a page.
 *
 * @param page - Playwright Page object
 */
export async function clearAuthentication(page: Page): Promise<void> {
  await page.evaluate((storageKey) => {
    localStorage.removeItem(storageKey);
  }, TOKEN_STORAGE_KEY);
}
