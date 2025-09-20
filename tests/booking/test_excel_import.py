#!/usr/bin/env python
"""
Test script for Enhanced Excel Import Service with Conflict Resolution

This script tests the functionality of the enhanced Excel import service
to ensure the conflict detection and resolution features work correctly.
"""

import pytest
import json
from datetime import datetime, timedelta
from django.test import TestCase
from django.contrib.auth.models import User
from django.core.files.uploadedfile import SimpleUploadedFile
from django.db import IntegrityError, transaction
from django.utils import timezone
from tests.utils.timezone_helpers import create_booking_dates, days_from_now

from api.models import Property, Booking, BookingImportLog
from api.services.enhanced_excel_import_service import (
    EnhancedExcelImportService, 
    ConflictResolutionService,
    BookingConflict,
    ConflictType
)

@pytest.mark.django_db
class TestEnhancedExcelImport(TestCase):
    """Test suite for enhanced Excel import functionality"""
    
    def setUp(self):
        """Create test user and property"""
        # Create test user with unique username to avoid conflicts
        self.username = f'test_import_user_{datetime.now().microsecond}'
        self.user = User.objects.create_user(
            username=self.username,
            email='test@example.com',
            first_name='Test',
            last_name='User',
        )
        
        # Create test property with unique name (Property model only has name and address)
        property_name = f'Test Property for Import {datetime.now().microsecond}'
        self.property = Property.objects.create(
            name=property_name,
            address='123 Test Street, Test City, CA 12345'
        )
    
    def tearDown(self):
        """Clean up test data"""
        try:
            # Clean up any bookings created during tests
            with transaction.atomic():
                Booking.objects.filter(property=self.property).delete()
        except Exception:
            pass  # Ignore cleanup errors
        
        try:
            with transaction.atomic():
                BookingImportLog.objects.filter(imported_by=self.user).delete()
        except Exception:
            pass  # Ignore cleanup errors
        
        try:
            # Clean up test objects
            with transaction.atomic():
                self.property.delete()
                self.user.delete()
        except Exception:
            pass  # Ignore cleanup errors
    
    def test_conflict_detection(self):
        """Test conflict detection logic"""
        # Create existing booking with proper transaction management
        with transaction.atomic():
            external_code = f'TEST123_{datetime.now().microsecond}'
            existing_booking = Booking.objects.create(
                property=self.property,
                external_code=external_code,
                guest_name='John Doe',
                check_in_date=days_from_now(1),
                check_out_date=days_from_now(3),
                external_status='confirmed',
                source='Airbnb'
            )
        
        # Test conflict types
        service = EnhancedExcelImportService(self.user)
        
        # Test date change conflict
        booking_data = {
            'external_code': external_code,
            'guest_name': 'John Doe',
            'property_name': self.property.name,
            'start_date': days_from_now(2),  # Different date
            'end_date': days_from_now(4),    # Different date
            'external_status': 'confirmed',
            'source': 'Airbnb'
        }
        
        conflict_result = service._detect_conflicts(booking_data, self.property, 1)
        
        # Assert conflict detection worked
        self.assertTrue(conflict_result['has_conflicts'], "Expected conflict not detected")
        
        # Test direct booking (should not auto-resolve)
        booking_data['source'] = 'Direct'
        conflict_result = service._detect_conflicts(booking_data, self.property, 2)
        
        self.assertTrue(conflict_result['has_conflicts'], "Direct booking should have conflicts")
        self.assertFalse(conflict_result['auto_resolve'], "Direct booking should require manual review")
    
    def test_conflict_serialization(self):
        """Test conflict serialization for frontend"""
        # Create test booking and conflict with proper transaction management
        with transaction.atomic():
            external_code = f'TEST456_{datetime.now().microsecond}'
            existing_booking = Booking.objects.create(
                property=self.property,
                external_code=external_code,
                guest_name='Jane Smith',
                check_in_date=days_from_now(5),
                check_out_date=days_from_now(7),
                external_status='confirmed',
                source='VRBO'
            )
        
        excel_data = {
            'external_code': external_code,
            'guest_name': 'Jane Smith Updated',
            'property_name': self.property.name,
            'start_date': days_from_now(6),
            'end_date': days_from_now(8),
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
        
        # Assert serialization worked correctly
        self.assertIn('confidence_score', serialized)
        self.assertIn('conflict_types', serialized)
        self.assertIn('changes_summary', serialized)
        self.assertIsInstance(serialized['conflict_types'], list)
        self.assertIsInstance(serialized['changes_summary'], dict)
    
    def test_conflict_resolution_service(self):
        """Test conflict resolution service"""
        # Create test booking with proper transaction management
        with transaction.atomic():
            external_code = f'TEST789_{datetime.now().microsecond}'
            existing_booking = Booking.objects.create(
                property=self.property,
                external_code=external_code,
                guest_name='Bob Wilson',
                check_in_date=days_from_now(10),
                check_out_date=days_from_now(12),
                external_status='confirmed',
                source='Direct'
            )
        
        # Create mock import log with conflicts data
        conflicts_data = [{
            "conflict_index": 0, 
            "existing_booking": {"id": existing_booking.pk}, 
            "excel_data": {
                "guest_name": "Bob Wilson Updated", 
                "start_date": "2024-01-15", 
                "end_date": "2024-01-17"
            }
        }]
        
        with transaction.atomic():
            import_log = BookingImportLog.objects.create(
                imported_by=self.user,
                total_rows=1,
                successful_imports=0,
                errors_count=0,
                errors_log=f'CONFLICTS_DATA:{json.dumps(conflicts_data)}'
            )
        
        resolution_service = ConflictResolutionService(self.user)
        
        # Test resolution with proper error handling
        resolutions = [{
            'conflict_index': 0,
            'action': 'update_existing',
            'apply_changes': ['guest_name']
        }]
        
        try:
            with transaction.atomic():
                results = resolution_service.resolve_conflicts(import_log.pk, resolutions)
                self.assertIsInstance(results, dict)
                # The actual keys returned are 'updated', 'created', 'skipped', 'errors'
                self.assertIn('updated', results)
                self.assertIn('created', results) 
                self.assertIn('skipped', results)
                self.assertIn('errors', results)
        except Exception as e:
            # If the resolution service has issues, we should still be able to continue
            self.fail(f"Conflict resolution failed unexpectedly: {e}")
    
    def test_database_constraint_handling(self):
        """Test proper handling of database constraint violations"""
        # Create a booking that might trigger constraint violations
        with transaction.atomic():
            external_code = f'CONSTRAINT_TEST_{datetime.now().microsecond}'
            booking = Booking.objects.create(
                property=self.property,
                external_code=external_code,
                guest_name='Constraint Test User',
                check_in_date=days_from_now(1),
                check_out_date=days_from_now(3),
                external_status='confirmed',
                source='Test'
            )
        
        # Test that we can handle operations that might cause integrity errors
        service = EnhancedExcelImportService(self.user)
        
        # This should work without constraint violations
        booking_data = {
            'external_code': f'DIFFERENT_CODE_{datetime.now().microsecond}',
            'guest_name': 'Different Guest',
            'property_name': self.property.name,
            'start_date': days_from_now(5),
            'end_date': days_from_now(7),
            'external_status': 'confirmed',
            'source': 'Test'
        }
        
        # Test conflict detection without transaction errors
        try:
            with transaction.atomic():
                conflict_result = service._detect_conflicts(booking_data, self.property, 1)
                self.assertIsInstance(conflict_result, dict)
                self.assertIn('has_conflicts', conflict_result)
        except IntegrityError:
            self.fail("Unexpected IntegrityError during conflict detection")
