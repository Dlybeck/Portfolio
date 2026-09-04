"""Theme Engine server-facing interface."""

from __future__ import annotations

from fastapi import Request

from core.theme_packs import ThemePackRegistry

def theme_context(
    request: Request,
    enabled: bool,
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
        "theme_board_variables": dict(selected.board_variables) if enabled else {},
        "theme_document_variables": (
            dict(selected.document_variables) if enabled else {}
        ),
        "theme_selector_enabled": enabled,
        "board_themes": registry.public_catalog(),
        "remember_theme": selected.id if enabled and requested is None else None,
    }
