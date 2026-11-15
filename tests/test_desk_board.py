"""The desk board module: fetch, five-minute cache, strict shape, offline copy. Desk itself is faked."""

from __future__ import annotations

from datetime import datetime, timezone

import pytest

from core import desk_board
from core.desk_board import Board, DeskBoard, DeskStatus, ago, describe, parse

GOOD = {
    "at": "2026-11-15T09:00:00Z",
    "working": 3,
    "waiting": 1,
    "idle": 4,
    "activeProjects": 5,
    "focusProjects": 2,
    "gpu": "busy",
    "lastActive": "2026-11-15T08:58:00Z",
}


class Clock:
    def __init__(self, t: float = 1_000_000.0) -> None:
        self.t = t

    def __call__(self) -> float:
        return self.t


class FakeDesk:
    """Answers like Desk would, counts the calls, and can be made to fail."""

    def __init__(self, answer: object = GOOD) -> None:
        self.answer = answer
        self.calls: list[tuple[str, str]] = []
        self.down = False

    def __call__(self, url: str, secret: str) -> object:
        self.calls.append((url, secret))
        if self.down:
            raise OSError("connection refused")
        return self.answer


def make(desk: FakeDesk, clock: Clock) -> DeskBoard:
    return DeskBoard("https://desk.invalid/board", "s3cret", fetch=desk, clock=clock)


def test_fresh_fetch_reads_every_field_and_sends_the_secret():
    desk, clock = FakeDesk(), Clock()
    board = make(desk, clock).get()
    assert board.state == "live"
    assert desk.calls == [("https://desk.invalid/board", "s3cret")]
    s = board.status
    assert (s.working, s.waiting, s.idle, s.active_projects, s.focus_projects, s.gpu) == (3, 1, 4, 5, 2, "busy")
    assert s.at == datetime(2026, 11, 15, 9, 0, tzinfo=timezone.utc)
    assert s.last_active == datetime(2026, 11, 15, 8, 58, tzinfo=timezone.utc)


def test_cache_hit_within_five_minutes_does_not_ask_again():
    desk, clock = FakeDesk(), Clock()
    board = make(desk, clock)
    board.get()
    clock.t += 299
    assert board.get().state == "live"
    assert len(desk.calls) == 1
    clock.t += 2  # past five minutes
    desk.answer = {**GOOD, "working": 0}
    assert board.get().status.working == 0
    assert len(desk.calls) == 2


def test_failure_with_a_previous_copy_shows_it_as_offline_with_its_age():
    desk, clock = FakeDesk(), Clock()
    board = make(desk, clock)
    board.get()
    clock.t += 600
    desk.down = True
    result = board.get()
    assert result.state == "offline"
    assert result.status.working == 3
    assert result.age(clock.t) == 600


def test_failure_without_a_previous_copy_is_offline_and_empty():
    desk, clock = FakeDesk(), Clock()
    desk.down = True
    result = make(desk, clock).get()
    assert result == Board("offline", None, None)


def test_after_a_failure_it_waits_a_minute_before_asking_again():
    desk, clock = FakeDesk(), Clock()
    desk.down = True
    board = make(desk, clock)
    board.get()
    clock.t += 30
    board.get()
    assert len(desk.calls) == 1
    desk.down = False
    clock.t += 31
    assert board.get().state == "live"
    assert len(desk.calls) == 2


def test_a_bad_answer_counts_as_a_failure():
    desk, clock = FakeDesk(answer=["not", "an", "object"]), Clock()
    assert make(desk, clock).get().state == "offline"
    desk2 = FakeDesk(answer={"names": ["secret project"]})
    assert make(desk2, Clock()).get().state == "offline"


@pytest.mark.parametrize("url, secret", [(None, None), ("", "x"), ("https://desk.invalid", ""), ("  ", "  ")])
def test_unset_config_never_fetches(url, secret):
    desk = FakeDesk()
    result = DeskBoard(url, secret, fetch=desk, clock=Clock()).get()
    assert result.state == "unconfigured" and result.status is None
    assert desk.calls == []


def test_from_env_reads_only_the_environment(monkeypatch):
    monkeypatch.delenv("DESK_BOARD_URL", raising=False)
    monkeypatch.delenv("DESK_BOARD_SECRET", raising=False)
    assert not desk_board.from_env().configured
    monkeypatch.setenv("DESK_BOARD_URL", "https://desk.invalid/board")
    monkeypatch.setenv("DESK_BOARD_SECRET", "s3cret\n")
    assert desk_board.from_env().configured


