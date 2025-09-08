"""
Task Creation Template System Models
"""
from django.db import models
from django.contrib.auth import get_user_model
from django.utils import timezone
from datetime import timedelta

User = get_user_model()


class AutoTaskTemplate(models.Model):
    """Template for automatically creating tasks during booking import"""
    
    TIMING_CHOICES = [
        ('before_checkin', 'Days Before Check-in'),
        ('after_checkout', 'Days After Check-out'),
        ('fixed_time', 'Fixed Time of Day'),
    ]
    
    TASK_TYPE_CHOICES = [
        ('cleaning', 'Cleaning'),
        ('maintenance', 'Maintenance'),
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
        """Create a task for a specific booking using this template"""
        from .models import Task  # Avoid circular import
        
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
        
        # Create task
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
            }
        )
        
        return task


# Add template tracking to existing models
class TaskTemplateTracking(models.Model):
    """Track which template created which task"""
    task = models.OneToOneField('Task', on_delete=models.CASCADE, related_name='template_info')
    template = models.ForeignKey(AutoTaskTemplate, on_delete=models.SET_NULL, null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        verbose_name = "Task Template Tracking"
        verbose_name_plural = "Task Template Tracking"
