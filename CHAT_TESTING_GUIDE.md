# AriStay Chat System - Testing Guide

**Date**: 2025-10-19  
**Test Users**: `duylam1407` (password: `1`), `user` (password: `Duylam@123`)

---

## 🧪 Manual Testing Checklist

### Pre-Test Setup

1. **Start Redis** (required for WebSocket)
   ```bash
   redis-server
   ```

2. **Start Django Server**
   ```bash
   cd aristay_backend
   python manage.py runserver
   # OR for WebSocket support:
   daphne backend.asgi:application -b 127.0.0.1 -p 8000
   ```

3. **Open Two Browser Windows** (or use incognito for second user)
   - Window 1: Login as `duylam1407` (password: `1`)
   - Window 2: Login as `user` (password: `Duylam@123`)

---

## 📋 Test Scenarios

### Test 1: Creating a Chat Room

**Steps** (as `duylam1407`):
1. Navigate to `/api/chat/`
2. Check if any rooms exist in the sidebar
3. Expected: Empty state or existing rooms

**UI Elements to Check**:
- [ ] Page loads without errors
- [ ] Room list sidebar is visible
- [ ] Search box is functional
- [ ] "No conversations yet" message if empty
- [ ] Responsive on mobile (resize browser)

---

### Test 2: Direct Message Creation (via Admin)

**Note**: Currently, rooms must be created via admin or API first.

**Steps**:
1. Login as admin at `/admin/`
2. Go to "Chat rooms" in admin panel
3. Click "Add Chat Room"
4. Fill in:
   - Room type: `direct`
   - Created by: `duylam1407`
   - Save
5. Go to "Chat participants"
6. Add two participants:
   - Participant 1: User=`duylam1407`, Room=(select room), Is admin=True
   - Participant 2: User=`user`, Room=(select room), Is admin=False

**Expected**: Room now appears in both users' chat interfaces

---

### Test 3: Sending Messages (REST API)

**WebSocket might not work without Daphne, but REST API should work**

**Browser Console Test** (on `/api/chat/` page):
```javascript
// Get the room ID from the sidebar (inspect element)
const roomId = 'YOUR_ROOM_UUID_HERE';

// Send a message via REST API
fetch(`/api/chat/messages/`, {
    method: 'POST',
    headers: {
        'Content-Type': 'application/json',
        'X-CSRFToken': document.querySelector('[name=csrf-token]').content
    },
    body: JSON.stringify({
        room: roomId,
        content: 'Hello from duylam1407!',
        message_type: 'text'
    })
}).then(r => r.json()).then(console.log);
```

---

### Test 4: WebSocket Connection Test

**Check if WebSocket connects** (Browser Console):
```javascript
// Check WebSocket connection
const wsProtocol = window.location.protocol === 'https:' ? 'wss:' : 'ws:';
const roomId = 'YOUR_ROOM_UUID_HERE'; // Get from URL or sidebar
const token = window.ChatApp?.wsToken || 'YOUR_JWT_TOKEN';

console.log('Testing WebSocket...');
console.log('Protocol:', wsProtocol);
console.log('Room ID:', roomId);
console.log('Token:', token ? 'Present' : 'Missing');

// Try to connect
const ws = new WebSocket(`${wsProtocol}//${window.location.host}/ws/chat/${roomId}/?token=${token}`);

