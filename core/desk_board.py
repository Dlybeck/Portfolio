"""The desk board: a few anonymous counts from Desk, David's private status service.

The portfolio's server asks Desk when a page needs the board and keeps the answer for five
minutes. A visitor's browser never talks to Desk, and Desk's address and secret come only from
the environment (DESK_BOARD_URL, DESK_BOARD_SECRET): they are never written into a page.

Only the fields below are read, each checked on its own; anything else Desk sends is dropped,
and a field that is the wrong shape is dropped too. There are no names in the data, so the board
can never show one.
"""

from __future__ import annotations

import json
import logging
import math
import os
import threading
import time
import urllib.request
from collections.abc import Callable
from dataclasses import dataclass
from datetime import datetime, timezone
from typing import Literal

logger = logging.getLogger(__name__)

TTL_SECONDS = 300  # a good answer is kept this long
RETRY_SECONDS = 60  # after a failure, wait this long before asking again (so a down desk never slows every page)
TIMEOUT_SECONDS = 2.0
MAX_BYTES = 16_384  # the real answer is about 200 bytes
MAX_COUNT = 10_000  # no believable count is larger

COUNTS = {  # Desk's field name -> ours
    "working": "working",
    "waiting": "waiting",
    "idle": "idle",
    "activeProjects": "active_projects",
    "focusProjects": "focus_projects",
}
GPU_STATES = ("busy", "idle")


@dataclass(frozen=True, slots=True)
class DeskStatus:
    """One answer from Desk. A field is None when Desk left it out or sent it in the wrong shape."""

    at: datetime | None = None
    working: int | None = None
    waiting: int | None = None
    idle: int | None = None
    active_projects: int | None = None
    focus_projects: int | None = None
    gpu: Literal["busy", "idle"] | None = None
    last_active: datetime | None = None


@dataclass(frozen=True, slots=True)
class Board:
    """What a page gets: the live answer, or the last good one (if any) while Desk is unreachable.

    state: "live" (fresh within five minutes), "offline" (the last fetch failed), or
    "unconfigured" (no address or secret in the environment).
    """

    state: Literal["live", "offline", "unconfigured"]
    status: DeskStatus | None
    fetched_at: float | None  # when `status` was fetched (epoch seconds), or None

    def age(self, now: float) -> float | None:
        """Seconds since `status` was fetched."""
        return None if self.fetched_at is None else max(0.0, now - self.fetched_at)


def _count(value: object) -> int | None:
    # bool is an int in Python; a true/false is not a count.
    if isinstance(value, bool) or not isinstance(value, int):
        return None
    return value if 0 <= value <= MAX_COUNT else None


def _time(value: object) -> datetime | None:
    if not isinstance(value, str) or len(value) > 40:
        return None
    try:
        parsed = datetime.fromisoformat(value)
    except ValueError:
        return None
    return parsed if parsed.tzinfo else parsed.replace(tzinfo=timezone.utc)


def parse(payload: object) -> DeskStatus | None:
    """Keep only the known fields, each in its known shape. None if nothing usable is left."""
    if not isinstance(payload, dict):
        return None
    fields: dict[str, object] = {ours: _count(payload.get(theirs)) for theirs, ours in COUNTS.items()}
    gpu = payload.get("gpu")
    fields["gpu"] = gpu if isinstance(gpu, str) and gpu in GPU_STATES else None
    fields["at"] = _time(payload.get("at"))
    fields["last_active"] = _time(payload.get("lastActive"))
    if all(fields[name] is None for name in COUNTS.values()) and fields["gpu"] is None:
        return None  # nothing a visitor could be shown
    return DeskStatus(**fields)  # type: ignore[arg-type]


def http_fetch(url: str, secret: str, timeout: float = TIMEOUT_SECONDS) -> object:
    """GET the board from Desk and decode its JSON. Raises on any failure."""
    if not url.startswith(("https://", "http://")):
        raise ValueError("DESK_BOARD_URL must be an http(s) address")
    request = urllib.request.Request(url, headers={"Authorization": f"Bearer {secret}", "Accept": "application/json"})
    with urllib.request.urlopen(request, timeout=timeout) as response:  # noqa: S310 (scheme checked above)
        body = response.read(MAX_BYTES + 1)
    if len(body) > MAX_BYTES:
        raise ValueError("desk board answer too large")
    return json.loads(body)


class DeskBoard:
    """Fetches Desk at most once per five minutes and remembers the last good answer."""

    def __init__(
        self,
        url: str | None,
        secret: str | None,
        fetch: Callable[[str, str], object] = http_fetch,
        clock: Callable[[], float] = time.time,
        ttl: float = TTL_SECONDS,
        retry: float = RETRY_SECONDS,
    ) -> None:
        self._url = (url or "").strip()
        self._secret = (secret or "").strip()
        self._fetch = fetch
        self._clock = clock
        self._ttl = ttl
        self._retry = retry
        self._lock = threading.Lock()
        self._good: DeskStatus | None = None
        self._good_at: float | None = None
        self._failed_at: float | None = None

    @property
    def configured(self) -> bool:
        return bool(self._url and self._secret)

    def get(self) -> Board:
        if not self.configured:
            return Board("unconfigured", None, None)
        now = self._clock()
        if self._fresh(now):
            return self._current(now)
        # One request refreshes; any others arriving meanwhile get what is already known instead of waiting.
        if not self._lock.acquire(blocking=self._good is None and self._failed_at is None):
            return self._current(now)
        try:
            now = self._clock()
            if not self._fresh(now):
                self._refresh(now)
            return self._current(now)
        finally:
            self._lock.release()

    def _fresh(self, now: float) -> bool:
        if self._failed_at is not None:
            return now - self._failed_at < self._retry
        return self._good_at is not None and now - self._good_at < self._ttl

    def _refresh(self, now: float) -> None:
        try:
            status = parse(self._fetch(self._url, self._secret))
            if status is None:
                raise ValueError("desk board answer had no usable fields")
        except Exception as error:  # noqa: BLE001 (any failure means offline)
            # Only the kind of error: its text could carry the address.
            logger.warning("desk board unavailable: %s", type(error).__name__)
            self._failed_at = now
            return
        self._good, self._good_at, self._failed_at = status, now, None

    def _current(self, now: float) -> Board:
        # A copy just past five minutes while another request refreshes it is still the live answer.
        if self._failed_at is not None or self._good is None:
            return Board("offline", self._good, self._good_at)
        return Board("live", self._good, self._good_at)


