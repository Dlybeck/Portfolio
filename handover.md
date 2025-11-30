## Handover Document: Dev Dashboard Proxy Issues

### **Problem Statement**

The web-based development dashboard, hosted on Google Cloud Run and acting as a proxy to a Mac server (running VS Code / code-server and Agor), is experiencing connectivity issues when accessed from a specific client (user's laptop on a particular WiFi network). The issue manifested after the user changed WiFi networks.

**Symptoms:**
-   **VS Code iframe:**
    -   Initially stuck in "(pending)" or `408 Request Timeout`.
    -   Currently loads the page but then displays "An unexpected error occurred that requires a reload of this page. The workbench failed to connect to the server (Error: WebSocket close with status code 1006)".
    -   Console logs show `WebSocket connection to 'wss://davidlybeck.com/dev/vscode/stable-...' failed: `.
    -   Repeated errors like `[remote-connection][Management]... the handshake timed out. Error: Time limit reached`.
    -   `CodeExpectedError: ENOPRO: No file system provider found` for various `vscode-remote:/Users/dlybeck/.local/share/code-server/User/...` paths.
    -   `GET .../vsda.js` and `GET .../vsda_bg.wasm` 404 (Not Found).
-   **Agor iframe:**
    -   Initially stuck in "(pending)" or `408 Request Timeout`.
    -   Currently "sorta working" (loads the UI), but login fails ("Connection timeout") and previous settings/progress are lost.
    -   Console logs show `GET https://davidlybeck.com/health 404 (Not Found)`.
    -   `Uncaught SyntaxError: Invalid or unexpected token` in Agor's main JS bundle (`index-Cvydvvaf.js`).

**Key Clues:**
-   Works correctly on user's phone (implies Cloud Run -> Mac tunnel is functional).
-   Issue started after a WiFi network change on the laptop (points to client-side network interaction with Cloud Run/Tailscale).
-   `curl` from agent's local machine to Cloud Run endpoints generally works, including proxying HTTP requests to the Mac.
-   The dashboard's internal terminal (which also uses a WebSocket proxied through Tailscale) has not been reported as consistently failing, but its implementation of WebSocket proxying differs from VS Code/Agor.

### **Past Work (Attempts & Outcomes)**

1.  **MTU Fragmentation (`TS_DEBUG_MTU`):**
    *   **Problem:** Google Cloud Run + Tailscale userspace networking can suffer from packet fragmentation for large payloads, leading to requests hanging.
    *   **Fix:** Added `export TS_DEBUG_MTU=512` to `cloud_run_entrypoint.sh` (deployed via root `Dockerfile`).
    *   **Outcome:** Eliminated initial `408 Request Timeout` for HTTP requests (now they load instantly), confirming fragmentation was a contributing factor.

2.  **Keep-Alive Mismatch & Buffering:**
    *   **Problem:** Long-running HTTP/WebSocket connections were being prematurely closed by Cloud Load Balancer (LB) or upstream due to perceived idleness, or Python proxy code was buffering entire responses.
    *   **Fixes:**
        *   Configured Uvicorn (`main.py`) with `timeout_keep_alive=75`, `ws_ping_interval=30`, `ws_ping_timeout=45`.
        *   Refactored Python proxy (`CodeServerProxy`, `AgorProxy`) to use `aiohttp` (from `httpx`) with `StreamingResponse` for HTTP requests.
        *   Disabled `aiohttp` connection pooling (`force_close=True` in connector limits) to ensure fresh connections.
    *   **Outcome:** Improved initial load times, fixed the `SyntaxError` for Agor's JS (by properly handling decompression), and removed general HTTP request timeouts.

3.  **HTTP Compression Headers:**
    *   **Problem:** Mismatch in `Accept-Encoding` negotiation leading to corrupted data.
    *   **Fixes:** Explicitly handled `Accept-Encoding` in `_prepare_headers` and implemented robust manual decompression in `AgorProxy` before rewriting.
    *   **Outcome:** Fixed Agor's `Uncaught SyntaxError` in JS.

4.  **Dockerfile Syntax Errors:**
    *   **Problem:** Repeated build failures due to incorrect line continuations (`\n\`) and variable expansion within `RUN echo` in the Dockerfile.
    *   **Fix:** Extracted the startup script into `cloud_run_entrypoint.sh` and used `COPY` in the Dockerfile.
    *   **Outcome:** Successful Cloud Run deployments.

### **Current State & Unresolved Issues**

Both VS Code and Agor iframes *load their initial HTML*, but the actual **application functionality** is broken due to underlying connection issues:

1.  **Agor:**
    *   **Status:** UI loads, but login fails ("Connection timeout"). Console shows `GET https://davidlybeck.com/health 404 (Not Found)`. Also, `favicon.png` is a 404.
    *   **Analysis:** The `404` for `/health` (and presumably `/auth`, `/api`) indicates that despite the aggressive string replacement in `AgorProxy`, some parts of Agor's JavaScript are still constructing API URLs without the `/dev/agor/` prefix, or the rewrite regexes are insufficient. The `favicon.png` 404 confirms the rewrite is still incomplete for static assets outside the core bundles.
    *   **Fixes Implemented:** Implemented aggressive path rewriting in `AgorProxy` for `/health`, `/auth`, `/api` including template literals and concatenation. Also fixed `favicon.png` 404. (These fixes were pushed in the last two commits, `a6a88d9` and `bd9e8dd`). **Outcome is pending user verification after these deployments.**

2.  **VS Code:**
    *   **Status:** UI loads, but "Workbench failed to connect to the server (Error: WebSocket close with status code 1006)". Console logs show `WebSocket connection to 'wss://davidlybeck.com/dev/vscode/stable-...' failed: `.
    *   Repeated errors like `[remote-connection]... the handshake timed out. Error: Time limit reached`.
    *   `CodeExpectedError: ENOPRO: No file system provider found` for various `vscode-remote:/Users/dlybeck/.local/share/code-server/User/...` paths.
    *   `GET .../vsda.js` and `GET .../vsda_bg.wasm` 404 (Not Found).
    *   **Analysis:** The `1006` WebSocket close implies the `code-server` on the Mac is rejecting/dropping the connection, or it's failing immediately after initial TCP setup. The "handshake timed out" suggests the application-level handshake (VS Code client <-> VS Code server) is failing. The `ENOPRO` is a direct consequence of the WS failure. The `vsda` 404s are likely assets not found on the upstream `code-server` and might or might not be critical to the core functionality.
    *   **Fixes Implemented:**
        *   Spoofed `Origin` header in `BaseProxy` to match the upstream `http://100.x.y.z`.
        *   Explicitly extracted `Sec-WebSocket-Protocol` from browser and passed it as `protocols` argument to `aiohttp.ws_connect`.
        *   **Latest Fix (just pushed, `bd9e8dd`):** Force `Sec-WebSocket-Protocol` into the `headers` dictionary when connecting via `aiohttp` to the upstream, in addition to passing it as a protocol argument. This ensures `code-server` sees the required auth/subprotocol header.

### **Ongoing Plan (for the next AI)**

The immediate goal is to achieve full functionality of both Agor and VS Code iframes, with stable long-lived connections, without manual intervention after network changes.

1.  **Verify Agor Functionality (Post-Rewrite Deployment):**
    *   **Action:** First, confirm if the latest `AgorProxy` rewrite (targeting template literals for API paths and favicon) has resolved the `/health` 404s and enabled successful login/functionality.
    *   **If `/health` 404s persist:**
        *   **Next Step:** Perform a more thorough analysis of Agor's main JavaScript bundle (`index-Cvydvvaf.js`) by fetching it through the proxy and searching for all instances of `/health`, `/auth`, `/api`, and `favicon.png` to identify patterns missed by current rewrite rules. Use `grep -oE` or similar to find context.
        *   **Next Step:** Implement a more robust regex-based replacement if string literals are insufficient, or try to identify Agor's base path configuration variable and set it dynamically.

2.  **Debug VS Code WebSocket `1006` Error (Post-Header Fix Deployment):**
    *   **Action:** Confirm if the `WebSocket close with status code 1006` error (and subsequent `ENOPRO` errors) persists after the deployment of the latest `BaseProxy` fix (passing `Sec-WebSocket-Protocol` as both argument and header).
    *   **If it persists:** This indicates `code-server` is still rejecting the WebSocket.
        *   **Next Step:** The `websockets` Python library (used by the Terminal WebSocket proxy, which is more stable) is a strong alternative. Refactor `BaseProxy.proxy_websocket` to use the `websockets` library directly (instead of `aiohttp`) for the WebSocket connection. This involves adapting the current logic for `websockets.connect` syntax and its proxy integration (via `proxy=SOCKS5_PROXY`). This aims to eliminate any `aiohttp` specific issues with SOCKS5.
        *   **Next Step:** Enable verbose logging for the `websockets` library on the server side to gain insight into the exact point of failure during the handshake (e.g., protocol negotiation, authentication challenge).

3.  **Address VS Code `vsda` 404s (Lower Priority):**
    *   **Action:** After the core WebSocket connection is stable, re-evaluate these 404s.
    *   **Analysis:** If the files (`vsda.js`, `vsda_bg.wasm`) are genuinely missing on the Mac's `code-server` installation (e.g., due to proprietary components), they might be benign warnings or require a different `code-server` build/configuration. If they are caused by path rewriting issues, `CodeServerProxy` might need to implement limited rewrite logic similar to Agor, or `code-server` on the Mac needs to be configured with `--base-path /`.
    *   **Next Step:** Try accessing `http://<MAC_SERVER_IP>:8888/stable-904942a1944f66a886b0ec5c0c60f312d559a6e6/static/node_modules/vsda/rust/web/vsda.js` directly from the Mac (via curl or browser) to see if the file exists there. This differentiates between a proxy issue and a missing file issue.

This document serves as a complete handover to continue debugging and resolving the remaining issues.