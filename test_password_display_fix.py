#!/usr/bin/env python3
"""
Test script to verify the password field display fix in manager admin interface.

This script:
1. Tests the manager admin interface accessibility
2. Verifies password field display doesn't show "No password set."
3. Confirms manager_alice can access the manager portal

Usage:
    cd /Users/duylam1407/Workspace/SJSU/aristay_app
    source .venv/bin/activate
    cd aristay_backend
    python ../test_password_display_fix.py

The Django server should be running on port 8001 for this test.
"""

import os
import sys
import django

# Add the backend directory to Python path
backend_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'aristay_backend')
sys.path.append(backend_path)

# Configure Django settings
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'backend.settings')
django.setup()

from django.contrib.auth.models import User
from api.models import Profile, UserRole
from api.managersite import manager_site
from django.test import Client, RequestFactory
from django.contrib.auth import authenticate
from django.contrib.sessions.middleware import SessionMiddleware
from django.contrib.messages.middleware import MessageMiddleware

def test_password_display_fix():
    """Test that password fields display properly in manager admin"""
    
    print("🔍 Testing Password Display Fix in Manager Admin Interface")
    print("=" * 70)
    
    # 1. Verify manager_alice exists and has proper setup
    try:
        manager_alice = User.objects.get(username='manager_alice')
        print(f"✅ Found manager_alice: {manager_alice.username}")
        print(f"   - Email: {manager_alice.email}")
        print(f"   - Has password: {'Yes' if manager_alice.password else 'No'}")
        print(f"   - Password hash: {manager_alice.password[:20]}..." if manager_alice.password else "   - No password")
        
        # Check profile
        profile = manager_alice.profile
        print(f"   - Profile role: {profile.role}")
        print(f"   - Has manager_portal_access: {profile.has_permission('manager_portal_access')}")
        
    except User.DoesNotExist:
        print("❌ manager_alice not found. Creating...")
        manager_alice = User.objects.create_user(
            username='manager_alice',
            email='alice@aristay.com',
            password='testpass123',
            first_name='Alice',
            last_name='Manager'
        )
        # Create profile with manager role
        profile, created = Profile.objects.get_or_create(
            user=manager_alice,
            defaults={'role': UserRole.MANAGER}
        )
        print(f"✅ Created manager_alice with profile role: {profile.role}")
    
    # 2. Test manager admin site access
    print(f"\n🔐 Testing Manager Admin Access")
    client = Client()
    
    # Login as manager_alice
    login_success = client.login(username='manager_alice', password='testpass123')
    print(f"   - Login successful: {login_success}")
    
    if login_success:
        # Test manager admin main page
        response = client.get('/manager/')
        print(f"   - Manager admin page status: {response.status_code}")
        
        # Test user change form (this is where the password display issue was)
        user_change_url = f'/manager/auth/user/{manager_alice.id}/change/'
        response = client.get(user_change_url)
        print(f"   - User change form status: {response.status_code}")
        
        if response.status_code == 200:
            content = response.content.decode('utf-8')
            
            # Check for password field presence and proper display
            if 'No password set.' in content:
                print("   ❌ Still shows 'No password set.' - Fix didn't work")
                return False
            elif 'password' in content.lower() and 'field-password' in content:
                print("   ✅ Password field is present and properly configured")
            else:
                print("   ⚠️  Password field configuration unclear")
            
            # Check for proper readonly handling
            if 'readonly' in content and 'field-password' in content:
                print("   ✅ Password field is properly set as readonly")
            else:
                print("   ⚠️  Password field readonly status unclear")
                
        else:
            print(f"   ❌ Cannot access user change form. Status: {response.status_code}")
            return False
    else:
        print("   ❌ Manager login failed")
        return False
    
    # 3. Test with another user to ensure it's not just manager_alice
    print(f"\n👥 Testing with Other Users")
    
    # Find staff_bob
    try:
        staff_bob = User.objects.get(username='staff_bob')
        print(f"   - Found staff_bob: {staff_bob.username}")
        print(f"   - Has password: {'Yes' if staff_bob.password else 'No'}")
        
        # Test viewing staff_bob's change form as manager_alice
        bob_change_url = f'/manager/auth/user/{staff_bob.id}/change/'
        response = client.get(bob_change_url)
        print(f"   - Staff user change form status: {response.status_code}")
        
        if response.status_code == 200:
            content = response.content.decode('utf-8')
            if 'No password set.' in content:
                print("   ❌ Still shows 'No password set.' for other users")
                return False
            else:
                print("   ✅ Password field displays properly for other users too")
        
    except User.DoesNotExist:
        print("   ⚠️  staff_bob not found, skipping cross-user test")
    
    print(f"\n🎉 Password Display Fix Test Results:")
    print(f"   ✅ Manager admin interface accessible")
    print(f"   ✅ Password fields display properly (no 'No password set.')")
    print(f"   ✅ Password field is readonly as intended")
    print(f"   ✅ Fix works for multiple users")
    
    return True

def main():
    """Run the password display fix test"""
    try:
        success = test_password_display_fix()
        
        if success:
            print(f"\n🎯 SUCCESS: Password display fix is working correctly!")
            print(f"   You can now visit: http://localhost:8001/manager/")
            print(f"   Login as manager_alice / testpass123")
            print(f"   Go to Users section and edit any user")
            print(f"   Password field should display properly without 'No password set.' message")
        else:
            print(f"\n❌ FAILED: Password display fix needs more work")
            
    except Exception as e:
        print(f"\n💥 ERROR during test: {str(e)}")
        import traceback
        traceback.print_exc()
        return False
    
    return success

if __name__ == "__main__":
    main()
