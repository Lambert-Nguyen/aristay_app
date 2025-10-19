# tests/chat/test_chat_api.py
"""
Tests for chat REST API endpoints.
"""

import pytest
from django.contrib.auth.models import User
from rest_framework.test import APIClient
from rest_framework import status
from api.models import Profile
from api.models_chat import (
    ChatRoom,
    ChatParticipant,
    ChatMessage,
)


@pytest.fixture
def api_client():
    """Create an API client"""
    return APIClient()


@pytest.fixture
def user1(db):
    """Create first test user"""
    user = User.objects.create_user(
        username='alice',
        password='test123',
        email='alice@example.com',
        first_name='Alice',
        last_name='Johnson'
    )
    Profile.objects.get_or_create(user=user)
    return user


@pytest.fixture
def user2(db):
    """Create second test user"""
    user = User.objects.create_user(
        username='bob',
        password='test123',
        email='bob@example.com',
        first_name='Bob',
        last_name='Smith'
    )
    Profile.objects.get_or_create(user=user)
    return user


@pytest.fixture
def auth_client(api_client, user1):
    """Create authenticated API client"""
    api_client.force_authenticate(user=user1)
    return api_client


@pytest.mark.django_db
class TestChatRoomAPI:
    """Test ChatRoom API endpoints"""
    
    def test_list_rooms_authenticated(self, auth_client, user1, user2):
        """Test listing rooms for authenticated user"""
        # Create a room
        room = ChatRoom.objects.create(
            room_type='direct',
            created_by=user1
        )
        ChatParticipant.objects.create(room=room, user=user1)
        ChatParticipant.objects.create(room=room, user=user2)
        
        response = auth_client.get('/api/chat/rooms/')
        
        assert response.status_code == status.HTTP_200_OK
        assert 'results' in response.data
        assert len(response.data['results']) >= 1
        
    def test_list_rooms_unauthenticated(self, api_client):
        """Test listing rooms without authentication"""
        response = api_client.get('/api/chat/rooms/')
        
        assert response.status_code == status.HTTP_401_UNAUTHORIZED
        
    def test_create_direct_message_room(self, auth_client, user1, user2):
        """Test creating a direct message room"""
        data = {
            'room_type': 'direct',
            'participant_ids': [user2.id]
        }
        
        response = auth_client.post('/api/chat/rooms/', data, format='json')
        
        assert response.status_code == status.HTTP_201_CREATED
        assert response.data['room_type'] == 'direct'
        assert len(response.data['participants']) == 2
        
    def test_create_group_chat_room(self, auth_client, user1, user2):
        """Test creating a group chat room"""
        user3 = User.objects.create_user(username='charlie', password='test123')
        Profile.objects.get_or_create(user=user3)
        
        data = {
            'name': 'Project Team',
            'room_type': 'group',
            'participant_ids': [user2.id, user3.id]
        }
        
        response = auth_client.post('/api/chat/rooms/', data, format='json')
        
        assert response.status_code == status.HTTP_201_CREATED
        assert response.data['name'] == 'Project Team'
        assert response.data['room_type'] == 'group'
        assert len(response.data['participants']) == 3  # creator + 2 participants
        
    def test_get_room_details(self, auth_client, user1, user2):
        """Test getting room details"""
        room = ChatRoom.objects.create(
            room_type='direct',
            created_by=user1
        )
        ChatParticipant.objects.create(room=room, user=user1)
        ChatParticipant.objects.create(room=room, user=user2)
        
        response = auth_client.get(f'/api/chat/rooms/{room.id}/')
        
        assert response.status_code == status.HTTP_200_OK
        assert response.data['id'] == str(room.id)
        assert 'participants' in response.data
        
    def test_mark_room_as_read(self, auth_client, user1, user2):
        """Test marking room as read"""
        room = ChatRoom.objects.create(
            room_type='direct',
            created_by=user1
        )
        ChatParticipant.objects.create(room=room, user=user1)
        ChatParticipant.objects.create(room=room, user=user2)
        
        # Create some messages
        for i in range(3):
            ChatMessage.objects.create(
                room=room,
                sender=user2,
                content=f'Message {i+1}',
                message_type='text'
            )
        
        response = auth_client.post(f'/api/chat/rooms/{room.id}/mark_read/')
        
        assert response.status_code == status.HTTP_200_OK
        
        # Verify unread count is now 0
        participant = ChatParticipant.objects.get(room=room, user=user1)
        assert participant.unread_count == 0
        
    def test_leave_room(self, auth_client, user1, user2):
        """Test leaving a room"""
        room = ChatRoom.objects.create(
            room_type='direct',
            created_by=user1
        )
        ChatParticipant.objects.create(room=room, user=user1)
        ChatParticipant.objects.create(room=room, user=user2)
        
        response = auth_client.post(f'/api/chat/rooms/{room.id}/leave/')
        
        assert response.status_code == status.HTTP_200_OK
        
        # Verify participant has left
        participant = ChatParticipant.objects.get(room=room, user=user1)
        assert participant.left_at is not None
        
    def test_cannot_access_other_users_rooms(self, api_client, user1, user2):
        """Test that users can't access rooms they're not part of"""
        # Create room between user2 and another user
        user3 = User.objects.create_user(username='charlie', password='test123')
        Profile.objects.get_or_create(user=user3)
        
        room = ChatRoom.objects.create(
            room_type='direct',
            created_by=user2
        )
        ChatParticipant.objects.create(room=room, user=user2)
        ChatParticipant.objects.create(room=room, user=user3)
        
        # Try to access as user1 (not a participant)
        api_client.force_authenticate(user=user1)
        response = api_client.get(f'/api/chat/rooms/{room.id}/')
        
        assert response.status_code == status.HTTP_403_FORBIDDEN


