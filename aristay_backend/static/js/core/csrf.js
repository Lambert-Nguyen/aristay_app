/**
 * CSRF Token Manager
 * Centralized CSRF token handling for all AJAX requests
 * 
 * Usage:
 *   import { CSRFManager } from '../core/csrf.js';
 *   const headers = CSRFManager.getFetchHeaders();
 */

export class CSRFManager {
  /**
   * Get CSRF token from DOM
   * Priority: 1) Hidden input 2) Meta tag
   * @returns {string} CSRF token value
   */
  static getToken() {
    // Priority 1: Check for hidden input (most common pattern)
    const input = document.querySelector('[name=csrfmiddlewaretoken]');
    if (input && input.value) {
      return input.value;
    }
    
    // Priority 2: Check for meta tag
    const meta = document.querySelector('meta[name="csrf-token"]');
    if (meta) {
      return meta.getAttribute('content') || '';
    }
    
    console.error('[CSRFManager] CSRF token not found in DOM');
    return '';
  }
  
  /**
   * Get headers object for fetch() requests
   * @returns {Object} Headers with X-CSRFToken
   */
  static getFetchHeaders() {
    return {
      'X-CSRFToken': this.getToken()
    };
  }
  
  /**
   * Validate that CSRF token exists
   * @returns {boolean} True if token exists
   */
  static hasToken() {
    return this.getToken().length > 0;
  }
}

// Expose globally for debugging
if (typeof window !== 'undefined') {
  window.CSRFManager = CSRFManager;
}
