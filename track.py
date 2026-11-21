"""Why Watch Verification & Tracking module for ddyno.

Walks forward point-in-time through every completed week of the active NFL season
(using ONLY prior weeks < w to diagnose each game, zero future data leakage) and grades:
  1. Watchability tier calibration (Must Watch / Strong Watch / Intriguing / Niche vs. how games played out)
  2. Scheme diagnosis hold rate (did teams actually play the offensive/defensive scheme diagnosed pregame?)
  3. Style-vs.-style edge accuracy & Scheme-vs.-Scheme 2026 matchup matrix
  4. Stakes outcome tracking (favorites vs. upsets, spread covers, high-stakes finishes)
  5. 'What to Watch For' cue verification (did the concrete on-field win condition predict who succeeded?)
"""
from __future__ import annotations

import math
from datetime import datetime, timezone

import numpy as np

import watch


def _approx_stakes_leverage(
    g: dict,
    hp: dict,
    ap: dict,
    profiles: dict[str, dict],
) -> tuple[float, float, str]:
    """Fast point-in-time stakes/leverage proxy (0-34 pts) using only standings entering week w."""
    wk = g["week"]
    # Season urgency ramps up as weeks progress
    urgency = min(1.35, 0.55 + (wk / 14.0) * 0.8)

    def team_contention(p: dict) -> float:
        # Distance from .500 / playoff bubble; contenders near .500-.850 have highest swing leverage
        wp = p["win_pct"]
        if wp >= 0.85:
            return 0.72  # #1 seed / bye stakes
        if wp >= 0.42:
            return 1.0 - abs(wp - 0.60) * 0.65
        if wp >= 0.30:
            return 0.45
        return 0.15

    h_c, a_c = team_contention(hp), team_contention(ap)
    same_div = g["div_game"]
    same_conf = hp["conf"] == ap["conf"]
    base_lev = (h_c + a_c) * 10.5 * urgency
    if same_div:
        base_lev *= 1.32
    elif same_conf:
        base_lev *= 1.12
    lev_pts = min(34.0, round(base_lev, 1))
    # Approximate swing percentage for labeling
    est_swing = round(min(48.0, lev_pts * 1.15), 1)
    if hp["div_rank"] == 1 and ap["div_rank"] == 1 and wk >= 6:
        label = f"Top-seed / division leaders ({ap['record']} vs {hp['record']})"
    elif same_div and max(h_c, a_c) >= 0.7:
        label = f"{hp['div']} division battle"
    elif min(h_c, a_c) >= 0.65:
        label = f"Playoff contenders clash ({ap['record']} vs {hp['record']})"
    elif max(h_c, a_c) >= 0.75:
        label = f"{hp['team'] if h_c >= a_c else ap['team']} protecting playoff positioning"
    else:
        label = "Lower-stakes / draft-order positioning"
    return lev_pts, est_swing, label


def _pregame_interest_score(
    g: dict,
    hp: dict,
    ap: dict,
    profiles: dict[str, dict],
    prior_meetings: list[dict],
) -> tuple[int, str, float, str]:
    """Point-in-time 0-100 Interest Score & tier using only pregame lines and prior-week profiles."""
    home, away = g["home_team"], g["away_team"]
    proj_spread = g["spread_line"] if g["spread_line"] is not None else (hp["rating"] - ap["rating"] + 1.8)
    abs_sp = abs(proj_spread)
    total_est = g["total_line"] if g["total_line"] is not None else (hp["ppg"] + ap["ppg"] + hp["papg"] + ap["papg"]) / 2.0

    lev_pts, est_swing, stakes_label = _approx_stakes_leverage(g, hp, ap, profiles)
    comp_pts = 24.0 * math.exp(-((abs_sp / 7.2) ** 1.45))
    pace_pts = max(2.0, min(18.0, 9.0 + (total_est - 44.0) * 0.95))
    if total_est <= 39.5 and abs_sp <= 4.5:
        pace_pts = min(14.0, pace_pts + 4.5)

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

    ctx_pts = 0.0
    if g["div_game"]:
        ctx_pts += 4.0 + (1.5 if prior_meetings else 0.0)
    elif hp["div_rank"] == 1 and ap["div_rank"] == 1:
        ctx_pts += 3.5
    if g["primetime"]:
        ctx_pts += 2.5
    if g["home_rest"] and g["away_rest"] and abs(g["home_rest"] - g["away_rest"]) >= 3:
        ctx_pts += 1.5
    if hp["streak_len"] >= 3 or ap["streak_len"] >= 3:
        ctx_pts += 1.5
    ctx_pts = min(10.0, ctx_pts)

    score = max(0, min(100, int(round(lev_pts + comp_pts + pace_pts + qual_pts + ctx_pts))))
    tier = (
        "Must Watch" if score >= 74
        else "Strong Watch" if score >= 58
        else "Intriguing" if score >= 42
        else "Niche"
    )
    return score, tier, est_swing, stakes_label


