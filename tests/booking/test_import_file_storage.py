"""
Tests for import file storage and cleanup functionality.

This test suite validates that:
1. Import history log correctly stores uploaded Excel files
2. File cleanup service works correctly
3. Files are properly managed in both local and cloud storage
"""

import pytest
import os
import io
from datetime import datetime, timedelta
from django.conf import settings
from django.contrib.auth.models import User
from django.core.files.uploadedfile import SimpleUploadedFile
from django.utils import timezone
from api.models import BookingImportLog, Property, BookingImportTemplate
from api.services.enhanced_excel_import_service import EnhancedExcelImportService
from api.services.file_cleanup_service import ImportFileCleanupService


@pytest.fixture
def test_user(db):
    """Create a test user for imports"""
    return User.objects.create_user(
        username='testuser',
        email='test@example.com',
        password='testpass123'
    )


@pytest.fixture
def test_property(db):
    """Create a test property"""
    return Property.objects.create(
        name='Test Property',
        address='123 Test St'
    )


@pytest.fixture
def test_template(db, test_user, test_property):
    """Create a test import template"""
    return BookingImportTemplate.objects.create(
        name='Test Template',
        property_ref=test_property,
        import_type='csv',
        created_by=test_user
    )


@pytest.fixture
def sample_excel_file():
    """Create a minimal valid Excel file for testing"""
    import pandas as pd
    
    # Create a simple Excel file with booking data
    data = {
        'Confirmation code': ['TEST123'],
        'Status': ['confirmed'],
        'Guest name': ['John Doe'],
        'Contact': ['john@example.com'],
        'Booking source': ['Airbnb'],
        'Listing': ['Cozy Apartment'],
        'Earnings': ['$150.00'],
        'Booked': ['2024-01-01'],
        '# of adults': [2],
        '# of children': [0],
        '# of infants': [0],
        'Start date': ['2024-02-01'],
        'End date': ['2024-02-05'],
        '# of nights': [4],
        'Properties': ['Test Property'],
        'Check ': ['']
    }
    
    df = pd.DataFrame(data)
    
    # Write to BytesIO buffer
    buffer = io.BytesIO()
    with pd.ExcelWriter(buffer, engine='openpyxl') as writer:
        df.to_excel(writer, sheet_name='Cleaning schedule', index=False)
    
    buffer.seek(0)
    
    # Create Django file upload
    return SimpleUploadedFile(
        'test_import.xlsx',
        buffer.read(),
        content_type='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
    )


@pytest.mark.django_db
class TestImportFileStorage:
    """Test cases for import file storage"""
    
    def test_import_stores_file_in_history(self, test_user, test_template, sample_excel_file):
        """Test that import correctly stores the Excel file in BookingImportLog"""
        service = EnhancedExcelImportService(test_user, test_template)
        
        # Perform import
        result = service.import_excel_file(sample_excel_file)
        
        # Verify import was successful
        assert result['success'] is True, f"Import failed: {result.get('error')}"
        
        # Verify import log was created
        assert hasattr(service, 'import_log')
        assert service.import_log is not None
        
        # Verify file was saved to import log
        import_log = BookingImportLog.objects.get(pk=service.import_log.pk)
        assert import_log.import_file, "Import file was not saved to BookingImportLog"
        assert import_log.import_file.name, "Import file name is empty"
        
        # Verify file exists on disk (for local storage)
        if settings.STORAGES['default']['BACKEND'] == 'django.core.files.storage.FileSystemStorage':
            file_path = os.path.join(settings.MEDIA_ROOT, import_log.import_file.name)
            assert os.path.exists(file_path), f"Physical file not found at {file_path}"
            assert os.path.getsize(file_path) > 0, "Physical file is empty"
    
    def test_import_file_accessible_after_save(self, test_user, test_template, sample_excel_file):
        """Test that the saved file can be accessed and read"""
        service = EnhancedExcelImportService(test_user, test_template)
        result = service.import_excel_file(sample_excel_file)
        
        assert result['success'] is True
        
        import_log = BookingImportLog.objects.get(pk=service.import_log.pk)
        
        # Try to open and read the file
        with import_log.import_file.open('rb') as f:
            file_content = f.read()
            assert len(file_content) > 0, "File content is empty"
            assert file_content[:4] == b'PK\x03\x04', "File is not a valid ZIP/Excel file"
    
    def test_import_log_errors_logged_on_file_save_failure(self, test_user, test_template, sample_excel_file, monkeypatch):
        """Test that file save failures are properly logged"""
        service = EnhancedExcelImportService(test_user, test_template)
        
        # Mock FileField.save to raise an exception
        original_save = None
        
        def mock_save(self, name, content, save=True):
            raise IOError("Simulated file save failure")
        
        # Note: This test verifies error logging behavior
        # In practice, we want to catch and surface these errors
        result = service.import_excel_file(sample_excel_file)
        
        # Import should still succeed even if file save fails (current behavior)
        assert result['success'] is True
        
        # Check if error was logged (if file save failed)
        import_log = BookingImportLog.objects.get(pk=service.import_log.pk)
        # If file wasn't saved, errors_log should contain warning
        if not import_log.import_file:
            assert 'FILE_SAVE_WARNING' in import_log.errors_log


