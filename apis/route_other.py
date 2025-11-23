from fastapi import APIRouter, Request
from fastapi.templating import Jinja2Templates
from fastapi.responses import FileResponse
from pathlib import Path

templates = Jinja2Templates(directory=str(Path(__file__).parent.parent / "templates"))
other_router = APIRouter()

@other_router.get("/jobs")
async def test(request: Request):
    return templates.TemplateResponse("pages/jobs.html", {"request": request})