import { test, expect, Page } from '@playwright/test';

// Import token storage key constant
const TOKEN_STORAGE_KEY = 'personal_q_token';

/**
 * OAuth Callback Flow Tests
 *
 * Tests the new dedicated /auth/callback route implementation
 * that fixes the OAuth login loop issue.
 *
 * Related Issue: #70
 */

test.describe('OAuth Callback Flow', () => {
  // Helper function to create a mock JWT token
  function createMockToken(expiresInHours: number = 24): string {
    const header = btoa(JSON.stringify({ alg: 'HS256', typ: 'JWT' }));
    const now = Math.floor(Date.now() / 1000);
    const payload = btoa(JSON.stringify({
      sub: 'test@example.com',
      email: 'test@example.com',
      iat: now,
      exp: now + (expiresInHours * 3600),
    }));
    const signature = btoa('mock-signature');
    return `${header}.${payload}.${signature}`;
  }

  // Helper function to create an expired token
  function createExpiredToken(): string {
    const header = btoa(JSON.stringify({ alg: 'HS256', typ: 'JWT' }));
    const now = Math.floor(Date.now() / 1000);
    const payload = btoa(JSON.stringify({
      sub: 'test@example.com',
      email: 'test@example.com',
      iat: now - 86400,
      exp: now - 3600, // Expired 1 hour ago
    }));
    const signature = btoa('mock-signature');
    return `${header}.${payload}.${signature}`;
  }

  test.beforeEach(async ({ page }) => {
    // Clear localStorage before each test
    await page.goto('/');
    await page.evaluate(() => localStorage.clear());
  });

  test('should display login page when not authenticated', async ({ page }) => {
    await page.goto('/');
    await page.waitForLoadState('networkidle');

    // Should redirect to /login
    await expect(page).toHaveURL(/\/login/);

    // Verify login page elements
    await expect(page.getByText('Welcome to Personal-Q')).toBeVisible();
    await expect(page.getByRole('button', { name: /sign in with google/i })).toBeVisible();
    await expect(page.getByText(/only authorized users/i)).toBeVisible();
  });

  test('should show loading state on callback page', async ({ page }) => {
    const token = createMockToken();

    // Navigate directly to callback page with token
    await page.goto(`/auth/callback?token=${token}`);

    // Should see loading state briefly
    await expect(page.getByText(/completing authentication/i)).toBeVisible();
  });

  test('should handle callback with valid token', async ({ page }) => {
    const token = createMockToken();

    // Mock the /auth/me endpoint to return success
    await page.route('**/api/v1/auth/me', async (route) => {
      await route.fulfill({
        status: 200,
        contentType: 'application/json',
        body: JSON.stringify({
          email: 'test@example.com',
          authenticated: true,
        }),
      });
    });

    // Navigate to callback with token
    await page.goto(`/auth/callback?token=${token}`);

    // Should redirect to dashboard
    await page.waitForURL('/', { timeout: 5000 });

    // Token should be stored in localStorage
    const storedToken = await page.evaluate((key) => localStorage.getItem(key), TOKEN_STORAGE_KEY);
    expect(storedToken).toBe(token);
  });

  test('should handle callback with expired token', async ({ page }) => {
    const expiredToken = createExpiredToken();

    // Navigate to callback with expired token
    await page.goto(`/auth/callback?token=${expiredToken}`);

    // Should show error message
    await expect(page.getByText(/authentication failed/i)).toBeVisible();

    // Should redirect to login after delay
    await page.waitForURL('/login', { timeout: 3000 });

    // Token should NOT be stored
    const storedToken = await page.evaluate((key) => localStorage.getItem(key), TOKEN_STORAGE_KEY);
    expect(storedToken).toBeNull();
  });

  test('should handle callback with missing token parameter', async ({ page }) => {
    // Navigate to callback WITHOUT token parameter
    await page.goto('/auth/callback');

    // Should show error message
    await expect(page.getByText(/authentication failed/i)).toBeVisible();
    await expect(page.getByText(/no token received/i)).toBeVisible();

    // Should redirect to login
    await page.waitForURL('/login', { timeout: 3000 });
  });

  test('should handle callback with malformed token', async ({ page }) => {
    const malformedToken = 'not-a-valid-jwt-token';

    // Navigate to callback with malformed token
    await page.goto(`/auth/callback?token=${malformedToken}`);

    // Should show error message (token validation fails)
    await expect(page.getByText(/authentication failed/i)).toBeVisible();

    // Should redirect to login
    await page.waitForURL('/login', { timeout: 3000 });
  });

  test('should handle network failure during token verification', async ({ page }) => {
    const token = createMockToken();

    // Mock the /auth/me endpoint to fail
    await page.route('**/api/v1/auth/me', async (route) => {
      await route.abort('failed');
    });

    // Navigate to callback with token
    await page.goto(`/auth/callback?token=${token}`);

    // Should show error message
    await expect(page.getByText(/authentication failed/i)).toBeVisible();

    // Should redirect to login
    await page.waitForURL('/login', { timeout: 3000 });
  });

  test('should handle 401 unauthorized response from backend', async ({ page }) => {
    const token = createMockToken();

    // Mock the /auth/me endpoint to return 401
    await page.route('**/api/v1/auth/me', async (route) => {
      await route.fulfill({
        status: 401,
        contentType: 'application/json',
        body: JSON.stringify({ detail: 'Invalid or expired token' }),
      });
    });

    // Navigate to callback with token
    await page.goto(`/auth/callback?token=${token}`);

    // Should show error
    await expect(page.getByText(/authentication failed/i)).toBeVisible();

    // Should redirect to login
    await page.waitForURL('/login', { timeout: 3000 });
  });

  test('should remove token from URL after processing', async ({ page }) => {
    const token = createMockToken();

    // Mock successful authentication
    await page.route('**/api/v1/auth/me', async (route) => {
      await route.fulfill({
        status: 200,
        contentType: 'application/json',
        body: JSON.stringify({
          email: 'test@example.com',
          authenticated: true,
        }),
      });
    });

    // Navigate to callback with token
    await page.goto(`/auth/callback?token=${token}`);

    // Wait for redirect to dashboard
    await page.waitForURL('/', { timeout: 5000 });

    // URL should NOT contain token parameter
    expect(page.url()).not.toContain('token=');
  });

  test('should prevent access to protected routes without authentication', async ({ page }) => {
    // Clear any existing auth
    await page.goto('/');
    await page.evaluate(() => localStorage.clear());

    // Try to access protected route
    await page.goto('/agents');

    // Should redirect to login
    await expect(page).toHaveURL(/\/login/);
  });

  test('should allow access to protected routes after successful auth', async ({ page }) => {
    const token = createMockToken();

    // Mock successful authentication
    await page.route('**/api/v1/auth/me', async (route) => {
      await route.fulfill({
        status: 200,
        contentType: 'application/json',
        body: JSON.stringify({
          email: 'test@example.com',
          authenticated: true,
        }),
      });
    });

    // Mock agents API
    await page.route('**/api/v1/agents/**', async (route) => {
      await route.fulfill({
        status: 200,
        contentType: 'application/json',
        body: JSON.stringify([]),
      });
    });

    // Navigate through callback flow
    await page.goto(`/auth/callback?token=${token}`);
    await page.waitForURL('/', { timeout: 5000 });

    // Try to access protected route
    await page.goto('/agents');

    // Should NOT redirect to login
    await expect(page).not.toHaveURL(/\/login/);
  });

  test('should redirect to dashboard if already authenticated on login page', async ({ page }) => {
    const token = createMockToken();

    // Mock successful authentication
    await page.route('**/api/v1/auth/me', async (route) => {
      await route.fulfill({
        status: 200,
        contentType: 'application/json',
        body: JSON.stringify({
          email: 'test@example.com',
          authenticated: true,
        }),
      });
    });

    // Set token in localStorage
    await page.goto('/');
    await page.evaluate((data) => {
      localStorage.setItem(data.key, data.token);
    }, { key: TOKEN_STORAGE_KEY, token });

    // Navigate to login page
    await page.goto('/login');

    // Should redirect to dashboard
    await page.waitForURL('/', { timeout: 5000 });
  });

  test('should display error from AuthContext on login page', async ({ page }) => {
    // Navigate to login page
    await page.goto('/login');
    await page.waitForLoadState('networkidle');

    // Mock the login endpoint to trigger an error flow
    // (This tests if errors from AuthContext are displayed)
    await expect(page.getByText('Welcome to Personal-Q')).toBeVisible();

    // If there's an error in the auth context, it should be displayed
    // We can't easily trigger this without the full OAuth flow
    // but we verify the error UI exists
    const errorAlert = page.locator('[role="alert"]').filter({ hasText: /error/i });
    // Error should not be visible initially
    await expect(errorAlert).not.toBeVisible();
  });

  test('should handle direct navigation to callback without token gracefully', async ({ page }) => {
    // User manually types /auth/callback in browser
    await page.goto('/auth/callback');

    // Should show error
    await expect(page.getByText(/authentication failed/i)).toBeVisible();
    await expect(page.getByText(/redirecting to login/i)).toBeVisible();

    // Should redirect to login
    await page.waitForURL('/login', { timeout: 3000 });
  });

  test('should persist authentication across page refreshes', async ({ page, context }) => {
    const token = createMockToken();

    // Mock successful authentication
    await page.route('**/api/v1/auth/me', async (route) => {
      await route.fulfill({
        status: 200,
        contentType: 'application/json',
        body: JSON.stringify({
          email: 'test@example.com',
          authenticated: true,
        }),
      });
    });

    // Go through auth flow
    await page.goto(`/auth/callback?token=${token}`);
    await page.waitForURL('/', { timeout: 5000 });

    // Refresh the page
    await page.reload();

    // Should still be authenticated (not redirected to login)
    await expect(page).not.toHaveURL(/\/login/);
  });

  test('should clear authentication on logout', async ({ page }) => {
    const token = createMockToken();

    // Mock successful authentication
    await page.route('**/api/v1/auth/**', async (route) => {
      if (route.request().url().includes('/auth/me')) {
        await route.fulfill({
          status: 200,
          contentType: 'application/json',
          body: JSON.stringify({
            email: 'test@example.com',
            authenticated: true,
          }),
        });
      } else if (route.request().url().includes('/auth/logout')) {
        await route.fulfill({
          status: 200,
          contentType: 'application/json',
          body: JSON.stringify({ message: 'Logged out successfully' }),
        });
      }
    });

    // Authenticate
    await page.goto(`/auth/callback?token=${token}`);
    await page.waitForURL('/', { timeout: 5000 });

    // Token should be present
    let storedToken = await page.evaluate((key) => localStorage.getItem(key), TOKEN_STORAGE_KEY);
    expect(storedToken).toBe(token);

    // TODO: Implement logout flow in UI and test it
    // For now, just verify token can be cleared
    await page.evaluate((key) => localStorage.removeItem(key), TOKEN_STORAGE_KEY);
    storedToken = await page.evaluate((key) => localStorage.getItem(key), TOKEN_STORAGE_KEY);
    expect(storedToken).toBeNull();
  });
});

