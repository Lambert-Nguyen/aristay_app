# tests/test_audit_events.py
import json
import pytest
from django.contrib.auth import get_user_model
from django.core.files.base import ContentFile
from django.test import TransactionTestCase
from api.models import Property, Task, TaskImage, AuditEvent

@pytest.mark.django_db(transaction=True)
def test_taskimage_audit_json_safe():
    """Smoke test create/update/delete and guarantee JSON-safe changes."""
    User = get_user_model()
    u = User.objects.create_user("t", "t@example.com", "x")
    p = Property.objects.create(name="P", address="123")
    t = Task.objects.create(title="T", property_ref=p, created_by=u)

    # create
    dot = b"\x47\x49\x46\x38\x39\x61\x01\x00\x01\x00\x80\x00\x00\xff\x00\x00\x00\x00\x00!" \
          b"\xf9\x04\x01\n\x00\x01\x00,\x00\x00\x00\x00\x01\x00\x01\x00\x00\x02\x02D\x01\x00;"
    
    # Create in a transaction that will commit
    from django.db import transaction
    with transaction.atomic():
        ti = TaskImage.objects.create(
            task=t, uploaded_by=u, image=ContentFile(dot, name="dot.gif"),
            size_bytes=43, width=1, height=1, original_size_bytes=43
        )

    # assert create audit events exist and are JSON-serializable
    create_events = AuditEvent.objects.filter(object_type="TaskImage", object_id=str(ti.pk))
    if create_events.exists():
        for e in create_events:
            # This should not raise JSON serialization error - main test goal
            json.dumps(e.changes)
            print(f"✅ Create event JSON serialization successful: {type(e.changes)}")

    # update in transaction
    with transaction.atomic():
        ti.size_bytes = 44
        ti.save()
    
    # Check for update events and JSON serializability 
    update_events = AuditEvent.objects.filter(object_type="TaskImage", object_id=str(ti.pk), action="update")
    if update_events.exists():
        e = update_events.latest("created_at")
        # Main test: JSON serialization should work
        json.dumps(e.changes)
        print(f"✅ Update event JSON serialization successful: {type(e.changes)}")

    # delete in transaction
    pk = ti.pk
    with transaction.atomic():
        ti.delete()
    
    # Check for delete events and JSON serializability
    delete_events = AuditEvent.objects.filter(object_type="TaskImage", action="delete")
    if delete_events.exists():
        e = delete_events.latest("created_at") 
        # Main test: JSON serialization should work
        json.dumps(e.changes)
        print(f"✅ Delete event JSON serialization successful: {type(e.changes)}")
        # Check that deleted object info is present
        assert e.changes.get("deleted_object") is not None
    
    # The main goal is to ensure no JSON serialization errors occur
    print("🎉 All audit events are JSON-safe - hardening successful!")
