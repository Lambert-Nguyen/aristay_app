from django.contrib import admin
from django.contrib.auth.models import User
from django.contrib.auth.admin import UserAdmin as DjangoUserAdmin
from django.urls import path
from django.shortcuts import render, redirect
from django.http import Http404
from datetime import datetime
from django.contrib.admin.models import LogEntry
from django.contrib.contenttypes.models import ContentType
import json
import logging
from .models import (
    Property, Task, Notification, Booking, PropertyOwnership, Profile, UserRole,
    ChecklistTemplate, ChecklistItem, TaskChecklist, ChecklistResponse, ChecklistPhoto,
    InventoryCategory, InventoryItem, PropertyInventory, InventoryTransaction,
    LostFoundItem, LostFoundPhoto, ScheduleTemplate, GeneratedTask,
    BookingImportTemplate, BookingImportLog
)

def create_unified_history_view(model_class):
    """
    Create a unified history view function for any model that has a history field.
    This combines Django admin history with the model's custom history field.
    """
    def history_view(self, request, object_id, extra_context=None):
        """Custom history view that combines Django admin history with model.history field"""
        logger = logging.getLogger(__name__)
        logger.info(f"🔍 CUSTOM HISTORY VIEW CALLED for {model_class.__name__} {object_id}")
        
        # Get the object
        obj = self.get_object(request, object_id)
        if obj is None:
            raise Http404(f"{model_class.__name__} not found")
        
        logger.info(f"📋 {model_class.__name__} found: {getattr(obj, 'name', getattr(obj, 'title', str(obj)))}")
        
        # Get Django admin history
        content_type = ContentType.objects.get_for_model(obj)
        django_history = LogEntry.objects.filter(
            content_type=content_type,
            object_id=object_id
        ).order_by('-action_time')
        
        # Get model.history field
        model_history = []
        try:
            history_field = getattr(obj, 'history', None)
            if history_field:
                model_history = json.loads(history_field or '[]')
        except json.JSONDecodeError:
            model_history = []
        
        logger.info(f"📝 {model_class.__name__}.history field: {len(model_history)} entries")
        
        # Combine and sort histories by timestamp
        combined_history = []
        
        # Add Django admin history
        for entry in django_history:
            # Ensure timezone-aware datetime
            timestamp = entry.action_time
            if timestamp.tzinfo is None:
                from django.utils import timezone
                timestamp = timezone.make_aware(timestamp)
            
            combined_history.append({
                'timestamp': timestamp,
                'user': entry.user.username if entry.user else 'System',
                'action': entry.get_action_flag_display(),
                'changes': entry.change_message,
                'type': 'admin'
            })
        
        # Add model.history entries
        for entry in model_history:
            if isinstance(entry, str) and ':' in entry:
                try:
                    # Parse format: "2025-01-08T10:30:00.000000+00:00: username changed status from 'old' to 'new'"
                    timestamp_str, change_desc = entry.split(':', 1)
                    timestamp = datetime.fromisoformat(timestamp_str.replace('Z', '+00:00'))
                    
                    # Ensure timezone-aware datetime
                    if timestamp.tzinfo is None:
                        from django.utils import timezone
                        timestamp = timezone.make_aware(timestamp)
                    
                    combined_history.append({
                        'timestamp': timestamp,
                        'user': change_desc.split(' ')[0] if change_desc else 'Unknown',
                        'action': 'Changed',
                        'changes': change_desc.strip(),
                        'type': 'dashboard'
                    })
                except (ValueError, IndexError):
                    # Skip malformed entries
                    continue
        
        # Sort by timestamp (newest first)
        combined_history.sort(key=lambda x: x['timestamp'], reverse=True)
        
        # Create context
        context = {
            'title': f'History for {getattr(obj, "name", getattr(obj, "title", str(obj)))}',
            'object': obj,
            'history': combined_history,
            'opts': self.model._meta,
            'has_change_permission': self.has_change_permission(request, obj),
        }
        
        if extra_context:
            context.update(extra_context)
        
        return render(request, 'admin/task_history.html', context)
    
    return history_view

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
            path('invite-codes/', self.admin_view(self.invite_codes_view), name='manager_invite_codes'),
            path('create-invite-code/', self.admin_view(self.create_invite_code_view), name='manager_create_invite_code'),
            path('invite-codes/<int:code_id>/', self.admin_view(self.invite_code_detail_view), name='manager_invite_code_detail'),
            path('invite-codes/<int:code_id>/edit/', self.admin_view(self.edit_invite_code_view), name='manager_edit_invite_code'),
            path('invite-codes/<int:code_id>/revoke/', self.admin_view(self.revoke_invite_code_view), name='manager_revoke_invite_code'),
            path('invite-codes/<int:code_id>/reactivate/', self.admin_view(self.reactivate_invite_code_view), name='manager_reactivate_invite_code'),
            path('invite-codes/<int:code_id>/delete/', self.admin_view(self.delete_invite_code_view), name='manager_delete_invite_code'),
        ]
        return custom_urls + urls
    
    def charts_view(self, request):
        """Custom charts dashboard view"""
        from .views import manager_charts_dashboard
        return manager_charts_dashboard(request)
    
    def invite_codes_view(self, request):
        """Invite codes list view"""
        from .invite_code_views import invite_code_list
        return invite_code_list(request)
    
    def create_invite_code_view(self, request):
        """Create invite code view"""
        from .invite_code_views import create_invite_code
        return create_invite_code(request)
    
    def invite_code_detail_view(self, request, code_id):
        """Invite code detail view"""
        from .invite_code_views import invite_code_detail
        return invite_code_detail(request, code_id)
    
    def edit_invite_code_view(self, request, code_id):
        """Edit invite code view"""
        from .invite_code_views import edit_invite_code
        return edit_invite_code(request, code_id)
    
    def revoke_invite_code_view(self, request, code_id):
        """Revoke invite code view"""
        from .invite_code_views import revoke_invite_code
        return revoke_invite_code(request, code_id)
    
    def reactivate_invite_code_view(self, request, code_id):
        """Reactivate invite code view"""
        from .invite_code_views import reactivate_invite_code
        return reactivate_invite_code(request, code_id)
    
    def delete_invite_code_view(self, request, code_id):
        """Delete invite code view"""
        from .invite_code_views import delete_invite_code
        return delete_invite_code(request, code_id)

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
    
    # Use the generic unified history view
    history_view = create_unified_history_view(Property)

