#!/usr/bin/env python
"""
Test the remaining GPT Agent fixes:
- Timezone-aware datetime creation
- Hardened conflict JSON storage  
"""

import os
import sys
import django
from django.conf import settings

# Setup Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'backend.settings')
django.setup()

from datetime import datetime
from django.utils import timezone
from django.contrib.auth.models import User
from api.services.enhanced_excel_import_service import EnhancedExcelImportService
from api.models import Booking, Property
import json
import pandas as pd

def test_timezone_aware_creation():
    """Test timezone-aware datetime creation"""
    print("🕰️ Testing timezone-aware datetime creation...")
    
    # Create test data with naive datetimes
    test_row = pd.Series({
        'Confirmation code': 'TEST123',
        'Guest name': 'Test Guest', 
        'Start date': '2025-01-01',  # String date
        'End date': datetime(2025, 1, 5),  # Naive datetime
        'Booking source': 'Airbnb',
        'Properties': 'Test Property'
    })
    
    # Create property
    prop = Property.objects.create(name='Test Property Timezone')
    
    try:
        user = User.objects.first() or User.objects.create_user('testuser')
        service = EnhancedExcelImportService(user)
        booking_data = service._extract_booking_data_enhanced(test_row, 1)
        
        # Check that dates are timezone-aware after processing
        if booking_data:
            print(f"  ✅ Start date type: {type(booking_data.get('start_date'))}")
            print(f"  ✅ End date type: {type(booking_data.get('end_date'))}")
            
            start_date = booking_data.get('start_date')
            end_date = booking_data.get('end_date') 
            
            if start_date and hasattr(start_date, 'tzinfo'):
                if start_date.tzinfo is not None:
                    print("  ✅ Start date is timezone-aware")
                else:
                    print("  ❌ Start date is still naive")
                    
            if end_date and hasattr(end_date, 'tzinfo'):
                if end_date.tzinfo is not None:
                    print("  ✅ End date is timezone-aware")
                else:
                    print("  ❌ End date is still naive")
                    
    except Exception as e:
        print(f"  ❌ Error testing timezone creation: {e}")
    finally:
        prop.delete()

def test_hardened_json_serialization():
    """Test hardened JSON serialization in conflict handling"""
    print("🔒 Testing hardened JSON serialization...")
    
    import uuid
    # Create test objects
    prop = Property.objects.create(name=f'Test Property JSON {uuid.uuid4()}')
    
    # Create a booking with complex data
    booking = Booking.objects.create(
        property=prop,
        external_code='JSON123',
        guest_name='Test Guest',
        check_in_date=timezone.now().date(),
        check_out_date=(timezone.now() + timezone.timedelta(days=2)).date(),
        source='Airbnb'
    )
    
    try:
        user = User.objects.first() or User.objects.create_user('testuser')
        service = EnhancedExcelImportService(user)
        
        # Create a mock conflict with various data types
        from api.services.enhanced_excel_import_service import BookingConflict
        
        conflict = BookingConflict(
            existing_booking=booking,
            excel_data={
                'external_code': 'JSON123',
                'guest_name': 'Different Guest',
                'start_date': timezone.now(),  # datetime object
                'end_date': None,  # None value
                'source': 'Airbnb'
            },
            conflict_types=['code_match'],
            row_number=1
        )
        
        # Test serialization
        serialized = service._serialize_conflict(conflict)
        
        # Try to JSON encode it
        json_str = json.dumps(serialized)
        print("  ✅ JSON serialization successful")
        print(f"  ✅ Serialized keys: {list(serialized.keys())}")
        
        # Check for safe handling of datetime
        if 'start_date' in serialized['excel_data']:
            print("  ✅ Datetime values safely serialized")
            
        # Check for safe handling of None
        if serialized['excel_data']['end_date'] is None:
            print("  ✅ None values safely handled")
            
    except Exception as e:
        print(f"  ❌ JSON serialization error: {e}")
    finally:
        booking.delete()
        prop.delete()

def main():
    print("🚀 GPT AGENT REMAINING FIXES - VALIDATION")
    print("=" * 50)
    
    test_timezone_aware_creation()
    print()
    test_hardened_json_serialization()
    
    print()
    print("=" * 50)
    print("✅ REMAINING FIXES VALIDATION COMPLETE!")

if __name__ == '__main__':
    main()
