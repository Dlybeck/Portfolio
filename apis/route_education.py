from fastapi import APIRouter, Request
from fastapi.templating import Jinja2Templates
from fastapi.responses import FileResponse

templates = Jinja2Templates(directory="templates")
education_router = APIRouter()

@education_router.get("/education/college")
async def test(request: Request):
    return templates.TemplateResponse("pages/education/college.html", {"request": request})

@education_router.get("/education/early_education")
async def test(request: Request):
    return templates.TemplateResponse("pages/education/early_education.html", {"request": request})