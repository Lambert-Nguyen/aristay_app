# api/signals.py
from django.dispatch import receiver
from django.db.models.signals import post_save
from .models import Notification
from .services.notification_service import NotificationService

@receiver(post_save, sender=Notification)
def push_notification(sender, instance: Notification, created, **kwargs):
    if not created or instance.push_sent:
        return
    success = NotificationService.push_to_device(
        instance.recipient, instance.task, instance.verb, instance.id
    )
    if success:
        instance.mark_pushed()