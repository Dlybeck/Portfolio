# Portfolio rebuild plan (Nov 6; for his glance before any build)
Claude Doc: https://claude.ai/artifact/TLfvo9TUzy1wZiAJZ6Vzsn (the doc is the source; this is a working copy for dev chats)

- Build round 17 of the preview (portfolio/first-looks.html, sources in first-looks/src) into repo Dlybeck/Portfolio. Same stack: FastAPI + Jinja + hand-written JS/CSS, no build step; push to main deploys Cloud Run (cloudbuild.yaml).
- Every route in core/portfolio.py DOCUMENTS (16) opens the notebook at its page; page content server-rendered in HTML; keep core/discovery.py metadata and person schema. Drop /_documents and /_theme-packs routes.
- Content moved from templates/pages/* (not retyped). Real links from templates. NBA predictor from static/json/results.json. 3D models from static/3Dmodels/*.glb with model-viewer self-hosted. Images resized/webp.
- Say hi: email, LinkedIn, resume needed from him.
- ScribbleScan sticker OCR: spike on dev server first (browser-sized handwriting model on a phone); fallback typed-text animation.
- Retire: core/theme_packs.py, core/themes.py, static/themes/*, themeEngine/themeReveal/themeSwap, chalkArrows*, mapPan, tile*.js, theme scripts/tests, docs/adr board records, .agents/skills/portfolio-grounding, AGENTS.md "navigation is exempt from redesign". New short notebook rules replace them. (Pending his OK.)
- Steps (PRs into dev, screenshots each): 1 groundwork (sync dev server copy, rules, dlybeck design, notebook/wheel/page engine, route map, tests) 2 inside pages 3 cover + stickers 4 OCR spike + ScribbleScan sticker 5 clean-up and launch checks (a11y, reduced motion, phone perf, Safari, real phone, SEO), fresh review, PR dev->main for his merge.
- Open for him: retire old themes/board (my pick yes); Say hi details; OCR test first.
