# Full realism polish

Vinyl and Cloudscape's previous removal decisions are superseded by the owner's
authorized [revisit](vinyl-cloudscape-revisit.md). They are now manual-preview
candidates, still outside random rotation pending review.

## Owner follow-up: timing, chooser focus, and dormant designs

The owner likes the corrected Postcard Swap but requested Original-like pacing.
Postcards now uses `.8s` instead of `1.1s`, preserving the staged physical path.
The chooser's unconditional `:focus-within` outline reproduced on pointer input
and persisted across Lily → Planets. Its shared presentation now tracks keyboard
input explicitly: pointer use has no keyboard ring, while Alt+T and keyboard use
retain it. Native select focus and semantics are preserved.

Vinyl's removal is a current label-layout failure, not an inability to use Swap.
The owner has reopened that design question and expressed renewed interest in
Cloudscape. Neither should be described as permanently rejected; both remain
dormant pending a revised design. No re-enablement is part of this timing/focus fix.

Active goal: **DO a full realism polish,. Removing any themes that cannot keep it**

Worktree `/home/dlybeck/Projects/Portfolio-worktrees/portfolio-dev`, branch `dev`,
base `0c737aa`. Local source, pack selection, assets, tests, captures and commits
are authorized. Deliver a private preview on `0.0.0.0:51354`. No main changes,
push or production deployment. Preserve Original literally. Preserve navigation,
neighbor availability, content, readable controls, and declarative architecture.
Removing a failed theme means disabling selection and random eligibility while
retaining recoverable source, not deleting project history.

## Correction to the prior receipt

The owner rejected the Reveal implementation despite its passing tests. Its
contract described the wrong endpoint and permitted writing to change on an
unchanged sleeve. The earlier completion receipt is not aesthetic or physical
acceptance. This document supersedes its interpretation of approved behavior.

Swap means **extract fully, bring in front, lay on top**; reverse those actions
on leaving. Both surfaces retain their own writing throughout. No replacement
writing, fade-through-material, stretching, object duplication, or sliding
through a closed edge. The extracted object must fit its carrier at matching
scales. A readable description cannot be justified by inventing an enormous
record label, writing on grooves, or relocating it onto a magically changing box.

## Acceptance / execution

Audit every installed theme: unfocused, focused, opening/closing, rapid reversal,
background, connectors, controls and opened Documents on desktop and phone.
Original is a preserved approved reference, not subject to reinterpretation.
The accepted natural worlds may use their established diagram/map annotations;
do not confuse annotations with physically printed surfaces, nor use that
distinction to excuse an impossible material or motion.

For every theme record a keep/fix/remove decision with rendered evidence. A
theme failing physical coherence or readable content is not selectable pending
repair. Disabled experimental themes cannot enter refresh randomization or be
forced through a direct URL. Preserve their source for recovery.

Implement genuinely staged Swap where it can meet the rule. Confirm object/text
identity, clear extraction before layer changes, opaque occlusion, reverse order,
neighbor clickability during motion, reduced motion and theme-switch cleanup.
Then run schema/registry/geometry/navigation/document/fidelity checks. Finish
only after the full catalog audit, required fixes/removals, actual visual review,
and private review delivery are proven. Green tests alone are insufficient.

## Current evidence

- Inventory: Original, Lily, Planets, Islands, Vinyl, Postcards, Botanical and
  Workbench are enabled; Clouds is already disabled.
- Vinyl and Postcards currently use the rejected two-pose Reveal. They need a
  new physical/content assessment, not a timing adjustment.
- Botanical and Workbench remain initial sketches, not owner-approved themes.

Validation/capture commands and resulting decisions are recorded below as work
is completed. This goal is active; none of the above is a completion claim.

## Catalog decisions

| Theme | Decision | Physical reading / finding |
| --- | --- | --- |
| Original | Preserve | Approved chalkboard, taped paper and arriving cover; literal fidelity boundary. |
| Lily Pond | Retain | Recognizable pads, veins and ripples; focus enlarges the same mapped object; field-notebook Documents. |
| Planets | Retain | Round bodies, rings and star-chart annotations; existing bounded background depth; observation-window Documents. |
| Island Chain | Retain / correct motion | Irregular coasts, beaches and ocean currents; replace fading land with Grow at measured closed scale; retain chart annotations and expedition-log Documents. |
| Postcards | Fix | Replace rejected extraction-only Reveal with a true opaque, staged Swap and persistent writing. |
| Vinyl | Remove from selection | The requested information does not fit the current record label at comfortable phone sizes. The previous implementation hid that failure by changing the sleeve's writing. The current design does not establish a credible record-on-top reading layout; retained source is not a claim that future vinyl designs are impossible. |
| Botanical | Remove from selection | Unapproved physical-card sketch; focused content changes on the mounted specimen's presentation rather than showing a coherent new physical surface. |
| Workbench | Remove from selection | Unapproved generic clipped-paper sketch, not a convincing distinct workbench interaction. Do not retain rejected sketches merely because their SVGs validate. |
| Clouds | Keep removed | Previously rejected, disabled physical metaphor; no redesign authorized. |

