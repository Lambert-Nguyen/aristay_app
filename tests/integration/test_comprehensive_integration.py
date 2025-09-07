#!/usr/bin/env python3
"""
Comprehensive Integration Test Suite

Tests all requested scenarios and verifies that other booking conflicts
properly require user review as requested by the user.
"""

import os
import sys
import django
from datetime import datetime, date

# Add the parent directory to the path to import Django modules
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

# Set up Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'backend.settings')
django.setup()

from api.models import Booking, Property
from django.contrib.auth.models import User
from api.services.enhanced_excel_import_service import EnhancedExcelImportService
from django.utils import timezone
from django.db import transaction

def setup_test_data():
    """Create test data for comprehensive testing"""
    print("🔧 Setting up test data...")
    
    # Create test property
    property_obj, created = Property.objects.get_or_create(
        name="Test Villa",
        defaults={'address': "123 Test St"}
    )
    
    # Create test user
    user, created = User.objects.get_or_create(
        username='testuser',
        defaults={'email': 'test@example.com'}
    )
    
    # Clean up any existing test bookings
    Booking.objects.filter(external_code__in=[
        'HMZE8BT5AC', 'HMDNHY93WB', 'HMHCA35ERM', 'TEST123', 'TEST456'
    ]).delete()
    
    # Create test bookings for various scenarios
    test_bookings = [
        # HMZE8BT5AC - Guest name encoding issue
        {
            'external_code': 'HMZE8BT5AC',
            'guest_name': 'Kathrin MĂ¼ller',  # Encoding issue
            'property': property_obj,
            'check_in_date': timezone.now().date(),
            'check_out_date': timezone.now().date() + timezone.timedelta(days=3),
            'external_status': 'Confirmed',
            'source': 'Airbnb'
        },
        
        # HMDNHY93WB - Status-only change
        {
            'external_code': 'HMDNHY93WB',
            'guest_name': 'John Smith',
            'property': property_obj,
            'check_in_date': timezone.now().date(),
            'check_out_date': timezone.now().date() + timezone.timedelta(days=2),
            'external_status': 'Confirmed',
            'source': 'Airbnb'
        },
        
        # HMHCA35ERM - Status-only change
        {
            'external_code': 'HMHCA35ERM',
            'guest_name': 'Jane Doe',
            'property': property_obj,
            'check_in_date': timezone.now().date() + timezone.timedelta(days=5),
            'check_out_date': timezone.now().date() + timezone.timedelta(days=7),
            'external_status': 'Confirmed',
            'source': 'VRBO'
        },
        
        # TEST123 - Date conflict test
        {
            'external_code': 'TEST123',
            'guest_name': 'Test Guest',
            'property': property_obj,
            'check_in_date': timezone.now().date() + timezone.timedelta(days=10),
            'check_out_date': timezone.now().date() + timezone.timedelta(days=12),
            'external_status': 'Confirmed',
            'source': 'Direct'
        },
        
        # TEST456 - Property conflict test
        {
            'external_code': 'TEST456',
            'guest_name': 'Another Guest',
            'property': property_obj,
            'check_in_date': timezone.now().date() + timezone.timedelta(days=15),
            'check_out_date': timezone.now().date() + timezone.timedelta(days=17),
            'external_status': 'Confirmed',
            'source': 'Booking.com'
        }
    ]
    
    created_bookings = []
    for booking_data in test_bookings:
        booking = Booking.objects.create(**booking_data)
        created_bookings.append(booking)
    
    print(f"✅ Created {len(created_bookings)} test bookings")
    return property_obj, user, created_bookings

