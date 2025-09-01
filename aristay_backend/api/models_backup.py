# api/models.py

import json
from zoneinfo import available_timezones
from django.conf import settings
from django.db import models
from django.db.models.signals import post_save
from django.utils import timezone
from django.dispatch import receiver
from django.contrib.auth.models import User

class Property(models.Model):
    name = models.CharField(max_length=100, unique=True)
    address = models.TextField(blank=True)
    
    # Enhanced fields for property management
    PROPERTY_TYPE_CHOICES = [
        ('house', 'House'),
        ('apartment', 'Apartment'),
        ('villa', 'Villa'),
        ('condo', 'Condo'),
        ('other', 'Other'),
    ]
    property_type = models.CharField(max_length=20, choices=PROPERTY_TYPE_CHOICES, default='house')
    is_active = models.BooleanField(default=True, help_text="Property is available for bookings")
    cleaning_frequency = models.CharField(max_length=50, choices=[
        ('daily', 'Daily'),
        ('weekly', 'Weekly'),
        ('biweekly', 'Bi-weekly'),
        ('monthly', 'Monthly'),
        ('custom', 'Custom')
    ], default='weekly')
    maintenance_schedule = models.TextField(blank=True, help_text="Maintenance schedule notes")
    notes = models.TextField(blank=True, help_text="General property notes")
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
    
    @property
    def current_booking(self):
        """Get the currently active booking if any"""
        now = timezone.now()
        return self.bookings.filter(
            check_in_date__lte=now,
            check_out_date__gte=now,
            status='active'
        ).first()
    
    @property
    def upcoming_bookings(self):
        """Get upcoming bookings"""
        now = timezone.now()
        return self.bookings.filter(
            check_in_date__gt=now,
            status='upcoming'
        ).order_by('check_in_date')
    
    @property
    def past_bookings(self):
        """Get completed bookings"""
        now = timezone.now()
        return self.bookings.filter(
            check_out_date__lt=now,
            status='completed'
        ).order_by('-check_out_date')


TASK_TYPE_CHOICES = [
    ('administration', 'Administration'),
    ('cleaning', 'Cleaning'),
    ('maintenance', 'Maintenance'),
    ('laundry', 'Laundry'),
    ('lawn_pool', 'Lawn/Pool')
]

class Task(models.Model):
    STATUS_CHOICES = [
        ('pending', 'Pending'),
        ('in_progress', 'In Progress'),
        ('waiting_dependency', 'Waiting for Dependency'),
        ('completed', 'Completed'),
        ('cancelled', 'Cancelled'),
        ('overdue', 'Overdue'),
    ]

    task_type    = models.CharField(max_length=20, choices=TASK_TYPE_CHOICES, default='cleaning')
    title        = models.CharField(max_length=200)
    description  = models.TextField(blank=True)
    property = models.ForeignKey('Property', on_delete=models.CASCADE, related_name='tasks', null=True, blank=True)
    booking = models.ForeignKey('Booking', on_delete=models.CASCADE, related_name='tasks', null=True, blank=True)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending')
    created_at   = models.DateTimeField(auto_now_add=True)
    created_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE,
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
    estimated_duration = models.IntegerField(help_text='Duration in minutes', null=True, blank=True)
    priority = models.CharField(max_length=20, choices=[
        ('low', 'Low'),
        ('medium', 'Medium'),
        ('high', 'High'),
        ('urgent', 'Urgent')
    ], default='medium')
    
    # Task-specific fields
    checklist_items = models.JSONField(default=list, blank=True, help_text="Checklist items for this task")
    photos_required = models.BooleanField(default=False, help_text="Photos required for completion")
    gps_checkin_required = models.BooleanField(default=False, help_text="GPS check-in required for completion")
    
    # Completion tracking
    completed_at = models.DateTimeField(null=True, blank=True)
    history = models.TextField(blank=True, default='[]')
    
    # users that do **not** want pushes for *this* task
    muted_by = models.ManyToManyField(
        settings.AUTH_USER_MODEL,
        related_name='muted_tasks',
        blank=True,
        help_text="Users that muted notifications for this task"
    )
    
    # Task dependencies
    prerequisite_tasks = models.ManyToManyField(
        'self',
        through='TaskDependency',
        symmetrical=False,
        related_name='dependent_tasks',
        blank=True,
        help_text="Tasks that must be completed before this task can start"
    )


    def __str__(self):
        prop_name = self.property.name if self.property else "No property"
        return f"{self.title} ({self.task_type}) - {prop_name}"

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
    
    @property
    def can_start(self):
        """Check if all prerequisite tasks are completed"""
        if not self.prerequisite_tasks.exists():
            return True
        
        for dependency in self.prerequisite_tasks.all():
            if dependency.prerequisite_task.status != 'completed':
                return False
        return True
    
    @property
    def blocked_tasks(self):
        """Get tasks that are blocked by this task"""
        return Task.objects.filter(prerequisite_tasks__prerequisite_task=self)
    
    def update_status_based_on_dependencies(self):
        """Update status based on dependency completion"""
        if self.status == 'waiting_dependency' and self.can_start:
            self.status = 'pending'
            self.save(update_fields=['status'])
        elif self.status == 'pending' and not self.can_start:
            self.status = 'waiting_dependency'
            self.save(update_fields=['status'])


