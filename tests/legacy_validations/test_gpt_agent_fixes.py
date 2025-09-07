#!/usr/bin/env python
"""
GPT Agent Fix Validation Script

Tests all critical fixes from the agent's review:
1. Case-insensitive source comparisons  
2. Scoped booking lookup with proper (property, source, external_code)
3. Date-vs-datetime handling with __date lookups
4. Scoped external code suffixing to prevent duplicates
5. Audit change detection using pre_save snapshots
6. Source normalization consistency
"""

import os
import sys
import django

# Setup Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'backend.settings')
sys.path.append(os.path.dirname(os.path.abspath(__file__)))
django.setup()

from django.contrib.auth import get_user_model
from django.utils import timezone
from datetime import datetime, timedelta
from api.models import Property, Booking, AuditEvent
from api.services.enhanced_excel_import_service import EnhancedExcelImportService, _normalize_source

User = get_user_model()

def test_source_normalization():
    """Test source normalization consistency"""
    print("🔤 Testing source normalization...")
    
    # Test canonical mappings
    test_cases = [
        ('airbnb', 'Airbnb'),
        ('AIRBNB', 'Airbnb'), 
        ('Airbnb', 'Airbnb'),
        ('vrbo', 'VRBO'),
        ('VRBO', 'VRBO'),
        ('booking.com', 'Booking.com'),
        ('direct', 'Direct'),
        ('owner', 'Owner'),
        ('unknown_source', 'Unknown_Source')  # Title case fallback
    ]
    
    for input_source, expected in test_cases:
        result = _normalize_source(input_source)
        assert result == expected, f"Expected {expected}, got {result} for input {input_source}"
        print(f"  ✅ '{input_source}' → '{result}'")
    
    return True

def test_case_insensitive_source_lookup():
    """Test case-insensitive source comparisons in conflict detection"""
    print("🔍 Testing case-insensitive source lookup...")
    
    # Create test data
    user = User.objects.get_or_create(username='test_case_user')[0]
    property_obj = Property.objects.create(name="Test Property", address="123 Test St")
    
    # Create booking with normalized source
    booking = Booking.objects.create(
        property=property_obj,
        source="Airbnb",  # Canonical form
        external_code="TEST123",
        guest_name="John Doe",
        check_in_date=timezone.now().date(),
        check_out_date=(timezone.now() + timedelta(days=2)).date()
    )
    
    service = EnhancedExcelImportService(user)
    
    # Test conflict detection with different case variations
    test_cases = [
        {'source': 'airbnb', 'should_find': True},    # lowercase
        {'source': 'AIRBNB', 'should_find': True},    # uppercase  
        {'source': 'Airbnb', 'should_find': True},    # normalized
        {'source': 'vrbo', 'should_find': False},     # different source
    ]
    
    for case in test_cases:
        booking_data = {
            'external_code': 'TEST123',
            'source': case['source'],
            'guest_name': 'John Updated',
            'start_date': timezone.now(),
            'end_date': timezone.now() + timedelta(days=2)
        }
        
        conflicts = service._detect_conflicts(booking_data, property_obj, 1)
        has_conflict = conflicts.get('has_conflicts', False)
        
        if case['should_find']:
            assert has_conflict, f"Should find conflict for source '{case['source']}'"
            print(f"  ✅ Found conflict for '{case['source']}' (case-insensitive match)")
        else:
            assert not has_conflict, f"Should NOT find conflict for source '{case['source']}'"
            print(f"  ✅ No conflict for '{case['source']}' (different source)")
    
    # Cleanup
    booking.delete()
    property_obj.delete()
    return True

