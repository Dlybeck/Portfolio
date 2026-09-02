---
id: "07"
title: Prototype an alternate shared Document Grammar
status: ready-for-agent
phase: 2
blocked_by:
  - "06"
---

# Prototype an alternate shared Document Grammar

## Context

The documents are intentionally uniform to keep the codebase maintainable, and their current structure descends from the hand-built second portfolio generation. An alternative may be valuable, but it should be experienced and compared before any canonical redesign is accepted.

## Requirements

- Create one development-only theme variant that explores a materially different shared Document Grammar.
- Apply the variant to at least two dissimilar kinds of content, such as one project document and one hobby or personal document.
- Express the variant through the theme system without adding content-specific navigation behavior or bespoke page structures.
- Preserve all document content, links, Board context, keyboard semantics, accessible names, and responsive behavior.
- Produce comparable desktop and phone review artifacts for the canonical and experimental treatments.
- Record what the experiment improves, what it weakens, and whether it should be adopted, revised, or discarded.
- Keep the canonical Document Grammar and current Board Theme unchanged unless the owner separately approves adoption.
- Do not introduce random public theme selection.

## Suggested approach

Choose two pages whose content pressures are meaningfully different, then build the smallest coherent visual system that serves both. Compare information hierarchy, personality, readability, and consistency rather than optimizing only for novelty.

## Done when

- The experimental grammar renders coherently on both representative documents at desktop and phone sizes.
- The experiment remains selectable only through the development theme mechanism.
- Content and interaction regression checks pass in both canonical and experimental presentations.
- Side-by-side review artifacts and a concise recommendation are ready for owner evaluation.
- No canonical styling has been replaced without explicit approval.

