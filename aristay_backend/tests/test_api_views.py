import json
from datetime import datetime, timedelta

from django.contrib.auth.models import User
from django.urls import reverse
from django.utils import timezone

from rest_framework import status
from rest_framework.test import APITestCase

from api.models import Booking, Profile, Property, Task, UserRole

from .base import BaseAPITestCase


class UserRegistrationAPITest(BaseAPITestCase):
    """Test user registration API endpoint"""

    def test_user_registration_success(self):
        """Test successful user registration"""
        url = reverse("user-register")
        data = {"username": "newuser", "email": "newuser@example.com", "password": "strongpassword123"}
        response = self.client.post(url, data, format="json")
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertTrue(User.objects.filter(username="newuser").exists())

    def test_user_registration_duplicate_username(self):
        """Test registration with duplicate username"""
        url = reverse("user-register")
        data = {
            "username": self.admin_user.username,  # Use actual existing username
            "email": "newadmin@example.com",
            "password": "strongpassword123",
        }
        response = self.client.post(url, data, format="json")
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_user_registration_invalid_email(self):
        """Test registration with invalid email"""
        url = reverse("user-register")
        data = {"username": "newuser", "email": "invalid-email", "password": "strongpassword123"}
        response = self.client.post(url, data, format="json")
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)


class TaskAPITest(BaseAPITestCase):
    """Test Task API endpoints"""

    def setUp(self):
        super().setUp()
        self.booking = Booking.objects.create(
            property=self.property1,
            check_in_date=timezone.now().date(),
            check_out_date=timezone.now().date() + timedelta(days=3),
            guest_name="Test Guest",
            guest_contact="guest@example.com",
        )
        self.task = Task.objects.create(
            property=self.property1,
            booking=self.booking,
            title="Test Task",
            description="Test description",
            task_type="cleaning",
            created_by=self.admin_user,
            assigned_to=self.staff_user,
        )

    def test_task_list_authenticated(self):
        """Test task list endpoint with authentication"""
        self.authenticate_user("admin")
        url = reverse("task-list")
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertGreaterEqual(len(response.data["results"]), 1)

    def test_task_list_unauthenticated(self):
        """Test task list endpoint without authentication"""
        url = reverse("task-list")
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)  # Read-only access

    def test_task_create_authenticated(self):
        """Test creating a task with authentication"""
        self.authenticate_user("admin")
        url = reverse("task-list")
        data = {
            "property": self.property1.id,
            "booking": self.booking.id,
            "title": "New Test Task",
            "description": "New task description",
            "task_type": "maintenance",
            "assigned_to": self.staff_user.id,
        }
        response = self.client.post(url, data, format="json")
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(response.data["title"], "New Test Task")

    def test_task_create_unauthenticated(self):
        """Test creating a task without authentication"""
        url = reverse("task-list")
        data = {"property": self.property1.id, "title": "New Test Task", "task_type": "cleaning"}
        response = self.client.post(url, data, format="json")
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_task_detail_retrieve(self):
        """Test retrieving a specific task"""
        self.authenticate_user("admin")
        url = reverse("task-detail", kwargs={"pk": self.task.id})
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["title"], "Test Task")

    def test_task_update(self):
        """Test updating a task"""
        self.authenticate_user("admin")
        url = reverse("task-detail", kwargs={"pk": self.task.id})
        data = {"title": "Updated Task Title", "status": "in-progress"}  # Use the correct status value with hyphen
        response = self.client.patch(url, data, format="json")
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["title"], "Updated Task Title")

    def test_task_delete(self):
        """Test deleting a task"""
        self.authenticate_user("admin")
        url = reverse("task-detail", kwargs={"pk": self.task.id})
        response = self.client.delete(url)
        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)
        self.assertFalse(Task.objects.filter(id=self.task.id).exists())

    def test_task_filter_by_status(self):
        """Test filtering tasks by status"""
        self.authenticate_user("admin")
        # Create additional task with different status
        Task.objects.create(property=self.property1, title="Completed Task", status="completed", created_by=self.admin_user)

        url = reverse("task-list")
        response = self.client.get(f"{url}?status=completed")
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        # Should find the completed task
        completed_tasks = [task for task in response.data["results"] if task["status"] == "completed"]
        self.assertGreater(len(completed_tasks), 0)


