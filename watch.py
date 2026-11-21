"""Game Watch & Outcome Implications engine for ddyno.

Analyzes the active NFL regular-season slate from nflverse schedules/games.csv to answer:
  1. What makes each game interesting (transparent 0-100 Interest Score + 5 drivers + matchup depth)
  2. What the implications of each outcome are (vectorized Monte Carlo playoff/division/bye/draft
     odds under 'If Away Wins' vs. 'If Home Wins', plus conference ripple effects)
  3. What specific outcomes to try and predict for those implications, wired directly into
     ddyno's halftime models with pregame context pre-filled.
"""
from __future__ import annotations

import csv
import io
import json
import math
import urllib.parse
import urllib.request
from datetime import datetime, timezone
from pathlib import Path

import numpy as np

NFLVERSE_SCHEDULE = "https://github.com/nflverse/nflverse-data/releases/download/schedules/games.csv"
NFLVERSE_TEAM_WEEK = "https://github.com/nflverse/nflverse-data/releases/download/stats_team/stats_team_week_{season}.csv"

# Conference, division, and display names for all 32 NFL teams (nflverse abbreviations).
TEAMS: dict[str, dict[str, str]] = {
    "BUF": {"name": "Bills", "city": "Buffalo", "conf": "AFC", "div": "AFC East"},
    "MIA": {"name": "Dolphins", "city": "Miami", "conf": "AFC", "div": "AFC East"},
    "NE":  {"name": "Patriots", "city": "New England", "conf": "AFC", "div": "AFC East"},
    "NYJ": {"name": "Jets", "city": "New York", "conf": "AFC", "div": "AFC East"},
    "BAL": {"name": "Ravens", "city": "Baltimore", "conf": "AFC", "div": "AFC North"},
    "CIN": {"name": "Bengals", "city": "Cincinnati", "conf": "AFC", "div": "AFC North"},
    "CLE": {"name": "Browns", "city": "Cleveland", "conf": "AFC", "div": "AFC North"},
    "PIT": {"name": "Steelers", "city": "Pittsburgh", "conf": "AFC", "div": "AFC North"},
    "HOU": {"name": "Texans", "city": "Houston", "conf": "AFC", "div": "AFC South"},
    "IND": {"name": "Colts", "city": "Indianapolis", "conf": "AFC", "div": "AFC South"},
    "JAX": {"name": "Jaguars", "city": "Jacksonville", "conf": "AFC", "div": "AFC South"},
    "TEN": {"name": "Titans", "city": "Tennessee", "conf": "AFC", "div": "AFC South"},
    "DEN": {"name": "Broncos", "city": "Denver", "conf": "AFC", "div": "AFC West"},
    "KC":  {"name": "Chiefs", "city": "Kansas City", "conf": "AFC", "div": "AFC West"},
    "LV":  {"name": "Raiders", "city": "Las Vegas", "conf": "AFC", "div": "AFC West"},
    "LAC": {"name": "Chargers", "city": "Los Angeles", "conf": "AFC", "div": "AFC West"},
    "DAL": {"name": "Cowboys", "city": "Dallas", "conf": "NFC", "div": "NFC East"},
    "NYG": {"name": "Giants", "city": "New York", "conf": "NFC", "div": "NFC East"},
    "PHI": {"name": "Eagles", "city": "Philadelphia", "conf": "NFC", "div": "NFC East"},
    "WAS": {"name": "Commanders", "city": "Washington", "conf": "NFC", "div": "NFC East"},
    "CHI": {"name": "Bears", "city": "Chicago", "conf": "NFC", "div": "NFC North"},
    "DET": {"name": "Lions", "city": "Detroit", "conf": "NFC", "div": "NFC North"},
    "GB":  {"name": "Packers", "city": "Green Bay", "conf": "NFC", "div": "NFC North"},
    "MIN": {"name": "Vikings", "city": "Minnesota", "conf": "NFC", "div": "NFC North"},
    "ATL": {"name": "Falcons", "city": "Atlanta", "conf": "NFC", "div": "NFC South"},
    "CAR": {"name": "Panthers", "city": "Carolina", "conf": "NFC", "div": "NFC South"},
    "NO":  {"name": "Saints", "city": "New Orleans", "conf": "NFC", "div": "NFC South"},
    "TB":  {"name": "Buccaneers", "city": "Tampa Bay", "conf": "NFC", "div": "NFC South"},
    "ARI": {"name": "Cardinals", "city": "Arizona", "conf": "NFC", "div": "NFC West"},
    "LA":  {"name": "Rams", "city": "Los Angeles", "conf": "NFC", "div": "NFC West"},
    "SF":  {"name": "49ers", "city": "San Francisco", "conf": "NFC", "div": "NFC West"},
    "SEA": {"name": "Seahawks", "city": "Seattle", "conf": "NFC", "div": "NFC West"},
}

TEAM_LIST = sorted(TEAMS.keys())
TEAM_IDX = {t: i for i, t in enumerate(TEAM_LIST)}
CONF_DIVS: dict[str, list[list[int]]] = {}
CONF_TEAMS: dict[str, np.ndarray] = {}
for _conf in ("AFC", "NFC"):
    _divs = sorted({TEAMS[t]["div"] for t in TEAM_LIST if TEAMS[t]["conf"] == _conf})
    CONF_DIVS[_conf] = [[TEAM_IDX[t] for t in TEAM_LIST if TEAMS[t]["div"] == d] for d in _divs]
    CONF_TEAMS[_conf] = np.array([TEAM_IDX[t] for t in TEAM_LIST if TEAMS[t]["conf"] == _conf], dtype=int)


def _opt_float(v: str | None) -> float | None:
    if v is None or v == "" or v == "NA":
        return None
    try:
        x = float(v)
        return x if math.isfinite(x) else None
    except ValueError:
        return None


def _opt_int(v: str | None) -> int | None:
    x = _opt_float(v)
    return int(round(x)) if x is not None else None


def _spread_to_prob(spread: float) -> float:
    """Convert home-favored spread (nflverse convention: >0 means home favored) to home win prob."""
    return 0.5 * (1.0 + math.erf(spread / (13.45 * math.sqrt(2.0))))


def _fmt_rec(w: int, l: int, t: int = 0) -> str:
    return f"{w}-{l}-{t}" if t else f"{w}-{l}"


def _ordinal(n: int) -> str:
    if 10 <= n % 100 <= 20:
        return f"{n}th"
    return f"{n}{ {1: 'st', 2: 'nd', 3: 'rd'}.get(n % 10, 'th') }"


def _fmt_spread(spread: float | None, home: str, away: str) -> str:
    if spread is None:
        return "Line TBD"
    if abs(spread) < 0.25:
        return "Pick'em"
    fav = home if spread > 0 else away
    val = abs(spread)
    s = f"{val:.1f}".rstrip("0").rstrip(".")
    return f"{fav} -{s}"


def _is_primetime(weekday: str, gametime: str) -> bool:
    wd = (weekday or "").strip().lower()
    if wd in ("thursday", "monday", "friday", "saturday"):
        return True
    try:
        hr = int((gametime or "13:00").split(":")[0])
        return hr >= 19
    except ValueError:
        return False


def _fetch_schedule_rows(url: str = NFLVERSE_SCHEDULE) -> list[dict[str, str]]:
    req = urllib.request.Request(url, headers={"User-Agent": "ddyno"})
    with urllib.request.urlopen(req, timeout=45) as r:
        return list(csv.DictReader(io.TextIOWrapper(r, encoding="utf-8", newline="")))


def _fetch_team_week_rows(season: int) -> list[dict[str, str]]:
    """Fetch per-team weekly offensive/defensive stats (~120 KB) for scheme & style analysis."""
    url = NFLVERSE_TEAM_WEEK.format(season=season)
    req = urllib.request.Request(url, headers={"User-Agent": "ddyno"})
    try:
        with urllib.request.urlopen(req, timeout=30) as r:
            return [x for x in csv.DictReader(io.TextIOWrapper(r, encoding="utf-8", newline="")) if x.get("season_type") == "REG"]
    except Exception:
        return []


def _num0(row: dict[str, str], key: str) -> float:
    return _opt_float(row.get(key)) or 0.0


