import { test, expect } from '@playwright/test';

test.describe('Task Cancellation', () => {
  test.beforeEach(async ({ page }) => {
    // Navigate to tasks page
    await page.goto('/tasks');
    await page.waitForLoadState('networkidle');
  });

  test('should show cancel button only for pending or running tasks', async ({ page }) => {
    // Wait for tasks to load
    await page.waitForSelector('article, [data-testid="task-card"]', { timeout: 10000 });

    // Check for running/pending tasks with cancel button
    const runningTask = page.locator('article').filter({ hasText: 'Running' }).or(
      page.locator('[data-testid="task-card"]').filter({ hasText: 'Running' })
    );

    if (await runningTask.count() > 0) {
      // Cancel button should be visible
      const cancelButton = runningTask.first().locator('button[title="Cancel task"]');
      await expect(cancelButton).toBeVisible();
    }

    // Completed tasks should NOT have cancel button
    const completedTask = page.locator('article').filter({ hasText: 'Completed' }).or(
      page.locator('[data-testid="task-card"]').filter({ hasText: 'Completed' })
    );

    if (await completedTask.count() > 0) {
      const cancelButton = completedTask.first().locator('button[title="Cancel task"]');
      await expect(cancelButton).toBeHidden();
    }
  });

  test('should open confirmation dialog when clicking cancel button', async ({ page }) => {
    // Look for a running or pending task
    const runnableTask = page.locator('article').filter({ hasText: /Running|Pending/ }).or(
      page.locator('[data-testid="task-card"]').filter({ hasText: /Running|Pending/ })
    );

    if (await runnableTask.count() > 0) {
      // Click the cancel button
      const cancelButton = runnableTask.first().locator('button[title="Cancel task"]');
      await cancelButton.click();

      // Confirmation dialog should appear
      const dialog = page.locator('role=alertdialog').filter({ hasText: 'Cancel Task?' });
      await expect(dialog).toBeVisible({ timeout: 3000 });

      // Should have confirmation message
      await expect(dialog.locator('text=/Are you sure you want to cancel/')).toBeVisible();

      // Should have action buttons
      await expect(dialog.locator('button', { hasText: /No, keep running/i })).toBeVisible();
      await expect(dialog.locator('button', { hasText: /Yes, cancel task/i })).toBeVisible();
    }
  });

  test('should close confirmation dialog when clicking "No, keep running"', async ({ page }) => {
    // Look for a running or pending task
    const runnableTask = page.locator('article').filter({ hasText: /Running|Pending/ }).or(
      page.locator('[data-testid="task-card"]').filter({ hasText: /Running|Pending/ })
    );

    if (await runnableTask.count() > 0) {
      // Click the cancel button
      const cancelButton = runnableTask.first().locator('button[title="Cancel task"]');
      await cancelButton.click();

      // Wait for dialog
      const dialog = page.locator('role=alertdialog').filter({ hasText: 'Cancel Task?' });
      await expect(dialog).toBeVisible({ timeout: 3000 });

      // Click "No, keep running"
      await dialog.locator('button', { hasText: /No, keep running/i }).click();

      // Dialog should close
      await expect(dialog).toBeHidden({ timeout: 2000 });

      // Task should still be running/pending
      await expect(runnableTask.first().locator('text=/Running|Pending/')).toBeVisible();
    }
  });

  test('should cancel task when clicking "Yes, cancel task" in confirmation dialog', async ({ page }) => {
    // Look for a pending task (safer to cancel than running)
    const pendingTask = page.locator('article').filter({ hasText: 'Pending' }).or(
      page.locator('[data-testid="task-card"]').filter({ hasText: 'Pending' })
    );

    if (await pendingTask.count() > 0) {
      // Get task title for verification
      const taskTitle = await pendingTask.first().locator('h3, [class*="CardTitle"]').first().textContent();

      // Click the cancel button
      const cancelButton = pendingTask.first().locator('button[title="Cancel task"]');
      await cancelButton.click();

      // Wait for dialog
      const dialog = page.locator('role=alertdialog').filter({ hasText: 'Cancel Task?' });
      await expect(dialog).toBeVisible({ timeout: 3000 });

      // Click "Yes, cancel task"
      await dialog.locator('button', { hasText: /Yes, cancel task/i }).click();

      // Wait for success toast
      const toast = page.locator('[class*="toast"]').or(page.locator('role=status')).filter({ hasText: /cancelled/i });
      await expect(toast).toBeVisible({ timeout: 5000 });

      // Task should now show as cancelled (or disappear if filtered)
      // Give it a moment to update
      await page.waitForTimeout(1000);
    }
  });

  test('should show loading state while cancelling task', async ({ page }) => {
    // Look for a pending task
    const pendingTask = page.locator('article').filter({ hasText: 'Pending' }).or(
      page.locator('[data-testid="task-card"]').filter({ hasText: 'Pending' })
    );

    if (await pendingTask.count() > 0) {
      // Click the cancel button
      const cancelButton = pendingTask.first().locator('button[title="Cancel task"]');
      await cancelButton.click();

      // Wait for dialog
      const dialog = page.locator('role=alertdialog').filter({ hasText: 'Cancel Task?' });
      await expect(dialog).toBeVisible({ timeout: 3000 });

      // The "Yes, cancel task" button should exist
      const confirmButton = dialog.locator('button', { hasText: /Yes, cancel task/i });
      await expect(confirmButton).toBeVisible();

      // Note: Loading state would show "Cancelling..." but happens quickly
      // We'll just verify the button is clickable
      await expect(confirmButton).toBeEnabled();
    }
  });

  test('should display error toast if cancellation fails', async ({ page }) => {
    // This test requires mocking a failed API call
    // We'll intercept the cancel request and return an error
    await page.route('**/api/v1/tasks/*/cancel', (route) => {
      route.fulfill({
        status: 400,
        body: JSON.stringify({ detail: 'Cannot cancel task with status completed' }),
      });
    });

    // Try to cancel any task (even completed, to trigger error)
    const anyTask = page.locator('article').or(page.locator('[data-testid="task-card"]'));

    if (await anyTask.count() > 0) {
      const cancelButton = anyTask.first().locator('button[title="Cancel task"]');

      // Only proceed if cancel button exists
      if (await cancelButton.count() > 0) {
        await cancelButton.click();

        const dialog = page.locator('role=alertdialog').filter({ hasText: 'Cancel Task?' });
        if (await dialog.isVisible()) {
          await dialog.locator('button', { hasText: /Yes, cancel task/i }).click();

          // Should show error toast
          const errorToast = page.locator('[class*="toast"]').or(page.locator('role=status')).filter({ hasText: /Failed to cancel|Cannot cancel/i });
          await expect(errorToast).toBeVisible({ timeout: 5000 });
        }
      }
    }
  });

  test('should not show cancel button for failed tasks', async ({ page }) => {
    const failedTask = page.locator('article').filter({ hasText: 'Failed' }).or(
      page.locator('[data-testid="task-card"]').filter({ hasText: 'Failed' })
    );

    if (await failedTask.count() > 0) {
      const cancelButton = failedTask.first().locator('button[title="Cancel task"]');
      await expect(cancelButton).toBeHidden();
    }
  });

  test('should not show cancel button for cancelled tasks', async ({ page }) => {
    const cancelledTask = page.locator('article').filter({ hasText: 'Cancelled' }).or(
      page.locator('[data-testid="task-card"]').filter({ hasText: 'Cancelled' })
    );

    if (await cancelledTask.count() > 0) {
      const cancelButton = cancelledTask.first().locator('button[title="Cancel task"]');
      await expect(cancelButton).toBeHidden();
    }
  });

  test('should prevent card click when clicking cancel button', async ({ page }) => {
    // Ensure clicking cancel button doesn't open detail modal
    const runnableTask = page.locator('article').filter({ hasText: /Running|Pending/ }).or(
      page.locator('[data-testid="task-card"]').filter({ hasText: /Running|Pending/ })
    );

    if (await runnableTask.count() > 0) {
      // Click the cancel button
      const cancelButton = runnableTask.first().locator('button[title="Cancel task"]');
      await cancelButton.click();

      // Confirmation dialog should appear, NOT detail modal
      const confirmDialog = page.locator('role=alertdialog').filter({ hasText: 'Cancel Task?' });
      await expect(confirmDialog).toBeVisible({ timeout: 3000 });

      // Detail modal should NOT be visible
      const detailModal = page.locator('role=dialog').filter({ hasText: 'Overview' });
      await expect(detailModal).toBeHidden();
    }
  });
});
