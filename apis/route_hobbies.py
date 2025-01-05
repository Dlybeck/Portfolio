from fastapi import APIRouter, Request
from fastapi.templating import Jinja2Templates
from fastapi.responses import FileResponse

templates = Jinja2Templates(directory="templates")
hobby_router = APIRouter()

@hobby_router.get("/hobbies/tennis")
async def test(request: Request):
    return templates.TemplateResponse("pages/hobbies/tennis.html", {"request": request})

@hobby_router.get("/hobbies/gaming")
async def test(request: Request):
    return templates.TemplateResponse("pages/hobbies/gaming.html", {"request": request})

@hobby_router.get("/hobbies/3d_printing/puzzles")
async def test(request: Request):
    return templates.TemplateResponse("pages/hobbies/3d_printing/puzzles.html", {"request": request})

@hobby_router.get("/hobbies/3d_printing/other_models")
async def test(request: Request):
    return templates.TemplateResponse("pages/hobbies/3d_printing/other_models.html", {"request": request})