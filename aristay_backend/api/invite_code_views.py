"""
Enhanced Invite Code Management Views
Supports both Admin and Manager portals with proper permissions
"""
import secrets
import string
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.utils import timezone
from django.http import JsonResponse
from django.db import transaction
from django.core.paginator import Paginator
from django.db.models import Q
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework import status
from .models import InviteCode, Profile, UserRole, TaskGroup
from .serializers import InviteCodeSerializer
from .decorators import staff_or_perm
from .authz import AuthzHelper
import logging

logger = logging.getLogger(__name__)


def generate_invite_code(length=8):
    """Generate a secure random invite code"""
    alphabet = string.ascii_uppercase + string.digits
    return ''.join(secrets.choice(alphabet) for _ in range(length))


def can_manage_invite_codes(user):
    """Check if user can manage invite codes"""
    if user.is_superuser:
        return True
    
    try:
        profile = user.profile
        return profile.role in [UserRole.MANAGER, UserRole.SUPERUSER]
    except Profile.DoesNotExist:
        # If no profile exists, check if user is superuser
        return user.is_superuser


@login_required
def invite_code_list(request):
    """List all invite codes with filtering and pagination"""
    if not can_manage_invite_codes(request.user):
        messages.error(request, 'Access denied. You do not have permission to manage invite codes.')
        return redirect('/api/portal/')
    
    # Get filter parameters
    role_filter = request.GET.get('role', '')
    task_group_filter = request.GET.get('task_group', '')
    status_filter = request.GET.get('status', '')
    search_query = request.GET.get('search', '')
    
    # Build queryset
    invite_codes = InviteCode.objects.select_related('created_by').all()
    
    # Apply filters
    if role_filter:
        invite_codes = invite_codes.filter(role=role_filter)
    
    if task_group_filter:
        invite_codes = invite_codes.filter(task_group=task_group_filter)
    
    if status_filter == 'active':
        invite_codes = invite_codes.filter(is_active=True)
    elif status_filter == 'inactive':
        invite_codes = invite_codes.filter(is_active=False)
    elif status_filter == 'expired':
        invite_codes = invite_codes.filter(expires_at__lt=timezone.now())
    elif status_filter == 'usable':
        invite_codes = invite_codes.filter(
            is_active=True
        ).filter(
            Q(expires_at__isnull=True) | Q(expires_at__gt=timezone.now())
        )
    
    if search_query:
        invite_codes = invite_codes.filter(
            Q(code__icontains=search_query) |
            Q(created_by__username__icontains=search_query) |
            Q(notes__icontains=search_query)
        )
    
    # Pagination
    paginator = Paginator(invite_codes, 20)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    
    # Get filter options
    role_choices = UserRole.choices
    task_group_choices = TaskGroup.choices
    
    context = {
        'invite_codes': page_obj.object_list,
        'page_obj': page_obj,
        'role_choices': role_choices,
        'task_group_choices': task_group_choices,
        'current_filters': {
            'role': role_filter,
            'task_group': task_group_filter,
            'status': status_filter,
            'search': search_query,
        },
        'is_manager_portal': request.path.startswith('/manager/'),
    }
    
    return render(request, 'invite_codes/list.html', context)


@login_required
def create_invite_code(request):
    """Create a new invite code"""
    if not can_manage_invite_codes(request.user):
        messages.error(request, 'Access denied. You do not have permission to create invite codes.')
        return redirect('/admin/')
    
    if request.method == 'POST':
        try:
            with transaction.atomic():
                # Get form data
                task_group = request.POST.get('task_group', TaskGroup.GENERAL)
                role = request.POST.get('role', UserRole.STAFF)
                max_uses = int(request.POST.get('max_uses', 1))
                expires_days = request.POST.get('expires_days', '')
                notes = request.POST.get('notes', '')
                
                # Validate role and task group
                if role not in [choice[0] for choice in UserRole.choices]:
                    messages.error(request, 'Invalid role selected.')
                    return render(request, 'invite_codes/create.html', {
                        'role_choices': UserRole.choices,
                        'task_group_choices': TaskGroup.choices,
                        'is_manager_portal': request.path.startswith('/manager/'),
                    })
                
                if task_group not in [choice[0] for choice in TaskGroup.choices]:
                    messages.error(request, 'Invalid task group selected.')
                    return render(request, 'invite_codes/create.html', {
                        'role_choices': UserRole.choices,
                        'task_group_choices': TaskGroup.choices,
                        'is_manager_portal': request.path.startswith('/manager/'),
                    })
                
                # Calculate expiration
                expires_at = None
                if expires_days and expires_days.isdigit():
                    expires_at = timezone.now() + timezone.timedelta(days=int(expires_days))
                
                # Generate unique code
                code = generate_invite_code()
                while InviteCode.objects.filter(code=code).exists():
                    code = generate_invite_code()
                
                # Create invite code
                invite = InviteCode.objects.create(
                    code=code,
                    created_by=request.user,
                    task_group=task_group,
                    role=role,
                    max_uses=max_uses,
                    expires_at=expires_at,
                    notes=notes
                )
                
                logger.info(f"Invite code created: {code} by {request.user.username} for role {role}")
                messages.success(request, f'Invite code created successfully: {code}')
                
                # Redirect based on portal
                if request.path.startswith('/manager/'):
                    return redirect('/manager/invite-codes/')
                else:
                    return redirect('/admin/invite-codes/')
                
        except Exception as e:
            logger.error(f"Error creating invite code: {e}")
            messages.error(request, f'Error creating invite code: {str(e)}')
    
    context = {
        'role_choices': UserRole.choices,
        'task_group_choices': TaskGroup.choices,
        'is_manager_portal': request.path.startswith('/manager/'),
    }
    
    return render(request, 'invite_codes/create.html', context)


