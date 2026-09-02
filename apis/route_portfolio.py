"""Public Board destinations and private Document rendering routes."""

from __future__ import annotations

from pathlib import Path

from fastapi import APIRouter, HTTPException, Request
from fastapi.responses import FileResponse, JSONResponse
from fastapi.templating import Jinja2Templates

from core.config import settings
from core.discovery import PERSON_SCHEMA, metadata_for
from core.portfolio import DOCUMENTS, PortfolioDocument, document_for_route, portfolio_state
from core.theme_packs import ThemePackRegistry
from core.themes import theme_context


templates = Jinja2Templates(directory=str(Path(__file__).parent.parent / "templates"))
portfolio_router = APIRouter()


@portfolio_router.get("/_theme-packs/{pack_id}.json", include_in_schema=False)
async def theme_pack_payload(pack_id: str):
    """Serve one fully validated pack to the development Theme Engine."""
    if not settings.THEME_LAB_ENABLED:
        raise HTTPException(status_code=404, detail="Theme Laboratory is disabled")
    registry = ThemePackRegistry.discover()
    pack = next(
        (
            candidate
            for candidate in registry.packs
            if candidate.id == pack_id and candidate.selection.enabled
        ),
        None,
    )
    if pack is None:
        raise HTTPException(status_code=404, detail="Unknown or invalid Theme Pack")
    return JSONResponse(pack.client_payload())


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
