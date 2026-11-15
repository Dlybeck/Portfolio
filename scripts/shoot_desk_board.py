"""Screenshots of the desk board preview (branch only). Needs the preview server running:

    DESK_BOARD_PREVIEW=1 uvicorn main:app --port 8765
    python scripts/shoot_desk_board.py [base-url]
"""

import sys
from pathlib import Path

from playwright.sync_api import sync_playwright

BASE = sys.argv[1] if len(sys.argv) > 1 else "http://127.0.0.1:8765"
OUT = Path(__file__).resolve().parent.parent / ".reports" / "desk-board"
SIZES = {"desktop": {"width": 1440, "height": 900}, "phone": {"width": 390, "height": 844}}
WHERE = {"a": "#say-hi", "b": "#say-hi", "c": ""}

OUT.mkdir(parents=True, exist_ok=True)
with sync_playwright() as p:
    browser = p.chromium.launch()
    for size, viewport in SIZES.items():
        page = browser.new_page(viewport=viewport, device_scale_factor=2 if size == "phone" else 1)
        page.goto(f"{BASE}/preview/desk-board")
        page.wait_for_timeout(600)
        page.screenshot(path=OUT / f"options-{size}.png", full_page=True)
        page.close()
        for option, hash_ in WHERE.items():
            for state in ("working", "resting", "offline"):
                page = browser.new_page(viewport=viewport, device_scale_factor=2 if size == "phone" else 1, reduced_motion="reduce")
                page.goto(f"{BASE}/preview/desk-board/{option}?state={state}{hash_}")
                page.wait_for_timeout(2200)
                page.screenshot(path=OUT / f"{option}-{state}-{size}.png")
                page.close()
    browser.close()
print("saved to", OUT)
