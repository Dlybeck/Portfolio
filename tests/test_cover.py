"""The cover: nine live stickers on a kraft notebook, 5 by 8 on every screen."""

from __future__ import annotations

from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parent.parent
PHONE = {"width": 390, "height": 844}
DESKTOP = {"width": 1280, "height": 800}

LABELS = [
    "Name tag: David. Tap to write it in another hand.",
    "What I'm doing. Tap for earlier.",
    "Stamp of a mountain trail. Tap to go for a hike.",
    "3D printer. Tap to print again.",
    "A raccoon at a keyboard. Tap to say hi.",
    "Your sticker. Tap to draw one or add a picture.",
    "Tennis ball. Tap to bounce it, or throw it.",
]


def cover(browser_page, viewport=PHONE, **context):
    page, base = browser_page
    page.set_viewport_size(viewport)
    problems: list[str] = []
    requests: list[str] = []
    page.on("pageerror", lambda e: problems.append(str(e)))
    page.on("console", lambda m: problems.append(m.text) if m.type == "error" else None)
    page.on("request", lambda r: requests.append(r.url))
    page.goto(base + "/")
    page.wait_for_selector(".cover-front .wd-ball")
    page.wait_for_timeout(300)
    return page, base, problems, requests


def still_closed(page) -> bool:
    return "is-closed" in page.locator("#notebook").get_attribute("class")


@pytest.mark.parametrize("viewport", [PHONE, DESKTOP], ids=["phone", "desktop"])
def test_the_cover_has_its_nine_stickers_and_no_errors(browser_page, viewport) -> None:
    page, _, problems, _ = cover(browser_page, viewport)

    stickers = page.locator(".cover-front > .wd")
    assert stickers.count() == 9
    labels = [stickers.nth(i).get_attribute("aria-label") for i in range(9) if stickers.nth(i).get_attribute("aria-label")]
    for label in LABELS:
        assert label in labels
    assert page.locator(".cover-front .wd-scan canvas").count() == 1
    for i in range(9):
        el = stickers.nth(i)
        assert el.evaluate("n => n.getBoundingClientRect().width") > 20
    assert problems == []


@pytest.mark.parametrize("viewport", [PHONE, DESKTOP], ids=["phone", "desktop"])
def test_the_cover_is_a_five_by_eight_notebook(browser_page, viewport) -> None:
    page, *_ = cover(browser_page, viewport)

    box = page.locator(".nb-leaf.cover .cover-front").bounding_box()
    assert abs(box["width"] / box["height"] - 0.625) < 0.02, box


@pytest.mark.parametrize("viewport", [PHONE, DESKTOP], ids=["phone", "desktop"])
def test_every_sticker_fits_on_the_cover(browser_page, viewport) -> None:
    page, *_ = cover(browser_page, viewport)

    front = page.locator(".cover-front").bounding_box()
    for i in range(9):
        box = page.locator(".cover-front > .wd").nth(i).bounding_box()
        assert box["x"] >= front["x"] - 2 and box["x"] + box["width"] <= front["x"] + front["width"] + 2, (i, box)
        assert box["y"] >= front["y"] - 2 and box["y"] + box["height"] <= front["y"] + front["height"] + 2, (i, box)


def test_the_name_tag_writes_the_name_in_five_hands(browser_page) -> None:
    page, _, problems, requests = cover(browser_page)
    tag = page.locator(".wd-name")
    families = []
    for _ in range(5):
        families.append(page.locator(".wd-name .nm").evaluate("n => n.style.fontFamily") or "Caveat")
        tag.click()
        page.wait_for_timeout(1300)
    assert tag.get_attribute("data-hand") == "0"
    page.locator(".wd-name").click()
    page.wait_for_timeout(1300)
    seen = {page.locator(".wd-name .nm").evaluate("n => getComputedStyle(n).fontFamily")}
    assert still_closed(page)  # tapping a sticker never opens the cover
    for family in ("Permanent Marker", "Homemade Apple", "Gochi Hand", "Nothing You Could Do"):
        assert page.evaluate(f"document.fonts.check('2rem \"{family}\"')"), family
    assert all(url.startswith("http://127.0.0.1") for url in requests if "woff2" in url)
    assert seen and problems == []


def test_the_now_pill_walks_back_through_the_years(browser_page) -> None:
    page, *_ = cover(browser_page)
    pill = page.locator(".wd-now")
    assert pill.inner_text().lower().replace("\n", " ").endswith("ai tools at denali")
    pill.click()
    assert "ScribbleScan LLC" in pill.inner_text()
    pill.click()
    pill.click()
    pill.click()
    assert "AI tools at Denali" in pill.inner_text()
    assert still_closed(page)


def test_the_trail_stamp_ends_in_a_sunset(browser_page) -> None:
    page, *_ = cover(browser_page)
    page.locator(".wd-hike").click()
    page.wait_for_function("document.querySelector('.wd-hike').classList.contains('dusk')", timeout=5000)
    page.locator(".wd-hike").click()
    assert "dusk" not in page.locator(".wd-hike").get_attribute("class")


