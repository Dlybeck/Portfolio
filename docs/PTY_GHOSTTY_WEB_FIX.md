# PTY Backend Fix for ghostty-web

## Problem
WebSocket connection from ghostty-web client throws:
```
Uncaught RangeError: offset is out of bounds at Uint8Array.set
at y.write (ghostty-web-BqArTMI8.js:1:1115576)
```

## Root Cause
**Your backend was sending binary WebSocket frames (`send_bytes()`), but ghostty-web expects text frames.**

## ghostty-web Protocol Specification

### Client → Server (Input)
1. **User input**: Raw text string
   ```javascript
   ws.send("ls\r")  // User typed "ls" and pressed Enter
   ```

2. **Resize control**: JSON string
   ```javascript
   ws.send(JSON.stringify({ type: 'resize', cols: 80, rows: 24 }))
   ```

### Server → Client (Output)
- **PTY output**: Raw text string ONLY (no binary frames)
  ```python
  await websocket.send_text(data.decode('utf-8', errors='ignore'))
  ```

## Changes Made

### 1. `/services/pty_service.py`

**Before:**
```python
# Line 46 - WRONG: Binary frame
await websocket.send_bytes(data)

# Lines 60-72 - WRONG: Custom resize protocol
if data.startswith(b'\x00'):
    parts = data[1:].split(b'\x00', 1)
    if len(parts) == 2 and parts[0] == b'resize':
        # ...
```

**After:**
```python
# Line 49 - CORRECT: Text frame
text = data.decode('utf-8', errors='ignore')
await websocket.send_text(text)

# Lines 66-76 - CORRECT: JSON resize protocol
if text.startswith('{'):
    try:
        control = json.loads(text)
        if control.get("type") == "resize":
            rows = control.get("rows", 24)
            cols = control.get("cols", 80)
            # ... resize PTY
```

### 2. Type Annotations Fixed
```python
# Before
async def handle_pty_websocket(self, websocket: WebSocket, pty_id: str, directory: str = None):

# After
async def handle_pty_websocket(self, websocket: WebSocket, pty_id: str, directory: str | None = None):
```

## Why This Fixes the Error

1. **Binary vs Text Frames**: WebSocket has two frame types:
   - **Binary frames** (opcode 0x2): Raw bytes
   - **Text frames** (opcode 0x1): UTF-8 encoded strings

2. **ghostty-web's Expectation**: 
   - The `write()` method expects text frames
   - It internally converts text to bytes for the WASM terminal
   - When it receives binary frames, it tries to write them directly to a fixed-size buffer
   - This causes "offset out of bounds" when the binary data doesn't match expected format

3. **UTF-8 Decoding with `errors='ignore'`**:
   - PTY output may contain invalid UTF-8 sequences (binary data, escape codes)
   - `errors='ignore'` skips invalid bytes instead of crashing
   - ghostty-web's WASM terminal handles the resulting text correctly

## Testing

Test with this client code:
```javascript
import { init, Terminal } from 'ghostty-web';

await init();
const term = new Terminal({ fontSize: 14 });
term.open(document.getElementById('terminal'));

const ws = new WebSocket('ws://localhost:8000/pty/test/connect');

ws.onmessage = (event) => {
  term.write(event.data);  // Should work now
};

term.onData((data) => {
  ws.send(data);  // User input
});

term.onResize(({ cols, rows }) => {
  ws.send(JSON.stringify({ type: 'resize', cols, rows }));
});
```

## Reference Implementation
See: https://github.com/coder/ghostty-web/blob/main/demo/bin/demo.js

Key lines:
- **Line 485**: `ws.send(data)` - Send user input as text
- **Line 491**: `ws.send(JSON.stringify({ type: 'resize', cols, rows }))` - Resize as JSON
- **Line 467**: `ptyProcess.onData((data) => ws.send(data))` - PTY output as text

## Additional Notes

- **No special headers/framing needed**: Just raw text frames
- **Resize is optional**: If not implemented, terminal won't resize but will still work
- **Error handling**: Use `errors='ignore'` when decoding PTY output to handle binary data gracefully
