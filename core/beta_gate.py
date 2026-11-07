"""A shared-passcode gate for private beta copies of the site.

Off unless the BETA_PASSCODE environment variable is set (production never sets it), so production behaves exactly
as it always has. When on, every request needs a signed cookie, handed out in exchange for the passcode, and every
response asks search engines to stay away.
"""

from __future__ import annotations

import hashlib
import hmac
import time
from collections import defaultdict, deque
from html import escape
from ipaddress import ip_address, ip_network
from urllib.parse import parse_qs, quote

from starlette.datastructures import MutableHeaders
from starlette.requests import Request
from starlette.responses import HTMLResponse, RedirectResponse, Response
from starlette.types import ASGIApp, Receive, Scope, Send

COOKIE_NAME = "beta_gate"
UNLOCK_PATH = "/_beta/unlock"
COOKIE_LIFETIME = 30 * 24 * 3600
ROBOTS_TXT = "User-agent: *\nDisallow: /\n"
MAX_FORM_BYTES = 4096
MAX_FAILURES = 5  # wrong guesses allowed per address ...
FAILURE_WINDOW = 15 * 60  # ... within this many seconds, after which that address waits out the window
MAX_TRACKED_ADDRESSES = 10_000

PAGE = """<!doctype html>
<html lang="en"><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<meta name="robots" content="noindex, nofollow">
<title>Private preview</title>
<style>
  :root {{ color-scheme: light dark; --paper: #f6f1e7; --ink: #26231f; --muted: #6f685d; --line: #cfc6b4; --accent: #26231f; }}
  @media (prefers-color-scheme: dark) {{ :root {{ --paper: #1d1b18; --ink: #ece6d8; --muted: #a49c8d; --line: #4a453c; --accent: #ece6d8; }} }}
  * {{ box-sizing: border-box; }}
  body {{ margin: 0; min-height: 100vh; display: grid; place-items: center; padding: 16px; background: var(--paper); color: var(--ink);
         font: 16px/1.5 ui-monospace, "SFMono-Regular", Menlo, Consolas, monospace; }}
  main {{ width: 100%; max-width: 22rem; }}
  h1 {{ margin: 0 0 .25rem; font: 600 1.4rem/1.2 Georgia, "Times New Roman", serif; }}
  p {{ margin: 0 0 1.25rem; color: var(--muted); font-size: .9rem; }}
  input, button {{ width: 100%; font: inherit; padding: .65rem .8rem; border: 1px solid var(--line); border-radius: 6px; }}
  input {{ background: transparent; color: var(--ink); margin-bottom: .75rem; }}
  button {{ background: var(--accent); color: var(--paper); border-color: var(--accent); cursor: pointer; }}
  p.error {{ color: #b3261e; margin: 0 0 .75rem; }}
  @media (prefers-color-scheme: dark) {{ p.error {{ color: #f2a29b; }} }}
</style></head>
<body><main>
<h1>Private preview</h1>
<p>This copy of the site is shared by invitation. Enter the passcode to continue.</p>
{error}<form method="post" action="{action}">
<input type="hidden" name="next" value="{next}">
<input type="password" name="passcode" autocomplete="current-password" aria-label="Passcode" autofocus required>
<button type="submit">Enter</button>
</form></main></body></html>
"""


def safe_next(target: str | None) -> str:
    """Only same-site relative paths survive; anything that could leave the site becomes '/'."""
    if not target or not target.startswith("/") or target.startswith("//"):
        return "/"
    if "\\" in target or any(ord(char) < 32 or ord(char) == 127 for char in target):
        return "/"
    return target


