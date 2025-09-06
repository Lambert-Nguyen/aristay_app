# 🔐 JWT Authentication Implementation Proposal

## Overview
Upgrade from basic TokenAuthentication to JWT with refresh tokens for enhanced security and session management.

## Implementation Plan

### Phase 1: Install JWT Dependencies
```bash
pip install djangorestframework-simplejwt
pip install cryptography  # For enhanced JWT security
```

### Phase 2: Settings Configuration
```python
# backend/settings.py
from datetime import timedelta

INSTALLED_APPS = [
    # ... existing apps
    'rest_framework_simplejwt',
]

REST_FRAMEWORK = {
    'DEFAULT_AUTHENTICATION_CLASSES': [
        'rest_framework_simplejwt.authentication.JWTAuthentication',
        'rest_framework.authentication.SessionAuthentication',  # Keep for admin
    ],
    'DEFAULT_PERMISSION_CLASSES': [
        'rest_framework.permissions.IsAuthenticatedOrReadOnly',
    ],
}

SIMPLE_JWT = {
    'ACCESS_TOKEN_LIFETIME': timedelta(minutes=60),
    'REFRESH_TOKEN_LIFETIME': timedelta(days=7),
    'ROTATE_REFRESH_TOKENS': True,
    'BLACKLIST_AFTER_ROTATION': True,
    'UPDATE_LAST_LOGIN': True,
    
    'ALGORITHM': 'HS256',
    'SIGNING_KEY': SECRET_KEY,
    'VERIFYING_KEY': None,
    'AUDIENCE': None,
    'ISSUER': 'aristay-app',
    'JSON_ENCODER': None,
    'JWK_URL': None,
    'LEEWAY': 0,
    
    'AUTH_HEADER_TYPES': ('Bearer',),
    'AUTH_HEADER_NAME': 'HTTP_AUTHORIZATION',
    'USER_ID_FIELD': 'id',
    'USER_ID_CLAIM': 'user_id',
    'USER_AUTHENTICATION_RULE': 'rest_framework_simplejwt.authentication.default_user_authentication_rule',
    
    'AUTH_TOKEN_CLASSES': ('rest_framework_simplejwt.tokens.AccessToken',),
    'TOKEN_TYPE_CLAIM': 'token_type',
    'TOKEN_USER_CLASS': 'rest_framework_simplejwt.models.TokenUser',
    
    'JTI_CLAIM': 'jti',
    'SLIDING_TOKEN_REFRESH_EXP_CLAIM': 'refresh_exp',
    'SLIDING_TOKEN_LIFETIME': timedelta(minutes=60),
    'SLIDING_TOKEN_REFRESH_LIFETIME': timedelta(days=7),
}
```

### Phase 3: Enhanced Authentication Views
```python
# api/auth_views.py
from rest_framework_simplejwt.views import TokenObtainPairView
from rest_framework_simplejwt.serializers import TokenObtainPairSerializer
from rest_framework_simplejwt.tokens import RefreshToken
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from django.contrib.auth import authenticate
import logging

logger = logging.getLogger('api.security')

class CustomTokenObtainPairSerializer(TokenObtainPairSerializer):
    @classmethod
    def get_token(cls, user):
        token = super().get_token(user)
        
        # Add custom claims
        token['role'] = user.profile.role if hasattr(user, 'profile') else 'viewer'
        token['permissions'] = list(user.get_all_permissions())
        token['is_staff'] = user.is_staff
        token['is_superuser'] = user.is_superuser
        
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
    serializer_class = CustomTokenObtainPairSerializer

@api_view(['POST'])
@permission_classes([IsAuthenticated])
def revoke_token(request):
    """Revoke refresh token (logout)"""
    try:
        refresh_token = request.data.get('refresh')
        token = RefreshToken(refresh_token)
        token.blacklist()
        
        logger.info(
            f"Token revoked for user: {request.user.username}",
            extra={
                'security_event': 'token_revoked',
                'user_id': request.user.id,
            }
        )
        
        return Response({'message': 'Token revoked successfully'})
    except Exception as e:
        logger.warning(f"Token revocation failed: {str(e)}")
        return Response({'error': 'Invalid token'}, status=400)

@api_view(['POST'])
@permission_classes([IsAuthenticated])
def revoke_all_tokens(request):
    """Revoke all tokens for current user"""
    try:
        from rest_framework_simplejwt.token_blacklist.models import OutstandingToken
        tokens = OutstandingToken.objects.filter(user=request.user)
        for token in tokens:
            RefreshToken(token.token).blacklist()
        
        logger.info(
            f"All tokens revoked for user: {request.user.username}",
            extra={
                'security_event': 'all_tokens_revoked',
                'user_id': request.user.id,
            }
        )
        
        return Response({'message': 'All tokens revoked successfully'})
    except Exception as e:
        logger.warning(f"All tokens revocation failed: {str(e)}")
        return Response({'error': 'Revocation failed'}, status=400)
```

