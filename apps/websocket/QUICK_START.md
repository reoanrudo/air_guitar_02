# WebSocket Quick Start Guide

## Fast Track to Using WebSocket in VirtuTune

### Prerequisites
```bash
# Install Redis (macOS)
brew install redis
brew services start redis

# Install Redis (Ubuntu/Debian)
sudo apt-get install redis-server
sudo systemctl start redis

# Install Redis (Windows)
# Download from https://redis.io/download
```

### Verify Setup
```bash
source .venv/bin/activate
python manage.py test apps.websocket.test_websocket
```

### Start Development Server
```bash
# Terminal 1: Start Redis
redis-server

# Terminal 2: Start Django
python manage.py runserver
```

### WebSocket Connection Example (JavaScript)

```javascript
// Connect to WebSocket
const sessionId = 1; // Your practice session ID
const ws = new WebSocket(`ws://localhost:8000/ws/guitar/${sessionId}/`);

// Connection opened
ws.onopen = function(event) {
    console.log('WebSocket connected');
};

// Listen for messages
ws.onmessage = function(event) {
    const data = JSON.parse(event.data);
    console.log('Received:', data);

    // Handle different message types
    switch(data.type) {
        case 'chord_change':
            console.log('Chord changed to:', data.data.chord);
            // Update UI
            break;
        case 'practice_update':
            console.log('Practice status:', data.data.status);
            break;
        case 'connection_update':
            console.log('Connection status:', data.data.status);
            break;
    }
};

// Send chord change
function sendChordChange(chord) {
    ws.send(JSON.stringify({
        type: 'chord_change',
        data: { chord: chord }
    }));
}

// Send practice start
function sendPracticeStart() {
    ws.send(JSON.stringify({
        type: 'practice_start',
        data: { timestamp: new Date().toISOString() }
    }));
}

// Send ping (keep-alive)
setInterval(() => {
    ws.send(JSON.stringify({
        type: 'ping',
        data: { timestamp: new Date().toISOString() }
    }));
}, 30000); // Every 30 seconds

// Connection closed
ws.onclose = function(event) {
    console.log('WebSocket disconnected');
};

// Error handling
ws.onerror = function(error) {
    console.error('WebSocket error:', error);
};
```

### Common Use Cases

#### 1. Smartphone Controller (Mobile)
```javascript
// User presses chord button on phone
sendChordChange('C');
```

#### 2. PC Display (Desktop)
```javascript
// Listen for chord changes from phone
ws.onmessage = function(event) {
    const data = JSON.parse(event.data);
    if (data.type === 'chord_change') {
        displayChord(data.data.chord);
        playChordSound(data.data.chord);
    }
};
```

#### 3. Practice Session Sync
```javascript
// Start practice on phone
function startPractice() {
    sendPracticeStart();
    startTimer();
}

// Stop practice on phone
function stopPractice() {
    ws.send(JSON.stringify({
        type: 'practice_end',
        data: { timestamp: new Date().toISOString() }
    }));
    stopTimer();
    saveProgress();
}
```

### Testing the Connection

#### Option 1: Manual Test Script
```bash
python apps/websocket/manual_test.py
```

#### Option 2: Browser Console
```javascript
// Open browser console on guitar page
const ws = new WebSocket('ws://localhost:8000/ws/guitar/1/');
ws.onmessage = (e) => console.log(JSON.parse(e.data));
```

#### Option 3: Python Client
```python
import asyncio
import websockets
import json

async def test():
    async with websockets.connect('ws://localhost:8000/ws/guitar/1/') as ws:
        # Send chord change
        await ws.send(json.dumps({
            "type": "chord_change",
            "data": {"chord": "C"}
        }))
        # Receive response
        response = await ws.recv()
        print(json.loads(response))

asyncio.run(test())
```

### Message Types Reference

| Type | Direction | Purpose |
|------|-----------|---------|
| `chord_change` | Both | Send/receive chord changes |
| `practice_start` | Both | Notify practice session started |
| `practice_end` | Both | Notify practice session ended |
| `ping` | Client → Server | Keep connection alive |
| `pong` | Server → Client | Ping response |
| `connection_update` | Server → Client | Notify connect/disconnect |
| `practice_update` | Server → Client | Broadcast practice status |
| `error` | Server → Client | Error notifications |

### Troubleshooting

#### Connection Refused
```bash
# Check if Redis is running
redis-cli ping
# Should return: PONG

# Check Django server
curl http://localhost:8000/
```

#### Messages Not Arriving
```javascript
// Check connection state
console.log('WebSocket state:', ws.readyState);
// 0=CONNECTING, 1=OPEN, 2=CLOSING, 3=CLOSED

// Reconnect if needed
if (ws.readyState === 3) {
    ws = new WebSocket(ws.url);
}
```

#### Session Not Found
```python
# Verify session exists in database
python manage.py shell
>>> from apps.progress.models import PracticeSession
>>> PracticeSession.objects.all()
```

### Production Deployment

```bash
# Use Daphne instead of runserver
daphne config.asgi:application -b 0.0.0.0 -p 8001

# With Nginx proxy
location /ws/ {
    proxy_pass http://127.0.0.1:8001;
    proxy_http_version 1.1;
    proxy_set_header Upgrade $http_upgrade;
    proxy_set_header Connection "upgrade";
}
```

### Security Notes

- Always use authenticated sessions
- Validate session IDs before connection
- Use HTTPS/WSS in production
- Implement rate limiting for connections

### Need Help?

- Full documentation: `apps/websocket/README.md`
- Implementation details: `apps/websocket/IMPLEMENTATION_SUMMARY.md`
- Test examples: `apps/websocket/test_websocket.py`
- Manual testing: `apps/websocket/manual_test.py`
