# api/services/notification_service.py

import json
from datetime import datetime, timedelta, timezone

import requests
from django.conf import settings
from django.utils import timezone as dj_tz

from google.oauth2 import service_account
from google.auth.transport.requests import Request

from api.models import Notification, Task


class NotificationService:
    # ------------------------------------------------------------------ #
    #   1)  ACCESS-TOKEN CACHE (class attributes)                        #
    # ------------------------------------------------------------------ #
    _fcm_token: str | None         = None
    _fcm_token_expiry: datetime | None = None          # UTC

    @classmethod
    def _get_fcm_token(cls) -> str:
        """
        Return a valid access-token, refreshing it only when needed
        (Google tokens are ~1 h valid).
        """
        if cls._fcm_token and cls._fcm_token_expiry:
            if cls._fcm_token_expiry - datetime.now(timezone.utc) > timedelta(
                minutes=5
            ):
                return cls._fcm_token   # still fresh

        cred = service_account.Credentials.from_service_account_file(
            settings.FIREBASE_CREDENTIALS_FILE,
            scopes=["https://www.googleapis.com/auth/firebase.messaging"],
        )
        cred.refresh(Request())
        # cache + remember expiry (cred.expiry is naïve UTC)
        cls._fcm_token        = cred.token
        cls._fcm_token_expiry = cred.expiry.replace(tzinfo=timezone.utc)
        return cls._fcm_token

    # ------------------------------------------------------------------ #
    #   2)  MAIN ENTRY CALLED ON TASK SAVE                               #
    # ------------------------------------------------------------------ #
    @staticmethod
    def process_task_change(task: Task,
                            verb: str = "assigned or status_changed"):
        """
        Push **every time the task is modified**.
        We suppress a push only when we already have an *unread* row that
        is **newer than** the current modification – i.e. the user still
        hasn’t opened the very last banner we sent for this task.
        """
        recipients = set()

        if task.assigned_to:
            recipients.add(task.assigned_to)
        if task.created_by and task.created_by != task.assigned_to:
            recipients.add(task.created_by)

        # drop everyone who muted this task
        recipients -= set(task.muted_by.all())

        for user in recipients:
            duplicate = Notification.objects.filter(
                recipient=user,
                task=task,
                verb=verb,
                read=False,
                timestamp__gte=task.modified_at
            ).exists()

            if duplicate:
                continue

            Notification.objects.create(
                recipient=user,
                task=task,
                verb=verb,
            )

    # ------------------------------------------------------------------ #
    #   3)  LOW-LEVEL PUSH SENDER                                        #
    # ------------------------------------------------------------------ #
    @classmethod
    def push_to_device(cls, user, task, verb, notification_id) -> bool:
        tokens = (
            user.devices.values_list("token", flat=True)
            .order_by()
            .distinct()
        )
        if not tokens:
            return False

        access_token = cls._get_fcm_token()
        project_id   = settings.FIREBASE_PROJECT_ID
        url          = f"https://fcm.googleapis.com/v1/projects/{project_id}/messages:send"

        ok = True
        headers = {
            "Authorization": f"Bearer {access_token}",
            "Content-Type":  "application/json",
        }

        for token in tokens:
            payload = {
                "message": {
                    "token": token,
                    "notification": {
                        "title": f"Task {verb}",
                        "body":  f'Task "{task.title}" has been {verb.replace("_", " ")}.',
                    },
                    "data": {
                        "task_id":         str(task.id),
                        "notification_id": str(notification_id),
                        "click_action":    "FLUTTER_NOTIFICATION_CLICK",
                    },
                }
            }

            resp = requests.post(url, headers=headers, json=payload, timeout=10)
            print("📤 Sent push to:", token)
            print("📦 Payload:", json.dumps(payload, indent=2))
            print("📩 FCM status:", resp.status_code)
            if resp.status_code != 200:
                ok = False

        return ok