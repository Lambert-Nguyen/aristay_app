#!/usr/bin/env python3
"""
Property/Date/Duplicate Safety Checks
"""

import os
import sys
import django
from datetime import timedelta

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'backend.settings')
django.setup()

from api.models import Booking, Property
from django.contrib.auth.models import User
from api.services.enhanced_excel_import_service import EnhancedExcelImportService
from django.utils import timezone
from django.db import transaction

def test_safety_checks():
    """Test property/date/duplicate safety checks"""
    print("🛡️  PROPERTY/DATE/DUPLICATE SAFETY VALIDATION")
    print("=" * 60)
    
    user, _ = User.objects.get_or_create(
        username='safety_user',
        defaults={'email': 'safety@aristay.com'}
    )
    
    # Create properties for testing
    property1, _ = Property.objects.get_or_create(
        name="Safety Villa 1",
        defaults={'address': "123 Safety Ave"}
    )
    
    property2, _ = Property.objects.get_or_create(
        name="Safety Villa 2", 
        defaults={'address': "456 Safety Blvd"}
    )
    
    service = EnhancedExcelImportService(user)
    
    # Test 1: Property Change Conflict
    print(f"\n📝 Test 1: Property Change Conflict")
    
    Booking.objects.filter(external_code='SAFETY_PROP').delete()
    
    test_booking = Booking.objects.create(
        external_code='SAFETY_PROP',
        guest_name='Property Test Guest',
        property=property1,
        check_in_date=timezone.now().date(),
        check_out_date=timezone.now().date() + timedelta(days=2),
        external_status='Confirmed',
        source='Airbnb'
    )
    
    conflict_data = {
        'external_code': 'SAFETY_PROP',
        'guest_name': 'Property Test Guest',
        'property_name': 'Safety Villa 2',  # Different property
        'start_date': timezone.now(),
        'end_date': timezone.now() + timedelta(days=2),
        'external_status': 'Confirmed',
        'source': 'Airbnb'
    }
    
    conflict_result = service._detect_conflicts(conflict_data, property2, row_number=1)
    
    print(f"   Auto-resolve: {conflict_result.get('auto_resolve', 'N/A')}")
    print(f"   Has conflicts: {conflict_result.get('has_conflicts', 'N/A')}")
    
    if conflict_result.get('conflict'):
        print(f"   Conflict types: {conflict_result['conflict'].conflict_types}")
        if 'property_change' in conflict_result['conflict'].conflict_types:
            print(f"   ✅ Property change conflict detected correctly")
        else:
            print(f"   ❌ Property change conflict not detected")
    else:
        print(f"   ⚠️  No conflict object created")
    
    # Test 2: Date Change Conflict
    print(f"\n📝 Test 2: Date Change Conflict")
    
    Booking.objects.filter(external_code='SAFETY_DATE').delete()
    
    # Ensure previous booking is not considered active for exclusion constraint
    # Delete the previous booking to avoid overlap violation on Postgres
    Booking.objects.filter(external_code='SAFETY_PROP').delete()

    test_booking = Booking.objects.create(
        external_code='SAFETY_DATE',
        guest_name='Date Test Guest',
        property=property1,
        check_in_date=timezone.now().date(),
        check_out_date=timezone.now().date() + timedelta(days=3),
        external_status='Confirmed',
        source='VRBO'
    )
    
    conflict_data = {
        'external_code': 'SAFETY_DATE',
        'guest_name': 'Date Test Guest',
        'property_name': 'Safety Villa 1',
        'start_date': timezone.now() + timedelta(days=1),  # Different dates
        'end_date': timezone.now() + timedelta(days=4),
        'external_status': 'Confirmed',
        'source': 'VRBO'
    }
    
    conflict_result = service._detect_conflicts(conflict_data, property1, row_number=1)
    
    print(f"   Auto-resolve: {conflict_result.get('auto_resolve', 'N/A')}")
    print(f"   Has conflicts: {conflict_result.get('has_conflicts', 'N/A')}")
    
    if conflict_result.get('conflict'):
        print(f"   Conflict types: {conflict_result['conflict'].conflict_types}")
        if 'date_change' in conflict_result['conflict'].conflict_types:
            print(f"   ✅ Date change conflict detected correctly")
        else:
            print(f"   ❌ Date change conflict not detected")
    else:
        print(f"   ⚠️  No conflict object created")
    
    # Test 3: Direct Booking Duplicate
    print(f"\n📝 Test 3: Direct Booking Duplicate")
    
    Booking.objects.filter(external_code='SAFETY_DIRECT').delete()
    
    test_booking = Booking.objects.create(
        external_code='SAFETY_DIRECT',
        guest_name='Direct Guest',
        property=property1,
        check_in_date=timezone.now().date() + timedelta(days=5),
        check_out_date=timezone.now().date() + timedelta(days=7),
        external_status='Confirmed',
        source='Direct'
    )
    
    conflict_data = {
        'external_code': 'SAFETY_DIRECT',
        'guest_name': 'Direct Guest',
        'property_name': 'Safety Villa 1',
        'start_date': timezone.now() + timedelta(days=5),
        'end_date': timezone.now() + timedelta(days=7),
        'external_status': 'Confirmed',
        'source': 'Direct'
    }
    
    conflict_result = service._detect_conflicts(conflict_data, property1, row_number=1)
    
    print(f"   Auto-resolve: {conflict_result.get('auto_resolve', 'N/A')}")
    print(f"   Has conflicts: {conflict_result.get('has_conflicts', 'N/A')}")
    
    if not conflict_result.get('auto_resolve', True):  # Should be False
        print(f"   ✅ Direct booking duplicate requires manual review")
    else:
        print(f"   ❌ Direct booking duplicate should not auto-resolve")
    
    # Cleanup
    Booking.objects.filter(external_code__in=['SAFETY_PROP', 'SAFETY_DATE', 'SAFETY_DIRECT']).delete()
    Property.objects.filter(name__startswith='Safety Villa').delete()

if __name__ == '__main__':
    test_safety_checks()
