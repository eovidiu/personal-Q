/**
 * Test Authentication Utilities
 *
 * Provides helper functions for authenticating in Playwright E2E tests without Google OAuth.
 * These utilities call the backend test-only authentication endpoint.
 *
 * SECURITY: Only available in non-production environments.
 * Production builds will have these functions stubbed out.
 */

import { TOKEN_STORAGE_KEY, API_BASE_URL } from '@/constants/auth';

/**
 * Test-only login that bypasses Google OAuth.
 *
 * Calls the backend /auth/test-login endpoint to obtain a real JWT token
 * without going through the Google OAuth flow.
 *
 * @param email - Email address to authenticate (must match ALLOWED_EMAIL)
 * @returns JWT access token
 * @throws Error if test auth is not available or authentication fails
 */
export async function loginForTesting(email: string): Promise<string> {
  // Environment check - only allow in development/test
  if (import.meta.env.PROD) {
    throw new Error(
      'Test authentication is not available in production builds. ' +
      'Use real Google OAuth authentication.'
    );
  }

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
      `Test login failed: ${error.detail || response.statusText}`
    );
  }

  const data = await response.json();
  return data.access_token;
}

/**
 * Set test token in localStorage and return it.
 *
 * This is useful for Playwright tests that need to set authentication
 * before navigating to the app.
 *
 * @param token - JWT token to store
 */
export function setTestToken(token: string): void {
  localStorage.setItem(TOKEN_STORAGE_KEY, token);
}

/**
 * Clear test authentication from localStorage.
 *
 * Useful for test cleanup and testing logout flows.
 */
export function clearTestAuth(): void {
  localStorage.removeItem(TOKEN_STORAGE_KEY);
}

/**
 * Validate test auth endpoint is available.
 *
 * Useful for test setup validation and debugging.
 *
 * @returns Promise<boolean> - true if test auth is available
 */
export async function isTestAuthAvailable(): Promise<boolean> {
  try {
    const response = await fetch(`${API_BASE_URL}/api/v1/auth/test-validate`);
    return response.ok;
  } catch {
    return false;
  }
}

/**
 * Complete test authentication flow.
 *
 * Combines login + token storage in one call.
 * This is the most common usage in Playwright tests.
 *
 * @param email - Email to authenticate
 * @returns JWT access token
 */
export async function authenticateForTesting(email: string): Promise<string> {
  const token = await loginForTesting(email);
  setTestToken(token);
  return token;
}