Removed themes keep their source but have both selection flags false. The
authoring command preserves those exclusions. Direct URLs, manual selection
and refresh randomization must all exclude them.

## Evidence and implementation checkpoints

- Baseline full catalog: `/tmp/portfolio-realism-baseline` (48 actual Home,
  long-copy and Document captures, desktop and phone). Catalog contact sheets
  inspected at both sizes. Existing documents/materials of retained natural
  themes do not need a new interpretation.
- Vinyl capacity receipt: `vinyl-label-capacity.json` in that directory. The
  current label is about 140px across. At phone size ScribbleScan's existing
  roles occupy 155px vertically even with its summary wrapping at a much wider
  199px. This excludes gaps, the circular edge and the spindle hole. This is
  evidence against the current design, not a claim that no future vinyl theme
  could ever work. An oversized label, groove text, or magically rewritten
  sleeve is not the fix.
- Shared `themeSwap.js` now owns reversible staging and opaque part planes.
  SVG/text nodes persist; the carrier title is independent, fixed writing.
  Postcard and envelope have matching contained dimensions. Extraction occurs
  before enlargement so neighboring tiles remain available.
- Initial rendered correction closed a small gap between the envelope pocket
  and flap that exposed the hidden card's writing. Initial browser tests also
  caught a first-paint pose delay on theme reactivation; installation now sets
  the pose before painting.
- Focused checks: **39 passed** in `/tmp/realism-focused.log`; staged Swap and
  exclusion checks: **17 passed** in `/tmp/realism-swap-final.log`.
- Final motion-frame review, refreshed Postcard captures and preservation
  comparison are complete; receipts are below.

The final motion audit found Islands' legacy Settle made land fade in/out.
Its preset now uses Grow with a `.38` endpoint scale, matching the measured
phone silhouette ratio `.377`. Grow's `.82` opacity endpoints are also removed:
Lily, Planets and Islands retain their solid materials throughout focus motion.
Their final artwork/Document states are unchanged; Original's Cover is untouched.

Broad regression before this final motion-only adjustment: **286 passed in
367.09 seconds**, `/tmp/realism-full.xml` and `/tmp/realism-full.log`.

## Completion audit / review delivery

| Requirement | Current evidence |
| --- | --- |
| Full catalog reviewed, not only the two new themes | Eight initially selectable themes captured in both viewports, Home/long-copy/Document; disabled Clouds assessed against its existing rejection. Per-theme dispositions above. |
| Physically coherent retained interaction | Final actual navigation sequences for all five retained worlds in `/tmp/realism-motion-final`, reviewed on phone and desktop. Postcards extracts, changes depth while clear, and rests on top; Grow no longer fades solids. |
| Constant writing / opaque occlusion | Browser samples assert persistent SVG/HTML identity, unchanged carrier and card writing, constant opacity, measured carrier clearance at the depth crossover, and exact depth order in both directions. No caption replacement rescues Vinyl. |
| Readability and usable controls | All 17 base/focused locations at 320/390/768/1440px; final Postcard contact sheets and opened Tennis/Programs/model Documents in `/tmp/realism-postcards-final`. Inspected both desktop and phone sheets. |
| Navigation, reversal, reduced motion, cleanup | Browser pointer and emulated-touch navigation, keyboard Open/Close, interrupted reversal, instant reduced-motion endpoints, and Original → Postcards reactivation. Neighbor hit tests exclude only offscreen destinations and existing fixed navbar occlusion during the unchanged camera transition. |
| Failed themes unavailable | Vinyl, Botanical, Workbench and Clouds excluded from registry selection, runtime selector, direct theme URLs and random candidates. Source retained; authoring reruns preserve exclusion flags. |
| Original preserved | Canonical fidelity guard passes. Home/Tennis desktop and phone screenshots match the unchanged baseline exactly. Existing-world comparison has 15/16 byte-identical PNGs; the lone Lily phone document difference is rasterization at a page corner, not a source/layout change. |
| Modular architecture preserved | Swap is three inert parameters plus bounded existing part poses; sanitizer/schema/model reject missing parts, invalid lifts, mismatched contained scales, and transparent parts. Independent-name fixture compiles. No installed theme IDs in runtime. |
| Regression and reproducibility | Broad suite 286 passed; final theme-focused suite **173 passed in 282.53 seconds** (`/tmp/realism-final-focused.xml` / `.log`); explicit solid-Grow checks **3 passed**; latest strict model/recipe tests **17 passed**. Asset/schema regeneration is byte-identical and `git diff --check` passes. |

Preservation captures: `/tmp/realism-existing-world-comparison`. Natural-world
SVG artwork and opened Document styles remain unchanged; Island motion tokens
and Grow's opacity are the deliberate final corrections, so preserving their
former fading transitions is not the criterion.

Delivery is the existing private local-dev preview:
`http://100.118.63.4:51354/?theme=postcards` (also `canonical`, `lily`, `planets`,
`islands`). No main change, push or production deployment. This is an agent-
reviewed implementation, not owner aesthetic approval or physical-phone/Safari
certification. The owner can revisit retired designs from retained source.
