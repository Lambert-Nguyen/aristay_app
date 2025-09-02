#!/usr/bin/env python
"""
Debug script to test dynamic permissions for the teststaff user
"""
import os
import sys
import django
from datetime import datetime

# Add the project directory to the Python path
sys.path.append('/Users/duylam1407/Workspace/SJSU/aristay_app/aristay_backend')

# Setup Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'backend.settings')
django.setup()

from django.contrib.auth.models import User
from api.models import Profile, UserRole, CustomPermission, UserPermissionOverride
from api.permissions import DynamicBookingPermissions

def debug_permissions():
    """Debug the permission system for teststaff user"""
    print("=== Permission Debugging for teststaff ===\n")
    
    # Find the teststaff user
    try:
        user = User.objects.get(username='teststaff')
        print(f"✅ Found user: {user.username}")
        print(f"   - Email: {user.email}")
        print(f"   - Is superuser: {user.is_superuser}")
        print(f"   - Is staff: {user.is_staff}")
        print(f"   - Is active: {user.is_active}")
    except User.DoesNotExist:
        print("❌ User 'teststaff' not found")
        return
    
    # Check user profile
    if hasattr(user, 'profile') and user.profile:
        profile = user.profile
        print(f"\n✅ User profile found:")
        print(f"   - Role: {profile.role}")
        print(f"   - Role display: {profile.get_role_display()}")
    else:
        print("\n❌ User profile not found")
        return
    
    # Check specific permission: view_bookings
    permission_name = 'view_bookings'
    has_permission = profile.has_permission(permission_name)
    print(f"\n🔑 Permission check for '{permission_name}': {has_permission}")
    
    # Check if permission exists
    try:
        perm_obj = CustomPermission.objects.get(name=permission_name, is_active=True)
        print(f"   ✅ Permission object exists: {perm_obj.get_name_display()}")
    except CustomPermission.DoesNotExist:
        print(f"   ❌ Permission '{permission_name}' not found or inactive")
        return
    
    # Check role-based permission
    from api.models import RolePermission
    try:
        role_perm = RolePermission.objects.get(
            role=profile.role,
            permission__name=permission_name,
            permission__is_active=True
        )
        print(f"   📋 Role permission: granted={role_perm.granted}, can_delegate={role_perm.can_delegate}")
    except RolePermission.DoesNotExist:
        print(f"   📋 No role permission found for {profile.role} -> {permission_name}")
    
    # Check user-specific overrides
    try:
        override = user.permission_overrides.get(
            permission__name=permission_name,
            permission__is_active=True
        )
        print(f"   🔄 Permission override found:")
        print(f"      - Granted: {override.granted}")
        print(f"      - Granted by: {override.granted_by}")
        print(f"      - Reason: {override.reason}")
        print(f"      - Expires at: {override.expires_at}")
        print(f"      - Created at: {override.created_at}")
        
        # Check if expired
        from django.utils import timezone
        if override.expires_at and timezone.now() > override.expires_at:
            print(f"      ⚠️  EXPIRED: Override has expired!")
        
    except UserPermissionOverride.DoesNotExist:
        print(f"   🔄 No permission override found")
    
    # Test DynamicBookingPermissions class
    print(f"\n🏗️  Testing DynamicBookingPermissions class:")
    try:
        perm_class = DynamicBookingPermissions()
        print(f"   ✅ Class instantiated successfully")
        print(f"   📋 Permission map: {perm_class.permission_map}")
        
        # Create a mock request
        class MockRequest:
            def __init__(self, user, method='GET'):
                self.user = user
                self.method = method
        
        mock_request = MockRequest(user, 'GET')
        has_perm = perm_class.has_permission(mock_request, None)
        print(f"   🔑 has_permission() result: {has_perm}")
        
    except Exception as e:
        print(f"   ❌ Error testing permission class: {e}")
    
    # List all user's permissions
    print(f"\n📜 All permissions for user:")
    all_perms = profile.get_all_permissions()
    for perm_name, granted in all_perms.items():
        status = "✅" if granted else "❌"
        print(f"   {status} {perm_name}")

if __name__ == "__main__":
    debug_permissions()
