/**
 * Photo Modal Module
 * Handles photo viewing modal with approval/rejection functionality
 */

import { APIClient } from '../core/api-client.js';

export class PhotoModal {
  constructor(modalId = 'photoModal') {
    this.modalId = modalId;
    this.modal = null;
    this.currentPhotoId = null;
    this.currentPhotoUrl = null;
    this.taskId = null;
    
    this.init();
  }

  init() {
    // Wait for DOM to be ready
    if (document.readyState === 'loading') {
      document.addEventListener('DOMContentLoaded', () => this.setupModal());
    } else {
      this.setupModal();
    }
  }

  setupModal() {
    this.modal = document.getElementById(this.modalId);
    
    if (!this.modal) {
      console.warn('Photo modal not found in DOM');
      return;
    }

    // Get task ID from page
    const taskContainer = document.getElementById('taskDetailContainer') || 
                         document.querySelector('[data-task-id]');
    if (taskContainer) {
      this.taskId = taskContainer.dataset.taskId;
    }

    this.initEventListeners();
    console.log('Photo modal initialized');
  }

  initEventListeners() {
    if (!this.modal) return;

    // Close on background click
    this.modal.addEventListener('click', (e) => {
      if (e.target === this.modal) {
        this.close();
      }
    });

    // Close button
    const closeBtn = this.modal.querySelector('.close-modal');
    if (closeBtn) {
      closeBtn.addEventListener('click', () => this.close());
    }

    // Escape key to close
    document.addEventListener('keydown', (e) => {
      if (e.key === 'Escape' && this.isOpen()) {
        this.close();
      }
    });

    // Approval/rejection buttons (event delegation)
    this.modal.addEventListener('click', async (e) => {
      const approveBtn = e.target.closest('.btn-approve');
      const rejectBtn = e.target.closest('.btn-reject');
      
      if (approveBtn && this.currentPhotoId) {
        await this.approvePhoto(this.currentPhotoId);
      } else if (rejectBtn && this.currentPhotoId) {
        await this.rejectPhoto(this.currentPhotoId);
      }
    });
  }

  open(photoUrl, photoId) {
    if (!this.modal) {
      console.error('Modal not initialized');
      return;
    }

    console.log('Opening photo modal:', { photoUrl, photoId });

    this.currentPhotoUrl = photoUrl;
    this.currentPhotoId = photoId;

    // Set photo
    const modalPhoto = this.modal.querySelector('#modalPhoto');
    if (modalPhoto) {
      modalPhoto.src = photoUrl;
      modalPhoto.alt = 'Task photo';
    }

    // Update approval buttons with photo ID
    const approveBtn = this.modal.querySelector('.btn-approve');
    const rejectBtn = this.modal.querySelector('.btn-reject');
    
    if (approveBtn) {
      approveBtn.dataset.photoId = photoId;
    }
    
    if (rejectBtn) {
      rejectBtn.dataset.photoId = photoId;
    }

    // Show modal
    this.modal.style.display = 'block';
    document.body.style.overflow = 'hidden'; // Prevent background scroll
  }

  close() {
    if (!this.modal) return;

    this.modal.style.display = 'none';
    document.body.style.overflow = ''; // Restore scroll
    
    this.currentPhotoUrl = null;
    this.currentPhotoId = null;
    
    console.log('Photo modal closed');
  }

  isOpen() {
    return this.modal && this.modal.style.display === 'block';
  }

  async approvePhoto(photoId) {
    if (!confirm('Approve this photo?')) return;

    try {
      const response = await APIClient.request(
        `/api/tasks/${this.taskId}/images/${photoId}/`,
        {
          method: 'PATCH',
          body: JSON.stringify({ photo_status: 'approved' })
        }
      );

      if (response.success || response.id) {
        alert('Photo approved successfully!');
        this.close();
        location.reload(); // Reload to show updated status
      }
    } catch (error) {
      console.error('Error approving photo:', error);
      alert(`Failed to approve photo: ${error.message}`);
    }
  }

  async rejectPhoto(photoId) {
    const reason = prompt('Why are you rejecting this photo?');
    if (!reason || reason.trim() === '') return;

    try {
      const response = await APIClient.request(
        `/api/tasks/${this.taskId}/images/${photoId}/`,
        {
          method: 'PATCH',
          body: JSON.stringify({ 
            photo_status: 'rejected',
            rejection_reason: reason.trim()
          })
        }
      );

      if (response.success || response.id) {
        alert('Photo rejected successfully!');
        this.close();
        location.reload(); // Reload to show updated status
      }
    } catch (error) {
      console.error('Error rejecting photo:', error);
      alert(`Failed to reject photo: ${error.message}`);
    }
  }
}

// Global bridge function for backward compatibility with inline onclick handlers
if (typeof window !== 'undefined') {
  window._photoModalInstance = null;

  window.openPhotoModal = function(photoUrl, photoId) {
    console.log('Global openPhotoModal called:', { photoUrl, photoId });
    
    if (!window._photoModalInstance) {
      window._photoModalInstance = new PhotoModal();
    }
    
    window._photoModalInstance.open(photoUrl, photoId);
  };

  window.testPhotoModal = function() {
    console.log('Testing photo modal...');
    const testUrl = 'https://via.placeholder.com/800x600?text=Test+Photo';
    window.openPhotoModal(testUrl, 999);
  };
}
