# api/consumers.py
"""
WebSocket consumers for real-time chat functionality.
Uses Django Channels with Redis as channel layer backend.
"""

import json
import logging
from channels.generic.websocket import AsyncWebsocketConsumer
from channels.db import database_sync_to_async
from django.contrib.auth.models import User
from django.utils import timezone
from rest_framework_simplejwt.tokens import AccessToken
from rest_framework_simplejwt.exceptions import TokenError

logger = logging.getLogger(__name__)


class ChatConsumer(AsyncWebsocketConsumer):
    """
    WebSocket consumer for real-time chat messaging.
    Handles message sending, typing indicators, and read receipts.
    """
    
    async def connect(self):
        """Handle WebSocket connection"""
        self.room_id = self.scope['url_route']['kwargs']['room_id']
        self.room_group_name = f'chat_{self.room_id}'
        self.user = None
        
        # Authenticate user from query params (JWT token)
        await self.authenticate_user()
        
        if not self.user:
            await self.close()
            return
        
        # Verify user is participant in this room
        is_participant = await self.check_participant()
        if not is_participant:
            await self.close()
            return
        
        # Join room group
        await self.channel_layer.group_add(
            self.room_group_name,
            self.channel_name
        )
        
        await self.accept()
        
        # Send user's unread count
        unread_count = await self.get_unread_count()
        await self.send(text_data=json.dumps({
            'type': 'connection_established',
            'room_id': self.room_id,
            'unread_count': unread_count,
            'user_id': self.user.id,
            'username': self.user.username,
        }))
        
        logger.info(f"User {self.user.username} connected to room {self.room_id}")
    
    async def disconnect(self, close_code):
        """Handle WebSocket disconnection"""
        if hasattr(self, 'room_group_name'):
            # Leave room group
            await self.channel_layer.group_discard(
                self.room_group_name,
                self.channel_name
            )
            
            # Clear typing indicator
            if self.user:
                await self.clear_typing_indicator()
                logger.info(f"User {self.user.username} disconnected from room {self.room_id}")
    
    async def receive(self, text_data):
        """Handle incoming WebSocket messages"""
        try:
            data = json.loads(text_data)
            message_type = data.get('type')
            
            if message_type == 'chat_message':
                await self.handle_chat_message(data)
            elif message_type == 'typing':
                await self.handle_typing(data)
            elif message_type == 'read_receipt':
                await self.handle_read_receipt(data)
            elif message_type == 'mark_room_read':
                await self.handle_mark_room_read(data)
            else:
                logger.warning(f"Unknown message type: {message_type}")
                
        except json.JSONDecodeError:
            logger.error(f"Invalid JSON received: {text_data}")
        except Exception as e:
            logger.error(f"Error processing message: {str(e)}", exc_info=True)
            await self.send(text_data=json.dumps({
                'type': 'error',
                'message': 'Failed to process message'
            }))
    
    async def handle_chat_message(self, data):
        """Handle new chat message"""
        content = data.get('message', '').strip()
        reply_to_id = data.get('reply_to')
        
        if not content:
            return
        
        # Save message to database
        message = await self.save_message(content, reply_to_id)
        
        if message:
            # Update room's modified_at timestamp
            await self.update_room_timestamp()
            
            # Broadcast message to room group
            await self.channel_layer.group_send(
                self.room_group_name,
                {
                    'type': 'chat_message_broadcast',
                    'message': await self.serialize_message(message)
                }
            )
            
            # Send push notifications to offline users
            await self.send_push_notifications(message)
    
    async def handle_typing(self, data):
        """Handle typing indicator"""
        is_typing = data.get('is_typing', False)
        
        if is_typing:
            await self.set_typing_indicator()
        else:
            await self.clear_typing_indicator()
        
        # Broadcast typing status to room (except sender)
        await self.channel_layer.group_send(
            self.room_group_name,
            {
                'type': 'typing_broadcast',
                'user_id': self.user.id,
                'username': self.user.username,
                'is_typing': is_typing
            }
        )
    
    async def handle_read_receipt(self, data):
        """Handle message read receipt"""
        message_id = data.get('message_id')
        if message_id:
            await self.mark_message_read(message_id)
            
            # Broadcast read receipt to room
            await self.channel_layer.group_send(
                self.room_group_name,
                {
                    'type': 'read_receipt_broadcast',
                    'message_id': message_id,
                    'user_id': self.user.id,
                    'read_at': timezone.now().isoformat()
                }
            )
    
    async def handle_mark_room_read(self, data):
        """Mark all messages in room as read"""
        await self.mark_room_read()
        
        # Send confirmation
        await self.send(text_data=json.dumps({
            'type': 'room_marked_read',
            'room_id': self.room_id
        }))
    
    # Broadcast handlers (called by channel layer)
    
    async def chat_message_broadcast(self, event):
        """Send chat message to WebSocket"""
        await self.send(text_data=json.dumps({
            'type': 'chat_message',
            'message': event['message']
        }))
    
    async def typing_broadcast(self, event):
        """Send typing indicator to WebSocket (except to self)"""
        if event['user_id'] != self.user.id:
            await self.send(text_data=json.dumps({
                'type': 'typing',
                'user_id': event['user_id'],
                'username': event['username'],
                'is_typing': event['is_typing']
            }))
    
    async def read_receipt_broadcast(self, event):
        """Send read receipt to WebSocket"""
        await self.send(text_data=json.dumps({
            'type': 'read_receipt',
            'message_id': event['message_id'],
            'user_id': event['user_id'],
            'read_at': event['read_at']
        }))
    
    # Database operations (sync wrapped in database_sync_to_async)
    
    @database_sync_to_async
    def authenticate_user(self):
        """Authenticate user from JWT token in query params"""
        try:
            # Get token from query params
            query_string = self.scope.get('query_string', b'').decode('utf-8')
            if not query_string:
                logger.warning("No query string in WebSocket connection")
                self.user = None
                return
            
            # Parse query string (handle URL encoding)
            from urllib.parse import parse_qs
            params = parse_qs(query_string)
            token = params.get('token', [None])[0]
            
            if not token:
                logger.warning("No token provided in WebSocket connection")
                self.user = None
                return
            
            # Verify JWT token
            access_token = AccessToken(token)
            user_id = access_token['user_id']
            
            # Get user
            self.user = User.objects.get(id=user_id)
            logger.info(f"WebSocket authenticated user: {self.user.username}")
            
        except TokenError as e:
            logger.warning(f"Invalid JWT token: {str(e)}")
            self.user = None
        except User.DoesNotExist:
            logger.warning(f"User not found for token")
            self.user = None
        except Exception as e:
            logger.error(f"Authentication error: {str(e)}", exc_info=True)
            self.user = None
    
    @database_sync_to_async
    def check_participant(self):
        """Check if user is participant in the room"""
        from api.models_chat import ChatParticipant
        
        return ChatParticipant.objects.filter(
            room_id=self.room_id,
            user=self.user,
            left_at__isnull=True
        ).exists()
    
    @database_sync_to_async
    def get_unread_count(self):
        """Get unread message count for user in room"""
        from api.models_chat import ChatRoom
        
        try:
            room = ChatRoom.objects.get(id=self.room_id)
            return room.get_unread_count(self.user)
        except ChatRoom.DoesNotExist:
            return 0
    
    @database_sync_to_async
    def save_message(self, content, reply_to_id=None):
        """Save chat message to database"""
        from api.models_chat import ChatMessage, ChatRoom
        
        try:
            room = ChatRoom.objects.get(id=self.room_id)
            
            reply_to = None
            if reply_to_id:
                try:
                    reply_to = ChatMessage.objects.get(id=reply_to_id, room=room)
                except ChatMessage.DoesNotExist:
                    pass
            
            message = ChatMessage.objects.create(
                room=room,
                sender=self.user,
                content=content,
                message_type='text',
                reply_to=reply_to
            )
            
            return message
            
        except ChatRoom.DoesNotExist:
            logger.error(f"Room {self.room_id} not found")
            return None
        except Exception as e:
            logger.error(f"Error saving message: {str(e)}", exc_info=True)
            return None
    
    @database_sync_to_async
    def update_room_timestamp(self):
        """Update room's modified_at timestamp"""
        from api.models_chat import ChatRoom
        
        try:
            ChatRoom.objects.filter(id=self.room_id).update(modified_at=timezone.now())
        except Exception as e:
            logger.error(f"Error updating room timestamp: {str(e)}")
    
    @database_sync_to_async
    def serialize_message(self, message):
        """Convert message object to dict for JSON serialization"""
        return {
            'id': str(message.id),
            'room_id': str(message.room_id),
            'sender': {
                'id': message.sender.id,
                'username': message.sender.username,
                'full_name': message.sender.get_full_name(),
            },
            'content': message.content,
            'message_type': message.message_type,
            'reply_to_id': str(message.reply_to_id) if message.reply_to_id else None,
            'created_at': message.created_at.isoformat(),
            'is_edited': message.is_edited,
            'edited_at': message.edited_at.isoformat() if message.edited_at else None,
        }
    
    @database_sync_to_async
    def set_typing_indicator(self):
        """Set typing indicator for user"""
        from api.models_chat import ChatTypingIndicator
        
        try:
            ChatTypingIndicator.objects.update_or_create(
                room_id=self.room_id,
                user=self.user
            )
        except Exception as e:
            logger.error(f"Error setting typing indicator: {str(e)}")
    
    @database_sync_to_async
    def clear_typing_indicator(self):
        """Clear typing indicator for user"""
        from api.models_chat import ChatTypingIndicator
        
        try:
            ChatTypingIndicator.objects.filter(
                room_id=self.room_id,
                user=self.user
            ).delete()
        except Exception as e:
            logger.error(f"Error clearing typing indicator: {str(e)}")
    
    @database_sync_to_async
    def mark_message_read(self, message_id):
        """Mark a specific message as read"""
        from api.models_chat import ChatMessage
        
        try:
            message = ChatMessage.objects.get(id=message_id, room_id=self.room_id)
            message.mark_read_by(self.user)
        except ChatMessage.DoesNotExist:
            logger.warning(f"Message {message_id} not found")
        except Exception as e:
            logger.error(f"Error marking message read: {str(e)}")
    
    @database_sync_to_async
    def mark_room_read(self):
        """Mark all messages in room as read"""
        from api.models_chat import ChatParticipant
        
        try:
            participant = ChatParticipant.objects.get(
                room_id=self.room_id,
                user=self.user
            )
            participant.mark_as_read()
        except ChatParticipant.DoesNotExist:
            logger.warning(f"Participant not found for user {self.user.id} in room {self.room_id}")
        except Exception as e:
            logger.error(f"Error marking room read: {str(e)}")
    
    @database_sync_to_async
    def send_push_notifications(self, message):
        """Send push notifications to offline participants"""
        from api.models_chat import ChatParticipant
        from api.models import Notification, NotificationVerb
        
        try:
            # Get all participants except sender
            participants = ChatParticipant.objects.filter(
                room_id=self.room_id,
                left_at__isnull=True
            ).exclude(user=self.user).select_related('user')
            
            for participant in participants:
                # Skip if user has muted this room
                if participant.is_muted_now():
                    continue
                
                # Create notification (will be picked up by notification service)
                # Note: This is a simplified version. You may want to create a 
                # dedicated ChatNotification model or extend the existing Notification model
                logger.info(f"Would send push notification to {participant.user.username} for new message")
                
        except Exception as e:
            logger.error(f"Error sending push notifications: {str(e)}", exc_info=True)

