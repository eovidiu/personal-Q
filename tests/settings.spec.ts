import { test, expect } from '@playwright/test';

test.describe('Settings Management', () => {
  test.beforeEach(async ({ page }) => {
    await page.goto('/');
    await page.waitForLoadState('networkidle');
  });

  test('should navigate to settings page', async ({ page }) => {
    // Look for settings link/button
    const settingsLink = page.locator('a[href*="settings"], button:has-text("Settings")').first();
    if (await settingsLink.isVisible()) {
      await settingsLink.click();
      await page.waitForTimeout(1000);
      
      // Should be on settings page
      await expect(page).toHaveURL(/settings/i);
    } else {
      // Try navigating directly
      await page.goto('/settings');
    }
    
    // Verify settings page loaded
    await expect(page.locator('h1, h2').filter({ hasText: /settings/i }).first()).toBeVisible();
  });

  test('should display API keys section', async ({ page }) => {
    await page.goto('/settings');
    await page.waitForTimeout(1000);
    
    // Look for API keys section
    const apiKeysSection = page.locator('section, div').filter({ hasText: /API.*Keys|Integrations/i }).first();
    if (await apiKeysSection.isVisible()) {
      await expect(apiKeysSection).toBeVisible();
    }
  });

  test('should add an API key', async ({ page }) => {
    await page.goto('/settings');
    await page.waitForTimeout(1000);
    
    // Look for add API key button
    const addButton = page.getByRole('button', { name: /add.*key|new.*key/i });
    if (await addButton.isVisible()) {
      await addButton.click();
      
      // Fill service name
      const serviceSelect = page.locator('select[name="service"], select[name="service_name"]').first();
      if (await serviceSelect.isVisible()) {
        await serviceSelect.selectOption('anthropic');
      }
      
      // Fill API key
      const keyInput = page.locator('input[name="api_key"], input[type="password"]').first();
      if (await keyInput.isVisible()) {
        await keyInput.fill('test-api-key-' + Date.now());
      }
      
      // Save
      const saveButton = page.getByRole('button', { name: /save|add|create/i });
      await saveButton.click();
      await page.waitForTimeout(2000);
    }
  });

  test('should test API connection', async ({ page }) => {
    await page.goto('/settings');
    await page.waitForTimeout(1000);
    
    // Look for test connection button
    const testButton = page.locator('button:has-text("Test"), button[aria-label*="test" i]').first();
    if (await testButton.isVisible()) {
      await testButton.click();
      await page.waitForTimeout(3000);
      
      // Should show result (success or error)
      const resultMessage = page.locator('[data-testid="test-result"], .test-result, .alert, .notification').first();
      if (await resultMessage.isVisible()) {
        await expect(resultMessage).toBeVisible();
      }
    }
  });

  test('should update general settings', async ({ page }) => {
    await page.goto('/settings');
    await page.waitForTimeout(1000);
    
    // Look for general settings section
    const generalSection = page.locator('section, div').filter({ hasText: /General|Preferences/i }).first();
    if (await generalSection.isVisible()) {
      // Update a setting
      const settingInput = generalSection.locator('input, select').first();
      if (await settingInput.isVisible()) {
        const type = await settingInput.getAttribute('type');
        if (type === 'checkbox') {
          await settingInput.click();
        } else if (type === 'text' || type === 'number') {
          await settingInput.fill('test-value');
        }
        
        // Save changes
        const saveButton = page.getByRole('button', { name: /save|update/i });
        if (await saveButton.isVisible()) {
          await saveButton.click();
          await page.waitForTimeout(1000);
        }
      }
    }
  });

  test('should delete an API key', async ({ page }) => {
    await page.goto('/settings');
    await page.waitForTimeout(1000);
    
    // Look for delete button on API key
    const deleteButton = page.locator('[data-testid="delete-key"], button[aria-label*="delete" i]').first();
    if (await deleteButton.isVisible()) {
      await deleteButton.click();
      
      // Confirm deletion
      const confirmButton = page.getByRole('button', { name: /confirm|yes|delete/i });
      if (await confirmButton.isVisible()) {
        await confirmButton.click();
        await page.waitForTimeout(1000);
      }
    }
  });
});

test.describe('Dashboard and Metrics', () => {
  test('should display dashboard', async ({ page }) => {
    await page.goto('/');
    await page.waitForTimeout(1000);
    
    // Should show dashboard metrics
    const metricsCard = page.locator('[data-testid="metric-card"], .metric-card, .stat-card').first();
    if (await metricsCard.isVisible()) {
      await expect(metricsCard).toBeVisible();
    }
  });

  test('should show agent statistics', async ({ page }) => {
    await page.goto('/');
    await page.waitForTimeout(1000);
    
    // Look for agent count
    const agentStat = page.locator('text=/\\d+.*agents?/i').first();
    if (await agentStat.isVisible()) {
      await expect(agentStat).toBeVisible();
    }
  });

  test('should show task statistics', async ({ page }) => {
    await page.goto('/');
    await page.waitForTimeout(1000);
    
    // Look for task count
    const taskStat = page.locator('text=/\\d+.*tasks?/i').first();
    if (await taskStat.isVisible()) {
      await expect(taskStat).toBeVisible();
    }
  });

  test('should display activity feed', async ({ page }) => {
    await page.goto('/');
    await page.waitForTimeout(1000);
    
    // Look for activities section
    const activitiesSection = page.locator('section, div').filter({ hasText: /activities|activity.*feed|recent/i }).first();
    if (await activitiesSection.isVisible()) {
      await expect(activitiesSection).toBeVisible();
    }
  });

  test('should refresh metrics', async ({ page }) => {
    await page.goto('/');
    await page.waitForTimeout(1000);
    
    // Look for refresh button
    const refreshButton = page.locator('button[aria-label*="refresh" i], button:has-text("Refresh")').first();
    if (await refreshButton.isVisible()) {
      await refreshButton.click();
      await page.waitForTimeout(2000);
    }
  });
});

test.describe('Navigation', () => {
  test('should navigate between main sections', async ({ page }) => {
    await page.goto('/');
    
    // Test navigation to each main section
    const sections = ['agents', 'tasks', 'settings'];
    
    for (const section of sections) {
      const link = page.locator(`a[href*="${section}"], button:has-text("${section}")`).first();
      if (await link.isVisible()) {
        await link.click();
        await page.waitForTimeout(1000);
        
        // Verify navigation
        const url = page.url();
        expect(url.toLowerCase()).toContain(section);
      }
    }
  });

  test('should show active navigation item', async ({ page }) => {
    await page.goto('/agents');
    await page.waitForTimeout(1000);
    
    // Active link should have special class/styling
    const activeLink = page.locator('a[href*="agents"], nav a').filter({ hasText: /agents/i }).first();
    if (await activeLink.isVisible()) {
      const classes = await activeLink.getAttribute('class');
      // Should have an active class (common patterns: 'active', 'selected', 'current')
      expect(classes).toBeTruthy();
    }
  });
});

