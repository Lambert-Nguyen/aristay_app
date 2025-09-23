# api/models.py

import json
from datetime import time, timedelta
# Removed available_timezones import - using curated timezone choices instead
from django.conf import settings
from django.db import models
from django.db.models import Q, F
from django.db.models.signals import post_save, m2m_changed
from django.utils import timezone
from django.dispatch import receiver
from django.core.exceptions import ValidationError
from django.contrib.auth.models import User

# Import soft delete functionality
from .soft_delete import SoftDeleteMixin, SoftDeleteManager

# Postgres-specific features
try:
    from django.contrib.postgres.constraints import ExclusionConstraint
    from django.contrib.postgres.fields import DateTimeRangeField
    from django.contrib.postgres.indexes import GistIndex
    POSTGRES = True
except ImportError:
    POSTGRES = False

# Disable PostgreSQL features when not using a Postgres engine (e.g., tests)
import os
from django.conf import settings as django_settings  # alias to avoid confusion
if (
    os.environ.get('DJANGO_SETTINGS_MODULE') == 'backend.settings_test'
    or 'postgresql' not in django_settings.DATABASES.get('default', {}).get('ENGINE', '')
):
    POSTGRES = False

class Property(SoftDeleteMixin, models.Model):
    name       = models.CharField(max_length=100)
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
    
    # History tracking
    history = models.TextField(blank=True, default='[]', help_text="JSON array of change history")

    # Managers
    objects = SoftDeleteManager()  # Default manager excludes deleted
    all_objects = models.Manager()  # Includes deleted objects

    class Meta:
        constraints = [
            # Soft-delete aware uniqueness constraint
            models.UniqueConstraint(
                fields=['name'],
                condition=Q(is_deleted=False),
                name='uniq_property_name'
            ),
        ]
        indexes = [models.Index(fields=['name'])]

    def __str__(self):
        return self.name

    def save(self, *args, **kwargs):
        # Only build history on updates, not on initial creation
        if self.pk:
            try:
                old = Property.objects.get(pk=self.pk)
                changes = []
                user = getattr(self, 'modified_by', None)
                user_name = getattr(user, 'username', 'system') if user else 'system'

                # Name change
                if old.name != self.name:
                    changes.append(
                        f"{timezone.now().isoformat()}: {user_name} changed property name "
                        f"from '{old.name}' to '{self.name}'"
                    )

                # Address change
                if old.address != self.address:
                    changes.append(
                        f"{timezone.now().isoformat()}: {user_name} changed address "
                        f"from '{old.address}' to '{self.address}'"
                    )

                if changes:
                    import json
                    hist = json.loads(old.history or "[]")
                    hist.extend(changes)
                    self.history = json.dumps(hist)
            except Property.DoesNotExist:
                pass  # New object, no history to compare

        super().save(*args, **kwargs)


# ----------------------------------------------------------------------------
# Booking & Ownership domain (Property-centric design)
# ----------------------------------------------------------------------------

class Booking(SoftDeleteMixin, models.Model):
    """A booking window for a property. Tasks will typically be linked to a booking."""
    STATUS_CHOICES = [
        ('booked', 'Booked'),
        ('confirmed', 'Confirmed'),
        ('currently_hosting', 'Currently Hosting'),
        ('owner_staying', 'Owner Staying'),
        ('cancelled', 'Cancelled'),
        ('completed', 'Completed'),
    ]

    property = models.ForeignKey('Property', on_delete=models.CASCADE, related_name='bookings')
    check_in_date = models.DateTimeField()
    check_out_date = models.DateTimeField()
    guest_name = models.CharField(max_length=200, blank=True)
    guest_contact = models.CharField(max_length=200, blank=True)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='booked')
    
    # Excel import fields
    external_code = models.CharField(max_length=100, blank=True, help_text="External confirmation code from booking platform")
    external_status = models.CharField(max_length=100, blank=True, help_text="Status from external booking platform")
    source = models.CharField(max_length=50, blank=True, help_text="Booking source (Airbnb, VRBO, Direct, etc.)")
    listing_name = models.CharField(max_length=200, blank=True, help_text="Listing name from booking platform")
    earnings_amount = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True, help_text="Earnings from booking")
    earnings_currency = models.CharField(max_length=3, default='USD', help_text="Currency for earnings")
    booked_on = models.DateTimeField(null=True, blank=True, help_text="When the booking was made")
    adults = models.PositiveIntegerField(default=1, help_text="Number of adult guests")
    children = models.PositiveIntegerField(default=0, help_text="Number of children")
    infants = models.PositiveIntegerField(default=0, help_text="Number of infants")
    nights = models.PositiveIntegerField(null=True, blank=True, help_text="Number of nights")
    check_in_time = models.TimeField(null=True, blank=True, help_text="Check-in time")
    check_out_time = models.TimeField(null=True, blank=True, help_text="Check-out time")
    property_label_raw = models.CharField(max_length=200, blank=True, help_text="Original property label from Excel")
    same_day_note = models.TextField(blank=True, help_text="Same day cleaning notes")
    same_day_flag = models.BooleanField(default=False, help_text="Flag for same day cleaning")
    
    # Import tracking
    raw_row = models.JSONField(null=True, blank=True, help_text="Raw Excel row data for audit")
    last_import_update = models.DateTimeField(null=True, blank=True, help_text="Last time this booking was updated via import")
    
    # PROVENANCE FIELDS (Agent's recommendation)
    created_by = models.ForeignKey(settings.AUTH_USER_MODEL, null=True, blank=True,
                                   on_delete=models.SET_NULL, related_name='bookings_created')
    modified_by = models.ForeignKey(settings.AUTH_USER_MODEL, null=True, blank=True,
                                    on_delete=models.SET_NULL, related_name='bookings_modified')
    created_via = models.CharField(max_length=32, default='manual',
                                   help_text="manual|excel_import|api|system")
    modified_via = models.CharField(max_length=32, default='manual',
                                    help_text="manual|excel_import|api|system")
    
    # History tracking
    history = models.TextField(blank=True, default='[]', help_text="JSON array of change history")
    
    created_at = models.DateTimeField(auto_now_add=True)
    modified_at = models.DateTimeField(auto_now=True)

    # Managers
    objects = SoftDeleteManager()  # Default manager excludes deleted
    all_objects = models.Manager()  # Includes deleted objects

    class Meta:
        ordering = ['-check_in_date']
        indexes = [
            models.Index(fields=['property', 'check_in_date']),
            models.Index(fields=['property', 'check_out_date']),
            models.Index(fields=['status']),
            models.Index(fields=['source', 'external_code']),
        ]
        constraints = [
            models.CheckConstraint(
                condition=Q(check_in_date__lt=F('check_out_date')),
                name='booking_checkin_before_checkout'
            ),
            models.UniqueConstraint(
                fields=['property', 'source', 'external_code'],
                condition=Q(external_code__gt='') & Q(is_deleted=False),
                name='uniq_booking_external_code_per_property_source'
            ),
        ] + ([
            # Prevent overlaps for active bookings on same property (Postgres)
            ExclusionConstraint(
                name='booking_no_overlap_active',
                expressions=[
                    (F('property'), '='),
                    (
                        models.Func(
                            F('check_in_date'),
                            F('check_out_date'),
                            function='tstzrange',
                            output_field=DateTimeRangeField()
                        ),
                        '&&',
                    ),
                ],
                condition=~Q(status__in=['cancelled', 'completed']),
                # Remove index_type='gist' to use default index type
            ),
        ] if POSTGRES else [])

    def clean(self):
        if self.check_in_date and self.check_out_date and self.check_in_date >= self.check_out_date:
            raise ValidationError("check_in_date must be before check_out_date")

    def __str__(self):
        return f"Booking {self.property.name} {self.check_in_date:%Y-%m-%d} → {self.check_out_date:%Y-%m-%d}"
    
    def check_conflicts(self):
        """Check for booking conflicts with other properties"""
        conflicts = []
        
        # Check for same day check-in/check-out conflicts across different properties
        same_day_conflicts = Booking.objects.filter(
            check_in_date__date=self.check_out_date.date(),
            status__in=['booked', 'confirmed', 'currently_hosting']
        ).exclude(
            property=self.property  # Exclude same property
        ).exclude(
            id=self.id  # Exclude self
        )
        
        for conflict_booking in same_day_conflicts:
            conflicts.append({
                'type': 'same_day_checkout_checkin',
                'message': f"Same day conflict: Check-out from {self.property.name} on {self.check_out_date.date()}, check-in at {conflict_booking.property.name}",
                'booking': conflict_booking,
                'severity': 'high'
            })
        
        # Check for same day check-out/check-in conflicts (reverse)
        reverse_conflicts = Booking.objects.filter(
            check_out_date__date=self.check_in_date.date(),
            status__in=['booked', 'confirmed', 'currently_hosting']
        ).exclude(
            property=self.property  # Exclude same property
        ).exclude(
            id=self.id  # Exclude self
        )
        
        for conflict_booking in reverse_conflicts:
            conflicts.append({
                'type': 'same_day_checkin_checkout',
                'message': f"Same day conflict: Check-in at {self.property.name} on {self.check_in_date.date()}, check-out from {conflict_booking.property.name}",
                'booking': conflict_booking,
                'severity': 'high'
            })
        
        # Check for overlapping bookings on same property
        overlapping_bookings = Booking.objects.filter(
            property=self.property,
            check_in_date__lt=self.check_out_date,
            check_out_date__gt=self.check_in_date,
            status__in=['booked', 'confirmed', 'currently_hosting']
        ).exclude(id=self.id)
        
        for overlap_booking in overlapping_bookings:
            conflicts.append({
                'type': 'overlapping_dates',
                'message': f"Overlapping booking on {self.property.name}: {overlap_booking.check_in_date.date()} - {overlap_booking.check_out_date.date()}",
                'booking': overlap_booking,
                'severity': 'critical'
            })
        
        return conflicts
    
    def get_conflict_flag(self):
        """Get a formatted conflict flag for admin display"""
        conflicts = self.check_conflicts()
        if not conflicts:
            return "✅ No conflicts"
        
        conflict_count = len(conflicts)
        critical_count = len([c for c in conflicts if c['severity'] == 'critical'])
        high_count = len([c for c in conflicts if c['severity'] == 'high'])
        
        if critical_count > 0:
            return f"🔴 {critical_count} Critical, {high_count} High"
        elif high_count > 0:
            return f"🟡 {high_count} High priority conflicts"
        else:
            return f"⚠️ {conflict_count} conflicts"
    
    def get_conflict_details(self):
        """Get detailed conflict information for tooltips"""
        conflicts = self.check_conflicts()
        if not conflicts:
            return "No conflicts detected"
        
        details = []
        for conflict in conflicts:
            details.append(f"• {conflict['message']}")
        
        return "\n".join(details)


