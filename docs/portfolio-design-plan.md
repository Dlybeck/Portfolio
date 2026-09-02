# Portfolio Design Plan

This plan preserves the portfolio as a living, explorable self-portrait while repairing accidental barriers and creating safe seams for future visual experimentation. It records the shared understanding reached during the September 2026 design grill; it does not authorize source changes or deployment.

## Product intent

- The portfolio is an authored personal experience, not a resume site or hiring funnel.
- The Viewer has priority. The experience should be unfamiliar and unique while remaining understandable at a glance.
- Exploration is self-guided. The Home note may provide a brief in-world clue for viewers who do not immediately infer the interaction, but there is no external tutorial or guided tour.
- Professional, educational, recreational, and historical work all contribute to the self-portrait. Age alone is not a reason to remove content.
- Curation comes from the graph: a centered section has one Parent and no more than three Children, producing a Neighborhood of at most five visible sections.

## Design invariants

- The parent-child Board remains the primary navigation structure.
- Home is the root of the Board.
- A destination link restores the Board at the requested location with its document open; content is not presented as a detached standalone site.
- Home and every visible website/document action work. Perfect browser-history reproduction is not a goal.
- The current Board Theme is the canonical public default.
- Board Themes may change any styling, including opened documents, but may not change topology, content, controls, URLs, the navigation sequence, responsive structural rules, or the general interaction experience.
- Opened documents retain a uniform Document Grammar for long-term maintainability. Its current v2-derived styling is acceptable but may be reconsidered as part of theme experimentation.
- The conversational voice and historical artifacts remain intact. Broken assets, spelling errors, wrong titles, stale factual labels, invalid markup, and broken links are defects rather than historical features.

## Workstream 1: Core integrity

### Repairs

- Fix the incorrect v1 image path.
- Recover the three unavailable v3 retrospective images from reproducible historical states when practical; otherwise remove or replace those image slots only after owner review.
- Correct spelling, obvious missing words, incorrect page titles, duplicate element identifiers, and unambiguous accessibility labels without rewriting the author's voice.
- Change the University of Puget Sound Technology Services end date to May 2025.
- Verify all visible internal and external links rather than assuming that preserved URLs still work.
- Ensure direct content URLs load the Board, move to the corresponding location, and open the requested document.
- Separate internal document rendering from the viewer-facing canonical route as needed so iframe loading does not create redirect loops.
- Ensure `/` means Home and all Home, Open, Close, Back, and nested document controls work.

### Review boundary

Mechanical corrections may be made directly. Changes to claims, dates other than the confirmed Technology Services end date, employment status, tone, or historical meaning require owner review.

ScribbleScan's historical performance claims remain on its pages. Numerical and `industry-leading` claims are excluded from structured/search metadata, and the current copy is not otherwise rewritten in this effort.

## Workstream 2: Inclusive professional discovery

### Keyboard interaction

- Keyboard navigation follows the Board hierarchy rather than the full offscreen DOM.
- The focus cycle includes the Parent, up to three Children, and the centered section only when it exposes an actionable document.
- Enter or Space moves to a focused neighbor or opens the centered document.
- Escape goes back within nested documents, closes a top-level document, moves one Parent step toward Home from the Board, and does nothing at Home.
- Focus treatment appears through `focus-visible` and should look native to the current theme.
- Pointer and touch behavior remain unchanged.

### Accessible adaptation

- Home and Close/Back use semantic controls.
- Meaningful images, iframes, and controls receive useful names; decorative media uses empty alternative text.
- Reduced motion responds only to the viewer's operating-system preference and does not alter the default animated experience.
- No separate accessibility mode or settings panel is introduced.

### Professional discovery layer

- Canonical domain: `https://davidlybeck.com/`.
- Search-facing title: `David Lybeck | Innovation AI Developer`.
- Search-facing description: `David Lybeck is an Innovation AI Developer and software builder exploring AI, handwriting recognition, 3D design, tennis, and personal projects through an interactive portfolio.`
- Current professional fact: Innovation AI Developer at Denali Advanced Integration since August 2025.
- Structured `Person.sameAs` identities:
  - `https://github.com/Dlybeck`
  - `https://www.linkedin.com/in/davidlybeck/`
- Do not publish email in structured metadata.
- Do not put ScribbleScan comparison numbers or `industry-leading` language in structured metadata.
- Add canonical, page-specific description, Open Graph, social-card, and appropriate `Person` structured metadata.
- Use a stable wide capture of the canonical Home Board as the social-preview image, incorporating the existing Personal Mark for now.

The bundled resume is stale and predates the Denali role. Replacing it is worthwhile but remains outside this effort; do not silently rewrite or fabricate a replacement.

## Workstream 3: Theme laboratory

- Add a simple theme selector to the navbar for development.
- Disable the selector for deployment.
- Unknown or unavailable themes fall back to the canonical current theme.
- Group alternate Board styling and any shared document-restyling prototype inside the same theme work.
- Preserve the current theme unchanged as the comparison baseline.
- Prototype a replacement Document Grammar against at least two dissimilar content types before considering adoption.
- Do not publicly randomize themes or ship an alternate theme until it independently meets the full acceptance gate and receives owner approval.

## Deferred work

- Create or select a new Personal Mark.
- Produce dedicated favicon, navbar, full-resolution, and social-preview derivatives of that mark.
- Update the resume.
- Randomly assign public themes.
- Remove historical coursework merely because it is old.
- Convert the visible site into a professional landing page.

## Acceptance gate

- Canonical desktop and phone captures remain visually equivalent unless an individually approved repair requires a visible change.
- Pointer and touch navigation behave as before.
- Every Board location retains one center and at most four neighbors.
- Direct content links open the intended document within the Board.
- All routes and visible buttons pass a link check.
- Keyboard behavior matches ADR 0004.
- Reduced motion affects only viewers who request it.
- Metadata validates, uses confirmed professional facts, and exposes no unintended private information.
- Theme controls are absent from the deployment configuration.
- Theme and document experiments are compared against the canonical current experience rather than assumed to be improvements.
- No source implementation, commit, push, or deployment proceeds from this plan without explicit owner approval.
