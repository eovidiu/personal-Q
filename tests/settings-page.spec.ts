/**
 * Playwright tests for Settings Page
 * Tests API key management functionality
 */

import { test, expect } from '@playwright/test';

test.describe('Settings Page', () => {
  test.beforeEach(async ({ page }) => {
    // Navigate to the settings page
    await page.goto('http://localhost:5173/settings');
  });

  test('should load the settings page without errors', async ({ page }) => {
    // Wait for the page to load
    await page.waitForLoadState('networkidle');

    // Check that the page heading is visible
    await expect(page.getByRole('heading', { name: /Settings/i })).toBeVisible();

    // Check for subtitle
    await expect(page.getByText(/Manage API keys for external services/i)).toBeVisible();
  });

  test('should display empty state when no API keys exist', async ({ page }) => {
    // Wait for page to load and data to fetch
    await page.waitForLoadState('networkidle');
    await page.waitForTimeout(2000);

    // Look for empty state message
    const emptyState = page.getByText(/No API Keys Configured/i);
    const hasEmptyState = await emptyState.isVisible().catch(() => false);

    if (hasEmptyState) {
      // Check for "Configure Your First API Key" button
      await expect(page.getByRole('button', { name: /Configure Your First API Key/i })).toBeVisible();
    }

    // Take screenshot
    await page.screenshot({ path: 'tests/screenshots/settings-empty-state.png', fullPage: true });
  });

  test('should have "Add API Key" button visible', async ({ page }) => {
    // Wait for page to load
    await page.waitForLoadState('networkidle');

    // Check for "Add API Key" button in header
    const addButton = page.getByRole('button', { name: /Add API Key/i }).first();
    await expect(addButton).toBeVisible();
  });

  test('should open dialog when "Add API Key" button is clicked', async ({ page }) => {
    // Wait for page to load
    await page.waitForLoadState('networkidle');
    await page.waitForTimeout(1000);

    // Click "Add API Key" button
    const addButton = page.getByRole('button', { name: /Add API Key/i }).first();
    await addButton.click();

    // Dialog should open
    await expect(page.getByRole('dialog')).toBeVisible();

    // Dialog should have title
    await expect(page.getByText(/Add API Key/i)).toBeVisible();

    // Service selector should be visible
    await expect(page.getByText(/Select a service/i)).toBeVisible();

    // Take screenshot
    await page.screenshot({ path: 'tests/screenshots/settings-add-dialog.png', fullPage: true });
  });

  test('should show service options in select dropdown', async ({ page }) => {
    // Wait for page to load
    await page.waitForLoadState('networkidle');
    await page.waitForTimeout(1000);

    // Click "Add API Key" button
    const addButton = page.getByRole('button', { name: /Add API Key/i }).first();
    await addButton.click();

    // Wait for dialog
    await page.waitForTimeout(500);

    // Click service select trigger
    const selectTrigger = page.getByRole('combobox');
    await selectTrigger.click();

    // Check for service options
    await expect(page.getByRole('option', { name: /Anthropic.*Claude API/i })).toBeVisible();
    await expect(page.getByRole('option', { name: /Slack/i })).toBeVisible();
    await expect(page.getByRole('option', { name: /Outlook/i })).toBeVisible();
    await expect(page.getByRole('option', { name: /OneDrive/i })).toBeVisible();
    await expect(page.getByRole('option', { name: /Obsidian/i })).toBeVisible();
  });

  test('should show API key field when Anthropic is selected', async ({ page }) => {
    // Wait for page to load
    await page.waitForLoadState('networkidle');
    await page.waitForTimeout(1000);

    // Click "Add API Key" button
    const addButton = page.getByRole('button', { name: /Add API Key/i }).first();
    await addButton.click();

    // Wait for dialog
    await page.waitForTimeout(500);

    // Click service select
    const selectTrigger = page.getByRole('combobox');
    await selectTrigger.click();

    // Select Anthropic
    await page.getByRole('option', { name: /Anthropic.*Claude API/i }).click();

    // Wait for fields to appear
    await page.waitForTimeout(500);

    // API Key field should be visible
    await expect(page.getByLabel(/API Key/i)).toBeVisible();

    // Password toggle button should be visible
    await expect(page.getByRole('button').filter({ has: page.locator('svg') }).first()).toBeVisible();

    // Take screenshot
    await page.screenshot({ path: 'tests/screenshots/settings-anthropic-form.png', fullPage: true });
  });

  test('should show OAuth fields when Slack is selected', async ({ page }) => {
    // Wait for page to load
    await page.waitForLoadState('networkidle');
    await page.waitForTimeout(1000);

    // Click "Add API Key" button
    const addButton = page.getByRole('button', { name: /Add API Key/i }).first();
    await addButton.click();

    // Wait for dialog
    await page.waitForTimeout(500);

    // Click service select
    const selectTrigger = page.getByRole('combobox');
    await selectTrigger.click();

    // Select Slack
    await page.getByRole('option', { name: /^Slack$/i }).click();

    // Wait for fields to appear
    await page.waitForTimeout(500);

    // Access Token field should be visible
    await expect(page.getByLabel(/Access Token/i)).toBeVisible();

    // Refresh Token field should be visible
    await expect(page.getByLabel(/Refresh Token/i)).toBeVisible();
  });

  test('should be able to navigate to settings from dashboard', async ({ page }) => {
    // Start at dashboard
    await page.goto('http://localhost:5173');
    await page.waitForLoadState('networkidle');

    // Click settings button in header
    const settingsButton = page.getByRole('link').filter({ has: page.locator('[title="Settings"]') });
    await settingsButton.click();

    // Should be on settings page
    await expect(page).toHaveURL(/\/settings/);
    await expect(page.getByRole('heading', { name: /Settings/i })).toBeVisible();
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

    // Navigate to settings page
    await page.goto('http://localhost:5173/settings');
    await page.waitForLoadState('networkidle');
    await page.waitForTimeout(2000);

    // Verify that API calls were made
    expect(requests.length).toBeGreaterThan(0);

    // Check for settings API endpoint call
    const hasSettingsCall = requests.some(url => url.includes('/api/v1/settings/api-keys'));

    console.log('API calls made:', requests);

    expect(hasSettingsCall).toBe(true);
  });

  test('should handle form validation', async ({ page }) => {
    // Wait for page to load
    await page.waitForLoadState('networkidle');
    await page.waitForTimeout(1000);

    // Click "Add API Key" button
    const addButton = page.getByRole('button', { name: /Add API Key/i }).first();
    await addButton.click();

    // Wait for dialog
    await page.waitForTimeout(500);

    // Try to submit without selecting service
    const submitButton = page.getByRole('button', { name: /Add API Key/i }).last();

    // Submit button should be disabled when no service selected
    await expect(submitButton).toBeDisabled();
  });

  test('should close dialog when cancel is clicked', async ({ page }) => {
    // Wait for page to load
    await page.waitForLoadState('networkidle');
    await page.waitForTimeout(1000);

    // Click "Add API Key" button
    const addButton = page.getByRole('button', { name: /Add API Key/i }).first();
    await addButton.click();

    // Wait for dialog
    await page.waitForTimeout(500);

    // Dialog should be visible
    await expect(page.getByRole('dialog')).toBeVisible();

    // Click cancel
    const cancelButton = page.getByRole('button', { name: /Cancel/i });
    await cancelButton.click();

    // Wait for dialog to close
    await page.waitForTimeout(500);

    // Dialog should be closed
    await expect(page.getByRole('dialog')).not.toBeVisible();
  });
});
