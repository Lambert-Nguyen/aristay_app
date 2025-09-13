# api/jwt_auth_views.py
"""
Enhanced JWT Authentication Views with Security Logging
"""

import logging
from datetime import datetime
from django.contrib.auth import authenticate
from django.contrib.auth.models import User
from django.utils import timezone
from django.utils.decorators import method_decorator
from django.views.decorators.cache import never_cache
from django.views.decorators.csrf import csrf_exempt
from django_ratelimit.decorators import ratelimit
from rest_framework import status
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework_simplejwt.views import TokenObtainPairView, TokenRefreshView
from rest_framework_simplejwt.serializers import TokenObtainPairSerializer
from rest_framework_simplejwt.tokens import RefreshToken
from rest_framework_simplejwt.token_blacklist.models import OutstandingToken
from rest_framework_simplejwt.exceptions import TokenError, InvalidToken
from drf_spectacular.utils import extend_schema_serializer

from .security_models import SecurityEvent, UserSession, SuspiciousActivity
from .throttles import RefreshTokenJtiRateThrottle

logger = logging.getLogger('api.security')


@extend_schema_serializer(component_name="JwtAuthViewsTokenObtainPairRequest")
class CustomTokenObtainPairSerializer(TokenObtainPairSerializer):
    """Enhanced JWT serializer with custom claims and security logging"""
    
    @classmethod
    def get_token(cls, user):
        token = super().get_token(user)
        
        # Add custom claims
        token['role'] = getattr(user.profile, 'role', 'viewer') if hasattr(user, 'profile') else 'viewer'
        token['permissions'] = list(user.profile.get_all_permissions()) if hasattr(user, 'profile') else []
        # Removed is_staff - using Profile.role instead
        token['is_superuser'] = user.is_superuser
        token['username'] = user.username
        token['email'] = user.email
        
        return token
    
    def validate(self, attrs):
        data = super().validate(attrs)
        
        # Add additional user info to response
        data['user'] = {
            'id': self.user.id,
            'username': self.user.username,
            'email': self.user.email,
            'role': getattr(self.user.profile, 'role', 'viewer') if hasattr(self.user, 'profile') else 'viewer',
            'is_superuser': self.user.is_superuser,
        }
        
        return data


@method_decorator([
    ratelimit(key='ip', rate='5/m', method='POST'),
    csrf_exempt,
    never_cache,
], name='dispatch')
class SecureTokenObtainPairView(TokenObtainPairView):
    """Secure token obtain with enhanced logging and rate limiting"""
    serializer_class = CustomTokenObtainPairSerializer
    throttle_scope = 'login'
    
    def post(self, request, *args, **kwargs):
        # Log attempt
        SecurityEvent.log_event('login_attempt', request=request)
        
        try:
            response = super().post(request, *args, **kwargs)
            
            # If successful, log success and create session
            if response.status_code == 200:
                username = request.data.get('username')
                try:
                    user = User.objects.get(username=username)
                    self._log_success(request, user)
                    self._create_session_record(request, user, response.data)
                except User.DoesNotExist:
                    pass
            else:
                self._log_failure(request, response)
            
            return response
            
        except Exception as e:
            self._log_failure(request, None, str(e))
            raise
    
    def _log_success(self, request, user):
        """Log successful authentication"""
        SecurityEvent.log_event(
            'login_success',
            request=request,
            user=user,
            severity='low'
        )
        logger.info(
            f"JWT token issued for user: {user.username}",
            extra={
                'security_event': 'token_issued',
                'user_id': user.id,
                'username': user.username,
                'ip_address': SecurityEvent._get_client_ip(request),
            }
        )
    
    def _log_failure(self, request, response, error=None):
        """Log failed authentication"""
        SecurityEvent.log_event(
            'login_failure',
            request=request,
            severity='medium',
            error=error,
            status_code=response.status_code if response else None
        )
        
        # Track suspicious activity
        ip_address = SecurityEvent._get_client_ip(request)
        suspicious, created = SuspiciousActivity.objects.get_or_create(
            ip_address=ip_address,
            activity_type='failed_login',
            defaults={'count': 1}
        )
        if not created:
            suspicious.increment()
    
    def _create_session_record(self, request, user, token_data):
        """Create session record for tracking"""
        # Extract JWT ID from token
        jwt_jti = ''
        try:
            access_token = token_data.get('access')
            if access_token:
                from rest_framework_simplejwt.tokens import UntypedToken
                token = UntypedToken(access_token)
                jwt_jti = str(token.get('jti', ''))
        except:
            pass
        
        UserSession.objects.create(
            user=user,
            session_key=f"jwt_{timezone.now().timestamp()}",
            ip_address=SecurityEvent._get_client_ip(request),
            user_agent=request.META.get('HTTP_USER_AGENT', ''),
            device_type=self._detect_device_type(request),
            jwt_jti=jwt_jti
        )
    
    def _detect_device_type(self, request):
        """Detect device type from user agent"""
        user_agent = request.META.get('HTTP_USER_AGENT', '').lower()
        
        if 'mobile' in user_agent or 'android' in user_agent or 'iphone' in user_agent:
            return 'mobile'
        elif 'tablet' in user_agent or 'ipad' in user_agent:
            return 'tablet'
        elif 'postman' in user_agent or 'insomnia' in user_agent:
            return 'api_client'
        else:
            return 'desktop'


