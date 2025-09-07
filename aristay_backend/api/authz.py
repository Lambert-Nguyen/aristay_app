# api/authz.py
"""
Centralized authorization helpers for AriStay application.
Provides consistent permission checking across views and templates.
"""

import logging
from django.db.models import Q

logger = logging.getLogger(__name__)


class AuthzHelper:
    """Centralized authorization helper for consistent permission checks"""
    
    @staticmethod
    def can_edit_task(user, task):
        """
        Check if user can edit a specific task
        
        Rules:
        - Superuser: Always allowed
        - Manager: Can edit any task
        - Task creator: Can edit tasks they created
        - Task assignee: Can edit their assigned tasks
        - Staff with change_tasks permission: Can edit tasks
        - Staff with manage_files permission: Can manage task files
        """
        if not user or not user.is_authenticated:
            return False
            
        if user.is_superuser:
            return True
            
        # Manager role can edit any task
        profile = getattr(user, 'profile', None)
        if profile and profile.role == 'manager':
            return True
            
        # Task creator can edit their own task - Agent's security enhancement
        if task.created_by == user:
            return True
            
        # Task assignee can edit their assigned task
        if task.assigned_to == user:
            return True
            
        # Check dynamic permissions
        if profile and (profile.has_permission('change_tasks') or profile.has_permission('manage_files')):
            return True
            
        return False
    
    @staticmethod
    def can_view_task(user, task):
        """
        Check if user can view a specific task
        
        Rules:
        - Superuser: Always allowed
        - Manager: Can view any task
        - Task assignee: Can view their own tasks
        - Staff with view_tasks or view_all_tasks permission: Can view tasks
        """
        if not user or not user.is_authenticated:
            return False
            
        if user.is_superuser:
            return True
            
        profile = getattr(user, 'profile', None)
        
        # Manager role can view any task
        if profile and profile.role == 'manager':
            return True
            
        # Task assignee can view their own task
        if task.assigned_to == user:
            return True
            
        # Check dynamic permissions
        if profile:
            if profile.has_permission('view_all_tasks') or profile.has_permission('view_tasks'):
                return True
                
        return False
    
    @staticmethod
    def can_assign_task(user, task=None):
        """
        Check if user can assign tasks to others
        
        Rules:
        - Superuser: Always allowed
        - Manager: Can assign any task
        - Staff with assign_tasks permission: Can assign tasks
        """
        if not user or not user.is_authenticated:
            return False
            
        if user.is_superuser:
            return True
            
        profile = getattr(user, 'profile', None)
        
        # Manager role can assign tasks
        if profile and profile.role == 'manager':
            return True
            
        # Check dynamic permission
        if profile and profile.has_permission('assign_tasks'):
            return True
            
        return False
    
    @staticmethod
    def can_manage_property(user, property_obj=None):
        """
        Check if user can manage properties
        
        Rules:
        - Superuser: Always allowed
        - Manager: Can manage any property
        - Staff with property management permissions: Can manage properties
        - Property owners: Can manage their own properties
        """
        if not user or not user.is_authenticated:
            return False
            
        if user.is_superuser:
            return True
            
        profile = getattr(user, 'profile', None)
        
        # Manager role can manage properties
        if profile and profile.role == 'manager':
            return True
            
        # Check property ownership if specific property provided
        if property_obj:
            from .models import PropertyOwnership
            return PropertyOwnership.objects.filter(
                property=property_obj,
                user=user,
                ownership_type__in=['owner','manager']
            ).exists()
                
        # Check dynamic permissions
        if profile:
            if profile.has_permission('change_properties'):
                return True
                
        return False
    
    @staticmethod
    def can_view_reports(user):
        """Check if user can view reports and analytics"""
        if not user or not user.is_authenticated:
            return False
            
        if user.is_superuser:
            return True
            
        profile = getattr(user, 'profile', None)
        
        # Manager role can view reports
        if profile and profile.role == 'manager':
            return True
            
        # Check dynamic permission
        if profile and profile.has_permission('view_reports'):
            return True
            
        return False
    
    @staticmethod
    def can_manage_users(user):
        """Check if user can manage other users"""
        if not user or not user.is_authenticated:
            return False
            
        if user.is_superuser:
            return True
            
        profile = getattr(user, 'profile', None)
        
        # Manager role can manage users
        if profile and profile.role == 'manager':
            return True
            
        # Check dynamic permission
        if profile and profile.has_permission('manage_users'):
            return True
            
        return False
    
    @staticmethod
    def get_accessible_properties(user):
        """
        Get queryset of properties user can access
        
        Returns:
        - Superuser: All properties
        - Manager: All properties
        - Property owners: Their owned properties
        - Staff: Properties they have tasks on or explicit access to
        """
        from .models import Property
        
        if not user or not user.is_authenticated:
            return Property.objects.none()
            
        if user.is_superuser:
            return Property.objects.all()
            
        profile = getattr(user, 'profile', None)
        
        # Manager role gets all properties
        if profile and profile.role == 'manager':
            return Property.objects.all()
            
        # Build query for accessible properties
        property_ids = set()
        
        # Properties user owns/manages via PropertyOwnership
        from .models import PropertyOwnership
        owned_properties = Property.objects.filter(
            ownerships__user=user,
            ownerships__ownership_type__in=['owner','manager']
        ).values_list('id', flat=True)
        property_ids.update(owned_properties)
        
        # Properties user has tasks on
        task_properties = Property.objects.filter(tasks__assigned_to=user).values_list('id', flat=True)
        property_ids.update(task_properties)
        
        # If user has view_all_properties permission, they get all
        if profile and profile.has_permission('view_properties'):
            return Property.objects.all()
            
        return Property.objects.filter(id__in=property_ids)
    
    @staticmethod
    def get_manager_users():
        """Get queryset of users who are managers (for notifications, etc.)"""
        from django.contrib.auth.models import User
        
        return User.objects.filter(
            Q(is_superuser=True) | 
            Q(profile__role='manager')
        ).select_related('profile')
    
    @staticmethod
    def has_role(user, role):
        """Check if user has a specific role"""
        if not user or not user.is_authenticated:
            return False
            
        if user.is_superuser and role in ['superuser', 'manager']:
            return True
            
        profile = getattr(user, 'profile', None)
        return profile and profile.role == role
    
    @staticmethod
    def get_user_role_display(user):
        """Get user's role for display purposes"""
        if not user or not user.is_authenticated:
            return "Anonymous"
            
        if user.is_superuser:
            return "Superuser"
            
        profile = getattr(user, 'profile', None)
        if profile:
            return profile.get_role_display()
            
        return "No Role"


# Convenience functions (can be used in templates)
def can_edit_task(user, task):
    """Template-friendly wrapper for task editing permission"""
    return AuthzHelper.can_edit_task(user, task)


def can_view_task(user, task):
    """Template-friendly wrapper for task viewing permission"""
    return AuthzHelper.can_view_task(user, task)


def can_manage_property(user, property_obj=None):
    """Template-friendly wrapper for property management permission"""
    return AuthzHelper.can_manage_property(user, property_obj)


def can_view_reports(user):
    """Template-friendly wrapper for reports permission"""
    return AuthzHelper.can_view_reports(user)


def has_role(user, role):
    """Template-friendly wrapper for role checking"""
    return AuthzHelper.has_role(user, role)
