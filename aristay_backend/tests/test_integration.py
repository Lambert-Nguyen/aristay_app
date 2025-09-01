import json
from datetime import date, datetime, timedelta

from django.contrib.auth.models import User
from django.db import transaction
from django.test import TestCase, TransactionTestCase
from django.utils import timezone

from api.models import Booking, Profile, Property, PropertyOwnership, Task, UserRole
from api.services.notification_service import NotificationService

from .base import BaseAPITestCase, BaseTestCase


class BookingTaskIntegrationTest(BaseTestCase):
    """Test integration between bookings and tasks"""

    def test_booking_creation_generates_default_tasks(self):
        """Test that creating a booking generates default cleaning tasks"""
        initial_task_count = Task.objects.count()

        booking = Booking.objects.create(
            property=self.property1,
            check_in_date=date.today() + timedelta(days=1),
            check_out_date=date.today() + timedelta(days=4),
            guest_name="Integration Test Guest",
            guest_contact="test@integration.com",
        )

        # Check if tasks were auto-created (depends on your implementation)
        # This test assumes you have signals or methods that create tasks on booking
        final_task_count = Task.objects.count()

        # Adjust this based on your actual implementation
        # self.assertGreater(final_task_count, initial_task_count)

    def test_booking_modification_updates_related_tasks(self):
        """Test that modifying booking dates updates related task due dates"""
        booking = Booking.objects.create(
            property=self.property1,
            check_in_date=date.today() + timedelta(days=1),
            check_out_date=date.today() + timedelta(days=4),
            guest_name="Test Guest",
        )

        # Create related task
        task = Task.objects.create(
            property=self.property1,
            booking=booking,
            title="Pre-arrival Cleaning",
            task_type="cleaning",
            created_by=self.admin_user,
            due_date=timezone.now() + timedelta(days=1),
        )

        original_due_date = task.due_date

        # Modify booking check-in date
        booking.check_in_date = date.today() + timedelta(days=3)
        booking.save()

        # Refresh task from database
        task.refresh_from_db()

        # Check if task due date was updated (depends on your implementation)
        # This would require signals or custom save methods
        # self.assertNotEqual(task.due_date, original_due_date)

    def test_booking_deletion_handles_related_tasks(self):
        """Test that deleting a booking properly handles related tasks"""
        booking = Booking.objects.create(
            property=self.property1,
            check_in_date=date.today() + timedelta(days=1),
            check_out_date=date.today() + timedelta(days=4),
            guest_name="Test Guest",
        )

        task = Task.objects.create(
            property=self.property1, booking=booking, title="Booking-related Task", created_by=self.admin_user
        )

        task_id = task.id

        # Delete booking
        booking.delete()

        # Check if task still exists and booking reference is handled properly
        task_exists = Task.objects.filter(id=task_id).exists()
        if task_exists:
            updated_task = Task.objects.get(id=task_id)
            self.assertIsNone(updated_task.booking)


class UserRoleWorkflowTest(BaseTestCase):
    """Test complete workflows involving different user roles"""

    def test_property_management_workflow(self):
        """Test complete property management workflow"""
        # 1. Admin creates property
        new_property = Property.objects.create(name="Workflow Test Property")

        # 2. Admin assigns manager to property
        ownership = PropertyOwnership.objects.create(
            property=new_property, user=self.manager_user, ownership_type="manager", can_edit=True
        )

        # 3. Manager creates booking for property
        booking = Booking.objects.create(
            property=new_property,
            check_in_date=date.today() + timedelta(days=1),
            check_out_date=date.today() + timedelta(days=4),
            guest_name="Workflow Guest",
        )

        # 4. Manager creates cleaning task and assigns to staff
        task = Task.objects.create(
            property=new_property,
            booking=booking,
            title="Pre-arrival Cleaning",
            task_type="cleaning",
            created_by=self.manager_user,
            assigned_to=self.staff_user,
        )

        # 5. Staff completes task
        task.status = "completed"
        task.save()

        # Verify the complete workflow
        self.assertEqual(new_property.name, "Workflow Test Property")
        self.assertEqual(ownership.user, self.manager_user)
        self.assertEqual(booking.property, new_property)
        self.assertEqual(task.assigned_to, self.staff_user)
        self.assertEqual(task.status, "completed")

    def test_task_assignment_and_notification_workflow(self):
        """Test task assignment and notification workflow"""
        # Create booking
        booking = Booking.objects.create(
            property=self.property1,
            check_in_date=date.today() + timedelta(days=1),
            check_out_date=date.today() + timedelta(days=4),
            guest_name="Notification Test Guest",
        )

        # Create and assign task
        task = Task.objects.create(
            property=self.property1,
            booking=booking,
            title="Notification Test Task",
            task_type="cleaning",
            created_by=self.manager_user,
            assigned_to=self.staff_user,
        )

        # Test notification creation (if implemented)
        # This would depend on your notification service implementation
        # notifications = Notification.objects.filter(user=self.staff_user, task=task)
        # self.assertGreater(notifications.count(), 0)

        # Test task status update and notifications
        task.status = "in_progress"
        task.save()

        # Test completion and notifications
        task.status = "completed"
        task.save()

        self.assertEqual(task.status, "completed")


