# 🧪 Chat Testing Instructions - Quick Start

**Date**: 2025-10-19  
**Test Users**: 
- User 1: `duylam1407` (password: `1`)
- User 2: `user` (password: `Duylam@123`)

---

## 🚀 Quick Start (5 Minutes)

### Step 1: Start Redis (Required for WebSocket)
```bash
redis-server
```
**Leave this running in a terminal window.**

### Step 2: Start Server with WebSocket Support
```bash
cd /Users/duylam1407/Workspace/SJSU/aristay_app/aristay_backend
daphne backend.asgi:application -b 127.0.0.1 -p 8000
```
**Use Daphne (not `runserver`) for WebSocket support!**

### Step 3: Create a Test Room via Django Admin

1. **Open**: http://localhost:8000/admin/
2. **Login**: as `duylam1407` (password: `1`)
3. **Navigate**: API → Chat rooms → Add Chat room
4. **Fill in**:
   - Room type: `direct`
   - Created by: `duylam1407`
   - Click **Save**
5. **Copy the Room ID** from the URL (UUID format)

### Step 4: Add Participants

1. **Navigate**: API → Chat participants → Add Chat participant
2. **Add Participant 1**:
   - Room: (select the room you just created)
   - User: `duylam1407`
   - Is admin: ✅ checked
   - Click **Save and add another**
3. **Add Participant 2**:
   - Room: (same room)
   - User: `user`
   - Is admin: ⬜ unchecked
   - Click **Save**

### Step 5: Open Chat in Two Browser Windows

**Window 1** (Regular browser):
1. Go to: http://localhost:8000/api/chat/
2. Login as: `duylam1407` (password: `1`)
3. You should see the room in the sidebar
4. Click on the room to select it

**Window 2** (Incognito/Private mode):
1. Go to: http://localhost:8000/api/chat/
2. Login as: `user` (password: `Duylam@123`)
3. You should see the same room in the sidebar
4. Click on the room to select it

### Step 6: Start Chatting! 💬

**In Window 1** (duylam1407):
- Type: "Hello from duylam1407!"
- Press Enter or click Send
- **Expected**: Message appears on the right (purple bubble)

**In Window 2** (user):
- **Expected**: Message appears on the left (white bubble) with sender name
- Type: "Hi! Got your message."
- Press Enter

**In Window 1**:
- **Expected**: Reply appears on the left

---

## 🔍 Troubleshooting

### Problem: No rooms visible

**Solution**: Create a room and add participants (see Step 3-4 above)

### Problem: WebSocket won't connect

**Check**:
1. Is Redis running? `redis-cli ping` should return `PONG`
2. Are you using Daphne? (not `runserver`)
3. Open browser console (F12) and look for WebSocket errors

**Browser Console Test**:
```javascript
// Paste this in console on /api/chat/ page
console.log('User ID:', ChatApp.userId);
console.log('Username:', ChatApp.username);
console.log('Token:', ChatApp.wsToken ? 'Present' : 'Missing');
console.log('Current Room:', ChatApp.currentRoom);
console.log('WebSocket State:', ChatApp.ws?.readyState);
```

### Problem: Messages don't send

**Check**:
1. Is a room selected? (Should see input box at bottom)
2. Is WebSocket connected? (Check connection status at top)
3. Open browser console for JavaScript errors

**Manual Test** (Browser Console):
```javascript
// Force send a message
ChatApp.ws.send(JSON.stringify({
    type: 'chat_message',
    message: 'Test message from console'
}));
```

---

## 📊 Run Diagnostics

**Paste this in browser console** on `/api/chat/` page:

```javascript
// Copy contents from CHAT_BROWSER_DIAGNOSTICS.js
// Or run this quick check:
console.log('Chat App State:', {
    userId: ChatApp.userId,
    username: ChatApp.username,
    hasToken: !!ChatApp.wsToken,
    currentRoom: ChatApp.currentRoom,
    wsState: ChatApp.ws?.readyState,
    rooms: document.querySelectorAll('.room-item').length
});
```

---

## ✅ Expected Behavior

### When Everything Works:

1. **Page loads**: No JavaScript errors in console
2. **Rooms visible**: Room appears in left sidebar
3. **Room selection**: Clicking room shows input box
4. **Connection**: Status shows "Connected" briefly
5. **Sending**: Messages appear immediately
6. **Receiving**: Other user sees messages in real-time
7. **Bidirectional**: Both users can send/receive
8. **Timestamps**: Show correct local time
9. **Alignment**: Own messages on right (purple), others on left (white)
10. **No lag**: Messages appear within 1 second

---

## 🐛 Known Issues

### Issue 1: Using `runserver` instead of Daphne

**Symptom**: WebSocket connections fail  
**Solution**: Use Daphne (see Step 2)

### Issue 2: Redis not running

**Symptom**: "Connection error" status  
**Solution**: Start Redis (`redis-server`)

### Issue 3: No rooms visible

**Symptom**: "No conversations yet" message  
**Solution**: Create room via admin (see Step 3-4)

### Issue 4: JWT token missing

**Symptom**: WebSocket 403 error  
**Check**: `api/views.py:chat_view()` generates token correctly

---

## 📸 What to Look For

### UI Issues to Report:

- [ ] Text overflow (messages too long)
- [ ] Layout breaks on mobile
- [ ] Buttons not clickable
- [ ] Colors hard to read
- [ ] Alignment issues
- [ ] Missing icons or emojis
- [ ] Scrolling doesn't work
- [ ] Input box doesn't resize
- [ ] Room list doesn't filter

### Functional Issues to Report:

- [ ] Messages don't send
- [ ] Messages don't receive
- [ ] WebSocket won't connect
- [ ] Page crashes or freezes
- [ ] JavaScript errors in console
- [ ] Slow performance (> 2sec delay)
- [ ] Messages appear out of order
- [ ] Messages disappear

---

## 📝 Report Template

```markdown
## Chat Testing Report

**Date**: [Date]
**Tester**: [Your Name]
**Users Tested**: duylam1407, user
**Server**: Daphne ✅ / runserver ⬜

### Test Results:
- Page loads: ✅/❌
- Room visible: ✅/❌
- WebSocket connects: ✅/❌
- Messages send: ✅/❌
- Messages receive: ✅/❌
- Real-time chat works: ✅/❌

### Issues Found:
1. [Description + screenshot]

### Browser Console Errors:
```
[Paste any errors here]
```

### Overall: Works ✅ / Needs fixes ❌
```

---

## 🎯 Success Criteria

✅ **Chat is working if**:
- Both users can access /api/chat/
- Room appears in sidebar
- Selecting room shows input
- WebSocket connects (status: "Connected")
- User 1 sends message → User 2 receives it
- User 2 sends message → User 1 receives it
- Messages appear within 1 second
- No JavaScript errors
- UI is responsive

---

## 📞 Need Help?

1. Check `CHAT_TESTING_GUIDE.md` for detailed instructions
2. Run diagnostics: paste `CHAT_BROWSER_DIAGNOSTICS.js` in console
3. Check server logs for errors
4. Check browser console for JavaScript errors
5. Verify Redis is running: `redis-cli ping`
6. Verify using Daphne (not runserver)

---

**Quick Recap**:
1. Start Redis: `redis-server`
2. Start Daphne: `daphne backend.asgi:application -b 127.0.0.1 -p 8000`
3. Create room + participants via admin
4. Open `/api/chat/` in two browsers
5. Login as both users
6. Select room in both
7. Start chatting!

🎉 **Happy Testing!**

