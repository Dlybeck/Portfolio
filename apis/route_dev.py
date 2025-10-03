"""
Dev Dashboard routes
Serves the dashboard interface and login page
Proxies requests to Mac development server via Tailscale
"""

from fastapi import APIRouter, Depends, Request, WebSocket, WebSocketDisconnect
from fastapi.responses import HTMLResponse, JSONResponse
from fastapi.templating import Jinja2Templates
from pydantic import BaseModel
from core.security import get_current_user
from services.terminal_service import get_or_create_session, close_session
import json
import asyncio
import os
import httpx
from pathlib import Path

# Mac server Tailscale IP (from your Tailscale network)
MAC_SERVER_IP = "100.84.184.84"
MAC_SERVER_PORT = 8080
MAC_SERVER_URL = f"http://{MAC_SERVER_IP}:{MAC_SERVER_PORT}"

# Tailscale SOCKS5 proxy (for userspace networking mode)
SOCKS5_PROXY = "socks5://localhost:1055"

# Detect if running in Cloud Run (proxy mode) or locally (direct mode)
IS_CLOUD_RUN = os.environ.get("K_SERVICE") is not None

# Check if services are available (Mac is reachable via Tailscale SOCKS5)
def is_mac_server_available():
    """Check if the Mac development server is reachable via Tailscale SOCKS5 proxy"""
    try:
        print(f"[DEBUG] Checking Mac server at {MAC_SERVER_IP}:{MAC_SERVER_PORT} via SOCKS5")

        # Use synchronous httpx client with SOCKS5 proxy
        with httpx.Client(timeout=3.0, proxy=SOCKS5_PROXY) as client:
            response = client.get(f"{MAC_SERVER_URL}/")
            is_available = response.status_code < 500
            print(f"[DEBUG] Mac server available: {is_available} (status: {response.status_code})")
            return is_available
    except Exception as e:
        print(f"[DEBUG] Mac server check failed: {e}")
        return False

dev_router = APIRouter(prefix="/dev", tags=["Dev Dashboard"])

templates = Jinja2Templates(directory="templates")


class ChatRequest(BaseModel):
    message: str
    working_dir: str = None


class DirectoryRequest(BaseModel):
    path: str


@dev_router.get("/debug/connectivity")
async def debug_connectivity():
    """Debug endpoint to test Mac connectivity"""
    import socket

    results = {
        "mac_ip": MAC_SERVER_IP,
        "mac_port": MAC_SERVER_PORT,
        "mac_url": MAC_SERVER_URL
    }

    # Test socket connection
    try:
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sock.settimeout(5)
        result = sock.connect_ex((MAC_SERVER_IP, MAC_SERVER_PORT))
        sock.close()
        results["socket_test"] = {
            "success": result == 0,
            "error_code": result
        }
    except Exception as e:
        results["socket_test"] = {"error": str(e)}

    # Test HTTP request through SOCKS5 proxy
    try:
        async with httpx.AsyncClient(timeout=5.0, proxy=SOCKS5_PROXY) as client:
            response = await client.get(f"{MAC_SERVER_URL}/")
            results["http_test"] = {
                "status": response.status_code,
                "success": True
            }
    except Exception as e:
        results["http_test"] = {
            "error": str(e),
            "success": False
        }

    # Test is_mac_server_available function
    results["is_available"] = is_mac_server_available()

    return results


@dev_router.get("/login", response_class=HTMLResponse)
async def login_page(request: Request):
    """Serve the login page"""
    return templates.TemplateResponse("dev/login.html", {"request": request})


@dev_router.get("", response_class=HTMLResponse)
async def project_selector(request: Request):
    """
    Project selector page - choose working directory
    """
    if not is_mac_server_available():
        return templates.TemplateResponse("dev/server_offline.html", {
            "request": request
        })
    return templates.TemplateResponse("dev/project_selector.html", {
        "request": request
    })