ws.onopen = () => console.log('✅ WebSocket Connected!');
ws.onerror = (e) => console.error('❌ WebSocket Error:', e);
ws.onclose = () => console.log('🔌 WebSocket Closed');
ws.onmessage = (e) => console.log('📨 Message:', JSON.parse(e.data));
```

---

## 🐛 Known Issues & Troubleshooting

### Issue 1: WebSocket Not Connecting

**Symptoms**:
- Messages don't appear in real-time
- Console shows WebSocket errors
- "Connection error" status in UI

**Cause**: Django's `runserver` may not fully support WebSocket connections

**Solution**:
```bash
# Use Daphne instead of runserver
pip install daphne
daphne backend.asgi:application -b 127.0.0.1 -p 8000
```

---

### Issue 2: No Rooms Visible

**Symptoms**:
- "No conversations yet" message appears
- Room list is empty

**Cause**: No rooms created yet, or user is not a participant

**Solution**:
1. Create room via admin panel
2. Add both users as participants
3. Refresh `/api/chat/` page

---

### Issue 3: Cannot Send Messages

**Symptoms**:
- Send button doesn't work
- No messages appear in chat area

**Debugging**:
1. Open browser console (F12)
2. Look for JavaScript errors
3. Check if `ChatApp.currentRoom` is set
4. Verify JWT token exists: `console.log(ChatApp.wsToken)`

---

### Issue 4: JWT Token Missing

**Symptoms**:
- Console error: "Failed to generate WebSocket token"
- WebSocket connection fails with 403

**Solution**:
```python
# In api/views.py, verify chat_view generates token
from rest_framework_simplejwt.tokens import AccessToken

try:
    access_token = AccessToken.for_user(request.user)
    ws_token = str(access_token)
except Exception as e:
    logger.error(f"Failed to generate WebSocket token: {str(e)}")
```

---

## 🎨 UI Elements to Test

### Desktop View (> 768px)

- [ ] Room list sidebar (320px width)
- [ ] Chat area takes remaining space
- [ ] Navigation bar works
- [ ] Buttons are clickable
- [ ] Text is readable
- [ ] Modal opens for photos (if implemented)

### Mobile View (< 768px)

- [ ] Room list is full width
- [ ] Room list slides in/out
- [ ] Mobile menu toggle works
- [ ] Touch targets are 44x44px minimum
- [ ] Text input works on mobile keyboard
- [ ] Send button is accessible
- [ ] No horizontal scrolling

### Interactive Elements

- [ ] Room selection highlights active room
- [ ] Message input auto-resizes
- [ ] Send button enables/disables correctly
- [ ] Enter key sends message
- [ ] Shift+Enter creates new line
- [ ] Room search filters rooms
- [ ] Hover effects work on desktop
- [ ] Loading states display correctly

---

## 🧩 Expected Behaviors

### When Selecting a Room:

1. Room item gets `active` class (purple background)
2. Chat header shows room name
3. Messages load in the chat area
4. Input area becomes visible
5. WebSocket connects (if Daphne running)
6. Connection status shows "Connected"

### When Sending a Message:

1. Message appears in chat area immediately
2. Message is marked as "own" (right-aligned, purple)
3. WebSocket broadcasts to other participants
4. Other user sees message in real-time
5. Timestamp is displayed correctly
6. Input clears after sending

### When Receiving a Message:

1. Message appears with animation (slideIn)
2. Message is left-aligned with sender name
3. Unread badge updates (if implemented)
4. Notification might appear (if implemented)

---

## 🔍 Detailed Testing Steps

### Scenario: Two Users Chatting

**Setup**:
1. Window 1: User `duylam1407` logged in at `/api/chat/`
2. Window 2: User `user` logged in at `/api/chat/`
3. Both users in the same room

**Test Steps**:

1. **User 1 (duylam1407) sends a message**:
   - Type: "Hello from duylam1407!"
   - Click Send or press Enter
   - **Expected**: Message appears on right side (purple bubble)

2. **User 2 (user) should receive the message**:
   - **Expected**: Message appears on left side (white bubble)
   - **Expected**: Sender name shows "duylam1407"
   - **Expected**: Timestamp displays correctly

3. **User 2 (user) replies**:
   - Type: "Hi duylam1407! Got your message."
   - Click Send
   - **Expected**: Message appears on right side for User 2

4. **User 1 (duylam1407) should receive the reply**:
   - **Expected**: Message appears on left side for User 1
   - **Expected**: Sender name shows "user"

5. **Test rapid messaging**:
   - Both users send multiple messages quickly
   - **Expected**: All messages appear in correct order
   - **Expected**: No messages are lost
   - **Expected**: UI doesn't break or freeze

6. **Test long messages**:
   - Send a very long message (500+ characters)
   - **Expected**: Message wraps correctly
   - **Expected**: No horizontal scrolling
   - **Expected**: Bubble adjusts size

7. **Test special characters**:
   - Send: `Hello! @user #test <script>alert('xss')</script>`
   - **Expected**: Special characters are escaped
   - **Expected**: No XSS vulnerability
   - **Expected**: Emoji work: 😀 🎉 💬

