"""
Custom template tags for dual timezone display in AriStay
Provides filters for showing both user timezone and Tampa, FL timezone
"""

from django import template
from django.utils import timezone
from django.conf import settings
import pytz
from datetime import datetime

register = template.Library()

# Tampa, Florida timezone (Eastern Time)
TAMPA_TIMEZONE = pytz.timezone('America/New_York')

# Timezone display names mapping
TIMEZONE_NAMES = {
    'America/New_York': 'Tampa, FL',
    'America/Los_Angeles': 'San Jose, CA', 
    'America/Chicago': 'Chicago, IL',
    'America/Denver': 'Denver, CO',
    'America/Phoenix': 'Phoenix, AZ',
    'America/Anchorage': 'Anchorage, AK',
    'Pacific/Honolulu': 'Honolulu, HI',
    'Asia/Ho_Chi_Minh': 'Ho Chi Minh, Vietnam',
    'Europe/London': 'London, UK',
    'UTC': 'UTC',
}

def get_timezone_name(tz_string):
    """Get friendly timezone name"""
    return TIMEZONE_NAMES.get(tz_string, tz_string)

def get_user_timezone(user):
    """Get user's timezone from profile, fallback to Tampa timezone"""
    try:
        if hasattr(user, 'profile') and user.profile and user.profile.timezone:
            return pytz.timezone(user.profile.timezone)
    except:
        pass
    return TAMPA_TIMEZONE

@register.filter
def dual_timezone(value, user=None):
    """
    Display datetime in both user timezone and Tampa timezone
    Usage: {{ task.created_at|dual_timezone:user }}
    """
    if not value:
        return ""
    
    if not isinstance(value, datetime):
        return str(value)
    
    # Ensure the datetime is timezone-aware
    if timezone.is_naive(value):
        value = timezone.make_aware(value, TAMPA_TIMEZONE)
    
    # Get user timezone
    user_tz = get_user_timezone(user) if user else TAMPA_TIMEZONE
    
    # Convert to both timezones
    user_time = value.astimezone(user_tz)
    tampa_time = value.astimezone(TAMPA_TIMEZONE)
    
    # Format the times
    user_tz_name = get_timezone_name(str(user_tz))
    tampa_tz_name = get_timezone_name('America/New_York')
    
    # If same timezone, show only once
    if str(user_tz) == str(TAMPA_TIMEZONE):
        return f"{tampa_time.strftime('%b %d, %Y %H:%M')} ({tampa_tz_name})"
    
    # Show both timezones
    return (f"{user_time.strftime('%b %d, %Y %H:%M')} ({user_tz_name}) | "
            f"{tampa_time.strftime('%b %d, %Y %H:%M')} ({tampa_tz_name})")

@register.filter
def user_timezone(value, user=None):
    """
    Display datetime in user's timezone only
    Usage: {{ task.created_at|user_timezone:user }}
    """
    if not value:
        return ""
    
    if not isinstance(value, datetime):
        return str(value)
    
    # Ensure the datetime is timezone-aware
    if timezone.is_naive(value):
        value = timezone.make_aware(value, TAMPA_TIMEZONE)
    
    # Get user timezone
    user_tz = get_user_timezone(user) if user else TAMPA_TIMEZONE
    user_time = value.astimezone(user_tz)
    user_tz_name = get_timezone_name(str(user_tz))
    
    return f"{user_time.strftime('%b %d, %Y %H:%M')} ({user_tz_name})"

@register.filter
def tampa_timezone(value):
    """
    Display datetime in Tampa timezone only (for logs and critical areas)
    Usage: {{ task.created_at|tampa_timezone }}
    """
    if not value:
        return ""
    
    if not isinstance(value, datetime):
        return str(value)
    
    # Ensure the datetime is timezone-aware
    if timezone.is_naive(value):
        value = timezone.make_aware(value, TAMPA_TIMEZONE)
    
    tampa_time = value.astimezone(TAMPA_TIMEZONE)
    tampa_tz_name = get_timezone_name('America/New_York')
    
    return f"{tampa_time.strftime('%b %d, %Y %H:%M')} ({tampa_tz_name})"