def _game_stats_from_row(off_row: dict[str, str], def_row: dict[str, str]) -> dict[str, float]:
    """Extract actual single-game offensive & defensive style metrics from weekly team rows."""
    n = watch._num0
    att, comp, sacks_s = n(off_row, "attempts"), n(off_row, "completions"), n(off_row, "sacks_suffered")
    py, air, yac = n(off_row, "passing_yards"), n(off_row, "passing_air_yards"), n(off_row, "passing_yards_after_catch")
    p20, pepa, ints = n(off_row, "passing_20"), n(off_row, "passing_epa"), n(off_row, "passing_interceptions")
    ptds = n(off_row, "passing_tds")
    car, ry, r10, repa = n(off_row, "carries"), n(off_row, "rushing_yards"), n(off_row, "rushing_10"), n(off_row, "rushing_epa")
    dsacks, dqbh = n(def_row, "def_sacks"), n(def_row, "def_qb_hits")
    dtfl, dint, dpd = n(def_row, "def_tackles_for_loss"), n(def_row, "def_interceptions"), n(def_row, "def_pass_defended")

    db = max(1.0, att + sacks_s)
    plays = max(1.0, db + car)
    return {
        "pass_rate": db / plays,
        "adot": air / max(1.0, att),
        "ypa": py / max(1.0, att),
        "yac_share": yac / max(1.0, py),
        "yac_per_comp": yac / max(1.0, comp),
        "exp_pass_rate": p20 / max(1.0, att),
        "p20": p20,
        "ptds": ptds,
        "ints": ints,
        "sacks_s": sacks_s,
        "sack_rate": sacks_s / db,
        "ypc": ry / max(1.0, car),
        "r10": r10,
        "pass_epa": pepa / db,
        "rush_epa": repa / max(1.0, car),
        "off_epa": (pepa + repa) / plays,
        "pressure_rate": (dsacks + dqbh) / db,
        "tfl_rate": dtfl / max(1.0, car),
        "ballhawk_rate": (dint + dpd) / max(1.0, att),
        "dsacks": dsacks,
        "dtfl": dtfl,
    }


def _check_off_scheme_held(off_key: str, act: dict[str, float]) -> tuple[bool, str]:
    """Check whether the offense actually played its pregame-diagnosed scheme in the game."""
    if off_key in ("air_vertical", "spread_pass"):
        ok = act["pass_rate"] >= 0.56
        return ok, f"{act['pass_rate'] * 100:.0f}% pass rate"
    if off_key in ("ground_control", "run_first"):
        ok = act["pass_rate"] <= 0.54 or act["ypc"] >= 4.4
        return ok, f"{(1 - act['pass_rate']) * 100:.0f}% run rate ({act['ypc']:.1f} YPC)"
    if off_key == "vertical_air":
        ok = act["adot"] >= 8.0 or act["p20"] >= 3
        return ok, f"{act['adot']:.1f}-yd aDOT, {int(act['p20'])} plays of 20+"
    if off_key == "explosive_balanced":
        ok = act["p20"] >= 3 or act["ypa"] >= 7.5
        return ok, f"{int(act['p20'])} plays of 20+, {act['ypa']:.1f} YPA"
    if off_key in ("yac_rhythm", "short_rhythm"):
        ok = act["yac_share"] >= 0.44 or act["adot"] <= 7.8
        return ok, f"{act['yac_share'] * 100:.0f}% YAC, {act['adot']:.1f}-yd aDOT"
    # Pro-Style balanced
    ok = 0.42 <= act["pass_rate"] <= 0.66
    return ok, f"{act['pass_rate'] * 100:.0f}% pass / {(1 - act['pass_rate']) * 100:.0f}% run"


