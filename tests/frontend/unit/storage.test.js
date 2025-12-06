/**
 * Unit tests for StorageManager
 */

import { StorageManager } from '../../../aristay_backend/static/js/core/storage.js';

describe('StorageManager', () => {
  beforeEach(() => {
    localStorage.clear();
  });
  
  afterEach(() => {
    localStorage.clear();
  });
  
  describe('set()', () => {
    test('stores string value', () => {
      const result = StorageManager.set('test_key', 'test_value');
      expect(result).toBe(true);
      expect(localStorage.getItem('test_key')).toBe('"test_value"');
    });
    
    test('stores object value', () => {
      const obj = { name: 'John', age: 30 };
      const result = StorageManager.set('user', obj);
      expect(result).toBe(true);
      
      const stored = JSON.parse(localStorage.getItem('user'));
      expect(stored).toEqual(obj);
    });
    
    test('stores array value', () => {
      const arr = [1, 2, 3, 4, 5];
      const result = StorageManager.set('numbers', arr);
      expect(result).toBe(true);
      
      const stored = JSON.parse(localStorage.getItem('numbers'));
      expect(stored).toEqual(arr);
    });
    
    test('stores boolean value', () => {
      StorageManager.set('is_active', true);
      const stored = JSON.parse(localStorage.getItem('is_active'));
      expect(stored).toBe(true);
    });
    
    test('stores null value', () => {
      StorageManager.set('nullable', null);
      const stored = JSON.parse(localStorage.getItem('nullable'));
      expect(stored).toBe(null);
    });
  });
  
  describe('get()', () => {
    test('retrieves stored value', () => {
      localStorage.setItem('test_key', JSON.stringify('test_value'));
      const value = StorageManager.get('test_key');
      expect(value).toBe('test_value');
    });
    
    test('retrieves object', () => {
      const obj = { name: 'Jane', role: 'admin' };
      localStorage.setItem('user', JSON.stringify(obj));
      
      const retrieved = StorageManager.get('user');
      expect(retrieved).toEqual(obj);
    });
    
    test('returns default value for non-existent key', () => {
      const defaultValue = { theme: 'light' };
      const value = StorageManager.get('preferences', defaultValue);
      expect(value).toEqual(defaultValue);
    });
    
    test('returns null by default for non-existent key', () => {
      const value = StorageManager.get('nonexistent');
      expect(value).toBe(null);
    });
  });
  
  describe('remove()', () => {
    test('removes stored value', () => {
      localStorage.setItem('test_key', '"test_value"');
      const result = StorageManager.remove('test_key');
      
      expect(result).toBe(true);
      expect(localStorage.getItem('test_key')).toBe(null);
    });
    
    test('returns true even if key does not exist', () => {
      const result = StorageManager.remove('nonexistent');
      expect(result).toBe(true);
    });
  });
  
  describe('clear()', () => {
    test('clears all storage', () => {
      StorageManager.set('key1', 'value1');
      StorageManager.set('key2', 'value2');
      StorageManager.set('key3', 'value3');
      
      const result = StorageManager.clear();
      expect(result).toBe(true);
      expect(localStorage.length).toBe(0);
    });
  });
  
  describe('has()', () => {
    test('returns true for existing key', () => {
      StorageManager.set('existing', 'value');
      expect(StorageManager.has('existing')).toBe(true);
    });
    
    test('returns false for non-existent key', () => {
      expect(StorageManager.has('nonexistent')).toBe(false);
    });
  });
  
  describe('keys()', () => {
    test('returns array of all keys', () => {
      StorageManager.set('key1', 'value1');
      StorageManager.set('key2', 'value2');
      StorageManager.set('key3', 'value3');
      
      const keys = StorageManager.keys();
      expect(keys).toEqual(['key1', 'key2', 'key3']);
    });
    
    test('returns empty array when storage is empty', () => {
      const keys = StorageManager.keys();
      expect(keys).toEqual([]);
    });
  });
  
  describe('size()', () => {
    test('returns approximate storage size', () => {
      StorageManager.set('small', 'x');
      const size = StorageManager.size();
      expect(size).toBeGreaterThan(0);
    });
    
    test('returns 0 for empty storage', () => {
      const size = StorageManager.size();
      expect(size).toBe(0);
    });
  });
});
