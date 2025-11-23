from fastapi import APIRouter, Request
from fastapi.templating import Jinja2Templates
from fastapi.responses import FileResponse
from pathlib import Path

templates = Jinja2Templates(directory=str(Path(__file__).parent.parent / "templates"))
project_router = APIRouter()

@project_router.get("/projects/websites/digital_planner")
async def test(request: Request):
    return templates.TemplateResponse("pages/projects/websites/digital_planner.html", {"request": request})

@project_router.get("/projects/websites/scribblescan")
async def test(request: Request):
    return templates.TemplateResponse("pages/projects/websites/scribblescan.html", {"request": request})

@project_router.get("/projects/websites/this_website")
async def test(request: Request):
    return templates.TemplateResponse("pages/projects/websites/this_website.html", {"request": request})

@project_router.get("/projects/websites/this_website/v1")
async def test(request: Request):
    return templates.TemplateResponse("pages/projects/websites/this_website/v1.html", {"request": request})

@project_router.get("/projects/websites/this_website/v2")
async def test(request: Request):
    return templates.TemplateResponse("pages/projects/websites/this_website/v2.html", {"request": request})

@project_router.get("/projects/programs")
async def test(request: Request):
    return templates.TemplateResponse("pages/projects/programs.html", {"request": request})

@project_router.get("/projects/nba_predictions")
async def test(request: Request):
    return templates.TemplateResponse("pages/projects/nba_predictions.html", {"request": request})
    