"""A turning leaf carries the real, complete page on its face (content, numbers, folio, corner fold), so nothing pops in once it lands."""

from __future__ import annotations

import pytest

# Shared by the in-page scripts: the boxes of everything on a page (so wrapping and numbers match), and a token per folio / corner fold.
HELPERS = """
const boxes = (root) => [...root.querySelectorAll('.page *')].filter((e) => !e.closest('model-viewer, .model-ph')).map((e) => [e.tagName, e.offsetWidth, e.offsetHeight]);
const token = (n) => {
  const kind = /(^| )(nb|face)-pn( |$)/.test(n.className) ? 'pn' : 'ear';
  const where = ['lft', 'rgt', 'prev', 'next'].find((c) => n.classList.contains(c));
  return kind + '.' + where + ':' + (kind === 'pn' ? n.textContent : '');
};
"""

# part way through the turn (pictures have had a moment to load): the face that is about to land
FACE = "(face) => {" + HELPERS + """
  const faceEl = document.querySelector('.nb-book .nb-leaf.is-flying').querySelector(face);
  return { boxes: boxes(faceEl), chrome: [...faceEl.querySelectorAll('.face-pn, .face-ear')].map(token).sort() };
}"""

# after it has landed: the live page on that side and the folio / corners showing for it
LIVE = "(side) => {" + HELPERS + """
  const book = document.querySelector('.nb-book');
  const mine = (n) => (side === 'l' ? n.classList.contains('lft') || n.classList.contains('prev') : n.classList.contains('rgt') || n.classList.contains('next'));
  const shown = (n) => getComputedStyle(n).visibility !== 'hidden' && getComputedStyle(n).display !== 'none';
  const chrome = [...book.querySelectorAll(':scope > .nb-pn, :scope > .nb-ear')].filter((n) => shown(n) && mine(n)).map(token).sort();
  return { boxes: boxes(book.querySelector(`.nb-page.${side} .nb-in`)), chrome };
}"""

CASES = [
    ("forward off the first spread", "/#contents", ".nb-ear.next", ".face.back", "l"),
    ("forward, a split spread", "/jobs", ".nb-ear.next", ".face.back", "l"),
    ("back onto a project", "/projects/nba_predictions", ".nb-ear.prev", ".face.back", "r"),
    ("back onto the work page", "/education/college", ".nb-ear.prev", ".face.back", "r"),
    ("back onto the first spread", "/projects/websites/scribblescan", ".nb-ear.prev", ".face.back", "r"),
]


@pytest.mark.parametrize("label,route,ear,face,side", CASES, ids=[c[0] for c in CASES])
def test_the_desktop_leafs_landing_face_is_the_page_that_appears(browser_page, label, route, ear, face, side) -> None:
    page, base = browser_page
    page.set_viewport_size({"width": 1440, "height": 900})
    page.goto(base + route)
    page.wait_for_selector("#notebook.nb--desktop")
    page.wait_for_timeout(900)

    page.evaluate(f"document.querySelector('{ear}').click()")
    page.wait_for_timeout(350)
    flying = page.evaluate(FACE, face)
    page.wait_for_timeout(1000)
    landed = page.evaluate(LIVE, side)

    assert flying["boxes"], "the leaf's face had no page on it"
    assert flying["boxes"] == landed["boxes"]  # same boxes: same wrapping, the numbers beside entries, the rows and controls
    assert flying["chrome"] == landed["chrome"]  # and the folio and corner fold it carried are the ones that show


def test_a_phone_page_turning_in_carries_its_folio_and_corners(mobile_browser_page) -> None:
    page, base = mobile_browser_page
    page.goto(base + "/projects/nba_predictions")
    page.wait_for_selector("#notebook.nb--phone")
    page.wait_for_timeout(900)

    page.evaluate(
        "() => {" + HELPERS + """
        const b = document.querySelector('.nb-book');
        const o = { bubbles: true, isPrimary: true, pointerId: 1, pointerType: 'touch', clientY: 400 };
        b.dispatchEvent(new PointerEvent('pointerdown', { ...o, clientX: 100 }));
        b.dispatchEvent(new PointerEvent('pointerup', { ...o, clientX: 250 }));
      }"""
    )
    page.wait_for_timeout(350)
    face = page.evaluate(
        "() => {" + HELPERS + """
        const f = document.querySelector('.nb-book .nb-leaf.is-flying .face.front');
        return { boxes: boxes(f), chrome: [...f.querySelectorAll('.face-pn, .face-ear')].map(token).sort() };
      }"""
    )
    page.wait_for_timeout(1000)
    live = page.evaluate(
        "() => {" + HELPERS + """
        const b = document.querySelector('.nb-book');
        const shown = (n) => getComputedStyle(n).display !== 'none';
        return { boxes: boxes(b.querySelector('.nb-page.one .nb-in')), chrome: [...b.querySelectorAll(':scope > .nb-pn.rgt, :scope > .nb-ear')].filter(shown).map(token).sort() };
      }"""
    )
    assert any(c == "pn.rgt:p.4 of 13" for c in face["chrome"]), face["chrome"]
    assert face["chrome"] == live["chrome"]
    assert face["boxes"] == live["boxes"]
