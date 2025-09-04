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
    path('api-token-auth/', obtain_auth_token, name='api_token_auth'),  # Add this line
    # Unified login system
    path('login/', UnifiedLoginView.as_view(), name='unified_login'),
    path('logout/', logout_view, name='unified_logout'),
    path('', UnifiedLoginView.as_view(), name='home'),  # Root URL redirects to login
    # support password‐reset confirm, complete, etc.
    path('api/auth/', include('django.contrib.auth.urls')),
]

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
