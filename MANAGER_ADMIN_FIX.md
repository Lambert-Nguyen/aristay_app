# Manager Admin "Add User" Fix

## Problem Identified

The same `KeyError: 'password1'` error was occurring in the **Manager Admin** (`/manager/auth/user/add/`) even after fixing the superuser admin. This happened because there are **two separate admin configurations**:

1. **Superuser Admin** (`/admin/`) - Uses `AriStayUserAdmin` class
2. **Manager Admin** (`/manager/`) - Uses `UserManagerAdmin` class

## Root Cause

The `UserManagerAdmin` class in `api/managersite.py` had the same issue:
- `exclude = ('password',)` excluded password fields  
- **Missing `add_fieldsets`** configuration for the "Add User" form
- Django's UserAdmin expects `password1` and `password2` fields when adding users

## Solution Applied

Added the missing `add_fieldsets` configuration to the `UserManagerAdmin` class in `api/managersite.py`:

```python
class UserManagerAdmin(ManagerPermissionMixin, DjangoUserAdmin):
    # ... existing configuration ...
    
    # Add fieldsets for creating new users (includes password fields)
    add_fieldsets = (
        (None, {
            'classes': ('wide',),
            'fields': ('username', 'password1', 'password2'),
        }),
        ('Personal info', {'fields': ('first_name', 'last_name', 'email')}),
        ('Permissions', {
            'fields': ('is_active', 'is_staff', 'groups'),
            'classes': ('collapse',)
        }),
    )
```

## Two Admin Systems

### Superuser Admin (`/admin/`)
- **Class**: `AriStayUserAdmin` in `api/admin.py`
- **Access**: Superusers only
- **Permissions**: Full user management capabilities
- **Status**: ✅ Fixed (previously)

### Manager Admin (`/manager/`)
- **Class**: `UserManagerAdmin` in `api/managersite.py`
- **Access**: Managers and superusers
- **Permissions**: Limited user management (no superuser/staff modification)
- **Status**: ✅ Fixed (now)

## How the Fix Works

### For Adding Users
- **`add_fieldsets`**: Used when creating new users (includes password1, password2)
- Django automatically switches to this fieldset for the "Add User" form

### For Editing Users  
- **`fieldsets`**: Used when editing existing users (excludes password fields)
- Password changes handled through separate views/actions

## Testing

1. **Manager Admin**: Navigate to `http://127.0.0.1:8000/manager/`
2. **Login**: Use manager account credentials
3. **Users Section**: Go to Users → Add User
4. **Form**: Should now load without errors and include username/password fields
5. **Save**: User creation should work successfully

## Verification

Both admin systems now properly handle user creation:

✅ **Superuser Admin** (`/admin/auth/user/add/`) - Working  
✅ **Manager Admin** (`/manager/auth/user/add/`) - Fixed  

## Files Modified

1. **`api/admin.py`**: Added `add_fieldsets` to `AriStayUserAdmin`
2. **`api/managersite.py`**: Added `add_fieldsets` to `UserManagerAdmin`

Both admin interfaces now have consistent behavior for user creation while maintaining their respective permission restrictions.