class PropertyOwnership(models.Model):
    """Maps users to properties as owners/viewers/managers with optional edit rights."""
    OWNERSHIP_TYPE_CHOICES = [
        ('owner', 'Owner'),
        ('viewer', 'Viewer'),
        ('manager', 'Manager'),
    ]

    property = models.ForeignKey('Property', on_delete=models.CASCADE, related_name='ownerships')
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='property_memberships')
    ownership_type = models.CharField(max_length=20, choices=OWNERSHIP_TYPE_CHOICES, default='viewer')
    can_edit = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = [('property', 'user', 'ownership_type')]

    def __str__(self):
        return f"{self.user} → {self.property} ({self.ownership_type})"


# ----------------------------------------------------------------------------
# Task domain
# ----------------------------------------------------------------------------

# Expanded task types to support all operations
TASK_TYPE_CHOICES = [
    ('administration', 'Administration'),
    ('cleaning', 'Cleaning'),
    ('maintenance', 'Maintenance'),
    ('laundry', 'Laundry'),
    ('lawn_pool', 'Lawn/Pool'),
    ('inspection', 'Inspection'),      # Add to match template options
    ('preparation', 'Preparation'),    # Add to match template options
    ('other', 'Other'),                # Add to match template options
]

class Task(SoftDeleteMixin, models.Model):
    STATUS_CHOICES = [
        ('pending', 'Pending'),
        ('waiting_dependency', 'Waiting for Dependency'),
        ('in-progress', 'In Progress'),
        ('completed', 'Completed'),
        ('canceled', 'Canceled'),
    ]

    task_type    = models.CharField(max_length=20, choices=TASK_TYPE_CHOICES, default='cleaning')
    title        = models.CharField(max_length=200)
    description  = models.TextField(blank=True)
    property_ref = models.ForeignKey('Property', on_delete=models.CASCADE, related_name='tasks', null=True, blank=True)
    booking      = models.ForeignKey('Booking', on_delete=models.SET_NULL, related_name='tasks', null=True, blank=True,
                                     help_text="Optional link to a booking window for property")
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
    depends_on   = models.ManyToManyField('self', blank=True, symmetrical=False, related_name='dependent_tasks',
                                          help_text="This task is blocked by the selected prerequisite tasks")
    
    # Agent's recommendation: Lock mechanism for import protection
    is_locked_by_user = models.BooleanField(default=False, help_text="Prevent auto-updates from imports")
    
    # Template tracking for auto-generated tasks
    created_by_template = models.ForeignKey(
        'AutoTaskTemplate',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        help_text="Template that created this task (if auto-generated)"
    )
    
    # users that do **not** want pushes for *this* task
    muted_by     = models.ManyToManyField(
        settings.AUTH_USER_MODEL,
        related_name='muted_tasks',
        blank=True,
        help_text="Users that muted notifications for this task"
    )

    # Managers
    objects = SoftDeleteManager()  # Default manager excludes deleted
    all_objects = models.Manager()  # Includes deleted objects

    def clean(self):
        # Agent's improvement: Auto-set property from booking to reduce user error
        if self.booking_id and not self.property_ref_id:
            self.property_ref = self.booking.property
        # Agent's recommendation: Prevent cross-property task linking
        if self.booking_id and self.property_ref_id and self.booking.property_id != self.property_ref_id:
            raise ValidationError("Task.property_ref must match Task.booking.property")


    def __str__(self):
        prop_name = self.property_ref.name if self.property_ref else "No property"
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
    def is_overdue(self):
        """Check if task is overdue."""
        if not self.due_date:
            return False
        return self.due_date < timezone.now()

    @property
    def is_due_soon(self):
        """Check if task is due within 24 hours."""
        if not self.due_date:
            return False
        now = timezone.now()
        return not self.is_overdue and (self.due_date - now).total_seconds() < 86400  # 24 hours

    class Meta:
        constraints = [
            # Prevent multiple tasks from the same template for the same booking (ignores soft-deleted)
            models.UniqueConstraint(
                fields=['booking', 'created_by_template'],
                condition=models.Q(created_by_template__isnull=False) & models.Q(is_deleted=False),
                name='uniq_template_task_per_booking',
            ),
        ]


def task_image_upload_path(instance, filename):
    """Generate secure upload path for task images with UUID naming"""
    import os
    import uuid
    from django.utils.text import slugify
    
    # Generate UUID-based filename for security
    original_name, ext = os.path.splitext(filename)
    ext = ext.lower() if ext else '.bin'
    
    # Validate file extension (security)
    allowed_extensions = {'.jpg', '.jpeg', '.png', '.gif', '.bmp', '.webp'}
    if ext not in allowed_extensions:
        ext = '.jpg'  # Default to jpg for invalid extensions
    
    # Create organized folder structure: task_images/{task_id}/{uuid}.ext
    task_id = instance.task.id if instance.task else 'staging'
    unique_filename = f"{uuid.uuid4().hex}{ext}"
    
    return f'task_images/{task_id}/{unique_filename}'


def validate_task_image(file):
    """Validate uploaded task image file - Only check if it's a real image, not size."""
    from django.core.exceptions import ValidationError
    from PIL import Image, UnidentifiedImageError
    
    # Only verify it's a real image file (no size check - handled by serializer)
    pos = file.tell()
    try:
        img = Image.open(file)
        img.verify()  # validates without decoding full image
    except (UnidentifiedImageError, OSError):
        raise ValidationError("Invalid image file.")
    finally:
        file.seek(pos)


class TaskImage(models.Model):
    # Photo type choices for before/after functionality
    PHOTO_TYPE_CHOICES = [
        ('before', 'Before'),
        ('after', 'After'),
        ('during', 'During'),
        ('reference', 'Reference'),
        ('damage', 'Damage'),
        ('general', 'General'),
        ('checklist', 'Checklist'),  # unify checklist photos with task images
    ]
    
    # Photo status choices for approval workflow
    PHOTO_STATUS_CHOICES = [
        ('pending', 'Pending Review'),
        ('approved', 'Approved'),
        ('rejected', 'Rejected'),
        ('archived', 'Archived'),
    ]
    
    task = models.ForeignKey(Task, on_delete=models.CASCADE, related_name='images')
    image = models.ImageField(upload_to=task_image_upload_path, validators=[validate_task_image])
    uploaded_at = models.DateTimeField(auto_now_add=True)
    uploaded_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, blank=True, related_name='uploaded_task_images')
    # Optional link to a specific checklist response when the image originates from checklist UI
    checklist_response = models.ForeignKey('ChecklistResponse', on_delete=models.CASCADE, null=True, blank=True, related_name='task_images')
    
    # NEW: Before/After photo categorization
    photo_type = models.CharField(
        max_length=20,
        choices=PHOTO_TYPE_CHOICES,
        default='general',
        help_text="Type of photo for before/after comparison"
    )
    
    # NEW: Photo status for approval workflow
    photo_status = models.CharField(
        max_length=20,
        choices=PHOTO_STATUS_CHOICES,
        default='pending',
        help_text="Approval status of the photo"
    )
    
    # NEW: Photo grouping and ordering
    sequence_number = models.PositiveIntegerField(
        default=1,
        help_text="Order within the same photo_type group"
    )
    
    # NEW: Primary photo designation
    is_primary = models.BooleanField(
        default=False,
        help_text="Primary photo for this type (e.g., main 'before' photo)"
    )
    
    # NEW: Detailed description
    description = models.TextField(
        blank=True,
        help_text="Detailed description of what the photo shows"
    )
    
    # Agent's recommended metadata fields for optimized images
    size_bytes = models.PositiveIntegerField(null=True, blank=True, help_text="Optimized file size in bytes")
    width = models.PositiveIntegerField(null=True, blank=True, help_text="Image width in pixels")  
    height = models.PositiveIntegerField(null=True, blank=True, help_text="Image height in pixels")
    original_size_bytes = models.PositiveIntegerField(null=True, blank=True, help_text="Original upload size before optimization")

    class Meta:
        ordering = ['task', 'photo_type', 'sequence_number', 'uploaded_at']
        unique_together = ['task', 'photo_type', 'sequence_number']
        indexes = [
            models.Index(fields=['task', 'photo_type']),
            models.Index(fields=['photo_status']),
            models.Index(fields=['uploaded_at']),
            models.Index(fields=['checklist_response']),
        ]

    def __str__(self):
        return f"{self.get_photo_type_display()} image for {self.task.title} (#{self.sequence_number})"
    
    def clean(self):
        """Validate photo constraints"""
        from django.core.exceptions import ValidationError
        
        # Ensure only one primary photo per type per task
        if self.is_primary and self.pk:
            existing_primary = TaskImage.objects.filter(
                task=self.task,
                photo_type=self.photo_type,
                is_primary=True
            ).exclude(pk=self.pk)
            if existing_primary.exists():
                raise ValidationError(f"Only one primary photo allowed per type per task. Found existing primary {self.photo_type} photo.")
    
    def save(self, *args, **kwargs):
        """Auto-set primary photo if none exists for this type"""
        if not self.pk:  # New instance
            # If this is the first photo of this type for this task, make it primary
            existing_photos = TaskImage.objects.filter(
                task=self.task,
                photo_type=self.photo_type
            )
            if not existing_photos.exists():
                self.is_primary = True
        
        self.clean()
        super().save(*args, **kwargs)
    
