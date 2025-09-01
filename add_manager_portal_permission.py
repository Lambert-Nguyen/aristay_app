#!/usr/bin/env python
"""
Add manager_portal_access permission to the system
"""
import os
import sys
import django

sys.path.append('/Users/duylam1407/Workspace/SJSU/aristay_app/aristay_backend')
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'backend.settings')
django.setup()

from api.models import CustomPermission

def add_manager_portal_permission():
    """Add manager_portal_access permission"""
    permission, created = CustomPermission.objects.get_or_create(
        name='manager_portal_access',
        defaults={
            'description': 'Access to the manager portal interface',
            'is_active': True
        }
    )
    
    if created:
        print(f"✅ Created permission: {permission.get_name_display()}")
    else:
        print(f"⚠️  Permission already exists: {permission.get_name_display()}")
    
    return permission

if __name__ == "__main__":
    add_manager_portal_permission()
