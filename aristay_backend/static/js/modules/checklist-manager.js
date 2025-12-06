/**
 * Checklist Manager Module
 * Handles checklist item completion, photo uploads, and notes management
 */

import { APIClient } from '../core/api-client.js';

export class ChecklistManager {
  constructor(container) {
    this.container = container || document.querySelector('.checklist-container');
    this.taskId = this.getTaskId();
    
    if (!this.container) {
      console.warn('Checklist container not found');
      return;
    }
    
    this.initEventListeners();
    console.log('✓ ChecklistManager initialized');
  }

  getTaskId() {
    const taskContainer = document.getElementById('taskDetailContainer') || 
                         document.querySelector('[data-task-id]');
    return taskContainer?.dataset.taskId || null;
  }

  initEventListeners() {
    // Event delegation for checkbox changes
    this.container.addEventListener('change', async (e) => {
      const checkbox = e.target.closest('.checklist-checkbox');
      if (checkbox) {
        const responseId = checkbox.dataset.responseId;
        const isCompleted = checkbox.checked;
        await this.updateChecklistItem(responseId, isCompleted);
      }
    });

    // Event delegation for photo uploads
    this.container.addEventListener('change', async (e) => {
      const fileInput = e.target.closest('input[type="file"]');
      if (fileInput && fileInput.classList.contains('photo-upload-input')) {
        await this.handlePhotoUpload(e);
      }
    });

    // Event delegation for notes buttons
    this.container.addEventListener('click', (e) => {
      const notesBtn = e.target.closest('.btn-notes');
      if (notesBtn) {
        const responseId = notesBtn.dataset.responseId;
        this.openNotesModal(responseId);
      }
    });
  }

  async updateChecklistItem(responseId, isCompleted) {
    if (!responseId) {
      console.error('Response ID is required');
      return;
    }

    console.log(`Updating checklist item ${responseId} to ${isCompleted ? 'completed' : 'incomplete'}`);

    try {
      const response = await APIClient.post(
        `/api/staff/checklist/${responseId}/update/`,
        { completed: isCompleted }
      );

      if (response.success || response.id) {
        console.log('✅ Checklist item updated successfully');
        
        // Update UI
        this.updateChecklistItemUI(responseId, isCompleted);
        this.updateProgressOverview();
        
        // Show success notification
        this.showNotification('Checklist item updated!', 'success');
      }
    } catch (error) {
      console.error('❌ Error updating checklist item:', error);
      
      // Revert checkbox state
      const checkbox = this.container.querySelector(
        `.checklist-checkbox[data-response-id="${responseId}"]`
      );
      if (checkbox) {
        checkbox.checked = !isCompleted;
      }
      
      this.showNotification(`Failed to update: ${error.message}`, 'error');
    }
  }

  updateChecklistItemUI(responseId, isCompleted) {
    const checklistItem = this.container.querySelector(
      `.checklist-item[data-response-id="${responseId}"]`
    );
    
    if (!checklistItem) return;

    // Toggle completed class
    if (isCompleted) {
      checklistItem.classList.add('completed');
    } else {
      checklistItem.classList.remove('completed');
    }

    // Update status text
    const statusText = checklistItem.querySelector('.checklist-status');
    if (statusText) {
      statusText.textContent = isCompleted ? '✅ Completed' : '⏸️ Not Complete';
    }

    // Update completion timestamp
    if (isCompleted) {
      const timestamp = new Date().toLocaleString();
      const timestampEl = checklistItem.querySelector('.completion-timestamp');
      if (timestampEl) {
        timestampEl.textContent = `Completed: ${timestamp}`;
        timestampEl.style.display = 'block';
      }
    }
  }

  updateProgressOverview() {
    // Count completed and total items
    const checkboxes = this.container.querySelectorAll('.checklist-checkbox');
    const completedCheckboxes = this.container.querySelectorAll('.checklist-checkbox:checked');
    
    const total = checkboxes.length;
    const completed = completedCheckboxes.length;
    const remaining = total - completed;
    const percentage = total > 0 ? Math.round((completed / total) * 100) : 0;

    // Update progress bar
    const progressFill = document.querySelector('.progress-fill');
    if (progressFill) {
      progressFill.style.width = `${percentage}%`;
    }

    // Update progress text
    const progressPercentage = document.querySelector('.progress-percentage');
    if (progressPercentage) {
      progressPercentage.textContent = `${percentage}%`;
    }

    const progressFraction = document.querySelector('.progress-fraction');
    if (progressFraction) {
      progressFraction.textContent = `${completed}/${total} completed`;
    }

    // Update detail counts
    const totalItemsEl = document.querySelector('.detail-value');
    if (totalItemsEl) {
      totalItemsEl.textContent = total;
    }

    const completedItemsEl = document.querySelectorAll('.detail-value')[1];
    if (completedItemsEl) {
      completedItemsEl.textContent = completed;
    }

    const remainingItemsEl = document.querySelectorAll('.detail-value')[2];
    if (remainingItemsEl) {
      remainingItemsEl.textContent = remaining;
    }

    // Update status message
    const statusMessage = document.querySelector('.status-message');
    if (statusMessage) {
      if (percentage === 100) {
        statusMessage.innerHTML = '🎉 All checklist items completed! You can now mark this task as complete.';
        statusMessage.className = 'status-message complete';
      } else {
        statusMessage.innerHTML = `Complete all required checklist items to finish this task.<br>Progress: ${percentage}%`;
        statusMessage.className = 'status-message incomplete';
      }
    }

    console.log(`✓ Progress updated: ${completed}/${total} (${percentage}%)`);
  }