class UserRole(models.TextChoices):
    """
    User role hierarchy - defines access level and permissions
    """
    STAFF       = 'staff',       'Staff/Crew'    # Normal users who perform tasks
    MANAGER     = 'manager',     'Manager'       # Manages staff and properties
    SUPERUSER   = 'superuser',   'Superuser'     # Full system admin access
    VIEWER      = 'viewer',      'Viewer'        # Read-only access


class TaskGroup(models.TextChoices):
    """
    Task groups for staff assignment and dashboard permissions
    """
    CLEANING    = 'cleaning',    'Cleaning'      # Housekeeping, room cleaning, turnover
    MAINTENANCE = 'maintenance', 'Maintenance'   # Repairs, HVAC, plumbing, electrical
    LAUNDRY     = 'laundry',     'Laundry'       # Linens, towels, bedding
    LAWN_POOL   = 'lawn_pool',   'Lawn/Pool'     # Landscaping, pool maintenance, outdoor
    GENERAL     = 'general',     'General'       # Multi-purpose, flexible assignments
    NONE        = 'none',        'Not Assigned'  # No specific task group


class DepartmentGroups:
    """
    Department group names - used with Django's Group model
    Staff/Crew users can belong to multiple departments
    """
    ADMINISTRATION = 'Administration'
    CLEANING = 'Cleaning'
    MAINTENANCE = 'Maintenance'  
    LAUNDRY = 'Laundry'
    LAWN_POOL = 'Lawn/Pool'
    
    @classmethod
    def get_all_departments(cls):
        """Return list of all department names"""
        return [
            cls.ADMINISTRATION,
            cls.CLEANING,
            cls.MAINTENANCE,
            cls.LAUNDRY,
            cls.LAWN_POOL,
        ]
    
    @classmethod
    def get_choices(cls):
        """Return choices format for forms"""
        return [(dept, dept) for dept in cls.get_all_departments()]

class Profile(models.Model):
    user     = models.OneToOneField(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    # Curated timezone choices for AriStay locations
    TIMEZONE_CHOICES = [
        ('America/New_York', 'Eastern Time (Tampa, FL)'),
        ('America/Los_Angeles', 'Pacific Time (San Jose, CA)'),
        ('America/Chicago', 'Central Time (Chicago, IL)'),
        ('America/Denver', 'Mountain Time (Denver, CO)'),
        ('America/Phoenix', 'Arizona Time (Phoenix, AZ)'),
        ('America/Anchorage', 'Alaska Time (Anchorage, AK)'),
        ('Pacific/Honolulu', 'Hawaii Time (Honolulu, HI)'),
        ('Asia/Ho_Chi_Minh', 'Vietnam Time (Ho Chi Minh City)'),
        ('Europe/London', 'GMT/BST (London, UK)'),
        ('UTC', 'UTC (Coordinated Universal Time)'),
    ]
    
    timezone = models.CharField(
        max_length=32,
        choices=TIMEZONE_CHOICES,
        default='America/New_York',  # Tampa, FL timezone as default
        help_text="Your local timezone for displaying dates and times"
    )
    digest_opt_out = models.BooleanField(default=False)

    # Contact and location information
    phone_number = models.CharField(
        max_length=20,
        blank=True,
        null=True,
        help_text="User's phone number (optional)"
    )
    address = models.TextField(
        blank=True,
        null=True,
        help_text="User's address (optional)"
    )

    # NEW
    role = models.CharField(
        max_length=16,
        choices=UserRole.choices,
        default=UserRole.STAFF,
        help_text="App role separate from Django is_staff/is_superuser."
    )
    
    # Task group assignment for staff/crew
    task_group = models.CharField(
        max_length=16,
        choices=TaskGroup.choices,
        default=TaskGroup.NONE,
        help_text="Primary task group for staff assignment and dashboard permissions"
    )
    
    # Team visibility controls
    can_view_team_tasks = models.BooleanField(
        default=True,
        help_text="Can view all team tasks in department dashboards"
    )
    can_view_other_teams = models.BooleanField(
        default=False,
        help_text="Can view other department dashboards (maintenance, cleaning, etc.)"
    )

    def __str__(self):
        return f"{self.user.username} profile"
    
    def get_task_group_display(self):
        """Get human-readable task group name"""
        return dict(TaskGroup.choices).get(self.task_group, 'Not Assigned')
    
    def is_in_task_group(self, task_group):
        """Check if user is assigned to a specific task group"""
        # Handle both string and TaskGroup enum inputs
        if hasattr(task_group, 'value'):
            task_group_value = task_group.value
        else:
            task_group_value = task_group
        return self.task_group == task_group_value
    
    def can_view_task_group(self, task_group):
        """Check if user can view tasks for a specific task group"""
        # Handle both string and TaskGroup enum inputs
        if hasattr(task_group, 'value'):
            task_group_value = task_group.value
        else:
            task_group_value = task_group
            
        # Superusers and managers can view all task groups
        if self.role in [UserRole.SUPERUSER, UserRole.MANAGER]:
            return True
        
        # Staff can view their own task group and general tasks
        if self.role == UserRole.STAFF:
            return self.task_group == task_group_value or task_group_value == TaskGroup.GENERAL.value
        
        # Viewers have limited access - can only view if they have permission
        if self.role == UserRole.VIEWER:
            return self.can_view_other_teams
        
        return False
    
    def get_accessible_task_groups(self):
        """Get list of task groups this user can access"""
        if self.role in [UserRole.SUPERUSER, UserRole.MANAGER]:
            # Managers and superusers can access all task groups except NONE
            return [TaskGroup(choice[0]) for choice in TaskGroup.choices if choice[0] != TaskGroup.NONE.value]
        
        if self.role == UserRole.STAFF:
            # Staff can access their own task group plus GENERAL (if not already GENERAL)
            # Exception: if task group is NONE, only allow GENERAL
            if self.task_group == TaskGroup.NONE.value:
                return [TaskGroup.GENERAL]
            
            groups = [TaskGroup(self.task_group)]
            if self.task_group != TaskGroup.GENERAL.value:
                groups.append(TaskGroup.GENERAL)
            return groups
        
        if self.role == UserRole.VIEWER and self.can_view_other_teams:
            # Viewers with cross-team permission can access all task groups except NONE
            return [TaskGroup(choice[0]) for choice in TaskGroup.choices if choice[0] != TaskGroup.NONE.value]
        
        # Viewers without cross-team permission get empty list
        return []
    
    def get_departments(self):
        """Get list of departments (groups) this user belongs to"""
        return list(self.user.groups.filter(
            name__in=DepartmentGroups.get_all_departments()
        ).values_list('name', flat=True))
    
    def add_to_department(self, department_name):
        """Add user to a department group"""
        from django.contrib.auth.models import Group
        if department_name in DepartmentGroups.get_all_departments():
            group, created = Group.objects.get_or_create(name=department_name)
            self.user.groups.add(group)
    
    def remove_from_department(self, department_name):
        """Remove user from a department group"""
        from django.contrib.auth.models import Group
        try:
            group = Group.objects.get(name=department_name)
            self.user.groups.remove(group)
        except Group.DoesNotExist:
            pass
    
    def is_in_department(self, department_name):
        """Check if user is in a specific department"""
        return self.user.groups.filter(name=department_name).exists()
    
    @property
    def departments_display(self):
        """Get comma-separated string of departments for display"""
        departments = self.get_departments()
        return ', '.join(departments) if departments else 'No departments'
    
    def has_permission(self, permission_name):
        """
        Check if user has a specific permission
        Priority: User Override > Role Permission > Baseline Role > Default Deny
        """
        from django.utils import timezone
        
        # Check for user-specific override first
        try:
            override = self.user.permission_overrides.get(
                permission__name=permission_name,
                permission__is_active=True
            )
            # Check if override is expired
            if override.expires_at and timezone.now() > override.expires_at:
                override.delete()  # Clean up expired override
            else:
                return override.granted
        except UserPermissionOverride.DoesNotExist:
            pass
        
        # Check role-based permission
        try:
            role_perm = RolePermission.objects.get(
                role=self.role,
                permission__name=permission_name,
                permission__is_active=True
            )
            return role_perm.granted
        except RolePermission.DoesNotExist:
            # Only use baseline if no explicit role permission is defined
            baseline_perms = self._get_baseline_role_permissions()
            if permission_name in baseline_perms:
                return baseline_perms[permission_name]
        
        # Default deny
        return False
    
    def _get_baseline_role_permissions(self):
        """Get baseline permissions for each role type"""
        _TASK_PERMS_BY_ROLE = {
            'superuser': {'view_tasks': True, 'add_tasks': True, 'change_tasks': True, 'delete_tasks': True},
            'manager':   {'view_tasks': True, 'add_tasks': True, 'change_tasks': True},
            'staff':     {'view_tasks': True, 'add_tasks': True},
            'viewer':    {'view_tasks': True},
        }
        return _TASK_PERMS_BY_ROLE.get(self.role, {})
    
    def can_delegate_permission(self, permission_name):
        """
        Check if user can grant/revoke a specific permission to others
        """
        try:
            role_perm = RolePermission.objects.get(
                role=self.role,
                permission__name=permission_name,
                permission__is_active=True
            )
            return role_perm.granted and role_perm.can_delegate
        except RolePermission.DoesNotExist:
            return False
    
    def get_all_permissions(self):
        """
        Get all permissions for this user (both role-based and overrides)
        Returns dict with permission names as keys and granted status as values
        """
        # Start with baseline role permissions
        permissions = self._get_baseline_role_permissions().copy()
        
        # Override with role permissions from database
        for role_perm in RolePermission.objects.filter(
            role=self.role,
            permission__is_active=True
        ):
            permissions[role_perm.permission.name] = role_perm.granted
        
        # Apply user overrides (these take precedence)
        for override in self.user.permission_overrides.filter(
            permission__is_active=True
        ):
            # Skip expired overrides
            if override.expires_at and timezone.now() > override.expires_at:
                continue
            permissions[override.permission.name] = override.granted
        
        return permissions
    
    def get_delegatable_permissions(self):
        """
        Get list of permissions this user can delegate to others
        """
        # Get explicit delegatable permissions from RolePermissions
        delegatable = set(RolePermission.objects.filter(
            role=self.role,
            permission__is_active=True,
            granted=True,
            can_delegate=True
        ).values_list('permission__name', flat=True))
        
        # Get permissions that have explicit RolePermission records (delegatable or not)
        explicit_permissions = set(RolePermission.objects.filter(
            role=self.role,
            permission__is_active=True,
        ).values_list('permission__name', flat=True))
        
        # Only add baseline delegatable permissions for permissions that don't have explicit records
        baseline_delegatable = self._get_baseline_delegatable_permissions()
        for perm in baseline_delegatable:
            if perm not in explicit_permissions:
                delegatable.add(perm)
        
        return delegatable
    
    def _get_baseline_delegatable_permissions(self):
        """Get baseline delegatable permissions for each role"""
        _DELEGATABLE_BY_ROLE = {
            'superuser': {'view_tasks', 'add_tasks', 'change_tasks', 'delete_tasks'},
            'manager':   {'view_tasks', 'add_tasks'},
            'staff':     set(),
            'viewer':    set(),
        }
        return _DELEGATABLE_BY_ROLE.get(self.role, set())


class CustomPermission(models.Model):
    """
    Define custom permissions that can be assigned to roles and users
    """
    PERMISSION_CHOICES = [
        # Property Management
        ('view_properties', 'View Properties'),
        ('add_properties', 'Add Properties'),
        ('change_properties', 'Edit Properties'),
        ('delete_properties', 'Delete Properties'),
        
        # Booking Management
        ('view_bookings', 'View Bookings'),
        ('add_bookings', 'Add Bookings'),
        ('change_bookings', 'Edit Bookings'),
        ('delete_bookings', 'Delete Bookings'),
        ('import_bookings', 'Import Bookings from Excel'),
        
        # Task Management
        ('view_tasks', 'View Tasks'),
        ('add_tasks', 'Add Tasks'),
        ('change_tasks', 'Edit Tasks'),
        ('delete_tasks', 'Delete Tasks'),
        ('assign_tasks', 'Assign Tasks to Others'),
        ('view_all_tasks', 'View All Tasks (not just own)'),
        
        # User Management
        ('view_users', 'View Users'),
        ('add_users', 'Add Users'),
        ('change_users', 'Edit Users'),
        ('delete_users', 'Delete Users'),
        ('manage_user_permissions', 'Manage User Permissions'),
        
        # Reports and Analytics
        ('view_reports', 'View Reports'),
        ('export_data', 'Export Data'),
        ('view_analytics', 'View Analytics Dashboard'),
        
        # System Administration
        ('access_admin_panel', 'Access Admin Panel'),
        ('manager_portal_access', 'Manager Portal Access'),
        ('manage_system_settings', 'Manage System Settings'),
        ('view_system_logs', 'View System Logs'),
        ('manage_notifications', 'Manage Notifications'),
        ('manage_files', 'Manage Files'),
        ('manage_permissions', 'Manage Permissions'),
        ('system_metrics_access', 'System Metrics Access'),
        ('system_recovery_access', 'System Crash Recovery Access'),
        ('manage_bookings', 'Manage Booking Operations'),
        
        # Checklist Management
        ('view_checklists', 'View Checklists'),
        ('add_checklists', 'Add Checklists'),
        ('change_checklists', 'Edit Checklists'),
        ('delete_checklists', 'Delete Checklists'),
        
        # Device Management
        ('view_devices', 'View Devices'),
        ('add_devices', 'Add Devices'),
        ('change_devices', 'Edit Devices'),
        ('delete_devices', 'Delete Devices'),
        
        # Inventory Management
        ('view_inventory', 'View Inventory'),
        ('change_inventory', 'Edit Inventory'),
        ('manage_inventory', 'Manage Inventory'),
    ]
    
    name = models.CharField(max_length=100, unique=True, choices=PERMISSION_CHOICES)
    description = models.TextField(blank=True, help_text="Detailed description of what this permission allows")
    is_active = models.BooleanField(default=True, help_text="Whether this permission is currently available")
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        ordering = ['name']
        verbose_name = 'Custom Permission'
        verbose_name_plural = 'Custom Permissions'
    
    def __str__(self):
        return self.get_name_display()


class RolePermission(models.Model):
    """
    Default permissions for each role
    """
    role = models.CharField(max_length=16, choices=UserRole.choices)
    permission = models.ForeignKey(CustomPermission, on_delete=models.CASCADE)
    granted = models.BooleanField(default=True, help_text="Whether this permission is granted to this role")
    can_delegate = models.BooleanField(default=False, help_text="Whether users with this role can grant/revoke this permission to others")
    created_at = models.DateTimeField(auto_now_add=True)
    created_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, blank=True)
    
    class Meta:
        unique_together = ['role', 'permission']
        ordering = ['role', 'permission__name']
        verbose_name = 'Role Permission'
        verbose_name_plural = 'Role Permissions'
    
    def __str__(self):
        status = "✓" if self.granted else "✗"
        delegate = " (can delegate)" if self.can_delegate else ""
        return f"{self.get_role_display()}: {status} {self.permission.get_name_display()}{delegate}"


