#!/usr/bin/env python
"""
Script to check and fix permissions in Heroku database
"""
import os
import django

# Setup Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'backend.settings')
django.setup()

from django.contrib.auth.models import User
from api.models import Profile, UserRole, CustomPermission, RolePermission

def check_and_fix_permissions():
    print("🔍 Checking permissions in Heroku database...")
    
    # Check if manager_portal_access permission exists
    try:
        perm = CustomPermission.objects.get(name='manager_portal_access')
        print(f'✅ Permission found: {perm.name}')
    except CustomPermission.DoesNotExist:
        print('❌ manager_portal_access permission not found')
        print('Creating permission...')
        perm = CustomPermission.objects.create(
            name='manager_portal_access',
            description='Manager Portal Access',
            is_active=True
        )
        print(f'✅ Created permission: {perm.name}')
    
    # Check if manager role has this permission
    try:
        role_perm = RolePermission.objects.get(role='manager', permission__name='manager_portal_access')
        print(f'✅ Role permission found: {role_perm.role} -> {role_perm.permission.name} = {role_perm.granted}')
    except RolePermission.DoesNotExist:
        print('❌ Role permission not found')
        print('Creating role permission...')
        role_perm = RolePermission.objects.create(
            role='manager',
            permission=perm,
            granted=True,
            can_delegate=False
        )
        print(f'✅ Created role permission: {role_perm.role} -> {role_perm.permission.name} = {role_perm.granted}')
    
    # Check testuser
    try:
        user = User.objects.get(username='testuser')
        profile = user.profile
        print(f'\\nUser: {user.username}')
        print(f'Profile role: {profile.role}')
        print(f'is_staff: {user.is_staff}')
        
        # Test permission
        has_perm = profile.has_permission('manager_portal_access')
        print(f'Has manager_portal_access: {has_perm}')
        
        # Test manager site permission
        from api.managersite import manager_site
        from django.test import RequestFactory
        
        factory = RequestFactory()
        request = factory.get('/manager/')
        request.user = user
        
        has_access = manager_site.has_permission(request)
        print(f'Manager site access: {has_access}')
        
    except User.DoesNotExist:
        print('❌ User testuser not found')
        print('Available users:')
        for user in User.objects.all():
            print(f'  - {user.username} (role: {getattr(user.profile, "role", "no profile")})')

if __name__ == '__main__':
    check_and_fix_permissions()
