"""
Unit tests for assign_task_groups management command
"""
import pytest
from django.test import TestCase
from django.core.management import call_command
from django.core.management.base import CommandError
from io import StringIO
from django.contrib.auth import get_user_model
from api.models import Profile, TaskGroup, UserRole

User = get_user_model()


class AssignTaskGroupsCommandTestCase(TestCase):
    """Test cases for assign_task_groups management command"""
    
    def setUp(self):
        """Set up test data"""
        # Create test users with different roles
        self.superuser = User.objects.create_user(
            username='superuser',
            email='super@test.com',
            password='testpass123',
            is_superuser=True,
            is_staff=True
        )
        
        self.manager = User.objects.create_user(
            username='manager',
            email='manager@test.com',
            password='testpass123'
        )
        
        self.staff1 = User.objects.create_user(
            username='staff1',
            email='staff1@test.com',
            password='testpass123'
        )
        
        self.staff2 = User.objects.create_user(
            username='staff2',
            email='staff2@test.com',
            password='testpass123'
        )
        
        # Create profiles for all users (signal may have already created them)
        superuser_profile, _ = Profile.objects.get_or_create(
            user=self.superuser, 
            defaults={'role': UserRole.SUPERUSER, 'task_group': TaskGroup.NONE}
        )
        superuser_profile.role = UserRole.SUPERUSER
        superuser_profile.save()
        
        manager_profile, _ = Profile.objects.get_or_create(
            user=self.manager, 
            defaults={'role': UserRole.MANAGER, 'task_group': TaskGroup.NONE}
        )
        manager_profile.role = UserRole.MANAGER
        manager_profile.save()
        
        staff1_profile, _ = Profile.objects.get_or_create(
            user=self.staff1, 
            defaults={'role': UserRole.STAFF, 'task_group': TaskGroup.NONE}
        )
        staff1_profile.role = UserRole.STAFF
        staff1_profile.save()
        
        staff2_profile, _ = Profile.objects.get_or_create(
            user=self.staff2, 
            defaults={'role': UserRole.STAFF, 'task_group': TaskGroup.NONE}
        )
        staff2_profile.role = UserRole.STAFF
        staff2_profile.save()
    
    def test_list_groups_command(self):
        """Test --list-groups option"""
        out = StringIO()
        call_command('assign_task_groups', '--list-groups', stdout=out)
        output = out.getvalue()
        
        self.assertIn('Available Task Groups:', output)
        self.assertIn('cleaning        - Cleaning', output)
        self.assertIn('maintenance     - Maintenance', output)
        self.assertIn('laundry         - Laundry', output)
        self.assertIn('lawn_pool       - Lawn/Pool', output)
        self.assertIn('general         - General', output)
        self.assertIn('none            - Not Assigned', output)
    
    def test_show_users_command(self):
        """Test --show-users option"""
        out = StringIO()
        call_command('assign_task_groups', '--show-users', stdout=out)
        output = out.getvalue()
        
        self.assertIn('Users and Task Groups:', output)
        self.assertIn('superuser', output)
        self.assertIn('manager', output)
        self.assertIn('staff1', output)
        self.assertIn('staff2', output)
        self.assertIn('Not Assigned', output)
    
    def test_auto_assign_command(self):
        """Test --auto-assign option"""
        out = StringIO()
        call_command('assign_task_groups', '--auto-assign', stdout=out)
        output = out.getvalue()
        
        # Check that staff users were assigned to general group
        self.assertIn('Assigned staff1 to general', output)
        self.assertIn('Assigned staff2 to general', output)
        self.assertIn('Auto-assigned task groups to 3 users', output)
        
        # Verify the assignments
        staff1_profile = Profile.objects.get(user=self.staff1)
        staff2_profile = Profile.objects.get(user=self.staff2)
        
        self.assertEqual(staff1_profile.task_group, TaskGroup.GENERAL)
        self.assertEqual(staff2_profile.task_group, TaskGroup.GENERAL)
        
        # Superuser and manager should remain NONE
        superuser_profile = Profile.objects.get(user=self.superuser)
        manager_profile = Profile.objects.get(user=self.manager)
        
        self.assertEqual(superuser_profile.task_group, TaskGroup.NONE)
        self.assertEqual(manager_profile.task_group, TaskGroup.NONE)
    
    def test_assign_specific_user_command(self):
        """Test assigning specific user to task group"""
        out = StringIO()
        call_command('assign_task_groups', '--username', 'staff1', '--task-group', 'cleaning', stdout=out)
        output = out.getvalue()
        
        self.assertIn('Updated staff1: Not Assigned → Cleaning', output)
        
        # Verify the assignment
        staff1_profile = Profile.objects.get(user=self.staff1)
        self.assertEqual(staff1_profile.task_group, TaskGroup.CLEANING)
    
    def test_assign_specific_user_invalid_user(self):
        """Test assigning task group to non-existent user"""
        out = StringIO()
        err = StringIO()
        
        # Command should not raise exception, but should print error message
        call_command('assign_task_groups', '--username', 'nonexistent', '--task-group', 'cleaning', 
                    stdout=out, stderr=err)
        
        # Check that error message was printed
        self.assertIn('User "nonexistent" not found', out.getvalue())
    
    def test_assign_specific_user_invalid_task_group(self):
        """Test assigning invalid task group"""
        out = StringIO()
        err = StringIO()
        
        with self.assertRaises(CommandError):  # Django's call_command converts SystemExit to CommandError
            call_command('assign_task_groups', '--username', 'staff1', '--task-group', 'invalid', 
                        stdout=out, stderr=err)
    
    def test_auto_assign_with_groups(self):
        """Test auto-assignment with Django groups"""
        from django.contrib.auth.models import Group
        
        # Create groups
        cleaning_group = Group.objects.create(name='Cleaning')
        maintenance_group = Group.objects.create(name='Maintenance')
        
        # Assign users to groups
        self.staff1.groups.add(cleaning_group)
        self.staff2.groups.add(maintenance_group)
        
        out = StringIO()
        call_command('assign_task_groups', '--auto-assign', stdout=out)
        output = out.getvalue()
        
        # Check that users were assigned based on their groups
        self.assertIn('Assigned staff1 to cleaning (based on Cleaning group)', output)
        self.assertIn('Assigned staff2 to maintenance (based on Maintenance group)', output)
        
        # Verify the assignments
        staff1_profile = Profile.objects.get(user=self.staff1)
        staff2_profile = Profile.objects.get(user=self.staff2)
        
        self.assertEqual(staff1_profile.task_group, TaskGroup.CLEANING)
        self.assertEqual(staff2_profile.task_group, TaskGroup.MAINTENANCE)
    
    def test_auto_assign_skips_existing_assignments(self):
        """Test that auto-assign skips users already assigned to task groups"""
        # Pre-assign staff1 to cleaning
        staff1_profile = Profile.objects.get(user=self.staff1)
        staff1_profile.task_group = TaskGroup.CLEANING
        staff1_profile.save()
        
        out = StringIO()
        call_command('assign_task_groups', '--auto-assign', stdout=out)
        output = out.getvalue()
        
        # Should only assign staff2, not staff1
        self.assertNotIn('staff1', output)
        self.assertIn('Assigned staff2 to general', output)
        self.assertIn('Auto-assigned task groups to 2 users', output)
        
        # Verify staff1 still has cleaning assignment
        staff1_profile.refresh_from_db()
        self.assertEqual(staff1_profile.task_group, TaskGroup.CLEANING)
    
    def test_assign_specific_user_creates_profile(self):
        """Test that assigning to user without profile creates profile"""
        # Create user without profile
        new_user = User.objects.create_user(
            username='newuser',
            email='new@test.com',
            password='testpass123'
        )
        
        # Delete any auto-created profile
        Profile.objects.filter(user=new_user).delete()
        
        out = StringIO()
        call_command('assign_task_groups', '--username', 'newuser', '--task-group', 'laundry', stdout=out)
        output = out.getvalue()
        
        self.assertIn('Created profile for newuser', output)
        self.assertIn('Updated newuser: Not Assigned → Laundry', output)
        
        # Verify the profile was created and assigned
        new_user_profile = Profile.objects.get(user=new_user)
        self.assertEqual(new_user_profile.task_group, TaskGroup.LAUNDRY)
        self.assertEqual(new_user_profile.role, UserRole.STAFF)  # Default role
    
    def test_command_without_arguments(self):
        """Test command without any arguments shows help"""
        out = StringIO()
        err = StringIO()
        
        # Command should not raise exception, but should print warning message
        call_command('assign_task_groups', stdout=out, stderr=err)
        
        # Should show warning about specifying an action
        self.assertIn('Please specify an action', out.getvalue())
    
    def test_assign_specific_user_updates_existing(self):
        """Test that assigning to user with existing task group updates it"""
        # Pre-assign staff1 to general
        staff1_profile = Profile.objects.get(user=self.staff1)
        staff1_profile.task_group = TaskGroup.GENERAL
        staff1_profile.save()
        
        out = StringIO()
        call_command('assign_task_groups', '--username', 'staff1', '--task-group', 'maintenance', stdout=out)
        output = out.getvalue()
        
        self.assertIn('Updated staff1: General → Maintenance', output)
        
        # Verify the update
        staff1_profile.refresh_from_db()
        self.assertEqual(staff1_profile.task_group, TaskGroup.MAINTENANCE)
