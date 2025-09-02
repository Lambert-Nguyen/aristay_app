# api/decorators.py

import logging
from functools import wraps
from django.contrib.auth.decorators import login_required
from django.core.exceptions import PermissionDenied
from django.shortcuts import redirect
from django.contrib.auth.views import redirect_to_login
from django.http import HttpResponseForbidden

logger = logging.getLogger(__name__)


def staff_or_perm(permission_name):
    """
    Compatibility decorator that allows access via:
    1. Superuser (always allowed)
    2. is_staff=True (legacy Django admin users)
    3. Dynamic permission via profile.has_permission()
    
    Use this for business logic views during transition period.
    Logs which path granted access for monitoring.
    
    Args:
        permission_name (str): The custom permission to check (e.g., 'view_reports')
    """
    def decorator(view_func):
        @wraps(view_func)
        @login_required
        def wrapper(request, *args, **kwargs):
            user = request.user
            profile = getattr(user, 'profile', None)
            
            if user.is_superuser:
                logger.debug("Access granted to %s for %s via superuser", user.username, permission_name)
                return view_func(request, *args, **kwargs)
            
            if user.is_staff:
                logger.debug("Legacy is_staff access granted to %s for %s", user.username, permission_name)
                return view_func(request, *args, **kwargs)
            
            if profile and profile.has_permission(permission_name):
                logger.debug("Dynamic permission access granted to %s for %s", user.username, permission_name)
                return view_func(request, *args, **kwargs)
            
            logger.debug("Access denied to %s for %s", user.username, permission_name)
            raise PermissionDenied(f"You don't have permission to access this resource. Required: {permission_name}")
        return wrapper
    return decorator


def perm_required(permission_name):
    """
    Strict permission decorator that only checks:
    1. Superuser (always allowed)
    2. Dynamic permission via profile.has_permission()
    
    Use this for new views or after migration is complete.
    Does NOT check is_staff (strict dynamic permissions only).
    
    Args:
        permission_name (str): The custom permission to check
    """
    def decorator(view_func):
        @wraps(view_func)
        @login_required
        def wrapper(request, *args, **kwargs):
            user = request.user
            
            # Path 1: Superuser
            if user.is_superuser:
                return view_func(request, *args, **kwargs)
            
            # Path 2: Dynamic permission only
            if hasattr(user, 'profile') and user.profile and user.profile.has_permission(permission_name):
                return view_func(request, *args, **kwargs)
            
            logger.warning(
                f"Strict permission denied to {user.username} for {permission_name}",
                extra={
                    'user_id': user.id,
                    'permission': permission_name,
                    'view': view_func.__name__
                }
            )
            raise PermissionDenied(f"You don't have permission to access this resource. Required: {permission_name}")
        
        return wrapper
    return decorator


def manager_required(view_func):
    """
    Decorator that requires manager role or superuser.
    Uses the custom role system, not Django's is_staff.
    """
    @wraps(view_func)
    @login_required
    def wrapper(request, *args, **kwargs):
        user = request.user
        
        if user.is_superuser:
            return view_func(request, *args, **kwargs)
        
        profile = getattr(user, 'profile', None)
        if profile and profile.role == 'manager':
            return view_func(request, *args, **kwargs)
        
        logger.warning(
            f"Manager access denied to {user.username}",
            extra={
                'user_id': user.id,
                'user_role': profile.role if profile else 'no_profile',
                'view': view_func.__name__
            }
        )
        raise PermissionDenied("Manager access required")
    
    return wrapper


def role_required(*allowed_roles):
    """
    Decorator that requires one of the specified roles or superuser.
    
    Args:
        allowed_roles: Tuple of role names (e.g., 'manager', 'staff')
    
    Usage:
        @role_required('manager', 'staff')
        def some_view(request):
            pass
    """
    def decorator(view_func):
        @wraps(view_func)
        @login_required
        def wrapper(request, *args, **kwargs):
            user = request.user
            
            if user.is_superuser:
                return view_func(request, *args, **kwargs)
            
            profile = getattr(user, 'profile', None)
            if profile and profile.role in allowed_roles:
                return view_func(request, *args, **kwargs)
            
            logger.warning(
                f"Role access denied to {user.username}. Required: {allowed_roles}, Has: {profile.role if profile else 'no_profile'}",
                extra={
                    'user_id': user.id,
                    'required_roles': allowed_roles,
                    'user_role': profile.role if profile else 'no_profile',
                    'view': view_func.__name__
                }
            )
            raise PermissionDenied(f"Access denied. Required roles: {', '.join(allowed_roles)}")
        
        return wrapper
    return decorator


# Convenience decorators for common role combinations
def manager_or_staff_required(view_func):
    """Shortcut for requiring manager or staff role"""
    return role_required('manager', 'staff')(view_func)


def department_required(*departments):
    """
    Decorator requiring user to be in specific department(s).
    
    Args:
        *departments: Department names like 'Cleaning', 'Maintenance', 'Laundry', 'Lawn & Pool'
        
    Usage:
        @department_required('Cleaning', 'Maintenance')
        def view(request):
            pass
    """
    
    def decorator(view_func):
        @wraps(view_func)
        @login_required
        def wrapped_view(request, *args, **kwargs):
            # Superusers bypass department checks
            if request.user.is_superuser:
                return view_func(request, *args, **kwargs)
                
            # Check if user has profile and is in required department
            profile = getattr(request.user, 'profile', None)
            if profile and any(profile.is_in_department(dept) for dept in departments):
                return view_func(request, *args, **kwargs)
                
            raise PermissionDenied(f"Department access required: {', '.join(departments)}")
        return wrapped_view
    return decorator


def any_staff_required(view_func):
    """
    DEPRECATED: Use department_required() instead.
    This decorator incorrectly assumed role names matched departments.
    """
    import warnings
    warnings.warn(
        "any_staff_required is deprecated. Use @department_required('Cleaning', 'Maintenance', 'Laundry', 'Lawn & Pool') instead.",
        DeprecationWarning,
        stacklevel=2
    )
    return department_required('Cleaning', 'Maintenance', 'Laundry', 'Lawn & Pool')(view_func)
