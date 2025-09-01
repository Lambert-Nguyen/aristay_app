import os

import django
from django.contrib.auth.models import User
from django.test import Client, TestCase
from django.urls import reverse

from rest_framework import status
from rest_framework.authtoken.models import Token
from rest_framework.test import APIClient, APITestCase

from api.models import Profile, Property, UserRole


class BaseTestCase(TestCase):
    """Base test case with common setup for all tests"""

    def setUp(self):
        """Set up test data for each test method"""
        # Create test users with unique usernames per test class
        test_id = self._testMethodName + str(id(self))

        self.admin_user = User.objects.create_user(
            username=f"admin_{test_id}",
            email=f"admin_{test_id}@aristay.com",
            password="testpass123",
            is_staff=True,
            is_superuser=True,
        )

        self.manager_user = User.objects.create_user(
            username=f"manager_{test_id}", email=f"manager_{test_id}@aristay.com", password="testpass123", is_staff=True
        )

        self.staff_user = User.objects.create_user(
            username=f"staff_{test_id}", email=f"staff_{test_id}@aristay.com", password="testpass123"
        )

        # Create profiles - use get_or_create to avoid duplicates
        Profile.objects.get_or_create(user=self.manager_user, defaults={"role": UserRole.MANAGER})
        Profile.objects.get_or_create(user=self.staff_user, defaults={"role": UserRole.STAFF})

        # Create test properties
        self.property1 = Property.objects.create(name=f"Test Property 1_{test_id}")
        self.property2 = Property.objects.create(name=f"Test Property 2_{test_id}")

        # Set up clients
        self.client = Client()
        self.api_client = APIClient()


class BaseAPITestCase(APITestCase):
    """Base API test case with authentication setup"""

    def setUp(self):
        """Set up test data for API tests"""
        # Create test users with unique usernames per test class
        test_id = self._testMethodName + str(id(self))

        self.admin_user = User.objects.create_user(
            username=f"admin_{test_id}",
            email=f"admin_{test_id}@aristay.com",
            password="testpass123",
            is_staff=True,
            is_superuser=True,
        )

        self.manager_user = User.objects.create_user(
            username=f"manager_{test_id}", email=f"manager_{test_id}@aristay.com", password="testpass123", is_staff=True
        )

        self.staff_user = User.objects.create_user(
            username=f"staff_{test_id}", email=f"staff_{test_id}@aristay.com", password="testpass123"
        )

        # Create profiles - use get_or_create to avoid duplicates
        Profile.objects.get_or_create(user=self.manager_user, defaults={"role": UserRole.MANAGER})
        Profile.objects.get_or_create(user=self.staff_user, defaults={"role": UserRole.STAFF})

        # Create tokens for API authentication
        self.admin_token = Token.objects.get_or_create(user=self.admin_user)[0]
        self.manager_token = Token.objects.get_or_create(user=self.manager_user)[0]
        self.staff_token = Token.objects.get_or_create(user=self.staff_user)[0]

        # Create test properties
        self.property1 = Property.objects.create(name=f"Test Property 1_{test_id}")
        self.property2 = Property.objects.create(name=f"Test Property 2_{test_id}")

    def authenticate_user(self, user_type="admin"):
        """Helper method to authenticate API client"""
        self.client = APIClient()  # Use APIClient for authentication
        if user_type == "admin":
            self.client.credentials(HTTP_AUTHORIZATION=f"Token {self.admin_token.key}")
        elif user_type == "manager":
            self.client.credentials(HTTP_AUTHORIZATION=f"Token {self.manager_token.key}")
        elif user_type == "staff":
            self.client.credentials(HTTP_AUTHORIZATION=f"Token {self.staff_token.key}")
