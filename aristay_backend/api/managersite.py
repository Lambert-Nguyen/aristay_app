from django.contrib import admin
from django.contrib.auth.models import User
from django.contrib.auth.admin import UserAdmin as DjangoUserAdmin
from django.urls import path
from django.shortcuts import render, redirect
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
    login_template = 'manager_admin/login.html'
    logout_template = None  # Use unified logout
    
    def logout(self, request, extra_context=None):
        """Override logout to redirect to unified logout"""
        from django.shortcuts import redirect
        from django.http import HttpResponseRedirect
        return HttpResponseRedirect('/api/logout/')

    def has_permission(self, request):
        if not (request.user and request.user.is_authenticated and request.user.is_active):
            return False
        if request.user.is_superuser:
            return True
        
        # For dynamic permissions: ALL users (including managers) need explicit portal access
        # This allows fine-grained control over who can access the manager portal
        if hasattr(request.user, 'profile') and request.user.profile:
            return request.user.profile.has_permission('manager_portal_access')
        
        return False
    
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
    
    def _has_permission(self, request, permission_name):
        """Check if user has a specific permission using the dynamic permission system"""
        if not (request.user and request.user.is_authenticated and request.user.is_active):
            return False
        if request.user.is_superuser:
            return True
        
        # Use the dynamic permission system
        if hasattr(request.user, 'profile') and request.user.profile:
            return request.user.profile.has_permission(permission_name)
        
        return False

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
    list_display = ('id', 'title', 'task_type', 'status', 'property_ref', 'booking', 'created_at')
    search_fields = ('title', 'description')
    list_filter = ('status', 'task_type', 'created_at', 'property_ref', 'booking')
    
    # Override to use dynamic permissions for tasks
    def has_view_permission(self, request, obj=None):
        return self._has_permission(request, 'view_tasks')
    
    def has_add_permission(self, request):
        return self._has_permission(request, 'add_tasks')
    
    def has_change_permission(self, request, obj=None):
        return self._has_permission(request, 'change_tasks')
    
    def has_delete_permission(self, request, obj=None):
        return self._has_permission(request, 'delete_tasks')

# Create a specialized BookingAdmin for dynamic permissions
class BookingAdmin(ManagerPermissionMixin, admin.ModelAdmin):
    list_display = ('id', 'guest_name', 'property', 'check_in_date', 'check_out_date', 'status')
    search_fields = ('guest_name', 'guest_contact', 'property__name')
    list_filter = ('status', 'check_in_date', 'property')
    
    # Override to use dynamic permissions for bookings
    def has_view_permission(self, request, obj=None):
        return self._has_permission(request, 'view_bookings')
    
    def has_add_permission(self, request):
        return self._has_permission(request, 'add_bookings')
    
    def has_change_permission(self, request, obj=None):
        return self._has_permission(request, 'change_bookings')
    
    def has_delete_permission(self, request, obj=None):
        return self._has_permission(request, 'delete_bookings')

