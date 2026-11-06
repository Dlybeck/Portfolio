"""Every public route renders the same notebook, opened at its own page."""

from __future__ import annotations

from pathlib import Path

from fastapi import APIRouter, Request
from fastapi.responses import FileResponse
from fastapi.templating import Jinja2Templates

from core import notebook, notebook_content
from core.discovery import PERSON_SCHEMA, metadata_for
from core.portfolio import DOCUMENTS, PortfolioDocument

templates = Jinja2Templates(directory=str(Path(__file__).parent.parent / "templates"))
portfolio_router = APIRouter()


def render_notebook(request: Request, document: PortfolioDocument | None = None):
    context = {
        "metadata": metadata_for(document),
        "person_schema": PERSON_SCHEMA,
        "nb": notebook,
        "content": notebook_content,
        "nb_data": notebook.client_data(),
    }
    return templates.TemplateResponse(request, "notebook/index.html", context)


@portfolio_router.get("/")
async def home(request: Request):
    return render_notebook(request)


@portfolio_router.get("/favicon.ico", include_in_schema=False)
async def favicon():
    return FileResponse("favicon.ico")


def destination_endpoint(document: PortfolioDocument):
    async def destination(request: Request):
        return render_notebook(request, document)

    return destination


for _document in DOCUMENTS:
    portfolio_router.add_api_route(
        _document.route,
        destination_endpoint(_document),
        methods=["GET"],
        name=f"destination_{_document.route.strip('/').replace('/', '_')}",
    )
