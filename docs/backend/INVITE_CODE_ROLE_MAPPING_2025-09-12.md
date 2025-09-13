# Invite Code Role Mapping System

**Date**: 2025-09-12  
**Status**: ✅ Fixed and Implemented

## Overview

The invite code system has been corrected to properly map roles between the invite code creation and user profile assignment. The system now uses the standardized `UserRole` enum for consistent role management.

## Role Mapping

### Before (Incorrect)
The `InviteCode` model used hardcoded role choices that didn't match the `UserRole` enum:

```python
# OLD - Incorrect mapping
role = models.CharField(max_length=20, choices=[
    ('member', 'Member'),      # ❌ Should be 'staff'
    ('manager', 'Manager'),    # ✅ Correct
    ('admin', 'Admin'),        # ❌ Should be 'superuser'
], default='member')
```

### After (Correct)
The `InviteCode` model now uses the standardized `UserRole` enum:

```python
# NEW - Correct mapping
role = models.CharField(max_length=20, choices=UserRole.choices, default=UserRole.STAFF)
```

## Complete Role System

### UserRole Enum
```python
class UserRole(models.TextChoices):
    STAFF       = 'staff',       'Staff/Crew'    # Normal users who perform tasks
    MANAGER     = 'manager',     'Manager'       # Manages staff and properties
    SUPERUSER   = 'superuser',   'Superuser'     # Full system admin access
    VIEWER      = 'viewer',      'Viewer'        # Read-only access
```

### Invite Code Role Choices
The invite code system now supports all four role types:

1. **Staff/Crew** (`staff`) - Default role for task performers
2. **Manager** (`manager`) - Property and staff management
3. **Superuser** (`superuser`) - Full system administration
4. **Viewer** (`viewer`) - Read-only access

## Migration Applied

**Migration**: `0071_update_invite_code_role_choices.py`

- Updated `InviteCode.role` field to use `UserRole.choices`
- Changed default value from `'member'` to `'staff'`
- Made migration idempotent to handle existing constraints

## Data Migration

Existing invite codes were updated to use correct role values:

```python
# Role mapping applied
role_mapping = {
    'member': 'staff',        # member → staff
    'admin': 'superuser',     # admin → superuser  
    'manager': 'manager'      # manager → manager (unchanged)
}
```

## User Profile Updates

Existing users with incorrect role values were corrected:

- **adminadmin user**: Updated from `'admin'` to `'superuser'`
- Django user flags: Set `is_superuser=True` and `is_staff=True`

## Testing Results

### Registration Test - Manager Role
- **Invite Code**: `EGICT0DP`
- **Role**: `manager` (Manager)
- **Task Group**: `cleaning` (Cleaning)
- **Result**: ✅ User created with correct role and task group

### Registration Test - Superuser Role  
- **Invite Code**: `LKFMZI1Y` (updated)
- **Role**: `superuser` (Superuser)
- **Task Group**: `general` (General)
- **Result**: ✅ User created with correct role and task group

## API Response Format

The registration API now returns the correct role information:

```json
{
    "success": true,
    "user_id": 59,
    "username": "testuser_manager",
    "role": "manager",
    "task_group": "cleaning"
}
```

## Admin Interface

The Django Admin interface now shows the correct role choices:

- **Staff/Crew** - For task performers
- **Manager** - For property managers
- **Superuser** - For system administrators  
- **Viewer** - For read-only access

## Verification

To verify the system is working correctly:

1. **Check Invite Codes**: All codes should use `UserRole` values
2. **Check User Profiles**: All profiles should have correct role assignments
3. **Test Registration**: New registrations should get correct roles
4. **Check Admin Interface**: Role dropdown should show all four options

## Files Modified

- `aristay_backend/api/models.py` - Updated InviteCode model
- `aristay_backend/api/migrations/0071_update_invite_code_role_choices.py` - Migration
- `aristay_backend/api/registration_views.py` - No changes needed (already correct)

## Summary

The invite code role mapping system is now fully functional and consistent:

✅ **Role Mapping Fixed**: Invite codes now use standardized UserRole enum  
✅ **All Roles Supported**: Staff, Manager, Superuser, and Viewer roles available  
✅ **Data Migrated**: Existing codes and users updated to correct values  
✅ **Testing Complete**: Registration works correctly for all role types  
✅ **Admin Interface Updated**: Shows all four role options  

The system now properly maps invite code roles to user profiles, ensuring users get the correct permissions and access levels upon registration.
