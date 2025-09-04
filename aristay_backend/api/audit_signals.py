"""
Agent's Phase 2: Audit system signals and middleware hooks
Auto-capture create/update/delete operations with who/where context
"""
import uuid
from django.db.models.signals import post_save, post_delete
from django.dispatch import receiver
from django.contrib.contenttypes.models import ContentType
from django.contrib.auth import get_user_model
from threading import local
import logging

logger = logging.getLogger(__name__)

# Thread-local storage for request context
_audit_context = local()

User = get_user_model()


def set_audit_context(user=None, request_id=None, ip_address=None, user_agent=None):
    """Set audit context for the current thread."""
    _audit_context.user = user
    _audit_context.request_id = request_id or str(uuid.uuid4())
    _audit_context.ip_address = ip_address
    _audit_context.user_agent = user_agent


def get_audit_context():
    """Get audit context for the current thread."""
    return {
        'user': getattr(_audit_context, 'user', None),
        'request_id': getattr(_audit_context, 'request_id', str(uuid.uuid4())),
        'ip_address': getattr(_audit_context, 'ip_address', None),
        'user_agent': getattr(_audit_context, 'user_agent', ''),
    }


def clear_audit_context():
    """Clear audit context for the current thread."""
    for attr in ['user', 'request_id', 'ip_address', 'user_agent']:
        if hasattr(_audit_context, attr):
            delattr(_audit_context, attr)


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
            if hasattr(value, 'isoformat'):  # datetime objects
                value = value.isoformat()
            elif hasattr(value, 'pk'):  # Foreign key objects
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
                    if hasattr(old_value, 'isoformat'):
                        old_value = old_value.isoformat()
                    elif hasattr(old_value, 'pk'):
                        old_value = {'id': old_value.pk, 'str': str(old_value)}
                    
                    if hasattr(new_value, 'isoformat'):
                        new_value = new_value.isoformat()
                    elif hasattr(new_value, 'pk'):
                        new_value = {'id': new_value.pk, 'str': str(new_value)}
                    
                    changes['fields_changed'].append(field_name)
                    changes['old_values'][field_name] = old_value
                    changes['new_values'][field_name] = new_value
            
            return changes
        except instance.__class__.DoesNotExist:
            # Instance doesn't exist in DB yet, treat as create
            return get_model_changes(instance, created=True)


# Agent's recommendation: Auto-capture create/update/delete signals
@receiver(post_save)
def audit_post_save(sender, instance, created, **kwargs):
    """Audit create and update operations."""
    # Skip audit events themselves and certain system models
    if sender.__name__ in ['AuditEvent', 'Session', 'LogEntry', 'Migration']:
        return
    
    action = 'create' if created else 'update'
    changes = get_model_changes(instance, created=created)
    
    create_audit_event(instance, action, changes)


@receiver(post_delete)
def audit_post_delete(sender, instance, **kwargs):
    """Audit delete operations."""
    # Skip audit events themselves and certain system models
    if sender.__name__ in ['AuditEvent', 'Session', 'LogEntry', 'Migration']:
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
        
        if hasattr(value, 'isoformat'):
            value = value.isoformat()
        elif hasattr(value, 'pk'):
            value = {'id': value.pk, 'str': str(value)}
        
        changes['deleted_object'][field_name] = value
    
    create_audit_event(instance, 'delete', changes)
