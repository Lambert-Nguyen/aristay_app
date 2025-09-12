"""
User registration views with invite code system
"""
import secrets
import string
from django.shortcuts import render, redirect
from django.contrib.auth import login
from django.contrib.auth.models import User
from django.contrib import messages
from django.utils import timezone
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_http_methods
from django.http import JsonResponse
from django.db import transaction
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import AllowAny
from rest_framework.response import Response
from rest_framework import status
from .models import InviteCode, Profile
from .serializers import UserRegistrationSerializer, InviteCodeValidationSerializer
import logging

logger = logging.getLogger(__name__)


def generate_invite_code(length=8):
    """Generate a secure random invite code"""
    alphabet = string.ascii_uppercase + string.digits
    return ''.join(secrets.choice(alphabet) for _ in range(length))


def registration_view(request):
    """User registration page with invite code validation"""
    if request.method == 'POST':
        invite_code = request.POST.get('invite_code', '').strip().upper()
        username = request.POST.get('username', '').strip()
        email = request.POST.get('email', '').strip()
        password = request.POST.get('password', '')
        password_confirm = request.POST.get('password_confirm', '')
        first_name = request.POST.get('first_name', '').strip()
        last_name = request.POST.get('last_name', '').strip()
        
        # Basic validation
        errors = []
        
        if not invite_code:
            errors.append('Invite code is required')
        if not username:
            errors.append('Username is required')
        if not email:
            errors.append('Email is required')
        if not password:
            errors.append('Password is required')
        if password != password_confirm:
            errors.append('Passwords do not match')
        if len(password) < 8:
            errors.append('Password must be at least 8 characters long')
        
        if not errors:
            try:
                # Validate invite code
                invite = InviteCode.objects.get(code=invite_code)
                if not invite.is_usable:
                    if invite.is_expired:
                        errors.append('This invite code has expired')
                    elif not invite.is_active:
                        errors.append('This invite code is no longer active')
                    else:
                        errors.append('This invite code has reached its usage limit')
                elif User.objects.filter(username=username).exists():
                    errors.append('Username already exists')
                elif User.objects.filter(email=email).exists():
                    errors.append('Email already exists')
                else:
                    # Create user and profile
                    with transaction.atomic():
                        user = User.objects.create_user(
                            username=username,
                            email=email,
                            password=password,
                            first_name=first_name,
                            last_name=last_name
                        )
                        
                        # Create profile with invite code settings
                        profile = Profile.objects.create(
                            user=user,
                            role=invite.role,
                            task_group=invite.task_group,
                        )
                        
                        # Mark invite code as used
                        invite.use_code(user)
                        
                        # Log the registration
                        logger.info(f"User {username} registered with invite code {invite_code}")
                        
                        # Auto-login the user
                        login(request, user)
                        messages.success(request, f'Welcome! You have been registered as a {invite.role}.')
                        return redirect('/api/portal/')
                        
            except InviteCode.DoesNotExist:
                errors.append('Invalid invite code')
            except Exception as e:
                logger.error(f"Registration error: {e}")
                errors.append('Registration failed. Please try again.')
        
        if errors:
            for error in errors:
                messages.error(request, error)
    
    return render(request, 'registration/register.html')


@api_view(['POST'])
@permission_classes([AllowAny])
def validate_invite_code(request):
    """API endpoint to validate invite code without registering"""
    serializer = InviteCodeValidationSerializer(data=request.data)
    if serializer.is_valid():
        code = serializer.validated_data['code']
        try:
            invite = InviteCode.objects.get(code=code)
            if invite.is_usable:
                return Response({
                    'valid': True,
                    'role': invite.role,
                    'task_group': invite.task_group,
                    'expires_at': invite.expires_at.isoformat() if invite.expires_at else None,
                    'max_uses': invite.max_uses,
                    'used_count': invite.used_count
                })
            else:
                return Response({
                    'valid': False,
                    'error': 'Code is not usable'
                })
        except InviteCode.DoesNotExist:
            return Response({
                'valid': False,
                'error': 'Invalid invite code'
            })
    else:
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


@api_view(['POST'])
@permission_classes([AllowAny])
def register_user(request):
    """API endpoint for user registration with invite code"""
    serializer = UserRegistrationSerializer(data=request.data)
    if serializer.is_valid():
        try:
            with transaction.atomic():
                # Validate invite code
                invite_code = serializer.validated_data['invite_code']
                invite = InviteCode.objects.get(code=invite_code)
                
                if not invite.is_usable:
                    return Response({
                        'error': 'Invite code is not usable'
                    }, status=status.HTTP_400_BAD_REQUEST)
                
                # Create user
                user = User.objects.create_user(
                    username=serializer.validated_data['username'],
                    email=serializer.validated_data['email'],
                    password=serializer.validated_data['password'],
                    first_name=serializer.validated_data.get('first_name', ''),
                    last_name=serializer.validated_data.get('last_name', '')
                )
                
                # Create or update profile (idempotent for tests)
                profile, _ = Profile.objects.get_or_create(user=user)
                profile.role = invite.role
                profile.task_group = invite.task_group
                profile.save()
                
                # Mark invite code as used
                invite.use_code(user)
                
                logger.info(f"User {user.username} registered via API with invite code {invite_code}")
                
                return Response({
                    'success': True,
                    'user_id': user.id,
                    'username': user.username,
                    'role': profile.role,
                    'task_group': profile.task_group
                }, status=status.HTTP_201_CREATED)
                
        except InviteCode.DoesNotExist:
            return Response({
                'error': 'Invalid invite code'
            }, status=status.HTTP_400_BAD_REQUEST)
        except Exception as e:
            logger.error(f"API registration error: {e}")
            return Response({
                'error': 'Registration failed'
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
    else:
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


# Admin views for invite code management
def admin_invite_codes(request):
    """Admin view to manage invite codes"""
    if not request.user.is_staff:
        messages.error(request, 'Access denied')
        return redirect('/admin/')
    
    invite_codes = InviteCode.objects.all()
    return render(request, 'admin/invite_codes.html', {
        'invite_codes': invite_codes
    })


def create_invite_code(request):
    """Create a new invite code"""
    if not request.user.is_staff:
        messages.error(request, 'Access denied')
        return redirect('/admin/')
    
    if request.method == 'POST':
        task_group = request.POST.get('task_group', 'general')
        role = request.POST.get('role', 'member')
        max_uses = int(request.POST.get('max_uses', 1))
        expires_days = request.POST.get('expires_days', '')
        notes = request.POST.get('notes', '')
        
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
        
        messages.success(request, f'Invite code created: {code}')
        return redirect('/admin/invite-codes/')
    
    return render(request, 'admin/create_invite_code.html')


def revoke_invite_code(request, code_id):
    """Revoke an invite code"""
    if not request.user.is_staff:
        messages.error(request, 'Access denied')
        return redirect('/admin/')
    
    try:
        invite = InviteCode.objects.get(id=code_id)
        invite.is_active = False
        invite.save()
        messages.success(request, f'Invite code {invite.code} has been revoked')
    except InviteCode.DoesNotExist:
        messages.error(request, 'Invite code not found')
    
    return redirect('/admin/invite-codes/')
