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
import json
import asyncio
import os
import httpx

# Mac server Tailscale IP (from your Tailscale network)
MAC_SERVER_IP = "100.84.184.84"
MAC_SERVER_PORT = 8080
MAC_SERVER_URL = f"http://{MAC_SERVER_IP}:{MAC_SERVER_PORT}"

# Check if services are available (Mac is reachable via Tailscale)
def is_mac_server_available():
    """Check if the Mac development server is reachable via Tailscale"""
    import socket
    try:
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sock.settimeout(2)
        result = sock.connect_ex((MAC_SERVER_IP, MAC_SERVER_PORT))
        sock.close()
        return result == 0
    except:
        return False

dev_router = APIRouter(prefix="/dev", tags=["Dev Dashboard"])

templates = Jinja2Templates(directory="templates")


class ChatRequest(BaseModel):
    message: str
    working_dir: str = None


class DirectoryRequest(BaseModel):
    path: str


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
    """Proxy chat requests to Mac server"""
    try:
        body = await req.body()
        async with httpx.AsyncClient(timeout=60.0) as client:
            response = await client.post(
                f"{MAC_SERVER_URL}/dev/api/chat",
                content=body,
                headers={"Content-Type": "application/json"}
            )
            return JSONResponse(content=response.json(), status_code=response.status_code)
    except Exception as e:
        return JSONResponse(content={"error": str(e)}, status_code=500)


@dev_router.post("/api/list-directory")
async def list_directory(
    req: Request,
    user: dict = Depends(get_current_user)
):
    """Proxy directory listing to Mac server"""
    try:
        body = await req.body()
        async with httpx.AsyncClient(timeout=10.0) as client:
            response = await client.post(
                f"{MAC_SERVER_URL}/dev/api/list-directory",
                content=body,
                headers={"Content-Type": "application/json"}
            )
            return JSONResponse(content=response.json(), status_code=response.status_code)
    except Exception as e:
        return JSONResponse(content={"error": str(e)}, status_code=500)


@dev_router.post("/api/parent-directory")
async def parent_directory(
    req: Request,
    user: dict = Depends(get_current_user)
):
    """Proxy parent directory request to Mac server"""
    try:
        body = await req.body()
        async with httpx.AsyncClient(timeout=10.0) as client:
            response = await client.post(
                f"{MAC_SERVER_URL}/dev/api/parent-directory",
                content=body,
                headers={"Content-Type": "application/json"}
            )
            return JSONResponse(content=response.json(), status_code=response.status_code)
    except Exception as e:
        return JSONResponse(content={"error": str(e)}, status_code=500)


@dev_router.websocket("/ws/terminal")
async def terminal_websocket(websocket: WebSocket, cwd: str = "~"):
    """
    WebSocket endpoint for terminal access
    """
    await websocket.accept()

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

        # Auto-launch claude
        terminal.write("claude\n")
        await asyncio.sleep(0.5)
        claude_output = terminal.read(timeout=0.5)
        if claude_output:
            await websocket.send_text(json.dumps({"type": "output", "data": claude_output}))

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
