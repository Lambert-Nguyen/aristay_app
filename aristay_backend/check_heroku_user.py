#!/usr/bin/env python
"""
Script to check and fix testuser in Heroku database
"""
import os
import django

# Setup Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'backend.settings')
django.setup()

from django.contrib.auth.models import User
from api.models import Profile, UserRole

def check_and_fix_testuser():
    print("🔍 Checking testuser in Heroku database...")
    
    try:
        # Check if testuser exists
        user = User.objects.get(username='testuser')
        print(f'✅ User found: {user.username}')
        
        # Check if user has profile
        try:
            profile = user.profile
            print(f'✅ Profile found: role={profile.role}')
        except:
            print('❌ No profile found')
            return
        
        # Check current permissions
        has_perm = profile.has_permission('manager_portal_access')
        print(f'Current manager_portal_access: {has_perm}')
        
        # Check if role needs to be updated
        if profile.role != UserRole.MANAGER:
            print(f'🔄 Updating role from {profile.role} to manager...')
            profile.role = UserRole.MANAGER
            profile.save()
            print(f'✅ Updated role to: {profile.role}')
        else:
            print(f'✅ Role already correct: {profile.role}')
        
        # Check if is_staff needs to be updated
        should_have_staff_access = profile.role in [UserRole.MANAGER, UserRole.SUPERUSER]
        if user.is_staff != should_have_staff_access:
            print(f'🔄 Updating is_staff from {user.is_staff} to {should_have_staff_access}...')
            user.is_staff = should_have_staff_access
            user.save(update_fields=['is_staff'])
            print(f'✅ Updated is_staff to: {user.is_staff}')
        else:
            print(f'✅ is_staff already correct: {user.is_staff}')
        
        # Final verification
        has_perm = profile.has_permission('manager_portal_access')
        print(f'✅ Final manager_portal_access: {has_perm}')
        
        # Test manager site permission
        from api.managersite import manager_site
        from django.test import RequestFactory
        
        factory = RequestFactory()
        request = factory.get('/manager/')
        request.user = user
        
        has_access = manager_site.has_permission(request)
        print(f'✅ Manager site access: {has_access}')
        
    except User.DoesNotExist:
        print('❌ User testuser not found in Heroku database')
        print('Available users:')
        for user in User.objects.all():
            print(f'  - {user.username} (role: {getattr(user.profile, "role", "no profile")})')

if __name__ == '__main__':
    check_and_fix_testuser()
