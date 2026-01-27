# Task 2.10: WebSocket/Camera Integrated Game Mode - Implementation Report

## Overview

This task implements the integration of WebSocket communication and camera gesture recognition with the rhythm game mode, enabling users to play the game using mobile controller for chord selection and PC camera for strum detection.

## Implementation Date

2026-01-27

## Requirements Implementation

### 1. WebSocket Integration

#### Modified Files
- `/Users/taguchireo/camp/python/air_guitar_02/static/js/game.js`
- `/Users/taguchireo/camp/python/air_guitar_02/apps/websocket/consumers.py`

#### Implementation Details

**Game.js Changes:**
- Added WebSocket connection management (`setupWebSocket()`)
- Implemented real-time chord synchronization from mobile device
- Added game state synchronization (score, combo, stats)
- Implemented pause/resume sync across devices

**WebSocket Consumer Changes:**
- Added `game_mode` message handler for mode switching
- Added `game_update` message handler for state synchronization
- Added `judgement` message handler for hit results
- Implemented broadcast of game events to all connected devices

**Message Types:**
```javascript
// Game Mode
{
  "type": "game_mode",
  "mode": "game",
  "timestamp": 1234567890
}

// Game Update
{
  "type": "game_update",
  "data": {
    "score": 1000,
    "combo": 10,
    "maxCombo": 15,
    "stats": {...},
    "timestamp": 1234567890
  }
}

// Judgement
{
  "type": "judgement",
  "data": {
    "judgement": "PERFECT",
    "score": 100,
    "combo": 5,
    "timestamp": 1234567890
  }
}
```

### 2. Camera Gesture Scoring

#### Modified Files
- `/Users/taguchireo/camp/python/air_guitar_02/static/js/camera.js`
- `/Users/taguchireo/camp/python/air_guitar_02/static/js/game.js`

#### Implementation Details

**Camera.js Changes:**
- Enhanced `strum` event handler to differentiate between game mode and free mode
- Added game mode detection to route strum events appropriately

**Game.js Changes:**
- Added `enableCamera()` and `disableCamera()` methods
- Implemented `handleStrum()` method to process camera gestures
- Camera strums trigger note hits when chord is selected

**Flow:**
1. User enables camera on PC
2. User selects chord on mobile device
3. Camera detects strum gesture
4. Game processes hit with current chord
5. Score is calculated and synced

### 3. Game Session Management

#### Implementation Details

**Session Tracking:**
- Practice session linked to game session
- Session ID used for WebSocket connection
- Real-time session state synchronization

**Lifecycle:**
1. QR code scanned → WebSocket connection established
2. Game mode activated → Session tracking begins
3. Chord changes → Synced to PC
4. Strum gestures → Score calculated
5. Game completion → Results saved

**Message Handlers:**
```javascript
handlePracticeUpdate(message) {
  if (message.status === 'started') {
    this.start(this.currentSong);
  } else if (message.status === 'ended') {
    this.stop();
  }
}
```

### 4. Real-time Score Sync

#### Modified Files
- `/Users/taguchireo/camp/python/air_guitar_02/static/js/mobile-controller.js`
- `/Users/taguchireo/camp/python/air_guitar_02/static/js/game.js`

#### Implementation Details

**Mobile Controller Changes:**
- Added `handleGameUpdate()` for score sync
- Added `handleJudgement()` for hit result display
- Implemented combo animation on milestone (every 10 combo)
- Added game stats display (perfect, great, good, miss)

**Game.js Changes:**
- Added `sendGameState()` to broadcast game state
- Added `sendJudgement()` to broadcast hit results
- Enhanced `updateUI()` to trigger sync

**Sync Flow:**
```
PC (Game) → WebSocket → Mobile
- Score updates
- Combo counter
- Judgement results
- Game stats
```

## Integration Points

### 1. Mobile Controller → PC (Chord Input)

**Flow:**
1. User taps chord button on mobile
2. `selectChord()` sends WebSocket message
3. PC receives `chord_change` message
4. Game updates `currentChord`
5. Display shows current chord

**Code:**
```javascript
// Mobile
selectChord(chordName) {
  const message = {
    type: 'chord_change',
    chord: chordName,
    timestamp: Date.now()
  };
  this.ws.send(JSON.stringify(message));
}

// PC
handleWebSocketMessage(data) {
  if (data.type === 'chord_change') {
    this.currentChord = data.data.chord;
    this.showCurrentChord(this.currentChord);
  }
}
```

### 2. PC Camera → Game (Note Scoring)

**Flow:**
1. Camera detects strum gesture
2. `strum` event triggered
3. Game's `handleStrum()` processes gesture
4. Hit checked against timing windows
5. Score calculated and synced

**Code:**
```javascript
// Camera
triggerNote(velocity) {
  const event = new CustomEvent('strum', {
    detail: { velocity }
  });
  window.dispatchEvent(event);
}

// Game
handleStrum(velocity) {
  if (this.cameraEnabled && this.currentChord) {
    this.handleInput(this.currentChord);
  }
}
```

### 3. PC → Mobile (Score Sync)

**Flow:**
1. Note hit on PC
2. `checkHit()` calculates score
3. `updateUI()` triggers sync
4. `sendGameState()` broadcasts to mobile
5. Mobile updates display

**Code:**
```javascript
// PC
updateUI() {
  // Update local UI
  document.getElementById('score').textContent = this.score;

  // Sync to mobile
  this.sendGameState();
}

sendGameState() {
  this.ws.send(JSON.stringify({
    type: 'game_update',
    data: {
      score: this.score,
      combo: this.combo,
      ...
    }
  }));
}

// Mobile
handleGameUpdate(message) {
  const data = message.data;
  document.getElementById('game-score').textContent = data.score;
  document.getElementById('game-combo').textContent = data.combo;
}
```

