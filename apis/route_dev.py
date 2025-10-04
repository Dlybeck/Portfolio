"""
Dev Dashboard routes
Serves the dashboard interface and login page
Proxies requests to Mac development server via Tailscale
"""

from fastapi import APIRouter, Depends, Request, WebSocket, WebSocketDisconnect
from fastapi.responses import HTMLResponse, JSONResponse, FileResponse, StreamingResponse
from fastapi.templating import Jinja2Templates
from pydantic import BaseModel
from core.security import get_current_user
from services.terminal_service import get_or_create_session, close_session
import json
import asyncio
import os
import httpx
from pathlib import Path
import mimetypes

# Mac server Tailscale IP (from your Tailscale network)
MAC_SERVER_IP = "100.84.184.84"
MAC_SERVER_PORT = 8080
MAC_SERVER_URL = f"http://{MAC_SERVER_IP}:{MAC_SERVER_PORT}"

# Tailscale SOCKS5 proxy (for userspace networking mode)
SOCKS5_PROXY = "socks5://localhost:1055"

# Detect if running in Cloud Run (proxy mode) or locally (direct mode)
IS_CLOUD_RUN = os.environ.get("K_SERVICE") is not None

# Cache for Mac server availability check
_mac_availability_cache = {
    "available": True,
    "last_check": 0,
    "cache_duration": 30  # Cache for 30 seconds
}

# Check if services are available (Mac is reachable via Tailscale SOCKS5)
async def is_mac_server_available():
    """Check if the Mac development server is reachable via Tailscale SOCKS5 proxy"""
    # If running locally on Mac, always return True
    if not IS_CLOUD_RUN:
        print(f"[DEBUG] Running on Mac locally - server available")
        return True

    # Check cache first
    import time
    current_time = time.time()
    if current_time - _mac_availability_cache["last_check"] < _mac_availability_cache["cache_duration"]:
        print(f"[DEBUG] Using cached Mac server availability: {_mac_availability_cache['available']}")
        return _mac_availability_cache["available"]

    # If in Cloud Run, check via SOCKS5 proxy with retry logic
    max_retries = 3
    for attempt in range(max_retries):
        try:
            print(f"[DEBUG] Checking Mac server (attempt {attempt + 1}/{max_retries}) at {MAC_SERVER_IP}:{MAC_SERVER_PORT} via SOCKS5")

            # Use async httpx client with SOCKS5 proxy and longer timeout
            async with httpx.AsyncClient(timeout=10.0, proxy=SOCKS5_PROXY) as client:
                response = await client.get(f"{MAC_SERVER_URL}/")
                is_available = response.status_code < 500
                print(f"[DEBUG] Mac server available: {is_available} (status: {response.status_code})")

                # Update cache
                _mac_availability_cache["available"] = is_available
                _mac_availability_cache["last_check"] = current_time
                return is_available
        except Exception as e:
            print(f"[DEBUG] Mac server check attempt {attempt + 1} failed: {e}")
            if attempt < max_retries - 1:
                # Wait a bit before retry (exponential backoff)
                await asyncio.sleep(0.5 * (2 ** attempt))
            else:
                # All retries failed, update cache to unavailable
                _mac_availability_cache["available"] = False
                _mac_availability_cache["last_check"] = current_time
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
    if not await is_mac_server_available():
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
    if not await is_mac_server_available():
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


@dev_router.get("/api/read-file")
async def read_file(
    path: str,
    req: Request,
    user: dict = Depends(get_current_user)
):
    """Read file and return its content - proxy if Cloud Run, execute locally if Mac"""
    if IS_CLOUD_RUN:
        # Cloud Run: Proxy to Mac
        try:
            # Get the original Authorization header from the request
            auth_header = req.headers.get("Authorization", "")
            headers = {"Authorization": auth_header}
            async with httpx.AsyncClient(timeout=30.0, proxy=SOCKS5_PROXY) as client:
                response = await client.get(
                    f"{MAC_SERVER_URL}/dev/api/read-file",
                    params={"path": path},
                    headers=headers
                )
                # Return file content with appropriate content type and length
                content_type = response.headers.get("content-type", "application/octet-stream")
                content_length = response.headers.get("content-length")

                response_headers = {"Content-Disposition": f'inline; filename="{Path(path).name}"'}
                if content_length:
                    response_headers["Content-Length"] = content_length

                return StreamingResponse(
                    iter([response.content]),
                    media_type=content_type,
                    headers=response_headers
                )
        except Exception as e:
            return JSONResponse(content={"error": str(e)}, status_code=500)
    else:
        # Mac: Execute locally
        try:
            file_path = os.path.expanduser(path)
            path_obj = Path(file_path)

            # Security: ensure file exists and is a file
            if not path_obj.exists() or not path_obj.is_file():
                return JSONResponse(content={"error": "File not found"}, status_code=404)

            # Guess content type
            content_type, _ = mimetypes.guess_type(file_path)
            if not content_type:
                content_type = "application/octet-stream"

            return FileResponse(
                file_path,
                media_type=content_type,
                headers={"Content-Disposition": f'inline; filename="{path_obj.name}"'}
            )
        except Exception as e:
            print(f"[ERROR] Failed to read file {path}: {e}")
            import traceback
            traceback.print_exc()
            return JSONResponse(content={"error": str(e)}, status_code=500)


@dev_router.websocket("/ws/terminal")
async def terminal_websocket(websocket: WebSocket, cwd: str = "~", session: str = None):
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
            ws_url = f"ws://{MAC_SERVER_IP}:{MAC_SERVER_PORT}/dev/ws/terminal?cwd={cwd}"
            if session:
                ws_url += f"&session={session}"

            async with aiohttp.ClientSession(connector=connector) as aio_session:
                async with aio_session.ws_connect(
                    ws_url,
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
    # Generate session ID from parameter or connection
    session_id = session if session else f"session_{id(websocket)}"

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
            """Read from terminal and batch send at 60fps for smooth rendering"""
            while True:
                # Collect all available output in a tight loop
                chunks = []
                deadline = asyncio.get_event_loop().time() + 0.016  # 16ms = ~60fps

                while asyncio.get_event_loop().time() < deadline:
                    output = terminal.read(timeout=0.001)
                    if output:
                        chunks.append(output)
                    else:
                        # No data available, break early
                        break

                # Send accumulated data in one message
                if chunks:
                    await websocket.send_text(json.dumps({"type": "output", "data": "".join(chunks)}))

                # Wait for next frame
                await asyncio.sleep(0.016)

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
