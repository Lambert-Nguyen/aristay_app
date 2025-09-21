"""
Test calendar URL generation fix
"""
import pytest
from django.test import TestCase
from django.urls import reverse
from django.contrib.auth import get_user_model
from rest_framework.test import APIClient
from rest_framework import status
from api.models import Task, Booking, Property, Profile
from tests.utils.timezone_helpers import create_task_dates, create_booking_dates

User = get_user_model()


@pytest.mark.django_db
class TestCalendarURLFix:
    """Test that calendar events generate correct URLs"""
    
    def test_calendar_events_task_url_generation(self):
        """Test that task events generate correct portal URLs"""
        # Create test data
        user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='testpass123'
        )
        
        # Create a property
        property_obj = Property.objects.create(
            name='Test Property',
            address='123 Test St'
        )
        
        # Create a task
        from django.utils import timezone
        due_date = create_task_dates(due_days=1)
        task = Task.objects.create(
            title='Test Task',
            description='Test Description',
            property_ref=property_obj,
            created_by=user,
            assigned_to=user,
            status='pending',
            due_date=due_date
        )
        
        # Test the calendar events endpoint
        client = APIClient()
        client.force_authenticate(user=user)
        
        response = client.get('/api/calendar/events/')
        assert response.status_code == status.HTTP_200_OK
        
        events = response.data
        task_events = [e for e in events if e['type'] == 'task']
        
        assert len(task_events) > 0
        
        # Check that the URL is correctly generated
        task_event = task_events[0]
        expected_url = reverse('portal-task-detail', args=[task.id])
        assert task_event['url'] == expected_url
        assert task_event['url'].startswith('/api/portal/tasks/')
    
    def test_calendar_events_booking_url_generation(self):
        """Test that booking events generate correct portal URLs"""
        # Create test data
        user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='testpass123'
        )
        
        # Create a property
        property_obj = Property.objects.create(
            name='Test Property',
            address='123 Test St'
        )
        
        # Create a booking
        from django.utils import timezone
        check_in, check_out = create_booking_dates(check_in_days=0, check_out_days=2)
        booking = Booking.objects.create(
            guest_name='Test Guest',
            property=property_obj,
            check_in_date=check_in,
            check_out_date=check_out,
            status='confirmed'
        )
        
        # Test the calendar events endpoint
        client = APIClient()
        client.force_authenticate(user=user)
        
        response = client.get('/api/calendar/events/')
        assert response.status_code == status.HTTP_200_OK
        
        events = response.data
        booking_events = [e for e in events if e['type'] == 'booking']
        
        assert len(booking_events) > 0
        
        # Check that the URL is correctly generated
        booking_event = booking_events[0]
        expected_url = reverse('portal-booking-detail', args=[property_obj.id, booking.id])
        assert booking_event['url'] == expected_url
        assert booking_event['url'].startswith('/api/portal/properties/')
        assert str(property_obj.id) in booking_event['url']
        assert str(booking.id) in booking_event['url']
    
    def test_calendar_day_events_api_url_generation(self):
        """Test that calendar_day_events_api generates correct URLs"""
        # Create test data
        user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='testpass123'
        )
        
        # Create a property
        property_obj = Property.objects.create(
            name='Test Property',
            address='123 Test St'
        )
        
        # Create a task for today
        from django.utils import timezone
        due_date = create_task_dates(due_days=0)
        
        task = Task.objects.create(
            title='Test Task Today',
            description='Test Description',
            property_ref=property_obj,
            created_by=user,
            assigned_to=user,
            status='pending',
            due_date=due_date
        )
        
        # Create a booking for today
        check_in, check_out = create_booking_dates(check_in_days=0, check_out_days=1)
        booking = Booking.objects.create(
            guest_name='Test Guest',
            property=property_obj,
            check_in_date=check_in,
            check_out_date=check_out,
            status='confirmed'
        )
        
        # Test the calendar day events API
        client = APIClient()
        client.force_authenticate(user=user)
        
        today = timezone.now().date()
        response = client.get(f'/api/calendar/day_events/?date={today}')
        assert response.status_code == status.HTTP_200_OK
        
        data = response.data
        events = data.get('events', [])
        
        # Check task event URL
        task_events = [e for e in events if e['type'] == 'task']
        if task_events:
            task_event = task_events[0]
            expected_url = reverse('portal-task-detail', args=[task.id])
            assert task_event['url'] == expected_url
        
        # Check booking event URL
        booking_events = [e for e in events if e['type'] == 'booking']
        if booking_events:
            booking_event = booking_events[0]
            expected_url = reverse('portal-booking-detail', args=[property_obj.id, booking.id])
            assert booking_event['url'] == expected_url
    
    def test_url_generation_with_missing_property(self):
        """Test URL generation handles missing property gracefully"""
        # Create test data
        user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='testpass123'
        )
        
        # Create a task without property
        task = Task.objects.create(
            title='Test Task No Property',
            description='Test Description',
            created_by=user,
            assigned_to=user,
            status='pending'
        )
        
        # Test the calendar events endpoint
        client = APIClient()
        client.force_authenticate(user=user)
        
        response = client.get('/api/calendar/events/')
        assert response.status_code == status.HTTP_200_OK
        
        events = response.data
        task_events = [e for e in events if e['type'] == 'task']
        
        # Should still generate URL even without property
        if task_events:
            task_event = task_events[0]
            expected_url = reverse('portal-task-detail', args=[task.id])
            assert task_event['url'] == expected_url
