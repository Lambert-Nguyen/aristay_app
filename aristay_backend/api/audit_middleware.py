"""
Agent's Phase 2: Audit middleware for request context capture
Automatically captures who/where information for all requests
"""
import uuid
from django.utils.deprecation import MiddlewareMixin
from api.audit_signals import set_audit_context, clear_audit_context


class AuditMiddleware(MiddlewareMixin):
    """
    Middleware to set audit context for each request.
    Agent's recommendation: auto-capture who/where for all operations.
    """
    
    def process_request(self, request):
        """Set audit context at the start of each request."""
        # Generate unique request ID
        request_id = str(uuid.uuid4())
        request.audit_request_id = request_id
        
        # Get user (could be None for anonymous requests)
        user = request.user if hasattr(request, 'user') and request.user.is_authenticated else None
        
        # Extract client IP address
        ip_address = self.get_client_ip(request)
        
        # Get user agent
        user_agent = request.META.get('HTTP_USER_AGENT', '')
        
        # Set audit context for this thread
        set_audit_context(
            user=user,
            request_id=request_id,
            ip_address=ip_address,
            user_agent=user_agent
        )
        
        return None
    
    def process_response(self, request, response):
        """Clear audit context at the end of each request."""
        clear_audit_context()
        return response
    
    def process_exception(self, request, exception):
        """Clear audit context on exception."""
        clear_audit_context()
        return None
    
    def get_client_ip(self, request):
        """Extract client IP address from request."""
        x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
        if x_forwarded_for:
            ip = x_forwarded_for.split(',')[0].strip()
        else:
            ip = request.META.get('REMOTE_ADDR')
        return ip
