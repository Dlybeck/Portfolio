# Select one complete world per unpinned refresh

When the Theme Engine is enabled, each unpinned full-page request selects one
enabled, random-eligible Theme Pack as a complete world, excluding the
immediately previous candidate when possible so a refresh visibly changes the
experience. An explicit `?theme=<pack-id>` pins a world for review and sharing,
the navbar selector remains a separately deployable authoring control, and
Canonical remains the fail-closed fallback. This supersedes ADR 0003 only
where it deferred public random selection; its quality requirement and
preservation of the navigation model remain active.
