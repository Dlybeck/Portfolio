---
id: "06"
title: Add the development Board Theme selector
status: ready-for-agent
phase: 2
blocked_by:
  - "01"
  - "02"
  - "03"
  - "04"
  - "05"
---

# Add the development Board Theme selector

## Context

The current visual treatment is the canonical Board Theme and must remain available unchanged. Future themes are experiments in presentation, not alternate products: they may restyle the Board, backgrounds, borders, controls, and document pages, but they must preserve topology, content, URLs, navigation sequence, responsive structure, and the general interaction model.

This is the first Phase 2 ticket and does not begin until the Phase 1 baseline is complete.

## Requirements

- Add a simple theme selector to the navigation area in development environments.
- Exclude or disable the selector in deployment builds.
- Keep the current theme as the canonical default with no intended visual change.
- Centralize theme registration and selection rather than scattering theme-specific conditions through navigation logic.
- Fall back safely to the canonical theme when a selected theme is missing or unknown.
- Define a theme boundary broad enough to style both the Board and shared document presentation.
- Keep content, URLs, Board topology, visible Neighborhood limits, control meaning, focus sequence, responsive structure, and interaction behavior invariant across themes.
- Include a clearly non-production diagnostic theme sufficient to prove switching and fallback behavior.
- Do not enable random theme assignment or expose an unfinished alternate theme publicly.
- Add automated checks for default selection, switching, fallback, persistence behavior if any, and production exclusion.

## Suggested approach

Introduce a declarative theme registry and a single environment-aware selector surface. Route presentation tokens and theme-owned assets through that boundary while keeping navigation and content models independent.

## Done when

- A developer can switch between the canonical and diagnostic themes without changing source code.
- Unknown theme input returns to the canonical presentation without breaking the Board.
- A deployment build contains no usable development selector.
- The canonical theme passes visual comparison against the Phase 1 baseline.
- Navigation, accessibility, direct destinations, and responsive behavior pass under both registered themes.

