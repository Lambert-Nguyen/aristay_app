"""
Debug authentication views for testing JWT functionality
"""
from rest_framework.views import APIView
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework import status
from .auth_mixins import DefaultAuthMixin


class WhoAmIView(DefaultAuthMixin, APIView):
    """Simple endpoint to test JWT authentication"""
    permission_classes = [IsAuthenticated]

    def get(self, request):
        """Return current user information"""
        return Response({
            "message": "JWT Authentication Working!",
            "user": request.user.username,
            "user_id": request.user.id,
            "is_staff": request.user.is_staff,
            "is_superuser": request.user.is_superuser,
            "authentication": str(request.auth.__class__.__name__) if request.auth else "None",
        }, status=status.HTTP_200_OK)
