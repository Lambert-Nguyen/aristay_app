"""
Integration tests for Invite Code Management system
Tests the complete workflow from creation to usage
"""
import pytest
from django.test import TestCase, Client
from django.contrib.auth import get_user_model
from django.utils import timezone
from datetime import timedelta
import json

from api.models import InviteCode, Profile, UserRole, TaskGroup

User = get_user_model()


class InviteCodeIntegrationTestCase(TestCase):
    """Integration tests for invite code management"""
    
    def setUp(self):
        """Set up test data"""
        # Create admin user
        self.admin = User.objects.create_user(
            username='admin',
            email='admin@test.com',
            password='testpass123',
            is_superuser=True,
            is_staff=True
        )
        
        # Create manager user
        self.manager = User.objects.create_user(
            username='manager',
            email='manager@test.com',
            password='testpass123',
            is_staff=True
        )
        # Ensure manager has correct profile
        Profile.objects.filter(user=self.manager).delete()
        Profile.objects.create(
            user=self.manager,
            role=UserRole.MANAGER,
            can_view_team_tasks=True
        )
        
        self.client = Client()
    
    def test_complete_invite_code_workflow_admin(self):
        """Test complete invite code workflow via admin portal"""
        self.client.login(username='admin', password='testpass123')
        
        # Step 1: Create invite code
        data = {
            'role': UserRole.STAFF,
            'task_group': TaskGroup.CLEANING,
            'max_uses': 3,
            'expires_days': '30',
            'notes': 'Integration test code'
        }
        
        response = self.client.post('/admin/create-invite-code/', data)
        self.assertEqual(response.status_code, 302)
        
        # Step 2: Verify code was created
        invite_code = InviteCode.objects.filter(notes='Integration test code').first()
        self.assertIsNotNone(invite_code)
        self.assertEqual(invite_code.role, UserRole.STAFF)
        self.assertEqual(invite_code.task_group, TaskGroup.CLEANING)
        self.assertEqual(invite_code.max_uses, 3)
        self.assertTrue(invite_code.is_active)
        self.assertTrue(invite_code.is_usable)
        
        # Step 3: View invite code list
        response = self.client.get('/admin/invite-codes/')
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, invite_code.code)
        
        # Step 4: View invite code detail
        response = self.client.get(f'/admin/invite-codes/{invite_code.id}/')
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, invite_code.code)
        self.assertContains(response, 'Basic Information')
        self.assertContains(response, 'Status & Usage')
        
        # Step 5: Edit invite code
        edit_data = {
            'role': UserRole.MANAGER,
            'task_group': TaskGroup.MAINTENANCE,
            'max_uses': 5,
            'expires_days': '60',
            'notes': 'Updated integration test code'
        }
        
        response = self.client.post(f'/admin/invite-codes/{invite_code.id}/edit/', edit_data)
        self.assertEqual(response.status_code, 302)
        
        # Step 6: Verify changes
        invite_code.refresh_from_db()
        self.assertEqual(invite_code.role, UserRole.MANAGER)
        self.assertEqual(invite_code.task_group, TaskGroup.MAINTENANCE)
        self.assertEqual(invite_code.max_uses, 5)
        self.assertEqual(invite_code.notes, 'Updated integration test code')
        
        # Step 7: Revoke invite code
        response = self.client.post(f'/admin/invite-codes/{invite_code.id}/revoke/')
        self.assertEqual(response.status_code, 302)
        
        # Step 8: Verify revocation
        invite_code.refresh_from_db()
        self.assertFalse(invite_code.is_active)
        self.assertFalse(invite_code.is_usable)
        
        # Step 9: Reactivate invite code
        response = self.client.post(f'/admin/invite-codes/{invite_code.id}/reactivate/')
        self.assertEqual(response.status_code, 302)
        
        # Step 10: Verify reactivation
        invite_code.refresh_from_db()
        self.assertTrue(invite_code.is_active)
        self.assertTrue(invite_code.is_usable)
        
        # Step 11: Delete invite code
        response = self.client.post(f'/admin/invite-codes/{invite_code.id}/delete/')
        self.assertEqual(response.status_code, 302)
        
        # Step 12: Verify deletion
        self.assertFalse(InviteCode.objects.filter(id=invite_code.id).exists())
    
    def test_complete_invite_code_workflow_manager(self):
        """Test complete invite code workflow via manager portal"""
        self.client.force_login(self.manager)
        
        # Step 1: Create invite code
        data = {
            'role': UserRole.STAFF,
            'task_group': TaskGroup.LAUNDRY,
            'max_uses': 2,
            'expires_days': '14',
            'notes': 'Manager created code'
        }
        
        response = self.client.post('/admin/create-invite-code/', data, HTTP_HOST='testserver')
        self.assertEqual(response.status_code, 302)
        
        # Step 2: Verify code was created
        invite_code = InviteCode.objects.filter(notes='Manager created code').first()
        self.assertIsNotNone(invite_code)
        self.assertEqual(invite_code.created_by, self.manager)
        self.assertEqual(invite_code.role, UserRole.STAFF)
        self.assertEqual(invite_code.task_group, TaskGroup.LAUNDRY)
        
        # Step 3: View invite code list
        response = self.client.get('/manager/invite-codes/')
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, invite_code.code)
        
        # Step 4: Test filtering
        response = self.client.get('/manager/invite-codes/?role=staff')
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, invite_code.code)
        
        # Step 5: Test search
        response = self.client.get('/manager/invite-codes/?search=Manager')
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, invite_code.code)
    
    def test_invite_code_api_workflow(self):
        """Test invite code management via API"""
        self.client.login(username='admin', password='testpass123')
        
        # Step 1: Create invite code via API
        data = {
            'role': UserRole.VIEWER,
            'task_group': TaskGroup.LAWN_POOL,
            'max_uses': 1,
            'expires_days': '7',
            'notes': 'API test code'
        }
        
        response = self.client.post('/api/invite-codes/create/', data, content_type='application/json')
        self.assertEqual(response.status_code, 201)
        
        response_data = response.json()
        self.assertTrue(response_data['success'])
        invite_code_id = response_data['data']['id']
        
        # Step 2: Verify code was created
        invite_code = InviteCode.objects.get(id=invite_code_id)
        self.assertEqual(invite_code.role, UserRole.VIEWER)
        self.assertEqual(invite_code.task_group, TaskGroup.LAWN_POOL)
        self.assertTrue(invite_code.is_active)
        
        # Step 3: Revoke invite code via API
        response = self.client.post(f'/api/invite-codes/{invite_code_id}/revoke/')
        self.assertEqual(response.status_code, 200)
        
        response_data = response.json()
        self.assertTrue(response_data['success'])
        
        # Step 4: Verify revocation
        invite_code.refresh_from_db()
        self.assertFalse(invite_code.is_active)
    
    def test_invite_code_filtering_and_search(self):
        """Test invite code filtering and search functionality"""
        # Create test invite codes
        codes = []
        for i, (role, task_group) in enumerate([
            (UserRole.STAFF, TaskGroup.CLEANING),
            (UserRole.MANAGER, TaskGroup.MAINTENANCE),
            (UserRole.STAFF, TaskGroup.LAUNDRY),
            (UserRole.VIEWER, TaskGroup.LAWN_POOL),
        ]):
            code = InviteCode.objects.create(
                code=f'FILTER{i:02d}',
                created_by=self.admin,
                task_group=task_group,
                role=role,
                notes=f'Filter test {i}'
            )
            codes.append(code)
        
        # Make one code expired
        codes[0].expires_at = timezone.now() - timedelta(days=1)
        codes[0].save()
        
        # Make one code inactive
        codes[1].is_active = False
        codes[1].save()
        
        self.client.login(username='admin', password='testpass123')
        
        # Test role filtering
        response = self.client.get('/admin/invite-codes/?role=staff')
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'FILTER00')  # Staff code
        self.assertContains(response, 'FILTER02')  # Staff code
        self.assertNotContains(response, 'FILTER01')  # Manager code
        self.assertNotContains(response, 'FILTER03')  # Viewer code
        
        # Test task group filtering
        response = self.client.get('/admin/invite-codes/?task_group=cleaning')
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'FILTER00')  # Cleaning code
        self.assertNotContains(response, 'FILTER01')  # Maintenance code
        
        # Test status filtering
        response = self.client.get('/admin/invite-codes/?status=expired')
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'FILTER00')  # Expired code
        self.assertNotContains(response, 'FILTER02')  # Active code
        
        response = self.client.get('/admin/invite-codes/?status=inactive')
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'FILTER01')  # Inactive code
        self.assertNotContains(response, 'FILTER02')  # Active code
        
        # Test search functionality
        response = self.client.get('/admin/invite-codes/?search=FILTER00')
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'FILTER00')
        self.assertNotContains(response, 'FILTER01')
        
        response = self.client.get('/admin/invite-codes/?search=Filter test 2')
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'FILTER02')
        self.assertNotContains(response, 'FILTER01')
    
    def test_invite_code_permissions(self):
        """Test invite code permissions across different user types"""
        # Create staff user
        staff = User.objects.create_user(
            username='staff',
            email='staff@test.com',
            password='testpass123'
        )
        Profile.objects.get_or_create(
            user=staff,
            defaults={'role': UserRole.STAFF}
        )
        
        # Create invite code
        invite_code = InviteCode.objects.create(
            code='PERM123',
            created_by=self.admin,
            task_group=TaskGroup.GENERAL,
            role=UserRole.STAFF
        )
        
        # Test staff user access (should be denied)
        self.client.login(username='staff', password='testpass123')
        
        admin_endpoints = [
            '/admin/invite-codes/',
            '/admin/create-invite-code/',
            f'/admin/invite-codes/{invite_code.id}/',
            f'/admin/invite-codes/{invite_code.id}/edit/',
            f'/admin/invite-codes/{invite_code.id}/revoke/',
            f'/admin/invite-codes/{invite_code.id}/reactivate/',
            f'/admin/invite-codes/{invite_code.id}/delete/',
        ]
        
        for endpoint in admin_endpoints:
            response = self.client.get(endpoint)
            self.assertIn(response.status_code, [302, 403], f"Staff should not access {endpoint}")
        
        manager_endpoints = [
            '/manager/invite-codes/',
            '/manager/create-invite-code/',
            f'/manager/invite-codes/{invite_code.id}/',
            f'/manager/invite-codes/{invite_code.id}/edit/',
            f'/manager/invite-codes/{invite_code.id}/revoke/',
            f'/manager/invite-codes/{invite_code.id}/reactivate/',
            f'/manager/invite-codes/{invite_code.id}/delete/',
        ]
        
        for endpoint in manager_endpoints:
            response = self.client.get(endpoint)
            self.assertIn(response.status_code, [302, 403], f"Staff should not access {endpoint}")
        
        # Test manager user access (should be allowed)
        self.client.login(username='manager', password='testpass123')
        
        response = self.client.get('/manager/invite-codes/')
        self.assertEqual(response.status_code, 200)
        
        response = self.client.get('/manager/create-invite-code/')
        self.assertEqual(response.status_code, 200)
        
        # Test admin user access (should be allowed)
        self.client.login(username='admin', password='testpass123')
        
        response = self.client.get('/admin/invite-codes/')
        self.assertEqual(response.status_code, 200)
        
        response = self.client.get('/admin/create-invite-code/')
        self.assertEqual(response.status_code, 200)
    
    def test_invite_code_usage_tracking(self):
        """Test invite code usage tracking"""
        # Create invite code with multiple uses
        invite_code = InviteCode.objects.create(
            code='USAGE123',
            created_by=self.admin,
            task_group=TaskGroup.GENERAL,
            role=UserRole.STAFF,
            max_uses=3
        )
        
        # Create test users
        users = []
        for i in range(3):
            user = User.objects.create_user(
                username=f'user{i}',
                email=f'user{i}@test.com',
                password='testpass123'
            )
            users.append(user)
        
        # Simulate code usage
        for user in users:
            invite_code.use_code(user)
        
        # Check usage tracking
        invite_code.refresh_from_db()
        self.assertEqual(invite_code.used_count, 3)
        self.assertEqual(invite_code.used_by.count(), 3)
        self.assertFalse(invite_code.is_usable)  # Max uses reached
        
        # Test that code cannot be used again
        new_user = User.objects.create_user(
            username='newuser',
            email='newuser@test.com',
            password='testpass123'
        )
        
        with self.assertRaises(ValueError):
            invite_code.use_code(new_user)
    
    def test_invite_code_expiration(self):
        """Test invite code expiration handling"""
        # Create expired invite code
        expired_code = InviteCode.objects.create(
            code='EXPIRED123',
            created_by=self.admin,
            task_group=TaskGroup.GENERAL,
            role=UserRole.STAFF,
            expires_at=timezone.now() - timedelta(days=1)
        )
        
        # Create expiring soon code
        expiring_code = InviteCode.objects.create(
            code='EXPIRING123',
            created_by=self.admin,
            task_group=TaskGroup.GENERAL,
            role=UserRole.STAFF,
            expires_at=timezone.now() + timedelta(hours=1)
        )
        
        # Create non-expiring code
        permanent_code = InviteCode.objects.create(
            code='PERMANENT123',
            created_by=self.admin,
            task_group=TaskGroup.GENERAL,
            role=UserRole.STAFF
        )
        
        # Test expiration properties
        self.assertTrue(expired_code.is_expired)
        self.assertFalse(expired_code.is_usable)
        
        self.assertFalse(expiring_code.is_expired)
        self.assertTrue(expiring_code.is_usable)
        
        self.assertFalse(permanent_code.is_expired)
        self.assertTrue(permanent_code.is_usable)
        
        # Test filtering by expiration status
        self.client.login(username='admin', password='testpass123')
        
        response = self.client.get('/admin/invite-codes/?status=expired')
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'EXPIRED123')
        self.assertNotContains(response, 'EXPIRING123')
        self.assertNotContains(response, 'PERMANENT123')
        
        response = self.client.get('/admin/invite-codes/?status=usable')
        self.assertEqual(response.status_code, 200)
        self.assertNotContains(response, 'EXPIRED123')
        self.assertContains(response, 'EXPIRING123')
        self.assertContains(response, 'PERMANENT123')


