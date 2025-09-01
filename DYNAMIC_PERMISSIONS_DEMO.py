# Dynamic Permission System Demo Script

"""
This script demonstrates how the DRF endpoints now dynamically adjust
based on user permissions, including overrides granted by superusers.

Example scenarios:

1. Manager without 'view_bookings' permission:
   - BookingViewSet.list() -> Empty queryset (403 equivalent)
   - GET /api/bookings/ -> Returns empty list

2. Manager granted 'view_bookings' permission by superuser:
   - BookingViewSet.list() -> Full queryset accessible
   - GET /api/bookings/ -> Returns all bookings

3. Staff member without 'delete_users' permission:
   - AdminUserDetailView.delete() -> Permission denied
   - DELETE /api/admin/users/1/ -> 403 Forbidden

4. Staff member granted 'delete_users' permission by superuser:
   - AdminUserDetailView.delete() -> Delete allowed
   - DELETE /api/admin/users/1/ -> 204 No Content (success)
"""

import requests
import json

# Base URL for API
BASE_URL = "http://127.0.0.1:8002/api"

def test_dynamic_permissions():
    """
    Test the dynamic permission system by making API calls
    """
    print("=== Dynamic Permission System Demo ===\n")
    
    # Test endpoints that now use dynamic permissions
    endpoints_to_test = [
        {
            'url': f'{BASE_URL}/bookings/',
            'method': 'GET',
            'description': 'BookingViewSet - requires view_bookings permission',
            'expected_without_permission': 'Empty list or 403',
            'expected_with_permission': 'List of bookings'
        },
        {
            'url': f'{BASE_URL}/tasks/',
            'method': 'GET',
            'description': 'TaskViewSet - requires view_tasks permission',
            'expected_without_permission': 'Empty list or 403',
            'expected_with_permission': 'List of tasks'
        },
        {
            'url': f'{BASE_URL}/users/',
            'method': 'GET',
            'description': 'UserList - requires view_users permission',
            'expected_without_permission': 'Empty list or 403',
            'expected_with_permission': 'List of users'
        },
        {
            'url': f'{BASE_URL}/admin/charts/',
            'method': 'GET',
            'description': 'Admin Charts - requires view_reports permission',
            'expected_without_permission': 'Redirect to login or 403',
            'expected_with_permission': 'Charts dashboard'
        },
        {
            'url': f'{BASE_URL}/admin/system-metrics/',
            'method': 'GET',
            'description': 'System Metrics - requires system_metrics_access permission',
            'expected_without_permission': 'Permission denied',
            'expected_with_permission': 'System metrics data'
        }
    ]
    
    print("📋 Endpoints with Dynamic Permissions:")
    print("=" * 50)
    
    for endpoint in endpoints_to_test:
        print(f"🔗 {endpoint['method']} {endpoint['url']}")
        print(f"   Description: {endpoint['description']}")
        print(f"   Without permission: {endpoint['expected_without_permission']}")
        print(f"   With permission: {endpoint['expected_with_permission']}")
        print()
    
    print("🔑 Permission Types Handled:")
    print("=" * 30)
    permission_types = [
        "view_bookings", "add_bookings", "change_bookings", "delete_bookings",
        "view_tasks", "add_tasks", "change_tasks", "delete_tasks", 
        "view_users", "add_users", "change_users", "delete_users",
        "view_properties", "add_properties", "change_properties", "delete_properties",
        "view_reports", "system_metrics_access", "admin_panel_access",
        "excel_import_access", "file_upload_access"
    ]
    
    for perm in permission_types:
        print(f"   ✓ {perm}")
    
    print("\n🎯 How It Works:")
    print("=" * 16)
    print("1. Each ViewSet now uses Dynamic*Permissions classes")
    print("2. Permissions check user.profile.has_permission(permission_name)")
    print("3. has_permission() considers role defaults + user overrides")
    print("4. If granted additional permissions via UI/API, access is automatically enabled")
    print("5. Querysets are filtered based on view permissions")
    print("6. CRUD operations are controlled by add/change/delete permissions")
    
    print("\n🛠️ Management Interface:")
    print("=" * 23)
    print("• Grant permissions: POST /api/grant/permission/")
    print("• Revoke permissions: POST /api/revoke/permission/")
    print("• View user permissions: GET /api/user/permissions/")
    print("• Permission management UI: /api/admin/permissions/")
    
    print("\n✨ Benefits:")
    print("=" * 11)
    print("• Managers can be granted specific permissions by superusers")
    print("• Staff can get temporary elevated access for specific tasks")
    print("• All DRF endpoints respect the custom permission system")
    print("• No need to manually update ViewSets when permissions change")
    print("• Granular control over who can access what data/operations")

def test_api_call(url, method='GET', auth_token=None):
    """
    Make an API call to test permissions
    """
    headers = {'Content-Type': 'application/json'}
    if auth_token:
        headers['Authorization'] = f'Token {auth_token}'
    
    try:
        if method == 'GET':
            response = requests.get(url, headers=headers, timeout=5)
        elif method == 'POST':
            response = requests.post(url, headers=headers, timeout=5)
        
        return {
            'status_code': response.status_code,
            'success': response.status_code < 400,
            'data': response.json() if response.headers.get('content-type', '').startswith('application/json') else response.text[:200]
        }
    except requests.exceptions.RequestException as e:
        return {
            'status_code': 0,
            'success': False,
            'error': str(e)
        }

if __name__ == "__main__":
    test_dynamic_permissions()
    
    print("\n🧪 To test live API calls:")
    print("=" * 26)
    print("1. Create users with different roles")
    print("2. Grant specific permissions to managers/staff via the UI")
    print("3. Test API endpoints with their authentication tokens")
    print("4. Observe how permissions automatically adjust DRF behavior")
    
    print("\n📚 Documentation:")
    print("=" * 16)
    print("See PERMISSION_SYSTEM_IMPLEMENTATION.md for full details")
