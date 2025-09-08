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
    def send_daily_digest(test_mode: bool = False) -> int:
        """
        Sends the digest to every user **iff** the global flag is enabled.
        Returns True if the digest actually ran; False otherwise.
        """
        if not settings.EMAIL_DIGEST_ENABLED:
            return 0
        sent = 0
        # ------------------------------------------------------------------
        User = get_user_model()
        
        status_colors = {
            'pending': '#e67e22',       # orange
            'in-progress': '#3498db',   # blue
            'completed': '#2ecc71',     # green
            'canceled': '#e74c3c',      # red
        }

        for user in User.objects.all():
            profile, _ = Profile.objects.get_or_create(user=user)
            if profile.digest_opt_out:
                continue  # Skip if user opted out
            try:
                user_tz = ZoneInfo(profile.timezone)
            except Exception:
                user_tz = dt_timezone.utc    # fallback

            local_now = timezone.now().astimezone(user_tz)
            local_yesterday = local_now - timedelta(days=1)
            utc_cutoff = local_yesterday.astimezone(dt_timezone.utc)

            tasks = Task.objects.filter(
                assigned_to=user,
                modified_at__gte=utc_cutoff
            ).select_related("property_ref")

            if not tasks.exists():
                continue

            # Group tasks by property and status
            grouped = defaultdict(lambda: defaultdict(list))
            print(f"[{user.email}] Tasks modified since cutoff ({utc_cutoff.isoformat()}):")
            for task in tasks:
                print(f"- {task.title} | {task.status} | {task.property_ref} | modified at {task.modified_at}")
                prop = task.property_ref.name if task.property_ref else "Unassigned"
                color = status_colors.get(task.status, '#333')
                task.status_color = color
                # Format relative due delta like "in 2 days" or "3 hours ago"
                if task.due_date:
                    delta = task.due_date.astimezone(user_tz) - local_now
                    seconds = delta.total_seconds()
                    if seconds < -86400:
                        task.due_delta = f"{int(abs(seconds)//86400)} days ago"
                    elif seconds < -3600:
                        task.due_delta = f"{int(abs(seconds)//3600)} hours ago"
                    elif seconds < 0:
                        task.due_delta = "just overdue"
                    elif seconds < 3600:
                        task.due_delta = f"in {int(seconds//60)} minutes"
                    elif seconds < 86400:
                        task.due_delta = f"in {int(seconds//3600)} hours"
                    else:
                        task.due_delta = f"in {int(seconds//86400)} days"
                grouped[prop][task.status].append(task)

            grouped_tasks = {
                prop: dict(status_dict)
                for prop, status_dict in grouped.items()
            }.items()

            name = (
                (user.get_full_name() if callable(user.get_full_name) else None)
                or getattr(user, "full_name", None)
                or user.username
                or "there"
            )

            context = {
                "name": name,
                "grouped_tasks": grouped_tasks,
                "status_colors": status_colors,
                "timezone_name": user_tz.key,
                "now": local_now,
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
            sent += 1 
        return sent