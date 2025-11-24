#!/usr/bin/env python
"""
Test dynamic permission revocation and granting for manager portal
"""
import os
import sys
import django

# Add backend to path using relative path
from pathlib import Path
PROJECT_ROOT = Path(__file__).resolve().parent
while not (PROJECT_ROOT / 'aristay_backend').exists() and PROJECT_ROOT.parent != PROJECT_ROOT:
    PROJECT_ROOT = PROJECT_ROOT.parent
BACKEND_DIR = PROJECT_ROOT / 'aristay_backend'
if str(BACKEND_DIR) not in sys.path:
    sys.path.insert(0, str(BACKEND_DIR))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'backend.settings')
django.setup()

from django.contrib.auth.models import User
from django.test import RequestFactory
from api.managersite import manager_site
from api.models import CustomPermission, UserPermissionOverride

def test_dynamic_permission_changes(teststaff_user):
    """Test that permission changes are immediately reflected"""
    print("=== Testing Dynamic Permission Changes ===\n")
    
    # Create the required permission if it doesn't exist
    portal_perm, created = CustomPermission.objects.get_or_create(
        name='manager_portal_access',
        defaults={'description': 'Access to manager portal'}
    )
    if created:
        print("📝 Created manager_portal_access permission")
    
    # Use teststaff user from fixture
    user = teststaff_user
    print(f"👤 User: {user.username}")
    
    # Create mock request
    factory = RequestFactory()
    request = factory.get('/manager/')
    request.user = user
    
    # Test 1: Current access (should be True)
    current_access = manager_site.has_permission(request)
    print(f"🔓 Current Manager Portal Access: {current_access}")
    
    # Test 2: Revoke manager_portal_access permission
    print(f"\n🚫 Revoking manager_portal_access permission...")
    override, created = UserPermissionOverride.objects.get_or_create(
        user=user,
        permission=portal_perm,
        defaults={'granted': False}
    )
    if not created:
        override.granted = False
        override.save()
    
    # Test access after revocation
    revoked_access = manager_site.has_permission(request)
    print(f"🔒 Access after revocation: {revoked_access}")
    
    # Test 3: Re-grant permission
    print(f"\n✅ Re-granting manager_portal_access permission...")
    override.granted = True
    override.save()
    
    # Test access after re-granting
    restored_access = manager_site.has_permission(request)
    print(f"🔓 Access after re-granting: {restored_access}")
    
    # Test 4: Test with a different user (should not have access)
    print(f"\n👤 Testing with different user...")
    try:
        other_user = User.objects.exclude(username='teststaff').first()
        if other_user:
            request.user = other_user
            other_access = manager_site.has_permission(request)
            print(f"🔒 {other_user.username} access: {other_access}")
        else:
            print("No other users found to test with")
    except Exception as e:
        print(f"Could not test other user: {e}")
    
    print(f"\n🎯 Summary:")
    print(f"   Original access: {current_access}")
    print(f"   After revocation: {revoked_access}")
    print(f"   After re-granting: {restored_access}")
    print(f"   Dynamic permissions: {'✅ WORKING' if current_access != revoked_access else '❌ NOT WORKING'}")

if __name__ == "__main__":
    test_dynamic_permission_changes()
