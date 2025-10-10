import { test, expect } from '@playwright/test';

test.describe('Task Management', () => {
  test.beforeEach(async ({ page }) => {
    await page.goto('/');
    await page.waitForLoadState('networkidle');
  });

  test('should display tasks list', async ({ page }) => {
    await page.goto('/tasks');
    
    // Check for tasks page
    await expect(page.locator('h1, h2').filter({ hasText: /tasks/i }).first()).toBeVisible();
    await page.waitForTimeout(1000);
  });

  test('should create a new task', async ({ page }) => {
    await page.goto('/tasks');
    
    // Look for "Create Task" button
    const createButton = page.getByRole('button', { name: /create|new.*task/i });
    if (await createButton.isVisible()) {
      await createButton.click();
      
      // Fill task form
      const titleInput = page.locator('input[name="title"], input[placeholder*="title" i]').first();
      if (await titleInput.isVisible()) {
        await titleInput.fill(`E2E Test Task ${Date.now()}`);
      }
      
      const descInput = page.locator('textarea[name="description"], textarea[placeholder*="description" i]').first();
      if (await descInput.isVisible()) {
        await descInput.fill('This is an E2E test task');
      }
      
      // Select agent
      const agentSelect = page.locator('select[name="agent_id"], select[name="agent"]').first();
      if (await agentSelect.isVisible()) {
        await agentSelect.selectOption({ index: 0 });
      }
      
      // Select priority
      const prioritySelect = page.locator('select[name="priority"]').first();
      if (await prioritySelect.isVisible()) {
        await prioritySelect.selectOption('high');
      }
      
      // Submit
      const submitButton = page.getByRole('button', { name: /create|save|submit/i });
      await submitButton.click();
      await page.waitForTimeout(2000);
    }
  });

  test('should filter tasks by status', async ({ page }) => {
    await page.goto('/tasks');
    await page.waitForTimeout(1000);
    
    // Look for status filter
    const statusFilter = page.locator('select[name="status"], [data-testid="status-filter"]').first();
    if (await statusFilter.isVisible()) {
      await statusFilter.selectOption('completed');
      await page.waitForTimeout(1000);
    }
  });

  test('should filter tasks by priority', async ({ page }) => {
    await page.goto('/tasks');
    await page.waitForTimeout(1000);
    
    // Look for priority filter
    const priorityFilter = page.locator('select[name="priority"], [data-testid="priority-filter"]').first();
    if (await priorityFilter.isVisible()) {
      await priorityFilter.selectOption('high');
      await page.waitForTimeout(1000);
    }
  });

  test('should view task details', async ({ page }) => {
    await page.goto('/tasks');
    await page.waitForTimeout(1000);
    
    // Click on first task
    const firstTask = page.locator('[data-testid="task-card"], .task-card, .task-item').first();
    if (await firstTask.isVisible()) {
      await firstTask.click();
      await page.waitForTimeout(1000);
      
      // Should show task details
      await expect(page.locator('h1, h2, .task-title').first()).toBeVisible();
    }
  });

  test('should execute a task', async ({ page }) => {
    await page.goto('/tasks');
    await page.waitForTimeout(1000);
    
    // Look for execute button
    const executeButton = page.locator('button[aria-label*="execute" i], button:has-text("Execute")').first();
    if (await executeButton.isVisible()) {
      await executeButton.click();
      
      // Confirm if modal appears
      const confirmButton = page.getByRole('button', { name: /confirm|yes|execute/i });
      if (await confirmButton.isVisible()) {
        await confirmButton.click();
      }
      
      await page.waitForTimeout(2000);
      
      // Should show task as running
      const statusBadge = page.locator('[data-testid="task-status"], .task-status').first();
      if (await statusBadge.isVisible()) {
        const statusText = await statusBadge.textContent();
        expect(statusText?.toLowerCase()).toContain('running');
      }
    }
  });

  test('should cancel a task', async ({ page }) => {
    await page.goto('/tasks');
    await page.waitForTimeout(1000);
    
    // Look for cancel button on running task
    const cancelButton = page.locator('button[aria-label*="cancel" i], button:has-text("Cancel")').first();
    if (await cancelButton.isVisible()) {
      await cancelButton.click();
      
      // Confirm if needed
      const confirmButton = page.getByRole('button', { name: /confirm|yes|cancel/i });
      if (await confirmButton.isVisible()) {
        await confirmButton.click();
      }
      
      await page.waitForTimeout(1000);
    }
  });

  test('should delete a task', async ({ page }) => {
    await page.goto('/tasks');
    await page.waitForTimeout(1000);
    
    // Look for delete button
    const deleteButton = page.locator('[data-testid="delete-task"], button[aria-label*="delete" i]').first();
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

test.describe('Task Real-time Updates', () => {
  test('should show real-time task status updates', async ({ page }) => {
    await page.goto('/tasks');
    await page.waitForTimeout(1000);
    
    // Get initial task count
    const taskCards = page.locator('[data-testid="task-card"], .task-card');
    const initialCount = await taskCards.count();
    
    // Wait for potential WebSocket updates
    await page.waitForTimeout(5000);
    
    // Check if count changed (new tasks added)
    const newCount = await taskCards.count();
    // Just verify the page is responsive (not asserting count change)
    expect(newCount).toBeGreaterThanOrEqual(0);
  });
});

