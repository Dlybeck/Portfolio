import pytest


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

    assert metrics["display"] == "inline-block"
    assert metrics["boxes"] == 1
    assert metrics["width"] <= metrics["parentWidth"] + 1
