#!/usr/bin/env python
"""
Test the actual HTTP API responses for teststaff user
"""
import pytest
import requests
import json
import os

# Skip this test in CI environment as it requires a running server  
pytestmark = pytest.mark.skipif(
    bool(os.getenv('CI')) or bool(os.getenv('TESTING')), 
    reason="Integration test requires running server"
)

def test_api_endpoints():
    """Test API endpoints with teststaff credentials"""
    print("=== Testing HTTP API for teststaff ===\n")
    
    base_url = "http://127.0.0.1:8002"
    
    # Test login first
    login_url = f"{base_url}/api/auth/login/"
    login_data = {
        "username": "teststaff",
        "password": "admin123"  # Adjust if different
    }
    
    print("🔐 Testing login...")
    try:
        login_response = requests.post(login_url, data=login_data)
        print(f"   Status: {login_response.status_code}")
        
        if login_response.status_code == 200:
            login_result = login_response.json()
            token = login_result.get('token')
            print(f"   ✅ Login successful, token: {token[:20]}...")
        else:
            print(f"   ❌ Login failed: {login_response.text}")
            return
    except Exception as e:
        print(f"   ❌ Login error: {e}")
        return
    
    # Test session-based authentication (for DRF browsable API)
    session = requests.Session()
    csrf_response = session.get(f"{base_url}/api/auth/login/")
    csrf_token = csrf_response.cookies.get('csrftoken')
    
    if csrf_token:
        login_data['csrfmiddlewaretoken'] = csrf_token
        session.headers.update({'X-CSRFToken': csrf_token})
        session_login = session.post(login_url, data=login_data)
        print(f"   📝 Session login status: {session_login.status_code}")
    
    # Test bookings endpoint with token authentication
    bookings_url = f"{base_url}/api/bookings/"
    headers = {
        "Authorization": f"Token {token}",
        "Accept": "application/json"
    }
    
    print(f"\n📋 Testing {bookings_url} with token auth...")
    try:
        response = requests.get(bookings_url, headers=headers)
        print(f"   Status: {response.status_code}")
        
        if response.status_code == 200:
            data = response.json()
            if isinstance(data, dict) and 'results' in data:
                count = len(data['results'])
                total = data.get('count', count)
                print(f"   ✅ Success: {count} bookings returned (total: {total})")
                
                # Show first booking
                if data['results']:
                    first_booking = data['results'][0]
                    print(f"      First booking: {first_booking.get('id')} - {first_booking.get('guest_name')}")
            else:
                print(f"   ⚠️  Unexpected response format: {type(data)}")
        else:
            print(f"   ❌ Error: {response.text}")
    except Exception as e:
        print(f"   ❌ Request error: {e}")
    
    # Test bookings endpoint with session authentication (DRF browsable API)
    print(f"\n🌐 Testing {bookings_url} with session auth (DRF browsable API)...")
    try:
        session_response = session.get(bookings_url, headers={"Accept": "text/html"})
        print(f"   Status: {session_response.status_code}")
        
        if session_response.status_code == 200:
            # Check if it looks like the DRF browsable API
            content = session_response.text
            if "Django REST framework" in content:
                print(f"   ✅ DRF browsable API loaded successfully")
                
                # Check for booking data in the HTML
                if "guest_name" in content or "bookings" in content.lower():
                    print(f"   ✅ Booking data appears to be present in the response")
                else:
                    print(f"   ⚠️  No booking data visible in the HTML response")
            else:
                print(f"   ⚠️  Response doesn't look like DRF browsable API")
        else:
            print(f"   ❌ Error: {session_response.status_code}")
            print(f"   Response snippet: {session_response.text[:200]}")
    except Exception as e:
        print(f"   ❌ Request error: {e}")
    
    # Test user permissions endpoint
    permissions_url = f"{base_url}/api/permissions/user/"
    print(f"\n🔑 Testing user permissions endpoint...")
    try:
        perm_response = requests.get(permissions_url, headers=headers)
        print(f"   Status: {perm_response.status_code}")
        
        if perm_response.status_code == 200:
            permissions = perm_response.json()
            print(f"   ✅ Permissions loaded")
            view_bookings = permissions.get('view_bookings', False)
            print(f"   📋 view_bookings permission: {view_bookings}")
        else:
            print(f"   ❌ Error: {perm_response.text}")
    except Exception as e:
        print(f"   ❌ Request error: {e}")

if __name__ == "__main__":
    test_api_endpoints()
