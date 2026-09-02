"""Theme Laboratory server-facing interface."""

from __future__ import annotations

from dataclasses import asdict, dataclass

from fastapi import Request


CANONICAL_THEME = "canonical"


@dataclass(frozen=True)
class BoardTheme:
    key: str
    label: str


BOARD_THEMES = (
    BoardTheme(CANONICAL_THEME, "Original"),
    BoardTheme("lily", "Lily Pond"),
    BoardTheme("planets", "Planets / Constellation"),
    BoardTheme("clouds", "Cloudscape"),
    BoardTheme("islands", "Island Chain"),
)
THEME_KEYS = frozenset(theme.key for theme in BOARD_THEMES)


def theme_context(request: Request, enabled: bool) -> dict[str, object]:
    """Return the rendered Board Theme context for one request."""
    requested = request.query_params.get("theme", CANONICAL_THEME)
    active_theme = requested if enabled and requested in THEME_KEYS else CANONICAL_THEME
    return {
        "active_theme": active_theme,
        "theme_lab_enabled": enabled,
        "board_themes": tuple(asdict(theme) for theme in BOARD_THEMES),
    }
