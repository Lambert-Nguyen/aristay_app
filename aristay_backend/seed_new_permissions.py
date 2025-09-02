#!/usr/bin/env python
"""
Seed script to create the new permissions added to PERMISSION_CHOICES.
Run this after adding the new permissions to the model choices.

Usage:
    python manage.py shell < seed_new_permissions.py
    
Or in Django shell:
    exec(open('seed_new_permissions.py').read())
"""

import os
import django

# Setup Django environment
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'backend.settings')
django.setup()

from api.models import CustomPermission

# New permissions that were added to PERMISSION_CHOICES
new_permissions = [
    'manage_files',
    'manage_permissions', 
    'system_metrics_access',
    'system_recovery_access',
    'manage_bookings',
    # Additional permissions for inventory and system access
    'view_inventory',
    'change_inventory',
    'manage_inventory',
]

created_count = 0
existing_count = 0

for permission_name in new_permissions:
    permission_obj, created = CustomPermission.objects.get_or_create(name=permission_name)
    
    if created:
        created_count += 1
        print(f"✅ Created permission: {permission_name}")
    else:
        existing_count += 1
        print(f"📋 Permission already exists: {permission_name}")

print(f"\n🎉 Summary:")
print(f"   Created: {created_count} new permissions")
print(f"   Existing: {existing_count} permissions")
print(f"   Total: {len(new_permissions)} permissions processed")

# Verify all permissions exist
print(f"\n🔍 Verification:")
all_new_perms = CustomPermission.objects.filter(name__in=new_permissions)
print(f"   Database has {all_new_perms.count()}/{len(new_permissions)} of the new permissions")

if all_new_perms.count() == len(new_permissions):
    print("✅ All new permissions successfully created/verified!")
else:
    missing = set(new_permissions) - set(all_new_perms.values_list('name', flat=True))
    print(f"❌ Missing permissions: {missing}")
