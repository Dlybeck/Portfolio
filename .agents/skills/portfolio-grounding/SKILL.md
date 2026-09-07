---
name: portfolio-grounding
description: Review Portfolio theme plans and pre-handoff visual work for physical continuity, whole-scene coherence, and unchanged navigation. Use for tiles, connectors, backgrounds, controls, animations, and opened documents; not for unrelated projects or nonvisual maintenance.
---

# Portfolio grounding

Challenge the design against the owner's rules; do not manufacture a story
that excuses it. This is a project-local review, not permission to redesign.

## Establish the review

From the repository root read `AGENTS.md`, the relevant terms in `CONTEXT.md`,
and `docs/theme-grounding-review.md` completely. Identify the current request,
authorized changes, affected scene, and approved elements to preserve. Read
referenced historical evidence only when relevant. A suggestion or agent
completion receipt is not owner approval.

## Plan checkpoint

Trace the proposed viewer experience: unfocused, focused, opened, and reversed.
For each changed object or cue, identify what it represents, what moves or
occludes it, and how any information change becomes visible. Assess the
objects, connectors, background, controls, and reading experience together.
Does the scene communicate its own logic, or only work after an explanation?

Compare navigation against the existing site; reject a plan that rearranges
tiles, replaces clicks, changes destinations, or makes viewers wait for or
follow decorative animation. Preserve artistic freedom inside that boundary.
An unproven creative idea may earn a bounded prototype, not final approval.
Record the specific uncertainty and the visible evidence that would resolve it.

## Pre-handoff checkpoint

Inspect the actual desktop and phone scene. View screenshots, not just save
them. For motion changes inspect intermediate frames, reversal, interruption,
and reduced motion; endpoints alone cannot prove physical continuity. For a
small change inspect the affected state and its surrounding neighborhood;
for a new theme cover Home, nested/long copy, and text/media-rich opened pages.
Include every affected theme. Known-bad cases are diagnostic fixtures, never
new visual baselines. Verify the preview corresponds to the source reviewed.

Use `scripts/check_grounding.py` for reproducible mechanical receipts; see
`docs/theme-grounding-review.md` for commands and evidence limits. Add targeted
tests when a newly found failure has a measurable seam. Geometry, asset hashes,
test counts, and a caption describing a metaphor cannot prove it is convincing.

Record one compact checkpoint in the task's existing notes: phase and scope,
source revision/dirty state, inspected evidence, specific findings, and next
action. Distinguish `ready` (reviewed within stated scope), `revise` (observed
failure), and `unverified` (missing evidence/authority). A plan being ready is
not a rendered result being ready; neither is owner aesthetic approval.

For each verdict account for navigation/Original preservation, physical
continuity, whole-scene/connector coherence, and readability/actionability.
Explain a dimension's irrelevance if it truly is unaffected; do not silently
omit connectors or opened pages from a whole-theme judgment.

Fix authorized failures and re-review the changed result. If the idea fails,
try a meaningfully different approach rather than rename the same decoration.
If fixing it exceeds the request, retain the finding and request authority;
audit-only work stays read-only. Carry unresolved findings across handoffs.

## Honest limits

This workflow makes scrutiny repeatable, not aesthetic judgment infallible.
Missing browser access means visual review is unverified. Mechanical success
does not override owner rejection. During review-system development, use
isolated fixtures to demonstrate failures; do not repair the live website.
