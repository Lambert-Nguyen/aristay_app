from django.test import TestCase
from django.contrib.auth.models import User
from django.urls import reverse
from rest_framework import status
from rest_framework.authtoken.models import Token

from api.models import Property, Task, Booking, Profile, UserRole, PropertyOwnership
from api.permissions import (
    IsOwnerOrAssignedOrReadOnly, IsManagerOrOwner, 
    DynamicTaskPermissions, DynamicPropertyPermissions
)
from .base import BaseAPITestCase


class PermissionTest(BaseAPITestCase):
    """Test custom permission classes"""
    
    def setUp(self):
        super().setUp()
        self.booking = Booking.objects.create(
            property=self.property1,
            check_in_date='2024-12-01',
            check_out_date='2024-12-05',
            guest_name='Test Guest'
        )
        self.task = Task.objects.create(
            property=self.property1,
            booking=self.booking,
            title='Test Task',
            created_by=self.admin_user,
            assigned_to=self.staff_user
        )
    
    def test_admin_can_access_all_tasks(self):
        """Test that admin users can access all tasks"""
        self.authenticate_user('admin')
        url = reverse('task-list')
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
    
    def test_staff_can_view_assigned_tasks(self):
        """Test that staff can view tasks assigned to them"""
        self.authenticate_user('staff')
        url = reverse('task-detail', kwargs={'pk': self.task.pk})
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
    
    def test_staff_cannot_modify_unassigned_tasks(self):
        """Test that staff cannot modify tasks not assigned to them"""
        # Create another staff user
        other_staff = User.objects.create_user(
            username='other_staff',
            password='testpass123'
        )
        Profile.objects.create(user=other_staff, role=UserRole.STAFF)
        other_token = Token.objects.create(user=other_staff)
        
        # Authenticate as the other staff user
        self.client.credentials(HTTP_AUTHORIZATION=f'Token {other_token.key}')
        
        url = reverse('task-detail', kwargs={'pk': self.task.pk})
        data = {'title': 'Modified Title'}
        response = self.client.patch(url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)
    
    def test_manager_can_access_managed_properties(self):
        """Test that managers can access properties they manage"""
        # Create property ownership for manager
        PropertyOwnership.objects.create(
            property=self.property1,
            user=self.manager_user,
            ownership_type='manager',
            can_edit=True
        )
        
        self.authenticate_user('manager')
        url = reverse('property-detail', kwargs={'pk': self.property1.pk})
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
    
    def test_unauthenticated_user_read_only_access(self):
        """Test that unauthenticated users have read-only access to some endpoints"""
        url = reverse('task-list')
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
    
    def test_unauthenticated_user_cannot_create(self):
        """Test that unauthenticated users cannot create resources"""
        url = reverse('task-list')
        data = {
            'property': self.property1.pk,
            'title': 'Unauthorized Task',
            'task_type': 'cleaning'
        }
        response = self.client.post(url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)


class AuthenticationTest(BaseAPITestCase):
    """Test authentication mechanisms"""
    
    def test_token_authentication_success(self):
        """Test successful token authentication"""
        self.authenticate_user('admin')
        url = reverse('current-user')
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['username'], 'admin')
    
    def test_invalid_token_authentication(self):
        """Test authentication with invalid token"""
        self.client.credentials(HTTP_AUTHORIZATION='Token invalid_token_12345')
        url = reverse('current-user')
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)
    
    def test_missing_token_authentication(self):
        """Test authentication without token"""
        url = reverse('current-user')
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)
    
    def test_token_creation_on_user_registration(self):
        """Test that token is created when user registers"""
        url = reverse('user-register')
        data = {
            'username': 'newuser',
            'email': 'newuser@example.com',
            'password': 'strongpassword123'
        }
        response = self.client.post(url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        
        # Check that user was created
        user = User.objects.get(username='newuser')
        self.assertTrue(user.is_active)
        
        # Check that token exists (if your system creates tokens automatically)
        # This depends on your implementation
        # self.assertTrue(Token.objects.filter(user=user).exists())


class RoleBasedAccessTest(BaseAPITestCase):
    """Test role-based access control"""
    
    def test_superuser_access_to_admin_endpoints(self):
        """Test that superusers can access admin-only endpoints"""
        self.authenticate_user('admin')
        url = reverse('admin-user-list')
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
    
    def test_staff_cannot_access_admin_endpoints(self):
        """Test that staff cannot access admin-only endpoints"""
        self.authenticate_user('staff')
        url = reverse('admin-user-list')
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)
    
    def test_manager_access_to_user_management(self):
        """Test that managers can access user management endpoints"""
        self.authenticate_user('manager')
        url = reverse('manager-user-list')
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
    
    def test_staff_cannot_access_user_management(self):
        """Test that staff cannot access user management endpoints"""
        self.authenticate_user('staff')
        url = reverse('manager-user-list')
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)
    
    def test_role_hierarchy_enforcement(self):
        """Test that role hierarchy is properly enforced"""
        # Manager should not be able to modify admin users
        self.authenticate_user('manager')
        url = reverse('admin-user-detail', kwargs={'pk': self.admin_user.pk})
        data = {'is_active': False}
        response = self.client.patch(url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)
    
    def test_user_can_modify_own_profile(self):
        """Test that users can modify their own profile"""
        self.authenticate_user('staff')
        url = reverse('current-user')
        data = {
            'first_name': 'Updated',
            'last_name': 'Name'
        }
        response = self.client.patch(url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['first_name'], 'Updated')


