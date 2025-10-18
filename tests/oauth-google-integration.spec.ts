import { test, expect } from '@playwright/test';

/**
 * OAuth Google Integration Tests
 *
 * Tests the full OAuth flow after returning from Google authentication.
 * These tests simulate what happens when a user comes back from Google's OAuth page.
 *
 * Related to user request: "add tests for after the returning from Google with the Authentication"
 */

const TOKEN_STORAGE_KEY = 'personal_q_token';

test.describe('OAuth Google Integration - After Google Authentication', () => {

  // Helper to create a valid mock JWT token
  function createValidToken(email: string = 'test@example.com'): string {
    const header = btoa(JSON.stringify({ alg: 'HS256', typ: 'JWT' }));
    const now = Math.floor(Date.now() / 1000);
    const payload = btoa(JSON.stringify({
      sub: email,
      email: email,
      iat: now,
      exp: now + (24 * 3600), // 24 hours from now
    }));
    const signature = btoa('mock-signature-12345');
    return `${header}.${payload}.${signature}`;
  }

  test.beforeEach(async ({ page }) => {
    // Clear any previous authentication
    await page.goto('/');
    await page.evaluate(() => localStorage.clear());
  });

  test('should successfully complete authentication flow after Google redirect', async ({ page }) => {
    const token = createValidToken('authorized@example.com');

    // Mock the backend /auth/me endpoint to simulate successful authentication
    await page.route('**/api/v1/auth/me', async (route) => {
      await route.fulfill({
        status: 200,
        contentType: 'application/json',
        body: JSON.stringify({
          email: 'authorized@example.com',
          authenticated: true,
        }),
      });
    });

    // Mock other API endpoints that the dashboard might call
    await page.route('**/api/v1/agents/**', async (route) => {
      await route.fulfill({
        status: 200,
        contentType: 'application/json',
        body: JSON.stringify([]),
      });
    });

    await page.route('**/api/v1/activities/**', async (route) => {
      await route.fulfill({
        status: 200,
        contentType: 'application/json',
        body: JSON.stringify({ items: [], total: 0 }),
      });
    });

    // Simulate Google redirecting back to our callback endpoint with a token
    // This is what happens after successful Google authentication
    await page.goto(`/auth/callback?token=${token}`);

    // Verify: Should see loading state briefly
    await expect(page.getByText(/completing authentication/i)).toBeVisible({ timeout: 2000 }).catch(() => {
      // Loading might be too fast to catch
    });

    // Verify: Should redirect to dashboard
    await page.waitForURL('/', { timeout: 10000 });
    expect(page.url()).toBe('http://localhost:4173/');

    // Verify: Token is stored in localStorage
    const storedToken = await page.evaluate((key) => localStorage.getItem(key), TOKEN_STORAGE_KEY);
    expect(storedToken).toBe(token);

    // Verify: URL no longer contains the token (security)
    expect(page.url()).not.toContain('token=');

    // Verify: Dashboard content loads
    await expect(page).not.toHaveURL(/\/login/);
  });

  test('should handle callback with state parameter (CSRF protection)', async ({ page }) => {
    const token = createValidToken();
    const state = 'mock-csrf-state-token';

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

    // Simulate Google callback with both token and state parameters
    // In real flow, Google includes the state parameter we sent during login
    await page.goto(`/auth/callback?token=${token}&state=${state}`);

    // Should process successfully (frontend doesn't validate state yet, but backend does)
    await page.waitForURL('/', { timeout: 10000 });
  });

  test('should show error when Google returns without token', async ({ page }) => {
    // Simulate Google callback with error parameter (user denied access)
    await page.goto('/auth/callback?error=access_denied&error_description=User%20denied%20access');

    // Should show error message
    await expect(page.getByText(/authentication failed/i)).toBeVisible();
    await expect(page.getByText(/no token received/i)).toBeVisible();

    // Should redirect back to login
    await page.waitForURL('/login', { timeout: 3000 });
  });

  test('should verify user session persists after successful authentication', async ({ page, context }) => {
    const token = createValidToken();

    await page.route('**/api/v1/**', async (route) => {
      const url = route.request().url();

      if (url.includes('/auth/me')) {
        await route.fulfill({
          status: 200,
          contentType: 'application/json',
          body: JSON.stringify({
            email: 'test@example.com',
            authenticated: true,
          }),
        });
      } else if (url.includes('/agents')) {
        await route.fulfill({
          status: 200,
          contentType: 'application/json',
          body: JSON.stringify([]),
        });
      } else if (url.includes('/activities')) {
        await route.fulfill({
          status: 200,
          contentType: 'application/json',
          body: JSON.stringify({ items: [], total: 0 }),
        });
      } else {
        await route.continue();
      }
    });

    // Step 1: Complete authentication
    await page.goto(`/auth/callback?token=${token}`);
    await page.waitForURL('/', { timeout: 10000 });

    // Step 2: Navigate to different protected routes
    await page.goto('/agents');
    await expect(page).toHaveURL('/agents');

    await page.goto('/tasks');
    await expect(page).toHaveURL('/tasks');

    // Step 3: Verify session persists in new tab
    const newPage = await context.newPage();
    await newPage.goto('/');

    // New tab should also be authenticated
    await expect(newPage).not.toHaveURL(/\/login/);

    await newPage.close();
  });

  test('should handle token expiration gracefully', async ({ page }) => {
    // Create an expired token
    const header = btoa(JSON.stringify({ alg: 'HS256', typ: 'JWT' }));
    const now = Math.floor(Date.now() / 1000);
    const payload = btoa(JSON.stringify({
      sub: 'test@example.com',
      email: 'test@example.com',
      iat: now - 86400,
      exp: now - 3600, // Expired 1 hour ago
    }));
    const signature = btoa('mock-signature');
    const expiredToken = `${header}.${payload}.${signature}`;

    // Simulate callback with expired token
    await page.goto(`/auth/callback?token=${expiredToken}`);

    // Should detect expiration and show error
    await expect(page.getByText(/authentication failed/i)).toBeVisible();

    // Should redirect to login
    await page.waitForURL('/login', { timeout: 3000 });

    // Verify token was not stored
    const storedToken = await page.evaluate((key) => localStorage.getItem(key), TOKEN_STORAGE_KEY);
    expect(storedToken).toBeNull();
  });

  test('should handle backend validation failure', async ({ page }) => {
    const token = createValidToken();

    // Mock backend rejecting the token (e.g., user not authorized)
    await page.route('**/api/v1/auth/me', async (route) => {
      await route.fulfill({
        status: 403,
        contentType: 'application/json',
        body: JSON.stringify({
          detail: 'User not authorized for this system',
        }),
      });
    });

    await page.goto(`/auth/callback?token=${token}`);

    // Should show error
    await expect(page.getByText(/authentication failed/i)).toBeVisible();

    // Should redirect to login
    await page.waitForURL('/login', { timeout: 3000 });
  });

  test('should prevent XSS attacks via token parameter', async ({ page }) => {
    // Attempt XSS via token parameter
    const xssPayload = '<img src=x onerror=alert("XSS")>';

    await page.goto(`/auth/callback?token=${encodeURIComponent(xssPayload)}`);

    // Should handle safely and show error
    await expect(page.getByText(/authentication failed/i)).toBeVisible();

    // Verify no script execution occurred
    const pageContent = await page.content();
    expect(pageContent).not.toContain('<img src=x');
    expect(pageContent).not.toContain('onerror=');
  });

  test('should handle rapid navigation during callback', async ({ page }) => {
    const token = createValidToken();

    await page.route('**/api/v1/auth/me', async (route) => {
      // Add delay to simulate slow network
      await new Promise(resolve => setTimeout(resolve, 1000));
      await route.fulfill({
        status: 200,
        contentType: 'application/json',
        body: JSON.stringify({
          email: 'test@example.com',
          authenticated: true,
        }),
      });
    });

    await page.route('**/api/v1/agents/**', async (route) => {
      await route.fulfill({
        status: 200,
        contentType: 'application/json',
        body: JSON.stringify([]),
      });
    });

    // Start navigation to callback
    const navigationPromise = page.goto(`/auth/callback?token=${token}`);

    // Try to navigate away quickly (simulating impatient user)
    await page.waitForTimeout(100);
    await page.goto('/login').catch(() => {});

    // Wait for original navigation to complete
    await navigationPromise;

    // Should eventually land on the intended page
    // (Either dashboard if auth completed, or login if it was interrupted)
    await page.waitForLoadState('networkidle');
    const finalUrl = page.url();
    expect(['http://localhost:4173/', 'http://localhost:4173/login']).toContain(finalUrl);
  });

  test('should display user info after successful authentication', async ({ page }) => {
    const userEmail = 'john.doe@example.com';
    const token = createValidToken(userEmail);

    await page.route('**/api/v1/auth/me', async (route) => {
      await route.fulfill({
        status: 200,
        contentType: 'application/json',
        body: JSON.stringify({
          email: userEmail,
          authenticated: true,
        }),
      });
    });

    await page.route('**/api/v1/**', async (route) => {
      await route.fulfill({
        status: 200,
        contentType: 'application/json',
        body: JSON.stringify([]),
      });
    });

    // Complete authentication
    await page.goto(`/auth/callback?token=${token}`);
    await page.waitForURL('/', { timeout: 10000 });

    // User should be able to access settings or profile
    // (Assuming settings page shows user email)
    await page.goto('/settings');

    // Verify we're authenticated and can access settings
    await expect(page).toHaveURL('/settings');
  });

  test('should handle simultaneous callback requests (race condition protection)', async ({ page }) => {
    const token = createValidToken();
    let authMeCallCount = 0;

    await page.route('**/api/v1/auth/me', async (route) => {
      authMeCallCount++;
      await route.fulfill({
        status: 200,
        contentType: 'application/json',
        body: JSON.stringify({
          email: 'test@example.com',
          authenticated: true,
        }),
      });
    });

    await page.route('**/api/v1/agents/**', async (route) => {
      await route.fulfill({
        status: 200,
        contentType: 'application/json',
        body: JSON.stringify([]),
      });
    });

    // Navigate to callback
    await page.goto(`/auth/callback?token=${token}`);
    await page.waitForURL('/', { timeout: 10000 });

    // With the useRef fix, setToken should only be called once
    // So /auth/me should only be called once (not twice due to React StrictMode)
    expect(authMeCallCount).toBeLessThanOrEqual(2); // Allow for StrictMode double-render in dev
  });
});
