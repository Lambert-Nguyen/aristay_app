# api/views_chat.py
"""
REST API views for chat system.
Provides endpoints for Flutter mobile app and web interface.
"""

import logging
from django.db.models import Q, Count, Max, Prefetch
from django.utils import timezone
from rest_framework import viewsets, status, filters
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from rest_framework.pagination import PageNumberPagination
from django_filters.rest_framework import DjangoFilterBackend
from drf_spectacular.utils import extend_schema, extend_schema_view, OpenApiParameter, OpenApiExample
from drf_spectacular.types import OpenApiTypes

from .models_chat import (
    ChatRoom,
    ChatParticipant,
    ChatMessage,
    ChatTypingIndicator
)
from .serializers_chat import (
    ChatRoomSerializer,
    ChatRoomListSerializer,
    ChatRoomCreateSerializer,
    ChatMessageSerializer,
    ChatMessageCreateSerializer,
    ChatParticipantSerializer,
    TypingIndicatorSerializer,
)
from .permissions_chat import (
    IsChatParticipant,
    IsMessageSender,
    IsChatRoomAdmin,
    CanCreateDirectMessage,
    IsAuthenticatedAndActive,
)

logger = logging.getLogger(__name__)


class ChatPagination(PageNumberPagination):
    """Custom pagination for chat messages"""
    page_size = 50
    page_size_query_param = 'page_size'
    max_page_size = 100


