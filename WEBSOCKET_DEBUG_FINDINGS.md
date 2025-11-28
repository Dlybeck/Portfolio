# WebSocket Proxy Investigation - Deep Dive Findings

## Critical Error Discovered

```
2025/11/28 06:01:15 socks5: client connection failed: could not read packet header
```

This error appears in the Tailscale SOCKS5 proxy logs on Cloud Run.

## What This Means

1. ✅ **The WebSocket connection DOES reach the SOCKS5 proxy** - we're not dealing with a routing/network issue
2. ❌ **The SOCKS5 handshake is failing** - Tailscale's SOCKS5 server cannot parse the packet header sent by `python-socks`
3. **"Packet header" in SOCKS5 context** likely refers to the initial SOCKS5 protocol handshake bytes

## SOCKS5 Protocol Handshake (RFC 1928)

Client sends:
```
+----+----------+----------+
|VER | NMETHODS | METHODS  |
+----+----------+----------+
| 1  |    1     | 1 to 255 |
+----+----------+----------+
```

Where:
- VER = 0x05 (SOCKS version 5)
- NMETHODS = number of authentication methods
- METHODS = list of supported methods

## Hypothesis: Protocol Mismatch

The error "could not read packet header" suggests:
1. `python-socks` is sending malformed SOCKS5 handshake bytes, OR
2. `python-socks` is using a different SOCKS version (SOCKS4?), OR
3. Something is corrupting the bytes before they reach Tailscale

## Test Results

### Local Mac Tests
- ✅ Direct WebSocket to `localhost:8888` works
- ✅ VS Code WebSocket path works locally
- ✅ Binary protocol confirmed (client sends first)

### Cloud Run Tests
- ❌ WebSocket hangs for 10s (open_timeout), then fails
- ❌ Tailscale logs show "could not read packet header"
- ❓ Terminal WebSocket status unknown (needs testing through Cloud Run)

## Key Code Differences

### Terminal WebSocket (route_dev_proxy.py:58-63)
```python
async with websockets.connect(
    ws_url,
    extra_headers=websocket.headers,  # FastAPI WebSocket.headers object
    proxy=settings.SOCKS5_PROXY,      # "socks5://localhost:1055"
    open_timeout=10
) as ws:
```

### VS Code WebSocket (base_proxy.py:214-219) - Current
```python
async with websockets.connect(
    ws_url,
    extra_headers=client_ws.headers,  # Same FastAPI object now
    proxy=proxy_url,                  # Same "socks5://localhost:1055"
    open_timeout=10                   # Same timeout
) as server_ws:
```

**They're now IDENTICAL** - yet one might work and one doesn't.

## Investigation Questions

1. **Does Terminal WebSocket actually work through Cloud Run?**
   - Need to test `/dev/ws/terminal` from browser while watching Cloud Run logs
   - If it also fails with "could not read packet header", then SOCKS5 is fundamentally broken

2. **Is python-socks version compatible with Tailscale's SOCKS5 server?**
   - Current version: python-socks 2.7.3
   - Tailscale SOCKS5: Custom Go implementation at `tailscale.com/net/socks5`

3. **What's the actual bytes being sent?**
   - Need packet capture or python-socks debug logging
   - Compare what works (if Terminal works) vs what doesn't

## Potential Root Causes

### 1. Tailscale SOCKS5 Server is UDP-only
**Likelihood: 20%**

Some SOCKS5 implementations only support UDP. The error "packet header" is often UDP terminology.

**Test**: Check Tailscale docs for SOCKS5 TCP vs UDP support

### 2. python-socks sends incompatible handshake
**Likelihood: 60%**

The `websockets` library uses `python-socks` for SOCKS proxy support. There may be a compatibility issue between:
- python-socks 2.7.3 client implementation
- Tailscale's custom Go SOCKS5 server implementation

**Evidence**:
- Error is specifically "could not read packet header"
- This happens during initial handshake before any WebSocket data

### 3. FastAPI WebSocket.headers causes issues
**Likelihood: 10%** (was 60%, now reduced)

We've matched Terminal pattern exactly. If it still fails, headers aren't the issue.

### 4. The SOCKS5 proxy isn't actually working
**Likelihood: 40%**