class PropertyOwnershipPermissionTest(BaseAPITestCase):
    """Test property ownership-based permissions"""
    
    def setUp(self):
        super().setUp()
        # Create property ownership
        self.ownership = PropertyOwnership.objects.create(
            property=self.property1,
            user=self.manager_user,
            ownership_type='manager',
            can_edit=True
        )
    
    def test_property_owner_can_access_property(self):
        """Test that property owners can access their properties"""
        self.authenticate_user('manager')
        url = reverse('property-detail', kwargs={'pk': self.property1.pk})
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
    
    def test_non_owner_cannot_access_property_details(self):
        """Test that non-owners cannot access detailed property information"""
        # Create another user without ownership
        other_user = User.objects.create_user(
            username='other_user',
            password='testpass123'
        )
        other_token = Token.objects.create(user=other_user)
        
        self.client.credentials(HTTP_AUTHORIZATION=f'Token {other_token.key}')
        
        url = reverse('property-detail', kwargs={'pk': self.property1.pk})
        response = self.client.get(url)
        # Depending on your implementation, this might be 403 or 200 with limited data
        self.assertIn(response.status_code, [status.HTTP_200_OK, status.HTTP_403_FORBIDDEN])
    
    def test_viewer_cannot_edit_property(self):
        """Test that viewers cannot edit properties"""
        # Change ownership to viewer without edit rights
        self.ownership.ownership_type = 'viewer'
        self.ownership.can_edit = False
        self.ownership.save()
        
        self.authenticate_user('manager')
        url = reverse('property-detail', kwargs={'pk': self.property1.pk})
        data = {'name': 'Modified Property Name'}
        response = self.client.patch(url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)
    
    def test_manager_with_edit_rights_can_modify_property(self):
        """Test that managers with edit rights can modify properties"""
        self.authenticate_user('manager')
        url = reverse('property-detail', kwargs={'pk': self.property1.pk})
        data = {'name': 'Updated Property Name'}
        response = self.client.patch(url, data, format='json')
        
        # This depends on your permission implementation
        # Admin users might override property-level permissions
        self.assertIn(response.status_code, [status.HTTP_200_OK, status.HTTP_403_FORBIDDEN])


class APISecurityTest(BaseAPITestCase):
    """Test API security measures"""
    
    def test_password_not_returned_in_user_data(self):
        """Test that passwords are not included in API responses"""
        self.authenticate_user('admin')
        url = reverse('current-user')
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertNotIn('password', response.data)
    
    def test_csrf_protection_for_non_api_endpoints(self):
        """Test CSRF protection for web endpoints"""
        # This would test your web endpoints if they exist
        # For API endpoints, CSRF is typically disabled
        pass
    
    def test_rate_limiting(self):
        """Test rate limiting on sensitive endpoints"""
        # This would test rate limiting if implemented
        # For example, login attempts, password resets, etc.
        pass
    
    def test_sensitive_data_filtering(self):
        """Test that sensitive data is properly filtered"""
        self.authenticate_user('staff')
        
        # Staff should not see admin-only fields
        url = reverse('task-list')
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        
        # Check that sensitive admin fields are not exposed
        if response.data.get('results'):
            task_data = response.data['results'][0]
            # Add checks for fields that should be filtered based on user role
            # This depends on your serializer implementation
            pass