@dev_router.get("/terminal", response_class=HTMLResponse)
async def terminal_dashboard(request: Request):
    """
    Terminal dashboard page
    Authentication is checked client-side via JavaScript
    """
    if not is_mac_server_available():
        return templates.TemplateResponse("dev/server_offline.html", {
            "request": request
        })
    return templates.TemplateResponse("dev/dashboard.html", {
        "request": request,
        "user": {"username": "admin"}
    })


@dev_router.post("/api/chat")
async def chat_with_claude(
    req: Request,
    user: dict = Depends(get_current_user)
):
    """Proxy chat requests to Mac server via Tailscale SOCKS5"""
    try:
        body = await req.body()
        # Forward the Authorization header from the original request
        auth_header = req.headers.get("Authorization", "")
        headers = {
            "Content-Type": "application/json",
            "Authorization": auth_header
        }
        async with httpx.AsyncClient(timeout=60.0, proxy=SOCKS5_PROXY) as client:
            response = await client.post(
                f"{MAC_SERVER_URL}/dev/api/chat",
                content=body,
                headers=headers
            )
            return JSONResponse(content=response.json(), status_code=response.status_code)
    except Exception as e:
        return JSONResponse(content={"error": str(e)}, status_code=500)


@dev_router.post("/api/list-directory")
async def list_directory(
    req: Request,
    user: dict = Depends(get_current_user)
):
    """List directories - proxy if Cloud Run, execute locally if Mac"""
    if IS_CLOUD_RUN:
        # Cloud Run: Proxy to Mac via Tailscale SOCKS5
        try:
            body = await req.body()
            auth_header = req.headers.get("Authorization", "")
            headers = {
                "Content-Type": "application/json",
                "Authorization": auth_header
            }
            async with httpx.AsyncClient(timeout=10.0, proxy=SOCKS5_PROXY) as client:
                response = await client.post(
                    f"{MAC_SERVER_URL}/dev/api/list-directory",
                    content=body,
                    headers=headers
                )
                return JSONResponse(content=response.json(), status_code=response.status_code)
        except Exception as e:
            return JSONResponse(content={"error": str(e)}, status_code=500)
    else:
        # Mac: Execute locally
        class DirectoryRequest(BaseModel):
            path: str

        try:
            body = await req.json()
            dir_req = DirectoryRequest(**body)

            # Expand ~ to home directory
            path = os.path.expanduser(dir_req.path)
            path_obj = Path(path)

            # Security: ensure path is absolute and exists
            if not path_obj.is_absolute():
                path_obj = Path.home() / path

            if not path_obj.exists() or not path_obj.is_dir():
                return JSONResponse(content={"error": "Directory not found"}, status_code=404)

            # List both directories and files (not hidden)
            directories = []
            files = []
            for item in sorted(path_obj.iterdir()):
                if item.name.startswith('.'):
                    continue
                if item.is_dir():
                    directories.append({
                        "name": item.name,
                        "path": str(item),
                        "type": "directory"
                    })
                elif item.is_file():
                    files.append({
                        "name": item.name,
                        "path": str(item),
                        "type": "file"
                    })

            response_data = {
                "directories": directories,
                "files": files,
                "current": str(path_obj),
                "is_root": path_obj == path_obj.parent
            }
            print(f"[DEBUG] Returning {len(directories)} dirs, {len(files)} files for {path_obj}")
            return JSONResponse(content=response_data)
        except Exception as e:
            return JSONResponse(content={"error": str(e)}, status_code=500)


@dev_router.post("/api/parent-directory")
async def parent_directory(
    req: Request,
    user: dict = Depends(get_current_user)
):
    """Get parent directory - proxy if Cloud Run, execute locally if Mac"""
    if IS_CLOUD_RUN:
        # Cloud Run: Proxy to Mac
        try:
            body = await req.body()
            auth_header = req.headers.get("Authorization", "")
            headers = {
                "Content-Type": "application/json",
                "Authorization": auth_header
            }
            async with httpx.AsyncClient(timeout=10.0, proxy=SOCKS5_PROXY) as client:
                response = await client.post(
                    f"{MAC_SERVER_URL}/dev/api/parent-directory",
                    content=body,
                    headers=headers
                )
                return JSONResponse(content=response.json(), status_code=response.status_code)
        except Exception as e:
            return JSONResponse(content={"error": str(e)}, status_code=500)
    else:
        # Mac: Execute locally
        class DirectoryRequest(BaseModel):
            path: str

        try:
            body = await req.json()
            dir_req = DirectoryRequest(**body)

            path = os.path.expanduser(dir_req.path)
            path_obj = Path(path)
            parent = path_obj.parent

            return JSONResponse(content={"parent": str(parent)})
        except Exception as e:
            return JSONResponse(content={"error": str(e)}, status_code=500)


