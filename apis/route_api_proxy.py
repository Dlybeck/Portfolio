"""
API Proxy Routes - Forward /api/agentbridge/* requests to Ubuntu server
"""

from fastapi import APIRouter, Depends, Request, WebSocket, Response
from core.security import get_session_user
from core.config import settings
import httpx
import logging
import json

logger = logging.getLogger(__name__)

api_proxy_router = APIRouter(prefix="/api/agentbridge", tags=["API Proxy - AgentBridge"])

# Target server (Ubuntu)
BACKEND_URL = f"http://{settings.MAC_SERVER_IP}:{settings.MAC_SERVER_PORT}"


@api_proxy_router.get("/{path:path}")
@api_proxy_router.post("/{path:path}")
@api_proxy_router.put("/{path:path}")
@api_proxy_router.delete("/{path:path}")
@api_proxy_router.patch("/{path:path}")
async def agentbridge_api_proxy(
    path: str,
    request: Request,
    user: dict = Depends(get_session_user)
):
    """
    🔒 Authenticated proxy to AgentBridge API on Ubuntu server
    Forwards /api/agentbridge/* requests to Ubuntu FastAPI instance
    """
    # Construct target URL
    target_url = f"{BACKEND_URL}/api/agentbridge/{path}"
    if request.url.query:
        target_url += f"?{request.url.query}"

    logger.info(f"Proxying {request.method} {request.url.path} -> {target_url}")

    try:
        # Forward request to Ubuntu
        async with httpx.AsyncClient(timeout=30.0) as client:
            # Get request body if any
            body = await request.body()

            # Forward headers, but replace Authorization with internal auth
            # since Cloud Run already validated the user
            forward_headers = {
                key: value
                for key, value in request.headers.items()
                if key.lower() not in ["host", "content-length", "authorization"]
            }
            # Add internal proxy header with user info
            forward_headers["X-Proxy-User"] = json.dumps(user)

            response = await client.request(
                method=request.method,
                url=target_url,
                headers=forward_headers,
                content=body if body else None
            )

            # Log response status
            logger.info(f"[API Proxy] Response from {target_url}: {response.status_code}")

            # Return response
            return Response(
                content=response.content,
                status_code=response.status_code,
                headers=dict(response.headers),
                media_type=response.headers.get("content-type")
            )

    except httpx.ConnectError as e:
        logger.error(f"Failed to connect to backend: {e}")
        return Response(
            content=json.dumps({"detail": "Backend server unavailable", "error": str(e)}),
            status_code=503,
            media_type="application/json"
        )
    except Exception as e:
        logger.error(f"AgentBridge API proxy error: {e}")
        return Response(
            content=json.dumps({"detail": f"Proxy error: {str(e)}", "error_type": type(e).__name__}),
            status_code=500,
            media_type="application/json"
        )


@api_proxy_router.websocket("/ws")
async def agentbridge_websocket_proxy(
    websocket: WebSocket,
    token: str = None
):
    """
    🔒 Authenticated WebSocket proxy to AgentBridge on Ubuntu server
    """
    # Accept the websocket connection
    await websocket.accept()

    # Verify authentication
    auth_token = token or websocket.cookies.get("session_token")
    if not auth_token:
        await websocket.close(code=1008, reason="Authentication required")
        return

    # Verify token
    try:
        from core.security import verify_token
        payload = verify_token(auth_token)
        if payload.get("type") != "access":
            await websocket.close(code=1008, reason="Invalid token")
            return
    except:
        await websocket.close(code=1008, reason="Invalid token")
        return

    # Proxy WebSocket to Ubuntu
    import websockets
    import asyncio

    ws_url = f"ws://{settings.MAC_SERVER_IP}:{settings.MAC_SERVER_PORT}/api/agentbridge/ws?token={auth_token}"
    logger.info(f"Proxying WebSocket -> {ws_url}")

    try:
        async with websockets.connect(ws_url) as backend_ws:
            async def forward_to_backend():
                try:
                    while True:
                        data = await websocket.receive_text()
                        await backend_ws.send(data)
                except Exception as e:
                    logger.error(f"AgentBridge WS forward error: {e}")

            async def forward_to_client():
                try:
                    async for msg in backend_ws:
                        await websocket.send_text(msg)
                except Exception as e:
                    logger.error(f"AgentBridge WS receive error: {e}")

            await asyncio.gather(forward_to_backend(), forward_to_client())

    except Exception as e:
        logger.error(f"AgentBridge WebSocket proxy error: {e}")
        await websocket.close()
