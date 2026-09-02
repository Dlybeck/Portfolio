"""Public Board destinations and private Document rendering routes."""

from __future__ import annotations

from pathlib import Path

from fastapi import APIRouter, HTTPException, Request
from fastapi.responses import FileResponse
from fastapi.templating import Jinja2Templates

from core.config import settings
from core.discovery import PERSON_SCHEMA, metadata_for
from core.portfolio import DOCUMENTS, PortfolioDocument, document_for_route, portfolio_state
from core.themes import theme_context


templates = Jinja2Templates(directory=str(Path(__file__).parent.parent / "templates"))
portfolio_router = APIRouter()


def render_board(request: Request, document: PortfolioDocument | None = None):
    return templates.TemplateResponse(
        request,
        "pages/home.html",
        {
            "portfolio_state": portfolio_state(document),
            "document": document,
            "metadata": metadata_for(document),
            "person_schema": PERSON_SCHEMA,
            **theme_context(request, settings.THEME_LAB_ENABLED),
        },
    )


@portfolio_router.get("/")
async def home(request: Request):
    return render_board(request)


@portfolio_router.get("/_documents/{document_path:path}", include_in_schema=False)
async def embedded_document(request: Request, document_path: str):
    document = document_for_route(document_path)
    if document is None:
        raise HTTPException(status_code=404, detail="Unknown portfolio document")
    return templates.TemplateResponse(
        request,
        document.template,
        {
            "metadata": metadata_for(document),
            "internal_document": True,
            **theme_context(request, settings.THEME_LAB_ENABLED),
        },
    )


@portfolio_router.get("/favicon.ico", include_in_schema=False)
async def favicon():
    return FileResponse("favicon.ico")


def destination_endpoint(document: PortfolioDocument):
    async def destination(request: Request):
        return render_board(request, document)

    return destination


for _document in DOCUMENTS:
    portfolio_router.add_api_route(
        _document.route,
        destination_endpoint(_document),
        methods=["GET"],
        name=f"destination_{_document.route.strip('/').replace('/', '_')}",
    )
