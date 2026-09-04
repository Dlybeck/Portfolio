# Theme Packs own bounded Viewer Artifacts

Opened Documents use one invariant Viewer and Document flow. A Theme Pack may
select one bounded `viewer-artifact` recipe and supply its frame, material,
label, colors, dimensions, and responsive values through presentation data.

The supported recipes are `none`, `field-notebook`, `observation-window`, and
`expedition-log`. The stable shell owns their fixed semantic decoration slots;
no installed Theme Pack name appears in runtime code or shared styles.

The approved assignments are:

- Original: `none`; Canonical presentation tokens reproduce the original lined,
  taped paper Viewer without an added artifact layer.
- Lily Pond: `field-notebook` with warm ruled field paper.
- Planets / Constellation: `observation-window` with the futuristic instrument
  frame.
- Island Chain: `expedition-log` with warm chart stock.

The former A/B/C selector, `shellvariant` state, and disposable prototype
stylesheet are removed. Old review URLs discard prototype parameters on load.
Adding a normal Theme Pack selects and configures an existing recipe through
pack data. A genuinely new artifact behavior requires an intentional extension
to the shared grammar rather than theme-specific runtime code.