@login_required
def edit_invite_code(request, code_id):
    """Edit an existing invite code"""
    if not can_manage_invite_codes(request.user):
        messages.error(request, 'Access denied. You do not have permission to edit invite codes.')
        return redirect('/admin/')
    
    invite_code = get_object_or_404(InviteCode, id=code_id)
    
    # Check if code has been used
    if invite_code.used_count > 0:
        messages.warning(request, 'This invite code has already been used and cannot be edited.')
        if request.path.startswith('/manager/'):
            return redirect('/manager/invite-codes/')
        else:
            return redirect('/admin/invite-codes/')
    
    if request.method == 'POST':
        try:
            with transaction.atomic():
                # Update fields
                invite_code.task_group = request.POST.get('task_group', invite_code.task_group)
                invite_code.role = request.POST.get('role', invite_code.role)
                invite_code.max_uses = int(request.POST.get('max_uses', invite_code.max_uses))
                invite_code.notes = request.POST.get('notes', invite_code.notes)
                
                # Handle expiration
                expires_days = request.POST.get('expires_days', '')
                if expires_days == '':
                    invite_code.expires_at = None
                elif expires_days.isdigit():
                    invite_code.expires_at = timezone.now() + timezone.timedelta(days=int(expires_days))
                
                invite_code.save()
                
                logger.info(f"Invite code updated: {invite_code.code} by {request.user.username}")
                messages.success(request, f'Invite code {invite_code.code} updated successfully.')
                
                # Redirect based on portal
                if request.path.startswith('/manager/'):
                    return redirect('/manager/invite-codes/')
                else:
                    return redirect('/admin/invite-codes/')
                
        except Exception as e:
            logger.error(f"Error updating invite code: {e}")
            messages.error(request, f'Error updating invite code: {str(e)}')
    
    context = {
        'invite_code': invite_code,
        'role_choices': UserRole.choices,
        'task_group_choices': TaskGroup.choices,
        'is_manager_portal': request.path.startswith('/manager/'),
    }
    
    return render(request, 'admin/edit_invite_code.html', context)


@login_required
def revoke_invite_code(request, code_id):
    """Revoke an invite code (deactivate it)"""
    if not can_manage_invite_codes(request.user):
        messages.error(request, 'Access denied. You do not have permission to revoke invite codes.')
        return redirect('/admin/')
    
    invite_code = get_object_or_404(InviteCode, id=code_id)
    
    if request.method == 'POST':
        try:
            invite_code.is_active = False
            invite_code.save()
            
            logger.info(f"Invite code revoked: {invite_code.code} by {request.user.username}")
            messages.success(request, f'Invite code {invite_code.code} has been revoked.')
            
        except Exception as e:
            logger.error(f"Error revoking invite code: {e}")
            messages.error(request, f'Error revoking invite code: {str(e)}')
    
    # Redirect based on portal
    if request.path.startswith('/manager/'):
        return redirect('/manager/invite-codes/')
    else:
        return redirect('/admin/invite-codes/')


@login_required
def reactivate_invite_code(request, code_id):
    """Reactivate a revoked invite code"""
    if not can_manage_invite_codes(request.user):
        messages.error(request, 'Access denied. You do not have permission to reactivate invite codes.')
        return redirect('/admin/')
    
    invite_code = get_object_or_404(InviteCode, id=code_id)
    
    if request.method == 'POST':
        try:
            invite_code.is_active = True
            invite_code.save()
            
            logger.info(f"Invite code reactivated: {invite_code.code} by {request.user.username}")
            messages.success(request, f'Invite code {invite_code.code} has been reactivated.')
            
        except Exception as e:
            logger.error(f"Error reactivating invite code: {e}")
            messages.error(request, f'Error reactivating invite code: {str(e)}')
    
    # Redirect based on portal
    if request.path.startswith('/manager/'):
        return redirect('/manager/invite-codes/')
    else:
        return redirect('/admin/invite-codes/')


