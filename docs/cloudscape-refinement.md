# Cloudscape refinement

Goal: Complete cloud theme refinement. Worktree:
`/home/dlybeck/Projects/Portfolio-worktrees/portfolio-dev`, branch `dev`,
base `6e691aa` with prior theme work retained in the dirty worktree.

The owner rejected the current execution: clouds share too much silhouette and
the sky is too plain. The refinement must improve those visible characteristics,
not merely increase numerical variation counts. Vinyl is outside this goal.

Allowed: local Cloudscape SVG/JSON authoring, relevant tests, rendered captures,
documentation, and the existing private preview on port 51354. No main/push,
production deployment, random-selection promotion, or unrelated-theme changes.
Preserve the shared theme architecture, parent/child navigation, neighboring
destinations, title/summary/Open states, and Original fidelity.

## Proof conditions

- Distinct silhouette families and compositions, not small edits of one outline;
  recognizable, clean SVG cloud forms with restrained coherent shading.
- A composed sky with sparse distant cloud/wisp layers at different depths;
  no repetitive wallpaper, blurred circular blobs, or tile-like background art.
- A focused phone cloud stays within the viewport with breathing room. Neighbor
  labels and click targets remain visible/actionable. Readable text and controls
  fit the actual painted surface at 320/390/768/1440px.
- Stable Grow identity and reduced-motion behavior; all page content/navigation
  and the plain-paper weather notebook remain functional and readable.
- Actual desktop/phone visual inspection of Home, long copy, all silhouettes,
  navigation transitions, and opened pages. Geometry checks complement—not
  replace—visual judgment.
- Source/asset reproducibility, pack validation, focused regression, Original
  fidelity, and private URL checks. Final receipt links the review and states
  that aesthetic acceptance and random promotion remain the owner's decisions.

Validation commands: targeted pytest in the existing phase-1 venv using the
remote Playwright endpoint, `scripts/check_canonical_fidelity.py`, deterministic
authoring regeneration, and browser captures from the private preview.

## Implemented refinement

- Six independent cloud drawings: broad billow, low bank, left-heavy tower,
  tapered windbank, ragged-bottom cluster, and high swell. Per-location recipes
  choose silhouettes appropriate to the amount of copy; subtle warm/cool
  palettes and restrained underside shading remain declarative assets.
- Two irregularly placed distant sky layers: thin wisps at depth `.12`, low
  cloud banks at `.30`. The clean SVG language is retained, without textures,
  circular haze, characters, or new navigation behavior.
- Smaller measured phone footprint, narrower base-label safe areas, and
  readable focused interiors. The painted cloud—not its nominal CSS tile
  width—is the viewport acceptance boundary.
- Grow uses matching base/expanded drawings and an opt-in responsive scale
  derived by the shared engine. This fixes the visible initial shrink caused
  by using one hardcoded scale across phone/desktop SVG sizes. Other packs
  keep their configured scales; switching removes the derived overrides.
- Warm-paper weather notebook and its functional binding remain unchanged.
  The visual metaphor is an illustrated sky study with annotations and an
  associated observation notebook, not text physically printed on vapor.

## Evidence checkpoint

Actual rendered captures are in `/tmp/cloud-refinement-review`. Reviewed the
six silhouettes, Home, long ScribbleScan copy, and Tennis/Jobs documents across
320px/390px phone and 1440px desktop compositions. Motion frames at
0/100/200/400ms show the same cloud growing in place. The first screenshots
exposed full-width phone art; subsequent painted-outline tests caught two
clipped neighboring labels. Both were corrected rather than weakening checks.

- Pack, responsive readability, documents, recipe and returning-theme suite:
  **98 passed**, `/tmp/cloud-refinement-regression.log` (exit receipt `0`).
- Accepted-theme navigation, keyboard/touch, canonical restoration and
  document retheming: **31 passed**, `/tmp/cloud-refinement-navigation.log`
  (exit receipt `0`).
- `scripts/check_canonical_fidelity.py`: PASS. Original, Lily, Planets and
  Islands pack files have no diff. Shared measured scaling is opt-in only.
