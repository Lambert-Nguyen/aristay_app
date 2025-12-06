/**
 * Navigation Manager Module
 * Handles prev/next task navigation and keyboard shortcuts
 */

import { APIClient } from '../core/api-client.js';

export class NavigationManager {
  constructor() {
    this.taskId = this.getTaskId();
    this.prevTaskId = null;
    this.nextTaskId = null;
    
    this.init();
    console.log('✓ NavigationManager initialized');
  }

  getTaskId() {
    const taskContainer = document.getElementById('taskDetailContainer') || 
                         document.querySelector('[data-task-id]');
    return taskContainer?.dataset.taskId || null;
  }

  async init() {
    await this.fetchNavigationData();
    this.initButtons();
    this.initKeyboardShortcuts();
    this.updateButtonStates();
  }

  async fetchNavigationData() {
    if (!this.taskId) {
      console.warn('No task ID found for navigation');
      return;
    }

    try {
      const response = await APIClient.get(`/api/tasks/${this.taskId}/navigation/`);
      
      if (response.success) {
        this.prevTaskId = response.prev_task_id;
        this.nextTaskId = response.next_task_id;
        console.log('✓ Navigation data loaded:', { prev: this.prevTaskId, next: this.nextTaskId });
      }
    } catch (error) {
      console.error('❌ Error fetching navigation data:', error);
      
      // Fallback: Try to get navigation from page data attributes
      this.loadNavigationFromDOM();
    }
  }

  loadNavigationFromDOM() {
    const navContainer = document.querySelector('.task-navigation') || 
                        document.querySelector('[data-nav-prev], [data-nav-next]');
    
    if (navContainer) {
      this.prevTaskId = navContainer.dataset.navPrev || null;
      this.nextTaskId = navContainer.dataset.navNext || null;
      console.log('✓ Navigation data loaded from DOM:', { prev: this.prevTaskId, next: this.nextTaskId });
    }
  }

  initButtons() {
    // Prev button
    const prevBtn = document.getElementById('prevTaskBtn') || 
                   document.querySelector('.btn-prev-task');
    if (prevBtn) {
      prevBtn.addEventListener('click', (e) => {
        e.preventDefault();
        this.navigateToPrev();
      });
    }

    // Next button
    const nextBtn = document.getElementById('nextTaskBtn') || 
                   document.querySelector('.btn-next-task');
    if (nextBtn) {
      nextBtn.addEventListener('click', (e) => {
        e.preventDefault();
        this.navigateToNext();
      });
    }

    // Back to list button
    const backBtn = document.getElementById('backToListBtn') || 
                   document.querySelector('.btn-back-to-list');
    if (backBtn) {
      backBtn.addEventListener('click', (e) => {
        e.preventDefault();
        this.navigateToList();
      });
    }
  }

  initKeyboardShortcuts() {
    document.addEventListener('keydown', (e) => {
      // Ignore if user is typing in input/textarea
      if (e.target.matches('input, textarea, [contenteditable]')) {
        return;
      }

      // Alt + Left Arrow = Previous task
      if (e.altKey && e.key === 'ArrowLeft') {
        e.preventDefault();
        this.navigateToPrev();
      }
      
      // Alt + Right Arrow = Next task
      if (e.altKey && e.key === 'ArrowRight') {
        e.preventDefault();
        this.navigateToNext();
      }
      
      // Escape = Back to list
      if (e.key === 'Escape') {
        e.preventDefault();
        this.navigateToList();
      }
    });

    console.log('✓ Keyboard shortcuts enabled: Alt+← (prev), Alt+→ (next), Esc (back)');
  }

  navigateToPrev() {
    if (!this.prevTaskId) {
      console.log('No previous task available');
      this.showNotification('No previous task', 'info');
      return;
    }

    console.log(`Navigating to previous task: ${this.prevTaskId}`);
    window.location.href = `/staff/tasks/${this.prevTaskId}/`;
  }

  navigateToNext() {
    if (!this.nextTaskId) {
      console.log('No next task available');
      this.showNotification('No next task', 'info');
      return;
    }

    console.log(`Navigating to next task: ${this.nextTaskId}`);
    window.location.href = `/staff/tasks/${this.nextTaskId}/`;
  }

  navigateToList(filters = null) {
    console.log('Navigating back to task list');
    
    // Build query string from filters if provided
    let url = '/staff/tasks/';
    if (filters) {
      const params = new URLSearchParams(filters);
      url += `?${params.toString()}`;
    }
    
    window.location.href = url;
  }

  updateButtonStates() {
    // Update prev button
    const prevBtn = document.getElementById('prevTaskBtn') || 
                   document.querySelector('.btn-prev-task');
    if (prevBtn) {
      if (this.prevTaskId) {
        prevBtn.disabled = false;
        prevBtn.classList.remove('disabled');
        prevBtn.setAttribute('aria-disabled', 'false');
      } else {
        prevBtn.disabled = true;
        prevBtn.classList.add('disabled');
        prevBtn.setAttribute('aria-disabled', 'true');
      }
    }

    // Update next button
    const nextBtn = document.getElementById('nextTaskBtn') || 
                   document.querySelector('.btn-next-task');
    if (nextBtn) {
      if (this.nextTaskId) {
        nextBtn.disabled = false;
        nextBtn.classList.remove('disabled');
        nextBtn.setAttribute('aria-disabled', 'false');
      } else {
        nextBtn.disabled = true;
        nextBtn.classList.add('disabled');
        nextBtn.setAttribute('aria-disabled', 'true');
      }
    }

    console.log('✓ Navigation buttons updated');
  }

  showNotification(message, type = 'info') {
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

    setTimeout(() => {
      notification.style.animation = 'slideOut 0.3s ease-out';
      setTimeout(() => {
        notification.remove();
      }, 300);
    }, 2000);
  }
}

// Global bridge functions for backward compatibility
if (typeof window !== 'undefined') {
  window.navigationManagerInstance = null;

  window.navigateToPrevTask = function() {
    if (window.navigationManagerInstance) {
      window.navigationManagerInstance.navigateToPrev();
    }
  };

  window.navigateToNextTask = function() {
    if (window.navigationManagerInstance) {
      window.navigationManagerInstance.navigateToNext();
    }
  };

  window.navigateToTaskList = function(filters = null) {
    if (window.navigationManagerInstance) {
      window.navigationManagerInstance.navigateToList(filters);
    }
  };
}