@pytest.mark.django_db
class InviteCodePerformanceTestCase(TestCase):
    """Performance tests for invite code management"""
    
    def setUp(self):
        """Set up test data"""
        self.admin = User.objects.create_user(
            username='admin',
            email='admin@test.com',
            password='testpass123',
            is_superuser=True
        )
        
        self.client = Client()
        self.client.login(username='admin', password='testpass123')
    
    def test_large_invite_code_list_performance(self):
        """Test performance with large number of invite codes"""
        # Create many invite codes
        for i in range(100):
            InviteCode.objects.create(
                code=f'PERF{i:03d}',
                created_by=self.admin,
                task_group=TaskGroup.GENERAL,
                role=UserRole.STAFF,
                notes=f'Performance test {i}'
            )
        
        # Test list view performance
        import time
        start_time = time.time()
        response = self.client.get('/admin/invite-codes/')
        end_time = time.time()
        
        self.assertEqual(response.status_code, 200)
        self.assertLess(end_time - start_time, 2.0)  # Should load within 2 seconds
        
        # Test filtering performance
        start_time = time.time()
        response = self.client.get('/admin/invite-codes/?role=staff')
        end_time = time.time()
        
        self.assertEqual(response.status_code, 200)
        self.assertLess(end_time - start_time, 1.0)  # Should filter within 1 second
        
        # Test search performance
        start_time = time.time()
        response = self.client.get('/admin/invite-codes/?search=PERF050')
        end_time = time.time()
        
        self.assertEqual(response.status_code, 200)
        self.assertLess(end_time - start_time, 1.0)  # Should search within 1 second
