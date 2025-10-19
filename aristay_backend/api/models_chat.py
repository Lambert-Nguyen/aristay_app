# api/models_chat.py
"""
Chat System Models for AriStay
Supports one-on-one and group chats with real-time messaging
"""

from django.db import models
from django.conf import settings
from django.utils import timezone
from django.core.validators import FileExtensionValidator
import uuid


class ChatRoom(models.Model):
    """
    Represents a chat room (one-on-one or group).
    Room names are auto-generated for consistency.
    """
    ROOM_TYPE_CHOICES = [
        ('direct', 'Direct Message'),
        ('group', 'Group Chat'),
        ('task', 'Task Discussion'),
        ('property', 'Property Discussion'),
    ]
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    name = models.CharField(max_length=255, blank=True, help_text="Display name for group chats")
    room_type = models.CharField(max_length=20, choices=ROOM_TYPE_CHOICES, default='direct')
    
    # For task/property-specific chats
    task = models.ForeignKey('Task', on_delete=models.CASCADE, null=True, blank=True, related_name='chat_rooms')
    property = models.ForeignKey('Property', on_delete=models.CASCADE, null=True, blank=True, related_name='chat_rooms')
    
    # Room metadata
    created_at = models.DateTimeField(auto_now_add=True)
    modified_at = models.DateTimeField(auto_now=True)
    created_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, related_name='created_rooms')
    
    # For soft delete pattern
    is_active = models.BooleanField(default=True)
    archived_at = models.DateTimeField(null=True, blank=True)
    
    class Meta:
        app_label = 'api'
        ordering = ['-modified_at']
        indexes = [
            models.Index(fields=['room_type', 'is_active']),
            models.Index(fields=['task']),
            models.Index(fields=['property']),
            models.Index(fields=['modified_at']),
        ]
        
    def __str__(self):
        if self.name:
            return self.name
        elif self.room_type == 'direct':
            participants = self.participants.all()[:2]
            return f"DM: {' & '.join([p.user.username for p in participants])}"
        return f"{self.get_room_type_display()} #{str(self.id)[:8]}"
    
    def get_display_name(self, for_user=None):
        """Get appropriate display name for the room"""
        if self.name:
            return self.name
        
        if self.room_type == 'direct' and for_user:
            # For direct messages, show the other person's name
            other_participants = self.participants.exclude(user=for_user)
            if other_participants.exists():
                other_user = other_participants.first().user
                return f"{other_user.get_full_name() or other_user.username}"
        
        if self.task:
            return f"Task: {self.task.title}"
        if self.property:
            return f"Property: {self.property.name}"
            
        return f"Chat #{str(self.id)[:8]}"
    
    def get_last_message(self):
        """Get the most recent message in this room"""
        return self.messages.filter(is_deleted=False).first()
    
    def get_unread_count(self, user):
        """Get unread message count for a specific user"""
        last_read = self.participants.filter(user=user).first()
        if not last_read:
            return 0
        
        if not last_read.last_read_at:
            return self.messages.filter(is_deleted=False).count()
        
        return self.messages.filter(
            created_at__gt=last_read.last_read_at,
            is_deleted=False
        ).exclude(sender=user).count()


class ChatParticipant(models.Model):
    """
    Represents a user's participation in a chat room.
    Tracks read status and user-specific settings.
    """
    room = models.ForeignKey(ChatRoom, on_delete=models.CASCADE, related_name='participants')
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='chat_participations')
    
    # Participant metadata
    joined_at = models.DateTimeField(auto_now_add=True)
    last_read_at = models.DateTimeField(null=True, blank=True)
    
    # Notification preferences
    muted = models.BooleanField(default=False)
    muted_until = models.DateTimeField(null=True, blank=True)
    
    # Role in room (for group chats)
    is_admin = models.BooleanField(default=False)
    
    # Soft delete
    left_at = models.DateTimeField(null=True, blank=True)
    
    class Meta:
        app_label = 'api'
        unique_together = [['room', 'user']]
        ordering = ['joined_at']
        indexes = [
            models.Index(fields=['user', 'room']),
            models.Index(fields=['last_read_at']),
        ]
        
    def __str__(self):
        return f"{self.user.username} in {self.room}"
    
    def mark_as_read(self):
        """Mark all messages as read up to now"""
        self.last_read_at = timezone.now()
        self.save(update_fields=['last_read_at'])
    
    def is_muted_now(self):
        """Check if participant has muted notifications"""
        if not self.muted:
            return False
        if self.muted_until and self.muted_until < timezone.now():
            return False
        return True