class TaskImage(models.Model):
    task = models.ForeignKey(Task, on_delete=models.CASCADE, related_name='images')
    image = models.ImageField(upload_to='task_images/%Y/%m/%d/')
    uploaded_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Image for {self.task.title}"
    
# Enhanced UserRole choices for the new role-based system
class UserRole(models.TextChoices):
    # Core roles
    CLEANING_STAFF = 'cleaning_staff', 'Cleaning Staff'
    MAINTENANCE_STAFF = 'maintenance_staff', 'Maintenance Staff'
    LAUNDRY_STAFF = 'laundry_staff', 'Laundry Staff'
    LAWN_POOL_VENDOR = 'lawn_pool_vendor', 'Lawn/Pool Vendor'
    
    # Management roles
    CREW_MANAGER = 'crew_manager', 'Crew Manager'  # Was 'manager'
    SUPERUSER = 'superuser', 'Superuser'           # Was 'owner'
    
    # Legacy roles (for backward compatibility)
    STAFF = 'staff', 'Staff'                       # Legacy
    MANAGER = 'manager', 'Manager'                 # Legacy
    OWNER = 'owner', 'Owner'                       # Legacy

class Profile(models.Model):
    user     = models.OneToOneField(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    timezone = models.CharField(
        max_length=32,
        choices=[(tz, tz) for tz in sorted(available_timezones())],
        default='UTC'
    )
    digest_opt_out = models.BooleanField(default=False)

    # Enhanced role system
    role = models.CharField(
        max_length=20,
        choices=UserRole.choices,
        default=UserRole.CLEANING_STAFF,
        help_text="Primary role for this user"
    )
    
    # Additional profile fields
    phone_number = models.CharField(max_length=20, blank=True)
    emergency_contact = models.CharField(max_length=200, blank=True)
    skills = models.JSONField(default=list, blank=True, help_text="List of skills/certifications")
    is_available = models.BooleanField(default=True, help_text="User is available for task assignment")

    def __str__(self):
        return f"{self.user.username} profile"
    
    @property
    def all_roles(self):
        """Get all roles assigned to this user"""
        return [assignment.role_type for assignment in self.user.role_assignments.all()]
    
    @property
    def primary_role(self):
        """Get the primary role for this user"""
        primary_assignment = self.user.role_assignments.filter(is_primary=True).first()
        return primary_assignment.role_type if primary_assignment else self.role
    
    def has_role(self, role_type):
        """Check if user has a specific role"""
        return self.user.role_assignments.filter(role_type=role_type).exists()
    
    def can_handle_task_type(self, task_type):
        """Check if user can handle a specific task type"""
        if self.user.is_superuser:
            return True
        
        role_mapping = {
            'cleaning': [UserRole.CLEANING_STAFF],
            'maintenance': [UserRole.MAINTENANCE_STAFF],
            'laundry': [UserRole.LAUNDRY_STAFF],
            'lawn_pool': [UserRole.LAWN_POOL_VENDOR],
            'administration': [UserRole.CREW_MANAGER, UserRole.SUPERUSER],
        }
        
        allowed_roles = role_mapping.get(task_type, [])
        return any(self.has_role(role) for role in allowed_roles)

@receiver(post_save, sender=settings.AUTH_USER_MODEL)
def create_user_profile(sender, instance, created, **kwargs):
    if created:
        # default role=staff; owners are superusers and can be marked owner later
        Profile.objects.create(user=instance)

@receiver(post_save, sender=User)
def sync_profile_role_on_user_save(sender, instance, **kwargs):
    profile, _ = Profile.objects.get_or_create(user=instance)
    if instance.is_superuser:
        # we don’t force profile.role to 'owner'; serializer maps superusers → 'owner'
        return
    desired = UserRole.MANAGER if instance.is_staff else UserRole.STAFF
    if profile.role != desired:
        profile.role = desired
        profile.save(update_fields=['role'])

class Device(models.Model):
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='devices')
    token = models.CharField(max_length=255, unique=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
        
    def __str__(self):
        return f"Device {self.token} for {self.user.username}"

class NotificationVerb(models.TextChoices):
    ASSIGNED          = "assigned",          "Assigned"
    UNASSIGNED        = "unassigned",        "Unassigned"
    STATUS_CHANGED    = "status_changed",    "Status changed"
    DUE_DATE_CHANGED  = "due_date_changed",  "Due date changed"
    TITLE_CHANGED     = "title_changed",     "Title changed"
    DESCRIPTION_CHANGED = "description_changed", "Description changed"
    PHOTO_ADDED       = "photo_added",       "Photo added"
    PHOTO_DELETED     = "photo_deleted",     "Photo deleted"
    CREATED           = "created",           "Task created"

class Notification(models.Model):
    recipient = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='notifications'
    )
    task = models.ForeignKey('Task', on_delete=models.CASCADE, related_name='notifications')
    verb = models.CharField(
        max_length=32,
        choices=NotificationVerb.choices,
        default=NotificationVerb.STATUS_CHANGED,
    )
    read = models.BooleanField(default=False)
    read_at = models.DateTimeField(null=True, blank=True)

    push_sent = models.BooleanField(default=False, editable=False)
    timestamp = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-timestamp']

    def __str__(self):
        return f"{self.verb} → {self.task.title} for {self.recipient.username}"

    def mark_pushed(self, commit: bool = True):
        if not self.push_sent:
            self.push_sent = True
            if commit:
                self.save(update_fields=["push_sent"])


