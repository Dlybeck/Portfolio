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
    selector_enabled: bool | None = None,
    registry: ThemePackRegistry | None = None,
) -> dict[str, object]:
    """Return the rendered Board Theme context for one request."""
    registry = registry or ThemePackRegistry.discover()
    requested = request.query_params.get("theme")
    selected = registry.select_for_request(
        requested,
        enabled=enabled,
        exclude_id=request.cookies.get("portfolio_theme") if requested is None else None,
    )
    return {
        "active_theme": selected.id,
        "active_theme_pack": selected.client_payload(),
        "theme_engine_enabled": enabled,
        "theme_selector_enabled": (
            enabled if selector_enabled is None else enabled and selector_enabled
        ),
        "board_themes": registry.public_catalog(),
        "remember_theme": selected.id if enabled and requested is None else None,
    }
