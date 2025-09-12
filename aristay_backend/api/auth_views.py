"""
Unified authentication views for AriStay backend
Handles role-based routing for Admin and Manager users
"""

import logging
from django.contrib.auth import authenticate, login
from django.contrib.auth.views import LoginView
from django.shortcuts import redirect
from django.urls import reverse_lazy
from django.contrib import messages
from django.http import HttpResponseRedirect
from django.conf import settings
from drf_spectacular.utils import extend_schema_serializer, extend_schema, inline_serializer
from rest_framework import serializers

logger = logging.getLogger('api.security')


class UnifiedLoginView(LoginView):
    """
    Unified login view that routes all authenticated users to the home screen:
    - All users → Home screen (/api/portal/) with role-based navigation options
    - Users can then choose to go to Admin, Manager, Properties, or Tasks
    - Provides unified navigation experience across all user types
    """
    template_name = 'auth/unified_login.html'
    redirect_authenticated_user = True
    
    def get_success_url(self):
        """
        Determine redirect URL based on user role and permissions
        """
        user = self.request.user
        next_url = self.request.GET.get('next')
        
        # Log the login attempt
        logger.info(
            f"User login successful: {user.username}",
            extra={
                'user_id': user.id,
                'username': user.username,
                'is_superuser': user.is_superuser,
                'is_staff': user.is_staff,
                'remote_addr': self.request.META.get('REMOTE_ADDR', 'unknown'),
                'user_agent': self.request.META.get('HTTP_USER_AGENT', 'unknown'),
            }
        )
        
        # Check if user has a profile with role information
        try:
            profile = user.profile
            user_role = profile.role if hasattr(profile, 'role') else None
        except:
            profile = None
            user_role = None
        
        # Priority 1: Honor explicit next parameter if it's a valid internal URL
        if next_url and self._is_safe_url(next_url):
            return next_url
        
        # Priority 2: Check if user has manager portal access and redirect to manager admin
        try:
            if (hasattr(user, 'profile') and user.profile and 
                user.profile.has_permission('manager_portal_access')):
                return '/manager/'
        except:
            pass
        
        # Priority 3: Route ALL other authenticated users to portal home screen
        # The portal will handle role-based access control and navigation
        return '/api/portal/'
    
    def _is_safe_url(self, url):
        """
        Check if the redirect URL is safe (internal to our application)
        """
        if not url:
            return False
        
        # Allow only internal URLs
        allowed_paths = ['/admin/', '/manager/', '/api/']
        return any(url.startswith(path) for path in allowed_paths)
    
    def form_valid(self, form):
        """
        Log successful login and perform additional security checks
        """
        response = super().form_valid(form)
        
        # Additional security logging
        user = form.get_user()
        logger.info(
            f"Authentication successful for user: {user.username}",
            extra={
                'event_type': 'login_success',
                'user_id': user.id,
                'username': user.username,
                'redirect_url': self.get_success_url(),
                'session_key': self.request.session.session_key,
            }
        )
        
        return response
    
    def form_invalid(self, form):
        """
        Log failed login attempts for security monitoring
        """
        username = form.cleaned_data.get('username', 'unknown')
        
        logger.warning(
            f"Authentication failed for username: {username}",
            extra={
                'event_type': 'login_failure',
                'username': username,
                'remote_addr': self.request.META.get('REMOTE_ADDR', 'unknown'),
                'user_agent': self.request.META.get('HTTP_USER_AGENT', 'unknown'),
                'form_errors': str(form.errors),
            }
        )
        
        return super().form_invalid(form)
    
    def get_context_data(self, **kwargs):
        """
        Add additional context for the template
        """
        context = super().get_context_data(**kwargs)
        context.update({
            'site_title': 'AriStay Management',
            'site_header': 'AriStay Management',
            'site_description': 'Access your management dashboards',
        })
        return context


def logout_view(request):
    """
    Custom logout view that logs the logout event and redirects to login
    """
    if request.user.is_authenticated:
        logger.info(
            f"User logout: {request.user.username}",
            extra={
                'event_type': 'logout',
                'user_id': request.user.id,
                'username': request.user.username,
                'session_key': request.session.session_key,
            }
        )
    
    from django.contrib.auth import logout
    logout(request)
    messages.success(request, "You have been successfully logged out.")
    return redirect('unified_login')


# ============================================================================
# JWT AUTHENTICATION VIEWS
# ============================================================================

from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.throttling import ScopedRateThrottle
from rest_framework_simplejwt.views import TokenObtainPairView
from rest_framework_simplejwt.serializers import TokenObtainPairSerializer
from rest_framework_simplejwt.tokens import RefreshToken
from rest_framework.decorators import api_view, permission_classes
from rest_framework.response import Response
from rest_framework import status


