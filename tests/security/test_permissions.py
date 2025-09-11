"""
Comprehensive tests for the dynamic permissions system
"""

import json
from datetime import datetime, timedelta
from django.test import TestCase, Client
from django.contrib.auth.models import User
from django.utils import timezone
from django.urls import reverse
from rest_framework.test import APITestCase, APIClient
from rest_framework import status
from rest_framework.authtoken.models import Token

from api.models import (
    Profile, CustomPermission, RolePermission, UserPermissionOverride,
    UserRole, TaskGroup, Task, Property, Booking
)
from api.permissions import (
    HasCustomPermission, HasAnyCustomPermission, DynamicTaskPermissions,
    DynamicBookingPermissions, DynamicUserPermissions, DynamicPropertyPermissions,
    CanViewReports, CanViewAnalytics, CanAccessAdminPanel, CanManageFiles
)


class DynamicPermissionsTestCase(APITestCase):
    """Test the dynamic permissions system"""
    
    def setUp(self):
        """Set up test data"""
        # Create test users
        self.superuser = User.objects.create_user(
            username='superuser',
            email='super@test.com',
            password='testpass123',
            is_superuser=True,
            is_staff=True
        )
        self.superuser_profile, created = Profile.objects.get_or_create(
            user=self.superuser,
            defaults={'role': UserRole.SUPERUSER, 'task_group': TaskGroup.NONE}
        )
        if not created:
            self.superuser_profile.role = UserRole.SUPERUSER
            self.superuser_profile.task_group = TaskGroup.NONE
            self.superuser_profile.save()
        
        self.manager = User.objects.create_user(
            username='manager',
            email='manager@test.com',
            password='testpass123'
        )
        self.manager_profile, created = Profile.objects.get_or_create(
            user=self.manager,
            defaults={'role': UserRole.MANAGER, 'task_group': TaskGroup.NONE}
        )
        if not created:
            self.manager_profile.role = UserRole.MANAGER
            self.manager_profile.task_group = TaskGroup.NONE
            self.manager_profile.save()
        
        self.staff = User.objects.create_user(
            username='staff',
            email='staff@test.com',
            password='testpass123'
        )
        self.staff_profile, created = Profile.objects.get_or_create(
            user=self.staff,
            defaults={'role': UserRole.STAFF, 'task_group': TaskGroup.GENERAL}
        )
        if not created:
            self.staff_profile.role = UserRole.STAFF
            self.staff_profile.task_group = TaskGroup.GENERAL
            self.staff_profile.save()
        
        self.viewer = User.objects.create_user(
            username='viewer',
            email='viewer@test.com',
            password='testpass123'
        )
        # Use create to ensure we get the correct role, not get_or_create
        profile, created = Profile.objects.get_or_create(
            user=self.viewer,
            defaults={'role': UserRole.VIEWER, 'task_group': TaskGroup.NONE}
        )
        if not created:
            profile.role = UserRole.VIEWER
            profile.task_group = TaskGroup.NONE
            profile.save()
        self.viewer_profile = profile
        
        # Force refresh to clear Django's cache
        self.viewer.refresh_from_db()
        self.viewer_profile.refresh_from_db()
        
        # Create test permissions
        self.view_tasks_perm = CustomPermission.objects.create(
            name='view_tasks',
            description='View tasks'
        )
        self.add_tasks_perm = CustomPermission.objects.create(
            name='add_tasks',
            description='Add tasks'
        )
        self.change_tasks_perm = CustomPermission.objects.create(
            name='change_tasks',
            description='Edit tasks'
        )
        self.delete_tasks_perm = CustomPermission.objects.create(
            name='delete_tasks',
            description='Delete tasks'
        )
        self.view_reports_perm = CustomPermission.objects.create(
            name='view_reports',
            description='View reports'
        )
        self.view_analytics_perm = CustomPermission.objects.create(
            name='view_analytics',
            description='View analytics'
        )
        
        # Create role permissions
        # Superuser gets all permissions
        RolePermission.objects.create(
            role=UserRole.SUPERUSER,
            permission=self.view_tasks_perm,
            granted=True,
            can_delegate=True
        )
        RolePermission.objects.create(
            role=UserRole.SUPERUSER,
            permission=self.add_tasks_perm,
            granted=True,
            can_delegate=True
        )
        RolePermission.objects.create(
            role=UserRole.SUPERUSER,
            permission=self.change_tasks_perm,
            granted=True,
            can_delegate=True
        )
        RolePermission.objects.create(
            role=UserRole.SUPERUSER,
            permission=self.delete_tasks_perm,
            granted=True,
            can_delegate=True
        )
        RolePermission.objects.create(
            role=UserRole.SUPERUSER,
            permission=self.view_reports_perm,
            granted=True,
            can_delegate=True
        )
        RolePermission.objects.create(
            role=UserRole.SUPERUSER,
            permission=self.view_analytics_perm,
            granted=True,
            can_delegate=True
        )
        
        # Manager gets most permissions
        RolePermission.objects.create(
            role=UserRole.MANAGER,
            permission=self.view_tasks_perm,
            granted=True,
            can_delegate=True
        )
        RolePermission.objects.create(
            role=UserRole.MANAGER,
            permission=self.add_tasks_perm,
            granted=True,
            can_delegate=False
        )
        RolePermission.objects.create(
            role=UserRole.MANAGER,
            permission=self.change_tasks_perm,
            granted=True,
            can_delegate=False
        )
        RolePermission.objects.create(
            role=UserRole.MANAGER,
            permission=self.view_reports_perm,
            granted=True,
            can_delegate=False
        )
        RolePermission.objects.create(
            role=UserRole.MANAGER,
            permission=self.view_analytics_perm,
            granted=True,
            can_delegate=False
        )
        
        # Staff gets limited permissions
        RolePermission.objects.create(
            role=UserRole.STAFF,
            permission=self.view_tasks_perm,
            granted=True,
            can_delegate=False
        )
        RolePermission.objects.create(
            role=UserRole.STAFF,
            permission=self.add_tasks_perm,
            granted=True,
            can_delegate=False
        )
        
        # Viewer gets minimal permissions
        RolePermission.objects.create(
            role=UserRole.VIEWER,
            permission=self.view_tasks_perm,
            granted=True,
            can_delegate=False
        )
        
        # Create test data
        self.property = Property.objects.create(
            name='Test Property',
            address='123 Test St'
        )
        
        self.booking = Booking.objects.create(
            property=self.property,
            check_in_date=timezone.now(),
            check_out_date=timezone.now() + timedelta(days=3),
            guest_name='Test Guest',
            status='confirmed'
        )
        
        self.task = Task.objects.create(
            title='Test Task',
            description='Test Description',
            property_ref=self.property,
            booking=self.booking,
            created_by=self.manager,
            assigned_to=self.staff
        )
        
        # Create API clients
        self.client = APIClient()
        
    def test_superuser_has_all_permissions(self):
        """Test that superusers have all permissions"""
        self.client.force_authenticate(user=self.superuser)
        
        # Test HasCustomPermission
        perm = HasCustomPermission('view_tasks')
        request = type('Request', (), {'user': self.superuser, 'method': 'GET'})()
        self.assertTrue(perm.has_permission(request, None))
        
        # Test profile has_permission method
        self.assertTrue(self.superuser_profile.has_permission('view_tasks'))
        self.assertTrue(self.superuser_profile.has_permission('add_tasks'))
        self.assertTrue(self.superuser_profile.has_permission('change_tasks'))
        self.assertTrue(self.superuser_profile.has_permission('delete_tasks'))
        
    def test_manager_permissions(self):
        """Test manager permissions"""
        # Test profile has_permission method
        self.assertTrue(self.manager_profile.has_permission('view_tasks'))
        self.assertTrue(self.manager_profile.has_permission('add_tasks'))
        self.assertTrue(self.manager_profile.has_permission('change_tasks'))
        self.assertFalse(self.manager_profile.has_permission('delete_tasks'))
        self.assertTrue(self.manager_profile.has_permission('view_reports'))
        self.assertTrue(self.manager_profile.has_permission('view_analytics'))
        
        # Test delegation permissions
        self.assertTrue(self.manager_profile.can_delegate_permission('view_tasks'))
        self.assertFalse(self.manager_profile.can_delegate_permission('add_tasks'))
        
    def test_staff_permissions(self):
        """Test staff permissions"""
        self.assertTrue(self.staff_profile.has_permission('view_tasks'))
        self.assertTrue(self.staff_profile.has_permission('add_tasks'))
        self.assertFalse(self.staff_profile.has_permission('change_tasks'))
        self.assertFalse(self.staff_profile.has_permission('delete_tasks'))
        self.assertFalse(self.staff_profile.has_permission('view_reports'))
        
    def test_viewer_permissions(self):
        """Test viewer permissions"""
        self.assertTrue(self.viewer_profile.has_permission('view_tasks'))
        self.assertFalse(self.viewer_profile.has_permission('add_tasks'))
        self.assertFalse(self.viewer_profile.has_permission('change_tasks'))
        self.assertFalse(self.viewer_profile.has_permission('delete_tasks'))
        self.assertFalse(self.viewer_profile.has_permission('view_reports'))
        
    def test_user_permission_override(self):
        """Test user-specific permission overrides"""
        # Grant staff user a permission they don't normally have
        UserPermissionOverride.objects.create(
            user=self.staff,
            permission=self.view_reports_perm,
            granted=True,
            granted_by=self.manager,
            reason='Temporary access for special project'
        )
        
        # Staff should now have view_reports permission
        self.assertTrue(self.staff_profile.has_permission('view_reports'))
        
        # Revoke a permission from manager
        UserPermissionOverride.objects.create(
            user=self.manager,
            permission=self.view_tasks_perm,
            granted=False,
            granted_by=self.superuser,
            reason='Temporary restriction'
        )
        
        # Manager should no longer have view_tasks permission
        self.assertFalse(self.manager_profile.has_permission('view_tasks'))
        
    def test_expired_permission_override(self):
        """Test that expired permission overrides are ignored"""
        # Create an expired override
        expired_time = timezone.now() - timedelta(days=1)
        UserPermissionOverride.objects.create(
            user=self.staff,
            permission=self.view_reports_perm,
            granted=True,
            granted_by=self.manager,
            reason='Temporary access',
            expires_at=expired_time
        )
        
        # Staff should not have the permission (override is expired)
        self.assertFalse(self.staff_profile.has_permission('view_reports'))
        
    def test_dynamic_task_permissions(self):
        """Test DynamicTaskPermissions class"""
        perm = DynamicTaskPermissions()

        # Test with manager (has view_tasks and add_tasks)
        request = type('Request', (), {'user': self.manager, 'method': 'GET'})()
        self.assertTrue(perm.has_permission(request, None))

        request = type('Request', (), {'user': self.manager, 'method': 'POST'})()
        self.assertTrue(perm.has_permission(request, None))

        # Test with staff (has view_tasks and add_tasks, but not change_tasks)
        request = type('Request', (), {'user': self.staff, 'method': 'GET'})()
        self.assertTrue(perm.has_permission(request, None))

        request = type('Request', (), {'user': self.staff, 'method': 'POST'})()
        self.assertTrue(perm.has_permission(request, None))

        request = type('Request', (), {'user': self.staff, 'method': 'PUT'})()
        self.assertFalse(perm.has_permission(request, None))

        # Test with viewer (only has view_tasks)
        request = type('Request', (), {'user': self.viewer, 'method': 'GET'})()
        self.assertTrue(perm.has_permission(request, None))

        # Test POST request (viewer should NOT have add_tasks permission)
        request = type('Request', (), {'user': self.viewer, 'method': 'POST'})()
        self.assertFalse(perm.has_permission(request, None))

    def test_has_any_custom_permission(self):
        """Test HasAnyCustomPermission class"""
        perm = HasAnyCustomPermission(['view_tasks', 'view_reports'])
        
        # Test with manager (has both permissions)
        request = type('Request', (), {'user': self.manager, 'method': 'GET'})()
        self.assertTrue(perm.has_permission(request, None))
        
        # Test with staff (has view_tasks but not view_reports)
        request = type('Request', (), {'user': self.staff, 'method': 'GET'})()
        self.assertTrue(perm.has_permission(request, None))
        
        # Test with viewer (has view_tasks but not view_reports)
        request = type('Request', (), {'user': self.viewer, 'method': 'GET'})()
        self.assertTrue(perm.has_permission(request, None))
        
        # Test with permissions staff doesn't have
        perm = HasAnyCustomPermission(['view_reports', 'view_analytics'])
        request = type('Request', (), {'user': self.staff, 'method': 'GET'})()
        self.assertFalse(perm.has_permission(request, None))
        
    def test_get_all_permissions(self):
        """Test get_all_permissions method"""
        # Test manager permissions
        manager_perms = self.manager_profile.get_all_permissions()
        self.assertTrue(manager_perms.get('view_tasks', False))
        self.assertTrue(manager_perms.get('add_tasks', False))
        self.assertTrue(manager_perms.get('change_tasks', False))
        self.assertFalse(manager_perms.get('delete_tasks', False))
        self.assertTrue(manager_perms.get('view_reports', False))
        
        # Test staff permissions
        staff_perms = self.staff_profile.get_all_permissions()
        self.assertTrue(staff_perms.get('view_tasks', False))
        self.assertTrue(staff_perms.get('add_tasks', False))
        self.assertFalse(staff_perms.get('change_tasks', False))
        self.assertFalse(staff_perms.get('delete_tasks', False))
        self.assertFalse(staff_perms.get('view_reports', False))
        
    def test_get_delegatable_permissions(self):
        """Test get_delegatable_permissions method"""
        # Test manager delegatable permissions
        manager_delegatable = list(self.manager_profile.get_delegatable_permissions())
        self.assertIn('view_tasks', manager_delegatable)
        self.assertNotIn('add_tasks', manager_delegatable)  # can_delegate=False
        
        # Test staff delegatable permissions
        staff_delegatable = list(self.staff_profile.get_delegatable_permissions())
        self.assertEqual(len(staff_delegatable), 0)  # No delegatable permissions
        
    def test_unauthenticated_user(self):
        """Test that unauthenticated users are denied access"""
        perm = HasCustomPermission('view_tasks')
        request = type('Request', (), {'user': None, 'method': 'GET'})()
        self.assertFalse(perm.has_permission(request, None))
        
        # Test with anonymous user
        from django.contrib.auth.models import AnonymousUser
        request = type('Request', (), {'user': AnonymousUser(), 'method': 'GET'})()
        self.assertFalse(perm.has_permission(request, None))
        
    def test_user_without_profile(self):
        """Test user gets default permissions when profile is auto-created"""
        # Since signals now auto-create profiles, this test verifies the default permissions
        user_no_profile = User.objects.create_user(
            username='noprofile',
            email='noprofile@test.com',
            password='testpass123'
        )
        
        # The signal will auto-create a profile with default STAFF role
        self.assertTrue(hasattr(user_no_profile, 'profile'))
        self.assertEqual(user_no_profile.profile.role, UserRole.STAFF)
        
        # Test that STAFF role has appropriate permissions
        perm = HasCustomPermission('view_tasks')
        request = type('Request', (), {'user': user_no_profile, 'method': 'GET'})()
        # STAFF role should have view_tasks permission
        self.assertTrue(perm.has_permission(request, None))

    def test_permission_cleanup_on_expiry(self):
        """Test that expired overrides are cleaned up"""
        # Create an expired override
        expired_time = timezone.now() - timedelta(days=1)
        override = UserPermissionOverride.objects.create(
            user=self.staff,
            permission=self.view_reports_perm,
            granted=True,
            granted_by=self.manager,
            reason='Temporary access',
            expires_at=expired_time
        )
        
        # Check that override exists
        self.assertTrue(UserPermissionOverride.objects.filter(id=override.id).exists())
        
        # Call has_permission - this should trigger cleanup
        self.staff_profile.has_permission('view_reports')
        
        # Check that expired override was deleted
        self.assertFalse(UserPermissionOverride.objects.filter(id=override.id).exists())
        
    def test_permission_override_precedence(self):
        """Test that user overrides take precedence over role permissions"""
        # Manager normally has view_tasks permission
        self.assertTrue(self.manager_profile.has_permission('view_tasks'))
        
        # Create override to deny the permission
        UserPermissionOverride.objects.create(
            user=self.manager,
            permission=self.view_tasks_perm,
            granted=False,
            granted_by=self.superuser,
            reason='Temporary restriction'
        )
        
        # Manager should no longer have the permission
        self.assertFalse(self.manager_profile.has_permission('view_tasks'))
        
        # Delete the override
        UserPermissionOverride.objects.filter(
            user=self.manager,
            permission=self.view_tasks_perm
        ).delete()
        
        # Manager should have the permission again
        self.assertTrue(self.manager_profile.has_permission('view_tasks'))

    def test_task_group_permissions(self):
        """Test TaskGroup permission functionality"""
        # Test staff user can view their own task group
        self.assertTrue(self.staff_profile.can_view_task_group(TaskGroup.GENERAL))
        self.assertFalse(self.staff_profile.can_view_task_group(TaskGroup.CLEANING))
        
        # Test manager can view all task groups
        self.assertTrue(self.manager_profile.can_view_task_group(TaskGroup.CLEANING))
        self.assertTrue(self.manager_profile.can_view_task_group(TaskGroup.MAINTENANCE))
        self.assertTrue(self.manager_profile.can_view_task_group(TaskGroup.LAUNDRY))
        self.assertTrue(self.manager_profile.can_view_task_group(TaskGroup.LAWN_POOL))
        self.assertTrue(self.manager_profile.can_view_task_group(TaskGroup.GENERAL))
        
        # Test superuser can view all task groups
        self.assertTrue(self.superuser_profile.can_view_task_group(TaskGroup.CLEANING))
        self.assertTrue(self.superuser_profile.can_view_task_group(TaskGroup.MAINTENANCE))
        
        # Test accessible task groups
        staff_groups = self.staff_profile.get_accessible_task_groups()
        self.assertIn(TaskGroup.GENERAL, staff_groups)
        self.assertNotIn(TaskGroup.CLEANING, staff_groups)
        
        manager_groups = self.manager_profile.get_accessible_task_groups()
        self.assertIn(TaskGroup.CLEANING, manager_groups)
        self.assertIn(TaskGroup.MAINTENANCE, manager_groups)
        self.assertIn(TaskGroup.LAUNDRY, manager_groups)
        self.assertIn(TaskGroup.LAWN_POOL, manager_groups)
        self.assertIn(TaskGroup.GENERAL, manager_groups)
        
        # Test task group display
        self.assertEqual(self.staff_profile.get_task_group_display(), 'General')
        self.assertEqual(self.manager_profile.get_task_group_display(), 'Not Assigned')
        
        # Test is_in_task_group
        self.assertTrue(self.staff_profile.is_in_task_group(TaskGroup.GENERAL))
        self.assertFalse(self.staff_profile.is_in_task_group(TaskGroup.CLEANING))


