# Theme Pack v1

Theme Pack v1 is the complete visual interface between the portfolio and a
Board Theme. Adding a conforming pack changes no Python, JavaScript, template,
or shared CSS source. A pack is installed by adding one directory under
`static/themes/`; the Theme Engine discovers it, validates it, and exposes it
to the Board only when every required contract passes.

## Ownership

The Theme Engine owns behavior and invariant structure:

- Parent/Child topology, the five-item Neighborhood, routes, history, and
  document flow.
- Semantic controls, keyboard order, pointer/touch behavior, and reduced-motion
  enforcement.
- Pack discovery, validation, SVG sanitization, deterministic selection,
  cleanup, fallback, text fitting, and responsive application.
- The stable Board, tile, document, media, and chrome DOM slots.

A Theme Pack owns the entire presentation:

- Fonts and every text role.
- Board surface, background layers, textures, ambience, and parallax styling.
- Navbar, Personal Mark treatment, Home/Close/Back controls, selector, and
  focus appearance.
- Base and expanded tile SVGs, palettes, silhouettes, ornaments, shadows,
  variation axes, and content-safe areas.
- Relationship lines: color, texture, width, opacity, wobble, caps,
  arrowheads, and decorative motion.
- Opened-document canvas, headings, body text, links, buttons, sections,
  separators, ornaments, media frames, code/model surfaces, captions,
  scrollbar, and Back-to-Top treatment.
- Decorative motion, hover response, responsive substitutions, contrast
  targets, random-selection eligibility, and preview metadata.

Content, topology, semantic meaning, focus order, and routes are never
theme-owned.

## Filesystem interface

```text
static/themes/<pack-id>/
├── theme.json
├── assets/
│   ├── board/
│   ├── chrome/
│   ├── connectors/
│   ├── tiles/
│   │   ├── base.svg
│   │   ├── expanded.svg
│   │   └── axes/
│   └── documents/
└── fonts/
```

`theme.json` is the only entrypoint. Every referenced file must resolve below
the pack directory. Parent traversal, remote URLs, scripts, event attributes,
foreign objects, and external SVG references are invalid.

## Manifest sections

Every manifest declares these top-level sections:

```json
{
  "$schema": "portfolio-theme-pack/v1",
  "id": "lily",
  "label": "Lily Pond",
  "version": 1,
  "selection": {},
  "typography": {},
  "colors": {},
  "board": {},
  "chrome": {},
  "connectors": {},
  "tiles": {},
  "documents": {},
  "motion": {},
  "responsive": {},
  "accessibility": {}
}
```

Unknown fields fail validation. That makes spelling mistakes and unsupported
AI output visible rather than silently ignored.

### Selection

- `enabled`: whether the pack may be activated.
- `randomEligible`: whether unpinned refresh selection may choose it.
- `randomWeight`: a positive integer used by weighted selection.
- `preview`: a local image used by development tooling.

Canonical remains the fail-closed fallback. A missing, disabled, malformed, or
unsafe requested pack never partially applies.

### Typography

Font sources are local pack assets or explicitly approved built-in families.
Roles are declared independently for navbar, base title, expanded title,
expanded summary, expanded action, document title, document heading, document
body, document link, caption, and code. Each role includes family, weight,
style, line height, letter spacing, and bounded responsive size.

### Colors and surfaces

Semantic tokens describe ink, secondary ink, links, focus, borders, shadows,
controls, viewer surfaces, document surfaces, and tile palette channels.
Backgrounds are constrained layer descriptions—solid, linear gradient, radial
gradient, repeating pattern, or local sanitized SVG—not unrestricted CSS.

### Board and chrome

The Board declares its background layer stack, ambient asset placements,
parallax factors, and decorative motion. Chrome declares navbar geometry,
Personal Mark treatment, controls, selector, viewer frame, states, and shadows.
All geometry is bounded so chrome cannot cover the active Neighborhood.

### Connectors

Connectors declare stroke tokens, width, opacity, dash/cap/head treatment,
wobble, texture, layering, and motion. The Theme Engine continues to calculate
relationship endpoints from the invariant graph.

### Tiles

Each installed pack provides compiled base and expanded SVG assets for every
Board location. The manifest records each asset pair's semantic factor values.
Palette and orientation are standard axes; packs add semantic axes such as
`notch`, `vein`, `surface`, `companion`, `density`, or `shore` without engine
changes. Human and AI authoring tools may use templates, fragments, or another
internal representation, but compilation happens before installation; the
runtime Theme Engine never interprets an executable or theme-specific drawing
language.

Each SVG state exposes an invisible `data-theme-content-area` geometry for its
HTML content. The Theme Engine maps content into that safe area and fits long
titles within declared minimum and maximum sizes. The validator proves the
safe area remains inside the rendered silhouette at desktop and phone sizes.
Base and expanded states keep the same Theme Instance identity and factor
selection even when their artwork differs.

Compiled SVG assets may use pack color variables but cannot contain
scripts, remote resources, event handlers, `foreignObject`, or navigation.
The Theme Engine namespaces IDs and rewrites local fragment references when it
creates repeated tile instances.

### Documents

Documents retain one semantic HTML grammar. A pack styles stable slots for the
canvas, header, section, separator, link, action, media, caption, code, model,
scrollbar, and Back-to-Top control. It may supply sanitized ornaments and
constrained section geometry, but it cannot hide or reorder content.

Text-dense and media/model-rich Documents are mandatory validation fixtures.
Document theming must be structurally visible; changing only colors does not
satisfy the contract.

### Motion, responsive behavior, and accessibility

Motion declarations select bounded durations, easing, transforms, and ambient
effects. The Theme Engine disables decorative motion when reduced motion is
requested. Responsive declarations may substitute assets, safe areas, font
bounds, and ornament density without changing Interaction Structure.

Every pack declares minimum contrast targets, a visible focus treatment, and
whether each asset is decorative. Missing accessibility declarations fail the
pack rather than inheriting an unknown state.

## Runtime selection

- An explicit `?theme=<id>` pins a valid pack for development and sharing.
- With no pin, a full page load selects an enabled, random-eligible pack.
- Internal exploration retains the selected Theme Instance.
- A subsequent unpinned refresh chooses again; when at least two packs are
  eligible, the immediately previous pack may be excluded.
- Variant choices inside a pack are deterministic for the pack seed and Board
  location. Random theme selection does not make individual objects flicker.

## Future AI seam

An AI integration produces the exact same Theme Pack directory as a human. It
has no privileged rendering path and cannot modify engine source. Its output
must pass, in order:

1. Manifest schema and path validation.
2. SVG and font safety validation.
3. Slot, token, axis, and safe-area completeness.
4. Contrast, focus, reduced-motion, responsive, and text-fit checks.
5. Board variation and document-grammar checks.
6. Owner-visible desktop and phone previews before publication.

The intended promise is zero engine changes for ordinary new worlds, not
unlimited new behavior without ever extending the Theme Pack language.

## Completion proof

Theme Pack v1 is complete only when:

- Canonical and all four alternate themes render through the Theme Engine with
  no theme IDs, colors, SVG geometry, or document styling hardcoded in engine
  source.
- A test fixture pack is installed and discovered using pack files alone.
- Removing one pack directory removes it cleanly without source edits.
- Invalid and unsafe packs fail closed to Canonical with actionable diagnostics.
- Random refresh selection, explicit pinning, and in-session continuity pass.
- Tile text fits the actual declared safe area for every Board location at
  desktop and phone sizes.
- Every pack produces a visibly native treatment for text-dense and
  media/model-rich Documents.
- Existing navigation, accessibility, metadata, content, and historical-work
  tests remain green.
