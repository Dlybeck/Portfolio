from fastapi import Request, Response
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.types import ASGIApp, Receive, Scope, Send
from services.opencode_web_proxy import get_opencode_proxy
import logging

logger = logging.getLogger(__name__)

class OpenCodeSubdomainMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next):
        host = request.headers.get("host", "")
        
        if "opencode.davidlybeck.com" in host or "opencode." in host:
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