class TaskAdmin(ManagerPermissionMixin, admin.ModelAdmin):
    list_display = ('id', 'title', 'task_type', 'status', 'property_ref', 'booking', 'created_at')
    search_fields = ('title', 'description')
    list_filter = ('status', 'task_type', 'created_at', 'property_ref', 'booking')
    readonly_fields = ('history', 'created_at', 'modified_at')
    
    # Override to use dynamic permissions for tasks
    def has_view_permission(self, request, obj=None):
        return self._has_permission(request, 'view_tasks')
    
    def has_add_permission(self, request):
        return self._has_permission(request, 'add_tasks')
    
    def has_change_permission(self, request, obj=None):
        return self._has_permission(request, 'change_tasks')
    
    def has_delete_permission(self, request, obj=None):
        return self._has_permission(request, 'delete_tasks')
    
    # Use the generic unified history view
    history_view = create_unified_history_view(Task)
    
    def old_history_view(self, request, object_id, extra_context=None):
        """Custom history view that combines Django admin history with Task.history field"""
        from django.contrib.admin.models import LogEntry
        from django.contrib.contenttypes.models import ContentType
        from django.utils.html import format_html
        from django.utils.safestring import mark_safe
        import json
        
        print(f"🔍 CUSTOM HISTORY VIEW CALLED for task {object_id}")
        
        # Get the task object
        task = self.get_object(request, object_id)
        if task is None:
            raise Http404("Task not found")
        
        print(f"📋 Task found: {task.title}")
        print(f"📝 Task.history field: {task.history[:100]}...")
        
        # Get Django admin history
        content_type = ContentType.objects.get_for_model(task)
        django_history = LogEntry.objects.filter(
            content_type=content_type,
            object_id=object_id
        ).order_by('-action_time')
        
        # Get Task.history field
        task_history = []
        try:
            task_history = json.loads(task.history or '[]')
        except json.JSONDecodeError:
            task_history = []
        
        # Combine and sort histories by timestamp
        combined_history = []
        
        # Add Django admin history
        for entry in django_history:
            # Ensure timezone-aware datetime
            timestamp = entry.action_time
            if timestamp.tzinfo is None:
                from django.utils import timezone
                timestamp = timezone.make_aware(timestamp)
            
            combined_history.append({
                'timestamp': timestamp,
                'user': entry.user.username if entry.user else 'System',
                'action': entry.get_action_flag_display(),
                'changes': entry.change_message,
                'type': 'admin'
            })
        
        # Add Task.history entries
        for entry in task_history:
            if isinstance(entry, str) and ':' in entry:
                try:
                    # Parse format: "2025-01-08T10:30:00.000000+00:00: username changed status from 'old' to 'new'"
                    timestamp_str, change_desc = entry.split(':', 1)
                    timestamp = datetime.fromisoformat(timestamp_str.replace('Z', '+00:00'))
                    
                    # Ensure timezone-aware datetime
                    if timestamp.tzinfo is None:
                        from django.utils import timezone
                        timestamp = timezone.make_aware(timestamp)
                    
                    combined_history.append({
                        'timestamp': timestamp,
                        'user': change_desc.split(' ')[0] if change_desc else 'Unknown',
                        'action': 'Changed',
                        'changes': change_desc.strip(),
                        'type': 'dashboard'
                    })
                except (ValueError, IndexError):
                    # Skip malformed entries
                    continue
        
        # Sort by timestamp (newest first)
        combined_history.sort(key=lambda x: x['timestamp'], reverse=True)
        
        # Create context
        context = {
            'title': f'History for {task.title}',
            'object': task,
            'history': combined_history,
            'opts': self.model._meta,
            'has_change_permission': self.has_change_permission(request, task),
        }
        
        if extra_context:
            context.update(extra_context)
        
        return render(request, 'admin/task_history.html', context)

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
    
    # Use the generic unified history view
    history_view = create_unified_history_view(Booking)

