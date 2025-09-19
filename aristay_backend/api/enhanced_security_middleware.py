# api/enhanced_security_middleware.py
"""
Enhanced Security Middleware for AriStay
"""

import logging
from django.conf import settings
from django.core.cache import cache
from django.http import HttpResponseForbidden
from django.utils import timezone
from django.utils.deprecation import MiddlewareMixin

from .security_models import SecurityEvent, SuspiciousActivity

logger = logging.getLogger('api.security')


class EnhancedSecurityMiddleware(MiddlewareMixin):
    """Enhanced authentication middleware with security logging and threat detection"""
    
    def __init__(self, get_response):
        self.get_response = get_response
        self.security_logger = logging.getLogger('api.security')
        super().__init__(get_response)
    
    def __call__(self, request):
        # Pre-process security checks
        blocked = self._check_blocked_ip(request)
        if blocked:
            return blocked
        
        self._log_request(request)
        self._check_suspicious_patterns(request)
        
        response = self.get_response(request)
        
        # Post-process security logging
        self._log_response(request, response)
        
        return response
    
    def _check_blocked_ip(self, request):
        """Check if IP is blocked due to suspicious activity"""
        ip_address = self._get_client_ip(request)
        
        # Check cache first for performance
        cache_key = f"blocked_ip:{ip_address}"
        if cache.get(cache_key):
            self.security_logger.warning(f"Blocked request from {ip_address}")
            return HttpResponseForbidden("Access denied")
        
        # Check database
        suspicious = SuspiciousActivity.objects.filter(
            ip_address=ip_address,
            blocked=True
        ).first()
        
        if suspicious:
            # Cache the result for 1 hour
            cache.set(cache_key, True, 3600)
            return HttpResponseForbidden("Access denied")
        
        return None
    
    def _log_request(self, request):
        """Log incoming requests for security analysis"""
        # Only log authentication-related requests to avoid noise
        auth_paths = [
            '/api/token/', '/api-token-auth/', '/login/',
            '/admin/', '/manager/', '/api/users/'
        ]
        
        if any(request.path.startswith(path) for path in auth_paths):
            self.security_logger.debug(
                f"Auth request: {request.method} {request.path}",
                extra={
                    'ip_address': self._get_client_ip(request),
                    'user_agent': request.META.get('HTTP_USER_AGENT', ''),
                    'user': request.user.username if hasattr(request, 'user') and request.user.is_authenticated else 'anonymous',
                }
            )
    
    def _check_suspicious_patterns(self, request):
        """Check for suspicious request patterns"""
        ip_address = self._get_client_ip(request)
        user_agent = request.META.get('HTTP_USER_AGENT', '')
        
        # Check for suspicious user agents
        suspicious_patterns = [
            'sqlmap', 'nikto', 'nmap', 'burp', 'owasp', 'scanner',
            'bot', 'crawler', 'spider', 'scraper'
        ]
        
        # Allow legitimate tools (customize based on your needs)
        legitimate_patterns = [
            'postman', 'insomnia', 'curl', 'wget', 'python-requests'  # Development tools
        ]
        
        is_suspicious = any(pattern in user_agent.lower() for pattern in suspicious_patterns)
        is_legitimate = any(pattern in user_agent.lower() for pattern in legitimate_patterns)
        
        if is_suspicious and not is_legitimate:
            self._record_suspicious_activity(
                ip_address, 'suspicious_user_agent',
                user_agent=user_agent, path=request.path
            )
            
            SecurityEvent.log_event(
                'suspicious_activity',
                request=request,
                severity='medium',
                pattern_type='user_agent',
                user_agent=user_agent
            )
        
        # Check for rapid requests (simple rate limiting check)
        self._check_request_frequency(request, ip_address)
        
        # Check for common attack patterns in URL
        self._check_url_patterns(request, ip_address)
    
    def _check_request_frequency(self, request, ip_address):
        """Check for rapid request patterns"""
        cache_key = f"request_freq:{ip_address}"
        current_count = cache.get(cache_key, 0)
        
        # Allow 100 requests per minute from same IP
        if current_count > 100:
            self._record_suspicious_activity(
                ip_address, 'high_request_frequency',
                count=current_count, path=request.path
            )
        else:
            cache.set(cache_key, current_count + 1, 60)  # 1 minute window
    
    def _check_url_patterns(self, request, ip_address):
        """Check for suspicious URL patterns"""
        path = request.path.lower()
        query = request.GET.urlencode().lower()
        
        # Common attack patterns
        attack_patterns = [
            'union', 'select', 'insert', 'delete', 'drop', 'exec',
            '../', '..\\', '/etc/passwd', '/proc/', 'cmd=', 'eval(',
            '<script', 'javascript:', 'onload=', 'onerror=',
            'wp-admin', 'wp-login', 'phpmyadmin', 'admin.php'
        ]
        
        full_request = f"{path}?{query}"
        
        if any(pattern in full_request for pattern in attack_patterns):
            self._record_suspicious_activity(
                ip_address, 'attack_pattern',
                path=request.path, query=request.GET.urlencode()
            )
            
            SecurityEvent.log_event(
                'suspicious_activity',
                request=request,
                severity='high',
                pattern_type='url_attack',
                path=request.path
            )
    
    def _record_suspicious_activity(self, ip_address, activity_type, **details):
        """Record suspicious activity"""
        suspicious, created = SuspiciousActivity.objects.get_or_create(
            ip_address=ip_address,
            activity_type=activity_type,
            defaults={'count': 1}
        )
        
        if not created:
            suspicious.increment()
            
            # Auto-block if threshold exceeded
            if suspicious.should_block():
                suspicious.blocked = True
                suspicious.save()
                
                # Cache the block for immediate enforcement
                cache_key = f"blocked_ip:{ip_address}"
                cache.set(cache_key, True, 3600)
                
                logger.warning(f"Auto-blocked IP {ip_address} for {activity_type} (count: {suspicious.count})")
    
    def _log_response(self, request, response):
        """Log security-relevant responses"""
        # Log failed authentication attempts
        if response.status_code in [401, 403]:
            SecurityEvent.log_event(
                'permission_denied',
                request=request,
                severity='medium',
                status_code=response.status_code,
                path=request.path
            )
        
        # Log rate limiting (if status 429)
        if response.status_code == 429:
            self._record_suspicious_activity(
                self._get_client_ip(request), 'rate_limit_exceeded',
                path=request.path
            )
            
            SecurityEvent.log_event(
                'rate_limit_exceeded',
                request=request,
                severity='medium',
                path=request.path
            )
    
    def _get_client_ip(self, request):
        """Get client IP handling proxies"""
        x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
        if x_forwarded_for:
            return x_forwarded_for.split(',')[0].strip()
        return request.META.get('REMOTE_ADDR', '127.0.0.1')


