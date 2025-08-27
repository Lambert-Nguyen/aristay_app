# api/permissions.py

from rest_framework.permissions import BasePermission, SAFE_METHODS
from .models import TaskImage

class IsOwner(BasePermission):
    """Superusers only."""
    def has_permission(self, request, view):
        return bool(request.user and request.user.is_authenticated and request.user.is_superuser)

class IsManagerOrOwner(BasePermission):
    """Managers (profile.role=='manager') or superusers."""
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