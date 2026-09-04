# Theme Packs own the expanded action treatment

The expanded Board location always exposes the same destination link in the
same semantic and navigational position. The Theme Engine owns that behavior,
including keyboard activation and the minimum accessible marker size.

Theme Packs choose one bounded Action Treatment through presentation data:

- `annotation` renders the link as writing directly on the world object.
- `marker` renders a larger, opaque, bordered in-world label.

Packs also own the action's existing typography and color tokens plus inert
border, padding, radius, shadow, decoration, and transform values. Adding a
world that uses either treatment requires no runtime change. A genuinely new
treatment requires an intentional shared-grammar extension rather than a
theme-name branch.

Canonical uses `annotation` to preserve the accepted paper presentation.
Planets / Constellation, Lily Pond, and Island Chain use `marker`. This decision
does not alter the Parent/Child Neighborhood, visible neighboring destinations,
link destination, focus order, document behavior, or responsive grid.