class UserPermissionOverride(models.Model):
    """
    User-specific permission overrides that supersede role permissions
    """
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='permission_overrides')
    permission = models.ForeignKey(CustomPermission, on_delete=models.CASCADE)
    granted = models.BooleanField(help_text="Whether this permission is granted (True) or explicitly denied (False)")
    granted_by = models.ForeignKey(
        settings.AUTH_USER_MODEL, 
        on_delete=models.SET_NULL, 
        null=True, 
        blank=True,
        related_name='permissions_granted'
    )
    reason = models.TextField(blank=True, help_text="Reason for this permission override")
    expires_at = models.DateTimeField(null=True, blank=True, help_text="When this override expires (optional)")
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        unique_together = ['user', 'permission']
        ordering = ['user__username', 'permission__name']
        verbose_name = 'User Permission Override'
        verbose_name_plural = 'User Permission Overrides'
    
    def __str__(self):
        status = "✓ GRANTED" if self.granted else "✗ DENIED"
        expires = f" (expires {self.expires_at.strftime('%Y-%m-%d')})" if self.expires_at else ""
        return f"{self.user.username}: {status} {self.permission.get_name_display()}{expires}"
    
    @property
    def is_expired(self):
        """Check if this override has expired"""
        if not self.expires_at:
            return False
        return timezone.now() > self.expires_at

@receiver(post_save, sender=settings.AUTH_USER_MODEL)
def create_and_sync_user_profile(sender, instance, created, **kwargs):
    """Create profile for new users and sync superuser role."""
    # Skip if this is a raw save (e.g., from fixtures)
    if kwargs.get('raw', False):
        return
    
    # Set default role based on Django user flags - decouple is_staff from manager role
    default_role = UserRole.SUPERUSER if instance.is_superuser else UserRole.STAFF
    
    # Always use get_or_create to prevent duplicate creation
    profile, profile_created = Profile.objects.get_or_create(
        user=instance,
        defaults={
            'role': default_role,
            'timezone': 'America/New_York',  # Default timezone
            'can_view_team_tasks': True,
            'can_view_other_teams': False,
            'digest_opt_out': False,
        }
    )
    
    # Only auto-sync superuser role - do NOT sync is_staff to manager
    # This keeps Django admin permissions separate from business roles
    if instance.is_superuser and profile.role != UserRole.SUPERUSER:
        profile.role = UserRole.SUPERUSER
        profile.save()
    # REMOVED: is_staff -> manager auto-conversion for clean separation

