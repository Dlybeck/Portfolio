# Reality-grounding review

Owner feedback, 2026-09-05: the oval planets are not an acceptable source of
variation. Review physical coherence, not just readability and fit.

This refines the accepted alternate artwork without changing Original Paper,
the Parent/Child Neighborhood, or the approved Viewer Artifacts. It supersedes
earlier blanket instructions to retain every alternate silhouette unchanged.

## Corrections

The reproduction found 24 SVG states with elliptical planet bodies. Programs
used radii 62 x 43; these were authored shapes, not viewport stretching. The
previous visual review missed this despite checking overflow and readability.

- Planets: circular projected globes at varied radii. Variation lives in size,
  surface, palette, moons, rings, and orientation, not squashed planetary bodies.
- Surface markings clip to the globe. Atmospheric edging follows its limb.
  Ring systems remain elliptical because they depict an inclined flat plane;
  separate rear/front arcs establish occlusion without double-painted seams.
- Lily Pond: ripple accents now sit on water behind the leaf, not on the leaf.
  Preserve the accepted leaf contours, notches, veins, flowers, and Grow motion.
- Island Chain: retain irregular coasts, beaches around land, lagoons enclosed
  by land, offshore islets, and water currents. This pass found no comparable
  silhouette/material defect requiring new island art.
- Opened pages: retain the approved notebook binding, expedition-log corners,
  and observation-window frame. They already identify a carrier for the text;
  no new telescope, coffee stains, creases, or narrative machinery is needed.

## Rule for subsequent authoring and review

Ask what each mark represents, what surface it belongs to, and what should
occlude it. A variation axis is not valuable if its outputs violate the object.
Flat leaves and islands can have oblique/irregular outlines; planetary globes
do not become ovals to fit text. UI annotations and invariant relationship
connectors remain navigational conventions, not literal objects to invent.

Keep the established clean SVG language. Physical coherence is not a request
for photorealism, exhaustive simulation, or more decoration.

## Reproduction and maintenance

`tests/test_theme_grounding.py` failed before correction on oval bodies,
unclipped surface art, missing front/back ring segments, and leaf-top ripples.
It also checks the rendered planetary aspect ratio at phone and desktop sizes.
Existing fit tests independently protect readable text and safe regions.

`scripts/ground_theme_assets.py` is an idempotent authoring pass. If historical
asset exporters are rerun, run comfort polish first, then grounding. Runtime
continues to consume only declarative Theme Packs and sanitized SVGs; no new
renderer behavior or theme-name branch was introduced.

Visual evidence: `/tmp/theme-grounding-final` contains desktop/phone contact
sheets and document captures. Final ring-seam/limb refinements were inspected
in `/tmp/planet-final-*-390.png` and `/tmp/planet-final-*-1440.png`.

Preview only; no main or production changes.

Validation receipt: pack/grounding/comfort run 71 passed; final targeted
grounding, rendered-circle, safe-area, and Home fit run 14 passed. Both modified
packs pass the sanitizer/manifest validator; Canonical fidelity and authoring
idempotency checks pass. No runtime, navigation, Island, or Original asset files
changed in this correction.
