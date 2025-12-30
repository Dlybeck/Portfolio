"""
Dev Dashboard Proxy and WebSocket Routes
"""

from fastapi import APIRouter, Depends, Request, WebSocket, WebSocketDisconnect, Response
from core.security import get_session_user
from services.code_server_proxy import get_proxy as get_vscode_proxy
from core.config import settings
import asyncio
import logging
import websockets

logger = logging.getLogger(__name__)

dev_proxy_router = APIRouter(prefix="/dev", tags=["Dev Dashboard - Proxy"])


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
    # MOCK RESPONSE: Handle missing optional VS Code components (vsda)
    # These files are proprietary to MS VS Code and missing in code-server.
    # Returning 200 OK (empty) prevents console errors/noise.
    if path.endswith("vsda.js"):
        return Response(content="", media_type="application/javascript")
    if path.endswith("vsda_bg.wasm"):
        return Response(content="", media_type="application/wasm")

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
        # Cloud Run: Proxy WebSocket to Mac via SOCKS5
        sock = None
        try:
            # Construct code-server WebSocket URL (code-server runs at root, not /dev/vscode/)
            # CRITICAL: websockets library expects ws://hostname:port/path
            # We must use the IP address to avoid DNS resolution issues in SOCKS proxy
            ws_url = f"ws://{settings.MAC_SERVER_IP}:{settings.CODE_SERVER_PORT}/{path}"

            # Preserve query parameters (critical for reconnectionToken)
            if websocket.url.query:
                ws_url += f"?{websocket.url.query}"
                logger.info(f"Code-server WS: Forwarding query params: {websocket.url.query}")

            logger.info(f"Code-server WS: Connecting to {ws_url}")

            # 1. Create SOCKS5 connection manually using python-socks
            # This bypasses websockets library's native proxy support which is flaky
            from python_socks.async_.asyncio import Proxy
            
            logger.info(f"Code-server WS: Creating SOCKS5 tunnel via {settings.SOCKS5_PROXY}")
            proxy = Proxy.from_url(settings.SOCKS5_PROXY)
            
            # Connect to the proxy, then tunnel to the destination
            # dest_host must be the IP address (100.x.y.z) to ensure SOCKS5 uses it directly
            sock = await proxy.connect(
                dest_host=settings.MAC_SERVER_IP,
                dest_port=settings.CODE_SERVER_PORT
            )
            logger.info("Code-server WS: SOCKS5 tunnel established successfully")

            # 2. Connect WebSocket over the existing SOCKS tunnel
            # NOTE: We are NOT passing extra_headers here because it causes a TypeError
            # ("unexpected keyword argument 'extra_headers'") when combined with 'sock' in websockets 15.0.
            # VS Code uses the 'reconnectionToken' in the query params (which we preserved) for session tracking.
            async with websockets.connect(
                ws_url,
                sock=sock, # Pass the connected socket
                open_timeout=20, # Allow extra time for handshake
                ping_interval=20,  # Send ping every 20 seconds to keep connection alive
                ping_timeout=60    # Close if no pong received for 60 seconds
            ) as ws:
                logger.info("Code-server WS: WebSocket handshake complete!")

                # Bidirectional proxy (EXACTLY like terminal)
                async def forward_to_mac():
                    try:
                        while True:
                            # Receive can range from text to bytes
                            message = await websocket.receive()
                            if "text" in message:
                                await ws.send(message["text"])
                            elif "bytes" in message:
                                await ws.send(message["bytes"])
                    except WebSocketDisconnect:
                        logger.info("Code-server WS: Client disconnected")
                    except Exception as e:
                        logger.error(f"Code-server WS forward to Mac error: {e}")

                async def forward_to_browser():
                    try:
                        async for msg in ws:
                            # Forward text or bytes back to browser
                            if isinstance(msg, str):
                                await websocket.send_text(msg)
                            else:
                                await websocket.send_bytes(msg)
                    except websockets.exceptions.ConnectionClosed:
                        logger.info("Code-server WS: Server disconnected")
                    except Exception as e:
                        logger.error(f"Code-server WS forward to browser error: {e}")

                await asyncio.gather(forward_to_mac(), forward_to_browser())

        except Exception as e:
            logger.error(f"Code-server WebSocket proxy error: {e}")
            # Close socket explicitly if it was created but WS failed
            if sock:
                try:
                    sock.close()
                except:
                    pass
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

        async with websockets.connect(
            ws_url,
            extra_headers=websocket.headers,
            ping_interval=20,  # Send ping every 20 seconds to keep connection alive
            ping_timeout=60    # Close if no pong received for 60 seconds
        ) as ws:
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

