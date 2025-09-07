#!/usr/bin/env python
"""
Test Combined Status and Guest Name Behavior
Verify that:
1. Status-only changes still auto-update 
2. Guest name changes require manual review
3. Combined changes also require manual review
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

def test_combined_behavior():
    """Test the combined behavior of status and guest name changes"""
    print("🔄 TESTING COMBINED STATUS + GUEST NAME BEHAVIOR")
    print("=" * 60)
    
    prop = None
    booking1 = None
    booking2 = None
    booking3 = None
    
    try:
        # Create test property and user
        prop = Property.objects.create(name=f'Combined Test Property {uuid.uuid4()}')
        user = User.objects.first() or User.objects.create_user('testuser')
        
        # Scenario 1: Status-only change (should auto-update)
        booking1 = Booking.objects.create(
            property=prop,
            external_code='STATUS001',
            guest_name='John Doe',
            check_in_date=date(2025, 1, 10),
            check_out_date=date(2025, 1, 15),
            source='Airbnb',
            external_status='Confirmed',
            status='confirmed'
        )
        
        # Scenario 2: Guest name-only change (should require manual review)
        booking2 = Booking.objects.create(
            property=prop,
            external_code='GUEST001',
            guest_name='Kathrin MĂ¼ller',  # Encoding issue
            check_in_date=date(2025, 1, 12),
            check_out_date=date(2025, 1, 17),
            source='Airbnb',
            external_status='Confirmed',
            status='confirmed'
        )
        
        # Scenario 3: Both status AND guest name change (should require manual review)
        booking3 = Booking.objects.create(
            property=prop,
            external_code='BOTH001',
            guest_name='Jane Smith',
            check_in_date=date(2025, 1, 20),
            check_out_date=date(2025, 1, 25),
            source='Airbnb',
            external_status='Confirmed',
            status='confirmed'
        )
        
        print("✅ Created test bookings:")
        print(f"   {booking1.external_code}: Status-only test")
        print(f"   {booking2.external_code}: Guest name-only test")
        print(f"   {booking3.external_code}: Combined change test")
        
        # Test data for import
        test_cases = [
            # Scenario 1: Status-only change
            {
                'name': 'Status-only change',
                'data': {
                    'Confirmation code': 'STATUS001',
                    'Guest name': 'John Doe',  # Same name
                    'Start date': date(2025, 1, 10),
                    'End date': date(2025, 1, 15),
                    'Booking source': 'Airbnb',
                    'Properties': prop.name,
                    'Status': 'Checking out today'  # Changed status
                },
                'expected_auto_resolve': True,
                'expected_conflicts': 1  # Status change only
            },
            # Scenario 2: Guest name-only change  
            {
                'name': 'Guest name-only change',
                'data': {
                    'Confirmation code': 'GUEST001',
                    'Guest name': 'Kathrin Muller',  # Fixed encoding
                    'Start date': date(2025, 1, 12),
                    'End date': date(2025, 1, 17),
                    'Booking source': 'Airbnb',
                    'Properties': prop.name,
                    'Status': 'Confirmed'  # Same status
                },
                'expected_auto_resolve': False,  # Should require manual review
                'expected_conflicts': 1  # Guest change only
            },
            # Scenario 3: Both changes
            {
                'name': 'Combined status + guest change',
                'data': {
                    'Confirmation code': 'BOTH001',
                    'Guest name': 'Jane Miller',  # Changed name
                    'Start date': date(2025, 1, 20),
                    'End date': date(2025, 1, 25),
                    'Booking source': 'Airbnb',
                    'Properties': prop.name,
                    'Status': 'Checking out today'  # Changed status
                },
                'expected_auto_resolve': False,  # Guest change prevents auto-resolve
                'expected_conflicts': 2  # Both status and guest change
            }
        ]
        
        service = EnhancedExcelImportService(user)
        results = []
        
        for i, test_case in enumerate(test_cases):
            print(f"\n🧪 Test Case {i+1}: {test_case['name']}")
            
            test_row = pd.Series(test_case['data'])
            booking_data = service._extract_booking_data_enhanced(test_row, i+1)
            
            if not booking_data:
                print("❌ Failed to extract booking data")
                continue
                
            conflict_result = service._detect_conflicts(booking_data, prop, i+1)
            
            if conflict_result['has_conflicts']:
                conflict = conflict_result['conflict']
                conflict_types = conflict.conflict_types
                auto_resolve = conflict_result['auto_resolve']
                
                print(f"   Conflict types: {conflict_types}")
                print(f"   Auto-resolve: {auto_resolve}")
                print(f"   Expected auto-resolve: {test_case['expected_auto_resolve']}")
                
                # Validate expectations
                auto_resolve_correct = auto_resolve == test_case['expected_auto_resolve']
                conflict_count_correct = len(conflict_types) == test_case['expected_conflicts']
                
                print(f"   Auto-resolve correct: {'✅' if auto_resolve_correct else '❌'}")
                print(f"   Conflict count correct: {'✅' if conflict_count_correct else '❌'}")
                
                # Show conflict details
                changes = conflict.get_changes_summary()
                if 'guest' in changes:
                    guest_info = changes['guest']
                    print(f"   Guest analysis: {guest_info.get('analysis', 'N/A')}")
                    
                results.append({
                    'name': test_case['name'],
                    'auto_resolve_correct': auto_resolve_correct,
                    'conflict_count_correct': conflict_count_correct,
                    'passed': auto_resolve_correct and conflict_count_correct
                })
            else:
                print("❌ Expected conflicts but none detected!")
                results.append({
                    'name': test_case['name'], 
                    'auto_resolve_correct': False,
                    'conflict_count_correct': False,
                    'passed': False
                })
        
        # Overall assessment
        print(f"\n📊 RESULTS SUMMARY:")
        all_passed = True
        for result in results:
            status = "✅ PASS" if result['passed'] else "❌ FAIL"
            print(f"   {result['name']}: {status}")
            if not result['passed']:
                all_passed = False
        
        if all_passed:
            print(f"\n🎉 ALL TESTS PASSED!")
            print(f"   ✅ Status-only changes auto-update")
            print(f"   ✅ Guest name changes require manual review") 
            print(f"   ✅ Combined changes require manual review")
        else:
            print(f"\n❌ Some tests failed - behavior needs adjustment")
            
        return all_passed
        
    except Exception as e:
        print(f"❌ Error during testing: {e}")
        import traceback
        traceback.print_exc()
        return False
    
    # Cleanup
    try:
        for booking in [booking1, booking2, booking3]:
            if booking:
                booking.delete()
        if prop:
            prop.delete()
    except:
        pass

def main():
    print("🚀 COMBINED STATUS + GUEST NAME BEHAVIOR TEST")
    print("Testing auto-resolve vs manual review logic")
    print("=" * 80)
    
    success = test_combined_behavior()
    
    print("\n" + "=" * 80)
    if success:
        print("✅ COMBINED BEHAVIOR TEST PASSED!")
        print("🎯 Status updates work automatically")
        print("🎯 Guest name changes require human review")
        print("🎯 System properly balances automation with data integrity")
    else:
        print("❌ Combined behavior test needs refinement")
    print("=" * 80)
    
    return success

if __name__ == '__main__':
    main()