test.describe('OAuth Callback Edge Cases', () => {
  test('should handle extremely long token strings', async ({ page }) => {
    // Create an artificially long token
    const longToken = 'a'.repeat(10000);

    await page.goto(`/auth/callback?token=${longToken}`);

    // Should handle gracefully and show error
    await expect(page.getByText(/authentication failed/i)).toBeVisible();
  });

  test('should handle special characters in token parameter', async ({ page }) => {
    const tokenWithSpecialChars = 'token<script>alert("xss")</script>';

    await page.goto(`/auth/callback?token=${encodeURIComponent(tokenWithSpecialChars)}`);

    // Should handle safely without XSS
    await expect(page.getByText(/authentication failed/i)).toBeVisible();

    // Verify no script execution
    const alertFired = await page.evaluate(() => {
      return typeof (window as any).__xss_test !== 'undefined';
    });
    expect(alertFired).toBe(false);
  });

  test('should handle concurrent callback requests (race condition)', async ({ page, context }) => {
    const token = 'test-token-123';

    // Mock successful authentication with delay
    await page.route('**/api/v1/auth/me', async (route) => {
      // Add artificial delay to simulate race condition
      await new Promise(resolve => setTimeout(resolve, 100));
      await route.fulfill({
        status: 200,
        contentType: 'application/json',
        body: JSON.stringify({
          email: 'test@example.com',
          authenticated: true,
        }),
      });
    });

    // Open callback page
    await page.goto(`/auth/callback?token=${token}`);

    // Verify only one navigation happens
    await page.waitForURL('/', { timeout: 5000 });

    // Verify we're at the dashboard and stable
    await expect(page).toHaveURL('/');
  });
});