def _compute_style_profiles(
    team_rows: list[dict[str, str]],
    finished_games: list[dict],
) -> tuple[dict[str, dict], dict[tuple[str, str], list[dict]]]:
    """Derive each team's offensive & defensive play style and game-by-game matchup logs."""
    if not team_rows:
        return {}, {}

    # Outcome map by (game_id, team) -> 'W'/'L'/'T'
    outcome_by_gt: dict[tuple[str, str], str] = {}
    for g in finished_games:
        hs, as_ = g["home_score"], g["away_score"]
        if hs is None or as_ is None:
            continue
        if hs > as_:
            outcome_by_gt[(g["game_id"], g["home_team"])] = "W"
            outcome_by_gt[(g["game_id"], g["away_team"])] = "L"
        elif as_ > hs:
            outcome_by_gt[(g["game_id"], g["away_team"])] = "W"
            outcome_by_gt[(g["game_id"], g["home_team"])] = "L"
        else:
            outcome_by_gt[(g["game_id"], g["home_team"])] = "T"
            outcome_by_gt[(g["game_id"], g["away_team"])] = "T"

    by_game: dict[str, dict[str, dict[str, str]]] = {}
    for r in team_rows:
        by_game.setdefault(r["game_id"], {})[r["team"]] = r

    raw: dict[str, dict[str, float]] = {}
    game_logs: dict[str, list[dict]] = {t: [] for t in TEAM_LIST}
    h2h_logs: dict[tuple[str, str], list[dict]] = {}

    for r in team_rows:
        t = r.get("team", "")
        opp_t = r.get("opponent_team", "")
        gid = r.get("game_id", "")
        opp = by_game.get(gid, {}).get(opp_t)
        if t not in TEAMS or opp_t not in TEAMS or not opp:
            continue
        a = raw.setdefault(t, {k: 0.0 for k in (
            "g", "att", "comp", "py", "air", "yac", "p20", "pepa", "sacks_s", "ints",
            "car", "ry", "r10", "repa",
            "o_att", "o_sacks_s", "o_py", "o_air", "o_yac", "o_p20", "o_pepa",
            "o_car", "o_ry", "o_r10", "o_repa",
            "dsacks", "dqbh", "dtfl", "dint", "dpd", "dff",
        )})
        att, sacks_s = _num0(r, "attempts"), _num0(r, "sacks_suffered")
        py, air, yac, p20 = _num0(r, "passing_yards"), _num0(r, "passing_air_yards"), _num0(r, "passing_yards_after_catch"), _num0(r, "passing_20")
        pepa, ints = _num0(r, "passing_epa"), _num0(r, "passing_interceptions")
        car, ry, r10, repa = _num0(r, "carries"), _num0(r, "rushing_yards"), _num0(r, "rushing_10"), _num0(r, "rushing_epa")

        o_att, o_sacks_s = _num0(opp, "attempts"), _num0(opp, "sacks_suffered")
        o_py, o_air, o_yac, o_p20 = _num0(opp, "passing_yards"), _num0(opp, "passing_air_yards"), _num0(opp, "passing_yards_after_catch"), _num0(opp, "passing_20")
        o_pepa = _num0(opp, "passing_epa")
        o_car, o_ry, o_r10, o_repa = _num0(opp, "carries"), _num0(opp, "rushing_yards"), _num0(opp, "rushing_10"), _num0(opp, "rushing_epa")

        dsacks, dqbh = _num0(r, "def_sacks"), _num0(r, "def_qb_hits")
        dtfl, dint, dpd, dff = _num0(r, "def_tackles_for_loss"), _num0(r, "def_interceptions"), _num0(r, "def_pass_defended"), _num0(r, "def_fumbles_forced")

        a["g"] += 1
        a["att"] += att; a["comp"] += _num0(r, "completions"); a["py"] += py; a["air"] += air; a["yac"] += yac
        a["p20"] += p20; a["pepa"] += pepa; a["sacks_s"] += sacks_s; a["ints"] += ints
        a["car"] += car; a["ry"] += ry; a["r10"] += r10; a["repa"] += repa
        a["o_att"] += o_att; a["o_sacks_s"] += o_sacks_s; a["o_py"] += o_py; a["o_air"] += o_air; a["o_yac"] += o_yac
        a["o_p20"] += o_p20; a["o_pepa"] += o_pepa; a["o_car"] += o_car; a["o_ry"] += o_ry; a["o_r10"] += o_r10; a["o_repa"] += o_repa
        a["dsacks"] += dsacks; a["dqbh"] += dqbh; a["dtfl"] += dtfl; a["dint"] += dint; a["dpd"] += dpd; a["dff"] += dff

        db = max(1.0, att + sacks_s)
        plays = max(1.0, db + car)
        odb = max(1.0, o_att + o_sacks_s)
        oplays = max(1.0, odb + o_car)
        res = outcome_by_gt.get((gid, t), "")
        wk = _opt_int(r.get("week")) or 0
        entry = {
            "game_id": gid, "week": wk, "opp": opp_t, "res": res,
            "off_epa": (pepa + repa) / plays, "pass_epa": pepa / db, "rush_epa": repa / max(1.0, car),
            "py": py, "ry": ry, "sacks_s": sacks_s, "p20": p20,
            "def_epa_allowed": (o_pepa + o_repa) / oplays, "def_pass_epa": o_pepa / odb, "def_rush_epa": o_repa / max(1.0, o_car),
            "dsacks": dsacks, "dqbh": dqbh, "dtfl": dtfl, "o_p20": o_p20,
        }
        game_logs[t].append(entry)
        h2h_logs.setdefault((t, opp_t), []).append(entry)

    if len(raw) < 16:
        return {}, {}

    # Compute per-team rate metrics
    metrics: dict[str, dict[str, float]] = {}
    for t, a in raw.items():
        db = max(1.0, a["att"] + a["sacks_s"])
        plays = max(1.0, db + a["car"])
        odb = max(1.0, a["o_att"] + a["o_sacks_s"])
        oplays = max(1.0, odb + a["o_car"])
        metrics[t] = {
            "pass_rate": db / plays,
            "adot": a["air"] / max(1.0, a["att"]),
            "yac_share": a["yac"] / max(1.0, a["py"]),
            "exp_pass_rate": a["p20"] / max(1.0, a["att"]),
            "chunk_rush_rate": a["r10"] / max(1.0, a["car"]),
            "pass_epa": a["pepa"] / db,
            "rush_epa": a["repa"] / max(1.0, a["car"]),
            "off_epa": (a["pepa"] + a["repa"]) / plays,
            "sack_rate": a["sacks_s"] / db,
            "int_rate": a["ints"] / max(1.0, a["att"]),
            "pressure_rate": (a["dsacks"] + a["dqbh"]) / odb,
            "def_sack_rate": a["dsacks"] / odb,
            "tfl_rate": a["dtfl"] / max(1.0, a["o_car"]),
            "ballhawk_rate": (a["dint"] + a["dpd"]) / max(1.0, a["o_att"]),
            "havoc_rate": (a["dsacks"] + a["dtfl"] + a["dint"] + a["dff"]) / oplays,
            "opp_exp_pass_rate": a["o_p20"] / max(1.0, a["o_att"]),
            "opp_adot": a["o_air"] / max(1.0, a["o_att"]),
            "opp_yac_share": a["o_yac"] / max(1.0, a["o_py"]),
            "opp_pass_epa": a["o_pepa"] / odb,
            "opp_rush_epa": a["o_repa"] / max(1.0, a["o_car"]),
            "def_epa_allowed": (a["o_pepa"] + a["o_repa"]) / oplays,
        }

    # League-wide z-scores & top-10 style buckets
    keys = list(next(iter(metrics.values())).keys())
    league_mean = {k: float(np.mean([metrics[t][k] for t in metrics])) for k in keys}
    league_std = {k: max(1e-6, float(np.std([metrics[t][k] for t in metrics]))) for k in keys}
    z = {t: {k: (metrics[t][k] - league_mean[k]) / league_std[k] for k in keys} for t in metrics}

    def top_set(key: str, n: int = 10, reverse: bool = True) -> set[str]:
        return set(sorted(metrics.keys(), key=lambda t: metrics[t][key], reverse=reverse)[:n])

    buckets = {
        # Defense buckets (for querying how an offense fares against them)
        "high_pressure": top_set("pressure_rate", 10, True),
        "anti_explosive": top_set("opp_exp_pass_rate", 10, False),
        "run_stuffer": top_set("tfl_rate", 10, True),
        "ballhawk_cov": top_set("opp_pass_epa", 10, False),
        "soft_front": top_set("pressure_rate", 12, False),
        # Offense buckets (for querying how a defense fares against them)
        "pass_heavy": top_set("pass_rate", 10, True),
        "run_first": top_set("pass_rate", 10, False),
        "vertical_exp": top_set("exp_pass_rate", 10, True) | top_set("adot", 8, True),
        "yac_quick": top_set("yac_share", 10, True),
        "balanced_off": set(sorted(metrics.keys(), key=lambda t: abs(z[t]["pass_rate"]))[:12]),
    }

    styles: dict[str, dict] = {}
    for t in metrics:
        m, zt = metrics[t], z[t]

        # Classify offensive play style
        if zt["pass_rate"] >= 0.85 and zt["adot"] >= 0.35:
            off_key, off_lbl, off_bucket, off_bucket_lbl = "air_vertical", "Vertical Spread Passing", "pass_heavy", "pass-heavy spread offenses"
        elif zt["pass_rate"] >= 0.8:
            off_key, off_lbl, off_bucket, off_bucket_lbl = "spread_pass", "High-Volume Spread Passing", "pass_heavy", "pass-heavy spread offenses"
        elif zt["exp_pass_rate"] >= 0.85 and zt["pass_epa"] >= 0.4:
            off_key, off_lbl, off_bucket, off_bucket_lbl = "explosive_balanced", "Explosive Play-Action & Balanced", "vertical_exp", "explosive passing offenses"
        elif zt["pass_rate"] <= -0.8 and (zt["rush_epa"] >= 0.15 or zt["chunk_rush_rate"] >= 0.25):
            off_key, off_lbl, off_bucket, off_bucket_lbl = "ground_control", "Run-First / Ground Control", "run_first", "run-first offenses"
        elif zt["pass_rate"] <= -0.75:
            off_key, off_lbl, off_bucket, off_bucket_lbl = "run_first", "Run-Heavy / Play-Action", "run_first", "run-first offenses"
        elif zt["adot"] >= 0.8 and zt["yac_share"] <= -0.25:
            off_key, off_lbl, off_bucket, off_bucket_lbl = "vertical_air", "Vertical Air-Yards Attack", "vertical_exp", "vertical & explosive passing offenses"
        elif zt["yac_share"] >= 0.8:
            off_key, off_lbl, off_bucket, off_bucket_lbl = "yac_rhythm", "Quick-Game & YAC Rhythm", "yac_quick", "quick-game / YAC offenses"
        elif zt["adot"] <= -0.55:
            off_key, off_lbl, off_bucket, off_bucket_lbl = "short_rhythm", "Short Rhythm & Possession", "yac_quick", "short-rhythm / YAC offenses"
        else:
            off_key, off_lbl, off_bucket, off_bucket_lbl = "balanced_multiple", "Balanced Multiple Offense", "balanced_off", "balanced offenses"

        # Classify defensive play style
        if zt["tfl_rate"] >= 0.7 and zt["opp_exp_pass_rate"] >= 0.4:
            def_key, def_lbl, def_bucket, def_bucket_lbl = "aggressive_front", "Aggressive Front / Boom-or-Bust", "high_pressure", "aggressive pressure fronts"
        elif zt["pressure_rate"] >= 0.9 and zt["havoc_rate"] >= 0.5:
            def_key, def_lbl, def_bucket, def_bucket_lbl = "pressure_havoc", "High-Pressure Havoc Front", "high_pressure", "high-pressure fronts"
        elif zt["opp_exp_pass_rate"] <= -0.65 and zt["ballhawk_rate"] >= 0.65:
            def_key, def_lbl, def_bucket, def_bucket_lbl = "ballhawk_shell", "Ball-Hawk Shell Coverage", "anti_explosive", "two-high / anti-explosive shells"
        elif zt["opp_exp_pass_rate"] <= -0.6 and zt["pressure_rate"] <= 0.35:
            def_key, def_lbl, def_bucket, def_bucket_lbl = "two_high_shell", "Two-High Anti-Explosive Shell", "anti_explosive", "two-high / anti-explosive shells"
        elif zt["tfl_rate"] >= 0.65 and zt["opp_rush_epa"] <= -0.15:
            def_key, def_lbl, def_bucket, def_bucket_lbl = "run_stuff_funnel", "Run-Stuffing Pass Funnel", "run_stuffer", "run-stuffing fronts"
        elif zt["opp_pass_epa"] <= -0.45 and zt["opp_rush_epa"] >= 0.2:
            def_key, def_lbl, def_bucket, def_bucket_lbl = "light_box_cov", "Light-Box Coverage (Run Funnel)", "ballhawk_cov", "coverage-first defenses"
        elif zt["pressure_rate"] >= 0.6:
            def_key, def_lbl, def_bucket, def_bucket_lbl = "pressure_front", "Pass-Rush Pressure Front", "high_pressure", "high-pressure fronts"
        else:
            def_key, def_lbl, def_bucket, def_bucket_lbl = "balanced_zone", "Balanced Zone / Bend-Don't-Break", "soft_front", "balanced zone defenses"

        styles[t] = {
            "metrics": m,
            "z": zt,
            "off_key": off_key, "off_label": off_lbl,
            "off_bucket": off_bucket, "off_bucket_label": off_bucket_lbl,
            "def_key": def_key, "def_label": def_lbl,
            "def_bucket": def_bucket, "def_bucket_label": def_bucket_lbl,
            "logs": game_logs.get(t, []),
            "buckets": buckets,
        }

    return styles, h2h_logs


