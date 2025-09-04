"""
Agent's Phase 2: Audit system signals and middleware hooks
Auto-capture create/update/delete operations with who/where context
Fixed per GPT agent recommendations: contextvars + pre_save snapshots
"""
import uuid
from contextvars import ContextVar
from django.db.models.signals import pre_save, post_save, post_delete
from django.dispatch import receiver
from django.contrib.auth import get_user_model
import logging

logger = logging.getLogger(__name__)

# Context variables for Django async compatibility (GPT agent fix)
_ctx: ContextVar[dict] = ContextVar(
    "audit_ctx",
    default={"user": None, "request_id": None, "ip_address": None, "user_agent": ""},
)
_pre_save_snapshots: ContextVar[dict] = ContextVar("audit_snap", default={})

User = get_user_model()


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


def _snapshot_instance(instance):
    """Shallow snapshot of field values for pre_save comparison."""
    return {f.name: getattr(instance, f.name, None) for f in instance._meta.fields}


def _serialize_value(value):
    """Serialize a value for JSON storage."""
    if value is None:
        return None
    if hasattr(value, 'isoformat'):
        return value.isoformat()
    if hasattr(value, 'pk'):
        return {'id': value.pk, 'str': str(value)}
    return value


@receiver(pre_save)
def audit_pre_save(sender, instance, **kwargs):
    """Capture instance state before save for proper diff."""
    # Avoid auditing the AuditEvent itself to prevent recursion
    if sender.__name__ in ['AuditEvent', 'Session', 'LogEntry', 'Migration']:
        return
    
    cache = dict(_pre_save_snapshots.get())
    cache[(sender, instance.pk or id(instance))] = _snapshot_instance(instance)
    _pre_save_snapshots.set(cache)


@receiver(post_save)
def audit_post_save(sender, instance, created, **kwargs):
    """Capture create/update operations with proper change detection."""
    # Avoid auditing the AuditEvent itself to prevent recursion
    if sender.__name__ in ['AuditEvent', 'Session', 'LogEntry', 'Migration']:
        return
    
    if created:
        # Handle creation
        changes = {
            'action': 'create',
            'new_values': {f.name: _serialize_value(getattr(instance, f.name, None)) 
                          for f in instance._meta.fields}
        }
        create_audit_event(instance, 'create', changes)
    else:
        # Handle update with proper diff from pre_save snapshot
        cache = dict(_pre_save_snapshots.get())
        snap = cache.pop((sender, instance.pk or id(instance)), None)
        _pre_save_snapshots.set(cache)
        
        changes = {'action': 'update', 'fields_changed': [], 'old_values': {}, 'new_values': {}}
        
        if snap:
            # Build proper diff using snapshot vs current state
            for f in instance._meta.fields:
                name = f.name
                old = snap.get(name)
                new = getattr(instance, name, None)
                if old != new:
                    changes['fields_changed'].append(name)
                    changes['old_values'][name] = _serialize_value(old)
                    changes['new_values'][name] = _serialize_value(new)
        
        create_audit_event(instance, 'update', changes)


@receiver(post_delete)
def audit_post_delete(sender, instance, **kwargs):
    """Capture delete operations."""
    # Avoid auditing the AuditEvent itself to prevent recursion
    if sender.__name__ in ['AuditEvent', 'Session', 'LogEntry', 'Migration']:
        return
    
    changes = {
        'action': 'delete',
        'deleted_object': {
            'id': instance.pk,
            'str': str(instance),
            'model': instance.__class__.__name__
        }
    }
    
    create_audit_event(instance, 'delete', changes)


def create_audit_event(instance, action, changes=None):
    """Create an audit event for the given instance and action."""
    # Avoid importing at module level to prevent circular imports
    from api.models import AuditEvent
    
    ctx = get_audit_context()
    
    try:
        AuditEvent.objects.create(
            object_type=instance.__class__.__name__,
            object_id=str(instance.pk) if instance.pk else str(id(instance)),
            action=action,
            actor=ctx['user'],
            request_id=ctx['request_id'],
            ip_address=ctx['ip_address'],
            user_agent=ctx['user_agent'],
            changes=changes or {'action': action},
        )
        logger.debug(f"Created audit event: {ctx.get('user', 'System')} {action} {instance.__class__.__name__}:{instance.pk}")
    except Exception as e:
        logger.error(f"Failed to create audit event: {e}")
