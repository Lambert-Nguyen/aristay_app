/**
 * Unit Tests for ChecklistManager Module
 * Tests checklist item management, photo uploads, notes, and progress tracking
 */

import { describe, it, expect, beforeEach, afterEach, jest } from '@jest/globals';
import { ChecklistManager } from '../../../aristay_backend/static/js/modules/checklist-manager.js';

// Mock APIClient
jest.mock('../../../aristay_backend/static/js/core/api-client.js', () => ({
  APIClient: {
    request: jest.fn(),
    upload: jest.fn(),
    get: jest.fn(),
    post: jest.fn(),
    patch: jest.fn(),
    delete: jest.fn(),
  }
}));

import { APIClient } from '../../../aristay_backend/static/js/core/api-client.js';

describe('ChecklistManager', () => {
  let checklistManager;
  let mockContainer;
  let mockTaskContainer;

  beforeEach(() => {
    // Reset DOM
    document.body.innerHTML = '';
    
    // Create mock task container with task ID
    mockTaskContainer = document.createElement('div');
    mockTaskContainer.id = 'taskDetailContainer';
    mockTaskContainer.dataset.taskId = '123';
    document.body.appendChild(mockTaskContainer);

    // Create mock checklist container
    mockContainer = document.createElement('div');
    mockContainer.className = 'checklist-container';
    mockContainer.innerHTML = `
      <div class="progress-overview">
        <div class="progress-bar-container">
          <div class="progress-bar-fill" style="width: 0%"></div>
        </div>
        <div class="progress-stats">
          <span class="progress-percentage">0%</span>
          <span class="progress-count">0/0 items completed</span>
        </div>
      </div>
      <div class="checklist-items">
        <div class="checklist-item" data-response-id="1">
          <input type="checkbox" class="checklist-checkbox" data-response-id="1">
          <span class="checklist-label">Test Task 1</span>
          <button class="btn-notes" data-response-id="1">Notes</button>
          <input type="file" class="photo-upload" data-response-id="1" multiple accept="image/*">
          <div class="photo-grid" data-response-id="1"></div>
        </div>
        <div class="checklist-item" data-response-id="2">
          <input type="checkbox" class="checklist-checkbox" data-response-id="2" checked>
          <span class="checklist-label">Test Task 2</span>
          <button class="btn-notes" data-response-id="2">Notes</button>
          <input type="file" class="photo-upload" data-response-id="2" multiple accept="image/*">
          <div class="photo-grid" data-response-id="2"></div>
        </div>
      </div>
    `;
    document.body.appendChild(mockContainer);

    // Create notes modal
    const notesModal = document.createElement('div');
    notesModal.id = 'notesModal';
    notesModal.innerHTML = `
      <textarea id="checklistNotes"></textarea>
      <button id="saveNotesBtn">Save</button>
      <button id="closeNotesBtn">Close</button>
    `;
    document.body.appendChild(notesModal);

    // Clear all mocks
    jest.clearAllMocks();
    
    // Reset window instances
    window.checklistManagerInstance = null;
  });

  afterEach(() => {
    document.body.innerHTML = '';
    jest.clearAllMocks();
  });

  describe('Constructor', () => {
    it('should initialize with default container', () => {
      checklistManager = new ChecklistManager();
      expect(checklistManager.container).toBe(mockContainer);
      expect(checklistManager.taskId).toBe('123');
    });

    it('should initialize with custom container', () => {
      const customContainer = document.createElement('div');
      customContainer.className = 'custom-checklist';
      document.body.appendChild(customContainer);

      checklistManager = new ChecklistManager(customContainer);
      expect(checklistManager.container).toBe(customContainer);
    });

    it('should handle missing container gracefully', () => {
      document.body.innerHTML = '';
      expect(() => {
        checklistManager = new ChecklistManager();
      }).not.toThrow();
    });

    it('should set up event listeners', () => {
      const addEventListenerSpy = jest.spyOn(mockContainer, 'addEventListener');
      checklistManager = new ChecklistManager();
      
      expect(addEventListenerSpy).toHaveBeenCalledWith('change', expect.any(Function));
      expect(addEventListenerSpy).toHaveBeenCalledWith('click', expect.any(Function));
    });
  });

  describe('updateChecklistItem()', () => {
    beforeEach(() => {
      checklistManager = new ChecklistManager();
    });

    it('should update checklist item to completed', async () => {
      APIClient.request.mockResolvedValue({
        success: true,
        id: 1,
        is_completed: true
      });

      await checklistManager.updateChecklistItem('1', true);

      expect(APIClient.request).toHaveBeenCalledWith(
        '/api/checklist-responses/1/',
        expect.objectContaining({
          method: 'PATCH',
          body: JSON.stringify({ is_completed: true })
        })
      );
    });

    it('should update checklist item to not completed', async () => {
      APIClient.request.mockResolvedValue({
        success: true,
        id: 2,
        is_completed: false
      });

      await checklistManager.updateChecklistItem('2', false);

      expect(APIClient.request).toHaveBeenCalledWith(
        '/api/checklist-responses/2/',
        expect.objectContaining({
          method: 'PATCH',
          body: JSON.stringify({ is_completed: false })
        })
      );
    });

    it('should update progress overview after successful update', async () => {
      APIClient.request.mockResolvedValue({ success: true });
      const updateProgressSpy = jest.spyOn(checklistManager, 'updateProgressOverview');

      await checklistManager.updateChecklistItem('1', true);

      expect(updateProgressSpy).toHaveBeenCalled();
    });

    it('should show success notification', async () => {
      APIClient.request.mockResolvedValue({ success: true });
      const showNotificationSpy = jest.spyOn(checklistManager, 'showNotification');

      await checklistManager.updateChecklistItem('1', true);

      expect(showNotificationSpy).toHaveBeenCalledWith(
        'Checklist item updated!',
        'success'
      );
    });

    it('should handle API errors gracefully', async () => {
      const error = new Error('Network error');
      APIClient.request.mockRejectedValue(error);
      const showNotificationSpy = jest.spyOn(checklistManager, 'showNotification');

      await checklistManager.updateChecklistItem('1', true);

      expect(showNotificationSpy).toHaveBeenCalledWith(
        'Failed to update checklist item: Network error',
        'error'
      );
    });

    it('should handle missing response ID', async () => {
      const consoleSpy = jest.spyOn(console, 'error').mockImplementation();

      await checklistManager.updateChecklistItem(null, true);

      expect(consoleSpy).toHaveBeenCalledWith('Response ID is required');
      expect(APIClient.request).not.toHaveBeenCalled();
      
      consoleSpy.mockRestore();
    });
  });

  describe('handlePhotoUpload()', () => {
    beforeEach(() => {
      checklistManager = new ChecklistManager();
    });

    it('should upload single photo', async () => {
      const mockFile = new File(['photo'], 'test.jpg', { type: 'image/jpeg' });
      const mockEvent = {
        target: {
          files: [mockFile],
          dataset: { responseId: '1' }
        }
      };

      APIClient.upload.mockResolvedValue({
        success: true,
        id: 101,
        image_url: '/media/photos/test.jpg',
        photo_type: 'checklist'
      });

      await checklistManager.handlePhotoUpload(mockEvent);

      expect(APIClient.upload).toHaveBeenCalledTimes(1);
      expect(APIClient.upload).toHaveBeenCalledWith(
        '/api/checklist-responses/1/photos/',
        expect.any(FormData)
      );
    });

    it('should upload multiple photos', async () => {
      const mockFiles = [
        new File(['photo1'], 'test1.jpg', { type: 'image/jpeg' }),
        new File(['photo2'], 'test2.jpg', { type: 'image/jpeg' }),
        new File(['photo3'], 'test3.jpg', { type: 'image/jpeg' })
      ];
      const mockEvent = {
        target: {
          files: mockFiles,
          dataset: { responseId: '1' }
        }
      };

      APIClient.upload.mockResolvedValue({
        success: true,
        id: 101,
        image_url: '/media/photos/test.jpg'
      });

      await checklistManager.handlePhotoUpload(mockEvent);

      expect(APIClient.upload).toHaveBeenCalledTimes(3);
    });

    it('should add photo to UI after successful upload', async () => {
      const mockFile = new File(['photo'], 'test.jpg', { type: 'image/jpeg' });
      const mockEvent = {
        target: {
          files: [mockFile],
          dataset: { responseId: '1' }
        }
      };

      const photoData = {
        success: true,
        id: 101,
        image_url: '/media/photos/test.jpg'
      };
      APIClient.upload.mockResolvedValue(photoData);

      const addPhotoSpy = jest.spyOn(checklistManager, 'addPhotoToChecklistItem');

      await checklistManager.handlePhotoUpload(mockEvent);

      expect(addPhotoSpy).toHaveBeenCalledWith('1', photoData);
    });

    it('should show success notification after upload', async () => {
      const mockFile = new File(['photo'], 'test.jpg', { type: 'image/jpeg' });
      const mockEvent = {
        target: {
          files: [mockFile],
          dataset: { responseId: '1' }
        }
      };

      APIClient.upload.mockResolvedValue({ success: true });
      const showNotificationSpy = jest.spyOn(checklistManager, 'showNotification');

      await checklistManager.handlePhotoUpload(mockEvent);

      expect(showNotificationSpy).toHaveBeenCalledWith(
        '1 photo(s) uploaded successfully!',
        'success'
      );
    });

    it('should handle upload errors', async () => {
      const mockFile = new File(['photo'], 'test.jpg', { type: 'image/jpeg' });
      const mockEvent = {
        target: {
          files: [mockFile],
          dataset: { responseId: '1' }
        }
      };

      const error = new Error('Upload failed');
      APIClient.upload.mockRejectedValue(error);
      const showNotificationSpy = jest.spyOn(checklistManager, 'showNotification');

      await checklistManager.handlePhotoUpload(mockEvent);

      expect(showNotificationSpy).toHaveBeenCalledWith(
        'Upload failed: Upload failed',
        'error'
      );
    });

    it('should handle missing files', async () => {
      const mockEvent = {
        target: {
          files: [],
          dataset: { responseId: '1' }
        }
      };

      const consoleSpy = jest.spyOn(console, 'error').mockImplementation();

      await checklistManager.handlePhotoUpload(mockEvent);

      expect(consoleSpy).toHaveBeenCalledWith('No files selected for upload');
      expect(APIClient.upload).not.toHaveBeenCalled();
      
      consoleSpy.mockRestore();
    });
  });

  describe('saveNotes()', () => {
    beforeEach(() => {
      checklistManager = new ChecklistManager();
    });

    it('should save notes successfully', async () => {
      APIClient.request.mockResolvedValue({
        success: true,
        notes: 'Test notes content'
      });

      await checklistManager.saveNotes('1', 'Test notes content');

      expect(APIClient.request).toHaveBeenCalledWith(
        '/api/checklist-responses/1/notes/',
        expect.objectContaining({
          method: 'PATCH',
          body: JSON.stringify({ notes: 'Test notes content' })
        })
      );
    });

    it('should show success notification', async () => {
      APIClient.request.mockResolvedValue({ success: true });
      const showNotificationSpy = jest.spyOn(checklistManager, 'showNotification');

      await checklistManager.saveNotes('1', 'Test notes');

      expect(showNotificationSpy).toHaveBeenCalledWith(
        'Notes saved successfully!',
        'success'
      );
    });

    it('should handle save errors', async () => {
      const error = new Error('Save failed');
      APIClient.request.mockRejectedValue(error);
      const showNotificationSpy = jest.spyOn(checklistManager, 'showNotification');

      await checklistManager.saveNotes('1', 'Test notes');

      expect(showNotificationSpy).toHaveBeenCalledWith(
        'Failed to save notes: Save failed',
        'error'
      );
    });

    it('should handle missing response ID', async () => {
      const consoleSpy = jest.spyOn(console, 'error').mockImplementation();

      await checklistManager.saveNotes(null, 'Test notes');

      expect(consoleSpy).toHaveBeenCalledWith('Response ID is required');
      expect(APIClient.request).not.toHaveBeenCalled();
      
      consoleSpy.mockRestore();
    });
  });

  describe('updateProgressOverview()', () => {
    beforeEach(() => {
      checklistManager = new ChecklistManager();
    });

    it('should calculate progress correctly - 0% complete', () => {
      // All checkboxes unchecked
      mockContainer.querySelectorAll('.checklist-checkbox').forEach(cb => cb.checked = false);

      checklistManager.updateProgressOverview();

      const progressBar = mockContainer.querySelector('.progress-bar-fill');
      const progressPercentage = mockContainer.querySelector('.progress-percentage');
      const progressCount = mockContainer.querySelector('.progress-count');

      expect(progressBar.style.width).toBe('0%');
      expect(progressPercentage.textContent).toBe('0%');
      expect(progressCount.textContent).toBe('0/2 items completed');
    });

    it('should calculate progress correctly - 50% complete', () => {
      // One checkbox checked, one unchecked
      const checkboxes = mockContainer.querySelectorAll('.checklist-checkbox');
      checkboxes[0].checked = true;
      checkboxes[1].checked = false;

      checklistManager.updateProgressOverview();

      const progressBar = mockContainer.querySelector('.progress-bar-fill');
      const progressPercentage = mockContainer.querySelector('.progress-percentage');
      const progressCount = mockContainer.querySelector('.progress-count');

      expect(progressBar.style.width).toBe('50%');
      expect(progressPercentage.textContent).toBe('50%');
      expect(progressCount.textContent).toBe('1/2 items completed');
    });

    it('should calculate progress correctly - 100% complete', () => {
      // All checkboxes checked
      mockContainer.querySelectorAll('.checklist-checkbox').forEach(cb => cb.checked = true);

      checklistManager.updateProgressOverview();

      const progressBar = mockContainer.querySelector('.progress-bar-fill');
      const progressPercentage = mockContainer.querySelector('.progress-percentage');
      const progressCount = mockContainer.querySelector('.progress-count');

      expect(progressBar.style.width).toBe('100%');
      expect(progressPercentage.textContent).toBe('100%');
      expect(progressCount.textContent).toBe('2/2 items completed');
    });

    it('should handle no checkboxes gracefully', () => {
      mockContainer.querySelector('.checklist-items').innerHTML = '';

      checklistManager.updateProgressOverview();

      const progressBar = mockContainer.querySelector('.progress-bar-fill');
      expect(progressBar.style.width).toBe('0%');
    });
  });

  describe('addPhotoToChecklistItem()', () => {
    beforeEach(() => {
      checklistManager = new ChecklistManager();
    });

    it('should add photo to photo grid', () => {
      const photoData = {
        id: 101,
        image_url: '/media/photos/test.jpg',
        photo_type: 'checklist'
      };

      checklistManager.addPhotoToChecklistItem('1', photoData);

      const photoGrid = mockContainer.querySelector('[data-response-id="1"] .photo-grid');
      const photoImg = photoGrid.querySelector('img');

      expect(photoImg).not.toBeNull();
      expect(photoImg.src).toContain('test.jpg');
      expect(photoImg.dataset.photoId).toBe('101');
    });

    it('should handle missing photo grid', () => {
      mockContainer.querySelector('.photo-grid').remove();
      const consoleSpy = jest.spyOn(console, 'warn').mockImplementation();

      const photoData = { id: 101, image_url: '/test.jpg' };
      checklistManager.addPhotoToChecklistItem('1', photoData);

      expect(consoleSpy).toHaveBeenCalled();
      consoleSpy.mockRestore();
    });
  });

  describe('Event Delegation', () => {
    beforeEach(() => {
      checklistManager = new ChecklistManager();
    });

    it('should handle checkbox change events', async () => {
      APIClient.request.mockResolvedValue({ success: true });
      const updateSpy = jest.spyOn(checklistManager, 'updateChecklistItem');

      const checkbox = mockContainer.querySelector('[data-response-id="1"].checklist-checkbox');
      checkbox.checked = true;
      checkbox.dispatchEvent(new Event('change', { bubbles: true }));

      // Wait for async operation
      await new Promise(resolve => setTimeout(resolve, 0));

      expect(updateSpy).toHaveBeenCalledWith('1', true);
    });

    it('should handle notes button clicks', () => {
      const notesBtn = mockContainer.querySelector('[data-response-id="1"].btn-notes');
      notesBtn.dispatchEvent(new Event('click', { bubbles: true }));

      const notesModal = document.getElementById('notesModal');
      expect(notesModal.style.display).toBe('block');
    });

    it('should handle file input changes', async () => {
      APIClient.upload.mockResolvedValue({ success: true, id: 101, image_url: '/test.jpg' });
      const uploadSpy = jest.spyOn(checklistManager, 'handlePhotoUpload');

      const fileInput = mockContainer.querySelector('[data-response-id="1"].photo-upload');
      const mockFile = new File(['photo'], 'test.jpg', { type: 'image/jpeg' });
      
      Object.defineProperty(fileInput, 'files', {
        value: [mockFile],
        writable: false
      });

      fileInput.dispatchEvent(new Event('change', { bubbles: true }));

      await new Promise(resolve => setTimeout(resolve, 0));

      expect(uploadSpy).toHaveBeenCalled();
    });
  });

  describe('Global Bridge Functions', () => {
    beforeEach(() => {
      checklistManager = new ChecklistManager();
      window.checklistManagerInstance = checklistManager;
    });

    it('should expose updateChecklistItem globally', () => {
      expect(window.updateChecklistItem).toBeDefined();
      expect(typeof window.updateChecklistItem).toBe('function');
    });

    it('should call instance method through global bridge', async () => {
      APIClient.request.mockResolvedValue({ success: true });
      const updateSpy = jest.spyOn(checklistManager, 'updateChecklistItem');

      await window.updateChecklistItem('1', true);

      expect(updateSpy).toHaveBeenCalledWith('1', true);
    });

    it('should expose uploadPhotos globally', () => {
      expect(window.uploadPhotos).toBeDefined();
      expect(typeof window.uploadPhotos).toBe('function');
    });
  });

  describe('Notification System', () => {
    beforeEach(() => {
      checklistManager = new ChecklistManager();
    });

    it('should show success notification', () => {
      checklistManager.showNotification('Success message', 'success');

      const notification = document.querySelector('.notification-success');
      expect(notification).not.toBeNull();
      expect(notification.textContent).toBe('Success message');
    });

    it('should show error notification', () => {
      checklistManager.showNotification('Error message', 'error');

      const notification = document.querySelector('.notification-error');
      expect(notification).not.toBeNull();
      expect(notification.textContent).toBe('Error message');
    });

    it('should auto-remove notification after 3 seconds', (done) => {
      checklistManager.showNotification('Test message', 'info');

      const notification = document.querySelector('.notification-info');
      expect(notification).not.toBeNull();

      setTimeout(() => {
        const notificationGone = document.querySelector('.notification-info');
        expect(notificationGone).toBeNull();
        done();
      }, 3500);
    });
  });
});
