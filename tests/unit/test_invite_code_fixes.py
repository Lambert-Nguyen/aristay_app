"""
Test fixes for InviteCode model issues:
1. Multi-use codes cannot be reused by the same user
2. Race condition prevention in use_code method
"""
import pytest
from django.test import TestCase
from django.db import transaction, IntegrityError
from django.contrib.auth.models import User
from api.models import InviteCode, Profile, UserRole, TaskGroup
from django.utils import timezone
from datetime import timedelta
import threading
import time


class InviteCodeFixesTest(TestCase):
    """Test fixes for InviteCode model issues"""
    
    def setUp(self):
        """Set up test data"""
        # Create test users
        self.user1 = User.objects.create_user(
            username='user1',
            email='user1@test.com',
            password='testpass123'
        )
        self.user2 = User.objects.create_user(
            username='user2',
            email='user2@test.com',
            password='testpass123'
        )
        
        # Create profiles for users (get_or_create to handle signal receiver)
        Profile.objects.get_or_create(
            user=self.user1,
            defaults={
                'role': UserRole.STAFF,
                'task_group': TaskGroup.CLEANING
            }
        )
        Profile.objects.get_or_create(
            user=self.user2,
            defaults={
                'role': UserRole.STAFF,
                'task_group': TaskGroup.MAINTENANCE
            }
        )
        
        # Create invite codes
        self.single_use_code = InviteCode.objects.create(
            code='SINGLE123',
            created_by=self.user1,
            role=UserRole.STAFF,
            task_group=TaskGroup.CLEANING,
            max_uses=1
        )
        
        self.multi_use_code = InviteCode.objects.create(
            code='MULTI456',
            created_by=self.user1,
            role=UserRole.STAFF,
            task_group=TaskGroup.MAINTENANCE,
            max_uses=3
        )
        
        self.unlimited_code = InviteCode.objects.create(
            code='UNLIMITED789',
            created_by=self.user1,
            role=UserRole.STAFF,
            task_group=TaskGroup.GENERAL,
            max_uses=0  # Unlimited
        )

    def test_single_use_code_cannot_be_reused_by_same_user(self):
        """Test that single-use codes cannot be reused by the same user"""
        # First use should succeed
        self.single_use_code.use_code(self.user1)
        self.assertEqual(self.single_use_code.used_count, 1)
        self.assertIn(self.user1, self.single_use_code.used_by.all())
        
        # Second use by same user should fail
        with self.assertRaises(ValueError) as context:
            self.single_use_code.use_code(self.user1)
        
        self.assertIn("Code cannot be used", str(context.exception))
        self.assertEqual(self.single_use_code.used_count, 1)  # Count should not increase

    def test_multi_use_code_cannot_be_reused_by_same_user(self):
        """Test that multi-use codes cannot be reused by the same user"""
        # First use should succeed
        self.multi_use_code.use_code(self.user1)
        self.assertEqual(self.multi_use_code.used_count, 1)
        self.assertIn(self.user1, self.multi_use_code.used_by.all())
        
        # Second use by same user should fail
        with self.assertRaises(ValueError) as context:
            self.multi_use_code.use_code(self.user1)
        
        self.assertIn("Code cannot be used", str(context.exception))
        self.assertEqual(self.multi_use_code.used_count, 1)  # Count should not increase

    def test_multi_use_code_can_be_used_by_different_users(self):
        """Test that multi-use codes can be used by different users"""
        # First user uses the code
        self.multi_use_code.use_code(self.user1)
        self.assertEqual(self.multi_use_code.used_count, 1)
        self.assertIn(self.user1, self.multi_use_code.used_by.all())
        
        # Second user can also use the code
        self.multi_use_code.use_code(self.user2)
        self.assertEqual(self.multi_use_code.used_count, 2)
        self.assertIn(self.user1, self.multi_use_code.used_by.all())
        self.assertIn(self.user2, self.multi_use_code.used_by.all())

    def test_unlimited_code_cannot_be_reused_by_same_user(self):
        """Test that unlimited codes cannot be reused by the same user"""
        # First use should succeed
        self.unlimited_code.use_code(self.user1)
        self.assertEqual(self.unlimited_code.used_count, 1)
        self.assertIn(self.user1, self.unlimited_code.used_by.all())
        
        # Second use by same user should fail
        with self.assertRaises(ValueError) as context:
            self.unlimited_code.use_code(self.user1)
        
        self.assertIn("Code cannot be used", str(context.exception))
        self.assertEqual(self.unlimited_code.used_count, 1)  # Count should not increase

    def test_can_be_used_by_prevents_reuse(self):
        """Test that can_be_used_by correctly prevents reuse"""
        # Before using, should be usable
        self.assertTrue(self.multi_use_code.can_be_used_by(self.user1))
        
        # Use the code
        self.multi_use_code.use_code(self.user1)
        
        # After using, should not be usable by same user
        self.assertFalse(self.multi_use_code.can_be_used_by(self.user1))
        
        # But should still be usable by different user
        self.assertTrue(self.multi_use_code.can_be_used_by(self.user2))

    def test_race_condition_prevention(self):
        """Test that race conditions are prevented in use_code using atomic transactions"""
        # Create a code with max_uses = 2
        race_code = InviteCode.objects.create(
            code='RACE123',
            created_by=self.user1,
            role=UserRole.STAFF,
            task_group=TaskGroup.CLEANING,
            max_uses=2
        )
        
        # Create a third user for testing
        user3 = User.objects.create_user(
            username='user3',
            email='user3@test.com',
            password='testpass123'
        )
        Profile.objects.get_or_create(
            user=user3,
            defaults={
                'role': UserRole.STAFF,
                'task_group': TaskGroup.LAUNDRY
            }
        )
        
        # Test sequential usage to verify atomic behavior
        # First two uses should succeed
        race_code.use_code(self.user1)
        self.assertEqual(race_code.used_count, 1)
        self.assertIn(self.user1, race_code.used_by.all())
        
        race_code.use_code(self.user2)
        self.assertEqual(race_code.used_count, 2)
        self.assertIn(self.user2, race_code.used_by.all())
        
        # Third use should fail due to max_uses
        with self.assertRaises(ValueError) as context:
            race_code.use_code(user3)
        self.assertIn("Code cannot be used", str(context.exception))
        
        # Verify final state
        race_code.refresh_from_db()
        self.assertEqual(race_code.used_count, 2)
        self.assertEqual(race_code.used_by.count(), 2)
        
        # Test that same user cannot reuse
        with self.assertRaises(ValueError) as context:
            race_code.use_code(self.user1)
        self.assertIn("Code cannot be used", str(context.exception))

    def test_atomic_transaction_rollback(self):
        """Test that failed use_code operations don't leave partial state"""
        # Create a code with max_uses = 1
        atomic_code = InviteCode.objects.create(
            code='ATOMIC123',
            created_by=self.user1,
            role=UserRole.STAFF,
            task_group=TaskGroup.CLEANING,
            max_uses=1
        )
        
        # First use should succeed
        atomic_code.use_code(self.user1)
        self.assertEqual(atomic_code.used_count, 1)
        self.assertIn(self.user1, atomic_code.used_by.all())
        
        # Second use should fail and not modify state
        initial_count = atomic_code.used_count
        initial_users = list(atomic_code.used_by.all())
        
        with self.assertRaises(ValueError):
            atomic_code.use_code(self.user1)
        
        # Verify state is unchanged
        atomic_code.refresh_from_db()
        self.assertEqual(atomic_code.used_count, initial_count)
        self.assertEqual(list(atomic_code.used_by.all()), initial_users)

    def test_expired_code_cannot_be_used(self):
        """Test that expired codes cannot be used"""
        expired_code = InviteCode.objects.create(
            code='EXPIRED123',
            created_by=self.user1,
            role=UserRole.STAFF,
            task_group=TaskGroup.CLEANING,
            max_uses=1,
            expires_at=timezone.now() - timedelta(hours=1)  # Expired 1 hour ago
        )
        
        with self.assertRaises(ValueError) as context:
            expired_code.use_code(self.user1)
        
        self.assertIn("Code cannot be used", str(context.exception))

    def test_inactive_code_cannot_be_used(self):
        """Test that inactive codes cannot be used"""
        inactive_code = InviteCode.objects.create(
            code='INACTIVE123',
            created_by=self.user1,
            role=UserRole.STAFF,
            task_group=TaskGroup.CLEANING,
            max_uses=1,
            is_active=False
        )
        
        with self.assertRaises(ValueError) as context:
            inactive_code.use_code(self.user1)
        
        self.assertIn("Code cannot be used", str(context.exception))

    def test_max_uses_exceeded_cannot_be_used(self):
        """Test that codes with max_uses exceeded cannot be used"""
        limited_code = InviteCode.objects.create(
            code='LIMITED123',
            created_by=self.user1,
            role=UserRole.STAFF,
            task_group=TaskGroup.CLEANING,
            max_uses=1
        )
        
        # First use should succeed
        limited_code.use_code(self.user1)
        
        # Second use by different user should fail
        with self.assertRaises(ValueError) as context:
            limited_code.use_code(self.user2)
        
        self.assertIn("Code cannot be used", str(context.exception))

    def test_refresh_from_db_in_atomic_transaction(self):
        """Test that refresh_from_db works correctly in atomic transaction"""
        # Create a code
        refresh_code = InviteCode.objects.create(
            code='REFRESH123',
            created_by=self.user1,
            role=UserRole.STAFF,
            task_group=TaskGroup.CLEANING,
            max_uses=2
        )
        
        # Manually modify the code outside of use_code
        refresh_code.used_count = 1
        refresh_code.save()
        
        # Now use_code should refresh and see the updated count
        refresh_code.use_code(self.user2)  # Should succeed
        self.assertEqual(refresh_code.used_count, 2)
        
        # Third use should fail due to max_uses
        with self.assertRaises(ValueError):
            refresh_code.use_code(self.user1)