def _check_def_scheme_held(def_key: str, act: dict[str, float]) -> tuple[bool, str]:
    """Check whether the defense actually played its pregame-diagnosed scheme in the game."""
    if def_key in ("pressure_havoc", "pressure_front"):
        ok = act["pressure_rate"] >= 0.22 or act["dsacks"] >= 3
        return ok, f"{act['pressure_rate'] * 100:.0f}% pressure, {int(act['dsacks'])} sacks"
    if def_key == "aggressive_front":
        ok = act["tfl_rate"] >= 0.18 or act["pressure_rate"] >= 0.22
        return ok, f"{act['tfl_rate'] * 100:.0f}% TFLs, {act['pressure_rate'] * 100:.0f}% pressure"
    if def_key in ("two_high_shell", "ballhawk_shell"):
        ok = act["exp_pass_rate"] <= 0.095 or act["ballhawk_rate"] >= 0.16
        return ok, f"{act['exp_pass_rate'] * 100:.1f}% explosives allowed, {act['ballhawk_rate'] * 100:.0f}% INT/PBU"
    if def_key == "run_stuff_funnel":
        ok = act["tfl_rate"] >= 0.17 or act["ypc"] <= 4.0
        return ok, f"{act['tfl_rate'] * 100:.0f}% TFLs, {act['ypc']:.1f} YPC allowed"
    if def_key == "light_box_cov":
        ok = act["ypa"] <= 6.8 or act["ballhawk_rate"] >= 0.15
        return ok, f"{act['ypa']:.1f} YPA allowed"
    ok = act["exp_pass_rate"] <= 0.12
    return ok, f"{act['exp_pass_rate'] * 100:.1f}% explosives allowed"


def _evaluate_watch_for_cue(
    os_: dict,
    ds_: dict,
    act: dict[str, float],
    off_won_game: bool,
) -> dict:
    """Evaluate an observable on-field 'What to watch for' trigger against whether the offense won."""
    om, dm = os_["metrics"], ds_["metrics"]
    oz, dz = os_["z"], ds_["z"]
    pass_net = om["pass_epa"] + dm["opp_pass_epa"]
    rush_net = om["rush_epa"] + dm["opp_rush_epa"]

    if dz["pressure_rate"] >= 0.65 and oz["sack_rate"] >= 0.35:
        cue_type = "Protection vs. Blitz"
        cue_rule = "Hold blitzing front under 3 sacks"
        triggered = act["sacks_s"] < 3
        actual_txt = f"{int(act['sacks_s'])} sacks taken ({act['pressure_rate'] * 100:.0f}% pressure)"
    elif dz["pressure_rate"] >= 0.65:
        cue_type = "Pocket vs. Pass Rush"
        cue_rule = "Handle rush (<3 sacks & 7.0+ yds/att)"
        triggered = (act["sacks_s"] < 3) and (act["ypa"] >= 7.0)
        actual_txt = f"{int(act['sacks_s'])} sacks, {act['ypa']:.1f} yds/att"
    elif ds_["def_key"] in ("two_high_shell", "ballhawk_shell") and os_["off_key"] in ("vertical_air", "explosive_balanced", "air_vertical"):
        cue_type = "Vertical vs. Two-High Shell"
        cue_rule = "Stay patient (0 INTs & 4.0+ yds/carry)"
        triggered = (act["ints"] == 0) and (act["ypc"] >= 4.0)
        actual_txt = f"{int(act['ints'])} INTs, {act['ypc']:.1f} yds/carry"
    elif os_["off_key"] in ("spread_pass", "air_vertical") and ds_["def_key"] in ("balanced_zone", "light_box_cov", "two_high_shell"):
        cue_type = "Spread vs. Zone"
        cue_rule = "Finish spread drives with 2+ pass TDs"
        triggered = act["ptds"] >= 2
        actual_txt = f"{int(act['ptds'])} pass TDs ({act['ypa']:.1f} YPA)"
    elif ds_["def_key"] == "ballhawk_shell":
        cue_type = "Turnover Battle vs. Ball-Hawks"
        cue_rule = "Protect football (0 interceptions thrown)"
        triggered = act["ints"] == 0
        actual_txt = f"{int(act['ints'])} INTs thrown ({act['ballhawk_rate'] * 100:.0f}% def INT/PBU)"
    elif os_["off_key"] in ("ground_control", "run_first") and ds_["def_key"] in ("run_stuff_funnel", "aggressive_front", "pressure_havoc"):
        cue_type = "Power Run vs. TFL Front"
        cue_rule = "Stay on schedule (4.0+ yards/carry)"
        triggered = act["ypc"] >= 4.0
        actual_txt = f"{act['ypc']:.1f} yds/carry ({int(act['dtfl'])} TFLs allowed)"
    elif os_["off_key"] == "yac_rhythm" or oz["yac_share"] >= 0.65:
        cue_type = "YAC Space vs. Tackling"
        cue_rule = "Turn short throws into 5.0+ YAC/completion"
        triggered = act["yac_per_comp"] >= 5.0
        actual_txt = f"{act['yac_per_comp']:.1f} YAC/comp ({act['yac_share'] * 100:.0f}% YAC share)"
    elif dm["opp_exp_pass_rate"] >= 0.095:
        cue_type = "Explosive Shots vs. Soft Deep Def"
        cue_rule = "Hit 3+ explosive passes of 20+ yards"
        triggered = act["p20"] >= 3
        actual_txt = f"{int(act['p20'])} plays of 20+ yds ({act['ypa']:.1f} YPA)"
    else:
        if pass_net >= rush_net:
            cue_type = "Passing Efficiency Edge"
            cue_rule = "Clear 7.2+ yards per pass attempt"
            triggered = act["ypa"] >= 7.2
            actual_txt = f"{act['ypa']:.1f} yds/att ({int(act['ptds'])} TDs, {int(act['ints'])} INT)"
        else:
            cue_type = "Ground Efficiency Edge"
            cue_rule = "Clear 4.3+ yards per carry"
            triggered = act["ypc"] >= 4.3
            actual_txt = f"{act['ypc']:.1f} yds/carry ({int(act['r10'])} runs of 10+)"

    # Grade strictly against winning the game (non-circular observable test)
    cue_correct = (triggered == off_won_game)
    verdict = (
        "Cue hit & offense won" if (triggered and off_won_game)
        else "Defense denied cue & won" if ((not triggered) and (not off_won_game))
        else "Cue hit, but team still lost" if triggered
        else "Team won despite missing cue"
    )
    return {
        "cue_type": cue_type,
        "rule": cue_rule,
        "triggered": triggered,
        "off_succeeded": off_won_game,
        "correct": cue_correct,
        "actual": actual_txt,
        "verdict": verdict,
    }


