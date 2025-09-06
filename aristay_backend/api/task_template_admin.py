"""
Admin interface for Task Templates system
"""
from django.contrib import admin
from .models import AutoTaskTemplate

@admin.register(AutoTaskTemplate)
class AutoTaskTemplateAdmin(admin.ModelAdmin):
    list_display = [
        'name', 
        'task_type', 
        'is_active', 
        'timing_type', 
        'timing_offset',
        'created_by',
        'get_property_count'
    ]
    list_filter = [
        'is_active', 
        'task_type', 
        'timing_type',
        'created_at'
    ]
    search_fields = ['name', 'title_template', 'description_template']
    
    fieldsets = [
        ('Basic Information', {
            'fields': ['name', 'is_active', 'task_type']
        }),
        ('Task Content', {
            'fields': ['title_template', 'description_template'],
            'description': 'Use placeholders like {property}, {guest_name}, {check_in_date}, {check_out_date}, {source}, {external_code}'
        }),
        ('Timing Configuration', {
            'fields': ['timing_type', 'timing_offset', 'timing_hour'],
            'description': 'Configure when tasks should be created relative to booking dates'
        }),
        ('Conditions', {
            'fields': ['property_types', 'booking_sources'],
            'description': 'Optional filters to apply template only to specific properties or booking sources'
        }),
        ('Assignment', {
            'fields': ['default_assignee']
        }),
    ]
    
    filter_horizontal = ['property_types']
    
    readonly_fields = ['created_by', 'created_at']
    
    def get_property_count(self, obj):
        """Show how many properties this template applies to"""
        if obj.property_types.exists():
            return f"{obj.property_types.count()} specific properties"
        return "All properties"
    get_property_count.short_description = "Applies To"
    
    def save_model(self, request, obj, form, change):
        """Set created_by field on new templates"""
        if not change:  # Creating new template
            obj.created_by = request.user
        super().save_model(request, obj, form, change)
    
    class Media:
        css = {
            'all': ('admin/css/task_template_admin.css',)
        }
        js = ('admin/js/task_template_admin.js',)
