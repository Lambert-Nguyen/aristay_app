#!/usr/bin/env python
"""
Grant manager portal access to teststaff user
"""
import os
import sys
import django

sys.path.append('/Users/duylam1407/Workspace/SJSU/aristay_app/aristay_backend')
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'backend.settings')
django.setup()

from django.contrib.auth.models import User
from api.models import CustomPermission, UserPermissionOverride

def grant_manager_portal_access():
    """Grant manager portal access to teststaff"""
    try:
        # Get teststaff user
        user = User.objects.get(username='teststaff')
        print(f"Found user: {user.username}")
        
        # Get manager portal permission
        permission = CustomPermission.objects.get(name='manager_portal_access')
        print(f"Found permission: {permission.get_name_display()}")
        
        # Get the superuser to grant the permission
        granter = User.objects.filter(is_superuser=True).first()
        
        # Grant the permission
        override, created = UserPermissionOverride.objects.get_or_create(
            user=user,
            permission=permission,
            defaults={
                'granted': True,
                'granted_by': granter,
                'reason': 'Manager portal access for testing dynamic permissions'
            }
        )
        
        if created:
            print(f"✅ Granted {permission.get_name_display()} to {user.username}")
        else:
            override.granted = True
            override.reason = 'Manager portal access for testing dynamic permissions'
            override.save()
            print(f"✅ Updated {permission.get_name_display()} for {user.username}")
            
    except User.DoesNotExist:
        print("❌ teststaff user not found")
    except CustomPermission.DoesNotExist:
        print("❌ manager_portal_access permission not found")

if __name__ == "__main__":
    grant_manager_portal_access()
