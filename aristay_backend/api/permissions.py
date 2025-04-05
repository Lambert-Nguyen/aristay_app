from rest_framework.permissions import BasePermission, SAFE_METHODS

class IsOwnerOrReadOnly(BasePermission):
    """
    Custom permission to allow only owners or admins to edit or delete an object.
    """
    def has_object_permission(self, request, view, obj):
        # Read permissions are allowed to any request.
        if request.method in SAFE_METHODS:
            return True
        
        # Write permissions are allowed only to the owner or admin.
        return obj.created_by == request.user or request.user.is_staff