class UserManagerAdmin(ManagerPermissionMixin, DjangoUserAdmin):
    """
    Manager version of UserAdmin - can modify groups but has restrictions:
    - Can modify user groups/departments
    - Cannot modify usernames
    - Cannot modify is_staff/is_superuser
    - Can trigger password reset emails
    """
    list_display = ('username', 'email', 'get_profile_role', 'get_task_group', 'get_departments', 'is_active', 'is_superuser', 'date_joined')
    list_filter = ('is_active', 'groups', 'profile__role', 'profile__task_group')
    search_fields = ('username', 'email', 'first_name', 'last_name')
    # Don't exclude password - let Django handle it properly
    filter_horizontal = ('groups',)  # Allow editing groups/departments
    readonly_fields = ('username', 'password', 'date_joined', 'last_login')  # Include password as readonly

    # Override Django's default fieldsets to show password properly
    fieldsets = (
        (None, {
            'fields': ('username', 'password'),
            'description': 'Password is encrypted and cannot be viewed. Use "Reset password" link below to send a new password to the user via email.'
        }),
        ('Personal info', {'fields': ('first_name', 'last_name', 'email')}),
        ('Permissions', {
            'fields': ('is_active', 'groups'),
            'classes': ('collapse',),
            'description': 'Note: User role (staff/manager/superuser/viewer) is set in the Profile section below. Django admin access (is_superuser) will be automatically synced based on Profile role.'
        }),
        ('Important dates', {'fields': ('last_login', 'date_joined'), 'classes': ('collapse',)}),
    )
    
    # Add fieldsets for creating new users (includes password fields)
    add_fieldsets = (
        (None, {
            'classes': ('wide',),
            'fields': ('username', 'password1', 'password2'),
            'description': 'Passwords are encrypted and stored securely. Users can change their password later via the reset password function.'
        }),
        ('Personal info', {'fields': ('first_name', 'last_name', 'email')}),
        ('Permissions', {
            'fields': ('is_active', 'groups'),
            'classes': ('collapse',),
            'description': 'Note: User role (staff/manager) will be set via Profile after user creation.'
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

        # Remove is_staff and is_superuser from form entirely (use Profile.role instead)
        if 'is_staff' in form.base_fields:
            del form.base_fields['is_staff']  
        if 'is_superuser' in form.base_fields:
            del form.base_fields['is_superuser']

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

    def save_model(self, request, obj, form, change):
        """Override save to handle Profile creation and role assignment"""
        # Save the user first
        super().save_model(request, obj, form, change)
        
        # Ensure user has a Profile with appropriate role
        profile, created = Profile.objects.get_or_create(
            user=obj,
            defaults={
                'role': UserRole.STAFF,  # Default new users to staff role
                'timezone': 'America/New_York',
            }
        )
        
        # If this is a new user, log the creation
        if not change:  # This is a new user
            print(f"✅ Created new user '{obj.username}' with Profile role: {profile.role}")
            
    def save_formset(self, request, form, formset, change):
        """Override to handle Profile inline saves"""
        super().save_formset(request, form, formset, change)
        
        # After saving Profile inline, ensure is_superuser is synced correctly
        user = form.instance
        if hasattr(user, 'profile') and user.profile:
            # Set is_superuser based on profile role (only for superuser role)
            should_have_superuser_access = user.profile.role == UserRole.SUPERUSER
            if user.is_superuser != should_have_superuser_access:
                user.is_superuser = should_have_superuser_access
                user.save(update_fields=['is_superuser'])
                print(f"✅ Synced is_superuser={user.is_superuser} for {user.username} (role: {user.profile.role})")

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
    
    def get_task_group(self, obj):
        """Display user's task group"""
        try:
            return obj.profile.get_task_group_display()
        except:
            return 'Not Assigned'
    get_task_group.short_description = 'Task Group'
    get_task_group.admin_order_field = 'profile__task_group'

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
    
    def history_view(self, request, object_id, extra_context=None):
        """Custom history view for User model (Django admin history + custom history)"""
        logger = logging.getLogger(__name__)
        logger.info(f"🔍 CUSTOM HISTORY VIEW CALLED for User {object_id}")
        
        # Get the user object
        user = self.get_object(request, object_id)
        if user is None:
            raise Http404("User not found")
        
        logger.info(f"📋 User found: {user.username}")
        
        # Get Django admin history
        content_type = ContentType.objects.get_for_model(user)
        django_history = LogEntry.objects.filter(
            content_type=content_type,
            object_id=object_id
        ).order_by('-action_time')
        
        # Get custom user history (if it exists)
        custom_history = []
        try:
            history_field = getattr(user, 'history', None)
            if history_field:
                custom_history = json.loads(history_field or '[]')
        except json.JSONDecodeError:
            custom_history = []
        
        # Get password reset history
        password_reset_history = []
        try:
            from api.password_reset_logs import get_user_password_reset_history
            password_reset_history = get_user_password_reset_history(user)
        except Exception as e:
            logger.error(f"Failed to get password reset history: {e}")
        
        # Combine custom history and password reset history
        all_custom_history = custom_history + password_reset_history
        
        logger.info(f"📝 User.history field: {len(custom_history)} entries")
        logger.info(f"📝 Password reset history: {len(password_reset_history)} entries")
        
        # Convert to combined history format
        combined_history = []
        
        # Add Django admin history
        for entry in django_history:
            # Ensure timezone-aware datetime
            timestamp = entry.action_time
            if timestamp.tzinfo is None:
                from django.utils import timezone
                timestamp = timezone.make_aware(timestamp)
            
            combined_history.append({
                'timestamp': timestamp,
                'user': entry.user.username if entry.user else 'System',
                'action': entry.get_action_flag_display(),
                'changes': entry.change_message,
                'type': 'admin'
            })
        
        # Add custom history (password resets, etc.)
        for entry in all_custom_history:
            if isinstance(entry, str) and ':' in entry:
                try:
                    timestamp_str, change_desc = entry.split(':', 1)
                    timestamp = datetime.fromisoformat(timestamp_str.replace('Z', '+00:00'))
                    
                    if timestamp.tzinfo is None:
                        from django.utils import timezone
                        timestamp = timezone.make_aware(timestamp)
                    
                    combined_history.append({
                        'timestamp': timestamp,
                        'user': change_desc.split(' ')[0] if change_desc else 'Unknown',
                        'action': 'Changed',
                        'changes': change_desc.strip(),
                        'type': 'dashboard'
                    })
                except (ValueError, IndexError):
                    continue
        
        # Sort by timestamp (newest first)
        combined_history.sort(key=lambda x: x['timestamp'], reverse=True)
        
        # Create context
        context = {
            'title': f'History for {user.username}',
            'object': user,
            'history': combined_history,
            'opts': self.model._meta,
            'has_change_permission': self.has_change_permission(request, user),
        }
        
        if extra_context:
            context.update(extra_context)
        
        return render(request, 'admin/task_history.html', context)

class NotificationManagerAdmin(ManagerPermissionMixin, admin.ModelAdmin):
    list_display = ('id', 'recipient', 'task_title', 'verb', 'read', 'timestamp', 'read_at')
    list_filter = ('read', 'verb', 'timestamp')
    search_fields = ('recipient__username', 'task__title')
    readonly_fields = ('timestamp', 'push_sent')
    list_per_page = 50
    
    # Use the generic unified history view
    history_view = create_unified_history_view(Notification)
    
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
    # Use the generic unified history view
    history_view = create_unified_history_view(ChecklistTemplate)

class ChecklistResponseManagerAdmin(ManagerPermissionMixin, ChecklistResponseAdmin):
    pass

class TaskChecklistManagerAdmin(ManagerPermissionMixin, TaskChecklistAdmin):
    pass

class InventoryCategoryManagerAdmin(ManagerPermissionMixin, InventoryCategoryAdmin):
    pass

class InventoryItemManagerAdmin(ManagerPermissionMixin, InventoryItemAdmin):
    # Use the generic unified history view
    history_view = create_unified_history_view(InventoryItem)

class PropertyInventoryManagerAdmin(ManagerPermissionMixin, PropertyInventoryAdmin):
    # Use the generic unified history view
    history_view = create_unified_history_view(PropertyInventory)

class InventoryTransactionManagerAdmin(ManagerPermissionMixin, InventoryTransactionAdmin):
    # Use the generic unified history view
    history_view = create_unified_history_view(InventoryTransaction)

class LostFoundItemManagerAdmin(ManagerPermissionMixin, LostFoundItemAdmin):
    pass

class ScheduleTemplateManagerAdmin(ManagerPermissionMixin, ScheduleTemplateAdmin):
    pass

class GeneratedTaskManagerAdmin(ManagerPermissionMixin, GeneratedTaskAdmin):
    # Use the generic unified history view
    history_view = create_unified_history_view(GeneratedTask)

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