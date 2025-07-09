# api/models.py

import json
from django.conf import settings
from django.db import models
from django.utils import timezone

class Property(models.Model):
    name       = models.CharField(max_length=100, unique=True)
    address    = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='properties_created',
        null=True,
        blank=True,
    )
    modified_at = models.DateTimeField(auto_now=True)
    modified_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        related_name='properties_modified',
        null=True,
        blank=True,
    )

    def __str__(self):
        return self.name


TASK_TYPE_CHOICES = [('cleaning', 'Cleaning'), ('maintenance', 'Maintenance')]

class Task(models.Model):
    STATUS_CHOICES = [
        ('pending', 'Pending'),
        ('in-progress', 'In Progress'),
        ('completed', 'Completed'),
        ('canceled', 'Canceled'),
    ]

    task_type    = models.CharField(max_length=20, choices=TASK_TYPE_CHOICES, default='cleaning')
    title        = models.CharField(max_length=200)
    description  = models.TextField(blank=True)
    property     = models.ForeignKey('Property', on_delete=models.CASCADE, related_name='tasks', null=True, blank=True)
    status       = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending')
    created_at   = models.DateTimeField(auto_now_add=True)
    created_by   = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE,
                                     related_name='cleaning_tasks', null=True, blank=True)
    assigned_to  = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL,
                                     related_name='assigned_tasks', null=True, blank=True)
    modified_at  = models.DateTimeField(auto_now=True)
    modified_by  = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL,
                                     related_name='modified_tasks', null=True, blank=True)
    history      = models.TextField(blank=True, default='[]')

    def __str__(self):
        return f"{self.title} ({self.task_type}) - {self.property.name}"

    def save(self, *args, **kwargs):
        # Only build history on updates, not on initial creation
        if self.pk:
            old = Task.objects.get(pk=self.pk)
            changes = []
            user = getattr(self.modified_by, 'username', None) or 'unknown'

            # Status change
            if old.status != self.status:
                changes.append(
                    f"{timezone.now().isoformat()}: {user} changed status "
                    f"from '{old.status}' to '{self.status}'"
                )

            # Assigned_to change
            if old.assigned_to_id != self.assigned_to_id:
                old_name = getattr(old.assigned_to, 'username', 'unassigned')
                new_name = getattr(self.assigned_to, 'username', 'unassigned')
                changes.append(
                    f"{timezone.now().isoformat()}: {user} changed assignee "
                    f"from '{old_name}' to '{new_name}'"
                )

            # Title change
            if old.title != self.title:
                changes.append(
                    f"{timezone.now().isoformat()}: {user} changed title "
                    f"from '{old.title}' to '{self.title}'"
                )

            # Description change
            if old.description != self.description:
                changes.append(
                    f"{timezone.now().isoformat()}: {user} changed description "
                    f"from '{old.description}' to '{self.description}'"
                )

            if changes:
                hist = json.loads(old.history or "[]")
                hist.extend(changes)
                self.history = json.dumps(hist)

        super().save(*args, **kwargs)