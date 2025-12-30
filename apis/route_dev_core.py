"""
Dev Dashboard Core Routes
"""

from fastapi import APIRouter, Depends, Request
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.templating import Jinja2Templates
from core.security import get_current_user
from core.config import settings
from pathlib import Path

templates = Jinja2Templates(directory=str(Path(__file__).parent.parent / "templates"))

dev_core_router = APIRouter(prefix="/dev", tags=["Dev Dashboard - Core"])


@dev_core_router.get("/login", response_class=HTMLResponse)
async def login_page(request: Request):
    """Serve the login page (works in both Cloud Run and local environments)"""
    return templates.TemplateResponse("dev/login.html", {"request": request})


@dev_core_router.get("", response_class=HTMLResponse)
async def dev_hub(request: Request):
    """
    Dev Hub - central dashboard for choosing development tools
    """
    # Extract token for the template
    token = request.cookies.get("session_token") or request.query_params.get("tkn")

    if not token:
        # Try Authorization header
        auth = request.headers.get("Authorization", "")
        if auth.startswith("Bearer "):
            token = auth.replace("Bearer ", "")

    if not token:
        return RedirectResponse(url="/dev/login", status_code=302)

    return templates.TemplateResponse("dev/hub.html", {"request": request, "token": token})


@dev_core_router.get("/speckit", response_class=HTMLResponse)
async def speckit_dashboard(request: Request):
    """
    Serve the Speckit Dashboard.
    """
    # Extract token for the template
    token = request.cookies.get("session_token") or request.query_params.get("tkn")

    if not token:
        # Try Authorization header
        auth = request.headers.get("Authorization", "")
        if auth.startswith("Bearer "):
            token = auth.replace("Bearer ", "")

    if not token:
        return RedirectResponse(url="/dev/login", status_code=302)

    return templates.TemplateResponse("dev/speckit_dashboard.html", {"request": request, "token": token})


@dev_core_router.get("/agentbridge", response_class=HTMLResponse)
async def agentbridge_dashboard(request: Request):
    """
    Serve the AgentBridge Dashboard.
    """
    # Extract token for the template
    token = request.cookies.get("session_token") or request.query_params.get("tkn")

    if not token:
        # Try Authorization header
        auth = request.headers.get("Authorization", "")
        if auth.startswith("Bearer "):
            token = auth.replace("Bearer ", "")

    if not token:
        return RedirectResponse(url="/dev/login", status_code=302)

    return templates.TemplateResponse("dev/agentbridge_dashboard.html", {"request": request, "token": token})


@dev_core_router.get("/agentbridge/debug", response_class=HTMLResponse)
async def agentbridge_debug():
    """
    Serve the AgentBridge debug tool (no auth required for debugging)
    """
    import os
    debug_file = Path(__file__).parent.parent / "test_file_browser.html"
    if os.path.exists(debug_file):
        with open(debug_file, 'r') as f:
            return HTMLResponse(content=f.read())
    return HTMLResponse(content="<h1>Debug file not found</h1>", status_code=404)
