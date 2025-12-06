/**
 * Baseline E2E tests
 * These tests verify core functionality before refactoring
 */

import { test, expect } from '@playwright/test';

test.describe('Staff Portal - Baseline Tests', () => {
  // Run these tests with a logged-in user
  test.use({ storageState: 'tests/frontend/e2e/.auth/user.json' });
  
  test('staff dashboard loads successfully', async ({ page }) => {
    await page.goto('/api/staff/dashboard/');
    
    // Check for main heading
    await expect(page.locator('h1, h2').first()).toBeVisible();
    
    // Verify no console errors
    const consoleErrors = [];
    page.on('console', msg => {
      if (msg.type() === 'error') {
        consoleErrors.push(msg.text());
      }
    });
    
    await page.waitForLoadState('networkidle');
    expect(consoleErrors).toHaveLength(0);
  });
  
  test('task list page loads', async ({ page }) => {
    await page.goto('/api/staff/tasks/');
    
    // Check for task list or empty state
    const taskList = page.locator('.task-card, .task-item, .empty-state');
    await expect(taskList.first()).toBeVisible();
  });
  
  test('CSRF token is present in DOM', async ({ page }) => {
    await page.goto('/api/staff/dashboard/');
    
    // Check for CSRF token in hidden input or meta tag
    const csrfInput = page.locator('input[name="csrfmiddlewaretoken"]');
    const csrfMeta = page.locator('meta[name="csrf-token"]');
    
    const hasToken = await csrfInput.count() > 0 || await csrfMeta.count() > 0;
    expect(hasToken).toBe(true);
  });
});

test.describe('Public Pages - Baseline Tests', () => {
  test('login page loads', async ({ page }) => {
    await page.goto('/api/staff/login/');
    
    // Check for login form
    await expect(page.locator('input[name="username"]')).toBeVisible();
    await expect(page.locator('input[name="password"]')).toBeVisible();
    await expect(page.locator('button[type="submit"]')).toBeVisible();
  });
  
  test('login page has no JavaScript errors', async ({ page }) => {
    const consoleErrors = [];
    page.on('console', msg => {
      if (msg.type() === 'error') {
        consoleErrors.push(msg.text());
      }
    });
    
    await page.goto('/api/staff/login/');
    await page.waitForLoadState('networkidle');
    
    expect(consoleErrors).toHaveLength(0);
  });
});

// Note: This requires setting up authentication state
// Run: npx playwright codegen http://localhost:8000/api/staff/login/
// to generate the authentication file
