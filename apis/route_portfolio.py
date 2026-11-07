"""Every public route renders the same notebook, opened at its own page."""

from __future__ import annotations

from pathlib import Path

from fastapi import APIRouter, Request
from fastapi.responses import FileResponse, PlainTextResponse, RedirectResponse, Response
from fastapi.templating import Jinja2Templates

from core import notebook, notebook_content
from core.images import img_size
from core.discovery import PERSON_SCHEMA, SITE_URL, metadata_for
from core.portfolio import DOCUMENTS, PortfolioDocument

templates = Jinja2Templates(directory=str(Path(__file__).parent.parent / "templates"))
templates.env.globals["img_size"] = img_size
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


@portfolio_router.get("/robots.txt", include_in_schema=False)
async def robots():
    return PlainTextResponse(f"User-agent: *\nAllow: /\n\nSitemap: {SITE_URL}/sitemap.xml\n")


@portfolio_router.get("/sitemap.xml", include_in_schema=False)
async def sitemap():
    """Every public address: the cover and each page route."""
    addresses = ["/", *(document.route for document in DOCUMENTS)]
    urls = "".join(f"<url><loc>{SITE_URL}{address}</loc></url>" for address in addresses)
    xml = f'<?xml version="1.0" encoding="UTF-8"?><urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">{urls}</urlset>'
    return Response(xml, media_type="application/xml")


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


# Pages taken out of the notebook keep a permanent address that leads somewhere useful.
RETIRED = {"/projects/websites/digital_planner": "/#projects"}


def retired_endpoint(target: str):
    async def retired():
        return RedirectResponse(target, status_code=301)

    return retired


for _route, _target in RETIRED.items():
    portfolio_router.add_api_route(_route, retired_endpoint(_target), methods=["GET"], include_in_schema=False)
