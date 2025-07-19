from django.contrib import admin
from django.utils import timezone
from django.utils.html import format_html
import json

from .models import Task, Property, TaskImage

class TaskImageInline(admin.TabularInline):
    model = TaskImage
    extra = 1
    readonly_fields = ('preview',)

    def preview(self, obj):
        if obj.image:
            return format_html(
                "<img src='{}' style='max-height:100px; margin:5px;'/>",
                obj.image.url
            )
        return ""
    preview.short_description = 'Image Preview'

@admin.register(Task)
class TaskAdmin(admin.ModelAdmin):
    list_display = (
        'title', 'task_type', 'property', 'status',
        'created_by', 'created_at_local',
        'modified_by', 'modified_at_local',
        'due_date',
    )
    readonly_fields = (
        'created_at', 'modified_at',
        'created_at_local', 'modified_at_local',
    )
    inlines = [TaskImageInline]

    class Media:
        js = ('admin/js/timezone_local.js',)

    def created_at_local(self, obj):
        local_dt = obj.created_at.astimezone(timezone.get_current_timezone())
        return local_dt.strftime('%Y-%m-%d %H:%M:%S %Z')
    created_at_local.short_description = 'Created (Local)'

    def modified_at_local(self, obj):
        local_dt = obj.modified_at.astimezone(timezone.get_current_timezone())
        return local_dt.strftime('%Y-%m-%d %H:%M:%S %Z')
    modified_at_local.short_description = 'Modified (Local)'

    def save_model(self, request, obj, form, change):
        user = request.user

        if not change:
            obj.created_by = user
            obj.modified_by = user
            obj.history = json.dumps([
                f"{timezone.now().isoformat()}: {user.username} created task"
            ])
        else:
            changes = []
            for field in form.changed_data:
                old = form.initial.get(field)
                new = form.cleaned_data.get(field)
                changes.append(f"changed {field} from '{old}' to '{new}'")
            if changes:
                try:
                    existing = json.loads(obj.history or '[]')
                except json.JSONDecodeError:
                    existing = []
                timestamp = timezone.now().isoformat()
                for c in changes:
                    existing.append(f"{timestamp}: {user.username} {c}")
                obj.history = json.dumps(existing)
                obj.modified_by = user

        super().save_model(request, obj, form, change)


@admin.register(Property)
class PropertyAdmin(admin.ModelAdmin):
    list_display = (
        'name',
        'created_by', 'created_at_local',
        'modified_by', 'modified_at_local',
    )
    readonly_fields = (
        'created_at', 'modified_at',
        'created_at_local', 'modified_at_local',
    )

    class Media:
        js = ('admin/js/timezone_local.js',)

    def created_at_local(self, obj):
        local = obj.created_at.astimezone(timezone.get_current_timezone())
        return local.strftime('%Y-%m-%d %H:%M:%S %Z')
    created_at_local.short_description = 'Created (Local)'

    def modified_at_local(self, obj):
        local = obj.modified_at.astimezone(timezone.get_current_timezone())
        return local.strftime('%Y-%m-%d %H:%M:%S %Z')
    modified_at_local.short_description = 'Modified (Local)'

    def save_model(self, request, obj, form, change):
        user = request.user
        if not change:
            obj.created_by = user
        obj.modified_by = user
        super().save_model(request, obj, form, change)