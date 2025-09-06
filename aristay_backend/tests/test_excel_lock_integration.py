"""
Test Excel import service respects Task.is_locked_by_user field.
Agent's recommendation: "Import lock wiring: double-check the Excel import path respects Task.is_locked_by_user"
"""
from unittest.mock import Mock
from datetime import datetime
from django.test import TestCase
from django.contrib.auth import get_user_model
from django.utils import timezone
from api.models import Property, Booking, Task
from api.services.excel_import_service import ExcelImportService

User = get_user_model()


class ExcelImportLockTest(TestCase):
    """Test Excel import respects task lock mechanism."""
    
    def setUp(self):
        """Set up test data."""
        self.user = User.objects.create_user(
            username='test_importer',
            email='importer@test.com',
            password='testpass123'
        )
        
        self.property = Property.objects.create(
            name='Test Property',
            address='123 Test St, Test City, CA 12345',
            created_by=self.user
        )
        
        # Create booking with associated task
        self.booking = Booking.objects.create(
            property=self.property,
            guest_name='Test Guest',
            check_in_date=timezone.make_aware(datetime(2024, 9, 10)),  # Agent's fix: standard datetime
            check_out_date=timezone.make_aware(datetime(2024, 9, 12)),  # Agent's fix: standard datetime
            external_code='TEST001',
            external_status='Confirmed',
            nights=2,
            created_by=self.user,
            created_via='test'
        )
        
        # Create locked task associated with booking
        self.locked_task = Task.objects.create(
            title='Cleaning Task',
            description='Test cleaning',
            property=self.property,
            booking=self.booking,
            status='in-progress',  # Agent's fix: use hyphen to match STATUS_CHOICES
            is_locked_by_user=True,  # LOCKED by user
            created_by=self.user
        )
        
    def test_update_associated_task_respects_lock(self):
        """Test _update_associated_task method respects is_locked_by_user."""
        # Create service instance
        service = ExcelImportService(user=self.user)
        
        # Mock booking data with status change
        booking_data = {
            'external_status': 'Cancelled'
        }
        
        # Call _update_associated_task with locked task
        service._update_associated_task(self.booking, booking_data)
        
        # Verify locked task was NOT updated
        self.locked_task.refresh_from_db()
        self.assertEqual(self.locked_task.status, 'in-progress')  # Should remain unchanged
        self.assertTrue(self.locked_task.is_locked_by_user)
        
    def test_update_associated_task_updates_unlocked(self):
        """Test _update_associated_task method updates unlocked tasks."""
        # Unlock the task
        self.locked_task.is_locked_by_user = False
        self.locked_task.save()
        
        # Create service instance
        service = ExcelImportService(user=self.user)
        
        # Mock booking data with status change
        booking_data = {
            'external_status': 'Cancelled'
        }
        
        # Call _update_associated_task with unlocked task
        service._update_associated_task(self.booking, booking_data)
        
        # Verify unlocked task WAS updated
        self.locked_task.refresh_from_db()
        self.assertEqual(self.locked_task.status, 'canceled')  # Should be updated (American spelling)
        self.assertFalse(self.locked_task.is_locked_by_user)
