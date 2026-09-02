"""Exercise every visible external anchor in the rendered portfolio documents."""

from __future__ import annotations

import asyncio
from html.parser import HTMLParser
from pathlib import Path
import sys

import httpx
from fastapi.testclient import TestClient

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from main import app


DOCUMENT_ROUTES = (
    "/jobs",
    "/education/college",
    "/education/early_education",
    "/education/agile_report",
    "/hobbies/tennis",
    "/hobbies/gaming",
    "/hobbies/3d_printing/puzzles",
    "/hobbies/3d_printing/other_models",
    "/projects/programs",
    "/projects/nba_predictions",
    "/projects/websites/digital_planner",
    "/projects/websites/scribblescan",
    "/projects/websites/this_website",
    "/projects/websites/this_website/v1",
    "/projects/websites/this_website/v2",
    "/projects/websites/this_website/v3",
)


class AnchorCollector(HTMLParser):
    def __init__(self) -> None:
        super().__init__()
        self.links: set[str] = set()

    def handle_starttag(
        self, tag: str, attrs: list[tuple[str, str | None]]
    ) -> None:
        if tag != "a":
            return
        href = dict(attrs).get("href")
        if href and href.startswith(("https://", "http://")):
            self.links.add(href)


def visible_external_links() -> list[str]:
    collector = AnchorCollector()
    with TestClient(app, base_url="http://testserver") as client:
        for route in DOCUMENT_ROUTES:
            response = client.get(route)
            response.raise_for_status()
            collector.feed(response.text)
    return sorted(collector.links)


async def check_link(
    client: httpx.AsyncClient, limiter: asyncio.Semaphore, link: str
) -> tuple[str, str]:
    async with limiter:
        try:
            response = await client.get(link)
        except httpx.HTTPError as error:
            return link, f"ERROR {type(error).__name__}"
        return link, str(response.status_code)


async def main() -> int:
    links = visible_external_links()
    limits = httpx.Limits(max_connections=6, max_keepalive_connections=3)
    timeout = httpx.Timeout(15, connect=8)
    headers = {"User-Agent": "DavidLybeckPortfolio-LinkAudit/1.0"}
    async with httpx.AsyncClient(
        follow_redirects=True,
        headers=headers,
        limits=limits,
        timeout=timeout,
    ) as client:
        limiter = asyncio.Semaphore(6)
        results = await asyncio.gather(
            *(check_link(client, limiter, link) for link in links)
        )

    definite_failures = 0
    for link, result in results:
        print(f"{result:>24}  {link}")
        if result in {"404", "410", "451"}:
            definite_failures += 1

    print(f"Checked {len(results)} unique visible external links")
    return 1 if definite_failures else 0


if __name__ == "__main__":
    raise SystemExit(asyncio.run(main()))
