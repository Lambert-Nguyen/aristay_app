/**
 * Unit Tests for Task Timer Module
 */

import { jest, describe, test, beforeEach, afterEach, expect } from '@jest/globals';
import { TaskTimer } from '../../../aristay_backend/static/js/modules/task-timer.js';
import { StorageManager } from '../../../aristay_backend/static/js/core/storage.js';

// Mock StorageManager
jest.mock('../../../aristay_backend/static/js/core/storage.js');

describe('TaskTimer', () => {
  let taskTimer;
  const mockTaskId = '123';

  beforeEach(() => {
    // Reset DOM
    document.body.innerHTML = `
      <div id="timerText">00:00:00</div>
      <button id="startTimerBtn">Start</button>
      <button id="pauseTimerBtn">Pause</button>
      <button id="stopTimerBtn">Stop</button>
    `;

    // Mock window methods
    global.confirm = jest.fn(() => true);
    
    // Clear mocks
    jest.clearAllMocks();
    StorageManager.get.mockReturnValue(null);
    StorageManager.set.mockImplementation(() => {});

    // Clear any existing timers
    jest.useFakeTimers();
  });

  afterEach(() => {
    jest.useRealTimers();
  });

  describe('Constructor and Initialization', () => {
    test('initializes with zero seconds', () => {
      taskTimer = new TaskTimer(mockTaskId);
      expect(taskTimer.seconds).toBe(0);
      expect(taskTimer.running).toBe(false);
    });

    test('loads state from storage', () => {
      const savedState = { seconds: 300, running: false };
      StorageManager.get.mockReturnValue(savedState);

      taskTimer = new TaskTimer(mockTaskId);

      expect(StorageManager.get).toHaveBeenCalledWith(`task_timer_${mockTaskId}`);
      expect(taskTimer.seconds).toBe(300);
    });

    test('auto-starts if timer was running', () => {
      const savedState = { seconds: 100, running: true };
      StorageManager.get.mockReturnValue(savedState);

      taskTimer = new TaskTimer(mockTaskId);

      expect(taskTimer.running).toBe(true);
      expect(taskTimer.interval).not.toBeNull();
    });

    test('updates display on init', () => {
      const savedState = { seconds: 3665, running: false }; // 1:01:05
      StorageManager.get.mockReturnValue(savedState);

      taskTimer = new TaskTimer(mockTaskId);

      const display = document.getElementById('timerText');
      expect(display.textContent).toBe('01:01:05');
    });
  });

  describe('start', () => {
    beforeEach(() => {
      taskTimer = new TaskTimer(mockTaskId);
    });

    test('starts timer from 0', () => {
      taskTimer.start();

      expect(taskTimer.running).toBe(true);
      expect(taskTimer.interval).not.toBeNull();
    });

    test('increments seconds every second', () => {
      taskTimer.start();

      jest.advanceTimersByTime(1000);
      expect(taskTimer.seconds).toBe(1);

      jest.advanceTimersByTime(1000);
      expect(taskTimer.seconds).toBe(2);

      jest.advanceTimersByTime(3000);
      expect(taskTimer.seconds).toBe(5);
    });

    test('updates display every second', () => {
      taskTimer.start();

      jest.advanceTimersByTime(1000);
      const display = document.getElementById('timerText');
      expect(display.textContent).toBe('00:00:01');

      jest.advanceTimersByTime(59000);
      expect(display.textContent).toBe('00:01:00');
    });

    test('saves state every 5 seconds', () => {
      taskTimer.start();

      jest.advanceTimersByTime(4000);
      expect(StorageManager.set).toHaveBeenCalledTimes(1); // Initial save

      jest.advanceTimersByTime(1000);
      expect(StorageManager.set).toHaveBeenCalledTimes(2); // Save at 5 seconds

      jest.advanceTimersByTime(5000);
      expect(StorageManager.set).toHaveBeenCalledTimes(3); // Save at 10 seconds
    });

    test('does not start if already running', () => {
      taskTimer.start();
      const firstInterval = taskTimer.interval;

      taskTimer.start();
      const secondInterval = taskTimer.interval;

      expect(firstInterval).toBe(secondInterval);
    });
  });

  describe('pause', () => {
    beforeEach(() => {
      taskTimer = new TaskTimer(mockTaskId);
    });

    test('pauses running timer', () => {
      taskTimer.start();
      jest.advanceTimersByTime(3000);

      taskTimer.pause();

      expect(taskTimer.running).toBe(false);
      expect(taskTimer.interval).toBeNull();
      expect(taskTimer.seconds).toBe(3);
    });

    test('saves state when paused', () => {
      taskTimer.start();
      jest.advanceTimersByTime(3000);
      StorageManager.set.mockClear();

      taskTimer.pause();

      expect(StorageManager.set).toHaveBeenCalledWith(
        `task_timer_${mockTaskId}`,
        expect.objectContaining({
          seconds: 3,
          running: false
        })
      );
    });

    test('does nothing if not running', () => {
      const result = taskTimer.pause();
      expect(taskTimer.running).toBe(false);
    });
  });

  describe('reset', () => {
    beforeEach(() => {
      taskTimer = new TaskTimer(mockTaskId);
    });

    test('resets timer to zero', () => {
      taskTimer.start();
      jest.advanceTimersByTime(10000);

      taskTimer.reset();

      expect(taskTimer.seconds).toBe(0);
      expect(taskTimer.running).toBe(false);
      expect(taskTimer.interval).toBeNull();
    });

    test('updates display to 00:00:00', () => {
      taskTimer.start();
      jest.advanceTimersByTime(5000);

      taskTimer.reset();

      const display = document.getElementById('timerText');
      expect(display.textContent).toBe('00:00:00');
    });

    test('requires confirmation', () => {
      global.confirm.mockReturnValue(false);

      taskTimer.start();
      jest.advanceTimersByTime(5000);

      taskTimer.reset();

      expect(taskTimer.seconds).toBe(5); // Not reset
    });
  });

  describe('formatTime', () => {
    beforeEach(() => {
      taskTimer = new TaskTimer(mockTaskId);
    });

    test('formats zero correctly', () => {
      expect(taskTimer.formatTime(0)).toBe('00:00:00');
    });

    test('formats seconds correctly', () => {
      expect(taskTimer.formatTime(45)).toBe('00:00:45');
    });

    test('formats minutes correctly', () => {
      expect(taskTimer.formatTime(125)).toBe('00:02:05');
    });

    test('formats hours correctly', () => {
      expect(taskTimer.formatTime(3665)).toBe('01:01:05');
    });

    test('handles large values', () => {
      expect(taskTimer.formatTime(36000)).toBe('10:00:00');
    });
  });

  describe('updateButtonStates', () => {
    beforeEach(() => {
      taskTimer = new TaskTimer(mockTaskId);
    });

    test('disables start when running', () => {
      taskTimer.running = true;
      taskTimer.updateButtonStates();

      const startBtn = document.getElementById('startTimerBtn');
      const pauseBtn = document.getElementById('pauseTimerBtn');

      expect(startBtn.disabled).toBe(true);
      expect(pauseBtn.disabled).toBe(false);
    });

    test('enables start when paused', () => {
      taskTimer.running = false;
      taskTimer.seconds = 10;
      taskTimer.updateButtonStates();

      const startBtn = document.getElementById('startTimerBtn');
      const pauseBtn = document.getElementById('pauseTimerBtn');
      const stopBtn = document.getElementById('stopTimerBtn');

      expect(startBtn.disabled).toBe(false);
      expect(pauseBtn.disabled).toBe(true);
      expect(stopBtn.disabled).toBe(false);
    });
  });

  describe('saveState', () => {
    beforeEach(() => {
      taskTimer = new TaskTimer(mockTaskId);
    });

    test('saves complete state to storage', () => {
      taskTimer.seconds = 100;
      taskTimer.running = true;

      taskTimer.saveState();

      expect(StorageManager.set).toHaveBeenCalledWith(
        `task_timer_${mockTaskId}`,
        expect.objectContaining({
          taskId: mockTaskId,
          seconds: 100,
          running: true,
          timestamp: expect.any(Number)
        })
      );
    });
  });

  describe('destroy', () => {
    beforeEach(() => {
      taskTimer = new TaskTimer(mockTaskId);
    });

    test('clears interval and saves state', () => {
      taskTimer.start();
      StorageManager.set.mockClear();

      taskTimer.destroy();

      expect(taskTimer.interval).toBeNull();
      expect(StorageManager.set).toHaveBeenCalled();
    });
  });

  describe('Global Bridge Functions', () => {
    test('exposes global window functions', () => {
      expect(typeof window.startTimer).toBe('function');
      expect(typeof window.pauseTimer).toBe('function');
      expect(typeof window.stopTimer).toBe('function');
      expect(typeof window.resetTimer).toBe('function');
    });

    test('global functions call instance methods', () => {
      taskTimer = new TaskTimer(mockTaskId);
      window.taskTimerInstance = taskTimer;
      jest.spyOn(taskTimer, 'start');

      window.startTimer();

      expect(taskTimer.start).toHaveBeenCalled();
    });
  });
});
