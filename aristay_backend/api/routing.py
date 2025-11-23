# api/routing.py
"""
WebSocket URL routing for Django Channels.
"""

from django.urls import re_path
from . import consumers

# UUID pattern: 8-4-4-4-12 hex digits with dashes
# Example: 550e8400-e29b-41d4-a716-446655440000
websocket_urlpatterns = [
    re_path(r'ws/chat/(?P<room_id>[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12})/$', consumers.ChatConsumer.as_asgi()),
]

