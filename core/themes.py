"""Theme Engine server-facing interface."""

from __future__ import annotations

from fastapi import Request

from core.theme_packs import (
    CANONICAL_THEME,
    ThemePackRegistry,
)

def theme_context(
    request: Request,
    enabled: bool,
    registry: ThemePackRegistry | None = None,
) -> dict[str, object]:
    """Return the rendered Board Theme context for one request."""
    registry = registry or ThemePackRegistry.discover()
    selected = registry.resolve(request.query_params.get("theme"), enabled=enabled)
    return {
        "active_theme": selected.id,
        "theme_lab_enabled": enabled,
        "board_themes": registry.public_catalog(),
    }
