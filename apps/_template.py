"""Starter template for adding a new standalone ML app to ddyno.

To launch a new standalone ML app on the same Render Starter instance:
  1. Copy this file to `apps/<your_slug>.py` (remove the leading underscore).
  2. Update `APP` metadata, API routes, and HTML below.
  3. Push to `main`.

That's it—no changes needed to `main.py`, `ui.py`, or `Dockerfile`.
- It automatically appears on the ddyno.com hub under its category.
- It is live immediately at `/apps/<your_slug>`.
- To also serve it on a subdomain (`mytool.ddyno.com`) or its own custom domain (`mytool.com`),
  add that hostname to `hosts` below (or set the `APP_HOSTS` env var in Render) and point DNS to Render.
"""
from __future__ import annotations

from fastapi import APIRouter
from fastapi.responses import HTMLResponse
from pydantic import BaseModel

from apps import page_shell

router = APIRouter()


class ExampleIn(BaseModel):
    value: float


@router.post("/api/apps/example/predict")
def predict(body: ExampleIn):
    return {"input": body.value, "result": round(body.value * 2.0, 2)}


@router.get("/apps/example", response_class=HTMLResponse)
def page():
    body = """
    <div class="mhead">
      <p class="eyebrow">Category</p>
      <h1 class="title">Example ML App</h1>
      <p class="lede">Standalone ML app sharing ddyno's design system and single always-on server.</p>
    </div>
    <div class="card blk">
      <h3>Try it</h3>
      <p class="note">Build custom inputs, charts, or API calls here—independent of the slider model pages.</p>
    </div>
    """
    return page_shell("Example ML App", body, crumb="Category", max_width="860px")


APP = {
    "slug": "example",
    "name": "Example ML App",
    "category": "Category",
    "url": "/apps/example",
    "summary": "One-sentence description shown on the hub.",
    "pill": "App",
    "cta": "Open app",
    "nav": False,
    "order": 50,
    "hosts": ["example.ddyno.com"],
    "router": router,
}