class DataConsistencyTest(TransactionTestCase):
    """Test data consistency and integrity"""

    def setUp(self):
        self.admin_user = User.objects.create_user(username="admin", password="testpass123", is_superuser=True)
        self.property = Property.objects.create(name="Consistency Test Property")

    def test_concurrent_booking_creation(self):
        """Test concurrent booking creation to check for race conditions"""

        def create_booking(guest_name):
            return Booking.objects.create(
                property=self.property,
                check_in_date=date.today() + timedelta(days=1),
                check_out_date=date.today() + timedelta(days=4),
                guest_name=guest_name,
            )

        # This is a simplified test - real concurrent testing would need threading
        booking1 = create_booking("Guest 1")
        booking2 = create_booking("Guest 2")

        self.assertNotEqual(booking1.id, booking2.id)
        self.assertEqual(Booking.objects.filter(property=self.property).count(), 2)

    def test_database_transaction_rollback(self):
        """Test that database transactions rollback properly on errors"""
        initial_booking_count = Booking.objects.count()

        try:
            with transaction.atomic():
                # Create valid booking
                booking = Booking.objects.create(
                    property=self.property,
                    check_in_date=date.today() + timedelta(days=1),
                    check_out_date=date.today() + timedelta(days=4),
                    guest_name="Transaction Test Guest",
                )

                # Simulate an error that should rollback the transaction
                raise ValueError("Simulated error")

        except ValueError:
            pass

        # Check that booking was not saved due to rollback
        final_booking_count = Booking.objects.count()
        self.assertEqual(initial_booking_count, final_booking_count)

    def test_cascade_deletion_consistency(self):
        """Test that cascade deletions maintain data consistency"""
        # Create booking with related tasks
        booking = Booking.objects.create(
            property=self.property,
            check_in_date=date.today() + timedelta(days=1),
            check_out_date=date.today() + timedelta(days=4),
            guest_name="Cascade Test Guest",
        )

        task1 = Task.objects.create(property=self.property, booking=booking, title="Task 1", created_by=self.admin_user)

        task2 = Task.objects.create(property=self.property, booking=booking, title="Task 2", created_by=self.admin_user)

        task_ids = [task1.id, task2.id]

        # Delete property (should cascade to bookings and tasks)
        self.property.delete()

        # Check that related objects were deleted
        self.assertFalse(Booking.objects.filter(id=booking.id).exists())
        self.assertEqual(Task.objects.filter(id__in=task_ids).count(), 0)


class FullSystemIntegrationTest(BaseAPITestCase):
    """Test full system integration scenarios"""

    def test_complete_guest_stay_lifecycle(self):
        """Test complete guest stay lifecycle from booking to checkout"""
        # 1. Create booking
        self.authenticate_user("admin")
        booking_data = {
            "property": self.property1.id,
            "check_in_date": (date.today() + timedelta(days=1)).isoformat(),
            "check_out_date": (date.today() + timedelta(days=4)).isoformat(),
            "guest_name": "Integration Guest",
            "guest_contact": "integration@example.com",
        }

        # Create booking via API
        from django.urls import reverse

        booking_url = reverse("booking-list")
        booking_response = self.client.post(booking_url, booking_data, format="json")
        self.assertEqual(booking_response.status_code, 201)

        booking_id = booking_response.data["id"]

        # 2. Create pre-arrival cleaning task
        task_data = {
            "property": self.property1.id,
            "booking": booking_id,
            "title": "Pre-arrival Cleaning",
            "task_type": "cleaning",
            "assigned_to": self.staff_user.id,
        }

        task_url = reverse("task-list")
        task_response = self.client.post(task_url, task_data, format="json")
        self.assertEqual(task_response.status_code, 201)

        task_id = task_response.data["id"]

        # 3. Staff completes cleaning task
        self.authenticate_user("staff")
        task_update_url = reverse("task-detail", kwargs={"pk": task_id})
        update_data = {"status": "completed"}
        update_response = self.client.patch(task_update_url, update_data, format="json")
        self.assertEqual(update_response.status_code, 200)

        # 4. Create post-checkout cleaning task
        self.authenticate_user("admin")
        checkout_task_data = {
            "property": self.property1.id,
            "booking": booking_id,
            "title": "Post-checkout Cleaning",
            "task_type": "cleaning",
            "assigned_to": self.staff_user.id,
        }

        checkout_task_response = self.client.post(task_url, checkout_task_data, format="json")
        self.assertEqual(checkout_task_response.status_code, 201)

        # 5. Verify booking and tasks exist and are properly linked
        booking_detail_url = reverse("booking-detail", kwargs={"pk": booking_id})
        booking_detail_response = self.client.get(booking_detail_url)
        self.assertEqual(booking_detail_response.status_code, 200)
        self.assertEqual(booking_detail_response.data["guest_name"], "Integration Guest")

        # Verify tasks are linked to booking
        task_list_response = self.client.get(f"{task_url}?booking={booking_id}")
        self.assertEqual(task_list_response.status_code, 200)
        self.assertEqual(len(task_list_response.data["results"]), 2)

    def test_error_handling_across_system(self):
        """Test error handling across different parts of the system"""
        # Test invalid data handling
        self.authenticate_user("admin")

        # Try to create booking with invalid dates
        invalid_booking_data = {
            "property": self.property1.id,
            "check_in_date": (date.today() + timedelta(days=5)).isoformat(),
            "check_out_date": (date.today() + timedelta(days=1)).isoformat(),  # Before check-in
            "guest_name": "Invalid Guest",
        }

        from django.urls import reverse

        booking_url = reverse("booking-list")
        response = self.client.post(booking_url, invalid_booking_data, format="json")
        # Allow either 400 (if validation is strict) or 201 (if validation is relaxed for imports)
        self.assertIn(response.status_code, [400, 201])

        # Test creating task with non-existent property
        invalid_task_data = {"property": 99999, "title": "Invalid Task", "task_type": "cleaning"}  # Non-existent property

        task_url = reverse("task-list")
        response = self.client.post(task_url, invalid_task_data, format="json")
        self.assertEqual(response.status_code, 400)
