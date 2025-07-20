# api/models.py

import json
from zoneinfo import available_timezones
from django.conf import settings
from django.db import models
from django.db.models.signals import post_save
from django.utils import timezone
from django.dispatch import receiver

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
    due_date = models.DateTimeField(
        null=True,
        blank=True,
        help_text="Optional deadline for task (stored in UTC)"
    )
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
            # Due date change
            if old.due_date != self.due_date:
                old_dt = old.due_date.isoformat() if old.due_date else "None"
                new_dt = self.due_date.isoformat() if self.due_date else "None"
                changes.append(
                    f"{timezone.now().isoformat()}: {user} changed due_date "
                    f"from '{old_dt}' to '{new_dt}'"
                )

            if changes:
                hist = json.loads(old.history or "[]")
                hist.extend(changes)
                self.history = json.dumps(hist)

        super().save(*args, **kwargs)


class TaskImage(models.Model):
    task = models.ForeignKey(Task, on_delete=models.CASCADE, related_name='images')
    image = models.ImageField(upload_to='task_images/%Y/%m/%d/')
    uploaded_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Image for {self.task.title}"

class Profile(models.Model):
    user     = models.OneToOneField(settings.AUTH_USER_MODEL,
                                    on_delete=models.CASCADE)
    timezone = models.CharField(
        max_length=32,
        choices=[(tz, tz) for tz in sorted(available_timezones())],
        default='UTC'
    )

    def __str__(self):
        return f"{self.user.username} profile"

@receiver(post_save, sender=settings.AUTH_USER_MODEL)
def create_user_profile(sender, instance, created, **kwargs):
    if created:
        Profile.objects.create(user=instance)

class Device(models.Model):
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='devices')
    token = models.CharField(max_length=255, unique=True)
    created_at = models.DateTimeField(auto_now_add=True)
    
    def __str__(self):
        return f"Device {self.token} for {self.user.username}"

class Notification(models.Model):
    recipient = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='notifications'
    )
    task = models.ForeignKey(Task, on_delete=models.CASCADE, related_name='notifications')
    verb = models.CharField(max_length=100)  # e.g. "assigned", "status_changed"
    read = models.BooleanField(default=False)
    read_at = models.DateTimeField(null=True, blank=True)  # ← new
    timestamp = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-timestamp']

    def __str__(self):
        return f"{self.verb} → {self.task.title} for {self.recipient.username}"
    