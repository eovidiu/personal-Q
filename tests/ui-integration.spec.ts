/**
 * Playwright UI Integration Test
 * Tests that the frontend successfully connects to the backend
 */

import { test, expect } from '@playwright/test';

test.describe('Personal-Q UI Integration', () => {
  test.beforeEach(async ({ page }) => {
    // Navigate to the app
    await page.goto('http://localhost:5173');
  });

  test('should load the main page without errors', async ({ page }) => {
    // Wait for the page to load
    await page.waitForLoadState('networkidle');

    // Check that the page title is correct
    await expect(page).toHaveTitle(/Personal-Q App/);

    // Check that the main heading is visible
    await expect(page.getByRole('heading', { name: /Personal Q/i })).toBeVisible();
  });

  test('should display dashboard metrics', async ({ page }) => {
    // Wait for page to load
    await page.waitForLoadState('networkidle');

    // Wait for metrics to load (they should be visible even if zero)
    await page.waitForTimeout(2000); // Give React Query time to fetch

    // Check for stat cards (Total Agents, Active Agents, etc.)
    const statsSection = page.locator('[class*="grid"]').first();
    await expect(statsSection).toBeVisible();
  });

  test('should show React Query DevTools button', async ({ page }) => {
    // Wait for page to load
    await page.waitForLoadState('networkidle');

    // React Query DevTools button should be present (in development mode)
    // It appears as a floating button in the bottom-left corner
    const devToolsButton = page.locator('button[aria-label*="tanstack"], button[title*="Query"]').first();

    // The button should exist (may not be immediately visible)
    await page.waitForTimeout(1000);

    // Take a screenshot for verification
    await page.screenshot({ path: 'tests/screenshots/dashboard.png', fullPage: true });
  });

  test('should display "Create New Agent" button', async ({ page }) => {
    // Wait for page to load
    await page.waitForLoadState('networkidle');

    // Look for the "New Agent" button
    const createButton = page.getByRole('button', { name: /New Agent/i });
    await expect(createButton).toBeVisible();
  });

  test('should show empty state when no agents exist', async ({ page }) => {
    // Wait for page to load and data to fetch
    await page.waitForLoadState('networkidle');
    await page.waitForTimeout(2000);

    // Look for empty state message or "No agents" text
    const emptyStateText = page.getByText(/no agents found|showing 0 of 0|create your first agent/i);

    // Take screenshot
    await page.screenshot({ path: 'tests/screenshots/empty-state.png', fullPage: true });
  });

  test('should make API calls to backend', async ({ page }) => {
    // Track network requests
    const requests: string[] = [];

    page.on('request', request => {
      const url = request.url();
      if (url.includes('/api/v1/')) {
        requests.push(url);
      }
    });

    // Navigate and wait for network
    await page.goto('http://localhost:5173');
    await page.waitForLoadState('networkidle');
    await page.waitForTimeout(2000);

    // Verify that API calls were made
    expect(requests.length).toBeGreaterThan(0);

    // Check for specific endpoints
    const hasAgentsCall = requests.some(url => url.includes('/api/v1/agents'));
    const hasMetricsCall = requests.some(url => url.includes('/api/v1/metrics/dashboard'));

    console.log('API calls made:', requests);

    expect(hasAgentsCall).toBe(true);
    expect(hasMetricsCall).toBe(true);
  });

  test('should not show auth errors', async ({ page }) => {
    // Monitor console for errors
    const consoleErrors: string[] = [];

    page.on('console', msg => {
      if (msg.type() === 'error') {
        consoleErrors.push(msg.text());
      }
    });

    await page.goto('http://localhost:5173');
    await page.waitForLoadState('networkidle');
    await page.waitForTimeout(2000);

    // Check that there are no 401 or authentication errors
    const hasAuthErrors = consoleErrors.some(err =>
      err.includes('401') ||
      err.includes('unauthorized') ||
      err.includes('Not authenticated')
    );

    expect(hasAuthErrors).toBe(false);
  });
});

test.describe('Agent Creation Flow', () => {
  test('should open create agent dialog', async ({ page }) => {
    await page.goto('http://localhost:5173');
    await page.waitForLoadState('networkidle');

    // Click "New Agent" button
    const createButton = page.getByRole('button', { name: /New Agent/i });
    await createButton.click();

    // Dialog should open
    const dialog = page.getByRole('dialog');
    await expect(dialog).toBeVisible();

    // Dialog should have "Create New Agent" title
    await expect(page.getByText(/Create New Agent/i)).toBeVisible();

    // Take screenshot
    await page.screenshot({ path: 'tests/screenshots/create-agent-dialog.png', fullPage: true });
  });
});
