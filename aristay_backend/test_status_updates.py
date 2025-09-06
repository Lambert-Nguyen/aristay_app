#!/usr/bin/env python
"""
Test Status Update Functionality
Test that status changes like "Confirmed" -> "Checking out today" are properly auto-updated
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
from api.services.enhanced_excel_import_service import EnhancedExcelImportService, ConflictType
from api.models import Booking, Property
import pandas as pd
import uuid

def test_status_update_functionality():
    """Test that status changes are properly auto-updated for platform bookings"""
    print("🔄 TESTING STATUS UPDATE FUNCTIONALITY")
    print("=" * 50)
    
    prop = None
    initial_booking = None
    
    try:
        # Create test property and user
        prop = Property.objects.create(name=f'Status Test Property {uuid.uuid4()}')
        user = User.objects.first() or User.objects.create_user('testuser')
        
        # Create initial booking with "Confirmed" status
        initial_booking = Booking.objects.create(
            property=prop,
            external_code='HMDNHY93WB',  # Same as example from user
            guest_name='Test Guest',
            check_in_date=timezone.now().date(),
            check_out_date=(timezone.now() + timezone.timedelta(days=2)).date(),
            source='Airbnb',
            external_status='Confirmed',
            status='confirmed'
        )
        
        print(f"✅ Created initial booking: {initial_booking.external_code}")
        print(f"   Initial external_status: '{initial_booking.external_status}'")
        print(f"   Initial Django status: '{initial_booking.status}'")
        
        # Create Excel row with updated status
        test_row = pd.Series({
            'Confirmation code': 'HMDNHY93WB',  # Same external code
            'Guest name': 'Test Guest',
            'Start date': initial_booking.check_in_date,
            'End date': initial_booking.check_out_date,
            'Booking source': 'Airbnb',
            'Properties': prop.name,
            'Status': 'Checking out today'  # New status
        })
        
        service = EnhancedExcelImportService(user)
        
        # Test conflict detection
        booking_data = service._extract_booking_data_enhanced(test_row, 1)
        
        if not booking_data:
            print("❌ Failed to extract booking data")
            return
            
        print(f"✅ Extracted booking data with status: '{booking_data.get('external_status')}'")
        
        # Test conflict detection logic
        conflict_result = service._detect_conflicts(booking_data, prop, 1)
        
        if conflict_result['has_conflicts']:
            print(f"✅ Conflict detected as expected")
            print(f"   Auto-resolve: {conflict_result['auto_resolve']}")
            print(f"   Is exact duplicate: {conflict_result.get('is_exact_duplicate', False)}")
            
            conflict_types = service._identify_conflict_types(initial_booking, booking_data)
            print(f"   Conflict types: {conflict_types}")
            
            if conflict_result['auto_resolve']:
                # Test auto-update
                print("🔄 Testing auto-update...")
                service._auto_update_booking(initial_booking, booking_data, test_row)
                
                # Refresh from database
                initial_booking.refresh_from_db()
                
                print(f"✅ Auto-update completed!")
                print(f"   Updated external_status: '{initial_booking.external_status}'")
                print(f"   Updated Django status: '{initial_booking.status}'")
                
                # Verify the updates
                if initial_booking.external_status == 'Checking out today':
                    print("✅ External status correctly updated!")
                else:
                    print(f"❌ External status not updated. Expected 'Checking out today', got '{initial_booking.external_status}'")
                
                if initial_booking.status == 'confirmed':  # Should still be confirmed
                    print("✅ Django status correctly maintained as 'confirmed'!")
                else:
                    print(f"❌ Django status incorrect. Expected 'confirmed', got '{initial_booking.status}'")
                    
            else:
                print("❌ Status-only changes should be auto-resolved for platform bookings!")
        else:
            print("❌ Should have detected status conflict!")
        
        # Test full import process
        print("\n🔄 Testing full import process...")
        
        # Reset the booking to original status
        initial_booking.external_status = 'Confirmed'
        initial_booking.status = 'confirmed'
        initial_booking.save()
        
        # Import the Excel data
        service = EnhancedExcelImportService(user)  # Fresh service
        service._process_booking_row_with_conflicts(test_row, 1)
        
        # Check results
        initial_booking.refresh_from_db()
        print(f"✅ Import process completed!")
        print(f"   Final external_status: '{initial_booking.external_status}'")
        print(f"   Final Django status: '{initial_booking.status}'")
        print(f"   Auto-updated count: {service.auto_updated_count}")
        print(f"   Conflicts for review: {len(service.conflicts_detected)}")
        
        if service.auto_updated_count > 0:
            print("✅ Status change was auto-updated as expected!")
        else:
            print("❌ Status change was not auto-updated!")
            
        if initial_booking.external_status == 'Checking out today':
            print("✅ Status update successful!")
        else:
            print("❌ Status was not updated in database!")
        
    except Exception as e:
        print(f"❌ Error during testing: {e}")
        import traceback
        traceback.print_exc()
    
    # Cleanup
    try:
        if initial_booking:
            initial_booking.delete()
    except:
        pass
    try:
        if prop:
            prop.delete()
    except:
        pass
    
    print("\n" + "=" * 50)
    print("🏁 STATUS UPDATE TEST COMPLETE")

if __name__ == '__main__':
    test_status_update_functionality()
