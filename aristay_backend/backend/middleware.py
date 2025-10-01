"""
Middleware for request logging, performance monitoring, security tracking, and timezone handling
"""
import time
import logging
import json
from django.utils.deprecation import MiddlewareMixin
from django.db import connection
from django.conf import settings
from django.utils import timezone
from django.shortcuts import redirect
from django.contrib import messages
import psutil
import os


class AdminAccessMiddleware(MiddlewareMixin):
    """
    Middleware to redirect managers from /admin/ to /manager/
    """
    
    def process_request(self, request):
        # Only process /admin/ requests (not /manager/ or /api/)
        if request.path.startswith('/admin/') and not request.path.startswith('/admin/login/'):
            if request.user.is_authenticated and not request.user.is_superuser:
                # Check if user is a manager
                try:
                    if hasattr(request.user, 'profile') and request.user.profile and request.user.profile.role == 'manager':
                        # Redirect manager to manager admin
                        return redirect('/manager/')
                except:
                    pass
                    
                # For non-superuser users trying to access admin
                if hasattr(request.user, 'profile') and request.user.profile.role in ['manager', 'staff', 'viewer']:
                    # Only add message if messages framework is available (not in tests)
                    if hasattr(request, '_messages'):
                        messages.error(request, 'Access Denied: Only superusers can access the admin area.')
                    return redirect('/api/portal/')
        return None


class TimezoneMiddleware(MiddlewareMixin):
    """
    Middleware to activate timezone based on user's profile settings
    Defaults to Tampa, FL timezone for consistency
    """
    
    def process_request(self, request):
        """Set timezone based on authenticated user's profile"""
        if hasattr(request, 'user') and request.user.is_authenticated:
            try:
                # Get user's timezone from profile
                user_timezone = getattr(request.user.profile, 'timezone', 'America/New_York')
                timezone.activate(user_timezone)
            except Exception:
                # Fallback to Tampa, FL timezone if profile doesn't exist or timezone is invalid
                timezone.activate('America/New_York')
        else:
            # Use Tampa, FL timezone for anonymous users (default)
            timezone.activate('America/New_York')


class RequestLoggingMiddleware(MiddlewareMixin):
    """
    Middleware to log all HTTP requests with performance metrics
    Tracks response times, database queries, memory usage, and security events
    """
    
    def __init__(self, get_response):
        self.get_response = get_response
        self.logger = logging.getLogger('api.performance')
        self.security_logger = logging.getLogger('api.security')
        super().__init__(get_response)
    
    def process_request(self, request):
        """Start timing and capture initial metrics"""
        request._start_time = time.time()
        request._start_queries = len(connection.queries)
        
        # Get initial memory usage
        try:
            process = psutil.Process(os.getpid())
            request._start_memory = process.memory_info().rss / 1024 / 1024  # MB
        except:
            request._start_memory = 0
        
        # Log security-relevant requests
        self._log_security_events(request)
        
        return None
    
    def process_response(self, request, response):
        """Log the completed request with performance metrics"""
        if not hasattr(request, '_start_time'):
            return response
        
        # Calculate timing
        duration = (time.time() - request._start_time) * 1000  # milliseconds
        
        # Calculate database metrics
        queries_count = len(connection.queries) - request._start_queries
        queries_time = sum(float(q['time']) for q in connection.queries[request._start_queries:]) * 1000
        
        # Calculate memory usage
        try:
            process = psutil.Process(os.getpid())
            end_memory = process.memory_info().rss / 1024 / 1024  # MB
            memory_delta = end_memory - request._start_memory
        except:
            end_memory = 0
            memory_delta = 0
        
        # Determine if this is a slow request
        is_slow = duration > getattr(settings, 'SLOW_REQUEST_THRESHOLD', 1000)
        
        # Log the request
        log_level = logging.WARNING if is_slow else logging.INFO
        
        self.logger.log(
            log_level,
            f"{request.method} {request.path} - {response.status_code} - {duration:.1f}ms",
            extra={
                'request': request,
                'duration': duration,
                'queries_count': queries_count,
                'queries_time': queries_time,
                'memory_usage': end_memory,
                'memory_delta': memory_delta,
                'response_status': response.status_code,
                'request_method': request.method,
                'request_path': request.path,
                'user_id': getattr(request.user, 'id', None) if hasattr(request, 'user') else None,
                'is_authenticated': getattr(request.user, 'is_authenticated', False) if hasattr(request, 'user') else False,
                'content_length': len(response.content) if hasattr(response, 'content') else 0,
                'slow_queries': self._get_slow_queries() if queries_time > 100 else [],
            }
        )
        
        # Log very slow requests as warnings
        if duration > 5000:  # 5 seconds
            self.logger.warning(
                f"Very slow request detected: {request.method} {request.path}",
                extra={
                    'request': request,
                    'duration': duration,
                    'performance_issue': True,
                    'queries_count': queries_count,
                    'queries_time': queries_time,
                }
            )
        
        return response
    
    def _log_security_events(self, request):
        """Log security-relevant events"""
        # Log authentication attempts
        if '/api/auth/' in request.path:
            self.security_logger.info(
                f"Authentication attempt: {request.method} {request.path}",
                extra={
                    'request': request,
                    'security_event': 'auth_attempt',
                    'security_category': 'authentication',
                    'user_agent': request.META.get('HTTP_USER_AGENT', ''),
                    'remote_addr': self._get_client_ip(request),
                }
            )
        
        # Log admin access
        if '/admin/' in request.path or '/manager/' in request.path:
            self.security_logger.info(
                f"Admin access: {request.method} {request.path}",
                extra={
                    'request': request,
                    'security_event': 'admin_access',
                    'security_category': 'privileged_access',
                    'user_id': getattr(request.user, 'id', None) if hasattr(request, 'user') else None,
                }
            )
        
        # Log suspicious patterns
        suspicious_patterns = [
            '/wp-admin/', '/.env', '/config/', '/backup/',
            'SELECT', 'UNION', 'script>', '<script',
            '../', '..\\', 'etc/passwd'
        ]
        
        # Safely read request body; avoid triggering RequestDataTooBig
        try:
            body_preview = request.body.decode('utf-8', errors='ignore')[:500]
        except Exception:
            body_preview = ''
        request_data = f"{request.path} {body_preview}"
        if any(pattern in request_data for pattern in suspicious_patterns):
            self.security_logger.warning(
                f"Suspicious request pattern detected: {request.method} {request.path}",
                extra={
                    'request': request,
                    'security_event': 'suspicious_pattern',
                    'security_category': 'potential_attack',
                    'pattern_detected': True,
                    'request_sample': request_data[:200],
                }
            )
    
    def _get_client_ip(self, request):
        """Get the real client IP address"""
        x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
        if x_forwarded_for:
            ip = x_forwarded_for.split(',')[0]
        else:
            ip = request.META.get('REMOTE_ADDR')
        return ip
    
    def _get_slow_queries(self):
        """Get details of slow database queries"""
        slow_queries = []
        for query in connection.queries[-10:]:  # Last 10 queries
            time_taken = float(query['time']) * 1000
            if time_taken > 100:  # 100ms threshold
                slow_queries.append({
                    'sql': query['sql'][:200],  # Truncate long queries
                    'time_ms': time_taken,
                })
        return slow_queries


