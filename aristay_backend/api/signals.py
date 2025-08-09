from django.dispatch import receiver
from django.db.models.signals import post_save
from .models import Task, Notification
from .services.notification_service import NotificationService

@receiver(post_save, sender=Task)
def task_updated(sender, instance, created, **kwargs):
    if created:
        return
    NotificationService.process_task_change(instance)

# ──────────────────────────────────────────────────────────────
#  NEW: push each Notification exactly once
# ──────────────────────────────────────────────────────────────

@receiver(post_save, sender=Notification)
def push_notification(sender, instance: Notification, created, **kwargs):
    """
    Whenever a Notification row is created (or saved with push_sent=False),
    fan-out the FCM push, then mark it as sent.
    """
    if instance.push_sent:
        return                               # already done

    # attempt the push
    success = NotificationService.push_to_device(
        instance.recipient,
        instance.task,
        instance.verb,
        instance.id,
    )

    if success:
        instance.mark_pushed()               # flips push_sent=True