def _split_summary(logs: list[dict], opp_set: set[str], side: str) -> dict | None:
    """Summarize a team's record and efficiency against a specific opponent style bucket."""
    hits = [x for x in logs if x["opp"] in opp_set]
    if not hits:
        return None
    w = sum(1 for x in hits if x["res"] == "W")
    l = sum(1 for x in hits if x["res"] == "L")
    t = sum(1 for x in hits if x["res"] == "T")
    if side == "off":
        epa = float(np.mean([x["off_epa"] for x in hits]))
        pepa = float(np.mean([x["pass_epa"] for x in hits]))
        repa = float(np.mean([x["rush_epa"] for x in hits]))
    else:
        epa = float(np.mean([x["def_epa_allowed"] for x in hits]))
        pepa = float(np.mean([x["def_pass_epa"] for x in hits]))
        repa = float(np.mean([x["def_rush_epa"] for x in hits]))
    return {"n": len(hits), "record": _fmt_rec(w, l, t), "epa": epa, "pass_epa": pepa, "rush_epa": repa}


def _one_side_matchup(
    off_team: str,
    def_team: str,
    qb_name: str,
    styles: dict[str, dict],
    h2h_logs: dict[tuple[str, str], list[dict]],
    before_week: int,
) -> dict:
    """Build an analytical scheme clash, style track record, and 'what to watch for' cue for one side."""
    os_ = styles[off_team]
    ds_ = styles[def_team]
    om, dm = os_["metrics"], ds_["metrics"]
    oz, dz = os_["z"], ds_["z"]
    buckets = os_["buckets"]

    # Analytical efficiency balance (+ favors offense, - favors defense)
    pass_net = om["pass_epa"] + dm["opp_pass_epa"]
    rush_net = om["rush_epa"] + dm["opp_rush_epa"]
    overall_net = om["pass_rate"] * pass_net + (1.0 - om["pass_rate"]) * rush_net
    if overall_net >= 0.07:
        edge_team, edge_label = off_team, f"Edge: {off_team} Off"
    elif overall_net <= -0.07:
        edge_team, edge_label = def_team, f"Edge: {def_team} Def"
    else:
        edge_team, edge_label = "", "Even style clash"

    # Build the analytical clash description (scheme + key numbers, no PPG rankings)
    _art = lambda s: "an" if s[:1].lower() in "aeiou" else "a"
    qb_prefix = f"Led by {qb_name}, " if qb_name else ""
    off_desc = (
        f"{qb_prefix}{off_team} runs {_art(os_['off_label'])} {os_['off_label']} scheme "
        f"({om['pass_rate'] * 100:.0f}% pass, {om['adot']:.1f}-yd avg depth of target, "
        f"{om['yac_share'] * 100:.0f}% of passing yards after the catch"
        + (f", {om['exp_pass_rate'] * 100:.1f}% explosive 20+ yd throws" if oz["exp_pass_rate"] >= 0.5 else "")
        + ")."
    )
    def_desc = (
        f"{def_team} counters with {_art(ds_['def_label'])} {ds_['def_label']} defense "
        f"({dm['pressure_rate'] * 100:.0f}% pressure rate, {dm['tfl_rate'] * 100:.0f}% tackles for loss on runs, "
        f"allowing {dm['opp_exp_pass_rate'] * 100:.1f}% explosive throws)."
    )

    # Identify the primary tactical tension & 'what to watch for' win condition
    if dz["pressure_rate"] >= 0.65 and oz["sack_rate"] >= 0.35:
        clash = f"{off_desc} {def_desc} That creates a clear protection stress test: {off_team} takes sacks on {om['sack_rate'] * 100:.1f}% of dropbacks against a front that disrupts timing relentlessly."
        watch_for = (
            f"Watch 1st-down pass protection and quick outlets: for {off_team}'s style to work, they must stay out of 3rd-and-long and hold {def_team} under 3 sacks. "
            f"If {def_team} wins early-down run stops and forces obvious passing downs, its pressure package takes over."
        )
    elif dz["pressure_rate"] >= 0.65:
        clash = f"{off_desc} {def_desc} It's a strength-on-strength trench clash—{off_team} keeps a clean pocket ({om['sack_rate'] * 100:.1f}% sack rate) against an aggressive pass rush."
        watch_for = (
            f"Watch whether {def_team}'s blitzes and stunts force early checkdowns: if {off_team} picks up pressure and hits intermediate windows behind the rush, big chunk plays open up; "
            f"if {def_team} collapses the pocket without extra rushers, {off_team}'s rhythm stalls."
        )
    elif ds_["def_key"] in ("two_high_shell", "ballhawk_shell") and os_["off_key"] in ("vertical_air", "explosive_balanced", "air_vertical"):
        clash = f"{off_desc} {def_desc} {off_team} hunts vertical chunk plays, while {def_team}'s shell is built to take away the deep shot and force long, patient drives."
        watch_for = (
            f"Watch {off_team}'s patience on underneath throws and early-down runs: if {off_team} takes the light-box yards and converts 3rd-and-short, {def_team} has to creep out of its shell; "
            f"if {off_team} forces contested throws into bracket coverage, {def_team}'s ball-hawks win the turnover battle."
        )
    elif os_["off_key"] in ("spread_pass", "air_vertical") and ds_["def_key"] in ("balanced_zone", "light_box_cov", "two_high_shell"):
        clash = f"{off_desc} {def_desc} {off_team} stresses zone spacing with high pass volume ({om['pass_rate'] * 100:.0f}%), forcing {def_team} to tackle cleanly underneath and close throwing windows quickly."
        watch_for = (
            f"Watch 3rd-down passing windows and red-zone conversion: {off_team}'s spread style wins when quick completions march down the field without stalling; "
            f"{def_team}'s zone wins by rallying to tackles in bounds, avoiding explosive busts, and forcing field goals."
        )
    elif ds_["def_key"] == "ballhawk_shell":
        clash = f"{off_desc} {def_desc} {def_team} relies on disciplined coverage and playmaking on the ball ({dm['ballhawk_rate'] * 100:.0f}% INT/PBU rate) rather than heavy pass rush."
        watch_for = (
            f"Watch quarterback decision-making over the middle: {off_team} succeeds by protecting the football and taking underneath completions; "
            f"{def_team}'s defense flips the game if disguised coverages bait even 1–2 turnover-worthy throws."
        )
    elif os_["off_key"] in ("ground_control", "run_first") and ds_["def_key"] in ("run_stuff_funnel", "aggressive_front", "pressure_havoc"):
        clash = f"{off_desc} {def_desc} Both sides want to dictate the line of scrimmage—{off_team} leans on physical rushing, while {def_team} shoots gaps to blow up plays behind the sticks."
        watch_for = (
            f"Watch yards before contact on 1st down: if {off_team} stays on schedule (4+ yards on early carries), play-action opens the middle of the field; "
            f"if {def_team} stacks TFLs and turns {off_team} one-dimensional, the pass defense takes control."
        )
    elif os_["off_key"] == "yac_rhythm" or oz["yac_share"] >= 0.65:
        clash = f"{off_desc} {def_desc} {off_team} gets the ball out fast and asks playmakers to break tackles in space, testing {def_team}'s open-field tackling and flat defenders."
        watch_for = (
            f"Watch tackling on screens, slants, and flat routes: {off_team}'s offense succeeds when short throws turn into 10+ yard gains after the catch; "
            f"{def_team} wins by rallying downhill, keeping everything in front, and forcing tight-window throws past the sticks."
        )
    elif dm["opp_exp_pass_rate"] >= 0.095:
        clash = f"{off_desc} {def_desc} {def_team} can be vulnerable to vertical shots ({dm['opp_exp_pass_rate'] * 100:.1f}% explosive pass rate allowed), giving {off_team} room to attack downfield if protection holds."
        watch_for = (
            f"Watch play-action and deep crossers: {off_team} wins this matchup by generating 3+ plays of 20+ yards and punishing single-high looks; "
            f"{def_team} survives by winning early downs and creating pressure before deep routes develop."
        )
    else:
        fav_path = "the passing game" if pass_net >= rush_net else "the ground game"
        clash = f"{off_desc} {def_desc} Analytically, {off_team}'s cleanest path runs through {fav_path} (pass net {pass_net:+.2f} EPA/db, rush net {rush_net:+.2f} EPA/carry)."
        watch_for = (
            f"Watch early-down efficiency in {fav_path}: if {off_team} stays ahead of the chains and avoids negative plays, its play-calling stays balanced; "
            f"{def_team} wins by tightening up in the red zone and forcing 3rd-and-long throws."
        )

    # Historical 2026 track record against this exact style (excluding games after before_week if browsing past weeks)
    off_logs = [x for x in os_["logs"] if x["week"] < before_week] or os_["logs"]
    def_logs = [x for x in ds_["logs"] if x["week"] < before_week] or ds_["logs"]
    off_vs = _split_summary(off_logs, buckets[ds_["def_bucket"]], "off")
    def_vs = _split_summary(def_logs, buckets[os_["off_bucket"]], "def")

    track_bits = []
    # Head-to-head style meeting earlier this season if any
    prior_h2h = [x for x in h2h_logs.get((off_team, def_team), []) if x["week"] < before_week]
    if prior_h2h:
        pm = prior_h2h[-1]
        track_bits.append(
            f"Head-to-head (Wk {pm['week']}): {off_team} produced {pm['off_epa']:+.2f} EPA/play "
            f"({int(pm['py'])} pass yds, {int(pm['ry'])} rush yds, {int(pm['sacks_s'])} sacks taken) against {def_team}."
        )
    if off_vs:
        track_bits.append(
            f"{off_team} vs. {ds_['def_bucket_label']}: {off_vs['record']} ({off_vs['n']}g), "
            f"{off_vs['epa']:+.2f} EPA/play (season avg {om['off_epa']:+.2f})."
        )
    if def_vs:
        track_bits.append(
            f"{def_team} def vs. {os_['off_bucket_label']}: {def_vs['record']} ({def_vs['n']}g), "
            f"allowing {def_vs['epa']:+.2f} EPA/play (season avg {dm['def_epa_allowed']:+.2f})."
        )

    return {
        "title": f"When {off_team} has the ball",
        "off_team": off_team,
        "def_team": def_team,
        "off_scheme": os_["off_label"],
        "def_scheme": ds_["def_label"],
        "edge_team": edge_team,
        "edge_label": edge_label,
        "clash": clash,
        "track_record": " ".join(track_bits) if track_bits else f"First real test of this style pairing in {off_team}'s and {def_team}'s schedule.",
        "watch_for": watch_for,
    }