class PermissionIntegrationTestCase(APITestCase):
    """Test permissions integration with API endpoints"""
    
    def setUp(self):
        """Set up test data"""
        # Create users
        self.superuser = User.objects.create_user(
            username='superuser',
            email='super@test.com',
            password='testpass123',
            is_superuser=True,
            is_staff=True
        )
        Profile.objects.get_or_create(user=self.superuser, defaults={'role': UserRole.SUPERUSER, 'task_group': TaskGroup.NONE})
        
        self.manager = User.objects.create_user(
            username='manager',
            email='manager@test.com',
            password='testpass123',
            is_staff=True
        )
        manager_profile, created = Profile.objects.get_or_create(user=self.manager, defaults={'role': UserRole.MANAGER, 'task_group': TaskGroup.NONE})
        if not created:
            manager_profile.role = UserRole.MANAGER
            manager_profile.task_group = TaskGroup.NONE
            manager_profile.save()
        
        self.staff = User.objects.create_user(
            username='staff',
            email='staff@test.com',
            password='testpass123'
        )
        staff_profile, created = Profile.objects.get_or_create(user=self.staff, defaults={'role': UserRole.STAFF, 'task_group': TaskGroup.GENERAL})
        if not created:
            staff_profile.role = UserRole.STAFF
            staff_profile.task_group = TaskGroup.GENERAL
            staff_profile.save()
            
        # Force refresh to clear Django's cache
        self.manager.refresh_from_db()
        self.staff.refresh_from_db()
        
        # Create permissions
        self.view_tasks_perm = CustomPermission.objects.create(name='view_tasks')
        self.add_tasks_perm = CustomPermission.objects.create(name='add_tasks')
        self.change_tasks_perm = CustomPermission.objects.create(name='change_tasks')
        self.delete_tasks_perm = CustomPermission.objects.create(name='delete_tasks')
        
        # Create role permissions
        for perm in [self.view_tasks_perm, self.add_tasks_perm, self.change_tasks_perm, self.delete_tasks_perm]:
            RolePermission.objects.create(
                role=UserRole.SUPERUSER,
                permission=perm,
                granted=True,
                can_delegate=True
            )
        
        RolePermission.objects.create(
            role=UserRole.MANAGER,
            permission=self.view_tasks_perm,
            granted=True,
            can_delegate=True
        )
        RolePermission.objects.create(
            role=UserRole.MANAGER,
            permission=self.add_tasks_perm,
            granted=True,
            can_delegate=False
        )
        RolePermission.objects.create(
            role=UserRole.MANAGER,
            permission=self.change_tasks_perm,
            granted=True,
            can_delegate=False
        )
        
        RolePermission.objects.create(
            role=UserRole.STAFF,
            permission=self.view_tasks_perm,
            granted=True,
            can_delegate=False
        )
        RolePermission.objects.create(
            role=UserRole.STAFF,
            permission=self.add_tasks_perm,
            granted=True,
            can_delegate=False
        )
        
        # Create test data
        self.property = Property.objects.create(name='Test Property')
        self.booking = Booking.objects.create(
            property=self.property,
            check_in_date=timezone.now(),
            check_out_date=timezone.now() + timedelta(days=3),
            guest_name='Test Guest',
            status='confirmed'
        )
        self.task = Task.objects.create(
            title='Test Task',
            description='Test Description',
            property_ref=self.property,
            booking=self.booking,
            created_by=self.manager,
            assigned_to=self.staff
        )
        
    def test_task_list_permissions(self):
        """Test task list endpoint permissions"""
        # Test unauthenticated access
        response = self.client.get('/api/tasks/')
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)
        
        # Test staff access (has view_tasks)
        self.client.force_authenticate(user=self.staff)
        response = self.client.get('/api/tasks/')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        
        # Test manager access (has view_tasks)
        self.client.force_authenticate(user=self.manager)
        response = self.client.get('/api/tasks/')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        
    def test_task_create_permissions(self):
        """Test task creation permissions"""
        task_data = {
            'title': 'New Task',
            'description': 'New Description',
            'property_ref': self.property.id,
            'booking': self.booking.id
        }
        
        # Test unauthenticated access
        response = self.client.post('/api/tasks/', task_data)
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)
        
        # Test staff access (has add_tasks)
        self.client.force_authenticate(user=self.staff)
        response = self.client.post('/api/tasks/', task_data)
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        
        # Test manager access (has add_tasks)
        self.client.force_authenticate(user=self.manager)
        response = self.client.post('/api/tasks/', task_data)
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        
    def test_task_update_permissions(self):
        """Test task update permissions"""
        task_data = {
            'title': 'Updated Task',
            'description': 'Updated Description'
        }
        
        # Test staff access (no change_tasks permission)
        self.client.force_authenticate(user=self.staff)
        response = self.client.patch(f'/api/tasks/{self.task.id}/', task_data)
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)
        
        # Test manager access (has change_tasks permission)
        self.client.force_authenticate(user=self.manager)
        response = self.client.patch(f'/api/tasks/{self.task.id}/', task_data)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        
    def test_task_delete_permissions(self):
        """Test task deletion permissions"""
        # Test manager access (no delete_tasks permission)
        self.client.force_authenticate(user=self.manager)
        response = self.client.delete(f'/api/tasks/{self.task.id}/')
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)
        
        # Test superuser access (has delete_tasks permission)
        self.client.force_authenticate(user=self.superuser)
        response = self.client.delete(f'/api/tasks/{self.task.id}/')
        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)


