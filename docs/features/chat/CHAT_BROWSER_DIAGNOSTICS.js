/**
 * AriStay Chat Diagnostics Script
 * 
 * Paste this into the browser console on /api/chat/ page
 * to diagnose issues with the chat system.
 */

(function() {
    console.log('%c🔍 AriStay Chat Diagnostics', 'font-size: 20px; color: #6366f1; font-weight: bold;');
    console.log('%c─'.repeat(50), 'color: #6366f1;');
    
    const results = {
        passed: [],
        failed: [],
        warnings: []
    };
    
    // Test 1: Check if on correct page
    if (window.location.pathname !== '/api/chat/') {
        results.warnings.push('⚠️  Not on /api/chat/ page (current: ' + window.location.pathname + ')');
    } else {
        results.passed.push('✅ On correct page');
    }
    
    // Test 2: Check ChatApp object
    if (typeof ChatApp !== 'undefined') {
        results.passed.push('✅ ChatApp object exists');
        
        // Test 2a: User ID
        if (ChatApp.userId) {
            results.passed.push(`✅ User ID: ${ChatApp.userId}`);
        } else {
            results.failed.push('❌ ChatApp.userId is missing');
        }
        
        // Test 2b: Username
        if (ChatApp.username) {
            results.passed.push(`✅ Username: ${ChatApp.username}`);
        } else {
            results.failed.push('❌ ChatApp.username is missing');
        }
        
        // Test 2c: JWT Token
        if (ChatApp.wsToken && ChatApp.wsToken !== '') {
            results.passed.push('✅ JWT token is present');
            console.log('   Token preview:', ChatApp.wsToken.substring(0, 20) + '...');
        } else {
            results.failed.push('❌ ChatApp.wsToken is missing or empty');
        }
        
        // Test 2d: Current Room
        if (ChatApp.currentRoom) {
            results.passed.push(`✅ Current room: ${ChatApp.currentRoom}`);
        } else {
            results.warnings.push('⚠️  No room selected (select a room first)');
        }
        
        // Test 2e: WebSocket
        if (ChatApp.ws) {
            const state = ChatApp.ws.readyState;
            const states = ['CONNECTING', 'OPEN', 'CLOSING', 'CLOSED'];
            if (state === WebSocket.OPEN) {
                results.passed.push('✅ WebSocket is OPEN and connected');
            } else {
                results.warnings.push(`⚠️  WebSocket state: ${states[state]} (${state})`);
            }
        } else {
            results.warnings.push('⚠️  WebSocket not initialized (select a room first)');
        }
        
    } else {
        results.failed.push('❌ ChatApp object does not exist');
    }
    
    // Test 3: Check DOM elements
    const requiredElements = [
        'roomList',
        'messagesContainer',
        'messageInput',
        'sendButton',
        'chatTitle',
        'typingIndicator',
        'connectionStatus'
    ];
    
    let missingElements = [];
    requiredElements.forEach(id => {
        if (document.getElementById(id)) {
            // Element exists
        } else {
            missingElements.push(id);
        }
    });
    
    if (missingElements.length === 0) {
        results.passed.push('✅ All required DOM elements present');
    } else {
        results.failed.push(`❌ Missing DOM elements: ${missingElements.join(', ')}`);
    }
    
    // Test 4: Check for JavaScript errors
    const originalError = console.error;
    let errorCount = 0;
    console.error = function() {
        errorCount++;
        originalError.apply(console, arguments);
    };
    
    // Test 5: Check room list
    const rooms = document.querySelectorAll('.room-item');
    if (rooms.length > 0) {
        results.passed.push(`✅ ${rooms.length} room(s) in sidebar`);
    } else {
        results.warnings.push('⚠️  No rooms in sidebar (create a room first)');
    }
    
    // Test 6: Check for CSRF token
    const csrfMeta = document.querySelector('[name=csrf-token]');
    if (csrfMeta && csrfMeta.content) {
        results.passed.push('✅ CSRF token found in meta tag');
    } else {
        results.failed.push('❌ CSRF token missing (required for API calls)');
    }
    
    // Test 7: Check network connectivity
    fetch('/api/chat/rooms/', {
        headers: {
            'Authorization': `Bearer ${ChatApp.wsToken}`
        }
    })
    .then(response => {
        if (response.ok) {
            console.log('✅ API connectivity: OK (status ' + response.status + ')');
        } else {
            console.log('❌ API connectivity: Failed (status ' + response.status + ')');
        }
    })
    .catch(error => {
        console.log('❌ API connectivity: Network error', error);
    });
    
    // Test 8: WebSocket connectivity test
    if (ChatApp.wsToken && rooms.length > 0) {
        const testRoomId = rooms[0].dataset.roomId;
        if (testRoomId) {
            console.log('   Testing WebSocket connection to room:', testRoomId);
            const wsProtocol = window.location.protocol === 'https:' ? 'wss:' : 'ws:';
            const wsUrl = `${wsProtocol}//${window.location.host}/ws/chat/${testRoomId}/?token=${ChatApp.wsToken}`;
            
            const testWs = new WebSocket(wsUrl);
            testWs.onopen = () => {
                console.log('✅ WebSocket test: Connection successful');
                testWs.close();
            };
            testWs.onerror = (e) => {
                console.log('❌ WebSocket test: Connection failed', e);
            };
            testWs.onclose = (e) => {
                if (e.code !== 1000) {
                    console.log('⚠️  WebSocket test: Closed with code', e.code, e.reason);
                }
            };
        }
    }
    
    // Print results
    console.log('%c\n📊 DIAGNOSTIC RESULTS', 'font-size: 16px; color: #059669; font-weight: bold;');
    console.log('%c─'.repeat(50), 'color: #6366f1;');
    
    if (results.passed.length > 0) {
        console.log('\n%c✅ PASSED (' + results.passed.length + ')', 'color: #059669; font-weight: bold;');
        results.passed.forEach(msg => console.log('   ' + msg));
    }
    
    if (results.warnings.length > 0) {
        console.log('\n%c⚠️  WARNINGS (' + results.warnings.length + ')', 'color: #f59e0b; font-weight: bold;');
        results.warnings.forEach(msg => console.log('   ' + msg));
    }
    
    if (results.failed.length > 0) {
        console.log('\n%c❌ FAILED (' + results.failed.length + ')', 'color: #ef4444; font-weight: bold;');
        results.failed.forEach(msg => console.log('   ' + msg));
    }
    
    // Overall assessment
    console.log('\n%c' + '─'.repeat(50), 'color: #6366f1;');
    
    if (results.failed.length === 0) {
        if (results.warnings.length === 0) {
            console.log('%c🎉 EXCELLENT! Chat system is fully functional.', 'font-size: 14px; color: #059669; font-weight: bold;');
        } else {
            console.log('%c✅ GOOD. Chat system is functional with minor warnings.', 'font-size: 14px; color: #059669; font-weight: bold;');
        }
    } else {
        console.log('%c⚠️  ISSUES DETECTED. Please fix the failed items above.', 'font-size: 14px; color: #ef4444; font-weight: bold;');
    }
    
    // Helpful commands
    console.log('\n%c🛠️  HELPFUL COMMANDS', 'font-size: 14px; color: #6366f1; font-weight: bold;');
    console.log('   ChatApp              - View chat state');
    console.log('   selectRoom("uuid")   - Select a room manually');
    console.log('   sendMessage()        - Send current message');
    console.log('   loadMessages("uuid") - Load messages for a room');
    
    console.log('\n%c📝 QUICK ACTIONS', 'font-size: 14px; color: #6366f1; font-weight: bold;');
    
    if (rooms.length > 0) {
        const firstRoomId = rooms[0].dataset.roomId;
        console.log(`   // Select first room:\n   selectRoom("${firstRoomId}")`);
    }
    
    console.log('   // Send a test message:\n   document.getElementById("messageInput").value = "Test message";\n   sendMessage();');
    
    console.log('\n%c' + '─'.repeat(50), 'color: #6366f1;');
    console.log('%cDiagnostics complete! 🎉', 'color: #6366f1; font-weight: bold;');
    
})();

