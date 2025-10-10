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
from services.session_manager import get_or_create_persistent_session, close_persistent_session
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
async def debug_connectivity(user: dict = Depends(get_current_user)):
    """🔒 Debug endpoint to test Mac connectivity - requires authentication"""
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

    # Test is_mac_server_available function (FIXED: added await)
    results["is_available"] = await is_mac_server_available()

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
    token: str = None
):
    """
    Read file and return its content - proxy if Cloud Run, execute locally if Mac
    Supports both header-based auth and query parameter token (for window.open)
    """
    # Authenticate either via query token or Authorization header
    authenticated = False

    if token:
        # Query parameter token (for window.open)
        try:
            from core.security import verify_token
            payload = verify_token(token)
            if payload.get("type") == "access":
                authenticated = True
                print(f"[DEBUG] Query token authenticated for user: {payload.get('sub')}")
        except Exception as e:
            print(f"[DEBUG] Query token authentication failed: {e}")

    if not authenticated:
        # Try Authorization header
        auth_header = req.headers.get("Authorization", "")
        if auth_header.startswith("Bearer "):
            header_token = auth_header.replace("Bearer ", "")
            try:
                from core.security import verify_token
                payload = verify_token(header_token)
                if payload.get("type") == "access":
                    authenticated = True
                    print(f"[DEBUG] Header token authenticated for user: {payload.get('sub')}")
            except Exception as e:
                print(f"[DEBUG] Header token authentication failed: {e}")

        if not authenticated:
            return JSONResponse(content={"error": "Unauthorized"}, status_code=401)

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


@dev_router.get("/debug/sessions")
async def debug_sessions(user: dict = Depends(get_current_user)):
    """🔒 Debug endpoint to inspect active sessions - requires authentication"""
    from services.session_manager import get_all_sessions

    sessions = get_all_sessions()

    return JSONResponse(content={
        "total_sessions": len(sessions),
        "sessions": sessions,
        "timestamp": __import__('datetime').datetime.now().isoformat()
    })


@dev_router.post("/api/kill-session")
async def kill_session(
    req: Request,
    user: dict = Depends(get_current_user)
):
    """🔒 Force kill a terminal session - requires authentication"""
    # Only works on Mac (local execution)
    if IS_CLOUD_RUN:
        return JSONResponse(
            content={"error": "Kill session only works on local Mac"},
            status_code=400
        )

    try:
        body = await req.json()
        session_id = body.get("session_id", "user_main_session")

        print(f"[DEBUG] Force killing session '{session_id}'")
        close_persistent_session(session_id)

        return JSONResponse(content={"success": True, "session_id": session_id})
    except Exception as e:
        print(f"[ERROR] Failed to kill session: {e}")
        return JSONResponse(content={"error": str(e)}, status_code=500)


@dev_router.websocket("/ws/terminal")
async def terminal_websocket(websocket: WebSocket, cwd: str = "~", session: str = None, token: str = None):
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
        print(f"[DEBUG] WebSocket authenticated for user: {payload.get('sub')}")
    except Exception as e:
        print(f"[DEBUG] WebSocket authentication failed: {e}")
        await websocket.close(code=1008, reason="Invalid authentication token")
        return

    await websocket.accept()

    if IS_CLOUD_RUN:
        # Cloud Run: Proxy WebSocket to Mac via SOCKS5
        import websockets
        import aiohttp
        from aiohttp_socks import ProxyConnector

        try:
            # Create SOCKS5 connector
            connector = ProxyConnector.from_url(SOCKS5_PROXY)

            # Connect to Mac's WebSocket through SOCKS5 (forward auth token)
            ws_url = f"ws://{MAC_SERVER_IP}:{MAC_SERVER_PORT}/dev/ws/terminal?cwd={cwd}&token={token}"
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

    # Mac: Execute terminal locally with persistent session
    # Check if client requested a new session (e.g., after kill button)
    session_param = request.query_params.get('session', None)

    if session_param:
        # Use custom session ID from client (for forced new sessions)
        session_id = session_param
    else:
        # Default: One main session for the user
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

        # Add this client/device to the session
        persistent_session.add_client(websocket)

        # Send buffered history to new client (catch up on what happened)
        history = persistent_session.get_buffered_history()
        if history:
            await websocket.send_text(json.dumps({"type": "output", "data": history}))

        # Start broadcast loop if not already running (only runs once per session)
        await persistent_session.start_broadcast_loop()

        # Auto-start Claude ONCE per session (not once per client)
        # Skip auto-start for terminal tab sessions (they should be plain bash)
        # Use lock to prevent race conditions when multiple clients connect simultaneously
        is_terminal_tab = session_id.startswith('terminal_tab_')
        if not is_terminal_tab:
            async with persistent_session.claude_start_lock:
                if not persistent_session.claude_started:
                    print("[DEBUG] Auto-starting Claude for this session...")
                    # Wait for terminal to fully initialize
                    await asyncio.sleep(1.5)
                    # Source shell profile to load PATH, then start claude
                    # Try .zshrc first (macOS default), fallback to .bashrc
                    persistent_session.write("source ~/.zshrc 2>/dev/null || source ~/.bashrc 2>/dev/null; exec claude\n")
                    persistent_session.claude_started = True
                    print("[DEBUG] Claude command sent with shell profile loaded")
        else:
            print("[DEBUG] Terminal tab session - skipping Claude auto-start")

        # Handle messages from this specific client
        async def handle_client_messages():
            """Handle messages from this client"""
            while True:
                message = await websocket.receive_text()
                data = json.loads(message)

                if data["type"] == "input":
                    # Write to terminal (will be broadcast to all clients)
                    persistent_session.write(data["data"])
                elif data["type"] == "resize":
                    # Resize terminal (affects all clients)
                    persistent_session.resize(data["rows"], data["cols"])

        # Only run the client message handler (broadcast loop runs separately)
        await handle_client_messages()

    except WebSocketDisconnect:
        # Client disconnected - remove from session
        persistent_session.remove_client(websocket)
        print(f"[DEBUG] Client disconnected, {len(persistent_session.connected_clients)} clients remaining")

        # CRITICAL: Close session if no clients left to prevent PTY leak
        if len(persistent_session.connected_clients) == 0:
            print(f"[DEBUG] No clients left, closing session '{session_id}' to prevent PTY leak")
            close_persistent_session(session_id)

    except Exception as e:
        print(f"Terminal error: {e}")
        # Remove client
        persistent_session.remove_client(websocket)

        # CRITICAL: Close session if no clients left to prevent PTY leak
        if len(persistent_session.connected_clients) == 0:
            print(f"[DEBUG] No clients left after error, closing session '{session_id}' to prevent PTY leak")
            close_persistent_session(session_id)

        try:
            await websocket.close()
        except:
            pass
