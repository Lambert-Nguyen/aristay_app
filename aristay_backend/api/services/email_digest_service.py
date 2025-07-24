# api/services/email_digest_service.py

from datetime import timedelta, timezone as dt_timezone
from collections import defaultdict
from zoneinfo import ZoneInfo

from django.conf import settings
from django.core.mail import EmailMultiAlternatives
from django.template.loader import render_to_string
from django.utils import timezone
from django.contrib.auth import get_user_model
from api.models import Task, Profile

class EmailDigestService:
    @staticmethod
    def send_daily_digest(test_mode=False):
        User = get_user_model()

        for user in User.objects.all():
            try:
                user_tz = ZoneInfo(user.profile.timezone)
            except Exception:
                user_tz = dt_timezone.utc    # fallback

            local_now = timezone.now().astimezone(user_tz)
            local_yesterday = local_now - timedelta(days=1)
            utc_cutoff = local_yesterday.astimezone(dt_timezone.utc)

            tasks = Task.objects.filter(
                assigned_to=user,
                modified_at__gte=utc_cutoff
            ).select_related("property")

            if not tasks.exists():
                continue

            # Group tasks by property and status
            grouped = defaultdict(lambda: defaultdict(list))
            for task in tasks:
                prop = task.property.name if task.property else "Unassigned"
                grouped[prop][task.status].append(task)

            grouped_tasks = grouped.items()

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