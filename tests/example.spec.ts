import { test, expect } from '@playwright/test';

test('has title', async ({ page }) => {
  await page.goto('/');

  // Expect a title "to contain" a substring.
  await expect(page).toHaveTitle(/Personal/);
});

test('homepage loads', async ({ page }) => {
  await page.goto('/');

  // Wait for the page to be visible
  await expect(page.locator('body')).toBeVisible();
});
