#!/usr/bin/env python
"""
Check teststaff user authentication details
"""
import os
import sys
import django

sys.path.append('/Users/duylam1407/Workspace/SJSU/aristay_app/aristay_backend')
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'backend.settings')
django.setup()

from django.contrib.auth.models import User

def check_user_auth():
    """Check teststaff user details"""
    try:
        user = User.objects.get(username='teststaff')
        print(f"User: {user.username}")
        print(f"Email: {user.email}")
        print(f"Is active: {user.is_active}")
        print(f"Is staff: {user.is_staff}")
        print(f"Is superuser: {user.is_superuser}")
        print(f"Last login: {user.last_login}")
        print(f"Date joined: {user.date_joined}")
        
        # Check if password is usable
        print(f"Has usable password: {user.has_usable_password()}")
        
        # Test a common password
        print(f"Password 'admin123' works: {user.check_password('admin123')}")
        print(f"Password 'password' works: {user.check_password('password')}")
        print(f"Password 'teststaff' works: {user.check_password('teststaff')}")
        
    except User.DoesNotExist:
        print("User 'teststaff' not found")

if __name__ == "__main__":
    check_user_auth()
