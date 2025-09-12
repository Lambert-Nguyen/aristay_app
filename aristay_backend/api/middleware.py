# api/middleware.py
"""
Centralized exception handling middleware for API requests
"""
import logging
from django.utils.deprecation import MiddlewareMixin
from django.http import JsonResponse, HttpResponseForbidden
from django.core.exceptions import PermissionDenied as DjangoPermissionDenied
from rest_framework.exceptions import PermissionDenied as DRFPermissionDenied

logger = logging.getLogger(__name__)


class ApiExceptionMiddleware(MiddlewareMixin):
    """
    Middleware to catch unhandled exceptions in API endpoints
    and return consistent JSON error responses
    """
    
    def process_exception(self, request, exception):
        """
        Handle unhandled exceptions, especially for API endpoints
        """
        # Log the exception with context
        logger.exception(
            "Unhandled exception in request",
            extra={
                "path": request.path,
                "method": request.method,
                "user": getattr(request.user, 'username', 'anonymous') if hasattr(request, 'user') else 'unknown',
                "remote_addr": request.META.get('REMOTE_ADDR', 'unknown'),
                "user_agent": request.META.get('HTTP_USER_AGENT', 'unknown'),
            }
        )
        
        # Map permission errors to 403 so UI tests expect 403 instead of 500
        if isinstance(exception, (DjangoPermissionDenied, DRFPermissionDenied)):
            if request.path.startswith("/api/"):
                return JsonResponse({
                    "success": False,
                    "error": "Forbidden",
                    "detail": "You don't have permission to perform this action."
                }, status=403)
            return HttpResponseForbidden("Forbidden")

        # Return JSON responses for other API path errors
        if request.path.startswith("/api/"):
            return JsonResponse({
                "success": False,
                "error": "An unexpected server error occurred. Please try again later.",
                "detail": "Internal server error"
            }, status=500)
        
        # Let Django handle non-API errors normally (return None)
        return None
