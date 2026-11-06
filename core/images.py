"""Sizes of the notebook's pictures (written by scripts/build_notebook_images.py)."""

from __future__ import annotations

import json
from functools import cache
from pathlib import Path

IMG_DIR = Path(__file__).resolve().parent.parent / "static" / "img"


@cache
def _manifest() -> dict[str, list[int]]:
    return json.loads((IMG_DIR / "manifest.json").read_text())


def img_size(name: str) -> tuple[int, int]:
    """Width and height of static/img/<name>, so a page can reserve its space."""
    width, height = _manifest()[name]
    return width, height
