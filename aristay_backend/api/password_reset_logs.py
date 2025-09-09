"""
Password reset logging utilities
"""
import logging
from django.contrib.auth import get_user_model
from django.utils import timezone
import json

logger = logging.getLogger(__name__)
User = get_user_model()


def log_password_reset_event(user, event_type, request=None, notes=None):
    """
    Log a password reset event for a user
    
    Args:
        user: User instance
        event_type: 'requested', 'completed', or 'failed'
        request: Django request object (optional)
        notes: Additional notes (optional)
    """
    try:
        from api.models import PasswordResetLog
        
        ip_address = None
        user_agent = None
        
        if request:
            ip_address = getattr(request, 'META', {}).get('REMOTE_ADDR')
            user_agent = getattr(request, 'META', {}).get('HTTP_USER_AGENT')
        
        PasswordResetLog.objects.create(
            user=user,
            event_type=event_type,
            ip_address=ip_address,
            user_agent=user_agent,
            notes=notes
        )
        
        logger.info(f"📝 Logged password reset {event_type} for {user.username}")
        
    except Exception as e:
        logger.error(f"❌ Failed to log password reset {event_type} for {user.username}: {e}")


def get_user_password_reset_history(user):
    """
    Get password reset history for a user in the same format as other history entries
    
    Returns:
        List of history entries in the format: [timestamp, description]
    """
    try:
        from api.models import PasswordResetLog
        
        logs = PasswordResetLog.objects.filter(user=user).order_by('-timestamp')
        history_entries = []
        
        for log in logs:
            timestamp = log.timestamp.isoformat()
            description = f"Password reset {log.event_type}"
            if log.notes:
                description += f" - {log.notes}"
            
            history_entries.append(f"{timestamp}: {description}")
        
        return history_entries
        
    except Exception as e:
        logger.error(f"❌ Failed to get password reset history for {user.username}: {e}")
        return []
