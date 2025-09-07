"""
Agent's Phase 2: Audit system signals and middleware hooks
Auto-capture create/update/delete operations with who/where context
Fixed per GPT agent recommendations: contextvars + pre_save snapshots + safer signal guards
"""
import uuid
from contextvars import ContextVar
from datetime import date, datetime
from decimal import Decimal
from uuid import UUID
from pathlib import Path
from django.db.models import Model
from django.db.models.fields.files import FieldFile
from django.forms.models import model_to_dict
from django.core.files.uploadedfile import UploadedFile
from django.db.models.signals import pre_save, post_save, post_delete, pre_delete
from django.dispatch import receiver
from django.contrib.auth import get_user_model
from django.contrib.admin.models import LogEntry
from django.contrib.sessions.models import Session
from django.db.migrations.recorder import MigrationRecorder
from django.db import transaction
from django.conf import settings
import logging
import json

logger = logging.getLogger(__name__)

# JSON serialization helpers (Agent recommendation for Cloudinary ImageFieldFile fix)
def _jsonable(value):
    """Coerce values into JSON-safe primitives."""
    if isinstance(value, (datetime, date)):
        return value.isoformat()
    if isinstance(value, FieldFile):
        # Prefer URL if available (already uploaded)
        return getattr(value, "url", None) or value.name or str(value)
    if isinstance(value, UploadedFile):
        return value.name
    if isinstance(value, (bytes, bytearray, memoryview)):
        return f"<{len(value)} bytes>"
    if isinstance(value, (Decimal, UUID, Path)):
        return str(value)
    if isinstance(value, Model):
        return f"{value._meta.label}:{getattr(value, 'pk', None)}"
    # Lists / dicts: coerce their contents
    if isinstance(value, dict):
        return {k: _jsonable(v) for k, v in value.items()}
    if isinstance(value, (list, tuple, set)):
        return [_jsonable(v) for v in value]
    return value

def _safe_model_snapshot(instance, fields=None):
    """Return a JSON-safe dict for a model instance."""
    data = model_to_dict(instance, fields=fields) if fields else model_to_dict(instance)
    return {k: _jsonable(v) for k, v in data.items()}

def _trim_changes(data, max_len=10000):
    """Trim payload size to prevent oversized audit logs."""
    try:
        s = json.dumps(data)
        if len(s) <= max_len:
            return data
    except Exception:
        return data
    
    # Lightweight trim strategy
    def _trim(v):
        if isinstance(v, str) and len(v) > 512:
            return v[:512] + "…"
        if isinstance(v, list) and len(v) > 50:
            return v[:50] + ["…trimmed…"]
        if isinstance(v, dict):
            return {k: _trim(vv) for k, vv in v.items()}
        return v
    return _trim(data)

# Context variables for Django async compatibility (GPT agent fix)
_ctx: ContextVar[dict] = ContextVar(
    "audit_ctx",
    default={"user": None, "request_id": None, "ip_address": None, "user_agent": ""},
)
_pre_save_snapshots: ContextVar[dict] = ContextVar("audit_snap", default={})
_pre_delete_snapshots: ContextVar[dict] = ContextVar("audit_pre_del_snap", default={})

User = get_user_model()

