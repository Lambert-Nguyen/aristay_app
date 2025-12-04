# tests/chat/test_chat_models.py
"""
Tests for chat models.
"""

import pytest
from django.contrib.auth.models import User
from django.utils import timezone
from api.models_chat import (
    ChatRoom,
    ChatParticipant,
    ChatMessage,
    ChatTypingIndicator,
)


@pytest.mark.django_db
class TestChatRoom:
    """Test ChatRoom model"""
    
    def test_create_direct_message_room(self):
        """Test creating a direct message room"""
        user1 = User.objects.create_user(username='alice', password='test123')
        user2 = User.objects.create_user(username='bob', password='test123')
        
        room = ChatRoom.objects.create(
            room_type='direct',
            created_by=user1
        )
        
        ChatParticipant.objects.create(room=room, user=user1, is_admin=True)
        ChatParticipant.objects.create(room=room, user=user2, is_admin=False)
        
        assert room.room_type == 'direct'
        assert room.participants.count() == 2
        assert room.is_active is True
        
    def test_create_group_chat_room(self):
        """Test creating a group chat room"""
        user1 = User.objects.create_user(username='alice', password='test123')
        user2 = User.objects.create_user(username='bob', password='test123')
        user3 = User.objects.create_user(username='charlie', password='test123')
        
        room = ChatRoom.objects.create(
            name='Project Team',
            room_type='group',
            created_by=user1
        )
        
        for user in [user1, user2, user3]:
            ChatParticipant.objects.create(room=room, user=user)
        
        assert room.name == 'Project Team'
        assert room.room_type == 'group'
        assert room.participants.count() == 3
        
    def test_get_display_name_direct_message(self):
        """Test display name for direct messages"""
        user1 = User.objects.create_user(
            username='alice',
            password='test123',
            first_name='Alice',
            last_name='Johnson'
        )
        user2 = User.objects.create_user(
            username='bob',
            password='test123',
            first_name='Bob',
            last_name='Smith'
        )
        
        room = ChatRoom.objects.create(
            room_type='direct',
            created_by=user1
        )
        
        ChatParticipant.objects.create(room=room, user=user1)
        ChatParticipant.objects.create(room=room, user=user2)
        
        # Display name for user1 should be Bob's name
        display_name = room.get_display_name(user1)
        assert 'Bob' in display_name or 'bob' in display_name.lower()
        
    def test_get_display_name_group_chat(self):
        """Test display name for group chats"""
        user1 = User.objects.create_user(username='alice', password='test123')
        
        room = ChatRoom.objects.create(
            name='Project Team',
            room_type='group',
            created_by=user1
        )
        
        display_name = room.get_display_name(user1)
        assert display_name == 'Project Team'
        
    def test_get_unread_count(self):
        """Test getting unread message count"""
        user1 = User.objects.create_user(username='alice', password='test123')
        user2 = User.objects.create_user(username='bob', password='test123')
        
        room = ChatRoom.objects.create(
            room_type='direct',
            created_by=user1
        )
        
        participant1 = ChatParticipant.objects.create(room=room, user=user1)
        participant2 = ChatParticipant.objects.create(room=room, user=user2)
        
        # Create 3 messages
        for i in range(3):
            ChatMessage.objects.create(
                room=room,
                sender=user2,
                content=f'Message {i+1}',
                message_type='text'
            )
        
        # user1 hasn't read any messages
        unread = room.get_unread_count(user1)
        assert unread == 3


@pytest.mark.django_db
class TestChatParticipant:
    """Test ChatParticipant model"""
    
    def test_mark_as_read(self):
        """Test marking room as read"""
        user = User.objects.create_user(username='alice', password='test123')
        room = ChatRoom.objects.create(
            room_type='direct',
            created_by=user
        )
        
        participant = ChatParticipant.objects.create(room=room, user=user)
        
        # Mark as read
        participant.mark_as_read()
        
        assert participant.last_read_at is not None
        assert participant.last_read_at <= timezone.now()
        
    def test_unread_count(self):
        """Test unread count calculation"""
        user1 = User.objects.create_user(username='alice', password='test123')
        user2 = User.objects.create_user(username='bob', password='test123')
        
        room = ChatRoom.objects.create(
            room_type='direct',
            created_by=user1
        )
        
        participant1 = ChatParticipant.objects.create(room=room, user=user1)
        participant2 = ChatParticipant.objects.create(room=room, user=user2)
        
        # Create 5 messages
        for i in range(5):
            ChatMessage.objects.create(
                room=room,
                sender=user2,
                content=f'Message {i+1}',
                message_type='text'
            )
        
        # participant1 hasn't read anything
        unread = participant1.unread_count
        assert unread == 5
        
        # Mark as read
        participant1.mark_as_read()
        assert participant1.unread_count == 0


