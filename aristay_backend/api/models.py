from django.conf import settings
from django.db import models

class CleaningTask(models.Model):
    STATUS_CHOICES = [
        ('pending', 'Pending'),
        ('in-progress', 'In Progress'),
        ('completed', 'Completed'),
        ('canceled', 'Canceled'),
    ]
    property_name = models.CharField(max_length=100)
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
    # Store task history as a JSON-encoded string (default empty list)
    history = models.TextField(blank=True, default='[]')

    def __str__(self):
        return f"{self.property_name} ({self.status})"