- Regenerating the whole Cloudscape pack produces identical SHA-256 results.
  `git diff --check` passes. Prior unrelated dirty work is retained.
- Final expanded acceptance suite: **26 passed in 48.85s**,
  `/tmp/cloud-refinement-final-acceptance.log` (exit receipt `0`). Covers all
  six silhouettes' first-frame size/position at 320/390/1440px; all 17
  locations' painted bounds, readable interiors and neighbor hit targets at
  320/390/768/1440px; resize and switching cleanup; touch/keyboard document
  round trips; distinct shapes, depth movement, and manual-only selection.
  An initial two-fixture test harness error was corrected by requesting only
  the selected Playwright fixture, then the complete suite was rerun.
- Private Tailscale URL opened Programs successfully with no JavaScript page
  errors. Programs' phone document, tablet Home, and Original after switching
  from Clouds were captured and visually inspected. Original retains taped,
  lined rectangular backing and its original inner document formatting.

## Completion audit

| Requirement | Authoritative evidence / outcome |
| --- | --- |
| Meaningfully varied cloud art | Six independently authored paths in `scripts/cloudscape_art.py`; six-family phone sheet and desktop captures visually reviewed. |
| Interesting but restrained sky | Two generated irregular-position layers, different depth coefficients; actual Home and nested neighborhoods inspected, layer movement verified in browser. |
| Comfortable phone composition and text | All-location painted-outline/label/hit tests at four widths; actual narrow-phone Home/long-copy and full six-family sheet inspected. |
| Stable motion and unchanged interaction | Measured starting size and center match existing art for all six families; actual transition frames inspected; reduced-motion, touch/keyboard and document round trips pass. |
| Readable notebook documents | Tennis photos and paragraph spacing pass browser checks; phone/desktop Tennis plus Programs/Jobs captures inspected, subject to the PDF-plugin limitation below. |
| Modular architecture and fidelity | Cloud visuals remain inert pack data; generic responsive scale is opt-in and cleaned on switch; schema/recipe suites and canonical guard pass; four approved pack directories unchanged. |
| Review delivery and authority | Private Tailscale preview verified; manual-only flags remain set; no main/push/deployment. Owner's keep/remove decision remains open. |

The refinement is complete for private review. This is not aesthetic approval
or a claim that Cloudscape must join the permanent collection.

## Owner review follow-up

The owner likes the refined sky visually but rejects the **Sky Observations**
book: the metaphor is not self-evident and does not naturally explain reading
portfolio topics such as Gaming. The prior engineering completion does not
approve this document concept. Do not rescue it by inventing explanatory lore.
The document design remains unchanged pending a replacement decision.

Unfocused titles also sat too low because all six drawings reused one base
content rectangle. A browser test comparing the label center with each cloud's
painted-area center reproduced the error at 320/390/1440px (roughly 14% vertical
displacement on the tall billow). Base markers now follow each silhouette's
optical center; the tapered bank uses a narrower area to preserve neighboring
labels at phone width. Focused artwork, motion, documents and runtime are
unchanged by this correction.

Correction validation: **12 passed**, `/tmp/cloud-title-alignment.log`; all
17 locations retain fitted readable text and usable phone neighbors. Before/
after screenshots inspected at 320/390/1440px (`/tmp/cloud-title-after-*.png`).
Canonical fidelity guard and diff checks pass. Private preview updated only.

At that follow-up, rule enforcement was still under discussion. The owner
subsequently authorized the Portfolio-only grounding-system goal; current
rules and review-system status are in `theme-grounding-review.md` and
`grounding-system-validation.md`. This does not approve or replace the rejected
Sky Observations document.

The headless Chromium Jobs screenshot leaves the embedded PDF pane blank;
it verifies notebook layout, not native PDF-plugin rendering. No PDF/content
changes are part of this refinement. Real-device/Safari certification and
owner aesthetic acceptance are not claimed.

## Review boundary

The owner's latest direction is to keep the ideas open, not to require either
Clouds or Vinyl to stay. Clouds remains manually selectable for review and
excluded from random rotation. This refinement does not approve or repair
Vinyl. No commit, main change, push, or production deployment was performed.
Private review: `http://100.118.63.4:51354/?theme=clouds`.