# GPT Agent Fix: Use model references instead of string-based checks for safer signal guards
def _should_skip_audit(sender):
    """Check if model should be skipped from audit based on model class, not string names."""
    # Import AuditEvent lazily to avoid circular imports
    try:
        from api.models import AuditEvent
        from django.contrib.auth.models import Permission
        from django.contrib.contenttypes.models import ContentType
        try:
            from rest_framework.authtoken.models import Token
        except Exception:
            Token = None
        
        skip_models = (AuditEvent, LogEntry, Session, MigrationRecorder.Migration, Permission, ContentType)
        if Token:
            skip_models += (Token,)
        return issubclass(sender, skip_models)
    except ImportError:
        # Fallback to string-based check if imports fail
        return sender.__name__ in ['AuditEvent', 'Session', 'LogEntry', 'Migration', 'Permission', 'ContentType', 'Token']


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
    # Check if audit is enabled
    if not getattr(settings, "AUDIT_ENABLED", True):
        return
    
    # Avoid importing at module level to prevent circular imports
    from api.models import AuditEvent
    
    # Skip auditing AuditEvent itself to prevent infinite loops
    if isinstance(instance, AuditEvent):
        return
    
    context = get_audit_context()
    
    # Ensure changes are JSON-safe and size-limited before storing
    safe_changes = _trim_changes(
        _jsonable(changes) if changes else {},
        max_len=getattr(settings, "AUDIT_MAX_CHANGES_BYTES", 10000),
    )
    
    def _write():
        try:
            ae = AuditEvent.objects.create(
                object_type=instance.__class__.__name__,
                object_id=str(getattr(instance, "pk", "unknown")),
                action=action,
                actor=context["user"],
                changes=safe_changes,
                request_id=context["request_id"],
                ip_address=context["ip_address"],
                user_agent=context["user_agent"],
            )
            logger.debug(f"Created audit event: {ae}")
        except Exception as e:
            logger.error(f"Failed to create audit event for {instance.__class__.__name__}:{getattr(instance,'pk',None)}: {e}")
    
    # Prefer after-commit to avoid breaking main transaction
    conn = transaction.get_connection()
    if conn.in_atomic_block:
        transaction.on_commit(_write)
    else:
        _write()


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
    """Serialize a value for JSON storage - now uses enhanced _jsonable helper."""
    return _jsonable(value)


@receiver(pre_save)
def audit_pre_save(sender, instance, **kwargs):
    """Capture object state before modification for proper change detection."""
    # Check if audit is enabled
    if not getattr(settings, "AUDIT_ENABLED", True):
        return
    
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
    # Check if audit is enabled
    if not getattr(settings, "AUDIT_ENABLED", True):
        return
    
    # GPT Agent Fix: Use safer model-based checks instead of string-based checks
    if _should_skip_audit(sender):
        return
    
    # GPT Agent Fix: Use snapshot-based diff instead of broken DB re-query
    changes = _diff_from_snapshot(sender, instance, created)
    action = 'create' if created else 'update'
    
    create_audit_event(instance, action, changes)


@receiver(pre_delete)
def audit_pre_delete(sender, instance, **kwargs):
    """Capture object state before deletion for safe audit logging."""
    # Check if audit is enabled
    if not getattr(settings, "AUDIT_ENABLED", True):
        return
    
    if _should_skip_audit(sender):
        return
    
    cache = dict(_pre_delete_snapshots.get())
    key = (sender, instance.pk or id(instance))
    
    # Capture a minimal, relation-safe snapshot
    minimal = {
        "model": instance._meta.label,
        "id": getattr(instance, "pk", None),
    }
    
    # Add first few simple fields only
    for f in list(instance._meta.fields)[:5]:
        try:
            minimal[f.name] = _jsonable(getattr(instance, f.name, None))
        except Exception:
            minimal[f.name] = "<unavailable>"
    
    cache[key] = minimal
    _pre_delete_snapshots.set(cache)


@receiver(post_delete)
def audit_post_delete(sender, instance, **kwargs):
    """Audit delete operations using safe pre-delete snapshots."""
    # Check if audit is enabled
    if not getattr(settings, "AUDIT_ENABLED", True):
        return
    
    if _should_skip_audit(sender):
        return
    
    cache = dict(_pre_delete_snapshots.get())
    key = (sender, instance.pk or id(instance))
    snapshot = cache.pop(key, None)
    _pre_delete_snapshots.set(cache)

    changes = {"action": "delete", "deleted_object": snapshot or {
        "model": instance._meta.label,
        "id": getattr(instance, "pk", None),
    }}
    
    create_audit_event(instance, "delete", changes)
