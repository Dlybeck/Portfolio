# Four new Theme Packs

## Goal contract

Implement the four proposed themes on `dev`: Vinyl collection, Botanical
collection, Maker's workbench, and Postcards & correspondence.

Worktree: `/home/dlybeck/Projects/Portfolio-worktrees/portfolio-dev`
Branch: `dev`; base: `559e304`. The previously clean dev branch was fast-forwarded
to the latest approved main before work began. Main is not modified.

Authority: local source/assets, tests, screenshots, local commits on dev, and a
private 0.0.0.0 preview. No production deployment, main push, AI feature, theme
workbench tooling, paid assets, or unrelated changes.

## Design / proof

- Four complete auto-discovered packs: every real location has base/expanded
  artwork, purposeful independent variation, typography, controls, background,
  motion preset, and fully themed opened Documents.
- Vinyl: circular records partly in illustrated sleeves; liner-note Documents.
- Botanical: pressed specimens mounted on cards; field-notebook Documents.
- Workbench: graph-paper technical sketches on a cutting mat; project notebook.
- Postcards: illustrated correspondence with envelopes; unfolded-letter pages.
- Preserve existing worlds byte-for-byte. Preserve neighboring destinations,
  navigation, content, and state behavior. Theme-specific runtime code is not
  an acceptable implementation path.
- Validate declared variation, sanitizer/manifest acceptance, actual text fit,
  controls, document flow, and desktop/phone screenshots. Inspect images before
  delivery; counts and overflow checks alone do not prove aesthetic quality.
- New packs are manually selectable and eligible for refresh randomization on
  dev, using existing selection semantics.

## Execution

Four auto-discovered packs are implemented. Run
`python scripts/build_collection_themes.py` to regenerate their ordinary
Theme Pack JSON and SVGs. This is an authoring tool, not a runtime dependency.
The generator targets only the four new directories; existing packs and
navigation sources are untouched.

Each pack has six independent variation channels, deterministic per-location
placement, all 34 base/expanded assets, its own background, motion preset,
typography, actions, and opened Document treatment.

Visual review corrected square jacket proportions and kept printed art inside
the sleeve; specimen mounting strips now follow the actual stem, bolt holes
sit inside the sketched flange, and stamps sit on the addressed envelope face.
One shared, opt-in SVG opacity rule prevents underlying titles ghosting through
opaque paper. It is not keyed to theme names and leaves legacy assets at their
existing opacity. No JavaScript, Python runtime, schema, or template change was
needed.

Desktop and phone screenshots have been inspected for all 17 focused locations,
complete Home neighborhoods, photo pages, text/link pages, and model pages.
The preview is private and local to dev:
`http://100.118.63.4:51354/?theme=vinyl` (also `botanical`, `workbench`, `postcards`).

Planned validation: `tests/test_new_theme_packs.py`, existing theme/keyboard/
document tests, `scripts/audit_theme_variants.py`, canonical fidelity, and visual
review captures from the dev preview on desktop and phone.

## Delivery receipt

Implementation commit: `60c9d66` on local `dev`. No push, main change, or
production deployment. Preview service: `portfolio-dev-theme-preview.service`,
bound to `0.0.0.0:51354`; the previous preview on 51353 remains available.

- Four runtime validator receipts pass: `/tmp/four-themes-<id>-receipt.json`.
  Each pack provides 17 locations, 187 Board tokens, 116 Document tokens,
  six variation axes, and one Board-attached background layer.
- Full regression: **289 passed in 364.35 seconds**, recorded in
  `/tmp/four-themes-verified-tests.xml` and `.log`.
- Final pack/interaction checks after the caption contrast and click-through
  assertions: **29 passed in 59.24 seconds**, recorded in
  `/tmp/four-themes-final-interaction-tests.log`.
- Browser fit checks cover every base and expanded location at 320, 390, 768,
  and 1440px. Click-through checks cover Home → Hobbies → Tennis → opened
  Document on desktop and phone with normal motion. Tests also cover round
  records, variant continuity, caption/link contrast, and unchanged legacy
  opacity.
- Initial broad failures were two fixed-catalog random-selection assertions
  and three premature iframe-style comparisons. Selection tests now derive
  tickets from the installed catalog; computed-style assertions wait for
  document resources. No existing theme was changed to satisfy them.
- All five existing pack directories remain byte-for-byte unchanged from
  `559e304`. Canonical fidelity checker passes. Compared Home and opened Tennis
  at desktop/phone against the unchanged implementation worktree: 14 of 16
  PNGs match byte-for-byte, including every Original capture. The two Lily
  Document captures differ only at 8 phone / 45 desktop corner pixels
  (maximum channel differences 4 / 10), consistent with rounded-edge
  rasterization. Both were visually inspected; no layout or content difference.
- Final reviewed screenshots and measurements: `/tmp/four-themes-review-delivery`.
  Existing-theme comparisons: `/tmp/four-themes-existing-world-comparison`.
- Generator reruns are deterministic; `git diff --check` passes.

Stopping boundary: implemented on dev and delivered for owner review. Validation
uses Chromium desktop/phone viewport emulation, not physical-device or Safari
certification. Aesthetic approval and any promotion to main remain the owner's.
