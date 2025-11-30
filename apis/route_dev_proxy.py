"""
Dev Dashboard Proxy and WebSocket Routes
"""

from fastapi import APIRouter, Depends, Request, WebSocket, WebSocketDisconnect
from core.security import get_session_user
from services.code_server_proxy import get_proxy as get_vscode_proxy
from services.session_manager import get_or_create_persistent_session, close_persistent_session
from core.config import settings
import asyncio
import json
import logging
import websockets
import os

logger = logging.getLogger(__name__)

dev_proxy_router = APIRouter(prefix="/dev", tags=["Dev Dashboard - Proxy"])


# ==================== Terminal WebSocket ====================
@dev_proxy_router.websocket("/ws/terminal")
async def terminal_websocket(websocket: WebSocket, cwd: str = "~", session: str = None, token: str = None, mode: str = None):
    """
    🔒 WebSocket endpoint for terminal access - requires JWT token
    Proxy if Cloud Run, execute if Mac
    """
    # Validate JWT token before accepting WebSocket connection
    if not token:
        await websocket.close(code=1008, reason="Missing authentication token")
        return

    try:
        from core.security import verify_token
        payload = verify_token(token)
        if payload.get("type") != "access":
            await websocket.close(code=1008, reason="Invalid token type")
            return
        logger.debug(f"WebSocket authenticated for user: {payload.get('sub')}")
    except Exception as e:
        logger.warning(f"WebSocket authentication failed: {e}")
        await websocket.close(code=1008, reason="Invalid authentication token")
        return

    await websocket.accept()

    if settings.K_SERVICE is not None:
        # Cloud Run: Proxy WebSocket to Mac via SOCKS5
        try:
            # Connect to Mac's WebSocket through SOCKS5 (forward auth token and mode)
            ws_url = f"ws://{settings.MAC_SERVER_IP}:{settings.MAC_SERVER_PORT}/dev/ws/terminal?cwd={cwd}&token={token}"
            if session:
                ws_url += f"&session={session}"
            if mode:
                ws_url += f"&mode={mode}"

            async with websockets.connect(
                ws_url,
                extra_headers=websocket.headers,
                proxy=settings.SOCKS5_PROXY,
                open_timeout=10
            ) as ws:
                # Bidirectional proxy
                async def forward_to_mac():
                    """Forward messages from browser to Mac"""
                    try:
                        while True:
                            data = await websocket.receive_text()
                            await ws.send(data)
                    except WebSocketDisconnect:
                        pass # Client disconnected
                    except Exception as e:
                        logger.error(f"Forward to Mac error: {e}")

                async def forward_to_browser():
                    """Forward messages from Mac to browser"""
                    try:
                        async for msg in ws:
                            await websocket.send_text(msg)
                    except websockets.exceptions.ConnectionClosed:
                        pass # Server disconnected
                    except Exception as e:
                        logger.error(f"Forward to browser error: {e}")

                # Run both directions concurrently
                await asyncio.gather(
                    forward_to_mac(),
                    forward_to_browser()
                )
        except Exception as e:
            logger.error(f"WebSocket proxy error: {e}")
            await websocket.close()
        return

    # Mac: Execute terminal locally with persistent session
    # Check if client requested a new session (e.g., after kill button)
    if session:
        session_id = session
    else:
        session_id = "user_main_session"

    # Expand working directory
    working_dir = os.path.expanduser(cwd)

    try:
        # Get or create persistent session
        persistent_session = get_or_create_persistent_session(
            session_id=session_id,
            working_dir=working_dir,
            command="bash"
        )

        # Set client's preferred mode if this is a new session
        if mode and mode in ['fancy', 'simple']:
            if not persistent_session.claude_started:
                persistent_session.term_mode = mode
                logger.debug(f"Setting initial term mode to '{mode}' for new session '{session_id}'")

        # Add this client to the session
        persistent_session.add_client(websocket)

        # Send buffered history to new client
        history = persistent_session.get_buffered_history()
        if history:
            await websocket.send_text(json.dumps({"type": "output", "data": history}))

        # Start broadcast loop if not already running
        await persistent_session.start_broadcast_loop()

        # Send current term mode to new client
        await websocket.send_text(json.dumps({
            "type": "current_term_mode",
            "mode": persistent_session.term_mode
        }))

        # Auto-start Claude ONCE per session (skip for terminal tab sessions)
        is_terminal_tab = session_id.startswith('terminal_tab_')
        if not is_terminal_tab:
            async with persistent_session.claude_start_lock:
                if not persistent_session.claude_started:
                    logger.debug(f"Auto-starting Claude in '{persistent_session.term_mode}' mode...")
                    await asyncio.sleep(1.5)
                    if persistent_session.term_mode == 'simple':
                        persistent_session.write("export TERM=dumb\n")
                    else:
                        persistent_session.write("export TERM=xterm-256color\n")
                    persistent_session.write("source ~/.zshrc 2>/dev/null || source ~/.bashrc 2>/dev/null; exec claude\n")
                    persistent_session.claude_started = True
                    logger.debug(f"Claude started with TERM={persistent_session.term_mode}")
        else:
            logger.debug("Terminal tab session - skipping Claude auto-start")

        # Handle messages from this client
        async def handle_client_messages():
            nonlocal last_pong_time
            while True:
                message = await websocket.receive_text()
                data = json.loads(message)

                if data["type"] == "input":
                    persistent_session.write(data["data"])
                elif data["type"] == "resize":
                    persistent_session.resize(data["rows"], data["cols"])
                elif data["type"] == "ping":
                    await websocket.send_text(json.dumps({"type": "pong"}))
                elif data["type"] == "pong":
                    last_pong_time = asyncio.get_event_loop().time()
                elif data["type"] == "toggle_term_mode":
                    new_mode = data.get("mode", "fancy")
                    logger.debug(f"Toggling term mode to '{new_mode}' for session '{session_id}'")
                    persistent_session.set_term_mode(new_mode)

                    # Broadcast mode change to all connected clients
                    mode_change_msg = json.dumps({"type": "term_mode_changed", "mode": new_mode})
                    disconnected = set()
                    for client in persistent_session.connected_clients:
                        try:
                            await client.send_text(mode_change_msg)
                        except Exception as e:
                            logger.error(f"Error sending mode change to client: {e}")
                            disconnected.add(client)

                    for client in disconnected:
                        persistent_session.remove_client(client)

                    close_persistent_session(session_id)
                    break

        # Track last pong time for timeout detection
        last_pong_time = asyncio.get_event_loop().time()
        ping_timeout = 10

        async def send_keepalive_pings():
            nonlocal last_pong_time
            try:
                while True:
                    await asyncio.sleep(15)
                    time_since_pong = asyncio.get_event_loop().time() - last_pong_time
                    if time_since_pong > ping_timeout:
                        logger.warning(f"Client timeout - no pong for {time_since_pong:.1f}s. Closing connection.")
                        break
                    try:
                        await websocket.send_text(json.dumps({"type": "ping"}))
                        logger.debug(f"Sent ping (last pong: {time_since_pong:.1f}s ago)")
                    except Exception as e:
                        logger.error(f"Ping failed: {e}")
                        break
            except asyncio.CancelledError:
                pass

        await asyncio.gather(handle_client_messages(), send_keepalive_pings())

    except WebSocketDisconnect:
        persistent_session.remove_client(websocket)
        logger.debug(f"Client disconnected, {len(persistent_session.connected_clients)} clients remaining")
        if len(persistent_session.connected_clients) == 0:
            logger.debug(f"No clients left, closing session '{session_id}' to prevent PTY leak")
            close_persistent_session(session_id)

    except Exception as e:
        logger.error(f"Terminal error: {e}")
        persistent_session.remove_client(websocket)
        if len(persistent_session.connected_clients) == 0:
            logger.debug(f"No clients left after error, closing session '{session_id}' to prevent PTY leak")
            close_persistent_session(session_id)
        try:
            await websocket.close()
        except:
            pass


