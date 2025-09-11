#!/usr/bin/env python3
"""
Final Validation Test Suite

Tests all requested fixes and validates that conflicts require manual review.
"""

import os
import sys
import django
from datetime import datetime, date

# Add the aristay_backend directory to the path to import Django modules
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', '..', 'aristay_backend'))

# Set up Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'aristay_backend.backend.settings')
django.setup()

from api.models import Booking, Property
from django.contrib.auth.models import User
from api.services.enhanced_excel_import_service import EnhancedExcelImportService, _analyze_guest_name_difference
from django.utils import timezone
from django.db import transaction

def test_requested_scenarios():
    """Test all specifically requested scenarios"""
    print("🎯 TESTING ALL REQUESTED SCENARIOS")
    print("=" * 50)
    
    # Test 1: HMZE8BT5AC encoding correction analysis
    print("\n📝 Test 1: HMZE8BT5AC encoding analysis")
    analysis = _analyze_guest_name_difference("Kathrin MĂ¼ller", "Kathrin Muller")
    if analysis['type'] == 'encoding_correction' and analysis['likely_encoding_issue']:
        print("   ✅ Encoding correction detected correctly")
    else:
        print(f"   ❌ Expected encoding_correction, got {analysis['type']}")
        return False
    
    # Test 2: Spanish diacritics
    print("\n📝 Test 2: José García → Jose Garcia")
    analysis = _analyze_guest_name_difference("José García", "Jose Garcia")
    if analysis['type'] == 'diacritics_only' and analysis['likely_encoding_issue']:
        print("   ✅ Diacritics-only change detected correctly")
    else:
        print(f"   ❌ Expected diacritics_only, got {analysis['type']}")
        return False
    
    # Test 3: Curly apostrophe
    print("\n📝 Test 3: Curly vs straight apostrophe")
    analysis = _analyze_guest_name_difference("O'Connor", "O'Connor")
    if analysis['type'] == 'diacritics_only':  # Normalization makes them same
        print("   ✅ Apostrophe difference handled correctly")
    else:
        print(f"   ❌ Expected diacritics_only, got {analysis['type']}")
        return False
    
    # Test 4: German ß → ss
    print("\n📝 Test 4: German ß → ss mapping")
    analysis = _analyze_guest_name_difference("Mußler", "Mussler")
    if analysis['type'] == 'diacritics_only' and analysis['likely_encoding_issue']:
        print("   ✅ German ß → ss mapping working")
    else:
        print(f"   ❌ Expected diacritics_only, got {analysis['type']}")
        return False
    
    # Test 5: Minor correction
    print("\n📝 Test 5: Minor typo correction")
    analysis = _analyze_guest_name_difference("John Smith", "Jon Smith")
    if analysis['type'] == 'minor_correction' and not analysis['likely_encoding_issue']:
        print("   ✅ Minor correction detected correctly")
    else:
        print(f"   ❌ Expected minor_correction, got {analysis['type']}")
        return False
    
    # Test 6: Significant change
    print("\n📝 Test 6: Significant name change")
    analysis = _analyze_guest_name_difference("John Smith", "Jane Doe")
    if analysis['type'] == 'significant_change' and not analysis['likely_encoding_issue']:
        print("   ✅ Significant change detected correctly")
    else:
        print(f"   ❌ Expected significant_change, got {analysis['type']}")
        return False
    
    print("\n✅ ALL NAME ANALYSIS TESTS PASSED!")
    return True

