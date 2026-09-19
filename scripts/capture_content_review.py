#!/usr/bin/env python3
"""Capture public content routes across themes and review viewports."""

from __future__ import annotations

import argparse
import base64
import json
import os
import re
import subprocess
from pathlib import Path
from urllib.parse import quote, urlparse

from playwright.sync_api import Browser, Page, sync_playwright

VIEWPORTS = {
    "desktop": {"width": 1440, "height": 900},
    "phone": {"width": 390, "height": 844},
    "narrow-phone": {"width": 320, "height": 568},
}


def parse_named_route(value: str) -> tuple[str, str]:
    label, separator, route = value.partition("=")
    if not separator or not re.fullmatch(r"[a-z0-9][a-z0-9-]*", label):
        raise argparse.ArgumentTypeError("Use label=/route for every route.")
    if not route.startswith("/") or route.startswith("//"):
        raise argparse.ArgumentTypeError("Routes must start with one slash.")
    return label, route


def themed_url(origin: str, route: str, theme: str) -> str:
    path, marker, fragment = route.partition("#")
    separator = "&" if "?" in path else "?"
    suffix = f"#{quote(fragment)}" if marker else ""
    return f"{origin}{path}{separator}theme={theme}{suffix}"


def source_state(root: Path) -> dict[str, object]:
    revision = subprocess.run(
        ["git", "rev-parse", "HEAD"],
        cwd=root,
        check=True,
        capture_output=True,
        text=True,
    ).stdout.strip()
    dirty = subprocess.run(
        ["git", "status", "--short"],
        cwd=root,
        check=True,
        capture_output=True,
        text=True,
    ).stdout.splitlines()
    return {"revision": revision, "dirty": dirty}


def wait_for_route(page: Page, route: str) -> None:
    if route == "/":
        page.locator('.tile-container[data-title="Home"].expanded').wait_for()
    elif route.startswith("/#"):
        title = route.removeprefix("/#").replace("%20", " ")
        page.locator(f'.tile-container[data-title="{title}"].expanded').wait_for()
    else:
        page.locator(".mini-window-container.open").wait_for()
        page.frame_locator(".mini-window").locator("#location").wait_for()
    page.evaluate("document.fonts.ready")


def overflow_state(page: Page, route: str) -> dict[str, bool]:
    parent = page.evaluate(
        "document.documentElement.scrollWidth > document.documentElement.clientWidth"
    )
    document = False
    if route != "/" and not route.startswith("/#"):
        document = page.frame_locator(".mini-window").locator("html").evaluate(
            "element => element.scrollWidth > element.clientWidth"
        )
    return {"board": parent, "document": document}


def write_contact_sheet(
    browser: Browser,
    output: Path,
    theme: str,
    viewport_name: str,
    captures: list[tuple[str, Path]],
) -> None:
    context = browser.new_context(viewport={"width": 1600, "height": 900})
    page = context.new_page()
    figures = []
    for label, capture in captures:
        encoded = base64.b64encode(capture.read_bytes()).decode("ascii")
        figures.append(
            "<figure><img src=\"data:image/webp;base64,"
            f"{encoded}\"><figcaption>{label}</figcaption></figure>"
        )
    page.set_content(
        "<style>body{margin:12px;background:#ddd;display:grid;"
        "grid-template-columns:repeat(5,minmax(0,1fr));gap:10px;"
        "font:16px sans-serif}figure{margin:0;background:#fff;padding:6px}"
        "img{display:block;width:100%;height:auto}figcaption{padding:6px 2px}"
        "</style>" + "".join(figures)
    )
    page.screenshot(
        path=str(output / f"{theme}-{viewport_name}-sheet.png"),
        full_page=True,
    )
    context.close()


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--origin", required=True)
    parser.add_argument("--theme", action="append", required=True)
    parser.add_argument("--route", action="append", required=True, type=parse_named_route)
    parser.add_argument("--output", required=True, type=Path)
    args = parser.parse_args()

    parsed = urlparse(args.origin)
    if (
        parsed.scheme not in {"http", "https"}
        or not parsed.hostname
        or parsed.username
        or parsed.password
    ):
        parser.error("Use an HTTP(S) preview origin without credentials.")
    if any(not re.fullmatch(r"[a-z][a-z0-9-]*", theme) for theme in args.theme):
        parser.error("Use theme identifiers, not paths.")

    root = Path(__file__).resolve().parent.parent
    output = args.output.resolve()
    output.mkdir(parents=True, exist_ok=False)
    origin = args.origin.rstrip("/")
    manifest: dict[str, object] = {
        "status": "incomplete",
        "origin": origin,
        "source": source_state(root),
        "themes": args.theme,
        "routes": dict(args.route),
        "viewports": VIEWPORTS,
        "captures": [],
        "page_errors": [],
        "console_errors": [],
    }

    def save_manifest() -> None:
        (output / "capture.json").write_text(
            json.dumps(manifest, indent=2) + "\n",
            encoding="utf-8",
        )

    save_manifest()
    try:
        with sync_playwright() as playwright:
            endpoint = os.environ.get("PLAYWRIGHT_WS_ENDPOINT")
            browser = (
                playwright.chromium.connect(endpoint)
                if endpoint
                else playwright.chromium.launch(headless=True)
            )
            try:
                for viewport_name, viewport in VIEWPORTS.items():
                    context = browser.new_context(
                        viewport=viewport,
                        device_scale_factor=1,
                        reduced_motion="reduce",
                        is_mobile=viewport_name != "desktop",
                        has_touch=viewport_name != "desktop",
                    )
                    page = context.new_page()
                    page.on(
                        "pageerror",
                        lambda error: manifest["page_errors"].append(str(error)),
                    )
                    page.on(
                        "console",
                        lambda message: (
                            manifest["console_errors"].append(message.text)
                            if message.type == "error"
                            else None
                        ),
                    )
                    for theme in args.theme:
                        sheet_captures: list[tuple[str, Path]] = []
                        for label, route in args.route:
                            page.goto(
                                themed_url(origin, route, theme),
                                wait_until="domcontentloaded",
                            )
                            wait_for_route(page, route)
                            active_theme = page.locator("html").get_attribute(
                                "data-board-theme"
                            )
                            if active_theme != theme:
                                raise RuntimeError(
                                    f"Requested {theme}, received {active_theme}."
                                )
                            filename = f"{theme}-{viewport_name}-{label}.webp"
                            capture_path = output / filename
                            page.screenshot(
                                path=str(capture_path),
                                type="webp",
                                quality=90,
                                animations="disabled",
                            )
                            overflows = overflow_state(page, route)
                            manifest["captures"].append(
                                {
                                    "file": filename,
                                    "url": page.url,
                                    "theme": theme,
                                    "viewport": viewport_name,
                                    "route": route,
                                    "overflow": overflows,
                                }
                            )
                            sheet_captures.append((label, capture_path))
                            save_manifest()
                        write_contact_sheet(
                            browser,
                            output,
                            theme,
                            viewport_name,
                            sheet_captures,
                        )
                    context.close()
            finally:
                browser.close()

        has_overflow = any(
            any(capture["overflow"].values()) for capture in manifest["captures"]
        )
        has_errors = bool(manifest["page_errors"] or manifest["console_errors"])
        manifest["status"] = (
            "captured-with-findings" if has_overflow or has_errors else "captured"
        )
    finally:
        save_manifest()

    print(
        f"{manifest['status']}: {len(manifest['captures'])} captures at {output}; "
        "contact sheets still require visual inspection"
    )
    return 1 if manifest["status"] != "captured" else 0


if __name__ == "__main__":
    raise SystemExit(main())