@extend_schema_view(
    list=extend_schema(
        summary="List all chat rooms for current user",
        description="Returns all rooms where the user is a participant, ordered by most recent activity.",
        parameters=[
            OpenApiParameter(
                name='room_type',
                type=OpenApiTypes.STR,
                enum=['direct', 'group', 'task', 'property'],
                description='Filter by room type'
            ),
            OpenApiParameter(
                name='search',
                type=OpenApiTypes.STR,
                description='Search in room names'
            ),
        ]
    ),
    create=extend_schema(
        summary="Create a new chat room",
        description="Create a direct message, group chat, or task/property-specific room.",
        request=ChatRoomCreateSerializer,
        responses={201: ChatRoomSerializer}
    ),
    retrieve=extend_schema(
        summary="Get room details",
        description="Get full details of a specific chat room including participants.",
    ),
)
class ChatRoomViewSet(viewsets.ModelViewSet):
    """
    ViewSet for managing chat rooms.
    
    Supports:
    - List rooms (filtered by participation)
    - Create new rooms (direct, group, task, property)
    - Get room details
    - Update room settings
    - Archive rooms
    - Leave rooms
    """
    
    permission_classes = [IsAuthenticated]
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_fields = ['room_type', 'is_active']
    search_fields = ['name']
    ordering_fields = ['modified_at', 'created_at']
    ordering = ['-modified_at']
    
    def get_queryset(self):
        """Return only rooms where user is a participant"""
        user = self.request.user
        
        # Base queryset: rooms where user is an active participant
        queryset = ChatRoom.objects.filter(
            participants__user=user,
            participants__left_at__isnull=True
        ).select_related(
            'created_by', 'task', 'property'
        ).prefetch_related(
            Prefetch(
                'participants',
                queryset=ChatParticipant.objects.select_related('user').filter(left_at__isnull=True)
            )
        ).distinct()
        
        # Filter by active status
        if self.request.query_params.get('include_archived') != 'true':
            queryset = queryset.filter(is_active=True)
        
        return queryset
    
    def get_serializer_class(self):
        """Use different serializers for different actions"""
        if self.action == 'list':
            return ChatRoomListSerializer
        elif self.action == 'create':
            return ChatRoomCreateSerializer
        return ChatRoomSerializer
    
    def get_permissions(self):
        """Different permissions for different actions"""
        if self.action == 'create':
            return [IsAuthenticated(), CanCreateDirectMessage()]
        elif self.action in ['update', 'partial_update', 'destroy']:
            return [IsAuthenticated(), IsChatParticipant(), IsChatRoomAdmin()]
        return [IsAuthenticated(), IsChatParticipant()]
    
    def perform_create(self, serializer):
        """Set created_by to current user"""
        serializer.save(created_by=self.request.user)
    
    @extend_schema(
        summary="Archive chat room",
        description="Archive a room (soft delete). Only admins can archive rooms.",
        request=None,
        responses={200: ChatRoomSerializer}
    )
    @action(detail=True, methods=['post'], permission_classes=[IsAuthenticated, IsChatParticipant, IsChatRoomAdmin])
    def archive(self, request, pk=None):
        """Archive a chat room"""
        room = self.get_object()
        room.is_active = False
        room.archived_at = timezone.now()
        room.save(update_fields=['is_active', 'archived_at'])
        
        serializer = self.get_serializer(room)
        return Response(serializer.data)
    
    @extend_schema(
        summary="Unarchive chat room",
        description="Restore an archived room. Only admins can unarchive rooms.",
        request=None,
        responses={200: ChatRoomSerializer}
    )
    @action(detail=True, methods=['post'], permission_classes=[IsAuthenticated, IsChatParticipant, IsChatRoomAdmin])
    def unarchive(self, request, pk=None):
        """Unarchive a chat room"""
        room = self.get_object()
        room.is_active = True
        room.archived_at = None
        room.save(update_fields=['is_active', 'archived_at'])
        
        serializer = self.get_serializer(room)
        return Response(serializer.data)
    
    @extend_schema(
        summary="Leave chat room",
        description="Remove yourself from a chat room. Cannot leave if you're the only admin.",
        request=None,
        responses={200: {'type': 'object', 'properties': {'message': {'type': 'string'}}}}
    )
    @action(detail=True, methods=['post'], permission_classes=[IsAuthenticated, IsChatParticipant])
    def leave(self, request, pk=None):
        """Leave a chat room"""
        room = self.get_object()
        
        try:
            participant = ChatParticipant.objects.get(
                room=room,
                user=request.user,
                left_at__isnull=True
            )
            
            # Check if user is the only admin
            if participant.is_admin:
                admin_count = ChatParticipant.objects.filter(
                    room=room,
                    is_admin=True,
                    left_at__isnull=True
                ).count()
                
                if admin_count == 1:
                    return Response(
                        {'error': 'Cannot leave room as the only admin. Assign another admin first.'},
                        status=status.HTTP_400_BAD_REQUEST
                    )
            
            # Mark as left
            participant.left_at = timezone.now()
            participant.save(update_fields=['left_at'])
            
            return Response({'message': 'Successfully left the room'})
            
        except ChatParticipant.DoesNotExist:
            return Response(
                {'error': 'You are not a participant in this room'},
                status=status.HTTP_404_NOT_FOUND
            )
    
    @extend_schema(
        summary="Mark room as read",
        description="Mark all messages in the room as read for current user.",
        request=None,
        responses={200: {'type': 'object', 'properties': {'message': {'type': 'string'}}}}
    )
    @action(detail=True, methods=['post'], permission_classes=[IsAuthenticated, IsChatParticipant])
    def mark_read(self, request, pk=None):
        """Mark all messages in room as read"""
        room = self.get_object()
        
        try:
            participant = ChatParticipant.objects.get(
                room=room,
                user=request.user,
                left_at__isnull=True
            )
            participant.mark_as_read()
            
            return Response({'message': 'Room marked as read'})
            
        except ChatParticipant.DoesNotExist:
            return Response(
                {'error': 'You are not a participant in this room'},
                status=status.HTTP_404_NOT_FOUND
            )
    
    @extend_schema(
        summary="Get room statistics",
        description="Get message count, participant count, and other room statistics.",
        responses={200: {
            'type': 'object',
            'properties': {
                'message_count': {'type': 'integer'},
                'participant_count': {'type': 'integer'},
                'unread_count': {'type': 'integer'},
                'last_message_at': {'type': 'string', 'format': 'date-time'},
            }
        }}
    )
    @action(detail=True, methods=['get'], permission_classes=[IsAuthenticated, IsChatParticipant])
    def stats(self, request, pk=None):
        """Get room statistics"""
        room = self.get_object()
        
        stats = {
            'message_count': room.messages.filter(is_deleted=False).count(),
            'participant_count': room.participants.filter(left_at__isnull=True).count(),
            'unread_count': room.get_unread_count(request.user),
            'last_message_at': room.modified_at,
        }
        
        return Response(stats)


