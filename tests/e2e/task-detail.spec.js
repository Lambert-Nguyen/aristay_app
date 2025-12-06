/**
 * E2E Tests - Task Detail Page
 * 
 * Tests complete user workflows with real browser interactions
 * Requires Django development server running on localhost:8000
 */

import { test, expect } from '@playwright/test';

// Test configuration
const BASE_URL = 'http://localhost:8000';
const TEST_USER = {
  username: 'teststaff',
  password: 'testpass123'
};

test.describe('Task Detail E2E Tests', () => {
  test.beforeEach(async ({ page }) => {
    // Login before each test
    await page.goto(`${BASE_URL}/api/staff/login/`);
    await page.fill('[name="username"]', TEST_USER.username);
    await page.fill('[name="password"]', TEST_USER.password);
    await page.click('button[type="submit"]');
    await page.waitForURL(/\/api\/staff\/(tasks|dashboard)/);
  });

  test.describe('Component Template Integration', () => {
    test('timer component loads and functions', async ({ page }) => {
      // Navigate to task detail page
      await page.goto(`${BASE_URL}/api/staff/tasks/1/`);
      
      // Verify timer component rendered
      await expect(page.locator('#taskTimer')).toBeVisible();
      await expect(page.locator('#timerText')).toHaveText('00:00:00');
      
      // Start timer
      await page.click('#startTimerBtn');
      
      // Wait a bit and verify timer is running
      await page.waitForTimeout(2000);
      const timerText = await page.locator('#timerText').textContent();
      expect(timerText).not.toBe('00:00:00');
      
      // Pause button should be visible
      await expect(page.locator('#pauseTimerBtn')).toBeVisible();
      await expect(page.locator('#startTimerBtn')).toBeHidden();
    });

    test('navigation component provides working links', async ({ page }) => {
      await page.goto(`${BASE_URL}/api/staff/tasks/1/`);
      
      // Verify navigation buttons exist
      await expect(page.locator('.btn-nav.prev-task')).toBeVisible();
      await expect(page.locator('.btn-nav.next-task')).toBeVisible();
      await expect(page.locator('.btn-nav.back-to-list')).toBeVisible();
      
      // Test back to list
      await page.click('.btn-nav.back-to-list');
      await expect(page).toHaveURL(/\/api\/staff\/tasks\//);
    });

    test('progress component updates dynamically', async ({ page }) => {
      await page.goto(`${BASE_URL}/api/staff/tasks/1/`);
      
      // Verify progress component rendered
      await expect(page.locator('.progress-overview')).toBeVisible();
      await expect(page.locator('.progress-percentage')).toBeVisible();
      
      // Get initial progress
      const initialProgress = await page.locator('.progress-percentage').textContent();
      
      // Complete a checklist item
      const firstCheckbox = page.locator('.checklist-checkbox').first();
      await firstCheckbox.check();
      
      // Wait for API call and UI update
      await page.waitForTimeout(1000);
      
      // Verify progress changed
      const updatedProgress = await page.locator('.progress-percentage').textContent();
      expect(updatedProgress).not.toBe(initialProgress);
    });

    test('checklist component handles item completion', async ({ page }) => {
      await page.goto(`${BASE_URL}/api/staff/tasks/1/`);
      
      // Find first uncompleted checklist item
      const checklistItem = page.locator('.checklist-item').first();
      const checkbox = checklistItem.locator('.checklist-checkbox');
      
      // Check the item
      await checkbox.check();
      
      // Wait for API response
      await page.waitForResponse(response => 
        response.url().includes('/api/') && response.status() === 200
      );
      
      // Verify item marked as completed
      await expect(checklistItem).toHaveClass(/completed/);
    });
  });

  test.describe('Complete Task Workflow', () => {
    test('user can complete entire task from start to finish', async ({ page }) => {
      await page.goto(`${BASE_URL}/api/staff/tasks/1/`);
      
      // Step 1: Start timer
      await page.click('#startTimerBtn');
      await expect(page.locator('#pauseTimerBtn')).toBeVisible();
      
      // Step 2: Complete all checklist items
      const checkboxes = await page.locator('.checklist-checkbox').all();
      for (const checkbox of checkboxes) {
        if (!(await checkbox.isChecked())) {
          await checkbox.check();
          await page.waitForTimeout(500); // Wait for API call
        }
      }
      
      // Step 3: Verify progress is 100%
      await expect(page.locator('.progress-percentage')).toHaveText('100%');
      
      // Step 4: Complete task button should be enabled
      const completeBtn = page.locator('.complete-task-btn');
      await expect(completeBtn).toBeVisible();
      await expect(completeBtn).toBeEnabled();
      
      // Step 5: Complete the task
      await completeBtn.click();
      
      // Step 6: Verify task status updated
      await expect(page.locator('.status-badge')).toContainText('Completed');
    });

    test('timer persists across page reloads', async ({ page }) => {
      await page.goto(`${BASE_URL}/api/staff/tasks/1/`);
      
      // Start timer
      await page.click('#startTimerBtn');
      await page.waitForTimeout(3000);
      
      // Get timer value
      const timerBeforeReload = await page.locator('#timerText').textContent();
      
      // Reload page
      await page.reload();
      
      // Verify timer restored
      const timerAfterReload = await page.locator('#timerText').textContent();
      expect(timerAfterReload).not.toBe('00:00:00');
      expect(timerAfterReload).toBe(timerBeforeReload);
    });
  });

  test.describe('Photo Upload Workflow', () => {
    test('user can upload photo to checklist item', async ({ page }) => {
      await page.goto(`${BASE_URL}/api/staff/tasks/1/`);
      
      // Find checklist item with photo upload
      const uploadBtn = page.locator('.btn-upload').first();
      await uploadBtn.scrollIntoViewIfNeeded();
      
      // Trigger file input
      const fileInput = page.locator('input[type="file"]').first();
      
      // Upload test image
      await fileInput.setInputFiles('tests/fixtures/test-photo.jpg');
      
      // Wait for upload to complete
      await page.waitForResponse(response =>
        response.url().includes('/photos/') && response.status() === 200
      );
      
      // Verify photo appears in grid
      await expect(page.locator('.photo-item img').first()).toBeVisible();
    });

    test('photo modal opens on image click', async ({ page }) => {
      await page.goto(`${BASE_URL}/api/staff/tasks/1/`);
      
      // Click on first photo
      const firstPhoto = page.locator('.photo-item img').first();
      await firstPhoto.click();
      
      // Verify modal opens
      const modal = page.locator('#photoModal');
      await expect(modal).toBeVisible();
      
      // Verify photo displayed in modal
      await expect(modal.locator('#modalPhoto')).toBeVisible();
      
      // Close modal with Escape key
      await page.keyboard.press('Escape');
      await expect(modal).toBeHidden();
    });
  });

  test.describe('Keyboard Shortcuts', () => {
    test('Alt+Left navigates to previous task', async ({ page }) => {
      await page.goto(`${BASE_URL}/api/staff/tasks/2/`); // Task 2 so prev exists
      
      // Get current URL
      const currentUrl = page.url();
      
      // Press Alt+Left
      await page.keyboard.press('Alt+ArrowLeft');
      
      // Verify navigation occurred
      await page.waitForURL(url => url.toString() !== currentUrl);
      expect(page.url()).toContain('/tasks/1/');
    });

    test('Alt+Right navigates to next task', async ({ page }) => {
      await page.goto(`${BASE_URL}/api/staff/tasks/1/`);
      
      const currentUrl = page.url();
      
      await page.keyboard.press('Alt+ArrowRight');
      
      await page.waitForURL(url => url.toString() !== currentUrl);
      expect(page.url()).toContain('/tasks/2/');
    });

    test('Escape returns to task list', async ({ page }) => {
      await page.goto(`${BASE_URL}/api/staff/tasks/1/`);
      
      await page.keyboard.press('Escape');
      
      await expect(page).toHaveURL(/\/api\/staff\/tasks\/$/);
    });

    test('keyboard shortcuts respect input focus', async ({ page }) => {
      await page.goto(`${BASE_URL}/api/staff/tasks/1/`);
      
      // Focus on textarea
      const textarea = page.locator('textarea.notes-input').first();
      await textarea.click();
      await textarea.fill('Test note');
      
      const urlBeforeShortcut = page.url();
      
      // Try navigation shortcut (should NOT work when textarea focused)
      await page.keyboard.press('Alt+ArrowRight');
      
      // Wait a bit
      await page.waitForTimeout(500);
      
      // Verify no navigation occurred
      expect(page.url()).toBe(urlBeforeShortcut);
    });
  });

  test.describe('Error Handling', () => {
    test('network error shows user-friendly message', async ({ page }) => {
      await page.goto(`${BASE_URL}/api/staff/tasks/1/`);
      
      // Intercept API call and force error
      await page.route('**/api/staff/checklist/**/update/', route => {
        route.abort('failed');
      });
      
      // Try to update checklist item
      const checkbox = page.locator('.checklist-checkbox').first();
      await checkbox.check();
      
      // Verify error notification appears
      await expect(page.locator('.notification.error')).toBeVisible();
      
      // Verify checkbox rolled back
      await expect(checkbox).not.toBeChecked();
    });

    test('handles 404 for missing task gracefully', async ({ page }) => {
      await page.goto(`${BASE_URL}/api/staff/tasks/99999/`);
      
      // Should show 404 page or redirect
      await expect(page.locator('body')).toContainText(/not found|404/i);
    });
  });

  test.describe('Mobile Responsiveness', () => {
    test.use({ viewport: { width: 375, height: 667 } }); // iPhone SE
    
    test('task detail renders correctly on mobile', async ({ page }) => {
      await page.goto(`${BASE_URL}/api/staff/tasks/1/`);
      
      // Verify key elements visible
      await expect(page.locator('.task-title')).toBeVisible();
      await expect(page.locator('#taskTimer')).toBeVisible();
      await expect(page.locator('.progress-overview')).toBeVisible();
      
      // Verify navigation buttons accessible
      await expect(page.locator('.navigation-actions')).toBeVisible();
    });

    test('checklist items stack vertically on mobile', async ({ page }) => {
      await page.goto(`${BASE_URL}/api/staff/tasks/1/`);
      
      const firstItem = page.locator('.checklist-item').first();
      const secondItem = page.locator('.checklist-item').nth(1);
      
      const firstBox = await firstItem.boundingBox();
      const secondBox = await secondItem.boundingBox();
      
      // Second item should be below first (not side-by-side)
      expect(secondBox.y).toBeGreaterThan(firstBox.y + firstBox.height);
    });
  });

  test.describe('Performance', () => {
    test('page loads within 3 seconds', async ({ page }) => {
      const startTime = Date.now();
      
      await page.goto(`${BASE_URL}/api/staff/tasks/1/`);
      await page.waitForLoadState('networkidle');
      
      const loadTime = Date.now() - startTime;
      expect(loadTime).toBeLessThan(3000);
    });

    test('JavaScript modules load correctly', async ({ page }) => {
      await page.goto(`${BASE_URL}/api/staff/tasks/1/`);
      
      // Verify no console errors
      const errors = [];
      page.on('console', msg => {
        if (msg.type() === 'error') errors.push(msg.text());
      });
      
      await page.waitForTimeout(1000);
      
      expect(errors).toHaveLength(0);
    });

    test('handles 100+ checklist items without lag', async ({ page }) => {
      // Assuming a test task with many items exists
      await page.goto(`${BASE_URL}/api/staff/tasks/999/`); // Large checklist task
      
      const startTime = Date.now();
      
      // Check all items
      const checkboxes = await page.locator('.checklist-checkbox').all();
      for (const checkbox of checkboxes.slice(0, 100)) {
        await checkbox.check({ timeout: 100 });
      }
      
      const totalTime = Date.now() - startTime;
      
      // Should complete in reasonable time (< 30 seconds for 100 items)
      expect(totalTime).toBeLessThan(30000);
    });
  });
});
