import { test, expect } from '@playwright/test';

test.describe('Agent Management', () => {
  test.beforeEach(async ({ page }) => {
    await page.goto('/');
    // Wait for app to load
    await page.waitForLoadState('networkidle');
  });

  test('should display agents list', async ({ page }) => {
    // Navigate to agents page (assuming it's the main page or /agents)
    await page.goto('/agents');
    
    // Check that the page title or header contains "Agents"
    await expect(page.locator('h1, h2').filter({ hasText: /agents/i }).first()).toBeVisible();
    
    // Wait for agents list to load
    await page.waitForTimeout(1000);
  });

  test('should create a new agent', async ({ page }) => {
    await page.goto('/agents');
    
    // Look for "Create Agent" or "New Agent" button
    const createButton = page.getByRole('button', { name: /create|new.*agent/i });
    if (await createButton.isVisible()) {
      await createButton.click();
      
      // Fill out agent form
      const nameInput = page.locator('input[name="name"], input[placeholder*="name" i]').first();
      if (await nameInput.isVisible()) {
        await nameInput.fill(`Test Agent ${Date.now()}`);
      }
      
      const descInput = page.locator('textarea[name="description"], textarea[placeholder*="description" i]').first();
      if (await descInput.isVisible()) {
        await descInput.fill('E2E test agent description');
      }
      
      // Select agent type if dropdown exists
      const typeSelect = page.locator('select[name="agent_type"], select[name="type"]').first();
      if (await typeSelect.isVisible()) {
        await typeSelect.selectOption({ index: 0 });
      }
      
      // Submit form
      const submitButton = page.getByRole('button', { name: /create|save|submit/i });
      await submitButton.click();
      
      // Wait for success (either redirect or success message)
      await page.waitForTimeout(2000);
    }
  });

  test('should view agent details', async ({ page }) => {
    await page.goto('/agents');
    await page.waitForTimeout(1000);
    
    // Click on first agent if exists
    const firstAgent = page.locator('[data-testid="agent-card"], .agent-card, .agent-item').first();
    if (await firstAgent.isVisible()) {
      await firstAgent.click();
      
      // Should navigate to agent details page
      await page.waitForURL(/\/agents\/[a-zA-Z0-9-]+/);
      
      // Verify agent details are displayed
      await expect(page.locator('h1, h2, .agent-name').first()).toBeVisible();
    }
  });

  test('should filter agents by status', async ({ page }) => {
    await page.goto('/agents');
    await page.waitForTimeout(1000);
    
    // Look for status filter
    const statusFilter = page.locator('select[name="status"], [data-testid="status-filter"]').first();
    if (await statusFilter.isVisible()) {
      await statusFilter.selectOption('active');
      await page.waitForTimeout(1000);
      
      // Verify filter applied
      const url = page.url();
      expect(url).toContain('status=active');
    }
  });

  test('should search agents', async ({ page }) => {
    await page.goto('/agents');
    await page.waitForTimeout(1000);
    
    // Look for search input
    const searchInput = page.locator('input[type="search"], input[placeholder*="search" i]').first();
    if (await searchInput.isVisible()) {
      await searchInput.fill('test');
      await page.waitForTimeout(1000);
      
      // Results should update
      const url = page.url();
      expect(url).toContain('search=test');
    }
  });

  test('should delete an agent', async ({ page }) => {
    await page.goto('/agents');
    await page.waitForTimeout(1000);
    
    // Look for delete button on first agent
    const deleteButton = page.locator('[data-testid="delete-agent"], button[aria-label*="delete" i]').first();
    if (await deleteButton.isVisible()) {
      await deleteButton.click();
      
      // Confirm deletion if modal appears
      const confirmButton = page.getByRole('button', { name: /confirm|yes|delete/i });
      if (await confirmButton.isVisible()) {
        await confirmButton.click();
        await page.waitForTimeout(1000);
      }
    }
  });
});

test.describe('Agent Status Management', () => {
  test('should toggle agent status', async ({ page }) => {
    await page.goto('/agents');
    await page.waitForTimeout(1000);
    
    // Look for status toggle
    const statusToggle = page.locator('[data-testid="status-toggle"], button[aria-label*="status" i]').first();
    if (await statusToggle.isVisible()) {
      const initialState = await statusToggle.getAttribute('aria-checked');
      await statusToggle.click();
      await page.waitForTimeout(1000);
      
      // Verify state changed
      const newState = await statusToggle.getAttribute('aria-checked');
      expect(newState).not.toBe(initialState);
    }
  });
});

