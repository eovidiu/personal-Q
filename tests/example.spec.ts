import { test, expect } from '@playwright/test';

test.describe('Homepage and Basic Functionality', () => {
  test('has correct title', async ({ page }) => {
    await page.goto('/');
    
    // Expect title to contain "Personal"
    await expect(page).toHaveTitle(/Personal/);
  });

  test('homepage loads successfully', async ({ page }) => {
    await page.goto('/');
    
    // Wait for page to be fully loaded
    await page.waitForLoadState('networkidle');
    
    // Body should be visible
    await expect(page.locator('body')).toBeVisible();
  });

  test('main navigation is visible', async ({ page }) => {
    await page.goto('/');
    await page.waitForTimeout(1000);
    
    // Navigation should be present
    const nav = page.locator('nav, header').first();
    await expect(nav).toBeVisible();
  });

  test('responds to viewport changes', async ({ page }) => {
    await page.goto('/');
    
    // Test mobile viewport
    await page.setViewportSize({ width: 375, height: 667 });
    await page.waitForTimeout(500);
    await expect(page.locator('body')).toBeVisible();
    
    // Test desktop viewport
    await page.setViewportSize({ width: 1920, height: 1080 });
    await page.waitForTimeout(500);
    await expect(page.locator('body')).toBeVisible();
  });

  test('handles page reload', async ({ page }) => {
    await page.goto('/');
    await page.waitForTimeout(1000);
    
    // Reload page
    await page.reload();
    await page.waitForLoadState('networkidle');
    
    // Should still be functional
    await expect(page.locator('body')).toBeVisible();
  });
});
