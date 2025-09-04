# 🚀 Task Creation Template System - Proposal

## Problem
Currently, automatic task creation during Excel import is hardcoded to create only "Pre-arrival Cleaning" tasks with fixed timing. Users cannot control:
- Which types of tasks to create automatically
- Task timing and scheduling
- Task templates and descriptions
- Multiple tasks per booking

## Proposed Solution: Task Creation Templates

### 1. New Model: `AutoTaskTemplate`
```python
class AutoTaskTemplate(models.Model):
    """Template for automatically creating tasks during booking import"""
    
    name = models.CharField(max_length=100)  # "Pre-arrival Cleaning Template"
    is_active = models.BooleanField(default=True)
    
    # Task Configuration
    task_type = models.CharField(max_length=20, choices=TASK_TYPE_CHOICES)
    title_template = models.CharField(max_length=200)  # "Pre-arrival Cleaning - {property}"
    description_template = models.TextField(blank=True)  # "Prepare for {guest_name} on {check_in_date}"
    
    # Timing Configuration
    timing_type = models.CharField(max_length=20, choices=[
        ('before_checkin', 'Days Before Check-in'),
        ('after_checkout', 'Days After Check-out'),
        ('fixed_time', 'Fixed Time of Day'),
    ])
    timing_offset = models.IntegerField(default=1)  # Days before/after
    timing_hour = models.TimeField(null=True, blank=True)  # For fixed time
    
    # Conditions
    property_types = models.ManyToManyField('Property', blank=True)  # Specific properties only
    booking_sources = models.CharField(max_length=200, blank=True)  # "Airbnb,VRBO" or empty for all
    
    # Assignment
    default_assignee = models.ForeignKey(User, null=True, blank=True, on_delete=models.SET_NULL)
    
    created_by = models.ForeignKey(User, on_delete=models.CASCADE)
    created_at = models.DateTimeField(auto_now_add=True)
```

### 2. Enhanced BookingImportTemplate
```python
class BookingImportTemplate(models.Model):
    # ... existing fields ...
    
    # Replace single auto_create_tasks with flexible templates
    auto_task_templates = models.ManyToManyField(
        'AutoTaskTemplate', 
        blank=True,
        help_text="Task templates to apply automatically during import"
    )
```

### 3. Admin Interface
- **Task Template Manager**: Create, edit, and test task templates
- **Import Template Settings**: Select which task templates to apply
- **Template Preview**: Show what tasks would be created before import

### 4. Usage Examples

**Example 1: Multiple Tasks for Short-term Rentals**
- Pre-arrival Cleaning (1 day before check-in)
- Welcome Package Preparation (2 hours before check-in)
- Post-checkout Inspection (2 hours after checkout)
- Deep Cleaning (1 day after checkout for 3+ night stays)

**Example 2: Property-Specific Tasks**
- Pool Properties: Pool cleaning tasks
- Pet-Friendly Properties: Pet cleanup tasks
- Luxury Properties: Concierge setup tasks

### 5. Benefits
✅ **Full User Control**: Admins configure what tasks are created
✅ **Flexible Timing**: Multiple timing options and conditions
✅ **Property-Specific**: Different task sets for different properties
✅ **Source Attribution**: All tasks track who/what created them
✅ **Template Reuse**: Save and reuse configurations
✅ **Gradual Rollout**: Can be implemented alongside existing hardcoded system

### 6. Implementation Priority
1. **Phase 1**: Create AutoTaskTemplate model and admin interface
2. **Phase 2**: Update excel_import_service to use templates
3. **Phase 3**: Migrate existing hardcoded logic to default template
4. **Phase 4**: Add advanced features (conditions, multiple assignments, etc.)
