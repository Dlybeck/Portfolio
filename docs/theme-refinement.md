# Theme Refinement Specification

Status: **Superseded in part by `theme-naturalism-restoration.md`**

This is the source of truth for the current theme-refinement discussion. It
exists so an implementation goal can reference a stable artifact instead of
trying to reproduce a long conversation. Resolved decisions are recorded as
soon as they are made; unresolved choices remain explicit.

The active goal authorizes source changes, tests, captures, local hosting, and
commits on `pilot/modular-theme-engine`. It does not authorize pushing, merging,
deployment, production changes, or changes to `main`.

Owner review after this pass approved Lily Pond and Planets and Constellations,
retained Island Chain with targeted cleanup, rejected the current Cloudscape,
and found that Canonical Paper still failed to preserve the original's natural
variation. `docs/theme-naturalism-restoration.md` is authoritative for that
follow-up goal and its updated theme dispositions.

## Working process

1. David and Codex resolve product questions collaboratively.
2. Codex records each resolved answer here before moving to the next question.
3. David reviews and approves the complete specification.
4. A short durable goal references the approved specification.
5. Codex implements autonomously within the recorded authority, hosts a
   remotely accessible preview, and stops for owner review.

## Product boundary

### Current work

The installed modular theme system and the static designs are broadly
successful—approximately 90% of the desired result. This is a focused
refinement pass, not an assumption that the theme system needs a wholesale
redesign.

The primary current problems are:

1. Text can be difficult to read, and the corrective text bubbles or boxes do
   not belong to the themes.
2. Motion can be visually inappropriate, unreliable, or both.

Canonical Paper also has a confirmed visual regression in its corners, rips,
tape, and paper variation. That is a restoration defect within this work, not
a request to reinterpret Paper.

### Explicitly not current work

An in-site AI feature that generates and applies a custom theme from a viewer's
request is a possible large future goal. It has not been selected or authorized
for implementation. The current refinement must not be expanded into that AI
feature.

## Existing system and designs to preserve

- The current modular Theme Pack system is the baseline. Refinement should
  extend or correct it only where the text and motion work demonstrates a need.
- A theme continues to own all presentation already covered by the Theme Pack:
  background, tiles and their visual variation, SVG layers, typography,
  colors, connectors and arrows, opened-page presentation, and decorative
  motion.
- Adding or switching an ordinary Theme Pack must not require theme-specific
  runtime code.
- One complete approved theme is selected on an unpinned refresh and remains
  stable during that exploration. Explicit theme selection remains available
  for development and review.
- Theme variation retains the combination depth demonstrated by the original
  Paper system, such as material, shape, tear, fold, tape, orientation, and
  color combinations rather than one repeated object per world.
- The approved themes share the established semi-realistic, solid-color,
  SVG-like visual universe.
- The currently approved static worlds are Canonical Paper, Lily Pads,
  Planets, Clouds, and Islands.
- Transit, Newspaper, and Puddles are rejected experiments and are not revived
  as part of this refinement.
- Characters are not required and should not be added merely to decorate a
  theme; the approved Lily Pads direction intentionally works without one.

## Grounded visual language

The purpose of each theme is to present a familiar real-world setting or object
in the established solid-color, SVG-like style. A Viewer should recognize what
they are looking at and understand its visual behavior without needing an
explanation.

Styling choices therefore need an understandable in-world reason. Text
readability alone does not justify distorting an object's natural form, adding
an arbitrary outline or backing shape, or changing its behavior. A focused
state may use a visual change that makes sense within the metaphor—for example,
an object appearing closer or a piece of paper unfolding—but it may not invent
an abstract shape merely because that shape is convenient for layout.

This rule does not require literal photorealism. It requires recognizable
objects, coherent physical or visual behavior, and theme treatments that feel
native to the represented world.

## Non-negotiable interaction structure

The existing Parent/Child Board navigation has no compromise. Themes and theme
motion do not change its topology, spatial relationships, controls, responsive
structure, or interaction sequence.

Each Board location retains its centered section, Parent, and up to three
Children. During Board focus and theme transitions, the centered section and
its visible neighboring destinations remain present and directly actionable.
An animation may not pan or zoom them out of reach, crop or cover them, disable
their hit targets, or change their pointer, touch, or keyboard relationships.
Visual ideas that require any of those compromises are out of bounds.

Keyboard interaction continues to follow the documented Board hierarchy.
Reduced motion remains an adaptation for viewers whose operating system
requests it; it does not replace the default animated experience.

## Fixed content-state contract

The current content states already work and do not need redesign:

- **Unfocused tile:** shows its title only.
- **Focused tile:** shows its title, short description, and link to its page
  when that page exists.
- **Opened page:** shows the page. The tile is not expected to contain the page
  itself.

Theme refinement preserves those states, their meaning, and their navigation.
Focused copy may be tightened when a former description is not actually short;
detailed credits and history remain on the opened page.
Opened pages may receive theme-native presentation, but their content does not
move inside the focused tile.

## Text refinement

### Confirmed problem

The current generic text bubbles or boxes are not an acceptable solution. They
can make words technically visible while looking foreign to the themed object.
Some current combinations remain difficult to read, especially on a phone.

