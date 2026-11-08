# Portfolio working rules

This is a living self-portrait, not a resume redesign. Read `CONTEXT.md` for project
language and `docs/adr/` for the decisions behind the notebook. Preserve unrelated work
and the current authorized delivery boundary. Pushing to `main` deploys the live site,
so work on a branch and open PRs into `dev`.

## The notebook is the interface

- A worn kraft cover opens onto a notebook you page through with the side wheel. Each story
  is one page that scrolls. Do not add a second way around the site (menus, tab bars, a
  board). Every page stays reachable by the wheel, the page corners, a swipe, the contents
  and plain links.
- Every route in `core/portfolio.py` renders the whole notebook, opened at its page. Page
  words are written into the HTML by the templates in `templates/notebook/pages/`; scripts
  only turn the pages. A visitor without scripts, a search engine and a link preview must
  all get the words.
- The order of pages and the phone and desktop layouts live in `core/notebook.py`. Change
  them there; the templates and the browser engine read the same data.

## Content

- The words are David's. Move them from where they live; do not retype or "improve" them.
  Never add copy that calls out recruiters or hiring.
- Real links go to real targets. Nothing that looks clickable is a placeholder.

## Design and code

- Use the dlybeck design system (`static/dlybeck/`): tokens for every color, size and
  duration. Light theme only until a dark theme is asked for; keep colors as tokens.
- No build step, no CDN: fonts, scripts and 3D viewer files are served from `static/`.
  One scoped exception: the scan pad's reader loads its library and model on first use (ADR 0003).
- Hand-written ES modules in `static/js/notebook/`, plain CSS in `static/css/notebook/`.
- Keyboard operable (wheel, page corners, links), reduced motion respected, text pairs
  at 4.5:1 or better.

## Checking work

- Passing tests does not approve the look. Open the page at 390px wide and at desktop width,
  watch a page turn, and fix what is wrong before handing off.
- Each PR into `dev` carries phone and desktop screenshots, written in your own words, with
  no secrets (the repository is public).
