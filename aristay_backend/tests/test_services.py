from django.test import TestCase
from django.contrib.auth.models import User
from django.core.files.uploadedfile import SimpleUploadedFile
from datetime import datetime, date, timedelta
from django.utils import timezone
import io
import json
import pandas as pd

from api.models import Property, Booking, Profile, UserRole
from api.services.excel_import_service import ExcelImportService, EnhancedExcelImportService
from .base import BaseTestCase


class ExcelImportServiceTest(BaseTestCase):
    """Test Excel import service functionality"""
    
    def setUp(self):
        super().setUp()
        self.excel_import_service = ExcelImportService()
        self.enhanced_excel_import_service = EnhancedExcelImportService()
    
    def create_test_excel_file(self, data_rows):
        """Helper method to create a test Excel file"""
        # Create a DataFrame
        df = pd.DataFrame(data_rows)
        
        # Create an in-memory Excel file
        excel_buffer = io.BytesIO()
        with pd.ExcelWriter(excel_buffer, engine='openpyxl') as writer:
            df.to_excel(writer, sheet_name='Bookings', index=False)
        excel_buffer.seek(0)
        
        # Create Django uploaded file
        return SimpleUploadedFile(
            "test_bookings.xlsx",
            excel_buffer.getvalue(),
            content_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
        )
    
    def test_basic_excel_import_success(self):
        """Test successful Excel import with valid data"""
        # Create test data
        test_data = [
            {
                'Property': self.property1.name,
                'Check In': (date.today() + timedelta(days=1)).strftime('%Y-%m-%d'),
                'Check Out': (date.today() + timedelta(days=4)).strftime('%Y-%m-%d'),
                'Guest Name': 'John Doe',
                'Guest Contact': 'john@example.com',
                'Status': 'confirmed'
            },
            {
                'Property': self.property2.name,
                'Check In': (date.today() + timedelta(days=5)).strftime('%Y-%m-%d'),
                'Check Out': (date.today() + timedelta(days=8)).strftime('%Y-%m-%d'),
                'Guest Name': 'Jane Smith',
                'Guest Contact': 'jane@example.com',
                'Status': 'confirmed'
            }
        ]
        
        excel_file = self.create_test_excel_file(test_data)
        
        # Test the import
        result = self.excel_import_service.import_bookings_from_excel(
            excel_file=excel_file,
            property_id=None,  # Auto-detect from file
            user=self.admin_user
        )
        
        self.assertTrue(result['success'])
        self.assertEqual(result['imported_count'], 2)
        self.assertEqual(len(result['errors']), 0)
        
        # Verify bookings were created
        self.assertEqual(Booking.objects.filter(guest_name='John Doe').count(), 1)
        self.assertEqual(Booking.objects.filter(guest_name='Jane Smith').count(), 1)
    
    def test_excel_import_with_invalid_property(self):
        """Test Excel import with invalid property name"""
        test_data = [
            {
                'Property': 'Non-existent Property',
                'Check In': (date.today() + timedelta(days=1)).strftime('%Y-%m-%d'),
                'Check Out': (date.today() + timedelta(days=4)).strftime('%Y-%m-%d'),
                'Guest Name': 'John Doe',
                'Status': 'confirmed'
            }
        ]
        
        excel_file = self.create_test_excel_file(test_data)
        
        result = self.excel_import_service.import_bookings_from_excel(
            excel_file=excel_file,
            property_id=None,
            user=self.admin_user
        )
        
        self.assertFalse(result['success'])
        self.assertEqual(result['imported_count'], 0)
        self.assertGreater(len(result['errors']), 0)
    
    def test_excel_import_with_invalid_dates(self):
        """Test Excel import with invalid date formats"""
        test_data = [
            {
                'Property': self.property1.name,
                'Check In': 'invalid-date',
                'Check Out': '2024-13-45',  # Invalid date
                'Guest Name': 'John Doe',
                'Status': 'confirmed'
            }
        ]
        
        excel_file = self.create_test_excel_file(test_data)
        
        result = self.excel_import_service.import_bookings_from_excel(
            excel_file=excel_file,
            property_id=None,
            user=self.admin_user
        )
        
        self.assertFalse(result['success'])
        self.assertEqual(result['imported_count'], 0)
        self.assertGreater(len(result['errors']), 0)
    
    def test_excel_import_with_overlapping_bookings(self):
        """Test Excel import with overlapping booking dates"""
        # Create existing booking
        existing_booking = Booking.objects.create(
            property=self.property1,
            check_in_date=date.today() + timedelta(days=1),
            check_out_date=date.today() + timedelta(days=5),
            guest_name='Existing Guest',
            status='confirmed'
        )
        
        # Try to import overlapping booking
        test_data = [
            {
                'Property': self.property1.name,
                'Check In': (date.today() + timedelta(days=2)).strftime('%Y-%m-%d'),
                'Check Out': (date.today() + timedelta(days=6)).strftime('%Y-%m-%d'),
                'Guest Name': 'Overlapping Guest',
                'Status': 'confirmed'
            }
        ]
        
        excel_file = self.create_test_excel_file(test_data)
        
        result = self.excel_import_service.import_bookings_from_excel(
            excel_file=excel_file,
            property_id=None,
            user=self.admin_user
        )
        
        # Should detect conflict
        self.assertFalse(result['success'])
        self.assertGreater(len(result['conflicts']), 0)
    
    def test_enhanced_excel_import_with_conflict_resolution(self):
        """Test enhanced Excel import with conflict resolution"""
        # Create existing booking
        existing_booking = Booking.objects.create(
            property=self.property1,
            check_in_date=date.today() + timedelta(days=1),
            check_out_date=date.today() + timedelta(days=5),
            guest_name='Existing Guest',
            status='confirmed'
        )
        
        # Prepare conflicting data
        test_data = [
            {
                'Property': self.property1.name,
                'Check In': (date.today() + timedelta(days=2)).strftime('%Y-%m-%d'),
                'Check Out': (date.today() + timedelta(days=6)).strftime('%Y-%m-%d'),
                'Guest Name': 'New Guest',
                'Status': 'confirmed'
            }
        ]
        
        excel_file = self.create_test_excel_file(test_data)
        
        # First, detect conflicts
        result = self.enhanced_excel_import_service.import_bookings_from_excel(
            excel_file=excel_file,
            property_id=None,
            user=self.admin_user
        )
        
        self.assertFalse(result['success'])
        self.assertGreater(len(result['conflicts']), 0)
        
        # Now resolve conflicts by overwriting
        conflict_resolutions = {
            str(existing_booking.id): 'overwrite'
        }
        
        result = self.enhanced_excel_import_service.resolve_conflicts(
            excel_file=excel_file,
            conflicts=result['conflicts'],
            resolutions=conflict_resolutions,
            user=self.admin_user
        )
        
        self.assertTrue(result['success'])
        self.assertEqual(result['imported_count'], 1)
        
        # Verify the booking was updated
        updated_booking = Booking.objects.get(id=existing_booking.id)
        self.assertEqual(updated_booking.guest_name, 'New Guest')
    
    def test_excel_import_missing_required_fields(self):
        """Test Excel import with missing required fields"""
        test_data = [
            {
                'Property': self.property1.name,
                'Check In': (date.today() + timedelta(days=1)).strftime('%Y-%m-%d'),
                # Missing Check Out date
                'Guest Name': 'John Doe',
                'Status': 'confirmed'
            }
        ]
        
        excel_file = self.create_test_excel_file(test_data)
        
        result = self.excel_import_service.import_bookings_from_excel(
            excel_file=excel_file,
            property_id=None,
            user=self.admin_user
        )
        
        self.assertFalse(result['success'])
        self.assertEqual(result['imported_count'], 0)
        self.assertGreater(len(result['errors']), 0)
    
    def test_excel_import_with_different_sheet_names(self):
        """Test Excel import with different sheet names"""
        test_data = [
            {
                'Property': self.property1.name,
                'Check In': (date.today() + timedelta(days=1)).strftime('%Y-%m-%d'),
                'Check Out': (date.today() + timedelta(days=4)).strftime('%Y-%m-%d'),
                'Guest Name': 'John Doe',
                'Status': 'confirmed'
            }
        ]
        
        # Create Excel file with custom sheet name
        df = pd.DataFrame(test_data)
        excel_buffer = io.BytesIO()
        with pd.ExcelWriter(excel_buffer, engine='openpyxl') as writer:
            df.to_excel(writer, sheet_name='Custom Sheet', index=False)
        excel_buffer.seek(0)
        
        excel_file = SimpleUploadedFile(
            "test_bookings.xlsx",
            excel_buffer.getvalue(),
            content_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
        )
        
        # Test with specific sheet name
        result = self.enhanced_excel_import_service.import_bookings_from_excel(
            excel_file=excel_file,
            property_id=None,
            user=self.admin_user,
            sheet_name='Custom Sheet'
        )
        
        self.assertTrue(result['success'])
        self.assertEqual(result['imported_count'], 1)
    
    def test_excel_import_empty_file(self):
        """Test Excel import with empty file"""
        # Create empty DataFrame
        df = pd.DataFrame()
        excel_buffer = io.BytesIO()
        with pd.ExcelWriter(excel_buffer, engine='openpyxl') as writer:
            df.to_excel(writer, sheet_name='Bookings', index=False)
        excel_buffer.seek(0)
        
        excel_file = SimpleUploadedFile(
            "empty.xlsx",
            excel_buffer.getvalue(),
            content_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
        )
        
        result = self.excel_import_service.import_bookings_from_excel(
            excel_file=excel_file,
            property_id=None,
            user=self.admin_user
        )
        
        self.assertFalse(result['success'])
        self.assertEqual(result['imported_count'], 0)
        self.assertGreater(len(result['errors']), 0)
    
    def test_excel_import_large_file_performance(self):
        """Test Excel import performance with larger dataset"""
        # Create larger dataset (100 bookings)
        test_data = []
        for i in range(100):
            test_data.append({
                'Property': self.property1.name if i % 2 == 0 else self.property2.name,
                'Check In': (date.today() + timedelta(days=i*7)).strftime('%Y-%m-%d'),
                'Check Out': (date.today() + timedelta(days=i*7+3)).strftime('%Y-%m-%d'),
                'Guest Name': f'Guest {i}',
                'Guest Contact': f'guest{i}@example.com',
                'Status': 'confirmed'
            })
        
        excel_file = self.create_test_excel_file(test_data)
        
        import time
        start_time = time.time()
        
        result = self.excel_import_service.import_bookings_from_excel(
            excel_file=excel_file,
            property_id=None,
            user=self.admin_user
        )
        
        end_time = time.time()
        processing_time = end_time - start_time
        
        self.assertTrue(result['success'])
        self.assertEqual(result['imported_count'], 100)
        self.assertLess(processing_time, 30)  # Should complete within 30 seconds
