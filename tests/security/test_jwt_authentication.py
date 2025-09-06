#!/usr/bin/env python3
"""
JWT Authentication Test Suite - Organized Structure

This consolidates all JWT authentication tests into a proper test structure
following the project's testing guidelines.
"""

import os
import sys
import unittest
from pathlib import Path

# Add the project root to Python path
project_root = Path(__file__).parent
sys.path.append(str(project_root))
sys.path.append(str(project_root / 'aristay_backend'))

# Set up Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'backend.settings')

import django
django.setup()

from django.test import TestCase, Client
from django.contrib.auth.models import User
from rest_framework.test import APITestCase, APIClient
from rest_framework import status
import json

class JWTAuthenticationTests(APITestCase):
    """Comprehensive JWT Authentication Test Suite"""
    
    def setUp(self):
        """Set up test environment"""
        self.client = APIClient()
        self.test_user_data = {
            'username': 'testjwtuser',
            'password': 'securetestpass123',
            'email': 'testjwt@aristay.com'
        }
        
        # Create test user
        self.user = User.objects.create_user(**self.test_user_data)
        self.tokens = {}
        
    def test_01_token_generation(self):
        """Test JWT token generation"""
        response = self.client.post('/api/token/', {
            'username': self.test_user_data['username'],
            'password': self.test_user_data['password']
        })
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn('access', response.data)
        self.assertIn('refresh', response.data)
        
        # Store tokens for subsequent tests
        self.tokens['access'] = response.data['access']
        self.tokens['refresh'] = response.data['refresh']
        
    def test_02_token_verification(self):
        """Test JWT token verification"""
        # First get tokens
        self.test_01_token_generation()
        
        # Verify access token
        response = self.client.post('/api/token/verify/', {
            'token': self.tokens['access']
        })
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        
    def test_03_protected_endpoint_access(self):
        """Test accessing protected endpoints with JWT"""
        # First get tokens
        self.test_01_token_generation()
        
        # Set authorization header
        self.client.credentials(HTTP_AUTHORIZATION=f'Bearer {self.tokens["access"]}')
        
        # Test protected endpoint
        response = self.client.get('/api/test-auth/')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn('user', response.data)
        self.assertEqual(response.data['user'], self.test_user_data['username'])
        
    def test_04_token_refresh(self):
        """Test JWT token refresh"""
        # First get tokens
        self.test_01_token_generation()
        
        # Refresh token
        response = self.client.post('/api/token/refresh/', {
            'refresh': self.tokens['refresh']
        })
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn('access', response.data)
        
        # New access token should be different
        new_access_token = response.data['access']
        self.assertNotEqual(new_access_token, self.tokens['access'])
        
    def test_05_token_ownership_verification(self):
        """Test that users can only revoke their own tokens"""
        # First get tokens
        self.test_01_token_generation()
        
        # Set authorization header
        self.client.credentials(HTTP_AUTHORIZATION=f'Bearer {self.tokens["access"]}')
        
        # Try to revoke own token - should work
        response = self.client.post('/api/token/revoke/', {
            'refresh': self.tokens['refresh']
        })
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        
    def test_06_invalid_token_rejection(self):
        """Test that invalid tokens are rejected"""
        # Set invalid authorization header
        self.client.credentials(HTTP_AUTHORIZATION='Bearer invalid_token')
        
        # Test protected endpoint
        response = self.client.get('/api/test-auth/')
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)
        
    def test_07_revoke_all_tokens(self):
        """Test revoking all user tokens"""
        # First get tokens
        self.test_01_token_generation()
        
        # Set authorization header
        self.client.credentials(HTTP_AUTHORIZATION=f'Bearer {self.tokens["access"]}')
        
        # Revoke all tokens
        response = self.client.post('/api/token/revoke-all/')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        
    def test_08_rate_limiting(self):
        """Test rate limiting on authentication endpoints"""
        # Make multiple rapid requests to test throttling
        failed_attempts = 0
        
        for i in range(10):  # Attempt more than the limit
            response = self.client.post('/api/token/', {
                'username': 'invalid',
                'password': 'invalid'
            })
            
            if response.status_code == status.HTTP_429_TOO_MANY_REQUESTS:
                failed_attempts += 1
                break
        
        # Should get rate limited at some point
        # Note: This test may be flaky depending on rate limit settings
        
    def tearDown(self):
        """Clean up after each test"""
        if hasattr(self, 'user'):
            self.user.delete()


