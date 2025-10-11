/**
 * Debug test to capture console errors causing blank screen
 */

import { test } from '@playwright/test';

test('capture console errors and take screenshot', async ({ page }) => {
  const consoleMessages: any[] = [];
  const errors: any[] = [];

  // Capture all console messages
  page.on('console', msg => {
    consoleMessages.push({
      type: msg.type(),
      text: msg.text(),
    });
    console.log(`[${msg.type()}] ${msg.text()}`);
  });

  // Capture page errors
  page.on('pageerror', error => {
    errors.push(error.message);
    console.log('PAGE ERROR:', error.message);
  });

  // Navigate to the page
  await page.goto('http://localhost:5173');

  // Wait a bit
  await page.waitForTimeout(3000);

  // Take screenshot
  await page.screenshot({ path: 'tests/screenshots/blank-screen-debug.png', fullPage: true });

  // Get the page content
  const html = await page.content();
  console.log('\n=== PAGE HTML ===');
  console.log(html.substring(0, 1000));

  // Check if React root is rendered
  const rootContent = await page.locator('#root').innerHTML();
  console.log('\n=== ROOT CONTENT ===');
  console.log(rootContent);

  console.log('\n=== CONSOLE MESSAGES ===');
  console.log(JSON.stringify(consoleMessages, null, 2));

  console.log('\n=== ERRORS ===');
  console.log(JSON.stringify(errors, null, 2));
});
