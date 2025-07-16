from django.utils import timezone
from django.core.mail import send_mail
from .models import Notification
from django.contrib.auth.models import User

def send_daily_digest():
    for user in User.objects.all():
        notifications = Notification.objects.filter(recipient=user, read=False)
        if notifications.exists():
            summary = "\n".join([
                f"[{n.timestamp.strftime('%Y-%m-%d %H:%M')}] {n.verb} task '{n.task.title}'"
                for n in notifications
            ])
            send_mail(
                subject="Aristay Daily Task Summary",
                message=summary,
                from_email=settings.DEFAULT_FROM_EMAIL,
                recipient_list=[user.email],
            )