def _build_style_matchups(
    g: dict,
    styles: dict[str, dict],
    h2h_logs: dict[tuple[str, str], list[dict]],
) -> list[dict]:
    """Return both sides of the ball (away offense vs home defense, home offense vs away defense)."""
    away, home = g["away_team"], g["home_team"]
    if away not in styles or home not in styles:
        return []
    return [
        _one_side_matchup(away, home, g.get("away_qb_name") or "", styles, h2h_logs, g["week"]),
        _one_side_matchup(home, away, g.get("home_qb_name") or "", styles, h2h_logs, g["week"]),
    ]


def _eval_league(
    wins: np.ndarray,
    div_wins: np.ndarray,
    conf_wins: np.ndarray,
    tie_noise: np.ndarray,
) -> dict[str, np.ndarray]:
    """Compute playoff, division-title, #1-seed bye, and top-5 draft probabilities across N sims."""
    n_sims = wins.shape[0]
    row_idx = np.arange(n_sims)
    playoff = np.zeros((n_sims, 32), dtype=bool)
    div_win = np.zeros((n_sims, 32), dtype=bool)
    bye = np.zeros((n_sims, 32), dtype=bool)

    div_score = wins + 1e-3 * div_wins + 1e-5 * conf_wins + 1e-7 * tie_noise
    conf_score = wins + 1e-3 * conf_wins + 1e-5 * tie_noise

    for conf in ("AFC", "NFC"):
        winners = np.empty((n_sims, 4), dtype=int)
        for d_i, members in enumerate(CONF_DIVS[conf]):
            m_arr = np.array(members, dtype=int)
            best_local = np.argmax(div_score[:, m_arr], axis=1)
            w_idx = m_arr[best_local]
            winners[:, d_i] = w_idx
            div_win[row_idx, w_idx] = True
            playoff[row_idx, w_idx] = True

        # #1 seed = highest conference score among the 4 division winners
        win_scores = conf_score[row_idx[:, None], winners]
        bye_idx = winners[row_idx, np.argmax(win_scores, axis=1)]
        bye[row_idx, bye_idx] = True

        # Wild card = top 3 non-division-winners in the conference
        c_teams = CONF_TEAMS[conf]
        wc_scores = conf_score[:, c_teams].copy()
        wc_scores[div_win[:, c_teams]] = -1e9
        top3_local = np.argpartition(wc_scores, -3, axis=1)[:, -3:]
        wc_idx = c_teams[top3_local]
        playoff[row_idx[:, None], wc_idx] = True

    # Bottom 5 league-wide records -> top-5 draft pick odds
    draft_score = wins + 1e-5 * tie_noise
    bot5 = np.argpartition(draft_score, 5, axis=1)[:, :5]
    top5 = np.zeros((n_sims, 32), dtype=bool)
    top5[row_idx[:, None], bot5] = True

    return {
        "playoff": playoff.mean(axis=0),
        "div": div_win.mean(axis=0),
        "bye": bye.mean(axis=0),
        "top5": top5.mean(axis=0),
    }


def _compute_team_profiles(finished: list[dict]) -> dict[str, dict]:
    """Compute records, scoring ranks, streaks, and ratings from completed games."""
    stats = {
        t: {
            "team": t,
            "name": TEAMS[t]["name"],
            "city": TEAMS[t]["city"],
            "conf": TEAMS[t]["conf"],
            "div": TEAMS[t]["div"],
            "w": 0, "l": 0, "t": 0,
            "div_w": 0, "div_l": 0, "div_t": 0,
            "conf_w": 0, "conf_l": 0, "conf_t": 0,
            "pf": 0.0, "pa": 0.0, "gp": 0,
            "results": [],  # chronological list of 'W', 'L', 'T'
        }
        for t in TEAM_LIST
    }

    for g in sorted(finished, key=lambda x: (x["week"], x["gameday"], x["game_id"])):
        h, a = g["home_team"], g["away_team"]
        hs, as_ = g["home_score"], g["away_score"]
        if h not in stats or a not in stats or hs is None or as_ is None:
            continue
        same_div = TEAMS[h]["div"] == TEAMS[a]["div"]
        same_conf = TEAMS[h]["conf"] == TEAMS[a]["conf"]

        stats[h]["gp"] += 1
        stats[a]["gp"] += 1
        stats[h]["pf"] += hs
        stats[h]["pa"] += as_
        stats[a]["pf"] += as_
        stats[a]["pa"] += hs

        if hs > as_:
            stats[h]["w"] += 1
            stats[a]["l"] += 1
            stats[h]["results"].append("W")
            stats[a]["results"].append("L")
            if same_div:
                stats[h]["div_w"] += 1
                stats[a]["div_l"] += 1
            if same_conf:
                stats[h]["conf_w"] += 1
                stats[a]["conf_l"] += 1
        elif as_ > hs:
            stats[a]["w"] += 1
            stats[h]["l"] += 1
            stats[a]["results"].append("W")
            stats[h]["results"].append("L")
            if same_div:
                stats[a]["div_w"] += 1
                stats[h]["div_l"] += 1
            if same_conf:
                stats[a]["conf_w"] += 1
                stats[h]["conf_l"] += 1
        else:
            stats[h]["t"] += 1
            stats[a]["t"] += 1
            stats[h]["results"].append("T")
            stats[a]["results"].append("T")
            if same_div:
                stats[h]["div_t"] += 1
                stats[a]["div_t"] += 1
            if same_conf:
                stats[h]["conf_t"] += 1
                stats[a]["conf_t"] += 1

    # Derived per-game rates and shrunk strength ratings
    for t, s in stats.items():
        gp = s["gp"]
        s["wins_eq"] = s["w"] + 0.5 * s["t"]
        s["div_wins_eq"] = s["div_w"] + 0.5 * s["div_t"]
        s["conf_wins_eq"] = s["conf_w"] + 0.5 * s["conf_t"]
        s["win_pct"] = s["wins_eq"] / gp if gp else 0.5
        s["ppg"] = s["pf"] / gp if gp else 22.0
        s["papg"] = s["pa"] / gp if gp else 22.0
        s["pd_pg"] = (s["pf"] - s["pa"]) / gp if gp else 0.0
        # Shrink toward 0 early in season
        s["rating"] = max(-11.0, min(11.0, s["pd_pg"] * (gp / (gp + 4.5))))
        s["record"] = _fmt_rec(s["w"], s["l"], s["t"])
        s["div_record"] = _fmt_rec(s["div_w"], s["div_l"], s["div_t"])
        s["conf_record"] = _fmt_rec(s["conf_w"], s["conf_l"], s["conf_t"])

        # Current streak
        res = s["results"]
        if res:
            last = res[-1]
            k = 0
            for r in reversed(res):
                if r == last:
                    k += 1
                else:
                    break
            s["streak_type"] = last
            s["streak_len"] = k
            s["streak"] = f"{last}{k}"
        else:
            s["streak_type"] = ""
            s["streak_len"] = 0
            s["streak"] = "—"

    # League ranks (1 = best)
    off_order = sorted(TEAM_LIST, key=lambda t: (-stats[t]["ppg"], t))
    def_order = sorted(TEAM_LIST, key=lambda t: (stats[t]["papg"], t))
    for i, t in enumerate(off_order, 1):
        stats[t]["off_rank"] = i
    for i, t in enumerate(def_order, 1):
        stats[t]["def_rank"] = i

    # Division ranks
    for conf in ("AFC", "NFC"):
        for members in CONF_DIVS[conf]:
            m_teams = [TEAM_LIST[i] for i in members]
            m_teams.sort(key=lambda t: (-stats[t]["win_pct"], -stats[t]["div_wins_eq"], -stats[t]["pd_pg"], t))
            for r, t in enumerate(m_teams, 1):
                stats[t]["div_rank"] = r

    return stats


def _build_model_url(slug: str, params: dict[str, float | int | str]) -> str:
    clean = {k: v for k, v in params.items() if v is not None and v != ""}
    return f"/m/{slug}" + (f"?{urllib.parse.urlencode(clean)}" if clean else "")


