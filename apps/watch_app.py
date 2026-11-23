"""Standalone app: NFL Why Watch & Track Record (/watch, /watch/track, /api/watch*)."""
from __future__ import annotations

import json
import threading
import time
from pathlib import Path

from fastapi import APIRouter, HTTPException
from fastapi.responses import HTMLResponse

import track
import ui
import watch

ROOT = Path(__file__).resolve().parent.parent
WATCH_REFRESH_SECONDS = 6 * 3600
WATCH_NOTES = ROOT / "models" / "watch_notes.json"
WATCH = {"data": None, "rows": None, "team_rows": None, "track": None, "weeks": {}, "live": False}

router = APIRouter()
_started = False


def _refresh_watch_forever():
    while True:
        try:
            bundle = watch.build_all_weeks_cache(notes_path=WATCH_NOTES)
            WATCH["data"] = bundle["active"]
            WATCH["rows"] = bundle["rows"]
            WATCH["team_rows"] = bundle["team_rows"]
            WATCH["weeks"] = {bundle["active"]["week"]: bundle["active"]}
            try:
                WATCH["track"] = track.build_track_data(
                    season=bundle["active"]["season"],
                    raw_rows=bundle["rows"],
                    team_rows=bundle["team_rows"],
                )
            except Exception as te:
                print("track refresh failed:", repr(te))
            WATCH["live"] = True
        except Exception as e:                           # keep snapshot / previous refresh; retry later
            print("watch refresh failed:", repr(e))
        time.sleep(WATCH_REFRESH_SECONDS if WATCH["live"] else 600)


def start_background_refresh():
    global _started
    if _started:
        return
    _started = True
    watch_snap = ROOT / "models" / "watch_snapshot.json"
    if watch_snap.exists():
        wdata = json.loads(watch_snap.read_text())
        WATCH["data"] = wdata
        WATCH["weeks"][wdata["week"]] = wdata
    track_snap = ROOT / "models" / "track_snapshot.json"
    if track_snap.exists():
        WATCH["track"] = json.loads(track_snap.read_text())
    threading.Thread(target=_refresh_watch_forever, daemon=True).start()


@router.get("/api/watch")
def api_watch(week: int | None = None):
    """Ranked NFL slate with interest breakdown, outcome implications, and outcomes to predict."""
    data = WATCH["data"]
    if not data:
        raise HTTPException(503, "Game watch data is still loading. Try again in a moment.")
    if week is None or week == data["week"]:
        return {**data, "live": WATCH["live"]}
    if week in WATCH["weeks"]:
        return {**WATCH["weeks"][week], "live": WATCH["live"]}
    if WATCH["rows"] is not None and week in data.get("available_weeks", []):
        computed = watch.build_watch_data(
            week=week, season=data["season"], notes_path=WATCH_NOTES,
            raw_rows=WATCH["rows"], team_rows=WATCH["team_rows"],
        )
        WATCH["weeks"][week] = computed
        return {**computed, "live": WATCH["live"]}
    raise HTTPException(404, f"Week {week} is not available right now.")


@router.get("/api/watch/track")
def api_watch_track():
    """Point-in-time verification scorecard and game-by-game audit log for Why Watch."""
    data = WATCH["track"]
    if not data:
        raise HTTPException(503, "Track record data is still loading. Try again in a moment.")
    return {**data, "live": WATCH["live"]}


@router.get("/watch", response_class=HTMLResponse)
@router.get("/watch/track", response_class=HTMLResponse)
def watch_page():
    return ui.WATCH


APP = {
    "slug": "watch",
    "name": "Why Watch",
    "category": "NFL",
    "url": "/watch",
    "summary": "What makes each game interesting, how each outcome shifts playoff odds, and what to predict.",
    "pill": "Slate",
    "cta": "Open Why Watch",
    "nav": True,
    "order": 10,
    "hosts": ["watch.ddyno.com", "nfl.ddyno.com"],
    "router": router,
    "on_startup": start_background_refresh,
}
