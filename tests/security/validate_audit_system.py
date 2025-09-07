#!/usr/bin/env python
"""
Phase 2 Audit System Validation Script
Quick functional test of the GPT agent's structured audit system
"""
import os
import sys
import django
import uuid
from datetime import datetime

# Add the current directory (where this script resides) to Python path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

# Set Django settings
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'backend.settings')

# Configure Django
django.setup()

from django.contrib.auth import get_user_model
from django.utils import timezone
from api.models import Property, Task, AuditEvent
from api.audit_signals import set_audit_context, get_audit_context, clear_audit_context

User = get_user_model()

def test_audit_system():
    """Test the complete audit system functionality."""
    print("🔍 Phase 2 Audit System Validation")
    print("=" * 50)
    
    # Generate unique suffix for this test run
    test_id = str(uuid.uuid4())[:8]
    
    # Create test user
    user, created = User.objects.get_or_create(
        username='audit_test_user',
        defaults={'email': 'audit@test.com'}
    )
    print(f"✓ Test user: {user.username} ({'created' if created else 'existing'})")
    
    # Test 1: Context Management
    print("\n1. Testing Audit Context Management")
    set_audit_context(
        user=user,
        request_id='test-123',
        ip_address='192.168.1.100',
        user_agent='Test Agent'
    )
    
    context = get_audit_context()
    assert context['user'] == user, "User context not set correctly"
    assert context['request_id'] == 'test-123', "Request ID not set correctly"
    assert context['ip_address'] == '192.168.1.100', "IP address not set correctly"
    print("✓ Audit context management working")
    
    # Test 2: Property Creation Audit
    print("\n2. Testing Property Creation Audit")
    initial_count = AuditEvent.objects.count()
    
    property_obj = Property.objects.create(
        name=f'Test Audit Property {test_id}',
        address=f'123 Test St {test_id}',
        created_by=user
    )
    
    final_count = AuditEvent.objects.count()
    assert final_count == initial_count + 1, f"Expected 1 new audit event, got {final_count - initial_count}"
    
    audit_event = AuditEvent.objects.latest('created_at')
    assert audit_event.object_type == 'Property', f"Expected Property, got {audit_event.object_type}"
    assert audit_event.action == 'create', f"Expected create, got {audit_event.action}"
    assert audit_event.actor == user, f"Expected {user}, got {audit_event.actor}"
    assert audit_event.request_id == 'test-123', f"Expected test-123, got {audit_event.request_id}"
    print(f"✓ Property creation audit captured: ID {audit_event.pk}")
    
    # Test 3: Property Update Audit
    print("\n3. Testing Property Update Audit")
    update_count = AuditEvent.objects.count()
    
    property_obj.name = f'Updated Test Property {test_id}'
    property_obj.save()
    
    updated_count = AuditEvent.objects.count()
    assert updated_count == update_count + 1, "Update audit event not created"
    
    update_event = AuditEvent.objects.latest('created_at')
    assert update_event.action == 'update', f"Expected update, got {update_event.action}"
    assert 'fields_changed' in update_event.changes, "fields_changed not in changes"
    print(f"✓ Property update audit captured (fields changed: {update_event.changes['fields_changed']})")
    
    # Check if we have old/new values even if fields_changed is different
    if 'old_values' in update_event.changes and 'new_values' in update_event.changes:
        print(f"  - Old values: {update_event.changes['old_values']}")
        print(f"  - New values: {update_event.changes['new_values']}")
    else:
        print(f"  - Changes structure: {list(update_event.changes.keys())}")
    
    # Test 4: Task Creation with Agent Features
    print("\n4. Testing Task Creation with Agent Features")
    task_count = AuditEvent.objects.count()
    
    task = Task.objects.create(
        title=f'Test Audit Task {test_id}',
        description='Testing the audit system',
        property=property_obj,
        status='pending',
        is_locked_by_user=True,  # Agent's lock feature
        created_by=user
    )
    
    task_audit_count = AuditEvent.objects.count()
    assert task_audit_count == task_count + 1, "Task creation audit event not created"
    
    task_event = AuditEvent.objects.latest('created_at')
    assert task_event.object_type == 'Task', f"Expected Task, got {task_event.object_type}"
    assert 'is_locked_by_user' in task_event.changes['new_values'], "Agent's lock field not captured"
    print(f"✓ Task creation with agent features captured: {task_event.pk}")
    
    # Test 5: Deletion Audit
    print("\n5. Testing Deletion Audit")
    delete_count = AuditEvent.objects.count()
    task_id = task.pk
    
    task.delete()
    
    final_delete_count = AuditEvent.objects.count()
    assert final_delete_count == delete_count + 1, "Delete audit event not created"
    
    delete_event = AuditEvent.objects.latest('created_at')
    assert delete_event.action == 'delete', f"Expected delete, got {delete_event.action}"
    assert delete_event.object_id == str(task_id), f"Expected {task_id}, got {delete_event.object_id}"
    assert 'deleted_object' in delete_event.changes, "deleted_object not in changes"
    print(f"✓ Task deletion audit captured: {delete_event.pk}")
    
    # Test 6: Audit Event Query Performance
    print("\n6. Testing Audit Event Queries")
    
    # Test filtering by object type
    property_events = AuditEvent.objects.filter(object_type='Property')
    task_events = AuditEvent.objects.filter(object_type='Task')
    print(f"✓ Property events: {property_events.count()}")
    print(f"✓ Task events: {task_events.count()}")
    
    # Test filtering by action
    create_events = AuditEvent.objects.filter(action='create')
    update_events = AuditEvent.objects.filter(action='update')
    delete_events = AuditEvent.objects.filter(action='delete')
    print(f"✓ Create events: {create_events.count()}")
    print(f"✓ Update events: {update_events.count()}")
    print(f"✓ Delete events: {delete_events.count()}")
    
    # Test filtering by user
    user_events = AuditEvent.objects.filter(actor=user)
    print(f"✓ User events: {user_events.count()}")
    
    # Test recent events
    recent_events = AuditEvent.objects.filter(
        created_at__gte=timezone.now() - timezone.timedelta(minutes=1)
    )
    print(f"✓ Recent events (last minute): {recent_events.count()}")
    
    # Test 7: JSONB Changes Field
    print("\n7. Testing JSONB Changes Field")
    latest_events = AuditEvent.objects.order_by('-created_at')[:3]
    
    for i, event in enumerate(latest_events, 1):
        changes = event.changes
        print(f"✓ Event {i} changes structure:")
        print(f"   - Action: {changes.get('action', 'N/A')}")
        if 'fields_changed' in changes:
            print(f"   - Fields changed: {changes['fields_changed']}")
        if 'new_values' in changes:
            print(f"   - New values keys: {list(changes['new_values'].keys())}")
        if 'deleted_object' in changes:
            print(f"   - Deleted object ID: {changes['deleted_object'].get('id', 'N/A')}")
    
    # Summary
    print("\n" + "=" * 50)
    print("🎉 Phase 2 Audit System Validation Complete!")
    print(f"Total audit events created: {AuditEvent.objects.count()}")
    print(f"Context management: ✓")
    print(f"Auto-capture signals: ✓")
    print(f"JSONB changes tracking: ✓")
    print(f"Multi-model support: ✓")
    print(f"Agent features integration: ✓")
    print("=" * 50)
    
    # Clean up context
    clear_audit_context()
    print("✓ Context cleared")

if __name__ == '__main__':
    try:
        test_audit_system()
    except Exception as e:
        print(f"❌ Test failed: {e}")
        import traceback
        traceback.print_exc()
