# Booking Import Permission Fix - 2025-10-13

## Issue Summary
**Issue:** Crew/staff role users were able to access the "import bookings" feature despite security requirements limiting this to superuser and manager roles only.

**Severity:** High - Security vulnerability allowing unauthorized data import operations

**Status:** ✅ RESOLVED

## Root Cause

The enhanced Excel import views were using the `@staff_or_perm('manage_bookings')` decorator:

```python
@staff_or_perm('manage_bookings')
def enhanced_excel_import_view(request):
    ...
```

### Problems Identified

1. **Incorrect Decorator Usage**: The `staff_or_perm` decorator allows access to ANY user with `is_staff=True` set in Django's User model (line 38-40 in decorators.py):
   ```python
   if user.is_staff:
       logger.debug("Legacy is_staff access granted to %s for %s", user.username, permission_name)
       return view_func(request, *args, **kwargs)
   ```

2. **Non-existent Permission**: The permission `manage_bookings` does not exist in the permission system defined in `setup_permissions.py`. The correct permission is `import_bookings`.

3. **Inconsistent with Legacy Implementation**: Legacy excel import views correctly use `@user_passes_test(is_superuser_or_manager)` which properly checks for superuser or manager role.

## Solution Applied

### Code Changes

Replaced the `@staff_or_perm('manage_bookings')` decorator with `@user_passes_test(is_superuser_or_manager)` on all enhanced excel import views:

**File:** `aristay_backend/api/views.py`

1. **enhanced_excel_import_view()** (line ~2212)
   - Before: `@staff_or_perm('manage_bookings')`
   - After: `@user_passes_test(is_superuser_or_manager)`

2. **enhanced_excel_import_api()** (line ~2294)
   - Before: `@staff_or_perm('manage_bookings')`
   - After: `@user_passes_test(is_superuser_or_manager)`

3. **preview_conflict_resolution()** (line ~2117)
   - Before: `@staff_or_perm('manage_bookings')`
   - After: `@user_passes_test(is_superuser_or_manager)`

4. **quick_resolve_conflict()** (line ~2165)
   - Before: `@staff_or_perm('manage_bookings')`
   - After: `@user_passes_test(is_superuser_or_manager)`

### Helper Function

All views now use the existing `is_superuser_or_manager()` helper function:

```python
def is_superuser_or_manager(user):
    """Check if user is superuser or manager"""
    return user.is_superuser or (hasattr(user, 'profile') and user.profile.role in [UserRole.MANAGER, UserRole.SUPERUSER])
```

This function:
- ✅ Returns `True` for superusers
- ✅ Returns `True` for users with manager role in their profile
- ✅ Returns `False` for staff/crew users

## Test Coverage

### New Test Suite
**File:** `tests/security/test_excel_import_permissions.py`

Comprehensive test coverage including:

1. **Unit Tests** - Verify the `is_superuser_or_manager()` function:
   - ✅ `test_superuser_passes_is_superuser_or_manager_check`
   - ✅ `test_manager_passes_is_superuser_or_manager_check`
   - ✅ `test_crew_fails_is_superuser_or_manager_check`

2. **Integration Tests** - Verify actual view access:
   - ✅ `test_superuser_can_access_enhanced_excel_import_view`
   - ✅ `test_manager_can_access_enhanced_excel_import_view`
   - ✅ `test_crew_cannot_access_enhanced_excel_import_view`
   - ✅ `test_superuser_can_access_enhanced_excel_import_api`
   - ✅ `test_manager_can_access_enhanced_excel_import_api`
   - ✅ `test_crew_cannot_access_enhanced_excel_import_api`
   - ✅ `test_legacy_excel_import_view_has_correct_permissions`

**Test Results:** All 10 tests passing ✅

### Running Tests

```bash
cd /home/runner/work/aristay_app/aristay_app
export DATABASE_URL="sqlite:///db.sqlite3"
python -m pytest tests/security/test_excel_import_permissions.py -v
```

## Verification

### Permission Matrix Compliance

| Feature | Superuser | Manager | Staff/Crew |
|---------|-----------|---------|------------|
| Import Bookings | ✅ Yes | ✅ Yes | ❌ **NO** (Fixed) |

This now matches the documented permission matrix in `docs/USER_WORKFLOWS.md`.

### Backward Compatibility

- ✅ **Superuser access**: Unchanged - still has full access
- ✅ **Manager access**: Unchanged - still has access to import bookings
- ✅ **Staff/crew access**: **FIXED** - now properly denied access
- ✅ **Legacy import views**: No changes - already had correct permissions
- ✅ **API endpoints**: Protected with same security

## Security Impact

### Before Fix
- 🔴 **Vulnerability**: Staff/crew users with `is_staff=True` could import bookings
- 🔴 **Data Integrity Risk**: Unauthorized users could modify booking data
- 🔴 **Audit Trail Risk**: Incorrect attribution of import operations

### After Fix
- ✅ **Secure**: Only superuser and manager roles can access import features
- ✅ **Data Integrity**: Protected - only authorized roles can import bookings
- ✅ **Audit Trail**: Accurate - only legitimate managers/admins recorded
- ✅ **Consistent**: Matches system-wide permission requirements

## Related Files

### Modified Files
1. `aristay_backend/api/views.py` - Fixed decorator usage on 4 views
2. `tests/security/test_excel_import_permissions.py` - New comprehensive test suite

### Reference Files
1. `aristay_backend/api/decorators.py` - Decorator definitions
2. `aristay_backend/api/models.py` - User roles and Profile model
3. `aristay_backend/api/management/commands/setup_permissions.py` - Permission definitions
4. `docs/USER_WORKFLOWS.md` - Permission matrix documentation
5. `docs/features/EXCEL_IMPORT_FEATURE.md` - Feature documentation

## Documentation Updates

The system documentation already correctly specified that only superuser and manager roles should have access to import bookings:

- ✅ `docs/USER_WORKFLOWS.md` - Permission matrix shows "Import Bookings" as Superuser ✅ and Manager ✅ only
- ✅ `docs/features/EXCEL_IMPORT_FEATURE.md` - States "Staff: No access to import features"

No documentation updates needed - code now matches documentation.

## Recommendations

1. **Future Decorator Usage**: 
   - Use `@perm_required('import_bookings')` for new import-related views to leverage the dynamic permission system
   - Avoid using `@staff_or_perm()` with non-existent permissions
   - Prefer role-based decorators (`@manager_required`, `@role_required()`) for role-specific features

2. **Permission Audits**:
   - Regular audits of decorator usage to ensure correct permission checks
   - Verify all booking management features use appropriate permission checks

3. **Testing Requirements**:
   - Add permission tests for all new security-sensitive features
   - Test both positive (authorized) and negative (unauthorized) access scenarios

## References

- **Issue:** "Investigate Crew role can import bookings despite restriction to superuser/manager"
- **PR:** copilot/fix-import-bookings-permissions
- **Commit:** 783be24 "Fix excel import permissions to restrict access to superuser/manager only"
- **Date:** 2025-10-13
