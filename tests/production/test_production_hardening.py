#!/usr/bin/env python3
"""
Additional idempotence and constraint tests as recommended by GPT colleague
Tests for production hardening of task template system
"""
import os
import sys
import django
import pytest

# Add the Django backend to the Python path
backend_path = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..', 'aristay_backend'))
sys.path.append(backend_path)
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'backend.settings')

# Setup Django
django.setup()

from datetime import datetime
from django.contrib.auth.models import User
from django.utils import timezone
from django.db import IntegrityError
from api.models import *
from api.services.enhanced_excel_import_service import EnhancedExcelImportService
import pandas as pd

def test_idempotent_task_creation():
    """Test: call create_automated_tasks([booking]) twice; assert count only increases on first call"""
    
    print("🧪 IDEMPOTENCE TEST: Task Creation")
    print("=" * 50)
    
    # Setup test data
    user, _ = User.objects.get_or_create(username='test_idempotence', defaults={
        'email': 'idempotence@test.com',
        'first_name': 'Test',
        'last_name': 'Idempotence'
    })
    
    property_obj, _ = Property.objects.get_or_create(
        name='Idempotence Test Villa',
        defaults={'address': '123 Idempotent St'}
    )
    
    # Clean up existing tasks for this booking
    Booking.objects.filter(external_code='IDEM001').delete()
    
    booking = Booking.objects.create(
        property=property_obj,
        check_in_date=timezone.make_aware(datetime(2025, 1, 15)),
        check_out_date=timezone.make_aware(datetime(2025, 1, 17)),
        guest_name='Test Guest Idempotent',
        external_code='IDEM001',
        status='confirmed'
    )
    
    service = EnhancedExcelImportService(user=user)
    
    # Get initial task count for this booking
    initial_tasks = Task.objects.filter(booking=booking).count()
    
    # First call - should create tasks
    print("📞 First call to create_automated_tasks...")
    count1 = service.create_automated_tasks([booking])
    tasks_after_first = Task.objects.filter(booking=booking).count()
    
    # Second call - should NOT create additional tasks (idempotent)
    print("📞 Second call to create_automated_tasks...")
    count2 = service.create_automated_tasks([booking])
    tasks_after_second = Task.objects.filter(booking=booking).count()
    
    print(f"✓ Initial tasks: {initial_tasks}")
    print(f"✓ First call created: {count1} tasks")
    print(f"✓ Second call created: {count2} tasks") 
    print(f"✓ Tasks after first call: {tasks_after_first}")
    print(f"✓ Tasks after second call: {tasks_after_second}")
    
    # Assertions - second call should create 0 tasks and total count should not increase
    if count2 == 0 and tasks_after_first == tasks_after_second:
        print("🎉 IDEMPOTENCE TEST PASSED: Second call created no duplicates!")
    else:
        print(f"❌ IDEMPOTENCE TEST FAILED: Second call should create 0 tasks, created {count2}")
        print(f"   Total tasks should remain {tasks_after_first}, but is {tasks_after_second}")
        raise AssertionError(f"Idempotence test failed - expected 0 new tasks on second call, got {count2}")
    
    # Cleanup
    booking.delete()
    
    # Test passes if we reach this point without assertions failing
    assert True

