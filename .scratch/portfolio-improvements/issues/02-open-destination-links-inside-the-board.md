---
id: "02"
title: Open destination links inside the Board
status: resolved
phase: 1
blocked_by: []
---

# Open destination links inside the Board

## Context

The Board is the portfolio's primary experience. A content destination must therefore reconstruct the relevant Board location and open its document rather than presenting that document as a detached standalone site. Internal document rendering may still require a separate representation so the outer route does not recurse or redirect indefinitely.

## Requirements

- Make Home the canonical root destination.
- Give each linkable document a canonical destination that loads the Board, moves to the correct Neighborhood, and opens the requested document.
- Keep internal document rendering distinct from canonical navigation wherever necessary to prevent redirect or embedding loops.
- Ensure links opened from within documents use the canonical Board-aware behavior.
- Preserve the parent-child Board topology and the maximum visible Neighborhood of one Parent, up to three Children, and the centered Section.
- Make Home, Open, Close, Back, and nested document navigation work from every supported entry point.
- Preserve pointer and touch behavior unless a change is required to fix a confirmed defect.
- Exact reconstruction of every intermediate Board state through browser Back and Forward is not required.
- Add automated coverage for canonical destinations, refreshes, internal navigation, and loop prevention.

## Suggested approach

Define one canonical mapping between a destination and its Board location, then use it for server entry, client navigation, and document links. Treat the internal document source as an implementation detail rather than a public destination.

## Done when

- Opening or refreshing every supported content destination shows the correct document within the correct Board context.
- Internal links transition to their destination without producing a detached page or redirect loop.
- Home, Open, Close, Back, and nested controls pass an interaction matrix from both Home and direct-entry states.
- Existing desktop and phone Board navigation remains recognizable and functional.
- Automated routing and interaction checks pass.