def test_extra_fields_are_dropped():
    status = parse({**GOOD, "projects": ["portfolio"], "chat": "fix the login", "working": 2})
    assert status is not None
    assert set(DeskStatus.__slots__) == {"at", "working", "waiting", "idle", "active_projects", "focus_projects", "gpu", "last_active"}
    assert "portfolio" not in repr(status) and "login" not in repr(status)


@pytest.mark.parametrize(
    "field, bad",
    [
        ("working", "3"), ("working", 2.5), ("working", True), ("working", -1), ("working", 10**9),
        ("waiting", None), ("idle", [1]), ("activeProjects", {"n": 1}), ("focusProjects", "two"),
        ("gpu", "on fire"), ("gpu", 1), ("at", "yesterday"), ("lastActive", 1731660000), ("lastActive", "x" * 100),
    ],
)
def test_malformed_fields_are_dropped_one_by_one(field, bad):
    status = parse({**GOOD, field: bad})
    assert status is not None
    ours = {"activeProjects": "active_projects", "focusProjects": "focus_projects", "lastActive": "last_active"}.get(field, field)
    assert getattr(status, ours) is None
    assert status.idle == 4 or field == "idle"  # the rest survive


def test_naive_times_are_read_as_utc():
    status = parse({**GOOD, "lastActive": "2026-11-15T08:58:00"})
    assert status.last_active.tzinfo is not None


def test_http_fetch_refuses_other_schemes():
    with pytest.raises(ValueError):
        desk_board.http_fetch("file:///etc/passwd", "x")


def test_failure_logs_never_include_the_address_or_secret(caplog):
    def broken(url, secret):
        raise OSError(f"cannot reach {url} with {secret}")

    DeskBoard("https://desk.invalid/board", "s3cret", fetch=broken, clock=Clock()).get()
    assert "desk.invalid" not in caplog.text and "s3cret" not in caplog.text


# ---------- the words ----------

NOW = datetime(2026, 11, 15, 9, 2, tzinfo=timezone.utc).timestamp()


@pytest.mark.parametrize(
    "seconds, words",
    [(5, "just now"), (60, "1 minute ago"), (150, "2 minutes ago"), (3600, "1 hour ago"), (7300, "2 hours ago"),
     (86_400, "yesterday"), (3 * 86_400, "3 days ago")],
)
def test_ago(seconds, words):
    assert ago(seconds) == words


def board(state="live", **fields) -> Board:
    status = parse({**GOOD, **fields})
    return Board(state, status, NOW - 120)


def test_working_view():
    view = describe(board(), NOW)
    assert view.mood == "working" and not view.stale
    assert view.headline == "3 AI chats working right now"
    assert [f.sentence for f in view.facts] == [
        "3 AI chats working right now", "1 AI chat waiting on me", "4 AI chats resting",
        "5 projects active in the last day", "2 projects in focus", "GPU busy training", "Last active 4 minutes ago",
    ]
    assert view.note == "Checked 2 minutes ago."


def test_waiting_view():
    view = describe(board(working=0, waiting=2), NOW)
    assert (view.mood, view.headline) == ("waiting", "2 AI chats waiting on me")


def test_resting_view():
    view = describe(board(working=0, waiting=0, gpu="idle"), NOW)
    assert (view.mood, view.headline) == ("resting", "Resting right now")
    assert "GPU idle" in [f.sentence for f in view.facts]


def test_offline_with_copy_view():
    view = describe(Board("offline", parse(GOOD), NOW - 3 * 3600), NOW)
    assert view.mood == "offline" and view.stale
    assert view.headline == "My desk is offline"
    assert view.note == "Showing the last copy, from 3 hours ago."
    assert view.facts  # the copy is still shown


@pytest.mark.parametrize("state", ["offline", "unconfigured"])
def test_offline_without_copy_view(state):
    view = describe(Board(state, None, None), NOW)
    assert view.mood == "offline" and view.facts == ()
    assert view.headline == "My desk isn't reachable right now"


def test_missing_fields_leave_their_line_out():
    view = describe(Board("live", parse({"working": 1}), NOW), NOW)
    assert [f.key for f in view.facts] == ["working"]
    assert view.headline == "1 AI chat working right now"


def test_a_last_copy_is_told_in_the_past_tense():
    view = describe(Board("offline", parse(GOOD), NOW - 3 * 3600), NOW)
    text = " ".join(view.sentences)
    assert "right now" not in text
    assert view.sentences[:3] == ("My desk is offline", "Last copy, from 3 hours ago", "3 AI chats were working")
    assert "GPU was busy training" in view.sentences


def test_sentences_do_not_repeat_the_headline():
    view = describe(board(), NOW)
    assert view.sentences[0] == "3 AI chats working right now"
    assert view.sentences.count("3 AI chats working right now") == 1
