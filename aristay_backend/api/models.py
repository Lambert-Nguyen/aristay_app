# api/models.py

import json
# Removed available_timezones import - using curated timezone choices instead
from django.conf import settings
from django.db import models
from django.db.models.signals import post_save
from django.utils import timezone
from django.dispatch import receiver
from django.contrib.auth.models import User

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


# ----------------------------------------------------------------------------
# Booking & Ownership domain (Property-centric design)
# ----------------------------------------------------------------------------

class Booking(models.Model):
    """A booking window for a property. Tasks will typically be linked to a booking."""
    STATUS_CHOICES = [
        ('upcoming', 'Upcoming'),
        ('active', 'Active'),
        ('completed', 'Completed'),
        ('cancelled', 'Cancelled'),
    ]

    property = models.ForeignKey('Property', on_delete=models.CASCADE, related_name='bookings')
    check_in_date = models.DateTimeField()
    check_out_date = models.DateTimeField()
    guest_name = models.CharField(max_length=200, blank=True)
    guest_contact = models.CharField(max_length=200, blank=True)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='upcoming')
    created_at = models.DateTimeField(auto_now_add=True)
    modified_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-check_in_date']

    def __str__(self):
        return f"Booking {self.property.name} {self.check_in_date:%Y-%m-%d} → {self.check_out_date:%Y-%m-%d}"


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
]

class Task(models.Model):
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
    property     = models.ForeignKey('Property', on_delete=models.CASCADE, related_name='tasks', null=True, blank=True)
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
    
    # users that do **not** want pushes for *this* task
    muted_by     = models.ManyToManyField(
        settings.AUTH_USER_MODEL,
        related_name='muted_tasks',
        blank=True,
        help_text="Users that muted notifications for this task"
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


class TaskImage(models.Model):
    task = models.ForeignKey(Task, on_delete=models.CASCADE, related_name='images')
    image = models.ImageField(upload_to='task_images/%Y/%m/%d/')
    uploaded_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Image for {self.task.title}"
    
class UserRole(models.TextChoices):
    """
    User role hierarchy - defines access level and permissions
    """
    STAFF       = 'staff',       'Staff/Crew'    # Normal users who perform tasks
    MANAGER     = 'manager',     'Manager'       # Manages staff and properties
    SUPERUSER   = 'superuser',   'Superuser'     # Full system admin access
    VIEWER      = 'viewer',      'Viewer'        # Read-only access


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

    # NEW
    role = models.CharField(
        max_length=16,
        choices=UserRole.choices,
        default=UserRole.STAFF,
        help_text="App role separate from Django is_staff/is_superuser."
    )

    def __str__(self):
        return f"{self.user.username} profile"
    
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

@receiver(post_save, sender=settings.AUTH_USER_MODEL)
def create_user_profile(sender, instance, created, **kwargs):
    if created:
        # Set default role based on Django user flags
        if instance.is_superuser:
            default_role = UserRole.SUPERUSER
        elif instance.is_staff:
            default_role = UserRole.MANAGER
        else:
            default_role = UserRole.STAFF
            
        Profile.objects.create(user=instance, role=default_role)

@receiver(post_save, sender=User)
def sync_profile_role_on_user_save(sender, instance, **kwargs):
    profile, _ = Profile.objects.get_or_create(user=instance)
    
    # Auto-sync profile role with Django user flags (only if it makes sense)
    if instance.is_superuser and profile.role != UserRole.SUPERUSER:
        profile.role = UserRole.SUPERUSER
        profile.save()
    elif instance.is_staff and not instance.is_superuser and profile.role == UserRole.STAFF:
        # Only auto-promote staff to manager if they're currently just staff
        profile.role = UserRole.MANAGER
        profile.save()

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
    
    class Meta:
        ordering = ['task_type', 'name']
    
    def __str__(self):
        return f"{self.get_task_type_display()} - {self.name}"


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
    
    class Meta:
        ordering = ['category', 'name']
    
    def __str__(self):
        return f"{self.name} ({self.get_unit_display()})"


class PropertyInventory(models.Model):
    """Tracks inventory levels for specific items at specific properties."""
    property_ref = models.ForeignKey('Property', on_delete=models.CASCADE, related_name='inventory')
    item = models.ForeignKey('InventoryItem', on_delete=models.CASCADE)
    
    # Stock levels
    current_stock = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    par_level = models.DecimalField(max_digits=10, decimal_places=2, help_text="Minimum stock level before reorder")
    max_level = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True, help_text="Maximum stock capacity")
    
    # Location within property
    storage_location = models.CharField(max_length=200, blank=True, help_text="Where this item is stored")
    
    last_updated = models.DateTimeField(auto_now=True)
    updated_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, blank=True)
    
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
    
    class Meta:
        ordering = ['-created_at']
    
    def __str__(self):
        sign = "+" if self.quantity > 0 else ""
        return f"{self.get_transaction_type_display()}: {sign}{self.quantity} {self.property_inventory.item.get_unit_display()}"


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
    
    class Meta:
        ordering = ['-found_date']
    
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
    time_of_day = models.TimeField(default='09:00:00', help_text="Default time for generated tasks")
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
    
    class Meta:
        unique_together = ['schedule', 'generated_for_date']
        ordering = ['-generated_for_date']
    
    def __str__(self):
        return f"Generated: {self.task.title} ({self.generated_for_date})"


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
    template = models.ForeignKey(BookingImportTemplate, on_delete=models.CASCADE, related_name='import_logs')
    import_file = models.FileField(upload_to='booking_imports/%Y/%m/', null=True, blank=True)
    
    # Results
    total_rows = models.IntegerField(default=0)
    successful_imports = models.IntegerField(default=0)
    errors_count = models.IntegerField(default=0)
    errors_log = models.TextField(blank=True)
    
    # Metadata
    imported_at = models.DateTimeField(auto_now_add=True)
    imported_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    
    class Meta:
        ordering = ['-imported_at']
    
    def __str__(self):
        return f"Import {self.imported_at.strftime('%Y-%m-%d %H:%M')} - {self.successful_imports}/{self.total_rows} success"
    