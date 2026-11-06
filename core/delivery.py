"""How the site's files are sent: compressed where that helps, and cached sensibly.

Pages are small text, so they are compressed. Pictures, fonts, video and PDFs already are, so they are
sent as they are (video also needs byte ranges). Fonts, pictures, models and the 3D viewer almost never
change, so browsers may keep them for a week; stylesheets, scripts and pages are always revalidated
(a cheap "not modified" answer), so a change shows up at once.
"""

from __future__ import annotations

from starlette.middleware.gzip import GZipMiddleware
from starlette.types import ASGIApp, Message, Receive, Scope, Send

ALREADY_COMPRESSED = (".webp", ".png", ".jpg", ".jpeg", ".woff2", ".mp4", ".pdf", ".zip", ".ico")
LONG_LIVED_FOLDERS = ("/static/fonts/", "/static/img/", "/static/3Dmodels/", "/static/vendor/", "/static/images/", "/static/PDF/", "/static/dlybeck/", "/static/programs/")
WEEK = 7 * 24 * 3600


class SelectiveGZip:
    """GZip for text-like responses only."""

    def __init__(self, app: ASGIApp) -> None:
        self.plain = app
        self.compressed = GZipMiddleware(app, minimum_size=800)

    async def __call__(self, scope: Scope, receive: Receive, send: Send) -> None:
        if scope["type"] == "http" and scope["path"].lower().endswith(ALREADY_COMPRESSED):
            await self.plain(scope, receive, send)
        else:
            await self.compressed(scope, receive, send)


class CacheControl:
    """Cache-Control for static files; pages and their code are revalidated every time."""

    def __init__(self, app: ASGIApp) -> None:
        self.app = app

    async def __call__(self, scope: Scope, receive: Receive, send: Send) -> None:
        if scope["type"] != "http":
            await self.app(scope, receive, send)
            return
        path = scope["path"]

        async def add_header(message: Message) -> None:
            if message["type"] == "http.response.start" and message["status"] in (200, 206, 304):
                headers = message.setdefault("headers", [])
                if not any(name.lower() == b"cache-control" for name, _ in headers):
                    if path.startswith(LONG_LIVED_FOLDERS):
                        value = f"public, max-age={WEEK}"
                    else:
                        value = "no-cache"
                    headers.append((b"cache-control", value.encode()))
            await send(message)

        await self.app(scope, receive, add_header)
