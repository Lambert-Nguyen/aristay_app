/**
 * Photo Manager Module
 * Handles photo gallery display and photo operations (view, delete, archive)
 */

import { APIClient } from '../core/api-client.js';

export class PhotoManager {
  constructor(container) {
    this.container = container || document.querySelector('.photo-gallery-grid');
    this.taskId = this.getTaskId();
    
    if (!this.container) {
      console.warn('Photo gallery container not found');
      return;
    }
    
    this.initEventListeners();
    console.log('✓ PhotoManager initialized');
  }

  getTaskId() {
    const taskContainer = document.getElementById('taskDetailContainer') || 
                         document.querySelector('[data-task-id]');
    return taskContainer?.dataset.taskId || null;
  }

  initEventListeners() {
    // Event delegation for photo clicks
    this.container.addEventListener('click', (e) => {
      const photoImg = e.target.closest('.gallery-photo-item img');
      if (photoImg) {
        const photoUrl = photoImg.dataset.photoUrl;
        const photoId = photoImg.dataset.photoId;
        
        if (photoUrl && photoId) {
          window.openPhotoModal(photoUrl, photoId);
        }
      }
    });

    // Event delegation for delete buttons
    this.container.addEventListener('click', async (e) => {
      const deleteBtn = e.target.closest('.btn-delete-photo');
      if (deleteBtn) {
        e.stopPropagation(); // Prevent triggering photo modal
        const photoId = deleteBtn.dataset.photoId;
        await this.deletePhoto(photoId);
      }
    });

    // Event delegation for archive buttons
    this.container.addEventListener('click', async (e) => {
      const archiveBtn = e.target.closest('.btn-archive-photo');
      if (archiveBtn) {
        e.stopPropagation();
        const photoId = archiveBtn.dataset.photoId;
        await this.archivePhoto(photoId);
      }
    });
  }

  async deletePhoto(photoId) {
    if (!photoId) {
      console.error('Photo ID is required');
      return;
    }

    if (!confirm('Are you sure you want to delete this photo? This action cannot be undone.')) {
      return;
    }

    console.log(`Deleting photo ${photoId}`);

    try {
      const response = await APIClient.request(
        `/api/tasks/${this.taskId}/images/${photoId}/`,
        { method: 'DELETE' }
      );

      if (response.success) {
        console.log('✅ Photo deleted successfully');
        
        // Remove photo from UI
        this.removePhotoFromUI(photoId);
        
        this.showNotification('Photo deleted successfully!', 'success');
      }
    } catch (error) {
      console.error('❌ Error deleting photo:', error);
      this.showNotification(`Failed to delete photo: ${error.message}`, 'error');
    }
  }

  async archivePhoto(photoId) {
    if (!photoId) {
      console.error('Photo ID is required');
      return;
    }

    console.log(`Archiving photo ${photoId}`);

    try {
      const response = await APIClient.request(
        `/api/tasks/${this.taskId}/images/${photoId}/`,
        {
          method: 'PATCH',
          body: JSON.stringify({ photo_status: 'archived' })
        }
      );

      if (response.success || response.id) {
        console.log('✅ Photo archived successfully');
        
        // Update photo status in UI
        this.updatePhotoStatusUI(photoId, 'archived');
        
        this.showNotification('Photo archived!', 'success');
      }
    } catch (error) {
      console.error('❌ Error archiving photo:', error);
      this.showNotification(`Failed to archive photo: ${error.message}`, 'error');
    }
  }

  removePhotoFromUI(photoId) {
    const photoElement = this.container.querySelector(`[data-photo-id="${photoId}"]`);
    if (photoElement) {
      // Add fade-out animation
      photoElement.style.transition = 'opacity 0.3s ease-out, transform 0.3s ease-out';
      photoElement.style.opacity = '0';
      photoElement.style.transform = 'scale(0.8)';
      
      // Remove after animation
      setTimeout(() => {
        photoElement.remove();
        console.log('✓ Photo removed from UI');
        
        // Check if gallery is empty
        this.checkEmptyGallery();
      }, 300);
    }
  }

  updatePhotoStatusUI(photoId, newStatus) {
    const photoElement = this.container.querySelector(`[data-photo-id="${photoId}"]`);
    if (!photoElement) return;

    // Update status badge
    const statusBadge = photoElement.querySelector('.photo-status');
    if (statusBadge) {
      statusBadge.textContent = this.getStatusDisplay(newStatus);
      statusBadge.className = `photo-status status-${newStatus}`;
    }

    // Update data attribute
    photoElement.dataset.photoStatus = newStatus;

    console.log(`✓ Photo ${photoId} status updated to ${newStatus}`);
  }

  getStatusDisplay(status) {
    const statusMap = {
      'pending': 'Pending Review',
      'approved': 'Approved',
      'rejected': 'Rejected',
      'archived': 'Archived'
    };
    return statusMap[status] || status;
  }

  checkEmptyGallery() {
    const photos = this.container.querySelectorAll('.gallery-photo-item');
    if (photos.length === 0) {
      // Show empty state
      const emptyState = document.createElement('div');
      emptyState.className = 'empty-gallery-state';
      emptyState.innerHTML = `
        <div class="empty-icon">📷</div>
        <p class="empty-message">No photos in this gallery</p>
      `;
      this.container.appendChild(emptyState);
    }
  }