class PropertyAPITest(BaseAPITestCase):
    """Test Property API endpoints"""

    def test_property_list(self):
        """Test property list endpoint"""
        self.authenticate_user("admin")
        url = reverse("property-list")
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertGreaterEqual(len(response.data), 2)  # We have 2 test properties

    def test_property_create_admin(self):
        """Test creating a property as admin"""
        self.authenticate_user("admin")
        url = reverse("property-list")
        data = {"name": "New Property"}
        response = self.client.post(url, data, format="json")
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(response.data["name"], "New Property")

    def test_property_create_non_admin(self):
        """Test creating a property as non-admin (should fail)"""
        self.authenticate_user("staff")
        url = reverse("property-list")
        data = {"name": "New Property"}
        response = self.client.post(url, data, format="json")
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_property_detail(self):
        """Test property detail endpoint"""
        self.authenticate_user("admin")
        url = reverse("property-detail", kwargs={"pk": self.property1.id})
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["name"], self.property1.name)

    def test_property_update_admin(self):
        """Test updating a property as admin"""
        self.authenticate_user("admin")
        url = reverse("property-detail", kwargs={"pk": self.property1.id})
        data = {"name": "Updated Property Name"}
        response = self.client.patch(url, data, format="json")
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["name"], "Updated Property Name")

    def test_property_update_non_admin(self):
        """Test updating a property as non-admin (should fail)"""
        self.authenticate_user("staff")
        url = reverse("property-detail", kwargs={"pk": self.property1.id})
        data = {"name": "Hacked Property Name"}
        response = self.client.patch(url, data, format="json")
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)


class BookingAPITest(BaseAPITestCase):
    """Test Booking API endpoints"""

    def setUp(self):
        super().setUp()
        self.booking = Booking.objects.create(
            property=self.property1,
            check_in_date=timezone.now().date(),
            check_out_date=timezone.now().date() + timedelta(days=3),
            guest_name="Test Guest",
            guest_contact="guest@example.com",
        )

    def test_booking_list(self):
        """Test booking list endpoint"""
        self.authenticate_user("admin")
        url = reverse("booking-list")
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertGreaterEqual(len(response.data["results"]), 1)

    def test_booking_create(self):
        """Test creating a booking"""
        self.authenticate_user("admin")
        url = reverse("booking-list")
        data = {
            "property": self.property2.id,
            "check_in_date": timezone.now().date() + timedelta(days=7),
            "check_out_date": timezone.now().date() + timedelta(days=10),
            "guest_name": "New Guest",
            "guest_contact": "newguest@example.com",
        }
        response = self.client.post(url, data, format="json")
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(response.data["guest_name"], "New Guest")

    def test_booking_detail(self):
        """Test booking detail endpoint"""
        self.authenticate_user("admin")
        url = reverse("booking-detail", kwargs={"pk": self.booking.id})
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["guest_name"], "Test Guest")

    def test_booking_update(self):
        """Test updating a booking"""
        self.authenticate_user("admin")
        url = reverse("booking-detail", kwargs={"pk": self.booking.id})
        data = {"guest_name": "Updated Guest Name"}
        response = self.client.patch(url, data, format="json")
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["guest_name"], "Updated Guest Name")


class AdminUserAPITest(BaseAPITestCase):
    """Test Admin User Management API endpoints"""

    def test_admin_user_list(self):
        """Test admin user list endpoint"""
        self.authenticate_user("admin")
        # Use the general user-list endpoint since admin-user-list doesn't exist
        url = reverse("user-list")
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertGreaterEqual(len(response.data["results"]), 3)  # We have 3 test users

    def test_admin_user_create(self):
        """Test admin user creation"""
        self.authenticate_user("admin")
        url = reverse("admin-create-user")  # Use the correct URL name
        data = {"username": "newstaffuser", "email": "newstaff@example.com", "password": "strongpassword123", "is_staff": True}
        response = self.client.post(url, data, format="json")
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertTrue(User.objects.filter(username="newstaffuser").exists())

    def test_admin_user_create_non_admin(self):
        """Test admin user creation by non-admin (should fail)"""
        self.authenticate_user("staff")
        url = reverse("admin-create-user")  # Use the correct URL name
        data = {"username": "hackuser", "email": "hack@example.com", "password": "password123"}
        response = self.client.post(url, data, format="json")
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_current_user_info(self):
        """Test getting current user information"""
        self.authenticate_user("admin")
        url = reverse("current-user")
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["username"], self.admin_user.username)
        self.assertTrue(response.data["is_superuser"])


class NotificationAPITest(BaseAPITestCase):
    """Test Notification API endpoints"""

    def test_notification_list(self):
        """Test notification list endpoint"""
        self.authenticate_user("staff")
        url = reverse("notification-list")
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)

    def test_device_registration(self):
        """Test device registration for push notifications"""
        self.authenticate_user("staff")
        url = reverse("device-register")
        data = {"token": "test_fcm_token_12345"}
        response = self.client.post(url, data, format="json")
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["status"], "registered")