@extend_schema_serializer(component_name="AuthViewsTokenObtainPairRequest")
class CustomTokenObtainPairSerializer(TokenObtainPairSerializer):
    """Custom JWT serializer with additional user claims"""
    
    @classmethod
    def get_token(cls, user):
        token = super().get_token(user)
        
        # Add essential claims only (removed permissions for security and payload size)
        token['role'] = getattr(getattr(user, 'profile', None), 'role', 'viewer')
        token['is_staff'] = user.is_staff
        token['is_superuser'] = user.is_superuser
        # Note: Granular permissions should be fetched via API when needed
        
        return token
    
    def validate(self, attrs):
        data = super().validate(attrs)
        
        # Log successful authentication
        logger.info(
            f"JWT token issued for user: {self.user.username}",
            extra={
                'security_event': 'token_issued',
                'user_id': self.user.id,
                'username': self.user.username,
            }
        )
        
        return data


class CustomTokenObtainPairView(TokenObtainPairView):
    """Custom JWT token obtain view with throttling and logging"""
    permission_classes = [AllowAny]
    throttle_classes = [ScopedRateThrottle]
    throttle_scope = 'login'
    serializer_class = CustomTokenObtainPairSerializer


# Throttled refresh view to apply token_refresh rate limiting
from rest_framework_simplejwt.views import TokenRefreshView as BaseTokenRefreshView
from api.throttles import RefreshTokenJtiRateThrottle

class TokenRefreshThrottledView(BaseTokenRefreshView):
    """JWT refresh view with per-token throttling applied"""
    permission_classes = [AllowAny]  # Explicit for future-proofing
    throttle_classes = [RefreshTokenJtiRateThrottle]  # Per-refresh-token limit
    throttle_scope = 'token_refresh'


from rest_framework_simplejwt.exceptions import TokenError

@extend_schema(
    operation_id="revoke_token",
    summary="Revoke refresh token",
    request=inline_serializer(
        name="RevokeTokenRequest",
        fields={
            "refresh": serializers.CharField(required=False),
            "refresh_token": serializers.CharField(required=False),
        }
    ),
    responses={200: inline_serializer(
        name="RevokeTokenResponse",
        fields={
            "success": serializers.BooleanField(),
            "message": serializers.CharField(),
        }
    )}
)
@api_view(['POST'])
@permission_classes([IsAuthenticated])
def revoke_token(request):
    """Revoke a specific refresh token (logout)"""
    refresh_token = request.data.get('refresh') or request.data.get('refresh_token')
    if not refresh_token:
        return Response({'error': 'Refresh token required'}, status=status.HTTP_400_BAD_REQUEST)
    
    try:
        # Verify token belongs to the requesting user (security check)
        token = RefreshToken(refresh_token)
        if int(token['user_id']) != request.user.id:
            return Response({'error': 'Token does not belong to you'}, status=status.HTTP_403_FORBIDDEN)
            
        token.blacklist()
        
        logger.info(
            "Token revoked",
            extra={
                'security_event': 'token_revoked',
                'user_id': request.user.id,
            }
        )
        
        return Response({'message': 'Token revoked successfully'})
    except TokenError:
        return Response({'error': 'Invalid or expired token'}, status=status.HTTP_400_BAD_REQUEST)


@extend_schema(
    operation_id="revoke_all_tokens",
    summary="Revoke all tokens for current user",
    request=inline_serializer(name="RevokeAllTokensRequest", fields={}),
    responses={200: inline_serializer(
        name="RevokeAllTokensResponse",
        fields={
            "success": serializers.BooleanField(),
            "revoked": serializers.IntegerField(required=False),
            "message": serializers.CharField(required=False),
        }
    )}
)
@api_view(['POST'])
@permission_classes([IsAuthenticated])
def revoke_all_tokens(request):
    """Revoke all tokens for current user"""
    try:
        from rest_framework_simplejwt.token_blacklist.models import OutstandingToken, BlacklistedToken
        
        # Get all outstanding tokens for the user
        outstanding_tokens = OutstandingToken.objects.filter(user=request.user)
        token_count = outstanding_tokens.count()
        
        # Blacklist all tokens directly using BlacklistedToken
        for token_obj in outstanding_tokens:
            BlacklistedToken.objects.get_or_create(token=token_obj)
        
        logger.info(
            "All tokens revoked",
            extra={
                'security_event': 'all_tokens_revoked',
                'user_id': request.user.id,
                'count': token_count,
            }
        )
        
        return Response({'message': f'All tokens revoked ({token_count})'})
    except Exception as e:
        logger.warning(f"All tokens revocation failed: {str(e)}")
        return Response({'error': 'Revocation failed'}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