@method_decorator([
    ratelimit(key='user', rate='10/m', method='POST'),
    never_cache,
], name='dispatch')
class SecureTokenRefreshView(TokenRefreshView):
    """Secure token refresh with logging"""
    throttle_classes = [RefreshTokenJtiRateThrottle]
    
    def post(self, request, *args, **kwargs):
        try:
            response = super().post(request, *args, **kwargs)
            
            if response.status_code == 200:
                SecurityEvent.log_event(
                    'token_refreshed',
                    request=request,
                    severity='low'
                )
            
            return response
        except TokenError as e:
            SecurityEvent.log_event(
                'token_refresh_failed',
                request=request,
                severity='medium',
                error=str(e)
            )
            raise


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def revoke_token(request):
    """Revoke refresh token (logout)"""
    try:
        refresh_token = request.data.get('refresh')
        if not refresh_token:
            return Response({'error': 'Refresh token required'}, status=400)
        
        token = RefreshToken(refresh_token)
        token.blacklist()
        
        # Deactivate session
        try:
            jwt_jti = str(token.get('jti', ''))
            if jwt_jti:
                sessions = UserSession.objects.filter(
                    user=request.user,
                    jwt_jti=jwt_jti,
                    is_active=True
                )
                sessions.update(is_active=False)
        except:
            pass
        
        SecurityEvent.log_event(
            'token_revoked',
            request=request,
            user=request.user,
            severity='low'
        )
        
        logger.info(
            f"Token revoked for user: {request.user.username}",
            extra={
                'security_event': 'token_revoked',
                'user_id': request.user.id,
            }
        )
        
        return Response({'message': 'Token revoked successfully'})
    except TokenError as e:
        SecurityEvent.log_event(
            'token_revocation_failed',
            request=request,
            severity='medium',
            error=str(e)
        )
        logger.warning(f"Token revocation failed: {str(e)}")
        return Response({'error': 'Invalid token'}, status=400)


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def revoke_all_tokens(request):
    """Revoke all tokens for current user"""
    try:
        # Blacklist all outstanding tokens
        tokens = OutstandingToken.objects.filter(user=request.user)
        for token_record in tokens:
            try:
                token = RefreshToken(token_record.token)
                token.blacklist()
            except TokenError:
                continue  # Token might already be blacklisted
        
        # Deactivate all sessions
        UserSession.objects.filter(user=request.user, is_active=True).update(is_active=False)
        
        SecurityEvent.log_event(
            'all_tokens_revoked',
            request=request,
            user=request.user,
            severity='medium',
            count=tokens.count()
        )
        
        logger.info(
            f"All tokens revoked for user: {request.user.username}",
            extra={
                'security_event': 'all_tokens_revoked',
                'user_id': request.user.id,
                'token_count': tokens.count(),
            }
        )
        
        return Response({'message': f'All tokens revoked successfully ({tokens.count()} tokens)'})
    except Exception as e:
        SecurityEvent.log_event(
            'token_revocation_failed',
            request=request,
            severity='high',
            error=str(e)
        )
        logger.warning(f"All tokens revocation failed: {str(e)}")
        return Response({'error': 'Revocation failed'}, status=500)


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def user_sessions(request):
    """Get user's active sessions"""
    sessions = UserSession.objects.filter(
        user=request.user,
        is_active=True
    ).order_by('-last_activity')[:10]
    
    sessions_data = []
    for session in sessions:
        sessions_data.append({
            'id': session.id,
            'device_type': session.device_type,
            'ip_address': session.ip_address,
            'location': session.location,
            'created_at': session.created_at,
            'last_activity': session.last_activity,
            'is_current': session.jwt_jti and request.auth and hasattr(request.auth, 'get') and session.jwt_jti == str(request.auth.get('jti', ''))
        })
    
    return Response({'sessions': sessions_data})


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def revoke_session(request, session_id):
    """Revoke specific session"""
    try:
        session = UserSession.objects.get(
            id=session_id,
            user=request.user,
            is_active=True
        )
        
        # Try to blacklist the specific token
        if session.jwt_jti:
            try:
                tokens = OutstandingToken.objects.filter(
                    user=request.user,
                    jti=session.jwt_jti
                )
                for token_record in tokens:
                    token = RefreshToken(token_record.token)
                    token.blacklist()
            except:
                pass
        
        session.deactivate()
        
        SecurityEvent.log_event(
            'session_revoked',
            request=request,
            user=request.user,
            severity='low',
            session_id=session_id
        )
        
        return Response({'message': 'Session revoked successfully'})
    except UserSession.DoesNotExist:
        return Response({'error': 'Session not found'}, status=404)
    except Exception as e:
        return Response({'error': 'Failed to revoke session'}, status=500)
