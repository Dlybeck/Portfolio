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
- Decorative motion, hover response, responsive substitutions, focus
  treatment, random-selection eligibility, and display label.

Content, topology, semantic meaning, focus order, and routes are never
theme-owned.

## Filesystem interface

```text
static/themes/<pack-id>/
├── theme.json
├── presentation.json
├── tiles.json
├── assets/
│   ├── tiles/
│   │   ├── <location>-base.svg
│   │   └── <location>-expanded.svg
│   ├── background.svg       # optional pack-owned depth layer
│   ├── background-near.svg  # optional additional depth layer
│   └── ... future validated asset classes
└── ... optional authoring sources ignored by runtime

schemas/theme-pack-v1/
├── theme.schema.json
├── presentation.schema.json
└── tiles.schema.json
```

`theme.json` is the only discovery entrypoint. It references the presentation
and compiled tile catalogs using pack-local paths. Every referenced file must
resolve below the pack directory. Parent traversal, remote URLs, scripts,
event attributes, foreign objects, and external SVG references are invalid.

## Manifest sections

Every manifest declares this strict top-level interface:

```json
{
  "$schema": "portfolio-theme-pack/v1",
  "id": "lily",
  "label": "Lily Pond",
  "version": 1,
  "tiles": "tiles.json",
  "presentation": "presentation.json",
  "background": [
    {"asset": "assets/background.svg", "depth": 0.30},
    {"asset": "assets/background-near.svg", "depth": 0.50}
  ],
  "selection": {
    "enabled": true,
    "randomEligible": true,
    "randomWeight": 1
  }
}
```

Unknown fields fail validation. That makes spelling mistakes and unsupported
AI output visible rather than silently ignored.

### Selection

- `enabled`: whether the pack may be activated.
- `randomEligible`: whether unpinned refresh selection may choose it.
- `randomWeight`: a positive integer used by weighted selection.

Canonical remains the fail-closed fallback. A missing, disabled, malformed, or
unsafe requested pack never partially applies.

### Presentation catalog

`presentation.json` is the complete styling contract. Its `board` and
`document` maps must contain the exact supported token sets; missing and
unknown tokens both reject the pack. Its `connectors` object uses a bounded,
typed grammar. Values are validated as inert values and cannot contain rules,
selectors, external URLs, imports, expressions, markup, or executable code.

The stable stylesheets translate these tokens onto semantic UI slots. They do
not contain any installed theme ID, world-specific color, or world-specific
geometry. This means an ordinary new visual world can replace every existing
presentation choice using pack files, while a genuinely new visual capability
requires an intentional versioned extension to the shared grammar.

### Typography

Font-family and size tokens are independent for navbar, controls, base title,
expanded title, expanded summary, expanded action, document title, document
heading, document body, document link, fields, buttons, loader, and code.
Weights, line heights, letter spacing, and phone-specific sizing are also
pack-owned. The currently approved fonts are loaded once by the stable shell;
packs select among those inert font-family values.

### Colors and surfaces

Semantic tokens describe ink, secondary ink, links, focus, borders, shadows,
controls, viewer surfaces, document surfaces, and media/code surfaces.
Background values may use inert colors and CSS gradient/pattern values but may
not reference remote content or inject unrestricted CSS.

### Grounded restraint for generated packs

A coherent pack uses visual evidence that belongs to its real-world metaphor.
Start with material and silhouette, then add functional details that explain
the object's identity, construction, or use. A notebook's binding rings belong;
a generic coffee stain or arbitrary crease does not. This constraint is
especially important for generated Theme Packs: the target is clean
solid-color SVG art with purposeful realism, not decorative accumulation or
simulated photorealism.

### Board and chrome