def _prediction_targets(
    g: dict,
    hp: dict,
    ap: dict,
    imp: dict | None,
    drivers_by_id: dict[str, dict],
) -> list[dict]:
    """Generate 3 concrete 'what outcomes to try and predict' recommendations for a game."""
    home, away = g["home_team"], g["away_team"]
    spread = g["spread_line"]
    proj_spread = spread if spread is not None else round((hp["rating"] - ap["rating"] + 1.8) * 2) / 2
    total = g["total_line"] if g["total_line"] is not None else round((hp["ppg"] + ap["ppg"] + hp["papg"] + ap["papg"]) / 2 * 2) / 2
    wind = 0 if (g.get("roof") in ("dome", "closed")) else (g["wind"] if g["wind"] is not None else 6)
    abs_sp = abs(proj_spread)
    fav = home if proj_spread >= 0 else away
    dog = away if proj_spread >= 0 else home
    game_tag = f"{away} @ {home} (Wk {g['week']})"

    # Baseline expected halftime score split for pre-filling halftime models
    h_exp_h1 = max(3, min(31, int(round((total + proj_spread) / 4.0))))
    a_exp_h1 = max(3, min(31, int(round((total - proj_spread) / 4.0))))

    po_swing = imp["total_playoff_swing"] if imp else 0.0
    div_swing = imp["total_div_swing"] if imp else 0.0
    bye_swing = imp["total_bye_swing"] if imp else 0.0
    draft_swing = imp["total_draft_swing"] if imp else 0.0

    # 1. Winner / Margin / Halftime Control target
    if bye_swing >= 25:
        win_why = (
            f"Both clubs have strong postseason equity, so the #1-seed bye ({bye_swing:.0f}-pt swing)"
            + (f" and division-title positioning ({div_swing:.0f}-pt swing)" if div_swing >= 15 else "")
            + f" are the real prize. Predict whether {fav} builds an early cushion or whether {dog} keeps win probability live into the fourth quarter."
        )
    elif po_swing >= 16 or div_swing >= 18:
        win_why = (
            f"A single result swings combined playoff odds by {po_swing:.0f} percentage points"
            + (f" and division odds by {div_swing:.0f} pts" if div_swing >= 12 else "")
            + f". Predicting whether {dog} can stay within one score at halftime—or force an upset—is the highest-leverage call on the board."
        )
    elif bye_swing >= 12:
        win_why = (
            f"Both clubs have strong postseason equity, so the #1-seed bye ({bye_swing:.0f}-pt swing) is the real prize. "
            f"Track whether {fav} builds an early cushion or lets this turn into a fourth-quarter coin flip."
        )
    elif draft_swing >= 20:
        win_why = (
            f"Playoff odds are slim, so the main implication is draft position ({draft_swing:.0f}-pt swing in top-5 pick odds). "
            f"Predicting an upset flips who controls early-round draft leverage."
        )
    else:
        win_why = (
            f"With {_fmt_spread(proj_spread, home, away)} on the board, the key call is whether {fav} separates before halftime "
            f"or whether {dog} keeps win probability live into the third quarter."
        )

    t1 = {
        "category": "Winner & Margin",
        "title": f"Who wins—and whether {fav} holds control at halftime",
        "benchmark": f"Pregame line: {_fmt_spread(proj_spread, home, away)} (expected half ~{a_exp_h1}–{h_exp_h1})",
        "why": win_why,
        "model_slug": "nfl-halftime-win",
        "model_label": "Run in Halftime Win Model",
        "model_url": _build_model_url("nfl-halftime-win", {
            "spread_line": max(-11.5, min(15.5, proj_spread)),
            "home_h1_pts": h_exp_h1,
            "away_h1_pts": a_exp_h1,
            "game": game_tag,
        }),
    }

    # 2. Scoring Pace / Final Total target
    if total >= 48.0:
        tot_title = f"Shootout pace: does the final clear {total:.1f}?"
        tot_why = (
            f"A {total:.1f} total signals one of the week's fastest scoring environments "
            f"({away} ranks #{ap['off_rank']} in scoring at {ap['ppg']:.1f} PPG; {home} ranks #{hp['off_rank']} at {hp['ppg']:.1f}). "
            f"If the winner comes from trading explosive drives, the over/under is tightly coupled to who survives a late possession game."
        )
    elif total <= 40.5:
        tot_title = f"Defensive squeeze: does scoring stay under {total:.1f}?"
        tot_why = (
            f"The low {total:.1f} total reflects defense and field position "
            f"({away} allows {ap['papg']:.1f} PPG, #{ap['def_rank']}; {home} allows {hp['papg']:.1f}, #{hp['def_rank']}). "
            f"In a game this compressed, one defensive touchdown or busted coverage flips both the total and the outright winner."
        )
    else:
        tot_title = f"Total points vs. {total:.1f} benchmark"
        tot_why = (
            f"The market expects a balanced {total:.1f}-point game ({int(round(total/2))}+ needed by halftime to stay on over pace). "
            f"Predicting whether explosive plays push scoring above baseline tells you if this breaks open or stays tight."
        )

    t2 = {
        "category": "Scoring & Pace",
        "title": tot_title,
        "benchmark": f"Pregame total: {total:.1f} · Half pace: {total / 2:.1f} pts" + (" · Dome/indoor" if g.get("roof") in ("dome", "closed") else f" · Wind ~{int(wind)} mph"),
        "why": tot_why,
        "model_slug": "nfl-halftime-total",
        "model_label": "Run in Halftime Total Model",
        "model_url": _build_model_url("nfl-halftime-total", {
            "total_line": max(33.0, min(55.5, total)),
            "wind": max(0, min(22, int(round(wind)))),
            "home_h1_pts": h_exp_h1,
            "away_h1_pts": a_exp_h1,
            "compare": total,
            "game": game_tag,
        }),
    }

    # 3. Game Script / Conditional Over-Under or Game-Type cluster
    if abs_sp >= 9.0:
        t3 = {
            "category": "Game Script & Blowout Risk",
            "title": f"Does {fav} cruise early, or does {dog} drag this into a live second half?",
            "benchmark": f"Upset alert if {dog} is within 3 pts at half (spread {_fmt_spread(proj_spread, home, away)})",
            "why": (
                f"With a heavy {_fmt_spread(proj_spread, home, away)} spread, the real forecasting edge is game script: "
                f"early blowouts drain second-half play volume and suppress scoring, whereas a close halftime turns the game into a high-leverage upset watch."
            ),
            "model_slug": "nfl-halftime-game-types",
            "model_label": "Classify Halftime Game Type",
            "model_url": _build_model_url("nfl-halftime-game-types", {
                "home_h1_pts": h_exp_h1,
                "away_h1_pts": a_exp_h1,
                "game": game_tag,
            }),
        }
    else:
        t3 = {
            "category": "Live Over/Under & Script",
            "title": f"Second-half scoring probability around {total:.1f}",
            "benchmark": f"Test live O/U at halftime using spread ({_fmt_spread(proj_spread, home, away)}) + pace",
            "why": (
                f"In a competitive matchup, halftime box-score efficiency (first downs and explosive plays, not just scoreboard points) "
                f"often predicts whether second-half scoring regresses or accelerates past {total:.1f}."
            ),
            "model_slug": "nfl-halftime-ou-logit",
            "model_label": "Test Live O/U Classifier",
            "model_url": _build_model_url("nfl-halftime-ou-logit", {
                "total_line": max(33.0, min(55.5, total)),
                "spread_line": max(-11.5, min(15.5, proj_spread)),
                "wind": max(0, min(22, int(round(wind)))),
                "line": total,
                "home_h1_pts": h_exp_h1,
                "away_h1_pts": a_exp_h1,
                "game": game_tag,
            }),
        }

    return [t1, t2, t3]