# ============================================================================
# NEW MODELS FOR ENHANCED ROLE-BASED SYSTEM
# ============================================================================

class UserRoleAssignment(models.Model):
    """
    Allows users to have multiple roles with one primary role
    """
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='role_assignments')
    role_type = models.CharField(max_length=20, choices=UserRole.choices)
    is_primary = models.BooleanField(default=True, help_text="Primary role for this user")
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        unique_together = ['user', 'role_type']
        ordering = ['-is_primary', 'created_at']
    
    def __str__(self):
        return f"{self.user.username} - {self.role_type} (Primary: {self.is_primary})"


class PropertyOwnership(models.Model):
    """
    Manages property ownership and viewer permissions
    """
    OWNERSHIP_TYPE_CHOICES = [
        ('owner', 'Owner'),
        ('viewer', 'Viewer'),
        ('manager', 'Manager'),
    ]
    
    property = models.ForeignKey(Property, on_delete=models.CASCADE, related_name='ownerships')
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='property_ownerships')
    ownership_type = models.CharField(max_length=20, choices=OWNERSHIP_TYPE_CHOICES)
    can_edit = models.BooleanField(default=False, help_text="Can modify property settings")
    can_view_tasks = models.BooleanField(default=True, help_text="Can view tasks for this property")
    can_view_reports = models.BooleanField(default=True, help_text="Can view property reports")
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        unique_together = ['property', 'user']
        ordering = ['ownership_type', 'created_at']
    
    def __str__(self):
        return f"{self.user.username} - {self.ownership_type} of {self.property.name}"


