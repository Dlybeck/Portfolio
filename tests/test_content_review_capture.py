import argparse

import pytest

from scripts.capture_content_review import VIEWPORTS, parse_named_route, themed_url


def test_review_matrix_covers_portrait_landscape_and_short_viewports() -> None:
    assert VIEWPORTS == {
        "desktop": {"width": 1440, "height": 900},
        "short-laptop": {"width": 1024, "height": 600},
        "phone": {"width": 390, "height": 844},
        "narrow-phone": {"width": 320, "height": 568},
        "phone-landscape": {"width": 568, "height": 320},
        "tablet-landscape": {"width": 844, "height": 390},
    }


@pytest.mark.parametrize(
    ("value", "expected"),
    (
        ("home=/", ("home", "/")),
        ("work=/jobs", ("work", "/jobs")),
        ("nested=/#ScribbleScan", ("nested", "/#ScribbleScan")),
    ),
)
def test_parse_named_route(value: str, expected: tuple[str, str]) -> None:
    assert parse_named_route(value) == expected


@pytest.mark.parametrize(
    "value",
    ("/jobs", "work", "work=jobs", "Work=/jobs", "work=//jobs"),
)
def test_parse_named_route_rejects_ambiguous_values(value: str) -> None:
    with pytest.raises(argparse.ArgumentTypeError):
        parse_named_route(value)


def test_themed_url_preserves_routes_queries_and_fragments() -> None:
    origin = "http://127.0.0.1:8098"

    assert themed_url(origin, "/", "canonical") == (
        "http://127.0.0.1:8098/?theme=canonical"
    )
    assert themed_url(origin, "/jobs?review=1", "clouds") == (
        "http://127.0.0.1:8098/jobs?review=1&theme=clouds"
    )
    assert themed_url(origin, "/#3D Printing", "vinyl") == (
        "http://127.0.0.1:8098/?theme=vinyl#3D%20Printing"
    )
