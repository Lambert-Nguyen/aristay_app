"""
Timezone helper functions for tests
"""
from datetime import datetime, timedelta
from django.utils import timezone


def create_task_dates(due_days=1):
    """Create task due date relative to now"""
    return timezone.now() + timedelta(days=due_days)


def create_booking_dates(check_in_days=0, check_out_days=1):
    """Create booking check-in and check-out dates relative to now"""
    check_in = timezone.now() + timedelta(days=check_in_days)
    check_out = timezone.now() + timedelta(days=check_out_days)
    return check_in, check_out
