#!/usr/bin/env python
"""
Test Real-World Status Update Issue
Test the specific case mentioned by user with confirmation codes HMDNHY93WB and HMHCA35ERM
"""

import os
import sys
import django
from django.conf import settings

# Setup Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'backend.settings')
django.setup()

from datetime import datetime, date
from django.utils import timezone
from django.contrib.auth.models import User
from api.services.enhanced_excel_import_service import EnhancedExcelImportService
from api.models import Booking, Property
import pandas as pd
import uuid

def test_real_world_status_update():
    """Test the specific issue with HMDNHY93WB and HMHCA35ERM bookings"""
    print("🔍 TESTING REAL-WORLD STATUS UPDATE ISSUE")
    print("=" * 60)
    
    prop = None
    booking1 = None
    booking2 = None
    
    try:
        # Create test property and user
        prop = Property.objects.create(name='Test Property Real World')
        user = User.objects.first() or User.objects.create_user('testuser')
        
        print("📋 SCENARIO: Import Cleaning_schedule_1 then Cleaning_schedule_2")
        print("   Booking HMDNHY93WB: 'Confirmed' -> 'Checking out today'")
        print("   Booking HMHCA35ERM: 'Confirmed' -> 'Checking out today'")
        
        # Step 1: Create initial bookings as if from Cleaning_schedule_1
        booking1 = Booking.objects.create(
            property=prop,
            external_code='HMDNHY93WB',
            guest_name='John Doe',
            check_in_date=date(2025, 1, 10),
            check_out_date=date(2025, 1, 15),
            source='Airbnb',
            external_status='Confirmed',
            status='confirmed'
        )
        
        booking2 = Booking.objects.create(
            property=prop,
            external_code='HMHCA35ERM',
            guest_name='Jane Smith', 
            check_in_date=date(2025, 1, 12),
            check_out_date=date(2025, 1, 17),
            source='Airbnb',
            external_status='Confirmed',
            status='confirmed'
        )
        
        print(f"✅ Created initial bookings:")
        print(f"   {booking1.external_code}: {booking1.external_status} -> {booking1.status}")
        print(f"   {booking2.external_code}: {booking2.external_status} -> {booking2.status}")
        
        # Step 2: Simulate Cleaning_schedule_2 import with status changes
        print(f"\n🔄 Simulating Cleaning_schedule_2 import...")
        
        # Create test Excel data for both bookings with updated status
        test_data = [
            {
                'Confirmation code': 'HMDNHY93WB',
                'Guest name': 'John Doe',
                'Start date': date(2025, 1, 10),
                'End date': date(2025, 1, 15),
                'Booking source': 'Airbnb',
                'Properties': 'Test Property Real World',
                'Status': 'Checking out today'
            },
            {
                'Confirmation code': 'HMHCA35ERM',
                'Guest name': 'Jane Smith',
                'Start date': date(2025, 1, 12),
                'End date': date(2025, 1, 17),
                'Booking source': 'Airbnb',
                'Properties': 'Test Property Real World',
                'Status': 'Checking out today'
            }
        ]
        
        service = EnhancedExcelImportService(user)
        
        for i, row_data in enumerate(test_data):
            print(f"\n   Processing row {i+1}: {row_data['Confirmation code']}")
            test_row = pd.Series(row_data)
            
            # Process the booking row
            service._process_booking_row_with_conflicts(test_row, i+1)
        
        # Step 3: Check the results
        print(f"\n📊 IMPORT RESULTS:")
        print(f"   Success count: {service.success_count}")
        print(f"   Auto-updated count: {service.auto_updated_count}")
        print(f"   Conflicts for review: {len(service.conflicts_detected)}")
        print(f"   Requires review: {service.requires_review}")
        
        # Step 4: Verify database updates
        print(f"\n🔍 DATABASE VERIFICATION:")
        
        booking1.refresh_from_db()
        booking2.refresh_from_db()
        
        print(f"   HMDNHY93WB:")
        print(f"     External Status: '{booking1.external_status}'")
        print(f"     Django Status: '{booking1.status}'")
        print(f"     Updated?: {'✅ YES' if booking1.external_status == 'Checking out today' else '❌ NO'}")
        
        print(f"   HMHCA35ERM:")
        print(f"     External Status: '{booking2.external_status}'")
        print(f"     Django Status: '{booking2.status}'")
        print(f"     Updated?: {'✅ YES' if booking2.external_status == 'Checking out today' else '❌ NO'}")
        
        # Step 5: Overall assessment
        both_updated = (booking1.external_status == 'Checking out today' and 
                       booking2.external_status == 'Checking out today')
        
        auto_updated_both = service.auto_updated_count >= 2
        no_conflicts = len(service.conflicts_detected) == 0
        
        print(f"\n🎯 ASSESSMENT:")
        print(f"   Both bookings updated: {'✅ YES' if both_updated else '❌ NO'}")
        print(f"   Auto-updated both: {'✅ YES' if auto_updated_both else '❌ NO'}")
        print(f"   No manual conflicts: {'✅ YES' if no_conflicts else '❌ NO'}")
        
        if both_updated and auto_updated_both and no_conflicts:
            print(f"\n🎉 SUCCESS: Status update issue has been FIXED!")
            print(f"   Platform bookings with status-only changes are now auto-updated correctly.")
        else:
            print(f"\n❌ ISSUE PERSISTS: Status updates are not working as expected.")
            
        return both_updated and auto_updated_both and no_conflicts
        
    except Exception as e:
        print(f"❌ Error during testing: {e}")
        import traceback
        traceback.print_exc()
        return False
    
    # Cleanup
    try:
        if booking1:
            booking1.delete()
        if booking2:
            booking2.delete()
        if prop:
            prop.delete()
    except:
        pass

def main():
    print("🚀 REAL-WORLD STATUS UPDATE FIX VALIDATION")
    print("Testing specific issue with Cleaning_schedule_1 -> Cleaning_schedule_2")
    print("=" * 80)
    
    success = test_real_world_status_update()
    
    print("\n" + "=" * 80)
    if success:
        print("✅ REAL-WORLD STATUS UPDATE ISSUE RESOLVED!")
        print("🎯 Your bookings will now be properly updated when status changes in Excel files.")
    else:
        print("❌ Status update issue still needs investigation.")
    print("=" * 80)
    
    return success

if __name__ == '__main__':
    main()