def from_env() -> DeskBoard:
    return DeskBoard(os.environ.get("DESK_BOARD_URL"), os.environ.get("DESK_BOARD_SECRET"))


# ---------- the words a visitor reads ----------


def ago(seconds: float) -> str:
    """'just now', '1 minute ago', '3 hours ago', 'yesterday', '4 days ago'."""
    seconds = max(0.0, seconds)
    if seconds < 60:
        return "just now"
    for size, unit in ((86_400, "day"), (3_600, "hour"), (60, "minute")):
        if seconds >= size:
            n = math.floor(seconds / size)
            if unit == "day" and n == 1:
                return "yesterday"
            return f"{n} {unit}{'' if n == 1 else 's'} ago"
    return "just now"


def _chats(n: int) -> str:
    return f"{n} AI chat{'' if n == 1 else 's'}"


def _projects(n: int) -> str:
    return f"{n} project{'' if n == 1 else 's'}"


@dataclass(frozen=True, slots=True)
class Fact:
    key: str  # stable id, for styling
    label: str  # short label: "Working now"
    value: str  # its value: "3 AI chats"
    sentence: str  # the same as one line: "3 AI chats working right now"
    count: int | None = None  # the number itself, for the counts


@dataclass(frozen=True, slots=True)
class View:
    """The board in words.

    mood: "working", "waiting", "resting", or "offline" (nothing to show at all).
    stale: True when the facts are the last good copy, not live.
    """

    mood: Literal["working", "waiting", "resting", "offline"]
    headline: str
    facts: tuple[Fact, ...]
    note: str  # the small line under it: when this was checked, or why it is old
    stale: bool

    @property
    def state(self) -> str:
        """The mood in a few words, for a treatment that shows the counts on their own."""
        if self.mood == "offline":
            return "Offline, last copy" if self.stale else "Offline"
        return {"working": "Working right now", "waiting": "Waiting on me", "resting": "Resting right now"}[self.mood]

    @property
    def sentences(self) -> tuple[str, ...]:
        """The headline, then every other fact as a line of its own (the headline's own fact is not repeated)."""
        lines = [self.headline]
        if self.stale:
            lines.append(self.note.replace("Showing the last copy", "Last copy").rstrip("."))  # short enough for one line
        return (*lines, *(f.sentence for f in self.facts if f.sentence != self.headline))

    def fact(self, key: str) -> Fact | None:
        return next((f for f in self.facts if f.key == key), None)


def describe(board: Board, now: float | None = None) -> View:
    now = time.time() if now is None else now
    status = board.status
    if status is None:
        return View("offline", "My desk isn't reachable right now", (), "Nothing to show until it's back.", False)

    # A last copy shown while Desk is unreachable is told in the past tense, never as "right now".
    stale = board.state == "offline"
    were = "were " if stale else ""

    facts: list[Fact] = []
    if status.working is not None:
        n = status.working
        facts.append(Fact("working", "Working" if stale else "Working now", _chats(n),
                          f"{_chats(n)} {were}working" + ("" if stale else " right now"), n))
    if status.waiting is not None:
        n = status.waiting
        facts.append(Fact("waiting", "Waiting on me", _chats(n), f"{_chats(n)} {were}waiting on me", n))
    if status.idle is not None:
        n = status.idle
        facts.append(Fact("idle", "Resting", _chats(n), f"{_chats(n)} {were}resting", n))
    if status.active_projects is not None:
        n = status.active_projects
        facts.append(Fact("active", "Active today", _projects(n), f"{_projects(n)} active in the last day", n))
    if status.focus_projects is not None:
        n = status.focus_projects
        facts.append(Fact("focus", "In focus", _projects(n), f"{_projects(n)} in focus", n))
    if status.gpu is not None:
        busy = status.gpu == "busy"
        value = "busy training" if busy else "idle"
        facts.append(Fact("gpu", "GPU", value, f"GPU {'was ' if stale else ''}{value}"))
    if status.last_active is not None:
        when = ago(now - status.last_active.timestamp())
        facts.append(Fact("last", "Last active", when, f"Last active {when}"))

    working, waiting = status.working or 0, status.waiting or 0
    if stale:
        mood, headline = "offline", "My desk is offline"
    elif working:
        mood, headline = "working", f"{_chats(working)} working right now"
    elif waiting:
        mood, headline = "waiting", f"{_chats(waiting)} waiting on me"
    else:
        mood, headline = "resting", "Resting right now"

    age = board.age(now)
    when = ago(age) if age is not None else "a while ago"
    note = f"Showing the last copy, from {when}." if stale else f"Checked {when}."
    return View(mood, headline, tuple(facts), note, stale)
