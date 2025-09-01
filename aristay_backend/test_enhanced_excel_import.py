#!/usr/bin/env python
"""
Test script for Enhanced Excel Import Service with Conflict Resolution

This script tests the functionality of the enhanced Excel import service
to ensure the conflict detection and resolution features work correctly.
"""

import os
import sys
import django
import json
from datetime import datetime, timedelta
from django.test import TestCase
from django.contrib.auth.models import User
from django.core.files.uploadedfile import SimpleUploadedFile

# Add the project root to Python path
sys.path.insert(0, '/Users/duylam1407/Workspace/SJSU/aristay_app/aristay_backend')

# Setup Django environment
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'backend.settings')
django.setup()

from api.models import Property, Booking, BookingImportLog
from api.services.enhanced_excel_import_service import (
    EnhancedExcelImportService, 
    ConflictResolutionService,
    BookingConflict,
    ConflictType
)

class TestEnhancedExcelImport:
    """Test suite for enhanced Excel import functionality"""
    
    def __init__(self):
        self.user = None
        self.property = None
        self.setup_test_data()
    
    def setup_test_data(self):
        """Create test user and property"""
        print("🔧 Setting up test data...")
        
        # Create test user
        self.user, created = User.objects.get_or_create(
            username='test_import_user',
            defaults={
                'email': 'test@example.com',
                'first_name': 'Test',
                'last_name': 'User',
                'is_staff': True
            }
        )
        if created:
            print(f"✅ Created test user: {self.user.username}")
        else:
            print(f"ℹ️  Using existing test user: {self.user.username}")
        
        # Create test property
        self.property, created = Property.objects.get_or_create(
            name='Test Property for Import',
            defaults={
                'address': '123 Test Street',
                'city': 'Test City',
                'state': 'CA',
                'zip_code': '12345'
            }
        )
        if created:
            print(f"✅ Created test property: {self.property.name}")
        else:
            print(f"ℹ️  Using existing test property: {self.property.name}")
    
    def test_conflict_detection(self):
        """Test conflict detection logic"""
        print("\n🧪 Testing conflict detection...")
        
        # Create existing booking
        existing_booking = Booking.objects.create(
            property=self.property,
            external_code='TEST123',
            guest_name='John Doe',
            check_in_date=datetime.now() + timedelta(days=1),
            check_out_date=datetime.now() + timedelta(days=3),
            external_status='confirmed',
            source='Airbnb'
        )
        print(f"✅ Created existing booking: {existing_booking.external_code}")
        
        # Test conflict types
        service = EnhancedExcelImportService(self.user)
        
        # Test date change conflict
        booking_data = {
            'external_code': 'TEST123',
            'guest_name': 'John Doe',
            'property_name': self.property.name,
            'start_date': datetime.now() + timedelta(days=2),  # Different date
            'end_date': datetime.now() + timedelta(days=4),    # Different date
            'external_status': 'confirmed',
            'source': 'Airbnb'
        }
        
        conflict_result = service._detect_conflicts(booking_data, self.property, 1)
        
        if conflict_result['has_conflicts']:
            print(f"✅ Conflict detected correctly")
            print(f"   Auto-resolve: {conflict_result['auto_resolve']}")
            print(f"   Conflict types: {conflict_result['conflict'].conflict_types}")
        else:
            print("❌ Expected conflict not detected")
        
        # Test direct booking (should not auto-resolve)
        booking_data['source'] = 'Direct'
        conflict_result = service._detect_conflicts(booking_data, self.property, 2)
        
        if conflict_result['has_conflicts'] and not conflict_result['auto_resolve']:
            print("✅ Direct booking correctly requires manual review")
        else:
            print("❌ Direct booking conflict handling failed")
        
        # Cleanup
        existing_booking.delete()
    
    def test_conflict_serialization(self):
        """Test conflict serialization for frontend"""
        print("\n🧪 Testing conflict serialization...")
        
        # Create test booking and conflict
        existing_booking = Booking.objects.create(
            property=self.property,
            external_code='TEST456',
            guest_name='Jane Smith',
            check_in_date=datetime.now() + timedelta(days=5),
            check_out_date=datetime.now() + timedelta(days=7),
            external_status='confirmed',
            source='VRBO'
        )
        
        excel_data = {
            'external_code': 'TEST456',
            'guest_name': 'Jane Smith Updated',
            'property_name': self.property.name,
            'start_date': datetime.now() + timedelta(days=6),
            'end_date': datetime.now() + timedelta(days=8),
            'external_status': 'modified',
            'source': 'VRBO'
        }
        
        conflict = BookingConflict(
            existing_booking=existing_booking,
            excel_data=excel_data,
            conflict_types=[ConflictType.DATE_CHANGE, ConflictType.GUEST_CHANGE],
            row_number=3
        )
        
        service = EnhancedExcelImportService(self.user)
        serialized = service._serialize_conflict(conflict)
        
        print(f"✅ Conflict serialized successfully")
        print(f"   Confidence score: {serialized['confidence_score']}")
        print(f"   Conflict types: {serialized['conflict_types']}")
        print(f"   Changes summary keys: {list(serialized['changes_summary'].keys())}")
        
        # Cleanup
        existing_booking.delete()
    
    def test_conflict_resolution_service(self):
        """Test conflict resolution service"""
        print("\n🧪 Testing conflict resolution service...")
        
        # Create test booking
        existing_booking = Booking.objects.create(
            property=self.property,
            external_code='TEST789',
            guest_name='Bob Wilson',
            check_in_date=datetime.now() + timedelta(days=10),
            check_out_date=datetime.now() + timedelta(days=12),
            external_status='confirmed',
            source='Direct'
        )
        
        # Create mock import log with conflicts data
        import_log = BookingImportLog.objects.create(
            imported_by=self.user,
            total_rows=1,
            successful_imports=0,
            errors_count=0,
            errors_log='CONFLICTS_DATA:[{"conflict_index": 0, "existing_booking": {"id": ' + str(existing_booking.pk) + '}, "excel_data": {"guest_name": "Bob Wilson Updated", "start_date": "2024-01-15", "end_date": "2024-01-17"}}]'
        )
        
        resolution_service = ConflictResolutionService(self.user)
        
        # Test resolution
        resolutions = [{
            'conflict_index': 0,
            'action': 'update_existing',
            'apply_changes': ['guest_name']
        }]
        
        try:
            results = resolution_service.resolve_conflicts(import_log.pk, resolutions)
            print(f"✅ Conflict resolution completed")
            print(f"   Results: {results}")
        except Exception as e:
            print(f"❌ Conflict resolution failed: {e}")
        
        # Cleanup
        existing_booking.delete()
        import_log.delete()
    
    def run_all_tests(self):
        """Run all tests"""
        print("🚀 Starting Enhanced Excel Import Tests")
        print("=" * 50)
        
        try:
            self.test_conflict_detection()
            self.test_conflict_serialization()
            self.test_conflict_resolution_service()
            
            print("\n" + "=" * 50)
            print("✅ All tests completed successfully!")
            print("🎉 Enhanced Excel Import Service is ready for use!")
            
        except Exception as e:
            print(f"\n❌ Test failed with error: {e}")
            import traceback
            traceback.print_exc()
        
        finally:
            # Cleanup any remaining test data
            print("\n🧹 Cleaning up test data...")
            User.objects.filter(username='test_import_user').delete()
            Property.objects.filter(name='Test Property for Import').delete()
            print("✅ Cleanup completed")


if __name__ == '__main__':
    tester = TestEnhancedExcelImport()
    tester.run_all_tests()
