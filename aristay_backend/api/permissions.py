# api/permissions.py

from rest_framework.permissions import BasePermission, SAFE_METHODS

class IsOwnerOrAssignedOrReadOnly(BasePermission):
    """
    Read-only for everyone.
    PATCH/PUT allowed for created_by or assigned_to.
    DELETE only allowed for staff/superuser.
    """

    def has_object_permission(self, request, view, obj):
        # always allow safe methods (GET, HEAD, OPTIONS)
        if request.method in SAFE_METHODS:
            return True

        user = request.user

        # staff and superusers can do anything
        if user.is_staff or user.is_superuser:
            return True

        # NORMAL USERS:
        # - PATCH/PUT allowed if creator or assignee
        if request.method in ('PATCH', 'PUT'):
            return obj.created_by == user or obj.assigned_to == user

        # - DELETE explicitly denied for non-staff
        if request.method == 'DELETE':
            return False

        # anything else (e.g. POST on detail) – deny
        return False