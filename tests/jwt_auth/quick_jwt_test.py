#!/usr/bin/env python3
"""
Quick JWT Test Script
"""

import requests
import json
import time

def test_jwt():
    """Test JWT authentication with correct endpoints"""
    
    print('🚀 Testing JWT Authentication System')
    print('=' * 50)
    
    # Wait a moment for server
    time.sleep(1)
    
    base_url = "http://127.0.0.1:8000"
    
    # Test JWT token generation
    print('🔐 Testing JWT Token Generation...')
    login_data = {
        'username': 'testuser',
        'password': 'testpassword123'
    }
    
    try:
        response = requests.post(
            f'{base_url}/api/token/',
            json=login_data,
            headers={'Content-Type': 'application/json'},
            timeout=10
        )
        
        print(f'Status Code: {response.status_code}')
        
        if response.status_code == 200:
            tokens = response.json()
            print('✅ JWT Token Generated Successfully!')
            print(f'Access Token: {tokens.get("access", "None")[:50]}...')
            print(f'Refresh Token: {tokens.get("refresh", "None")[:50]}...')
            
            access_token = tokens.get('access')
            refresh_token = tokens.get('refresh')
            
            # Test token refresh
            if refresh_token:
                print('\n🔄 Testing Token Refresh...')
                refresh_response = requests.post(
                    f'{base_url}/api/token/refresh/',
                    json={'refresh': refresh_token},
                    headers={'Content-Type': 'application/json'},
                    timeout=10
                )
                
                if refresh_response.status_code == 200:
                    new_token = refresh_response.json()
                    print('✅ Token Refresh Successful!')
                    print(f'New Access Token: {new_token.get("access", "None")[:50]}...')
                else:
                    print(f'❌ Token Refresh Failed: {refresh_response.status_code}')
            
            # Test protected endpoint
            if access_token:
                print('\n🛡️ Testing Protected Endpoint...')
                protected_response = requests.get(
                    f'{base_url}/api/user/sessions/',
                    headers={
                        'Authorization': f'Bearer {access_token}',
                        'Content-Type': 'application/json'
                    },
                    timeout=10
                )
                
                print(f'Protected endpoint status: {protected_response.status_code}')
                if protected_response.status_code == 200:
                    print('✅ Protected endpoint access successful!')
                else:
                    print(f'❌ Protected endpoint failed: {protected_response.text}')
            
        else:
            print(f'❌ JWT Token Generation Failed: {response.status_code}')
            print(f'Response: {response.text}')
            
    except requests.exceptions.ConnectionError:
        print('❌ Connection Error: Could not connect to server')
        print('Make sure Django server is running on http://127.0.0.1:8000')
    except requests.exceptions.Timeout:
        print('❌ Request Timeout: Server took too long to respond')
    except Exception as e:
        print(f'❌ Unexpected Error: {e}')
    
    print('\n' + '=' * 50)
    print('🎯 JWT Test Complete')

if __name__ == '__main__':
    test_jwt()
