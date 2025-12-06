/**
 * Task Detail Page - Main Entry Point
 * Initializes all modules for the task detail page
 */

import { TaskActions } from '../modules/task-actions.js';
import { TaskTimer } from '../modules/task-timer.js';
import { PhotoModal } from '../modules/photo-modal.js';

class TaskDetailPage {
  constructor() {
    this.taskId = this.getTaskId();
    
    if (!this.taskId) {
      console.error('Task ID not found');
      return;
    }

    console.log('Initializing Task Detail Page for task:', this.taskId);

    // Initialize all modules
    this.initModules();
    
    // Set up global bridge functions
    this.setupGlobalBridges();
  }

  getTaskId() {
    // Try to get task ID from various sources
    const taskContainer = document.getElementById('taskDetailContainer');
    if (taskContainer && taskContainer.dataset.taskId) {
      return taskContainer.dataset.taskId;
    }

    // Fallback: try to get from URL
    const match = window.location.pathname.match(/\/tasks\/(\d+)\//);
    if (match && match[1]) {
      return match[1];
    }

    // Fallback: try data attribute on any element
    const anyElement = document.querySelector('[data-task-id]');
    if (anyElement) {
      return anyElement.dataset.taskId;
    }

    return null;
  }

  initModules() {
    try {
      // Initialize Task Actions
      this.actions = new TaskActions(this.taskId);
      console.log('✓ Task Actions initialized');

      // Initialize Task Timer
      this.timer = new TaskTimer(this.taskId);
      console.log('✓ Task Timer initialized');

      // Initialize Photo Modal
      this.photoModal = new PhotoModal();
      console.log('✓ Photo Modal initialized');

    } catch (error) {
      console.error('Error initializing modules:', error);
    }
  }

  setupGlobalBridges() {
    // Store instances globally for bridge functions
    window.taskActionsInstance = this.actions;
    window.taskTimerInstance = this.timer;
    window._photoModalInstance = this.photoModal;
    
    console.log('✓ Global bridges established');
  }

  destroy() {
    // Clean up when page is unloaded
    if (this.timer) {
      this.timer.destroy();
    }
  }
}

// Initialize when DOM is ready
if (document.readyState === 'loading') {
  document.addEventListener('DOMContentLoaded', () => {
    window.taskDetailPageInstance = new TaskDetailPage();
  });
} else {
  window.taskDetailPageInstance = new TaskDetailPage();
}

// Clean up on page unload
window.addEventListener('beforeunload', () => {
  if (window.taskDetailPageInstance) {
    window.taskDetailPageInstance.destroy();
  }
});

export { TaskDetailPage };
