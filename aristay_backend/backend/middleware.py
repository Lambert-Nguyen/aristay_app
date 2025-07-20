# backend/middleware.py

from django.utils import timezone

class TimezoneMiddleware:
    """
    Reads request.user.profile.timezone and activates it.
    """
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        if request.user.is_authenticated:
            tz = getattr(request.user, 'profile', None) and request.user.profile.timezone
            if tz:
                timezone.activate(tz)
        response = self.get_response(request)
        return response