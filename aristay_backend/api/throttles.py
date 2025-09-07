# api/throttles.py
"""
Custom throttles for enhanced security
"""
from rest_framework.throttling import SimpleRateThrottle
from rest_framework_simplejwt.tokens import RefreshToken
from rest_framework.exceptions import ParseError


class RefreshTokenJtiRateThrottle(SimpleRateThrottle):
    """
    Throttle refresh token requests by the JWT ID (jti) rather than IP address.
    This prevents attackers from rotating IPs to bypass rate limits.
    """
    scope = 'token_refresh'  # uses existing rate (2/minute)

    def get_cache_key(self, request, view):
        if request.method != 'POST':
            return None
            
        # Extract refresh token from request data
        token_str = (request.data or {}).get('refresh') or (request.data or {}).get('refresh_token')
        if not token_str:
            # No token -> let view handle the 400; don't throttle this request specifically
            return None
            
        try:
            # Extract JTI from the refresh token
            token = RefreshToken(token_str)
            jti = str(token['jti'])
        except Exception:
            # Invalid token -> still return a key to rate limit obvious hammering
            jti = f"invalid:{hash(token_str) % 1000000}"  # Bounded hash for cache efficiency
            
        return self.cache_format % {"scope": self.scope, "ident": jti}
