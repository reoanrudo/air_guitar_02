# Camera Gesture Recognition - Quick Reference Guide

## For Developers

### How to Use

#### 1. Enable Camera in Your Page

```html
<video id="camera-video" playsinline></video>
<button id="enable-camera-btn">Enable Camera</button>
<button id="disable-camera-btn">Disable Camera</button>
```

#### 2. Listen for Strum Events

```javascript
window.addEventListener('strum', function(event) {
    const velocity = event.detail.velocity;
    console.log('Strum detected with velocity:', velocity);

    // Trigger sound, animation, etc.
    playGuitarSound(velocity);
    showVisualFeedback(velocity);
});
```

#### 3. Create GestureRecognizer Instance

```javascript
const gestureRecognizer = new GestureRecognizer();
await gestureRecognizer.startCamera(videoElement);
```

---

### API Reference

#### GestureRecognizer Class

##### Constructor
```javascript
const recognizer = new GestureRecognizer();
```

##### Methods

**startCamera(videoElement)**
- Starts camera and begins gesture detection
- Returns: Promise<void>
- Throws: Error if camera permission denied

```javascript
await recognizer.startCamera(document.getElementById('camera-video'));
```

**stopCamera()**
- Stops camera and cleans up resources
- Returns: void

```javascript
recognizer.stopCamera();
```

**isActive()**
- Checks if camera is currently active
- Returns: boolean

```javascript
if (recognizer.isActive()) {
    console.log('Camera is running');
}
```

---

### Event Details

#### 'strum' Event

**Properties:**
- `detail.velocity`: number (0-1 range)

**Example:**
```javascript
window.addEventListener('strum', (event) => {
    const velocity = event.detail.velocity;
    // Use velocity to control volume or intensity
});
```

---

### Configuration

#### MediaPipe Settings

To adjust detection sensitivity, modify in `camera.js`:

```javascript
this.hands.setOptions({
    maxNumHands: 1,              // Number of hands to detect
    modelComplexity: 1,          // 0=fast, 1=balanced, 2=accurate
    minDetectionConfidence: 0.7, // 0-1, higher = stricter
    minTrackingConfidence: 0.7   // 0-1, higher = stricter
});
```

#### Strum Threshold

Adjust strum sensitivity in `isStrumming()`:

```javascript
const STRUM_THRESHOLD = 0.05;  // Increase for less sensitivity
```

---

### CSS Classes

#### Camera Styles
```css
.camera-gesture        /* Main container */
.camera-controls       /* Button container */
.camera-indicator      /* Status indicator */
.camera-indicator.active  /* When camera is on */
.camera-video         /* Video element */
.camera-instructions  /* User instructions */
```

#### Animations
```css
.strumming            /* Applied to guitar neck on strum */
@keyframes pulse      /* Indicator animation */
@keyframes strumFlash /* Neck flash animation */
```

---

### Testing

#### Run Tests
```bash
# Open test runner in browser
open static/js/tests/camera.test.html

# Or open demo page
open static/js/tests/camera-demo.html
```

#### Test Coverage
- Unit tests for all methods
- Integration tests with guitar page
- Privacy verification tests
- Error handling tests

---

### Troubleshooting

#### Camera Not Starting
1. Check browser permissions
2. Ensure HTTPS (or localhost)
3. Check console for errors
4. Verify camera not in use by other apps

#### Strum Not Detected
1. Ensure good lighting
2. Hand must be in frame
3. Move hand downward clearly
4. Try adjusting STRUM_THRESHOLD

#### Performance Issues
1. Reduce resolution to 320x240
2. Set modelComplexity to 0
3. Close other browser tabs
4. Check CPU usage

---

### File Locations

```
static/js/
├── camera.js                           # Main implementation
└── tests/
    ├── camera.test.js                  # Unit tests
    ├── camera-integration.test.js      # Integration tests
    ├── camera.test.html                # Test runner
    └── camera-demo.html                # Demo page

docs/
├── camera-gesture-implementation.md    # Full documentation
├── camera-implementation-summary.md    # Implementation summary
└── camera-implementation-checklist.md  # Verification checklist

apps/guitar/templates/guitar/
└── guitar.html                         # Updated with camera UI

static/css/
└── guitar.css                          # Updated with camera styles
```

---

### Browser Requirements

- **HTTPS**: Required for camera access (except localhost)
- **Permissions**: Camera permission must be granted
- **JavaScript**: Must be enabled
- **CDN Access**: MediaPipe libraries must be accessible

---

### Privacy Considerations

✅ **No Storage**: Frames processed and discarded immediately
✅ **No Transmission**: All processing is client-side
✅ **Visual Indicator**: Shows when camera is active
✅ **User Control**: Explicit enable/disable buttons

---

### Common Patterns

#### Toggle Camera
```javascript
let recognizer = null;
const video = document.getElementById('camera-video');

async function toggleCamera() {
    if (recognizer && recognizer.isActive()) {
        recognizer.stopCamera();
        recognizer = null;
    } else {
        recognizer = new GestureRecognizer();
        await recognizer.startCamera(video);
    }
}
```

#### Handle Strum with Sound
```javascript
window.addEventListener('strum', (event) => {
    const { velocity } = event.detail;
    const volume = velocity; // 0-1 range

    // Play guitar sound with velocity-based volume
    playGuitarSound(currentChord, volume);
});
```

#### Show Visual Feedback
```javascript
window.addEventListener('strum', (event) => {
    const neck = document.querySelector('.guitar-neck');
    neck.classList.add('strumming');

    setTimeout(() => {
        neck.classList.remove('strumming');
    }, 200);
});
```

---

### Performance Tips

1. **Use appropriate resolution**: 640x480 is optimal
2. **Limit model complexity**: 1 is best for most use cases
3. **Clean up resources**: Always call stopCamera() when done
4. **Debounce events**: If needed, add debouncing to strum events
5. **Monitor CPU**: Check performance on low-end devices

---

### Next Steps

After implementation:
1. Test with real users
2. Collect feedback on gesture sensitivity
3. Adjust thresholds based on usage
4. Consider additional gestures
5. Optimize for target devices

---

### Support

For issues or questions:
- Check troubleshooting section
- Review full documentation
- Examine test files for examples
- Check browser console for errors

---

**Last Updated**: 2026-01-27
**Version**: 1.0.0
**Maintainer**: Sub-Agent-4
