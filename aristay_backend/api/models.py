from django.conf import settings
from django.db import models

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
    task_type = models.CharField(
        max_length=20,
        choices=TASK_TYPE_CHOICES,
        default='cleaning'
    )
    title = models.CharField(max_length=200)
    description = models.TextField(blank=True)
    property = models.ForeignKey(
        'Property',
        on_delete=models.CASCADE,
        related_name='tasks',
        null=True,
        blank=True)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending')
    created_at = models.DateTimeField(auto_now_add=True)
    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL, 
        on_delete=models.CASCADE,
        related_name='cleaning_tasks',
        null=True,
        blank=True
    )
    # Add assigned_to as an optional field. You can later update permissions to allow admins to set this.
    assigned_to = models.ForeignKey(
        settings.AUTH_USER_MODEL, 
        on_delete=models.SET_NULL,
        related_name='assigned_tasks',
        null=True,
        blank=True
    )
    modified_at = models.DateTimeField(auto_now=True)
    modified_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        related_name='modified_tasks',
        null=True,
        blank=True
    )
    # Store task history as a JSON-encoded string (default empty list)
    history = models.TextField(blank=True, default='[]')

    def __str__(self):
        return f"{self.title} ({self.task_type}) - {self.property.name}"