---

## 🚨 Critical Issues to Watch For

### Security Issues:
- [ ] XSS attacks (script injection in messages)
- [ ] CSRF token validation
- [ ] JWT token exposure in console
- [ ] Unauthorized room access

### Performance Issues:
- [ ] Slow message loading (> 2 seconds)
- [ ] Memory leaks (check browser memory)
- [ ] WebSocket reconnection loops
- [ ] Excessive API calls

### UI/UX Issues:
- [ ] Text overflow without wrapping
- [ ] Broken layout on mobile
- [ ] Buttons not clickable
- [ ] Poor contrast (text hard to read)
- [ ] Loading states missing
- [ ] Error messages not displayed

---

## 📊 Testing Results Template

```markdown
## Test Session Report

**Date**: [Date]
**Tester**: [Your Name]
**Server**: `runserver` or `daphne`
**Redis**: Running? Yes/No

### Test Results:

| Test | Status | Notes |
|------|--------|-------|
| Page loads | ✅/❌ | |
| Room list displays | ✅/❌ | |
| Room selection works | ✅/❌ | |
| WebSocket connects | ✅/❌ | |
| Messages send (User 1) | ✅/❌ | |
| Messages receive (User 2) | ✅/❌ | |
| Bidirectional chat | ✅/❌ | |
| Mobile responsive | ✅/❌ | |
| No JavaScript errors | ✅/❌ | |
| No console warnings | ✅/❌ | |

### Issues Found:
1. [Describe issue]
2. [Describe issue]

### Screenshots:
[Attach screenshots of any issues]
```

---

## 🛠️ Quick Fixes for Common Issues

### Fix 1: WebSocket 404 Error

**Edit** `backend/urls.py`:
```python
from django.urls import path, include

urlpatterns = [
    # ... existing patterns ...
    path('api/', include('api.urls')),
]
```

**Ensure** WebSocket routing is in `backend/asgi.py` (already done).

---

### Fix 2: CSRF Token Missing

**Edit** `chat/chatbox.html`:
```javascript
function getCsrfToken() {
    return document.querySelector('[name=csrf-token]')?.content || 
           document.querySelector('[name=csrfmiddlewaretoken]')?.value ||
           '';
}
```

---

### Fix 3: Room Not Loading

**Browser Console**:
```javascript
// Check if room data exists
console.log('Rooms:', document.querySelectorAll('.room-item').length);

// Manually select first room
const firstRoom = document.querySelector('.room-item');
if (firstRoom) {
    firstRoom.click();
}
```

---

## ✅ Success Criteria

The chat system is working correctly if:

1. ✅ Both users can access `/api/chat/` without errors
2. ✅ Room list displays correctly
3. ✅ Selecting a room loads messages
4. ✅ Messages can be sent via REST API (even without WebSocket)
5. ✅ Messages appear in the chat area
6. ✅ UI is responsive on mobile
7. ✅ No JavaScript errors in console
8. ✅ CSRF protection works
9. ✅ JWT authentication succeeds

**Bonus** (requires Daphne):
10. ✅ WebSocket connects successfully
11. ✅ Real-time message delivery works
12. ✅ Typing indicators function
13. ✅ Read receipts update

---

## 📝 Next Steps After Testing

If issues are found:
1. Document the issue with screenshots
2. Check browser console for errors
3. Check server logs for errors
4. Create a bug report with reproduction steps
5. Prioritize critical issues (can't send messages, can't access)

If everything works:
1. Test with more users (3-5 people)
2. Test on different browsers (Chrome, Firefox, Safari)
3. Test on real mobile devices
4. Load test with many messages
5. Deploy to staging for QA

---

**Testing Completed**: ⬜  
**Issues Found**: [Number]  
**Critical Issues**: [Number]  
**Status**: ⬜ Ready for Production | ⬜ Needs Fixes