def _build_why_watch(
    g: dict,
    hp: dict,
    ap: dict,
    imp: dict | None,
    drivers: list[dict],
    prior_meetings: list[dict],
) -> tuple[str, list[dict]]:
    """Build a crisp 1-line hook and 3 structured 'Why Watch' depth points."""
    home, away = g["home_team"], g["away_team"]
    spread = g["spread_line"]
    proj_spread = spread if spread is not None else (hp["rating"] - ap["rating"] + 1.8)
    total = g["total_line"]
    abs_sp = abs(proj_spread)
    po_swing = imp["total_playoff_swing"] if imp else 0.0
    div_swing = imp["total_div_swing"] if imp else 0.0
    bye_swing = imp["total_bye_swing"] if imp else 0.0
    draft_swing = imp["total_draft_swing"] if imp else 0.0

    # 1-line hook for the slate row
    if g["finished"]:
        winner = home if g["home_score"] > g["away_score"] else away if g["away_score"] > g["home_score"] else None
        score_txt = f"{away} {g['away_score']}–{g['home_score']} {home}"
        hook = f"Final: {score_txt}. " + (
            f"{winner} took a {abs(g['home_score'] - g['away_score'])}-pt decision"
            + (f" in a {g['home_score'] + g['away_score']}-pt game." if g["home_score"] is not None else ".")
            if winner else "Finished in a tie."
        )
    elif bye_swing >= 30:
        hook = f"{TEAMS[home]['conf']} #1-seed showdown: {bye_swing:.0f}-pt swing in first-round bye odds on a {_fmt_spread(spread, home, away)} line."
    elif po_swing >= 22 and abs_sp <= 5.5:
        hook = f"High-stakes swing game: {po_swing:.0f}-pt playoff leverage on a {_fmt_spread(spread, home, away)} line."
    elif g["div_game"] and div_swing >= 20:
        hook = f"{TEAMS[home]['div']} pivot game: {div_swing:.0f}-pt division-title swing."
    elif div_swing >= 25:
        hook = f"Playoff & division ripple: {po_swing:.0f}-pt playoff and {div_swing:.0f}-pt division-title swing."
    elif total is not None and total >= 50.0:
        hook = f"Expected shootout ({total:.1f} total) featuring {g['away_qb_name'] or away} vs. {g['home_qb_name'] or home}."
    elif total is not None and total <= 39.5 and abs_sp <= 4.5:
        hook = f"Tight defensive rock fight: {_fmt_spread(spread, home, away)} with a {total:.1f} total."
    elif po_swing >= 16:
        hook = f"Real postseason leverage ({po_swing:.0f}-pt combined playoff swing) between {away} ({ap['record']}) and {home} ({hp['record']})."
    elif bye_swing >= 14:
        hook = f"Top-seed race: {bye_swing:.0f}-pt swing in conference #1-seed bye odds."
    elif abs_sp <= 3.5:
        hook = f"Close matchup ({_fmt_spread(spread, home, away)}) between {away} ({ap['record']}) and {home} ({hp['record']})."
    elif draft_swing >= 25:
        hook = f"Draft-order stakes ({draft_swing:.0f}-pt top-5 pick swing) as {away} visits {home}."
    else:
        hook = f"{_fmt_spread(spread, home, away)} mismatch; watch whether {away if proj_spread > 0 else home} keeps it live past halftime."

    # Detailed 3-bullet "Why Watch" breakdown
    notes = []

    # Bullet 1: Stakes
    if imp:
        h_po, a_po = imp["home"]["base"]["playoff"], imp["away"]["base"]["playoff"]
        if po_swing >= 12 or div_swing >= 15 or bye_swing >= 10:
            bits = [
                f"{away} ({ap['record']}, {_ordinal(ap['div_rank'])} in {ap['div']}) enters with {a_po:.0f}% playoff odds; "
                f"{home} ({hp['record']}, {_ordinal(hp['div_rank'])} in {hp['div']}) sits at {h_po:.0f}%."
            ]
            if bye_swing >= 25:
                bits.append(f"With both clubs positioned near the top of the {hp['conf']}, conference #1-seed bye odds swing by {bye_swing:.0f} percentage points.")
            if po_swing >= 12:
                bits.append(f"This single result moves their combined playoff probability by {po_swing:.0f} percentage points.")
            if div_swing >= 15:
                bits.append(f"Division-title odds shift by {div_swing:.0f} pts.")
            elif 10 <= bye_swing < 25:
                bits.append(f"Conference #1-seed bye odds swing by {bye_swing:.0f} pts.")
            stakes_text = " ".join(bits)
        elif draft_swing >= 18:
            stakes_text = (
                f"Both teams sit on the outside of the playoff race ({away} {a_po:.0f}%, {home} {h_po:.0f}%), "
                f"making draft position the primary consequence—this outcome swings top-5 draft-pick odds by {draft_swing:.0f} points."
            )
        else:
            stakes_text = (
                f"{away} ({ap['record']}, {a_po:.0f}% playoff odds) faces {home} ({hp['record']}, {h_po:.0f}% playoff odds). "
                f"Overall playoff leverage is modest ({po_swing:.0f}-pt combined swing), so watch for momentum and margin signals."
            )
    else:
        stakes_text = (
            f"{away} ({ap['record']}, {_ordinal(ap['div_rank'])} in {ap['div']}) vs. "
            f"{home} ({hp['record']}, {_ordinal(hp['div_rank'])} in {hp['div']})."
        )
    notes.append({"label": "The Stakes", "text": stakes_text})

    # Bullet 2: Context / Edge / Rematch / Rest
    ctx_bits = []
    if g["div_game"]:
        if prior_meetings:
            pm = prior_meetings[-1]
            pm_w = pm["home_team"] if pm["home_score"] > pm["away_score"] else pm["away_team"]
            ctx_bits.append(
                f"Divisional rematch: {pm_w} won Week {pm['week']} ({pm['away_team']} {pm['away_score']}–{pm['home_score']} {pm['home_team']}), "
                f"putting a season sweep and head-to-head tiebreaker on the line."
            )
        else:
            ctx_bits.append(f"First {TEAMS[home]['div']} meeting of the season—division wins double as primary tiebreakers.")
    if g.get("primetime"):
        ctx_bits.append(f"Standalone {g['weekday']} night window ({g['gametime']} ET) at {g['stadium'] or home}.")
    h_rest, a_rest = g.get("home_rest"), g.get("away_rest")
    if h_rest and a_rest and abs(h_rest - a_rest) >= 3:
        rested = home if h_rest > a_rest else away
        ctx_bits.append(f"Rest edge to {rested} ({max(h_rest, a_rest)} days rest vs. {min(h_rest, a_rest)}).")
    if hp["streak_len"] >= 3 or ap["streak_len"] >= 3:
        parts = []
        if ap["streak_len"] >= 3:
            parts.append(f"{away} is on a {ap['streak']} streak")
        if hp["streak_len"] >= 3:
            parts.append(f"{home} is on a {hp['streak']} streak")
        ctx_bits.append("Recent form: " + " and ".join(parts) + ".")
    if not ctx_bits:
        roof = g.get("roof") or "outdoors"
        ctx_bits.append(
            f"Played at {g['stadium'] or home} ({'indoors' if roof in ('dome', 'closed') else roof}). "
            f"Market line is {_fmt_spread(spread, home, away)}"
            + (f" with a {total:.1f} total." if total is not None else ".")
        )
    notes.append({"label": "Context & Angles", "text": " ".join(ctx_bits)})

    return hook, notes


def _standings_notes_for_branch(
    winner: str,
    loser: str,
    wp: dict,
    lp: dict,
    g: dict,
    branch_w: dict,
    branch_l: dict,
    prior_meetings: list[dict],
) -> list[str]:
    """Plain-English standings and tiebreaker bullets for one outcome branch."""
    notes = []
    w_new = _fmt_rec(wp["w"] + 1, wp["l"], wp["t"])
    l_new = _fmt_rec(lp["w"], lp["l"] + 1, lp["t"])
    notes.append(f"{winner} moves to {w_new}; {loser} drops to {l_new}.")

    w_po_d = branch_w["after"]["playoff"] - branch_w["base"]["playoff"]
    l_po_d = branch_l["after"]["playoff"] - branch_l["base"]["playoff"]
    if abs(w_po_d) >= 3 or abs(l_po_d) >= 3:
        notes.append(
            f"Playoff odds shift to {branch_w['after']['playoff']:.0f}% ({w_po_d:+.0f} pts) for {winner} "
            f"and {branch_l['after']['playoff']:.0f}% ({l_po_d:+.0f} pts) for {loser}."
        )

    if g["div_game"]:
        if prior_meetings:
            pm = prior_meetings[-1]
            pm_w = pm["home_team"] if pm["home_score"] > pm["away_score"] else pm["away_team"]
            if pm_w == winner:
                notes.append(f"{winner} completes a 2–0 season sweep over {loser}, locking in the head-to-head tiebreaker in the {wp['div']}.")
            else:
                notes.append(f"Splits the {wp['div']} season series 1–1, pushing any tiebreaker to division record.")
        else:
            notes.append(f"Gives {winner} the early head-to-head tiebreaker and a crucial division win in the {wp['div']}.")
    elif wp["conf"] == lp["conf"]:
        notes.append(f"Counts as a {wp['conf']} conference win for {winner}—critical for wild-card tiebreakers.")

    if branch_w["after"]["div"] - branch_w["base"]["div"] >= 8:
        notes.append(f"Boosts {winner}'s {wp['div']} title odds to {branch_w['after']['div']:.0f}% ({branch_w['after']['div'] - branch_w['base']['div']:+.0f} pts).")
    if branch_w["after"]["bye"] - branch_w["base"]["bye"] >= 5:
        notes.append(f"Pushes {winner}'s #1-seed bye chance to {branch_w['after']['bye']:.0f}% ({branch_w['after']['bye'] - branch_w['base']['bye']:+.0f} pts).")
    if branch_l["after"]["playoff"] <= 5 and branch_l["base"]["playoff"] >= 10:
        notes.append(f"Effectively pushes {loser} to the brink of elimination ({branch_l['after']['playoff']:.0f}% remaining).")
    elif branch_l["after"]["top5"] - branch_l["base"]["top5"] >= 8:
        notes.append(f"Moves {loser}'s top-5 draft-pick odds to {branch_l['after']['top5']:.0f}% ({branch_l['after']['top5'] - branch_l['base']['top5']:+.0f} pts).")

    return notes


