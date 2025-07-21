from django.conf import settings
from django.core.mail import EmailMultiAlternatives
from django.utils import timezone
from datetime import timedelta
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

            task_lines = [f"[{task.status.capitalize()}] {task.title}" for task in recent_tasks]
            task_html = "".join(f"<li><strong>{task.status.capitalize()}</strong>: {task.title}</li>" for task in recent_tasks)

            name = (
                (callable(getattr(user, 'get_full_name', None)) and user.get_full_name())
                or getattr(user, 'full_name', None)
                or user.username
                or "there"
            )

            subject = "🧹 Daily Task Digest – Aristay"
            from_email = settings.DEFAULT_FROM_EMAIL
            to_email = [user.email]

            text_content = (
                f"Hi {name},\n\n"
                f"Here are your updated tasks from the past day:\n\n"
                + "\n".join(f"• {line}" for line in task_lines) +
                "\n\nBest,\nAristay Task Management Team"
            )

            html_content = (
                f"<p>Hi {name},</p>"
                f"<p>Here are your updated tasks from the past day:</p>"
                f"<ul>{task_html}</ul>"
                f"<p>Best,<br>Aristay Task Management Team</p>"
            )

            if test_mode:
                print("To:", user.email)
                print(text_content)
                print("=" * 40)
            else:
                msg = EmailMultiAlternatives(subject, text_content, from_email, to_email)
                msg.attach_alternative(html_content, "text/html")
                msg.send()