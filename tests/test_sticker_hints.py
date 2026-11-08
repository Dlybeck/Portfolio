"""The cover's sticker hint: one sticker at a time plays a quiet preview of its own animation."""

from __future__ import annotations

import re

DESKTOP = {"width": 1280, "height": 800}
PHONE = {"width": 390, "height": 844}

# records every moment a sticker gets (or loses) the .hint class, with the page's own clock
RECORD = """() => {
  window.__hints = [];
  const seen = new WeakSet();
  const watch = new MutationObserver((list) => {
    for (const m of list) {
      const el = m.target;
      if (el.classList.contains('hint') && !seen.has(el)) { seen.add(el); window.__hints.push({ t: Math.round(performance.now()), cls: [...el.classList].find((c) => c.startsWith('wd-') && c !== 'wd-sh') }); }
      if (!el.classList.contains('hint')) seen.delete(el);
    }
  });
  watch.observe(document.querySelector('.nb-book'), { subtree: true, attributes: true, attributeFilter: ['class'] });
}"""


def start(browser_page, viewport=DESKTOP, reduced=False):
    page, base = browser_page
    if reduced:
        page.emulate_media(reduced_motion="reduce")
    page.set_viewport_size(viewport)
    page.clock.install()
    page.goto(base + "/")
    page.wait_for_selector("#notebook.nb--desktop, #notebook.nb--phone")
    page.clock.run_for(500)
    page.evaluate(RECORD)
    return page


def hints(page) -> list:
    return page.evaluate("window.__hints")


def test_one_sticker_at_a_time_plays_a_hint_on_a_slow_steady_cycle(browser_page) -> None:
    page = start(browser_page)
    page.clock.run_for(40_000)

    seen = hints(page)
    assert len(seen) >= 6, seen
    gaps = [b["t"] - a["t"] for a, b in zip(seen, seen[1:])]
    assert all(3500 <= g <= 6500 for g in gaps), gaps  # roughly one every 4 to 6 seconds
    assert len({h["cls"] for h in seen}) >= 6  # they take turns
    # never two at once
    assert page.evaluate("document.querySelectorAll('.cover-front .hint').length") <= 1


def test_a_hint_never_runs_the_real_action_or_moves_anything(browser_page) -> None:
    page = start(browser_page)
    before = page.evaluate("""() => ({ name: document.querySelector('.wd-name').dataset.hand, now: document.querySelector('.wd-now b').textContent,
      dialog: !!document.querySelector('dialog[open]'), closed: document.getElementById('notebook').classList.contains('is-closed'), path: location.pathname,
      boxes: [...document.querySelectorAll('.cover-front .wd')].map((e) => [e.offsetLeft, e.offsetTop, e.offsetWidth, e.offsetHeight]) })""")
    page.clock.run_for(40_000)
    after = page.evaluate("""() => ({ name: document.querySelector('.wd-name').dataset.hand, now: document.querySelector('.wd-now b').textContent,
      dialog: !!document.querySelector('dialog[open]'), closed: document.getElementById('notebook').classList.contains('is-closed'), path: location.pathname,
      boxes: [...document.querySelectorAll('.cover-front .wd')].map((e) => [e.offsetLeft, e.offsetTop, e.offsetWidth, e.offsetHeight]) })""")

    assert before == after  # same hand, same pill, no dialog, still shut, same address, nothing shifted by a pixel
    assert len(hints(page)) >= 6


def test_the_hint_animations_use_only_transform_and_opacity_properties(browser_page) -> None:
    page = start(browser_page)
    props = page.evaluate("""() => {
      const out = {};
      for (const sheet of document.styleSheets) {
        let rules; try { rules = sheet.cssRules; } catch { continue; }
        for (const r of rules) if (r.type === CSSRule.KEYFRAMES_RULE && r.name.startsWith('hint-')) {
          out[r.name] = [...new Set([...r.cssRules].flatMap((k) => [...k.style]))];
        }
      }
      return out;
    }""")
    allowed = {"opacity", "translate", "scale", "rotate", "transform"}
    assert len(props) >= 8, props
    for name, used in props.items():
        assert set(used) <= allowed, (name, used)


def test_touching_any_sticker_stops_the_hints_for_the_rest_of_the_visit(browser_page) -> None:
    page = start(browser_page)
    page.clock.run_for(8_000)
    assert len(hints(page)) >= 1
    page.locator(".wd-now").click()
    page.evaluate(RECORD)  # start counting again from here
    page.clock.run_for(40_000)
    assert hints(page) == []


def test_a_keyboard_press_on_a_sticker_also_stops_the_hints(browser_page) -> None:
    page = start(browser_page)
    page.locator(".wd-now").focus()
    page.keyboard.press("Enter")
    page.evaluate(RECORD)
    page.clock.run_for(30_000)
    assert hints(page) == []


def test_the_hints_stop_once_the_cover_is_open(browser_page) -> None:
    page = start(browser_page)
    page.clock.run_for(4_000)
    page.locator(".cover-open").click(no_wait_after=True)
    page.clock.run_for(2_000)
    page.evaluate(RECORD)
    page.clock.run_for(30_000)
    assert hints(page) == []
    assert page.locator(".cover-front .hint").count() == 0


def test_with_reduced_motion_there_are_no_hints(browser_page) -> None:
    page = start(browser_page, reduced=True)
    page.clock.run_for(40_000)
    assert hints(page) == []


def test_the_hints_wait_while_the_tab_is_hidden_and_come_back_after(browser_page) -> None:
    page = start(browser_page)
    page.evaluate("""() => { Object.defineProperty(document, 'hidden', { configurable: true, get: () => true });
      document.dispatchEvent(new Event('visibilitychange')); }""")
    page.clock.run_for(30_000)
    assert hints(page) == []
    page.evaluate("""() => { Object.defineProperty(document, 'hidden', { configurable: true, get: () => false });
      document.dispatchEvent(new Event('visibilitychange')); }""")
    page.clock.run_for(15_000)
    assert len(hints(page)) >= 1


def test_the_hints_wait_while_the_page_is_scrolling(browser_page) -> None:
    page = start(browser_page)
    # keep a scroll going right through the first few ticks
    for _ in range(14):
        page.evaluate("window.dispatchEvent(new Event('scroll'))")
        page.clock.run_for(500)
    assert hints(page) == []
    page.clock.run_for(15_000)
    assert len(hints(page)) >= 1


def test_phones_get_the_same_hints(browser_page) -> None:
    page = start(browser_page, PHONE)
    page.clock.run_for(20_000)
    assert len(hints(page)) >= 3


def test_every_hinted_sticker_has_its_own_animation_defined() -> None:
    from pathlib import Path

    css = (Path(__file__).resolve().parent.parent / "static/css/notebook/stickers.css").read_text()
    js = (Path(__file__).resolve().parent.parent / "static/js/notebook/stickers/hints.js").read_text()
    classes = re.findall(r'\["(\.wd-[\w-]+)", \d+\]', js)
    assert len(classes) == 7
    for cls in classes:
        assert f"{cls}.hint" in css, cls