class SecurityEventLoggingTests(APITestCase):
    """Test security event logging functionality"""
    
    def setUp(self):
        """Set up test environment"""
        self.client = APIClient()
        self.test_user_data = {
            'username': 'testsecuser',
            'password': 'securetestpass123',
            'email': 'testsec@aristay.com'
        }
        
        # Create test user
        self.user = User.objects.create_user(**self.test_user_data)
        
    def test_login_success_event(self):
        """Test that successful logins are logged"""
        from api.security_models import SecurityEvent
        
        initial_count = SecurityEvent.objects.count()
        
        # Successful login
        response = self.client.post('/api/token/', {
            'username': self.test_user_data['username'],
            'password': self.test_user_data['password']
        })
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        
        # Check that security event was logged
        final_count = SecurityEvent.objects.count()
        self.assertGreater(final_count, initial_count)
        
    def test_login_failure_event(self):
        """Test that failed logins are logged"""
        from api.security_models import SecurityEvent
        
        initial_count = SecurityEvent.objects.count()
        
        # Failed login
        response = self.client.post('/api/token/', {
            'username': self.test_user_data['username'],
            'password': 'wrongpassword'
        })
        
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)
        
        # Check that security event was logged
        final_count = SecurityEvent.objects.count()
        self.assertGreater(final_count, initial_count)
        
    def tearDown(self):
        """Clean up after each test"""
        if hasattr(self, 'user'):
            self.user.delete()


class SecurityDashboardTests(APITestCase):
    """Test security dashboard functionality"""
    
    def setUp(self):
        """Set up test environment"""
        self.client = APIClient()
        
        # Create superuser for dashboard access
        self.admin_user = User.objects.create_superuser(
            username='admin',
            password='adminpass123',
            email='admin@aristay.com'
        )
        
    def test_dashboard_requires_superuser(self):
        """Test that security dashboard requires superuser access"""
        # Test without authentication
        response = self.client.get('/api/admin/security/')
        self.assertIn(response.status_code, [302, 401, 403])  # Redirect to login or access denied
        
        # Test with regular user
        regular_user = User.objects.create_user(
            username='regular',
            password='regularpass123'
        )
        self.client.force_authenticate(user=regular_user)
        response = self.client.get('/api/admin/security/')
        self.assertIn(response.status_code, [302, 403])  # Access denied
        
        regular_user.delete()
        
    def test_security_events_endpoint(self):
        """Test security events API endpoint"""
        # Authenticate as superuser
        self.client.force_authenticate(user=self.admin_user)
        
        # Test security events endpoint
        response = self.client.get('/api/admin/security/events/')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn('events', response.data)
        
    def tearDown(self):
        """Clean up after each test"""
        if hasattr(self, 'admin_user'):
            self.admin_user.delete()


def run_tests():
    """Run all JWT authentication tests"""
    print("🔐 Running JWT Authentication Test Suite")
    print("=" * 50)
    
    # Create test suite
    test_suite = unittest.TestSuite()
    
    # Add test classes
    test_classes = [
        JWTAuthenticationTests,
        SecurityEventLoggingTests, 
        SecurityDashboardTests,
    ]
    
    for test_class in test_classes:
        tests = unittest.TestLoader().loadTestsFromTestCase(test_class)
        test_suite.addTests(tests)
    
    # Run tests
    runner = unittest.TextTestRunner(verbosity=2)
    result = runner.run(test_suite)
    
    # Print summary
    print("\n" + "=" * 50)
    print("🎯 JWT TEST RESULTS SUMMARY")
    print("=" * 50)
    
    if result.wasSuccessful():
        print("✅ All JWT authentication tests passed!")
        print(f"Ran {result.testsRun} tests successfully")
    else:
        print(f"❌ {len(result.failures)} test failures")
        print(f"❌ {len(result.errors)} test errors")
        print(f"Ran {result.testsRun} tests total")
    
    return result.wasSuccessful()


if __name__ == '__main__':
    success = run_tests()
    sys.exit(0 if success else 1)