def build_track_data(
    season: int | None = None,
    raw_rows: list[dict[str, str]] | None = None,
    team_rows: list[dict[str, str]] | None = None,
    min_week: int = 3,
) -> dict:
    """Walk forward through completed games (week >= min_week) and grade Why Watch accuracy."""
    rows = raw_rows if raw_rows is not None else watch._fetch_schedule_rows()
    now = datetime.now(timezone.utc)

    reg_by_season: dict[int, list[dict[str, str]]] = {}
    for r in rows:
        if r.get("game_type") != "REG":
            continue
        s = watch._opt_int(r.get("season"))
        if s is not None:
            reg_by_season.setdefault(s, []).append(r)
    if not reg_by_season:
        raise RuntimeError("No regular-season NFL games found for tracking")

    if season is None:
        cand = sorted(reg_by_season.keys(), reverse=True)
        season = next(
            (s for s in cand if any(g.get("result") not in ("", "NA", None) for g in reg_by_season[s])),
            cand[0],
        )

    t_rows = team_rows if team_rows is not None else watch._fetch_team_week_rows(season)

    # Parse all regular-season games for this season
    games: list[dict] = []
    for r in reg_by_season[season]:
        ht, at = r["home_team"], r["away_team"]
        if ht not in watch.TEAMS or at not in watch.TEAMS:
            continue
        res = watch._opt_float(r.get("result"))
        hs, as_ = watch._opt_int(r.get("home_score")), watch._opt_int(r.get("away_score"))
        if res is None or hs is None or as_ is None:
            continue
        games.append({
            "game_id": r["game_id"],
            "season": season,
            "week": watch._opt_int(r.get("week")) or 1,
            "gameday": r.get("gameday") or "",
            "weekday": r.get("weekday") or "",
            "gametime": r.get("gametime") or "",
            "primetime": watch._is_primetime(r.get("weekday") or "", r.get("gametime") or ""),
            "away_team": at,
            "home_team": ht,
            "away_score": as_,
            "home_score": hs,
            "result": res,
            "overtime": r.get("overtime") == "1",
            "spread_line": watch._opt_float(r.get("spread_line")),
            "total_line": watch._opt_float(r.get("total_line")),
            "div_game": r.get("div_game") == "1",
            "away_rest": watch._opt_int(r.get("away_rest")),
            "home_rest": watch._opt_int(r.get("home_rest")),
            "away_qb_name": (r.get("away_qb_name") or "").strip(),
            "home_qb_name": (r.get("home_qb_name") or "").strip(),
        })

    # Index team_rows by game_id -> team and by week
    by_game_team: dict[str, dict[str, dict[str, str]]] = {}
    for r in t_rows:
        by_game_team.setdefault(r["game_id"], {})[r["team"]] = r

    finished_weeks = sorted({g["week"] for g in games})
    eval_weeks = [w for w in finished_weeks if w >= min_week]
    graded_games: list[dict] = []

    # Aggregators
    tier_order = ["Must Watch", "Strong Watch", "Intriguing", "Niche"]
    tier_stats = {t: {"tier": t, "games": 0, "delivered": 0, "one_score": 0, "upsets": 0, "margins": [], "totals": []} for t in tier_order}
    scheme_matrix: dict[tuple[str, str], dict] = {}
    cue_stats: dict[str, dict] = {}

    diag_total, diag_held = 0, 0
    edge_total, edge_correct = 0, 0
    cue_total, cue_correct = 0, 0
    fav_total, fav_won, fav_covered = 0, 0, 0
    high_stakes_total, high_stakes_close, high_stakes_upsets = 0, 0, 0

    for wk in eval_weeks:
        # Strict point-in-time slice: ONLY weeks < wk!
        prior_games = [g for g in games if g["week"] < wk]
        prior_team_rows = [r for r in t_rows if (watch._opt_int(r.get("week")) or 0) < wk]
        if not prior_games:
            continue
        profiles = watch._compute_team_profiles(prior_games)
        styles, _ = watch._compute_style_profiles(prior_team_rows, prior_games)

        week_games = [g for g in games if g["week"] == wk]
        for g in week_games:
            home, away = g["home_team"], g["away_team"]
            hp, ap = profiles[home], profiles[away]
            prior_h2h = [x for x in prior_games if {x["home_team"], x["away_team"]} == {home, away}]

            score, tier, est_swing, stakes_label = _pregame_interest_score(g, hp, ap, profiles, prior_h2h)

            hs, as_ = g["home_score"], g["away_score"]
            margin = abs(hs - as_)
            total_pts = hs + as_
            one_score = (margin <= 8) or g["overtime"]
            winner = home if hs > as_ else away if as_ > hs else "TIE"

            sp = g["spread_line"]
            upset = False
            fav_team = None
            spread_result = "No line"
            if sp is not None and abs(sp) >= 0.5:
                fav_team = home if sp > 0 else away
                fav_total += 1
                fav_margin = (hs - as_) if sp > 0 else (as_ - hs)
                if fav_margin > 0:
                    fav_won += 1
                elif fav_margin < 0:
                    upset = True
                if fav_margin > abs(sp):
                    fav_covered += 1
                    spread_result = f"{fav_team} covered ({watch._fmt_spread(sp, home, away)})"
                elif fav_margin < abs(sp):
                    spread_result = f"{away if fav_team == home else home} covered ({watch._fmt_spread(sp, home, away)})"
                else:
                    spread_result = f"Push ({watch._fmt_spread(sp, home, away)})"

            big_upset = upset and sp is not None and abs(sp) >= 5.0
            shootout_close = (total_pts >= 50) and (margin <= 14)
            delivered = one_score or shootout_close or big_upset

            ts = tier_stats[tier]
            ts["games"] += 1
            ts["delivered"] += int(delivered)
            ts["one_score"] += int(one_score)
            ts["upsets"] += int(upset)
            ts["margins"].append(margin)
            ts["totals"].append(total_pts)

            if score >= 58:
                high_stakes_total += 1
                high_stakes_close += int(one_score)
                high_stakes_upsets += int(upset)

            # Grade both sides of the ball (scheme diagnosis, style edge, scheme-vs-scheme, what-to-watch-for cue)
            sides_graded = []
            h_row = by_game_team.get(g["game_id"], {}).get(home)
            a_row = by_game_team.get(g["game_id"], {}).get(away)
            if h_row and a_row and home in styles and away in styles:
                for off_t, def_t, off_r, def_r in (
                    (away, home, a_row, h_row),
                    (home, away, h_row, a_row),
                ):
                    os_, ds_ = styles[off_t], styles[def_t]
                    act = _game_stats_from_row(off_r, def_r)
                    off_won_game = (winner == off_t)

                    # 1. Scheme diagnosis hold checks
                    off_held, off_act_txt = _check_off_scheme_held(os_["off_key"], act)
                    def_held, def_act_txt = _check_def_scheme_held(ds_["def_key"], act)
                    diag_total += 2
                    diag_held += int(off_held) + int(def_held)

                    # 2. Style edge check
                    om, dm = os_["metrics"], ds_["metrics"]
                    pass_net = om["pass_epa"] + dm["opp_pass_epa"]
                    rush_net = om["rush_epa"] + dm["opp_rush_epa"]
                    net = om["pass_rate"] * pass_net + (1.0 - om["pass_rate"]) * rush_net
                    if net >= 0.07:
                        pred_edge = f"Edge: {off_t} Off"
                        edge_hit = act["off_epa"] >= 0.0
                        edge_total += 1
                        edge_correct += int(edge_hit)
                    elif net <= -0.07:
                        pred_edge = f"Edge: {def_t} Def"
                        edge_hit = act["off_epa"] <= 0.0
                        edge_total += 1
                        edge_correct += int(edge_hit)
                    else:
                        pred_edge = "Even style clash"
                        edge_hit = None

                    # 3. Scheme-vs-Scheme matrix entry
                    mk = (os_["off_label"], ds_["def_label"])
                    sm = scheme_matrix.setdefault(mk, {
                        "off_scheme": os_["off_label"], "def_scheme": ds_["def_label"],
                        "games": 0, "off_wins": 0, "off_pos_epa": 0, "epas": [], "pts": [],
                    })
                    sm["games"] += 1
                    sm["off_wins"] += int(off_won_game)
                    sm["off_pos_epa"] += int(act["off_epa"] >= 0.0)
                    sm["epas"].append(act["off_epa"])
                    sm["pts"].append(hs if off_t == home else as_)

                    # 4. 'What to Watch For' cue evaluation
                    cue = _evaluate_watch_for_cue(os_, ds_, act, off_won_game)
                    cue_total += 1
                    cue_correct += int(cue["correct"])
                    cs = cue_stats.setdefault(cue["cue_type"], {"cue_type": cue["cue_type"], "total": 0, "correct": 0, "triggered_win": 0, "triggered_n": 0})
                    cs["total"] += 1
                    cs["correct"] += int(cue["correct"])
                    if cue["triggered"]:
                        cs["triggered_n"] += 1
                        cs["triggered_win"] += int(cue["off_succeeded"])

                    sides_graded.append({
                        "off_team": off_t,
                        "def_team": def_t,
                        "off_scheme": os_["off_label"],
                        "def_scheme": ds_["def_label"],
                        "off_held": off_held,
                        "off_actual": off_act_txt,
                        "def_held": def_held,
                        "def_actual": def_act_txt,
                        "pred_edge": pred_edge,
                        "edge_hit": edge_hit,
                        "actual_epa": round(act["off_epa"], 2),
                        "cue": cue,
                    })

            # Stakes outcome summary
            if winner == "TIE":
                stakes_outcome = f"Ended in a {as_}–{hs} tie."
            elif upset:
                stakes_outcome = f"Upset: {winner} won {as_}–{hs} ({spread_result})."
            else:
                stakes_outcome = f"{winner} won {as_}–{hs} ({spread_result})."

            graded_games.append({
                "game_id": g["game_id"],
                "week": wk,
                "gameday": g["gameday"],
                "away_team": away,
                "home_team": home,
                "away_record_pre": ap["record"],
                "home_record_pre": hp["record"],
                "away_score": as_,
                "home_score": hs,
                "winner": winner,
                "margin": margin,
                "total_pts": total_pts,
                "overtime": g["overtime"],
                "spread_label": watch._fmt_spread(sp, home, away),
                "total_line": g["total_line"],
                "interest_score": score,
                "tier": tier,
                "delivered": delivered,
                "one_score": one_score,
                "upset": upset,
                "stakes_pre": stakes_label,
                "stakes_outcome": stakes_outcome,
                "sides": sides_graded,
            })

    # Finalize summary tables
    tier_rows = []
    for t in tier_order:
        s = tier_stats[t]
        n = s["games"]
        tier_rows.append({
            "tier": t,
            "games": n,
            "delivered_pct": round(100.0 * s["delivered"] / n, 1) if n else 0.0,
            "one_score_pct": round(100.0 * s["one_score"] / n, 1) if n else 0.0,
            "upset_pct": round(100.0 * s["upsets"] / n, 1) if n else 0.0,
            "avg_margin": round(float(np.mean(s["margins"])), 1) if n else 0.0,
            "avg_total": round(float(np.mean(s["totals"])), 1) if n else 0.0,
        })

    # Top Must/Strong Watch vs Niche comparison
    top_g = tier_stats["Must Watch"]["games"] + tier_stats["Strong Watch"]["games"]
    top_del = tier_stats["Must Watch"]["delivered"] + tier_stats["Strong Watch"]["delivered"]
    low_g = tier_stats["Niche"]["games"]
    low_del = tier_stats["Niche"]["delivered"]

    matrix_rows = []
    for sm in scheme_matrix.values():
        n = sm["games"]
        if n < 2:
            continue
        matrix_rows.append({
            "off_scheme": sm["off_scheme"],
            "def_scheme": sm["def_scheme"],
            "games": n,
            "off_win_pct": round(100.0 * sm["off_wins"] / n, 1),
            "off_pos_epa_pct": round(100.0 * sm["off_pos_epa"] / n, 1),
            "avg_epa": round(float(np.mean(sm["epas"])), 2),
            "avg_pts": round(float(np.mean(sm["pts"])), 1),
        })
    matrix_rows.sort(key=lambda r: (-r["games"], -abs(r["avg_epa"])))

    cue_rows = []
    for cs in cue_stats.values():
        n = cs["total"]
        cue_rows.append({
            "cue_type": cs["cue_type"],
            "games": n,
            "hit_pct": round(100.0 * cs["correct"] / n, 1) if n else 0.0,
            "when_triggered_pct": round(100.0 * cs["triggered_win"] / cs["triggered_n"], 1) if cs["triggered_n"] else 0.0,
        })
    cue_rows.sort(key=lambda r: (-r["games"], -r["hit_pct"]))

    # Most recent week first, then highest Interest Score first
    graded_games.sort(key=lambda x: (-x["week"], -x["interest_score"], x["game_id"]))

    return {
        "season": season,
        "weeks_evaluated": eval_weeks,
        "games_graded": len(graded_games),
        "updated": now.strftime("%Y-%m-%d %H:%M UTC"),
        "summary": {
            "top_tiers_delivered_pct": round(100.0 * top_del / top_g, 1) if top_g else 0.0,
            "top_tiers_games": top_g,
            "niche_delivered_pct": round(100.0 * low_del / low_g, 1) if low_g else 0.0,
            "scheme_hold_pct": round(100.0 * diag_held / diag_total, 1) if diag_total else 0.0,
            "scheme_checks": diag_total,
            "edge_accuracy_pct": round(100.0 * edge_correct / edge_total, 1) if edge_total else 0.0,
            "edge_calls": edge_total,
            "cue_hit_pct": round(100.0 * cue_correct / cue_total, 1) if cue_total else 0.0,
            "cue_checks": cue_total,
            "fav_win_pct": round(100.0 * fav_won / fav_total, 1) if fav_total else 0.0,
            "fav_cover_pct": round(100.0 * fav_covered / fav_total, 1) if fav_total else 0.0,
            "high_stakes_close_pct": round(100.0 * high_stakes_close / high_stakes_total, 1) if high_stakes_total else 0.0,
            "high_stakes_upset_pct": round(100.0 * high_stakes_upsets / high_stakes_total, 1) if high_stakes_total else 0.0,
        },
        "tiers": tier_rows,
        "scheme_matrix": matrix_rows[:24],
        "cues": cue_rows,
        "games": graded_games,
    }