@pytest.mark.django_db
def test_constraint_integrity():
    """Test: try to manually create a second task with same (booking, created_by_template); assert IntegrityError"""
    from django.db import transaction
    
    print("\n🧪 CONSTRAINT TEST: DB-Level Uniqueness")
    print("=" * 50)
    
    # Setup test data
    user, _ = User.objects.get_or_create(username='test_constraint', defaults={
        'email': 'constraint@test.com',
        'first_name': 'Test',
        'last_name': 'Constraint'
    })
    
    property_obj, _ = Property.objects.get_or_create(
        name='Constraint Test Villa',
        defaults={'address': '123 Constraint St'}
    )
    
    # Clean up and create test template
    AutoTaskTemplate.objects.filter(name__icontains='Constraint').delete()
    
    template = AutoTaskTemplate.objects.create(
        name='Constraint Test Template',
        task_type='maintenance',
        title_template='Maintain {property}',
        timing_type='before_checkin',
        timing_offset=2,
        created_by=user,
        is_active=True
    )
    
    # Create test booking
    Booking.objects.filter(external_code='CONST001').delete()
    
    booking = Booking.objects.create(
        property=property_obj,
        check_in_date=timezone.make_aware(datetime(2025, 1, 20)),
        check_out_date=timezone.make_aware(datetime(2025, 1, 22)),
        guest_name='Test Guest Constraint',
        external_code='CONST001',
        status='confirmed'
    )
    
    # Create first task (should succeed)
    print("📝 Creating first task...")
    task1 = Task.objects.create(
        title='First Task',
        task_type='maintenance',
        booking=booking,
        property_ref=property_obj,
        created_by_template=template,
    )
    print(f"✓ First task created successfully: {task1.title}")
    
    # Try to create second task with same booking+template (should fail)
    print("📝 Attempting to create duplicate task...")
    constraint_worked = False
    
    try:
        with transaction.atomic():
            task2 = Task.objects.create(
                title='Duplicate Task',
                task_type='maintenance',
                booking=booking,
                property_ref=property_obj,
                created_by_template=template,
            )
            print(f"❌ CONSTRAINT TEST FAILED: Duplicate task was created: {task2.title}")
            task2.delete()
            assert False, "Constraint test failed - duplicate task was allowed"
            
    except IntegrityError as e:
        # Accept IntegrityError regardless of backend-specific message
        print("🎉 CONSTRAINT TEST PASSED: DB constraint prevented duplicate task!")
        constraint_worked = True
    
    # Cleanup
    try:
        task1.delete()
        booking.delete()
        template.delete()
    except Exception as cleanup_error:
        print(f"Warning: Cleanup error (expected): {cleanup_error}")
    
    assert constraint_worked, "Database constraint test failed"
    
    # Test passes if we reach this point
    assert constraint_worked

def test_status_mapping_consistency():
    """Test: verify unified status mapping works consistently in create and update scenarios"""
    
    print("\n🧪 STATUS MAPPING TEST: Unified Mapping Consistency")
    print("=" * 50)
    
    from api.services.enhanced_excel_import_service import _map_external_status
    
    # Test various status mappings
    test_cases = [
        ('Pending', 'booked'),
        ('Requested', 'booked'),
        ('Confirmed', 'confirmed'),
        ('Cancelled', 'cancelled'),
        ('Canceled', 'cancelled'),
        ('Completed', 'completed'),
        ('Owner Staying', 'owner_staying'),
        ('Currently Hosting', 'currently_hosting'),
        ('Some Random Status', 'confirmed'),  # default fallback
    ]
    
    print("📋 Testing status mappings...")
    for external, expected_internal in test_cases:
        actual_internal = _map_external_status(external)
        if actual_internal == expected_internal:
            print(f"✓ '{external}' → '{actual_internal}' ✅")
        else:
            print(f"❌ '{external}' → '{actual_internal}' (expected '{expected_internal}')")
            raise AssertionError(f"Status mapping inconsistent: {external} → {actual_internal} != {expected_internal}")
    
    print("🎉 STATUS MAPPING TEST PASSED: All mappings are consistent!")
    # Test passes if we reach this point
    assert True

if __name__ == '__main__':
    try:
        test_idempotent_task_creation()
        test_constraint_integrity() 
        test_status_mapping_consistency()
        
        print("\n" + "=" * 60)
        print("🚀 ALL PRODUCTION HARDENING TESTS PASSED!")
        print("✅ Idempotent task creation working")
        print("✅ DB constraints preventing duplicates") 
        print("✅ Status mapping unified and consistent")
        print("=" * 60)
        
    except Exception as e:
        print(f"\n💥 Production hardening test failed: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