def test_specific_scenarios():
    """Test all requested specific scenarios"""
    print("\n🎯 TESTING SPECIFIC REQUESTED SCENARIOS")
    print("=" * 60)
    
    property_obj, user, _ = setup_test_data()
    service = EnhancedExcelImportService(user)
    
    test_cases = [
        {
            'name': 'HMZE8BT5AC - Encoding correction (should require manual review)',
            'excel_data': {
                'external_code': 'HMZE8BT5AC',
                'guest_name': 'Kathrin Muller',  # Fixed encoding
                'property_name': 'Test Villa',
                'start_date': timezone.now(),
                'end_date': timezone.now() + timezone.timedelta(days=3),
                'external_status': 'Confirmed',
                'source': 'Airbnb'
            },
            'expected_auto_resolve': False,  # Should require manual review
            'expected_conflicts': ['guest_change'],
            'expected_analysis_type': 'encoding_correction'
        },
        
        {
            'name': 'HMDNHY93WB - Status-only change (should auto-update)',
            'excel_data': {
                'external_code': 'HMDNHY93WB',
                'guest_name': 'John Smith',  # Same guest
                'property_name': 'Test Villa',
                'start_date': timezone.now(),
                'end_date': timezone.now() + timezone.timedelta(days=2),
                'external_status': 'Checking out today',  # Status change
                'source': 'Airbnb'
            },
            'expected_auto_resolve': True,  # Should auto-update
            'expected_conflicts': ['status_change'],
            'expected_analysis_type': None  # No guest name analysis
        },
        
        {
            'name': 'HMHCA35ERM - Status-only change (should auto-update)',
            'excel_data': {
                'external_code': 'HMHCA35ERM',
                'guest_name': 'Jane Doe',  # Same guest
                'property_name': 'Test Villa',
                'start_date': timezone.now() + timezone.timedelta(days=5),
                'end_date': timezone.now() + timezone.timedelta(days=7),
                'external_status': 'Checking out today',  # Status change
                'source': 'VRBO'
            },
            'expected_auto_resolve': True,  # Should auto-update
            'expected_conflicts': ['status_change'],
            'expected_analysis_type': None  # No guest name analysis
        },
        
        {
            'name': 'José García → Jose Garcia (diacritics, should require manual review)',
            'excel_data': {
                'external_code': 'NEW001',
                'guest_name': 'Jose Garcia',  # ASCII version
                'property_name': 'Test Villa',
                'start_date': timezone.now() + timezone.timedelta(days=20),
                'end_date': timezone.now() + timezone.timedelta(days=23),
                'external_status': 'Confirmed',
                'source': 'Airbnb'
            },
            'existing_guest_name': 'José García',  # Create booking with diacritics
            'expected_auto_resolve': False,  # Should require manual review
            'expected_conflicts': ['guest_change'],
            'expected_analysis_type': 'diacritics_only'
        },
        
        {
            'name': 'Combined status + guest change (should require manual review)',
            'excel_data': {
                'external_code': 'COMBINED001',
                'guest_name': 'Johnny Smith',  # Different guest name
                'property_name': 'Test Villa',
                'start_date': timezone.now() + timezone.timedelta(days=25),
                'end_date': timezone.now() + timezone.timedelta(days=27),
                'external_status': 'Checked Out',  # Different status
                'source': 'Airbnb'
            },
            'existing_guest_name': 'John Smith',  # Create booking with different name
            'existing_status': 'Confirmed',
            'expected_auto_resolve': False,  # Should require manual review
            'expected_conflicts': ['guest_change', 'status_change'],
            'expected_analysis_type': 'minor_correction'
        }
    ]
    
    passed = 0
    failed = 0
    
    for i, case in enumerate(test_cases, 1):
        print(f"\n📝 Test Case {i}: {case['name']}")
        
        try:
            # Create specific booking if needed
            if 'existing_guest_name' in case:
                existing_booking = Booking.objects.create(
                    external_code=case['excel_data']['external_code'],
                    guest_name=case['existing_guest_name'],
                    property=property_obj,
                    check_in_date=case['excel_data']['start_date'].date(),
                    check_out_date=case['excel_data']['end_date'].date(),
                    external_status=case.get('existing_status', 'Confirmed'),
                    source=case['excel_data']['source']
                )
            
            # Test conflict detection
            conflict_result = service._detect_conflicts(case['excel_data'], property_obj, row_number=1)
            
            # Check auto-resolve expectation
            if conflict_result['auto_resolve'] == case['expected_auto_resolve']:
                print(f"   ✅ Auto-resolve: {conflict_result['auto_resolve']} (as expected)")
            else:
                print(f"   ❌ Auto-resolve: Expected {case['expected_auto_resolve']}, got {conflict_result['auto_resolve']}")
                failed += 1
                continue
            
            # Check conflict types if conflicts exist
            if conflict_result['has_conflicts']:
                actual_conflicts = conflict_result['conflict'].conflict_types
                expected_conflicts = case['expected_conflicts']
                
                if all(expected in actual_conflicts for expected in expected_conflicts):
                    print(f"   ✅ Conflict types: {actual_conflicts}")
                else:
                    print(f"   ❌ Conflict types: Expected {expected_conflicts}, got {actual_conflicts}")
                    failed += 1
                    continue
                
                # Check guest name analysis if expected
                if case['expected_analysis_type']:
                    analysis = conflict_result['conflict'].excel_data.get('_guest_name_analysis', {})
                    if analysis.get('type') == case['expected_analysis_type']:
                        print(f"   ✅ Analysis type: {analysis.get('type')}")
                    else:
                        print(f"   ❌ Analysis type: Expected {case['expected_analysis_type']}, got {analysis.get('type')}")
                        failed += 1
                        continue
            
            passed += 1
            
        except Exception as e:
            print(f"   💥 ERROR: {e}")
            failed += 1
        finally:
            # Clean up created booking
            if 'existing_guest_name' in case:
                Booking.objects.filter(external_code=case['excel_data']['external_code']).delete()
    
    print("\n" + "=" * 60)
    print(f"🎯 SPECIFIC SCENARIOS TEST RESULTS:")
    print(f"   ✅ Passed: {passed}")
    print(f"   ❌ Failed: {failed}")
    print(f"   📊 Total: {len(test_cases)}")
    
    return failed == 0