### Phase 4: URL Configuration
```python
# backend/urls.py
from rest_framework_simplejwt.views import (
    TokenRefreshView,
    TokenVerifyView,
)
from api.auth_views import CustomTokenObtainPairView, revoke_token, revoke_all_tokens

urlpatterns = [
    # JWT endpoints
    path('api/token/', CustomTokenObtainPairView.as_view(), name='token_obtain_pair'),
    path('api/token/refresh/', TokenRefreshView.as_view(), name='token_refresh'),
    path('api/token/verify/', TokenVerifyView.as_view(), name='token_verify'),
    path('api/token/revoke/', revoke_token, name='token_revoke'),
    path('api/token/revoke-all/', revoke_all_tokens, name='token_revoke_all'),
    
    # Keep existing endpoints for backward compatibility
    path('api-token-auth/', CustomTokenObtainPairView.as_view()),
]
```

## Security Benefits

### 1. **Token Expiration**
- Access tokens expire in 60 minutes
- Refresh tokens expire in 7 days
- Automatic rotation prevents long-term exposure

### 2. **Session Management**
- Track active sessions per user
- Revoke individual or all tokens
- Blacklist tokens on logout/password change

### 3. **Enhanced Claims**
- User role and permissions in token payload
- Reduced database queries for authorization
- Stateless authentication

### 4. **Audit Logging**
- All token operations logged
- Failed authentication attempts tracked
- Token revocation events recorded

## Migration Strategy

### Backward Compatibility
```python
# Maintain both authentication methods during migration
REST_FRAMEWORK = {
    'DEFAULT_AUTHENTICATION_CLASSES': [
        'rest_framework_simplejwt.authentication.JWTAuthentication',
        'rest_framework.authentication.TokenAuthentication',  # Legacy support
        'rest_framework.authentication.SessionAuthentication',
    ],
}
```

### Mobile App Updates
```dart
// Update Flutter app token handling
class AuthService {
  static const String accessTokenKey = 'access_token';
  static const String refreshTokenKey = 'refresh_token';
  
  Future<void> refreshTokenIfNeeded() async {
    final accessToken = await storage.read(key: accessTokenKey);
    if (_isTokenExpired(accessToken)) {
      await _refreshToken();
    }
  }
  
  Future<void> _refreshToken() async {
    final refreshToken = await storage.read(key: refreshTokenKey);
    // Call refresh endpoint and update tokens
  }
}
```

## Production Considerations

### 1. **Environment Variables**
```bash
# .env
JWT_SECRET_KEY=your-super-secure-secret-key
JWT_ACCESS_TOKEN_LIFETIME=3600  # 1 hour
JWT_REFRESH_TOKEN_LIFETIME=604800  # 7 days
```

### 2. **Monitoring**
- Track token usage patterns
- Monitor failed authentication attempts
- Alert on suspicious token activity

### 3. **Rate Limiting Enhancement**
```python
SIMPLE_JWT_RATE_LIMITS = {
    'token_obtain': '5/minute',
    'token_refresh': '10/minute',
    'password_reset': '3/hour',
}
```

## Timeline
- **Week 1**: Install dependencies, configure settings
- **Week 2**: Implement custom views and test endpoints
- **Week 3**: Update mobile app authentication
- **Week 4**: Production deployment and monitoring setup
