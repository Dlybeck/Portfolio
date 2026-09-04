# PROTOTYPE: Grounded Viewer shells

Question: How literal must the outer Viewer become before it reads as a
recognizable object in each alternate world?

The earlier document comparison is preserved in branch history at `e4f817c`.
Owner feedback selected Quiet Canvas (`A`) as its strongest reading structure.
That structure stays constant, but a literal artifact must supply a believable
material surface; painting a world's background color onto supposed paper is
not grounding.

On any opened alternate-theme document, use the temporary bottom switcher or
the `shellvariant` query parameter:

- `A` — Native artifact: an observatory terminal, pond field guide, or
  expedition chart case, depending on the active world.
- `B` — Observation window: one shared glass-and-hardware viewing instrument.
- `C` — Archive folio: one portable physical portfolio that follows David
  between worlds.

## Review decisions

- Planets / Constellation selects `B`. The glass-and-hardware observation
  window reads as a plausible futuristic viewing instrument.
- Lily `A` remains a candidate, not an approval. It is a bound pond field
  notebook, so its interior is warm ruled field paper rather than blue water.
- Islands `A` remains a candidate, not an approval. It is an expedition field
  log, so its interior is warm chart stock rather than blue sea.
- `B` and `C` remain comparison controls for Lily and Islands; neither is an
  approved direction.

## Reality-grounding gate

No candidate is described as approved until a pass answers all of these from
the Viewer's perspective:

1. What recognizable real-world object or scene is this?
2. What physical material carries the text, and would that material actually
   have this color, edge, spacing, and surface?
3. Why do the page, controls, decoration, and motion belong to that object?
4. Does any treatment exist only to solve readability or look polished, with
   no in-world reason?

If the object needs its label to explain what it is, or any answer is missing,
the candidate remains an experiment.

All candidates preserve real content, document navigation, the Quiet Canvas
reading structure, and the Board. Canonical is excluded from shell experiments
and must match untouched `main` for its opened-page presentation. This is
disposable prototype code on
`codex/document-viewer-prototype`; a validated direction must be rewritten into
Theme Pack data before it is considered production implementation.
