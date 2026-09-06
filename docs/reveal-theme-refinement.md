# Reveal theme refinement

## Goal contract

Finish refining the two new themes the owner selected: Vinyl Collection and
Postcards & Letters. Their physical interactions, not just their still artwork,
must make sense. Deliver a visually verified private preview on local `dev`.

Worktree: `/home/dlybeck/Projects/Portfolio-worktrees/portfolio-dev`
Branch: `dev`; base: `63e567b`.

Authority: local implementation, declarative assets, tests, screenshots, local
commits, and the existing private preview on `0.0.0.0:51354`. No main changes,
push, production deployment, AI generator, or changes to Original/Lily/Planets/
Islands. Botanical and Workbench are not part of this refinement.

## Approved behavior

- Grow: the same object enlarges and shrinks.
- Cover: a larger separate surface arrives from a side, as in Original.
- Reveal/swap: a contained object emerges from behind its carrier and retracts.
  Vinyl draws a record from its sleeve. Postcards opens an envelope to reveal
  its card. No duplicate complete object arriving from off-screen.
- Preserve the existing `settle` compatibility preset used by approved themes;
  the new authoring choice is Reveal, not a forced migration of existing packs.
- Use shared, bounded part transforms and pack-owned artwork/configuration,
  not theme-name branches or theme-specific JavaScript.
- Base shows title; focused shows title, description, and existing Open link;
  opened Document behavior is unchanged. Neighbors and navigation never change.
- Review the whole interaction: what object is it, what happened on focus, and
  does reversing it still make physical sense? Do not approve from stills alone.
- Record remains circular. Lettering belongs on a physical printed/written
  surface. If a believable record label cannot hold the real summaries, use
  liner notes rather than distort the record or shrink text to unreadability.

## Proof

Validate schema/sanitization, new-pack installation without renderer edits,
motion reversal and rapid reselection, reduced motion, theme cleanup, direct
entry, keyboard and pointer navigation, real content fit at phone/tablet/desktop,
and opened Documents. Inspect motion-frame captures and final stills. Compare
all existing theme sources and representative renders to the base. Commit the
review candidate on dev with exact test and preview receipts.

## Implementation and visual findings

The shared `themeReveal.js` adapter installs bounded SVG part poses and attaches
the existing semantic text to the configured carrier. Pack validation rejects
missing/unknown parts, nonfinite or excessive transforms, invalid title safe
areas, and text on inverted or foreground parts. There are no theme-id branches
in the runtime. `docs/theme-pack-v1.md` documents the authoring contract.

Vinyl uses a circular record emerging from the same square sleeve: title on its
label, longer copy and Open on the sleeve. Postcards uses an opening envelope
with an extracted illustrated card. Both shrink/retract on leaving and reverse
from the currently rendered pose on reselection. No legacy cover exit is queued.

Visual review corrected an early card/envelope size mismatch, an exposed card
under a closed flap, translucent flap overlap during opening, duplicate titles
during closing, and insufficient separation between postcard artwork and long
titles. Final objects fit their carriers at both endpoint scales. Decorative
art stays secondary to readable content. The opened Documents retain their
existing liner-note/letter treatments; navigation and neighboring destinations
are unchanged.

## Validation receipt

- Full regression: **306 passed**, with one stale error-message assertion for
  the former three-value preset list. The validator correctly rejected the
  unknown preset; the assertion was updated to include Reveal. Initial receipt:
  `/tmp/reveal-full-tests.xml` and `/tmp/reveal-full-tests.log` (424.19 seconds).
- Final focused regression receipt: `/tmp/reveal-final-tests.xml` and `.log`.
  It includes the corrected assertion, all new-pack checks, all content-fit
  checks, and the dedicated Reveal behavior/authoring tests.
- Readability geometry: all 17 base/focused locations at 320, 390, 768, 1440px;
  separate label/content safe areas retain the existing minimum font checks.
- Reveal checks cover same-node identity, interrupted-transition continuity,
  rapid reselection, desktop/phone neighbor clicks, Open/Close, reduced motion,
  cleanup when switching to Original and back, carrier containment, recipe
  reproducibility, and independently named pack compilation.
- Reviewed desktop/phone stills, focused-location contact sheets and Documents:
  `/tmp/reveal-review-final`; final postcard artwork-spacing captures:
  `/tmp/reveal-postcards-final-390.png` and `-1440.png`.
- Reviewed opening/closing frames at 0/160/350/650ms in the actual shared
  renderer: `/tmp/reveal-motion-review`. Capture tool:
  `scripts/review_reveal_motion.py`. The final artwork-spacing correction does
  not alter the recorded movement geometry.
- Existing-theme Home/Tennis comparisons against the unchanged `559e304`
  preview: **15/16 PNGs byte-identical**. The only difference is eight Lily
  phone corner antialiasing pixels, maximum channel difference 4, bounds
  `(9,83)-(12,84)`. No content/layout difference. Evidence:
  `/tmp/reveal-existing-world-comparison`.
- Original, Lily, Planets, Islands, Clouds, Botanical and Workbench pack files
  are unchanged against the goal base. Running the complete authoring command
  leaves every theme file byte-identical. `git diff --check` passes.

Preview service: `portfolio-dev-theme-preview.service`, worktree `portfolio-dev`,
bound to `0.0.0.0:51354`. Review `?theme=vinyl` and `?theme=postcards` on
`http://100.118.63.4:51354/`. Main and production are not changed.

Stopping boundary: a tested local-dev review candidate, not aesthetic approval
or production promotion. Phone validation is Chromium viewport/touch emulation,
not a claim of physical-device or Safari certification.
