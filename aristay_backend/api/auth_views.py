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
        
        # Priority 2: Route ALL authenticated users to portal home screen
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
            'site_title': 'AriStay Login',
            'site_header': 'AriStay Administration',
            'site_description': 'Access your admin or manager dashboard',
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
