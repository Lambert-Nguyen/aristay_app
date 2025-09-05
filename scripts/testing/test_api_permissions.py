#!/usr/bin/env python
"""
API permissions test runner
Run with: python scripts/test_api_permissions.py
"""

import os
import sys
import django
import requests
import json

# Add the backend directory to Python path
backend_dir = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 'aristay_backend')
sys.path.insert(0, backend_dir)

# Change to backend directory
os.chdir(backend_dir)

# Setup Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'backend.settings')
django.setup()

from django.contrib.auth.models import User
from rest_framework.authtoken.models import Token
from api.models import Profile, UserRole


def test_api_permissions():
    """Test API endpoints with dynamic permissions"""
    print("🌐 Testing API Endpoints with Dynamic Permissions")
    print("=" * 60)
    
    base_url = "http://localhost:8000"
    
    # Test 1: Unauthenticated access
    print("\n1. Testing unauthenticated access...")
    try:
        response = requests.get(f"{base_url}/api/tasks/", timeout=5)
        print(f"   GET /api/tasks/ (no auth): {response.status_code} {'✓' if response.status_code == 401 else '✗'}")
    except requests.exceptions.RequestException as e:
        print(f"   ✗ Connection error: {e}")
        print("   Make sure the Django server is running on localhost:8000")
        return
    
    # Test 2: Get teststaff user and token
    print("\n2. Getting teststaff user and token...")
    try:
        teststaff = User.objects.get(username='teststaff')
        token, created = Token.objects.get_or_create(user=teststaff)
        print(f"   Found user: {teststaff.username} (role: {teststaff.profile.role})")
        print(f"   Token: {token.key[:10]}...")
        
        headers = {
            'Authorization': f'Token {token.key}',
            'Content-Type': 'application/json'
        }
        
    except User.DoesNotExist:
        print("   ✗ teststaff user not found")
        return
    
    # Test 3: Test task endpoints with manager permissions
    print("\n3. Testing task endpoints with manager permissions...")
    
    # GET tasks (should work - manager has view_tasks)
    response = requests.get(f"{base_url}/api/tasks/", headers=headers, timeout=5)
    print(f"   GET /api/tasks/: {response.status_code} {'✓' if response.status_code == 200 else '✗'}")
    
    # POST task (should work - manager has add_tasks)
    task_data = {
        'title': 'Test Task from API',
        'description': 'Test Description',
        'status': 'pending'
    }
    response = requests.post(f"{base_url}/api/tasks/", headers=headers, json=task_data, timeout=5)
    print(f"   POST /api/tasks/: {response.status_code} {'✓' if response.status_code == 201 else '✗'}")
    
    if response.status_code == 201:
        task_id = response.json().get('id')
        print(f"   Created task ID: {task_id}")
        
        # PATCH task (should work - manager has change_tasks)
        update_data = {'title': 'Updated Task Title'}
        response = requests.patch(f"{base_url}/api/tasks/{task_id}/", headers=headers, json=update_data, timeout=5)
        print(f"   PATCH /api/tasks/{task_id}/: {response.status_code} {'✓' if response.status_code == 200 else '✗'}")
        
        # DELETE task (should fail - manager doesn't have delete_tasks)
        response = requests.delete(f"{base_url}/api/tasks/{task_id}/", headers=headers, timeout=5)
        print(f"   DELETE /api/tasks/{task_id}/: {response.status_code} {'✓' if response.status_code == 403 else '✗'} (expected 403)")
    
    # Test 4: Test property endpoints
    print("\n4. Testing property endpoints...")
    
    # GET properties (should work - manager has view_properties)
    response = requests.get(f"{base_url}/api/properties/", headers=headers, timeout=5)
    print(f"   GET /api/properties/: {response.status_code} {'✓' if response.status_code == 200 else '✗'}")
    
    # POST property (should work - manager has add_properties)
    property_data = {
        'name': 'Test Property from API',
        'address': '123 Test Street'
    }
    response = requests.post(f"{base_url}/api/properties/", headers=headers, json=property_data, timeout=5)
    print(f"   POST /api/properties/: {response.status_code} {'✓' if response.status_code == 201 else '✗'}")
    
    # Test 5: Test booking endpoints
    print("\n5. Testing booking endpoints...")
    
    # GET bookings (should work - manager has view_bookings)
    response = requests.get(f"{base_url}/api/bookings/", headers=headers, timeout=5)
    print(f"   GET /api/bookings/: {response.status_code} {'✓' if response.status_code == 200 else '✗'}")
    
    # Test 6: Test user endpoints
    print("\n6. Testing user endpoints...")
    
    # GET users (should work - manager has view_users)
    response = requests.get(f"{base_url}/api/users/", headers=headers, timeout=5)
    print(f"   GET /api/users/: {response.status_code} {'✓' if response.status_code == 200 else '✗'}")
    
    # Test 7: Test with a staff user (limited permissions)
    print("\n7. Testing with staff user (limited permissions)...")
    
    try:
        # Create a staff user for testing
        staff_user = User.objects.create_user(
            username='teststaff_limited',
            email='staff@test.com',
            password='testpass123'
        )
        Profile.objects.get_or_create(user=staff_user, defaults={'role': UserRole.STAFF})
        staff_token, created = Token.objects.get_or_create(user=staff_user)
        
        staff_headers = {
            'Authorization': f'Token {staff_token.key}',
            'Content-Type': 'application/json'
        }
        
        print(f"   Created staff user: {staff_user.username}")
        
        # GET tasks (should work - staff has view_tasks)
        response = requests.get(f"{base_url}/api/tasks/", headers=staff_headers, timeout=5)
        print(f"   Staff GET /api/tasks/: {response.status_code} {'✓' if response.status_code == 200 else '✗'}")
        
        # POST task (should work - staff has add_tasks)
        task_data = {
            'title': 'Staff Task',
            'description': 'Staff Description',
            'status': 'pending'
        }
        response = requests.post(f"{base_url}/api/tasks/", headers=staff_headers, json=task_data, timeout=5)
        print(f"   Staff POST /api/tasks/: {response.status_code} {'✓' if response.status_code == 201 else '✗'}")
        
        # PATCH task (should fail - staff doesn't have change_tasks)
        if response.status_code == 201:
            task_id = response.json().get('id')
            update_data = {'title': 'Updated by Staff'}
            response = requests.patch(f"{base_url}/api/tasks/{task_id}/", headers=staff_headers, json=update_data, timeout=5)
            print(f"   Staff PATCH /api/tasks/{task_id}/: {response.status_code} {'✓' if response.status_code == 403 else '✗'} (expected 403)")
        
        # Clean up
        staff_user.delete()
        print("   Cleaned up staff user")
        
    except Exception as e:
        print(f"   Error testing staff user: {e}")
    
    # Test 8: Test permission override
    print("\n8. Testing permission override...")
    
    try:
        from api.models import UserPermissionOverride, CustomPermission
        
        # Create a temporary override to deny view_tasks
        view_tasks_perm = CustomPermission.objects.get(name='view_tasks')
        override = UserPermissionOverride.objects.create(
            user=teststaff,
            permission=view_tasks_perm,
            granted=False,
            granted_by=teststaff,
            reason='Test API override',
            expires_at=None  # No expiration
        )
        
        print("   Created override to deny view_tasks")
        
        # GET tasks (should fail now)
        response = requests.get(f"{base_url}/api/tasks/", headers=headers, timeout=5)
        print(f"   GET /api/tasks/ with override: {response.status_code} {'✓' if response.status_code == 403 else '✗'} (expected 403)")
        
        # Clean up override
        override.delete()
        print("   Cleaned up override")
        
        # GET tasks (should work again)
        response = requests.get(f"{base_url}/api/tasks/", headers=headers, timeout=5)
        print(f"   GET /api/tasks/ after cleanup: {response.status_code} {'✓' if response.status_code == 200 else '✗'}")
        
    except Exception as e:
        print(f"   Error testing override: {e}")
    
    print("\n" + "=" * 60)
    print("✅ API permission testing completed!")


if __name__ == '__main__':
    test_api_permissions()
