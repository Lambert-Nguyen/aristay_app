# api/permissions.py

from rest_framework.permissions import BasePermission, SAFE_METHODS
from .models import TaskImage


class HasCustomPermission(BasePermission):
    """
    Permission class that checks against the custom permission system
    Usage: permission_classes = [HasCustomPermission('view_tasks')]
    """
    
    def __init__(self, permission_name):
        self.permission_name = permission_name
    
    def __call__(self):
        """Allow this class to be instantiated with parameters"""
        return self
    
    def has_permission(self, request, view):
        """Check if user has the specified permission"""
        if not (request.user and request.user.is_authenticated):
            return False
        
        # Superusers always have access
        if request.user.is_superuser:
            return True
        
        # Check custom permission system
        if hasattr(request.user, 'profile') and request.user.profile:
            return request.user.profile.has_permission(self.permission_name)
        
        return False


class HasAnyCustomPermission(BasePermission):
    """
    Permission class that checks if user has any of the specified permissions
    Usage: permission_classes = [HasAnyCustomPermission(['view_tasks', 'add_tasks'])]
    """
    
    def __init__(self, permission_names):
        self.permission_names = permission_names if isinstance(permission_names, list) else [permission_names]
    
    def __call__(self):
        return self
    
    def has_permission(self, request, view):
        if not (request.user and request.user.is_authenticated):
            return False
        
        if request.user.is_superuser:
            return True
        
        if hasattr(request.user, 'profile') and request.user.profile:
            for permission_name in self.permission_names:
                if request.user.profile.has_permission(permission_name):
                    return True
        
        return False


class IsOwner(BasePermission):
    """Superusers only (Superuser)."""
    def has_permission(self, request, view):
        return bool(request.user and request.user.is_authenticated and request.user.is_superuser)


class IsManagerOrOwner(BasePermission):
    """Managers (profile.role=='manager') or Superusers."""
    def has_permission(self, request, view):
        u = request.user
        if not (u and u.is_authenticated):
            return False
        if u.is_superuser:
            return True
        role = getattr(getattr(u, 'profile', None), 'role', 'staff')
        return role == 'manager'


class IsOwnerOrAssignedOrReadOnly(BasePermission):
    """
    - Anyone can read.
    - Only the task's creator, assignee, or staff can write or delete,
      whether you're operating on a Task or on a TaskImage.
    """
    def has_object_permission(self, request, view, obj):
        # always allow GET, HEAD, OPTIONS
        if request.method in SAFE_METHODS:
            return True

        # if they're acting on an image, drill down to its task
        if isinstance(obj, TaskImage):
            task = obj.task
        else:
            task = obj

        # allow if user is creator, assignee, or admin
        user = request.user
        return (
            user.is_staff or
            task.created_by == user or
            task.assigned_to == user
        )


# Permission helper functions
def create_permission_class(permission_name):
    """
    Factory function to create permission classes for specific permissions
    Usage: permission_classes = [create_permission_class('view_tasks')]
    """
    class DynamicPermission(HasCustomPermission):
        def has_permission(self, request, view):
            if not (request.user and request.user.is_authenticated):
                return False
            
            if request.user.is_superuser:
                return True
            
            if hasattr(request.user, 'profile') and request.user.profile:
                return request.user.profile.has_permission(permission_name)
            
            return False
    
    return DynamicPermission


class DynamicCRUDPermissions(BasePermission):
    """
    Dynamic CRUD permissions that adjust based on user's actual permissions
    Maps HTTP methods to permission requirements
    """
    
    def __init__(self, permission_map=None):
        """
        permission_map: dict mapping HTTP methods to permission names
        Example: {
            'GET': ['view_bookings'],
            'POST': ['add_bookings'], 
            'PUT': ['change_bookings'],
            'PATCH': ['change_bookings'],
            'DELETE': ['delete_bookings']
        }
        """
        self.permission_map = permission_map or {}
    
    def has_permission(self, request, view):
        if not (request.user and request.user.is_authenticated):
            return False
        
        if request.user.is_superuser:
            return True
        
        # Get required permissions for this HTTP method
        method = request.method
        required_permissions = self.permission_map.get(method, [])
        
        # If no permissions specified for this method, deny access
        if not required_permissions:
            return False
        
        # Check if user has any of the required permissions
        if hasattr(request.user, 'profile') and request.user.profile:
            for permission in required_permissions:
                if request.user.profile.has_permission(permission):
                    return True
        
        return False


class DynamicBookingPermissions(DynamicCRUDPermissions):
    """Booking-specific permissions"""
    
    def __init__(self):
        permission_map = {
            'GET': ['view_bookings'],
            'POST': ['add_bookings'],
            'PUT': ['change_bookings'],
            'PATCH': ['change_bookings'],
            'DELETE': ['delete_bookings']
        }
        super().__init__(permission_map)


class DynamicTaskPermissions(DynamicCRUDPermissions):
    """Task-specific permissions"""
    
    def __init__(self):
        permission_map = {
            'GET': ['view_tasks'],
            'POST': ['add_tasks'],
            'PUT': ['change_tasks'],
            'PATCH': ['change_tasks'],
            'DELETE': ['delete_tasks']
        }
        super().__init__(permission_map)


class DynamicUserPermissions(DynamicCRUDPermissions):
    """User management permissions"""
    
    def __init__(self):
        permission_map = {
            'GET': ['view_users'],
            'POST': ['add_users'],
            'PUT': ['change_users'],
            'PATCH': ['change_users'],
            'DELETE': ['delete_users']
        }
        super().__init__(permission_map)


class DynamicPropertyPermissions(DynamicCRUDPermissions):
    """Property management permissions"""
    
    def __init__(self):
        permission_map = {
            'GET': ['view_properties'],
            'POST': ['add_properties'],
            'PUT': ['change_properties'],
            'PATCH': ['change_properties'],
            'DELETE': ['delete_properties']
        }
        super().__init__(permission_map)


class CanViewReports(BasePermission):
    """Permission to view reports and analytics"""
    
    def has_permission(self, request, view):
        if not (request.user and request.user.is_authenticated):
            return False
        
        if request.user.is_superuser:
            return True
        
        if hasattr(request.user, 'profile') and request.user.profile:
            return request.user.profile.has_permission('view_reports')
        
        return False


class CanViewAnalytics(BasePermission):
    """Permission to view analytics dashboard"""
    
    def has_permission(self, request, view):
        if not (request.user and request.user.is_authenticated):
            return False
        
        if request.user.is_superuser:
            return True
        
        if hasattr(request.user, 'profile') and request.user.profile:
            return request.user.profile.has_permission('view_analytics')
        
        return False


class CanAccessAdminPanel(BasePermission):
    """Permission to access admin panel"""
    
    def has_permission(self, request, view):
        if not (request.user and request.user.is_authenticated):
            return False
        
        if request.user.is_superuser:
            return True
        
        if hasattr(request.user, 'profile') and request.user.profile:
            return request.user.profile.has_permission('admin_panel_access')
        
        return False


class CanManageFiles(BasePermission):
    """Permission to manage file uploads and imports"""
    
    def has_permission(self, request, view):
        if not (request.user and request.user.is_authenticated):
            return False
        
        if request.user.is_superuser:
            return True
        
        if hasattr(request.user, 'profile') and request.user.profile:
            return (request.user.profile.has_permission('excel_import_access') or
                   request.user.profile.has_permission('file_upload_access'))
        
        return False