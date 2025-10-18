import { test, expect } from './fixtures/auth';

/**
 * Integration test for Update Agent functionality
 *
 * Prerequisites:
 * - Backend must be running on http://localhost:8000
 * - Frontend must be running on http://localhost:5173
 * - Database must have test agents
 * - ALLOWED_EMAIL environment variable must be set
 *
 * This test verifies:
 * 1. Agent update dialog opens correctly
 * 2. Form fields are populated with current agent data
 * 3. Updates are saved with correct field name transformations (camelCase -> snake_case)
 * 4. Dialog closes after successful update
 * 5. Updated data appears on the page
 *
 * Authentication:
 * Uses test auth fixture to bypass Google OAuth for automated testing.
 */

test.describe('Agent Update Integration', () => {
  // No beforeEach needed - authenticatedPage fixture handles auth automatically

  test('should successfully update agent name and description', async ({ authenticatedPage: page }) => {
    // Navigate to agents page
    await page.goto('http://localhost:5173/agents');
    await page.waitForLoadState('networkidle');

    // Click on first agent card to go to detail page
    const firstAgentCard = page.locator('[data-testid="agent-card"]').first();
    await firstAgentCard.click();

    // Wait for agent detail page
    await page.waitForURL(/\/agent\/.*/, { timeout: 5000 });

    // Click Configure button to open edit dialog
    const configureButton = page.getByRole('button', { name: /configure/i });
    await expect(configureButton).toBeVisible({ timeout: 5000 });
    await configureButton.click();

    // Wait for dialog to appear
    const dialog = page.getByRole('dialog');
    await expect(dialog).toBeVisible({ timeout: 5000 });

    // Store original values
    const nameInput = page.getByLabel(/agent name/i);
    const descriptionInput = page.getByLabel(/description/i);

    const originalName = await nameInput.inputValue();
    const originalDescription = await descriptionInput.inputValue();

    // Update fields
    const timestamp = Date.now();
    const newName = `Updated Agent ${timestamp}`;
    const newDescription = `Updated description ${timestamp}`;

    await nameInput.fill('');
    await nameInput.fill(newName);
    await descriptionInput.fill('');
    await descriptionInput.fill(newDescription);

    // Intercept the PUT request to verify field names
    let updateRequestBody: any = null;
    page.on('request', request => {
      if (request.method() === 'PUT' && request.url().includes('/api/v1/agents/')) {
        updateRequestBody = request.postDataJSON();
      }
    });

    // Submit form
    const updateButton = page.getByRole('button', { name: /update agent/i });
    await updateButton.click();

    // Wait for dialog to close (indicating success)
    await expect(dialog).not.toBeVisible({ timeout: 10000 });

    // Verify the request body had correct field names
    if (updateRequestBody) {
      // Backend expects snake_case field names
      expect(updateRequestBody).toHaveProperty('agent_type'); // NOT 'type'
      expect(updateRequestBody).toHaveProperty('max_tokens'); // NOT 'maxTokens'
      expect(updateRequestBody).toHaveProperty('system_prompt'); // NOT 'systemPrompt'

      // Verify our changes
      expect(updateRequestBody.name).toBe(newName);
      expect(updateRequestBody.description).toBe(newDescription);
    }

    // Verify updated name appears on page
    await expect(page.locator('h1', { hasText: newName })).toBeVisible({ timeout: 5000 });

    // Cleanup: Restore original values
    await configureButton.click();
    await expect(dialog).toBeVisible();
    await nameInput.fill('');
    await nameInput.fill(originalName);
    await descriptionInput.fill('');
    await descriptionInput.fill(originalDescription);
    await updateButton.click();
    await expect(dialog).not.toBeVisible({ timeout: 10000 });
  });

  test('should update temperature slider', async ({ authenticatedPage: page }) => {
    // Navigate to agents page
    await page.goto('http://localhost:5173/agents');
    await page.waitForLoadState('networkidle');

    // Click on first agent
    await page.locator('[data-testid="agent-card"]').first().click();
    await page.waitForURL(/\/agent\/.*/, { timeout: 5000 });

    // Open edit dialog
    await page.getByRole('button', { name: /configure/i }).click();
    const dialog = page.getByRole('dialog');
    await expect(dialog).toBeVisible();

    // Find temperature slider
    const temperatureSlider = page.locator('input[type="range"]#temperature');
    await expect(temperatureSlider).toBeVisible();

    // Store original value
    const originalValue = await temperatureSlider.inputValue();

    // Set new temperature value
    await temperatureSlider.fill('0.9');

    // Submit
    await page.getByRole('button', { name: /update agent/i }).click();
    await expect(dialog).not.toBeVisible({ timeout: 10000 });

    // Reopen and verify temperature was updated
    await page.getByRole('button', { name: /configure/i }).click();
    await expect(dialog).toBeVisible();
    const updatedValue = await page.locator('input[type="range"]#temperature').inputValue();
    expect(parseFloat(updatedValue)).toBeCloseTo(0.9, 1);

    // Cleanup: Restore original
    await page.locator('input[type="range"]#temperature').fill(originalValue);
    await page.getByRole('button', { name: /update agent/i }).click();
    await expect(dialog).not.toBeVisible({ timeout: 10000 });
  });

  test('should update max tokens input', async ({ authenticatedPage: page }) => {
    // Navigate to agents page
    await page.goto('http://localhost:5173/agents');
    await page.waitForLoadState('networkidle');

    // Click on first agent
    await page.locator('[data-testid="agent-card"]').first().click();
    await page.waitForURL(/\/agent\/.*/, { timeout: 5000 });

    // Open edit dialog
    await page.getByRole('button', { name: /configure/i }).click();
    const dialog = page.getByRole('dialog');
    await expect(dialog).toBeVisible();

    // Find max tokens input
    const maxTokensInput = page.getByLabel(/max tokens/i);
    await expect(maxTokensInput).toBeVisible();

    // Store original value
    const originalValue = await maxTokensInput.inputValue();

    // Set new value
    await maxTokensInput.fill('4096');

    // Intercept request to verify field name transformation
    let updateRequestBody: any = null;
    page.on('request', request => {
      if (request.method() === 'PUT' && request.url().includes('/api/v1/agents/')) {
        updateRequestBody = request.postDataJSON();
      }
    });

    // Submit
    await page.getByRole('button', { name: /update agent/i }).click();
    await expect(dialog).not.toBeVisible({ timeout: 10000 });

    // Verify field name is snake_case
    if (updateRequestBody) {
      expect(updateRequestBody).toHaveProperty('max_tokens');
      expect(updateRequestBody.max_tokens).toBe(4096);
    }

    // Cleanup
    await page.getByRole('button', { name: /configure/i }).click();
    await expect(dialog).toBeVisible();
    await page.getByLabel(/max tokens/i).fill(originalValue);
    await page.getByRole('button', { name: /update agent/i }).click();
    await expect(dialog).not.toBeVisible({ timeout: 10000 });
  });

  test('should update system prompt', async ({ authenticatedPage: page }) => {
    // Navigate to agents page
    await page.goto('http://localhost:5173/agents');
    await page.waitForLoadState('networkidle');

    // Click on first agent
    await page.locator('[data-testid="agent-card"]').first().click();
    await page.waitForURL(/\/agent\/.*/, { timeout: 5000 });

    // Open edit dialog
    await page.getByRole('button', { name: /configure/i }).click();
    const dialog = page.getByRole('dialog');
    await expect(dialog).toBeVisible();

    // Find system prompt textarea
    const systemPromptInput = page.getByLabel(/system prompt/i);
    await expect(systemPromptInput).toBeVisible();

    // Store original value
    const originalValue = await systemPromptInput.inputValue();

    // Set new value
    const newPrompt = `You are a helpful test assistant. Timestamp: ${Date.now()}`;
    await systemPromptInput.fill(newPrompt);

    // Intercept request to verify field name transformation
    let updateRequestBody: any = null;
    page.on('request', request => {
      if (request.method() === 'PUT' && request.url().includes('/api/v1/agents/')) {
        updateRequestBody = request.postDataJSON();
      }
    });

    // Submit
    await page.getByRole('button', { name: /update agent/i }).click();
    await expect(dialog).not.toBeVisible({ timeout: 10000 });

    // Verify field name is snake_case
    if (updateRequestBody) {
      expect(updateRequestBody).toHaveProperty('system_prompt');
      expect(updateRequestBody.system_prompt).toBe(newPrompt);
    }

    // Cleanup
    await page.getByRole('button', { name: /configure/i }).click();
    await expect(dialog).toBeVisible();
    await page.getByLabel(/system prompt/i).fill(originalValue);
    await page.getByRole('button', { name: /update agent/i }).click();
    await expect(dialog).not.toBeVisible({ timeout: 10000 });
  });
});
