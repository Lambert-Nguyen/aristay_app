"""
Calendar API Template Integration Tests
Tests for calendar API endpoints and template integration
"""
import pytest
from django.test import TestCase, Client, override_settings
from django.contrib.auth import get_user_model
from api.models import Property, Task, Booking, Profile
from django.utils import timezone
from datetime import timedelta

User = get_user_model()


@override_settings(
    AUTHENTICATION_BACKENDS=[
        'django.contrib.auth.backends.ModelBackend',
    ]
)
class CalendarAPITemplateIntegrationTestCase(TestCase):
    """Test cases for Calendar API and template integration"""
    
    def setUp(self):
        """Set up test data"""
        self.client = Client()
        
        # Create test users
        self.manager = User.objects.create_user(
            'manager', 'manager@test.com', 'password123'
        )
        
        self.staff = User.objects.create_user(
            'staff', 'staff@test.com', 'password123'
        )
        
        # Create profiles
        Profile.objects.get_or_create(
            user=self.manager,
            defaults={'role': 'manager', 'timezone': 'UTC'}
        )
        Profile.objects.get_or_create(
            user=self.staff,
            defaults={'role': 'staff', 'timezone': 'UTC'}
        )
        
        # Create test property
        self.property = Property.objects.create(
            name='Test Property',
            address='123 Test St'
        )
        
        # Create test task
        self.task = Task.objects.create(
            title='Test Task',
            property_ref=self.property,
            due_date=timezone.now() + timedelta(days=1),
            status='pending',
            created_by=self.manager
        )
        
        # Create test booking
        self.booking = Booking.objects.create(
            property=self.property,
            check_in_date=timezone.now().date(),
            check_out_date=(timezone.now() + timedelta(days=2)).date(),
            guest_name='Test Guest',
            status='confirmed'
        )
    
    def test_calendar_events_api_returns_data(self):
        """Test that calendar events API returns proper data"""
        self.client.force_login(self.manager)
        response = self.client.get('/api/calendar/events/')
        
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertIsInstance(data, list)
        
        # Should contain both task and booking events
        event_types = [event.get('type') for event in data]
        self.assertIn('task', event_types)
        self.assertIn('booking', event_types)
    
    def test_calendar_events_api_contains_required_fields(self):
        """Test that calendar events API contains required fields"""
        self.client.force_login(self.manager)
        response = self.client.get('/api/calendar/events/')
        
        self.assertEqual(response.status_code, 200)
        data = response.json()
        
        if data:
            event = data[0]
            required_fields = ['id', 'title', 'start', 'type', 'status', 'color']
            for field in required_fields:
                self.assertIn(field, event)
    
    def test_calendar_tasks_api_returns_tasks(self):
        """Test that calendar tasks API returns task data"""
        self.client.force_login(self.manager)
        response = self.client.get('/api/calendar/tasks/')
        
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertIsInstance(data, list)
        
        if data:
            task = data[0]
            self.assertIn('id', task)
            self.assertIn('title', task)
            self.assertIn('due_date', task)
            self.assertIn('status', task)
    
    def test_calendar_bookings_api_returns_bookings(self):
        """Test that calendar bookings API returns booking data"""
        self.client.force_login(self.manager)
        response = self.client.get('/api/calendar/bookings/')
        
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertIsInstance(data, list)
        
        if data:
            booking = data[0]
            self.assertIn('id', booking)
            self.assertIn('property_name', booking)
            self.assertIn('check_in_date', booking)
            self.assertIn('check_out_date', booking)
            self.assertIn('status', booking)
    
    def test_calendar_properties_api_returns_properties(self):
        """Test that calendar properties API returns property data"""
        self.client.force_login(self.manager)
        response = self.client.get('/api/calendar/properties/')
        
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertIsInstance(data, list)
        
        if data:
            property_data = data[0]
            self.assertIn('id', property_data)
            self.assertIn('name', property_data)
    
    def test_calendar_users_api_returns_users(self):
        """Test that calendar users API returns user data"""
        self.client.force_login(self.manager)
        response = self.client.get('/api/calendar/users/')
        
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertIsInstance(data, list)
        
        if data:
            user_data = data[0]
            self.assertIn('id', user_data)
            self.assertIn('username', user_data)
    
    def test_calendar_day_events_api_returns_day_events(self):
        """Test that calendar day events API returns day-specific events"""
        self.client.force_login(self.manager)
        
        # Test with today's date
        today = timezone.now().date()
        response = self.client.get(f'/api/calendar/day_events/?date={today}')
        
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertIn('date', data)
        self.assertIn('tasks', data)
        self.assertIn('bookings', data)
        self.assertIn('events', data)
        self.assertIn('total_events', data)
    
    def test_calendar_events_api_with_filters(self):
        """Test that calendar events API works with filters"""
        self.client.force_login(self.manager)
        
        # Test with property filter
        response = self.client.get(f'/api/calendar/events/?property_id={self.property.id}')
        self.assertEqual(response.status_code, 200)
        
        # Test with status filter
        response = self.client.get('/api/calendar/events/?status=pending')
        self.assertEqual(response.status_code, 200)
        
        # Test with date range
        start_date = timezone.now().date()
        end_date = start_date + timedelta(days=7)
        response = self.client.get(f'/api/calendar/events/?start_date={start_date}&end_date={end_date}')
        self.assertEqual(response.status_code, 200)
    
    def test_calendar_api_requires_authentication(self):
        """Test that calendar API requires authentication"""
        # Test without authentication
        response = self.client.get('/api/calendar/events/')
        self.assertEqual(response.status_code, 401)
        
        response = self.client.get('/api/calendar/tasks/')
        self.assertEqual(response.status_code, 401)
        
        response = self.client.get('/api/calendar/bookings/')
        self.assertEqual(response.status_code, 401)
    
    def test_calendar_api_permission_filtering(self):
        """Test that calendar API respects user permissions"""
        # Test with staff user (limited permissions)
        self.client.force_login(self.staff)
        response = self.client.get('/api/calendar/events/')
        
        self.assertEqual(response.status_code, 200)
        data = response.json()
        # Staff should see limited data based on permissions
        self.assertIsInstance(data, list)
    
    def test_calendar_template_api_integration(self):
        """Test that calendar template properly integrates with API"""
        self.client.force_login(self.manager)
        response = self.client.get('/api/portal/calendar/')
        
        self.assertEqual(response.status_code, 200)
        
        # Check that template contains API endpoint references
        self.assertContains(response, '/api/calendar/events/')
        self.assertContains(response, '/api/calendar/properties/')
        self.assertContains(response, '/api/calendar/users/')
        self.assertContains(response, '/api/calendar/day_events/')
    
    def test_calendar_template_javascript_api_calls(self):
        """Test that calendar template JavaScript makes proper API calls"""
        self.client.force_login(self.manager)
        response = self.client.get('/api/portal/calendar/')
        
        self.assertEqual(response.status_code, 200)
        
        # Check for JavaScript API call functions
        self.assertContains(response, 'fetch(')
        self.assertContains(response, 'loadCalendarEvents')
        self.assertContains(response, 'loadFilterOptions')
        self.assertContains(response, 'showDayEvents')
    
    def test_calendar_template_error_handling(self):
        """Test that calendar template handles API errors properly"""
        self.client.force_login(self.manager)
        response = self.client.get('/api/portal/calendar/')
        
        self.assertEqual(response.status_code, 200)
        
        # Check for error handling
        self.assertContains(response, 'catch')
        self.assertContains(response, 'console.error')
        self.assertContains(response, 'showError')
        self.assertContains(response, 'hideLoading')
    
    def test_calendar_template_loading_states(self):
        """Test that calendar template shows loading states"""
        self.client.force_login(self.manager)
        response = self.client.get('/api/portal/calendar/')
        
        self.assertEqual(response.status_code, 200)
        
        # Check for loading states
        self.assertContains(response, 'loadingIndicator')
        self.assertContains(response, 'Loading...')
        self.assertContains(response, 'showLoading')
        self.assertContains(response, 'hideLoading')
    
    def test_calendar_template_data_processing(self):
        """Test that calendar template processes API data correctly"""
        self.client.force_login(self.manager)
        response = self.client.get('/api/portal/calendar/')
        
        self.assertEqual(response.status_code, 200)
        
        # Check for data processing functions
        self.assertContains(response, 'processedEvents')
        self.assertContains(response, 'extendedProps')
        self.assertContains(response, 'toISOString')
        self.assertContains(response, 'split')