The Tailscale SOCKS5 proxy might not be functioning correctly in Cloud Run environment.

**Evidence**:
- Logs show "SOCKS5 proxy (:1055): ✅ listening" but that only means port is open
- We've never confirmed a successful SOCKS5 connection through it
- HTTP proxy might work where SOCKS5 doesn't

### 5. WebSocket-specific SOCKS5 issue
**Likelihood: 30%**

The SOCKS5 protocol upgrade for WebSocket might not be handled correctly.

**Evidence**:
- Regular HTTP requests work fine through the proxy
- WebSocket upgrade headers might confuse python-socks or Tailscale

## Next Steps (Prioritized)

### 1. CRITICAL: Test if Terminal WebSocket works through Cloud Run
```bash
# Open browser dev tools, go to Network tab (WS filter)
# Open Terminal tab in dashboard
# Watch for WebSocket connection
# Check Cloud Run logs for same "could not read packet header" error
```

**If Terminal also fails**: SOCKS5 is broken, need different approach
**If Terminal works**: There's a subtle difference we're missing

### 2. Try socks5h:// instead of socks5://
```python
SOCKS5_PROXY: str = "socks5h://localhost:1055"
```

The 'h' makes SOCKS proxy resolve hostnames. Might help with Tailscale.

### 3. Enable python-socks debug logging
```python
import logging
logging.basicConfig(level=logging.DEBUG)
logging.getLogger('python_socks').setLevel(logging.DEBUG)
```

This might show what bytes python-socks is actually sending.

### 4. Try different SOCKS proxy library
Use `aiohttp-socks` directly instead of websockets' built-in proxy support:

```python
from aiohttp_socks import ProxyConnector
# Create custom connection through SOCKS first
# Then upgrade to WebSocket manually
```

### 5. Switch to HTTP CONNECT proxy instead of SOCKS5
Tailscale might support HTTP proxy better than SOCKS5 for WebSockets.

## References

