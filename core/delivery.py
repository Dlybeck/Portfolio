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
LONG_LIVED_FOLDERS = ("/static/fonts/", "/static/img/", "/static/3Dmodels/", "/static/vendor/", "/static/PDF/", "/static/dlybeck/", "/static/programs/")
# Code that changes with the site is never cached for long (the vendored viewer is the exception: it is pinned).
ALWAYS_REVALIDATED = (".css", ".js", ".html")
WEEK = 7 * 24 * 3600


def _wants_a_range(scope: Scope) -> bool:
    return any(name == b"range" for name, _ in scope["headers"])


class SelectiveGZip:
    """GZip for whole text-like responses only: never for pictures, fonts and video, nor for byte ranges."""

    def __init__(self, app: ASGIApp) -> None:
        self.plain = app
        self.compressed = GZipMiddleware(app, minimum_size=800)

    async def __call__(self, scope: Scope, receive: Receive, send: Send) -> None:
        if scope["type"] != "http" or scope["path"].lower().endswith(ALREADY_COMPRESSED) or _wants_a_range(scope):
            await self.plain(scope, receive, send)
            return

        async def vary_on_encoding(message: Message) -> None:
            # 304 and 206 answers come back unzipped but must still say the answer depends on the encoding
            if message["type"] == "http.response.start" and message["status"] in (206, 304):
                headers = message.setdefault("headers", [])
                if not any(name.lower() == b"vary" for name, _ in headers):
                    headers.append((b"vary", b"Accept-Encoding"))
            await send(message)

        await self.compressed(scope, receive, vary_on_encoding)


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
                    code = path.endswith(ALWAYS_REVALIDATED) and not path.startswith("/static/vendor/")
                    if path.startswith(LONG_LIVED_FOLDERS) and not code:
                        value = f"public, max-age={WEEK}"
                    else:
                        value = "no-cache"
                    headers.append((b"cache-control", value.encode()))
            await send(message)

        await self.app(scope, receive, add_header)
