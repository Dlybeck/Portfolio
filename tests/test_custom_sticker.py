"""The custom sticker: a shape and a background colour you can pick, saved with it."""

from __future__ import annotations

import json

import pytest

PHONE = {"width": 360, "height": 740}
DESKTOP = {"width": 1280, "height": 800}
KEY, STYLE_KEY = "nb-your-sticker", "nb-your-sticker-style"
INK = (0x14, 0x1C, 0x2B)
SWATCHES = {"white": "#ffffff", "lemon": "#ffe94d", "pink": "#ff8fcf", "tangerine": "#ffb238", "mint": "#6cf0b0", "sky": "#a5d0fd"}
# a tiny white JPEG, like the stickers saved before shapes existed
OLD_JPEG = "data:image/jpeg;base64,/9j/4AAQSkZJRgABAQEASABIAAD/2wBDAP//////////////////////////////////////////////////////////////////////////////////////wgALCAABAAEBAREA/8QAFBABAAAAAAAAAAAAAAAAAAAAAP/aAAgBAQABPxA="


def luminance(rgb):
    c = [v / 255 for v in rgb]
    c = [x / 12.92 if x <= 0.03928 else ((x + 0.055) / 1.055) ** 2.4 for x in c]
    return 0.2126 * c[0] + 0.7152 * c[1] + 0.0722 * c[2]


def contrast(a, b) -> float:
    hi, lo = sorted((luminance(a), luminance(b)), reverse=True)
    return (hi + 0.05) / (lo + 0.05)


def visit(browser_page, viewport=DESKTOP, storage=None):
    page, base = browser_page
    page.set_viewport_size(viewport)
    if storage:
        page.goto(base + "/")
        page.evaluate("(items) => { for (const [k, v] of Object.entries(items)) localStorage.setItem(k, v); }", storage)
    page.goto(base + "/")
    page.wait_for_selector("#notebook.nb--desktop, #notebook.nb--phone")
    page.wait_for_timeout(500)
    return page


def open_maker(page):
    page.locator(".wd-mine").click()
    page.wait_for_selector("dialog.maker[open]")
    return page.locator("dialog.maker")


def draw(page):
    box = page.locator(".maker canvas").bounding_box()
    page.mouse.move(box["x"] + 60, box["y"] + 90)
    page.mouse.down()
    page.mouse.move(box["x"] + 160, box["y"] + 140, steps=6)
    page.mouse.up()


def test_the_swatch_text_colour_is_readable_on_every_background() -> None:
    for name, hex_ in SWATCHES.items():
        rgb = tuple(int(hex_[i:i + 2], 16) for i in (1, 3, 5))
        assert contrast(INK, rgb) >= 4.5, (name, contrast(INK, rgb))


def test_nothing_changes_until_someone_picks_something(browser_page) -> None:
    page = visit(browser_page)

    classes = page.locator(".wd-mine").get_attribute("class")
    assert "styled" not in classes and "has" not in classes
    assert page.locator(".wd-mine").evaluate("n => getComputedStyle(n).borderStyle") == "dashed"  # the dashed outline, as before
    assert page.locator(".wd-mine .mn-shape").evaluate("n => getComputedStyle(n).maskImage") in ("none", "")
    maker = open_maker(page)
    assert maker.locator('[data-shape-pick="circle"]').get_attribute("aria-pressed") == "true"
    assert maker.locator('[data-bg-pick="white"]').get_attribute("aria-pressed") == "true"
    page.locator('[data-action="cancel"]').click()
    assert page.evaluate("[localStorage.getItem('nb-your-sticker-style'), localStorage.getItem('nb-your-sticker')]") == [None, None]


def test_the_maker_offers_seven_shapes_and_six_colours_with_names(browser_page) -> None:
    page = visit(browser_page)
    maker = open_maker(page)

    assert maker.locator("[data-shape-pick]").evaluate_all("els => els.map(e => e.getAttribute('aria-label'))") == ["Circle", "Rounded square", "Square", "Pentagon", "Hexagon", "Triangle", "Diamond"]
    assert maker.locator("[data-bg-pick]").evaluate_all("els => els.map(e => e.getAttribute('aria-label'))") == [f"{n} background" for n in ("White", "Lemon", "Pink", "Tangerine", "Mint", "Sky")]
    assert maker.locator('[role="group"][aria-label="Shape"]').count() == 1 and maker.locator('[role="group"][aria-label="Background color"]').count() == 1


@pytest.mark.parametrize("shape", ["rounded", "hexagon", "diamond"])
def test_a_drawing_keeps_the_chosen_shape_and_colour_and_they_survive_a_reload(browser_page, shape) -> None:
    page = visit(browser_page)
    maker = open_maker(page)
    maker.locator(f'[data-shape-pick="{shape}"]').click()
    maker.locator('[data-bg-pick="mint"]').click()
    assert page.locator("dialog.maker").get_attribute("data-shape") == shape  # the preview follows
    draw(page)
    page.locator('[data-action="done"]').click()

    sticker = page.locator(".wd-mine")
    assert "styled" in sticker.get_attribute("class") and "has" in sticker.get_attribute("class")
    assert sticker.get_attribute("data-shape") == shape
    assert sticker.evaluate("n => n.style.getPropertyValue('--sticker-bg')") == "#6cf0b0"
    assert json.loads(page.evaluate("localStorage.getItem('nb-your-sticker-style')")) == {"shape": shape, "bg": "mint"}
    assert page.evaluate("localStorage.getItem('nb-your-sticker')").startswith("data:image/png")  # a see-through drawing, so the colour shows behind it
    page.reload()
    page.wait_for_selector("#notebook.nb--desktop")
    page.wait_for_timeout(400)
    assert page.locator(".wd-mine").get_attribute("data-shape") == shape
    assert page.locator(".wd-mine").evaluate("n => n.style.getPropertyValue('--sticker-bg')") == "#6cf0b0"
    maker = open_maker(page)  # and the maker opens on what was picked
    assert maker.locator(f'[data-shape-pick="{shape}"]').get_attribute("aria-pressed") == "true"
    assert maker.locator('[data-bg-pick="mint"]').get_attribute("aria-pressed") == "true"


