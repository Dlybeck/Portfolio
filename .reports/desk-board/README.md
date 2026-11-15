# Desk board: options for the portfolio

A small, anonymous "what I'm working on" board for davidlybeck.com, fed by Desk. Nothing here is on the live
site yet: no existing page, template or nav changed. Branch: `claude/desk-board-7e0cad`.

## Run the preview

```bash
uv venv -p 3.12 .venv && uv pip install -p .venv -r requirements-dev.txt
DESK_BOARD_PREVIEW=1 .venv/bin/uvicorn main:app --port 8765
```

Open http://127.0.0.1:8765/preview/desk-board for the three options side by side, each in four states (working,
resting, offline with a last copy, offline with nothing yet), using made-up counts. Each option's links open the
real notebook with that option placed where it would live (`/preview/desk-board/a?state=working`, `b`, `c`).
Add `DESK_BOARD_URL` and `DESK_BOARD_SECRET` to the command and a `live` link appears, read from Desk itself.

The preview route only exists when `DESK_BOARD_PREVIEW=1` is set. The live service never sets it.
Re-take the screenshots with `.venv/bin/python scripts/shoot_desk_board.py` while the preview runs.

## The options

| | Where | What | Screenshots |
|---|---|---|---|
| **A: a few lines on Say hi** | Say hi page, under the contact links (last page on a phone, left page of the last spread on desktop) | Plain words in the page's own type: one status line with a dot, then labelled rows. Reads as part of the page. | `a-*-desktop.png`, `a-*-phone.png` |
| **B: a card inside the back cover** | Desktop: the bare kraft inside of the back cover, facing Say hi. Phone: at the foot of Say hi, because a phone has no inside cover | A note card ("at my desk" in the hand font) with three counts you can read at a glance (working, waiting on me, resting), then four short lines | `b-*` |
| **C: a live sticker on the cover** | Front cover, under the scan pad, above the notes label | A vinyl pill, a sibling of the "now" pill: `LIVE · 3 AI chats working right now`; tapping it steps through the other lines | `c-*` |

`options-desktop.png` and `options-phone.png` show all three side by side.

What every option says, and only this: AI chats working, waiting on me, and resting; projects active in the
last day; projects in focus; GPU busy training or idle; last active N ago; when it was checked. Desk's data has
no names, and none are made up. When Desk can't be reached, the board says "My desk is offline" and shows the
last copy in the past tense ("2 AI chats were working", "Last copy, from 2 hours ago"), never "right now". With
no copy at all, it says "My desk isn't reachable right now".

## My pick: B

- It gives the board a page that is bare kraft today, so it adds to the notebook without crowding anything.
  A puts more text on Say hi. C adds a ninth sticker to a full cover.
- The three big counts show the point ("he's building things right now") in a second. A makes you read rows;
  C shows one line at a time, so most visitors never see past the first.
- It looks like something tucked into the notebook (paper card, sticker edge, hand-written heading), the same
  family as the scan pad. No new kinds of decoration.
- On a phone it moves to the foot of Say hi, in the same form.

C is the runner-up if you want it seen by everyone: it's the only one on the first screen. One thing that
needs your judgement on C: at the cover's size, a long line such as "5 projects active in the last day" gets
close to the band on a phone.

## What was built

- `core/desk_board.py`: fetches `DESK_BOARD_URL` with `Authorization: Bearer DESK_BOARD_SECRET` (2 s timeout,
  stdlib only, so no new dependency), keeps a good answer for 5 minutes, and waits 1 minute after a failure
  before trying again, so a down desk never slows page loads. It checks each field on its own: unknown fields
  are dropped, and a field in the wrong shape is dropped while the others stay. If nothing usable is left,
  that counts as a failure. Logs name only the kind of error, never the address or secret. `describe()` turns
  the result into the words above.
- `templates/notebook/_desk.html` + `static/css/notebook/desk.css`: the three treatments, with the words
  written by the server.
- `apis/route_desk_preview.py`, `templates/desk_preview/`: the preview, mounted from `main.py` only when
  `DESK_BOARD_PREVIEW=1`.
- Tests: `tests/test_desk_board.py` (fresh fetch, cache hit, failure with and without a copy, retry wait,
  unset config, extra and malformed fields, wording) and `tests/test_desk_preview.py` (not mounted on the site;
  no address or secret in any preview page; a real HTTP fetch sends the bearer header). Full suite: 476 passed.

## To ship (your steps)

1. **Choose an option** (A, B or C). Wiring it in is a small follow-up: call `desk_board` from
   `render_notebook` (with `run_in_threadpool`, because the fetch blocks), render that option's macro in its
   place (Say hi, or the inside back cover for B, which the scripts build, so it needs a server-written
   source the engine can move there, plus phone and desktop checks), link `desk.css`, delete the other two
   treatments and the preview route, and leave the board out when the state is `unconfigured`.
2. **Set the two variables on the Cloud Run service** (`portfolio`, region `us-west1`). Use Secret Manager for
   the secret:
   ```bash
   printf %s 'THE_SECRET' | gcloud secrets create desk-board-secret --data-file=-
   ```
   ```bash
   gcloud run services update portfolio --region us-west1 --update-env-vars DESK_BOARD_URL=https://YOUR-DESK/board --update-secrets DESK_BOARD_SECRET=desk-board-secret:latest
   ```
   The service account needs `roles/secretmanager.secretAccessor` on that secret. `gcloud run deploy` in
   `cloudbuild.yaml` keeps env vars that are already set. Desk's URL must be reachable from Cloud Run (public
   HTTPS, e.g. through your tunnel).
3. **Merge to `main`** (through `dev`, as `AGENTS.md` says). Pushing `main` deploys.

Notes: pages are sent `no-cache`, so each visit gets the server's current copy. The 5-minute cache is per Cloud
Run instance (min instances is 1, so in practice one copy). The board shows when you were last active,
to within minutes. That is the one thing it reveals about your schedule.
