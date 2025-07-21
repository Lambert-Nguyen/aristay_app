from django.conf import settings
from django.core.mail import send_mail
from django.utils import timezone
from datetime import timedelta
import os

from django.contrib.auth import get_user_model
from api.models import Task

class EmailDigestService:
    @staticmethod
    def send_daily_digest(test_mode=False):
        yesterday = timezone.now() - timedelta(days=1)
        User = get_user_model()

        for user in User.objects.all():
            recent_tasks = Task.objects.filter(
                assigned_to=user,
                modified_at__gte=yesterday
            )

            if not recent_tasks.exists():
                continue

            # Safely get user's name
            name = (
                getattr(user, 'get_full_name', lambda: None)()
                or getattr(user, 'full_name', None)
                or getattr(user, 'username', None)
                or "there"
            )

            # Format task list
            body = "\n".join(
                f"• [{task.status.title()}] {task.title}" for task in recent_tasks
            )

            message = f"""Hi {name},

Here are your updated tasks from the past day:

{body}

Best,
Aristay Task Management Team"""

            if test_mode:
                print("To:", user.email)
                print(message)
                print("="*40)
            else:
                send_mail(
                    subject="🧹 Daily Task Digest – Aristay",
                    message=message,
                    from_email=settings.DEFAULT_FROM_EMAIL,
                    recipient_list=[user.email],
                    fail_silently=False,
                )