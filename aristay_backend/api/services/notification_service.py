from api.models import Notification
from django.conf import settings
import requests

class NotificationService:
    @staticmethod
    def process_task_change(task):
        # You may want to refactor and pass in old state too
        if not task.assigned_to:
            return

        Notification.objects.create(
            recipient=task.assigned_to,
            task=task,
            verb='assigned or status_changed'
        )

        NotificationService.push_to_device(task.assigned_to, task, "assigned or status_changed")

    @staticmethod
    def push_to_device(user, task, verb):
        tokens = user.devices.values_list('token', flat=True)
        for token in tokens:
            requests.post(
                'https://fcm.googleapis.com/fcm/send',
                headers={
                    'Authorization': f'key={settings.FCM_SERVER_KEY}',
                    'Content-Type': 'application/json',
                },
                json={
                    'to': token,
                    'notification': {
                        'title': f'Task {verb}',
                        'body': f'Task "{task.title}" has been {verb.replace("_", " ")}.',
                    },
                    'data': {'task_id': task.id}
                }
            )