# ddyno

FastAPI service behind ddyno.com. Hosts small ML models with slider inputs.

- `main.py`: model registry, standalone app auto-loader, host-header domain routing, generic prediction API, pages.
- `apps/`: drop-in standalone ML applications (auto-discovered at startup). Includes `watch_app.py`, `ncr_app.py`, and `_template.py`.
- `watch.py`, `track.py`, `schemes.py`: NFL Why Watch slate scoring, walk-forward verification, and scheme playbook diagrams.
- `ui.py`: HTML and CSS for the hub, the model page, the Why Watch page, and the NCR page.
- `models/<slug>/`: one folder per slider model.

## Run locally

    pip install -r requirements.txt
    uvicorn main:app --reload

## Add a slider model

Create `models/<slug>/` with:

- `meta.json`: name, category, summary, the input features (label, side, unit, min, max, default, step, description) and the model card.
- `model.json`: intercept, coefficients, covariance matrix, residual standard error, feature means and percentiles.
- `train.py`: the offline script that writes both files.

The hub lists it under its category and `/m/<slug>` builds the sliders from `meta.json`. Linear regression works with no code changes. For another model type, add a function to `ENGINES` in `main.py`.

## Add a standalone ML app

1. Copy `apps/_template.py` to `apps/<slug>.py` and define an `APP` dict with its FastAPI `router`.
2. Push to `main` — no edits needed to `main.py`, `ui.py`, or `Dockerfile`.
3. It automatically appears on the hub under its category and runs on the same always-on Render Starter instance.
4. **Subdomain or custom domain routing:** add hostnames (e.g., `["nfl.ddyno.com"]` or `["mycustomdomain.com"]`) to `APP["hosts"]` — or set the `APP_HOSTS` env var in Render (`{"watch": ["nfl.ddyno.com"]}`) — and requests to `/` on that host will serve the app directly.

## API

- `GET /api/health`
- `GET /api/models`
- `GET /api/apps`
- `GET /api/models/{slug}`
- `POST /api/models/{slug}/predict` with `{"inputs": {...}, "line": 47.5}` (`line` is optional)
- `GET /api/watch` (optional `?week=11`)
- `GET /api/watch/track`
