# tests/api/test_calendar_api.py
"""
Tests for calendar API endpoints
"""

import pytest
from django.test import TestCase
from django.urls import reverse
from django.utils import timezone
from datetime import datetime, timedelta
from rest_framework.test import APIClient
from rest_framework import status
from django.contrib.auth.models import User
from api.models import Task, Booking, Property, Profile
from api.calendar_serializers import CalendarEventSerializer


@pytest.mark.django_db
class CalendarAPITestCase(TestCase):
    """Test calendar API endpoints"""
    
    def setUp(self):
        """Set up test data"""
        self.client = APIClient()
        
        # Create test user
        self.user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='testpass123'
        )
        
        # Create user profile - use get_or_create to avoid unique constraint issues
        self.profile, created = Profile.objects.get_or_create(
            user=self.user,
            defaults={
                'role': 'manager',
                'timezone': 'UTC'
            }
        )
        
        # Create test property
        self.property = Property.objects.create(
            name='Test Property',
            address='123 Test St'
        )
        
        # Create test tasks
        self.task1 = Task.objects.create(
            title='Test Task 1',
            description='Test task description',
            property_ref=self.property,
            due_date=timezone.now() + timedelta(days=1),
            status='pending',
            created_by=self.user,
            assigned_to=self.user
        )
        
        self.task2 = Task.objects.create(
            title='Test Task 2',
            description='Another test task',
            property_ref=self.property,
            due_date=timezone.now() + timedelta(days=2),
            status='in-progress',
            created_by=self.user
        )
        
        # Create test bookings
        self.booking1 = Booking.objects.create(
            property=self.property,
            check_in_date=timezone.now() + timedelta(days=3),
            check_out_date=timezone.now() + timedelta(days=5),
            guest_name='John Doe',
            guest_contact='john@example.com',
            status='confirmed'
        )
        
        self.booking2 = Booking.objects.create(
            property=self.property,
            check_in_date=timezone.now() + timedelta(days=7),
            check_out_date=timezone.now() + timedelta(days=9),
            guest_name='Jane Smith',
            guest_contact='jane@example.com',
            status='booked'
        )
        
        # Authenticate user
        self.client.force_authenticate(user=self.user)
    
    def test_calendar_events_endpoint(self):
        """Test calendar events endpoint returns unified events"""
        url = reverse('calendar-events')
        response = self.client.get(url)
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIsInstance(response.data, list)
        
        # Check that we have both tasks and bookings
        event_types = [event['type'] for event in response.data]
        self.assertIn('task', event_types)
        self.assertIn('booking', event_types)
    
    def test_calendar_events_with_filters(self):
        """Test calendar events with filtering"""
        url = reverse('calendar-events')
        
        # Test property filter
        response = self.client.get(url, {'property_id': self.property.id})
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        
        # Test status filter
        response = self.client.get(url, {'status': 'pending'})
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        
        # Test date range filter
        start_date = timezone.now().date()
        end_date = start_date + timedelta(days=10)
        response = self.client.get(url, {
            'start_date': start_date.isoformat(),
            'end_date': end_date.isoformat()
        })
        self.assertEqual(response.status_code, status.HTTP_200_OK)
    
    def test_calendar_events_include_exclude(self):
        """Test calendar events include/exclude options"""
        url = reverse('calendar-events')
        
        # Test tasks only
        response = self.client.get(url, {'include_tasks': True, 'include_bookings': False})
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        event_types = [event['type'] for event in response.data]
        self.assertIn('task', event_types)
        self.assertNotIn('booking', event_types)
        
        # Test bookings only
        response = self.client.get(url, {'include_tasks': False, 'include_bookings': True})
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        event_types = [event['type'] for event in response.data]
        self.assertIn('booking', event_types)
        self.assertNotIn('task', event_types)
    
    def test_calendar_tasks_endpoint(self):
        """Test calendar tasks endpoint"""
        url = reverse('calendar-tasks')
        response = self.client.get(url)
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIsInstance(response.data, list)
        
        # Check task data structure
        if response.data:
            task = response.data[0]
            self.assertIn('id', task)
            self.assertIn('title', task)
            self.assertIn('status', task)
            self.assertIn('due_date', task)
    
    def test_calendar_bookings_endpoint(self):
        """Test calendar bookings endpoint"""
        url = reverse('calendar-bookings')
        response = self.client.get(url)
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIsInstance(response.data, list)
        
        # Check booking data structure
        if response.data:
            booking = response.data[0]
            self.assertIn('id', booking)
            self.assertIn('property_name', booking)
            self.assertIn('check_in_date', booking)
            self.assertIn('check_out_date', booking)
    
    def test_calendar_day_events_endpoint(self):
        """Test calendar day events endpoint"""
        # Test with a date that has events
        test_date = (timezone.now() + timedelta(days=1)).date()
        url = reverse('calendar-day-events')
        response = self.client.get(url, {'date': test_date.isoformat()})
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn('date', response.data)
        self.assertIn('tasks', response.data)
        self.assertIn('bookings', response.data)
        self.assertIn('total_events', response.data)
    
    def test_calendar_day_events_invalid_date(self):
        """Test calendar day events with invalid date"""
        url = reverse('calendar-day-events')
        response = self.client.get(url, {'date': 'invalid-date'})
        
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn('error', response.data)
    
    def test_calendar_day_events_missing_date(self):
        """Test calendar day events without date parameter"""
        url = reverse('calendar-day-events')
        response = self.client.get(url)
        
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn('error', response.data)
    
    def test_calendar_events_unauthorized(self):
        """Test calendar events without authentication"""
        self.client.force_authenticate(user=None)
        url = reverse('calendar-events')
        response = self.client.get(url)
        
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)
    
    def test_calendar_events_permission_filtering(self):
        """Test calendar events respect user permissions"""
        # Create a user without view permissions
        limited_user = User.objects.create_user(
            username='limiteduser',
            email='limited@example.com',
            password='testpass123'
        )
        
        limited_profile, created = Profile.objects.get_or_create(
            user=limited_user,
            defaults={
                'role': 'staff',
                'timezone': 'UTC'
            }
        )
        
        # Create a task assigned to the limited user
        limited_task = Task.objects.create(
            title='Limited User Task',
            description='Task for limited user',
            property_ref=self.property,
            due_date=timezone.now() + timedelta(days=1),
            status='pending',
            created_by=limited_user,
            assigned_to=limited_user
        )
        
        # Authenticate as limited user
        self.client.force_authenticate(user=limited_user)
        
        url = reverse('calendar-events')
        response = self.client.get(url)
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        
        # Should only see tasks the user is involved with
        task_titles = [event['title'] for event in response.data if event['type'] == 'task']
        self.assertIn('Limited User Task', task_titles)
        # Should not see tasks created by other users (unless they have view permissions)
        # This depends on the permission implementation


