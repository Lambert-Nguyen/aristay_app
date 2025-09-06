"""
Agent's Phase 2: Audit middleware for request context capture
Fixed per GPT agent: compatible with both Django middleware chain and direct test instantiation
"""
import uuid
from .audit_signals import set_audit_context, clear_audit_context


def get_client_ip(request):
    """Extract client IP from request."""
    x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
    if x_forwarded_for:
        ip = x_forwarded_for.split(',')[0].strip()
    else:
        ip = request.META.get('REMOTE_ADDR', '')
    return ip


class AuditMiddleware:
    """
    Compatible middleware for both Django's middleware chain and direct
    instantiation in tests (process_request/process_response).
    """
    def __init__(self, get_response=None):
        self.get_response = get_response or (lambda r: r)

    def __call__(self, request):
        self.process_request(request)
        response = self.get_response(request)
        return self.process_response(request, response)

    def process_request(self, request):
        """Capture request context for audit trail."""
        user = getattr(request, "user", None)
        user_agent = request.META.get("HTTP_USER_AGENT", "")
        ip = get_client_ip(request)
        
        set_audit_context(
            user=user if getattr(user, "is_authenticated", False) else None,
            request_id=uuid.uuid4().hex,
            ip_address=ip or None,
            user_agent=user_agent or "",
        )
        return None

    def process_response(self, request, response):
        """Clear audit context after request."""
        clear_audit_context()
        return response

    def process_exception(self, request, exception):
        """Clear audit context on exception."""
        clear_audit_context()
        return None
