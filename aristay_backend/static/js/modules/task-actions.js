/**
 * Task Actions Module
 * Handles all task CRUD operations and quick actions
 */

import { APIClient } from '../core/api-client.js';

export class TaskActions {
  constructor(taskId) {
    this.taskId = taskId;
    this.initEventListeners();
  }

  initEventListeners() {
    // Start task button
    const startBtn = document.querySelector('.btn-action.start-task');
    if (startBtn) {
      startBtn.addEventListener('click', () => this.startTask());
    }

    // Complete task button
    const completeBtn = document.querySelector('.btn-action.complete-task');
    if (completeBtn) {
      completeBtn.addEventListener('click', () => this.completeTask());
    }

    // Add note button
    const noteBtn = document.querySelector('.btn-action.add-note');
    if (noteBtn) {
      noteBtn.addEventListener('click', () => this.addNote());
    }

    // Share task button
    const shareBtn = document.querySelector('.btn-action.share-task');
    if (shareBtn) {
      shareBtn.addEventListener('click', () => this.shareTask());
    }

    // Report lost & found button
    const reportBtn = document.querySelector('.btn-action.report-lost-found');
    if (reportBtn) {
      reportBtn.addEventListener('click', () => this.reportLostFound());
    }

    // Duplicate task button (already has onclick, but can use event delegation)
    const duplicateBtn = document.querySelector('.btn-action.duplicate-task');
    if (duplicateBtn) {
      duplicateBtn.addEventListener('click', () => this.duplicateTask());
    }

    // Delete task button (already has onclick, but can use event delegation)
    const deleteBtn = document.querySelector('.btn-action.delete-task');
    if (deleteBtn) {
      deleteBtn.addEventListener('click', () => {
        const taskTitle = document.querySelector('.task-title')?.textContent || 'this task';
        this.deleteTask(taskTitle);
      });
    }
  }

  async startTask() {
    if (!confirm('Start this task now?')) return;

    try {
      const response = await APIClient.post(`/api/staff/tasks/${this.taskId}/start/`, {});
      
      if (response.success) {
        // Update UI
        this.updateTaskStatus('in-progress');
        alert('Task started successfully!');
        location.reload(); // Reload to show updated status
      }
    } catch (error) {
      console.error('Error starting task:', error);
      alert(`Failed to start task: ${error.message}`);
    }
  }

  async completeTask() {
    if (!confirm('Mark this task as complete?')) return;

    try {
      const response = await APIClient.post(`/api/staff/tasks/${this.taskId}/complete/`, {});
      
      if (response.success) {
        // Update UI
        this.updateTaskStatus('completed');
        alert('Task completed successfully!');
        location.reload(); // Reload to show updated status
      }
    } catch (error) {
      console.error('Error completing task:', error);
      alert(`Failed to complete task: ${error.message}`);
    }
  }

  async addNote() {
    const note = prompt('Add a note to this task:');
    if (!note || note.trim() === '') return;

    try {
      const response = await APIClient.post(`/api/staff/tasks/${this.taskId}/notes/`, {
        content: note.trim()
      });
      
      if (response.success) {
        alert('Note added successfully!');
        location.reload(); // Reload to show new note
      }
    } catch (error) {
      console.error('Error adding note:', error);
      alert(`Failed to add note: ${error.message}`);
    }
  }

  async shareTask() {
    // Share functionality - could be email, link copy, etc.
    const url = window.location.href;
    
    if (navigator.share) {
      try {
        await navigator.share({
          title: 'Task: ' + document.querySelector('.task-title')?.textContent,
          url: url
        });
      } catch (error) {
        console.error('Error sharing:', error);
        this.copyToClipboard(url);
      }
    } else {
      this.copyToClipboard(url);
    }
  }

  copyToClipboard(text) {
    if (navigator.clipboard) {
      navigator.clipboard.writeText(text).then(() => {
        alert('Task link copied to clipboard!');
      }).catch(err => {
        console.error('Failed to copy:', err);
        this.fallbackCopy(text);
      });
    } else {
      this.fallbackCopy(text);
    }
  }

