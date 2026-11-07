# Exploring the notebook: three mock-up directions

Static, self-contained HTML. Open any file in a browser (best at phone width, or use device tools at 390px).
Nothing here is wired into the site; the words are placeholders, not David's copy. Progress is kept
in the browser's localStorage only. Use the arrows on the dial to turn pages.

| | Direction | The viewer's loop | Where it lives on the page | What it costs |
|---|---|---|---|---|
| **A** `a-margin-doodles.html` | **Margin doodles.** Pencil drawings in the margin; tap one and a sticky note unfolds with a small extra. A row of nine ticks at the foot of every page counts finds ("3 of 9"); the last one stamps the page. | Notice, tap, be rewarded; look for the rest. | Right margin and page foot. Words are never covered. | Nine small SVGs and nine short notes written by David. No new navigation. |
| **B** `b-sticky-flags.html` | **Sticky flags.** Tap any line to highlight it; a coloured flag sticks out of the book edge. A postcard at the foot of each page lists what you flagged, with copy as text. | Read, keep what you like, leave with a keepsake. | Right edge of the book and the page foot. | Needs no new content, but adds a second place to look (flags and the postcard), and rewards reading more than finding. |
| **C** `c-red-thread.html` | **Red thread.** A few words carry a red pin. Tap one and it offers "follow the thread"; a red line draws across and the page turns to its twin word, which glows. A tiny pin map at the foot lights as threads are followed. | Follow a thought from page to page. | Inline in the words, plus the page foot. | Cross-links to author, and the pin map must never turn into a menu (see below). |

## Pick: A, with C's threads as a later add-on

- **A fits the notebook's own rules.** The notebook is the interface (see `AGENTS.md`); the wheel stays the way around. Doodles add no route, no menu and no tab bar, and they ask nothing of a viewer who ignores them.
- **It is the most discovery per unit of work.** The reward is a surprise, which is the opposite of the skipping that was removed with Say hi. Finding all nine is a goal without being a checklist.
- **B** rewards curation, not curiosity. The flags also compete with the section tabs for the same right edge, and a postcard of highlights drifts toward a summary page, which the self-portrait deliberately is not.
- **C** is lovely but its pin map reads as a board, which `docs/adr/0001-the-notebook-replaces-the-board.md` retired. Keep the inline thread words (real links, still plain links without scripts) and drop the map, or fold the thread idea into A: some doodles could point to another page.

## Notes for a build

- Doodles need real, plain-HTML fallbacks: the note text must be in the page source, so search engines, link previews and visitors without scripts get it (`AGENTS.md`, every route renders the whole notebook).
- Each doodle is a real button with an accessible name; the counter is announced politely, not on a timer. Reduced motion turns off the wiggle and the unfold.
- The idle wiggle (one unfound doodle after ~4s) is the only nudge; a counter appears only after the first find.
- Keep finds per device in localStorage, guarded by try/catch; never send them anywhere.
- Short landscape (see PR 47): the doodles sit in the page's right padding, which exists on both pages of the spread.
