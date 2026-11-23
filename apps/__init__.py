"""Auto-discovered standalone ML apps for ddyno.

Drop any module `apps/<slug>.py` (or package `apps/<slug>/__init__.py`) exporting an `APP` dict:
    APP = {
        "slug": "my-app",
        "name": "My ML App",
        "category": "Category",
        "url": "/apps/my-app",
        "summary": "Short description shown on the hub.",
        "pill": "App",                 # optional badge text on the hub
        "cta": "Open app",             # optional button text on the hub
        "nav": False,                  # optional: show link in top navigation bar
        "order": 50,                   # optional: sort order among apps
        "hosts": ["my-app.ddyno.com"], # optional: subdomains or custom domains routed to `url` at `/`
        "router": router,              # FastAPI APIRouter with this app's pages & API endpoints
        "on_startup": fn,              # optional zero-arg callable run once at server startup
    }

Files/folders starting with `_` (like `_template.py`) are ignored.
You can also bind extra subdomains or custom domains at runtime via the APP_HOSTS env var:
    APP_HOSTS='{"watch": ["nfl.ddyno.com", "whywatchnfl.com"]}'
"""
from __future__ import annotations

import importlib
import json
import os
from pathlib import Path

import ui


def _parse_host_overrides() -> dict[str, list[str]]:
    raw = (os.environ.get("APP_HOSTS") or "").strip()
    if not raw:
        return {}
    try:
        parsed = json.loads(raw)
        if not isinstance(parsed, dict):
            return {}
        out: dict[str, list[str]] = {}
        for slug, hosts in parsed.items():
            if isinstance(hosts, str):
                out[str(slug)] = [hosts]
            elif isinstance(hosts, list):
                out[str(slug)] = [str(h) for h in hosts if h]
        return out
    except Exception as e:
        print("Invalid APP_HOSTS env var:", repr(e))
        return {}


def discover_apps() -> tuple[list[dict], dict[str, dict]]:
    """Import every non-private module in apps/ and return (apps_list, host_map)."""
    app_dir = Path(__file__).resolve().parent
    overrides = _parse_host_overrides()
    found: list[dict] = []

    candidates: list[str] = []
    for p in sorted(app_dir.iterdir()):
        if p.name.startswith("_"):
            continue
        if p.is_file() and p.suffix == ".py":
            candidates.append(p.stem)
        elif p.is_dir() and (p / "__init__.py").exists():
            candidates.append(p.name)

    for mod_name in candidates:
        mod = importlib.import_module(f"apps.{mod_name}")
        spec = getattr(mod, "APP", None)
        if not isinstance(spec, dict) or "router" not in spec:
            continue
        entry = {
            "slug": spec["slug"],
            "name": spec["name"],
            "category": spec.get("category", "Apps"),
            "url": spec["url"],
            "summary": spec.get("summary", ""),
            "pill": spec.get("pill", "App"),
            "cta": spec.get("cta", "Open app"),
            "nav": bool(spec.get("nav", False)),
            "order": int(spec.get("order", 50)),
            "hosts": list(spec.get("hosts") or []),
            "router": spec["router"],
            "on_startup": spec.get("on_startup"),
        }
        for extra_host in overrides.get(entry["slug"], []):
            if extra_host not in entry["hosts"]:
                entry["hosts"].append(extra_host)
        found.append(entry)

    found.sort(key=lambda a: (a["order"], a["name"].lower()))

    host_map: dict[str, dict] = {}
    for entry in found:
        for h in entry["hosts"]:
            clean = h.strip().lower().split(":", 1)[0]
            if clean:
                host_map[clean] = entry

    return found, host_map


def page_shell(
    title: str,
    body_html: str,
    crumb: str = "",
    active_nav: str = "",
    max_width: str = "",
) -> str:
    """Wrap any standalone app's HTML in ddyno's shared dark theme and top navigation bar."""
    crumb_html = f'<span class="crumb">{crumb}</span>' if crumb else ""
    models_cls = ' class="on"' if active_nav == "models" else ""
    watch_cls = ' class="on"' if active_nav == "watch" else ""
    style_attr = f' style="max-width:{max_width}"' if max_width else ""
    return (
        ui.HEAD.replace("__TITLE__", f"{title} · ddyno")
        + f'<header class="top"><a class="brand" href="/"><i></i>ddyno</a>{crumb_html}'
        + f'<nav class="nav" aria-label="Primary"><a href="/"{models_cls}>Models</a><a href="/watch"{watch_cls}>Why Watch</a></nav></header>'
        + f'<div class="wrap"{style_attr}>{body_html}</div></body></html>'
    )