@pytest.mark.django_db
class TestChatMessage:
    """Test ChatMessage model"""
    
    def test_create_text_message(self):
        """Test creating a text message"""
        user = User.objects.create_user(username='alice', password='test123')
        room = ChatRoom.objects.create(
            room_type='direct',
            created_by=user
        )
        
        message = ChatMessage.objects.create(
            room=room,
            sender=user,
            content='Hello world!',
            message_type='text'
        )
        
        assert message.content == 'Hello world!'
        assert message.message_type == 'text'
        assert message.is_deleted is False
        assert message.is_edited is False
        
    def test_mark_read_by(self):
        """Test marking message as read"""
        user1 = User.objects.create_user(username='alice', password='test123')
        user2 = User.objects.create_user(username='bob', password='test123')
        
        room = ChatRoom.objects.create(
            room_type='direct',
            created_by=user1
        )
        
        message = ChatMessage.objects.create(
            room=room,
            sender=user2,
            content='Test message',
            message_type='text'
        )
        
        # Mark as read by user1
        message.mark_read_by(user1)
        
        assert str(user1.id) in message.read_by
        assert message.read_by[str(user1.id)] is not None
        
    def test_soft_delete(self):
        """Test soft deleting a message"""
        user = User.objects.create_user(username='alice', password='test123')
        room = ChatRoom.objects.create(
            room_type='direct',
            created_by=user
        )
        
        message = ChatMessage.objects.create(
            room=room,
            sender=user,
            content='This will be deleted',
            message_type='text'
        )
        
        original_content = message.content
        message.soft_delete()
        
        assert message.is_deleted is True
        assert message.deleted_at is not None
        assert message.content == '[Message deleted]'
        
    def test_reply_to_message(self):
        """Test replying to a message"""
        user = User.objects.create_user(username='alice', password='test123')
        room = ChatRoom.objects.create(
            room_type='direct',
            created_by=user
        )
        
        original_message = ChatMessage.objects.create(
            room=room,
            sender=user,
            content='Original message',
            message_type='text'
        )
        
        reply = ChatMessage.objects.create(
            room=room,
            sender=user,
            content='Reply to original',
            message_type='text',
            reply_to=original_message
        )
        
        assert reply.reply_to == original_message
        assert reply.reply_to_id == original_message.id


@pytest.mark.django_db
class TestChatTypingIndicator:
    """Test ChatTypingIndicator model"""
    
    def test_create_typing_indicator(self):
        """Test creating a typing indicator"""
        user = User.objects.create_user(username='alice', password='test123')
        room = ChatRoom.objects.create(
            room_type='direct',
            created_by=user
        )
        
        indicator = ChatTypingIndicator.objects.create(
            room=room,
            user=user
        )
        
        assert indicator.user == user
        assert indicator.room == room
        assert indicator.started_at is not None
        
    def test_automatic_cleanup_old_indicators(self):
        """Test that old typing indicators can be cleaned up"""
        user = User.objects.create_user(username='alice', password='test123')
        room = ChatRoom.objects.create(
            room_type='direct',
            created_by=user
        )
        
        # Create indicator
        indicator = ChatTypingIndicator.objects.create(
            room=room,
            user=user
        )
        indicator_id = indicator.id
        
        # Make it old (more than 10 seconds)
        old_time = timezone.now() - timezone.timedelta(seconds=15)
        ChatTypingIndicator.objects.filter(id=indicator_id).update(started_at=old_time)
        
        # Verify it exists before cleanup
        assert ChatTypingIndicator.objects.filter(id=indicator_id).exists()
        
        # Manually clean up stale indicators (this would be done by a periodic task)
        stale_cutoff = timezone.now() - timezone.timedelta(seconds=10)
        deleted_count = ChatTypingIndicator.objects.filter(started_at__lt=stale_cutoff).delete()[0]
        
        # Verify deletion happened
        assert deleted_count > 0
        # Indicator should be deleted
        assert not ChatTypingIndicator.objects.filter(id=indicator_id).exists()

