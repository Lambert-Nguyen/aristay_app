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
    Unified login view that routes users based on their role:
    - Superusers/Staff → Admin site (/admin/)
    - Managers → Manager site (/manager/)
    - Regular users → Appropriate dashboard or error message
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
        
        # Priority 2: Route based on Django permissions (Superuser/staff)
        if user.is_superuser:
            return '/admin/'
        elif user.is_staff:
            # Staff users could be either admin or manager
            # Check profile role if available
            if user_role == 'manager':
                return '/manager/'
            else:
                return '/admin/'  # Default staff to admin
        
        # Priority 3: Route based on profile role
        if user_role == 'manager':
            return '/manager/'
        elif user_role == 'owner':
            # legacy label maps to Superuser; send to admin
            return '/admin/'
        
        # Priority 4: Default fallback
        # If user doesn't have admin/manager permissions, show an error
        try:
            messages.error(
                self.request, 
                "You don't have permission to access the admin or manager interface. "
                "Please contact your administrator if you believe this is an error."
            )
        except Exception:
            # Handle case where messages framework is not available
            pass
        
        # Logout the user since they can't access any admin interface
        from django.contrib.auth import logout
        logout(self.request)
        return reverse_lazy('unified_login')
    
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
