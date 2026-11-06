# Portfolio (davidlybeck.com)

FastAPI + Jinja + hand-written JS and CSS. No build step. See `AGENTS.md` for the working rules,
`CONTEXT.md` for the words we use, and `docs/adr/` for why it is built this way.

## Run it

```
pip install -r requirements.txt
python main.py            # http://localhost:8080
```

or with Docker:

```
docker build -t portfolio .
docker run -p 8080:8080 portfolio
```

## Test it

```
pip install -r requirements-dev.txt
playwright install chromium
pytest
```

## Where things are

- `core/portfolio.py`: the public routes, and which notebook page each opens
- `core/notebook.py`: the pages, their order on a phone and on desktop
- `templates/notebook/`: the page and the words on every notebook page
- `static/js/notebook/`: the book (page turns), the wheel and the cover
- `static/css/notebook/` and `static/dlybeck/`: styles and the dlybeck design system files

Pushing to `main` deploys the live site (Cloud Build to Cloud Run).