  async uploadPhotos(files, photoType = 'general') {
    if (!files || files.length === 0) {
      console.error('No files provided for upload');
      return;
    }

    console.log(`Uploading ${files.length} photo(s) of type: ${photoType}`);

    const results = [];

    try {
      for (const file of files) {
        const result = await this.uploadSinglePhoto(file, photoType);
        results.push(result);
      }

      this.showNotification(`${files.length} photo(s) uploaded successfully!`, 'success');
      return results;
    } catch (error) {
      console.error('❌ Error uploading photos:', error);
      this.showNotification(`Upload failed: ${error.message}`, 'error');
      throw error;
    }
  }

  async uploadSinglePhoto(file, photoType = 'general') {
    const formData = new FormData();
    formData.append('image', file);
    formData.append('photo_type', photoType);
    formData.append('task_id', this.taskId);

    try {
      const response = await APIClient.upload(
        `/api/staff/photos/upload/?task=${this.taskId}`,
        formData
      );

      if (response.success || response.id) {
        console.log('✅ Photo uploaded:', file.name);
        
        // Add photo to gallery UI
        this.addPhotoToGallery(response);
        
        return response;
      }
    } catch (error) {
      console.error(`❌ Failed to upload ${file.name}:`, error);
      throw error;
    }
  }

  addPhotoToGallery(photoData) {
    // Remove empty state if exists
    const emptyState = this.container.querySelector('.empty-gallery-state');
    if (emptyState) {
      emptyState.remove();
    }

    // Create photo element
    const photoDiv = document.createElement('div');
    photoDiv.className = 'gallery-photo-item';
    photoDiv.dataset.photoType = photoData.photo_type;
    photoDiv.dataset.photoId = photoData.id;
    photoDiv.dataset.photoStatus = photoData.photo_status || 'pending';

    const img = document.createElement('img');
    img.src = photoData.image_url || photoData.url;
    img.alt = `${photoData.photo_type} photo`;
    img.dataset.photoUrl = photoData.image_url || photoData.url;
    img.dataset.photoId = photoData.id;

    const photoMeta = document.createElement('div');
    photoMeta.className = 'photo-meta';

    const photoHeader = document.createElement('div');
    photoHeader.className = 'photo-header';

    const typeBadge = document.createElement('span');
    typeBadge.className = 'photo-type-badge';
    typeBadge.textContent = this.getPhotoTypeDisplay(photoData.photo_type);

    const statusBadge = document.createElement('span');
    statusBadge.className = `photo-status status-${photoData.photo_status || 'pending'}`;
    statusBadge.textContent = this.getStatusDisplay(photoData.photo_status || 'pending');

    photoHeader.appendChild(typeBadge);
    photoHeader.appendChild(statusBadge);
    photoMeta.appendChild(photoHeader);

    if (photoData.description) {
      const description = document.createElement('p');
      description.className = 'photo-description';
      description.textContent = photoData.description;
      photoMeta.appendChild(description);
    }

    photoDiv.appendChild(img);
    photoDiv.appendChild(photoMeta);

    // Add to beginning of gallery (newest first)
    this.container.insertBefore(photoDiv, this.container.firstChild);

    // Add entrance animation
    photoDiv.style.opacity = '0';
    photoDiv.style.transform = 'scale(0.8)';
    photoDiv.style.transition = 'opacity 0.3s ease-out, transform 0.3s ease-out';
    
    setTimeout(() => {
      photoDiv.style.opacity = '1';
      photoDiv.style.transform = 'scale(1)';
    }, 10);

    console.log('✓ Photo added to gallery UI');
  }

  getPhotoTypeDisplay(photoType) {
    const typeMap = {
      'before': 'Before',
      'after': 'After',
      'during': 'During',
      'issue': 'Issue',
      'general': 'General'
    };
    return typeMap[photoType] || photoType;
  }

  filterPhotosByType(photoType) {
    const allPhotos = this.container.querySelectorAll('.gallery-photo-item');
    
    allPhotos.forEach(photo => {
      if (photoType === 'all' || photo.dataset.photoType === photoType) {
        photo.style.display = 'block';
      } else {
        photo.style.display = 'none';
      }
    });

    console.log(`✓ Gallery filtered by type: ${photoType}`);
  }

  filterPhotosByStatus(status) {
    const allPhotos = this.container.querySelectorAll('.gallery-photo-item');
    
    allPhotos.forEach(photo => {
      if (status === 'all' || photo.dataset.photoStatus === status) {
        photo.style.display = 'block';
      } else {
        photo.style.display = 'none';
      }
    });

    console.log(`✓ Gallery filtered by status: ${status}`);
  }

  showNotification(message, type = 'info') {
    // Create notification element
    const notification = document.createElement('div');
    notification.className = `notification notification-${type}`;
    notification.textContent = message;
    notification.style.cssText = `
      position: fixed;
      top: 20px;
      right: 20px;
      padding: 16px 24px;
      background: ${type === 'success' ? '#10b981' : type === 'error' ? '#ef4444' : '#3b82f6'};
      color: white;
      border-radius: 8px;
      box-shadow: 0 4px 6px rgba(0, 0, 0, 0.1);
      z-index: 10000;
      animation: slideIn 0.3s ease-out;
    `;

    document.body.appendChild(notification);

    // Auto-remove after 3 seconds
    setTimeout(() => {
      notification.style.animation = 'slideOut 0.3s ease-out';
      setTimeout(() => {
        notification.remove();
      }, 300);
    }, 3000);
  }
}

// Global bridge functions for backward compatibility
if (typeof window !== 'undefined') {
  window.photoManagerInstance = null;

  window.deletePhoto = function(photoId) {
    if (window.photoManagerInstance) {
      window.photoManagerInstance.deletePhoto(photoId);
    }
  };

  window.archivePhoto = function(photoId) {
    if (window.photoManagerInstance) {
      window.photoManagerInstance.archivePhoto(photoId);
    }
  };
}