def test_other_conflict_types():
    """Verify that other booking conflicts also require user review"""
    print("\n🔍 TESTING OTHER CONFLICT TYPES REQUIRE MANUAL REVIEW")
    print("=" * 60)
    
    property_obj, user, _ = setup_test_data()
    service = EnhancedExcelImportService(user)
    
    # Create second property for property conflicts
    property2, _ = Property.objects.get_or_create(
        name="Test Villa 2",
        defaults={'address': "456 Test Ave"}
    )
    
    other_conflict_tests = [
        {
            'name': 'Date Change Conflict',
            'existing_data': {
                'external_code': 'DATE001',
                'guest_name': 'Date Test Guest',
                'property': property_obj,
                'check_in_date': timezone.now().date(),
                'check_out_date': timezone.now().date() + timezone.timedelta(days=3),
                'external_status': 'Confirmed',
                'source': 'Airbnb'
            },
            'excel_data': {
                'external_code': 'DATE001',
                'guest_name': 'Date Test Guest',  # Same guest
                'property_name': 'Test Villa',
                'start_date': timezone.now() + timezone.timedelta(days=1),  # Different dates
                'end_date': timezone.now() + timezone.timedelta(days=4),
                'external_status': 'Confirmed',
                'source': 'Airbnb'
            },
            'expected_auto_resolve': False,  # Date changes should require review
            'expected_conflict_type': 'date_change'
        },
        
        {
            'name': 'Property Change Conflict',
            'existing_data': {
                'external_code': 'PROP001',
                'guest_name': 'Property Test Guest',
                'property': property_obj,
                'check_in_date': timezone.now().date() + timezone.timedelta(days=5),
                'check_out_date': timezone.now().date() + timezone.timedelta(days=7),
                'external_status': 'Confirmed',
                'source': 'VRBO'
            },
            'excel_data': {
                'external_code': 'PROP001',
                'guest_name': 'Property Test Guest',  # Same guest
                'property_name': 'Test Villa 2',  # Different property
                'start_date': timezone.now() + timezone.timedelta(days=5),
                'end_date': timezone.now() + timezone.timedelta(days=7),
                'external_status': 'Confirmed',
                'source': 'VRBO'
            },
            'expected_auto_resolve': False,  # Property changes should require review
            'expected_conflict_type': 'property_change'
        },
        
        {
            'name': 'Direct Booking Duplicate',
            'existing_data': {
                'external_code': 'DIRECT001',
                'guest_name': 'Direct Guest',
                'property': property_obj,
                'check_in_date': timezone.now().date() + timezone.timedelta(days=10),
                'check_out_date': timezone.now().date() + timezone.timedelta(days=12),
                'external_status': 'Confirmed',
                'source': 'Direct'
            },
            'excel_data': {
                'external_code': 'DIRECT001',
                'guest_name': 'Direct Guest',  # Exact same
                'property_name': 'Test Villa',
                'start_date': timezone.now() + timezone.timedelta(days=10),
                'end_date': timezone.now() + timezone.timedelta(days=12),
                'external_status': 'Confirmed',
                'source': 'Direct'
            },
            'expected_auto_resolve': False,  # Direct booking duplicates should require review
            'expected_conflict_type': 'duplicate_direct'
        }
    ]
    
    passed = 0
    failed = 0
    
    for i, case in enumerate(other_conflict_tests, 1):
        print(f"\n📝 Test Case {i}: {case['name']}")
        
        try:
            # Create existing booking
            existing_booking = Booking.objects.create(**case['existing_data'])
            
            # Test conflict detection
            conflict_result = service._detect_conflicts(case['excel_data'], property_obj, row_number=1)
            
            # Check that it requires manual review
            if not conflict_result['auto_resolve']:
                print(f"   ✅ Manual review required: {not conflict_result['auto_resolve']}")
            else:
                print(f"   ❌ Should require manual review but auto_resolve=True")
                failed += 1
                continue
            
            # Check conflict type
            if conflict_result['has_conflicts']:
                actual_conflicts = conflict_result['conflict'].conflict_types
                if case['expected_conflict_type'] in actual_conflicts:
                    print(f"   ✅ Conflict type found: {case['expected_conflict_type']}")
                else:
                    print(f"   ❌ Expected {case['expected_conflict_type']}, got {actual_conflicts}")
                    failed += 1
                    continue
            
            passed += 1
            
        except Exception as e:
            print(f"   💥 ERROR: {e}")
            failed += 1
        finally:
            # Clean up
            Booking.objects.filter(external_code=case['existing_data']['external_code']).delete()
    
    print("\n" + "=" * 60)
    print(f"🔍 OTHER CONFLICT TYPES TEST RESULTS:")
    print(f"   ✅ Passed: {passed}")
    print(f"   ❌ Failed: {failed}")
    print(f"   📊 Total: {len(other_conflict_tests)}")
    
    return failed == 0

