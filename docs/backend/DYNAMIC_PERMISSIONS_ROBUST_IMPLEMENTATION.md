# Dynamic Permissions System - Robust Implementation

## Overview

The AriStay application now features a comprehensive, robust dynamic permissions system that provides fine-grained access control with role-based permissions, user-specific overrides, and expiration capabilities.

## 🏗️ Architecture

### Core Components

1. **CustomPermission Model** - Defines available permissions
2. **RolePermission Model** - Maps permissions to roles
3. **UserPermissionOverride Model** - User-specific permission overrides
4. **Profile Model** - User roles and permission checking logic
5. **Permission Classes** - DRF permission classes for API endpoints

### Permission Hierarchy

```
Superuser (Full Access)
├── All permissions granted
├── Can delegate all permissions
└── Bypasses all permission checks

Manager (Management Access)
├── View/Add/Edit most resources
├── Cannot delete critical resources
├── Can delegate limited permissions
└── Access to reports and analytics

Staff (Operational Access)
├── View tasks and properties
├── Add tasks
├── Cannot edit/delete others' tasks
└── Limited system access

Viewer (Read-Only Access)
├── View-only permissions
├── No modification capabilities
└── Minimal system access
```

## 🔐 Permission System Features

### 1. Role-Based Permissions

Each role has predefined permissions:

- **Superuser**: 38 permissions (full access)
- **Manager**: 35 permissions (management access)
- **Staff**: 8 permissions (operational access)
- **Viewer**: 6 permissions (read-only access)

### 2. User Permission Overrides

Users can have specific permission overrides that:
- ✅ **Grant** permissions not available to their role
- ❌ **Deny** permissions normally available to their role
- ⏰ **Expire** automatically after a set time
- 📝 **Track** who granted the override and why

### 3. Dynamic Permission Classes

The system includes specialized permission classes:

```python
# Basic permission checking
HasCustomPermission('view_tasks')

# Multiple permission checking
HasAnyCustomPermission(['view_tasks', 'view_reports'])

# CRUD-based permissions
DynamicTaskPermissions()  # Maps HTTP methods to permissions
DynamicBookingPermissions()
DynamicUserPermissions()
DynamicPropertyPermissions()

# Specialized permissions
CanViewReports()
CanViewAnalytics()
CanAccessAdminPanel()
CanManageFiles()
```

## 🚀 Setup and Usage

### 1. Initialize Permissions

```bash
# Set up all default permissions and role mappings
python manage.py setup_permissions

# Reset all permissions (use with caution)
python manage.py setup_permissions --reset
```

### 2. Using in Views

```python
from api.permissions import DynamicTaskPermissions

class TaskViewSet(viewsets.ModelViewSet):
    permission_classes = [DynamicTaskPermissions]
    # Automatically maps:
    # GET -> view_tasks
    # POST -> add_tasks
    # PUT/PATCH -> change_tasks
    # DELETE -> delete_tasks
```

### 3. Checking Permissions in Code

```python
# Check if user has permission
if user.profile.has_permission('view_reports'):
    # Show reports

# Get all user permissions
permissions = user.profile.get_all_permissions()

# Check delegation rights
if user.profile.can_delegate_permission('add_tasks'):
    # Can grant this permission to others
```

## 🧪 Testing

### Manual Testing

```bash
# Test permission system
python test_permissions_manual.py

# Test API endpoints
python test_api_permissions.py
```

### Automated Testing

```bash
# Run permission tests
python manage.py test tests.test_dynamic_permissions
```

## 📊 Permission Categories

### Property Management
- `view_properties` - View property listings
- `add_properties` - Create new properties
- `change_properties` - Edit existing properties
- `delete_properties` - Remove properties

### Booking Management
- `view_bookings` - View booking information
- `add_bookings` - Create new bookings
- `change_bookings` - Edit existing bookings
- `delete_bookings` - Remove bookings
- `import_bookings` - Import bookings from Excel

### Task Management
- `view_tasks` - View task listings
- `add_tasks` - Create new tasks
- `change_tasks` - Edit existing tasks
- `delete_tasks` - Remove tasks
- `assign_tasks` - Assign tasks to others
- `view_all_tasks` - View all tasks (not just own)

### User Management
- `view_users` - View user listings
- `add_users` - Create new users
- `change_users` - Edit user information
- `delete_users` - Remove users
- `manage_user_permissions` - Manage user permissions