class SessionTrackingMiddleware(MiddlewareMixin):
    """Track user sessions and update activity timestamps"""
    
    def __init__(self, get_response):
        self.get_response = get_response
        super().__init__(get_response)
    
    def __call__(self, request):
        response = self.get_response(request)
        
        # Update session activity for authenticated users
        if hasattr(request, 'user') and request.user.is_authenticated:
            self._update_session_activity(request)
        
        return response
    
    def _update_session_activity(self, request):
        """Update last activity timestamp for user sessions"""
        try:
            # For JWT tokens, try to get JTI
            jwt_jti = None
            if hasattr(request, 'auth') and request.auth and hasattr(request.auth, 'get'):
                jwt_jti = str(request.auth.get('jti', ''))
            
            # Update sessions based on JWT JTI or user
            if jwt_jti:
                from .security_models import UserSession
                UserSession.objects.filter(
                    user=request.user,
                    jwt_jti=jwt_jti,
                    is_active=True
                ).update(last_activity=timezone.now())
            else:
                # Fall back to updating all active sessions for the user
                from .security_models import UserSession
                UserSession.objects.filter(
                    user=request.user,
                    is_active=True
                ).update(last_activity=timezone.now())
        
        except Exception as e:
            # Don't break the request if session tracking fails
            logger.debug(f"Session tracking error: {str(e)}")


class SecurityHeadersEnhancedMiddleware(MiddlewareMixin):
    """Enhanced security headers middleware"""
    
    def __init__(self, get_response):
        self.get_response = get_response
        super().__init__(get_response)
    
    def __call__(self, request):
        response = self.get_response(request)
        
        # Add security headers
        self._add_security_headers(response)
        
        return response
    
    def _add_security_headers(self, response):
        """Add comprehensive security headers"""
        if not settings.DEBUG:
            # Basic security headers
            response['X-Content-Type-Options'] = 'nosniff'
            response['X-Frame-Options'] = 'DENY'
            response['X-XSS-Protection'] = '1; mode=block'
            response['Referrer-Policy'] = 'strict-origin-when-cross-origin'
            
            # Advanced security headers
            response['Strict-Transport-Security'] = 'max-age=31536000; includeSubDomains'
            response['Content-Security-Policy'] = (
                "default-src 'self'; "
                "script-src 'self' 'unsafe-inline' 'unsafe-eval' https://cdn.jsdelivr.net https://cdnjs.cloudflare.com; "
                "style-src 'self' 'unsafe-inline' https://cdn.jsdelivr.net https://cdnjs.cloudflare.com; "
                "img-src 'self' data: https:; "
                "connect-src 'self'; "
                "font-src 'self' https://cdn.jsdelivr.net https://cdnjs.cloudflare.com data:"
            )
            
            # Permissions policy (replace Feature-Policy)
            response['Permissions-Policy'] = (
                'geolocation=(), microphone=(), camera=(), '
                'payment=(), usb=(), magnetometer=(), gyroscope=()'
            )
        
        # Add custom headers for API identification
        response['X-API-Version'] = '1.0'
        response['X-Security-Enhanced'] = 'true'
