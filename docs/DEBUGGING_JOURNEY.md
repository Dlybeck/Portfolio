# Debugging Journey: VS Code WebSocket Connection in Cloud Run

## Objective
Fix the "Workbench failed to connect to the server (Error: WebSocket close with status code 1006)" error when accessing VS Code through the Cloud Run proxy.

## Timeline & Attempts

### 1. Initial State
- **Symptoms:** VS Code loads UI but fails to connect to backend. Console shows WebSocket handshake timeouts and 1006 errors.
- **Configuration:** `aiohttp` used for both HTTP and WebSocket proxying.
- **Suspect:** `aiohttp` might be mishandling the SOCKS5 proxy handshake or headers for WebSockets.

### 2. Attempt 1: Manual Socket Handshake (Commit: `bd9e8dd`)
- **Hypothesis:** `aiohttp`'s WebSocket implementation via SOCKS5 is flaky.
- **Action:** Implemented a manual socket creation and SOCKS5 handshake using Python's standard `socket` library, then passed this socket to `websockets.connect`.
- **Result:** **FAILED**.
- **Logs:** `Error: Time limit reached` and `socks5: client connection failed: could not read packet header`.
- **Analysis:** The manual socket code used blocking calls (`sock.connect`, `sock.recv`) inside an async function, freezing the event loop and causing timeouts.

### 3. Attempt 2: Use `python-socks` Library (Commit: `ca64420`)
- **Hypothesis:** The manual socket implementation was buggy and blocking. Using the robust `python-socks` library (async-native) would fix the handshake.
- **Action:** Replaced manual socket code with `python_socks.async_.asyncio.Proxy.from_url(...).connect(...)`.
- **Result:** **FAILED**.
- **Logs:** `failed to connect to SOCKS proxy` (Application) and `socks5: client connection failed: could not read packet header` (Tailscale).
- **Analysis:** The library failed to connect to the proxy server itself.

### 4. Attempt 3: Change `127.0.0.1` to `localhost` (Commit: `1e08c6d`)
- **Hypothesis:** `tailscaled` in Cloud Run binds to `localhost` (IPv6 `::1`) but not IPv4 `127.0.0.1`. The health check used `localhost` and worked, while the app used `127.0.0.1` and failed.
- **Action:** Updated `core/config.py` to use `socks5://localhost:1055`.
- **Result:** **PENDING/FAILED** (User reports "Same thing at least on the ui end").
- **Analysis:** Need to check logs. If it still fails with "connection refused", then `localhost` might not be resolving correctly in the container or `tailscaled` is binding to something else entirely.

## Current Status
- **SOCKS5 Proxy:** Reported as "listening" by health check.
- **WebSocket Connection:** Consistently failing to establish a tunnel through the SOCKS5 proxy.
- **Error Pattern:** The app tries to connect to the SOCKS proxy, fails, and the VS Code client times out.

## Next Steps
1.  **Analyze Logs:** detailed check of the latest failure after the `localhost` change.
2.  **Verify Connectivity:** Can we even `curl` the SOCKS proxy port from within Python?
3.  **Consider Alternatives:**
    - Is `ws://100.84.184.84:8888` actually reachable? (HTTP works, so yes).
    - Is `python-socks` compatible with `tailscaled`'s SOCKS implementation?
    - Should we revert to `aiohttp` but fix the configuration?

## Resolution (Successful)
The final working configuration required three specific fixes combined:
1.  **Bypass `websockets` Proxy:** We manually created the SOCKS5 tunnel using `python-socks` (async) and passed the connected socket to `websockets.connect(sock=...)`. This bypassed the flaky native proxy implementation in the `websockets` library.
2.  **Use `localhost`:** We changed the SOCKS5 proxy URL to `socks5://localhost:1055` because `tailscaled` in Cloud Run binds to `localhost` (likely IPv6 `::1`) and not the hardcoded `127.0.0.1`.
3.  **Fix Argument Conflict:** We removed `extra_headers` from the `websockets.connect` call when using `sock`. This resolved a `TypeError` in `websockets` v15+ where passing headers alongside a pre-connected socket caused a crash in the underlying loop factory.

### Cleanup & Polish
After connectivity was restored, we addressed console noise:
-   **Mocked `vsda` Files:** `vsda.js` and `vsda_bg.wasm` (Microsoft proprietary components) were 404ing. We implemented a mock handler in `apis/route_dev_proxy.py` to return empty 200 OK responses for these specific files. This prevents client-side errors for components that are legitimately missing from the open-source `code-server` build.

