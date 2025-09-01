#!/usr/bin/env python
"""
Test the manager dashboard endpoint with dynamic permissions
"""
import os
import sys
import django

sys.path.append('/Users/duylam1407/Workspace/SJSU/aristay_app/aristay_backend')
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'backend.settings')
django.setup()

from django.contrib.auth.models import User
from django.test import RequestFactory
from api.views import manager_overview
from api.permissions import CanViewAnalytics

def test_dashboard_access():
    """Test dashboard access with dynamic permissions"""
    print("=== Testing Manager Dashboard Access ===\n")
    
    # Get teststaff user
    user = User.objects.get(username='teststaff')
    print(f"👤 User: {user.username}")
    
    # Create mock request
    factory = RequestFactory()
    request = factory.get('/api/manager/dashboard/')
    request.user = user
    
    # Test the permission class directly
    permission = CanViewAnalytics()
    has_permission = permission.has_permission(request, None)
    print(f"🔑 CanViewAnalytics permission: {has_permission}")
    
    # Test the view directly
    try:
        response = manager_overview(request)
        print(f"✅ Dashboard access: SUCCESS")
        print(f"   Response status: {response.status_code}")
        
        # Check if response contains expected data
        if hasattr(response, 'data') and response.data:
            data = response.data
            print(f"   Contains tasks data: {'tasks' in data}")
            print(f"   Contains users data: {'users' in data}")
            
            if 'tasks' in data:
                print(f"   Total tasks: {data['tasks'].get('total', 'N/A')}")
            if 'users' in data:
                print(f"   Total users: {data['users'].get('total', 'N/A')}")
                
    except Exception as e:
        print(f"❌ Dashboard access failed: {e}")
    
    # Test with user without permission
    print(f"\n🚫 Testing with user without view_analytics permission...")
    try:
        # Find a user without analytics permission
        other_users = User.objects.exclude(username='teststaff').exclude(is_superuser=True)
        test_user = None
        
        for u in other_users:
            if hasattr(u, 'profile') and not u.profile.has_permission('view_analytics'):
                test_user = u
                break
        
        if test_user:
            request.user = test_user
            permission_result = permission.has_permission(request, None)
            print(f"   User {test_user.username} permission: {permission_result}")
        else:
            print("   No user without analytics permission found to test with")
            
    except Exception as e:
        print(f"   Error testing without permission: {e}")

if __name__ == "__main__":
    test_dashboard_access()
