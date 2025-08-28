from django.contrib import admin
from django.contrib.auth.models import User
from django.urls import path
from django.shortcuts import render
from .models import (
    Property, Task, Notification, Booking, PropertyOwnership, Profile,
    ChecklistTemplate, ChecklistItem, TaskChecklist, ChecklistResponse, ChecklistPhoto,
    InventoryCategory, InventoryItem, PropertyInventory, InventoryTransaction,
    LostFoundItem, LostFoundPhoto, ScheduleTemplate, GeneratedTask,
    BookingImportTemplate, BookingImportLog
)

class ManagerAdminSite(admin.AdminSite):
    site_header = "AriStay Manager"
    site_title  = "AriStay Manager"
    index_title = "Management Console"
    index_template = 'manager_admin/index.html'
    logout_template = None  # Use unified logout
    
    def logout(self, request, extra_context=None):
        """Override logout to redirect to unified logout"""
        from django.shortcuts import redirect
        return redirect('unified_logout')

    def has_permission(self, request):
        if not (request.user and request.user.is_authenticated and request.user.is_active):
            return False
        if request.user.is_superuser:
            return True
        role = getattr(getattr(request.user, 'profile', None), 'role', 'staff')
        return role == 'manager'
    
    def get_urls(self):
        """Add custom URLs to the manager admin site"""
        urls = super().get_urls()
        custom_urls = [
            path('charts/', self.admin_view(self.charts_view), name='manager_charts'),
        ]
        return custom_urls + urls
    
    def charts_view(self, request):
        """Custom charts dashboard view"""
        from .views import manager_charts_dashboard
        return manager_charts_dashboard(request)

manager_site = ManagerAdminSite(name='manager_admin')

# --- NEW: centralize “is manager” permission logic for ModelAdmins ---
class ManagerPermissionMixin:
    def _is_manager(self, request):
        if not (request.user and request.user.is_authenticated and request.user.is_active):
            return False
        if request.user.is_superuser:
            return True
        role = getattr(getattr(request.user, 'profile', None), 'role', 'staff')
        return role == 'manager'

    # Show app on index
    def has_module_permission(self, request):
        return self._is_manager(request)

    # CRUD perms for the model
    def has_view_permission(self, request, obj=None):
        return self._is_manager(request)

    def has_add_permission(self, request):
        return self._is_manager(request)

    def has_change_permission(self, request, obj=None):
        return self._is_manager(request)

    def has_delete_permission(self, request, obj=None):
        # optional: managers can’t delete; return self._is_manager(request) to allow
        return request.user.is_superuser  # tighten if you like
# ---------------------------------------------------------------------

class PropertyAdmin(ManagerPermissionMixin, admin.ModelAdmin):
    list_display = ('id', 'name', 'created_at', 'modified_at')
    search_fields = ('name',)

class TaskAdmin(ManagerPermissionMixin, admin.ModelAdmin):
    list_display = ('id', 'title', 'task_type', 'status', 'property', 'booking', 'created_at')
    search_fields = ('title', 'description')
    list_filter = ('status', 'task_type', 'created_at', 'property', 'booking')

class UserManagerAdmin(ManagerPermissionMixin, admin.ModelAdmin):
    list_display  = ('username', 'email', 'get_profile_role', 'timezone_display', 'is_active', 'is_staff', 'is_superuser', 'date_joined')
    list_filter   = ('is_active', 'is_staff', 'is_superuser')
    search_fields = ('username', 'email', 'first_name', 'last_name')
    readonly_fields = ('last_login', 'date_joined',)
    exclude = ('password',)  # never show password hash

    # Import ProfileInline from admin.py
    from .admin import ProfileInline
    inlines = [ProfileInline]

    actions = ['activate_users', 'deactivate_users']

    def get_queryset(self, request):
        qs = super().get_queryset(request)
        # Managers shouldn’t see owner accounts
        if not request.user.is_superuser:
            qs = qs.exclude(is_superuser=True)
        return qs

    def get_readonly_fields(self, request, obj=None):
        ro = list(super().get_readonly_fields(request, obj))
        if not request.user.is_superuser:
            # prevent privilege escalation via admin
            ro += ['is_staff', 'is_superuser', 'user_permissions', 'groups']
        return ro

    actions = ['send_password_reset']

    def send_password_reset(self, request, queryset):
        # Trigger Django's password reset flow for selected users
        from django.contrib.auth.forms import PasswordResetForm
        sent = 0
        for user in queryset:
            if not user.email:
                continue
            form = PasswordResetForm(data={'email': user.email})
            if form.is_valid():
                form.save(
                    email_template_name="registration/password_reset_email.html",
                    request=request,
                )
                sent += 1
        self.message_user(request, f"Password reset email sent to {sent} user(s).")
    send_password_reset.short_description = "Send password reset email"

    def save_model(self, request, obj, form, change):
        # extra guardrails for managers
        if not request.user.is_superuser:
            obj.is_superuser = False
            # optional: don’t let managers grant Django-staff
            # obj.is_staff = obj.is_staff and obj.pk == request.user.pk
        super().save_model(request, obj, form, change)

    def activate_users(self, request, queryset):
        updated = queryset.exclude(is_superuser=True).update(is_active=True)
        self.message_user(request, f"Activated {updated} user(s).")

    def deactivate_users(self, request, queryset):
        updated = queryset.exclude(is_superuser=True).update(is_active=False)
        self.message_user(request, f"Deactivated {updated} user(s).")

    def timezone_display(self, obj):
        try:
            tz = obj.profile.timezone
        except Exception:
            tz = 'America/New_York'
        return tz
    timezone_display.short_description = 'Timezone'
    
    def get_profile_role(self, obj):
        try:
            return obj.profile.get_role_display()
        except Exception:
            return 'Staff'
    get_profile_role.short_description = 'Role'

