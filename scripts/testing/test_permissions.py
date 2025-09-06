#!/usr/bin/env python
"""
Permission system test runner
Run with: python scripts/test_permissions.py
"""

import os
import sys
import django

from pathlib import Path
import pytest

# Robust path resolution
REPO_ROOT = Path(__file__).resolve().parents[2]
backend_dir = REPO_ROOT / "aristay_backend"

if not backend_dir.exists():
    pytest.skip("Backend dir not found; skipping script-based tests on this environment", allow_module_level=True)

# Add the backend directory to Python path
sys.path.insert(0, str(backend_dir))

# Change to backend directory
os.chdir(str(backend_dir))

# Setup Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'backend.settings')
django.setup()

from django.contrib.auth.models import User
from api.models import Profile, UserRole, CustomPermission, RolePermission, UserPermissionOverride
from api.permissions import HasCustomPermission, DynamicTaskPermissions
from django.utils import timezone
from datetime import timedelta


def test_permission_system():
    """Test the dynamic permission system"""
    print("🔐 Testing Dynamic Permission System")
    print("=" * 50)
    
    # Test 1: Check if permissions exist
    print("\n1. Checking if permissions exist...")
    permissions = CustomPermission.objects.all()
    print(f"   Found {permissions.count()} permissions")
    
    # Test 2: Check role permissions
    print("\n2. Checking role permissions...")
    for role in UserRole.choices:
        role_name = role[0]
        role_perms = RolePermission.objects.filter(role=role_name)
        print(f"   {role_name.upper()}: {role_perms.count()} permissions")
    
    # Test 3: Test with existing users
    print("\n3. Testing with existing users...")
    
    # Find teststaff user
    try:
        teststaff = User.objects.get(username='teststaff')
        profile = teststaff.profile
        print(f"   Found user: {teststaff.username} (role: {profile.role})")
        
        # Test some permissions
        test_permissions = ['view_tasks', 'add_tasks', 'change_tasks', 'delete_tasks', 'view_reports']
        for perm_name in test_permissions:
            has_perm = profile.has_permission(perm_name)
            print(f"   {perm_name}: {'✓' if has_perm else '✗'}")
            
    except User.DoesNotExist:
        print("   teststaff user not found")
    
    # Test 4: Test permission classes
    print("\n4. Testing permission classes...")
    
    # Create a mock request
    class MockRequest:
        def __init__(self, user, method='GET'):
            self.user = user
            self.method = method
    
    try:
        teststaff = User.objects.get(username='teststaff')
        
        # Test HasCustomPermission
        perm = HasCustomPermission('view_tasks')
        request = MockRequest(teststaff)
        result = perm.has_permission(request, None)
        print(f"   HasCustomPermission('view_tasks'): {'✓' if result else '✗'}")
        
        # Test DynamicTaskPermissions
        dynamic_perm = DynamicTaskPermissions()
        request = MockRequest(teststaff, 'GET')
        result = dynamic_perm.has_permission(request, None)
        print(f"   DynamicTaskPermissions GET: {'✓' if result else '✗'}")
        
        request = MockRequest(teststaff, 'POST')
        result = dynamic_perm.has_permission(request, None)
        print(f"   DynamicTaskPermissions POST: {'✓' if result else '✗'}")
        
    except User.DoesNotExist:
        print("   teststaff user not found for permission class tests")
    
    # Test 5: Test user permission overrides
    print("\n5. Testing user permission overrides...")
    
    try:
        teststaff = User.objects.get(username='teststaff')
        profile = teststaff.profile
        
        # Create a temporary override
        view_reports_perm = CustomPermission.objects.get(name='view_reports')
        
        # Check if user already has this permission
        has_reports = profile.has_permission('view_reports')
        print(f"   User has view_reports: {'✓' if has_reports else '✗'}")
        
        # Create an override to deny the permission
        override, created = UserPermissionOverride.objects.get_or_create(
            user=teststaff,
            permission=view_reports_perm,
            defaults={
                'granted': False,
                'granted_by': teststaff,
                'reason': 'Test override',
                'expires_at': timezone.now() + timedelta(hours=1)
            }
        )
        
        if created:
            print("   Created temporary override to deny view_reports")
            has_reports_after = profile.has_permission('view_reports')
            print(f"   User has view_reports after override: {'✓' if has_reports_after else '✗'}")
            
            # Clean up
            override.delete()
            print("   Cleaned up test override")
        else:
            print("   Override already exists")
            
    except User.DoesNotExist:
        print("   teststaff user not found for override tests")
    except CustomPermission.DoesNotExist:
        print("   view_reports permission not found")
    
    # Test 6: Test expired overrides
    print("\n6. Testing expired overrides...")
    
    try:
        teststaff = User.objects.get(username='teststaff')
        profile = teststaff.profile
        
        # Create an expired override
        view_tasks_perm = CustomPermission.objects.get(name='view_tasks')
        expired_override = UserPermissionOverride.objects.create(
            user=teststaff,
            permission=view_tasks_perm,
            granted=False,
            granted_by=teststaff,
            reason='Expired test override',
            expires_at=timezone.now() - timedelta(hours=1)  # Expired
        )
        
        print("   Created expired override")
        has_tasks = profile.has_permission('view_tasks')
        print(f"   User has view_tasks (should ignore expired override): {'✓' if has_tasks else '✗'}")
        
        # Clean up
        expired_override.delete()
        print("   Cleaned up expired override")
        
    except User.DoesNotExist:
        print("   teststaff user not found for expired override tests")
    except CustomPermission.DoesNotExist:
        print("   view_tasks permission not found")
    
    print("\n" + "=" * 50)
    print("✅ Permission system test completed!")


if __name__ == '__main__':
    test_permission_system()