def build_watch_data(
    week: int | None = None,
    season: int | None = None,
    n_sims: int = 2500,
    notes_path: Path | None = None,
    raw_rows: list[dict[str, str]] | None = None,
    team_rows: list[dict[str, str]] | None = None,
) -> dict:
    """Build the complete Why Watch dataset for one week (defaults to active week)."""
    rows = raw_rows if raw_rows is not None else _fetch_schedule_rows()
    now = datetime.now(timezone.utc)

    # Pick latest season that has regular-season games (or the explicitly requested season)
    reg_by_season: dict[int, list[dict[str, str]]] = {}
    for r in rows:
        if r.get("game_type") != "REG":
            continue
        s = _opt_int(r.get("season"))
        if s is not None:
            reg_by_season.setdefault(s, []).append(r)
    if not reg_by_season:
        raise RuntimeError("No regular-season NFL games found in schedule feed")

    if season is None:
        # Prefer the current season if it has at least one finished game; otherwise most recent with finished games
        cand_seasons = sorted(reg_by_season.keys(), reverse=True)
        season = next(
            (s for s in cand_seasons if any(g.get("result") not in ("", "NA", None) for g in reg_by_season[s])),
            cand_seasons[0],
        )

    raw_season = reg_by_season[season]
    games: list[dict] = []
    for r in raw_season:
        ht, at = r["home_team"], r["away_team"]
        if ht not in TEAMS or at not in TEAMS:
            continue
        res = _opt_float(r.get("result"))
        hs, as_ = _opt_int(r.get("home_score")), _opt_int(r.get("away_score"))
        finished = res is not None and hs is not None and as_ is not None
        wk = _opt_int(r.get("week")) or 1
        games.append({
            "game_id": r["game_id"],
            "season": season,
            "week": wk,
            "gameday": r.get("gameday") or "",
            "weekday": r.get("weekday") or "",
            "gametime": r.get("gametime") or "",
            "primetime": _is_primetime(r.get("weekday") or "", r.get("gametime") or ""),
            "away_team": at,
            "home_team": ht,
            "away_score": as_,
            "home_score": hs,
            "result": res,
            "finished": finished,
            "spread_line": _opt_float(r.get("spread_line")),
            "total_line": _opt_float(r.get("total_line")),
            "div_game": r.get("div_game") == "1",
            "away_rest": _opt_int(r.get("away_rest")),
            "home_rest": _opt_int(r.get("home_rest")),
            "roof": (r.get("roof") or "").strip().lower(),
            "wind": _opt_float(r.get("wind")),
            "temp": _opt_float(r.get("temp")),
            "away_qb_name": (r.get("away_qb_name") or "").strip(),
            "home_qb_name": (r.get("home_qb_name") or "").strip(),
            "away_coach": (r.get("away_coach") or "").strip(),
            "home_coach": (r.get("home_coach") or "").strip(),
            "stadium": (r.get("stadium") or "").strip(),
        })

    available_weeks = sorted({g["week"] for g in games})
    unfinished_weeks = sorted({g["week"] for g in games if not g["finished"]})
    active_week = unfinished_weeks[0] if unfinished_weeks else available_weeks[-1]
    target_week = week if week in available_weeks else active_week

    finished_all = [g for g in games if g["finished"]]
    remaining_all = [g for g in games if not g["finished"]]
    through_week = max((g["week"] for g in finished_all), default=0)

    # Team profiles from all completed games + scheme/play-style profiles from weekly team stats
    profiles = _compute_team_profiles(finished_all)
    t_rows = team_rows if team_rows is not None else _fetch_team_week_rows(season)
    styles, h2h_logs = _compute_style_profiles(t_rows, finished_all)

    # Optional manual editorial notes (models/watch_notes.json)
    editorial: dict[str, dict] = {}
    if notes_path and notes_path.exists():
        try:
            editorial = json.loads(notes_path.read_text())
        except Exception:
            editorial = {}

    # Vectorized Monte Carlo simulation for all remaining games
    rng = np.random.default_rng(season * 1000 + target_week * 13 + 7)
    base_wins = np.array([profiles[t]["wins_eq"] for t in TEAM_LIST], dtype=float)
    base_div = np.array([profiles[t]["div_wins_eq"] for t in TEAM_LIST], dtype=float)
    base_conf = np.array([profiles[t]["conf_wins_eq"] for t in TEAM_LIST], dtype=float)
    tie_noise = rng.random((n_sims, 32))

    n_rem = len(remaining_all)
    rem_home_idx = np.array([TEAM_IDX[g["home_team"]] for g in remaining_all], dtype=int) if n_rem else np.array([], dtype=int)
    rem_away_idx = np.array([TEAM_IDX[g["away_team"]] for g in remaining_all], dtype=int) if n_rem else np.array([], dtype=int)
    rem_same_div = np.array([TEAMS[g["home_team"]]["div"] == TEAMS[g["away_team"]]["div"] for g in remaining_all], dtype=bool) if n_rem else np.array([], dtype=bool)
    rem_same_conf = np.array([TEAMS[g["home_team"]]["conf"] == TEAMS[g["away_team"]]["conf"] for g in remaining_all], dtype=bool) if n_rem else np.array([], dtype=bool)

    rem_probs = np.empty(n_rem, dtype=float)
    for idx_g, g in enumerate(remaining_all):
        sp = g["spread_line"]
        if sp is None:
            sp = profiles[g["home_team"]]["rating"] - profiles[g["away_team"]]["rating"] + 1.8
        rem_probs[idx_g] = _spread_to_prob(sp)

    # Base simulated outcomes: shape (n_sims, n_rem)
    u = rng.random((n_sims, n_rem)) if n_rem else np.zeros((n_sims, 0))
    home_win_mat = u < rem_probs[None, :] if n_rem else np.zeros((n_sims, 0), dtype=bool)

    sim_wins = np.broadcast_to(base_wins, (n_sims, 32)).copy()
    sim_div = np.broadcast_to(base_div, (n_sims, 32)).copy()
    sim_conf = np.broadcast_to(base_conf, (n_sims, 32)).copy()

    for idx_g in range(n_rem):
        hw = home_win_mat[:, idx_g]
        h_i, a_i = rem_home_idx[idx_g], rem_away_idx[idx_g]
        sim_wins[:, h_i] += hw
        sim_wins[:, a_i] += ~hw
        if rem_same_div[idx_g]:
            sim_div[:, h_i] += hw
            sim_div[:, a_i] += ~hw
        if rem_same_conf[idx_g]:
            sim_conf[:, h_i] += hw
            sim_conf[:, a_i] += ~hw

    base_odds = _eval_league(sim_wins, sim_div, sim_conf, tie_noise)
    rem_pos_by_id = {g["game_id"]: i for i, g in enumerate(remaining_all)}

    # Evaluate each game in target_week
    week_games = [g for g in games if g["week"] == target_week]
    analyzed = []

    for g in week_games:
        home, away = g["home_team"], g["away_team"]
        hp, ap = profiles[home], profiles[away]
        h_i, a_i = TEAM_IDX[home], TEAM_IDX[away]

        # Prior finished meetings between these two teams this season
        prior = [
            x for x in finished_all
            if x["week"] < g["week"] and {x["home_team"], x["away_team"]} == {home, away}
        ]

        # Outcome implications via Common Random Numbers if unfinished
        imp = None
        if g["game_id"] in rem_pos_by_id:
            col = rem_pos_by_id[g["game_id"]]
            hw = home_win_mat[:, col]
            sd_flag = rem_same_div[col]
            sc_flag = rem_same_conf[col]

            def eval_forced(force_home_win: bool) -> dict[str, np.ndarray]:
                w = sim_wins.copy()
                d = sim_div.copy()
                c = sim_conf.copy()
                if force_home_win:
                    flip = (~hw).astype(float)
                    w[:, h_i] += flip
                    w[:, a_i] -= flip
                    if sd_flag:
                        d[:, h_i] += flip
                        d[:, a_i] -= flip
                    if sc_flag:
                        c[:, h_i] += flip
                        c[:, a_i] -= flip
                else:
                    flip = hw.astype(float)
                    w[:, h_i] -= flip
                    w[:, a_i] += flip
                    if sd_flag:
                        d[:, h_i] -= flip
                        d[:, a_i] += flip
                    if sc_flag:
                        c[:, h_i] -= flip
                        c[:, a_i] += flip
                return _eval_league(w, d, c, tie_noise)

            if_h = eval_forced(True)
            if_a = eval_forced(False)

            def pack_team(idx_t: int, forced: dict[str, np.ndarray]) -> dict:
                base_d = {k: round(float(base_odds[k][idx_t] * 100), 1) for k in ("playoff", "div", "bye", "top5")}
                after_d = {k: round(float(forced[k][idx_t] * 100), 1) for k in ("playoff", "div", "bye", "top5")}
                delta_d = {k: round(after_d[k] - base_d[k], 1) for k in ("playoff", "div", "bye", "top5")}
                return {"base": base_d, "after": after_d, "delta": delta_d}

            h_on_h = pack_team(h_i, if_h)
            a_on_h = pack_team(a_i, if_h)
            h_on_a = pack_team(h_i, if_a)
            a_on_a = pack_team(a_i, if_a)

            po_swing = abs(h_on_h["after"]["playoff"] - h_on_a["after"]["playoff"]) + abs(a_on_a["after"]["playoff"] - a_on_h["after"]["playoff"])
            div_swing = abs(h_on_h["after"]["div"] - h_on_a["after"]["div"]) + abs(a_on_a["after"]["div"] - a_on_h["after"]["div"])
            bye_swing = abs(h_on_h["after"]["bye"] - h_on_a["after"]["bye"]) + abs(a_on_a["after"]["bye"] - a_on_h["after"]["bye"])
            draft_swing = abs(h_on_h["after"]["top5"] - h_on_a["after"]["top5"]) + abs(a_on_a["after"]["top5"] - a_on_h["after"]["top5"])

            # Find top 2 conference third-party teams affected (ripple effects)
            confs = {TEAMS[home]["conf"], TEAMS[away]["conf"]}
            ripples = []
            for o_i, ot in enumerate(TEAM_LIST):
                if o_i in (h_i, a_i) or TEAMS[ot]["conf"] not in confs:
                    continue
                po_d = float((if_h["playoff"][o_i] - if_a["playoff"][o_i]) * 100)
                dv_d = float((if_h["div"][o_i] - if_a["div"][o_i]) * 100)
                by_d = float((if_h["bye"][o_i] - if_a["bye"][o_i]) * 100)
                mag = abs(po_d) + 0.65 * abs(dv_d) + 0.45 * abs(by_d)
                if max(abs(po_d), abs(dv_d), abs(by_d)) >= 1.5:
                    # Determine dominant metric and which winner helps this team
                    if abs(po_d) >= abs(dv_d) and abs(po_d) >= abs(by_d):
                        metric, diff = "playoff", po_d
                    elif abs(dv_d) >= abs(by_d):
                        metric, diff = "division", dv_d
                    else:
                        metric, diff = "#1-seed bye", by_d
                    roots_for = home if diff > 0 else away
                    ripples.append({
                        "team": ot,
                        "name": TEAMS[ot]["name"],
                        "record": profiles[ot]["record"],
                        "roots_for": roots_for,
                        "metric": metric,
                        "swing": round(abs(diff), 1),
                        "if_home_playoff": round(float(if_h["playoff"][o_i] * 100), 1),
                        "if_away_playoff": round(float(if_a["playoff"][o_i] * 100), 1),
                        "_mag": mag,
                    })
            ripples.sort(key=lambda r: -r["_mag"])
            ripples = [{k: v for k, v in r.items() if k != "_mag"} for r in ripples[:3]]

            imp = {
                "home": {"team": home, "base": h_on_h["base"], "if_home": h_on_h, "if_away": h_on_a},
                "away": {"team": away, "base": a_on_h["base"], "if_home": a_on_h, "if_away": a_on_a},
                "total_playoff_swing": round(po_swing, 1),
                "total_div_swing": round(div_swing, 1),
                "total_bye_swing": round(bye_swing, 1),
                "total_draft_swing": round(draft_swing, 1),
                "branches": {
                    "home": {
                        "winner": home,
                        "loser": away,
                        "label": f"If {home} wins",
                        "home": h_on_h,
                        "away": a_on_h,
                        "notes": _standings_notes_for_branch(home, away, hp, ap, g, h_on_h, a_on_h, prior),
                    },
                    "away": {
                        "winner": away,
                        "loser": home,
                        "label": f"If {away} wins",
                        "home": h_on_a,
                        "away": a_on_a,
                        "notes": _standings_notes_for_branch(away, home, ap, hp, g, a_on_a, h_on_a, prior),
                    },
                },
                "ripples": ripples,
            }

        # --- Transparent 5-driver Interest Score (0-100) ---
        proj_spread = g["spread_line"] if g["spread_line"] is not None else (hp["rating"] - ap["rating"] + 1.8)
        abs_sp = abs(proj_spread)
        total_est = g["total_line"] if g["total_line"] is not None else (hp["ppg"] + ap["ppg"] + hp["papg"] + ap["papg"]) / 2.0

        # 1. Playoff & Division Leverage (max 34)
        if imp:
            raw_lev = (
                imp["total_playoff_swing"] * 0.65
                + imp["total_div_swing"] * 0.32
                + imp["total_bye_swing"] * 0.35
            )
            lev_pts = min(34.0, raw_lev * 0.88)
            if imp["total_bye_swing"] >= 25 and imp["total_bye_swing"] > imp["total_playoff_swing"] * 1.4:
                lev_val = f"±{imp['total_bye_swing']:.0f}% #1-seed swing"
            elif imp["total_div_swing"] >= 20 and imp["total_div_swing"] > imp["total_playoff_swing"] * 1.3:
                lev_val = f"±{imp['total_div_swing']:.0f}% div swing"
            else:
                lev_val = f"±{imp['total_playoff_swing']:.0f}% PO swing"
            if lev_pts < 4.0 and imp["total_draft_swing"] >= 20.0:
                lev_pts = min(8.0, imp["total_draft_swing"] * 0.16)
                lev_val = f"±{imp['total_draft_swing']:.0f}% top-5 draft"
        else:
            # Completed game fallback based on teams' current playoff relevance
            rel = (base_odds["playoff"][h_i] + base_odds["playoff"][a_i]) * 50.0
            lev_pts = min(26.0, rel * 0.35)
            lev_val = "Completed game"

        # 2. Competitiveness / Drama (max 24)
        comp_pts = 24.0 * math.exp(-((abs_sp / 7.2) ** 1.45))
        comp_val = _fmt_spread(g["spread_line"], home, away)

        # 3. Scoring Pace & Fireworks (max 18)
        pace_pts = max(2.0, min(18.0, 9.0 + (total_est - 44.0) * 0.95))
        if total_est <= 39.5 and abs_sp <= 4.5:
            pace_pts = min(14.0, pace_pts + 4.5)
            pace_val = f"{total_est:.1f} total (rock fight)"
        else:
            pace_val = f"{total_est:.1f} O/U"

        # 4. Matchup Quality & Contrast (max 14)
        avg_wp = 0.5 * (hp["win_pct"] + ap["win_pct"])
        qual_pts = max(0.0, min(10.0, ((avg_wp - 0.22) / 0.52) * 10.0))
        contrast = 0.0
        if (ap["off_rank"] <= 10 and hp["def_rank"] <= 10) or (hp["off_rank"] <= 10 and ap["def_rank"] <= 10):
            contrast += 3.0
        elif ap["off_rank"] <= 10 and hp["off_rank"] <= 10:
            contrast += 2.5
        if hp["win_pct"] >= 0.5 and ap["win_pct"] >= 0.5:
            contrast += 1.5
        qual_pts = min(14.0, qual_pts + contrast)
        qual_val = f"{ap['record']} vs {hp['record']}"

        # 5. Storyline & Context (max 10)
        ctx_pts = 0.0
        ctx_tags = []
        if g["div_game"]:
            ctx_pts += 4.0 + (1.5 if prior else 0.0)
            ctx_tags.append("Divisional rematch" if prior else "Divisional")
        elif hp["div_rank"] == 1 and ap["div_rank"] == 1:
            ctx_pts += 3.5
            ctx_tags.append("Division leaders")
        if g["primetime"]:
            ctx_pts += 2.5
            ctx_tags.append(f"{g['weekday'][:3]} night")
        if g["home_rest"] and g["away_rest"] and abs(g["home_rest"] - g["away_rest"]) >= 3:
            ctx_pts += 1.5
            ctx_tags.append("Rest edge")
        if hp["streak_len"] >= 3 or ap["streak_len"] >= 3:
            ctx_pts += 1.5
            ctx_tags.append("Hot streak")
        ctx_pts = min(10.0, ctx_pts)
        ctx_val = " · ".join(ctx_tags) if ctx_tags else "Standard Sunday"

        drivers = [
            {"id": "leverage", "label": "Stakes & playoff leverage", "points": round(lev_pts, 1), "max": 34, "value": lev_val},
            {"id": "competitiveness", "label": "Competitiveness (spread)", "points": round(comp_pts, 1), "max": 24, "value": comp_val},
            {"id": "pace", "label": "Scoring pace & style", "points": round(pace_pts, 1), "max": 18, "value": pace_val},
            {"id": "quality", "label": "Team quality & contrast", "points": round(qual_pts, 1), "max": 14, "value": qual_val},
            {"id": "context", "label": "Rivalry & spotlight context", "points": round(ctx_pts, 1), "max": 10, "value": ctx_val},
        ]
        drivers_by_id = {d["id"]: d for d in drivers}
        interest_score = int(round(sum(d["points"] for d in drivers)))
        interest_score = max(0, min(100, interest_score))
        tier = (
            "Must Watch" if interest_score >= 74
            else "Strong Watch" if interest_score >= 58
            else "Intriguing" if interest_score >= 42
            else "Niche"
        )

        # Tags for client-side filtering
        tags = []
        if imp and (imp["total_playoff_swing"] >= 16 or imp["total_div_swing"] >= 18 or imp["total_bye_swing"] >= 20):
            tags.append("High Leverage")
        if abs_sp <= 4.0:
            tags.append("Toss-ups")
        if total_est >= 47.5:
            tags.append("Shootouts")
        if g["div_game"]:
            tags.append("Divisional")
        if g["primetime"]:
            tags.append("Primetime")

        hook, why_notes = _build_why_watch(g, hp, ap, imp, drivers, prior)
        style_matchups = _build_style_matchups(g, styles, h2h_logs)
        targets = _prediction_targets(g, hp, ap, imp, drivers_by_id)

        # Optional custom editorial override from models/watch_notes.json
        ed = editorial.get(g["game_id"])
        if ed:
            if ed.get("hook"):
                hook = ed["hook"]
            if ed.get("note"):
                why_notes.insert(0, {"label": "Editor's Note", "text": ed["note"]})

        home_wp_mkt = round(_spread_to_prob(proj_spread) * 100)
        a_st, h_st = styles.get(away, {}), styles.get(home, {})
        analyzed.append({
            "game_id": g["game_id"],
            "week": g["week"],
            "gameday": g["gameday"],
            "weekday": g["weekday"],
            "gametime": g["gametime"],
            "primetime": g["primetime"],
            "finished": g["finished"],
            "div_game": g["div_game"],
            "stadium": g["stadium"],
            "roof": g["roof"],
            "spread_line": g["spread_line"],
            "spread_label": _fmt_spread(g["spread_line"], home, away),
            "total_line": g["total_line"],
            "home_win_prob": home_wp_mkt,
            "away_win_prob": 100 - home_wp_mkt,
            "away": {
                "team": away, "name": ap["name"], "city": ap["city"], "conf": ap["conf"], "div": ap["div"],
                "record": ap["record"], "div_rank": ap["div_rank"], "streak": ap["streak"],
                "ppg": round(ap["ppg"], 1), "papg": round(ap["papg"], 1),
                "off_rank": ap["off_rank"], "def_rank": ap["def_rank"],
                "off_scheme": a_st.get("off_label", ""), "def_scheme": a_st.get("def_label", ""),
                "qb": g["away_qb_name"], "coach": g["away_coach"], "rest": g["away_rest"],
                "score": g["away_score"],
                "playoff_pct": round(float(base_odds["playoff"][a_i] * 100), 1),
                "div_pct": round(float(base_odds["div"][a_i] * 100), 1),
            },
            "home": {
                "team": home, "name": hp["name"], "city": hp["city"], "conf": hp["conf"], "div": hp["div"],
                "record": hp["record"], "div_rank": hp["div_rank"], "streak": hp["streak"],
                "ppg": round(hp["ppg"], 1), "papg": round(hp["papg"], 1),
                "off_rank": hp["off_rank"], "def_rank": hp["def_rank"],
                "off_scheme": h_st.get("off_label", ""), "def_scheme": h_st.get("def_label", ""),
                "qb": g["home_qb_name"], "coach": g["home_coach"], "rest": g["home_rest"],
                "score": g["home_score"],
                "playoff_pct": round(float(base_odds["playoff"][h_i] * 100), 1),
                "div_pct": round(float(base_odds["div"][h_i] * 100), 1),
            },
            "interest_score": interest_score,
            "tier": tier,
            "tags": tags,
            "hook": hook,
            "why_watch": why_notes,
            "style_matchups": style_matchups,
            "drivers": drivers,
            "implications": imp,
            "predict": targets,
        })

    # Rank: upcoming games first by Interest Score desc, then finished games by Interest Score desc
    analyzed.sort(key=lambda x: (x["finished"], -x["interest_score"], x["gameday"], x["gametime"]))
    for rank_i, item in enumerate(analyzed, 1):
        item["rank"] = rank_i

    return {
        "season": season,
        "week": target_week,
        "active_week": active_week,
        "through_week": through_week,
        "available_weeks": available_weeks,
        "n_sims": n_sims,
        "updated": now.strftime("%Y-%m-%d %H:%M UTC"),
        "games": analyzed,
    }


def build_all_weeks_cache(n_sims: int = 2500, notes_path: Path | None = None) -> dict:
    """Fetch schedule + weekly team stats once and keep rows for on-demand week switches."""
    rows = _fetch_schedule_rows()
    reg_seasons = sorted(
        {_opt_int(r.get("season")) for r in rows if r.get("game_type") == "REG" and _opt_int(r.get("season")) is not None},
        reverse=True,
    )
    active_season = next(
        (s for s in reg_seasons if any(r.get("season") == str(s) and r.get("game_type") == "REG" and r.get("result") not in ("", "NA", None) for r in rows)),
        reg_seasons[0],
    )
    team_rows = _fetch_team_week_rows(active_season)
    active_data = build_watch_data(week=None, season=active_season, n_sims=n_sims, notes_path=notes_path, raw_rows=rows, team_rows=team_rows)
    return {"active": active_data, "rows": rows, "team_rows": team_rows}
