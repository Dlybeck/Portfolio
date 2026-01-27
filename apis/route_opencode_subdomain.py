from fastapi import Request
from starlette.middleware.base import BaseHTTPMiddleware
from services.opencode_web_proxy import get_opencode_proxy

class OpenCodeSubdomainMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next):
        host = request.headers.get("host", "")
        
        if "opencode.davidlybeck.com" in host or "opencode." in host:
            path = request.url.path.lstrip("/")
            
            if request.headers.get("upgrade", "").lower() == "websocket":
                return await call_next(request)
            
            proxy = get_opencode_proxy()
            return await proxy.proxy_request(request, path)
        
        return await call_next(request)

opencode_subdomain_middleware = OpenCodeSubdomainMiddleware