class ChatMessage(models.Model):
    """
    Represents an individual message in a chat room.
    Supports text, images, and file attachments.
    """
    MESSAGE_TYPE_CHOICES = [
        ('text', 'Text Message'),
        ('image', 'Image'),
        ('file', 'File Attachment'),
        ('system', 'System Message'),
    ]
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    room = models.ForeignKey(ChatRoom, on_delete=models.CASCADE, related_name='messages')
    sender = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, related_name='sent_messages')
    
    # Message content
    message_type = models.CharField(max_length=20, choices=MESSAGE_TYPE_CHOICES, default='text')
    content = models.TextField(help_text="Message text content")
    
    # Attachments (optional)
    attachment = models.FileField(
        upload_to='chat_attachments/%Y/%m/%d/',
        null=True,
        blank=True,
        validators=[FileExtensionValidator(allowed_extensions=['jpg', 'jpeg', 'png', 'gif', 'pdf', 'doc', 'docx', 'xls', 'xlsx'])]
    )
    attachment_name = models.CharField(max_length=255, blank=True)
    attachment_size = models.IntegerField(null=True, blank=True, help_text="File size in bytes")
    
    # Reply/thread support
    reply_to = models.ForeignKey('self', on_delete=models.SET_NULL, null=True, blank=True, related_name='replies')
    
    # Metadata
    created_at = models.DateTimeField(auto_now_add=True, db_index=True)
    modified_at = models.DateTimeField(auto_now=True)
    
    # Edit/delete tracking
    is_edited = models.BooleanField(default=False)
    edited_at = models.DateTimeField(null=True, blank=True)
    is_deleted = models.BooleanField(default=False)
    deleted_at = models.DateTimeField(null=True, blank=True)
    
    # Read receipts (stored as JSON for scalability)
    read_by = models.JSONField(default=dict, help_text="User IDs and timestamps who have read this message")
    
    class Meta:
        app_label = 'api'
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['room', '-created_at']),
            models.Index(fields=['sender']),
            models.Index(fields=['is_deleted', '-created_at']),
        ]
        
    def __str__(self):
        sender_name = self.sender.username if self.sender else "System"
        preview = self.content[:50] if self.content else f"[{self.message_type}]"
        return f"{sender_name}: {preview}"
    
    def mark_read_by(self, user):
        """Mark message as read by a specific user"""
        if not self.read_by:
            self.read_by = {}
        
        self.read_by[str(user.id)] = timezone.now().isoformat()
        self.save(update_fields=['read_by'])
    
    def is_read_by(self, user):
        """Check if message has been read by a user"""
        return str(user.id) in (self.read_by or {})
    
    def soft_delete(self):
        """Soft delete the message"""
        self.is_deleted = True
        self.deleted_at = timezone.now()
        self.content = "[Message deleted]"
        self.save(update_fields=['is_deleted', 'deleted_at', 'content'])


class ChatTypingIndicator(models.Model):
    """
    Temporary model to track who is currently typing in a room.
    Used for real-time typing indicators via WebSocket.
    """
    room = models.ForeignKey(ChatRoom, on_delete=models.CASCADE, related_name='typing_users')
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    started_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        app_label = 'api'
        unique_together = [['room', 'user']]
        indexes = [
            models.Index(fields=['room', 'started_at']),
        ]
        
    def __str__(self):
        return f"{self.user.username} typing in {self.room}"
    
    def is_stale(self):
        """Check if typing indicator is stale (>10 seconds old)"""
        return timezone.now() - self.started_at > timezone.timedelta(seconds=10)

