/**
 * Unit Tests for PhotoManager Module
 * Tests photo gallery management, CRUD operations, filtering, and animations
 */

import { describe, it, expect, beforeEach, afterEach, jest } from '@jest/globals';
import { PhotoManager } from '../../../aristay_backend/static/js/modules/photo-manager.js';

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

describe('PhotoManager', () => {
  let photoManager;
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

    // Create mock photo gallery container
    mockContainer = document.createElement('div');
    mockContainer.className = 'photo-gallery-grid';
    mockContainer.innerHTML = `
      <div class="gallery-photo-item" data-photo-id="1" data-photo-type="before" data-photo-status="approved">
        <img src="/media/photo1.jpg" data-photo-url="/media/photo1.jpg" data-photo-id="1" alt="before photo">
        <div class="photo-meta">
          <div class="photo-header">
            <span class="photo-type-badge">Before</span>
            <span class="photo-status status-approved">Approved</span>
          </div>
        </div>
        <button class="btn-delete-photo" data-photo-id="1">Delete</button>
        <button class="btn-archive-photo" data-photo-id="1">Archive</button>
      </div>
      <div class="gallery-photo-item" data-photo-id="2" data-photo-type="after" data-photo-status="pending">
        <img src="/media/photo2.jpg" data-photo-url="/media/photo2.jpg" data-photo-id="2" alt="after photo">
        <div class="photo-meta">
          <div class="photo-header">
            <span class="photo-type-badge">After</span>
            <span class="photo-status status-pending">Pending Review</span>
          </div>
        </div>
        <button class="btn-delete-photo" data-photo-id="2">Delete</button>
        <button class="btn-archive-photo" data-photo-id="2">Archive</button>
      </div>
    `;
    document.body.appendChild(mockContainer);

    // Mock window.confirm
    global.confirm = jest.fn(() => true);

    // Mock window.openPhotoModal
    window.openPhotoModal = jest.fn();

    // Clear all mocks
    jest.clearAllMocks();
    
    // Reset window instances
    window.photoManagerInstance = null;
  });

  afterEach(() => {
    document.body.innerHTML = '';
    jest.clearAllMocks();
    delete global.confirm;
  });

  describe('Constructor', () => {
    it('should initialize with default container', () => {
      photoManager = new PhotoManager();
      expect(photoManager.container).toBe(mockContainer);
      expect(photoManager.taskId).toBe('123');
    });

    it('should initialize with custom container', () => {
      const customContainer = document.createElement('div');
      customContainer.className = 'custom-gallery';
      document.body.appendChild(customContainer);

      photoManager = new PhotoManager(customContainer);
      expect(photoManager.container).toBe(customContainer);
    });

    it('should handle missing container gracefully', () => {
      document.querySelector('.photo-gallery-grid').remove();
      const consoleSpy = jest.spyOn(console, 'warn').mockImplementation();

      photoManager = new PhotoManager();

      expect(consoleSpy).toHaveBeenCalledWith('Photo gallery container not found');
      consoleSpy.mockRestore();
    });

    it('should set up event listeners', () => {
      const addEventListenerSpy = jest.spyOn(mockContainer, 'addEventListener');
      photoManager = new PhotoManager();
      
      // Should have click event listeners for photos, delete, and archive
      expect(addEventListenerSpy).toHaveBeenCalledWith('click', expect.any(Function));
    });
  });

  describe('deletePhoto()', () => {
    beforeEach(() => {
      photoManager = new PhotoManager();
    });

    it('should delete photo successfully', async () => {
      APIClient.request.mockResolvedValue({ success: true });

      await photoManager.deletePhoto('1');

      expect(global.confirm).toHaveBeenCalledWith(
        'Are you sure you want to delete this photo? This action cannot be undone.'
      );
      expect(APIClient.request).toHaveBeenCalledWith(
        '/api/tasks/123/images/1/',
        expect.objectContaining({ method: 'DELETE' })
      );
    });

    it('should remove photo from UI after successful delete', async () => {
      APIClient.request.mockResolvedValue({ success: true });
      const removeSpy = jest.spyOn(photoManager, 'removePhotoFromUI');

      await photoManager.deletePhoto('1');

      expect(removeSpy).toHaveBeenCalledWith('1');
    });

    it('should show success notification', async () => {
      APIClient.request.mockResolvedValue({ success: true });
      const showNotificationSpy = jest.spyOn(photoManager, 'showNotification');

      await photoManager.deletePhoto('1');

      expect(showNotificationSpy).toHaveBeenCalledWith(
        'Photo deleted successfully!',
        'success'
      );
    });

    it('should not delete if user cancels confirmation', async () => {
      global.confirm.mockReturnValue(false);

      await photoManager.deletePhoto('1');

      expect(APIClient.request).not.toHaveBeenCalled();
    });

    it('should handle delete errors', async () => {
      const error = new Error('Delete failed');
      APIClient.request.mockRejectedValue(error);
      const showNotificationSpy = jest.spyOn(photoManager, 'showNotification');

      await photoManager.deletePhoto('1');

      expect(showNotificationSpy).toHaveBeenCalledWith(
        'Failed to delete photo: Delete failed',
        'error'
      );
    });

    it('should handle missing photo ID', async () => {
      const consoleSpy = jest.spyOn(console, 'error').mockImplementation();

      await photoManager.deletePhoto(null);

      expect(consoleSpy).toHaveBeenCalledWith('Photo ID is required');
      expect(APIClient.request).not.toHaveBeenCalled();
      
      consoleSpy.mockRestore();
    });
  });

  describe('archivePhoto()', () => {
    beforeEach(() => {
      photoManager = new PhotoManager();
    });

    it('should archive photo successfully', async () => {
      APIClient.request.mockResolvedValue({
        success: true,
        id: 1,
        photo_status: 'archived'
      });

      await photoManager.archivePhoto('1');

      expect(APIClient.request).toHaveBeenCalledWith(
        '/api/tasks/123/images/1/',
        expect.objectContaining({
          method: 'PATCH',
          body: JSON.stringify({ photo_status: 'archived' })
        })
      );
    });

    it('should update photo status in UI', async () => {
      APIClient.request.mockResolvedValue({ success: true, id: 1 });
      const updateSpy = jest.spyOn(photoManager, 'updatePhotoStatusUI');

      await photoManager.archivePhoto('1');

      expect(updateSpy).toHaveBeenCalledWith('1', 'archived');
    });

    it('should show success notification', async () => {
      APIClient.request.mockResolvedValue({ success: true, id: 1 });
      const showNotificationSpy = jest.spyOn(photoManager, 'showNotification');

      await photoManager.archivePhoto('1');

      expect(showNotificationSpy).toHaveBeenCalledWith('Photo archived!', 'success');
    });

    it('should handle archive errors', async () => {
      const error = new Error('Archive failed');
      APIClient.request.mockRejectedValue(error);
      const showNotificationSpy = jest.spyOn(photoManager, 'showNotification');

      await photoManager.archivePhoto('1');

      expect(showNotificationSpy).toHaveBeenCalledWith(
        'Failed to archive photo: Archive failed',
        'error'
      );
    });

    it('should handle missing photo ID', async () => {
      const consoleSpy = jest.spyOn(console, 'error').mockImplementation();

      await photoManager.archivePhoto(null);

      expect(consoleSpy).toHaveBeenCalledWith('Photo ID is required');
      expect(APIClient.request).not.toHaveBeenCalled();
      
      consoleSpy.mockRestore();
    });
  });

  describe('removePhotoFromUI()', () => {
    beforeEach(() => {
      photoManager = new PhotoManager();
      jest.useFakeTimers();
    });

    afterEach(() => {
      jest.useRealTimers();
    });

    it('should remove photo element from DOM', () => {
      const photoElement = mockContainer.querySelector('[data-photo-id="1"]');
      expect(photoElement).not.toBeNull();

      photoManager.removePhotoFromUI('1');

      // Fast-forward animation
      jest.advanceTimersByTime(300);

      const removedPhoto = mockContainer.querySelector('[data-photo-id="1"]');
      expect(removedPhoto).toBeNull();
    });

    it('should apply fade-out animation', () => {
      const photoElement = mockContainer.querySelector('[data-photo-id="1"]');

      photoManager.removePhotoFromUI('1');

      expect(photoElement.style.opacity).toBe('0');
      expect(photoElement.style.transform).toBe('scale(0.8)');
    });

    it('should check for empty gallery after removal', () => {
      const checkEmptySpy = jest.spyOn(photoManager, 'checkEmptyGallery');

      photoManager.removePhotoFromUI('1');
      jest.advanceTimersByTime(300);

      expect(checkEmptySpy).toHaveBeenCalled();
    });
  });

  describe('updatePhotoStatusUI()', () => {
    beforeEach(() => {
      photoManager = new PhotoManager();
    });

    it('should update status badge text', () => {
      photoManager.updatePhotoStatusUI('1', 'approved');

      const statusBadge = mockContainer.querySelector('[data-photo-id="1"] .photo-status');
      expect(statusBadge.textContent).toBe('Approved');
    });

    it('should update status badge class', () => {
      photoManager.updatePhotoStatusUI('1', 'rejected');

      const statusBadge = mockContainer.querySelector('[data-photo-id="1"] .photo-status');
      expect(statusBadge.className).toBe('photo-status status-rejected');
    });

    it('should update data attribute', () => {
      photoManager.updatePhotoStatusUI('1', 'archived');

      const photoElement = mockContainer.querySelector('[data-photo-id="1"]');
      expect(photoElement.dataset.photoStatus).toBe('archived');
    });

    it('should handle missing photo element', () => {
      photoManager.updatePhotoStatusUI('999', 'approved');
      // Should not throw error
    });
  });

  describe('checkEmptyGallery()', () => {
    beforeEach(() => {
      photoManager = new PhotoManager();
    });

    it('should show empty state when no photos', () => {
      mockContainer.innerHTML = '';

      photoManager.checkEmptyGallery();

      const emptyState = mockContainer.querySelector('.empty-gallery-state');
      expect(emptyState).not.toBeNull();
      expect(emptyState.textContent).toContain('No photos in this gallery');
    });

    it('should not show empty state when photos exist', () => {
      photoManager.checkEmptyGallery();

      const emptyState = mockContainer.querySelector('.empty-gallery-state');
      expect(emptyState).toBeNull();
    });
  });

  describe('uploadPhotos()', () => {
    beforeEach(() => {
      photoManager = new PhotoManager();
    });

    it('should upload single photo', async () => {
      const mockFile = new File(['photo'], 'test.jpg', { type: 'image/jpeg' });
      
      APIClient.upload.mockResolvedValue({
        success: true,
        id: 101,
        image_url: '/media/test.jpg',
        photo_type: 'general'
      });

      const results = await photoManager.uploadPhotos([mockFile], 'general');

      expect(APIClient.upload).toHaveBeenCalledTimes(1);
      expect(results).toHaveLength(1);
    });

    it('should upload multiple photos', async () => {
      const mockFiles = [
        new File(['photo1'], 'test1.jpg', { type: 'image/jpeg' }),
        new File(['photo2'], 'test2.jpg', { type: 'image/jpeg' }),
        new File(['photo3'], 'test3.jpg', { type: 'image/jpeg' })
      ];

      APIClient.upload.mockResolvedValue({
        success: true,
        id: 101,
        image_url: '/media/test.jpg'
      });

      const results = await photoManager.uploadPhotos(mockFiles, 'before');

      expect(APIClient.upload).toHaveBeenCalledTimes(3);
      expect(results).toHaveLength(3);
    });

    it('should show success notification', async () => {
      const mockFiles = [new File(['photo'], 'test.jpg', { type: 'image/jpeg' })];
      APIClient.upload.mockResolvedValue({ success: true, id: 101, image_url: '/test.jpg' });
      const showNotificationSpy = jest.spyOn(photoManager, 'showNotification');

      await photoManager.uploadPhotos(mockFiles, 'general');

      expect(showNotificationSpy).toHaveBeenCalledWith(
        '1 photo(s) uploaded successfully!',
        'success'
      );
    });

    it('should handle upload errors', async () => {
      const mockFiles = [new File(['photo'], 'test.jpg', { type: 'image/jpeg' })];
      const error = new Error('Upload failed');
      APIClient.upload.mockRejectedValue(error);
      const showNotificationSpy = jest.spyOn(photoManager, 'showNotification');

      await expect(photoManager.uploadPhotos(mockFiles, 'general')).rejects.toThrow('Upload failed');

      expect(showNotificationSpy).toHaveBeenCalledWith(
        'Upload failed: Upload failed',
        'error'
      );
    });

    it('should handle missing files', async () => {
      const consoleSpy = jest.spyOn(console, 'error').mockImplementation();

      await photoManager.uploadPhotos([], 'general');

      expect(consoleSpy).toHaveBeenCalledWith('No files provided for upload');
      expect(APIClient.upload).not.toHaveBeenCalled();
      
      consoleSpy.mockRestore();
    });
  });

  describe('uploadSinglePhoto()', () => {
    beforeEach(() => {
      photoManager = new PhotoManager();
    });

    it('should upload photo with correct form data', async () => {
      const mockFile = new File(['photo'], 'test.jpg', { type: 'image/jpeg' });
      
      APIClient.upload.mockResolvedValue({
        success: true,
        id: 101,
        image_url: '/media/test.jpg'
      });

      await photoManager.uploadSinglePhoto(mockFile, 'before');

      expect(APIClient.upload).toHaveBeenCalledWith(
        '/api/staff/photos/upload/?task=123',
        expect.any(FormData)
      );
    });

    it('should add photo to gallery after upload', async () => {
      const mockFile = new File(['photo'], 'test.jpg', { type: 'image/jpeg' });
      const photoData = {
        success: true,
        id: 101,
        image_url: '/media/test.jpg',
        photo_type: 'before'
      };
      
      APIClient.upload.mockResolvedValue(photoData);
      const addPhotoSpy = jest.spyOn(photoManager, 'addPhotoToGallery');

      await photoManager.uploadSinglePhoto(mockFile, 'before');

      expect(addPhotoSpy).toHaveBeenCalledWith(photoData);
    });

    it('should handle upload failure', async () => {
      const mockFile = new File(['photo'], 'test.jpg', { type: 'image/jpeg' });
      const error = new Error('Network error');
      
      APIClient.upload.mockRejectedValue(error);

      await expect(photoManager.uploadSinglePhoto(mockFile, 'general')).rejects.toThrow('Network error');
    });
  });

  describe('addPhotoToGallery()', () => {
    beforeEach(() => {
      photoManager = new PhotoManager();
      jest.useFakeTimers();
    });

    afterEach(() => {
      jest.useRealTimers();
    });

    it('should add photo to gallery', () => {
      const photoData = {
        id: 103,
        image_url: '/media/new-photo.jpg',
        photo_type: 'after',
        photo_status: 'pending',
        description: 'Test description'
      };

      photoManager.addPhotoToGallery(photoData);

      const newPhoto = mockContainer.querySelector('[data-photo-id="103"]');
      expect(newPhoto).not.toBeNull();
    });

    it('should remove empty state before adding photo', () => {
      mockContainer.innerHTML = '<div class="empty-gallery-state">Empty</div>';

      const photoData = {
        id: 103,
        image_url: '/media/new-photo.jpg',
        photo_type: 'general',
        photo_status: 'pending'
      };

      photoManager.addPhotoToGallery(photoData);

      const emptyState = mockContainer.querySelector('.empty-gallery-state');
      expect(emptyState).toBeNull();
    });

    it('should add photo at beginning of gallery', () => {
      const photoData = {
        id: 103,
        image_url: '/media/new-photo.jpg',
        photo_type: 'general',
        photo_status: 'pending'
      };

      photoManager.addPhotoToGallery(photoData);

      const firstPhoto = mockContainer.querySelector('.gallery-photo-item');
      expect(firstPhoto.dataset.photoId).toBe('103');
    });

    it('should apply entrance animation', () => {
      const photoData = {
        id: 103,
        image_url: '/media/new-photo.jpg',
        photo_type: 'general',
        photo_status: 'pending'
      };

      photoManager.addPhotoToGallery(photoData);

      const newPhoto = mockContainer.querySelector('[data-photo-id="103"]');
      expect(newPhoto.style.opacity).toBe('0');
      expect(newPhoto.style.transform).toBe('scale(0.8)');

      jest.advanceTimersByTime(10);

      expect(newPhoto.style.opacity).toBe('1');
      expect(newPhoto.style.transform).toBe('scale(1)');
    });

    it('should include description if provided', () => {
      const photoData = {
        id: 103,
        image_url: '/media/new-photo.jpg',
        photo_type: 'general',
        photo_status: 'pending',
        description: 'Test description'
      };

      photoManager.addPhotoToGallery(photoData);

      const description = mockContainer.querySelector('[data-photo-id="103"] .photo-description');
      expect(description).not.toBeNull();
      expect(description.textContent).toBe('Test description');
    });
  });

  describe('filterPhotosByType()', () => {
    beforeEach(() => {
      photoManager = new PhotoManager();
    });

    it('should show only before photos', () => {
      photoManager.filterPhotosByType('before');

      const beforePhoto = mockContainer.querySelector('[data-photo-type="before"]');
      const afterPhoto = mockContainer.querySelector('[data-photo-type="after"]');

      expect(beforePhoto.style.display).toBe('block');
      expect(afterPhoto.style.display).toBe('none');
    });

    it('should show only after photos', () => {
      photoManager.filterPhotosByType('after');

      const beforePhoto = mockContainer.querySelector('[data-photo-type="before"]');
      const afterPhoto = mockContainer.querySelector('[data-photo-type="after"]');

      expect(beforePhoto.style.display).toBe('none');
      expect(afterPhoto.style.display).toBe('block');
    });

    it('should show all photos', () => {
      photoManager.filterPhotosByType('all');

      const allPhotos = mockContainer.querySelectorAll('.gallery-photo-item');
      allPhotos.forEach(photo => {
        expect(photo.style.display).toBe('block');
      });
    });
  });

  describe('filterPhotosByStatus()', () => {
    beforeEach(() => {
      photoManager = new PhotoManager();
    });

    it('should show only approved photos', () => {
      photoManager.filterPhotosByStatus('approved');

      const approvedPhoto = mockContainer.querySelector('[data-photo-status="approved"]');
      const pendingPhoto = mockContainer.querySelector('[data-photo-status="pending"]');

      expect(approvedPhoto.style.display).toBe('block');
      expect(pendingPhoto.style.display).toBe('none');
    });

    it('should show only pending photos', () => {
      photoManager.filterPhotosByStatus('pending');

      const approvedPhoto = mockContainer.querySelector('[data-photo-status="approved"]');
      const pendingPhoto = mockContainer.querySelector('[data-photo-status="pending"]');

      expect(approvedPhoto.style.display).toBe('none');
      expect(pendingPhoto.style.display).toBe('block');
    });

    it('should show all photos', () => {
      photoManager.filterPhotosByStatus('all');

      const allPhotos = mockContainer.querySelectorAll('.gallery-photo-item');
      allPhotos.forEach(photo => {
        expect(photo.style.display).toBe('block');
      });
    });
  });

  describe('Event Delegation', () => {
    beforeEach(() => {
      photoManager = new PhotoManager();
    });

    it('should open photo modal on image click', () => {
      const photoImg = mockContainer.querySelector('[data-photo-id="1"] img');
      photoImg.click();

      expect(window.openPhotoModal).toHaveBeenCalledWith('/media/photo1.jpg', '1');
    });

    it('should handle delete button click', async () => {
      APIClient.request.mockResolvedValue({ success: true });
      const deleteSpy = jest.spyOn(photoManager, 'deletePhoto');

      const deleteBtn = mockContainer.querySelector('[data-photo-id="1"].btn-delete-photo');
      deleteBtn.click();

      await new Promise(resolve => setTimeout(resolve, 0));

      expect(deleteSpy).toHaveBeenCalledWith('1');
    });

    it('should handle archive button click', async () => {
      APIClient.request.mockResolvedValue({ success: true, id: 1 });
      const archiveSpy = jest.spyOn(photoManager, 'archivePhoto');

      const archiveBtn = mockContainer.querySelector('[data-photo-id="1"].btn-archive-photo');
      archiveBtn.click();

      await new Promise(resolve => setTimeout(resolve, 0));

      expect(archiveSpy).toHaveBeenCalledWith('1');
    });
  });

  describe('Global Bridge Functions', () => {
    beforeEach(() => {
      photoManager = new PhotoManager();
      window.photoManagerInstance = photoManager;
    });

    it('should expose deletePhoto globally', () => {
      expect(window.deletePhoto).toBeDefined();
      expect(typeof window.deletePhoto).toBe('function');
    });

    it('should call deletePhoto through global bridge', async () => {
      APIClient.request.mockResolvedValue({ success: true });
      const deleteSpy = jest.spyOn(photoManager, 'deletePhoto');

      await window.deletePhoto('1');

      expect(deleteSpy).toHaveBeenCalledWith('1');
    });

    it('should expose archivePhoto globally', () => {
      expect(window.archivePhoto).toBeDefined();
      expect(typeof window.archivePhoto).toBe('function');
    });

    it('should call archivePhoto through global bridge', async () => {
      APIClient.request.mockResolvedValue({ success: true, id: 1 });
      const archiveSpy = jest.spyOn(photoManager, 'archivePhoto');

      await window.archivePhoto('1');

      expect(archiveSpy).toHaveBeenCalledWith('1');
    });
  });

  describe('Helper Methods', () => {
    beforeEach(() => {
      photoManager = new PhotoManager();
    });

    it('should get correct status display', () => {
      expect(photoManager.getStatusDisplay('pending')).toBe('Pending Review');
      expect(photoManager.getStatusDisplay('approved')).toBe('Approved');
      expect(photoManager.getStatusDisplay('rejected')).toBe('Rejected');
      expect(photoManager.getStatusDisplay('archived')).toBe('Archived');
    });

    it('should get correct photo type display', () => {
      expect(photoManager.getPhotoTypeDisplay('before')).toBe('Before');
      expect(photoManager.getPhotoTypeDisplay('after')).toBe('After');
      expect(photoManager.getPhotoTypeDisplay('during')).toBe('During');
      expect(photoManager.getPhotoTypeDisplay('issue')).toBe('Issue');
      expect(photoManager.getPhotoTypeDisplay('general')).toBe('General');
    });
  });

  describe('Notification System', () => {
    beforeEach(() => {
      photoManager = new PhotoManager();
      jest.useFakeTimers();
    });

    afterEach(() => {
      jest.useRealTimers();
    });

    it('should show notification', () => {
      photoManager.showNotification('Test message', 'success');

      const notification = document.querySelector('.notification-success');
      expect(notification).not.toBeNull();
      expect(notification.textContent).toBe('Test message');
    });

    it('should auto-remove notification after 3 seconds', () => {
      photoManager.showNotification('Test message', 'info');

      const notification = document.querySelector('.notification-info');
      expect(notification).not.toBeNull();

      jest.advanceTimersByTime(3300);

      const notificationGone = document.querySelector('.notification-info');
      expect(notificationGone).toBeNull();
    });
  });
});
