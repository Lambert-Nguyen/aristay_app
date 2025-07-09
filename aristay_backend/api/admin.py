from django.contrib import admin
from .models import Task
import json
from django.utils import timezone

@admin.register(Task)
class TaskAdmin(admin.ModelAdmin):
    list_display = ('title','task_type','property','status','created_by','modified_by','created_at','modified_at')
    readonly_fields = ('created_at','modified_at')

    def save_model(self, request, obj, form, change):
        user = request.user
        if not change:
            # on create
            obj.created_by  = user
            obj.modified_by = user
            obj.history     = json.dumps([f"{timezone.now().isoformat()}: {user.username} created task"])
        else:
            # on edit
            # compare form.changed_data for fields that actually changed
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