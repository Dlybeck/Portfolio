from fastapi import APIRouter, Request
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates
from core.dev_utils import require_auth, extract_token
from pathlib import Path

templates = Jinja2Templates(directory=str(Path(__file__).parent.parent / "templates"))

dev_pages_router = APIRouter()

def get_context(request: Request) -> dict:
    return {
        "request": request,
        "token": getattr(request.state, 'token', extract_token(request)),
        "workspace": "/home/dlybeck/Documents/portfolio"
    }

@dev_pages_router.get("/login", response_class=HTMLResponse)
async def login_page(request: Request):
    return templates.TemplateResponse("dev/login.html", {"request": request})

@dev_pages_router.get("/", response_class=HTMLResponse)
@require_auth
async def hub_page(request: Request):
    return templates.TemplateResponse("dev/hub.html", get_context(request))

@dev_pages_router.get("/vscode", response_class=HTMLResponse)
@require_auth
async def vscode_page(request: Request):
    return templates.TemplateResponse("dev/vscode.html", get_context(request))

@dev_pages_router.get("/terminal", response_class=HTMLResponse)
@require_auth
async def terminal_page(request: Request):
    return templates.TemplateResponse("dev/terminal.html", get_context(request))
