#!/usr/bin/env python
"""
Test dashboard API endpoint with proper authentication
"""
import os
import sys
import django

sys.path.append('/Users/duylam1407/Workspace/SJSU/aristay_app/aristay_backend')
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'backend.settings')
django.setup()

from django.contrib.auth.models import User
from django.test import Client
from rest_framework.authtoken.models import Token

def test_dashboard_api():
    """Test dashboard API with proper authentication"""
    print("=== Testing Dashboard API with Authentication ===\n")
    
    # Get teststaff user
    user = User.objects.get(username='teststaff')
    print(f"👤 User: {user.username}")
    
    # Get or create token for authentication
    token, created = Token.objects.get_or_create(user=user)
    print(f"🔑 Token: {token.key[:20]}...")
    
    # Create test client
    client = Client()
    
    # Test without authentication
    print(f"\n🚫 Testing without authentication:")
    response = client.get('/api/manager/dashboard/')
    print(f"   Status: {response.status_code}")
    
    # Test with token authentication
    print(f"\n✅ Testing with token authentication:")
    response = client.get('/api/manager/dashboard/', HTTP_AUTHORIZATION=f'Token {token.key}')
    print(f"   Status: {response.status_code}")
    
    if response.status_code == 200:
        data = response.json()
        print(f"   ✅ SUCCESS!")
        print(f"   Tasks total: {data.get('tasks', {}).get('total', 'N/A')}")
        print(f"   Users total: {data.get('users', {}).get('total', 'N/A')}")
    elif response.status_code == 401:
        print(f"   ❌ Still getting 401 - authentication issue")
        print(f"   Response: {response.content.decode()[:200]}...")
    elif response.status_code == 403:
        print(f"   ❌ Permission denied - authorization issue")
        print(f"   Response: {response.content.decode()[:200]}...")
    else:
        print(f"   ❌ Other error: {response.status_code}")
        print(f"   Response: {response.content.decode()[:200]}...")

if __name__ == "__main__":
    test_dashboard_api()
