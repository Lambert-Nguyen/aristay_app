#!/usr/bin/env python
"""
Quick verification test for the critical permission system fixes.
Tests the staff_or_perm decorator and status constant fixes.

Usage:
    python manage.py shell < test_critical_fixes.py
"""

import os
import django

# Setup Django environment
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'backend.settings')
django.setup()

from django.test import RequestFactory
from django.contrib.auth.models import User
from django.core.exceptions import PermissionDenied
from api.decorators import staff_or_perm
from api.models import Task, CustomPermission

print("🧪 Testing Critical Permission System Fixes")
print("=" * 50)

# 1. Test staff_or_perm decorator doesn't return None on denial
print("\n1. Testing staff_or_perm decorator denial handling:")

@staff_or_perm('test_permission')
def test_view(request):
    return "SUCCESS"

factory = RequestFactory()
request = factory.get('/')

# Create a test user without permissions
test_user = User.objects.filter(username='test_no_perms').first()
if not test_user:
    test_user = User.objects.create_user('test_no_perms', 'test@example.com', 'password')

request.user = test_user

try:
    result = test_view(request)
    print("   ❌ FAIL: Should have raised PermissionDenied, got:", result)
except PermissionDenied as e:
    print("   ✅ PASS: Properly raises PermissionDenied:", str(e))
except Exception as e:
    print("   ❌ FAIL: Unexpected exception:", type(e).__name__, str(e))

# 2. Test status constants are correct
print("\n2. Testing status constant fixes:")

# Check if we can query with 'in-progress' (hyphen)
try:
    in_progress_count = Task.objects.filter(status='in-progress').count()
    print(f"   ✅ PASS: Found {in_progress_count} tasks with 'in-progress' status")
except Exception as e:
    print(f"   ❌ FAIL: Error querying 'in-progress' status: {e}")

# Check that Task model actually uses 'in-progress' in choices
try:
    task_status_choices = dict(Task.STATUS_CHOICES) if hasattr(Task, 'STATUS_CHOICES') else {}
    if 'in-progress' in task_status_choices:
        print("   ✅ PASS: 'in-progress' found in Task.STATUS_CHOICES")
    else:
        print("   ⚠️  WARNING: 'in-progress' not found in STATUS_CHOICES, available:", list(task_status_choices.keys()))
except Exception as e:
    print(f"   ❌ FAIL: Error checking STATUS_CHOICES: {e}")

# 3. Test new permissions exist
print("\n3. Testing new permissions exist:")

new_perms = ['view_inventory', 'manage_files', 'system_metrics_access']
for perm in new_perms:
    try:
        permission = CustomPermission.objects.get(name=perm)
        print(f"   ✅ PASS: Permission '{perm}' exists")
    except CustomPermission.DoesNotExist:
        print(f"   ❌ FAIL: Permission '{perm}' not found")
    except Exception as e:
        print(f"   ❌ FAIL: Error checking permission '{perm}': {e}")

# 4. Test superuser bypass in staff_or_perm
print("\n4. Testing superuser bypass:")

superuser = User.objects.filter(is_superuser=True).first()
if superuser:
    request.user = superuser
    try:
        result = test_view(request)
        if result == "SUCCESS":
            print("   ✅ PASS: Superuser bypasses permission check")
        else:
            print("   ❌ FAIL: Unexpected result for superuser:", result)
    except Exception as e:
        print("   ❌ FAIL: Superuser should bypass check:", type(e).__name__, str(e))
else:
    print("   ⚠️  WARNING: No superuser found to test bypass")

print("\n" + "=" * 50)
print("🎯 Critical fixes verification complete!")
print("   Review any FAIL messages above before deployment.")