  async handlePhotoUpload(event) {
    const input = event.target;
    const files = input.files;
    
    if (!files || files.length === 0) {
      return;
    }

    // Get response ID from parent checklist item
    const checklistItem = input.closest('.checklist-item');
    const responseId = checklistItem?.dataset.responseId;

    if (!responseId) {
      console.error('Cannot upload photo: Response ID not found');
      this.showNotification('Upload failed: Invalid checklist item', 'error');
      return;
    }

    console.log(`Uploading ${files.length} photo(s) for checklist item ${responseId}`);

    try {
      for (const file of files) {
        await this.uploadSinglePhoto(responseId, file);
      }

      // Clear file input
      input.value = '';
      
      this.showNotification('Photos uploaded successfully!', 'success');
    } catch (error) {
      console.error('❌ Error uploading photos:', error);
      this.showNotification(`Upload failed: ${error.message}`, 'error');
    }
  }

  async uploadSinglePhoto(responseId, file) {
    const formData = new FormData();
    formData.append('photo', file);
    formData.append('checklist_response_id', responseId);
    formData.append('task_id', this.taskId);

    try {
      const response = await APIClient.upload('/api/staff/checklist/photo/upload/', formData);
      
      if (response.success || response.id) {
        console.log('✅ Photo uploaded:', file.name);
        
        // Add photo to UI
        this.addPhotoToChecklistItem(responseId, response);
        
        return response;
      }
    } catch (error) {
      console.error(`❌ Failed to upload ${file.name}:`, error);
      throw error;
    }
  }

  addPhotoToChecklistItem(responseId, photoData) {
    const checklistItem = this.container.querySelector(
      `.checklist-item[data-response-id="${responseId}"]`
    );
    
    if (!checklistItem) return;

    const photoGrid = checklistItem.querySelector('.photo-preview-grid');
    if (!photoGrid) return;

    // Create photo element
    const photoDiv = document.createElement('div');
    photoDiv.className = 'photo-item';
    photoDiv.dataset.photoId = photoData.id;

    const img = document.createElement('img');
    img.src = photoData.image_url || photoData.url;
    img.alt = 'Checklist photo';
    img.dataset.photoUrl = photoData.image_url || photoData.url;
    img.dataset.photoId = photoData.id;
    img.onclick = () => window.openPhotoModal(img.dataset.photoUrl, photoData.id);

    photoDiv.appendChild(img);
    photoGrid.appendChild(photoDiv);

    console.log('✓ Photo added to checklist item UI');
  }

  openNotesModal(responseId) {
    const modal = document.getElementById('noteModal');
    if (!modal) {
      console.error('Notes modal not found');
      return;
    }

    // Get current notes from checklist item
    const checklistItem = this.container.querySelector(
      `.checklist-item[data-response-id="${responseId}"]`
    );
    
    const currentNotes = checklistItem?.querySelector('.item-notes')?.textContent || '';

    // Set notes in modal
    const notesInput = modal.querySelector('.notes-input');
    if (notesInput) {
      notesInput.value = currentNotes;
    }

    // Store response ID for saving
    modal.dataset.responseId = responseId;

    // Show modal
    modal.style.display = 'block';
    document.body.style.overflow = 'hidden';

    // Focus on textarea
    if (notesInput) {
      notesInput.focus();
    }
  }

  async saveNotes(responseId, notes) {
    if (!responseId) {
      console.error('Response ID is required');
      return;
    }

    try {
      const response = await APIClient.post(
        `/api/staff/checklist/${responseId}/notes/`,
        { notes: notes.trim() }
      );

      if (response.success || response.id) {
        console.log('✅ Notes saved successfully');
        
        // Update UI
        this.updateNotesUI(responseId, notes);
        
        // Close modal
        this.closeModal();
        
        this.showNotification('Notes saved!', 'success');
      }
    } catch (error) {
      console.error('❌ Error saving notes:', error);
      this.showNotification(`Failed to save notes: ${error.message}`, 'error');
    }
  }

  updateNotesUI(responseId, notes) {
    const checklistItem = this.container.querySelector(
      `.checklist-item[data-response-id="${responseId}"]`
    );
    
    if (!checklistItem) return;

    const notesElement = checklistItem.querySelector('.item-notes');
    if (notesElement) {
      notesElement.textContent = notes;
      
      // Show/hide notes section based on content
      if (notes.trim()) {
        notesElement.style.display = 'block';
      } else {
        notesElement.style.display = 'none';
      }
    }
  }

  closeModal() {
    const modals = document.querySelectorAll('.note-modal');
    modals.forEach(modal => {
      modal.style.display = 'none';
    });
    document.body.style.overflow = '';
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
  window.checklistManagerInstance = null;

  window.updateChecklistItem = function(responseId, isCompleted) {
    if (window.checklistManagerInstance) {
      window.checklistManagerInstance.updateChecklistItem(responseId, isCompleted);
    }
  };

  window.uploadPhotos = function(responseId, inputElement) {
    if (window.checklistManagerInstance) {
      window.checklistManagerInstance.handlePhotoUpload({ target: inputElement });
    }
  };
}
