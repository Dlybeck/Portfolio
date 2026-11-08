"""The brown back board stays under the cover's free edge for the whole opening and closing (desktop).

The cover swings with rotateY and perspective, so its edge follows cos(angle), not the easing. swing.js drives the cover,
the book's slide and the board's clip from one angle each frame. Time is controlled with Playwright's fake clock, so the
frames are exact and repeatable.
"""

from __future__ import annotations


import pytest

DESKTOP = {"width": 1440, "height": 900}
OPEN_MS = 800
FRAME_MS = 16

# the cover's drawn edge and the board's visible edge, in page px, read from the real boxes
MEASURE = """() => {
  const book = document.querySelector('.nb-book'), back = document.querySelector('.nb-back');
  const leaf = document.querySelector('.nb-leaf.cover');
  const b = book.getBoundingClientRect(), r = back.getBoundingClientRect();
  const cover = leaf ? leaf.getBoundingClientRect() : null;
  const spine = b.left + b.width / 2;
  const clip = getComputedStyle(back).clipPath;
  // computed insets are written in CSS shorthand (equal left and right collapse), so expand to find the left value
  const v = clip.startsWith('inset(') ? clip.slice(6, -1).split(' ').map(parseFloat) : [0];
  const inset = v.length === 4 ? v[3] : v.length === 1 ? v[0] : v[1];
  const m = leaf ? getComputedStyle(leaf).transform : 'none';
  const cos = m.startsWith('matrix3d') ? parseFloat(m.slice(9).split(',')[0]) : 1;
  return {
    spine, half: b.width / 2, open: Math.acos(Math.max(-1, Math.min(1, cos))) / Math.PI,
    coverEdge: cover ? (cos >= 0 ? cover.right : cover.left) : null,
    boardEdge: r.left + inset,
  };
}"""


def settle(page, route):
    page.clock.install(time=0)
    page.set_viewport_size(DESKTOP)
    page.goto(page.base + route)
    page.wait_for_selector("#notebook.nb--desktop")
    page.clock.run_for(1500)
    page.clock.pause_at(3000)  # a fixed instant after load; the clock stands still from here


def frames(page, fractions=(0, 0.25, 0.5, 0.75, 1.0)):
    """Step the paused clock to each fraction of the move and read both edges."""
    page.clock.run_for(FRAME_MS)  # the loop's first frame sets its start time
    out, done = [], 0
    for f in fractions:
        step = round(f * OPEN_MS) - done
        if step > 0:
            page.clock.run_for(step)
            done += step
        out.append({"at": f, **page.evaluate(MEASURE)})
    return out


def check(shots):
    for s in shots:
        if s["coverEdge"] is None:  # the leaf is gone at the end of an opening: the board is the whole book
            continue
        under = s["coverEdge"] - s["spine"]
        # the clip also opens up to 12px more as the cover lands, so the board's soft shadow is not cut off at its edge
        slack = 12 * min(1, max(0, -under / s["half"]))
        rim = s["coverEdge"] - (s["boardEdge"] + slack)
        # the board shows 2px past the cover's edge when shut and its full 12px margin when flat open; between, it pokes
        # past the edge by that rim and never falls short of it
        want = 2 if under >= 0 else 2 + 10 * min(1, -under / s["half"])
        if under >= 0:
            assert s["boardEdge"] <= s["coverEdge"] + 0.5, s
        else:
            assert abs(rim - want) <= 1.0, (rim, want, s)


@pytest.fixture
def page(browser_page):
    page, base = browser_page
    page.base = base
    return page


def test_the_back_board_edge_follows_the_cover_edge_through_the_whole_opening(page) -> None:
    settle(page, "/")
    page.locator(".cover-open").click(no_wait_after=True)
    shots = frames(page)

    check(shots)
    opens = [s["open"] for s in shots if s["coverEdge"] is not None]
    assert opens == sorted(opens) and 0.4 < shots[2]["open"] < 0.6  # ease-in-out: half way at half the time
    # at 75% the cover has crossed 90 degrees and lies over the left half: the board has to be out there with it
    assert shots[3]["coverEdge"] < shots[3]["spine"] - 100 and shots[3]["boardEdge"] < shots[3]["coverEdge"]
    page.clock.run_for(100)
    assert page.evaluate("getComputedStyle(document.querySelector('.nb-back')).clipPath") == "inset(-10px -12px -12px)"


def test_the_back_board_edge_follows_the_cover_edge_through_the_whole_closing(page) -> None:
    settle(page, "/jobs")
    page.evaluate("document.querySelector('[data-home]').click()")
    shots = frames(page)

    check(shots)
    opens = [s["open"] for s in shots]
    assert opens == sorted(opens, reverse=True) and 0.4 < shots[2]["open"] < 0.6
    assert shots[1]["coverEdge"] < shots[1]["spine"]  # at 25% the cover is still lying over the left half
    page.clock.run_for(100)
    shut = page.evaluate("getComputedStyle(document.querySelector('.nb-back')).clipPath")
    assert "calc(50%" in shut  # the stylesheet's shut state again (the driver let go): only the right half shows
