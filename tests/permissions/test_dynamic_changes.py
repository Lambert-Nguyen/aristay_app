#!/usr/bin/env python
"""
Test dynamic permission revocation and granting for manager portal
"""
import os
import sys
import django

sys.path.append('/Users/duylam1407/Workspace/SJSU/aristay_app/aristay_backend')
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'backend.settings')
django.setup()

from django.contrib.auth.models import User
from django.test import RequestFactory
from api.managersite import manager_site
from api.models import CustomPermission, UserPermissionOverride

def test_dynamic_permission_changes():
    """Test that permission changes are immediately reflected"""
    print("=== Testing Dynamic Permission Changes ===\n")
    
    # Get teststaff user
    user = User.objects.get(username='teststaff')
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
    portal_perm = CustomPermission.objects.get(name='manager_portal_access')
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
