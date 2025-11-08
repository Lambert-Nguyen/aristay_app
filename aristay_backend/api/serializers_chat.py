# api/serializers_chat.py
"""
Serializers for chat system - supporting both web and Flutter mobile clients
"""

from rest_framework import serializers
from django.contrib.auth.models import User
from django.db.models import Q, Count, Max
from django.utils import timezone

from .models_chat import (
    ChatRoom,
    ChatParticipant,
    ChatMessage,
    ChatTypingIndicator
)


class UserBriefSerializer(serializers.ModelSerializer):
    """Brief user info for chat messages"""
    full_name = serializers.SerializerMethodField()
    
    class Meta:
        model = User
        fields = ['id', 'username', 'full_name', 'email']
        
    def get_full_name(self, obj):
        return obj.get_full_name() or obj.username


class ChatParticipantSerializer(serializers.ModelSerializer):
    """Participant info in a chat room"""
    user = UserBriefSerializer(read_only=True)
    unread_count = serializers.SerializerMethodField()
    is_muted = serializers.SerializerMethodField()
    
    class Meta:
        model = ChatParticipant
        fields = [
            'id', 'user', 'room', 'joined_at', 'last_read_at',
            'is_admin', 'unread_count', 'is_muted', 'left_at'
        ]
        read_only_fields = ['id', 'joined_at']
        
    def get_unread_count(self, obj):
        """Get unread message count for this participant"""
        if not obj.last_read_at:
            return obj.room.messages.filter(is_deleted=False).count()
        
        return obj.room.messages.filter(
            created_at__gt=obj.last_read_at,
            is_deleted=False
        ).exclude(sender=obj.user).count()
    
    def get_is_muted(self, obj):
        return obj.is_muted_now()


class ChatMessageSerializer(serializers.ModelSerializer):
    """Message in a chat room"""
    sender = UserBriefSerializer(read_only=True)
    reply_to = serializers.SerializerMethodField()
    is_read = serializers.SerializerMethodField()
    read_count = serializers.SerializerMethodField()
    
    class Meta:
        model = ChatMessage
        fields = [
            'id', 'room', 'sender', 'message_type', 'content',
            'attachment', 'attachment_name', 'attachment_size',
            'reply_to', 'created_at', 'modified_at',
            'is_edited', 'edited_at', 'is_deleted', 'deleted_at',
            'is_read', 'read_count', 'read_by'
        ]
        read_only_fields = [
            'id', 'created_at', 'modified_at', 'is_edited',
            'edited_at', 'is_deleted', 'deleted_at', 'read_by'
        ]
        
    def get_reply_to(self, obj):
        """Get brief info about replied message"""
        if not obj.reply_to:
            return None
        
        return {
            'id': str(obj.reply_to.id),
            'sender': {
                'id': obj.reply_to.sender.id,
                'username': obj.reply_to.sender.username,
            },
            'content': obj.reply_to.content[:100],  # Preview only
            'created_at': obj.reply_to.created_at.isoformat(),
        }
    
    def get_is_read(self, obj):
        """Check if current user has read this message"""
        request = self.context.get('request')
        if not request or not request.user.is_authenticated:
            return False
        
        return obj.is_read_by(request.user)
    
    def get_read_count(self, obj):
        """Get number of users who have read this message"""
        return len(obj.read_by or {})


class ChatMessageCreateSerializer(serializers.ModelSerializer):
    """Serializer for creating new messages"""
    
    class Meta:
        model = ChatMessage
        fields = [
            'room', 'content', 'message_type', 'attachment',
            'attachment_name', 'reply_to'
        ]
        
    def validate_room(self, value):
        """Ensure user is participant in the room"""
        request = self.context.get('request')
        if not request:
            raise serializers.ValidationError("Request context required")
        
        if not ChatParticipant.objects.filter(
            room=value,
            user=request.user,
            left_at__isnull=True
        ).exists():
            raise serializers.ValidationError("You are not a participant in this room")
        
        return value
    
    def validate_reply_to(self, value):
        """Ensure reply_to message is in the same room"""
        if value and str(value.room_id) != str(self.initial_data.get('room')):
            raise serializers.ValidationError("Reply message must be in the same room")
        
        return value
    
    def create(self, validated_data):
        """Create message with sender"""
        request = self.context.get('request')
        validated_data['sender'] = request.user
        
        # Auto-detect message type if not provided
        if not validated_data.get('message_type'):
            if validated_data.get('attachment'):
                ext = validated_data['attachment'].name.split('.')[-1].lower()
                if ext in ['jpg', 'jpeg', 'png', 'gif']:
                    validated_data['message_type'] = 'image'
                else:
                    validated_data['message_type'] = 'file'
            else:
                validated_data['message_type'] = 'text'
        
        # Set attachment metadata
        if validated_data.get('attachment'):
            file = validated_data['attachment']
            if not validated_data.get('attachment_name'):
                validated_data['attachment_name'] = file.name
            validated_data['attachment_size'] = file.size
        
        return super().create(validated_data)