def cleanup_test_data():
    """Clean up test data"""
    print("\n🧹 Cleaning up test data...")
    Booking.objects.filter(
        external_code__in=['HMZE8BT5AC', 'HMDNHY93WB', 'HMHCA35ERM', 'TEST123', 'TEST456']
    ).delete()
    Property.objects.filter(name__in=['Test Villa', 'Test Villa 2']).delete()

if __name__ == '__main__':
    try:
        print("🚀 COMPREHENSIVE INTEGRATION TEST SUITE")
        print("=" * 60)
        
        with transaction.atomic():
            specific_success = test_specific_scenarios()
            other_conflicts_success = test_other_conflict_types()
            
            overall_success = specific_success and other_conflicts_success
            
            print("\n" + "=" * 60)
            print("🎯 OVERALL RESULTS:")
            print(f"   📝 Specific scenarios: {'✅ PASS' if specific_success else '❌ FAIL'}")
            print(f"   🔍 Other conflict types: {'✅ PASS' if other_conflicts_success else '❌ FAIL'}")
            
            if overall_success:
                print("\n🎉 ALL INTEGRATION TESTS PASSED!")
                print("✅ Guest name changes require manual review")
                print("✅ Status-only changes auto-update") 
                print("✅ Other conflict types require manual review")
                print("✅ Enhanced name analysis working correctly")
                print("🚀 SYSTEM IS PRODUCTION READY!")
            else:
                print("\n⚠️  Some tests failed. Please review implementation.")
            
    except Exception as e:
        print(f"💥 Test suite error: {e}")
    finally:
        cleanup_test_data()
