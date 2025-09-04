"""
Core mixins for AriStay models.

This module provides reusable mixins that add common functionality to models:
- TimeStampedMixin: created_at, modified_at timestamps
- UserStampedMixin: created_by, modified_by user tracking
- SourceStampedMixin: created_via, modified_via source tracking
- SoftDeleteMixin: is_deleted, deleted_at soft delete functionality
"""

from django.conf import settings
from django.db import models
from django.utils import timezone


class TimeStampedMixin(models.Model):
    """Add created_at and modified_at timestamp fields to any model."""
    created_at = models.DateTimeField(auto_now_add=True)
    modified_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        abstract = True


class UserStampedMixin(models.Model):
    """Add created_by and modified_by user tracking to any model."""
    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL, 
        null=True, 
        blank=True,
        on_delete=models.SET_NULL, 
        related_name="%(class)s_created"
    )
    modified_by = models.ForeignKey(
        settings.AUTH_USER_MODEL, 
        null=True, 
        blank=True,
        on_delete=models.SET_NULL, 
        related_name="%(class)s_modified"
    )
    
    class Meta:
        abstract = True


class SourceStampedMixin(models.Model):
    """Add created_via and modified_via source tracking to any model."""
    
    class ChangeSource(models.TextChoices):
        MANUAL = "manual", "Manual"
        EXCEL_IMPORT = "excel_import", "Excel Import"
        API = "api", "API"
        SYSTEM = "system", "System"
        MIGRATION = "migration", "Data Migration"

    created_via = models.CharField(
        max_length=32, 
        choices=ChangeSource.choices, 
        default=ChangeSource.MANUAL
    )
    modified_via = models.CharField(
        max_length=32, 
        choices=ChangeSource.choices, 
        default=ChangeSource.MANUAL
    )
    
    class Meta:
        abstract = True


class SoftDeleteQuerySet(models.QuerySet):
    """Custom QuerySet that provides soft delete functionality."""
    
    def delete(self):
        """Soft delete all objects in the queryset."""
        count = self.filter(is_deleted=False).count()
        self.update(
            is_deleted=True,
            deleted_at=timezone.now()
        )
        return count, {'soft_deleted': count}
    
    def hard_delete(self):
        """Permanently delete objects (use with caution)."""
        return super().delete()
    
    def alive(self):
        """Return only non-deleted objects."""
        return self.filter(is_deleted=False)
    
    def dead(self):
        """Return only soft-deleted objects."""
        return self.filter(is_deleted=True)


class SoftDeleteManager(models.Manager):
    """Manager that excludes soft-deleted objects by default."""
    
    def get_queryset(self):
        return SoftDeleteQuerySet(self.model, using=self._db).filter(is_deleted=False)
    
    def with_deleted(self):
        """Include soft-deleted objects in queryset."""
        return SoftDeleteQuerySet(self.model, using=self._db)
    
    def only_deleted(self):
        """Return only soft-deleted objects."""
        return SoftDeleteQuerySet(self.model, using=self._db).filter(is_deleted=True)


class SoftDeleteMixin(models.Model):
    """Add soft delete functionality to any model."""
    
    is_deleted = models.BooleanField(default=False, db_index=True)
    deleted_at = models.DateTimeField(null=True, blank=True)
    deleted_by = models.ForeignKey(
        settings.AUTH_USER_MODEL, 
        null=True, 
        blank=True,
        on_delete=models.SET_NULL, 
        related_name="%(class)s_deleted"
    )
    deletion_reason = models.CharField(max_length=200, blank=True)

    # Managers
    objects = SoftDeleteManager()
    all_objects = SoftDeleteQuerySet.as_manager()

    class Meta:
        abstract = True

    def delete(self, using=None, keep_parents=False):
        """Override delete to perform soft delete instead."""
        self.soft_delete()
        return 1, {self._meta.label: 1}

    def soft_delete(self, user=None, reason=""):
        """Mark this object as deleted without removing from database."""
        if self.is_deleted:
            return  # Already deleted
            
        self.is_deleted = True
        self.deleted_at = timezone.now()
        self.deleted_by = user
        self.deletion_reason = reason[:200]  # Truncate if too long
        self.save(update_fields=["is_deleted", "deleted_at", "deleted_by", "deletion_reason"])

    def restore(self, user=None):
        """Restore a soft-deleted object."""
        if not self.is_deleted:
            return  # Not deleted
            
        self.is_deleted = False
        self.deleted_at = None
        self.deleted_by = None
        self.deletion_reason = ""
        self.save(update_fields=["is_deleted", "deleted_at", "deleted_by", "deletion_reason"])

    def hard_delete(self):
        """Permanently delete this object (use with extreme caution)."""
        super().delete()
