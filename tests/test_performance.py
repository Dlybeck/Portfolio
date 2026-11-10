"""Things that keep the notebook light on slow devices: scripts named up front, and animations that stay off the main thread."""

from __future__ import annotations

import re
from pathlib import Path

from fastapi.testclient import TestClient

from core.preload import notebook_scripts

ROOT = Path(__file__).resolve().parent.parent
STICKERS_CSS = (ROOT / "static/css/notebook/stickers.css").read_text()


def _preloads(html: str, rel: str) -> list[str]:
    return re.findall(rf'<link rel="{rel}" href="([^"]+)"', html)


def test_the_page_names_every_script_it_starts_with(client: TestClient) -> None:
    html = client.get("/").text
    modules, data = notebook_scripts()

    assert _preloads(html, "modulepreload") == list(modules)
    assert set(data) <= set(_preloads(html, "preload"))
    # the start-up modules from the first import (book, cover) down to the leaves (the sticker reader and its ink)
    for expected in ("/static/js/notebook/stickers/index.js", "/static/js/notebook/stickers/ocr.js", "/static/js/notebook/swing.js"):
        assert any(src.split("?")[0] == expected for src in modules), expected


def test_only_what_start_up_imports_is_preloaded(client: TestClient) -> None:
    modules, data = notebook_scripts()
    names = {src.split("?")[0] for src in modules}

    # loaded on demand or in a worker, so fetching them up front would spend the visitor's data for nothing
    assert "/static/js/notebook/stickers/ocr.worker.js" not in names
    assert not any("model-viewer" in src for src in modules)
    assert data == ("/static/js/notebook/stickers/layout.json?v=1",)


def test_every_preloaded_file_exists_with_the_version_the_import_asks_for(client: TestClient) -> None:
    modules, data = notebook_scripts()
    for src in (*modules, *data):
        assert client.get(src).status_code == 200, src


def test_the_scan_follows_a_version_bump_in_an_import(tmp_path: Path, monkeypatch) -> None:
    from core import preload

    (tmp_path / "static/js/notebook").mkdir(parents=True)
    (tmp_path / "static/js/notebook/main.js").write_text('import { a } from "./a.js?v=7";\nconst x = import("./lazy.js");\n')
    (tmp_path / "static/js/notebook/a.js").write_text('import "../shared.js";\nexport const a = 1;\n')
    (tmp_path / "static/shared.js").write_text("")
    monkeypatch.setattr(preload, "ROOT", tmp_path)
    preload.notebook_scripts.cache_clear()
    try:
        assert preload.notebook_scripts() == (("/static/js/notebook/a.js?v=7", "/static/js/shared.js"), ())
    finally:
        preload.notebook_scripts.cache_clear()


def _keyframes(name: str) -> str:
    """The body of a one-line @keyframes rule, without its comments."""
    match = re.search(rf"^@keyframes {name} (.*)$", STICKERS_CSS, re.M)
    assert match, name
    return re.sub(r"/\*.*?\*/", "", match.group(1))


def test_the_live_dot_and_printer_gantry_animate_only_what_the_compositor_can_draw() -> None:
    # A box-shadow or a `top` that changes every frame repaints (or re-lays-out) the whole filtered sticker on the main thread.
    for name in ("pulse", "gantry"):
        properties = set(re.findall(r"([a-z-]+)\s*:", _keyframes(name)))
        assert properties <= {"transform", "opacity", "translate"}, (name, properties)
