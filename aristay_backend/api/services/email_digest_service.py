# api/services/email_digest_service.py

from django.conf import settings
from django.core.mail import EmailMultiAlternatives
from django.template.loader import render_to_string
from django.utils import timezone
from datetime import timedelta
from collections import defaultdict

from django.contrib.auth import get_user_model
from api.models import Task

class EmailDigestService:
    @staticmethod
    def send_daily_digest(test_mode=False):
        yesterday = timezone.now() - timedelta(days=1)
        User = get_user_model()

        for user in User.objects.all():
            tasks = Task.objects.filter(
                assigned_to=user,
                modified_at__gte=yesterday
            ).select_related("property")

            if not tasks.exists():
                continue

            # Group tasks by property
            grouped = defaultdict(list)
            for task in tasks:
                property_name = task.property.name if task.property else "Unassigned"
                grouped[property_name].append(task)
            grouped_tasks = list(grouped.items())

            name = (
                (user.get_full_name() if callable(user.get_full_name) else None)
                or getattr(user, "full_name", None)
                or user.username
                or "there"
            )

            context = {
                "name": name,
                "grouped_tasks": grouped_tasks,
            }

            subject = "🧹 Daily Task Digest – Aristay"
            from_email = settings.DEFAULT_FROM_EMAIL
            to_email = [user.email]

            text_body = render_to_string("emails/digest.txt", context)
            html_body = render_to_string("emails/digest.html", context)

            if test_mode:
                print(f"To: {user.email}")
                print(text_body)
                print("=" * 40)
                continue

            msg = EmailMultiAlternatives(subject, text_body, from_email, to_email)
            msg.attach_alternative(html_body, "text/html")
            msg.send()