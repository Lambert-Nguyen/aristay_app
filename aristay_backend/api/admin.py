from django.contrib import admin
from django.utils import timezone
from django.utils.html import format_html
import json


from django.contrib.auth.models import User
from django.contrib.auth.admin import UserAdmin as DefaultUserAdmin

from .models import Task, Property, TaskImage, Profile, Notification, Device

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
        'created_by', 'assigned_to',        # add assignee column
        'created_at_local', 'modified_at_local',
        'due_date',
    )
    readonly_fields = (
        'created_at', 'modified_at',
        'created_at_local', 'modified_at_local',
    )
    # ─────────────────────────────────────────────────────────────
    # Make the Many-to-Many user-friendly
    # ─────────────────────────────────────────────────────────────
    filter_horizontal = ('muted_by',)
    
    inlines = [TaskImageInline]

    class Media:
        js = ('admin/js/timezone_local.js',)

    def created_at_local(self, obj):
        local_dt = obj.created_at.astimezone(timezone.get_current_timezone())
        return local_dt.strftime('%Y-%m-%d %H:%M:%S %Z')
    created_at_local.short_description = 'Created (Local)'
    created_at_local.admin_order_field = 'created_at'  # ← this makes it sortable

    def modified_at_local(self, obj):
        local_dt = obj.modified_at.astimezone(timezone.get_current_timezone())
        return local_dt.strftime('%Y-%m-%d %H:%M:%S %Z')
    modified_at_local.short_description = 'Modified (Local)'
    modified_at_local.admin_order_field = 'modified_at'  # ← sortable

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
        
# —————— new: inline your users’ Profile in the User admin ——————

class ProfileInline(admin.StackedInline):
    model = Profile
    fk_name = 'user'
    fields = ('timezone', 'digest_opt_out')
    extra = 1        # always show one blank form if none exists
    max_num = 1      # never allow more than one
    can_delete = False
    verbose_name_plural = 'Profile'

class UserAdmin(DefaultUserAdmin):
    inlines = (ProfileInline,)

    def get_inline_instances(self, request, obj=None):
        # only for *editing* an existing user
        if obj is not None:
            # create their Profile if it doesn’t already exist
            Profile.objects.get_or_create(user=obj)
            return super().get_inline_instances(request, obj)
        return []

    # (optional) show timezone in the user list view:
    list_display = DefaultUserAdmin.list_display + ('get_timezone',)
    def get_timezone(self, obj):
        return obj.profile.timezone
    get_timezone.short_description = 'Timezone'

# swap out Django’s built-in UserAdmin for ours
admin.site.unregister(User)
admin.site.register(User, UserAdmin)

@admin.register(Notification)
class NotificationAdmin(admin.ModelAdmin):
    list_display = ('task', 'recipient', 'verb', 'read', 'read_at', 'timestamp')
    list_filter = ('read', 'verb', 'timestamp')
    search_fields = ('task__title', 'recipient__username', 'verb')
    readonly_fields = ('read_at', 'timestamp', 'push_sent')

    actions = ['resend_push']

    def resend_push(self, request, queryset):
        unsent = queryset.filter(push_sent=False)
        sent   = 0
        for n in unsent:
            if NotificationService.push_to_device(n.recipient, n.task, n.verb, n.id):
                n.mark_pushed(commit=True)
                sent += 1
        self.message_user(request, f"Successfully resent {sent} notification(s).")
    resend_push.short_description = "Resend push for selected (unsent) notifications"
    
@admin.register(Profile)
class ProfileAdmin(admin.ModelAdmin):
    list_display = ("user", "timezone", "digest_opt_out")
    list_editable = ("digest_opt_out",)

@admin.register(Device)
class DeviceAdmin(admin.ModelAdmin):
    list_display = ('user', 'token', 'created_at', 'updated_at')
    search_fields = ('user__username', 'token')
    readonly_fields = ('created_at', 'updated_at')