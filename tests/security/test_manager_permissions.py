#!/usr/bin/env python
"""
Test the dynamic manager portal permissions for teststaff user
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
from api.models import Task, Booking

def test_manager_portal_access():
    """Test manager portal access for teststaff"""
    print("=== Testing Manager Portal Access for teststaff ===\n")
    
    # Get teststaff user
    try:
        user = User.objects.get(username='teststaff')
        print(f"✅ Found user: {user.username}")
        print(f"   Role: {user.profile.role}")
    except User.DoesNotExist:
        print("❌ teststaff user not found")
        return
    
    # Create mock request
    factory = RequestFactory()
    request = factory.get('/manager/')
    request.user = user
    
    # Test manager site access
    has_site_access = manager_site.has_permission(request)
    print(f"\n🏛️  Manager Site Access: {has_site_access}")
    
    # Test specific permissions
    permissions_to_test = [
        'manager_portal_access',
        'view_tasks',
        'add_tasks', 
        'change_tasks',
        'delete_tasks',
        'view_bookings',
        'add_bookings',
        'change_bookings',
        'delete_bookings'
    ]
    
    print(f"\n🔑 Permission Details:")
    for perm in permissions_to_test:
        has_perm = user.profile.has_permission(perm)
        status = "✅" if has_perm else "❌"
        print(f"   {status} {perm}: {has_perm}")
    
    # Test Task admin permissions
    from api.managersite import TaskAdmin
    task_admin = TaskAdmin(Task, manager_site)
    
    print(f"\n📋 Task Admin Permissions:")
    print(f"   📖 has_view_permission: {task_admin.has_view_permission(request)}")
    print(f"   ➕ has_add_permission: {task_admin.has_add_permission(request)}")
    print(f"   ✏️  has_change_permission: {task_admin.has_change_permission(request)}")
    print(f"   🗑️  has_delete_permission: {task_admin.has_delete_permission(request)}")
    
    # Test Booking admin permissions
    from api.managersite import BookingAdmin
    booking_admin = BookingAdmin(Booking, manager_site)
    
    print(f"\n🏨 Booking Admin Permissions:")
    print(f"   📖 has_view_permission: {booking_admin.has_view_permission(request)}")
    print(f"   ➕ has_add_permission: {booking_admin.has_add_permission(request)}")
    print(f"   ✏️  has_change_permission: {booking_admin.has_change_permission(request)}")
    print(f"   🗑️  has_delete_permission: {booking_admin.has_delete_permission(request)}")
    
    # Test URLs that should be accessible
    test_urls = [
        '/manager/',
        '/manager/api/task/',
        '/manager/api/booking/',
    ]
    
    print(f"\n🌐 URL Access Test:")
    for url in test_urls:
        mock_request = factory.get(url)
        mock_request.user = user
        site_access = manager_site.has_permission(mock_request)
        status = "✅" if site_access else "❌"
        print(f"   {status} {url}: {site_access}")

if __name__ == "__main__":
    test_manager_portal_access()
