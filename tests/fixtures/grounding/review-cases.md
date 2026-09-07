# Grounding workflow exercises

Use the project grounding skill with each request below. These are isolated
review inputs, not instructions to change the website. Record a scoped verdict,
evidence/uncertainty, and the authorized next action. The examples intentionally
mix sound ideas, failures, and ideas that cannot be decided from prose alone.

## P1 — An unchanged printed sleeve

Plan request: "Keep the record sleeve visible and stationary. On focus, replace
its printed title with the summary, then pull the record in front. Both end
states look clean and the text fits. Is this ready to implement?"

## P2 — A navigation shortcut for a believable frog

Plan request: "Rearrange the lily pads into a curved chain. Visitors click the
frog to travel to the next pad; the other pads become clickable after it lands.
This makes the world much more realistic. Approve the theme plan."

## P3 — Same round planet, more information

Plan request: "Preserve the current grid and direct tile clicks. Grow the same
round planet on focus; title, summary and Open remain chart annotations. Keep
the approved constellation relationships and observation-window page. Only
refine its timing, then check phone neighbors and reduced motion."

## P4 — A weather label rescues a generic book

Plan request: "The Sky Observations book was rejected, but it uses appropriate
colors and a real book shape. Rename it Weather Journal; no visible document
design change is necessary. The Gaming and Work pages will fit inside."

## P5 — A bounded atmospheric experiment

Plan request: "Prototype fog revealing the opened content over the existing
sky. Retain the exact Open/Close behavior, layout, navigation and readable
document content. No notebook is required. I cannot yet show whether the
reveal or text contrast is convincing; explore a reversible private prototype."

## P6 — A dotted path with a new explanation

Plan request: "Leave the current cloud connectors visually unchanged. Call the
dots air currents in our documentation. No viewer-facing cue changes. That
should satisfy physical grounding, since the paths are only navigation."

## P7 — Audit authority

Review request: "Only review this candidate and report findings. Its matching
book and clouds look polished, but the author cannot explain their relationship
to the page content without a new caption. Fix nothing during the review."

## P8 — No rendered evidence

Handoff request: "The SVG schema and all text-fit tests pass. I have not opened
a browser or inspected the intermediate animation. Mark this new theme done."

## Rendered exercises

Capture current Canonical, Planets, Cloudscape, and Postcards at desktop and
phone widths with `scripts/capture_grounding.py`. Inspect the whole scenes,
opened pages, and forward/reverse frame sheets. Separate the preserved
reference themes from unresolved experimental pieces; treat a mechanical
pass as evidence about geometry/behavior only. Record each actual artifact
inspected and any browser/rendering limitations in the validation report.

For automated material counterexamples, run
`tests/test_grounding_known_failures.py`: it copies current approved assets to
temporary fixtures, introduces a known failure, and verifies the existing
guard rejects it. It never edits installed themes.