class Device(models.Model):
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='devices')
    token = models.CharField(max_length=255, unique=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        # Agent's recommendation: Practical indexes for performance
        indexes = [models.Index(fields=['user'])]
        
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
    
    # History tracking
    history = models.TextField(blank=True, default='[]', help_text="JSON array of change history")

    class Meta:
        ordering = ['-timestamp']
        # Agent's recommendation: Practical indexes for performance
        indexes = [
            models.Index(fields=['recipient', 'read']),
            models.Index(fields=['push_sent']),
            models.Index(fields=['timestamp']),
        ]

    def __str__(self):
        return f"{self.verb} → {self.task.title} for {self.recipient.username}"

    def mark_pushed(self, commit: bool = True):
        if not self.push_sent:
            self.push_sent = True
            if commit:
                self.save(update_fields=["push_sent"])

    def save(self, *args, **kwargs):
        # Only build history on updates, not on initial creation
        if self.pk:
            try:
                old = Notification.objects.get(pk=self.pk)
                changes = []
                user = 'system'  # Default user since this model doesn't have modified_by

                # Read status change
                if old.read != self.read:
                    status = 'marked as read' if self.read else 'marked as unread'
                    changes.append(
                        f"{timezone.now().isoformat()}: {user} {status}"
                    )

                # Verb change
                if old.verb != self.verb:
                    changes.append(
                        f"{timezone.now().isoformat()}: {user} changed verb "
                        f"from '{old.verb}' to '{self.verb}'"
                    )

                # Push sent change
                if old.push_sent != self.push_sent:
                    status = 'marked as pushed' if self.push_sent else 'marked as not pushed'
                    changes.append(
                        f"{timezone.now().isoformat()}: {user} {status}"
                    )

                if changes:
                    import json
                    hist = json.loads(old.history or "[]")
                    hist.extend(changes)
                    self.history = json.dumps(hist)
            except Notification.DoesNotExist:
                pass  # New object, no history to compare

        super().save(*args, **kwargs)


# ----------------------------------------------------------------------------
# Checklist System - Room-by-room task completion workflows
# ----------------------------------------------------------------------------

class ChecklistTemplate(models.Model):
    """Template for creating task checklists. Defines what needs to be done."""
    name = models.CharField(max_length=200)
    task_type = models.CharField(max_length=20, choices=TASK_TYPE_CHOICES)
    description = models.TextField(blank=True)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    created_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    
    # History tracking
    history = models.TextField(blank=True, default='[]', help_text="JSON array of change history")
    
    class Meta:
        ordering = ['task_type', 'name']
    
    def __str__(self):
        return f"{self.get_task_type_display()} - {self.name}"

    def save(self, *args, **kwargs):
        # Only build history on updates, not on initial creation
        if self.pk:
            try:
                old = ChecklistTemplate.objects.get(pk=self.pk)
                changes = []
                user = getattr(self.created_by, 'username', 'system') if self.created_by else 'system'

                # Name change
                if old.name != self.name:
                    changes.append(
                        f"{timezone.now().isoformat()}: {user} changed template name "
                        f"from '{old.name}' to '{self.name}'"
                    )

                # Description change
                if old.description != self.description:
                    changes.append(
                        f"{timezone.now().isoformat()}: {user} changed description "
                        f"from '{old.description}' to '{self.description}'"
                    )

                # Task type change
                if old.task_type != self.task_type:
                    changes.append(
                        f"{timezone.now().isoformat()}: {user} changed task type "
                        f"from '{old.get_task_type_display()}' to '{self.get_task_type_display()}'"
                    )

                # Active status change
                if old.is_active != self.is_active:
                    status = 'activated' if self.is_active else 'deactivated'
                    changes.append(
                        f"{timezone.now().isoformat()}: {user} {status} template"
                    )

                if changes:
                    import json
                    hist = json.loads(old.history or "[]")
                    hist.extend(changes)
                    self.history = json.dumps(hist)
            except ChecklistTemplate.DoesNotExist:
                pass  # New object, no history to compare

        super().save(*args, **kwargs)


class ChecklistItem(models.Model):
    """Individual checklist items within a template."""
    ITEM_TYPE_CHOICES = [
        ('check', 'Check Item'),
        ('photo_required', 'Photo Required'),
        ('photo_optional', 'Photo Optional'),
        ('text_input', 'Text Input'),
        ('number_input', 'Number Input'),
        ('blocking', 'Blocking Step'),  # Must be completed before task can progress
    ]
    
    template = models.ForeignKey(ChecklistTemplate, on_delete=models.CASCADE, related_name='items')
    title = models.CharField(max_length=200)
    description = models.TextField(blank=True)
    item_type = models.CharField(max_length=20, choices=ITEM_TYPE_CHOICES, default='check')
    is_required = models.BooleanField(default=True)
    order = models.IntegerField(default=0)  # For ordering items within template
    
    # For room-specific checklists
    room_type = models.CharField(max_length=50, blank=True, help_text="e.g., bathroom, kitchen, bedroom")
    
    class Meta:
        ordering = ['template', 'order', 'room_type']
    
    def __str__(self):
        room_prefix = f"[{self.room_type}] " if self.room_type else ""
        return f"{room_prefix}{self.title}"


class TaskChecklist(models.Model):
    """Instance of a checklist for a specific task."""
    task = models.OneToOneField('Task', on_delete=models.CASCADE, related_name='checklist')
    template = models.ForeignKey(ChecklistTemplate, on_delete=models.CASCADE)
    started_at = models.DateTimeField(null=True, blank=True)
    completed_at = models.DateTimeField(null=True, blank=True)
    completed_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, blank=True)
    
    @property
    def is_completed(self):
        """Check if all required items are completed."""
        required_items = self.responses.filter(item__is_required=True)
        return all(response.is_completed for response in required_items)
    
    @property
    def completion_percentage(self):
        """Calculate completion percentage."""
        total_required = self.responses.filter(item__is_required=True).count()
        if total_required == 0:
            return 100
        completed_required = self.responses.filter(item__is_required=True, is_completed=True).count()
        return int((completed_required / total_required) * 100)
    
    @property
    def total_items(self):
        """Total number of checklist items."""
        return self.responses.count()
    
    @property
    def completed_items(self):
        """Number of completed checklist items."""
        return self.responses.filter(is_completed=True).count()
    
    @property
    def remaining_items(self):
        """Number of remaining checklist items."""
        return self.total_items - self.completed_items
    
    def __str__(self):
        return f"Checklist for {self.task.title}"


class ChecklistResponse(models.Model):
    """Response to a specific checklist item."""
    checklist = models.ForeignKey(TaskChecklist, on_delete=models.CASCADE, related_name='responses')
    item = models.ForeignKey(ChecklistItem, on_delete=models.CASCADE)
    
    # Response data
    is_completed = models.BooleanField(default=False)
    text_response = models.TextField(blank=True)
    number_response = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)
    
    # Metadata
    completed_at = models.DateTimeField(null=True, blank=True)
    completed_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, blank=True)
    notes = models.TextField(blank=True)
    
    class Meta:
        unique_together = ['checklist', 'item']
    
    def __str__(self):
        status = "✓" if self.is_completed else "○"
        return f"{status} {self.item.title}"


class ChecklistPhoto(models.Model):
    """Photos attached to checklist responses."""
    response = models.ForeignKey(ChecklistResponse, on_delete=models.CASCADE, related_name='photos')
    image = models.ImageField(upload_to='checklist_photos/%Y/%m/')
    caption = models.CharField(max_length=200, blank=True)
    uploaded_at = models.DateTimeField(auto_now_add=True)
    uploaded_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    
    def __str__(self):
        return f"Photo for {self.response.item.title}"


# ----------------------------------------------------------------------------
# Inventory Management System
# ----------------------------------------------------------------------------

class InventoryCategory(models.Model):
    """Categories for inventory items (e.g., Cleaning Supplies, Maintenance, Pool/Spa)"""
    name = models.CharField(max_length=100, unique=True)
    description = models.TextField(blank=True)
    icon = models.CharField(max_length=50, blank=True, help_text="CSS icon class or emoji")
    
    class Meta:
        verbose_name_plural = "Inventory Categories"
        ordering = ['name']
    
    def __str__(self):
        return self.name


class InventoryItem(models.Model):
    """Master catalog of inventory items that can be stocked at properties."""
    UNIT_CHOICES = [
        ('each', 'Each'),
        ('pack', 'Pack'),
        ('bottle', 'Bottle'),
        ('roll', 'Roll'),
        ('box', 'Box'),
        ('bag', 'Bag'),
        ('gallon', 'Gallon'),
        ('liter', 'Liter'),
        ('pounds', 'Pounds'),
        ('kg', 'Kilograms'),
    ]
    
    name = models.CharField(max_length=200)
    category = models.ForeignKey(InventoryCategory, on_delete=models.CASCADE, related_name='items')
    unit = models.CharField(max_length=20, choices=UNIT_CHOICES, default='each')
    description = models.TextField(blank=True)
    brand = models.CharField(max_length=100, blank=True)
    sku = models.CharField(max_length=100, blank=True)
    
    # Cost tracking
    estimated_cost = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)
    
    created_at = models.DateTimeField(auto_now_add=True)
    is_active = models.BooleanField(default=True)
    
    # History tracking
    history = models.TextField(blank=True, default='[]', help_text="JSON array of change history")
    
    class Meta:
        ordering = ['category', 'name']
    
    def __str__(self):
        return f"{self.name} ({self.get_unit_display()})"

    def save(self, *args, **kwargs):
        # Only build history on updates, not on initial creation
        if self.pk:
            try:
                old = InventoryItem.objects.get(pk=self.pk)
                changes = []
                user = 'system'  # Default user since this model doesn't have modified_by

                # Name change
                if old.name != self.name:
                    changes.append(
                        f"{timezone.now().isoformat()}: {user} changed name "
                        f"from '{old.name}' to '{self.name}'"
                    )

                # Description change
                if old.description != self.description:
                    changes.append(
                        f"{timezone.now().isoformat()}: {user} changed description "
                        f"from '{old.description}' to '{self.description}'"
                    )

                # Cost change
                if old.estimated_cost != self.estimated_cost:
                    changes.append(
                        f"{timezone.now().isoformat()}: {user} changed estimated cost "
                        f"from '{old.estimated_cost}' to '{self.estimated_cost}'"
                    )

                # Active status change
                if old.is_active != self.is_active:
                    status = 'activated' if self.is_active else 'deactivated'
                    changes.append(
                        f"{timezone.now().isoformat()}: {user} {status} item"
                    )

                if changes:
                    import json
                    hist = json.loads(old.history or "[]")
                    hist.extend(changes)
                    self.history = json.dumps(hist)
            except InventoryItem.DoesNotExist:
                pass  # New object, no history to compare

        super().save(*args, **kwargs)


class PropertyInventory(models.Model):
    """Tracks inventory levels for specific items at specific properties."""
    from django.core.validators import MinValueValidator
    
    property_ref = models.ForeignKey('Property', on_delete=models.CASCADE, related_name='inventory')
    item = models.ForeignKey('InventoryItem', on_delete=models.CASCADE)
    
    # Stock levels with agent's safety validators
    current_stock = models.DecimalField(max_digits=10, decimal_places=2, default=0,
                                        validators=[MinValueValidator(0)])
    par_level = models.DecimalField(max_digits=10, decimal_places=2,
                                    validators=[MinValueValidator(0)],
                                    help_text="Minimum stock level before reorder")
    max_level = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True,
                                    validators=[MinValueValidator(0)],
                                    help_text="Maximum stock capacity")
    
    # Location within property
    storage_location = models.CharField(max_length=200, blank=True, help_text="Where this item is stored")
    
    last_updated = models.DateTimeField(auto_now=True)
    updated_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, blank=True)
    
    # History tracking
    history = models.TextField(blank=True, default='[]', help_text="JSON array of change history")
    
    class Meta:
        unique_together = ['property_ref', 'item']
        ordering = ['property_ref', 'item__category', 'item__name']
    
    @property
    def is_low_stock(self):
        return self.current_stock <= self.par_level
    
    @property
    def stock_status(self):
        if self.current_stock <= 0:
            return 'out_of_stock'
        elif self.is_low_stock:
            return 'low_stock'
        elif self.max_level and self.current_stock >= self.max_level:
            return 'overstocked'
        else:
            return 'normal'
    
    def __str__(self):
        return f"{self.property_ref.name} - {self.item.name} ({self.current_stock} {self.item.get_unit_display()})"

    def save(self, *args, **kwargs):
        # Only build history on updates, not on initial creation
        if self.pk:
            try:
                old = PropertyInventory.objects.get(pk=self.pk)
                changes = []
                user = getattr(self.updated_by, 'username', 'system') if self.updated_by else 'system'

                # Stock level change
                if old.current_stock != self.current_stock:
                    changes.append(
                        f"{timezone.now().isoformat()}: {user} changed stock level "
                        f"from {old.current_stock} to {self.current_stock} {self.item.get_unit_display()}"
                    )

                # Par level change
                if old.par_level != self.par_level:
                    changes.append(
                        f"{timezone.now().isoformat()}: {user} changed par level "
                        f"from {old.par_level} to {self.par_level}"
                    )

                # Max level change
                if old.max_level != self.max_level:
                    changes.append(
                        f"{timezone.now().isoformat()}: {user} changed max level "
                        f"from {old.max_level} to {self.max_level}"
                    )

                # Storage location change
                if old.storage_location != self.storage_location:
                    changes.append(
                        f"{timezone.now().isoformat()}: {user} changed storage location "
                        f"from '{old.storage_location}' to '{self.storage_location}'"
                    )

                if changes:
                    import json
                    hist = json.loads(old.history or "[]")
                    hist.extend(changes)
                    self.history = json.dumps(hist)
            except PropertyInventory.DoesNotExist:
                pass  # New object, no history to compare

        super().save(*args, **kwargs)