class Booking(models.Model):
    """
    Manages property bookings and guest information
    """
    BOOKING_STATUS_CHOICES = [
        ('upcoming', 'Upcoming'),
        ('active', 'Active'),
        ('completed', 'Completed'),
        ('cancelled', 'Cancelled'),
    ]
    
    property = models.ForeignKey(Property, on_delete=models.CASCADE, related_name='bookings')
    check_in_date = models.DateTimeField()
    check_out_date = models.DateTimeField()
    guest_name = models.CharField(max_length=200)
    guest_contact = models.CharField(max_length=100, blank=True)
    guest_email = models.EmailField(blank=True)
    status = models.CharField(max_length=20, choices=BOOKING_STATUS_CHOICES, default='upcoming')
    notes = models.TextField(blank=True, help_text="Special instructions or notes")
    created_at = models.DateTimeField(auto_now_add=True)
    modified_at = models.DateTimeField(auto_now=True)
    created_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='bookings_created')
    modified_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='bookings_modified')
    
    class Meta:
        ordering = ['-check_in_date']
        indexes = [
            models.Index(fields=['property', 'check_in_date']),
            models.Index(fields=['status', 'check_in_date']),
        ]
    
    def __str__(self):
        return f"{self.property.name} - {self.guest_name} ({self.check_in_date.date()} to {self.check_out_date.date()})"
    
    @property
    def is_active(self):
        """Check if booking is currently active"""
        now = timezone.now()
        return self.check_in_date <= now <= self.check_out_date
    
    @property
    def duration_days(self):
        """Calculate booking duration in days"""
        return (self.check_out_date - self.check_in_date).days


class TaskDependency(models.Model):
    """
    Manages task dependencies and prerequisites
    """
    DEPENDENCY_TYPE_CHOICES = [
        ('must_complete', 'Must Complete'),
        ('must_start', 'Must Start'),
        ('soft_dependency', 'Soft Dependency'),
    ]
    
    task = models.ForeignKey('Task', on_delete=models.CASCADE, related_name='task_dependencies')
    prerequisite_task = models.ForeignKey('Task', on_delete=models.CASCADE, related_name='dependent_tasks')
    dependency_type = models.CharField(max_length=20, choices=DEPENDENCY_TYPE_CHOICES, default='must_complete')
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        unique_together = ['task', 'prerequisite_task']
        ordering = ['dependency_type', 'created_at']
    
    def __str__(self):
        return f"{self.prerequisite_task.title} → {self.task.title} ({self.dependency_type})"
    
    def clean(self):
        """Prevent circular dependencies"""
        from django.core.exceptions import ValidationError
        if self.task == self.prerequisite_task:
            raise ValidationError("A task cannot depend on itself")
        
        # Check for circular dependencies (simplified check)
        if self.prerequisite_task.prerequisite_tasks.filter(prerequisite_task=self.task).exists():
            raise ValidationError("Circular dependency detected")


class TaskTemplate(models.Model):
    """
    Templates for different property types and task types
    """
    PROPERTY_TYPE_CHOICES = [
        ('house', 'House'),
        ('apartment', 'Apartment'),
        ('villa', 'Villa'),
        ('condo', 'Condo'),
        ('other', 'Other'),
    ]
    
    TASK_TYPE_CHOICES = [
        ('administration', 'Administration'),
        ('cleaning', 'Cleaning'),
        ('maintenance', 'Maintenance'),
        ('laundry', 'Laundry'),
        ('lawn_pool', 'Lawn/Pool'),
    ]
    
    name = models.CharField(max_length=200, help_text="Template name")
    property_type = models.CharField(max_length=20, choices=PROPERTY_TYPE_CHOICES)
    task_type = models.CharField(max_length=20, choices=TASK_TYPE_CHOICES)
    title = models.CharField(max_length=200)
    description = models.TextField()
    estimated_duration = models.IntegerField(help_text="Estimated duration in minutes", null=True, blank=True)
    checklist_items = models.JSONField(default=list, blank=True, help_text="Default checklist items")
    photos_required = models.BooleanField(default=False)
    gps_checkin_required = models.BooleanField(default=False)
    priority = models.CharField(max_length=20, choices=[
        ('low', 'Low'),
        ('medium', 'Medium'),
        ('high', 'High'),
        ('urgent', 'Urgent')
    ], default='medium')
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    modified_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        unique_together = ['property_type', 'task_type', 'name']
        ordering = ['property_type', 'task_type', 'name']
    
    def __str__(self):
        return f"{self.property_type} - {self.task_type} - {self.name}"