The Board declares its background stack, ambient-mark treatment and placement,
tile typography and shadows, hover/motion treatment, and component visibility.
Chrome tokens own navbar, Personal Mark, controls, selector, viewer frame,
states, radii, filters, padding, rotations, and shadows. The theme may show or
hide declared decorative components such as ambient marks, tape, chrome
decoration, and title underlines; it cannot hide semantic content or controls.
Tile and expanded-cover dimensions have desktop and phone slots, so object
geometry can vary while the invariant grid and Parent/Child model stay fixed.

The `action-treatment` token selects one of two stable expanded-link adapters:
`annotation` keeps the destination as writing directly on an object, while
`marker` gives it a filled, bordered in-world label with a 44-pixel touch target. Packs
own the action font, size, ink, background, border, padding, radius, shadow,
decoration, and transform. The Theme Engine continues to own the link target,
placement, focus order, activation behavior, and minimum readable marker size.

The `viewer-artifact` token selects one stable opened-Document carrier:
`none`, `field-notebook`, `observation-window`, or `expedition-log`. Packs own
the carrier label, ink, accent/detail colors, outer frame surface, border,
shadow, dimensions, iframe radius, and desktop/phone geometry. The stable
Viewer supplies the same label and hardware slots for every pack. This keeps
the reviewed physical treatments configurable without A/B/C runtime state or
theme-name selectors.

### Connectors

Connectors declare color, width, opacity, cap, dash pattern, curve family,
rough/glow/none texture, halo, endpoint inset, head style and placement, head
dimensions, and wobble. The Theme Engine continues to calculate relationship
endpoints from the invariant graph; no pack can change which locations are
related. A bounded `variation` block independently perturbs width, wobble,
dash rhythm, opacity, and marker scale from a stable relationship seed. This
keeps a hand-made or natural network from becoming machine-stamped without
making a connector flicker between renders.

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

Each location also declares inert transform and motion channels. `transforms`
owns independent base and expanded rotation and X/Y offset plus a detail
rotation for real-world elements such as tape. `motion` provides small bounded
per-location offsets to the pack-selected motion preset. Optional `typography`
and `layout` blocks let a pack fit a difficult real title or choose a different
expanded object proportion without runtime knowledge of the theme or title.

`theme.json` may declare up to four ordered `background` layers. Every layer
contains only a pack-local sanitized SVG `asset` and a `depth` from `0` to `1`.
Array order is back to front. `0` stays fixed to the viewport, `1` moves with
the Board, and intermediate values move by that proportion of the Board shift.
This is the preferred slot for irregular stars, water currents, paper grain,
or another non-repeating environment. CSS background tokens remain available
for real materials whose repetition is intentional.

Depth layers are decorative and pointer-inert. They cannot contain tiles,
labels, focus surfaces, hit targets, documents, or relationship connectors;
those remain together at full Board movement. Packs may omit layers or keep a
single layer at depth `1`. Multiple depths are used only when the real-world
metaphor supports them, and reduced-motion mode removes their transition while
preserving the final composition.

Compiled SVG assets may use pack color variables but cannot contain
scripts, remote resources, event handlers, `foreignObject`, or navigation.
The Theme Engine namespaces IDs and rewrites local fragment references when it
creates repeated tile instances.

### Documents

Documents retain one semantic HTML grammar. A pack styles stable slots for the
canvas, header, section, separator, link, action, media, caption, code/model,
focus, form field, output/result, selection, scrollbar, bullet, and Back-to-Top
control. The pack owns fonts, sizes, weights, spacing, hover states, all text
colors, backgrounds, borders, radii, and shadows. It cannot hide or reorder
content.

The document contract also exposes container and panel box sizing, paragraph
rhythm, per-heading-level sizes, action display, separate form-button styling,
and distinct media/model geometry. These are presentation choices rather than
invariant layout so a pack can reproduce a real reference without adding a
theme-name branch to the engine.

Text-dense and media/model-rich Documents are mandatory validation fixtures.
Document theming must be structurally visible; changing only colors does not
satisfy the contract.

### Motion, responsive behavior, and accessibility

