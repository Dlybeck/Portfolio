from fastapi import APIRouter, Request
from fastapi.templating import Jinja2Templates
from fastapi.responses import FileResponse

templates = Jinja2Templates(directory="templates")
project_router = APIRouter()

@project_router.get("/projects/websites/digital_planner")
async def test(request: Request):
    return templates.TemplateResponse("pages/projects/websites/digital_planner.html", {"request": request})

@project_router.get("/projects/websites/this_website")
async def test(request: Request):
    return templates.TemplateResponse("pages/projects/websites/this_website.html", {"request": request})

@project_router.get("/projects/programs")
async def test(request: Request):
    return templates.TemplateResponse("pages/projects/programs.html", {"request": request})