# api/services/notification_service.py
import json
from datetime import datetime, timedelta, timezone
import requests
from django.conf import settings

from api.models import Notification, Task, NotificationVerb

class NotificationService:
    _fcm_token: str | None = None
    _fcm_token_expiry: datetime | None = None

    @classmethod
    def _get_fcm_token(cls) -> str:
        from google.oauth2 import service_account
        from google.auth.transport.requests import Request

        if cls._fcm_token and cls._fcm_token_expiry:
            if cls._fcm_token_expiry - datetime.now(timezone.utc) > timedelta(minutes=5):
                return cls._fcm_token

        cred = service_account.Credentials.from_service_account_file(
            settings.FIREBASE_CREDENTIALS_FILE,
            scopes=["https://www.googleapis.com/auth/firebase.messaging"],
        )
        cred.refresh(Request())
        cls._fcm_token        = cred.token
        cls._fcm_token_expiry = cred.expiry.replace(tzinfo=timezone.utc)
        return cls._fcm_token

    # ---------------- recipients ----------------
    @staticmethod
    def _recipients(task: Task, *, actor=None):
        people = set()
        if task.assigned_to:
            people.add(task.assigned_to)
        if task.created_by and task.created_by != task.assigned_to:
            people.add(task.created_by)
        # respect per-task mutes
        people -= set(task.muted_by.all())
        # don’t notify the person who performed the action
        if actor is not None:
            people.discard(actor)
        return people

    # ---------------- public API ----------------
    @staticmethod
    def notify_on_create(task: Task, *, actor=None):
        """On creation, ping the assignee (if any) and creator (if different)."""
        # If an assignee exists, the most useful verb is "assigned"
        verb = NotificationVerb.ASSIGNED if task.assigned_to else NotificationVerb.CREATED
        NotificationService._emit(task, [verb], actor=actor)

    @staticmethod
    def notify_on_update(old: Task, new: Task, *, actor=None):
        """Compare fields and send precise verbs."""
        verbs: list[str] = []

        if old.assigned_to_id != new.assigned_to_id:
            if new.assigned_to_id:
                verbs.append(NotificationVerb.ASSIGNED)
            else:
                verbs.append(NotificationVerb.UNASSIGNED)

        if old.status != new.status:
            verbs.append(NotificationVerb.STATUS_CHANGED)

        if old.title != new.title:
            verbs.append(NotificationVerb.TITLE_CHANGED)

        if old.description != new.description:
            verbs.append(NotificationVerb.DESCRIPTION_CHANGED)

        if old.due_date != new.due_date:
            verbs.append(NotificationVerb.DUE_DATE_CHANGED)

        if verbs:
            NotificationService._emit(new, verbs, actor=actor)

    @staticmethod
    def notify_task_photo(task: Task, *, added: bool, actor=None):
        NotificationService._emit(
            task,
            [NotificationVerb.PHOTO_ADDED if added else NotificationVerb.PHOTO_DELETED],
            actor=actor,
        )

    # ---------------- internals ----------------
    @staticmethod
    def _emit(task: Task, verbs: list[str], *, actor=None):
        for user in NotificationService._recipients(task, actor=actor):
            for verb in verbs:
                # de-dupe: if an unread row for same (user, task, verb) exists newer than the
                # last modification, skip to avoid stacking banners
                duplicate = Notification.objects.filter(
                    recipient=user, task=task, verb=verb, read=False,
                    timestamp__gte=task.modified_at
                ).exists()
                if duplicate:
                    continue
                Notification.objects.create(
                    recipient=user,
                    task=task,
                    verb=verb,
                )

    @classmethod
    def push_to_device(cls, user, task, verb, notification_id) -> bool:
        tokens = user.devices.values_list("token", flat=True).order_by().distinct()
        if not tokens:
            return False

        access_token = cls._get_fcm_token()
        url = f"https://fcm.googleapis.com/v1/projects/{settings.FIREBASE_PROJECT_ID}/messages:send"
        headers = {"Authorization": f"Bearer {access_token}", "Content-Type": "application/json"}

        ok = True
        for token in tokens:
            payload = {
                "message": {
                    "token": token,
                    "notification": {
                        "title": f"Task {verb.replace('_', ' ')}",
                        "body":  f"“{task.title}”",
                    },
                    "data": {
                        "task_id":         str(task.id),
                        "notification_id": str(notification_id),
                        "verb":            verb,
                        "click_action":    "FLUTTER_NOTIFICATION_CLICK",
                    },
                }
            }
            resp = requests.post(url, headers=headers, json=payload, timeout=10)
            if resp.status_code != 200:
                ok = False
        return ok