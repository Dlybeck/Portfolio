# Keyboard navigation follows the board hierarchy

Keyboard navigation mirrors the board's parent-child model rather than exposing every offscreen tile. Tab cycles through the Parent, Children, and the centered section only when that center has an actionable document; Enter moves to a focused neighbor or opens the centered document. Escape follows the same hierarchy: it goes back within nested documents, closes a top-level document, moves one Parent step toward Home from the board, and does nothing at Home.
