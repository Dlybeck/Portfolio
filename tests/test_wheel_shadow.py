"""The wheel's drop shadow stays down and to the right however far the wheel is turned.

The dial rotates, so a shadow drawn on it would swing round with it. It is drawn on the fixed wrapper instead."""

from __future__ import annotations

import pytest

LAYOUTS = {
    "phone": {"width": 390, "height": 844},
    "desktop": {"width": 1440, "height": 900},
    "short-landscape": {"width": 900, "height": 420},
}
SCHEMES = ["light", "dark"]

READ = """() => {
  const dial = document.querySelector('.wheel-dial');
  const wheel = document.querySelector('.wheel');
  const ring = getComputedStyle(wheel, '::before');
  return {
    dialShadow: getComputedStyle(dial).boxShadow,
    ringShadow: ring.boxShadow,
    ringEvents: ring.pointerEvents,
    ringWidth: parseFloat(ring.width),
    dialWidth: parseFloat(getComputedStyle(dial).width),
  };
}"""


def offsets(shadow: str) -> tuple[float, float]:
    """The x and y offsets of 'rgb(..) 4px 4px 0px 0px'."""
    numbers = [part for part in shadow.replace(",", " ").split() if part.endswith("px")]
    return float(numbers[0][:-2]), float(numbers[1][:-2])


@pytest.mark.browser
@pytest.mark.parametrize("scheme", SCHEMES)
@pytest.mark.parametrize("layout", LAYOUTS, ids=list(LAYOUTS))
def test_the_shadow_stays_down_and_right_when_the_wheel_turns(new_page, live_server_url, layout, scheme) -> None:
    page = new_page(viewport=LAYOUTS[layout], color_scheme=scheme)
    page.goto(live_server_url + "/jobs")
    page.wait_for_selector("#notebook.nb--phone, #notebook.nb--desktop")
    page.wait_for_timeout(600)

    for degrees in (0, 90, 180, 270):
        page.evaluate("(d) => { document.querySelector('.wheel-dial').style.rotate = d + 'deg'; }", degrees)
        state = page.evaluate(READ)

        assert state["dialShadow"] == "none", (degrees, state["dialShadow"])  # the turning part has no shadow
        dx, dy = offsets(state["ringShadow"])  # the fixed ring does, and it is down and to the right
        assert dx > 0 and dy > 0, (degrees, state["ringShadow"])
        assert state["ringEvents"] == "none"  # and it never takes a touch from the dial
        assert abs(state["ringWidth"] - state["dialWidth"]) < 1  # same circle, so the shadow hugs the drawn edge
