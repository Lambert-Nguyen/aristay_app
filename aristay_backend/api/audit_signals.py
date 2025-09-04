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


def get_model_changes(instance, created=False):
    """Get changes for a model instance."""
    if created:
        # For new instances, all fields are "changes"
        changes = {
            'action': 'create',
            'fields_changed': [],
            'new_values': {}
        }
        
        for field in instance._meta.fields:
            field_name = field.name
            value = getattr(instance, field_name, None)
            
            # Convert to JSON-serializable format
            if hasattr(value, 'isoformat') and value is not None:  # datetime objects
                value = value.isoformat()
            elif hasattr(value, 'pk') and value is not None:  # Foreign key objects
                value = {'id': value.pk, 'str': str(value)}
            
            changes['new_values'][field_name] = value
            changes['fields_changed'].append(field_name)
        
        return changes
    else:
        # For updates, check what actually changed
        if not hasattr(instance, '_state') or not instance._state.db:
            return {}
        
        try:
            # Get the old instance from database
            old_instance = instance.__class__.objects.get(pk=instance.pk)
            changes = {
                'action': 'update',
                'fields_changed': [],
                'old_values': {},
                'new_values': {}
            }
            
            for field in instance._meta.fields:
                field_name = field.name
                old_value = getattr(old_instance, field_name, None)
                new_value = getattr(instance, field_name, None)
                
                if old_value != new_value:
                    # Convert to JSON-serializable format
                    if hasattr(old_value, 'isoformat') and old_value is not None:
                        old_value = old_value.isoformat()
                    elif hasattr(old_value, 'pk') and old_value is not None:
                        old_value = {'id': old_value.pk, 'str': str(old_value)}
                    
                    if hasattr(new_value, 'isoformat') and new_value is not None:
                        new_value = new_value.isoformat()
                    elif hasattr(new_value, 'pk') and new_value is not None:
                        new_value = {'id': new_value.pk, 'str': str(new_value)}
                    
                    changes['fields_changed'].append(field_name)
                    changes['old_values'][field_name] = old_value
                    changes['new_values'][field_name] = new_value
            
            return changes
        except instance.__class__.DoesNotExist:
            # Instance doesn't exist in DB yet, treat as create
            return get_model_changes(instance, created=True)


def _serialize_value(value):
    """Serialize a value for JSON storage."""
    if value is None:
        return None
    if hasattr(value, 'isoformat') and value is not None:
        return value.isoformat()
    if hasattr(value, 'pk') and value is not None:
        return {'id': value.pk, 'str': str(value)}
    return value


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
    """Audit create and update operations."""
    # GPT Agent Fix: Use safer model-based checks instead of string-based checks
    if _should_skip_audit(sender):
        return
    
    action = 'create' if created else 'update'
    changes = get_model_changes(instance, created=created)
    
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