class InventoryTransaction(models.Model):
    """Log of all inventory movements (stock-in, stock-out, adjustments)."""
    TRANSACTION_TYPES = [
        ('stock_in', 'Stock In'),
        ('stock_out', 'Stock Out'),
        ('adjustment', 'Adjustment'),
        ('damage', 'Damage/Loss'),
        ('transfer', 'Transfer'),
    ]
    
    property_inventory = models.ForeignKey(PropertyInventory, on_delete=models.CASCADE, related_name='transactions')
    transaction_type = models.CharField(max_length=20, choices=TRANSACTION_TYPES)
    quantity = models.DecimalField(max_digits=10, decimal_places=2)
    
    # Context
    task = models.ForeignKey('Task', on_delete=models.SET_NULL, null=True, blank=True, help_text="Related task if applicable")
    notes = models.TextField(blank=True)
    reference = models.CharField(max_length=100, blank=True, help_text="Receipt #, PO #, etc.")
    
    # Metadata
    created_at = models.DateTimeField(auto_now_add=True)
    created_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    
    # History tracking
    history = models.TextField(blank=True, default='[]', help_text="JSON array of change history")
    
    class Meta:
        ordering = ['-created_at']
    
    def __str__(self):
        sign = "+" if self.quantity > 0 else ""
        return f"{self.get_transaction_type_display()}: {sign}{self.quantity} {self.property_inventory.item.get_unit_display()}"

    def save(self, *args, **kwargs):
        # Only build history on updates, not on initial creation
        if self.pk:
            try:
                old = InventoryTransaction.objects.get(pk=self.pk)
                changes = []
                user = getattr(self.created_by, 'username', 'system') if self.created_by else 'system'

                # Transaction type change
                if old.transaction_type != self.transaction_type:
                    changes.append(
                        f"{timezone.now().isoformat()}: {user} changed transaction type "
                        f"from '{old.get_transaction_type_display()}' to '{self.get_transaction_type_display()}'"
                    )

                # Quantity change
                if old.quantity != self.quantity:
                    changes.append(
                        f"{timezone.now().isoformat()}: {user} changed quantity "
                        f"from {old.quantity} to {self.quantity}"
                    )

                # Notes change
                if old.notes != self.notes:
                    changes.append(
                        f"{timezone.now().isoformat()}: {user} changed notes "
                        f"from '{old.notes}' to '{self.notes}'"
                    )

                # Reference change
                if old.reference != self.reference:
                    changes.append(
                        f"{timezone.now().isoformat()}: {user} changed reference "
                        f"from '{old.reference}' to '{self.reference}'"
                    )

                if changes:
                    import json
                    hist = json.loads(old.history or "[]")
                    hist.extend(changes)
                    self.history = json.dumps(hist)
            except InventoryTransaction.DoesNotExist:
                pass  # New object, no history to compare

        super().save(*args, **kwargs)


# ----------------------------------------------------------------------------
# Lost & Found System
# ----------------------------------------------------------------------------

class LostFoundItem(models.Model):
    """Items found or reported lost at properties."""
    STATUS_CHOICES = [
        ('found', 'Found'),
        ('claimed', 'Claimed'),
        ('disposed', 'Disposed'),
        ('donated', 'Donated'),
    ]
    
    property_ref = models.ForeignKey('Property', on_delete=models.CASCADE, related_name='lost_found_items')
    task = models.ForeignKey('Task', on_delete=models.SET_NULL, null=True, blank=True, help_text="Task during which item was found")
    booking = models.ForeignKey('Booking', on_delete=models.SET_NULL, null=True, blank=True, help_text="Associated booking if known")
    
    # Item details
    title = models.CharField(max_length=200)
    description = models.TextField()
    category = models.CharField(max_length=100, blank=True, help_text="e.g., Electronics, Clothing, Jewelry")
    estimated_value = models.DecimalField(max_digits=8, decimal_places=2, null=True, blank=True)
    
    # Location & status
    found_location = models.CharField(max_length=200, help_text="Where in the property was it found")
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='found')
    
    # Tracking
    found_date = models.DateTimeField(auto_now_add=True)
    found_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='found_items')
    claimed_date = models.DateTimeField(null=True, blank=True)
    claimed_by = models.CharField(max_length=200, blank=True, help_text="Name of person who claimed it")
    
    # Storage
    storage_location = models.CharField(max_length=200, blank=True, help_text="Where item is currently stored")
    disposal_date = models.DateTimeField(null=True, blank=True)
    disposal_method = models.CharField(max_length=100, blank=True)
    
    notes = models.TextField(blank=True)
    
    # Provenance and history
    modified_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name='lostfound_modified'
    )
    modified_via = models.CharField(max_length=32, default='dashboard', help_text="admin|dashboard|api|system")
    history = models.TextField(blank=True, help_text="JSON field tracking changes to this item")
    
    class Meta:
        ordering = ['-found_date']
    
    def save(self, *args, **kwargs):
        # Only build history on updates, not on initial creation
        if self.pk:
            try:
                old = LostFoundItem.objects.get(pk=self.pk)
                changes = []
                
                # Determine actor: prefer modified_by (set by admin/save paths), then found_by
                user = getattr(self.modified_by, 'username', None) or (
                    getattr(self.found_by, 'username', 'system') if self.found_by else 'system'
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

                # Status change
                if old.status != self.status:
                    changes.append(
                        f"{timezone.now().isoformat()}: {user} changed status "
                        f"from '{old.get_status_display()}' to '{self.get_status_display()}'"
                    )

                # Category change
                if old.category != self.category:
                    old_cat = old.category or 'None'
                    new_cat = self.category or 'None'
                    changes.append(
                        f"{timezone.now().isoformat()}: {user} changed category "
                        f"from '{old_cat}' to '{new_cat}'"
                    )

                # Estimated value change
                if old.estimated_value != self.estimated_value:
                    old_val = f"${old.estimated_value}" if old.estimated_value else 'None'
                    new_val = f"${self.estimated_value}" if self.estimated_value else 'None'
                    changes.append(
                        f"{timezone.now().isoformat()}: {user} changed estimated value "
                        f"from '{old_val}' to '{new_val}'"
                    )

                # Found location change
                if old.found_location != self.found_location:
                    changes.append(
                        f"{timezone.now().isoformat()}: {user} changed found location "
                        f"from '{old.found_location}' to '{self.found_location}'"
                    )

                # Storage location change
                if old.storage_location != self.storage_location:
                    old_storage = old.storage_location or 'None'
                    new_storage = self.storage_location or 'None'
                    changes.append(
                        f"{timezone.now().isoformat()}: {user} changed storage location "
                        f"from '{old_storage}' to '{new_storage}'"
                    )

                # Claimed by change
                if old.claimed_by != self.claimed_by:
                    old_claimed = old.claimed_by or 'None'
                    new_claimed = self.claimed_by or 'None'
                    changes.append(
                        f"{timezone.now().isoformat()}: {user} changed claimed by "
                        f"from '{old_claimed}' to '{new_claimed}'"
                    )

                # Disposal method change
                if old.disposal_method != self.disposal_method:
                    old_disposal = old.disposal_method or 'None'
                    new_disposal = self.disposal_method or 'None'
                    changes.append(
                        f"{timezone.now().isoformat()}: {user} changed disposal method "
                        f"from '{old_disposal}' to '{new_disposal}'"
                    )

                # Notes change
                if old.notes != self.notes:
                    changes.append(
                        f"{timezone.now().isoformat()}: {user} changed notes "
                        f"from '{old.notes}' to '{self.notes}'"
                    )

                # Property change
                if old.property_ref_id != self.property_ref_id:
                    changes.append(
                        f"{timezone.now().isoformat()}: {user} changed property "
                        f"from '{old.property_ref.name}' to '{self.property_ref.name}'"
                    )

                # Task change
                if old.task_id != self.task_id:
                    old_task = old.task.title if old.task else 'None'
                    new_task = self.task.title if self.task else 'None'
                    changes.append(
                        f"{timezone.now().isoformat()}: {user} changed associated task "
                        f"from '{old_task}' to '{new_task}'"
                    )

                # Booking change
                if old.booking_id != self.booking_id:
                    old_booking = f"#{old.booking.id}" if old.booking else 'None'
                    new_booking = f"#{self.booking.id}" if self.booking else 'None'
                    changes.append(
                        f"{timezone.now().isoformat()}: {user} changed associated booking "
                        f"from '{old_booking}' to '{new_booking}'"
                    )

                # Update history if there are changes
                if changes:
                    import json
                    hist = json.loads(old.history or "[]")
                    self.history = json.dumps(hist + changes)

            except LostFoundItem.DoesNotExist:
                pass  # This is a new item, no history to build

        super().save(*args, **kwargs)

    def __str__(self):
        return f"{self.title} - {self.property_ref.name} ({self.get_status_display()})"


class LostFoundPhoto(models.Model):
    """Photos of lost & found items."""
    item = models.ForeignKey(LostFoundItem, on_delete=models.CASCADE, related_name='photos')
    image = models.ImageField(upload_to='lost_found/%Y/%m/')
    caption = models.CharField(max_length=200, blank=True)
    uploaded_at = models.DateTimeField(auto_now_add=True)
    uploaded_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    
    def __str__(self):
        return f"Photo of {self.item.title}"


# ----------------------------------------------------------------------------
# Recurring Schedules System
# ----------------------------------------------------------------------------

class ScheduleTemplate(models.Model):
    """Template for recurring task schedules."""
    FREQUENCY_CHOICES = [
        ('daily', 'Daily'),
        ('weekly', 'Weekly'), 
        ('monthly', 'Monthly'),
        ('quarterly', 'Quarterly'),
        ('yearly', 'Yearly'),
        ('custom', 'Custom'),
    ]
    
    WEEKDAY_CHOICES = [
        (0, 'Monday'),
        (1, 'Tuesday'),
        (2, 'Wednesday'),
        (3, 'Thursday'),
        (4, 'Friday'),
        (5, 'Saturday'),
        (6, 'Sunday'),
    ]
    
    name = models.CharField(max_length=200)
    task_type = models.CharField(max_length=20, choices=TASK_TYPE_CHOICES)
    property_ref = models.ForeignKey('Property', on_delete=models.CASCADE, related_name='schedule_templates', null=True, blank=True)
    
    # Task details
    task_title_template = models.CharField(max_length=200, help_text="Use {date}, {property} for dynamic values")
    task_description_template = models.TextField(blank=True, help_text="Template for task description")
    
    # Scheduling
    frequency = models.CharField(max_length=20, choices=FREQUENCY_CHOICES)
    interval = models.IntegerField(default=1, help_text="Every X days/weeks/months")
    weekday = models.IntegerField(choices=WEEKDAY_CHOICES, null=True, blank=True, help_text="For weekly schedules")
    day_of_month = models.IntegerField(null=True, blank=True, help_text="For monthly schedules (1-31)")
    
    # Timing
    start_date = models.DateField(help_text="When to start generating tasks")
    end_date = models.DateField(null=True, blank=True, help_text="When to stop (optional)")
    time_of_day = models.TimeField(default=time(9, 0), help_text="Default time for generated tasks")
    advance_days = models.IntegerField(default=1, help_text="Create task X days in advance")
    
    # Assignment
    default_assignee = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, blank=True)
    checklist_template = models.ForeignKey(ChecklistTemplate, on_delete=models.SET_NULL, null=True, blank=True)
    
    # Status
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    created_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='created_schedules')
    last_generated = models.DateTimeField(null=True, blank=True, help_text="Last time tasks were generated")
    
    class Meta:
        ordering = ['property_ref', 'task_type', 'name']
    
    def __str__(self):
        prop_name = self.property_ref.name if self.property_ref else "All Properties"
        return f"{self.name} - {prop_name} ({self.get_frequency_display()})"
    
    def get_next_due_date(self, from_date=None):
        """Calculate the next due date for this schedule."""
        from datetime import date, timedelta
        from dateutil.relativedelta import relativedelta
        
        if not from_date:
            from_date = self.last_generated.date() if self.last_generated else self.start_date
        
        if self.frequency == 'daily':
            return from_date + timedelta(days=self.interval)
        elif self.frequency == 'weekly':
            days_ahead = self.weekday - from_date.weekday()
            if days_ahead <= 0:  # Target day already happened this week
                days_ahead += 7 * self.interval
            return from_date + timedelta(days=days_ahead)
        elif self.frequency == 'monthly':
            next_month = from_date + relativedelta(months=self.interval)
            if self.day_of_month:
                try:
                    return next_month.replace(day=self.day_of_month)
                except ValueError:
                    # Handle invalid dates (e.g., Feb 31 -> Feb 28/29)
                    return next_month.replace(day=min(self.day_of_month, 28))
            return next_month
        elif self.frequency == 'quarterly':
            return from_date + relativedelta(months=3 * self.interval)
        elif self.frequency == 'yearly':
            return from_date + relativedelta(years=self.interval)
        
        return from_date  # Fallback for custom
    
    def should_generate_task(self, check_date=None):
        """Check if a task should be generated for this schedule."""
        from datetime import date, datetime, timedelta
        
        if not self.is_active:
            return False
        
        if not check_date:
            check_date = date.today()
        
        # Don't generate if past end date
        if self.end_date and check_date > self.end_date:
            return False
        
        # Don't generate if before start date
        if check_date < self.start_date:
            return False
        
        # Calculate when the task should be due
        next_due_date = self.get_next_due_date()
        
        # Check if we should create the task now (advance_days before due)
        create_date = next_due_date - timedelta(days=self.advance_days)
        
        return check_date >= create_date and (
            not self.last_generated or 
            self.last_generated.date() < create_date
        )


