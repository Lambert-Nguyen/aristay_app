# User Admin "Add User" Fix

## Problem Identified

When clicking "Add User" in the Django admin interface, the following error occurred:

```
KeyError: 'password1'
Traceback (most recent call last):
  ...
  File "/Users/duylam1407/Workspace/SJSU/aristay_app/.venv/lib/python3.13/site-packages/django/contrib/auth/forms.py", line 610, in __init__
    self.fields["password1"].required = False
    ~~~~~~~~~~~^^^^^^^^^^^^^
KeyError: 'password1'
```

## Root Cause

The `AriStayUserAdmin` class in `api/admin.py` had:
- `exclude = ('password',)` which excluded password fields from the form
- **Missing `add_fieldsets`** configuration for the "Add User" form
- Django's UserAdmin expects `password1` and `password2` fields in the add form

## Solution Applied

Added the missing `add_fieldsets` configuration to the `AriStayUserAdmin` class:

```python
class AriStayUserAdmin(DjangoUserAdmin):
    # ... existing configuration ...
    
    # Add fieldsets for creating new users (includes password fields)
    add_fieldsets = (
        (None, {
            'classes': ('wide',),
            'fields': ('username', 'password1', 'password2'),
        }),
        ('Personal info', {'fields': ('first_name', 'last_name', 'email')}),
        ('Permissions', {
            'fields': ('is_active', 'is_staff', 'is_superuser', 'groups', 'user_permissions'),
            'classes': ('collapse',)
        }),
    )
```

## How It Works

- **`fieldsets`**: Used for editing existing users (excludes password fields since they're handled separately)
- **`add_fieldsets`**: Used specifically for adding new users (includes `password1` and `password2` fields)
- Django automatically uses the appropriate fieldset based on whether you're adding or editing

## Result

✅ **Fixed**: "Add User" button now works correctly
✅ **Maintained**: Existing user editing functionality remains unchanged  
✅ **Security**: Password fields are properly handled in both add and edit scenarios

## Testing

1. Navigate to Django admin at `/admin/`
2. Go to Users section
3. Click "Add User" button
4. Form should now load without errors and include username and password fields
5. User creation should work normally

This fix resolves the immediate issue while maintaining all existing functionality and security measures.
