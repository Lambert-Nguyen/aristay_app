"""
Agent's Phase 2: Audit system signals and middleware hooks
Auto-capture create/update/delete operations with who/where context
Fixed per GPT agent recommendations: contextvars + pre_save snapshots + safer signal guards
"""
import uuid
from contextvars import ContextVar
from django.db.models.signals import pre_save, post_save, post_delete
from django.dispatch import receiver
from django.contrib.auth import get_user_model
from django.contrib.admin.models import LogEntry
from django.contrib.sessions.models import Session
from django.db.migrations.recorder import MigrationRecorder
import logging

logger = logging.getLogger(__name__)

# Context variables for Django async compatibility (GPT agent fix)
_ctx: ContextVar[dict] = ContextVar(
    "audit_ctx",
    default={"user": None, "request_id": None, "ip_address": None, "user_agent": ""},
)
_pre_save_snapshots: ContextVar[dict] = ContextVar("audit_snap", default={})

User = get_user_model()

# GPT Agent Fix: Use model references instead of string-based checks for safer signal guards
def _should_skip_audit(sender):
    """Check if model should be skipped from audit based on model class, not string names."""
    # Import AuditEvent lazily to avoid circular imports
    try:
        from api.models import AuditEvent
        skip_models = (AuditEvent, LogEntry, Session, MigrationRecorder.Migration)
        return issubclass(sender, skip_models)
    except ImportError:
        # Fallback to string-based check if imports fail
        return sender.__name__ in ['AuditEvent', 'Session', 'LogEntry', 'Migration']


def get_audit_context():
    """Get audit context for the current request."""
    data = dict(_ctx.get())
    if not data.get("request_id"):
        data["request_id"] = uuid.uuid4().hex
        _ctx.set(data)
    return data


def set_audit_context(user=None, request_id=None, ip_address=None, user_agent=""):
    """Set audit context for the current request."""
    d = dict(get_audit_context())
    if user is not None:
        d["user"] = user
    if request_id:
        d["request_id"] = request_id
    if ip_address is not None:
        d["ip_address"] = ip_address
    if user_agent is not None:
        d["user_agent"] = user_agent
    _ctx.set(d)


def clear_audit_context():
    """Clear audit context for the current request."""
    _ctx.set({"user": None, "request_id": uuid.uuid4().hex, "ip_address": None, "user_agent": ""})


def create_audit_event(instance, action, changes=None):
    """Create an audit event for the given instance and action."""
    # Avoid importing at module level to prevent circular imports
    from api.models import AuditEvent
    
    # Skip auditing AuditEvent itself to prevent infinite loops
    if isinstance(instance, AuditEvent):
        return
    
    context = get_audit_context()
    
    try:
        audit_event = AuditEvent.objects.create(
            object_type=instance.__class__.__name__,
            object_id=str(instance.pk) if instance.pk else 'unknown',
            action=action,
            actor=context['user'],
            changes=changes or {},
            request_id=context['request_id'],
            ip_address=context['ip_address'],
            user_agent=context['user_agent'],
        )
        logger.debug(f"Created audit event: {audit_event}")
    except Exception as e:
        logger.error(f"Failed to create audit event for {instance}: {e}")


def _diff_from_snapshot(sender, instance, created):
    """Generate change diff using pre_save snapshot (GPT Agent Fix)"""
    if created:
        # For new instances, all fields are "new"
        changes = {
            'action': 'create',
            'new_values': {f.name: _serialize_value(getattr(instance, f.name, None)) 
                          for f in instance._meta.fields}
        }
        return changes
    
    # For updates, use the pre_save snapshot
    key = (sender, instance.pk or id(instance))
    cache = dict(_pre_save_snapshots.get())
    old_values = cache.get(key, {})
    
    changes = {'action': 'update', 'fields_changed': [], 'old_values': {}, 'new_values': {}}
    
    for f in instance._meta.fields:
        name = f.name
        old_val = old_values.get(name)
        new_val = getattr(instance, name, None)
        if old_val != new_val:
            changes['fields_changed'].append(name)
            changes['old_values'][name] = _serialize_value(old_val)
            changes['new_values'][name] = _serialize_value(new_val)
    
    # Clean up the snapshot after use
    if key in cache:
        cache.pop(key)
        _pre_save_snapshots.set(cache)
    
    return changes


def get_model_changes(instance, created=False):
    """DEPRECATED: Get changes for a model instance - use _diff_from_snapshot instead"""
    # This is kept for backward compatibility but should not be used
    # The GPT agent identified this as broken because it queries DB after save
    return _diff_from_snapshot(instance.__class__, instance, created)


def _serialize_value(value):
    """Serialize a value for JSON storage with FieldFile handling."""
    from django.db.models.fields.files import FieldFile
    from decimal import Decimal
    from datetime import datetime, date
    
    if value is None:
        return None
    if isinstance(value, (str, int, float, bool)):
        return value
    if isinstance(value, Decimal):
        return float(value)
    if isinstance(value, (datetime, date)) and value is not None:
        return value.isoformat()
    if isinstance(value, FieldFile):
        # Save the stored path or empty string
        return value.name or ""
    if hasattr(value, 'pk') and value is not None:
        return {'id': value.pk, 'str': str(value)}
    try:
        return str(value)
    except Exception:
        return "<unserializable>"


@receiver(pre_save)
def audit_pre_save(sender, instance, **kwargs):
    """Capture object state before modification for proper change detection."""
    # GPT Agent Fix: Use safer model-based checks instead of string-based checks
    if _should_skip_audit(sender):
        return
    
    # Store snapshot with cache cleanup as GPT agent recommended
    cache = dict(_pre_save_snapshots.get())
    
    # Clean old snapshots to prevent memory leaks
    cache = {k: v for k, v in list(cache.items())[-100:]}  # Keep last 100
    
    # Store current object state as snapshot for diff calculation
    cache[(sender, instance.pk or id(instance))] = {
        f.name: getattr(instance, f.name, None) for f in instance._meta.fields
    }
    _pre_save_snapshots.set(cache)


# Agent's recommendation: Auto-capture create/update/delete signals
@receiver(post_save)
def audit_post_save(sender, instance, created, **kwargs):
    """Audit create and update operations using pre_save snapshots."""
    # GPT Agent Fix: Use safer model-based checks instead of string-based checks
    if _should_skip_audit(sender):
        return
    
    # GPT Agent Fix: Use snapshot-based diff instead of broken DB re-query
    changes = _diff_from_snapshot(sender, instance, created)
    action = 'create' if created else 'update'
    
    create_audit_event(instance, action, changes)


@receiver(post_delete)
def audit_post_delete(sender, instance, **kwargs):
    """Audit delete operations."""
    # GPT Agent Fix: Use safer model-based checks instead of string-based checks
    if _should_skip_audit(sender):
        return
    
    changes = {
        'action': 'delete',
        'deleted_object': {
            'id': instance.pk,
            'str': str(instance),
        }
    }
    
    # Try to capture some key fields before deletion
    for field in instance._meta.fields[:5]:  # Limit to first 5 fields
        field_name = field.name
        value = getattr(instance, field_name, None)
        
        if hasattr(value, 'isoformat') and value is not None:
            value = value.isoformat()
        elif hasattr(value, 'pk') and value is not None:
            value = {'id': value.pk, 'str': str(value)}
        
        changes['deleted_object'][field_name] = value
    
    create_audit_event(instance, 'delete', changes)
