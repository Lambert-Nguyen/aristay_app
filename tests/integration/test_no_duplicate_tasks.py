#!/usr/bin/env python3
"""
Regression test to ensure no duplicate template-created tasks per booking
Based on agent colleague's recommendation to prevent the duplicate task issue from recurring
"""
import os
import sys
import django

# Add the Django backend to the Python path
sys.path.append('/Users/duylam1407/Workspace/SJSU/aristay_app/aristay_backend')
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'backend.settings')

# Setup Django
django.setup()

from datetime import datetime
from django.contrib.auth.models import User
from django.utils import timezone
from api.models import *
from api.services.enhanced_excel_import_service import EnhancedExcelImportService
import pandas as pd

def test_no_duplicate_template_tasks():
    """Regression test: assert exactly N tasks per booking for N active templates"""
    
    print("🧪 REGRESSION TEST: No Duplicate Template Tasks")
    print("=" * 60)
    
    # Setup test data
    user, _ = User.objects.get_or_create(username='test_regression', defaults={
        'email': 'test@regression.com',
        'first_name': 'Test',
        'last_name': 'Regression'
    })
    
    property_obj, _ = Property.objects.get_or_create(
        name='Regression Test Villa',
        defaults={'address': '123 Test St, Test City, CA 12345'}
    )
    
    # Clean up any existing test templates and create exactly 2 active ones
    # Deactivate ALL existing templates to ensure isolation
    AutoTaskTemplate.objects.all().update(is_active=False)
    AutoTaskTemplate.objects.filter(name__icontains='Regression').delete()
    
    template1 = AutoTaskTemplate.objects.create(
        name='Regression Clean Test',
        task_type='cleaning',
        title_template='Clean {property} for {guest_name}',
        timing_type='before_checkin',
        timing_offset=1,
        created_by=user,
        is_active=True
    )
    
    template2 = AutoTaskTemplate.objects.create(
        name='Regression Inspect Test',
        task_type='inspection',
        title_template='Inspect {property} after {guest_name}',
        timing_type='after_checkout',
        timing_offset=0,
        created_by=user,
        is_active=True
    )
    
    print(f"✓ Created 2 active templates: {template1.name}, {template2.name}")
    
    # Create a test booking
    Task.objects.filter(booking__external_code='REGTEST001').delete()  # Clean up tasks first
    Booking.objects.filter(external_code='REGTEST001').delete()  # Clean up booking
    
    test_data = [{
        'Property': 'Regression Test Villa',
        'Check-in date': '2025-01-01',
        'Check-out date': '2025-01-03',
        'Guest name': 'Test Guest',
        'Source': 'Test Source',
        'Confirmation code': 'REGTEST001',
        'Status': 'Confirmed',
        'Adults': 2,
        'Children': 0,
        'Nights': 2,
        'Guest phone': '+1-555-TEST'
    }]
    
    df = pd.DataFrame(test_data)
    service = EnhancedExcelImportService(user=user)
    service.total_rows = len(df)
    service.import_log = service._create_import_log(None)
    
    # Process the booking (use the same pattern as the main test)
    created_bookings = []
    for index, row in df.iterrows():
        booking_data = {
            'property_label_raw': row['Property'],
            'start_date': timezone.make_aware(datetime.strptime(row['Check-in date'], '%Y-%m-%d')),
            'end_date': timezone.make_aware(datetime.strptime(row['Check-out date'], '%Y-%m-%d')),
            'guest_name': row['Guest name'],
            'source': row['Source'],
            'external_code': row['Confirmation code'],
            'external_status': row['Status'],
            'adults': row['Adults'],
            'children': row['Children'],
            'nights': row['Nights'],
            'guest_phone': row['Guest phone']
        }
        
        # Create booking directly using the internal method
        booking = service._create_booking(booking_data, property_obj, row)
        created_bookings.append(booking)
    
    # Create automated tasks
    task_count = service.create_automated_tasks(created_bookings)
    
    # The critical assertion: exactly 2 tasks per booking (1 per active template)
    expected_tasks = 2  # 2 active templates
    actual_tasks = task_count
    
    print(f"✓ Expected tasks per booking: {expected_tasks}")
    print(f"✓ Actual tasks created: {actual_tasks}")
    
    if actual_tasks == expected_tasks:
        print("🎉 REGRESSION TEST PASSED: No duplicate tasks detected!")
    else:
        print(f"❌ REGRESSION TEST FAILED: Expected {expected_tasks} tasks, got {actual_tasks}")
        # Check for duplicate tasks
        booking = created_bookings[0]  # Get first booking from list
        tasks_by_type = {}
        for task in Task.objects.filter(booking=booking, created_by_template__isnull=False):
            task_type = task.task_type
            tasks_by_type[task_type] = tasks_by_type.get(task_type, 0) + 1
        
        print(f"Tasks by type: {tasks_by_type}")
        for task_type, count in tasks_by_type.items():
            if count > 1:
                print(f"  ❌ DUPLICATE: {count} {task_type} tasks found!")
        
        raise AssertionError(f"Duplicate task creation detected: expected {expected_tasks}, got {actual_tasks}")
    
    # Cleanup
    for booking in created_bookings:
        booking.delete()
    template1.delete()
    template2.delete()
    
    # Restore original template states
    AutoTaskTemplate.objects.filter(name__in=['Post-checkout Inspection', 'Pre-arrival Cleaning']).update(is_active=True)
    
    print("✓ Test completed successfully - no task duplication issues found!")

if __name__ == '__main__':
    try:
        test_no_duplicate_template_tasks()
        print("\n🚀 All regression tests passed!")
    except Exception as e:
        print(f"\n💥 Regression test failed: {e}")
        sys.exit(1)