class ChatRoomSerializer(serializers.ModelSerializer):
    """Chat room with participants and last message"""
    participants = ChatParticipantSerializer(many=True, read_only=True)
    last_message = serializers.SerializerMethodField()
    unread_count = serializers.SerializerMethodField()
    display_name = serializers.SerializerMethodField()
    created_by = UserBriefSerializer(read_only=True)
    participant_count = serializers.SerializerMethodField()
    
    class Meta:
        model = ChatRoom
        fields = [
            'id', 'name', 'room_type', 'task', 'property',
            'created_at', 'modified_at', 'created_by',
            'is_active', 'archived_at',
            'participants', 'participant_count', 'last_message',
            'unread_count', 'display_name'
        ]
        read_only_fields = ['id', 'created_at', 'modified_at']
        
    def get_last_message(self, obj):
        """Get the most recent message"""
        last_msg = obj.get_last_message()
        if not last_msg:
            return None
        
        return ChatMessageSerializer(last_msg, context=self.context).data
    
    def get_unread_count(self, obj):
        """Get unread count for current user"""
        request = self.context.get('request')
        if not request or not request.user.is_authenticated:
            return 0
        
        return obj.get_unread_count(request.user)
    
    def get_display_name(self, obj):
        """Get display name for current user"""
        request = self.context.get('request')
        user = request.user if request and request.user.is_authenticated else None
        
        return obj.get_display_name(for_user=user)
    
    def get_participant_count(self, obj):
        """Get active participant count"""
        return obj.participants.filter(left_at__isnull=True).count()


class ChatRoomCreateSerializer(serializers.ModelSerializer):
    """Serializer for creating new chat rooms"""
    participant_ids = serializers.ListField(
        child=serializers.IntegerField(),
        write_only=True,
        required=False,
        help_text="List of user IDs to add as participants"
    )
    
    class Meta:
        model = ChatRoom
        fields = [
            'name', 'room_type', 'task', 'property', 'participant_ids'
        ]
        
    def validate_participant_ids(self, value):
        """Ensure all users exist"""
        if not value:
            return value
        
        user_count = User.objects.filter(id__in=value).count()
        if user_count != len(value):
            raise serializers.ValidationError("Some user IDs are invalid")
        
        return value
    
    def validate(self, attrs):
        """Validate room creation rules"""
        room_type = attrs.get('room_type', 'direct')
        participants = attrs.get('participant_ids', [])
        
        # For direct messages, ensure exactly 2 participants (including creator)
        if room_type == 'direct':
            if len(participants) != 1:  # 1 other user + creator = 2 total
                raise serializers.ValidationError({
                    'participant_ids': "Direct messages must have exactly 1 other participant"
                })
        
        # For task/property rooms, ensure task/property is provided
        if room_type == 'task' and not attrs.get('task'):
            raise serializers.ValidationError({
                'task': "Task is required for task-type rooms"
            })
        
        if room_type == 'property' and not attrs.get('property'):
            raise serializers.ValidationError({
                'property': "Property is required for property-type rooms"
            })
        
        return attrs
    
    def create(self, validated_data):
        """Create room with participants"""
        request = self.context.get('request')
        participant_ids = validated_data.pop('participant_ids', [])
        
        validated_data['created_by'] = request.user
        
        # For direct messages, check if room already exists
        if validated_data.get('room_type') == 'direct' and participant_ids:
            other_user_id = participant_ids[0]
            
            # Find existing direct message room between these users
            existing_room = ChatRoom.objects.filter(
                room_type='direct',
                participants__user=request.user
            ).filter(
                participants__user_id=other_user_id
            ).distinct().first()
            
            if existing_room:
                return existing_room
        
        # Create room
        room = super().create(validated_data)
        
        # Add creator as participant
        ChatParticipant.objects.create(
            room=room,
            user=request.user,
            is_admin=True
        )
        
        # Add other participants
        for user_id in participant_ids:
            user = User.objects.get(id=user_id)
            ChatParticipant.objects.create(
                room=room,
                user=user,
                is_admin=False
            )
        
        return room


class ChatRoomListSerializer(serializers.ModelSerializer):
    """Lightweight serializer for room list"""
    display_name = serializers.SerializerMethodField()
    unread_count = serializers.SerializerMethodField()
    last_message_preview = serializers.SerializerMethodField()
    last_message_time = serializers.SerializerMethodField()
    participant_count = serializers.SerializerMethodField()
    
    class Meta:
        model = ChatRoom
        fields = [
            'id', 'display_name', 'room_type', 'is_active',
            'unread_count', 'last_message_preview', 'last_message_time',
            'participant_count', 'modified_at'
        ]
        
    def get_display_name(self, obj):
        request = self.context.get('request')
        user = request.user if request and request.user.is_authenticated else None
        return obj.get_display_name(for_user=user)
    
    def get_unread_count(self, obj):
        request = self.context.get('request')
        if not request or not request.user.is_authenticated:
            return 0
        return obj.get_unread_count(request.user)
    
    def get_last_message_preview(self, obj):
        last_msg = obj.get_last_message()
        if not last_msg:
            return "No messages yet"
        
        preview = last_msg.content
        if last_msg.message_type != 'text':
            preview = f"[{last_msg.get_message_type_display()}]"
        
        return preview[:100]
    
    def get_last_message_time(self, obj):
        last_msg = obj.get_last_message()
        return last_msg.created_at if last_msg else obj.created_at
    
    def get_participant_count(self, obj):
        return obj.participants.filter(left_at__isnull=True).count()


class TypingIndicatorSerializer(serializers.ModelSerializer):
    """Typing indicator status"""
    user = UserBriefSerializer(read_only=True)
    
    class Meta:
        model = ChatTypingIndicator
        fields = ['id', 'room', 'user', 'started_at']
        read_only_fields = ['id', 'started_at']

