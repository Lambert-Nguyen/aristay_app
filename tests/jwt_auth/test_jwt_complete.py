#!/usr/bin/env python3
"""
Quick test script for JWT authentication system
"""
import pytest
import requests
import json
import time
import os

# Skip this test in CI environment as it requires a running server
pytestmark = pytest.mark.skipif(
    bool(os.getenv('CI')) or bool(os.getenv('TESTING')), 
    reason="Integration test requires running server"
)

print("🔐 Testing JWT Authentication System")
print("=" * 50)

# Configuration
BASE_URL = "http://127.0.0.1:8000"
TEST_USER = {
    "username": "admin",  # Assuming you have an admin user
    "password": "admin"   # Change this to your actual admin password
}

def test_jwt_authentication():
    """Test JWT token generation, refresh, and revocation"""
    
    print("\n1. Testing JWT Token Generation...")
    
    # Test JWT token generation
    login_url = f"{BASE_URL}/api/token/"
    response = requests.post(
        login_url,
        json=TEST_USER,
        headers={'Content-Type': 'application/json'},
        timeout=10
    )
    
    if response.status_code == 200:
        tokens = response.json()
        access_token = tokens.get('access')
        refresh_token = tokens.get('refresh')
        
        print(f"✅ JWT Login successful!")
        print(f"   Access Token: {access_token[:50]}..." if access_token else "   No access token")
        print(f"   Refresh Token: {refresh_token[:50]}..." if refresh_token else "   No refresh token")
        
        if not access_token or not refresh_token:
            print("❌ Missing tokens in response")
            return False
            
        # Test API access with JWT token
        print("\n2. Testing API Access with JWT Token...")
        api_url = f"{BASE_URL}/api/users/me/"
        api_response = requests.get(
            api_url,
            headers={'Authorization': f'Bearer {access_token}'},
            timeout=10
        )
        
        if api_response.status_code == 200:
            user_data = api_response.json()
            print(f"✅ API access successful!")
            print(f"   User: {user_data.get('username', 'Unknown')}")
        else:
            print(f"❌ API access failed: {api_response.status_code}")
            print(f"   Response: {api_response.text}")
        
        # Test token refresh
        print("\n3. Testing Token Refresh...")
        refresh_url = f"{BASE_URL}/api/token/refresh/"
        refresh_response = requests.post(
            refresh_url,
            json={'refresh': refresh_token},
            headers={'Content-Type': 'application/json'},
            timeout=10
        )
        
        if refresh_response.status_code == 200:
            new_tokens = refresh_response.json()
            new_access = new_tokens.get('access')
            print(f"✅ Token refresh successful!")
            print(f"   New Access Token: {new_access[:50]}..." if new_access else "   No new access token")
        else:
            print(f"❌ Token refresh failed: {refresh_response.status_code}")
            print(f"   Response: {refresh_response.text}")
        
        # Test token revocation
        print("\n4. Testing Token Revocation...")
        revoke_url = f"{BASE_URL}/api/token/revoke/"
        revoke_response = requests.post(
            revoke_url,
            json={'refresh': refresh_token},
            headers={
                'Authorization': f'Bearer {access_token}',
                'Content-Type': 'application/json'
            },
            timeout=10
        )
        
        if revoke_response.status_code == 200:
            print("✅ Token revocation successful!")
            print(f"   Message: {revoke_response.json().get('message', 'Token revoked')}")
        else:
            print(f"❌ Token revocation failed: {revoke_response.status_code}")
            print(f"   Response: {revoke_response.text}")
            
        return True
        
    else:
        print(f"❌ JWT Login failed: {response.status_code}")
        print(f"   Response: {response.text}")
        return False

def test_rate_limiting():
    """Test rate limiting on login endpoint"""
    print("\n5. Testing Rate Limiting...")
    
    login_url = f"{BASE_URL}/api/token/"
    
    # Make rapid requests to test throttling
    for i in range(7):  # Should hit rate limit at 6 requests (limit is 5/minute)
        response = requests.post(
            login_url,
            json={"username": "invalid", "password": "invalid"},
            headers={'Content-Type': 'application/json'},
            timeout=5
        )
        
        if response.status_code == 429:
            print(f"✅ Rate limiting working! Hit limit at request {i+1}")
            break
        else:
            print(f"   Request {i+1}: {response.status_code}")
        
        time.sleep(0.5)  # Small delay between requests
    else:
        print("⚠️  Rate limiting may not be working as expected")

def main():
    """Run all JWT tests"""
    try:
        # Wait a moment for server to be fully ready
        time.sleep(2)
        
        success = test_jwt_authentication()
        if success:
            test_rate_limiting()
        
        print("\n" + "=" * 50)
        print("🏁 JWT Authentication Test Complete")
        
    except requests.exceptions.ConnectionError:
        print("❌ Could not connect to Django server at http://127.0.0.1:8000")
        print("   Make sure the server is running: python manage.py runserver 8000")
    except requests.exceptions.Timeout:
        print("❌ Request timed out")
    except Exception as e:
        print(f"❌ Unexpected error: {e}")

if __name__ == "__main__":
    main()
