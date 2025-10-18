import { test, expect } from '@playwright/test';

/**
 * AgentCard Component Tests
 *
 * Tests the AgentCard component with various edge cases to ensure
 * it handles missing or incomplete data gracefully.
 *
 * Created to prevent: "Cannot read properties of undefined" errors
 * after OAuth authentication when backend returns incomplete agent data.
 */

test.describe('AgentCard Component - Edge Cases', () => {

  test.beforeEach(async ({ page }) => {
    // Set up authentication
    const mockToken = btoa(JSON.stringify({
      header: { alg: 'HS256', typ: 'JWT' },
      payload: {
        sub: 'test@example.com',
        email: 'test@example.com',
        iat: Math.floor(Date.now() / 1000),
        exp: Math.floor(Date.now() / 1000) + (24 * 3600),
      },
    }));

    await page.goto('/');
    await page.evaluate((token) => {
      localStorage.setItem('personal_q_token', token);
    }, mockToken);

    // Mock auth endpoint
    await page.route('**/api/v1/auth/me', async (route) => {
      await route.fulfill({
        status: 200,
        contentType: 'application/json',
        body: JSON.stringify({
          email: 'test@example.com',
          authenticated: true,
        }),
      });
    });
  });

  test('should handle agent with missing tasksCompleted field', async ({ page }) => {
    // Mock agents endpoint with incomplete data
    await page.route('**/api/v1/agents', async (route) => {
      await route.fulfill({
        status: 200,
        contentType: 'application/json',
        body: JSON.stringify([
          {
            id: '1',
            name: 'Test Agent',
            description: 'Test description',
            type: 'conversational',
            status: 'active',
            model: 'GPT-4',
            // Missing: tasksCompleted, successRate, uptime, tags, lastActive
          },
        ]),
      });
    });

    await page.goto('/agents');
    await page.waitForLoadState('networkidle');

    // Should display agent with default values
    await expect(page.getByText('Test Agent')).toBeVisible();
    await expect(page.getByText('0')).toBeVisible(); // Default tasksCompleted
    await expect(page.getByText('0%')).toBeVisible(); // Default successRate/uptime
  });

  test('should handle agent with unknown type', async ({ page }) => {
    await page.route('**/api/v1/agents', async (route) => {
      await route.fulfill({
        status: 200,
        contentType: 'application/json',
        body: JSON.stringify([
          {
            id: '2',
            name: 'Unknown Type Agent',
            description: 'Has unknown agent type',
            type: 'unknown_type_not_in_config', // Unknown type
            status: 'active',
            model: 'Claude',
            tasksCompleted: 100,
            successRate: 95,
            uptime: 99,
            tags: ['test'],
            lastActive: '1 hour ago',
          },
        ]),
      });
    });

    await page.goto('/agents');
    await page.waitForLoadState('networkidle');

    // Should display agent with "General" fallback label
    await expect(page.getByText('Unknown Type Agent')).toBeVisible();
    await expect(page.getByText('General')).toBeVisible(); // Fallback type
  });

  test('should handle agent with null/undefined optional fields', async ({ page }) => {
    await page.route('**/api/v1/agents', async (route) => {
      await route.fulfill({
        status: 200,
        contentType: 'application/json',
        body: JSON.stringify([
          {
            id: '3',
            name: 'Null Fields Agent',
            description: 'Has null optional fields',
            type: 'analytical',
            status: 'inactive',
            model: 'GPT-3.5',
            tasksCompleted: null,
            successRate: null,
            uptime: null,
            tags: null,
            lastActive: null,
          },
        ]),
      });
    });

    await page.goto('/agents');
    await page.waitForLoadState('networkidle');

    // Should handle null values gracefully
    await expect(page.getByText('Null Fields Agent')).toBeVisible();
    await expect(page.getByText('Never')).toBeVisible(); // Default lastActive
  });

  test('should handle agent with empty tags array', async ({ page }) => {
    await page.route('**/api/v1/agents', async (route) => {
      await route.fulfill({
        status: 200,
        contentType: 'application/json',
        body: JSON.stringify([
          {
            id: '4',
            name: 'No Tags Agent',
            description: 'Has no tags',
            type: 'creative',
            status: 'training',
            model: 'GPT-4',
            tasksCompleted: 50,
            successRate: 88,
            uptime: 92,
            tags: [], // Empty array
            lastActive: '5 minutes ago',
          },
        ]),
      });
    });

    await page.goto('/agents');
    await page.waitForLoadState('networkidle');

    // Should render without errors
    await expect(page.getByText('No Tags Agent')).toBeVisible();
    await expect(page.getByText('50')).toBeVisible();
  });

  test('should handle agent with very large task numbers', async ({ page }) => {
    await page.route('**/api/v1/agents', async (route) => {
      await route.fulfill({
        status: 200,
        contentType: 'application/json',
        body: JSON.stringify([
          {
            id: '5',
            name: 'High Volume Agent',
            description: 'Handles many tasks',
            type: 'automation',
            status: 'active',
            model: 'GPT-4',
            tasksCompleted: 1234567890, // Large number
            successRate: 99.99,
            uptime: 100,
            tags: ['high-volume', 'production'],
            lastActive: 'Just now',
          },
        ]),
      });
    });

    await page.goto('/agents');
    await page.waitForLoadState('networkidle');

    // Should format large numbers with locale string
    await expect(page.getByText('High Volume Agent')).toBeVisible();
    // The exact format depends on locale, but should contain commas/separators
    const taskCount = await page.locator('text=/1,234,567,890|1\\.234\\.567\\.890/').count();
    expect(taskCount).toBeGreaterThan(0);
  });

  test('should handle multiple agents with mixed data completeness', async ({ page }) => {
    await page.route('**/api/v1/agents', async (route) => {
      await route.fulfill({
        status: 200,
        contentType: 'application/json',
        body: JSON.stringify([
          {
            id: '6',
            name: 'Complete Agent',
            description: 'Has all fields',
            type: 'conversational',
            status: 'active',
            model: 'GPT-4',
            tasksCompleted: 100,
            successRate: 95,
            uptime: 99,
            tags: ['complete'],
            lastActive: '1 min ago',
          },
          {
            id: '7',
            name: 'Incomplete Agent',
            description: 'Missing fields',
            type: 'analytical',
            status: 'error',
            model: 'Claude',
            // Missing optional fields
          },
        ]),
      });
    });

    await page.goto('/agents');
    await page.waitForLoadState('networkidle');

    // Both agents should render
    await expect(page.getByText('Complete Agent')).toBeVisible();
    await expect(page.getByText('Incomplete Agent')).toBeVisible();
  });

  test('should not crash when accessing agent detail with incomplete data', async ({ page }) => {
    await page.route('**/api/v1/agents/999', async (route) => {
      await route.fulfill({
        status: 200,
        contentType: 'application/json',
        body: JSON.stringify({
          id: '999',
          name: 'Minimal Agent',
          description: 'Minimal data',
          type: 'conversational',
          status: 'active',
          model: 'GPT-4',
          // Missing most optional fields
        }),
      });
    });

    await page.goto('/agent/999');

    // Should load without crashing
    await expect(page.getByText('Minimal Agent')).toBeVisible();
  });

  test('should handle agent status not in statusConfig', async ({ page }) => {
    await page.route('**/api/v1/agents', async (route) => {
      await route.fulfill({
        status: 200,
        contentType: 'application/json',
        body: JSON.stringify([
          {
            id: '8',
            name: 'Unknown Status Agent',
            description: 'Has unknown status',
            type: 'conversational',
            status: 'unknown_status', // Not in statusConfig
            model: 'GPT-4',
            tasksCompleted: 10,
            successRate: 80,
            uptime: 90,
            tags: ['test'],
            lastActive: 'Recently',
          },
        ]),
      });
    });

    await page.goto('/agents');

    // Should handle gracefully (may show as fallback or error status)
    await expect(page.getByText('Unknown Status Agent')).toBeVisible();
  });

  test('should display "View Details" button for all agents', async ({ page }) => {
    await page.route('**/api/v1/agents', async (route) => {
      await route.fulfill({
        status: 200,
        contentType: 'application/json',
        body: JSON.stringify([
          {
            id: '9',
            name: 'Test Agent',
            description: 'Test',
            type: 'conversational',
            status: 'active',
            model: 'GPT-4',
          },
        ]),
      });
    });

    await page.goto('/agents');
    await page.waitForLoadState('networkidle');

    // View Details button should be present
    const viewDetailsButton = page.getByRole('link', { name: /view details/i });
    await expect(viewDetailsButton).toBeVisible();

    // Should navigate to detail page when clicked
    await viewDetailsButton.click();
    await expect(page).toHaveURL(/\/agent\/9/);
  });
});