class ErrorLoggingMiddleware(MiddlewareMixin):
    """
    Middleware to capture and log unhandled exceptions
    """
    
    def __init__(self, get_response):
        self.get_response = get_response
        self.logger = logging.getLogger('api')
        super().__init__(get_response)
    
    def process_exception(self, request, exception):
        """Log unhandled exceptions with context"""
        self.logger.error(
            f"Unhandled exception in {request.method} {request.path}: {str(exception)}",
            exc_info=True,
            extra={
                'request': request,
                'exception_type': type(exception).__name__,
                'exception_message': str(exception),
                'user_id': getattr(request.user, 'id', None) if hasattr(request, 'user') else None,
                'request_data': self._get_request_data(request),
            }
        )
        return None
    
    def _get_request_data(self, request):
        """Safely extract request data for logging"""
        try:
            data = {}
            if request.method in ['POST', 'PUT', 'PATCH']:
                if request.content_type == 'application/json':
                    body = request.body.decode('utf-8')
                    if body:
                        data['json'] = json.loads(body)
                elif hasattr(request, 'POST'):
                    data['form'] = dict(request.POST)
            
            # Sanitize sensitive data
            if 'json' in data and isinstance(data['json'], dict):
                data['json'] = self._sanitize_data(data['json'])
            if 'form' in data and isinstance(data['form'], dict):
                data['form'] = self._sanitize_data(data['form'])
            
            return data
        except:
            return {'error': 'Could not parse request data'}
    
    def _sanitize_data(self, data):
        """Remove sensitive data from request logs"""
        if not isinstance(data, dict):
            return data
        
        sensitive_keys = {
            'password', 'token', 'secret', 'key', 'authorization',
            'cookie', 'session', 'csrf', 'api_key', 'auth_token'
        }
        
        sanitized = {}
        for key, value in data.items():
            if isinstance(key, str) and any(sensitive in key.lower() for sensitive in sensitive_keys):
                sanitized[key] = '[REDACTED]'
            elif isinstance(value, dict):
                sanitized[key] = self._sanitize_data(value)
            else:
                sanitized[key] = value
        
        return sanitized


class SecurityHeadersMiddleware(MiddlewareMixin):
    """
    Middleware to add security headers and log security-related responses
    """
    
    def __init__(self, get_response):
        self.get_response = get_response
        self.security_logger = logging.getLogger('api.security')
        super().__init__(get_response)
    
    def process_response(self, request, response):
        """Add security headers and log security events"""
        # Add security headers for production
        if not settings.DEBUG:
            response['X-Content-Type-Options'] = 'nosniff'
            response['X-Frame-Options'] = 'DENY'
            response['X-XSS-Protection'] = '1; mode=block'
            response['Referrer-Policy'] = 'strict-origin-when-cross-origin'
            response['Permissions-Policy'] = 'geolocation=(), microphone=(), camera=()'
        
        # Log failed authentication attempts
        if response.status_code in [401, 403]:
            self.security_logger.warning(
                f"Access denied: {request.method} {request.path} - {response.status_code}",
                extra={
                    'request': request,
                    'security_event': 'access_denied',
                    'security_category': 'authorization',
                    'status_code': response.status_code,
                    'user_id': getattr(request.user, 'id', None) if hasattr(request, 'user') else None,
                }
            )
        
        # Log rate limiting (if status 429)
        if response.status_code == 429:
            self.security_logger.warning(
                f"Rate limit exceeded: {request.method} {request.path}",
                extra={
                    'request': request,
                    'security_event': 'rate_limit_exceeded',
                    'security_category': 'abuse_prevention',
                }
            )
        
        return response