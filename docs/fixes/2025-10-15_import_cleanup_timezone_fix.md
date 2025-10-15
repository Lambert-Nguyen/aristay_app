# Fix: Import History Log and File Cleanup Service

**Date**: 2025-10-15  
**Issue**: Import history log does not store uploaded Excel files and file clean up service is unusable  
**Status**: ✅ FIXED

## Problem Summary

The file cleanup service was completely broken and unable to find or delete old import files. This was causing:
1. Storage bloat from accumulating import files
2. Inability to manage disk space
3. Confusion about whether imports were storing files properly

## Root Cause

The cleanup service had a **critical timezone bug**:

```python
# BEFORE (BROKEN):
cutoff_date = datetime.now() - timedelta(days=days_to_keep)
```

This created a **naive datetime**, but Django's `BookingImportLog.imported_at` field uses `auto_now_add=True`, which stores **timezone-aware datetimes**. Python cannot compare naive and timezone-aware datetimes, causing the cleanup query to fail silently and return zero results.

## Files Fixed

### 1. `api/services/file_cleanup_service.py`
- **Line 6**: Added `from django.utils import timezone`
- **Line 33**: Changed `datetime.now()` to `timezone.now()`

```python
# FIXED:
cutoff_date = timezone.now() - timedelta(days=days_to_keep)
```

### 2. `api/management/commands/cleanup_old_imports.py`
- **Line 15**: Added `from django.utils import timezone`
- **Line 64**: Changed `datetime.now()` to `timezone.now()`

## Verification

Added comprehensive test suite (`tests/booking/test_import_file_storage.py`) with 9 tests:

### Import File Storage Tests (3 tests)
- ✅ `test_import_stores_file_in_history` - Verifies files are saved
- ✅ `test_import_file_accessible_after_save` - Verifies files can be read
- ✅ `test_import_log_errors_logged_on_file_save_failure` - Verifies error handling

### File Cleanup Tests (5 tests)
- ✅ `test_cleanup_identifies_old_files` - Verifies old files are found
- ✅ `test_cleanup_preserves_recent_files` - Verifies recent files are kept
- ✅ `test_cleanup_deletes_files` - Verifies files are actually deleted
- ✅ `test_storage_stats_calculation` - Verifies stats calculation
- ✅ `test_cleanup_handles_missing_files_gracefully` - Verifies error handling

### Management Command Test (1 test)
- ✅ `test_management_command_exists` - Verifies command is available

## Running Tests

```bash
# Run all import/cleanup tests
cd /home/runner/work/aristay_app/aristay_app
DATABASE_URL="sqlite:///tmp/test_db.sqlite3" python -m pytest tests/booking/test_import_file_storage.py -v

# Run specific test
DATABASE_URL="sqlite:///tmp/test_db.sqlite3" python -m pytest tests/booking/test_import_file_storage.py::TestFileCleanupService::test_cleanup_identifies_old_files -v
```

## Usage

### Via Python Service
```python
from api.services.file_cleanup_service import ImportFileCleanupService

# Dry run to see what would be deleted
result = ImportFileCleanupService.cleanup_old_files(days_to_keep=30, dry_run=True)
print(f"Would delete {result['files_found']} files ({result['total_size_mb']} MB)")

# Actually delete old files
result = ImportFileCleanupService.cleanup_old_files(days_to_keep=30, dry_run=False)
print(f"Deleted {result['files_deleted']} files, freed {result['space_freed_mb']} MB")

# Get storage statistics
stats = ImportFileCleanupService.get_storage_stats()
print(f"Total: {stats['total_files']} files, {stats['total_size_mb']} MB")
```

### Via Management Command
```bash
# Dry run (see what would be deleted)
python manage.py cleanup_old_imports --days 30 --dry-run

# Actually delete files
python manage.py cleanup_old_imports --days 30 --force

# Keep only last 10 imports
python manage.py cleanup_old_imports --keep 10 --force
```

### Via Admin Interface
Navigate to: `/admin/api/bookingimportlog/file-cleanup/`

## Impact

- ✅ File cleanup service now works correctly
- ✅ Import history log confirmed to store files properly (always worked, just cleanup was broken)
- ✅ Management command now functional
- ✅ Admin interface cleanup actions now work
- ✅ Comprehensive test coverage ensures this won't break again

## Notes

1. **Import file storage was never broken** - files were always being saved correctly. The issue was only in the cleanup service.

2. **The timezone bug affected ALL cleanup operations**:
   - Python service calls
   - Management commands
   - Admin actions
   - Cron jobs

3. **This is a common Django pitfall** - always use `timezone.now()` instead of `datetime.now()` when working with Django models that have timezone-aware datetime fields.

4. **No data loss** - all previously imported files are still stored and accessible. The cleanup service can now find and manage them properly.

## Related Files

- `api/services/file_cleanup_service.py` - Main cleanup service
- `api/management/commands/cleanup_old_imports.py` - Management command
- `api/admin_file_cleanup.py` - Admin interface actions
- `scripts/admin/cleanup_cron.py` - Cron job script
- `tests/booking/test_import_file_storage.py` - Test suite
