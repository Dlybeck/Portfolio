from fastapi import Request, Response
from fastapi.responses import RedirectResponse
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.types import ASGIApp, Receive, Scope, Send
from services.opencode_web_proxy import get_opencode_proxy
from core.dev_utils import extract_token
import logging

logger = logging.getLogger(__name__)

class OpenCodeSubdomainMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next):
        host = request.headers.get("host", "")

        if "opencode.davidlybeck.com" in host or "opencode." in host:
            # Check authentication before proxying
            token = extract_token(request)

            if not token:
                # Redirect to login page
                return_url = str(request.url)
                login_url = f"https://davidlybeck.com/dev/login?redirect={return_url}"
                logger.warning(f"Unauthenticated access attempt to {request.url.path}")
                return RedirectResponse(url=login_url, status_code=307)

            # Token exists - proceed with proxy
            logger.info(f"Authenticated request to opencode subdomain: {request.url.path}")
            path = request.url.path.lstrip("/")
            proxy = get_opencode_proxy()
            return await proxy.proxy_request(request, path)

        return await call_next(request)

class OpenCodeWebSocketMiddleware:
    def __init__(self, app: ASGIApp):
        self.app = app

    async def __call__(self, scope: Scope, receive: Receive, send: Send):
        if scope["type"] == "websocket":
            headers_dict = {k.decode(): v.decode() for k, v in scope.get("headers", [])}
            host = headers_dict.get("host", "")
            path = scope["path"]

            logger.info(f"WebSocket connection: host={host}, path={path}")

            if "opencode.davidlybeck.com" in host or "opencode." in host:
                # Check authentication for WebSocket connections
                # Extract token from query params or cookies
                query_string = scope.get("query_string", b"").decode()
                from urllib.parse import parse_qs
                query_params = parse_qs(query_string)

                token = None
                # Check query param first (most common for WebSocket)
                if "tkn" in query_params:
                    token = query_params["tkn"][0]

                # Check cookie header
                if not token:
                    cookie_header = headers_dict.get("cookie", "")
                    if "session_token=" in cookie_header:
                        # Simple cookie parsing
                        for cookie_part in cookie_header.split(";"):
                            cookie_part = cookie_part.strip()
                            if cookie_part.startswith("session_token="):
                                token = cookie_part.split("=", 1)[1]
                                break

                if not token:
                    logger.warning(f"Unauthenticated WebSocket attempt to {path}")
                    # Close WebSocket with auth error
                    from starlette.websockets import WebSocket as StarletteWebSocket
                    websocket = StarletteWebSocket(scope, receive=receive, send=send)
                    await websocket.close(code=1008, reason="Not authenticated")
                    return

                logger.info(f"Authenticated WebSocket to opencode subdomain: {path}")

                if path.startswith("/pty/"):
                    logger.info(f"PTY WebSocket - passing to local router: {path}")
                    await self.app(scope, receive, send)
                    return

                from starlette.websockets import WebSocket as StarletteWebSocket

                websocket = StarletteWebSocket(scope, receive=receive, send=send)
                path_clean = path.lstrip("/")

                logger.info(f"OpenCode WebSocket matched! Proxying: {path_clean}")
                proxy = get_opencode_proxy()
                try:
                    await proxy.proxy_websocket(websocket, path_clean)
                except Exception as e:
                    logger.error(f"WebSocket proxy error: {e}", exc_info=True)
                    try:
                        await websocket.close(code=1011, reason=str(e))
                    except:
                        pass
                return

        await self.app(scope, receive, send)

opencode_subdomain_middleware = OpenCodeSubdomainMiddleware
