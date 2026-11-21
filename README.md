# ddyno

FastAPI service behind ddyno.com. Hosts small ML models with slider inputs.

- `main.py`: model registry, generic prediction API, pages. Also the NCR text demo.
- `watch.py`: NFL Why Watch slate scoring, Monte Carlo outcome implications, and prediction target links.
- `ui.py`: HTML and CSS for the hub, the model page, the Why Watch page, and the NCR page.
- `models/<slug>/`: one folder per model.

## Run locally

    pip install -r requirements.txt
    uvicorn main:app --reload

## Add a model

Create `models/<slug>/` with:

- `meta.json`: name, category, summary, the input features (label, side, unit, min, max, default, step, description) and the model card.
- `model.json`: intercept, coefficients, covariance matrix, residual standard error, feature means and percentiles.
- `train.py`: the offline script that writes both files.

The hub lists it under its category and `/m/<slug>` builds the sliders from `meta.json`. Linear regression works with no code changes. For another model type, add a function to `ENGINES` in `main.py`.

## API

- `GET /api/models`
- `GET /api/models/{slug}`
- `POST /api/models/{slug}/predict` with `{"inputs": {...}, "line": 47.5}` (`line` is optional)
- `GET /api/watch` (optional `?week=11`)
