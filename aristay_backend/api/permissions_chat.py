# api/permissions_chat.py
"""
Custom permissions for chat system.
Ensures users can only access rooms they're participants in.
"""

from rest_framework import permissions
from .models_chat import ChatParticipant, ChatMessage


class IsChatParticipant(permissions.BasePermission):
    """
    Only participants of a chat room can access it.
    Used for ChatRoomViewSet and ChatMessageViewSet.
    """
    
    def has_object_permission(self, request, view, obj):
        """Check if user is a participant in the room"""
        # For ChatRoom objects
        if hasattr(obj, 'participants'):
            return ChatParticipant.objects.filter(
                room=obj,
                user=request.user,
                left_at__isnull=True
            ).exists()
        
        # For ChatMessage objects
        if hasattr(obj, 'room'):
            return ChatParticipant.objects.filter(
                room=obj.room,
                user=request.user,
                left_at__isnull=True
            ).exists()
        
        return False


class IsMessageSender(permissions.BasePermission):
    """
    Only the sender of a message can edit or delete it.
    Used for ChatMessageViewSet update/destroy actions.
    """
    
    def has_object_permission(self, request, view, obj):
        """Check if user is the message sender"""
        # Allow GET requests (viewing) if user is participant (checked by IsChatParticipant)
        if request.method in permissions.SAFE_METHODS:
            return True
        
        # For POST/PUT/PATCH/DELETE, must be the sender
        return obj.sender == request.user


class IsChatRoomAdmin(permissions.BasePermission):
    """
    Only room admins can perform administrative actions.
    Used for adding/removing participants, changing room settings.
    """
    
    def has_object_permission(self, request, view, obj):
        """Check if user is a room admin"""
        # For ChatRoom objects
        if hasattr(obj, 'participants'):
            room = obj
        # For ChatParticipant objects
        elif hasattr(obj, 'room'):
            room = obj.room
        else:
            return False
        
        # Allow GET requests for all participants
        if request.method in permissions.SAFE_METHODS:
            return ChatParticipant.objects.filter(
                room=room,
                user=request.user,
                left_at__isnull=True
            ).exists()
        
        # For modification, must be admin
        return ChatParticipant.objects.filter(
            room=room,
            user=request.user,
            is_admin=True,
            left_at__isnull=True
        ).exists()


class CanCreateDirectMessage(permissions.BasePermission):
    """
    Users can only create direct messages with other active users.
    Prevents creating DMs with invalid users.
    """
    
    def has_permission(self, request, view):
        """Check if user can create a chat room"""
        if request.method != 'POST':
            return True
        
        # For direct messages, validate the other participant exists
        if request.data.get('room_type') == 'direct':
            participant_ids = request.data.get('participant_ids', [])
            if not participant_ids or len(participant_ids) != 1:
                return False
            
            # Check if participant exists and is not the creator
            from django.contrib.auth.models import User
            try:
                other_user = User.objects.get(id=participant_ids[0])
                return other_user != request.user and other_user.is_active
            except User.DoesNotExist:
                return False
        
        return True


class IsAuthenticatedAndActive(permissions.BasePermission):
    """
    User must be authenticated and active.
    """
    
    def has_permission(self, request, view):
        return bool(
            request.user and
            request.user.is_authenticated and
            request.user.is_active
        )

