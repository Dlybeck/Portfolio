#!/usr/bin/env python3
"""Validate one inert Theme Pack directory and emit a machine receipt."""

from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from core.theme_packs import InvalidThemeAsset, load_theme_pack  # noqa: E402


def file_digest(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("pack", type=Path, help="Theme Pack directory")
    args = parser.parse_args()
    pack_dir = args.pack.resolve()
    try:
        pack = load_theme_pack(pack_dir)
        if not pack.tiles or not pack.board_variables or not pack.document_variables:
            raise InvalidThemeAsset("an installable Theme Pack must be a complete visual world")
    except (InvalidThemeAsset, OSError, ValueError) as error:
        print(json.dumps({"valid": False, "pack": str(pack_dir), "error": str(error)}))
        return 1

    files = sorted(path for path in pack_dir.rglob("*") if path.is_file())
    axes = sorted({name for _, tile in pack.tiles for name, _ in tile.factors})
    receipt = {
        "valid": True,
        "schema": pack.manifest.schema_id,
        "id": pack.id,
        "label": pack.label,
        "tileCount": len(pack.tiles),
        "boardTokenCount": len(pack.board_variables),
        "documentTokenCount": len(pack.document_variables),
        "backgroundDepths": [depth for depth, _ in pack.background_layers],
        "variationAxes": axes,
        "files": {
            str(path.relative_to(pack_dir)): file_digest(path) for path in files
        },
    }
    print(json.dumps(receipt, indent=2, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
