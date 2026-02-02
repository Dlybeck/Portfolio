from fastapi import APIRouter, Request, HTTPException, WebSocket, Response
from core.dev_utils import require_auth
from services.code_server_proxy import get_proxy as get_vscode_proxy
from services.opencode_web_proxy import get_opencode_proxy

dev_proxy_router = APIRouter(tags=["Dev Proxy"])

@dev_proxy_router.api_route("/vscode-proxy/{path:path}", methods=["GET", "POST", "PUT", "DELETE", "PATCH"])
async def proxy_vscode(request: Request, path: str):
    token = request.query_params.get("tkn") or request.cookies.get("session_token")
    if not token:
        auth = request.headers.get("Authorization", "")
        if auth.startswith("Bearer "):
            token = auth.replace("Bearer ", "")
            
    if not token:
        raise HTTPException(status_code=401, detail="Not authenticated")
    
    if path.endswith("vsda.js"):
        return Response(content="", media_type="application/javascript")
    if path.endswith("vsda_bg.wasm"):
        return Response(content="", media_type="application/wasm")
        
    proxy = get_vscode_proxy()
    return await proxy.proxy_request(request, path)

@dev_proxy_router.websocket("/vscode-proxy/{path:path}")
async def proxy_vscode_ws(websocket: WebSocket, path: str):
    token = websocket.query_params.get("tkn") or websocket.cookies.get("session_token")
    if not token:
        await websocket.close(code=1008, reason="Missing authentication")
        return
        
    proxy = get_vscode_proxy()
    await proxy.proxy_websocket(websocket, path)

@dev_proxy_router.api_route("/opencode-proxy/{path:path}", methods=["GET", "POST", "PUT", "DELETE", "PATCH"])
async def proxy_opencode(request: Request, path: str):
    token = request.query_params.get("tkn") or request.cookies.get("session_token")
    if not token:
        auth = request.headers.get("Authorization", "")
        if auth.startswith("Bearer "):
            token = auth.replace("Bearer ", "")
            
    if not token:
        raise HTTPException(status_code=401, detail="Not authenticated")
    
    proxy = get_opencode_proxy()
    return await proxy.proxy_request(request, path)

@dev_proxy_router.websocket("/opencode-proxy/{path:path}")
async def proxy_opencode_ws(websocket: WebSocket, path: str):
    token = websocket.query_params.get("tkn") or websocket.cookies.get("session_token")
    if not token:
        await websocket.close(code=1008, reason="Missing authentication")
        return
        
    proxy = get_opencode_proxy()
    await proxy.proxy_websocket(websocket, path)
