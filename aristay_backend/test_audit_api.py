#!/usr/bin/env python3
"""
Phase 2 Audit System API Validation
Test the complete audit system via HTTP API endpoints
"""
import os
import requests
import json
from datetime import datetime

BASE_URL = os.getenv("ARISTAY_BASE_URL", "http://127.0.0.1:8001")

def test_audit_api():
    """Test the audit system API endpoints."""
    print("🌐 Phase 2 Audit System API Validation")
    print("=" * 50)
    
    # Test 1: Check server is running
    print("\n1. Testing Server Connectivity")
    try:
        response = requests.get(f'{BASE_URL}/api/', timeout=5)
        print(f"✓ Server is running (status: {response.status_code})")
    except requests.RequestException as e:
        print(f"❌ Server connection failed: {e}")
        return
    
    # Test 2: Try to access audit events (should require auth)
    print("\n2. Testing API Authentication")
    try:
        response = requests.get(f'{BASE_URL}/api/audit-events/', timeout=5)
        if response.status_code == 401:
            print("✓ API properly requires authentication")
        else:
            print(f"⚠️  Unexpected status: {response.status_code}")
    except requests.RequestException as e:
        print(f"❌ API request failed: {e}")
        return
    
    # Test 3: Check admin interface is accessible
    print("\n3. Testing Admin Interface")
    try:
        response = requests.get(f'{BASE_URL}/admin/', timeout=5)
        if response.status_code in [200, 302]:  # 302 = redirect to login
            print("✓ Admin interface is accessible")
        else:
            print(f"⚠️  Admin interface status: {response.status_code}")
    except requests.RequestException as e:
        print(f"❌ Admin interface failed: {e}")
        return
    
    # Test 4: Check if audit events admin is registered
    print("\n4. Testing Audit Events Admin Registration")
    try:
        response = requests.get(f'{BASE_URL}/admin/api/auditevent/', timeout=5)
        if response.status_code in [200, 302]:  # 302 = redirect to login
            print("✓ Audit Events admin is registered")
        else:
            print(f"⚠️  Audit Events admin status: {response.status_code}")
    except requests.RequestException as e:
        print(f"❌ Audit Events admin failed: {e}")
    
    print("\n" + "=" * 50)
    print("🎉 Phase 2 Audit System API Validation Complete!")
    print(f"Server running at: {BASE_URL}")
    print(f"Admin interface: {BASE_URL}/admin/")
    print(f"Audit Events API: {BASE_URL}/api/audit-events/")
    print(f"Audit Events Admin: {BASE_URL}/admin/api/auditevent/")
    print("=" * 50)

if __name__ == '__main__':
    test_audit_api()