# ==================== CODE-SERVER PROXY ROUTES ====================
@dev_proxy_router.get("/vscode/{path:path}")
@dev_proxy_router.post("/vscode/{path:path}")
@dev_proxy_router.put("/vscode/{path:path}")
@dev_proxy_router.delete("/vscode/{path:path}")
@dev_proxy_router.patch("/vscode/{path:path}")
async def vscode_proxy(
    path: str,
    request: Request,
    user: dict = Depends(get_session_user)
):
    """
    🔒 Authenticated proxy to code-server
    """
    proxy = get_vscode_proxy()
    return await proxy.proxy_request(request, path)


@dev_proxy_router.websocket("/vscode/{path:path}")
async def vscode_websocket_proxy(
    websocket: WebSocket,
    path: str,
    token: str = None,
    tkn: str = None
):
    """
    🔒 Authenticated WebSocket proxy to code-server
    """
    auth_token = tkn or token or websocket.cookies.get("session_token")
    if not auth_token:
        referer = websocket.headers.get("referer", "")
        if "tkn=" in referer:
            import urllib.parse
            parsed = urllib.parse.urlparse(referer)
            params = urllib.parse.parse_qs(parsed.query)
            if "tkn" in params and params["tkn"]:
                auth_token = params["tkn"][0]
                logger.debug("Extracted token from Referer header")

    if not auth_token:
        logger.warning("No authentication token found (cookie, query, or referer)")
        await websocket.close(code=1008, reason="Missing authentication token")
        return

    try:
        from core.security import verify_token
        payload = verify_token(auth_token)
        if payload.get("type") != "access":
            await websocket.close(code=1008, reason="Invalid token type")
            return
        logger.debug(f"Authenticated user: {payload.get('sub')}")
    except Exception as e:
        logger.warning(f"Authentication failed: {e}")
        await websocket.close(code=1008, reason="Invalid authentication token")
        return

    await websocket.accept()

    if settings.K_SERVICE is not None:
        # Cloud Run: Proxy WebSocket to Mac via SOCKS5 (same pattern as terminal)
        try:
            # Construct code-server WebSocket URL (code-server runs at root, not /dev/vscode/)
            ws_url = f"ws://{settings.MAC_SERVER_IP}:{settings.MAC_SERVER_PORT}/{path}"

            # Preserve query parameters (critical for reconnectionToken)
            if websocket.url.query:
                ws_url += f"?{websocket.url.query}"
                logger.info(f"Code-server WS: Forwarding query params: {websocket.url.query}")

            logger.info(f"Code-server WS: Connecting to {ws_url}")

            # Connect using simple pattern (EXACTLY like terminal)
            async with websockets.connect(
                ws_url,
                extra_headers=websocket.headers,
                proxy=settings.SOCKS5_PROXY,  # Native library support
                open_timeout=10
            ) as ws:
                logger.info("Code-server WS: Connected successfully!")

                # Bidirectional proxy (EXACTLY like terminal)
                async def forward_to_mac():
                    try:
                        while True:
                            data = await websocket.receive_text()
                            await ws.send(data)
                    except WebSocketDisconnect:
                        pass
                    except Exception as e:
                        logger.error(f"Code-server WS forward to Mac error: {e}")

                async def forward_to_browser():
                    try:
                        async for msg in ws:
                            await websocket.send_text(msg)
                    except websockets.exceptions.ConnectionClosed:
                        pass
                    except Exception as e:
                        logger.error(f"Code-server WS forward to browser error: {e}")

                await asyncio.gather(forward_to_mac(), forward_to_browser())

        except Exception as e:
            logger.error(f"Code-server WebSocket proxy error: {e}")
            await websocket.close()
        return

    # Mac: Direct connection (no proxy needed)
    try:
        # Connect directly to local code-server
        ws_url = f"ws://127.0.0.1:{settings.CODE_SERVER_PORT}/{path}"
        if websocket.url.query:
            ws_url += f"?{websocket.url.query}"
            logger.info(f"Code-server WS (local): Forwarding query params: {websocket.url.query}")

        logger.info(f"Code-server WS (local): Connecting to {ws_url}")

        async with websockets.connect(ws_url, extra_headers=websocket.headers) as ws:
            logger.info("Code-server WS (local): Connected!")

            # Same bidirectional forwarding
            async def forward_to_server():
                try:
                    while True:
                        data = await websocket.receive_text()
                        await ws.send(data)
                except WebSocketDisconnect:
                    pass
                except Exception as e:
                    logger.error(f"Code-server WS (local) forward error: {e}")

            async def forward_to_client():
                try:
                    async for msg in ws:
                        await websocket.send_text(msg)
                except websockets.exceptions.ConnectionClosed:
                    pass
                except Exception as e:
                    logger.error(f"Code-server WS (local) receive error: {e}")

            await asyncio.gather(forward_to_server(), forward_to_client())

    except Exception as e:
        logger.error(f"Code-server WebSocket error (local): {e}")
        await websocket.close()

