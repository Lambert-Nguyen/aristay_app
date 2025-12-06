/**
 * Unit tests for CSRFManager
 */

import { CSRFManager } from '../../../aristay_backend/static/js/core/csrf.js';

describe('CSRFManager', () => {
  beforeEach(() => {
    // Clear DOM before each test
    document.body.innerHTML = '';
  });
  
  describe('getToken()', () => {
    test('returns token from hidden input', () => {
      document.body.innerHTML = `
        <input type="hidden" name="csrfmiddlewaretoken" value="test-token-123" />
      `;
      
      const token = CSRFManager.getToken();
      expect(token).toBe('test-token-123');
    });
    
    test('returns token from meta tag when input not found', () => {
      document.body.innerHTML = `
        <meta name="csrf-token" content="meta-token-456" />
      `;
      
      const token = CSRFManager.getToken();
      expect(token).toBe('meta-token-456');
    });
    
    test('prioritizes input over meta tag', () => {
      document.body.innerHTML = `
        <input type="hidden" name="csrfmiddlewaretoken" value="input-token" />
        <meta name="csrf-token" content="meta-token" />
      `;
      
      const token = CSRFManager.getToken();
      expect(token).toBe('input-token');
    });
    
    test('returns empty string when no token found', () => {
      const token = CSRFManager.getToken();
      expect(token).toBe('');
    });
    
    test('handles empty input value', () => {
      document.body.innerHTML = `
        <input type="hidden" name="csrfmiddlewaretoken" value="" />
        <meta name="csrf-token" content="meta-token" />
      `;
      
      const token = CSRFManager.getToken();
      expect(token).toBe('meta-token');
    });
  });
  
  describe('getFetchHeaders()', () => {
    test('returns headers object with CSRF token', () => {
      document.body.innerHTML = `
        <input type="hidden" name="csrfmiddlewaretoken" value="test-token" />
      `;
      
      const headers = CSRFManager.getFetchHeaders();
      expect(headers).toEqual({
        'X-CSRFToken': 'test-token'
      });
    });
  });
  
  describe('hasToken()', () => {
    test('returns true when token exists', () => {
      document.body.innerHTML = `
        <input type="hidden" name="csrfmiddlewaretoken" value="test-token" />
      `;
      
      expect(CSRFManager.hasToken()).toBe(true);
    });
    
    test('returns false when token does not exist', () => {
      expect(CSRFManager.hasToken()).toBe(false);
    });
  });
});