@pytest.mark.django_db
class CalendarSerializerTestCase(TestCase):
    """Test calendar serializers"""
    
    def test_calendar_event_serializer(self):
        """Test CalendarEventSerializer"""
        data = {
            'id': 1,
            'title': 'Test Event',
            'start': timezone.now().isoformat(),
            'end': (timezone.now() + timedelta(hours=2)).isoformat(),
            'allDay': False,
            'type': 'task',
            'status': 'pending',
            'color': '#ffc107',
            'property_name': 'Test Property',
            'guest_name': None,
            'assigned_to': 'testuser',
            'description': 'Test description',
            'url': '/tasks/1/'
        }
        
        serializer = CalendarEventSerializer(data=data)
        if not serializer.is_valid():
            print(f"Serializer errors: {serializer.errors}")
        self.assertTrue(serializer.is_valid())
        
        validated_data = serializer.validated_data
        self.assertEqual(validated_data['title'], 'Test Event')
        self.assertEqual(validated_data['type'], 'task')
        self.assertEqual(validated_data['status'], 'pending')


@pytest.mark.django_db
class CalendarHTMLViewTestCase(TestCase):
    """Test calendar HTML views"""
    
    def setUp(self):
        """Set up test data"""
        self.user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='testpass123'
        )
        
        self.profile, created = Profile.objects.get_or_create(
            user=self.user,
            defaults={
                'role': 'manager',
                'timezone': 'UTC'
            }
        )
        
        self.property = Property.objects.create(
            name='Test Property',
            address='123 Test St'
        )
    
    def test_calendar_view_authenticated(self):
        """Test calendar view with authenticated user"""
        self.client.force_login(self.user)
        response = self.client.get('/api/calendar/')
        
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Property Management Calendar')
        self.assertContains(response, 'FullCalendar')
    
    def test_calendar_view_unauthorized(self):
        """Test calendar view without authentication"""
        response = self.client.get('/api/calendar/')
        
        # Should redirect to login
        self.assertEqual(response.status_code, 302)
    
    def test_calendar_properties_api(self):
        """Test calendar properties API"""
        self.client.force_login(self.user)
        response = self.client.get('/api/calendar/properties/')
        
        self.assertEqual(response.status_code, 200)
        self.assertIsInstance(response.json(), list)
        
        if response.json():
            property_data = response.json()[0]
            self.assertIn('id', property_data)
            self.assertIn('name', property_data)
    
    def test_calendar_users_api(self):
        """Test calendar users API"""
        self.client.force_login(self.user)
        response = self.client.get('/api/calendar/users/')
        
        self.assertEqual(response.status_code, 200)
        self.assertIsInstance(response.json(), list)
        
        if response.json():
            user_data = response.json()[0]
            self.assertIn('id', user_data)
            self.assertIn('username', user_data)
    
    def test_calendar_stats_api(self):
        """Test calendar stats API"""
        self.client.force_login(self.user)
        response = self.client.get('/api/calendar/stats/')
        
        self.assertEqual(response.status_code, 200)
        stats = response.json()
        
        self.assertIn('total_tasks', stats)
        self.assertIn('total_bookings', stats)
        self.assertIn('pending_tasks', stats)
        self.assertIn('active_bookings', stats)
