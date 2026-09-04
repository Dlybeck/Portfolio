# Theme Packs own bounded decorative depth layers

Theme Packs may declare zero to four ordered, sanitized SVG background layers.
Each layer has only an asset path and a bounded depth factor from `0` to `1`:
`0` stays fixed to the viewport, `1` moves with the Board, and intermediate
values move proportionally. Array order is back to front.

Depth is presentation, so the Theme Engine implements it generically and a
pack selects it using inert data. Tiles, labels, focus surfaces, hit targets,
documents, and relationship connectors cannot enter these layers. They remain
together at full Board movement so Parent/Child navigation and Neighborhood
geometry never change.

Multiple depths are optional and must follow the world's real-life metaphor.
Planets / Constellation is the first enabled use: fixed distant lighting,
nearly fixed far stars, subtly moving nearer stars, and full-motion navigation
objects. Original Paper and Lily Pond deliberately remain single-plane;
Island Chain remains single-plane until a separate visual review justifies
depth. Reduced-motion mode preserves final positions but removes transitions.

