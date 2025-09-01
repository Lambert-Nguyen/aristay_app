import os
import django
from django.test import TestCase, Client
from django.contrib.auth.models import User
from django.urls import reverse
from rest_framework.test import APITestCase, APIClient
from rest_framework.authtoken.models import Token
from rest_framework import status
from api.models import Property, Profile, UserRole


class BaseTestCase(TestCase):
    """Base test case with common setup for all tests"""
    
    def setUp(self):
        """Set up test data for each test method"""
        # Create test users
        self.admin_user = User.objects.create_user(
            username='admin',
            email='admin@aristay.com',
            password='testpass123',
            is_staff=True,
            is_superuser=True
        )
        
        self.manager_user = User.objects.create_user(
            username='manager',
            email='manager@aristay.com',
            password='testpass123',
            is_staff=True
        )
        
        self.staff_user = User.objects.create_user(
            username='staff',
            email='staff@aristay.com',
            password='testpass123'
        )
        
        # Create profiles
        Profile.objects.create(user=self.manager_user, role=UserRole.MANAGER)
        Profile.objects.create(user=self.staff_user, role=UserRole.STAFF)
        
        # Create test properties
        self.property1 = Property.objects.create(name='Test Property 1')
        self.property2 = Property.objects.create(name='Test Property 2')
        
        # Set up clients
        self.client = Client()
        self.api_client = APIClient()


class BaseAPITestCase(APITestCase):
    """Base API test case with authentication setup"""
    
    def setUp(self):
        """Set up test data for API tests"""
        # Create test users
        self.admin_user = User.objects.create_user(
            username='admin',
            email='admin@aristay.com',
            password='testpass123',
            is_staff=True,
            is_superuser=True
        )
        
        self.manager_user = User.objects.create_user(
            username='manager',
            email='manager@aristay.com',
            password='testpass123',
            is_staff=True
        )
        
        self.staff_user = User.objects.create_user(
            username='staff',
            email='staff@aristay.com',
            password='testpass123'
        )
        
        # Create profiles
        Profile.objects.create(user=self.manager_user, role=UserRole.MANAGER)
        Profile.objects.create(user=self.staff_user, role=UserRole.STAFF)
        
        # Create tokens for API authentication
        self.admin_token = Token.objects.create(user=self.admin_user)
        self.manager_token = Token.objects.create(user=self.manager_user)
        self.staff_token = Token.objects.create(user=self.staff_user)
        
        # Create test properties
        self.property1 = Property.objects.create(name='Test Property 1')
        self.property2 = Property.objects.create(name='Test Property 2')
    
    def authenticate_user(self, user_type='admin'):
        """Helper method to authenticate API client"""
        self.client = APIClient()  # Use APIClient for authentication
        if user_type == 'admin':
            self.client.credentials(HTTP_AUTHORIZATION=f'Token {self.admin_token.key}')
        elif user_type == 'manager':
            self.client.credentials(HTTP_AUTHORIZATION=f'Token {self.manager_token.key}')
        elif user_type == 'staff':
            self.client.credentials(HTTP_AUTHORIZATION=f'Token {self.staff_token.key}')
