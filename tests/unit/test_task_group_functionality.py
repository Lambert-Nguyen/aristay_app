"""
Unit tests for TaskGroup functionality
"""
import pytest
from django.test import TestCase
from django.contrib.auth import get_user_model
from api.models import Profile, TaskGroup, UserRole

User = get_user_model()


class TaskGroupFunctionalityTestCase(TestCase):
    """Test cases for TaskGroup functionality"""
    
    def setUp(self):
        """Set up test data"""
        # Create test users with different roles and task groups
        self.superuser = User.objects.create_user(
            username='superuser',
            email='super@test.com',
            password='testpass123',
            is_superuser=True,
        )
        self.superuser_profile, _ = Profile.objects.get_or_create(
            user=self.superuser,
            defaults={'role': UserRole.SUPERUSER, 'task_group': TaskGroup.NONE}
        )
        # Update role after creation since signal may have overridden it
        self.superuser_profile.role = UserRole.SUPERUSER
        self.superuser_profile.save()
        
        self.manager = User.objects.create_user(
            username='manager',
            email='manager@test.com',
            password='testpass123'
        )
        self.manager_profile, _ = Profile.objects.get_or_create(
            user=self.manager,
            defaults={'role': UserRole.MANAGER, 'task_group': TaskGroup.NONE}
        )
        # Update role after creation since signal may have overridden it
        self.manager_profile.role = UserRole.MANAGER
        self.manager_profile.save()
        
        self.cleaning_staff = User.objects.create_user(
            username='cleaning_staff',
            email='cleaning@test.com',
            password='testpass123'
        )
        self.cleaning_profile, created = Profile.objects.get_or_create(
            user=self.cleaning_staff,
            defaults={'role': UserRole.STAFF, 'task_group': TaskGroup.CLEANING}
        )
        if not created:
            self.cleaning_profile.task_group = TaskGroup.CLEANING
            self.cleaning_profile.save()
        
        self.maintenance_staff = User.objects.create_user(
            username='maintenance_staff',
            email='maintenance@test.com',
            password='testpass123'
        )
        self.maintenance_profile, created = Profile.objects.get_or_create(
            user=self.maintenance_staff,
            defaults={'role': UserRole.STAFF, 'task_group': TaskGroup.MAINTENANCE}
        )
        if not created:
            self.maintenance_profile.task_group = TaskGroup.MAINTENANCE
            self.maintenance_profile.save()
        
        self.general_staff = User.objects.create_user(
            username='general_staff',
            email='general@test.com',
            password='testpass123'
        )
        self.general_profile, created = Profile.objects.get_or_create(
            user=self.general_staff,
            defaults={'role': UserRole.STAFF, 'task_group': TaskGroup.GENERAL}
        )
        if not created:
            self.general_profile.task_group = TaskGroup.GENERAL
            self.general_profile.save()
        
        self.viewer = User.objects.create_user(
            username='viewer',
            email='viewer@test.com',
            password='testpass123'
        )
        self.viewer_profile, created = Profile.objects.get_or_create(
            user=self.viewer,
            defaults={'role': UserRole.VIEWER, 'task_group': TaskGroup.NONE}
        )
        # Update role after creation since signal may have overridden it
        self.viewer_profile.role = UserRole.VIEWER
        self.viewer_profile.task_group = TaskGroup.NONE
        self.viewer_profile.save()
    
    def test_task_group_choices(self):
        """Test that TaskGroup choices are properly defined"""
        choices = TaskGroup.choices
        expected_choices = [
            ('cleaning', 'Cleaning'),
            ('maintenance', 'Maintenance'),
            ('laundry', 'Laundry'),
            ('lawn_pool', 'Lawn/Pool'),
            ('general', 'General'),
            ('none', 'Not Assigned'),
        ]
        
        self.assertEqual(len(choices), len(expected_choices))
        for expected_choice in expected_choices:
            self.assertIn(expected_choice, choices)
    
    def test_get_task_group_display(self):
        """Test get_task_group_display method"""
        self.assertEqual(self.cleaning_profile.get_task_group_display(), 'Cleaning')
        self.assertEqual(self.maintenance_profile.get_task_group_display(), 'Maintenance')
        self.assertEqual(self.general_profile.get_task_group_display(), 'General')
        self.assertEqual(self.superuser_profile.get_task_group_display(), 'Not Assigned')
    
    def test_is_in_task_group(self):
        """Test is_in_task_group method"""
        self.assertTrue(self.cleaning_profile.is_in_task_group(TaskGroup.CLEANING))
        self.assertFalse(self.cleaning_profile.is_in_task_group(TaskGroup.MAINTENANCE))
        self.assertTrue(self.general_profile.is_in_task_group(TaskGroup.GENERAL))
        self.assertFalse(self.general_profile.is_in_task_group(TaskGroup.CLEANING))
    
    def test_can_view_task_group_staff(self):
        """Test can_view_task_group for staff users"""
        # Debug: Check what task groups the profiles actually have
        print(f"Cleaning profile task_group: {self.cleaning_profile.task_group}")
        print(f"Maintenance profile task_group: {self.maintenance_profile.task_group}")
        print(f"General profile task_group: {self.general_profile.task_group}")
        
        # Staff can view their own task group
        self.assertTrue(self.cleaning_profile.can_view_task_group(TaskGroup.CLEANING))
        self.assertTrue(self.maintenance_profile.can_view_task_group(TaskGroup.MAINTENANCE))
        self.assertTrue(self.general_profile.can_view_task_group(TaskGroup.GENERAL))
        
        # Staff can view general tasks
        self.assertTrue(self.cleaning_profile.can_view_task_group(TaskGroup.GENERAL))
        self.assertTrue(self.maintenance_profile.can_view_task_group(TaskGroup.GENERAL))
        
        # Staff cannot view other specific task groups
        self.assertFalse(self.cleaning_profile.can_view_task_group(TaskGroup.MAINTENANCE))
        self.assertFalse(self.cleaning_profile.can_view_task_group(TaskGroup.LAUNDRY))
        self.assertFalse(self.cleaning_profile.can_view_task_group(TaskGroup.LAWN_POOL))
        
        self.assertFalse(self.maintenance_profile.can_view_task_group(TaskGroup.CLEANING))
        self.assertFalse(self.maintenance_profile.can_view_task_group(TaskGroup.LAUNDRY))
    
    def test_can_view_task_group_managers(self):
        """Test can_view_task_group for managers and superusers"""
        # Managers and superusers can view all task groups
        for task_group in [TaskGroup.CLEANING, TaskGroup.MAINTENANCE, TaskGroup.LAUNDRY, 
                          TaskGroup.LAWN_POOL, TaskGroup.GENERAL]:
            self.assertTrue(self.manager_profile.can_view_task_group(task_group))
            self.assertTrue(self.superuser_profile.can_view_task_group(task_group))
    
    def test_can_view_task_group_viewers(self):
        """Test can_view_task_group for viewers"""
        # Viewers have limited access by default
        self.assertFalse(self.viewer_profile.can_view_task_group(TaskGroup.CLEANING))
        self.assertFalse(self.viewer_profile.can_view_task_group(TaskGroup.MAINTENANCE))
        
        # Enable cross-team viewing for viewer
        self.viewer_profile.can_view_other_teams = True
        self.viewer_profile.save()
        
        # Now viewer can view all task groups
        for task_group in [TaskGroup.CLEANING, TaskGroup.MAINTENANCE, TaskGroup.LAUNDRY, 
                          TaskGroup.LAWN_POOL, TaskGroup.GENERAL]:
            self.assertTrue(self.viewer_profile.can_view_task_group(task_group))
    
    def test_get_accessible_task_groups_staff(self):
        """Test get_accessible_task_groups for staff users"""
        # Cleaning staff can access cleaning and general
        cleaning_groups = self.cleaning_profile.get_accessible_task_groups()
        self.assertIn(TaskGroup.CLEANING, cleaning_groups)
        self.assertIn(TaskGroup.GENERAL, cleaning_groups)
        self.assertNotIn(TaskGroup.MAINTENANCE, cleaning_groups)
        
        # Maintenance staff can access maintenance and general
        maintenance_groups = self.maintenance_profile.get_accessible_task_groups()
        self.assertIn(TaskGroup.MAINTENANCE, maintenance_groups)
        self.assertIn(TaskGroup.GENERAL, maintenance_groups)
        self.assertNotIn(TaskGroup.CLEANING, maintenance_groups)
        
        # General staff can only access general
        general_groups = self.general_profile.get_accessible_task_groups()
        self.assertEqual(general_groups, [TaskGroup.GENERAL])
    
    def test_get_accessible_task_groups_managers(self):
        """Test get_accessible_task_groups for managers and superusers"""
        # Managers and superusers can access all task groups except NONE
        expected_groups = [TaskGroup.CLEANING, TaskGroup.MAINTENANCE, TaskGroup.LAUNDRY, 
                          TaskGroup.LAWN_POOL, TaskGroup.GENERAL]
        
        manager_groups = self.manager_profile.get_accessible_task_groups()
        superuser_groups = self.superuser_profile.get_accessible_task_groups()
        
        print(f"Manager profile role: {self.manager_profile.role}")
        print(f"Manager profile task_group: {self.manager_profile.task_group}")
        print(f"Manager groups: {manager_groups}")
        print(f"Superuser profile role: {self.superuser_profile.role}")
        print(f"Superuser profile task_group: {self.superuser_profile.task_group}")
        print(f"Superuser groups: {superuser_groups}")
        
        for group in expected_groups:
            self.assertIn(group, manager_groups)
            self.assertIn(group, superuser_groups)
        
        self.assertNotIn(TaskGroup.NONE, manager_groups)
        self.assertNotIn(TaskGroup.NONE, superuser_groups)
    
    def test_get_accessible_task_groups_viewers(self):
        """Test get_accessible_task_groups for viewers"""
        # Viewer with limited access gets empty list
        viewer_groups = self.viewer_profile.get_accessible_task_groups()
        self.assertEqual(viewer_groups, [])
        
        # Enable cross-team viewing for viewer
        self.viewer_profile.can_view_other_teams = True
        self.viewer_profile.save()
        
        # Now viewer can access all task groups
        viewer_groups = self.viewer_profile.get_accessible_task_groups()
        expected_groups = [TaskGroup.CLEANING, TaskGroup.MAINTENANCE, TaskGroup.LAUNDRY, 
                          TaskGroup.LAWN_POOL, TaskGroup.GENERAL]
        
        for group in expected_groups:
            self.assertIn(group, viewer_groups)
    
    def test_task_group_default_values(self):
        """Test that task groups have correct default values"""
        # Test that new profiles get NONE as default task group
        new_user = User.objects.create_user(
            username='new_user',
            email='new@test.com',
            password='testpass123'
        )
        # The post_save signal will create a profile automatically
        new_profile = Profile.objects.get(user=new_user)
        
        self.assertEqual(new_profile.task_group, TaskGroup.NONE)
        self.assertEqual(new_profile.get_task_group_display(), 'Not Assigned')
    
    def test_task_group_string_representation(self):
        """Test string representation of TaskGroup choices"""
        # Test that we can get the display value from the choice
        task_group_dict = dict(TaskGroup.choices)
        self.assertEqual(task_group_dict[TaskGroup.CLEANING], 'Cleaning')
        self.assertEqual(task_group_dict[TaskGroup.MAINTENANCE], 'Maintenance')
        self.assertEqual(task_group_dict[TaskGroup.LAUNDRY], 'Laundry')
        self.assertEqual(task_group_dict[TaskGroup.LAWN_POOL], 'Lawn/Pool')
        self.assertEqual(task_group_dict[TaskGroup.GENERAL], 'General')
        self.assertEqual(task_group_dict[TaskGroup.NONE], 'Not Assigned')
    
    def test_task_group_permission_edge_cases(self):
        """Test edge cases for task group permissions"""
        # Test with invalid task group
        self.assertFalse(self.cleaning_profile.can_view_task_group('invalid_group'))
        
        # Test with None task group
        self.assertFalse(self.cleaning_profile.can_view_task_group(None))
        
        # Test that staff with NONE task group can only view general
        none_staff = User.objects.create_user(
            username='none_staff',
            email='none@test.com',
            password='testpass123'
        )
        # The post_save signal will create a profile automatically
        none_profile = Profile.objects.get(user=none_staff)
        none_profile.role = UserRole.STAFF
        none_profile.task_group = TaskGroup.NONE
        none_profile.save()
        
        self.assertFalse(none_profile.can_view_task_group(TaskGroup.CLEANING))
        self.assertFalse(none_profile.can_view_task_group(TaskGroup.MAINTENANCE))
        self.assertTrue(none_profile.can_view_task_group(TaskGroup.GENERAL))
        
        # Test accessible groups for NONE staff
        none_groups = none_profile.get_accessible_task_groups()
        self.assertEqual(none_groups, [TaskGroup.GENERAL])