  fallbackCopy(text) {
    const textarea = document.createElement('textarea');
    textarea.value = text;
    textarea.style.position = 'fixed';
    textarea.style.opacity = '0';
    document.body.appendChild(textarea);
    textarea.select();
    try {
      document.execCommand('copy');
      alert('Task link copied to clipboard!');
    } catch (err) {
      console.error('Fallback copy failed:', err);
      alert('Failed to copy link. Please copy manually: ' + text);
    }
    document.body.removeChild(textarea);
  }

  async reportLostFound() {
    const description = prompt('Describe the lost or found item:');
    if (!description || description.trim() === '') return;

    try {
      const response = await APIClient.post(`/api/staff/tasks/${this.taskId}/lost-found/`, {
        description: description.trim(),
        found: confirm('Was this item FOUND? (Cancel if LOST)')
      });
      
      if (response.success) {
        alert('Lost & Found report submitted successfully!');
        location.reload();
      }
    } catch (error) {
      console.error('Error submitting lost & found:', error);
      alert(`Failed to submit report: ${error.message}`);
    }
  }

  async duplicateTask() {
    if (!confirm('Create a duplicate of this task?')) return;

    try {
      const response = await APIClient.post(`/api/staff/tasks/${this.taskId}/duplicate/`, {});
      
      if (response.success && response.new_task_id) {
        alert('Task duplicated successfully!');
        window.location.href = `/api/staff/tasks/${response.new_task_id}/`;
      }
    } catch (error) {
      console.error('Error duplicating task:', error);
      alert(`Failed to duplicate task: ${error.message}`);
    }
  }

  async deleteTask(taskTitle) {
    if (!confirm(`Are you sure you want to delete "${taskTitle}"? This cannot be undone.`)) return;

    try {
      const response = await APIClient.request(`/api/staff/tasks/${this.taskId}/`, {
        method: 'DELETE'
      });
      
      if (response.success) {
        alert('Task deleted successfully!');
        window.location.href = '/api/staff/tasks/';
      }
    } catch (error) {
      console.error('Error deleting task:', error);
      alert(`Failed to delete task: ${error.message}`);
    }
  }

  updateTaskStatus(newStatus) {
    const statusBadge = document.querySelector('.status-badge');
    if (statusBadge) {
      statusBadge.className = `status-badge status-${newStatus.replace('-', '')}`;
      statusBadge.textContent = newStatus.replace('-', ' ').toUpperCase();
    }

    // Update button states
    const startBtn = document.querySelector('.btn-action.start-task');
    const completeBtn = document.querySelector('.btn-action.complete-task');
    
    if (newStatus === 'in-progress') {
      if (startBtn) startBtn.disabled = true;
      if (completeBtn) completeBtn.disabled = false;
    } else if (newStatus === 'completed') {
      if (startBtn) startBtn.disabled = true;
      if (completeBtn) completeBtn.disabled = true;
    }
  }
}

// Global bridge functions for backward compatibility with inline onclick handlers
if (typeof window !== 'undefined') {
  window.taskActionsInstance = null;
  
  window.startTask = function(taskId) {
    if (window.taskActionsInstance) {
      window.taskActionsInstance.startTask();
    }
  };
  
  window.completeTask = function(taskId) {
    if (window.taskActionsInstance) {
      window.taskActionsInstance.completeTask();
    }
  };
  
  window.addNote = function() {
    if (window.taskActionsInstance) {
      window.taskActionsInstance.addNote();
    }
  };
  
  window.shareTask = function() {
    if (window.taskActionsInstance) {
      window.taskActionsInstance.shareTask();
    }
  };
  
  window.reportLostFound = function() {
    if (window.taskActionsInstance) {
      window.taskActionsInstance.reportLostFound();
    }
  };
  
  window.duplicateTask = function(taskId) {
    if (window.taskActionsInstance) {
      window.taskActionsInstance.duplicateTask();
    }
  };
  
  window.deleteTask = function(taskId, taskTitle) {
    if (window.taskActionsInstance) {
      window.taskActionsInstance.deleteTask(taskTitle);
    }
  };
}