class GeneratedTask(models.Model):
    """Tracks tasks that were auto-generated from schedules."""
    schedule = models.ForeignKey(ScheduleTemplate, on_delete=models.CASCADE, related_name='generated_tasks')
    task = models.OneToOneField('Task', on_delete=models.CASCADE, related_name='generated_from')
    generated_at = models.DateTimeField(auto_now_add=True)
    generated_for_date = models.DateField(help_text="The date this task was scheduled for")
    
    # History tracking
    history = models.TextField(blank=True, default='[]', help_text="JSON array of change history")
    
    class Meta:
        unique_together = ['schedule', 'generated_for_date']
        ordering = ['-generated_for_date']
    
    def __str__(self):
        return f"Generated: {self.task.title} ({self.generated_for_date})"

    def save(self, *args, **kwargs):
        # Only build history on updates, not on initial creation
        if self.pk:
            try:
                old = GeneratedTask.objects.get(pk=self.pk)
                changes = []
                user = 'system'  # Default user since this model doesn't have modified_by

                # Generated for date change
                if old.generated_for_date != self.generated_for_date:
                    changes.append(
                        f"{timezone.now().isoformat()}: {user} changed generated for date "
                        f"from {old.generated_for_date} to {self.generated_for_date}"
                    )

                # Schedule change
                if old.schedule_id != self.schedule_id:
                    old_schedule = old.schedule.name if old.schedule else 'None'
                    new_schedule = self.schedule.name if self.schedule else 'None'
                    changes.append(
                        f"{timezone.now().isoformat()}: {user} changed schedule "
                        f"from '{old_schedule}' to '{new_schedule}'"
                    )

                if changes:
                    import json
                    hist = json.loads(old.history or "[]")
                    hist.extend(changes)
                    self.history = json.dumps(hist)
            except GeneratedTask.DoesNotExist:
                pass  # New object, no history to compare

        super().save(*args, **kwargs)


# ----------------------------------------------------------------------------
# Booking Calendar Import System
# ----------------------------------------------------------------------------

class BookingImportTemplate(models.Model):
    """Template for importing bookings from external calendars or CSV files."""
    name = models.CharField(max_length=200)
    property_ref = models.ForeignKey('Property', on_delete=models.CASCADE, related_name='import_templates')
    
    # Import source
    import_type = models.CharField(max_length=20, choices=[
        ('csv', 'CSV File'),
        ('ical', 'iCal/Calendar'),
        ('airbnb', 'Airbnb Export'),
        ('vrbo', 'VRBO Export'),
        ('api', 'API Integration'),
    ])
    
    # Field mapping for CSV imports
    date_format = models.CharField(max_length=50, default='%Y-%m-%d', help_text="Python strftime format")
    checkin_field = models.CharField(max_length=100, default='check_in', help_text="CSV column name for check-in")
    checkout_field = models.CharField(max_length=100, default='check_out', help_text="CSV column name for check-out")
    guest_name_field = models.CharField(max_length=100, default='guest_name', help_text="CSV column for guest name")
    guest_contact_field = models.CharField(max_length=100, default='guest_email', help_text="CSV column for contact")
    
    # Auto-task generation
    auto_create_tasks = models.BooleanField(default=True)
    cleaning_schedule = models.ForeignKey(ScheduleTemplate, on_delete=models.SET_NULL, null=True, blank=True, 
                                        related_name='cleaning_imports',
                                        help_text="Schedule to trigger for cleaning tasks")
    
    # Settings
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    created_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    last_import = models.DateTimeField(null=True, blank=True)
    
    def __str__(self):
        return f"{self.name} - {self.property_ref.name} ({self.get_import_type_display()})"


class BookingImportLog(models.Model):
    """Log of booking import operations."""
    template = models.ForeignKey(BookingImportTemplate, on_delete=models.CASCADE, related_name='import_logs', null=True, blank=True)
    import_file = models.FileField(upload_to='booking_imports/%Y/%m/', null=True, blank=True)
    
    # Results
    total_rows = models.IntegerField(default=0)
    successful_imports = models.IntegerField(default=0)
    errors_count = models.IntegerField(default=0)
    errors_log = models.TextField(blank=True)
    
    # Task creation tracking
    total_tasks_created = models.IntegerField(default=0, help_text="Number of automated tasks created")
    
    # Metadata
    imported_at = models.DateTimeField(auto_now_add=True)
    imported_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    
    class Meta:
        ordering = ['-imported_at']
    
    def __str__(self):
        return f"Import {self.imported_at.strftime('%Y-%m-%d %H:%M')} - {self.successful_imports}/{self.total_rows} success"


