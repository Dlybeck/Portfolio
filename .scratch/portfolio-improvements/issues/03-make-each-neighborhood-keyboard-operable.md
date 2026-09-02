---
id: "03"
title: Make each Neighborhood keyboard-operable
status: resolved
phase: 1
blocked_by: []
---

# Make each Neighborhood keyboard-operable

## Context

Keyboard navigation should express the same visible parent-child model as pointer navigation. It must not expose the offscreen implementation tree or turn the portfolio into a conventional document menu. A visitor should be able to learn the Board by interacting with the small set of things currently in view.

## Requirements

- Expose only the visible Parent, up to three Children, and the centered Section to the Board keyboard cycle.
- Include the centered Section only when it represents an actionable document.
- Keep the keyboard cycle at a maximum of five Board items.
- Let Enter and Space move to a visible Section or open its document, according to the same behavior as pointer activation.
- Implement hierarchical Escape behavior:
  - From a nested document view, return one document level.
  - From a top-level open document, close it to the Board.
  - From the Board, move to the Parent.
  - At Home, do nothing.
- Use semantic interactive controls for Home, Close, Back, and other actions.
- Provide a clearly visible focus treatment that belongs to the current theme.
- Prevent hidden or offscreen Board elements from entering normal keyboard navigation.
- Preserve existing pointer and touch behavior.
- Add automated keyboard coverage for the focus order and Escape state matrix.

## Suggested approach

Model focus from the current Neighborhood rather than relying on incidental document order. Centralize the transition rules so pointer and keyboard activation share navigation behavior, while document-level Escape handling can precede Board-level movement.

## Done when

- Tab and reverse-Tab cycle predictably through no more than the five intended Board targets.
- Enter and Space activate every visible target correctly.
- Each row of the Escape hierarchy behaves as specified.
- Home, Close, and Back expose correct control semantics and accessible names.
- Focus remains visible across supported viewport sizes.
- Pointer and touch regression checks pass.