### Reports and Analytics
- `view_reports` - Access reports
- `export_data` - Export data
- `view_analytics` - View analytics dashboard

### System Administration
- `access_admin_panel` - Access Django admin
- `manager_portal_access` - Access manager portal
- `manage_system_settings` - Manage system settings
- `view_system_logs` - View system logs
- `manage_notifications` - Manage notifications

### File Management
- `excel_import_access` - Excel import functionality
- `file_upload_access` - File upload capabilities

## 🔧 Advanced Features

### 1. Permission Override Management

```python
# Grant temporary permission
UserPermissionOverride.objects.create(
    user=staff_user,
    permission=view_reports_perm,
    granted=True,
    granted_by=manager_user,
    reason='Special project access',
    expires_at=timezone.now() + timedelta(days=7)
)

# Deny permission
UserPermissionOverride.objects.create(
    user=manager_user,
    permission=delete_tasks_perm,
    granted=False,
    granted_by=superuser,
    reason='Temporary restriction'
)
```

### 2. Automatic Cleanup

The system automatically:
- ✅ Removes expired permission overrides
- ✅ Handles missing permissions gracefully
- ✅ Logs permission checks for auditing

### 3. Delegation System

Users can delegate permissions they have with `can_delegate=True`:

```python
# Check if user can delegate permission
if user.profile.can_delegate_permission('add_tasks'):
    # User can grant this permission to others

# Get all delegatable permissions
delegatable = user.profile.get_delegatable_permissions()
```

## 🛡️ Security Features

### 1. Default Deny
- All permissions default to **denied**
- Explicit permission grants required
- No accidental access

### 2. Permission Precedence
1. **User Overrides** (highest priority)
2. **Role Permissions** (default)
3. **Default Deny** (fallback)

### 3. Audit Trail
- All permission overrides are logged
- Tracks who granted permissions and when
- Expiration dates for temporary access

### 4. Superuser Bypass
- Superusers bypass all permission checks
- Always have full access
- Can manage all permissions

## 📈 Performance Considerations

### 1. Efficient Queries
- Uses `select_related` for permission lookups
- Caches role permissions
- Minimal database hits per request

### 2. Permission Caching
- Role permissions are cached
- User overrides checked on-demand
- Expired overrides cleaned up automatically

### 3. Database Optimization
- Indexed foreign keys
- Unique constraints prevent duplicates
- Efficient permission lookups

## 🔍 Monitoring and Debugging

### 1. Permission Checking
```python
# Debug user permissions
user.profile.get_all_permissions()
user.profile.get_delegatable_permissions()

# Check specific permission
user.profile.has_permission('view_tasks')
```

### 2. API Testing
```bash
# Test with different users
curl -H "Authorization: Token <token>" http://localhost:8000/api/tasks/
```

### 3. Logging
The system logs:
- Permission check results
- Override creations and deletions
- Expired override cleanup

## 🚨 Error Handling

### 1. Graceful Degradation
- Missing permissions return `False`
- Invalid permission names are ignored
- Database errors are caught and logged

### 2. API Responses
- `401 Unauthorized` - No authentication
- `403 Forbidden` - Insufficient permissions
- `200 OK` - Permission granted

### 3. Edge Cases
- Users without profiles are denied access
- Expired overrides are automatically cleaned up
- Inactive permissions are ignored

## 📝 Best Practices

### 1. Permission Naming
- Use descriptive names: `view_tasks`, `add_properties`
- Follow consistent patterns: `action_resource`
- Use lowercase with underscores

### 2. Role Design
- Keep roles simple and clear
- Avoid too many roles
- Use overrides for exceptions

### 3. Security
- Regularly audit permissions
- Remove unused overrides
- Monitor permission changes

## 🎯 Future Enhancements

### 1. Planned Features
- Permission groups for easier management
- Time-based permission scheduling
- Permission request workflow
- Advanced audit logging

### 2. Integration
- LDAP/AD integration
- SSO compatibility
- Mobile app permissions
- API rate limiting based on permissions

## 📚 Related Documentation

- [Permission System Implementation](PERMISSION_SYSTEM_IMPLEMENTATION.md)
- [Dynamic DRF Permissions](DYNAMIC_DRF_PERMISSIONS.md)
- [Manager Admin Fix](MANAGER_ADMIN_FIX.md)
- [Complete User Admin Fix](COMPLETE_USER_ADMIN_FIX.md)

---

**Last Updated**: September 1, 2025  
**Version**: 1.0  
**Status**: ✅ Production Ready
