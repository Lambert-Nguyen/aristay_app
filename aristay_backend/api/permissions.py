from rest_framework.permissions import BasePermission, SAFE_METHODS

class IsOwnerOrAssignedOrReadOnly(BasePermission):
    """
    Read-only for everyone.
    Writes allowed if request.user is:
      • the creator (created_by), or
      • the assignee (assigned_to), or
      • a staff/superuser.
    """
    def has_object_permission(self, request, view, obj):
        # always allow safe methods
        if request.method in SAFE_METHODS:
            return True

        user = request.user
        # staff can do anything
        if user.is_staff or user.is_superuser:
            return True

        # allow creator or assigned user
        return (
            obj.created_by == user or
            obj.assigned_to == user
        )