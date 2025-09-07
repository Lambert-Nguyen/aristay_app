"""
Authentication mixins for AriStay API views
"""
from rest_framework.authentication import SessionAuthentication, TokenAuthentication
from rest_framework_simplejwt.authentication import JWTAuthentication


class DefaultAuthMixin:
    """
    Ensure all API views accept Bearer JWT in addition to legacy Token and session.
    Apply this mixin to ViewSets to enable JWT authentication.
    """
    authentication_classes = (JWTAuthentication, TokenAuthentication, SessionAuthentication)