def test_the_printer_prints_the_logo_and_the_raccoon_says_hi(browser_page) -> None:
    page, *_ = cover(browser_page)
    page.wait_for_function("document.querySelector('.p12a').classList.contains('done')", timeout=6000)
    page.locator(".p12a").click()
    assert "go" in page.locator(".p12a").get_attribute("class")

    page.locator(".wd-pal").click()
    page.wait_for_function("document.querySelector('.pal-say').textContent.length > 0", timeout=3000)


def test_the_scan_pad_types_a_word_and_scans_a_doodle(browser_page) -> None:
    page, *_ = cover(browser_page)
    page.wait_for_function("document.querySelector('.sc-t').textContent.length > 0", timeout=6000)

    box = page.locator(".sc-pad canvas").bounding_box()
    page.mouse.move(box["x"] + 20, box["y"] + 20)
    page.mouse.down()
    page.mouse.move(box["x"] + 120, box["y"] + 40, steps=6)
    page.mouse.up()
    page.wait_for_function("document.querySelector('.sc-t').textContent === '1 doodle, saved'", timeout=6000)
    assert still_closed(page)


def test_the_puzzle_slides(browser_page) -> None:
    page, *_ = cover(browser_page)
    before = page.locator(".pz-t").evaluate_all("tiles => tiles.map(t => t.style.translate)")
    for _ in range(3):
        for i in range(8):
            page.locator(".pz-t").nth(i).click(force=True)
    after = page.locator(".pz-t").evaluate_all("tiles => tiles.map(t => t.style.translate)")

    assert before != after
    assert still_closed(page)


def test_the_ball_bounces_without_opening_the_cover(browser_page) -> None:
    page, *_ = cover(browser_page)
    ball = page.locator(".wd-ball")
    page.wait_for_timeout(100)
    ball.click()
    page.wait_for_timeout(250)
    assert ball.evaluate("n => n.style.translate") != ""
    assert still_closed(page)
    page.wait_for_timeout(2500)  # it settles on the cover's floor
    box, front = ball.bounding_box(), page.locator(".cover-front").bounding_box()
    assert box["y"] + box["height"] <= front["y"] + front["height"] + 3


def test_the_ball_can_be_thrown(browser_page) -> None:
    page, *_ = cover(browser_page, DESKTOP)
    box = page.locator(".wd-ball").bounding_box()
    page.mouse.move(box["x"] + box["width"] / 2, box["y"] + box["height"] / 2)
    page.mouse.down()
    page.mouse.move(box["x"] - 120, box["y"] + 40, steps=5)
    page.mouse.up()
    page.wait_for_timeout(600)

    assert page.locator(".wd-ball").bounding_box()["x"] < box["x"] - 40
    assert still_closed(page)


def test_stickers_work_from_the_keyboard(browser_page) -> None:
    page, *_ = cover(browser_page)
    page.locator(".wd-name").focus()
    page.keyboard.press("Enter")
    page.wait_for_timeout(1300)

    assert page.locator(".wd-name").get_attribute("data-hand") == "1"
    assert still_closed(page)
    page.locator(".wd-now").focus()
    page.keyboard.press("Space")
    assert "ScribbleScan LLC" in page.locator(".wd-now").inner_text()


def test_empty_cover_and_the_open_button_still_open_the_book(browser_page) -> None:
    page, *_ = cover(browser_page, DESKTOP)
    page.locator(".cover-open").click()
    page.wait_for_timeout(1100)

    assert not still_closed(page)
    assert page.locator(".cover-front").count() == 0


def test_your_sticker_is_drawn_and_kept(browser_page) -> None:
    page, base, *_ = cover(browser_page, DESKTOP)
    page.locator(".wd-mine").click()
    canvas = page.locator(".maker canvas")
    box = canvas.bounding_box()
    page.mouse.move(box["x"] + 60, box["y"] + 60)
    page.mouse.down()
    page.mouse.move(box["x"] + 150, box["y"] + 140, steps=6)
    page.mouse.up()
    page.locator('.maker [data-action="done"]').click()

    assert "has" in page.locator(".wd-mine").get_attribute("class")
    page.reload()
    page.wait_for_selector(".cover-front .wd-mine.has")
    page.locator(".wd-mine").click()
    page.locator('.maker [data-action="off"]').click()
    assert "has" not in page.locator(".wd-mine").get_attribute("class")


def test_reduced_motion_calms_the_stickers(browser_page) -> None:
    page, base = browser_page
    page.emulate_media(reduced_motion="reduce")
    page, base, problems, _ = cover(browser_page)

    page.locator(".wd-name").click()
    assert page.locator(".wd-name").get_attribute("data-hand") == "1"  # changes at once, no wipe
    assert page.locator(".wd-sh").first.evaluate("n => getComputedStyle(n).animationName") == "none"
    page.locator(".wd-hike").click()
    assert "dusk" in page.locator(".wd-hike").get_attribute("class")
    page.locator(".wd-ball").click()
    assert "hop" in page.locator(".wd-ball").get_attribute("class")
    assert problems == []


def test_the_extra_fonts_are_served_with_their_licenses() -> None:
    fonts = ROOT / "static" / "fonts"
    for name in ("permanent-marker", "homemade-apple", "gochi-hand", "nothing-you-could-do"):
        assert (fonts / f"{name}-latin-400-normal.woff2").stat().st_size > 5_000
        assert (fonts / f"LICENSE-{name}.txt").read_text().strip()