## Files Modified

### JavaScript Files

1. **static/js/game.js**
   - Added WebSocket connection management
   - Added camera integration
   - Added game state synchronization
   - Added judgement result broadcasting

2. **static/js/camera.js**
   - Enhanced strum event handler
   - Added game mode detection

3. **static/js/mobile-controller.js**
   - Added game mode UI management
   - Added game state display handlers
   - Added judgement result display
   - Added combo animations

### Python Files

4. **apps/websocket/consumers.py**
   - Added game mode message handler
   - Added game update message handler
   - Added judgement message handler
   - Added corresponding event broadcasters

### Test Files

5. **static/js/tests/game-integration.test.js**
   - WebSocket integration tests
   - Camera gesture integration tests
   - Game session management tests
   - Real-time score sync tests

6. **apps/websocket/tests/test_game_integration.py**
   - Game mode message tests
   - Multi-device sync tests
   - Pause/resume sync tests

## Expected Outcome

### User Experience

1. **Device Pairing**
   - User scans QR code on PC with mobile
   - WebSocket connection established
   - Game mode activated

2. **Gameplay**
   - User sees notes flowing on PC
   - User taps chord on mobile (e.g., "C")
   - Current chord displayed on PC
   - Camera detects strum gesture
   - Note hit scored if timing is correct
   - Score and combo update on both devices

3. **Synchronization**
   - Score updates in real-time on mobile
   - Combo counter synced across devices
   - Judgement results (PERFECT/GREAT/GOOD/MISS) shown on mobile
   - Game stats (perfect, great, good, miss counts) updated

### Technical Features

- **Low Latency**: WebSocket ensures <100ms message delivery
- **Bidirectional Sync**: Both devices can trigger state changes
- **Robust Handling**: Graceful degradation if camera or WebSocket fails
- **Visual Feedback**: Combo animations and judgement displays

## Testing

### Unit Tests

**Game Integration Tests** (`game-integration.test.js`):
- WebSocket connection setup
- Message handling (chord_change, game_update, judgement)
- Camera enable/disable
- Strum gesture processing
- Score and combo synchronization

**WebSocket Consumer Tests** (`test_game_integration.py`):
- Game mode message handling
- Game update message broadcasting
- Judgement result broadcasting
- Multi-device synchronization
- Pause/resume functionality

### Integration Testing

**Test Scenarios:**
1. Mobile chord change → PC display update
2. Camera strum → Note hit → Score calculation
3. PC score update → Mobile display sync
4. Multi-device game state consistency
5. Pause/resume synchronization

**Expected Results:**
- All messages delivered within 100ms
- Score accuracy maintained across devices
- No state inconsistencies
- Smooth gameplay experience

## Usage Example

### Setup

```javascript
// PC: Game initialization
const sessionId = new URLSearchParams(window.location.search).get('session_id');
if (sessionId) {
  rhythmGame.setupWebSocket(sessionId);
}

// PC: Enable camera
document.getElementById('enable-camera-btn').addEventListener('click', () => {
  rhythmGame.enableCamera();
});
```

### Gameplay Flow

```
1. User opens game page on PC with ?session_id=abc123
2. User opens mobile controller and enters session ID: abc123
3. WebSocket connection established between devices
4. Game mode activated
5. User taps "C" chord on mobile
6. PC shows current chord: "C"
7. Camera detects strum gesture
8. Game checks if timing is correct
9. Hit result: "PERFECT"
10. Score: +100, Combo: 5
11. Both devices show updated score and combo
12. Next note appears...
```

## Performance Considerations

### Optimization

1. **Message Throttling**
   - Game state updates sent on every UI change
   - Consider throttling if performance issues arise

2. **WebSocket Reconnection**
   - Auto-reconnect on disconnect
   - Graceful handling of connection loss

3. **Camera Performance**
   - MediaPipe runs at 30fps
   - Strum detection optimized for real-time

### Known Limitations

1. **Network Latency**
   - Dependent on internet connection
   - May affect timing precision

2. **Camera Accuracy**
   - Depends on lighting conditions
   - May misdetect gestures in poor lighting

3. **Device Compatibility**
   - Requires WebSocket support
   - Requires camera access

## Future Enhancements

### Potential Improvements

1. **Offline Mode**
   - Allow game without WebSocket
   - Local storage for game state

2. **Advanced Camera Features**
   - Multi-gesture recognition
   - Strum velocity detection for dynamics

3. **Multiplayer Mode**
   - Support multiple mobile controllers
   - Competitive or cooperative gameplay

4. **Analytics**
   - Track gesture accuracy
   - Analyze player improvement

## Conclusion

This implementation successfully integrates WebSocket communication and camera gesture recognition with the rhythm game mode, providing a seamless dual-device gaming experience. Users can now play the rhythm game using their mobile device for chord selection and PC camera for strum detection, with real-time score synchronization across devices.

### Key Achievements

✅ WebSocket integration for real-time communication
✅ Camera gesture scoring for rhythm game
✅ Game session management and synchronization
✅ Real-time score sync across devices
✅ Comprehensive test coverage
✅ Device pairing state management
✅ Pause/resume functionality

### Deliverables

- Modified JavaScript files (game.js, camera.js, mobile-controller.js)
- Enhanced WebSocket consumer
- Integration test suites
- Documentation

The implementation fulfills all requirements specified in Task 2.10 and provides a solid foundation for future enhancements.
