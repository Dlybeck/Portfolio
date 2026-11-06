"""Make the 1200 by 630 picture that link previews show (static/img/social/home-notebook.webp).

Start the site first (python main.py), then:

    python scripts/build_social_image.py [http://127.0.0.1:8080]

Needs Playwright (with Chromium) and Pillow. The cover is photographed from the running site, so the
picture always matches what visitors see.
"""

from __future__ import annotations

import io
import sys
from pathlib import Path

from PIL import Image, ImageDraw, ImageFont
from playwright.sync_api import sync_playwright

ROOT = Path(__file__).resolve().parent.parent
OUT = ROOT / "static" / "img" / "social" / "home-notebook.webp"
BACKGROUND = "#f4f6fa"
INK = "#141c2b"


def photograph_cover(base: str) -> Image.Image:
    with sync_playwright() as p:
        browser = p.chromium.launch()
        page = browser.new_page(viewport={"width": 1280, "height": 900}, device_scale_factor=2)
        page.goto(base + "/")
        page.wait_for_selector(".cover-front .wd-ball")
        page.wait_for_timeout(5500)  # the pad has written its first word
        shot = page.locator(".cover-front").screenshot()
        browser.close()
    return Image.open(io.BytesIO(shot)).convert("RGB")


def main() -> None:
    base = sys.argv[1] if len(sys.argv) > 1 else "http://127.0.0.1:8080"
    cover = photograph_cover(base)
    canvas = Image.new("RGB", (1200, 630), BACKGROUND)
    height = 560
    cover = cover.resize((round(cover.width * height / cover.height), height), Image.LANCZOS)
    canvas.paste(cover, (1200 - cover.width - 90, (630 - height) // 2))
    draw = ImageDraw.Draw(canvas)
    # PIL cannot read woff2, so the words use the system's closest bold sans; the cover carries the brand
    try:
        big = ImageFont.truetype("DejaVuSans-Bold.ttf", 76)
        small = ImageFont.truetype("DejaVuSans.ttf", 34)
    except OSError:
        big = small = ImageFont.load_default()
    draw.text((80, 190), "David\nLybeck", font=big, fill=INK, spacing=6)
    draw.text((80, 400), "Innovation AI Developer", font=small, fill="#5a6578")
    draw.text((80, 450), "A portfolio you page through", font=small, fill="#5a6578")
    OUT.parent.mkdir(parents=True, exist_ok=True)
    canvas.save(OUT, "WEBP", quality=88)
    print(f"{OUT.relative_to(ROOT)}: {OUT.stat().st_size // 1000} KB")


if __name__ == "__main__":
    main()
