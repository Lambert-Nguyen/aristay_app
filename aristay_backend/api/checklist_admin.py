"""
Enhanced admin interface for checklist management
"""
from django.contrib import admin
from django.utils.html import format_html
from django.urls import path, reverse
from django.shortcuts import render, redirect
from django.contrib import messages
from django.http import JsonResponse
from django.db import transaction
from api.models import ChecklistTemplate, ChecklistItem, TaskChecklist
import json


class ChecklistItemInline(admin.TabularInline):
    model = ChecklistItem
    extra = 0
    fields = ('order', 'title', 'item_type', 'is_required', 'room_type', 'description')
    ordering = ['order', 'room_type']


class ChecklistTemplateAdmin(admin.ModelAdmin):
    list_display = ('name', 'task_type', 'item_count', 'is_active', 'created_at', 'created_by')
    list_filter = ('task_type', 'is_active', 'created_at')
    search_fields = ('name', 'description')
    inlines = [ChecklistItemInline]
    readonly_fields = ('created_at', 'history')
    
    fieldsets = (
        (None, {
            'fields': ('name', 'task_type', 'description', 'is_active', 'created_by')
        }),
        ('History', {
            'fields': ('history', 'created_at'),
            'classes': ('collapse',)
        }),
    )
    
    def item_count(self, obj):
        """Display the number of items in this template"""
        count = obj.items.count()
        if count > 0:
            return format_html(
                '<span style="color: green; font-weight: bold;">{}</span>',
                count
            )
        return format_html(
            '<span style="color: red;">{}</span>',
            count
        )
    item_count.short_description = 'Items'
    
    def save_model(self, request, obj, form, change):
        if not change:
            obj.created_by = request.user
        super().save_model(request, obj, form, change)
    
    def get_urls(self):
        urls = super().get_urls()
        custom_urls = [
            path('duplicate/<int:template_id>/', 
                 self.admin_site.admin_view(self.duplicate_template), 
                 name='checklist_template_duplicate'),
            path('preview/<int:template_id>/', 
                 self.admin_site.admin_view(self.preview_template), 
                 name='checklist_template_preview'),
        ]
        return custom_urls + urls
    
    def duplicate_template(self, request, template_id):
        """Duplicate a checklist template"""
        try:
            original = ChecklistTemplate.objects.get(id=template_id)
            
            # Create new template
            new_template = ChecklistTemplate.objects.create(
                name=f"{original.name} (Copy)",
                task_type=original.task_type,
                description=original.description,
                is_active=True,
                created_by=request.user
            )
            
            # Copy all items
            for item in original.items.all():
                ChecklistItem.objects.create(
                    template=new_template,
                    title=item.title,
                    description=item.description,
                    item_type=item.item_type,
                    is_required=item.is_required,
                    order=item.order,
                    room_type=item.room_type
                )
            
            messages.success(request, f'Successfully duplicated template "{original.name}"')
            return redirect(f'../{new_template.id}/change/')
            
        except ChecklistTemplate.DoesNotExist:
            messages.error(request, 'Template not found')
            return redirect('..')
        except Exception as e:
            messages.error(request, f'Error duplicating template: {str(e)}')
            return redirect('..')
    
    def preview_template(self, request, template_id):
        """Preview a checklist template"""
        try:
            template = ChecklistTemplate.objects.get(id=template_id)
            
            # Group items by room type
            items_by_room = {}
            for item in template.items.all():
                room = item.room_type or 'General'
                if room not in items_by_room:
                    items_by_room[room] = []
                items_by_room[room].append(item)
            
            context = {
                'template': template,
                'items_by_room': items_by_room,
                'title': f'Preview: {template.name}',
            }
            
            return render(request, 'admin/checklist_template_preview.html', context)
            
        except ChecklistTemplate.DoesNotExist:
            messages.error(request, 'Template not found')
            return redirect('..')
    
    # Use the generic unified history view
    history_view = create_unified_history_view(ChecklistTemplate)


class TaskChecklistAdmin(admin.ModelAdmin):
    list_display = ('task', 'template', 'completion_percentage', 'is_completed', 'started_at', 'completed_at')
    list_filter = ('is_completed', 'template__task_type', 'started_at', 'completed_at')
    search_fields = ('task__title', 'template__name')
    readonly_fields = ('completion_percentage', 'total_items', 'completed_items', 'remaining_items')
    
    fieldsets = (
        (None, {
            'fields': ('task', 'template', 'started_at', 'completed_at', 'completed_by')
        }),
        ('Progress', {
            'fields': ('completion_percentage', 'total_items', 'completed_items', 'remaining_items'),
            'classes': ('collapse',)
        }),
    )
    
    def completion_percentage(self, obj):
        """Display completion percentage with color coding"""
        percentage = obj.completion_percentage
        if percentage == 100:
            color = 'green'
        elif percentage >= 75:
            color = 'orange'
        else:
            color = 'red'
        
        return format_html(
            '<span style="color: {}; font-weight: bold;">{}%</span>',
            color, percentage
        )
    completion_percentage.short_description = 'Progress'
    
    # Use the generic unified history view
    history_view = create_unified_history_view(TaskChecklist)


# Import the create_unified_history_view function
from api.admin import create_unified_history_view
