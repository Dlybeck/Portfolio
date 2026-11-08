"""The brown back board stays under the cover's free edge for the whole opening and closing (desktop).

The cover swings with rotateY and perspective, so its edge follows cos(angle), not the easing. swing.js drives the cover,
the book's slide and the board's clip from one angle each frame. Time is controlled with Playwright's fake clock, so the
frames are exact and repeatable.
"""

from __future__ import annotations


import pytest

SIZES = [(1440, 900), (1024, 768), (1920, 1080)]  # the board has to track the cover at every desktop size
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
  const parts = clip.startsWith('inset(') ? clip.slice(6, -1).split(' ') : ['0'];
  const px = (t) => (t.endsWith('%') ? (parseFloat(t) * r.width) / 100 : parseFloat(t));
  const inset = parts.length === 4 ? px(parts[3]) : parts.length === 1 ? px(parts[0]) : px(parts[1]);
  const m = leaf ? getComputedStyle(leaf).transform : 'none';
  const cos = m.startsWith('matrix3d') ? parseFloat(m.slice(9).split(',')[0]) : 1;
  return {
    spine, half: leaf ? leaf.offsetWidth : b.width / 2, open: Math.acos(Math.max(-1, Math.min(1, cos))) / Math.PI,
    coverEdge: cover ? (cos >= 0 ? cover.right : cover.left) : null,
    boardEdge: r.left + inset,
  };
}"""


def settle(page, route, size):
    page.clock.install(time=0)
    page.set_viewport_size({"width": size[0], "height": size[1]})
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
    """The back board and the cover are one board: once the cover is over the left half the board's edge IS the cover's edge."""
    for s in shots:
        if s["coverEdge"] is None:  # the leaf is gone at the end of an opening: the board is the whole book
            continue
        under = s["coverEdge"] - s["spine"]
        # the clip also opens up to the board's 12px rim as the cover lands, so the board's hard shadow is not cut off at its edge
        slack = 12 * min(1, max(0, -under / s["half"]))
        edge = s["boardEdge"] + slack
        if under >= 0:
            assert abs(edge - s["spine"]) <= 1.0, s  # shut side: flush at the spine, under the cover
        else:
            assert abs(edge - s["coverEdge"]) <= 1.5, (edge, s)


@pytest.fixture
def page(browser_page):
    page, base = browser_page
    page.base = base
    return page


@pytest.mark.parametrize("size", SIZES)
def test_the_back_board_edge_follows_the_cover_edge_through_the_whole_opening(page, size) -> None:
    settle(page, "/", size)
    page.locator(".cover-open").click(no_wait_after=True)
    shots = frames(page)

    check(shots)
    opens = [s["open"] for s in shots if s["coverEdge"] is not None]
    assert opens == sorted(opens) and 0.4 < shots[2]["open"] < 0.6  # ease-in-out: half way at half the time
    # at 75% the cover has crossed 90 degrees and lies over the left half: the board has to be out there with it
    assert shots[3]["coverEdge"] < shots[3]["spine"] - 100 and shots[3]["boardEdge"] < shots[3]["spine"] - 100
    page.clock.run_for(100)
    assert page.evaluate("getComputedStyle(document.querySelector('.nb-back')).clipPath") == "inset(-12px)"


@pytest.mark.parametrize("size", SIZES)
def test_the_back_board_edge_follows_the_cover_edge_through_the_whole_closing(page, size) -> None:
    settle(page, "/jobs", size)
    page.evaluate("document.querySelector('[data-home]').click()")
    shots = frames(page)

    check(shots)
    opens = [s["open"] for s in shots]
    assert opens == sorted(opens, reverse=True) and 0.4 < shots[2]["open"] < 0.6
    assert shots[1]["coverEdge"] < shots[1]["spine"]  # at 25% the cover is still lying over the left half
    page.clock.run_for(100)
    shut = page.evaluate("getComputedStyle(document.querySelector('.nb-back')).clipPath")
    assert "50%" in shut  # the stylesheet's shut state again (the driver let go): only the cover's half shows, flush at the spine