def test_scoped_duplicate_prevention():
    """Test scoped external code suffixing prevents duplicates"""
    print("🛡️ Testing scoped duplicate prevention...")
    
    user = User.objects.get_or_create(username='test_dup_user')[0]
    property1 = Property.objects.create(name="Property 1", address="111 Test St")
    property2 = Property.objects.create(name="Property 2", address="222 Test St")
    
    service = EnhancedExcelImportService(user)
    
    # Create first booking
    booking_data1 = {
        'external_code': 'DUP123',
        'source': 'Airbnb',
        'guest_name': 'Alice Test',
        'start_date': timezone.now(),
        'end_date': timezone.now() + timedelta(days=1),
        'nights': 1
    }
    
    # This should create DUP123
    booking1 = service._create_booking(booking_data1, property1, {})
    assert booking1.external_code == 'DUP123'
    print(f"  ✅ First booking created: {booking1.external_code}")
    
    # Create second booking with same code on same property/source - should get suffix
    booking_data2 = booking_data1.copy()
    booking_data2['guest_name'] = 'Bob Test'
    
    booking2 = service._create_booking(booking_data2, property1, {})
    assert booking2.external_code == 'DUP123 #2'
    print(f"  ✅ Second booking got suffix: {booking2.external_code}")
    
    # Create third booking - should get #3
    booking_data3 = booking_data1.copy() 
    booking_data3['guest_name'] = 'Charlie Test'
    
    booking3 = service._create_booking(booking_data3, property1, {})
    assert booking3.external_code == 'DUP123 #3'
    print(f"  ✅ Third booking got suffix: {booking3.external_code}")
    
    # Create booking on different property - should use original code
    booking4 = service._create_booking(booking_data1, property2, {})
    assert booking4.external_code == 'DUP123'  # Different property, can reuse code
    print(f"  ✅ Different property allows original code: {booking4.external_code}")
    
    # Cleanup
    for booking in [booking1, booking2, booking3, booking4]:
        booking.delete()
    property1.delete()
    property2.delete()
    return True

def test_audit_snapshot_system():
    """Test audit system uses pre_save snapshots correctly"""
    print("📋 Testing audit snapshot system...")
    
    # Clear any existing audit events
    AuditEvent.objects.filter(object_type='Property').delete()
    
    # Create a property (should generate create audit)
    property_obj = Property.objects.create(name="Audit Test Property", address="456 Audit St")
    
    # Check create audit was generated
    create_events = AuditEvent.objects.filter(
        object_type='Property',
        object_id=str(property_obj.pk),
        action='create'
    )
    assert create_events.exists(), "Should have create audit event"
    create_event = create_events.first()
    assert 'new_values' in create_event.changes
    print(f"  ✅ Create audit event generated with new_values")
    
    # Update the property (should generate update audit with proper diff)
    property_obj.name = "Updated Audit Property"
    property_obj.save()
    
    # Check update audit was generated
    update_events = AuditEvent.objects.filter(
        object_type='Property',
        object_id=str(property_obj.pk),
        action='update'
    ).order_by('-id')
    
    assert update_events.exists(), "Should have update audit event"
    update_event = update_events.first()
    
    # Verify proper diff structure
    changes = update_event.changes
    assert 'fields_changed' in changes, "Should have fields_changed"
    assert 'old_values' in changes, "Should have old_values"
    assert 'new_values' in changes, "Should have new_values"
    assert 'name' in changes['fields_changed'], "Name should be in changed fields"
    
    print(f"  ✅ Update audit event has proper diff structure")
    print(f"    - Changed fields: {changes['fields_changed']}")
    print(f"    - Old name: {changes['old_values'].get('name')}")
    print(f"    - New name: {changes['new_values'].get('name')}")
    
    # Cleanup
    property_obj.delete()
    return True

def main():
    """Run all GPT agent fix validation tests"""
    print("🚀 GPT AGENT FIX VALIDATION - COMPREHENSIVE TESTING")
    print("=" * 60)
    print()
    
    try:
        test_source_normalization()
        print()
        
        test_case_insensitive_source_lookup()
        print()
        
        test_scoped_duplicate_prevention()
        print()
        
        test_audit_snapshot_system()
        print()
        
        print("=" * 60)
        print("✅ ALL GPT AGENT FIXES VALIDATED SUCCESSFULLY!")
        print("✅ Case-insensitive source lookups working")
        print("✅ Scoped duplicate prevention working")  
        print("✅ Audit snapshots providing proper diffs")
        print("✅ Source normalization consistent")
        print("✅ Production-ready improvements confirmed!")
        print("🚀 READY FOR DEPLOYMENT!")
        
    except Exception as e:
        print(f"\n❌ Test failed: {e}")
        import traceback
        traceback.print_exc()
        return False
    
    return True

if __name__ == '__main__':
    success = main()
    sys.exit(0 if success else 1)
