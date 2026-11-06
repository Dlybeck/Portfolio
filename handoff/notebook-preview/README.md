# Notebook preview handoff (reference only; delete this folder in the step 1 PR)

This is the approved design for the davidlybeck.com rebuild: round 17 of the preview Boss reviewed on Nov 4 to 6, 2026.
Build plan: `build-plan.md` (Boss approved it on Nov 6, including retiring the old board and theme packs and testing handwriting reading first).

## What to build from
- `preview.html` is the whole preview as one self-contained page (it opens on round 17). Images and models are not included: every picture in it came from this repo's `static/` folder, converted to webp, so use the originals here.
- The approved direction is the mount made by
  `R7.make('cover13a','tr-worn tr-vinyl tr-r9 in-worn in-r12 in-r13 c14 s15b s16 s18')`
  i.e. the kraft worn-notebook cover with vinyl stickers (cover13a, take A, no TENNIS sticker), the worn inside pages, the round 14 contents, and round 17's layout (s18: one scrolling page per story; swipe only on rows marked data-sw16: site version snapshots, the seven themes, the 3D models).
- Everything else in the preview (other covers, sticker sets, typists, round 15 to 16 layouts, the comparison shell) is history. Don't port it.

## Source files (`src/`)
Built by `build.py` in this order. CSS: r2 to r9, r11 to r18. JS: r1 code from `index.r2.html` lines 459 to 728 (logo, reduce-motion, R1 helpers), then r2, r3, r4, r5, r6, r9, r12, r13, r14, r15, r16, r17, r18, r7, r11, shell.
- r2: notebook engine (pages, page turns, phone tuck, page order PH and DK, secOf, notebook()).
- r4: the side wheel (momentum, live page flips, cover detent).
- r6, r12, r13: live cover stickers (ScribbleScan pad, now pill, printer, puzzle, name tag that rewrites in five hand fonts, trail stamp, tennis ball spin, raccoon, blank sticker maker).
- r7: cover maker `R7.make` and cover open/close. r9, r11: sticker set and inside-page accents.
- r14: all page contents in Boss's wording (`R14.BODY`, jobs, courses, archive, games, versions, themes). Text came from `templates/pages/*`; move text from the templates, don't retype.
- r15: swipe row decorator (only rows inside `[data-sw16]` matter now). r16.css: swipe styles.
- r17: the content split into sections (`CH`); r18: joins them into one scrolling page per story.
- shell.*: the comparison wrapper around the preview. Not needed.

## Things the preview faked
- Link chips (dashed) are real links on the live site: take the targets from the current templates.
- 3D models were converted to glTF JSON for the preview; use `static/3Dmodels/*.glb`, and serve model-viewer from the site instead of a CDN.
- NBA predictor was a sketch; wire it to `static/json/results.json` like the current page.
- Say hi: email, LinkedIn and resume come from Boss before step 5.
- ScribbleScan pad shows typed text; step 4 tests a phone-sized handwriting model first.
