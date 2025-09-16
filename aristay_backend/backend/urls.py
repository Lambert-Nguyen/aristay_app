"""
URL configuration for backend project.

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/5.1/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  path('', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  path('', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.urls import include, path
    2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))
"""

from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static
from api.managersite import manager_site
from api.invite_code_views import invite_code_list, create_invite_code, edit_invite_code, revoke_invite_code, reactivate_invite_code, delete_invite_code, invite_code_detail
from api.registration_views import registration_view
from api.auth_views import UnifiedLoginView, logout_view

# JWT Authentication imports
from rest_framework_simplejwt.views import TokenVerifyView
from api.jwt_auth_views import SecureTokenObtainPairView, SecureTokenRefreshView
from api.auth_views import CustomTokenObtainPairView, TokenRefreshThrottledView, revoke_token, revoke_all_tokens
from api.auth_debug_views import WhoAmIView

# OpenAPI documentation imports
from drf_spectacular.views import SpectacularAPIView, SpectacularSwaggerView, SpectacularRedocView

# Deprecation wrapper for legacy route
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_http_methods

@csrf_exempt
@require_http_methods(["POST"])
def deprecated_token_auth(request, *args, **kwargs):
    """Legacy token auth endpoint with deprecation headers"""
    response = CustomTokenObtainPairView.as_view()(request, *args, **kwargs)
    if hasattr(response, '__setitem__'):  # HttpResponse-like object
        response['Deprecation'] = 'true'
        response['Link'] = '</api/token/>; rel="successor-version"'
        response['Warning'] = f'299 - "Deprecated endpoint. Use /api/token/ instead. Removal planned for {getattr(settings, "DEPRECATED_TOKEN_AUTH_REMOVAL_DATE", "Q2 2026")}."'
    return response

# Security Dashboard imports
from api.security_dashboard import (
    security_dashboard, security_events, active_sessions, 
    terminate_session, security_analytics
)

# Custom Password Reset imports
from api.password_reset_views import (
    PasswordResetView, PasswordResetDoneView, 
    PasswordResetConfirmView, PasswordResetCompleteView
)

urlpatterns = [
    path('admin/', admin.site.urls),
    path('admin/invite-codes/', invite_code_list, name='admin_invite_codes'),
    path('admin/create-invite-code/', create_invite_code, name='admin_create_invite_code'),
    path('admin/invite-codes/<int:code_id>/', invite_code_detail, name='admin_invite_code_detail'),
    path('admin/invite-codes/<int:code_id>/edit/', edit_invite_code, name='admin_edit_invite_code'),
    path('admin/invite-codes/<int:code_id>/revoke/', revoke_invite_code, name='admin_revoke_invite_code'),
    path('admin/invite-codes/<int:code_id>/reactivate/', reactivate_invite_code, name='admin_reactivate_invite_code'),
    path('admin/invite-codes/<int:code_id>/delete/', delete_invite_code, name='admin_delete_invite_code'),
    path('manager/', include((manager_site.urls[0], 'admin'), namespace='manager_admin')),   # Manager console
    path('api/', include('api.urls')),
    
    # OpenAPI Documentation endpoints
    path('schema/', SpectacularAPIView.as_view(), name='schema'),
    path('docs/', SpectacularSwaggerView.as_view(url_name='schema'), name='swagger-ui'),
    path('redoc/', SpectacularRedocView.as_view(url_name='schema'), name='redoc'),
    
    # JWT Authentication endpoints
    path('api/token/', SecureTokenObtainPairView.as_view(), name='token_obtain_pair'),
    path('api/token/refresh/', SecureTokenRefreshView.as_view(), name='token_refresh'),
    path('api/token/verify/', TokenVerifyView.as_view(), name='token_verify'),
    path('api/token/revoke/', revoke_token, name='token_revoke'),
    path('api/token/revoke-all/', revoke_all_tokens, name='token_revoke_all'),
    
    # JWT Debug endpoint
    path('api/test-auth/', WhoAmIView.as_view(), name='test-auth'),
    
    # Security Dashboard endpoints
    path('api/admin/security/', security_dashboard, name='security_dashboard'),
    path('api/admin/security/events/', security_events, name='security_events'),
    path('api/admin/security/sessions/', active_sessions, name='active_sessions'),
    path('api/admin/security/sessions/<int:session_id>/terminate/', terminate_session, name='terminate_session'),
    path('api/admin/security/analytics/', security_analytics, name='security_analytics'),
    
    # Legacy token auth - backward compatibility with deprecation headers
    path('api-token-auth/', deprecated_token_auth, name='api_token_auth_legacy'),  # DEPRECATED - removal Q2 2026
    path('jwt-token-auth/', CustomTokenObtainPairView.as_view(), name='jwt_token_auth'),
    
    # Unified login system
    path('login/', UnifiedLoginView.as_view(), name='unified_login'),
    path('logout/', logout_view, name='unified_logout'),
    path('', UnifiedLoginView.as_view(), name='home'),  # Root URL redirects to login
    
    # User registration (HTML form)
    path('register/', registration_view, name='register'),
    
    # Password reset endpoints - using custom views with audit logging
    path('api/auth/password_reset/', 
         PasswordResetView.as_view(), 
         name='password_reset'),
    path('api/auth/password_reset/done/', 
         PasswordResetDoneView.as_view(), 
         name='password_reset_done'),
    path('api/auth/reset/<uidb64>/<token>/', 
         PasswordResetConfirmView.as_view(), 
         name='password_reset_confirm'),
    path('api/auth/reset/done/', 
         PasswordResetCompleteView.as_view(), 
         name='password_reset_complete'),
]

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
