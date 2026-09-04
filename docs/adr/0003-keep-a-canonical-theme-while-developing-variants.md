# Keep a canonical theme while developing variants

Status: superseded in part by ADR 0007 for runtime selection and ADR 0011 for
manual selection. Canonical remains
the fail-closed fallback, but it is no longer the only unpinned public choice
when the Theme Engine is enabled.

The initial Theme Laboratory kept the current Board Theme as its guaranteed
public default because it was already familiar, responsive, and
movement-legible. A separately deployable navbar selector allowed experiments
without replacing that known experience, while every candidate still had to
preserve the navigation structure and general interaction experience.
