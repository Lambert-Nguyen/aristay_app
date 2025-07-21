from django.conf import settings
from django.core.mail import send_mail
from django.utils import timezone
from datetime import timedelta

from django.contrib.auth import get_user_model
from api.models import Task

class EmailDigestService:
    @staticmethod
    def send_daily_digest():
        yesterday = timezone.now() - timedelta(days=1)
        User = get_user_model()

        for user in User.objects.all():
            recent_tasks = Task.objects.filter(
                assigned_to=user,
                modified_at__gte=yesterday
            )

            if not recent_tasks.exists():
                continue

            body = "\n".join(
                f"- [{task.status}] {task.title}" for task in recent_tasks
            )

            send_mail(
                subject="🧹 Daily Task Digest – Aristay",
                message=f"Hi {user.get_full_name()},\n\nHere are your updated tasks:\n\n{body}",
                from_email=settings.DEFAULT_FROM_EMAIL,
                recipient_list=[user.email],
                fail_silently=False,
            )