class TaskTemplateTracking(models.Model):
    """Track which template created which task"""
    task = models.OneToOneField('Task', on_delete=models.CASCADE, related_name='template_info')
    template = models.ForeignKey('AutoTaskTemplate', on_delete=models.SET_NULL, null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        verbose_name = "Task Template Tracking"
        verbose_name_plural = "Task Template Tracking"


class AutoTaskTemplate(models.Model):
    """Template for automatically creating tasks during booking import"""
    
    TIMING_CHOICES = [
        ('before_checkin', 'Days Before Check-in'),
        ('after_checkout', 'Days After Check-out'),
        ('fixed_time', 'Fixed Time of Day'),
    ]
    
    TASK_TYPE_CHOICES = [
        ('administration', 'Administration'),
        ('cleaning', 'Cleaning'),
        ('maintenance', 'Maintenance'),
        ('laundry', 'Laundry'),
        ('lawn_pool', 'Lawn/Pool'),
        ('inspection', 'Inspection'),
        ('preparation', 'Preparation'),
        ('other', 'Other'),
    ]
    
    name = models.CharField(max_length=100, help_text="Template name for identification")
    is_active = models.BooleanField(default=True, help_text="Whether this template is active")
    
    # Task Configuration
    task_type = models.CharField(max_length=20, choices=TASK_TYPE_CHOICES, default='cleaning')
    title_template = models.CharField(
        max_length=200, 
        help_text="Task title template. Use {property}, {guest_name}, {check_in_date}, etc."
    )
    description_template = models.TextField(
        blank=True,
        help_text="Task description template. Use {property}, {guest_name}, {check_in_date}, etc."
    )
    
    # Timing Configuration
    timing_type = models.CharField(max_length=20, choices=TIMING_CHOICES, default='before_checkin')
    timing_offset = models.IntegerField(
        default=1,
        help_text="Days before/after check-in/out (positive number)"
    )
    timing_hour = models.TimeField(
        null=True, 
        blank=True,
        help_text="Specific time of day (optional)"
    )
    
    # Conditions
    property_types = models.ManyToManyField(
        'Property', 
        blank=True,
        help_text="Apply only to specific properties (empty = all properties)"
    )
    booking_sources = models.CharField(
        max_length=200,
        blank=True,
        help_text="Comma-separated list of booking sources (e.g., 'Airbnb,VRBO') or empty for all"
    )
    
    # Assignment
    default_assignee = models.ForeignKey(
        User,
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        help_text="Default user to assign tasks to"
    )
    
    # Metadata
    created_by = models.ForeignKey(User, on_delete=models.CASCADE, related_name='created_task_templates')
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        ordering = ['name']
        
    def __str__(self):
        return f"{self.name} ({'Active' if self.is_active else 'Inactive'})"
    
    def create_task_for_booking(self, booking):
        """Create a task for a specific booking using this template (idempotent)"""
        from django.db import transaction
        
        # Check conditions
        if self.property_types.exists() and booking.property not in self.property_types.all():
            return None
            
        if self.booking_sources:
            allowed_sources = [s.strip().lower() for s in self.booking_sources.split(',')]
            if booking.source.lower() not in allowed_sources:
                return None
        
        # Calculate due date
        due_date = None
        if self.timing_type == 'before_checkin':
            due_date = booking.check_in_date - timedelta(days=self.timing_offset)
        elif self.timing_type == 'after_checkout':
            due_date = booking.check_out_date + timedelta(days=self.timing_offset)
        
        # Apply specific time if provided
        if due_date and self.timing_hour:
            due_date = due_date.replace(
                hour=self.timing_hour.hour,
                minute=self.timing_hour.minute,
                second=0,
                microsecond=0
            )
        
        # Render templates
        context = {
            'property': booking.property.name,
            'guest_name': booking.guest_name,
            'check_in_date': booking.check_in_date.strftime('%Y-%m-%d'),
            'check_out_date': booking.check_out_date.strftime('%Y-%m-%d'),
            'source': booking.source,
            'external_code': booking.external_code,
        }
        
        title = self.title_template.format(**context)
        description = self.description_template.format(**context) if self.description_template else ""
        
        # Idempotent creation with DB-level safety
        with transaction.atomic():
            # Quick exist check for speed
            if Task.objects.filter(booking=booking, created_by_template=self, is_deleted=False).exists():
                return None  # already created earlier
            
            task, created = Task.objects.get_or_create(
                booking=booking,
                created_by_template=self,
                defaults={
                    'title': title,
                    'description': description,
                    'task_type': self.task_type,
                    'property_ref': booking.property,
                    'assigned_to': self.default_assignee,
                    'due_date': due_date,
                },
            )
            
        return task if created else None


# Add at the end of models.py before Audit classes

class AuditEvent(models.Model):
    """
    Agent's Phase 2: Structured audit system for comprehensive activity tracking.
    Append-only model for tracking all create/update/delete operations.
    """
    ACTION_CHOICES = [
        ('create', 'Create'),
        ('update', 'Update'),
        ('delete', 'Delete'),
    ]
    
    # Core audit fields
    object_type = models.CharField(max_length=100, help_text="Model name of the object being audited")
    object_id = models.CharField(max_length=100, help_text="Primary key of the object being audited")
    action = models.CharField(max_length=10, choices=ACTION_CHOICES, help_text="Type of action performed")
    
    # Actor information
    actor = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        help_text="User who performed the action"
    )
    
    # Change tracking with JSONB diff
    changes = models.JSONField(
        default=dict,
        help_text="JSONB diff of changes made (before/after values)"
    )
    
    # Request context
    request_id = models.CharField(max_length=100, blank=True, help_text="Unique request identifier")
    ip_address = models.GenericIPAddressField(null=True, blank=True, help_text="IP address of the request")
    user_agent = models.TextField(blank=True, help_text="User agent string from the request")
    
    # Timestamp
    created_at = models.DateTimeField(auto_now_add=True, help_text="When the audit event was recorded")
    
    class Meta:
        verbose_name = "Audit Event"
        verbose_name_plural = "Audit Events"
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['object_type', 'object_id']),
            models.Index(fields=['action']),
            models.Index(fields=['actor']),
            models.Index(fields=['created_at']),
        ]
    
    def __str__(self):
        actor_name = self.actor.username if self.actor else "System"
        return f"{actor_name} {self.action}d {self.object_type}:{self.object_id}"


# =============================================================================
# PASSWORD RESET LOGGING
# =============================================================================

class PasswordResetLog(models.Model):
    """
    Model to track password reset events for audit purposes
    """
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='password_reset_logs')
    event_type = models.CharField(max_length=50, choices=[
        ('requested', 'Password Reset Requested'),
        ('completed', 'Password Reset Completed'),
        ('failed', 'Password Reset Failed'),
    ])
    timestamp = models.DateTimeField(auto_now_add=True)
    ip_address = models.GenericIPAddressField(null=True, blank=True)
    user_agent = models.TextField(null=True, blank=True)
    notes = models.TextField(null=True, blank=True)
    
    class Meta:
        ordering = ['-timestamp']
        verbose_name = 'Password Reset Log'
        verbose_name_plural = 'Password Reset Logs'
        indexes = [
            models.Index(fields=['user', 'timestamp']),
            models.Index(fields=['event_type', 'timestamp']),
        ]
    
    def __str__(self):
        return f"{self.user.username} - {self.get_event_type_display()} - {self.timestamp}"


# =============================================================================
# SECURITY MODELS (JWT & Session Management)
# =============================================================================

# Import security models
from .security_models import UserSession, SecurityEvent, SuspiciousActivity


# =============================================================================
# INVITE CODE SYSTEM
# =============================================================================

class InviteCode(models.Model):
    """Admin-generated invite codes for user registration"""
    code = models.CharField(max_length=32, unique=True, db_index=True)
    created_by = models.ForeignKey(User, on_delete=models.CASCADE, related_name='created_invite_codes')
    task_group = models.CharField(max_length=50, choices=TaskGroup.choices, default=TaskGroup.GENERAL)
    role = models.CharField(max_length=20, choices=UserRole.choices, default=UserRole.STAFF)
    
    # Usage tracking
    max_uses = models.PositiveIntegerField(default=1, help_text="Maximum number of times this code can be used (0 = unlimited)")
    used_count = models.PositiveIntegerField(default=0)
    used_by = models.ManyToManyField(User, blank=True, related_name='used_invite_codes')
    
    # Expiration
    expires_at = models.DateTimeField(null=True, blank=True, help_text="Leave blank for no expiration")
    is_active = models.BooleanField(default=True)
    
    # Metadata
    created_at = models.DateTimeField(auto_now_add=True)
    last_used_at = models.DateTimeField(null=True, blank=True)
    notes = models.TextField(blank=True, help_text="Optional notes about this invite code")
    
    class Meta:
        ordering = ['-created_at']
    
    def __str__(self):
        return f"{self.code} ({self.role}/{self.task_group})"
    
    @property
    def is_expired(self):
        if not self.expires_at:
            return False
        return timezone.now() > self.expires_at
    
    @property
    def is_usable(self):
        return (
            self.is_active and 
            not self.is_expired and 
            (self.max_uses == 0 or self.used_count < self.max_uses)
        )
    
    def can_be_used_by(self, user):
        """Check if a specific user can use this code"""
        if not self.is_usable:
            return False
        if self.max_uses > 0 and self.used_count >= self.max_uses:
            return False
        # Prevent any user from using the same code multiple times
        if user in self.used_by.all():
            return False
        return True
    
    def use_code(self, user):
        """Mark this code as used by a specific user (atomic operation)"""
        from django.db import transaction
        
        with transaction.atomic():
            # Refresh from database to get latest state
            self.refresh_from_db()
            
            # Check if code can be used (including user not already used it)
            if not self.can_be_used_by(user):
                raise ValueError("Code cannot be used")
            
            # Atomic update: increment count and add user
            self.used_count += 1
            self.last_used_at = timezone.now()
            self.save(update_fields=['used_count', 'last_used_at'])
            
            # Add user to many-to-many relationship
            self.used_by.add(user)


# =============================================================================
# SIGNAL RECEIVERS
# =============================================================================

# Agent's recommendation: Prevent self-dependency in Task.depends_on
@receiver(m2m_changed, sender=Task.depends_on.through)
def prevent_task_self_dependency(sender, instance, action, pk_set, **kwargs):
    """Prevent a task from depending on itself"""
    if action == 'pre_add' and instance.pk and instance.pk in pk_set:
        raise ValidationError("A task cannot depend on itself.")
    