class BetaGate:
    """Pure ASGI middleware so it can sit outermost and mark every response, compressed or not."""

    def __init__(self, app: ASGIApp, passcode: str) -> None:
        self.app = app
        self.passcode = passcode.encode()
        # Derived from the passcode, so changing the passcode invalidates every cookie already handed out.
        self.key = hashlib.sha256(b"portfolio-beta-gate:" + self.passcode).digest()
        self.failures: dict[str, deque[float]] = defaultdict(deque)

    # -- cookie ---------------------------------------------------------------------------------------------------
    def _sign(self, expires: int) -> str:
        return hmac.new(self.key, str(expires).encode(), hashlib.sha256).hexdigest()

    def make_cookie(self, now: float | None = None) -> str:
        expires = int((time.time() if now is None else now) + COOKIE_LIFETIME)
        return f"{expires}.{self._sign(expires)}"

    def cookie_is_valid(self, value: str | None, now: float | None = None) -> bool:
        if not value or "." not in value:
            return False
        expires_text, _, signature = value.partition(".")
        # a real expiry is ten digits; the length cap also keeps int() clear of Python's huge-number limit
        if not expires_text.isascii() or not expires_text.isdigit() or len(expires_text) > 12:
            return False
        expires = int(expires_text)
        signature_ok = hmac.compare_digest(signature.encode(), self._sign(expires).encode())
        return signature_ok and expires > (time.time() if now is None else now)

    # -- slowdown -------------------------------------------------------------------------------------------------
    @staticmethod
    def client_address(request: Request) -> str:
        # Behind Cloud Run the rightmost X-Forwarded-For entry is the one Google's front end recorded; earlier ones
        # are client-supplied and could be forged to dodge the limit.
        forwarded = request.headers.get("x-forwarded-for", "")
        address = forwarded.split(",")[-1].strip() if forwarded.strip() else (request.client.host if request.client else "unknown")
        try:
            parsed = ip_address(address)
        except ValueError:
            return address
        # one household or host holds a whole /64 of IPv6 addresses, so count them together
        return str(ip_network(f"{parsed}/64", strict=False)) if parsed.version == 6 else address

    def _recent_failures(self, address: str) -> deque[float]:
        attempts = self.failures.get(address)
        if attempts is None:
            return deque()
        cutoff = time.monotonic() - FAILURE_WINDOW
        while attempts and attempts[0] < cutoff:
            attempts.popleft()
        if not attempts:
            del self.failures[address]
        return attempts

    def _record_failure(self, address: str) -> None:
        if address not in self.failures and len(self.failures) >= MAX_TRACKED_ADDRESSES:
            del self.failures[next(iter(self.failures))]  # the longest-tracked address makes room
        self.failures[address].append(time.monotonic())

    # -- responses ------------------------------------------------------------------------------------------------
    @staticmethod
    def gate_page(next_path: str, error: str = "", status: int = 401) -> Response:
        notice = f'<p class="error" role="alert">{escape(error)}</p>\n' if error else ""
        html = PAGE.format(error=notice, action=UNLOCK_PATH, next=escape(next_path, quote=True))
        return HTMLResponse(html, status_code=status, headers={"Cache-Control": "no-store"})

    async def _unlock(self, request: Request) -> Response:
        address = self.client_address(request)
        if len(self._recent_failures(address)) >= MAX_FAILURES:
            return self.gate_page("/", "Too many attempts. Please wait a few minutes.", 429)

        body = b""
        async for chunk in request.stream():
            body += chunk
            if len(body) > MAX_FORM_BYTES:
                return self.gate_page("/", "That request was too large.", 413)
        form = parse_qs(body.decode("utf-8", "replace"), keep_blank_values=True)
        next_path = safe_next((form.get("next") or [""])[0])
        offered = (form.get("passcode") or [""])[0].encode()

        if not hmac.compare_digest(hashlib.sha256(offered).digest(), hashlib.sha256(self.passcode).digest()):
            self._record_failure(address)
            return self.gate_page(next_path, "That passcode is not right.")

        self.failures.pop(address, None)
        response = RedirectResponse(quote(next_path, safe="/?&=%#:@!$'()*+,;~-._"), status_code=303)
        response.set_cookie(
            COOKIE_NAME, self.make_cookie(), max_age=COOKIE_LIFETIME, httponly=True, secure=True, samesite="lax", path="/"
        )
        return response

    async def _handle(self, scope: Scope, receive: Receive, send: Send) -> None:
        request = Request(scope, receive)
        path = scope["path"]
        if path == "/robots.txt":
            response: Response = Response(ROBOTS_TXT, media_type="text/plain")
        elif path == UNLOCK_PATH and request.method == "POST":
            response = await self._unlock(request)
        elif self.cookie_is_valid(request.cookies.get(COOKIE_NAME)):
            await self.app(scope, receive, send)
            return
        else:
            query = scope["query_string"].decode("latin-1")
            response = self.gate_page(safe_next(path + (f"?{query}" if query else "")))
        await response(scope, receive, send)

    async def __call__(self, scope: Scope, receive: Receive, send: Send) -> None:
        if scope["type"] != "http":
            if scope["type"] == "websocket":  # the site has none; refuse rather than let one past the gate
                await send({"type": "websocket.close", "code": 1008})
            else:
                await self.app(scope, receive, send)
            return

        async def send_with_noindex(message) -> None:
            if message["type"] == "http.response.start":
                MutableHeaders(scope=message)["X-Robots-Tag"] = "noindex, nofollow"
            await send(message)

        await self._handle(scope, receive, send_with_noindex)
