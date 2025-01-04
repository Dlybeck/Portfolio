from fastapi import APIRouter, Request
from fastapi.templating import Jinja2Templates
from fastapi.responses import FileResponse

templates = Jinja2Templates(directory="templates")
hobby_router = APIRouter()