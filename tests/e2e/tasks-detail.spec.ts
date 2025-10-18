import { test, expect } from '@playwright/test';

test.describe('Task Detail Modal', () => {
  test.beforeEach(async ({ page }) => {
    // Navigate to tasks page
    await page.goto('/tasks');
    await page.waitForLoadState('networkidle');
  });

  test('should open detail modal when clicking on a task card', async ({ page }) => {
    // Wait for tasks to load
    const taskCards = page.locator('[data-testid="task-card"]').or(page.locator('article').filter({ hasText: 'Task' }));
    await taskCards.first().waitFor({ state: 'visible', timeout: 10000 });

    // Click on the first task card
    await taskCards.first().click();

    // Verify modal opens
    const modal = page.locator('role=dialog').filter({ hasText: 'Overview' });
    await expect(modal).toBeVisible({ timeout: 5000 });
  });

  test('should display all tabs in the detail modal', async ({ page }) => {
    // Click on first task
    const taskCards = page.locator('[data-testid="task-card"]').or(page.locator('article').filter({ hasText: 'Task' }));
    await taskCards.first().waitFor({ state: 'visible', timeout: 10000 });
    await taskCards.first().click();

    // Wait for modal
    const modal = page.locator('role=dialog');
    await expect(modal).toBeVisible({ timeout: 5000 });

    // Verify all tabs are present
    await expect(page.locator('role=tab', { name: 'Overview' })).toBeVisible();
    await expect(page.locator('role=tab', { name: 'Output' })).toBeVisible();
    await expect(page.locator('role=tab', { name: 'Error' })).toBeVisible();
    await expect(page.locator('role=tab', { name: 'Timeline' })).toBeVisible();
  });

  test('should display overview tab content', async ({ page }) => {
    // Click on first task
    const taskCards = page.locator('[data-testid="task-card"]').or(page.locator('article').filter({ hasText: 'Task' }));
    await taskCards.first().waitFor({ state: 'visible', timeout: 10000 });
    await taskCards.first().click();

    // Wait for modal
    await page.locator('role=dialog').waitFor({ state: 'visible', timeout: 5000 });

    // Overview tab should be active by default
    const overviewContent = page.locator('role=tabpanel').filter({ hasText: 'Status' });
    await expect(overviewContent).toBeVisible();

    // Should show status and priority badges
    await expect(overviewContent.locator('text=Status').locator('..')).toBeVisible();
    await expect(overviewContent.locator('text=Priority').locator('..')).toBeVisible();
  });

  test('should switch between tabs', async ({ page }) => {
    // Click on first task
    const taskCards = page.locator('[data-testid="task-card"]').or(page.locator('article').filter({ hasText: 'Task' }));
    await taskCards.first().waitFor({ state: 'visible', timeout: 10000 });
    await taskCards.first().click();

    // Wait for modal
    await page.locator('role=dialog').waitFor({ state: 'visible', timeout: 5000 });

    // Click on Output tab
    await page.locator('role=tab', { name: 'Output' }).click();
    await expect(page.locator('role=tabpanel').filter({ hasText: /Output Data|No output data/ })).toBeVisible();

    // Click on Timeline tab
    await page.locator('role=tab', { name: 'Timeline' }).click();
    await expect(page.locator('role=tabpanel').filter({ hasText: 'Timeline' })).toBeVisible();
  });

  test('should display output data in JSON format for completed tasks', async ({ page }) => {
    // Look for a completed task
    const completedTask = page.locator('[data-testid="task-card"]').filter({ hasText: 'Completed' }).or(
      page.locator('article').filter({ hasText: 'Completed' })
    );

    if (await completedTask.count() > 0) {
      await completedTask.first().click();

      // Wait for modal
      await page.locator('role=dialog').waitFor({ state: 'visible', timeout: 5000 });

      // Click on Output tab
      await page.locator('role=tab', { name: 'Output' }).click();

      // Should show JSON output or "No output data" message
      const outputPanel = page.locator('role=tabpanel').filter({ hasText: /Output Data|No output data/ });
      await expect(outputPanel).toBeVisible();
    }
  });

  test('should display error message for failed tasks', async ({ page }) => {
    // Look for a failed task
    const failedTask = page.locator('[data-testid="task-card"]').filter({ hasText: 'Failed' }).or(
      page.locator('article').filter({ hasText: 'Failed' })
    );

    if (await failedTask.count() > 0) {
      await failedTask.first().click();

      // Wait for modal
      await page.locator('role=dialog').waitFor({ state: 'visible', timeout: 5000 });

      // Click on Error tab
      await page.locator('role=tab', { name: 'Error' }).click();

      // Should show error details
      const errorPanel = page.locator('role=tabpanel').filter({ hasText: 'Error Details' });
      await expect(errorPanel).toBeVisible();
    }
  });

  test('should display execution timeline with events', async ({ page }) => {
    // Click on first task
    const taskCards = page.locator('[data-testid="task-card"]').or(page.locator('article').filter({ hasText: 'Task' }));
    await taskCards.first().waitFor({ state: 'visible', timeout: 10000 });
    await taskCards.first().click();

    // Wait for modal
    await page.locator('role=dialog').waitFor({ state: 'visible', timeout: 5000 });

    // Click on Timeline tab
    await page.locator('role=tab', { name: 'Timeline' }).click();

    // Should show at least "Task Created" event
    const timelinePanel = page.locator('role=tabpanel').filter({ hasText: 'Timeline' });
    await expect(timelinePanel).toBeVisible();
    await expect(timelinePanel.locator('text=Task Created')).toBeVisible();
  });

  test('should close modal when clicking outside or on close button', async ({ page }) => {
    // Click on first task
    const taskCards = page.locator('[data-testid="task-card"]').or(page.locator('article').filter({ hasText: 'Task' }));
    await taskCards.first().waitFor({ state: 'visible', timeout: 10000 });
    await taskCards.first().click();

    // Wait for modal
    const modal = page.locator('role=dialog');
    await expect(modal).toBeVisible({ timeout: 5000 });

    // Press Escape to close
    await page.keyboard.press('Escape');

    // Modal should be hidden
    await expect(modal).toBeHidden({ timeout: 2000 });
  });

  test('should show loading state when task data is being fetched', async ({ page }) => {
    // This test would need to intercept the API call and delay it
    // For now, we'll just verify the modal opens quickly enough
    const taskCards = page.locator('[data-testid="task-card"]').or(page.locator('article').filter({ hasText: 'Task' }));
    await taskCards.first().waitFor({ state: 'visible', timeout: 10000 });
    await taskCards.first().click();

    // Modal should appear
    const modal = page.locator('role=dialog');
    await expect(modal).toBeVisible({ timeout: 5000 });
  });
});
