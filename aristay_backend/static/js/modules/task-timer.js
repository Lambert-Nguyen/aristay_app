/**
 * Task Timer Module
 * Handles timer functionality with localStorage persistence
 */

import { StorageManager } from '../core/storage.js';

export class TaskTimer {
  constructor(taskId) {
    this.taskId = taskId;
    this.storageKey = `task_timer_${taskId}`;
    this.seconds = 0;
    this.running = false;
    this.interval = null;
    
    this.loadState();
    this.initUI();
    this.initEventListeners();
    
    // Auto-start if timer was running
    if (this.running) {
      this.start();
    }
  }

  loadState() {
    const saved = StorageManager.get(this.storageKey);
    if (saved) {
      this.seconds = saved.seconds || 0;
      this.running = saved.running || false;
      console.log('Timer state loaded:', saved);
    }
  }

  saveState() {
    const state = {
      taskId: this.taskId,
      seconds: this.seconds,
      running: this.running,
      timestamp: Date.now()
    };
    StorageManager.set(this.storageKey, state);
    console.log('Timer state saved:', state);
  }

  initUI() {
    const timerDisplay = document.getElementById('timerText');
    if (timerDisplay) {
      timerDisplay.textContent = this.formatTime(this.seconds);
    }

    // Update button states
    this.updateButtonStates();
  }

  initEventListeners() {
    const startBtn = document.getElementById('startTimerBtn');
    const pauseBtn = document.getElementById('pauseTimerBtn');
    const stopBtn = document.getElementById('stopTimerBtn');

    if (startBtn) {
      startBtn.addEventListener('click', () => this.start());
    }

    if (pauseBtn) {
      pauseBtn.addEventListener('click', () => this.pause());
    }

    if (stopBtn) {
      stopBtn.addEventListener('click', () => this.reset());
    }
  }

  start() {
    if (this.running) return;

    this.running = true;
    this.saveState();
    this.updateButtonStates();

    this.interval = setInterval(() => {
      this.seconds++;
      this.updateDisplay();
      
      // Save state every 5 seconds to avoid excessive writes
      if (this.seconds % 5 === 0) {
        this.saveState();
      }
    }, 1000);

    console.log('Timer started');
  }

  pause() {
    if (!this.running) return;

    this.running = false;
    this.saveState();
    this.updateButtonStates();

    if (this.interval) {
      clearInterval(this.interval);
      this.interval = null;
    }

    console.log('Timer paused at:', this.formatTime(this.seconds));
  }

  reset() {
    if (!confirm('Reset timer to 00:00:00?')) return;

    this.running = false;
    this.seconds = 0;
    this.saveState();
    this.updateDisplay();
    this.updateButtonStates();

    if (this.interval) {
      clearInterval(this.interval);
      this.interval = null;
    }

    console.log('Timer reset');
  }

  updateDisplay() {
    const timerDisplay = document.getElementById('timerText');
    if (timerDisplay) {
      timerDisplay.textContent = this.formatTime(this.seconds);
    }
  }

  updateButtonStates() {
    const startBtn = document.getElementById('startTimerBtn');
    const pauseBtn = document.getElementById('pauseTimerBtn');
    const stopBtn = document.getElementById('stopTimerBtn');

    if (this.running) {
      if (startBtn) startBtn.disabled = true;
      if (pauseBtn) pauseBtn.disabled = false;
      if (stopBtn) stopBtn.disabled = false;
    } else {
      if (startBtn) startBtn.disabled = false;
      if (pauseBtn) pauseBtn.disabled = true;
      if (stopBtn) stopBtn.disabled = this.seconds === 0;
    }
  }

  formatTime(totalSeconds) {
    const hours = Math.floor(totalSeconds / 3600);
    const minutes = Math.floor((totalSeconds % 3600) / 60);
    const seconds = totalSeconds % 60;
    
    return [hours, minutes, seconds]
      .map(val => String(val).padStart(2, '0'))
      .join(':');
  }

  destroy() {
    // Clean up when component is destroyed
    if (this.interval) {
      clearInterval(this.interval);
    }
    this.saveState();
  }
}

// Global bridge functions for backward compatibility
if (typeof window !== 'undefined') {
  window.taskTimerInstance = null;

  window.startTimer = function() {
    if (window.taskTimerInstance) {
      window.taskTimerInstance.start();
    }
  };

  window.pauseTimer = function() {
    if (window.taskTimerInstance) {
      window.taskTimerInstance.pause();
    }
  };

  window.stopTimer = function() {
    if (window.taskTimerInstance) {
      window.taskTimerInstance.reset();
    }
  };

  window.resetTimer = function() {
    if (window.taskTimerInstance) {
      window.taskTimerInstance.reset();
    }
  };
}
