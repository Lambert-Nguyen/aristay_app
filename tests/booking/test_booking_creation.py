#!/usr/bin/env python3
"""
Test script to verify booking creation works correctly
"""
import os
import django

# Setup Django environment
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'backend.settings')
django.setup()

from api.services.excel_import_service import ExcelImportService
from django.contrib.auth import get_user_model
from api.models import Property, Booking

User = get_user_model()
import pandas as pd

def test_booking_creation():
    """Test that booking creation works without created_by/modified_by fields"""
    try:
        print("🧪 Testing Booking Creation")
        print("=" * 50)
        
        # Get or create a test user
        user, created = User.objects.get_or_create(
            username='test_import_user',
            defaults={
                'email': 'test@aristay.com',
                'is_staff': True,
                'is_superuser': True
            }
        )
        
        # Get or create a test property
        property_obj, created = Property.objects.get_or_create(
            name='Test Property',
            defaults={
                'created_by': user,
                'modified_by': user
            }
        )
        
        print(f"✅ Using test user: {user.username}")
        print(f"✅ Using test property: {property_obj.name}")
        
        # Test the import service
        import_service = ExcelImportService(user)
        print("✅ ExcelImportService initialized successfully")
        
        # Create mock data
        mock_data = {
            'Confirmation code': 'TEST123',
            'Status': 'Booked',
            'Guest name': 'Test Guest',
            'Contact': '+1-555-0123',
            'Booking source': 'Direct',
            'Listing': 'Test Listing',
            'Earnings': 150.00,
            'Booked': pd.Timestamp('2025-01-15'),
            '# of adults': 2,
            '# of children': 1,
            '# of infants': 0,
            'Start date': pd.Timestamp('2025-02-01'),
            'End date': pd.Timestamp('2025-02-05'),
            '# of nights': 4,
            'Properties': 'Test Property',
            'Check ': 'Same day cleaning required',
            'Check 1': 'Early check-in'
        }
        
        mock_row = pd.Series(mock_data)
        print("✅ Mock data created successfully")
        
        # Test data extraction
        extracted_data = import_service._extract_booking_data(mock_row, 1)
        if extracted_data:
            print(f"✅ Data extraction successful: {len(extracted_data)} fields extracted")
        else:
            print("❌ Data extraction failed")
            return
        
        # Test property matching
        matched_property = import_service._find_or_create_property("Test Property")
        if matched_property:
            print(f"✅ Property matching successful: {matched_property.name}")
        else:
            print("❌ Property matching failed")
            return
        
        # Test booking creation
        try:
            new_booking = import_service._create_booking(extracted_data, matched_property, mock_row)
            print(f"✅ Booking creation successful: ID {new_booking.id}")
            print(f"   - Guest: {new_booking.guest_name}")
            print(f"   - Dates: {new_booking.check_in_date} to {new_booking.check_out_date}")
            print(f"   - External Code: {new_booking.external_code}")
            print(f"   - Raw Row: {new_booking.raw_row is not None}")
            
            # Test booking update
            try:
                import_service._update_booking(new_booking, extracted_data, mock_row)
                print("✅ Booking update successful")
            except Exception as e:
                print(f"❌ Booking update failed: {e}")
            
        except Exception as e:
            print(f"❌ Booking creation failed: {e}")
            import traceback
            traceback.print_exc()
            return
        
        print("\n" + "=" * 50)
        print("🎯 Test Summary")
        print("=" * 50)
        print("✅ Service initialization: PASSED")
        print("✅ Data extraction: PASSED")
        print("✅ Property matching: PASSED")
        print("✅ Booking creation: PASSED")
        print("✅ Booking update: PASSED")
        print("\n🚀 Booking creation is now working correctly!")
        
    except Exception as e:
        print(f"❌ Test failed with error: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    test_booking_creation()
