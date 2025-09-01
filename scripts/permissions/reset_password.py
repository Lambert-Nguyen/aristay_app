#!/usr/bin/env python
"""
Reset teststaff user password
"""
import os
import sys
import django

sys.path.append('/Users/duylam1407/Workspace/SJSU/aristay_app/aristay_backend')
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'backend.settings')
django.setup()

from django.contrib.auth.models import User

def reset_password():
    """Reset teststaff password"""
    try:
        user = User.objects.get(username='teststaff')
        user.set_password('testpass123')
        user.save()
        print(f"✅ Password reset for {user.username}")
        print(f"   New password: testpass123")
        
        # Verify the password works
        if user.check_password('testpass123'):
            print(f"   ✅ Password verification successful")
        else:
            print(f"   ❌ Password verification failed")
            
    except User.DoesNotExist:
        print("User 'teststaff' not found")

if __name__ == "__main__":
    reset_password()
