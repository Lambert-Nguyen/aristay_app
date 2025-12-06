/**
 * API Client
 * Unified abstraction for all API requests with automatic CSRF handling
 * 
 * Usage:
 *   import { APIClient } from '../core/api-client.js';
 *   
 *   // JSON POST
 *   const data = await APIClient.post('/api/staff/tasks/123/status/', { status: 'completed' });
 *   
 *   // File upload
 *   const formData = new FormData();
 *   formData.append('photo', file);
 *   const result = await APIClient.upload('/api/staff/photos/upload/', formData);
 */

import { CSRFManager } from './csrf.js';

export class APIClient {
  /**
   * Base request method
   * @param {string} url - API endpoint URL
   * @param {Object} options - Fetch options
   * @returns {Promise<Object>} Response JSON
   */
  static async request(url, options = {}) {
    const defaults = {
      method: 'GET',
      headers: {},
      credentials: 'same-origin'
    };
    
    const config = { ...defaults, ...options };
    
    // Add CSRF token for mutating requests
    if (['POST', 'PUT', 'PATCH', 'DELETE'].includes(config.method)) {
      config.headers = {
        ...config.headers,
        ...CSRFManager.getFetchHeaders()
      };
    }
    
    // Add Content-Type for JSON (but NOT for FormData!)
    if (config.body && !(config.body instanceof FormData)) {
      config.headers['Content-Type'] = 'application/json';
    }
    
    try {
      const response = await fetch(url, config);
      
      // Handle non-OK responses
      if (!response.ok) {
        let errorMessage = `HTTP ${response.status}`;
        
        try {
          const errorData = await response.json();
          errorMessage = errorData.error || errorData.message || errorMessage;
        } catch {
          // If JSON parsing fails, use status text
          errorMessage = response.statusText || errorMessage;
        }
        
        throw new APIError(errorMessage, response.status);
      }
      
      // Handle 204 No Content
      if (response.status === 204) {
        return { success: true };
      }
      
      return await response.json();
      
    } catch (error) {
      if (error instanceof APIError) {
        throw error;
      }
      
      // Network errors, CORS issues, etc.
      console.error('[APIClient] Request failed:', error);
      throw new APIError('Network request failed. Please check your connection.', 0);
    }
  }
  
  /**
   * GET request
   * @param {string} url - API endpoint URL
   * @param {Object} params - URL query parameters
   * @returns {Promise<Object>} Response JSON
   */
  static async get(url, params = {}) {
    const queryString = new URLSearchParams(params).toString();
    const fullUrl = queryString ? `${url}?${queryString}` : url;
    return this.request(fullUrl, { method: 'GET' });
  }
  
  /**
   * POST request with JSON body
   * @param {string} url - API endpoint URL
   * @param {Object} data - Request body
   * @returns {Promise<Object>} Response JSON
   */
  static async post(url, data) {
    return this.request(url, {
      method: 'POST',
      body: JSON.stringify(data)
    });
  }
  
  /**
   * PUT request with JSON body
   * @param {string} url - API endpoint URL
   * @param {Object} data - Request body
   * @returns {Promise<Object>} Response JSON
   */
  static async put(url, data) {
    return this.request(url, {
      method: 'PUT',
      body: JSON.stringify(data)
    });
  }
  
  /**
   * PATCH request with JSON body
   * @param {string} url - API endpoint URL
   * @param {Object} data - Request body
   * @returns {Promise<Object>} Response JSON
   */
  static async patch(url, data) {
    return this.request(url, {
      method: 'PATCH',
      body: JSON.stringify(data)
    });
  }
  
  /**
   * DELETE request
   * @param {string} url - API endpoint URL
   * @returns {Promise<Object>} Response JSON
   */
  static async delete(url) {
    return this.request(url, { method: 'DELETE' });
  }
  
  /**
   * Upload files with multipart/form-data
   * @param {string} url - API endpoint URL
   * @param {FormData} formData - Form data with files
   * @returns {Promise<Object>} Response JSON
   */
  static async upload(url, formData) {
    if (!(formData instanceof FormData)) {
      throw new Error('upload() requires FormData instance');
    }
    
    return this.request(url, {
      method: 'POST',
      body: formData
      // Note: Content-Type is automatically set by browser for FormData
    });
  }
}

/**
 * Custom API Error class
 */
export class APIError extends Error {
  constructor(message, status) {
    super(message);
    this.name = 'APIError';
    this.status = status;
  }
}

// Expose globally for debugging
if (typeof window !== 'undefined') {
  window.APIClient = APIClient;
  window.APIError = APIError;
}
