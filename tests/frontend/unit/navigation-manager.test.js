/**
 * Unit Tests for NavigationManager Module
 * Tests task navigation, keyboard shortcuts, and button state management
 */

import { describe, it, expect, beforeEach, afterEach, jest } from '@jest/globals';
import { NavigationManager } from '../../../aristay_backend/static/js/modules/navigation-manager.js';

// Mock APIClient
jest.mock('../../../aristay_backend/static/js/core/api-client.js', () => ({
  APIClient: {
    request: jest.fn(),
    get: jest.fn(),
    post: jest.fn(),
    patch: jest.fn(),
    delete: jest.fn(),
  }
}));

import { APIClient } from '../../../aristay_backend/static/js/core/api-client.js';

describe('NavigationManager', () => {
  let navigationManager;
  let mockTaskContainer;
  let mockNavContainer;

  beforeEach(() => {
    // Reset DOM
    document.body.innerHTML = '';
    
    // Create mock task container with task ID
    mockTaskContainer = document.createElement('div');
    mockTaskContainer.id = 'taskDetailContainer';
    mockTaskContainer.dataset.taskId = '123';
    document.body.appendChild(mockTaskContainer);

    // Create navigation container with buttons
    mockNavContainer = document.createElement('div');
    mockNavContainer.className = 'task-navigation';
    mockNavContainer.dataset.navPrev = '122';
    mockNavContainer.dataset.navNext = '124';
    mockNavContainer.innerHTML = `
      <button id="backToListBtn" class="btn-back-to-list">Back to List</button>
      <button id="prevTaskBtn" class="btn-prev-task">Previous</button>
      <button id="nextTaskBtn" class="btn-next-task">Next</button>
    `;
    document.body.appendChild(mockNavContainer);

    // Mock window.location
    delete window.location;
    window.location = { href: '', pathname: '/staff/tasks/123/' };

    // Clear all mocks
    jest.clearAllMocks();
    
    // Reset window instances
    window.navigationManagerInstance = null;
  });

  afterEach(() => {
    document.body.innerHTML = '';
    jest.clearAllMocks();
  });

  describe('Constructor', () => {
    it('should initialize with task ID', async () => {
      APIClient.get.mockResolvedValue({
        success: true,
        prev_task_id: '122',
        next_task_id: '124'
      });

      navigationManager = new NavigationManager();
      
      // Wait for async init
      await new Promise(resolve => setTimeout(resolve, 0));

      expect(navigationManager.taskId).toBe('123');
    });

    it('should fetch navigation data from API', async () => {
      APIClient.get.mockResolvedValue({
        success: true,
        prev_task_id: '122',
        next_task_id: '124'
      });

      navigationManager = new NavigationManager();
      await new Promise(resolve => setTimeout(resolve, 0));

      expect(APIClient.get).toHaveBeenCalledWith('/api/tasks/123/navigation/');
    });

    it('should set up keyboard shortcuts', async () => {
      APIClient.get.mockResolvedValue({
        success: true,
        prev_task_id: '122',
        next_task_id: '124'
      });

      const addEventListenerSpy = jest.spyOn(document, 'addEventListener');
      
      navigationManager = new NavigationManager();
      await new Promise(resolve => setTimeout(resolve, 0));

      expect(addEventListenerSpy).toHaveBeenCalledWith('keydown', expect.any(Function));
    });

    it('should update button states after initialization', async () => {
      APIClient.get.mockResolvedValue({
        success: true,
        prev_task_id: '122',
        next_task_id: '124'
      });

      navigationManager = new NavigationManager();
      await new Promise(resolve => setTimeout(resolve, 0));

      const prevBtn = document.getElementById('prevTaskBtn');
      const nextBtn = document.getElementById('nextTaskBtn');

      expect(prevBtn.disabled).toBe(false);
      expect(nextBtn.disabled).toBe(false);
    });
  });

  describe('fetchNavigationData()', () => {
    it('should fetch navigation data successfully', async () => {
      APIClient.get.mockResolvedValue({
        success: true,
        prev_task_id: '122',
        next_task_id: '124'
      });

      navigationManager = new NavigationManager();
      await navigationManager.fetchNavigationData();

      expect(navigationManager.prevTaskId).toBe('122');
      expect(navigationManager.nextTaskId).toBe('124');
    });

    it('should handle API errors with DOM fallback', async () => {
      APIClient.get.mockRejectedValue(new Error('API error'));

      navigationManager = new NavigationManager();
      await navigationManager.fetchNavigationData();

      // Should fall back to DOM data attributes
      expect(navigationManager.prevTaskId).toBe('122');
      expect(navigationManager.nextTaskId).toBe('124');
    });

    it('should handle missing task ID', async () => {
      mockTaskContainer.remove();
      const consoleSpy = jest.spyOn(console, 'warn').mockImplementation();

      navigationManager = new NavigationManager();
      await navigationManager.fetchNavigationData();

      expect(consoleSpy).toHaveBeenCalledWith('No task ID found for navigation');
      consoleSpy.mockRestore();
    });
  });

  describe('loadNavigationFromDOM()', () => {
    it('should load navigation data from DOM attributes', () => {
      navigationManager = new NavigationManager();
      navigationManager.loadNavigationFromDOM();

      expect(navigationManager.prevTaskId).toBe('122');
      expect(navigationManager.nextTaskId).toBe('124');
    });

    it('should handle missing navigation container', () => {
      mockNavContainer.remove();
      
      navigationManager = new NavigationManager();
      navigationManager.loadNavigationFromDOM();

      expect(navigationManager.prevTaskId).toBeUndefined();
      expect(navigationManager.nextTaskId).toBeUndefined();
    });
  });

  describe('navigateToPrev()', () => {
    beforeEach(async () => {
      APIClient.get.mockResolvedValue({
        success: true,
        prev_task_id: '122',
        next_task_id: '124'
      });

      navigationManager = new NavigationManager();
      await new Promise(resolve => setTimeout(resolve, 0));
    });

    it('should navigate to previous task', () => {
      navigationManager.navigateToPrev();

      expect(window.location.href).toBe('/staff/tasks/122/');
    });

    it('should show notification if no previous task', () => {
      navigationManager.prevTaskId = null;
      const showNotificationSpy = jest.spyOn(navigationManager, 'showNotification');

      navigationManager.navigateToPrev();

      expect(showNotificationSpy).toHaveBeenCalledWith('No previous task', 'info');
      expect(window.location.href).not.toBe('/staff/tasks/122/');
    });
  });

  describe('navigateToNext()', () => {
    beforeEach(async () => {
      APIClient.get.mockResolvedValue({
        success: true,
        prev_task_id: '122',
        next_task_id: '124'
      });

      navigationManager = new NavigationManager();
      await new Promise(resolve => setTimeout(resolve, 0));
    });

    it('should navigate to next task', () => {
      navigationManager.navigateToNext();

      expect(window.location.href).toBe('/staff/tasks/124/');
    });

    it('should show notification if no next task', () => {
      navigationManager.nextTaskId = null;
      const showNotificationSpy = jest.spyOn(navigationManager, 'showNotification');

      navigationManager.navigateToNext();

      expect(showNotificationSpy).toHaveBeenCalledWith('No next task', 'info');
      expect(window.location.href).not.toBe('/staff/tasks/124/');
    });
  });

  describe('navigateToList()', () => {
    beforeEach(async () => {
      APIClient.get.mockResolvedValue({
        success: true,
        prev_task_id: '122',
        next_task_id: '124'
      });

      navigationManager = new NavigationManager();
      await new Promise(resolve => setTimeout(resolve, 0));
    });

    it('should navigate to task list', () => {
      navigationManager.navigateToList();

      expect(window.location.href).toBe('/staff/tasks/');
    });

    it('should navigate with filters', () => {
      const filters = {
        status: 'pending',
        assigned_to: 'me'
      };

      navigationManager.navigateToList(filters);

      expect(window.location.href).toContain('/staff/tasks/?');
      expect(window.location.href).toContain('status=pending');
      expect(window.location.href).toContain('assigned_to=me');
    });
  });

  describe('updateButtonStates()', () => {
    beforeEach(async () => {
      navigationManager = new NavigationManager();
    });

    it('should enable buttons when navigation is available', async () => {
      navigationManager.prevTaskId = '122';
      navigationManager.nextTaskId = '124';

      navigationManager.updateButtonStates();

      const prevBtn = document.getElementById('prevTaskBtn');
      const nextBtn = document.getElementById('nextTaskBtn');

      expect(prevBtn.disabled).toBe(false);
      expect(prevBtn.classList.contains('disabled')).toBe(false);
      expect(nextBtn.disabled).toBe(false);
      expect(nextBtn.classList.contains('disabled')).toBe(false);
    });

    it('should disable prev button when no previous task', () => {
      navigationManager.prevTaskId = null;
      navigationManager.nextTaskId = '124';

      navigationManager.updateButtonStates();

      const prevBtn = document.getElementById('prevTaskBtn');
      const nextBtn = document.getElementById('nextTaskBtn');

      expect(prevBtn.disabled).toBe(true);
      expect(prevBtn.classList.contains('disabled')).toBe(true);
      expect(nextBtn.disabled).toBe(false);
    });

    it('should disable next button when no next task', () => {
      navigationManager.prevTaskId = '122';
      navigationManager.nextTaskId = null;

      navigationManager.updateButtonStates();

      const prevBtn = document.getElementById('prevTaskBtn');
      const nextBtn = document.getElementById('nextTaskBtn');

      expect(prevBtn.disabled).toBe(false);
      expect(nextBtn.disabled).toBe(true);
      expect(nextBtn.classList.contains('disabled')).toBe(true);
    });

    it('should set aria-disabled attributes', () => {
      navigationManager.prevTaskId = null;
      navigationManager.nextTaskId = '124';

      navigationManager.updateButtonStates();

      const prevBtn = document.getElementById('prevTaskBtn');
      const nextBtn = document.getElementById('nextTaskBtn');

      expect(prevBtn.getAttribute('aria-disabled')).toBe('true');
      expect(nextBtn.getAttribute('aria-disabled')).toBe('false');
    });
  });

  describe('Button Event Listeners', () => {
    beforeEach(async () => {
      APIClient.get.mockResolvedValue({
        success: true,
        prev_task_id: '122',
        next_task_id: '124'
      });

      navigationManager = new NavigationManager();
      await new Promise(resolve => setTimeout(resolve, 0));
    });

    it('should handle prev button click', () => {
      const prevBtn = document.getElementById('prevTaskBtn');
      const navigateSpy = jest.spyOn(navigationManager, 'navigateToPrev');

      prevBtn.click();

      expect(navigateSpy).toHaveBeenCalled();
    });

    it('should handle next button click', () => {
      const nextBtn = document.getElementById('nextTaskBtn');
      const navigateSpy = jest.spyOn(navigationManager, 'navigateToNext');

      nextBtn.click();

      expect(navigateSpy).toHaveBeenCalled();
    });

    it('should handle back to list button click', () => {
      const backBtn = document.getElementById('backToListBtn');
      const navigateSpy = jest.spyOn(navigationManager, 'navigateToList');

      backBtn.click();

      expect(navigateSpy).toHaveBeenCalled();
    });
  });

  describe('Keyboard Shortcuts', () => {
    beforeEach(async () => {
      APIClient.get.mockResolvedValue({
        success: true,
        prev_task_id: '122',
        next_task_id: '124'
      });

      navigationManager = new NavigationManager();
      await new Promise(resolve => setTimeout(resolve, 0));
    });

    it('should navigate to previous task with Alt+Left', () => {
      const navigateSpy = jest.spyOn(navigationManager, 'navigateToPrev');

      const event = new KeyboardEvent('keydown', {
        key: 'ArrowLeft',
        altKey: true,
        bubbles: true
      });
      document.dispatchEvent(event);

      expect(navigateSpy).toHaveBeenCalled();
    });

    it('should navigate to next task with Alt+Right', () => {
      const navigateSpy = jest.spyOn(navigationManager, 'navigateToNext');

      const event = new KeyboardEvent('keydown', {
        key: 'ArrowRight',
        altKey: true,
        bubbles: true
      });
      document.dispatchEvent(event);

      expect(navigateSpy).toHaveBeenCalled();
    });

    it('should navigate to list with Escape', () => {
      const navigateSpy = jest.spyOn(navigationManager, 'navigateToList');

      const event = new KeyboardEvent('keydown', {
        key: 'Escape',
        bubbles: true
      });
      document.dispatchEvent(event);

      expect(navigateSpy).toHaveBeenCalled();
    });

    it('should ignore keyboard shortcuts when typing in input', () => {
      const navigateSpy = jest.spyOn(navigationManager, 'navigateToPrev');

      const input = document.createElement('input');
      document.body.appendChild(input);

      const event = new KeyboardEvent('keydown', {
        key: 'ArrowLeft',
        altKey: true,
        bubbles: true
      });
      Object.defineProperty(event, 'target', { value: input, writable: false });
      document.dispatchEvent(event);

      expect(navigateSpy).not.toHaveBeenCalled();
    });

    it('should ignore keyboard shortcuts when typing in textarea', () => {
      const navigateSpy = jest.spyOn(navigationManager, 'navigateToList');

      const textarea = document.createElement('textarea');
      document.body.appendChild(textarea);

      const event = new KeyboardEvent('keydown', {
        key: 'Escape',
        bubbles: true
      });
      Object.defineProperty(event, 'target', { value: textarea, writable: false });
      document.dispatchEvent(event);

      expect(navigateSpy).not.toHaveBeenCalled();
    });
  });

  describe('Global Bridge Functions', () => {
    beforeEach(async () => {
      APIClient.get.mockResolvedValue({
        success: true,
        prev_task_id: '122',
        next_task_id: '124'
      });

      navigationManager = new NavigationManager();
      await new Promise(resolve => setTimeout(resolve, 0));
      window.navigationManagerInstance = navigationManager;
    });

    it('should expose navigateToPrevTask globally', () => {
      expect(window.navigateToPrevTask).toBeDefined();
      expect(typeof window.navigateToPrevTask).toBe('function');
    });

    it('should call navigateToPrev through global bridge', () => {
      const navigateSpy = jest.spyOn(navigationManager, 'navigateToPrev');

      window.navigateToPrevTask();

      expect(navigateSpy).toHaveBeenCalled();
    });

    it('should expose navigateToNextTask globally', () => {
      expect(window.navigateToNextTask).toBeDefined();
      expect(typeof window.navigateToNextTask).toBe('function');
    });

    it('should call navigateToNext through global bridge', () => {
      const navigateSpy = jest.spyOn(navigationManager, 'navigateToNext');

      window.navigateToNextTask();

      expect(navigateSpy).toHaveBeenCalled();
    });

    it('should expose navigateToTaskList globally', () => {
      expect(window.navigateToTaskList).toBeDefined();
      expect(typeof window.navigateToTaskList).toBe('function');
    });

    it('should call navigateToList through global bridge', () => {
      const navigateSpy = jest.spyOn(navigationManager, 'navigateToList');

      window.navigateToTaskList();

      expect(navigateSpy).toHaveBeenCalled();
    });

    it('should pass filters through global bridge', () => {
      const navigateSpy = jest.spyOn(navigationManager, 'navigateToList');
      const filters = { status: 'pending' };

      window.navigateToTaskList(filters);

      expect(navigateSpy).toHaveBeenCalledWith(filters);
    });
  });

  describe('Notification System', () => {
    beforeEach(async () => {
      APIClient.get.mockResolvedValue({
        success: true,
        prev_task_id: '122',
        next_task_id: '124'
      });

      navigationManager = new NavigationManager();
      await new Promise(resolve => setTimeout(resolve, 0));
      jest.useFakeTimers();
    });

    afterEach(() => {
      jest.useRealTimers();
    });

    it('should show notification', () => {
      navigationManager.showNotification('Test message', 'info');

      const notification = document.querySelector('.notification-info');
      expect(notification).not.toBeNull();
      expect(notification.textContent).toBe('Test message');
    });

    it('should auto-remove notification after 2 seconds', () => {
      navigationManager.showNotification('Test message', 'info');

      const notification = document.querySelector('.notification-info');
      expect(notification).not.toBeNull();

      jest.advanceTimersByTime(2300);

      const notificationGone = document.querySelector('.notification-info');
      expect(notificationGone).toBeNull();
    });

    it('should show different notification types', () => {
      navigationManager.showNotification('Success', 'success');
      navigationManager.showNotification('Error', 'error');
      navigationManager.showNotification('Info', 'info');

      expect(document.querySelector('.notification-success')).not.toBeNull();
      expect(document.querySelector('.notification-error')).not.toBeNull();
      expect(document.querySelector('.notification-info')).not.toBeNull();
    });
  });

  describe('getTaskId()', () => {
    it('should get task ID from taskDetailContainer', () => {
      navigationManager = new NavigationManager();
      const taskId = navigationManager.getTaskId();

      expect(taskId).toBe('123');
    });

    it('should get task ID from data attribute', () => {
      mockTaskContainer.remove();
      
      const altContainer = document.createElement('div');
      altContainer.dataset.taskId = '456';
      document.body.appendChild(altContainer);

      navigationManager = new NavigationManager();
      const taskId = navigationManager.getTaskId();

      expect(taskId).toBe('456');
    });

    it('should return null if no task ID found', () => {
      document.body.innerHTML = '';

      navigationManager = new NavigationManager();
      const taskId = navigationManager.getTaskId();

      expect(taskId).toBeNull();
    });
  });
});
