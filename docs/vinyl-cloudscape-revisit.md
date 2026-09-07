# Vinyl and Cloudscape revisit

Owner request: revisit both concepts, keeping the previously agreed navigation,
physical continuity, readability, modularity, and Original fidelity rules.
This supersedes their dormant disposition in `full-realism-polish.md`.

## Subsequent owner review

The owner rejected this iteration: Vinyl did not read clearly as a record and
crowded out the phone neighborhood; Clouds remained too similar against a plain
sky. The passing checks below are historical engineering evidence, **not owner
acceptance**. Neither concept is required to stay. Both remain open experiments,
not random-refresh candidates. The current Cloud-only follow-up is documented
in [Cloudscape refinement](cloudscape-refinement.md); it does not repair or
approve Vinyl.

## Vinyl: printed picture disc, not an oversized center label

The earlier black-record design only made the small center label writable, then
improperly moved the description onto the sleeve. The revised record is a
picture disc: printed artwork beneath the playable surface is a real production
format ([manufacturer reference](https://www.duplication.com/picture-disc-pressing/)).
This makes a larger printed area credible without pretending a normal record
has an enormous paper label or allowing its jacket's writing to change.

The printed title sits above the spindle; summary and controls sit below it.
The disc stays round, fits inside its square jacket, fully clears the top edge,
then moves in front and rests on the jacket. Closing reverses that path.
The jacket's own title remains attached and unchanged. Full pages use the
existing cream liner-notes document treatment. Swap pacing stays at `.8s`.

The shared Swap renderer now accepts the existing optional title-area marker
when `reveal.titlePart` equals `swap.movingPart`. This is a split printed layout
on one surface, not permission to put the title on an independently moving part.
Both rectangles are sanitized and validated. There are no installed-theme-name
branches in runtime code. Postcards' layout remains unchanged.

## Cloudscape: cumulus study and weather-observation notebook

Recognizable irregular lobes and a flatter shaded underside replace circular
text holders. Per-location peaks, hues, underside, highlights, wisps, and small
orientation differences remain deterministic pack-owned variations.

The board is an illustrated sky study, with the same annotation convention as
the accepted planet/island maps—not literal ink magically suspended in vapor.
The same cloud grows on focus; it does not turn into a card. Connectors are
restrained dashed diagram lines, not physical strings through clouds. The sky
has a quiet color gradient, no repeated ellipse wallpaper or blurred disks.

Opening a location reveals a weather-observation notebook: pale paper, a slate
cover, functional binding rings, and the existing reading layout. It is not blue
paper, a cloud-shaped document, or a simulated cockpit. This is an illustration
with an associated field document, not a claim the notebook is floating in sky.

## Review boundary

Both are enabled for direct URLs and manual selection in the private preview.
Both remain **excluded from random refresh selection** pending owner review.
No main push or production deployment is authorized by this task. Original and
the accepted Lily, Planets, Islands, and Postcards art must remain unchanged.

Authoring: `python scripts/refine_collection_reveals.py` and
`python -m scripts.revisit_cloudscape`. The collection builder also preserves
Vinyl's manual-only review status. The scripts emit inert SVG/JSON assets; they
are not runtime renderers.

## Validation / preview receipt

- Readability and opened-document checks for both returning themes at
  320/390/768/1440px: **10 passed**, `/tmp/returning-comfort-final.log`.
- Initial broader pack/swap suite: 109 passed, one Vinyl palette-evidence
  failure. The artwork was outside its declared palette group; grouping it
  correctly repaired the authoring audit without changing the physical layout.
- Final targeted authoring/variation/independent-pack checks: **6 passed**.
  The prior run already passed record clearance, stable writing, neighbor
  hit testing, spindle avoidance, and cleanup/reactivation assertions.
- Original fidelity guard passes; no edits to Original/Lily/Planets/Islands
  pack sources. The prior turn's Postcard timing/chooser-focus work is retained.
- Actual rendered previews: `/tmp/portfolio-returning-themes`; all-location
  catalog and forward/reverse motion sheets: `/tmp/portfolio-returning-final`.
  Reviewed phone and desktop captures, including long descriptions and pages.
- Expanded regression completed: **253 passed in 360.09s**, recorded in
  `/tmp/returning-final-regression.log`. This covers theme selection, rendering,
  comfortable content geometry, documents, physical swaps, pack validation,
  and the returning-theme checks.
- Final continuation check: both private review URLs return HTTP 200 with all
  17 locations reporting fitted content. Fresh phone screenshots were visually
  inspected (`/tmp/returning-final-live-vinyl.png` and
  `/tmp/returning-final-live-clouds.png`). Original fidelity and diff checks
  still pass. No additional design changes were needed after the regression run.

Private previews: `http://100.118.63.4:51354/?theme=vinyl` and
`http://100.118.63.4:51354/?theme=clouds`. Changes remain local on `dev`.
