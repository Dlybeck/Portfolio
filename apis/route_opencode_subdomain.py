from fastapi import APIRouter, Request, HTTPException, WebSocket
from services.opencode_web_proxy import get_opencode_proxy

opencode_subdomain_router = APIRouter()

@opencode_subdomain_router.api_route("/{path:path}", methods=["GET", "POST", "PUT", "DELETE", "PATCH"])
async def proxy_opencode_root(request: Request, path: str = ""):
    """Proxy all requests from opencode.davidlybeck.com subdomain"""
    host = request.headers.get("host", "")
    
    if "opencode.davidlybeck.com" not in host and "opencode." not in host:
        raise HTTPException(status_code=404, detail="Not found")
    
    proxy = get_opencode_proxy()
    return await proxy.proxy_request(request, path)

@opencode_subdomain_router.websocket("/{path:path}")
async def proxy_opencode_ws_root(websocket: WebSocket, path: str = ""):
    """Proxy WebSocket connections from opencode.davidlybeck.com subdomain"""
    host = websocket.headers.get("host", "")
    
    if "opencode.davidlybeck.com" not in host and "opencode." not in host:
        await websocket.close(code=1008, reason="Invalid host")
        return
        
    proxy = get_opencode_proxy()
    await proxy.proxy_websocket(websocket, path)
