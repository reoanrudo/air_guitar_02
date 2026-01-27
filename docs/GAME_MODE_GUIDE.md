# VirtuTune Game Mode - Quick Start Guide

## Overview

VirtuTune's integrated game mode allows you to play the rhythm game using:
- **Mobile Device**: Select chords (left hand input)
- **PC with Camera**: Detect strum gestures (right hand input)

## Setup

### 1. Start Game on PC

1. Navigate to the game page: `http://localhost:8000/game/play/<song_id>/?session_id=<your_session_id>`
2. The game will initialize with the selected song

### 2. Connect Mobile Device

1. Open mobile controller: `http://localhost:8000/mobile/controller/`
2. Enter the session ID displayed on PC (or scan QR code)
3. Wait for connection confirmation

### 3. Enable Camera

1. Click "Enable Camera" button on PC
2. Allow camera access when prompted
3. Position yourself so your hand is visible in the camera frame

## Gameplay

### Controls

**Mobile Device (Chord Selection):**
- Tap chord buttons (C, G, Am, F, etc.) to select the current chord
- The selected chord will be displayed on PC
- Change chords before notes reach the judgment line

**PC Camera (Strum Detection):**
- Raise your hand in front of the camera
- Make a downward strumming motion when the note reaches the judgment line
- The game will detect the gesture and score the note

**Keyboard (Alternative):**
- Press letter keys (A-Z) corresponding to chord names
- Press Space to pause/resume

### Scoring

- **PERFECT**: Hit within 50ms of perfect timing (100 points)
- **GREAT**: Hit within 100ms (80 points)
- **GOOD**: Hit within 150ms (60 points)
- **MISS**: Missed the note (0 points, combo reset)

### Combos

- Consecutive hits build your combo
- Higher combos = more impressive display
- Combo milestones (10, 20, 30...) trigger special animations

## Real-time Synchronization

### What Syncs Between Devices

**From Mobile to PC:**
- Chord changes
- Practice start/stop
- Pause/resume commands

**From PC to Mobile:**
- Score updates
- Combo counter
- Judgement results (PERFECT/GREAT/GOOD/MISS)
- Game statistics (perfect, great, good, miss counts)

### Display Elements

**PC Display:**
- Game canvas with flowing notes
- Current chord display
- Judgment line
- Score, combo, accuracy
- Camera feed (if enabled)

**Mobile Display:**
- Chord selection grid
- Current chord indicator
- Game score and combo
- Judgement results
- Game statistics
- Practice timer

## Tips for Best Performance

### Camera Setup

1. **Lighting**: Ensure good, even lighting
2. **Positioning**: Sit at arm's length from camera
3. **Background**: Use plain background if possible
4. **Hand Visibility**: Ensure your hand is clearly visible

### Gameplay Tips

1. **Anticipation**: Look ahead to upcoming notes
2. **Chord Changes**: Change chords early to allow for reaction time
3. **Strum Timing**: Strum slightly before the note reaches the line (latency compensation)
4. **Consistency**: Maintain steady strumming rhythm

### Troubleshooting

**Camera Not Detecting Strums:**
- Check lighting conditions
- Ensure hand is visible in frame
- Make more pronounced strumming motion
- Verify camera is enabled (check for "Camera: On" indicator)

**Mobile Not Connecting:**
- Verify session ID matches
- Check WebSocket connection status
- Ensure both devices are on same network
- Refresh page and try reconnecting

**Score Not Syncing:**
- Check WebSocket connection is active
- Verify both devices are on same session
- Refresh page if connection lost

## Game Modes

### Free Mode

- Practice without notes
- Use mobile for chord selection
- Use camera for strumming
- No scoring or timing pressure

### Rhythm Game Mode

- Notes flow from right to left
- Hit notes at the judgment line
- Score based on timing accuracy
- Combo system for consecutive hits

## Technical Details

### WebSocket Messages

**Chord Change:**
```json
{
  "type": "chord_change",
  "data": {
    "chord": "C",
    "timestamp": 1234567890
  }
}
```

**Game Update:**
```json
{
  "type": "game_update",
  "data": {
    "score": 1000,
    "combo": 10,
    "maxCombo": 15,
    "stats": {
      "perfect": 5,
      "great": 3,
      "good": 2,
      "miss": 0
    }
  }
}
```

**Judgement:**
```json
{
  "type": "judgement",
  "data": {
    "judgement": "PERFECT",
    "score": 100,
    "combo": 5
  }
}
```

### Camera Gesture Detection

- Uses MediaPipe Hands for hand tracking
- Detects downward motion of wrist (landmark 0)
- Strum threshold: 0.05 (adjustable in camera.js)
- Sampling rate: 30fps

## Advanced Configuration

### Adjusting Strum Sensitivity

Edit `/static/js/camera.js`:
```javascript
// Lower value = more sensitive
const STRUM_THRESHOLD = 0.05; // Default
```

### Adjusting Timing Windows

Edit `/static/js/game.js`:
```javascript
this.timingWindows = {
  perfect: 50,  // ms
  great: 100,   // ms
  good: 150     // ms
};
```

### Adjusting Note Speed

Edit `/static/js/game.js`:
```javascript
this.noteSpeed = 300; // pixels per second
```

## Support

For issues or questions:
1. Check the implementation guide: `/docs/TASK_2.10_IMPLEMENTATION.md`
2. Review test files for examples
3. Check browser console for errors
4. Verify WebSocket connection in network tab

## Future Enhancements

Planned features:
- Offline mode support
- Advanced camera gestures (velocity detection)
- Multiplayer competitive mode
- Performance analytics
- Custom difficulty settings
