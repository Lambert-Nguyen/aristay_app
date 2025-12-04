#!/usr/bin/env python
"""
Test script for CRUD operations in staff tasks portal.
This script tests the new CRUD functionality without requiring a full test suite.
"""

import os
import sys
import django
from django.test import TestCase, Client
from django.contrib.auth.models import User
from django.urls import reverse

# Add the backend directory to Python path
# Add backend to path using relative path
from pathlib import Path
PROJECT_ROOT = Path(__file__).resolve().parent
while not (PROJECT_ROOT / 'aristay_backend').exists() and PROJECT_ROOT.parent != PROJECT_ROOT:
    PROJECT_ROOT = PROJECT_ROOT.parent
BACKEND_DIR = PROJECT_ROOT / 'aristay_backend'
if str(BACKEND_DIR) not in sys.path:
    sys.path.insert(0, str(BACKEND_DIR))

# Set up Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'backend.settings')
django.setup()

from api.models import Task, Property, Profile

def test_crud_operations():
    """Test all CRUD operations for tasks."""
    print("🧪 Testing CRUD Operations for Staff Tasks Portal")
    print("=" * 60)
    
    # Create test client
    client = Client()
    
    # Create test user and profile
    try:
        user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='testpass123'
        )
        
        profile = Profile.objects.create(
            user=user,
            role='manager',
            timezone='America/New_York'
        )
        
        print("✅ Created test user and profile")
    except Exception as e:
        print(f"❌ Error creating user: {e}")
        return False
    
    # Create test property
    try:
        property_obj = Property.objects.create(
            name='Test Property',
            address='123 Test St',
            city='Test City',
            state='FL',
            zip_code='12345'
        )
        print("✅ Created test property")
    except Exception as e:
        print(f"❌ Error creating property: {e}")
        return False
    
    # Test 1: Login
    try:
        login_success = client.login(username='testuser', password='testpass123')
        if login_success:
            print("✅ User login successful")
        else:
            print("❌ User login failed")
            return False
    except Exception as e:
        print(f"❌ Login error: {e}")
        return False
    
    # Test 2: Access tasks list
    try:
        response = client.get('/api/staff/tasks/')
        if response.status_code == 200:
            print("✅ Tasks list accessible")
        else:
            print(f"❌ Tasks list failed: {response.status_code}")
            return False
    except Exception as e:
        print(f"❌ Tasks list error: {e}")
        return False
    
    # Test 3: Access task creation form
    try:
        response = client.get('/api/staff/tasks/create/')
        if response.status_code == 200:
            print("✅ Task creation form accessible")
        else:
            print(f"❌ Task creation form failed: {response.status_code}")
            return False
    except Exception as e:
        print(f"❌ Task creation form error: {e}")
        return False
    
    # Test 4: Create a task
    try:
        task_data = {
            'title': 'Test Task',
            'description': 'This is a test task',
            'task_type': 'cleaning',
            'status': 'pending',
            'assigned_to': user.id,
            'property_ref': property_obj.id,
            'due_date': '2024-12-31T09:00'
        }
        
        response = client.post('/api/staff/tasks/create/', task_data)
        if response.status_code == 302:  # Redirect after successful creation
            print("✅ Task creation successful")
            
            # Get the created task
            task = Task.objects.filter(title='Test Task').first()
            if task:
                print(f"✅ Task created with ID: {task.id}")
            else:
                print("❌ Task not found after creation")
                return False
        else:
            print(f"❌ Task creation failed: {response.status_code}")
            print(f"Response content: {response.content.decode()[:500]}")
            return False
    except Exception as e:
        print(f"❌ Task creation error: {e}")
        return False
    
    # Test 5: Access task detail
    try:
        response = client.get(f'/api/staff/tasks/{task.id}/')
        if response.status_code == 200:
            print("✅ Task detail accessible")
        else:
            print(f"❌ Task detail failed: {response.status_code}")
            return False
    except Exception as e:
        print(f"❌ Task detail error: {e}")
        return False
    
    # Test 6: Access task edit form
    try:
        response = client.get(f'/api/staff/tasks/{task.id}/edit/')
        if response.status_code == 200:
            print("✅ Task edit form accessible")
        else:
            print(f"❌ Task edit form failed: {response.status_code}")
            return False
    except Exception as e:
        print(f"❌ Task edit form error: {e}")
        return False
    
    # Test 7: Update task
    try:
        update_data = {
            'title': 'Updated Test Task',
            'description': 'This is an updated test task',
            'task_type': 'cleaning',
            'status': 'in-progress',
            'assigned_to': user.id,
            'property_ref': property_obj.id,
            'due_date': '2024-12-31T10:00'
        }
        
        response = client.post(f'/api/staff/tasks/{task.id}/edit/', update_data)
        if response.status_code == 302:  # Redirect after successful update
            print("✅ Task update successful")
            
            # Verify the update
            task.refresh_from_db()
            if task.title == 'Updated Test Task':
                print("✅ Task title updated correctly")
            else:
                print("❌ Task title not updated")
                return False
        else:
            print(f"❌ Task update failed: {response.status_code}")
            print(f"Response content: {response.content.decode()[:500]}")
            return False
    except Exception as e:
        print(f"❌ Task update error: {e}")
        return False
    
    # Test 8: Duplicate task
    try:
        response = client.get(f'/api/staff/tasks/{task.id}/duplicate/')
        if response.status_code == 302:  # Redirect after successful duplication
            print("✅ Task duplication successful")
            
            # Check if duplicate was created
            duplicate_task = Task.objects.filter(title='Updated Test Task (Copy)').first()
            if duplicate_task:
                print(f"✅ Duplicate task created with ID: {duplicate_task.id}")
            else:
                print("❌ Duplicate task not found")
                return False
        else:
            print(f"❌ Task duplication failed: {response.status_code}")
            return False
    except Exception as e:
        print(f"❌ Task duplication error: {e}")
        return False
    
    # Test 9: Delete task
    try:
        response = client.post(f'/api/staff/tasks/{task.id}/delete/')
        if response.status_code == 302:  # Redirect after successful deletion
            print("✅ Task deletion successful")
            
            # Check if task was deleted
            if not Task.objects.filter(id=task.id).exists():
                print("✅ Task deleted from database")
            else:
                print("❌ Task still exists in database")
                return False
        else:
            print(f"❌ Task deletion failed: {response.status_code}")
            return False
    except Exception as e:
        print(f"❌ Task deletion error: {e}")
        return False
    
    # Cleanup
    try:
        # Delete remaining test data
        Task.objects.filter(title__contains='Test Task').delete()
        Property.objects.filter(name='Test Property').delete()
        User.objects.filter(username='testuser').delete()
        print("✅ Cleanup completed")
    except Exception as e:
        print(f"⚠️ Cleanup warning: {e}")
    
    print("\n🎉 All CRUD operations tests passed!")
    return True

if __name__ == '__main__':
    success = test_crud_operations()
    sys.exit(0 if success else 1)
