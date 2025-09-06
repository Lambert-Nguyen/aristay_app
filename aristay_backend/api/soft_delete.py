"""
Soft Delete Mixin and Manager for Aristay Models
"""
from django.db import models
from django.utils import timezone
from django.contrib.auth import get_user_model

User = get_user_model()


class SoftDeleteMixin(models.Model):
    """Mixin to add soft delete functionality"""
    is_deleted = models.BooleanField(default=False, db_index=True)
    deleted_at = models.DateTimeField(null=True, blank=True)
    deleted_by = models.ForeignKey(
        User,
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name='%(class)s_deleted'
    )
    deletion_reason = models.CharField(max_length=200, blank=True)

    class Meta:
        abstract = True

    def soft_delete(self, user=None, reason=""):
        """Soft delete this object"""
        self.is_deleted = True
        self.deleted_at = timezone.now()
        self.deleted_by = user
        self.deletion_reason = reason
        self.save()

    def restore(self, user=None):
        """Restore soft deleted object"""
        self.is_deleted = False
        self.deleted_at = None
        self.deleted_by = None
        self.deletion_reason = ""
        self.save()

    def hard_delete(self):
        """Permanently delete this object"""
        super().delete()


class SoftDeleteManager(models.Manager):
    """Manager that excludes soft deleted objects by default"""
    
    def get_queryset(self):
        return super().get_queryset().filter(is_deleted=False)

    def with_deleted(self):
        """Include soft deleted objects"""
        return super().get_queryset()

    def only_deleted(self):
        """Only soft deleted objects"""
        return super().get_queryset().filter(is_deleted=True)