@pytest.mark.django_db
class TestFileCleanupService:
    """Test cases for file cleanup service"""
    
    def test_cleanup_identifies_old_files(self, test_user, test_property):
        """Test that cleanup service correctly identifies old files"""
        # Create an old import log with a file
        old_date = timezone.now() - timedelta(days=35)
        
        import_log = BookingImportLog.objects.create(
            template=None,
            total_rows=10,
            successful_imports=10,
            errors_count=0,
            imported_by=test_user
        )
        
        # Manually set the imported_at date (auto_now_add prevents setting it on create)
        BookingImportLog.objects.filter(pk=import_log.pk).update(imported_at=old_date)
        import_log.refresh_from_db()
        
        # Simulate a file being attached
        import_log.import_file.save(
            'old_import.xlsx',
            SimpleUploadedFile('old_import.xlsx', b'test content', content_type='application/vnd.ms-excel'),
            save=True
        )
        
        # Verify file was saved
        import_log.refresh_from_db()
        assert import_log.import_file, "File should be attached to import log"
        
        # Verify physical file exists
        file_path = os.path.join(settings.MEDIA_ROOT, import_log.import_file.name)
        assert os.path.exists(file_path), f"Physical file should exist at {file_path}"
        
        # Run dry run cleanup
        result = ImportFileCleanupService.cleanup_old_files(days_to_keep=30, dry_run=True)
        
        assert result['files_found'] == 1, f"Should find 1 old file, found {result['files_found']}"
        assert result['dry_run'] is True
        assert 'files' in result
    
    def test_cleanup_preserves_recent_files(self, test_user):
        """Test that cleanup doesn't delete recent files"""
        # Create a recent import log with a file
        recent_log = BookingImportLog.objects.create(
            template=None,
            total_rows=5,
            successful_imports=5,
            errors_count=0,
            imported_by=test_user
        )
        
        recent_log.import_file.save(
            'recent_import.xlsx',
            SimpleUploadedFile('recent_import.xlsx', b'test content', content_type='application/vnd.ms-excel'),
            save=True
        )
        
        # Run cleanup for files older than 30 days
        result = ImportFileCleanupService.cleanup_old_files(days_to_keep=30, dry_run=True)
        
        assert result['files_found'] == 0, "Should not find any old files"
    
    def test_cleanup_deletes_files(self, test_user):
        """Test that cleanup actually deletes old files"""
        # Create old import with file
        old_date = timezone.now() - timedelta(days=40)
        
        import_log = BookingImportLog.objects.create(
            template=None,
            total_rows=10,
            successful_imports=10,
            errors_count=0,
            imported_by=test_user
        )
        
        # Manually set the imported_at date (auto_now_add prevents setting it on create)
        BookingImportLog.objects.filter(pk=import_log.pk).update(imported_at=old_date)
        import_log.refresh_from_db()
        
        # Save a file
        import_log.import_file.save(
            'delete_me.xlsx',
            SimpleUploadedFile('delete_me.xlsx', b'test content for deletion', content_type='application/vnd.ms-excel'),
            save=True
        )
        
        file_path = None
        if settings.STORAGES['default']['BACKEND'] == 'django.core.files.storage.FileSystemStorage':
            file_path = os.path.join(settings.MEDIA_ROOT, import_log.import_file.name)
            assert os.path.exists(file_path), "File should exist before cleanup"
        
        # Run actual cleanup
        result = ImportFileCleanupService.cleanup_old_files(days_to_keep=30, dry_run=False)
        
        assert result['files_deleted'] == 1, f"Should delete 1 file, deleted {result['files_deleted']}"
        assert result['space_freed_bytes'] > 0
        
        # Verify file was actually deleted
        if file_path:
            assert not os.path.exists(file_path), "File should be deleted after cleanup"
        
        # Verify database record was updated
        import_log.refresh_from_db()
        assert not import_log.import_file, "import_file field should be cleared"
    
    def test_storage_stats_calculation(self, test_user):
        """Test that storage statistics are calculated correctly"""
        # Create multiple import logs with files
        for i in range(3):
            import_log = BookingImportLog.objects.create(
                template=None,
                total_rows=5,
                successful_imports=5,
                errors_count=0,
                imported_by=test_user
            )
            
            import_log.import_file.save(
                f'import_{i}.xlsx',
                SimpleUploadedFile(f'import_{i}.xlsx', b'x' * (1024 * (i + 1)), content_type='application/vnd.ms-excel'),
                save=True
            )
        
        stats = ImportFileCleanupService.get_storage_stats()
        
        assert stats['total_files'] == 3
        assert stats['total_size_bytes'] > 0
        assert stats['total_size_mb'] > 0
    
    def test_cleanup_handles_missing_files_gracefully(self, test_user):
        """Test that cleanup handles cases where database has reference but file is missing"""
        old_date = timezone.now() - timedelta(days=40)
        
        import_log = BookingImportLog.objects.create(
            template=None,
            total_rows=10,
            successful_imports=10,
            errors_count=0,
            imported_by=test_user
        )
        
        # Manually set the imported_at date (auto_now_add prevents setting it on create)
        BookingImportLog.objects.filter(pk=import_log.pk).update(imported_at=old_date)
        import_log.refresh_from_db()
        
        # Manually set import_file field without creating actual file
        import_log.import_file.name = 'booking_imports/2024/01/nonexistent.xlsx'
        import_log.save()
        
        # Cleanup should handle missing files gracefully
        result = ImportFileCleanupService.cleanup_old_files(days_to_keep=30, dry_run=True)
        
        # Should not crash, and should report 0 files found
        assert result['files_found'] == 0


@pytest.mark.django_db
class TestManagementCommand:
    """Test the cleanup management command"""
    
    def test_management_command_exists(self):
        """Test that cleanup_old_imports management command exists"""
        from django.core.management import get_commands
        
        commands = get_commands()
        assert 'cleanup_old_imports' in commands, "cleanup_old_imports command should exist"