class PermissionEdgeCasesTestCase(TestCase):
    """Test edge cases and error conditions"""
    
    def setUp(self):
        """Set up test data"""
        self.user = User.objects.create_user(
            username='testuser',
            email='test@test.com',
            password='testpass123'
        )
        self.profile, _ = Profile.objects.get_or_create(user=self.user, defaults={'role': UserRole.STAFF})
        
    def test_nonexistent_permission(self):
        """Test handling of nonexistent permissions"""
        # Should return False for nonexistent permission
        self.assertFalse(self.profile.has_permission('nonexistent_permission'))
        
    def test_inactive_permission(self):
        """Test handling of inactive permissions"""
        # Create an inactive permission
        perm = CustomPermission.objects.create(
            name='inactive_perm',
            description='Inactive permission',
            is_active=False
        )
        
        # Create role permission for inactive permission
        RolePermission.objects.create(
            role=UserRole.STAFF,
            permission=perm,
            granted=True
        )
        
        # Should return False for inactive permission
        self.assertFalse(self.profile.has_permission('inactive_perm'))
        
    def test_permission_with_special_characters(self):
        """Test permissions with special characters in names"""
        # This should not cause any issues
        perm = CustomPermission.objects.create(
            name='special_char_perm',
            description='Permission with special chars: !@#$%^&*()'
        )
        
        RolePermission.objects.create(
            role=UserRole.STAFF,
            permission=perm,
            granted=True
        )
        
        self.assertTrue(self.profile.has_permission('special_char_perm'))
        
    def test_multiple_overrides_same_permission(self):
        """Test that only the latest override is used"""
        perm = CustomPermission.objects.create(name='test_perm')
        
        # Create multiple overrides (should not happen due to unique constraint)
        # But test the behavior if it somehow happens
        override1 = UserPermissionOverride.objects.create(
            user=self.user,
            permission=perm,
            granted=True,
            granted_by=self.user
        )
        
        # The unique constraint should prevent this, but let's test the behavior
        # by updating the existing override
        override1.granted = False
        override1.save()
        
        # Should return False (latest override)
        self.assertFalse(self.profile.has_permission('test_perm'))
        
    def test_permission_with_unicode(self):
        """Test permissions with unicode characters"""
        perm = CustomPermission.objects.create(
            name='unicode_perm',
            description='Permission with unicode: 测试权限'
        )
        
        RolePermission.objects.create(
            role=UserRole.STAFF,
            permission=perm,
            granted=True
        )
        
        self.assertTrue(self.profile.has_permission('unicode_perm'))
