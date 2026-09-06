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
Final validation is in progress; preview is private and local to dev:
`http://100.118.63.4:51354/?theme=vinyl` (also `botanical`, `workbench`, `postcards`).

Planned validation: `tests/test_new_theme_packs.py`, existing theme/keyboard/
document tests, `scripts/audit_theme_variants.py`, canonical fidelity, and visual
review captures from the dev preview on desktop and phone.