@register.simple_tag
def current_time_dual(user=None):
    """
    Show current time in both user and Tampa timezone
    Usage: {% current_time_dual user %}
    """
    now = timezone.now()
    
    # Get user timezone
    user_tz = get_user_timezone(user) if user else TAMPA_TIMEZONE
    
    # Convert to both timezones
    user_time = now.astimezone(user_tz)
    tampa_time = now.astimezone(TAMPA_TIMEZONE)
    
    # Format the times
    user_tz_name = get_timezone_name(str(user_tz))
    tampa_tz_name = get_timezone_name('America/New_York')
    
    # If same timezone, show only once
    if str(user_tz) == str(TAMPA_TIMEZONE):
        return f"Current time: {tampa_time.strftime('%b %d, %Y %H:%M')} ({tampa_tz_name})"
    
    # Show both timezones
    return (f"Current time: {user_time.strftime('%b %d, %Y %H:%M')} ({user_tz_name}) | "
            f"Server time: {tampa_time.strftime('%b %d, %Y %H:%M')} ({tampa_tz_name})")

@register.simple_tag
def timezone_info(user=None):
    """
    Get timezone information for JavaScript or display
    Usage: {% timezone_info user %}
    """
    user_tz = get_user_timezone(user) if user else TAMPA_TIMEZONE
    user_tz_name = get_timezone_name(str(user_tz))
    tampa_tz_name = get_timezone_name('America/New_York')
    
    return {
        'user_timezone': str(user_tz),
        'user_timezone_name': user_tz_name,
        'server_timezone': 'America/New_York',
        'server_timezone_name': tampa_tz_name,
        'same_timezone': str(user_tz) == str(TAMPA_TIMEZONE),
    }

@register.filter
def format_duration_dual(start_time, end_time=None):
    """
    Format duration between two times with timezone info
    Usage: {{ start_time|format_duration_dual:end_time }}
    """
    if not start_time:
        return ""
    
    if end_time is None:
        end_time = timezone.now()
    
    if not isinstance(start_time, datetime) or not isinstance(end_time, datetime):
        return ""
    
    # Calculate duration
    if timezone.is_naive(start_time):
        start_time = timezone.make_aware(start_time, TAMPA_TIMEZONE)
    if timezone.is_naive(end_time):
        end_time = timezone.make_aware(end_time, TAMPA_TIMEZONE)
    
    duration = end_time - start_time
    
    # Format duration
    total_seconds = int(duration.total_seconds())
    days = total_seconds // 86400
    hours = (total_seconds % 86400) // 3600
    minutes = (total_seconds % 3600) // 60
    
    if days > 0:
        return f"{days}d {hours}h {minutes}m"
    elif hours > 0:
        return f"{hours}h {minutes}m"
    else:
        return f"{minutes}m"

# Add available timezone choices for user profile
@register.simple_tag
def get_timezone_choices():
    """Get available timezone choices for user profile"""
    return [
        ('America/New_York', 'Eastern Time (Tampa, FL)'),
        ('America/Los_Angeles', 'Pacific Time (San Jose, CA)'),
        ('America/Chicago', 'Central Time (Chicago, IL)'),
        ('America/Denver', 'Mountain Time (Denver, CO)'),
        ('America/Phoenix', 'Arizona Time (Phoenix, AZ)'),
        ('America/Anchorage', 'Alaska Time (Anchorage, AK)'),
        ('Pacific/Honolulu', 'Hawaii Time (Honolulu, HI)'),
        ('Asia/Ho_Chi_Minh', 'Vietnam Time (Ho Chi Minh City)'),
        ('Europe/London', 'GMT/BST (London, UK)'),
        ('UTC', 'UTC (Coordinated Universal Time)'),
    ]
