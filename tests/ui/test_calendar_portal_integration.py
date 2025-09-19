"""
Calendar Portal Integration Tests
Tests for calendar integration with portal templates
"""
import pytest
from django.test import TestCase, Client, override_settings
from django.contrib.auth import get_user_model

User = get_user_model()


@override_settings(
    AUTHENTICATION_BACKENDS=[
        'django.contrib.auth.backends.ModelBackend',
    ]
)
class CalendarPortalIntegrationTestCase(TestCase):
    """Test cases for Calendar portal integration"""
    
    def setUp(self):
        """Set up test data"""
        self.client = Client()
        
        # Create test users
        self.superuser = User.objects.create_superuser(
            'admin', 'admin@test.com', 'password123'
        )
        
        self.manager = User.objects.create_user(
            'manager', 'manager@test.com', 'password123'
        )
        
        # Create profiles
        from api.models import Profile
        Profile.objects.get_or_create(
            user=self.manager,
            defaults={'role': 'manager', 'timezone': 'UTC'}
        )
    
    def test_portal_home_contains_calendar_card(self):
        """Test that portal home contains calendar card"""
        self.client.force_login(self.manager)
        response = self.client.get('/api/portal/')
        
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Calendar View')
        self.assertContains(response, 'Open Calendar')
        self.assertContains(response, '/api/portal/calendar/')
    
    def test_portal_navigation_contains_calendar_link(self):
        """Test that portal navigation contains calendar link"""
        self.client.force_login(self.manager)
        response = self.client.get('/api/portal/')
        
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, '📅 Calendar')
        self.assertContains(response, 'href="/api/portal/calendar/"')
    
    def test_portal_calendar_extends_base_template(self):
        """Test that portal calendar extends base template"""
        self.client.force_login(self.manager)
        response = self.client.get('/api/portal/calendar/')
        
        self.assertEqual(response.status_code, 200)
        # Check for portal base template elements
        self.assertContains(response, 'portal-container')
        self.assertContains(response, 'portal-header')
    
    def test_calendar_card_styling(self):
        """Test that calendar card has proper styling"""
        self.client.force_login(self.manager)
        response = self.client.get('/api/portal/')
        
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'text-align: center')
        self.assertContains(response, 'padding: 1.5rem')
        self.assertContains(response, 'font-size: 2.5rem')
    
    def test_calendar_navigation_styling(self):
        """Test that calendar navigation has proper styling"""
        self.client.force_login(self.manager)
        response = self.client.get('/api/portal/')
        
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'button')
        self.assertContains(response, '📅')
    
    def test_calendar_access_permissions(self):
        """Test that calendar access respects permissions"""
        # Test with manager
        self.client.force_login(self.manager)
        response = self.client.get('/api/portal/calendar/')
        self.assertEqual(response.status_code, 200)
        
        # Test without authentication
        self.client.logout()
        response = self.client.get('/api/portal/calendar/')
        self.assertEqual(response.status_code, 302)  # Redirect to login
    
    def test_calendar_card_responsive_design(self):
        """Test that calendar card is responsive"""
        self.client.force_login(self.manager)
        response = self.client.get('/api/portal/')
        
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'width: 100%')
        self.assertContains(response, 'display: block')
    
    def test_calendar_integration_consistency(self):
        """Test that calendar integration is consistent across portal"""
        self.client.force_login(self.manager)
        
        # Test portal home
        home_response = self.client.get('/api/portal/')
        self.assertEqual(home_response.status_code, 200)
        
        # Test calendar page
        calendar_response = self.client.get('/api/portal/calendar/')
        self.assertEqual(calendar_response.status_code, 200)
        
        # Both should have consistent styling
        self.assertContains(home_response, 'portal-container')
        self.assertContains(calendar_response, 'portal-container')
