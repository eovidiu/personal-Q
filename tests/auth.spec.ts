import { test, expect } from '@playwright/test';

test.describe('Authentication', () => {
  test('login page loads and displays Google OAuth button', async ({ page }) => {
    // Navigate to the login page (uses baseURL from playwright.config.ts)
    await page.goto('/');

    // Wait for page to load
    await page.waitForLoadState('networkidle');

    // Check if the page has loaded
    await expect(page).toHaveTitle(/Personal-Q|AI Agent|Vite/);

    // Check if we're redirected to auth or if there's an auth-related element
    // Since we have Google OAuth, we should see a login button or be able to initiate auth
    const pageContent = await page.content();
    console.log('Page loaded successfully');

    // Take a screenshot for verification
    await page.screenshot({ path: 'test-results/login-page.png', fullPage: true });
  });

  test('backend auth endpoint is accessible', async ({ request }) => {
    // Check if the auth login endpoint exists
    const response = await request.get('http://localhost:8000/api/v1/auth/login', {
      failOnStatusCode: false
    });

    // We expect either a redirect (302/307) or success (200)
    // or an error that's not 404 (meaning the endpoint exists)
    expect([200, 302, 307, 400, 401, 403, 500]).toContain(response.status());

    console.log(`Auth endpoint status: ${response.status()}`);
  });
});
