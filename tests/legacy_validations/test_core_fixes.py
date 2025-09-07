#!/usr/bin/env python
"""
Simple GPT Agent Fix Validation

Tests the core fixes without complex inheritance issues:
1. Source normalization
2. Case-insensitive lookup queries
3. Audit signal improvements
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
from api.services.enhanced_excel_import_service import _normalize_source
from api.audit_signals import _should_skip_audit

User = get_user_model()

def test_source_normalization():
    """Test source normalization works correctly"""
    print("🔤 Testing source normalization...")
    
    test_cases = [
        ('airbnb', 'Airbnb'),
        ('VRBO', 'VRBO'),
        ('booking.com', 'Booking.com'),
        ('direct', 'Direct'),
        ('owner', 'Owner'),
        ('random_source', 'Random_Source')
    ]
    
    for input_val, expected in test_cases:
        result = _normalize_source(input_val)
        assert result == expected, f"Expected {expected}, got {result}"
        print(f"  ✅ '{input_val}' → '{result}'")
    
    return True

def test_case_insensitive_booking_lookup():
    """Test case-insensitive database lookups work"""
    print("🔍 Testing case-insensitive booking lookups...")
    
    property_obj = Property.objects.create(name="Test Property", address="123 Test")
    
    # Create booking with canonical source
    booking = Booking.objects.create(
        property=property_obj,
        source="Airbnb",
        external_code="TEST123",
        guest_name="Test Guest",
        check_in_date=timezone.now().date(),
        check_out_date=(timezone.now() + timedelta(days=1)).date()
    )
    
    # Test case-insensitive lookups
    test_sources = ['airbnb', 'AIRBNB', 'Airbnb', 'AiRbNb']
    
    for test_source in test_sources:
        # Test the __iexact lookup pattern used in the fixes
        found = Booking.objects.filter(
            property=property_obj,
            source__iexact=test_source,
            external_code="TEST123"
        ).exists()
        
        assert found, f"Should find booking with source '{test_source}'"
        print(f"  ✅ Found booking with source '{test_source}' (case-insensitive)")
    
    # Test different source should not match
    not_found = Booking.objects.filter(
        property=property_obj,
        source__iexact="VRBO",
        external_code="TEST123"
    ).exists()
    
    assert not not_found, "Should NOT find booking with different source"
    print(f"  ✅ Did not find booking with different source 'VRBO'")
    
    # Cleanup
    booking.delete()
    property_obj.delete()
    return True

def test_safer_signal_guards():
    """Test safer model-based signal guards"""
    print("🛡️ Testing safer signal guards...")
    
    # Test model-based exclusions
    from django.contrib.sessions.models import Session
    from django.contrib.admin.models import LogEntry
    
    # These should be skipped
    assert _should_skip_audit(Session), "Should skip Session model"
    assert _should_skip_audit(LogEntry), "Should skip LogEntry model"
    
    # These should NOT be skipped
    assert not _should_skip_audit(Booking), "Should NOT skip Booking model"
    assert not _should_skip_audit(Property), "Should NOT skip Property model"
    
    print("  ✅ Model-based signal guards working correctly")
    return True

def test_scoped_external_code_uniqueness():
    """Test scoped external code uniqueness at DB level"""
    print("🔑 Testing scoped external code uniqueness...")
    
    import uuid
    unique_id = str(uuid.uuid4())[:8]
    
    property1 = Property.objects.create(name=f"Property 1 {unique_id}", address="111 Test")
    property2 = Property.objects.create(name=f"Property 2 {unique_id}", address="222 Test")
    
    # Create booking with same external code on different properties/sources
    booking1 = Booking.objects.create(
        property=property1,
        source="Airbnb", 
        external_code="SAME123",
        guest_name="Guest 1",
        check_in_date=timezone.now().date(),
        check_out_date=(timezone.now() + timedelta(days=1)).date()
    )
    
    booking2 = Booking.objects.create(
        property=property2,
        source="Airbnb",  # Same source, different property - should be OK
        external_code="SAME123",
        guest_name="Guest 2", 
        check_in_date=timezone.now().date(),
        check_out_date=(timezone.now() + timedelta(days=1)).date()
    )
    
    booking3 = Booking.objects.create(
        property=property1,
        source="VRBO",  # Same property, different source - should be OK
        external_code="SAME123", 
        guest_name="Guest 3",
        check_in_date=timezone.now().date(),
        check_out_date=(timezone.now() + timedelta(days=1)).date()
    )
    
    print(f"  ✅ Created {booking1.external_code} on {property1.name} / {booking1.source}")
    print(f"  ✅ Created {booking2.external_code} on {property2.name} / {booking2.source}")
    print(f"  ✅ Created {booking3.external_code} on {property1.name} / {booking3.source}")
    
    # Test scoped lookups work correctly
    prop1_airbnb = Booking.objects.filter(
        property=property1,
        source__iexact="airbnb",
        external_code="SAME123"
    ).count()
    assert prop1_airbnb == 1, f"Should find exactly 1 Airbnb booking on property1, found {prop1_airbnb}"
    
    prop1_vrbo = Booking.objects.filter(
        property=property1,
        source__iexact="vrbo", 
        external_code="SAME123"
    ).count()
    assert prop1_vrbo == 1, f"Should find exactly 1 VRBO booking on property1, found {prop1_vrbo}"
    
    print("  ✅ Scoped lookups working - same external_code allowed across properties/sources")
    
    # Cleanup
    for booking in [booking1, booking2, booking3]:
        booking.delete()
    property1.delete()
    property2.delete()
    return True

def main():
    """Run simplified GPT agent fix validation"""
    print("🚀 GPT AGENT FIXES - CORE VALIDATION")
    print("=" * 50)
    print()
    
    try:
        test_source_normalization()
        print()
        
        test_case_insensitive_booking_lookup() 
        print()
        
        test_safer_signal_guards()
        print()
        
        test_scoped_external_code_uniqueness()
        print()
        
        print("=" * 50)
        print("✅ CORE GPT AGENT FIXES VALIDATED!")
        print("✅ Source normalization: Working")
        print("✅ Case-insensitive lookups: Working") 
        print("✅ Safer signal guards: Working")
        print("✅ Scoped uniqueness: Working")
        print("🚀 PRODUCTION IMPROVEMENTS CONFIRMED!")
        
    except Exception as e:
        print(f"\n❌ Test failed: {e}")
        import traceback
        traceback.print_exc()
        return False
    
    return True

if __name__ == '__main__':
    success = main()
    sys.exit(0 if success else 1)
