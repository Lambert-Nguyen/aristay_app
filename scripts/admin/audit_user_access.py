#!/usr/bin/env python
"""
Audit script to check for users who might be locked out after permission system changes.
This helps verify the decoupling didn't unintentionally block legitimate users.

Usage:
    python manage.py shell < audit_user_access.py
"""

import os
import django

# Setup Django environment
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'backend.settings')
django.setup()

from django.contrib.auth.models import User
from api.models import Profile

print("🔍 User Access Audit Report")
print("=" * 50)

# 1. Find users with unusual role states
print("\n1. Users with unusual role configurations:")
unusual_users = (User.objects
                .filter(is_superuser=False)
                .select_related('profile')
                .exclude(profile__role__in=['manager','staff','viewer']))

if unusual_users.exists():
    print("   ⚠️  Users with unexpected roles:")
    for user in unusual_users:
        profile_role = getattr(user.profile, 'role', 'NO_PROFILE') if hasattr(user, 'profile') else 'NO_PROFILE'
        print(f"      - {user.username} (is_staff={user.is_staff}, role={profile_role})")
else:
    print("   ✅ All users have valid roles")

# 2. Check managers who are NOT is_staff (should still work with new system)
print("\n2. Managers without is_staff flag:")
non_staff_managers = User.objects.filter(
    is_superuser=False, 
    is_staff=False, 
    profile__role='manager'
).select_related('profile')

print(f"   📊 Found {non_staff_managers.count()} managers without is_staff")
if non_staff_managers.exists():
    print("   ✅ These users should still have access via role-based permissions:")
    for user in non_staff_managers:
        print(f"      - {user.username}")

# 3. Check legacy is_staff users who are NOT managers
print("\n3. Legacy is_staff users (not managers):")
legacy_staff = User.objects.filter(
    is_superuser=False,
    is_staff=True
).exclude(profile__role='manager').select_related('profile')

print(f"   📊 Found {legacy_staff.count()} is_staff users who are not managers")
if legacy_staff.exists():
    print("   ℹ️  These users will access via legacy is_staff compatibility:")
    for user in legacy_staff:
        profile_role = getattr(user.profile, 'role', 'NO_PROFILE') if hasattr(user, 'profile') else 'NO_PROFILE'
        print(f"      - {user.username} (role={profile_role})")

# 4. Users without profiles
print("\n4. Users without profiles:")
no_profile_users = User.objects.filter(profile__isnull=True, is_superuser=False)

if no_profile_users.exists():
    print("   ⚠️  Users without profiles (may have limited access):")
    for user in no_profile_users:
        print(f"      - {user.username} (is_staff={user.is_staff})")
else:
    print("   ✅ All users have profiles")

# 5. Summary statistics
print("\n5. Access Summary:")
total_users = User.objects.filter(is_superuser=False).count()
superusers = User.objects.filter(is_superuser=True).count()
managers = User.objects.filter(profile__role='manager').count()
staff = User.objects.filter(profile__role='staff').count()
viewers = User.objects.filter(profile__role='viewer').count()

print(f"   📊 Total non-superusers: {total_users}")
print(f"   👑 Superusers: {superusers}")
print(f"   👔 Managers: {managers}")
print(f"   👷 Staff: {staff}")
print(f"   👀 Viewers: {viewers}")

# 6. Potential access issues
print("\n6. Potential Access Issues:")
issues = []

# Users with staff role but no department assignments
# Note: Skip department check if relationship doesn't exist or is complex
try:
    staff_no_dept = User.objects.filter(
        profile__role='staff',
        profile__department__isnull=True
    ).select_related('profile').count()
except:
    # If department field doesn't exist or relationship is different
    staff_no_dept = 0

if staff_no_dept > 0:
    issues.append(f"   ⚠️  {staff_no_dept} staff users have no department assignments")

# Users with viewer role (might have limited access)
viewer_count = User.objects.filter(profile__role='viewer').count()
if viewer_count > 0:
    issues.append(f"   ℹ️  {viewer_count} users have 'viewer' role (limited access by design)")

if not issues:
    print("   ✅ No obvious access issues detected")
else:
    for issue in issues:
        print(issue)

print("\n" + "=" * 50)
print("🎯 Recommendations:")
print("   1. Review users with unusual roles")
print("   2. Ensure staff users have appropriate department assignments")
print("   3. Test key user workflows after deployment")
print("   4. Monitor logs for access denied patterns")
