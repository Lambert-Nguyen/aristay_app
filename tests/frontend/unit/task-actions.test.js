/**
 * Unit Tests for Task Actions Module
 */

import { jest, describe, test, beforeEach, expect } from '@jest/globals';
import { TaskActions } from '../../../aristay_backend/static/js/modules/task-actions.js';
import { APIClient } from '../../../aristay_backend/static/js/core/api-client.js';

// Mock APIClient
jest.mock('../../../aristay_backend/static/js/core/api-client.js');

describe('TaskActions', () => {
  let taskActions;
  const mockTaskId = '123';

  beforeEach(() => {
    // Reset DOM
    document.body.innerHTML = `
      <div class="task-title">Test Task</div>
      <div class="status-badge status-pending">Pending</div>
      <button class="btn-action start-task" data-task-id="${mockTaskId}">Start</button>
      <button class="btn-action complete-task" data-task-id="${mockTaskId}">Complete</button>
      <button class="btn-action add-note" data-task-id="${mockTaskId}">Add Note</button>
      <button class="btn-action share-task" data-task-id="${mockTaskId}">Share</button>
      <button class="btn-action report-lost-found" data-task-id="${mockTaskId}">Report</button>
      <button class="btn-action duplicate-task">Duplicate</button>
      <button class="btn-action delete-task">Delete</button>
    `;

    // Mock window methods
    global.confirm = jest.fn(() => true);
    global.alert = jest.fn();
    global.prompt = jest.fn();
    
    // Mock location
    delete window.location;
    window.location = { href: '', reload: jest.fn() };

    // Clear mocks
    jest.clearAllMocks();

    taskActions = new TaskActions(mockTaskId);
  });

  describe('Constructor and Initialization', () => {
    test('stores task ID', () => {
      expect(taskActions.taskId).toBe(mockTaskId);
    });

    test('initializes event listeners', () => {
      const startBtn = document.querySelector('.btn-action.start-task');
      expect(startBtn).toBeTruthy();
    });
  });

  describe('startTask', () => {
    test('calls API to start task when confirmed', async () => {
      APIClient.post.mockResolvedValue({ success: true });

      await taskActions.startTask();

      expect(global.confirm).toHaveBeenCalledWith('Start this task now?');
      expect(APIClient.post).toHaveBeenCalledWith(
        `/api/staff/tasks/${mockTaskId}/start/`,
        {}
      );
      expect(window.location.reload).toHaveBeenCalled();
    });

    test('does not call API when cancelled', async () => {
      global.confirm.mockReturnValue(false);

      await taskActions.startTask();

      expect(APIClient.post).not.toHaveBeenCalled();
    });

    test('handles API errors gracefully', async () => {
      const errorMessage = 'Network error';
      APIClient.post.mockRejectedValue(new Error(errorMessage));

      await taskActions.startTask();

      expect(global.alert).toHaveBeenCalledWith(`Failed to start task: ${errorMessage}`);
    });
  });

  describe('completeTask', () => {
    test('calls API to complete task when confirmed', async () => {
      APIClient.post.mockResolvedValue({ success: true });

      await taskActions.completeTask();

      expect(global.confirm).toHaveBeenCalledWith('Mark this task as complete?');
      expect(APIClient.post).toHaveBeenCalledWith(
        `/api/staff/tasks/${mockTaskId}/complete/`,
        {}
      );
      expect(window.location.reload).toHaveBeenCalled();
    });

    test('does not call API when cancelled', async () => {
      global.confirm.mockReturnValue(false);

      await taskActions.completeTask();

      expect(APIClient.post).not.toHaveBeenCalled();
    });
  });

  describe('addNote', () => {
    test('adds note when valid input provided', async () => {
      const noteContent = 'This is a test note';
      global.prompt.mockReturnValue(noteContent);
      APIClient.post.mockResolvedValue({ success: true });

      await taskActions.addNote();

      expect(global.prompt).toHaveBeenCalledWith('Add a note to this task:');
      expect(APIClient.post).toHaveBeenCalledWith(
        `/api/staff/tasks/${mockTaskId}/notes/`,
        { content: noteContent }
      );
      expect(window.location.reload).toHaveBeenCalled();
    });

    test('does not add note when cancelled', async () => {
      global.prompt.mockReturnValue(null);

      await taskActions.addNote();

      expect(APIClient.post).not.toHaveBeenCalled();
    });

    test('does not add empty note', async () => {
      global.prompt.mockReturnValue('   ');

      await taskActions.addNote();

      expect(APIClient.post).not.toHaveBeenCalled();
    });
  });

  describe('shareTask', () => {
    test('uses Web Share API when available', async () => {
      global.navigator.share = jest.fn().mockResolvedValue();

      await taskActions.shareTask();

      expect(navigator.share).toHaveBeenCalledWith({
        title: expect.any(String),
        url: expect.any(String)
      });
    });

    test('falls back to clipboard when Web Share API not available', async () => {
      global.navigator.share = undefined;
      global.navigator.clipboard = {
        writeText: jest.fn().mockResolvedValue()
      };

      await taskActions.shareTask();

      expect(navigator.clipboard.writeText).toHaveBeenCalled();
      expect(global.alert).toHaveBeenCalledWith('Task link copied to clipboard!');
    });
  });

  describe('duplicateTask', () => {
    test('duplicates task and navigates to new task', async () => {
      const newTaskId = '456';
      APIClient.post.mockResolvedValue({ success: true, new_task_id: newTaskId });

      await taskActions.duplicateTask();

      expect(global.confirm).toHaveBeenCalledWith('Create a duplicate of this task?');
      expect(APIClient.post).toHaveBeenCalledWith(
        `/api/staff/tasks/${mockTaskId}/duplicate/`,
        {}
      );
      expect(window.location.href).toBe(`/api/staff/tasks/${newTaskId}/`);
    });
  });

  describe('deleteTask', () => {
    test('deletes task and navigates to task list', async () => {
      const taskTitle = 'Test Task';
      APIClient.request.mockResolvedValue({ success: true });

      await taskActions.deleteTask(taskTitle);

      expect(global.confirm).toHaveBeenCalledWith(
        `Are you sure you want to delete "${taskTitle}"? This cannot be undone.`
      );
      expect(APIClient.request).toHaveBeenCalledWith(
        `/api/staff/tasks/${mockTaskId}/`,
        { method: 'DELETE' }
      );
      expect(window.location.href).toBe('/api/staff/tasks/');
    });

    test('does not delete when cancelled', async () => {
      global.confirm.mockReturnValue(false);

      await taskActions.deleteTask('Test Task');

      expect(APIClient.request).not.toHaveBeenCalled();
    });
  });

  describe('updateTaskStatus', () => {
    test('updates status badge correctly', () => {
      taskActions.updateTaskStatus('in-progress');

      const statusBadge = document.querySelector('.status-badge');
      expect(statusBadge.className).toBe('status-badge status-inprogress');
      expect(statusBadge.textContent).toBe('IN PROGRESS');
    });

    test('updates button states when status changes', () => {
      const startBtn = document.querySelector('.btn-action.start-task');
      const completeBtn = document.querySelector('.btn-action.complete-task');

      taskActions.updateTaskStatus('in-progress');

      expect(startBtn.disabled).toBe(true);
      expect(completeBtn.disabled).toBe(false);

      taskActions.updateTaskStatus('completed');

      expect(startBtn.disabled).toBe(true);
      expect(completeBtn.disabled).toBe(true);
    });
  });

  describe('Global Bridge Functions', () => {
    test('exposes global window functions', () => {
      expect(typeof window.startTask).toBe('function');
      expect(typeof window.completeTask).toBe('function');
      expect(typeof window.addNote).toBe('function');
      expect(typeof window.shareTask).toBe('function');
      expect(typeof window.duplicateTask).toBe('function');
      expect(typeof window.deleteTask).toBe('function');
    });

    test('global functions call instance methods', async () => {
      window.taskActionsInstance = taskActions;
      jest.spyOn(taskActions, 'startTask');

      window.startTask(mockTaskId);

      expect(taskActions.startTask).toHaveBeenCalled();
    });
  });
});
