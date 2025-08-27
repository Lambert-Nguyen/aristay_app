from django.contrib import admin
from django.urls import path
from django.shortcuts import render
from django.http import HttpResponseRedirect
from django.urls import reverse
from .models import Property, Task, TaskImage

class CustomAdminSite(admin.AdminSite):
    site_header = "AriStay Administration"
    site_title = "AriStay Admin"
    index_title = "Welcome to AriStay Administration"
    
    def get_urls(self):
        urls = super().get_urls()
        custom_urls = [
            path('analytics/', self.admin_view(self.analytics_view), name='admin_analytics'),
        ]
        return custom_urls + urls
    
    def analytics_view(self, request):
        # Redirect to our charts dashboard
        return HttpResponseRedirect('/api/admin/charts/')

# Use the custom admin site
admin_site = CustomAdminSite(name='admin')

class TaskImageInline(admin.TabularInline):
    model = TaskImage
    extra = 0
    readonly_fields = ('uploaded_at', 'preview')
    fields = ('image', 'preview', 'uploaded_at')

    def preview(self, obj):
        if obj.image:
            return f'<img src="{obj.image.url}" width="100" height="100" style="object-fit: cover;" />'
        return "No image"
    preview.allow_tags = True
    preview.short_description = 'Image Preview'

class TaskAdmin(admin.ModelAdmin):
    list_display = ('id', 'title', 'task_type', 'status', 'property', 'assigned_to', 'created_at', 'due_date')
    list_filter = ('status', 'task_type', 'created_at', 'property', 'assigned_to')
    search_fields = ('title', 'description')
    readonly_fields = ('created_at', 'modified_at', 'history')
    
    fieldsets = (
        (None, {
            'fields': ('title', 'description', 'task_type', 'property', 'status', 'assigned_to', 'due_date')
        }),
        ('Tracking', {
            'fields': ('created_by', 'created_at', 'modified_by', 'modified_at'),
            'classes': ('collapse',)
        }),
        ('History', {
            'fields': ('history',),
            'classes': ('collapse',)
        }),
    )
    
    inlines = [TaskImageInline]

    def save_model(self, request, obj, form, change):
        if not change:  # If creating a new object
            obj.created_by = request.user
        obj.modified_by = request.user
        super().save_model(request, obj, form, change)

class PropertyAdmin(admin.ModelAdmin):
    list_display = ('id', 'name', 'address', 'created_at', 'created_by')
    search_fields = ('name', 'address')
    readonly_fields = ('created_at', 'modified_at')
    
    def save_model(self, request, obj, form, change):
        if not change:  # If creating a new object
            obj.created_by = request.user
        obj.modified_by = request.user
        super().save_model(request, obj, form, change)

# Register models with the custom admin site
admin_site.register(Task, TaskAdmin)
admin_site.register(Property, PropertyAdmin)

# Also register with default admin for backward compatibility
admin.site.register(Task, TaskAdmin)
admin.site.register(Property, PropertyAdmin)