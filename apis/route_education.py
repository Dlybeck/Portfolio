from fastapi import APIRouter, Request
from fastapi.templating import Jinja2Templates
from fastapi.responses import FileResponse
from pathlib import Path

templates = Jinja2Templates(directory=str(Path(__file__).parent.parent / "templates"))
education_router = APIRouter()

@education_router.get("/education/college")
async def test(request: Request):
    return templates.TemplateResponse("pages/education/college.html", {"request": request})

@education_router.get("/education/early_education")
async def test(request: Request):
    return templates.TemplateResponse("pages/education/early_education.html", {"request": request})

@education_router.get("/education/agile_report")
async def agile_report(request: Request):
    return templates.TemplateResponse("pages/education/agile_report.html", {"request": request})