class NotificationManagerAdmin(ManagerPermissionMixin, admin.ModelAdmin):
    list_display = ('id', 'recipient', 'task_title', 'verb', 'read', 'timestamp', 'read_at')
    list_filter = ('read', 'verb', 'timestamp')
    search_fields = ('recipient__username', 'task__title')
    readonly_fields = ('timestamp', 'push_sent')
    list_per_page = 50
    
    fieldsets = (
        (None, {
            'fields': ('recipient', 'task', 'verb', 'read', 'read_at')
        }),
        ('System Info', {
            'fields': ('timestamp', 'push_sent'),
            'classes': ('collapse',)
        }),
    )
    
    def task_title(self, obj):
        return obj.task.title if obj.task else 'N/A'
    task_title.short_description = 'Task Title'
    
    def get_queryset(self, request):
        return super().get_queryset(request).select_related('recipient', 'task')

# ============================================================================
# MVP Phase 1: Manager Admin for new models (reuse admin classes from admin.py)
# ============================================================================

# Import admin classes from admin.py to maintain consistency
from .admin import (
    ChecklistTemplateAdmin, ChecklistResponseAdmin, TaskChecklistAdmin,
    InventoryCategoryAdmin, InventoryItemAdmin, PropertyInventoryAdmin, InventoryTransactionAdmin,
    LostFoundItemAdmin, ScheduleTemplateAdmin, GeneratedTaskAdmin,
    BookingImportTemplateAdmin, BookingImportLogAdmin
)

# Create manager-permission wrapped versions
class ChecklistTemplateManagerAdmin(ManagerPermissionMixin, ChecklistTemplateAdmin):
    pass

class ChecklistResponseManagerAdmin(ManagerPermissionMixin, ChecklistResponseAdmin):
    pass

class TaskChecklistManagerAdmin(ManagerPermissionMixin, TaskChecklistAdmin):
    pass

class InventoryCategoryManagerAdmin(ManagerPermissionMixin, InventoryCategoryAdmin):
    pass

class InventoryItemManagerAdmin(ManagerPermissionMixin, InventoryItemAdmin):
    pass

class PropertyInventoryManagerAdmin(ManagerPermissionMixin, PropertyInventoryAdmin):
    pass

class InventoryTransactionManagerAdmin(ManagerPermissionMixin, InventoryTransactionAdmin):
    pass

class LostFoundItemManagerAdmin(ManagerPermissionMixin, LostFoundItemAdmin):
    pass

class ScheduleTemplateManagerAdmin(ManagerPermissionMixin, ScheduleTemplateAdmin):
    pass

class GeneratedTaskManagerAdmin(ManagerPermissionMixin, GeneratedTaskAdmin):
    pass

class BookingImportTemplateManagerAdmin(ManagerPermissionMixin, BookingImportTemplateAdmin):
    pass

class BookingImportLogManagerAdmin(ManagerPermissionMixin, BookingImportLogAdmin):
    pass

# register on the manager site
manager_site.register(Property, PropertyAdmin)
manager_site.register(Task, TaskAdmin)
manager_site.register(User, UserManagerAdmin)
manager_site.register(Notification, NotificationManagerAdmin)
manager_site.register(Booking)
manager_site.register(PropertyOwnership)

# Register MVP Phase 1 models
manager_site.register(ChecklistTemplate, ChecklistTemplateManagerAdmin)
manager_site.register(ChecklistResponse, ChecklistResponseManagerAdmin)
manager_site.register(TaskChecklist, TaskChecklistManagerAdmin)
manager_site.register(InventoryCategory, InventoryCategoryManagerAdmin)
manager_site.register(InventoryItem, InventoryItemManagerAdmin)
manager_site.register(PropertyInventory, PropertyInventoryManagerAdmin)
manager_site.register(InventoryTransaction, InventoryTransactionManagerAdmin)
manager_site.register(LostFoundItem, LostFoundItemManagerAdmin)
manager_site.register(ScheduleTemplate, ScheduleTemplateManagerAdmin)
manager_site.register(GeneratedTask, GeneratedTaskManagerAdmin)
manager_site.register(BookingImportTemplate, BookingImportTemplateManagerAdmin)
manager_site.register(BookingImportLog, BookingImportLogManagerAdmin)