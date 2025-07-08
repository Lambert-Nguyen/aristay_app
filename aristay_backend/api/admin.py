from django.contrib import admin
from .models import Property, Task

@admin.register(Property)
class PropertyAdmin(admin.ModelAdmin):
    list_display = ('name', 'created_by', 'created_at', 'modified_by', 'modified_at')

    def save_model(self, request, obj, form, change):
        if not change:
            obj.created_by = request.user
        else:
            obj.modified_by = request.user
        super().save_model(request, obj, form, change)

@admin.register(Task)
class TaskAdmin(admin.ModelAdmin):
    list_display = (
        'task_type', 'title', 'property', 'status',
        'created_by', 'created_at',
        'modified_by', 'modified_at',
    )

    def save_model(self, request, obj, form, change):
        if change:
            obj.modified_by = request.user
        super().save_model(request, obj, form, change)