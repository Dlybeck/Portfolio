from fastapi import APIRouter, Request
from fastapi.templating import Jinja2Templates
from fastapi.responses import FileResponse

templates = Jinja2Templates(directory="templates")
general_router = APIRouter()

@general_router.get("/")
async def test(request: Request):
    return templates.TemplateResponse("pages/home.html", {"request": request})

@general_router.get('/favicon.ico', include_in_schema=False)
async def favicon():
    return FileResponse('favicon.ico')