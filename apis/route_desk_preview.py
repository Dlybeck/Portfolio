"""Preview of the desk board's three options. Not part of the site.

Mounted only when DESK_BOARD_PREVIEW=1 is set (see main.py), so the live site never has it, and
nothing links to it. Two kinds of page:

  /preview/desk-board               the three options side by side, each in four states
  /preview/desk-board/{a,b,c}       the real notebook with one option placed where it would live
                                    (?state=working|resting|offline|empty|live)

Sample states use made-up counts. "live" asks Desk itself, through core/desk_board, when
DESK_BOARD_URL and DESK_BOARD_SECRET are set.
"""

from __future__ import annotations

import time
from pathlib import Path

from fastapi import APIRouter, HTTPException, Request
from fastapi.concurrency import run_in_threadpool
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates

from apis.route_portfolio import render_notebook
from core import desk_board
from core.desk_board import Board, describe, parse

templates = Jinja2Templates(directory=str(Path(__file__).parent.parent / "templates"))
desk_preview_router = APIRouter(prefix="/preview/desk-board", include_in_schema=False)
_live = desk_board.from_env()


def _iso(seconds_ago: float) -> str:
    return time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime(time.time() - seconds_ago))


def sample(state: str) -> Board:
    """Made-up boards for each state the board can be in."""
    now = time.time()
    if state == "working":
        status = parse({"at": _iso(40), "working": 3, "waiting": 1, "idle": 4, "activeProjects": 5,
                        "focusProjects": 2, "gpu": "busy", "lastActive": _iso(70)})
        return Board("live", status, now - 130)
    if state == "resting":
        status = parse({"at": _iso(60), "working": 0, "waiting": 0, "idle": 2, "activeProjects": 3,
                        "focusProjects": 2, "gpu": "idle", "lastActive": _iso(3 * 3600 + 600)})
        return Board("live", status, now - 60)
    if state == "offline":
        status = parse({"at": _iso(2 * 3600), "working": 2, "waiting": 0, "idle": 3, "activeProjects": 4,
                        "focusProjects": 2, "gpu": "idle", "lastActive": _iso(2 * 3600 + 300)})
        return Board("offline", status, now - 2 * 3600)
    if state == "empty":
        return Board("offline", None, None)
    raise HTTPException(404)


STATES = (("working", "Working"), ("resting", "Resting"), ("offline", "Offline, last copy"), ("empty", "Offline, nothing yet"))

OPTIONS = (
    {
        "id": "a", "name": "A · A few lines on Say hi",
        "where": "The Say hi page, under the contact links. Last page on a phone, left page of the last spread on desktop.",
        "what": "Plain words in the page's own type: one status line, then labelled rows. Reads like part of the page, not a widget.",
    },
    {
        "id": "b", "name": "B · A card inside the back cover",
        "where": "Desktop: the bare kraft inside of the back cover, beside Say hi. Phone: at the foot of Say hi (a phone has no inside cover).",
        "what": "A note card with three counts you take in at a glance, then four short lines. Fills a page that is empty today.",
    },
    {
        "id": "c", "name": "C · A live sticker on the cover",
        "where": "The front cover, under the scan pad, beside the notes label. The first thing every visitor sees.",
        "what": "A vinyl pill, sibling of the \"now\" pill: one line at a time, tap for the next. Smallest and most seen; the details take taps.",
    },
)


async def _board_for(state: str) -> Board:
    if state == "live":
        return await run_in_threadpool(_live.get)
    return sample(state)


@desk_preview_router.get("")
async def side_by_side(request: Request):
    views = {key: describe(sample(key)) for key, _ in STATES}
    live = describe(await run_in_threadpool(_live.get)) if _live.configured else None
    return templates.TemplateResponse(request, "desk_preview/index.html", {
        "options": OPTIONS, "states": STATES, "views": views, "live": live,
    })


def _macro(name: str):
    return getattr(templates.get_template("notebook/_desk.html").module, name)


INJECT = """
<script>
// Preview only: place the option where it would live once the notebook has drawn its cover and pages.
(() => {
  const card = document.getElementById("desk-preview-inside");
  const pill = document.getElementById("desk-preview-cover");
  const place = () => {
    const back = document.querySelector(".cover-inside--back:not(.has-desk)");
    if (card && back) {
      back.classList.add("has-desk"); back.removeAttribute("aria-hidden");
      const slot = document.createElement("div"); slot.className = "desk-inside-slot";
      slot.append(card.content.cloneNode(true)); back.append(slot);
    }
    const front = document.querySelector(".cover-front:not(.has-desk)");
    if (pill && front) {
      front.classList.add("has-desk");
      const slot = document.createElement("div"); slot.className = "wd-slot desk-cover-slot";
      slot.append(pill.content.cloneNode(true)); front.append(slot);
      const el = slot.querySelector(".wd-desk"), lines = JSON.parse(el.dataset.lines);
      let i = 0;
      const next = (e) => {
        e.stopPropagation(); e.preventDefault();
        i = (i + 1) % lines.length;
        el.querySelector("span").textContent = lines[i];
        el.setAttribute("aria-label", lines[i] + ". Tap for more.");
        el.classList.remove("flip"); void el.offsetWidth; el.classList.add("flip");
      };
      for (const t of ["pointerdown", "pointerup"]) el.addEventListener(t, (e) => e.stopPropagation());
      el.addEventListener("click", next);
      el.addEventListener("keydown", (e) => { if (e.key === "Enter" || e.key === " ") next(e); });
    }
  };
  new MutationObserver(place).observe(document.body, { childList: true, subtree: true });
  place();
})();
</script>
<style>
.desk-inside-slot { position: absolute; left: 50%; top: 9cqh; translate: -50% 0; width: min(78cqw, 320px); pointer-events: auto; }
.desk-cover-slot { left: 12cqw; top: 81.6cqh; rotate: 2.5deg; z-index: 3; }
.nb--desktop .page .desk-phone-only { display: none; }
.desk-preview-flag { position: fixed; right: 8px; bottom: 8px; z-index: 999; padding: 2px 8px; border-radius: 999px; background: var(--hi); border: 1.5px solid var(--ink-fixed); font: 600 0.68rem/1.4 var(--font-mono); }
</style>
"""


@desk_preview_router.get("/{option}")
async def in_notebook(request: Request, option: str, state: str = "working"):
    if option not in ("a", "b", "c"):
        raise HTTPException(404)
    view = describe(await _board_for(state))
    html = render_notebook(request).body.decode()

    head = '<link rel="stylesheet" href="/static/css/notebook/desk.css?v=1"><meta name="robots" content="noindex">'
    html = html.replace("</head>", head + "</head>", 1)
    marker = 'id="page-say"'
    at = html.index(marker)
    end = html.index("</section>", at)
    extra = ""
    if option == "a":
        html = html[:end] + str(_macro("desk_log")(view)) + html[end:]
    elif option == "b":
        card = str(_macro("desk_card")(view))
        html = html[:end] + f'<div class="desk-phone-only" style="margin-top:20px">{card}</div>' + html[end:]
        extra = f'<template id="desk-preview-inside">{card}</template>'
    else:
        extra = f'<template id="desk-preview-cover">{_macro("desk_pill")(view)}</template>'
    flag = f'<div class="desk-preview-flag">Preview · option {option.upper()} · {state}</div>'
    body_end = html.rindex("</body>")
    html = html[:body_end] + extra + INJECT + flag + html[body_end:]
    return HTMLResponse(html, headers={"Cache-Control": "no-store"})
