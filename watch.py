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

    # Bullet 2: Matchup & Style
    qb_txt = (
        f"{g['away_qb_name']} vs. {g['home_qb_name']} at quarterback. "
        if g.get("away_qb_name") and g.get("home_qb_name") else ""
    )
    style_bits = [
        f"{qb_txt}{away} averages {ap['ppg']:.1f} PPG (#{ap['off_rank']} offense) and allows {ap['papg']:.1f} (#{ap['def_rank']} defense), "
        f"while {home} scores {hp['ppg']:.1f} (#{hp['off_rank']}) and allows {hp['papg']:.1f} (#{hp['def_rank']})."
    ]
    if ap["off_rank"] <= 10 and hp["def_rank"] <= 10:
        style_bits.append(f"Classic strength-on-strength: {away}'s top-10 offense tests {home}'s top-10 defense.")
    elif hp["off_rank"] <= 10 and ap["def_rank"] <= 10:
        style_bits.append(f"Classic strength-on-strength: {home}'s top-10 offense meets {away}'s top-10 defense.")
    elif ap["off_rank"] <= 10 and hp["off_rank"] <= 10:
        style_bits.append("Two top-10 scoring offenses collide, putting red-zone efficiency and explosive plays at center stage.")
    elif ap["def_rank"] <= 10 and hp["def_rank"] <= 10:
        style_bits.append("Two top-10 defenses limit easy yards—turnovers and field position carry outsized weight.")
    notes.append({"label": "Matchup & Style", "text": " ".join(style_bits)})

    # Bullet 3: Context / Edge / Rematch / Rest
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

    # Team profiles from all completed games
    profiles = _compute_team_profiles(finished_all)

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
        targets = _prediction_targets(g, hp, ap, imp, drivers_by_id)

        # Optional custom editorial override from models/watch_notes.json
        ed = editorial.get(g["game_id"])
        if ed:
            if ed.get("hook"):
                hook = ed["hook"]
            if ed.get("note"):
                why_notes.insert(0, {"label": "Editor's Note", "text": ed["note"]})

        home_wp_mkt = round(_spread_to_prob(proj_spread) * 100)
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
    """Fetch schedule once and compute the active week plus keep raw rows for on-demand week switches."""
    rows = _fetch_schedule_rows()
    active_data = build_watch_data(week=None, n_sims=n_sims, notes_path=notes_path, raw_rows=rows)
    return {"active": active_data, "rows": rows}
