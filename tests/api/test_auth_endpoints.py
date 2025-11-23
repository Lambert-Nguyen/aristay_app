#!/usr/bin/env python
"""
Test dashboard API endpoint with proper authentication
"""
import os
import sys
import django

# Add backend to path using relative path
from pathlib import Path
PROJECT_ROOT = Path(__file__).resolve().parent
while not (PROJECT_ROOT / 'aristay_backend').exists() and PROJECT_ROOT.parent != PROJECT_ROOT:
    PROJECT_ROOT = PROJECT_ROOT.parent
BACKEND_DIR = PROJECT_ROOT / 'aristay_backend'
if str(BACKEND_DIR) not in sys.path:
    sys.path.insert(0, str(BACKEND_DIR))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'backend.settings')
django.setup()

from django.contrib.auth.models import User
from django.test import Client
from rest_framework.authtoken.models import Token

def test_dashboard_api(teststaff_user):
    """Test dashboard API with proper authentication"""
    print("=== Testing Dashboard API with Authentication ===\n")
    
    # Use teststaff user from fixture
    user = teststaff_user
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
