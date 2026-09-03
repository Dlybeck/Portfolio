# Preserve self-discovered spatial navigation

The portfolio uses a spatial board as its primary structure rather than a conventional menu or prescribed reading order. Its controls must be understandable at a glance, but realizing how the board works and choosing to explore it are intentional parts of the experience; a brief in-world clue may support that realization without introducing an external tutorial or guided tour.

The navigation model is a hard product invariant, not a theme option. A Board
location continues to expose its centered section and neighboring Parent and
Children throughout focus and theme motion. Those neighboring destinations
remain visible and directly actionable through pointer, touch, and keyboard
interaction.

A theme may animate or restyle the Board, but it may not pan, zoom, crop,
cover, disable, reorder, or move neighboring destinations in a way that changes
their availability or the established spatial relationships. A transition that
requires compromising the Neighborhood is rejected even when its visual effect
would otherwise suit the theme.
