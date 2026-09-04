# Theme switching lives at Home

When the Theme Engine is enabled, an unpinned page load still selects a complete
eligible world at random. Manual selection is a secondary discovery affordance
inside the focused Home location rather than persistent navbar chrome. Home
uses the shared greeting, “Welcome! Click to explore the neighboring tiles,”
followed by “Don't like what you see?” and an in-world “Try something different”
dropdown trigger.

Choosing a named world pins it through `?theme=<pack-id>` for navigation and
sharing. Choosing “Surprise me” removes that pin and returns selection to the
server-owned random rotation. The chooser borrows the pack's existing Action
Treatment, so a new Theme Pack requires no control-specific code.

The native select remains outside the invariant Neighborhood Tab cycle. `Alt+T`
returns to Home when necessary and focuses the chooser, preserving a direct
keyboard route without adding a sixth Neighborhood item. This supersedes the
navbar-selector clauses in ADR 0003 and ADR 0007; their remaining decisions
stay active.