- [Tailscale SOCKS5 Package](https://pkg.go.dev/tailscale.com/net/socks5)
- [Tailscale Userspace Networking](https://tailscale.com/kb/1112/userspace-networking)
- [python-socks GitHub](https://github.com/romis2012/python-socks)
- [websockets Proxy Documentation](https://websockets.readthedocs.io/en/stable/topics/proxies.html)
- [SOCKS5 RFC 1928](https://www.rfc-editor.org/rfc/rfc1928)
- [NordVPN SOCKS5 Explanation](https://nordvpn.com/blog/socks5-proxy/)
- [websockets Issue #1592 - blocks until open_timeout](https://github.com/python-websockets/websockets/issues/1592)

## Timeline of Attempts

1. **websockets library refactor** - Changed from aiohttp to websockets (Terminal already used this, so wasn't the issue)
2. **Query parameter forwarding** - Added reconnectionToken to URL (logs confirmed it worked)
3. **Origin header removal** - Removed spoofing (didn't help, connection fails before headers matter)
4. **Exact Terminal pattern match** - Made VS Code identical to Terminal (current state)

All attempts focused on application-level fixes, but the issue is at the SOCKS5 protocol level.

---

## CRITICAL UPDATE - Latest Test Results

### Current Logs Show:
```
2025-11-28 06:35:55,831 - [CodeServerProxy] Query params: reconnectionToken=...
```

**Then nothing.** No "Connecting to upstream WebSocket..." log, no SOCKS5 error.

### This Means:
The code is **hanging BEFORE** reaching `websockets.connect()`. Looking at base_proxy.py:212, the log at line 212 should appear but doesn't.

Wait - the logs DO show query params (line 201) but NOT "Headers type" (line 202) or the divider (line 203).

**The code is crashing/hanging between lines 201 and 212!**

### Code Between Those Lines (base_proxy.py:202-212):
```python
logger.info(f"[{self.__class__.__name__}] Headers type: {type(client_ws.headers)}")  # Line 202 - NOT LOGGED
logger.info(f"[{self.__class__.__name__}] ==============================")  # Line 203 - NOT LOGGED

# Configure Proxy for websockets library  # Line 205
proxy_url = None  # Line 206
if IS_CLOUD_RUN:  # Line 207
    proxy_url = SOCKS5_PROXY  # Line 208
    logger.info(f"[{self.__class__.__name__}] Using websockets proxy: {proxy_url}")  # Line 209 - NOT LOGGED

try:  # Line 211
    logger.info(f"[{self.__class__.__name__}] Connecting to upstream WebSocket...")  # Line 212 - NOT LOGGED
```

### Hypothesis:
**Accessing `client_ws.headers` (line 202, line 216) is blocking/hanging!**

This is a FastAPI/Starlette WebSocket object. Maybe calling `type(client_ws.headers)` or iterating it for `extra_headers` parameter blocks waiting for the WebSocket handshake to complete?

### The Actual Problem:
We call `await websocket.accept()` in route_dev_proxy.py:289, THEN try to access `client_ws.headers` in base_proxy.py.

But maybe after accept(), the headers property blocks or raises an exception?

### Fix: Don't Access Headers After Accept
The Terminal WebSocket gets headers BEFORE connecting:
```python
async with websockets.connect(
    ws_url,
    extra_headers=websocket.headers,  # ← Accessed here, after accept()
```

Let me check - is Terminal also calling `await websocket.accept()` first?

YES! Line 46 in route_dev_proxy.py: `await websocket.accept()`

So both access headers after accept. But Terminal uses `websocket.headers` directly (the FastAPI WebSocket object), while we pass it to a function and then access it.

**New hypothesis: The headers are being accessed in a different async context or something is wrong with how we're passing the WebSocket object.**

---

## Update: IPv4 Fix Attempt (Failed)

### Change Made
Changed `SOCKS5_PROXY` from `socks5://localhost:1055` to `socks5://127.0.0.1:1055`

### Rationale
In containers, `localhost` might resolve to IPv6 `::1` while Tailscale SOCKS5 only listens on IPv4.

### Result
**Still fails with same error: "failed to connect to SOCKS proxy"**

### New Discovery: Error is from websockets library

The error "failed to connect to SOCKS proxy" is a generic error from the `websockets` library when the SOCKS5 connection fails. It doesn't tell us WHY.

From [websockets proxy docs](https://websockets.readthedocs.io/en/stable/topics/proxies.html):
- websockets uses python-socks for SOCKS proxy support
- python-socks must be installed (it is: v2.7.3)
- The proxy parameter accepts URLs like `socks5://host:port`

### Hypothesis: Tailscaled SOCKS5 server isn't actually running

The health check shows "SOCKS5 proxy (:1055): ✅ listening" but this only checks if port 1055 accepts TCP connections. It doesn't verify:
1. The SOCKS5 protocol is actually implemented on that port
2. Tailscaled is running at all
3. The SOCKS5 server initialized correctly

### Evidence:
1. Error is consistent: "failed to connect to SOCKS proxy"
2. No "could not read packet header" errors anymore (those only appeared once)
3. Connection fails immediately (no timeout)

### Next Tests Required:

1. **Verify tailscaled is actually running in Cloud Run:**
   Add logging to cloud_run_entrypoint.sh to confirm tailscaled starts

2. **Test SOCKS5 protocol directly:**
   ```python
   import socket
   import struct
   
   # SOCKS5 handshake
   sock = socket.socket()
   sock.connect(('127.0.0.1', 1055))
   # Send version + methods
   sock.send(b'\x05\x01\x00')  # SOCKS5, 1 method, no auth
   response = sock.recv(2)
   print(response)  # Should be b'\x05\x00' if SOCKS5 working
   ```

3. **Check if python-socks needs asyncio extras:**
   From search: "pip install python-socks[asyncio]"
   We might only have the base package

4. **Try connecting without websockets library:**
   Manually create SOCKS connection, then upgrade to WebSocket

### Sources
- [python-websockets proxy docs](https://websockets.readthedocs.io/en/stable/topics/proxies.html)
- [python-socks GitHub](https://github.com/romis2012/python-socks)
- [WebSocket SOCKS proxy issue #475](https://github.com/python-websockets/websockets/issues/475)
- [Python Socks needed - Issue #817](https://github.com/websocket-client/websocket-client/issues/817)
