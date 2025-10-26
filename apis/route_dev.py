"""
Dev Dashboard routes
Serves the dashboard interface and login page
Proxies requests to Mac development server via Tailscale
"""

from fastapi import APIRouter, Depends, Request, WebSocket, WebSocketDisconnect
from fastapi.responses import HTMLResponse, JSONResponse, FileResponse, StreamingResponse
from fastapi.templating import Jinja2Templates
from pydantic import BaseModel
from core.security import get_current_user, get_session_user
from services.session_manager import get_or_create_persistent_session, close_persistent_session
from services.socks5_connection_manager import proxy_request
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

    # If in Cloud Run, check via SOCKS5 proxy with auto-retry
    try:
        print(f"[DEBUG] Checking Mac server at {MAC_SERVER_IP}:{MAC_SERVER_PORT} via connection manager")

        # Use connection manager with built-in retry logic
        response = await proxy_request("GET", f"{MAC_SERVER_URL}/")
        is_available = response.status_code < 500
        print(f"[DEBUG] Mac server available: {is_available} (status: {response.status_code})")

        # Update cache
        _mac_availability_cache["available"] = is_available
        _mac_availability_cache["last_check"] = current_time
        return is_available
    except Exception as e:
        print(f"[DEBUG] Mac server check failed after retries: {e}")
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

    # Test HTTP request through connection manager
    try:
        response = await proxy_request("GET", f"{MAC_SERVER_URL}/")
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


@dev_router.get("/debug/tailscale-health")
async def debug_tailscale_health(user: dict = Depends(get_current_user)):
    """🔒 Debug endpoint for Tailscale and SOCKS5 health - requires authentication"""
    import os
    from services.tailscale_health_monitor import get_health_monitor
    from services.socks5_connection_manager import get_connection_manager

    # Check if in Cloud Run
    is_cloud_run = os.environ.get("K_SERVICE") is not None

    if not is_cloud_run:
        return {
            "environment": "local",
            "message": "Tailscale health monitoring only runs in Cloud Run",
            "tailscale_ip": MAC_SERVER_IP,
        }

    # Get health status from monitor
    monitor = get_health_monitor()
    health_status = monitor.get_status()

    # Get SOCKS5 connection manager stats
    conn_manager = get_connection_manager()
    socks5_health = await conn_manager.check_socks5_health()
    conn_stats = conn_manager.get_stats()

    # Format timestamps
    import time
    from datetime import datetime

    def format_timestamp(ts):
        if ts:
            return datetime.fromtimestamp(ts).strftime("%Y-%m-%d %H:%M:%S")
        return None

    return {
        "environment": "cloud_run",
        "tailscale_monitor": {
            "healthy": health_status["healthy"],
            "status": health_status["status"],
            "consecutive_failures": health_status["consecutive_failures"],
            "last_check": format_timestamp(health_status["last_check_time"]),
            "stats": {
                "total_checks": health_status["stats"]["total_checks"],
                "failures": health_status["stats"]["failures"],
                "recoveries": health_status["stats"]["recoveries"],
                "last_failure": format_timestamp(health_status["stats"].get("last_failure_time")),
                "last_recovery": format_timestamp(health_status["stats"].get("last_recovery_time")),
            }
        },
        "socks5_proxy": socks5_health,
        "connection_manager": {
            "client_active": conn_stats["client_active"],
            "client_age_seconds": round(conn_stats["client_age_seconds"], 1),
            "max_age_seconds": conn_stats["max_age_seconds"],
            "requests": {
                "total": conn_stats["stats"]["total_requests"],
                "failed": conn_stats["stats"]["failed_requests"],
                "retried": conn_stats["stats"]["retried_requests"],
                "last_error": conn_stats["stats"]["last_error"],
                "last_error_time": format_timestamp(conn_stats["stats"]["last_error_time"]),
            }
        },
        "target": {
            "mac_ip": MAC_SERVER_IP,
            "mac_port": MAC_SERVER_PORT,
        }
    }


@dev_router.get("/login", response_class=HTMLResponse)
async def login_page(request: Request):
    """Serve the login page (works in both Cloud Run and local environments)"""
    return templates.TemplateResponse("dev/login.html", {"request": request})


@dev_router.get("", response_class=HTMLResponse)
async def dev_dashboard_redirect(request: Request):
    """
    Redirect /dev to /dev/terminal (VS Code)
    Works in both Cloud Run (proxies to Mac) and local environments
    """
    from fastapi.responses import RedirectResponse
    return RedirectResponse(url="/dev/terminal", status_code=302)


