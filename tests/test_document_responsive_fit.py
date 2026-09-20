import pytest


DOCUMENT_ACTION_ROUTES = (
    "/projects/programs",
    "/projects/websites/this_website",
    "/projects/websites/scribblescan",
)
DOCUMENT_ACTION_THEMES = (
    "canonical",
    "clouds",
    "islands",
    "lily",
    "planets",
    "postcards",
    "vinyl",
)
DOCUMENT_ACTION_WIDTHS = (240, 275, 320, 342, 381, 513, 600, 601, 716, 882, 900)


def action_geometry(page) -> dict[str, object]:
    return page.locator("html").evaluate(
        """() => {
            const actions = [...document.querySelectorAll(
                '.internal-link:not(.plain-internal-link), .external-btn'
            )];
            const boxes = actions.map((element) => {
                const rect = element.getBoundingClientRect();
                const parent = element.parentElement.getBoundingClientRect();
                return {
                    text: element.textContent.trim(),
                    left: rect.left,
                    right: rect.right,
                    top: rect.top,
                    bottom: rect.bottom,
                    width: rect.width,
                    height: rect.height,
                    parentLeft: parent.left,
                    parentRight: parent.right,
                    clientRects: element.getClientRects().length,
                };
            });
            const overlaps = [];
            for (let left = 0; left < boxes.length; left += 1) {
                for (let right = left + 1; right < boxes.length; right += 1) {
                    const a = boxes[left];
                    const b = boxes[right];
                    const overlapX = Math.min(a.right, b.right) - Math.max(a.left, b.left);
                    const overlapY = Math.min(a.bottom, b.bottom) - Math.max(a.top, b.top);
                    if (overlapX > 1 && overlapY > 1) overlaps.push([a.text, b.text]);
                }
            }
            return {
                boxes,
                overlaps,
                clientWidth: document.documentElement.clientWidth,
                scrollWidth: document.documentElement.scrollWidth,
            };
        }"""
    )


def test_document_actions_follow_one_intrinsic_layout_contract(browser_page) -> None:
    page, origin = browser_page

    for theme in DOCUMENT_ACTION_THEMES:
        for route in DOCUMENT_ACTION_ROUTES:
            for width in DOCUMENT_ACTION_WIDTHS:
                page.set_viewport_size({"width": width, "height": 720})
                page.goto(
                    f"{origin}/_documents{route}?theme={theme}",
                    wait_until="domcontentloaded",
                )
                metrics = action_geometry(page)
                assert metrics["boxes"], (theme, route, width)
                assert metrics["scrollWidth"] <= metrics["clientWidth"] + 1, (
                    theme,
                    route,
                    width,
                    metrics,
                )
                assert not metrics["overlaps"], (theme, route, width, metrics)
                for box in metrics["boxes"]:
                    assert box["clientRects"] == 1, (theme, route, width, box)
                    assert box["width"] >= 44, (theme, route, width, box)
                    assert box["height"] >= 44, (theme, route, width, box)
                    assert box["left"] >= box["parentLeft"] - 1, (
                        theme,
                        route,
                        width,
                        box,
                    )
                    assert box["right"] <= box["parentRight"] + 1, (
                        theme,
                        route,
                        width,
                        box,
                    )


@pytest.mark.parametrize("width", (320, 390, 1440))
@pytest.mark.parametrize(
    "route",
    ("/jobs", "/projects/websites/scribblescan"),
)
def test_canonical_padded_documents_do_not_overflow_horizontally(
    browser_page,
    route: str,
    width: int,
) -> None:
    page, origin = browser_page
    height = 900 if width > 600 else 844
    page.set_viewport_size({"width": width, "height": height})
    page.goto(f"{origin}{route}?theme=canonical", wait_until="domcontentloaded")

    document = page.frame_locator(".mini-window")
    document.locator("#location").wait_for()
    dimensions = document.locator("html").evaluate(
        """element => ({
            clientWidth: element.clientWidth,
            scrollWidth: element.scrollWidth,
        })"""
    )

    assert dimensions["scrollWidth"] <= dimensions["clientWidth"] + 1


def test_narrow_scribblescan_action_renders_as_one_button_box(
    browser_page,
) -> None:
    page, origin = browser_page
    page.set_viewport_size({"width": 320, "height": 568})
    page.goto(
        f"{origin}/projects/websites/scribblescan?theme=canonical",
        wait_until="domcontentloaded",
    )

    action = page.frame_locator(".mini-window").get_by_role(
        "link", name="View the preserved demo"
    )
    metrics = action.evaluate(
        """element => ({
            display: getComputedStyle(element).display,
            boxes: element.getClientRects().length,
            width: element.getBoundingClientRect().width,
            parentWidth: element.parentElement.getBoundingClientRect().width,
        })"""
    )

    assert metrics["display"] == "flex"
    assert metrics["boxes"] == 1
    assert metrics["width"] >= 44
    assert metrics["width"] <= metrics["parentWidth"] + 1


@pytest.mark.parametrize("width", (320, 390))
@pytest.mark.parametrize(
    "theme",
    ("canonical", "clouds", "islands", "lily", "planets", "postcards", "vinyl"),
)
def test_website_version_actions_do_not_overlap_on_phones(
    browser_page,
    theme: str,
    width: int,
) -> None:
    page, origin = browser_page
    page.set_viewport_size({"width": width, "height": 844})
    page.goto(
        f"{origin}/projects/websites/this_website?theme={theme}",
        wait_until="domcontentloaded",
    )

    document = page.frame_locator(".mini-window")
    document.locator("#location").wait_for()
    actions = document.locator(".document-actions > .internal-link")
    expect_count = 3
    assert actions.count() == expect_count
    boxes = [actions.nth(index).bounding_box() for index in range(expect_count)]
    assert all(box is not None for box in boxes)

    for previous, current in zip(boxes, boxes[1:]):
        assert previous is not None
        assert current is not None
        assert previous["y"] + previous["height"] <= current["y"] + 1
