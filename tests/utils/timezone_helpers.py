"""
Timezone utilities for tests to ensure all datetime creation is timezone-aware.
This prevents naive datetime warnings and ensures consistency with production timezone (Tampa, FL).
"""
from datetime import datetime, date, time, timedelta
from django.utils import timezone as django_timezone
import pytz


# Tampa, FL timezone (America/New_York)
TAMPA_TZ = pytz.timezone('America/New_York')


def make_aware(dt, tz=None):
    """
    Make a datetime timezone-aware using Tampa timezone by default.
    
    Args:
        dt: datetime object (naive or aware)
        tz: timezone to use (defaults to Tampa, FL)
    
    Returns:
        timezone-aware datetime object
    """
    if tz is None:
        tz = TAMPA_TZ
    
    if django_timezone.is_aware(dt):
        return dt
    
    return tz.localize(dt)


def now_tampa():
    """Get current time in Tampa, FL timezone."""
    return django_timezone.now().astimezone(TAMPA_TZ)


def today_tampa():
    """Get today's date in Tampa, FL timezone."""
    return now_tampa().date()


def create_datetime(year, month, day, hour=0, minute=0, second=0, microsecond=0, tz=None):
    """
    Create a timezone-aware datetime object.
    
    Args:
        year, month, day, hour, minute, second, microsecond: datetime components
        tz: timezone to use (defaults to Tampa, FL)
    
    Returns:
        timezone-aware datetime object
    """
    if tz is None:
        tz = TAMPA_TZ
    
    dt = datetime(year, month, day, hour, minute, second, microsecond)
    return tz.localize(dt)


def create_date_tampa(year, month, day):
    """
    Create a date object (timezone-naive, but represents Tampa date).
    
    Args:
        year, month, day: date components
    
    Returns:
        date object
    """
    return date(year, month, day)


def create_time_tampa(hour=0, minute=0, second=0, microsecond=0):
    """
    Create a time object (timezone-naive).
    
    Args:
        hour, minute, second, microsecond: time components
    
    Returns:
        time object
    """
    return time(hour, minute, second, microsecond)


def days_from_now(days, tz=None):
    """
    Get a datetime that is N days from now in Tampa timezone.
    
    Args:
        days: number of days (positive for future, negative for past)
        tz: timezone to use (defaults to Tampa, FL)
    
    Returns:
        timezone-aware datetime object
    """
    if tz is None:
        tz = TAMPA_TZ
    
    return now_tampa() + timedelta(days=days)


def days_from_date(base_date, days, tz=None):
    """
    Get a datetime that is N days from a given date in Tampa timezone.
    
    Args:
        base_date: base date (date or datetime object)
        days: number of days to add/subtract
        tz: timezone to use (defaults to Tampa, FL)
    
    Returns:
        timezone-aware datetime object
    """
    if tz is None:
        tz = TAMPA_TZ
    
    if isinstance(base_date, date) and not isinstance(base_date, datetime):
        # Convert date to datetime at midnight
        base_datetime = datetime.combine(base_date, time.min)
    else:
        base_datetime = base_date
    
    # Make sure it's timezone-aware
    if not django_timezone.is_aware(base_datetime):
        base_datetime = tz.localize(base_datetime)
    
    return base_datetime + timedelta(days=days)


# Common test dates in Tampa timezone
def get_test_dates():
    """
    Get common test dates in Tampa timezone.
    
    Returns:
        dict with common test dates
    """
    today = today_tampa()
    
    return {
        'today': today,
        'tomorrow': today + timedelta(days=1),
        'yesterday': today - timedelta(days=1),
        'next_week': today + timedelta(days=7),
        'last_week': today - timedelta(days=7),
        'next_month': today + timedelta(days=30),
        'last_month': today - timedelta(days=30),
    }


# Convenience functions for common test scenarios
def create_booking_dates(check_in_days=1, check_out_days=3, tz=None):
    """
    Create check-in and check-out dates for booking tests.
    
    Args:
        check_in_days: days from now for check-in
        check_out_days: days from now for check-out
        tz: timezone to use (defaults to Tampa, FL)
    
    Returns:
        tuple of (check_in_date, check_out_date) as timezone-aware datetimes
    """
    if tz is None:
        tz = TAMPA_TZ
    
    check_in = days_from_now(check_in_days, tz)
    check_out = days_from_now(check_out_days, tz)
    
    return check_in, check_out


def create_task_dates(due_days=1, tz=None):
    """
    Create due date for task tests.
    
    Args:
        due_days: days from now for due date
        tz: timezone to use (defaults to Tampa, FL)
    
    Returns:
        timezone-aware datetime object
    """
    if tz is None:
        tz = TAMPA_TZ
    
    return days_from_now(due_days, tz)


def create_invite_code_dates(expires_days=30, tz=None):
    """
    Create expiration date for invite code tests.
    
    Args:
        expires_days: days from now for expiration (can be negative for expired dates)
        tz: timezone to use (defaults to Tampa, FL)
    
    Returns:
        timezone-aware datetime object
    """
    if tz is None:
        tz = TAMPA_TZ
    
    return days_from_now(expires_days, tz)


def create_expired_datetime(days_ago=1, tz=None):
    """
    Create an expired datetime for testing.
    
    Args:
        days_ago: how many days ago (positive number)
        tz: timezone to use (defaults to Tampa, FL)
    
    Returns:
        timezone-aware datetime object in the past
    """
    if tz is None:
        tz = TAMPA_TZ
    
    return days_from_now(-days_ago, tz)


def create_datetime_with_hours(hours=1, tz=None):
    """
    Create a datetime N hours from now.
    
    Args:
        hours: hours from now (can be negative for past)
        tz: timezone to use (defaults to Tampa, FL)
    
    Returns:
        timezone-aware datetime object
    """
    if tz is None:
        tz = TAMPA_TZ
    
    return now_tampa() + timedelta(hours=hours)