def test_conflict_behavior():
    """Test that conflicts behave as expected"""
    print("\n🔍 TESTING CONFLICT BEHAVIOR")
    print("=" * 50)
    
    try:
        # Setup
        user, _ = User.objects.get_or_create(username='testuser', defaults={'email': 'test@example.com'})
        property_obj, _ = Property.objects.get_or_create(
            name="Test Property",
            defaults={'address': "123 Test St"}
        )
        
        # Clean up any existing test data
        Booking.objects.filter(external_code__startswith='TEST_').delete()
        
        service = EnhancedExcelImportService(user)
        
        # Test Case 1: Status-only change should auto-resolve for platform bookings
        print("\n📝 Test 1: Status-only change (platform booking)")
        
        booking1 = Booking.objects.create(
            external_code='TEST_STATUS',
            guest_name='John Smith',
            property=property_obj,
            check_in_date=timezone.now().date() + timezone.timedelta(days=1),
            check_out_date=timezone.now().date() + timezone.timedelta(days=3),
            external_status='Confirmed',
            source='Airbnb'
        )
        
        excel_data_status = {
            'external_code': 'TEST_STATUS',
            'guest_name': 'John Smith',  # Same guest
            'property_name': 'Test Property',
            'start_date': timezone.now().date() + timezone.timedelta(days=1),  # Same dates as existing booking
            'end_date': timezone.now().date() + timezone.timedelta(days=3),    # Same dates as existing booking
            'external_status': 'Checking out today',  # Different status
            'source': 'Airbnb'
        }
        
        conflict_result = service._detect_conflicts(excel_data_status, property_obj, row_number=1)
        
        if conflict_result['auto_resolve'] and 'status_change' in conflict_result['conflict'].conflict_types:
            print("   ✅ Status-only change auto-resolves correctly")
        else:
            print(f"   ❌ Status-only change should auto-resolve, got auto_resolve={conflict_result['auto_resolve']}")
            return False
        
        # Test Case 2: Guest name change should require manual review
        print("\n📝 Test 2: Guest name change (requires manual review)")
        
        booking2 = Booking.objects.create(
            external_code='TEST_GUEST',
            guest_name='Kathrin MĂ¼ller',  # Encoding issue
            property=property_obj,
            check_in_date=timezone.now().date() + timezone.timedelta(days=5),
            check_out_date=timezone.now().date() + timezone.timedelta(days=8),
            external_status='Confirmed',
            source='Airbnb'
        )
        
        excel_data_guest = {
            'external_code': 'TEST_GUEST',
            'guest_name': 'Kathrin Muller',  # Fixed encoding
            'property_name': 'Test Property',
            'start_date': timezone.now(),
            'end_date': timezone.now() + timezone.timedelta(days=3),
            'external_status': 'Confirmed',
            'source': 'Airbnb'
        }
        
        conflict_result = service._detect_conflicts(excel_data_guest, property_obj, row_number=1)
        
        if not conflict_result['auto_resolve'] and 'guest_change' in conflict_result['conflict'].conflict_types:
            print("   ✅ Guest name change requires manual review correctly")
            
            # Check that the analysis is attached
            analysis = conflict_result['conflict'].excel_data.get('_guest_name_analysis', {})
            if analysis.get('type') == 'encoding_correction':
                print("   ✅ Guest name analysis attached correctly")
            else:
                print(f"   ❌ Expected encoding_correction analysis, got {analysis.get('type')}")
                return False
        else:
            print(f"   ❌ Guest name change should require manual review, got auto_resolve={conflict_result['auto_resolve']}")
            return False
        
        # Test Case 3: Direct booking should never auto-resolve
        print("\n📝 Test 3: Direct booking duplicate (never auto-resolve)")
        
        booking3 = Booking.objects.create(
            external_code='TEST_DIRECT',
            guest_name='Direct Guest',
            property=property_obj,
            check_in_date=timezone.now().date() + timezone.timedelta(days=10),
            check_out_date=timezone.now().date() + timezone.timedelta(days=12),
            external_status='Confirmed',
            source='Direct'
        )
        
        excel_data_direct = {
            'external_code': 'TEST_DIRECT',
            'guest_name': 'Direct Guest',  # Same everything
            'property_name': 'Test Property',
            'start_date': timezone.now() + timezone.timedelta(days=5),
            'end_date': timezone.now() + timezone.timedelta(days=7),
            'external_status': 'Confirmed',
            'source': 'Direct'
        }
        
        conflict_result = service._detect_conflicts(excel_data_direct, property_obj, row_number=1)
        
        if not conflict_result['auto_resolve']:
            print("   ✅ Direct booking requires manual review correctly")
        else:
            print(f"   ❌ Direct booking should never auto-resolve, got auto_resolve={conflict_result['auto_resolve']}")
            return False
        
        print("\n✅ ALL CONFLICT BEHAVIOR TESTS PASSED!")
        return True
        
    except Exception as e:
        print(f"   💥 ERROR in conflict behavior test: {e}")
        return False
    finally:
        # Cleanup
        Booking.objects.filter(external_code__startswith='TEST_').delete()