@dev_router.websocket("/ws/terminal")
async def terminal_websocket(websocket: WebSocket, cwd: str = "~"):
    """
    WebSocket endpoint for terminal access - proxy if Cloud Run, execute if Mac
    """
    await websocket.accept()

    if IS_CLOUD_RUN:
        # Cloud Run: Proxy WebSocket to Mac via SOCKS5
        import websockets
        import aiohttp
        from aiohttp_socks import ProxyConnector

        try:
            # Create SOCKS5 connector
            connector = ProxyConnector.from_url(SOCKS5_PROXY)

            # Connect to Mac's WebSocket through SOCKS5
            async with aiohttp.ClientSession(connector=connector) as session:
                async with session.ws_connect(
                    f"ws://{MAC_SERVER_IP}:{MAC_SERVER_PORT}/dev/ws/terminal?cwd={cwd}",
                    timeout=aiohttp.ClientTimeout(total=3600)
                ) as ws:
                    # Bidirectional proxy
                    async def forward_to_mac():
                        """Forward messages from browser to Mac"""
                        try:
                            while True:
                                data = await websocket.receive_text()
                                await ws.send_str(data)
                        except Exception as e:
                            print(f"Forward to Mac error: {e}")

                    async def forward_to_browser():
                        """Forward messages from Mac to browser"""
                        try:
                            async for msg in ws:
                                if msg.type == aiohttp.WSMsgType.TEXT:
                                    await websocket.send_text(msg.data)
                                elif msg.type == aiohttp.WSMsgType.ERROR:
                                    break
                        except Exception as e:
                            print(f"Forward to browser error: {e}")

                    # Run both directions concurrently
                    await asyncio.gather(
                        forward_to_mac(),
                        forward_to_browser()
                    )
        except Exception as e:
            print(f"WebSocket proxy error: {e}")
            await websocket.close()
        return

    # Mac: Execute terminal locally
    # Generate session ID from connection
    session_id = f"session_{id(websocket)}"

    # Expand working directory
    working_dir = os.path.expanduser(cwd)

    try:
        # Create terminal session in the specified directory
        terminal = get_or_create_session(session_id, command="bash")

        # Change to working directory
        terminal.write(f"cd {working_dir}\n")
        await asyncio.sleep(0.3)

        # Send initial prompt
        await asyncio.sleep(0.5)
        initial_output = terminal.read(timeout=0.1)
        if initial_output:
            await websocket.send_text(json.dumps({"type": "output", "data": initial_output}))

        # Main loop - handle messages concurrently
        async def read_from_terminal():
            """Read from terminal and send to websocket"""
            while True:
                output = terminal.read(timeout=0.02)
                if output:
                    await websocket.send_text(json.dumps({"type": "output", "data": output}))
                await asyncio.sleep(0.02)  # 20ms polling interval for responsive but smooth updates

        async def handle_client_messages():
            """Handle messages from client"""
            while True:
                message = await websocket.receive_text()
                data = json.loads(message)

                if data["type"] == "input":
                    terminal.write(data["data"])
                elif data["type"] == "resize":
                    terminal.resize(data["rows"], data["cols"])

        # Run both tasks concurrently
        await asyncio.gather(
            read_from_terminal(),
            handle_client_messages()
        )

    except WebSocketDisconnect:
        close_session(session_id)
    except Exception as e:
        print(f"Terminal error: {e}")
        close_session(session_id)
        try:
            await websocket.close()
        except:
            pass
