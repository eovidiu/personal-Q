import { test, expect } from '@playwright/test';

test('debug: capture page rendering and console errors', async ({ page }) => {
  const consoleMessages: string[] = [];
  const consoleErrors: string[] = [];

  // Capture console messages
  page.on('console', msg => {
    const text = msg.text();
    consoleMessages.push(`[${msg.type()}] ${text}`);
    if (msg.type() === 'error') {
      consoleErrors.push(text);
    }
  });

  // Capture page errors
  page.on('pageerror', error => {
    consoleErrors.push(`PAGE ERROR: ${error.message}`);
  });

  await page.goto('/');
  await page.waitForTimeout(2000);

  // Take screenshot
  await page.screenshot({ path: 'test-results/debug-rendering.png', fullPage: true });

  // Get HTML content
  const bodyHTML = await page.locator('body').innerHTML();
  const rootHTML = await page.locator('#root').innerHTML();

  console.log('\n=== CONSOLE MESSAGES ===');
  consoleMessages.forEach(msg => console.log(msg));

  console.log('\n=== CONSOLE ERRORS ===');
  consoleErrors.forEach(err => console.log(err));

  console.log('\n=== BODY HTML (first 500 chars) ===');
  console.log(bodyHTML.substring(0, 500));

  console.log('\n=== ROOT HTML (first 500 chars) ===');
  console.log(rootHTML.substring(0, 500));

  // Report results
  expect(consoleErrors).toHaveLength(0);
});
