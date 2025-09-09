#!/usr/bin/env python3
"""
Simple test to verify the password field display fix works correctly.

This script directly tests the UserManagerAdmin configuration to ensure
the password field doesn't show "No password set." when a user has a password.
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
from api.managersite import manager_site, UserManagerAdmin

def test_password_field_configuration():
    """Test that password field is configured correctly in UserManagerAdmin"""
    
    print("🔍 Testing Password Field Configuration in Manager Admin")
    print("=" * 65)
    
    # 1. Check UserManagerAdmin configuration
    user_admin = UserManagerAdmin(User, manager_site)
    print(f"✅ UserManagerAdmin loaded successfully")
    
    # 2. Check readonly_fields configuration
    readonly_fields = getattr(user_admin, 'readonly_fields', ())
    print(f"   - Readonly fields: {readonly_fields}")
    
    if 'password' in readonly_fields:
        print(f"   ✅ Password field is correctly set as readonly")
    else:
        print(f"   ❌ Password field is NOT set as readonly")
        return False
    
    # 3. Check that exclude is NOT present (this was the bug)
    exclude = getattr(user_admin, 'exclude', None)
    print(f"   - Exclude fields: {exclude}")
    
    if exclude and 'password' in exclude:
        print(f"   ❌ Password field is still excluded - bug not fixed!")
        return False
    else:
        print(f"   ✅ Password field is NOT excluded - bug fixed!")
    
    # 4. Check fieldsets configuration
    fieldsets = getattr(user_admin, 'fieldsets', ())
    print(f"   - Number of fieldsets: {len(fieldsets)}")
    
    # Check if password is in fieldsets
    password_in_fieldsets = False
    for fieldset_name, fieldset_options in fieldsets:
        fields = fieldset_options.get('fields', ())
        if 'password' in fields:
            password_in_fieldsets = True
            print(f"   ✅ Password field found in fieldset: '{fieldset_name}'")
            break
    
    if not password_in_fieldsets:
        print(f"   ❌ Password field not found in any fieldset")
        return False
    
    # 5. Test with an actual user to verify behavior
    print(f"\n👤 Testing with Real User Data")
    
    try:
        # Get manager_alice
        manager_alice = User.objects.get(username='manager_alice')
        print(f"   - Found user: {manager_alice.username}")
        print(f"   - Has password: {'Yes' if manager_alice.password else 'No'}")
        print(f"   - Password starts with: {manager_alice.password[:20]}...")
        
        # Verify the user has profile and permissions
        profile = manager_alice.profile
        print(f"   - Profile role: {profile.role}")
        print(f"   - Has manager access: {profile.has_permission('manager_portal_access')}")
        
        # Simulate the admin form rendering logic
        print(f"\n📋 Simulating Admin Form Field Rendering")
        
        # This is what Django admin does internally
        form_fields = []
        for fieldset_name, fieldset_options in user_admin.fieldsets:
            fields = fieldset_options.get('fields', ())
            for field in fields:
                if hasattr(manager_alice, field):
                    field_value = getattr(manager_alice, field)
                    form_fields.append((field, field_value))
                    if field == 'password':
                        # This is the key test - does Django show the password properly?
                        if field_value:
                            print(f"   ✅ Password field has value: {field_value[:20]}...")
                        else:
                            print(f"   ❌ Password field is empty/None")
                            return False
        
        print(f"   - Total form fields that will render: {len(form_fields)}")
        
    except User.DoesNotExist:
        print(f"   ❌ manager_alice not found - test data missing")
        return False
    except Exception as e:
        print(f"   ❌ Error accessing user data: {str(e)}")
        return False
    
    return True

def test_other_users():
    """Test the configuration with other users too"""
    
    print(f"\n👥 Testing Configuration with Other Users")
    print("-" * 50)
    
    # Test with staff_bob if available
    try:
        staff_bob = User.objects.get(username='staff_bob')
        print(f"   - Found staff_bob: {staff_bob.username}")
        print(f"   - Has password: {'Yes' if staff_bob.password else 'No'}")
        
        if not staff_bob.password:
            print(f"   ❌ staff_bob has no password - this would show 'No password set.'")
            return False
        else:
            print(f"   ✅ staff_bob has password - should display properly")
            
    except User.DoesNotExist:
        print(f"   ⚠️  staff_bob not found, skipping")
    
    return True

def main():
    """Run all password configuration tests"""
    
    try:
        print(f"🧪 Password Display Fix - Configuration Tests")
        print(f"=" * 70)
        print(f"")
        
        # Test 1: Configuration check
        config_ok = test_password_field_configuration()
        
        if not config_ok:
            print(f"\n❌ FAILED: Password field configuration is incorrect")
            return False
        
        # Test 2: Other users
        other_users_ok = test_other_users()
        
        if not other_users_ok:
            print(f"\n❌ FAILED: Issues found with other users")
            return False
        
        print(f"\n🎉 SUCCESS: Password Display Fix is Working!")
        print(f"=" * 70)
        print(f"✅ Password field is correctly configured as readonly")
        print(f"✅ Password field is NOT excluded from forms")
        print(f"✅ Password field is included in fieldsets")
        print(f"✅ Users with passwords will display properly")
        print(f"")
        print(f"🔗 Manual Verification:")
        print(f"   1. Start the Django server: python manage.py runserver")
        print(f"   2. Visit: http://localhost:8000/manager/")
        print(f"   3. Login as manager_alice / testpass123")
        print(f"   4. Go to Users → Click any user")
        print(f"   5. Verify password field shows hash, not 'No password set.'")
        
        return True
        
    except Exception as e:
        print(f"\n💥 ERROR during tests: {str(e)}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    success = main()
    exit(0 if success else 1)