@extend_schema_view(
    list=extend_schema(
        summary="List messages in a room",
        description="Get paginated list of messages in a chat room, ordered by newest first.",
        parameters=[
            OpenApiParameter(
                name='room',
                type=OpenApiTypes.UUID,
                location=OpenApiParameter.QUERY,
                description='Filter by room ID',
                required=True
            ),
        ]
    ),
    create=extend_schema(
        summary="Send a message",
        description="Send a new message to a chat room. Supports text, images, and file attachments.",
        request=ChatMessageCreateSerializer,
        responses={201: ChatMessageSerializer}
    ),
    retrieve=extend_schema(
        summary="Get message details",
        description="Get full details of a specific message including read receipts.",
    ),
)
class ChatMessageViewSet(viewsets.ModelViewSet):
    """
    ViewSet for managing chat messages.
    
    Supports:
    - List messages in a room (paginated)
    - Send new messages
    - Get message details
    - Edit messages (sender only)
    - Delete messages (soft delete, sender only)
    - Mark messages as read
    """
    
    serializer_class = ChatMessageSerializer
    permission_classes = [IsAuthenticated, IsChatParticipant]
    pagination_class = ChatPagination
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_fields = ['message_type', 'sender']
    search_fields = ['content']
    ordering_fields = ['created_at']
    ordering = ['-created_at']
    
    def get_queryset(self):
        """Return messages from rooms where user is a participant"""
        user = self.request.user
        
        queryset = ChatMessage.objects.filter(
            room__participants__user=user,
            room__participants__left_at__isnull=True,
            is_deleted=False
        ).select_related(
            'sender', 'room', 'reply_to', 'reply_to__sender'
        ).distinct()
        
        # Filter by room if specified
        room_id = self.request.query_params.get('room')
        if room_id:
            queryset = queryset.filter(room_id=room_id)
        
        return queryset
    
    def get_serializer_class(self):
        """Use different serializers for different actions"""
        if self.action == 'create':
            return ChatMessageCreateSerializer
        return ChatMessageSerializer
    
    def create(self, request, *args, **kwargs):
        """Override create to use ChatMessageCreateSerializer for input, but return response with ChatMessageSerializer."""
        serializer = ChatMessageCreateSerializer(data=request.data, context=self.get_serializer_context())
        serializer.is_valid(raise_exception=True)
        self.perform_create(serializer)
        instance = serializer.instance
        output_serializer = ChatMessageSerializer(instance, context=self.get_serializer_context())
        headers = self.get_success_headers(output_serializer.data)
        return Response(output_serializer.data, status=status.HTTP_201_CREATED, headers=headers)
    def get_permissions(self):
        """Different permissions for different actions"""
        if self.action in ['update', 'partial_update', 'destroy']:
            return [IsAuthenticated(), IsChatParticipant(), IsMessageSender()]
        return [IsAuthenticated(), IsChatParticipant()]
    
    def perform_update(self, serializer):
        """Mark message as edited"""
        serializer.save(is_edited=True, edited_at=timezone.now())
    
    def perform_destroy(self, instance):
        """Soft delete the message"""
        instance.soft_delete()
    
    @extend_schema(
        summary="Mark message as read",
        description="Mark a specific message as read by current user.",
        request=None,
        responses={200: ChatMessageSerializer}
    )
    @action(detail=True, methods=['post'], permission_classes=[IsAuthenticated, IsChatParticipant])
    def mark_read(self, request, pk=None):
        """Mark message as read"""
        message = self.get_object()
        message.mark_read_by(request.user)
        
        serializer = self.get_serializer(message)
        return Response(serializer.data)
    
    @extend_schema(
        summary="Search messages",
        description="Full-text search across all messages in accessible rooms.",
        parameters=[
            OpenApiParameter(
                name='q',
                type=OpenApiTypes.STR,
                location=OpenApiParameter.QUERY,
                description='Search query',
                required=True
            ),
            OpenApiParameter(
                name='room',
                type=OpenApiTypes.UUID,
                location=OpenApiParameter.QUERY,
                description='Limit search to specific room (optional)'
            ),
        ]
    )
    @action(detail=False, methods=['get'], permission_classes=[IsAuthenticated])
    def search(self, request):
        """Search messages across all accessible rooms"""
        query = request.query_params.get('q', '').strip()
        
        if not query or len(query) < 3:
            return Response(
                {'error': 'Search query must be at least 3 characters'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        queryset = self.get_queryset().filter(
            Q(content__icontains=query)
        )
        
        # Limit to specific room if provided
        room_id = request.query_params.get('room')
        if room_id:
            queryset = queryset.filter(room_id=room_id)
        
        # Paginate results
        page = self.paginate_queryset(queryset)
        if page is not None:
            serializer = self.get_serializer(page, many=True)
            return self.get_paginated_response(serializer.data)
        
        serializer = self.get_serializer(queryset, many=True)
        return Response(serializer.data)


@extend_schema_view(
    list=extend_schema(
        summary="List participants in a room",
        description="Get all active participants in a chat room.",
        parameters=[
            OpenApiParameter(
                name='room',
                type=OpenApiTypes.UUID,
                location=OpenApiParameter.QUERY,
                description='Filter by room ID',
                required=True
            ),
        ]
    ),
    create=extend_schema(
        summary="Add participant to room",
        description="Add a new participant to a chat room. Requires admin permissions.",
        request=ChatParticipantSerializer,
        responses={201: ChatParticipantSerializer}
    ),
)
class ChatParticipantViewSet(viewsets.ModelViewSet):
    """
    ViewSet for managing chat participants.
    
    Supports:
    - List participants in a room
    - Add participants (admin only)
    - Update participant settings (mute, admin status)
    - Remove participants (admin only)
    """
    
    serializer_class = ChatParticipantSerializer
    permission_classes = [IsAuthenticated, IsChatRoomAdmin]
    filter_backends = [DjangoFilterBackend]
    filterset_fields = ['room', 'user', 'is_admin']
    
    def get_queryset(self):
        """Return participants from rooms where user is a participant"""
        user = self.request.user
        
        queryset = ChatParticipant.objects.filter(
            room__participants__user=user,
            room__participants__left_at__isnull=True,
            left_at__isnull=True
        ).select_related('user', 'room').distinct()
        
        # Filter by room if specified
        room_id = self.request.query_params.get('room')
        if room_id:
            queryset = queryset.filter(room_id=room_id)
        
        return queryset
    
    def perform_destroy(self, instance):
        """Mark participant as left instead of deleting"""
        instance.left_at = timezone.now()
        instance.save(update_fields=['left_at'])
    
    @extend_schema(
        summary="Mute room notifications",
        description="Mute or unmute notifications for this participant.",
        request={
            'type': 'object',
            'properties': {
                'muted': {'type': 'boolean'},
                'muted_until': {'type': 'string', 'format': 'date-time', 'nullable': True}
            }
        },
        responses={200: ChatParticipantSerializer}
    )
    @action(detail=True, methods=['post'], permission_classes=[IsAuthenticated])
    def mute(self, request, pk=None):
        """Mute/unmute notifications for this participant"""
        participant = self.get_object()
        
        # Only allow users to mute themselves
        if participant.user != request.user:
            return Response(
                {'error': 'You can only mute/unmute your own participation'},
                status=status.HTTP_403_FORBIDDEN
            )
        
        muted = request.data.get('muted', True)
        muted_until = request.data.get('muted_until')
        
        participant.muted = muted
        participant.muted_until = muted_until
        participant.save(update_fields=['muted', 'muted_until'])
        
        serializer = self.get_serializer(participant)
        return Response(serializer.data)


@extend_schema_view(
    list=extend_schema(
        summary="Get typing indicators",
        description="Get list of users currently typing in a room.",
        parameters=[
            OpenApiParameter(
                name='room',
                type=OpenApiTypes.UUID,
                location=OpenApiParameter.QUERY,
                description='Room ID',
                required=True
            ),
        ]
    ),
)
class TypingIndicatorViewSet(viewsets.ReadOnlyModelViewSet):
    """
    ViewSet for typing indicators (read-only).
    
    Actual typing indicators are managed via WebSocket.
    This endpoint is for polling-based clients.
    """
    
    serializer_class = TypingIndicatorSerializer
    permission_classes = [IsAuthenticated, IsChatParticipant]
    
    def get_queryset(self):
        """Return typing indicators for accessible rooms"""
        user = self.request.user
        room_id = self.request.query_params.get('room')
        
        if not room_id:
            return ChatTypingIndicator.objects.none()
        
        # Check if user is participant in the room
        is_participant = ChatParticipant.objects.filter(
            room_id=room_id,
            user=user,
            left_at__isnull=True
        ).exists()
        
        if not is_participant:
            return ChatTypingIndicator.objects.none()
        
        # Return typing indicators, excluding current user
        queryset = ChatTypingIndicator.objects.filter(
            room_id=room_id
        ).exclude(
            user=user
        ).select_related('user')
        
        # Remove stale indicators (older than 10 seconds)
        stale_cutoff = timezone.now() - timezone.timedelta(seconds=10)
        ChatTypingIndicator.objects.filter(started_at__lt=stale_cutoff).delete()
        
        return queryset

