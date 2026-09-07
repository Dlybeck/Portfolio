# Vinyl packaging: reality check

Research date: 2026-09-07. Scope: answer the owner's questions about Vinyl
prototype B's nested packaging and C's loose paper. No website edits,
integration, deployment, or new aesthetic approval.

## Manufacturer evidence

- An inner sleeve is a protective pocket around the record, placed inside
  the outer jacket. Printed inner sleeves can carry lyrics and artwork;
  nested packaging is intentional, not a second invented case.
  [Precision Record Pressing: inner sleeves](https://www.precisionpressing.com/print/inner-sleeves)
- Separate printed inserts are available for liner notes, lyrics and artwork,
  including single sheets and folded formats. They are an optional packaging
  element, not something every record must include.
  [Precision Record Pressing: inserts](https://www.precisionpressing.com/print/inserts)
- Vinyl Plant independently describes inner sleeves fitting outer jackets
  and shows actual products with these combinations.
  [Manufacturer packaging catalog](https://vinylplant.ee/vinyl_packaging/)

Viewed manufacturer photographs in Chromium, not merely their captions:

- [Printed inner sleeve and outer jacket](https://vinylplant.ee/wp-content/uploads/2024/12/VP_Vinyl_Outer-Single-Pocket-k367.webp)
- [Outer jacket, paper insert, black inner sleeve and record](https://vinylplant.ee/wp-content/uploads/2024/12/VP_Vinyl_Outer-Single-Pocket-jv-k460.webp)

Browser inspection captures: `/tmp/vinyl-packaging-research-sleeve.png` and
`/tmp/vinyl-packaging-research-insert.png`. These references are evidence, not
assets licensed or copied into the theme.

## What this establishes for our prototypes

**A: rejected by the owner.** Its oversized-label direction is not a candidate.

**B: grounded concept, imperfect drawing.** Jacket + printed inner sleeve +
record is a supported arrangement. However, the current prototype's paper
pocket is 216 units wide and only 159 tall; the disc is 196 units across
(`static/prototypes/theme-grounding.js`). If that drawing represents the
entire sleeve, it could not fully contain the record. A future revision should
depict a near-square, full-sized sleeve with a credible opening and a partly
withdrawn record, distinguish thin paper from the heavier jacket, and retain
the extract/place sequence. This is our design inference from the references,
not a manufacturer's endorsement of the animation. Phone fit must be solved
without making the sleeve physically too short again.

**C: real object, separate handling question.** A loose liner-note sheet is
authentic. Our insert must remain visibly separate paper, not a label glued
over the grooves. The existence of inserts does not prove the current coupled
record/insert movement is convincing. B has a clearer physical relationship
because its paper actually holds the record; this is a recommendation, not
owner acceptance.

Grounding verdict for this research: B and C have real-world references, but
neither current rendering receives a blanket pass. No new rendered behavior
was implemented or visually certified. Navigation, Original, opened pages,
connectors and runtime are unchanged; their earlier unresolved findings remain.