### Required outcome

For every approved theme, the existing unfocused and focused content must be
readable and feel intentionally composed with the object that carries it. The
solution must preserve the fixed content-state contract and must not fall back
to a generic corrective bubble or box shared across otherwise unrelated
themes. It also may not distort an object or add an unexplained backing shape
solely to create room or contrast for text.

There is no universal rule that text must appear directly on the themed object.
That choice depends on the world. A theme may place text directly on an object
or use a recognizable in-world carrier when that is more coherent. The carrier
and composition are theme-owned; the information shown and the interaction
states are not.

Opened pages must remain readable and should visibly belong to the selected
theme while preserving the existing page structure and content.

### Resolved composition

The stable engine owns semantic content roles, fitting, and readable minimums.
Each Theme Pack owns the carrier art, its content-safe area, type choices,
contrast, dimensions, and action decoration. No runtime branch knows the name
of a theme.

| Theme | Text direction |
| --- | --- |
| Canonical Paper | Text remains directly on the paper, following the original presentation |
| Lily Pads | Text sits directly on the selected leaf within its natural interior |
| Planets | Text sits directly on the selected planet using its native palette and contrast |
| Clouds | Text sits directly on the cloud bank; no corrective label or bubble is added |
| Islands | Text sits on the navigable landmass rather than on a floating UI card |

Opened pages retain one semantic reading structure. Their typography, canvas,
reading surfaces, media treatment, controls, and decoration are supplied by the
active Theme Pack so they remain functional documents that visibly belong to
the current world.

### Integrated Viewer artifacts

The reviewed Viewer carriers are no longer prototypes. Original retains its
lined, taped paper Viewer; Lily Pond selects a bound field notebook; Planets /
Constellation selects the observation window; and Island Chain selects an
expedition field log. The carrier recipe, label, frame, responsive geometry,
and Document material are Theme Pack data. There is no viewer-variant switcher
or shareable prototype parameter.

## Motion refinement

### Confirmed problems

- The current motion can feel janky on a phone.
- Planets can appear as though a second, larger planet flies in and covers the
  selected one. The intended direction is for the selected planet itself to
  grow.
- Lily Pads can flash through an erroneous grow, shrink, grow, shrink sequence
  when leaving focus.
- Motion that suits one metaphor can feel out of place when applied to another.

### Confirmed direction

Motion should become a deliberate theme customization step while the Theme
Engine continues to preserve navigation and transition reliability. Two
baseline transition families are worth solidifying:

- **Grow:** the selected object itself expands into focus and reverses on exit;
  a second object does not fly in to cover it.
- **Cover:** a larger themed surface enters over the selected object and
  reverses away on exit, matching the established Paper metaphor.
- **Settle:** the focused form resolves in place with a restrained scale and
  opacity change. It does not introduce another object or move the camera.

Enter and exit must not flash, replay, or leave stale visual states. Reduced
motion must preserve the same final navigation and content states.

### Preset assignment and ownership

| Theme | Motion preset |
| --- | --- |
| Canonical Paper | Cover |
| Lily Pads | Grow |
| Planets | Grow |
| Clouds | Settle |
| Islands | Settle |

The stable engine implements the bounded presets. A Theme Pack selects a preset
and supplies its duration, easing, scale, rotation, and offsets. Ordinary new
themes select from these presets without adding runtime code. Decorative SVG
detail may animate only when it does not change content or navigation state.

## Canonical Paper restoration

Canonical Paper must recover the visual quality it had before the Theme Pack
conversion. Its original paper materials, clipped or folded corners, rips,
tape, and per-tile combination depth are the reference. The current oversized
translucent corner folds, harsh sawtooth tears, repetitive rectangles, and lost
material variety are regressions.

Restoration should be expressed through the modular theme system rather than by
reintroducing a second Paper-only runtime. Desktop and phone comparisons with
the preserved pre-regression version are required before owner review.

## Acceptance evidence

- Existing pointer, touch, keyboard, Parent/Child, Neighborhood, document, and
  responsive behavior remains unchanged.
- Every neighboring destination remains visible and actionable throughout each
  motion recipe.
- Every approved theme is reviewed on desktop and phone in unfocused, focused,
  entering, exiting, and opened-page states.
- Real titles, descriptions, and optional page links remain readable without a
  generic corrective bubble or box.
- Planets grow from the selected object rather than introducing a covering
  duplicate.
- Lily Pads exit without flashing or replaying contradictory transitions.
- Canonical Paper matches the quality and variation of its pre-regression
  reference.
- Reduced motion reaches the same correct final states without decorative
  movement.
- Automated checks supplement rather than replace owner visual review.

## Delivery boundary for the active goal

- Worktree: `/home/dlybeck/Projects/Portfolio-worktrees/portfolio-phase-1`
- Branch: `pilot/modular-theme-engine`
- Local source changes, tests, captures, local hosting, and commits may be
  authorized by the eventual goal.
- The review preview must bind beyond localhost so David can inspect it from a
  remote computer and phone.
- Blocked items should be collected while independent work continues, then
  raised together when no further meaningful unblocked work remains.
- Pushing, merging into `dev`, deployment, production changes, and all changes
  to `main` require fresh owner confirmation.
