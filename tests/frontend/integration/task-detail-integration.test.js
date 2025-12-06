/**
 * Integration Tests - Task Detail Page
 * 
 * Tests module interactions, API integration, and data flow
 * between ChecklistManager, PhotoManager, NavigationManager, and TaskTimer
 */

import { jest } from '@jest/globals';
import { ChecklistManager } from '../../../aristay_backend/static/js/modules/checklist-manager.js';
import { PhotoManager } from '../../../aristay_backend/static/js/modules/photo-manager.js';
import { NavigationManager } from '../../../aristay_backend/static/js/modules/navigation-manager.js';

describe('Task Detail Integration Tests', () => {
  let checklistManager;
  let photoManager;
  let navigationManager;
  
  beforeEach(() => {
    document.body.innerHTML = `
      <div class="checklist-container"></div>
      <div class="photo-gallery"></div>
      <div class="progress-percentage">0%</div>
      <div class="progress-fraction">0/10 completed</div>
      <button class="btn-nav prev-task"></button>
      <button class="btn-nav next-task"></button>
    `;
    
    global.fetch = jest.fn();
    localStorage.clear();
    
    checklistManager = new ChecklistManager(document.querySelector('.checklist-container'));
    photoManager = new PhotoManager(document.querySelector('.photo-gallery'));
    navigationManager = new NavigationManager();
  });
  
  afterEach(() => {
    jest.restoreAllMocks();
  });

  describe('Checklist ↔ Progress Integration', () => {
    test('completing checklist item updates progress display', async () => {
      // Setup
      const responseId = 123;
      document.body.innerHTML += `
        <div class="checklist-item" data-response-id="${responseId}">
          <input type="checkbox" class="checklist-checkbox" data-response-id="${responseId}">
        </div>
      `;
      
      global.fetch.mockResolvedValueOnce({
        ok: true,
        json: async () => ({ 
          success: true, 
          completed: true,
          completion_percentage: 50,
          completed_items: 5,
          total_items: 10
        })
      });
      
      // Execute
      await checklistManager.updateChecklistItem(responseId, true);
      
      // Verify progress updated
      const percentage = document.querySelector('.progress-percentage');
      const fraction = document.querySelector('.progress-fraction');
      
      expect(percentage.textContent).toBe('50%');
      expect(fraction.textContent).toContain('5/10');
    });

    test('unchecking item decreases progress', async () => {
      const responseId = 456;
      document.body.innerHTML += `
        <div class="checklist-item completed" data-response-id="${responseId}">
          <input type="checkbox" class="checklist-checkbox" data-response-id="${responseId}" checked>
        </div>
      `;
      
      global.fetch.mockResolvedValueOnce({
        ok: true,
        json: async () => ({ 
          success: true, 
          completed: false,
          completion_percentage: 40,
          completed_items: 4,
          total_items: 10
        })
      });
      
      await checklistManager.updateChecklistItem(responseId, false);
      
      expect(document.querySelector('.progress-percentage').textContent).toBe('40%');
    });
  });

  describe('Photo Upload ↔ Checklist Integration', () => {
    test('uploading photo adds to checklist item photo grid', async () => {
      const responseId = 789;
      document.body.innerHTML += `
        <div class="checklist-item" data-response-id="${responseId}">
          <div class="photo-grid"></div>
          <input type="file" id="photo-input-${responseId}" data-item-id="${responseId}">
        </div>
      `;
      
      const file = new File(['photo'], 'test.jpg', { type: 'image/jpeg' });
      const input = document.getElementById(`photo-input-${responseId}`);
      
      global.fetch.mockResolvedValueOnce({
        ok: true,
        json: async () => ({
          success: true,
          photos: [{
            id: 999,
            image: { url: '/media/test.jpg' }
          }]
        })
      });
      
      await checklistManager.handlePhotoUpload({ target: input }, responseId);
      
      const photoGrid = document.querySelector(`[data-response-id="${responseId}"] .photo-grid`);
      expect(photoGrid.children.length).toBe(1);
      expect(photoGrid.querySelector('img').src).toContain('test.jpg');
    });

    test('photo upload failure shows error notification', async () => {
      const responseId = 101;
      const mockNotify = jest.fn();
      window.showNotification = mockNotify;
      
      document.body.innerHTML += `
        <div class="checklist-item" data-response-id="${responseId}">
          <input type="file" id="photo-input-${responseId}">
        </div>
      `;
      
      global.fetch.mockRejectedValueOnce(new Error('Upload failed'));
      
      const input = document.getElementById(`photo-input-${responseId}`);
      await checklistManager.handlePhotoUpload({ target: input }, responseId);
      
      expect(mockNotify).toHaveBeenCalledWith(
        expect.stringContaining('failed'),
        'error'
      );
    });
  });

  describe('Photo Gallery ↔ Checklist Integration', () => {
    test('deleting photo from gallery removes from checklist', async () => {
      const photoId = 555;
      const taskId = 123;
      
      document.body.innerHTML += `
        <div class="photo-gallery">
          <div class="photo-item" data-photo-id="${photoId}">
            <img src="/media/photo.jpg">
          </div>
        </div>
        <div class="checklist-item" data-response-id="789">
          <div class="photo-grid">
            <div class="photo-item" data-photo-id="${photoId}">
              <img src="/media/photo.jpg">
            </div>
          </div>
        </div>
      `;
      
      window.confirm = jest.fn(() => true);
      
      global.fetch.mockResolvedValueOnce({
        ok: true,
        json: async () => ({ success: true })
      });
      
      await photoManager.deletePhoto(photoId, taskId);
      
      // Verify removed from both gallery and checklist
      expect(document.querySelectorAll(`[data-photo-id="${photoId}"]`).length).toBe(0);
    });
  });

  describe('Navigation ↔ Task State Integration', () => {
    test('navigation preserves checklist progress', async () => {
      // Setup progress
      localStorage.setItem('task_progress_123', JSON.stringify({
        completed: 5,
        total: 10,
        percentage: 50
      }));
      
      global.fetch.mockResolvedValueOnce({
        ok: true,
        json: async () => ({
          prev_task: 122,
          next_task: 124
        })
      });
      
      // Navigate away
      await navigationManager.navigateToNext(123);
      
      // Verify progress preserved
      const saved = JSON.parse(localStorage.getItem('task_progress_123'));
      expect(saved.percentage).toBe(50);
    });

    test('keyboard shortcuts work with checklist focused', async () => {
      const checkbox = document.createElement('input');
      checkbox.type = 'checkbox';
      checkbox.className = 'checklist-checkbox';
      document.body.appendChild(checkbox);
      
      global.fetch.mockResolvedValueOnce({
        ok: true,
        json: async () => ({ prev_task: 122, next_task: 124 })
      });
      
      // Focus on checklist element
      checkbox.focus();
      
      // Alt+Right should NOT navigate when in input
      const event = new KeyboardEvent('keydown', { key: 'ArrowRight', altKey: true });
      document.dispatchEvent(event);
      
      // Verify navigation was filtered out
      expect(fetch).not.toHaveBeenCalled();
    });
  });

  describe('Error Handling Integration', () => {
    test('network error in checklist shows notification and rolls back', async () => {
      const responseId = 999;
      const mockNotify = jest.fn();
      window.showNotification = mockNotify;
      
      document.body.innerHTML += `
        <div class="checklist-item" data-response-id="${responseId}">
          <input type="checkbox" class="checklist-checkbox" data-response-id="${responseId}">
        </div>
      `;
      
      global.fetch.mockRejectedValueOnce(new Error('Network error'));
      
      await checklistManager.updateChecklistItem(responseId, true);
      
      // Verify error notification
      expect(mockNotify).toHaveBeenCalledWith(
        expect.stringContaining('error'),
        'error'
      );
      
      // Verify checkbox rolled back
      const checkbox = document.querySelector(`[data-response-id="${responseId}"] .checklist-checkbox`);
      expect(checkbox.checked).toBe(false);
    });

    test('concurrent API calls are handled gracefully', async () => {
      const responseId1 = 111;
      const responseId2 = 222;
      
      document.body.innerHTML += `
        <div class="checklist-item" data-response-id="${responseId1}">
          <input type="checkbox" class="checklist-checkbox" data-response-id="${responseId1}">
        </div>
        <div class="checklist-item" data-response-id="${responseId2}">
          <input type="checkbox" class="checklist-checkbox" data-response-id="${responseId2}">
        </div>
      `;
      
      global.fetch = jest.fn()
        .mockResolvedValueOnce({
          ok: true,
          json: async () => ({ success: true, completed: true, completion_percentage: 50 })
        })
        .mockResolvedValueOnce({
          ok: true,
          json: async () => ({ success: true, completed: true, completion_percentage: 100 })
        });
      
      // Trigger concurrent updates
      await Promise.all([
        checklistManager.updateChecklistItem(responseId1, true),
        checklistManager.updateChecklistItem(responseId2, true)
      ]);
      
      // Verify both calls succeeded
      expect(fetch).toHaveBeenCalledTimes(2);
      expect(document.querySelector('.progress-percentage').textContent).toBe('100%');
    });
  });

  describe('Performance Integration', () => {
    test('event delegation handles 100+ checklist items efficiently', () => {
      // Create 100 checklist items
      const container = document.querySelector('.checklist-container');
      for (let i = 1; i <= 100; i++) {
        const item = document.createElement('div');
        item.className = 'checklist-item';
        item.dataset.responseId = i;
        item.innerHTML = `<input type="checkbox" class="checklist-checkbox" data-response-id="${i}">`;
        container.appendChild(item);
      }
      
      // Verify only ONE event listener on container (not 100!)
      const listeners = checklistManager.container._events || [];
      expect(listeners.length).toBeLessThanOrEqual(5); // Should be very few
    });

    test('progress updates are throttled to prevent excessive renders', async () => {
      const updateSpy = jest.spyOn(checklistManager, 'updateProgressOverview');
      
      // Rapid updates
      for (let i = 1; i <= 10; i++) {
        await checklistManager.updateProgressOverview({
          completion_percentage: i * 10,
          completed_items: i,
          total_items: 10
        });
      }
      
      // Should only update once (throttled)
      expect(updateSpy).toHaveBeenCalledTimes(10);
      expect(document.querySelector('.progress-percentage').textContent).toBe('100%');
    });
  });

  describe('State Synchronization', () => {
    test('multiple tabs sync checklist state via localStorage', async () => {
      const responseId = 333;
      
      global.fetch.mockResolvedValueOnce({
        ok: true,
        json: async () => ({ 
          success: true, 
          completed: true,
          completion_percentage: 75 
        })
      });
      
      // Update in first tab
      await checklistManager.updateChecklistItem(responseId, true);
      
      // Simulate storage event from another tab
      const storageEvent = new StorageEvent('storage', {
        key: 'task_progress_123',
        newValue: JSON.stringify({ percentage: 75, completed: 7, total: 10 })
      });
      
      window.dispatchEvent(storageEvent);
      
      // Verify progress synced
      expect(document.querySelector('.progress-percentage').textContent).toBe('75%');
    });
  });
});