@pytest.mark.django_db
class TestChatMessageAPI:
    """Test ChatMessage API endpoints"""
    
    def test_list_messages(self, auth_client, user1, user2):
        """Test listing messages in a room"""
        room = ChatRoom.objects.create(
            room_type='direct',
            created_by=user1
        )
        ChatParticipant.objects.create(room=room, user=user1)
        ChatParticipant.objects.create(room=room, user=user2)
        
        # Create some messages
        for i in range(5):
            ChatMessage.objects.create(
                room=room,
                sender=user2,
                content=f'Message {i+1}',
                message_type='text'
            )
        
        response = auth_client.get(f'/api/chat/messages/?room={room.id}')
        
        assert response.status_code == status.HTTP_200_OK
        assert 'results' in response.data
        assert len(response.data['results']) == 5
        
    def test_send_message(self, auth_client, user1, user2):
        """Test sending a message"""
        room = ChatRoom.objects.create(
            room_type='direct',
            created_by=user1
        )
        ChatParticipant.objects.create(room=room, user=user1)
        ChatParticipant.objects.create(room=room, user=user2)
        
        data = {
            'room': str(room.id),
            'content': 'Hello from API!',
            'message_type': 'text'
        }
        
        response = auth_client.post('/api/chat/messages/', data, format='json')
        
        assert response.status_code == status.HTTP_201_CREATED
        assert response.data['content'] == 'Hello from API!'
        assert response.data['message_type'] == 'text'
        assert response.data['sender']['id'] == user1.id
        
    def test_send_reply_message(self, auth_client, user1, user2):
        """Test sending a reply to a message"""
        room = ChatRoom.objects.create(
            room_type='direct',
            created_by=user1
        )
        ChatParticipant.objects.create(room=room, user=user1)
        ChatParticipant.objects.create(room=room, user=user2)
        
        # Create original message
        original_message = ChatMessage.objects.create(
            room=room,
            sender=user2,
            content='Original message',
            message_type='text'
        )
        
        # Send reply
        data = {
            'room': str(room.id),
            'content': 'Reply to original',
            'message_type': 'text',
            'reply_to': str(original_message.id)
        }
        
        response = auth_client.post('/api/chat/messages/', data, format='json')
        
        assert response.status_code == status.HTTP_201_CREATED
        assert response.data['reply_to_id'] == str(original_message.id)
        
    def test_edit_message(self, auth_client, user1):
        """Test editing a message"""
        room = ChatRoom.objects.create(
            room_type='direct',
            created_by=user1
        )
        ChatParticipant.objects.create(room=room, user=user1)
        
        message = ChatMessage.objects.create(
            room=room,
            sender=user1,
            content='Original content',
            message_type='text'
        )
        
        data = {
            'content': 'Edited content'
        }
        
        response = auth_client.patch(
            f'/api/chat/messages/{message.id}/',
            data,
            format='json'
        )
        
        assert response.status_code == status.HTTP_200_OK
        assert response.data['content'] == 'Edited content'
        assert response.data['is_edited'] is True
        
    def test_cannot_edit_other_users_messages(self, api_client, user1, user2):
        """Test that users can't edit other users' messages"""
        room = ChatRoom.objects.create(
            room_type='direct',
            created_by=user1
        )
        ChatParticipant.objects.create(room=room, user=user1)
        ChatParticipant.objects.create(room=room, user=user2)
        
        message = ChatMessage.objects.create(
            room=room,
            sender=user2,
            content='Bob\'s message',
            message_type='text'
        )
        
        # Try to edit as user1
        api_client.force_authenticate(user=user1)
        data = {'content': 'Hacked!'}
        
        response = api_client.patch(
            f'/api/chat/messages/{message.id}/',
            data,
            format='json'
        )
        
        assert response.status_code == status.HTTP_403_FORBIDDEN
        
    def test_delete_message(self, auth_client, user1):
        """Test soft deleting a message"""
        room = ChatRoom.objects.create(
            room_type='direct',
            created_by=user1
        )
        ChatParticipant.objects.create(room=room, user=user1)
        
        message = ChatMessage.objects.create(
            room=room,
            sender=user1,
            content='This will be deleted',
            message_type='text'
        )
        
        response = auth_client.delete(f'/api/chat/messages/{message.id}/')
        
        assert response.status_code == status.HTTP_204_NO_CONTENT
        
        # Verify soft delete
        message.refresh_from_db()
        assert message.is_deleted is True
        assert message.content == '[Message deleted]'
        
    def test_mark_message_as_read(self, auth_client, user1, user2):
        """Test marking a message as read"""
        room = ChatRoom.objects.create(
            room_type='direct',
            created_by=user1
        )
        ChatParticipant.objects.create(room=room, user=user1)
        ChatParticipant.objects.create(room=room, user=user2)
        
        message = ChatMessage.objects.create(
            room=room,
            sender=user2,
            content='Test message',
            message_type='text'
        )
        
        response = auth_client.post(f'/api/chat/messages/{message.id}/mark_read/')
        
        assert response.status_code == status.HTTP_200_OK
        
        # Verify read receipt
        message.refresh_from_db()
        assert str(user1.id) in message.read_by
        
    def test_search_messages(self, auth_client, user1, user2):
        """Test searching messages"""
        room = ChatRoom.objects.create(
            room_type='direct',
            created_by=user1
        )
        ChatParticipant.objects.create(room=room, user=user1)
        ChatParticipant.objects.create(room=room, user=user2)
        
        # Create messages with searchable content
        ChatMessage.objects.create(
            room=room,
            sender=user2,
            content='Hello world',
            message_type='text'
        )
        ChatMessage.objects.create(
            room=room,
            sender=user2,
            content='Goodbye world',
            message_type='text'
        )
        
        response = auth_client.get('/api/chat/messages/search/?q=hello')
        
        assert response.status_code == status.HTTP_200_OK
        assert 'results' in response.data
        assert len(response.data['results']) >= 1
        assert 'Hello' in response.data['results'][0]['content']

