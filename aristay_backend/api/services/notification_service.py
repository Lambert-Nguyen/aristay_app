from api.models import Notification, Task
from django.conf import settings
from django.utils import timezone
import requests
import json

from google.oauth2 import service_account
from google.auth.transport.requests import Request

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

        # Log to task.history
        history = json.loads(task.history or '[]')
        timestamp = timezone.now().isoformat()
        history.append(f"{timestamp}: System notified {task.assigned_to.username} (push)")
        Task.objects.filter(pk=task.pk).update(history=json.dumps(history))

    @staticmethod
    def push_to_device(user, task, verb):
        tokens = user.devices.values_list('token', flat=True)

        credentials = service_account.Credentials.from_service_account_file(
            settings.FIREBASE_CREDENTIALS_FILE,
            scopes=['https://www.googleapis.com/auth/firebase.messaging'],
        )
        credentials.refresh(Request())  # get valid access token

        access_token = credentials.token
        project_id = settings.FIREBASE_PROJECT_ID
        url = f'https://fcm.googleapis.com/v1/projects/{project_id}/messages:send'

        for token in tokens:
            payload = {
                "message": {
                    "token": token,
                    "notification": {
                        "title": f"Task {verb}",
                        "body": f'Task "{task.title}" has been {verb.replace("_", " ")}.',
                    },
                    "data": {
                        "task_id": str(task.id),
                        "click_action": "FLUTTER_NOTIFICATION_CLICK",
                    }
                }
            }

            headers = {
                "Authorization": f"Bearer {access_token}",
                "Content-Type": "application/json",
            }

            response = requests.post(url, headers=headers, json=payload)
            print('📤 Sent push to:', token)
            print('📦 Payload:', json.dumps(payload, indent=2))
            print('📩 FCM status:', response.status_code)
            print('📩 FCM response:', response.text)