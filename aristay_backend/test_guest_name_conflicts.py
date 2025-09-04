#!/usr/bin/env python
"""
Test Guest Name Conflict Analysis
Test the specific case with HMZE8BT5AC booking: "Kathrin MĂ¼ller" vs "Kathrin Muller"
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
from api.services.enhanced_excel_import_service import EnhancedExcelImportService, _analyze_guest_name_difference
from api.models import Booking, Property
import pandas as pd
import uuid

def test_guest_name_analysis():
    """Test guest name difference analysis"""
    print("👥 TESTING GUEST NAME ANALYSIS")
    print("=" * 40)
    
    # Test various guest name scenarios
    test_cases = [
        # Case 1: Encoding issue (the real example)
        {
            'existing': 'Kathrin MĂ¼ller',
            'new': 'Kathrin Muller', 
            'expected_type': 'encoding_correction',
            'expected_encoding_issue': True
        },
        # Case 2: Diacritics only
        {
            'existing': 'José García',
            'new': 'Jose Garcia',
            'expected_type': 'diacritics_only', 
            'expected_encoding_issue': True
        },
        # Case 3: Minor typo
        {
            'existing': 'John Smith',
            'new': 'Jon Smith',
            'expected_type': 'minor_correction',
            'expected_encoding_issue': False
        },
        # Case 4: Significant change
        {
            'existing': 'John Smith', 
            'new': 'Jane Doe',
            'expected_type': 'significant_change',
            'expected_encoding_issue': False
        },
        # Case 5: Missing data
        {
            'existing': 'John Smith',
            'new': '',
            'expected_type': 'missing_data',
            'expected_encoding_issue': False
        }
    ]
    
    for i, case in enumerate(test_cases, 1):
        print(f"\n📝 Test Case {i}: {case['existing']} → {case['new']}")
        
        analysis = _analyze_guest_name_difference(case['existing'], case['new'])
        
        print(f"   Result: {analysis['type']}")
        print(f"   Description: {analysis['description']}")
        print(f"   Encoding issue: {analysis['likely_encoding_issue']}")
        
        # Validate results
        if analysis['type'] == case['expected_type']:
            print("   ✅ Type detection correct")
        else:
            print(f"   ❌ Type detection wrong. Expected {case['expected_type']}, got {analysis['type']}")
            
        if analysis['likely_encoding_issue'] == case['expected_encoding_issue']:
            print("   ✅ Encoding detection correct")
        else:
            print(f"   ❌ Encoding detection wrong. Expected {case['expected_encoding_issue']}, got {analysis['likely_encoding_issue']}")

def test_real_world_guest_name_conflict():
    """Test the real-world scenario with HMZE8BT5AC"""
    print("\n🎯 TESTING REAL-WORLD GUEST NAME CONFLICT")
    print("=" * 50)
    
    prop = None
    booking = None
    
    try:
        # Create test property and user
        prop = Property.objects.create(name=f'Guest Name Test Property {uuid.uuid4()}')
        user = User.objects.first() or User.objects.create_user('testuser')
        
        # Create initial booking with encoding issue in name
        booking = Booking.objects.create(
            property=prop,
            external_code='HMZE8BT5AC',
            guest_name='Kathrin MĂ¼ller',  # Encoding issue
            check_in_date=date(2025, 1, 20),
            check_out_date=date(2025, 1, 25),
            source='Airbnb',
            external_status='Confirmed',
            status='confirmed'
        )
        
        print(f"✅ Created booking with name: '{booking.guest_name}'")
        
        # Create Excel row with corrected name
        test_row = pd.Series({
            'Confirmation code': 'HMZE8BT5AC',
            'Guest name': 'Kathrin Muller',  # Corrected name
            'Start date': date(2025, 1, 20),
            'End date': date(2025, 1, 25),
            'Booking source': 'Airbnb',
            'Properties': prop.name,
            'Status': 'Confirmed'  # Same status
        })
        
        service = EnhancedExcelImportService(user)
        
        # Extract booking data
        booking_data = service._extract_booking_data_enhanced(test_row, 1)
        
        if not booking_data:
            print("❌ Failed to extract booking data")
            return False
        
        print(f"✅ Excel data extracted with name: '{booking_data.get('guest_name')}'")
        
        # Test conflict detection
        conflict_result = service._detect_conflicts(booking_data, prop, 1)
        
        if conflict_result['has_conflicts']:
            print("✅ Conflict detected as expected")
            
            conflict = conflict_result['conflict']
            conflict_types = conflict.conflict_types
            
            print(f"   Conflict types: {conflict_types}")
            print(f"   Auto-resolve: {conflict_result['auto_resolve']}")
            
            # Check the guest name analysis
            changes = conflict.get_changes_summary()
            guest_info = changes.get('guest', {})
            
            print(f"\n📊 GUEST NAME CONFLICT ANALYSIS:")
            print(f"   Current: '{guest_info.get('current')}'")
            print(f"   Excel: '{guest_info.get('excel')}'") 
            print(f"   Analysis: {guest_info.get('analysis')}")
            print(f"   Change type: {guest_info.get('change_type')}")
            print(f"   Likely encoding issue: {guest_info.get('likely_encoding_issue')}")
            
            # This should NOT auto-resolve (per your requirement)
            if not conflict_result['auto_resolve']:
                print("✅ Correctly flagged for manual review (not auto-resolved)")
            else:
                print("❌ Should require manual review, not auto-resolve")
                
            # The conflict info should help the user understand it's likely an encoding fix
            if guest_info.get('likely_encoding_issue'):
                print("✅ Correctly identified as likely encoding issue")
            else:
                print("❌ Should have identified as encoding issue")
                
            return not conflict_result['auto_resolve'] and guest_info.get('likely_encoding_issue')
            
        else:
            print("❌ Should have detected guest name conflict!")
            return False
        
    except Exception as e:
        print(f"❌ Error during testing: {e}")
        import traceback
        traceback.print_exc()
        return False
    
    # Cleanup
    try:
        if booking:
            booking.delete()
        if prop:
            prop.delete()
    except:
        pass

def main():
    print("🚀 GUEST NAME CONFLICT ANALYSIS TESTING")
    print("Testing encoding issues and guest name analysis")
    print("=" * 80)
    
    # Test the analysis function
    test_guest_name_analysis()
    
    # Test the real-world scenario
    success = test_real_world_guest_name_conflict()
    
    print("\n" + "=" * 80)
    if success:
        print("✅ GUEST NAME CONFLICT ANALYSIS WORKING!")
        print("🎯 Encoding issues like 'MĂ¼ller' → 'Muller' will be flagged for review")
        print("📋 Detailed analysis helps users make informed decisions")
    else:
        print("❌ Guest name conflict analysis needs refinement")
    print("=" * 80)
    
    return success

if __name__ == '__main__':
    main()