def test_json_serialization():
    """Test that the JSON serialization fix works"""
    print("\n🔧 TESTING JSON SERIALIZATION FIX")
    print("=" * 50)
    
    try:
        user, _ = User.objects.get_or_create(username='testuser', defaults={'email': 'test@example.com'})
        property_obj, _ = Property.objects.get_or_create(
            name="Test Property",
            defaults={'address': "123 Test St"}
        )
        
        # Clean up
        Booking.objects.filter(external_code='TEST_JSON').delete()
        
        service = EnhancedExcelImportService(user)
        
        booking = Booking.objects.create(
            external_code='TEST_JSON',
            guest_name='José García',
            property=property_obj,
            check_in_date=timezone.now().date(),
            check_out_date=timezone.now().date() + timezone.timedelta(days=2),
            external_status='Confirmed',
            source='Airbnb'
        )
        
        excel_data = {
            'external_code': 'TEST_JSON',
            'guest_name': 'Jose Garcia',  # Diacritics removed
            'property_name': 'Test Property',
            'start_date': timezone.now(),
            'end_date': timezone.now() + timezone.timedelta(days=2),
            'external_status': 'Confirmed',
            'source': 'Airbnb'
        }
        
        conflict_result = service._detect_conflicts(excel_data, property_obj, row_number=1)
        
        if conflict_result['has_conflicts']:
            # Test serialization
            serialized = service._serialize_conflict(conflict_result['conflict'])
            
            # Check that changes_summary is still a dict (not a string)
            changes_summary = serialized.get('changes_summary', {})
            if isinstance(changes_summary, dict):
                print("   ✅ JSON serialization working - changes_summary is dict")
                
                # Check for nested guest analysis
                guest_info = changes_summary.get('guest', {})
                if isinstance(guest_info, dict) and 'analysis' in guest_info:
                    print("   ✅ Nested guest analysis preserved correctly")
                    return True
                else:
                    print(f"   ❌ Guest analysis not preserved correctly: {guest_info}")
                    return False
            else:
                print(f"   ❌ changes_summary should be dict, got {type(changes_summary)}")
                return False
        else:
            print("   ❌ Expected conflict but none detected")
            return False
            
    except Exception as e:
        print(f"   💥 ERROR in JSON serialization test: {e}")
        return False
    finally:
        # Cleanup
        Booking.objects.filter(external_code='TEST_JSON').delete()

if __name__ == '__main__':
    print("🚀 FINAL VALIDATION TEST SUITE")
    print("=" * 60)
    
    try:
        with transaction.atomic():
            # Run all tests
            name_analysis_success = test_requested_scenarios()
            conflict_behavior_success = test_conflict_behavior()
            json_serialization_success = test_json_serialization()
            
            overall_success = name_analysis_success and conflict_behavior_success and json_serialization_success
            
            print("\n" + "=" * 60)
            print("🎯 FINAL VALIDATION RESULTS:")
            print(f"   📊 Name Analysis: {'✅ PASS' if name_analysis_success else '❌ FAIL'}")
            print(f"   🔍 Conflict Behavior: {'✅ PASS' if conflict_behavior_success else '❌ FAIL'}")
            print(f"   🔧 JSON Serialization: {'✅ PASS' if json_serialization_success else '❌ FAIL'}")
            
            if overall_success:
                print("\n🎉 ALL REQUESTED IMPROVEMENTS IMPLEMENTED!")
                print("✅ HMZE8BT5AC scenario handled correctly")
                print("✅ Status updates auto-resolve for platform bookings")
                print("✅ Guest name changes require manual review")
                print("✅ Enhanced name analysis with German ß → ss")
                print("✅ JSON serialization preserves nested structures")
                print("✅ Conflict detection works for all scenarios")
                print("🚀 SYSTEM READY FOR PRODUCTION!")
            else:
                print("\n⚠️  Some validations failed. Please review.")
    
    except Exception as e:
        print(f"💥 Test suite error: {e}")
        import traceback
        traceback.print_exc()
