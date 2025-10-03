"""
Dev Dashboard routes
Serves the dashboard interface and login page
"""

from fastapi import APIRouter, Depends, Request, WebSocket, WebSocketDisconnect
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates
from pydantic import BaseModel
from core.security import get_current_user
from services.claude_service import execute_claude_command
from services.terminal_service import get_or_create_session, close_session
import json
import asyncio
import os
from pathlib import Path

# Check if services are available (Mac is reachable)
def is_mac_server_available():
    """Check if the Mac development server is reachable"""
    import socket
    try:
        # Try to connect to local services
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sock.settimeout(2)
        result = sock.connect_ex(('127.0.0.1', 8080))
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
    request: ChatRequest,
    user: dict = Depends(get_current_user)
):
    """
    Chat endpoint that executes claude commands
    Requires authentication
    """
    result = await execute_claude_command(
        message=request.message,
        working_dir=request.working_dir
    )

    return result


@dev_router.post("/api/list-directory")
async def list_directory(
    request: DirectoryRequest,
    user: dict = Depends(get_current_user)
):
    """List directories in a given path"""
    try:
        # Expand ~ to home directory
        path = os.path.expanduser(request.path)
        path_obj = Path(path)

        # Security: ensure path is absolute and exists
        if not path_obj.is_absolute():
            path_obj = Path.home() / path

        if not path_obj.exists() or not path_obj.is_dir():
            return {"error": "Directory not found"}

        # List only directories (not hidden)
        directories = []
        for item in sorted(path_obj.iterdir()):
            if item.is_dir() and not item.name.startswith('.'):
                directories.append({
                    "name": item.name,
                    "path": str(item)
                })

        return {
            "directories": directories,
            "current": str(path_obj),
            "is_root": path_obj == path_obj.parent
        }

    except Exception as e:
        return {"error": str(e)}


@dev_router.post("/api/parent-directory")
async def parent_directory(
    request: DirectoryRequest,
    user: dict = Depends(get_current_user)
):
    """Get parent directory of current path"""
    try:
        path = os.path.expanduser(request.path)
        path_obj = Path(path)
        parent = path_obj.parent

        return {"parent": str(parent)}
    except Exception as e:
        return {"error": str(e)}


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
