# api/managersite.py
from django.contrib import admin
from django.contrib.auth.models import User
from .models import Property, Task

class ManagerAdminSite(admin.AdminSite):
    site_header = "AriStay Manager"
    site_title  = "AriStay Manager"
    index_title = "Management Console"

    def has_permission(self, request):
        if not request.user or not request.user.is_authenticated:
            return False
        if request.user.is_superuser:
            return True
        role = getattr(getattr(request.user, 'profile', None), 'role', 'staff')
        return role == 'manager'

manager_site = ManagerAdminSite(name='manager_admin')

class PropertyAdmin(admin.ModelAdmin):
    list_display = ('id', 'name', 'created_at', 'modified_at')
    search_fields = ('name',)

class TaskAdmin(admin.ModelAdmin):
    list_display = ('id', 'title', 'task_type', 'status', 'property', 'created_at')
    search_fields = ('title', 'description')
    list_filter = ('status', 'task_type', 'created_at')

class UserManagerAdmin(admin.ModelAdmin):
    list_display  = ('username', 'email', 'is_active', 'is_staff', 'is_superuser', 'date_joined')
    list_filter   = ('is_active', 'is_staff', 'is_superuser')
    search_fields = ('username', 'email', 'first_name', 'last_name')
    readonly_fields = ('last_login', 'date_joined',)

    actions = ['activate_users', 'deactivate_users']

    def get_readonly_fields(self, request, obj=None):
        ro = list(super().get_readonly_fields(request, obj))
        if not request.user.is_superuser:
            ro += ['is_staff', 'is_superuser', 'user_permissions', 'groups']
        return ro

    def activate_users(self, request, queryset):
        updated = queryset.exclude(is_superuser=True).update(is_active=True)
        self.message_user(request, f"Activated {updated} user(s).")

    def deactivate_users(self, request, queryset):
        updated = queryset.exclude(is_superuser=True).update(is_active=False)
        self.message_user(request, f"Deactivated {updated} user(s).")

# register on the manager site
manager_site.register(Property, PropertyAdmin)
manager_site.register(Task, TaskAdmin)
manager_site.register(User, UserManagerAdmin)