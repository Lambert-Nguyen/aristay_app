/**
 * Storage Manager
 * Wrapper for localStorage with error handling and JSON serialization
 * 
 * Usage:
 *   import { StorageManager } from '../core/storage.js';
 *   
 *   StorageManager.set('user_preferences', { theme: 'dark' });
 *   const prefs = StorageManager.get('user_preferences', { theme: 'light' });
 */

export class StorageManager {
  /**
   * Set item in localStorage with JSON serialization
   * @param {string} key - Storage key
   * @param {*} value - Value to store (will be JSON stringified)
   * @returns {boolean} Success status
   */
  static set(key, value) {
    try {
      const serialized = JSON.stringify(value);
      localStorage.setItem(key, serialized);
      return true;
    } catch (error) {
      console.error(`[StorageManager] Failed to set '${key}':`, error);
      return false;
    }
  }
  
  /**
   * Get item from localStorage with JSON parsing
   * @param {string} key - Storage key
   * @param {*} defaultValue - Default value if key doesn't exist
   * @returns {*} Parsed value or default
   */
  static get(key, defaultValue = null) {
    try {
      const item = localStorage.getItem(key);
      
      if (item === null) {
        return defaultValue;
      }
      
      return JSON.parse(item);
    } catch (error) {
      console.error(`[StorageManager] Failed to get '${key}':`, error);
      return defaultValue;
    }
  }
  
  /**
   * Remove item from localStorage
   * @param {string} key - Storage key
   * @returns {boolean} Success status
   */
  static remove(key) {
    try {
      localStorage.removeItem(key);
      return true;
    } catch (error) {
      console.error(`[StorageManager] Failed to remove '${key}':`, error);
      return false;
    }
  }
  
  /**
   * Clear all items from localStorage
   * @returns {boolean} Success status
   */
  static clear() {
    try {
      localStorage.clear();
      return true;
    } catch (error) {
      console.error('[StorageManager] Failed to clear storage:', error);
      return false;
    }
  }
  
  /**
   * Check if key exists in localStorage
   * @param {string} key - Storage key
   * @returns {boolean} True if key exists
   */
  static has(key) {
    return localStorage.getItem(key) !== null;
  }
  
  /**
   * Get all keys in localStorage
   * @returns {string[]} Array of keys
   */
  static keys() {
    try {
      return Object.keys(localStorage);
    } catch (error) {
      console.error('[StorageManager] Failed to get keys:', error);
      return [];
    }
  }
  
  /**
   * Get storage size in bytes (approximate)
   * @returns {number} Storage size
   */
  static size() {
    try {
      let total = 0;
      for (let key in localStorage) {
        if (localStorage.hasOwnProperty(key)) {
          total += localStorage[key].length + key.length;
        }
      }
      return total;
    } catch (error) {
      console.error('[StorageManager] Failed to calculate size:', error);
      return 0;
    }
  }
}

// Expose globally for debugging
if (typeof window !== 'undefined') {
  window.StorageManager = StorageManager;
}
