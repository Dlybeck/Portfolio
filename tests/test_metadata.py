from html.parser import HTMLParser
import json
import re

from fastapi.testclient import TestClient
import pytest

from core.discovery import PRIMARY_DESCRIPTION, PRIMARY_TITLE, SITE_URL
from core.portfolio import DOCUMENTS


class HeadParser(HTMLParser):
    def __init__(self) -> None:
        super().__init__()
        self.meta: dict[str, str] = {}
        self.links: dict[str, str] = {}
        self.title = ""
        self.structured_data: list[dict[str, object]] = []
        self._in_title = False
        self._json_ld: list[str] | None = None

    def handle_starttag(
        self, tag: str, attrs: list[tuple[str, str | None]]
    ) -> None:
        values = dict(attrs)
        if tag == "meta":
            key = values.get("name") or values.get("property")
            if key:
                self.meta[key] = values.get("content") or ""
        elif tag == "link" and values.get("rel"):
            self.links[values["rel"]] = values.get("href") or ""
        elif tag == "title":
            self._in_title = True
        elif tag == "script" and values.get("type") == "application/ld+json":
            self._json_ld = []

    def handle_data(self, data: str) -> None:
        if self._in_title:
            self.title += data
        if self._json_ld is not None:
            self._json_ld.append(data)

    def handle_endtag(self, tag: str) -> None:
        if tag == "title":
            self._in_title = False
        elif tag == "script" and self._json_ld is not None:
            self.structured_data.append(json.loads("".join(self._json_ld)))
            self._json_ld = None


def parsed_head(html: str) -> HeadParser:
    parser = HeadParser()
    parser.feed(html)
    return parser


def test_home_publishes_the_confirmed_professional_identity(
    client: TestClient,
) -> None:
    response = client.get("/")
    head = parsed_head(response.text)

    assert head.title.strip() == PRIMARY_TITLE
    assert head.meta["description"] == PRIMARY_DESCRIPTION
    assert head.links["canonical"] == f"{SITE_URL}/"
    assert head.meta["og:title"] == PRIMARY_TITLE
    assert head.meta["og:description"] == PRIMARY_DESCRIPTION
    assert head.meta["og:url"] == f"{SITE_URL}/"
    assert head.meta["og:image"] == f"{SITE_URL}/static/images/social/home-board.webp"
    assert head.meta["og:image:width"] == "1200"
    assert head.meta["og:image:height"] == "630"
    assert head.meta["twitter:card"] == "summary_large_image"

    person = next(
        item for item in head.structured_data if item.get("@type") == "Person"
    )
    assert person["name"] == "David Lybeck"
    assert person["jobTitle"] == "Innovation AI Developer"
    assert person["worksFor"] == {
        "@type": "Organization",
        "name": "Denali Advanced Integration",
    }
    assert "August 2025" in person["description"]
    assert person["sameAs"] == [
        "https://github.com/Dlybeck",
        "https://www.linkedin.com/in/davidlybeck/",
    ]


@pytest.mark.parametrize("document", DOCUMENTS, ids=lambda document: document.route)
def test_every_public_destination_has_specific_canonical_social_metadata(
    client: TestClient, document
) -> None:
    response = client.get(document.route)
    head = parsed_head(response.text)

    assert response.status_code == 200
    assert head.title.strip() == f"{document.page_title} | David Lybeck"
    assert head.links["canonical"] == f"{SITE_URL}{document.route}"
    assert head.meta["description"] == document.description
    assert head.meta["og:title"] == head.title.strip()
    assert head.meta["og:description"] == document.description
    assert head.meta["og:url"] == f"{SITE_URL}{document.route}"
    assert head.meta["twitter:title"] == head.title.strip()
    assert head.meta["twitter:description"] == document.description


def test_internal_documents_are_noindex_and_canonicalize_to_public_destinations(
    client: TestClient,
) -> None:
    response = client.get("/_documents/projects/programs")
    head = parsed_head(response.text)

    assert head.meta["robots"] == "noindex, nofollow"
    assert head.links["canonical"] == f"{SITE_URL}/projects/programs"


def test_metadata_excludes_private_and_historical_promotional_claims(
    client: TestClient,
) -> None:
    for route in ("/", "/jobs", "/projects/websites/scribblescan"):
        head = parsed_head(client.get(route).text)
        metadata = json.dumps(
            {
                "meta": head.meta,
                "links": head.links,
                "structured_data": head.structured_data,
            }
        ).lower()

        assert "email" not in metadata
        assert not re.search(r"[\w.+-]+@[\w.-]+\.[a-z]{2,}", metadata)
        assert "industry-leading" not in metadata
        assert "industry leading" not in metadata
        assert "character accuracy" not in metadata
        assert not re.search(r"\b\d{1,3}%", metadata)


def test_social_preview_is_a_public_wide_webp(client: TestClient) -> None:
    response = client.get("/static/images/social/home-board.webp")

    assert response.status_code == 200
    assert response.headers["content-type"] == "image/webp"
    assert len(response.content) > 20_000
