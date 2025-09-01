from django.test import TestCase
from django.contrib.auth.models import User
from django.core.exceptions import ValidationError
from django.db import IntegrityError
from datetime import datetime, timedelta
from django.utils import timezone

from api.models import (
    Property, Profile, UserRole, Task, Booking, PropertyOwnership,
    TaskImage, Device, Notification, NotificationVerb, TaskChecklist,
    ChecklistResponse
)
from .base import BaseTestCase


class PropertyModelTest(BaseTestCase):
    """Test Property model functionality"""
    
    def test_property_creation(self):
        """Test creating a property"""
        property_count = Property.objects.count()
        Property.objects.create(name='New Test Property')
        self.assertEqual(Property.objects.count(), property_count + 1)
    
    def test_property_str_representation(self):
        """Test property string representation"""
        self.assertEqual(str(self.property1), 'Test Property 1')
    
    def test_property_name_required(self):
        """Test that property name is required"""
        with self.assertRaises(IntegrityError):
            Property.objects.create(name=None)


class ProfileModelTest(BaseTestCase):
    """Test Profile model functionality"""
    
    def test_profile_creation(self):
        """Test creating a profile"""
        user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='testpass123'
        )
        profile = Profile.objects.create(user=user, role=UserRole.STAFF)
        self.assertEqual(profile.role, UserRole.STAFF)
        self.assertEqual(profile.timezone, 'UTC')
    
    def test_profile_str_representation(self):
        """Test profile string representation"""
        profile = Profile.objects.get(user=self.staff_user)
        expected = f"Profile for {self.staff_user.username}"
        self.assertEqual(str(profile), expected)


class TaskModelTest(BaseTestCase):
    """Test Task model functionality"""
    
    def setUp(self):
        super().setUp()
        self.booking = Booking.objects.create(
            property=self.property1,
            check_in_date=timezone.now().date(),
            check_out_date=timezone.now().date() + timedelta(days=3),
            guest_name='Test Guest',
            guest_contact='test@guest.com'
        )
    
    def test_task_creation(self):
        """Test creating a task"""
        task = Task.objects.create(
            property=self.property1,
            booking=self.booking,
            title='Test Task',
            description='Test task description',
            task_type='cleaning',
            created_by=self.admin_user,
            assigned_to=self.staff_user
        )
        self.assertEqual(task.title, 'Test Task')
        self.assertEqual(task.status, 'pending')  # Default status
        self.assertEqual(task.property, self.property1)
    
    def test_task_str_representation(self):
        """Test task string representation"""
        task = Task.objects.create(
            property=self.property1,
            title='Test Task',
            created_by=self.admin_user
        )
        expected = f"Task: Test Task (pending)"
        self.assertEqual(str(task), expected)
    
    def test_task_status_choices(self):
        """Test task status validation"""
        task = Task.objects.create(
            property=self.property1,
            title='Test Task',
            created_by=self.admin_user,
            status='completed'
        )
        self.assertEqual(task.status, 'completed')


class BookingModelTest(BaseTestCase):
    """Test Booking model functionality"""
    
    def test_booking_creation(self):
        """Test creating a booking"""
        booking = Booking.objects.create(
            property=self.property1,
            check_in_date=timezone.now().date(),
            check_out_date=timezone.now().date() + timedelta(days=2),
            guest_name='Test Guest',
            guest_contact='guest@example.com'
        )
        self.assertEqual(booking.guest_name, 'Test Guest')
        self.assertEqual(booking.status, 'confirmed')  # Default status
    
    def test_booking_str_representation(self):
        """Test booking string representation"""
        booking = Booking.objects.create(
            property=self.property1,
            check_in_date=timezone.now().date(),
            check_out_date=timezone.now().date() + timedelta(days=2),
            guest_name='John Doe'
        )
        self.assertIn('John Doe', str(booking))
        self.assertIn(self.property1.name, str(booking))
    
    def test_booking_date_validation(self):
        """Test booking date validation"""
        # Check-out date should be after check-in date
        with self.assertRaises(ValidationError):
            booking = Booking(
                property=self.property1,
                check_in_date=timezone.now().date() + timedelta(days=2),
                check_out_date=timezone.now().date(),  # Earlier than check-in
                guest_name='Test Guest'
            )
            booking.full_clean()


class PropertyOwnershipModelTest(BaseTestCase):
    """Test PropertyOwnership model functionality"""
    
    def test_property_ownership_creation(self):
        """Test creating property ownership"""
        ownership = PropertyOwnership.objects.create(
            property=self.property1,
            user=self.manager_user,
            ownership_type='manager',
            can_edit=True
        )
        self.assertEqual(ownership.ownership_type, 'manager')
        self.assertTrue(ownership.can_edit)
    
    def test_property_ownership_unique_constraint(self):
        """Test unique constraint on property ownership"""
        PropertyOwnership.objects.create(
            property=self.property1,
            user=self.manager_user,
            ownership_type='manager'
        )
        
        # Should not be able to create duplicate ownership
        with self.assertRaises(IntegrityError):
            PropertyOwnership.objects.create(
                property=self.property1,
                user=self.manager_user,
                ownership_type='manager'
            )
    
    def test_property_ownership_str_representation(self):
        """Test property ownership string representation"""
        ownership = PropertyOwnership.objects.create(
            property=self.property1,
            user=self.manager_user,
            ownership_type='viewer'
        )
        expected = f"{self.manager_user} → {self.property1} (viewer)"
        self.assertEqual(str(ownership), expected)


class DeviceModelTest(BaseTestCase):
    """Test Device model for push notifications"""
    
    def test_device_creation(self):
        """Test creating a device"""
        device = Device.objects.create(
            user=self.staff_user,
            token='test_fcm_token_123'
        )
        self.assertEqual(device.user, self.staff_user)
        self.assertEqual(device.token, 'test_fcm_token_123')
    
    def test_device_str_representation(self):
        """Test device string representation"""
        device = Device.objects.create(
            user=self.staff_user,
            token='test_token'
        )
        expected = f"Device for {self.staff_user.username}"
        self.assertEqual(str(device), expected)


class NotificationModelTest(BaseTestCase):
    """Test Notification model functionality"""
    
    def setUp(self):
        super().setUp()
        self.booking = Booking.objects.create(
            property=self.property1,
            check_in_date=timezone.now().date(),
            check_out_date=timezone.now().date() + timedelta(days=2),
            guest_name='Test Guest'
        )
        self.task = Task.objects.create(
            property=self.property1,
            booking=self.booking,
            title='Test Task',
            created_by=self.admin_user,
            assigned_to=self.staff_user
        )
    
    def test_notification_creation(self):
        """Test creating a notification"""
        notification = Notification.objects.create(
            user=self.staff_user,
            task=self.task,
            verb=NotificationVerb.ASSIGNED
        )
        self.assertEqual(notification.user, self.staff_user)
        self.assertEqual(notification.task, self.task)
        self.assertEqual(notification.verb, NotificationVerb.ASSIGNED)
        self.assertFalse(notification.read)
    
    def test_notification_str_representation(self):
        """Test notification string representation"""
        notification = Notification.objects.create(
            user=self.staff_user,
            task=self.task,
            verb=NotificationVerb.ASSIGNED
        )
        self.assertIn(self.staff_user.username, str(notification))
        self.assertIn('assigned', str(notification))
