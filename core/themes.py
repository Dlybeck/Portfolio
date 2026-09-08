"""Theme Engine server-facing interface."""

from __future__ import annotations

from fastapi import Request

from core.theme_packs import ThemePackRegistry
from core.portfolio import document_for_route

def theme_context(
    request: Request,
    enabled: bool,
    registry: ThemePackRegistry | None = None,
) -> dict[str, object]:
    """Return the rendered Board Theme context for one request."""
    registry = registry or ThemePackRegistry.discover()
    requested = request.query_params.get("theme")
    selected = registry.resolve(requested, enabled=enabled)
    board_variables = dict(selected.board_variables) if enabled else {}
    document_variables = dict(selected.document_variables) if enabled else {}
    route = request.url.path.removeprefix('/_documents')
    document = document_for_route(route)
    assignment = dict(selected.tiles).get(document.board_title) if document else None
    if enabled and assignment and assignment.reading_surface:
        material = assignment.reading_surface
        board_variables.update({'viewer-bg': material.page_color, 'viewer-border': material.surround_color})
        document_variables['page-bg'] = material.page_color
    return {
        "active_theme": selected.id,
        "active_theme_pack": selected.client_payload(),
        "theme_engine_enabled": enabled,
        "theme_board_variables": board_variables,
        "theme_document_variables": document_variables,
        "theme_selector_enabled": enabled,
        "board_themes": registry.public_catalog(),
    }
