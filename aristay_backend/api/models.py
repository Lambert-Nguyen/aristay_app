from django.conf import settings  # Import settings for the user model
from django.db import models

class CleaningTask(models.Model):
    property_name = models.CharField(max_length=100)
    status = models.CharField(max_length=20, default='pending')
    created_at = models.DateTimeField(auto_now_add=True)
    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL, 
        on_delete=models.CASCADE,
        related_name='cleaning_tasks',
        null=True,   # Allow null if a task is created without a user (optional)
        blank=True
    )

    def __str__(self):
        return f"{self.property_name} ({self.status})"