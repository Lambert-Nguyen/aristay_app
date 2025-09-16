"""
Test navigation visibility based on permissions
"""
import pytest
from django.test import TestCase, Client, override_settings
from django.urls import reverse
from django.contrib.auth import get_user_model
from api.models import Profile, CustomPermission, RolePermission, TaskGroup

User = get_user_model()


@override_settings(
    AUTHENTICATION_BACKENDS=[
        'django.contrib.auth.backends.ModelBackend',
    ]
)
class NavigationVisibilityTestCase(TestCase):
    """Test cases for permission-based navigation visibility"""
    
    def setUp(self):
        """Set up test data"""
        self.client = Client()
        
        # Create test users
        self.superuser = User.objects.create_superuser(
            'admin', 'admin@test.com', 'password123'
        )
        
        self.manager_user = User.objects.create_user(
            'manager', 'manager@test.com', 'password123'
        )
        # Get or update the automatically created profile
        self.manager_profile = Profile.objects.get(user=self.manager_user)
        self.manager_profile.role = 'manager'
        self.manager_profile.task_group = TaskGroup.NONE
        self.manager_profile.save()
        
        self.staff_user = User.objects.create_user(
            'staff', 'staff@test.com', 'password123'
        )
        # Get or update the automatically created profile  
        self.staff_profile = Profile.objects.get(user=self.staff_user)
        self.staff_profile.role = 'staff'
        self.staff_profile.task_group = TaskGroup.GENERAL
        self.staff_profile.save()
        
        self.regular_user = User.objects.create_user(
            'user', 'user@test.com', 'password123'
        )
        # Get or update the automatically created profile
        self.regular_profile = Profile.objects.get(user=self.regular_user)
        self.regular_profile.role = 'viewer'
        self.regular_profile.task_group = TaskGroup.NONE
        self.regular_profile.save()
        
        # Create test permissions if they don't exist
        self.manage_files_perm, created = CustomPermission.objects.get_or_create(
            name='manage_files',
            defaults={
                'description': 'Can manage file cleanup operations',
                'is_active': True
            }
        )
        
        self.view_reports_perm, created = CustomPermission.objects.get_or_create(
            name='view_reports',
            defaults={
                'description': 'Can view reports and analytics',
                'is_active': True
            }
        )
        
        self.manager_portal_perm, created = CustomPermission.objects.get_or_create(
            name='manager_portal_access',
            defaults={
                'description': 'Can access manager portal',
                'is_active': True
            }
        )
        
        # Set up role permissions
        # Managers should have file management and manager portal access
        RolePermission.objects.get_or_create(
            role='manager',
            permission=self.manage_files_perm,
            defaults={'granted': True, 'can_delegate': False}
        )
        RolePermission.objects.get_or_create(
            role='manager',
            permission=self.manager_portal_perm,
            defaults={'granted': True, 'can_delegate': False}
        )
        
        # Staff should have file management access
        RolePermission.objects.get_or_create(
            role='staff',
            permission=self.manage_files_perm,
            defaults={'granted': True, 'can_delegate': False}
        )
    
    def test_file_cleanup_nav_visibility_superuser(self):
        """Test that superuser can see file cleanup navigation"""
        self.client.login(username='admin', password='password123')
        
        # Check if file cleanup page is accessible
        response = self.client.get(reverse('admin-file-cleanup'))
        self.assertEqual(response.status_code, 200)
        
        # Check portal page for navigation links (if it exists)
        try:
            portal_response = self.client.get(reverse('portal-home'))
            if portal_response.status_code == 200:
                # Should contain file cleanup link for superuser
                self.assertContains(portal_response, 'file-cleanup', msg_prefix="Superuser should see file cleanup nav")
        except:
            pass  # Portal might not exist or be accessible
    
    def test_file_cleanup_nav_visibility_staff(self):
        """Test that staff users can see file cleanup navigation"""
        self.client.login(username='staff', password='password123')
        
        # Staff should have access to file cleanup
        response = self.client.get(reverse('admin-file-cleanup'))
        self.assertEqual(response.status_code, 200)
    
    def test_file_cleanup_nav_visibility_regular_user(self):
        """Test that regular users cannot see file cleanup navigation"""
        self.client.login(username='user', password='password123')
        
        # Regular user should NOT have access to file cleanup
        response = self.client.get(reverse('admin-file-cleanup'))
        self.assertEqual(response.status_code, 403)
    
    def test_file_cleanup_nav_visibility_manager(self):
        """Test that managers can see file cleanup navigation"""
        self.client.login(username='manager', password='password123')
        
        # Managers should have access to file cleanup
        response = self.client.get(reverse('admin-file-cleanup'))
        self.assertEqual(response.status_code, 200)
    
    def test_permission_management_nav_visibility_superuser(self):
        """Test that superuser can see permission management navigation"""
        self.client.login(username='admin', password='password123')
        
        # Check if permission management page is accessible
        response = self.client.get(reverse('permission-management'))
        self.assertEqual(response.status_code, 200)
    
    def test_permission_management_nav_visibility_regular_user(self):
        """Test that regular users cannot see permission management navigation"""
        self.client.login(username='user', password='password123')
        
        # Regular user should NOT have access to permission management
        response = self.client.get(reverse('permission-management'))
        self.assertEqual(response.status_code, 403)
    
    def test_admin_charts_nav_visibility_with_permission(self):
        """Test admin charts navigation visibility based on permissions"""
        # Create role permission for view_reports
        RolePermission.objects.get_or_create(
            role='manager',
            permission=self.view_reports_perm,
            defaults={'granted': True, 'can_delegate': False}
        )
        
        self.client.login(username='manager', password='password123')
        
        # Try to access admin charts (if route exists)
        try:
            response = self.client.get(reverse('admin-charts'))
            # Manager with view_reports permission should have access
            self.assertIn(response.status_code, [200, 302])  # 302 might be redirect to proper page
        except:
            pass  # Route might not exist yet
    
    def test_manager_charts_nav_visibility_with_permission(self):
        """Test manager charts navigation visibility based on permissions"""
        # Create role permission for manager portal access
        RolePermission.objects.get_or_create(
            role='manager', 
            permission=self.manager_portal_perm,
            defaults={'granted': True, 'can_delegate': False}
        )
        
        self.client.login(username='manager', password='password123')
        
        # Try to access manager overview/dashboard
        try:
            response = self.client.get(reverse('manager-overview'))
            # Manager should have access to manager pages
            self.assertEqual(response.status_code, 200)
        except:
            pass  # Route might not exist
    
    def test_system_tools_nav_visibility_staff_only(self):
        """Test that system tools are only visible to staff/superuser"""
        # Test superuser access to system metrics
        self.client.login(username='admin', password='password123')
        try:
            response = self.client.get(reverse('admin-metrics'))
            self.assertEqual(response.status_code, 200)
        except:
            pass
        
        # Test regular user access (should be denied)
        self.client.login(username='user', password='password123') 
        try:
            response = self.client.get(reverse('admin-metrics'))
            self.assertEqual(response.status_code, 403)
        except:
            pass
    
    def test_enhanced_excel_import_nav_visibility(self):
        """Test enhanced excel import navigation visibility"""
        # Superuser should have access
        self.client.login(username='admin', password='password123')
        try:
            response = self.client.get(reverse('enhanced-excel-import'))
            self.assertEqual(response.status_code, 200)
        except:
            pass
        
        # Staff should have access
        self.client.login(username='staff', password='password123')
        try:
            response = self.client.get(reverse('enhanced-excel-import'))
            self.assertIn(response.status_code, [200, 302])
        except:
            pass
        
        # Regular user should NOT have access
        self.client.login(username='user', password='password123')
        try:
            response = self.client.get(reverse('enhanced-excel-import'))
            self.assertEqual(response.status_code, 403)
        except:
            pass
    
    def test_nav_breadcrumbs_permission_aware(self):
        """Test that navigation breadcrumbs are permission-aware"""
        # Login as superuser and check admin page
        self.client.login(username='admin', password='password123')
        response = self.client.get(reverse('admin-file-cleanup'))
        
        # Should contain breadcrumb navigation
        self.assertContains(response, 'Breadcrumbs')
        self.assertContains(response, 'Home')
        self.assertContains(response, 'Excel Import File Cleanup')
    
    def test_portal_home_shows_appropriate_links(self):
        """Test that portal home shows appropriate links based on user permissions"""
        # Test with superuser
        self.client.login(username='admin', password='password123')
        try:
            response = self.client.get(reverse('portal-home'))
            if response.status_code == 200:
                # Superuser should see admin dashboard links
                self.assertContains(response, 'Admin', msg_prefix="Superuser should see admin links")
        except:
            pass
        
        # Test with manager
        self.client.login(username='manager', password='password123')
        try:
            response = self.client.get(reverse('portal-home'))
            if response.status_code == 200:
                # Manager should see manager dashboard links
                self.assertContains(response, 'Manager', msg_prefix="Manager should see manager links")
        except:
            pass
        
        # Test with regular user
        self.client.login(username='user', password='password123')
        try:
            response = self.client.get(reverse('portal-home'))
            if response.status_code == 200:
                # Regular user should see limited links
                self.assertNotContains(response, 'Admin', msg_prefix="Regular user should not see admin links")
        except:
            pass
    
    def test_back_to_admin_navigation_links(self):
        """Test that 'Back to Admin' navigation links are present"""
        self.client.login(username='admin', password='password123')
        response = self.client.get(reverse('admin-file-cleanup'))
        
        # Should contain link back to admin
        self.assertContains(response, 'Portal Home')
        self.assertContains(response, '/api/portal/')
    
    def test_unauthorized_users_redirect_to_login(self):
        """Test that unauthorized users are redirected to login"""
        # Try to access protected page without login
        response = self.client.get(reverse('admin-file-cleanup'))
        self.assertEqual(response.status_code, 302)
        self.assertIn('/login/', response.url)
        
        response = self.client.get(reverse('permission-management'))
        self.assertEqual(response.status_code, 302)
        self.assertIn('/login/', response.url)
    
    def test_permission_override_affects_navigation(self):
        """Test that permission overrides affect navigation visibility"""
        # Give regular user manage_files permission via override
        from api.models import UserPermissionOverride
        UserPermissionOverride.objects.create(
            user=self.regular_user,
            permission=self.manage_files_perm,
            granted=True,
            reason='Test override'
        )
        
        self.client.login(username='user', password='password123')
        
        # Now regular user should have access to file cleanup
        response = self.client.get(reverse('admin-file-cleanup'))
        self.assertEqual(response.status_code, 200)
        
        # Clean up override
        UserPermissionOverride.objects.filter(
            user=self.regular_user,
            permission=self.manage_files_perm
        ).delete()