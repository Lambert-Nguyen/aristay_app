from django.dispatch import receiver
from django.db.models.signals import post_save
from .models import Task
from .services.notification_service import NotificationService

@receiver(post_save, sender=Task)
def task_updated(sender, instance, created, **kwargs):
    if created:
        return
    NotificationService.process_task_change(instance)