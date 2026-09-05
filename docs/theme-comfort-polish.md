# Theme comfort polish

## Goal contract

Polish Lily Pond, Planets, and Island Chain so text, controls, and opened pages
feel comfortably sized, readable, and naturally placed on desktop and phone.
Preserve their visual identities, Original Paper, navigation, and modular theme
architecture. Deliver a preview for owner review.

Worktree: `/home/dlybeck/Projects/Portfolio-worktrees/portfolio-phase-1`
Branch: `codex/theme-comfort-polish`
Base: `06ab2d362cdbeb5f21cb4f38d14bb059f988ed02`

Authority: local edits, tests, screenshots, commits, and the existing private
preview. Production deployment is outside this delivery target.

## Evidence and approach

- Inspect every Board location in the three alternate worlds at desktop and
  phone sizes, plus representative text, photo, and model documents.
- Improve readable sizes and whitespace by adjusting pack-owned typography,
  usable content areas, proportions, and visual weight. Avoid solving fit by
  squeezing text smaller or adding arbitrary text-box backgrounds.
- Retain recognizable leaf veins, shorelines, planetary features, notebook
  binding, and observation-window construction; reduce competition with text.
- Verify safe-area fit, readable minimum sizes, navigation, and theme switching.
- Compare Original Paper against the base; it is a preservation constraint.
- Capture the final private preview and inspect the images before delivery.

Validation: focused `tests/test_themes.py` layout and keyboard checks,
`tests/test_theme_packs.py`, `tests/test_destination_links.py`, and
`scripts/check_canonical_fidelity.py`; broaden only when failures warrant it.

Initial evidence: 24 production screenshots in
`/tmp/portfolio-polish-review`. Lily veins cross body text; Island Work Experience
crowds the lower shoreline; light Planets text washes out on pale surfaces;
phone notebook paragraphs wrap into narrow columns.

## Delivered candidate

- Alternate Board text is larger, higher contrast, and more consistent across
  summaries and actions. Focused objects have more room, and their independent
  rotations remain varied but less steep for reading. Neighbor positions and
  navigation logic are unchanged.
- Fixed a geometry mismatch: proportional container bounds ignored SVG
  letterboxing and offsets. Packs can now opt into rendered-SVG coordinates;
  content remains inside the actual object instead of merely passing a box
  overflow check. Canonical keeps the historical mapping.
- Veins and surface details retain their shapes but compete less with letters.
  No text-box overlays, new decorative objects, or theme-name renderer branches.
- Alternate Documents use wider phone reading columns, comfortable notebook
  type, compact title spacing, and separation between adjacent photographs.
  Their approved notebook, expedition-log, and observation-window shells remain.
- `scripts/polish_theme_assets.py` records the idempotent candidate authoring
  pass. The installed JSON and SVG files remain the runtime source of truth;
  the script is not a rendering dependency. If older asset-generation scripts
  are rerun, reapply this pass before review.

## Validation receipt

- Visually inspected all 17 expanded locations in each alternate theme at
  1440x900 and 390x844, plus full Board neighborhoods and text/photo/model
  Documents. Also inspected difficult Puzzles layouts at 320px and tablet size.
- Browser regression assertions cover all base and expanded content against
  the actual rendered SVG marker at 320, 390, 768, and 1440px. They enforce
  readable minimum type sizes and verify phone Document reading width,
  photo separation, and lack of horizontal overflow.
- Original's existing presentation values, assets, and variation assignments
  are unchanged. Canonical fidelity checker passes. All six representative
  Original Document screenshots and all 34 isolated tile captures match the
  baseline byte-for-byte. Two initial phone Board captures differed because
  locator screenshots scrolled the map; the review script now uses viewport
  crops that do not move the camera.
- First full regression run: 239 passed, one stale reduced-motion assertion
  expected 800ms instead of Original Home's existing 790ms variation. Updated
  that test to pin Original and account for its variation; accessibility
  rerun: 3 passed. No animation behavior was changed to satisfy the test.
- Final complete regression rerun: **240 passed in 256.46 seconds**.
  Receipt: `/tmp/theme-comfort-verified-tests.xml`; log:
  `/tmp/theme-comfort-verified-tests.log`.
- Authoring script idempotency and `git diff --check` pass.

Local visual evidence: `/tmp/theme-comfort-before`,
`/tmp/theme-comfort-reviewed` (six contact sheets, individual screenshots,
Documents, and measurements). Final Island ink was additionally checked in
`islands-final-ink.png`; narrow-device checks use `*-narrow-*.png`.

Review preview: `http://100.118.63.4:51353/?theme=lily` (also `planets` and
`islands`). Existing preview service remains bound to `0.0.0.0:51353`.

Stopping boundary: candidate prepared for owner visual review, not promoted to
main or production. Validation used Chromium viewport emulation, not a physical
phone or every browser engine. Final aesthetic acceptance remains the owner's.