@dev_router.get("/terminal", response_class=HTMLResponse)
async def terminal_dashboard(request: Request):
    """
    VS Code dashboard (replaces old terminal dashboard)
    Extracts token from cookie/header/query and passes it to code-server
    """
    from fastapi.responses import RedirectResponse

    # Extract token from multiple sources (same logic as get_session_user)
    token = None

    # Try session cookie first
    token = request.cookies.get("session_token")

    # Try Authorization header
    if not token:
        auth_header = request.headers.get("Authorization", "")
        if auth_header.startswith("Bearer "):
            token = auth_header.replace("Bearer ", "")

    # Try query parameter
    if not token:
        token = request.query_params.get("tkn")

    if not token:
        # No authentication found, redirect to login
        return RedirectResponse(url="/dev/login", status_code=302)

    # Validate token
    try:
        from core.security import verify_token
        payload = verify_token(token)
        if payload.get("type") != "access":
            return RedirectResponse(url="/dev/login", status_code=302)
    except:
        return RedirectResponse(url="/dev/login", status_code=302)

    # Redirect to code-server proxy with token in query parameter
    # This allows the WebSocket connections to read the token
    return RedirectResponse(url=f"/dev/vscode/?tkn={token}", status_code=302)


@dev_router.post("/api/chat")
async def chat_with_claude(
    req: Request,
    user: dict = Depends(get_current_user)
):
    """Proxy chat requests to Mac server via connection manager with auto-retry"""
    try:
        body = await req.body()
        # Forward the Authorization header from the original request
        auth_header = req.headers.get("Authorization", "")
        headers = {
            "Content-Type": "application/json",
            "Authorization": auth_header
        }
        response = await proxy_request(
            "POST",
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
        # Cloud Run: Proxy to Mac via connection manager
        try:
            body = await req.body()
            auth_header = req.headers.get("Authorization", "")
            headers = {
                "Content-Type": "application/json",
                "Authorization": auth_header
            }
            response = await proxy_request(
                "POST",
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
        # Cloud Run: Proxy to Mac via connection manager
        try:
            body = await req.body()
            auth_header = req.headers.get("Authorization", "")
            headers = {
                "Content-Type": "application/json",
                "Authorization": auth_header
            }
            response = await proxy_request(
                "POST",
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
        # Cloud Run: Proxy to Mac via connection manager
        try:
            # Get the original Authorization header from the request
            auth_header = req.headers.get("Authorization", "")
            headers = {"Authorization": auth_header}
            response = await proxy_request(
                "GET",
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


@dev_router.post("/api/save-file")
async def save_file(
    req: Request,
    user: dict = Depends(get_current_user)
):
    """
    Save file content - proxy if Cloud Run, execute locally if Mac
    Requires authentication (JWT token)
    """
    if IS_CLOUD_RUN:
        # Cloud Run: Proxy to Mac via connection manager
        try:
            body = await req.body()
            auth_header = req.headers.get("Authorization", "")
            headers = {
                "Content-Type": "application/json",
                "Authorization": auth_header
            }
            response = await proxy_request(
                "POST",
                f"{MAC_SERVER_URL}/dev/api/save-file",
                content=body,
                headers=headers
            )
            return JSONResponse(content=response.json(), status_code=response.status_code)
        except Exception as e:
            return JSONResponse(content={"error": str(e)}, status_code=500)
    else:
        # Mac: Execute locally
        class SaveFileRequest(BaseModel):
            path: str
            content: str

        try:
            body = await req.json()
            save_req = SaveFileRequest(**body)

            # Security validations
            file_path = save_req.path

            # Validate file path is absolute
            if not os.path.isabs(file_path):
                return JSONResponse(
                    content={"error": "File path must be absolute"},
                    status_code=400
                )

            # Prevent directory traversal attacks
            if ".." in file_path:
                return JSONResponse(
                    content={"error": "Invalid file path (directory traversal not allowed)"},
                    status_code=400
                )

            # Expand ~ to home directory
            file_path = os.path.expanduser(file_path)
            path_obj = Path(file_path)

            # Check file exists
            if not path_obj.exists():
                return JSONResponse(
                    content={"error": "File not found"},
                    status_code=404
                )

            # Check it's a file (not a directory)
            if not path_obj.is_file():
                return JSONResponse(
                    content={"error": "Path is not a file"},
                    status_code=400
                )

            # Check file is writable
            if not os.access(file_path, os.W_OK):
                return JSONResponse(
                    content={"error": "Permission denied - file is not writable"},
                    status_code=403
                )

            # Write content to file with UTF-8 encoding
            # Preserve line endings (don't convert)
            bytes_written = path_obj.write_text(save_req.content, encoding='utf-8')

            print(f"[DEBUG] Saved {bytes_written} bytes to {file_path}")

            return JSONResponse(content={
                "success": True,
                "message": f"File saved successfully",
                "bytes_written": bytes_written,
                "path": str(path_obj)
            })

        except PermissionError as e:
            return JSONResponse(
                content={"error": f"Permission denied: {str(e)}"},
                status_code=403
            )
        except Exception as e:
            print(f"[ERROR] Failed to save file: {e}")
            import traceback
            traceback.print_exc()
            return JSONResponse(
                content={"error": str(e)},
                status_code=500
            )


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
async def terminal_websocket(websocket: WebSocket, cwd: str = "~", session: str = None, token: str = None, mode: str = None):
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

            # Connect to Mac's WebSocket through SOCKS5 (forward auth token and mode)
            ws_url = f"ws://{MAC_SERVER_IP}:{MAC_SERVER_PORT}/dev/ws/terminal?cwd={cwd}&token={token}"
            if session:
                ws_url += f"&session={session}"
            if mode:
                ws_url += f"&mode={mode}"

            async with aiohttp.ClientSession(connector=connector) as aio_session:
                async with aio_session.ws_connect(
                    ws_url,
                    timeout=aiohttp.ClientTimeout(total=43200)  # 12 hours for long dev sessions
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
    # FastAPI already injects the 'session' query parameter
    if session:
        # Use custom session ID from client (for forced new sessions)
        session_id = session
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

        # Set client's preferred mode if this is a new session or if mode is specified
        # Validate mode parameter
        if mode and mode in ['fancy', 'simple']:
            # If this is a new session (claude_started=False), set the preferred mode
            if not persistent_session.claude_started:
                persistent_session.term_mode = mode
                print(f"[DEBUG] Setting initial term mode to '{mode}' for new session '{session_id}'")

        # Add this client/device to the session
        persistent_session.add_client(websocket)

        # Send buffered history to new client (catch up on what happened)
        history = persistent_session.get_buffered_history()
        if history:
            await websocket.send_text(json.dumps({"type": "output", "data": history}))

        # Start broadcast loop if not already running (only runs once per session)
        await persistent_session.start_broadcast_loop()

        # Auto-start Claude ONCE per session (not once per client)
        # Send current term mode to new client
        await websocket.send_text(json.dumps({
            "type": "current_term_mode",
            "mode": persistent_session.term_mode
        }))

        # Skip auto-start for terminal tab sessions (they should be plain bash)
        # Use lock to prevent race conditions when multiple clients connect simultaneously
        is_terminal_tab = session_id.startswith('terminal_tab_')
        if not is_terminal_tab:
            async with persistent_session.claude_start_lock:
                if not persistent_session.claude_started:
                    print(f"[DEBUG] Auto-starting Claude in '{persistent_session.term_mode}' mode...")
                    # Wait for terminal to fully initialize
                    await asyncio.sleep(1.5)
                    # Set TERM based on mode
                    if persistent_session.term_mode == 'simple':
                        persistent_session.write("export TERM=dumb\n")
                    else:
                        persistent_session.write("export TERM=xterm-256color\n")
                    # Source shell profile to load PATH, then start claude
                    # Try .zshrc first (macOS default), fallback to .bashrc
                    persistent_session.write("source ~/.zshrc 2>/dev/null || source ~/.bashrc 2>/dev/null; exec claude\n")
                    persistent_session.claude_started = True
                    print(f"[DEBUG] Claude started with TERM={persistent_session.term_mode}")
        else:
            print("[DEBUG] Terminal tab session - skipping Claude auto-start")

        # Handle messages from this specific client
        async def handle_client_messages():
            """Handle messages from this client"""
            nonlocal last_pong_time
            while True:
                message = await websocket.receive_text()
                data = json.loads(message)

                if data["type"] == "input":
                    # Write to terminal (will be broadcast to all clients)
                    persistent_session.write(data["data"])
                elif data["type"] == "resize":
                    # Resize terminal (affects all clients)
                    persistent_session.resize(data["rows"], data["cols"])
                elif data["type"] == "ping":
                    # Client sent ping - respond with pong
                    await websocket.send_text(json.dumps({"type": "pong"}))
                    # print(f"[WebSocket] Received ping, sent pong")
                elif data["type"] == "pong":
                    # Client responded to ping - update timestamp
                    last_pong_time = asyncio.get_event_loop().time()
                    # print(f"[WebSocket] Received pong from client")
                elif data["type"] == "toggle_term_mode":
                    # Toggle terminal mode and restart Claude
                    new_mode = data.get("mode", "fancy")
                    print(f"[DEBUG] Toggling term mode to '{new_mode}' for session '{session_id}'")

                    # Update session mode
                    persistent_session.set_term_mode(new_mode)

                    # Broadcast mode change to all connected clients
                    mode_change_msg = json.dumps({
                        "type": "term_mode_changed",
                        "mode": new_mode
                    })
                    disconnected = set()
                    for client in persistent_session.connected_clients:
                        try:
                            await client.send_text(mode_change_msg)
                        except Exception as e:
                            print(f"[DEBUG] Error sending mode change to client: {e}")
                            disconnected.add(client)

                    # Clean up disconnected clients
                    for client in disconnected:
                        persistent_session.remove_client(client)

                    # Close session to restart with new TERM
                    from services.session_manager import close_persistent_session
                    close_persistent_session(session_id)

                    # Client will auto-reconnect and new session will use new TERM
                    break

        # Track last pong time for timeout detection
        last_pong_time = asyncio.get_event_loop().time()
        ping_timeout = 10  # seconds - close if no pong response

        async def send_keepalive_pings():
            """Send ping every 15 seconds to keep connection alive"""
            nonlocal last_pong_time
            try:
                while True:
                    await asyncio.sleep(15)  # Reduced from 30s for mobile

                    # Check if client responded to last ping
                    time_since_pong = asyncio.get_event_loop().time() - last_pong_time
                    if time_since_pong > ping_timeout:
                        print(f"[WebSocket] Client timeout - no pong for {time_since_pong:.1f}s. Closing connection.")
                        break

                    try:
                        await websocket.send_text(json.dumps({"type": "ping"}))
                        print(f"[WebSocket] Sent ping (last pong: {time_since_pong:.1f}s ago)")
                    except Exception as e:
                        print(f"[WebSocket] Ping failed: {e}")
                        break
            except asyncio.CancelledError:
                pass

        # Run both client message handler and ping sender
        await asyncio.gather(
            handle_client_messages(),
            send_keepalive_pings()
        )

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


# ==================== CODE-SERVER PROXY ROUTES ====================

from services.code_server_proxy import get_proxy


@dev_router.get("/vscode/{path:path}")
@dev_router.post("/vscode/{path:path}")
@dev_router.put("/vscode/{path:path}")
@dev_router.delete("/vscode/{path:path}")
@dev_router.patch("/vscode/{path:path}")
async def vscode_proxy(
    path: str,
    request: Request,
    user: dict = Depends(get_session_user)
):
    """
    🔒 Authenticated proxy to code-server

    All HTTP methods supported (GET, POST, PUT, DELETE, PATCH)
    Requires session cookie authentication
    """
    proxy = get_proxy()
    return await proxy.proxy_request(request, path)


@dev_router.websocket("/vscode/{path:path}")
async def vscode_websocket_proxy(
    websocket: WebSocket,
    path: str,
    token: str = None,
    tkn: str = None
):
    """
    🔒 Authenticated WebSocket proxy to code-server

    This route handles ALL WebSocket connections to code-server.
    FastAPI will route WebSocket upgrade requests here instead of the HTTP GET route.

    Required for:
    - Terminal connections
    - Live file updates
    - Extension communication

    Authentication via (checked in order):
    1. Query parameter 'tkn' (from page URL)
    2. Query parameter 'token' (legacy)
    3. Session cookie (same-domain only)
    4. Extract from Referer header (if page was loaded with tkn parameter)
    """
    # Try to get token from multiple sources
    auth_token = None

    # Try query parameter 'tkn' first (passed from page URL)
    if tkn:
        auth_token = tkn
        print(f"[WS Auth] Using 'tkn' query parameter for authentication")

    # Try query parameter 'token' (legacy)
    elif token:
        auth_token = token
        print(f"[WS Auth] Using 'token' query parameter for authentication")

    # Try session cookie (same-domain only)
    elif websocket.cookies.get("session_token"):
        auth_token = websocket.cookies.get("session_token")
        print(f"[WS Auth] Using session cookie for authentication")

    # Try to extract from Referer header as last resort
    else:
        referer = websocket.headers.get("referer", "")
        if "tkn=" in referer:
            # Extract token from referer URL
            import urllib.parse
            parsed = urllib.parse.urlparse(referer)
            params = urllib.parse.parse_qs(parsed.query)
            if "tkn" in params and params["tkn"]:
                auth_token = params["tkn"][0]
                print(f"[WS Auth] Extracted token from Referer header")

    if not auth_token:
        print(f"[WS Auth] No authentication token found (cookie, query, or referer)")
        await websocket.close(code=1008, reason="Missing authentication token")
        return

    try:
        from core.security import verify_token
        payload = verify_token(auth_token)
        if payload.get("type") != "access":
            await websocket.close(code=1008, reason="Invalid token type")
            return
        print(f"[WS Auth] Authenticated user: {payload.get('sub')}")
    except Exception as e:
        print(f"[WS Auth] Authentication failed: {e}")
        await websocket.close(code=1008, reason="Invalid authentication token")
        return

    # Accept connection
    await websocket.accept()

    # Proxy to code-server
    proxy = get_proxy()
    await proxy.proxy_websocket(websocket, path)