class UserManagerAdmin(ManagerPermissionMixin, DjangoUserAdmin):
    """
    Manager version of UserAdmin - can modify groups but has restrictions:
    - Can modify user groups/departments
    - Cannot modify usernames
    - Cannot modify is_staff/is_superuser
    - Can trigger password reset emails
    """
    list_display = ('username', 'email', 'get_profile_role', 'get_departments', 'is_active', 'is_staff', 'date_joined')
    list_filter = ('is_active', 'is_staff', 'groups', 'profile__role')
    search_fields = ('username', 'email', 'first_name', 'last_name')
    exclude = ('password',)  # hide hashed password
    filter_horizontal = ('groups',)  # Allow editing groups/departments
    readonly_fields = ('username', 'date_joined', 'last_login')  # Managers cannot modify usernames

    # Override Django's default fieldsets to avoid field conflicts
    fieldsets = (
        (None, {'fields': ('username', 'password')}),
        ('Personal info', {'fields': ('first_name', 'last_name', 'email')}),
        ('Permissions', {
            'fields': ('is_active', 'is_staff', 'groups'),
            'classes': ('collapse',)
        }),
        ('Important dates', {'fields': ('last_login', 'date_joined'), 'classes': ('collapse',)}),
    )
    
    # Add fieldsets for creating new users (includes password fields)
    add_fieldsets = (
        (None, {
            'classes': ('wide',),
            'fields': ('username', 'password1', 'password2'),
        }),
        ('Personal info', {'fields': ('first_name', 'last_name', 'email')}),
        ('Permissions', {
            'fields': ('is_active', 'is_staff', 'groups'),
            'classes': ('collapse',)
        }),
    )

    def has_permission(self, request):
        """Check if user has permission to access this admin interface"""
        return self._is_manager(request)

    # Import ProfileInline from admin.py
    from .admin import ProfileInline
    inlines = [ProfileInline]

    actions = ['activate_users', 'deactivate_users', 'send_password_reset']

    def get_queryset(self, request):
        """Filter queryset to exclude superusers"""
        qs = super().get_queryset(request)
        return qs.exclude(is_superuser=True)

    def get_form(self, request, obj=None, **kwargs):
        """Customize form for managers"""
        form = super().get_form(request, obj, **kwargs)

        # Managers should not be able to modify is_staff or is_superuser
        if 'is_staff' in form.base_fields:
            form.base_fields['is_staff'].disabled = True
        if 'is_superuser' in form.base_fields:
            form.base_fields['is_superuser'].disabled = True

        # Only remove password change fields when EDITING existing users (obj exists)
        # For new users (obj is None), we need the password fields
        if obj is not None:  # This is an edit form, not an add form
            # Remove password change fields for managers (they can only trigger resets)
            if 'password1' in form.base_fields:
                del form.base_fields['password1']
            if 'password2' in form.base_fields:
                del form.base_fields['password2']

        return form

    def get_readonly_fields(self, request, obj=None):
        """Make username readonly for managers"""
        ro = list(super().get_readonly_fields(request, obj))
        if hasattr(request, 'user') and request.user and not request.user.is_superuser:
            ro.append('username')
        return ro

    def send_password_reset(self, request, queryset):
        """Trigger Django's password reset flow for selected users"""
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

    def activate_users(self, request, queryset):
        """Activate selected users"""
        updated = queryset.exclude(is_superuser=True).update(is_active=True)
        self.message_user(request, f"Activated {updated} user(s).")

    def deactivate_users(self, request, queryset):
        """Deactivate selected users"""
        updated = queryset.exclude(is_superuser=True).update(is_active=False)
        self.message_user(request, f"Deactivated {updated} user(s).")

    def get_departments(self, obj):
        """Display user's departments"""
        try:
            return obj.profile.departments_display or 'No departments'
        except:
            return 'No profile'
    get_departments.short_description = 'Departments'

    def get_profile_role(self, obj):
        """Display user's role"""
        try:
            return obj.profile.get_role_display()
        except:
            return 'Staff'
    get_profile_role.short_description = 'Role'

    def has_delete_permission(self, request, obj=None):
        """Managers cannot delete users"""
        return False

    def get_actions(self, request):
        """Customize actions for managers"""
        actions = super().get_actions(request)

        # Remove bulk delete for managers
        if 'delete_selected' in actions:
            del actions['delete_selected']

        # Add password reset action
        actions['send_password_reset'] = (
            self.send_password_reset,
            'send_password_reset',
            'Send password reset email to selected users'
        )

        return actions

    def get_urls(self):
        """Add password reset URL and override password change for managers"""
        from django.urls import path
        from django.contrib.admin.sites import AdminSite
        urls = super().get_urls()
        custom_urls = [
            path('<id>/password-reset/', AdminSite.admin_view(self, self.password_reset_view), name='manager_user_password_reset'),
            # Override password change URL to prevent managers from accessing it
            path('<id>/password/', AdminSite.admin_view(self, self.blocked_password_change), name='manager_user_password_change'),
        ]
        return custom_urls + urls

    def blocked_password_change(self, request, id):
        """Block managers from accessing password change form"""
        from django.contrib import messages
        from django.shortcuts import redirect

        messages.error(request, "You don't have permission to change user passwords. Use the 'Send Password Reset Email' button instead.")
        return redirect('manager_admin:auth_user_change', id)

    def password_reset_view(self, request, id):
        """Password reset view for managers"""
        from django.contrib.auth.forms import PasswordResetForm
        from django.shortcuts import get_object_or_404, redirect
        from django.contrib import messages

        user = get_object_or_404(User, pk=id)

        # Managers can only reset passwords for non-superuser accounts
        if user.is_superuser:
            messages.error(request, "You cannot reset passwords for superuser accounts.")
            return redirect('manager_admin:auth_user_change', id)

        if not user.email:
            messages.error(request, f"User {user.username} doesn't have an email address.")
            return redirect('manager_admin:auth_user_change', id)

        try:
            form = PasswordResetForm(data={'email': user.email})
            if form.is_valid():
                form.save(
                    email_template_name="registration/password_reset_email.html",
                    request=request,
                )
                messages.success(request, f"Password reset email sent to {user.username}.")
            else:
                messages.error(request, f"Failed to send password reset email to {user.username}.")
        except Exception as e:
            messages.error(request, f"Error sending password reset: {str(e)}")

        return redirect('manager_admin:auth_user_change', id)

    def change_view(self, request, object_id, form_url='', extra_context=None):
        """Add password reset button to manager change view"""
        extra_context = extra_context or {}

        # Add password reset URL for managers
        if object_id:
            from django.urls import reverse
            try:
                extra_context['password_reset_url'] = reverse('manager_admin:manager_user_password_reset', args=[object_id])
            except:
                pass

        return super().change_view(request, object_id, form_url, extra_context)

    def save_model(self, request, obj, form, change):
        """Extra guardrails for managers"""
        if not request.user.is_superuser:
            obj.is_superuser = False  # Prevent privilege escalation
        super().save_model(request, obj, form, change)

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
manager_site.register(Booking, BookingAdmin)
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