The `focus-motion` Board token selects one stable focus preset: `cover`, `grow`,
or `settle`. `cover` places and removes a larger surface, `grow` expands and
reverses the selected object itself, and `settle` resolves the focused form in
place without a camera move. Timing, easing, offsets, scale, and rotation remain
pack-owned presentation tokens. Adding an ordinary theme therefore requires a
preset selection and parameters, not theme-specific runtime code.

The stable styles disable decorative motion when reduced motion is requested.
Responsive tokens may adjust type sizing while SVG view boxes and content-safe
areas keep tile art and text together without changing Interaction Structure.

Motion never owns navigation. During focus, entry, and exit transitions, every
neighboring destination in the current Neighborhood remains visible and
directly actionable through the same pointer, touch, and keyboard relationship.
No motion recipe may globally pan, zoom, crop, cover, disable, reorder, or move
those destinations in a way that changes their availability or established
spatial relationship.

Every pack must provide a visible focus color. Theme SVGs are inserted as
decorative, pointer-inert artwork; the stable semantic HTML remains the
accessible control surface.

## Runtime selection

- An explicit `?theme=<id>` pins a valid pack for development and sharing.
- With no pin, a full page load selects an enabled, random-eligible pack.
- Internal exploration retains the selected Theme Instance.
- A subsequent unpinned refresh chooses again; when at least two packs are
  eligible, the immediately previous pack may be excluded.
- Variant choices inside a pack are deterministic for the pack seed and Board
  location. Random theme selection does not make individual objects flicker.

Deployment enables the engine and selector independently:

```text
THEMES_ENABLED=true
THEME_SELECTOR_ENABLED=false
```

For local authoring, `THEME_LAB_ENABLED=true` enables both. The theme-enabled
shell loads only the neutral Board/Document structure stylesheets and the
validated pack mapping; the original pre-pack CSS/JavaScript presenter is
loaded only when the engine is disabled.

## Future AI seam

An AI integration produces the exact same Theme Pack directory as a human. It
has no privileged rendering path and cannot modify engine source. Its output
must pass, in order:

1. Manifest schema and path validation.
2. SVG and inert presentation-value safety validation.
3. Slot, token, axis, and safe-area completeness.
4. Contrast, focus, reduced-motion, responsive, and text-fit checks.
5. Board variation and document-grammar checks.
6. Owner-visible desktop and phone previews before publication.

The intended promise is zero engine changes for ordinary new worlds, not
unlimited new behavior without ever extending the Theme Pack language.

## Authoring and validation

Create a complete random-ineligible starter pack outside the installed
directory, then edit only its files. It remains available for deliberate
selection once installed, but cannot appear on random refresh until its owner
opts it in. Its neutral six-axis SVG grammar already passes the rendered
variation and continuity baseline, so authors begin from a working contract
rather than a deliberately failing placeholder:

```bash
.venv/bin/python scripts/scaffold_theme_pack.py rain-garden "Rain Garden" /tmp/theme-work
```

Validate either human- or AI-authored output with the same runtime validator:

```bash
.venv/bin/python scripts/validate_theme_pack.py /tmp/theme-work/rain-garden
```

The validator emits a JSON receipt containing the installed file hashes,
location count, presentation-token counts, ordered background depths, and
variation axes. It exits nonzero for an incomplete or unsafe pack. Generate
the checked-in JSON Schemas from the runtime contract with:

```bash
.venv/bin/python scripts/export_theme_pack_schemas.py
```

The schema files are useful while generating JSON; the validator remains the
authority because it also performs local-path and SVG safety checks that JSON
Schema cannot express.

Once installed, no audit list needs updating. Both visual tools discover all
enabled packs through the runtime registry:

```bash
.venv/bin/python scripts/audit_theme_variants.py
.venv/bin/python scripts/capture_theme_matrix.py
```

## Completion proof

Theme Pack v1 is complete only when:

- Canonical and every enabled alternate theme render through the Theme Engine with
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
