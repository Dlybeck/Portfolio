"""Which files the notebook's scripts need, so the page can ask for them all at once.

The notebook starts from one module (main.js) that imports others, which import others. A browser only learns
about a module when the one that imports it has arrived and been read, so about thirty small files load one
after another, each waiting for the last. Naming them in the page's head lets the browser fetch them in parallel.

The list is read from the scripts' own import lines, so it can never drift from them: a version bump in an
import ("./book.js?v=5") is followed automatically. It is a hint only; a file the scan misses still loads
the ordinary way. Read once per process.
"""

from __future__ import annotations

import posixpath
import re
from functools import cache
from pathlib import Path
from urllib.parse import urlsplit

ROOT = Path(__file__).parent.parent
ENTRY = "/static/js/notebook/main.js"

# `import ... from "./x.js?v=1"` and `import "./x.js"`; a dynamic import(...) is loaded on demand and is not matched
_IMPORT = re.compile(r"""(?:\bfrom|\bimport)\s*["'](\.{1,2}/[^"']+)["']""")
# the sticker layout, fetched once at start-up: new URL("./layout.json?v=1", import.meta.url)
_DATA = re.compile(r"""new URL\(\s*["'](\./[^"']+\.json[^"']*)["']\s*,\s*import\.meta\.url""")


def _resolve(importer: str, specifier: str) -> str:
    """The absolute URL (path and query) that a relative specifier means inside `importer`."""
    parts = urlsplit(specifier)
    path = posixpath.normpath(posixpath.join(posixpath.dirname(urlsplit(importer).path), parts.path))
    return f"{path}?{parts.query}" if parts.query else path


@cache
def notebook_scripts() -> tuple[tuple[str, ...], tuple[str, ...]]:
    """(modules, data files) the notebook needs at start-up, found from main.js. Missing files are skipped."""
    modules: dict[str, None] = {}
    data: dict[str, None] = {}
    pending = [ENTRY]
    seen = {ENTRY}
    while pending:
        url = pending.pop()
        file = ROOT / urlsplit(url).path.lstrip("/")
        if not file.is_file():
            continue
        source = file.read_text(encoding="utf-8")
        for specifier in _IMPORT.findall(source):
            child = _resolve(url, specifier)
            if child not in seen:
                seen.add(child)
                modules[child] = None
                pending.append(child)
        for specifier in _DATA.findall(source):
            data[_resolve(url, specifier)] = None
    return tuple(modules), tuple(data)
