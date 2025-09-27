"""
Timezone helper functions for tests.
"""
from datetime import timedelta
from django.utils import timezone


def create_task_dates(due_days=1):
    """Create task due date relative to now"""
    return timezone.now() + timedelta(days=due_days)


def create_booking_dates(check_in_days=0, check_out_days=1):
    """Create booking check-in and check-out dates relative to now"""
    check_in = timezone.now() + timedelta(days=check_in_days)
    check_out = timezone.now() + timedelta(days=check_out_days)
    return check_in, check_out


def days_from_now(days):
    """Create a datetime that is N days from now"""
    return timezone.now() + timedelta(days=days)


def create_expired_datetime(days_ago=30):
    """Create a datetime that is N days ago (expired)"""
    return timezone.now() - timedelta(days=days_ago)


def create_invite_code_dates(expiry_days=7):
    """Create invite code expiry date relative to now"""
    return timezone.now() + timedelta(days=expiry_days)


def create_datetime_with_hours(hours_from_now=1):
    """Create a datetime that is N hours from now"""
    return timezone.now() + timedelta(hours=hours_from_now)
