# AriStay Chat API Documentation for Flutter/iOS

**Version**: 1.0.0  
**Last Updated**: 2025-10-19  
**Base URL**: `https://aristay-internal.cloud/api`

---

## 📋 Table of Contents

1. [Authentication](#authentication)
2. [REST API Endpoints](#rest-api-endpoints)
   - [Chat Rooms](#chat-rooms)
   - [Messages](#messages)
   - [Participants](#participants)
3. [WebSocket Protocol](#websocket-protocol)
4. [Data Models](#data-models)
5. [Flutter/Dart Examples](#flutterdart-examples)
6. [Error Handling](#error-handling)
7. [Best Practices](#best-practices)

---

## 🔐 Authentication

All API requests require JWT authentication.

### Getting JWT Tokens

```http
POST /api/token/
Content-Type: application/json

{
  "username": "user@example.com",
  "password": "password123"
}
```

**Response**:
```json
{
  "access": "eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9...",
  "refresh": "eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9..."
}
```

### Using Tokens

**REST API**:
```http
GET /api/chat/rooms/
Authorization: Bearer <access_token>
```

**WebSocket**:
```
ws://aristay-internal.cloud/ws/chat/<room_id>/?token=<access_token>
```

### Token Refresh

```http
POST /api/token/refresh/
Content-Type: application/json

{
  "refresh": "<refresh_token>"
}
```

---

## 🔌 REST API Endpoints

### Chat Rooms

#### List All Rooms

```http
GET /api/chat/rooms/
Authorization: Bearer <access_token>
```

**Query Parameters**:
- `room_type` (optional): `direct`, `group`, `task`, `property`
- `search` (optional): Search in room names
- `include_archived` (optional): `true` to include archived rooms

**Response**:
```json
{
  "count": 5,
  "next": null,
  "previous": null,
  "results": [
    {
      "id": "550e8400-e29b-41d4-a716-446655440000",
      "display_name": "John Doe",
      "room_type": "direct",
      "is_active": true,
      "unread_count": 3,
      "last_message_preview": "Hey, how are you?",
      "last_message_time": "2025-10-19T14:30:00Z",
      "participant_count": 2,
      "modified_at": "2025-10-19T14:30:00Z"
    }
  ]
}
```

#### Create New Room

```http
POST /api/chat/rooms/
Authorization: Bearer <access_token>
Content-Type: application/json

{
  "room_type": "direct",
  "participant_ids": [5]
}
```

**For Group Chat**:
```json
{
  "name": "Project Team",
  "room_type": "group",
  "participant_ids": [5, 7, 9]
}
```

**For Task Discussion**:
```json
{
  "room_type": "task",
  "task": 42,
  "participant_ids": [5, 7]
}
```

**Response**: Full room object with participants

#### Get Room Details

```http
GET /api/chat/rooms/{room_id}/
Authorization: Bearer <access_token>
```

**Response**:
```json
{
  "id": "550e8400-e29b-41d4-a716-446655440000",
  "name": "",
  "room_type": "direct",
  "task": null,
  "property": null,
  "created_at": "2025-10-19T10:00:00Z",
  "modified_at": "2025-10-19T14:30:00Z",
  "created_by": {
    "id": 3,
    "username": "alice",
    "full_name": "Alice Johnson",
    "email": "alice@example.com"
  },
  "is_active": true,
  "archived_at": null,
  "participants": [
    {
      "id": 1,
      "user": {
        "id": 3,
        "username": "alice",
        "full_name": "Alice Johnson",
        "email": "alice@example.com"
      },
      "room": "550e8400-e29b-41d4-a716-446655440000",
      "joined_at": "2025-10-19T10:00:00Z",
      "last_read_at": "2025-10-19T14:25:00Z",
      "is_admin": true,
      "unread_count": 0,
      "is_muted": false,
      "left_at": null
    },
    {
      "id": 2,
      "user": {
        "id": 5,
        "username": "bob",
        "full_name": "Bob Smith",
        "email": "bob@example.com"
      },
      "room": "550e8400-e29b-41d4-a716-446655440000",
      "joined_at": "2025-10-19T10:00:00Z",
      "last_read_at": "2025-10-19T14:20:00Z",
      "is_admin": false,
      "unread_count": 3,
      "is_muted": false,
      "left_at": null
    }
  ],
  "participant_count": 2,
  "last_message": {
    "id": "660e8400-e29b-41d4-a716-446655440001",
    "sender": {
      "id": 5,
      "username": "bob",
      "full_name": "Bob Smith",
      "email": "bob@example.com"
    },
    "content": "Hey, how are you?",
    "message_type": "text",
    "created_at": "2025-10-19T14:30:00Z",
    "is_edited": false
  },
  "unread_count": 3,
  "display_name": "Bob Smith"
}
```

#### Mark Room as Read

```http
POST /api/chat/rooms/{room_id}/mark_read/
Authorization: Bearer <access_token>
```

**Response**:
```json
{
  "message": "Room marked as read"
}
```

#### Leave Room

```http
POST /api/chat/rooms/{room_id}/leave/
Authorization: Bearer <access_token>
```

**Response**:
```json
{
  "message": "Successfully left the room"
}
```

#### Archive Room

```http
POST /api/chat/rooms/{room_id}/archive/
Authorization: Bearer <access_token>
```

**Response**: Updated room object

#### Get Room Statistics

```http
GET /api/chat/rooms/{room_id}/stats/
Authorization: Bearer <access_token>
```

**Response**:
```json
{
  "message_count": 142,
  "participant_count": 2,
  "unread_count": 3,
  "last_message_at": "2025-10-19T14:30:00Z"
}
```

---

### Messages

#### List Messages in Room

```http
GET /api/chat/messages/?room={room_id}
Authorization: Bearer <access_token>
```

**Query Parameters**:
- `room` (required): Room UUID
- `page` (optional): Page number (default: 1)
- `page_size` (optional): Results per page (default: 50, max: 100)
- `ordering` (optional): `created_at` (oldest first) or `-created_at` (newest first)

**Response**:
```json
{
  "count": 142,
  "next": "https://aristay-internal.cloud/api/chat/messages/?page=2&room=550e8400...",
  "previous": null,
  "results": [
    {
      "id": "660e8400-e29b-41d4-a716-446655440001",
      "room": "550e8400-e29b-41d4-a716-446655440000",
      "sender": {
        "id": 5,
        "username": "bob",
        "full_name": "Bob Smith",
        "email": "bob@example.com"
      },
      "message_type": "text",
      "content": "Hey, how are you?",
      "attachment": null,
      "attachment_name": "",
      "attachment_size": null,
      "reply_to": null,
      "created_at": "2025-10-19T14:30:00Z",
      "modified_at": "2025-10-19T14:30:00Z",
      "is_edited": false,
      "edited_at": null,
      "is_deleted": false,
      "deleted_at": null,
      "is_read": true,
      "read_count": 1,
      "read_by": {
        "3": "2025-10-19T14:31:00Z"
      }
    }
  ]
}
```

#### Send Message

```http
POST /api/chat/messages/
Authorization: Bearer <access_token>
Content-Type: application/json

{
  "room": "550e8400-e29b-41d4-a716-446655440000",
  "content": "Hello from Flutter!",
  "message_type": "text"
}
```

**For Reply**:
```json
{
  "room": "550e8400-e29b-41d4-a716-446655440000",
  "content": "Great question!",
  "reply_to": "660e8400-e29b-41d4-a716-446655440001"
}
```

**For Image/File** (multipart/form-data):
```http
POST /api/chat/messages/
Authorization: Bearer <access_token>
Content-Type: multipart/form-data

room: 550e8400-e29b-41d4-a716-446655440000
content: Check out this photo!
attachment: <file>
```

**Response**: Full message object

#### Get Message Details

```http
GET /api/chat/messages/{message_id}/
Authorization: Bearer <access_token>
```

#### Edit Message

```http
PATCH /api/chat/messages/{message_id}/
Authorization: Bearer <access_token>
Content-Type: application/json

{
  "content": "Updated message content"
}
```

**Note**: Only sender can edit. Auto-sets `is_edited: true` and `edited_at`.

#### Delete Message

```http
DELETE /api/chat/messages/{message_id}/
Authorization: Bearer <access_token>
```

**Note**: Soft delete. Sets content to "[Message deleted]", `is_deleted: true`.

#### Mark Message as Read

```http
POST /api/chat/messages/{message_id}/mark_read/
Authorization: Bearer <access_token>
```

#### Search Messages

```http
GET /api/chat/messages/search/?q=hello&room={room_id}
Authorization: Bearer <access_token>
```

**Query Parameters**:
- `q` (required): Search query (min 3 characters)
- `room` (optional): Limit to specific room

---

### Participants

#### List Participants

```http
GET /api/chat/participants/?room={room_id}
Authorization: Bearer <access_token>
```

#### Add Participant (Admin Only)

```http
POST /api/chat/participants/
Authorization: Bearer <access_token>
Content-Type: application/json

{
  "room": "550e8400-e29b-41d4-a716-446655440000",
  "user": 7,
  "is_admin": false
}
```

#### Remove Participant (Admin Only)

```http
DELETE /api/chat/participants/{participant_id}/
Authorization: Bearer <access_token>
```

#### Mute/Unmute Notifications

```http
POST /api/chat/participants/{participant_id}/mute/
Authorization: Bearer <access_token>
Content-Type: application/json

{
  "muted": true,
  "muted_until": "2025-10-20T14:30:00Z"
}
```

**Unmute**:
```json
{
  "muted": false
}
```

---

## 🔌 WebSocket Protocol

### Connection

```dart
final wsUrl = 'wss://aristay-internal.cloud/ws/chat/$roomId/?token=$accessToken';
final channel = WebSocketChannel.connect(Uri.parse(wsUrl));
```

### Event Types

#### 1. Connection Established (Server → Client)

Sent when connection is successful.

```json
{
  "type": "connection_established",
  "room_id": "550e8400-e29b-41d4-a716-446655440000",
  "unread_count": 3,
  "user_id": 5,
  "username": "bob"
}
```

#### 2. Chat Message (Bidirectional)

**Client → Server** (Send message):
```json
{
  "type": "chat_message",
  "message": "Hello from Flutter!",
  "reply_to": "660e8400-e29b-41d4-a716-446655440001"
}
```

**Server → Client** (Receive message):
```json
{
  "type": "chat_message",
  "message": {
    "id": "770e8400-e29b-41d4-a716-446655440002",
    "room_id": "550e8400-e29b-41d4-a716-446655440000",
    "sender": {
      "id": 3,
      "username": "alice",
      "full_name": "Alice Johnson"
    },
    "content": "Hello from Flutter!",
    "message_type": "text",
    "reply_to_id": null,
    "created_at": "2025-10-19T14:35:00Z",
    "is_edited": false,
    "edited_at": null
  }
}
```

#### 3. Typing Indicator (Bidirectional)

**Client → Server** (Start typing):
```json
{
  "type": "typing",
  "is_typing": true
}
```

**Client → Server** (Stop typing):
```json
{
  "type": "typing",
  "is_typing": false
}
```

**Server → Client** (Other user typing):
```json
{
  "type": "typing",
  "user_id": 5,
  "username": "bob",
  "is_typing": true
}
```

#### 4. Read Receipt (Bidirectional)

**Client → Server** (Mark as read):
```json
{
  "type": "read_receipt",
  "message_id": "660e8400-e29b-41d4-a716-446655440001"
}
```

**Server → Client** (User read message):
```json
{
  "type": "read_receipt",
  "message_id": "660e8400-e29b-41d4-a716-446655440001",
  "user_id": 3,
  "read_at": "2025-10-19T14:36:00Z"
}
```

#### 5. Mark Room Read (Client → Server)

```json
{
  "type": "mark_room_read"
}
```

**Server → Client** (Confirmation):
```json
{
  "type": "room_marked_read",
  "room_id": "550e8400-e29b-41d4-a716-446655440000"
}
```

#### 6. Error (Server → Client)

```json
{
  "type": "error",
  "message": "Failed to process message"
}
```

---

## 📊 Data Models

### ChatRoom

```dart
class ChatRoom {
  final String id;
  final String? name;
  final String roomType; // 'direct', 'group', 'task', 'property'
  final int? taskId;
  final int? propertyId;
  final DateTime createdAt;
  final DateTime modifiedAt;
  final UserBrief? createdBy;
  final bool isActive;
  final DateTime? archivedAt;
  final List<ChatParticipant> participants;
  final int participantCount;
  final ChatMessage? lastMessage;
  final int unreadCount;
  final String displayName;
}
```

### ChatMessage

```dart
class ChatMessage {
  final String id;
  final String roomId;
  final UserBrief sender;
  final String messageType; // 'text', 'image', 'file', 'system'
  final String content;
  final String? attachmentUrl;
  final String? attachmentName;
  final int? attachmentSize;
  final String? replyToId;
  final DateTime createdAt;
  final DateTime modifiedAt;
  final bool isEdited;
  final DateTime? editedAt;
  final bool isDeleted;
  final DateTime? deletedAt;
  final bool isRead;
  final int readCount;
  final Map<String, String> readBy; // userId: timestamp
}
```

### ChatParticipant

```dart
class ChatParticipant {
  final int id;
  final UserBrief user;
  final String roomId;
  final DateTime joinedAt;
  final DateTime? lastReadAt;
  final bool isAdmin;
  final int unreadCount;
  final bool isMuted;
  final DateTime? mutedUntil;
  final DateTime? leftAt;
}
```

### UserBrief

```dart
class UserBrief {
  final int id;
  final String username;
  final String fullName;
  final String email;
}
```

---

## 📱 Flutter/Dart Examples

### Complete Chat Implementation

```dart
import 'package:http/http.dart' as http;
import 'package:web_socket_channel/web_socket_channel.dart';
import 'dart:convert';

class ChatService {
  final String baseUrl = 'https://aristay-internal.cloud/api';
  final String wsBaseUrl = 'wss://aristay-internal.cloud/ws';
  String? accessToken;
  
  // WebSocket channel
  WebSocketChannel? _channel;
  
  /// Initialize with JWT token
  void setAccessToken(String token) {
    accessToken = token;
  }
  
  /// Get authorization headers
  Map<String, String> get headers => {
    'Authorization': 'Bearer $accessToken',
    'Content-Type': 'application/json',
  };
  
  /// List all chat rooms
  Future<List<ChatRoom>> getRooms() async {
    final response = await http.get(
      Uri.parse('$baseUrl/chat/rooms/'),
      headers: headers,
    );
    
    if (response.statusCode == 200) {
      final data = json.decode(response.body);
      return (data['results'] as List)
          .map((json) => ChatRoom.fromJson(json))
          .toList();
    } else {
      throw Exception('Failed to load rooms');
    }
  }
  
  /// Get room details
  Future<ChatRoom> getRoom(String roomId) async {
    final response = await http.get(
      Uri.parse('$baseUrl/chat/rooms/$roomId/'),
      headers: headers,
    );
    
    if (response.statusCode == 200) {
      return ChatRoom.fromJson(json.decode(response.body));
    } else {
      throw Exception('Failed to load room');
    }
  }
  
  /// Create new direct message room
  Future<ChatRoom> createDirectMessage(int userId) async {
    final response = await http.post(
      Uri.parse('$baseUrl/chat/rooms/'),
      headers: headers,
      body: json.encode({
        'room_type': 'direct',
        'participant_ids': [userId],
      }),
    );
    
    if (response.statusCode == 201) {
      return ChatRoom.fromJson(json.decode(response.body));
    } else {
      throw Exception('Failed to create room');
    }
  }
  
  /// Get messages in room
  Future<List<ChatMessage>> getMessages(String roomId, {int page = 1}) async {
    final response = await http.get(
      Uri.parse('$baseUrl/chat/messages/?room=$roomId&page=$page&page_size=50&ordering=created_at'),
      headers: headers,
    );
    
    if (response.statusCode == 200) {
      final data = json.decode(response.body);
      return (data['results'] as List)
          .map((json) => ChatMessage.fromJson(json))
          .toList();
    } else {
      throw Exception('Failed to load messages');
    }
  }
  
  /// Send message via REST API
  Future<ChatMessage> sendMessage(String roomId, String content, {String? replyToId}) async {
    final response = await http.post(
      Uri.parse('$baseUrl/chat/messages/'),
      headers: headers,
      body: json.encode({
        'room': roomId,
        'content': content,
        'message_type': 'text',
        if (replyToId != null) 'reply_to': replyToId,
      }),
    );
    
    if (response.statusCode == 201) {
      return ChatMessage.fromJson(json.decode(response.body));
    } else {
      throw Exception('Failed to send message');
    }
  }
  
  /// Mark room as read
  Future<void> markRoomAsRead(String roomId) async {
    await http.post(
      Uri.parse('$baseUrl/chat/rooms/$roomId/mark_read/'),
      headers: headers,
    );
  }
  
  /// Connect to WebSocket
  void connectWebSocket(String roomId, {
    required Function(Map<String, dynamic>) onMessage,
    required Function() onConnected,
    required Function(String) onError,
  }) {
    final wsUrl = '$wsBaseUrl/chat/$roomId/?token=$accessToken';
    
    try {
      _channel = WebSocketChannel.connect(Uri.parse(wsUrl));
      
      _channel!.stream.listen(
        (message) {
          final data = json.decode(message);
          
          if (data['type'] == 'connection_established') {
            onConnected();
          }
          
          onMessage(data);
        },
        onError: (error) {
          onError(error.toString());
        },
        onDone: () {
          // Handle disconnection
          print('WebSocket disconnected');
        },
      );
    } catch (e) {
      onError(e.toString());
    }
  }
  
  /// Send message via WebSocket
  void sendMessageWS(String content, {String? replyToId}) {
    if (_channel != null) {
      _channel!.sink.add(json.encode({
        'type': 'chat_message',
        'message': content,
        if (replyToId != null) 'reply_to': replyToId,
      }));
    }
  }
  
  /// Send typing indicator
  void sendTypingIndicator(bool isTyping) {
    if (_channel != null) {
      _channel!.sink.add(json.encode({
        'type': 'typing',
        'is_typing': isTyping,
      }));
    }
  }
  
  /// Close WebSocket
  void closeWebSocket() {
    _channel?.sink.close();
    _channel = null;
  }
}
```

### Usage Example

```dart
class ChatScreen extends StatefulWidget {
  final String roomId;
  
  const ChatScreen({Key? key, required this.roomId}) : super(key: key);
  
  @override
  _ChatScreenState createState() => _ChatScreenState();
}

class _ChatScreenState extends State<ChatScreen> {
  final ChatService _chatService = ChatService();
  final TextEditingController _messageController = TextEditingController();
  List<ChatMessage> messages = [];
  bool isTyping = false;
  String? typingUser;
  
  @override
  void initState() {
    super.initState();
    _loadMessages();
    _connectWebSocket();
  }
  
  Future<void> _loadMessages() async {
    try {
      final loadedMessages = await _chatService.getMessages(widget.roomId);
      setState(() {
        messages = loadedMessages;
      });
    } catch (e) {
      print('Error loading messages: $e');
    }
  }
  
  void _connectWebSocket() {
    _chatService.connectWebSocket(
      widget.roomId,
      onMessage: (data) {
        if (data['type'] == 'chat_message') {
          setState(() {
            messages.add(ChatMessage.fromJson(data['message']));
          });
        } else if (data['type'] == 'typing') {
          setState(() {
            isTyping = data['is_typing'];
            typingUser = data['username'];
          });
        }
      },
      onConnected: () {
        print('Connected to chat');
      },
      onError: (error) {
        print('WebSocket error: $error');
      },
    );
  }
  
  void _sendMessage() {
    final content = _messageController.text.trim();
    if (content.isEmpty) return;
    
    _chatService.sendMessageWS(content);
    _messageController.clear();
  }
  
  @override
  void dispose() {
    _chatService.closeWebSocket();
    _messageController.dispose();
    super.dispose();
  }
  
  @override
  Widget build(BuildContext context) {
    return Scaffold(
      appBar: AppBar(
        title: Text('Chat'),
        subtitle: isTyping ? Text('$typingUser is typing...') : null,
      ),
      body: Column(
        children: [
          Expanded(
            child: ListView.builder(
              itemCount: messages.length,
              itemBuilder: (context, index) {
                final message = messages[index];
                return MessageBubble(message: message);
              },
            ),
          ),
          Container(
            padding: EdgeInsets.all(8),
            child: Row(
              children: [
                Expanded(
                  child: TextField(
                    controller: _messageController,
                    decoration: InputDecoration(
                      hintText: 'Type a message...',
                      border: OutlineInputBorder(),
                    ),
                    onChanged: (text) {
                      // Send typing indicator
                      _chatService.sendTypingIndicator(text.isNotEmpty);
                    },
                  ),
                ),
                SizedBox(width: 8),
                IconButton(
                  icon: Icon(Icons.send),
                  onPressed: _sendMessage,
                ),
              ],
            ),
          ),
        ],
      ),
    );
  }
}
```

---

## ❌ Error Handling

### HTTP Status Codes

- `200 OK` - Success
- `201 Created` - Resource created
- `400 Bad Request` - Invalid input
- `401 Unauthorized` - Invalid/expired token
- `403 Forbidden` - No permission
- `404 Not Found` - Resource not found
- `500 Internal Server Error` - Server error

### Error Response Format

```json
{
  "error": "Error message",
  "detail": "Detailed error description"
}
```

### Handling Errors in Flutter

```dart
try {
  final rooms = await chatService.getRooms();
} on http.ClientException catch (e) {
  // Network error
  print('Network error: $e');
} on FormatException catch (e) {
  // JSON parsing error
  print('Parse error: $e');
} catch (e) {
  // Other errors
  print('Error: $e');
}
```

---

## ✅ Best Practices

### 1. Token Management

- Store tokens securely using `flutter_secure_storage`
- Refresh tokens before expiry
- Handle 401 errors by refreshing token

### 2. WebSocket Reconnection

```dart
void _handleReconnection() {
  Future.delayed(Duration(seconds: 2), () {
    if (_shouldReconnect) {
      _connectWebSocket();
    }
  });
}
```

### 3. Message Pagination

- Load messages in chunks (50 per page)
- Implement infinite scroll
- Cache messages locally

### 4. Typing Indicators

- Debounce typing events (send after 500ms of inactivity)
- Clear indicator after 10 seconds

### 5. Offline Support

- Queue messages when offline
- Sync when connection restored
- Show pending status

### 6. Optimization

- Use `ListView.builder` for message lists
- Lazy load images
- Implement message caching
- Use WebSocket for real-time, REST for history

### 7. Security

- Always validate JWT tokens
- Never log sensitive data
- Use HTTPS/WSS in production

---

## 📞 Support

For issues or questions:
- Email: support@aristay.com
- Docs: https://docs.aristay.com
- API Status: https://status.aristay.com

---

**Last Updated**: 2025-10-19  
**API Version**: 1.0.0  
**Maintained by**: AriStay Development Team

