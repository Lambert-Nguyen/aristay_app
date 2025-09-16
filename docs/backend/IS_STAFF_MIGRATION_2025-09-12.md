# Migration from is_staff to Dynamic Permission System

**Date**: 2025-09-12  
**Status**: ✅ Completed

## Overview

Successfully migrated the entire codebase from using Django's `is_staff` flag for business permissions to our dynamic permission system based on `Profile.role`. This eliminates confusion between Django admin access and business role permissions.

## What Was Changed

### 1. **Registration Views** (`api/registration_views.py`)
- **Before**: `if not request.user.is_staff:`
- **After**: `if not (request.user.is_superuser or (hasattr(request.user, 'profile') and request.user.profile.role in ['manager', 'superuser'])):`

### 2. **Serializers** (`api/serializers.py`)
- **UserSerializer**: Removed `is_staff` from fields, kept `is_superuser` for Django admin access
- **AdminUserAdminSerializer**: Removed `is_staff` field
- **AdminUserCreateSerializer**: Replaced `is_staff` boolean with `role` choice field

### 3. **Templates**
- **staff/dashboard.html**: `user.is_staff` → `user.profile.role in 'manager,superuser'`
- **portal/base.html**: `user.is_staff` → `user.profile.role in 'manager,superuser'`
- **admin/base_site.html**: `user.is_staff` → `user.profile.role == 'manager'`
- **admin/index.html**: `user.is_staff` → `user.profile.role in 'manager,superuser'`

### 4. **Admin Interface** (`api/admin.py`)
- **list_display**: Replaced `is_staff` with `get_profile_role`
- **list_filter**: Removed `is_staff` filter
- **Sync logic**: Removed `is_staff` sync, kept only `is_superuser` sync
- **Form restrictions**: Removed `is_staff` field restrictions

### 5. **Authentication Views** (`api/auth_views.py`)
- **Login logging**: Replaced `is_staff` with `role` from profile
- **JWT tokens**: Replaced `is_staff` with `role` from profile

### 6. **Management Commands**
- **seed_test_data.py**: Replaced `is_staff` with `role` in user definitions
- **create_sample_checklists_optimized.py**: Removed `is_staff` from admin user creation

## Current Permission System

### Role Hierarchy
```python
class UserRole(models.TextChoices):
    STAFF       = 'staff',       'Staff/Crew'    # Task performers
    MANAGER     = 'manager',     'Manager'       # Property managers
    SUPERUSER   = 'superuser',   'Superuser'     # System administrators
    VIEWER      = 'viewer',      'Viewer'        # Read-only access
```

### Permission Checks
```python
# Manager-level access
if user.is_superuser or (hasattr(user, 'profile') and user.profile.role in ['manager', 'superuser']):
    # Allow access

# Superuser-only access
if user.is_superuser:
    # Allow access

# Role-specific access
if user.profile.role == 'manager':
    # Manager-specific features
```

## Django Admin Access

- **`is_superuser`**: Controls Django admin access (kept for Django admin functionality)
- **`is_staff`**: Removed from business logic (was causing confusion)
- **`Profile.role`**: Controls business permissions and UI access

## Testing Results

✅ **Permission System**: All role-based checks work correctly  
✅ **Admin Access**: Superusers can access Django admin  
✅ **Manager Access**: Managers can access manager features but not superuser features  
✅ **Staff Access**: Staff users have appropriate limited access  
✅ **Templates**: All UI elements show/hide based on profile role  
✅ **API Responses**: JWT tokens include correct role information  

## Files Modified

### Core Files
- `aristay_backend/api/registration_views.py` - Permission checks
- `aristay_backend/api/serializers.py` - API serialization
- `aristay_backend/api/admin.py` - Admin interface
- `aristay_backend/api/auth_views.py` - Authentication

### Templates
- `aristay_backend/api/templates/staff/dashboard.html`
- `aristay_backend/api/templates/portal/base.html`
- `aristay_backend/api/templates/admin/base_site.html`
- `aristay_backend/api/templates/admin/index.html`

### Management Commands
- `aristay_backend/api/management/commands/seed_test_data.py`
- `aristay_backend/api/management/commands/create_sample_checklists_optimized.py`

## Benefits

1. **Clear Separation**: Django admin access (`is_superuser`) vs business permissions (`Profile.role`)
2. **No Confusion**: Eliminated `is_staff` ambiguity between Django and business logic
3. **Consistent**: All permission checks now use the same `Profile.role` system
4. **Maintainable**: Single source of truth for business permissions
5. **Extensible**: Easy to add new roles without touching Django user model

## Migration Notes

- **Existing Users**: All existing users maintain their current permissions
- **Backward Compatibility**: `is_superuser` still controls Django admin access
- **Profile Creation**: Users without profiles get default `staff` role
- **API Changes**: JWT tokens now include `role` instead of `is_staff`

## Verification

To verify the migration was successful:

1. **Check User Roles**: All users should have appropriate `Profile.role` values
2. **Test Permissions**: Manager users can access manager features but not superuser features
3. **Check Templates**: UI elements show/hide based on profile role
4. **Verify API**: JWT tokens include correct role information
5. **Admin Access**: Only superusers can access Django admin

The system now has a clean, consistent permission model that separates Django admin access from business role permissions.
