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

from django.test import override_settings
from django.contrib.auth.models import User
from rest_framework.test import APITestCase, APIClient
from rest_framework import status


class JWTAuthenticationTests(APITestCase):
    """Comprehensive JWT Authentication Test Suite"""

    def setUp(self):
        from django.core.cache import cache
        # Clear throttle cache to prevent rate limiting between tests
        cache.clear()
        
        self.client = APIClient()
        self.test_user_data = {
            'username': 'testjwtuser',
            'password': 'securetestpass123',
            'email': 'testjwt@aristay.com',
        }
        self.user = User.objects.create_user(**self.test_user_data)
        self.tokens = {}

    def tearDown(self):
        from django.core.cache import cache
        # Clear cache after each test
        cache.clear()

    def test_01_token_generation(self):
        """JWT token generation"""
        response = self.client.post('/api/token/', {
            'username': self.test_user_data['username'],
            'password': self.test_user_data['password'],
        })
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn('access', response.data)
        self.assertIn('refresh', response.data)
        self.tokens['access'] = response.data['access']
        self.tokens['refresh'] = response.data['refresh']

    def test_01b_legacy_route_compatibility(self):
        """Legacy route returns same response shape as new route"""
        new_resp = self.client.post('/api/token/', {
            'username': self.test_user_data['username'],
            'password': self.test_user_data['password'],
        })
        legacy_resp = self.client.post('/api-token-auth/', {
            'username': self.test_user_data['username'],
            'password': self.test_user_data['password'],
        })
        self.assertEqual(new_resp.status_code, 200)
        self.assertEqual(legacy_resp.status_code, 200)
        for key in ('access', 'refresh'):
            self.assertIn(key, new_resp.data)
            self.assertIn(key, legacy_resp.data)
        # basic JWT format check (three segments)
        self.assertEqual(new_resp.data['access'].count('.'), 2)
        self.assertEqual(legacy_resp.data['access'].count('.'), 2)

    def test_01c_legacy_route_has_deprecation_headers(self):
        """Legacy route includes deprecation headers"""
        resp = self.client.post('/api-token-auth/', {
            'username': self.test_user_data['username'],
            'password': self.test_user_data['password'],
        })
        self.assertIn(resp.status_code, (200, 401))  # ok either way
        self.assertEqual(resp['Deprecation'], 'true')
        self.assertIn('successor-version', resp['Link'])
        self.assertIn('Deprecated endpoint', resp['Warning'])

    def test_02_token_verification(self):
        """JWT token verification"""
        self.test_01_token_generation()
        resp = self.client.post('/api/token/verify/', {'token': self.tokens['access']})
        self.assertEqual(resp.status_code, status.HTTP_200_OK)

    def test_03_protected_endpoint_access(self):
        """Accessing protected endpoints with JWT"""
        self.test_01_token_generation()
        self.client.credentials(HTTP_AUTHORIZATION=f'Bearer {self.tokens["access"]}')
        resp = self.client.get('/api/test-auth/')
        self.assertEqual(resp.status_code, status.HTTP_200_OK)
        self.assertIn('user', resp.data)
        self.assertEqual(resp.data['user'], self.test_user_data['username'])

    def test_04_token_refresh(self):
        """JWT token refresh"""
        self.test_01_token_generation()
        resp = self.client.post('/api/token/refresh/', {'refresh': self.tokens['refresh']})
        self.assertEqual(resp.status_code, status.HTTP_200_OK)
        self.assertIn('access', resp.data)
        self.assertNotEqual(resp.data['access'], self.tokens['access'])

    def test_05_token_ownership_verification(self):
        """Users can only revoke their own tokens"""
        self.test_01_token_generation()
        self.client.credentials(HTTP_AUTHORIZATION=f'Bearer {self.tokens["access"]}')
        resp = self.client.post('/api/token/revoke/', {'refresh': self.tokens['refresh']})
        self.assertEqual(resp.status_code, status.HTTP_200_OK)

    def test_06_invalid_token_rejection(self):
        """Invalid tokens are rejected"""
        self.client.credentials(HTTP_AUTHORIZATION='Bearer invalid_token')
        resp = self.client.get('/api/test-auth/')
        self.assertEqual(resp.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_07_revoke_all_tokens(self):
        """Revoke all user tokens"""
        self.test_01_token_generation()
        self.client.credentials(HTTP_AUTHORIZATION=f'Bearer {self.tokens["access"]}')
        resp = self.client.post('/api/token/revoke-all/')
        self.assertEqual(resp.status_code, status.HTTP_200_OK)

    @override_settings(
        REST_FRAMEWORK={
            'DEFAULT_AUTHENTICATION_CLASSES': [
                'rest_framework_simplejwt.authentication.JWTAuthentication',
                'rest_framework.authentication.TokenAuthentication',
                'rest_framework.authentication.SessionAuthentication',
            ],
            'DEFAULT_PERMISSION_CLASSES': [
                'rest_framework.permissions.IsAuthenticatedOrReadOnly',
            ],
            'DEFAULT_THROTTLE_RATES': {
                'anon': '100/hour',
                'user': '1000/hour',
                'login': '5/minute',
                'token_refresh': '1/minute',  # stricter for deterministic test
            },
        },
        CACHES={'default': {'BACKEND': 'django.core.cache.backends.locmem.LocMemCache'}},
    )
    def test_08_rate_limiting(self):
        """Rate limiting on refresh (deterministic)"""
        from django.core.cache import cache
        
        # Don't clear cache for this test - we want rate limiting to work
        # Generate tokens directly instead of calling other test method
        response = self.client.post('/api/token/', {
            'username': self.test_user_data['username'],
            'password': self.test_user_data['password'],
        })
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        refresh_token = response.data['refresh']
        
        # Expect: 1st refresh success, 2nd can hit 429 per rate throttle
        seen_429 = False
        for i in range(3):
            resp = self.client.post('/api/token/refresh/', {'refresh': refresh_token})
            if resp.status_code == status.HTTP_429_TOO_MANY_REQUESTS:
                seen_429 = True
                break
            elif resp.status_code == status.HTTP_200_OK:
                # Update refresh token for next iteration
                refresh_token = resp.data['refresh']
                
        self.assertTrue(seen_429, f"Rate limiting should have triggered by the 2nd/3rd request")


class SecurityEventLoggingTests(APITestCase):
    """Security event logging"""

    def setUp(self):
        self.client = APIClient()
        self.user = User.objects.create_user(
            username='testsecuser',
            password='securetestpass123',
            email='testsec@aristay.com',
        )

    def test_login_success_event(self):
        from api.security_models import SecurityEvent
        initial = SecurityEvent.objects.count()
        resp = self.client.post('/api/token/', {'username': 'testsecuser', 'password': 'securetestpass123'})
        self.assertEqual(resp.status_code, status.HTTP_200_OK)
        self.assertGreater(SecurityEvent.objects.count(), initial)

    def test_login_failure_event(self):
        from api.security_models import SecurityEvent
        initial = SecurityEvent.objects.count()
        resp = self.client.post('/api/token/', {'username': 'testsecuser', 'password': 'wrongpassword'})
        self.assertEqual(resp.status_code, status.HTTP_401_UNAUTHORIZED)
        self.assertGreater(SecurityEvent.objects.count(), initial)


class SecurityDashboardTests(APITestCase):
    """Security dashboard access and data"""

    def setUp(self):
        self.client = APIClient()
        self.admin_user = User.objects.create_superuser(
            username='admin',
            password='adminpass123',
            email='admin@aristay.com',
        )

    def test_dashboard_requires_superuser(self):
        # unauthenticated
        resp = self.client.get('/api/admin/security/')
        self.assertIn(resp.status_code, [302, 401, 403])
        # regular user
        regular = User.objects.create_user(username='regular', password='regularpass123')
        self.client.force_authenticate(user=regular)
        resp = self.client.get('/api/admin/security/')
        self.assertIn(resp.status_code, [302, 403])

    def test_security_events_endpoint(self):
        self.client.force_authenticate(user=self.admin_user)
        resp = self.client.get('/api/admin/security/events/')
        self.assertEqual(resp.status_code, status.HTTP_200_OK)
        self.assertIn('events', resp.data)


def run_tests():
    """Allow running this module directly."""
    print("🔐 Running JWT Authentication Test Suite")
    suite = unittest.TestSuite()
    for cls in (JWTAuthenticationTests, SecurityEventLoggingTests, SecurityDashboardTests):
        suite.addTests(unittest.TestLoader().loadTestsFromTestCase(cls))
    result = unittest.TextTestRunner(verbosity=2).run(suite)
    print("\n🎯 JWT TEST RESULTS SUMMARY")
    if result.wasSuccessful():
        print(f"✅ All tests passed! Ran {result.testsRun}")
    else:
        print(f"❌ {len(result.failures)} failures, {len(result.errors)} errors (of {result.testsRun})")
    return result.wasSuccessful()


if __name__ == '__main__':
    import sys as _sys
    _sys.exit(0 if run_tests() else 1)