def test_a_shape_and_colour_alone_make_the_blank_sticker_and_its_words_stay_readable(browser_page) -> None:
    page = visit(browser_page)
    maker = open_maker(page)
    maker.locator('[data-shape-pick="triangle"]').click()
    maker.locator('[data-bg-pick="pink"]').click()
    page.locator('[data-action="done"]').click()

    sticker = page.locator(".wd-mine")
    assert "styled" in sticker.get_attribute("class") and "has" not in sticker.get_attribute("class")
    assert sticker.locator(".mn-shape").evaluate("n => getComputedStyle(n).backgroundColor") == "rgb(255, 143, 207)"
    assert sticker.locator(".mn-shape").evaluate("n => getComputedStyle(n).maskImage").startswith("url(")  # it really is shaped
    colour = sticker.locator(".mn-t").evaluate("n => getComputedStyle(n).color")
    rgb = tuple(int(v) for v in colour[colour.index("(") + 1:colour.index(")")].split(",")[:3])
    assert contrast(rgb, (255, 143, 207)) >= 4.5


def test_older_stickers_with_no_shape_or_colour_still_look_the_same(browser_page) -> None:
    page = visit(browser_page, storage={KEY: OLD_JPEG})

    sticker = page.locator(".wd-mine")
    assert "has" in sticker.get_attribute("class") and "styled" not in sticker.get_attribute("class")
    assert sticker.get_attribute("data-shape") == "circle"
    maker = open_maker(page)
    assert maker.locator('[data-shape-pick="circle"]').get_attribute("aria-pressed") == "true"
    assert maker.locator('[data-bg-pick="white"]').get_attribute("aria-pressed") == "true"


@pytest.mark.parametrize("junk", ["not json", "{}", '{"shape": "dragon", "bg": "plaid"}', '{"shape": 3}', "null", '"star"'])
def test_damaged_saved_styles_fall_back_to_the_original_look(browser_page, junk) -> None:
    page = visit(browser_page, storage={KEY: OLD_JPEG, STYLE_KEY: junk})

    sticker = page.locator(".wd-mine")
    assert "styled" not in sticker.get_attribute("class")
    assert sticker.get_attribute("data-shape") == "circle"


def test_a_half_damaged_style_keeps_what_is_valid(browser_page) -> None:
    page = visit(browser_page, storage={KEY: OLD_JPEG, STYLE_KEY: '{"shape": "hexagon", "bg": "plaid"}'})

    assert page.locator(".wd-mine").get_attribute("data-shape") == "hexagon"
    assert page.locator(".wd-mine").evaluate("n => n.style.getPropertyValue('--sticker-bg')") == "#ffffff"


@pytest.mark.parametrize("retired", ["star", "heart"])
def test_the_retired_shapes_become_a_circle_and_keep_their_colour(browser_page, retired) -> None:
    page = visit(browser_page, storage={KEY: OLD_JPEG, STYLE_KEY: json.dumps({"shape": retired, "bg": "sky"})})

    assert page.locator(".wd-mine").get_attribute("data-shape") == "circle"
    assert page.locator(".wd-mine").evaluate("n => n.style.getPropertyValue('--sticker-bg')") == "#a5d0fd"
    assert page.locator(".wd-mine .mn-shape").evaluate("n => getComputedStyle(n).maskImage").startswith("url(")  # still a shape, not a blank box


def test_taking_it_off_clears_the_picture_and_the_style(browser_page) -> None:
    page = visit(browser_page, storage={KEY: OLD_JPEG, STYLE_KEY: json.dumps({"shape": "hexagon", "bg": "sky"})})
    open_maker(page)
    page.locator('[data-action="off"]').click()

    assert page.evaluate("[localStorage.getItem('nb-your-sticker'), localStorage.getItem('nb-your-sticker-style')]") == [None, None]
    assert "styled" not in page.locator(".wd-mine").get_attribute("class")


def test_the_pickers_work_from_the_keyboard(browser_page) -> None:
    page = visit(browser_page)
    page.locator(".wd-mine").focus()
    page.keyboard.press("Enter")
    page.wait_for_selector("dialog.maker[open]")
    hexagon = page.locator('[data-shape-pick="hexagon"]')
    hexagon.focus()
    page.keyboard.press("Space")
    assert hexagon.get_attribute("aria-pressed") == "true"
    assert hexagon.evaluate("n => getComputedStyle(n).outlineStyle") != "none"  # the focus ring shows
    sky = page.locator('[data-bg-pick="sky"]')
    sky.focus()
    page.keyboard.press("Enter")
    assert sky.get_attribute("aria-pressed") == "true"


def test_the_pickers_are_big_enough_for_a_thumb_and_fit_a_small_phone(browser_page) -> None:
    page = visit(browser_page, PHONE)
    maker = open_maker(page)

    sizes = maker.locator(".maker-opts button").evaluate_all("els => els.map(e => { const r = e.getBoundingClientRect(); return [r.width, r.height, r.right]; })")
    assert len(sizes) == 13
    box = maker.bounding_box()
    for w, h, right in sizes:
        assert w >= 32 and h >= 32  # comfortably over the 24px minimum
        assert right <= box["x"] + box["width"]  # nothing hangs out of the dialog
    assert not page.evaluate("document.documentElement.scrollWidth > innerWidth")
