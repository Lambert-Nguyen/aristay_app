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
from rest_framework.authtoken.views import obtain_auth_token  # Import the token view
from django.conf import settings
from django.conf.urls.static import static
from api.managersite import manager_site
from api.auth_views import UnifiedLoginView, logout_view

# JWT Authentication imports
from rest_framework_simplejwt.views import TokenRefreshView, TokenVerifyView
from api.auth_views import CustomTokenObtainPairView, revoke_token, revoke_all_tokens
from api.auth_debug_views import WhoAmIView

# Security Dashboard imports (TODO: implement later)
# from api.security_dashboard import (
#     security_dashboard, security_events, active_sessions, 
#     terminate_session, security_analytics
# )

# Agent's Phase 2: Add audit API router
from rest_framework.routers import DefaultRouter
from api.audit_views import AuditEventViewSet

# Create router for audit API
audit_router = DefaultRouter()
audit_router.register(r'audit-events', AuditEventViewSet, basename='auditevent')

urlpatterns = [
    path('admin/', admin.site.urls),
    path('manager/', include((manager_site.urls[0], 'admin'), namespace='manager_admin')),   # Manager console
    path('api/', include('api.urls')),
    path('api/', include(audit_router.urls)),  # Add audit API endpoints
    
    # JWT Authentication endpoints
    path('api/token/', CustomTokenObtainPairView.as_view(), name='token_obtain_pair'),
    path('api/token/refresh/', TokenRefreshView.as_view(), name='token_refresh'),
    path('api/token/verify/', TokenVerifyView.as_view(), name='token_verify'),
    path('api/token/revoke/', revoke_token, name='token_revoke'),
    path('api/token/revoke-all/', revoke_all_tokens, name='token_revoke_all'),
    
    # JWT Debug endpoint
    path('api/test-auth/', WhoAmIView.as_view(), name='test-auth'),
    
    # Security Dashboard endpoints (TODO: implement later)
    # path('api/admin/security/', security_dashboard, name='security_dashboard'),
    # path('api/admin/security/events/', security_events, name='security_events'),
    # path('api/admin/security/sessions/', active_sessions, name='active_sessions'),
    # path('api/admin/security/sessions/<int:session_id>/terminate/', terminate_session, name='terminate_session'),
    # path('api/admin/security/analytics/', security_analytics, name='security_analytics'),
    
    # Legacy token auth (backward compatibility)
    path('api-token-auth/', CustomTokenObtainPairView.as_view(), name='api_token_auth'),
    
    # Unified login system
    path('login/', UnifiedLoginView.as_view(), name='unified_login'),
    path('logout/', logout_view, name='unified_logout'),
    path('', UnifiedLoginView.as_view(), name='home'),  # Root URL redirects to login
    
    # Password reset endpoints
    path('api/auth/', include('django.contrib.auth.urls')),
]

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
