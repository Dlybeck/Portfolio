"""The notebook's table of contents: sections, pages, and the order they turn in.

One source of truth. The templates render from it, and the browser engine gets
the same data as JSON so the wheel, the page numbers and the URLs agree.
"""

from __future__ import annotations

from dataclasses import dataclass

from core.portfolio import DOCUMENTS


@dataclass(frozen=True, slots=True)
class Section:
    id: str
    tab: str  # label on the wheel and in the page footer
    color: str  # a dlybeck paper color name


@dataclass(frozen=True, slots=True)
class Page:
    id: str
    section: str
    title: str
    kicker: str  # the small line above a title, and in the contents list
    summary: str  # one line, used in the contents list
    # How a desktop spread is laid out:
    #   "list":  left = the section's list of stories, right = this story
    #   "split": left = the first <section> of the page, right = the rest
    #   "pair":  left = this page, right = the page named by `pair`
    layout: str = "list"
    pair: str | None = None
    phone_only: bool = False  # index pages that a desktop spread replaces
    path: str | None = None  # canonical route; None for pages without one

    @property
    def href(self) -> str:
        """A real link to this page; pages without a route open by hash."""
        return self.path or f"/#{HASHES[self.id]}"


SECTIONS = (
    Section("me", "About", "lemon"),
    Section("projects", "Projects", "sky"),
    Section("work", "Work", "mint"),
    Section("school", "School", "pink"),
    Section("hobbies", "Hobbies", "tangerine"),
    Section("say", "Say hi", "note"),
)

_CANONICAL = {}
for _doc in DOCUMENTS:
    _CANONICAL.setdefault(_doc.page, _doc.route)


def _page(id: str, section: str, title: str, kicker: str, summary: str, **kw) -> Page:
    return Page(id, section, title, kicker, summary, path=_CANONICAL.get(id), **kw)


PAGES = (
    _page("me", "me", "David Lybeck", "Hi, I'm David", "", layout="pair", pair="toc"),
    _page("toc", "me", "Contents", "", "", phone_only=True),
    _page("projects", "projects", "Projects", "5 entries", "", phone_only=True),
    _page("scribblescan", "projects", "ScribbleScan", "2025 to now",
          "Handwriting digitization, from a hosted product to an offline, privacy-first experiment."),
    _page("site", "projects", "This website", "2022 to now",
          "You're looking at it! Four versions so far, and how each was made."),
    _page("nba", "projects", "NBA Prediction AI", "2024 · partner project",
          "A neural network that called the 2024 playoffs with only 2 mistakes."),
    _page("planner", "projects", "Digital Planner", "2022 · class team",
          "A calendar and to-do list built with a four-person class team."),
    _page("programs", "projects", "Programs", "2021 to 2024",
          "Software experiments and selected coursework, from sorts to a Connect 4 bot."),
    _page("work", "work", "Work", "Work · 8 roles", "From coaching tennis to building AI tools.",
          layout="split"),
    _page("school", "school", "School", "Class of 2025", "Schools I've gone to and classes I've taken.",
          layout="split"),
    _page("hobbies", "hobbies", "Hobbies", "3 entries", "", phone_only=True),
    _page("printing", "hobbies", "3D printing", "Puzzles and models",
          "Puzzle boxes I designed, one with 45,000+ downloads. I bet you can't solve them."),
    _page("gaming", "hobbies", "Gaming", "Shorter games",
          "Some of my favorites. I'll race you in Mario Kart Wii."),
    _page("tennis", "hobbies", "Tennis", "Since middle school",
          "I've played for as long as I remember. Let me know if you want to hit."),
    _page("say", "say", "Say hi", "", "", layout="split"),
)

PAGES_BY_ID = {page.id: page for page in PAGES}

# Phone: one page at a time, all fifteen. Desktop: spreads, so the index pages drop out.
PHONE_ORDER = tuple(page.id for page in PAGES)
DESKTOP_ORDER = tuple(page.id for page in PAGES if not page.phone_only)

# What the contents and the section lists show, in order.
CONTENTS = ("projects", "work", "school", "hobbies", "say")
LISTS = {
    "projects": ("scribblescan", "site", "nba", "planner", "programs"),
    "hobbies": ("printing", "gaming", "tennis"),
}
LIST_LEADS = {
    "projects": "Personal projects I've developed, and how they were made.",
    "hobbies": "All my favorites! (Coding gets its own section.)",
}

# Routes that have no page of their own open the closed index pages by hash.
HASHES = {"me": "about", "toc": "contents", "projects": "projects", "hobbies": "hobbies", "say": "say-hi"}


def client_data() -> dict[str, object]:
    """What the browser engine needs, as plain JSON."""
    return {
        "phone": list(PHONE_ORDER),
        "desktop": list(DESKTOP_ORDER),
        "sections": [{"id": s.id, "tab": s.tab, "color": s.color} for s in SECTIONS],
        "pages": {
            page.id: {
                "section": page.section,
                "title": page.title,
                "layout": page.layout,
                "pair": page.pair,
                "path": page.path,
                "hash": HASHES.get(page.id),
            }
            for page in PAGES
        },
        "lists": {name: list(ids) for name, ids in LISTS.items()},
        "routes": {doc.route: {"page": doc.page, "anchor": doc.anchor} for doc in DOCUMENTS},
    }