@login_required
def delete_invite_code(request, code_id):
    """Delete an invite code permanently"""
    if not can_manage_invite_codes(request.user):
        messages.error(request, 'Access denied. You do not have permission to delete invite codes.')
        return redirect('/admin/')
    
    invite_code = get_object_or_404(InviteCode, id=code_id)
    
    # Check if code has been used
    if invite_code.used_count > 0:
        messages.error(request, 'Cannot delete invite code that has been used.')
        if request.path.startswith('/manager/'):
            return redirect('/manager/invite-codes/')
        else:
            return redirect('/admin/invite-codes/')
    
    if request.method == 'POST':
        try:
            code = invite_code.code
            invite_code.delete()
            
            logger.info(f"Invite code deleted: {code} by {request.user.username}")
            messages.success(request, f'Invite code {code} has been deleted.')
            
        except Exception as e:
            logger.error(f"Error deleting invite code: {e}")
            messages.error(request, f'Error deleting invite code: {str(e)}')
    
    # Redirect based on portal
    if request.path.startswith('/manager/'):
        return redirect('/manager/invite-codes/')
    else:
        return redirect('/admin/invite-codes/')


@login_required
def invite_code_detail(request, code_id):
    """View detailed information about an invite code"""
    if not can_manage_invite_codes(request.user):
        messages.error(request, 'Access denied. You do not have permission to view invite code details.')
        return redirect('/admin/')
    
    invite_code = get_object_or_404(InviteCode, id=code_id)
    
    context = {
        'invite_code': invite_code,
        'is_manager_portal': request.path.startswith('/manager/'),
    }
    
    return render(request, 'admin/invite_code_detail.html', context)


# API Views for AJAX operations
@api_view(['POST'])
@permission_classes([IsAuthenticated])
def create_invite_code_api(request):
    """API endpoint for creating invite codes via AJAX"""
    if not can_manage_invite_codes(request.user):
        return Response({'error': 'Access denied'}, status=status.HTTP_403_FORBIDDEN)
    
    try:
        with transaction.atomic():
            # Get data from request
            task_group = request.data.get('task_group', TaskGroup.GENERAL)
            role = request.data.get('role', UserRole.STAFF)
            max_uses = int(request.data.get('max_uses', 1))
            expires_days = request.data.get('expires_days', '')
            notes = request.data.get('notes', '')
            
            # Validate inputs
            if role not in [choice[0] for choice in UserRole.choices]:
                return Response({'error': 'Invalid role'}, status=status.HTTP_400_BAD_REQUEST)
            
            if task_group not in [choice[0] for choice in TaskGroup.choices]:
                return Response({'error': 'Invalid task group'}, status=status.HTTP_400_BAD_REQUEST)
            
            # Calculate expiration
            expires_at = None
            if expires_days and str(expires_days).isdigit():
                expires_at = timezone.now() + timezone.timedelta(days=int(expires_days))
            
            # Generate unique code
            code = generate_invite_code()
            while InviteCode.objects.filter(code=code).exists():
                code = generate_invite_code()
            
            # Create invite code
            invite = InviteCode.objects.create(
                code=code,
                created_by=request.user,
                task_group=task_group,
                role=role,
                max_uses=max_uses,
                expires_at=expires_at,
                notes=notes
            )
            
            logger.info(f"Invite code created via API: {code} by {request.user.username}")
            
            # Return serialized data
            serializer = InviteCodeSerializer(invite)
            return Response({
                'success': True,
                'message': f'Invite code created: {code}',
                'data': serializer.data
            }, status=status.HTTP_201_CREATED)
            
    except Exception as e:
        logger.error(f"Error creating invite code via API: {e}")
        return Response({'error': str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def revoke_invite_code_api(request, code_id):
    """API endpoint for revoking invite codes via AJAX"""
    if not can_manage_invite_codes(request.user):
        return Response({'error': 'Access denied'}, status=status.HTTP_403_FORBIDDEN)
    
    try:
        invite_code = InviteCode.objects.get(id=code_id)
        invite_code.is_active = False
        invite_code.save()
        
        logger.info(f"Invite code revoked via API: {invite_code.code} by {request.user.username}")
        
        return Response({
            'success': True,
            'message': f'Invite code {invite_code.code} has been revoked'
        })
        
    except InviteCode.DoesNotExist:
        return Response({'error': 'Invite code not found'}, status=status.HTTP_404_NOT_FOUND)
    except Exception as e:
        logger.error(f"Error revoking invite code via API: {e}")
        return Response({'error': str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
