# Every route renders the whole notebook

Each public route (`core/portfolio.py`) returns the same HTML document: every page of the
notebook written out by the server, with the route's own title, description and canonical
address in the head. Scripts take those pages and show one (phone) or two (desktop) at a time.

Why: search engines, link previews and visitors without scripts get the words, with no
second copy of the content to keep in step. Turning a page is instant because the next page
is already in the document; the address is updated with `pushState` so back and forward work.

Costs we accept: each route repeats the other pages' text (about 35 KB of HTML), which the
canonical link and per-route metadata keep from competing with each other. Pages without a
route of their own (the contents, the Projects and Hobbies lists, Say hi) open by hash on `/`.
