"""ddyno: a small host for ML models.

Every folder in models/ that contains meta.json and model.json becomes a model page
at /m/<slug> with sliders built from meta.json. Inference is plain numpy.
To add a model, drop in a folder. No code changes needed for a model whose "type" already has an engine below:
linear_regression, logistic_regression, random_forest_classifier, svm_classifier, logistic_classifier, kmeans.
"""
import csv
import io
import json
import math
import re
import threading
import time
import urllib.request
from datetime import datetime, timezone
from pathlib import Path

import numpy as np
from fastapi import FastAPI, HTTPException
from fastapi.responses import HTMLResponse, Response
from pydantic import BaseModel, Field
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.linear_model import LogisticRegression
from sklearn.pipeline import make_pipeline

import ui

ROOT = Path(__file__).resolve().parent
app = FastAPI(title="ddyno")

# ------------------------------------------------------------------ model registry
REGISTRY = {}
PLOT_SVG = {}
for meta_path in sorted((ROOT / "models").glob("*/meta.json")):
    model_path = meta_path.with_name("model.json")
    if model_path.exists():
        meta = json.loads(meta_path.read_text())
        bundle = meta_path.with_name("plots.json")      # diagnostic plots, SVGs inlined
        if bundle.exists():
            items = json.loads(bundle.read_text())
            for it in items:
                PLOT_SVG[(meta["slug"], it["id"])] = it.pop("svg")
                it["url"] = f"/plots/{meta['slug']}/{it['id']}.svg"
            meta["plots"] = items
        REGISTRY[meta["slug"]] = {"meta": meta, "model": json.loads(model_path.read_text())}

# Pages that are not slider models still show up on the hub through this list.
BUILT_IN = [{"slug": "ncr", "name": "NCR Classifier", "category": "Manufacturing", "url": "/apps/ncr",
             "summary": "Paste a manufacturing non-conformance description and get the likely flaw category."}]

OPS = {
    "absdiff": lambda a, b: abs(a - b),
    "diff": lambda a, b: a - b,
    "sum": lambda *a: sum(a),
    "product": lambda a, b: a * b,
    "pace": lambda h, a, line: h + a - line / 2,     # halftime points minus half the pregame over/under
    "need": lambda line, h, a: line - h - a,          # points still needed to clear the user's total
    "need_vs_pace": lambda line, h, a, t: line - h - a - t / 2,
    "square": lambda v: v * v,
    "fav_lead": lambda h, a, spread: (h - a) * (-1.0 if spread < 0 else 1.0),
}


def fmt(v, decimals=1):
    return f"{v:.{decimals}f}".rstrip("0").rstrip(".") if decimals else f"{v:.0f}"


def tag(feature):
    return {"home": "Home", "away": "Away"}.get(feature.get("side"), "")


def read_inputs(meta, inputs):
    feats = {f["name"]: f for f in meta["features"]}
    x = {}
    for name, f in feats.items():
        if name not in inputs:
            raise HTTPException(422, f"Missing input: {name}")
        v = float(inputs[name])
        if not math.isfinite(v) or v < f.get("hard_min", f["min"]) or v > f.get("hard_max", f["max"]):
            raise HTTPException(422, f"{f['label']} is outside the allowed range.")
        x[name] = v
    derived = {d["name"]: d for d in meta.get("derived", [])}
    derive(derived, x)
    return feats, derived, x


def derive(derived, x):
    for name, d in derived.items():
        x[name] = float(OPS[d["op"]](*[x[a] for a in d["args"]]))
    return x


def unusual_inputs(feats, model, x):
    warnings = []
    for n, f in feats.items():
        p = model["percentiles"].get(n)
        if p and not f.get("choices") and (x[n] < p["1"] or x[n] > p["99"]):
            side = f"{tag(f)} " if tag(f) else ""
            where = "higher" if x[n] > p["99"] else "lower"
            warnings.append(f"{side}{f['label'].lower()}".capitalize() + f" of {fmt(x[n])} is {where} than 99% of past games "
                            f"(usual range {fmt(p['1'])} to {fmt(p['99'])}). The model has seen very little like it.")
    return warnings


def predict_linear(entry, inputs, line=None, params=None):
    meta, model = entry["meta"], entry["model"]
    feats, derived, x = read_inputs(meta, inputs)

    order = model["feature_order"]                       # "const" first
    vec = np.array([1.0] + [x[n] for n in order[1:]])
    coefs = np.array([model["intercept"]] + [model["coefficients"][n] for n in order[1:]])
    pred = float(vec @ coefs)
    s = model["residual_std_error"]
    sd = math.sqrt(s * s + float(vec @ np.array(model["covariance"]) @ vec))

    floor = None
    if meta.get("floor"):
        floor = float(OPS[meta["floor"]["op"]](*[x[a] for a in meta["floor"]["args"]]))
    clip = (lambda v: max(v, floor)) if floor is not None else (lambda v: v)
    intervals = {lvl: {"low": clip(pred - t * sd), "high": pred + t * sd} for lvl, t in model["t_crit"].items()}
    pred_shown = clip(pred)

    # How far each input moves this prediction away from an average game.
    drivers = []
    for n in order[1:]:
        f = feats.get(n) or derived[n]
        side = tag(f)
        drivers.append({"name": n, "label": f["label"], "side": side, "value": x[n],
                        "typical": model["feature_means"][n], "unit": f.get("unit", ""),
                        "effect": model["coefficients"][n] * (x[n] - model["feature_means"][n]),
                        "computed": n in derived})
    drivers.sort(key=lambda d: -abs(d["effect"]))
    warnings = unusual_inputs(feats, model, x)

    unit = meta["target"].get("unit", "")
    lo, hi = intervals["80"]["low"], intervals["80"]["high"]
    parts = [f"The model expects about {fmt(pred_shown)} {meta['target']['label'].lower()}, "
             f"most likely landing between {fmt(lo, 0)} and {fmt(hi, 0)}."]
    if floor is not None and meta.get("synopsis_extra"):
        parts.append(meta["synopsis_extra"].format(floor=fmt(floor), remaining=fmt(pred_shown - floor), pred=fmt(pred_shown)))
    name = lambda d: f"{(d['side'] + ' ').lower() if d['side'] else ''}{d['label'].lower()}"
    ups = [d for d in drivers if d["effect"] > 0.5]
    downs = [d for d in drivers if d["effect"] < -0.5]
    avg = fmt(model["target_mean"])
    say = lambda d: f"{name(d)} ({fmt(d['value'])}, worth {'+' if d['effect'] > 0 else ''}{fmt(d['effect'])})"
    if ups and downs:
        parts.append(f"Against an average game ({avg} {unit}), the biggest push up comes from {say(ups[0])}, "
                     f"and the biggest drag is {say(downs[0])}.")
    elif ups or downs:
        group, word = (ups, "pushes up come from") if ups else (downs, "drags are")
        if len(group) > 1:
            parts.append(f"Against an average game ({avg} {unit}), the biggest {word} {say(group[0])} and {say(group[1])}.")
        else:
            parts.append(f"Against an average game ({avg} {unit}), the main driver is {say(group[0])}.")
    else:
        parts.append(f"These inputs look like an average game ({avg} {unit}), so nothing stands out.")

    compare = None
    if line is not None and math.isfinite(line):
        p_over = 0.5 * (1 - math.erf((line - pred) / (sd * math.sqrt(2))))
        if floor is not None and line < floor:
            p_over = 1.0
        gap = pred_shown - line
        lean = "over" if gap > 0 else "under"
        compare = {"line": line, "p_over": p_over, "gap": gap, "lean": lean}
        if abs(gap) < 1.5:
            parts.append(f"That is almost exactly on the {fmt(line)} line, so the model has no real lean.")
        else:
            parts.append(f"That is {fmt(abs(gap))} points {lean} the {fmt(line)} line, which puts the chance of going over "
                         f"at about {round(100 * p_over)}%."
                         + (" A gap this size is smaller than the model's typical miss." if abs(gap) < 0.8 * sd else ""))

    return {"kind": "number", "prediction": pred_shown, "sd": sd, "intervals": intervals, "floor": floor,
            "baseline": model["target_mean"], "drivers": drivers, "warnings": warnings,
            "synopsis": " ".join(parts), "compare": compare}


def predict_logistic(entry, inputs, line=None, params=None):
    meta, model = entry["meta"], entry["model"]
    feats, derived, x = read_inputs(meta, inputs)
    sig = lambda z: 1 / (1 + math.exp(-z))
    order = model["feature_order"]
    vec = np.array([1.0] + [x[n] for n in order[1:]])
    coefs = np.array([model["intercept"]] + [model["coefficients"][n] for n in order[1:]])
    z = float(vec @ coefs)
    se = math.sqrt(float(vec @ np.array(model["covariance"]) @ vec))
    p = sig(z)
    intervals = {lvl: {"low": sig(z - c * se), "high": sig(z + c * se)} for lvl, c in model["z_crit"].items()}

    # Baseline is an average game; each driver shows what that one input does on its own.
    z0 = model["intercept"] + sum(model["coefficients"][n] * model["feature_means"][n] for n in order[1:])
    base = sig(z0)
    drivers = []
    for n in order[1:]:
        f = feats.get(n) or derived[n]
        shift = model["coefficients"][n] * (x[n] - model["feature_means"][n])
        choices = f.get("choices")
        drivers.append({"name": n, "label": f["label"], "side": tag(f), "value": x[n], "unit": f.get("unit", ""),
                        "value_label": choices.get(str(int(x[n]))) if choices else None,
                        "typical": None if choices else model["feature_means"][n],
                        "effect": 100 * (sig(z0 + shift) - base), "computed": n in derived})
    drivers.sort(key=lambda d: -abs(d["effect"]))
    warnings = unusual_inputs(feats, model, x)

    pos, neg = meta["target"]["positive"], meta["target"]["negative"]
    fav, fav_p = (pos, p) if p >= 0.5 else (neg, 1 - p)
    strength = ("a toss-up that leans to" if fav_p < 0.6 else "a modest edge for" if fav_p < 0.75
                else "a strong edge for" if fav_p < 0.9 else "close to locked up for")
    parts = [f"The model gives the {pos.lower()} team about a {round(100 * p)}% chance to win and the {neg.lower()} team "
             f"{100 - round(100 * p)}%. That is {strength} the {fav.lower()} side."]
    name = lambda d: f"{(d['side'] + ' ').lower() if d['side'] else ''}{d['label'].lower()}"
    val = lambda d: d["value_label"] or fmt(d["value"])
    big = [d for d in drivers if abs(d["effect"]) >= 2]
    if big:
        d = big[0]
        txt = (f"Compared with an average game ({round(100 * base)}% {pos.lower()}), the biggest factor is {name(d)} "
               f"({val(d)}), which on its own moves the {pos.lower()} team's chance by {d['effect']:+.0f} points")
        if len(big) > 1:
            txt += f", followed by {name(big[1])} ({val(big[1])}, {big[1]['effect']:+.0f})"
        parts.append(txt + ".")
    else:
        parts.append(f"These inputs look like an average game ({round(100 * base)}% {pos.lower()}), so nothing stands out.")
    conf = meta["card"].get("confident")
    if conf and fav_p >= 0.8:
        parts.append(f"In testing, picks this confident were right about {round(100 * conf['accuracy'])}% of the time.")
    elif conf and fav_p < 0.6:
        parts.append(f"In testing, picks this close were right only about {round(100 * conf['tossup_accuracy'])}% of the time, so treat it as a coin flip.")
    return {"kind": "probability", "probability": p, "intervals": intervals, "baseline": base,
            "labels": {"positive": pos, "negative": neg}, "drivers": drivers, "warnings": warnings,
            "synopsis": " ".join(parts), "compare": None}


# ------------------------------------------------ over/under classifiers (forest, SVM)
def forest_chance(model, x, n_trees=None):
    """Average leaf over-rate across the first n trees, plus how many of those trees lean over."""
    row = [x[n] for n in model["feature_order"]]
    trees = model["trees"][:n_trees] if n_trees else model["trees"]
    votes = []
    for t in trees:
        f, thr, left, right, i = t["f"], t["t"], t["l"], t["r"], 0
        while f[i] >= 0:
            i = left[i] if row[f[i]] <= thr[i] else right[i]
        votes.append(t["v"][i])
    return float(np.mean(votes)), sum(v >= 0.5 for v in votes), len(votes)


def svm_distance(entry, x):
    """Signed distance-like score from the SVM boundary. Positive is the over side."""
    model = entry["model"]
    if "np" not in entry:
        entry["np"] = {k: np.array(model[k], dtype=float) for k in ("mean", "scale", "support_vectors", "dual_coef")}
    a = entry["np"]
    z = (np.array([x[n] for n in model["feature_order"]]) - a["mean"]) / a["scale"]
    if model["kernel"] == "rbf":
        k = np.exp(-model["gamma"] * ((a["support_vectors"] - z) ** 2).sum(axis=1))
    else:
        k = a["support_vectors"] @ z
    return float(a["dual_coef"] @ k + model["intercept"])


def logit_chance(entry, x):
    model = entry["model"]
    if "np" not in entry:
        entry["np"] = {k: np.array(model[k], dtype=float) for k in ("mean", "scale", "coef")}
    a = entry["np"]
    z = (np.array([x[n] for n in model["feature_order"]]) - a["mean"]) / a["scale"]
    return 1 / (1 + math.exp(-(float(a["coef"] @ z) + model["intercept"])))


def predict_classifier(entry, inputs, line=None, params=None):
    """Chance the game finishes over the total the user entered (the 'line' input)."""
    meta, model = entry["meta"], entry["model"]
    feats, derived, x = read_inputs(meta, inputs)
    params = params or {}
    kind = meta["type"]
    if kind == "random_forest_classifier":
        total = len(model["trees"])
        n_use = params.get("n_trees", total)
        if not math.isfinite(n_use) or n_use < 1 or n_use > total:
            raise HTTPException(422, f"Trees that vote must be between 1 and {total}.")
        n_use = int(n_use)
        raw_chance = lambda v: forest_chance(model, v, n_use)[0]
    elif kind == "svm_classifier":
        pl = model["platt"]
        raw_chance = lambda v: 1 / (1 + math.exp(-(pl["a"] * svm_distance(entry, v) + pl["b"])))
    else:
        raw_chance = lambda v: logit_chance(entry, v)

    board = x["home_h1_pts"] + x["away_h1_pts"]
    target = x["line"]
    with_inputs = lambda **change: derive(derived, {**{k: x[k] for k in feats}, **change})
    # A total at or below the halftime score is already beaten, whatever the model says.
    chance = lambda v: 1.0 if v["line"] < v["home_h1_pts"] + v["away_h1_pts"] else raw_chance(v)
    p = chance(x)

    # Break-even total: the number where the model is 50/50. Bisection, since the chance falls as the total rises.
    lo, hi = board + 0.5, board + 80.0
    for _ in range(9):
        mid = (lo + hi) / 2
        if chance(with_inputs(line=mid)) >= 0.5:
            lo = mid
        else:
            hi = mid
    fair = round((lo + hi) / 2 * 2) / 2

    # Each driver: put that one halftime input back to typical, keep your total, and see how far the chance moves.
    base = chance(derive(derived, {n: model["typical"][n] for n in feats}))
    drivers = []
    for n, f in feats.items():
        if n == "line":
            continue
        drivers.append({"name": n, "label": f["label"], "side": tag(f), "value": x[n], "unit": f.get("unit", ""),
                        "value_label": None, "typical": model["typical"][n],
                        "effect": 100 * (p - chance(with_inputs(**{n: model["typical"][n]}))), "computed": False})
    drivers.sort(key=lambda d: -abs(d["effect"]))
    warnings = unusual_inputs(feats, model, x)

    pos, neg = meta["target"]["positive"], meta["target"]["negative"]
    fav, fav_p = (pos, p) if p >= 0.5 else (neg, 1 - p)
    need = target - board
    if need < 0:
        parts = [f"There are already {fmt(board)} points on the board, which is more than your total of {fmt(target)}. The over has already hit."]
    else:
        strength = (f"a toss-up that leans to the {fav.lower()}" if fav_p < 0.6 else f"a modest lean to the {fav.lower()}" if fav_p < 0.75
                    else f"a strong lean to the {fav.lower()}" if fav_p < 0.9 else f"close to settled for the {fav.lower()}")
        parts = [f"The model gives about a {round(100 * p)}% chance this game finishes over {fmt(target)} and {100 - round(100 * p)}% that it stays under. "
                 f"That is {strength}.",
                 f"With {fmt(board)} points on the board, the second half needs at least {math.floor(need) + 1} more. "
                 f"The model's break-even total for this game is about {fmt(fair)}: it leans over on anything lower and under on anything higher."]
        name = lambda d: f"{(d['side'] + ' ').lower() if d['side'] else ''}{d['label'].lower()}"
        big = [d for d in drivers if abs(d["effect"]) >= 2]
        if big:
            d = big[0]
            txt = (f"The input doing the most is {name(d)} ({fmt(d['value'])}): with a typical value there instead "
                   f"({fmt(d['typical'])}) and the same total, the over chance would be {abs(d['effect']):.0f} points {'lower' if d['effect'] > 0 else 'higher'}")
            if len(big) > 1:
                txt += f". Next is {name(big[1])} ({fmt(big[1]['value'])}, {big[1]['effect']:+.0f})"
            parts.append(txt + ".")
        conf = meta["card"].get("confident")
        if conf and fav_p >= 0.8 and conf.get("accuracy") is not None:
            parts.append(f"In testing, calls this confident were right about {round(100 * conf['accuracy'])}% of the time.")
        elif conf and fav_p < 0.6 and conf.get("tossup_accuracy") is not None:
            parts.append(f"In testing, calls this close were right only about {round(100 * conf['tossup_accuracy'])}% of the time, so treat it as a coin flip.")

    if need < 0:
        detail = "Your total is below the halftime score."
    elif kind == "random_forest_classifier":
        _, lean, used = forest_chance(model, x, n_use)
        detail = (f"{lean} of the {used} trees lean over." if used > 1 else "Only one tree is voting, so the answer is whatever its leaf says.")
        if used < len(model["trees"]):
            detail += f" The tuned model uses all {len(model['trees'])}; with fewer trees the answer gets jumpier."
    elif kind == "svm_classifier":
        detail = (f"SVM score {svm_distance(entry, x):+.2f}. Zero is the boundary between over and under, positive is the over side, "
                  f"and scores past about 1 in either direction are well clear of it.")
    else:
        detail = None
    return {"kind": "probability", "probability": p, "intervals": None, "baseline": base,
            "labels": {"positive": pos, "negative": neg}, "drivers": drivers, "warnings": warnings,
            "synopsis": " ".join(parts), "compare": None, "detail": detail,
            "headline": f"Chance the game finishes over {fmt(target)}", "fair_line": fair, "line": target, "need": need}


# ------------------------------------------------------------- k-means game types
def predict_kmeans(entry, inputs, line=None, params=None):
    meta, model = entry["meta"], entry["model"]
    feats, derived, x = read_inputs(meta, inputs)
    k = (params or {}).get("k", model["default_k"])
    if not math.isfinite(k) or str(int(k)) not in model["solutions"]:
        raise HTTPException(422, "That number of game types is not available.")
    sol = model["solutions"][str(int(k))]
    order = model["feature_order"]
    z = (np.array([x[n] for n in order]) - np.array(model["mean"])) / np.array(model["scale"])
    dist = [float(np.sqrt(((np.array(c["centroid_z"]) - z) ** 2).sum())) for c in sol["clusters"]]
    rank = sorted(range(len(dist)), key=lambda i: dist[i])
    best, second = sol["clusters"][rank[0]], sol["clusters"][rank[1]]
    brief = lambda c, d: {"id": c["id"], "name": c["name"], "share": c["share"], "distance": d,
                          "centroid": c["centroid"], "profile": c["profile"]}
    clusters = [brief(sol["clusters"][i], dist[i]) for i in rank]
    border = dist[rank[1]] < 1.25 * dist[rank[0]] + 0.15
    fit = ("far from the centre of any type" if dist[rank[0]] > sol["distance_p95"]
           else "near the middle of that type" if dist[rank[0]] <= sol["distance_p50"] else "a fair way from its centre")

    # How far each input sits from an average halftime, in standard deviations.
    drivers = [{"name": n, "label": feats[n]["label"], "side": tag(feats[n]), "value": x[n], "unit": feats[n].get("unit", ""),
                "value_label": None, "typical": model["mean"][i], "effect": float(z[i]), "computed": False}
               for i, n in enumerate(order)]
    drivers.sort(key=lambda d: -abs(d["effect"]))
    warnings = unusual_inputs(feats, model, x)

    pr, allg = best["profile"], model["overall"]
    parts = [f"This halftime looks most like a '{best['name']}' game, a type that covers about {round(100 * best['share'])}% of past games. "
             f"Your inputs are {fit}."]
    if border:
        parts.append(f"It is a border case: '{second['name']}' is almost as close, so read both rows.")
    parts.append(f"Games of this type finished with {fmt(pr['final_total'])} combined points on average (all games: {fmt(allg['final_total'])}), "
                 f"the home team won {round(100 * pr['home_win'])}% of them, and {round(100 * pr['over'])}% went over their pregame total.")
    parts.append("The model was never shown how games ended. It only grouped halftime box scores that look alike, and the results were looked up afterwards.")
    return {"kind": "cluster", "k": int(k), "cluster": clusters[0], "clusters": clusters, "border": border, "overall": allg,
            "drivers": drivers, "warnings": warnings, "synopsis": " ".join(parts), "compare": None}


ENGINES = {"linear_regression": predict_linear, "logistic_regression": predict_logistic,
           "random_forest_classifier": predict_classifier, "svm_classifier": predict_classifier,
           "logistic_classifier": predict_classifier, "kmeans": predict_kmeans}


class PredictIn(BaseModel):
    inputs: dict[str, float]
    line: float | None = None
    params: dict[str, float] | None = None      # optional model settings, e.g. {"n_trees": 50} or {"k": 5}


@app.get("/api/health")
def health():
    return {"ok": True, "models": len(REGISTRY)}


@app.get("/api/models")
def list_models():
    out = [{"slug": s, "name": e["meta"]["name"], "category": e["meta"]["category"],
            "summary": e["meta"]["summary"], "url": f"/m/{s}"} for s, e in REGISTRY.items()]
    return {"models": out + BUILT_IN}


@app.get("/plots/{slug}/{name}")
def plot_file(slug: str, name: str):
    svg = PLOT_SVG.get((slug, name[:-4])) if name.endswith(".svg") else None
    if svg is None:
        raise HTTPException(404, "Plot not found")
    return Response(svg, media_type="image/svg+xml", headers={"Cache-Control": "public, max-age=3600"})


@app.get("/api/models/{slug}")
def model_meta(slug: str):
    if slug not in REGISTRY:
        raise HTTPException(404, "Unknown model")
    return REGISTRY[slug]["meta"]


@app.post("/api/models/{slug}/predict")
def model_predict(slug: str, body: PredictIn):
    if slug not in REGISTRY:
        raise HTTPException(404, "Unknown model")
    entry = REGISTRY[slug]
    return ENGINES[entry["meta"]["type"]](entry, body.inputs, body.line, body.params)


# ------------------------------------------------------------- league leaders (sideline figures)
# Who currently leads the league in a handful of stats. The pages draw one generic position figure per leader.
# Data: nflverse public files (player season stats, ESPN Total QBR, schedule with head coaches).
# Refreshed in the background every few hours; a snapshot shipped in models/ is used until the first refresh lands.
NFLVERSE = "https://github.com/nflverse/nflverse-data/releases/download/"
LEADER_REFRESH_SECONDS = 6 * 3600
AFC = {"BAL", "BUF", "CIN", "CLE", "DEN", "HOU", "IND", "JAX", "KC", "LV", "LAC", "MIA", "NE", "NYJ", "PIT", "TEN"}
# Where each group shows up. Any group whose page is missing falls back to the hub, so all 21 figures are always somewhere.
LEADER_PAGES = {"coach_afc": "hub", "coach_nfc": "hub", "qbr": "nfl-halftime-total", "pass_td": "nfl-halftime-total",
                "ypc": "nfl-halftime-win", "rec_yds": "nfl-halftime-ou-logit", "rec_td": "nfl-halftime-ou-forest",
                "sacks": "nfl-halftime-ou-svm", "tackles": "nfl-halftime-game-types"}
LEADERS = {"data": None, "live": False}


def _rows(url):
    req = urllib.request.Request(url, headers={"User-Agent": "ddyno"})
    with urllib.request.urlopen(req, timeout=45) as r:
        yield from csv.DictReader(io.TextIOWrapper(r, encoding="utf-8", newline=""))


def _num(v):
    try:
        return float(v)
    except (TypeError, ValueError):
        return 0.0


def build_leaders(now=None):
    now = now or datetime.now(timezone.utc)
    season = now.year if now.month >= 9 else now.year - 1

    # Schedule: games played per team (for the yards-per-carry qualifier), latest finished week, coach records.
    played, coaches, week = {}, {}, 0
    for g in _rows(NFLVERSE + "schedules/games.csv"):
        if g["season"] != str(season) or g["game_type"] != "REG" or g["result"] in ("", "NA"):
            continue
        week = max(week, int(_num(g["week"])))
        margin = _num(g["result"])                       # home score minus away score
        for side, sign in (("home", 1), ("away", -1)):
            team = g[f"{side}_team"]
            played[team] = played.get(team, 0) + 1
            c = coaches.setdefault(g[f"{side}_coach"], {"name": g[f"{side}_coach"], "team": team, "w": 0, "l": 0, "t": 0, "diff": 0})
            c["team"] = team
            c["w" if sign * margin > 0 else "l" if sign * margin < 0 else "t"] += 1
            c["diff"] += sign * margin
    if not played:
        raise RuntimeError("no finished games for the season yet")

    num_by_id, num_by_name = {}, {}
    try:
        for r in _rows(NFLVERSE + f"rosters/roster_{season}.csv"):
            raw = (r.get("jersey_number") or "").strip()
            if not raw or raw == "NA":
                continue
            num = raw.split(".", 1)[0]
            if not num.isdigit():
                continue
            gid = (r.get("gsis_id") or "").strip()
            if gid:
                num_by_id[gid] = num
            nm = (r.get("full_name") or "").strip().lower()
            tm = (r.get("team") or "").strip()
            if nm:
                num_by_name[(nm, tm)] = num
                num_by_name.setdefault((nm, ""), num)
    except Exception:
        pass

    def jersey_for(name, team, gid=""):
        key = name.strip().lower()
        return num_by_id.get(gid) or num_by_name.get((key, team)) or num_by_name.get((key, "")) or ""

    players = []
    for p in _rows(NFLVERSE + f"stats_player/stats_player_reg_{season}.csv"):
        nm, tm = p["player_display_name"], p["recent_team"]
        players.append({"name": nm, "pos": p["position"], "team": tm,
                        "number": jersey_for(nm, tm, (p.get("player_id") or "").strip()),
                        "carries": _num(p["carries"]), "rush_yds": _num(p["rushing_yards"]), "pass_td": _num(p["passing_tds"]),
                        "pass_yds": _num(p["passing_yards"]), "rec_td": _num(p["receiving_tds"]), "rec_yds": _num(p["receiving_yards"]),
                        "sacks": _num(p["def_sacks"]), "tackles": _num(p["def_tackles_solo"]) + _num(p["def_tackle_assists"]),
                        "solo": _num(p["def_tackles_solo"])})

    qbr = [{"name": q["name_display"], "team": q["team_abb"],
            "number": jersey_for(q["name_display"], q["team_abb"]),
            "qbr": _num(q["qbr_total"]), "plays": _num(q["qb_plays"])}
           for q in _rows(NFLVERSE + "espn_data/qbr_season_level.csv")
           if q["season"] == str(season) and q["season_type"] == "Regular" and q["qualified"].upper() == "TRUE"]

    whole = lambda v: f"{v:.0f}"
    def top(pool, key, n, show, tie=None, detail=None):
        ranked = sorted(pool, key=lambda p: (-key(p), -(tie(p) if tie else 0), p["name"]))[:n]
        return [{"name": p["name"], "team": p["team"], "number": p.get("number", ""),
                 "value": show(key(p)), "detail": detail(p) if detail else ""} for p in ranked]

    # NFL qualifier for rushing average: 6.25 carries per game the player's team has played.
    backs = [p for p in players if p["pos"] == "RB" and p["carries"] >= 6.25 * played.get(p["team"], 99)]
    passers = [p for p in players if p["pos"] == "QB"]
    wideouts = [p for p in players if p["pos"] == "WR"]
    def coach_group(conf):
        pool = [c for c in coaches.values() if (c["team"] in AFC) == (conf == "AFC")]
        ranked = sorted(pool, key=lambda c: (-c["w"], c["l"], -c["diff"], c["name"]))[:2]
        return [{"name": c["name"], "team": c["team"], "value": f"{c['w']}-{c['l']}" + (f"-{c['t']}" if c["t"] else ""),
                 "detail": f"{c['diff']:+.0f} point margin"} for c in ranked]

    groups = [
        {"id": "ypc", "role": "rb", "title": "Yards per carry", "unit": "per carry", "note": "Running backs with at least 6.25 carries per team game.",
         "players": top(backs, lambda p: p["rush_yds"] / p["carries"], 3, lambda v: f"{v:.2f}", detail=lambda p: f"{whole(p['rush_yds'])} yds on {whole(p['carries'])} carries")},
        {"id": "qbr", "role": "qb", "title": "Total QBR", "unit": "QBR", "note": "ESPN Total QBR, qualified passers.",
         "players": top(qbr, lambda p: p["qbr"], 2, lambda v: f"{v:.1f}", detail=lambda p: f"{whole(p['plays'])} plays")},
        {"id": "pass_td", "role": "qb", "title": "Passing touchdowns", "unit": "pass TD", "note": "",
         "players": top(passers, lambda p: p["pass_td"], 2, whole, tie=lambda p: p["pass_yds"], detail=lambda p: f"{whole(p['pass_yds'])} pass yds")},
        {"id": "rec_td", "role": "wr", "title": "Receiving touchdowns", "unit": "rec TD", "note": "Wide receivers.",
         "players": top(wideouts, lambda p: p["rec_td"], 3, whole, tie=lambda p: p["rec_yds"], detail=lambda p: f"{whole(p['rec_yds'])} rec yds")},
        {"id": "rec_yds", "role": "wr", "title": "Receiving yards", "unit": "rec yds", "note": "Wide receivers.",
         "players": top(wideouts, lambda p: p["rec_yds"], 3, whole, detail=lambda p: f"{whole(p['rec_td'])} TD")},
        {"id": "sacks", "role": "rush", "title": "Sacks", "unit": "sacks", "note": "",
         "players": top(players, lambda p: p["sacks"], 2, lambda v: f"{v:g}", tie=lambda p: p["tackles"], detail=lambda p: p["pos"])},
        {"id": "tackles", "role": "tackle", "title": "Tackles", "unit": "tackles", "note": "Solo plus assisted.",
         "players": top(players, lambda p: p["tackles"], 2, whole, tie=lambda p: p["solo"], detail=lambda p: f"{whole(p['solo'])} solo")},
        {"id": "coach_afc", "role": "coach", "title": "Most wins, AFC coaches", "unit": "record", "note": "This season.", "players": coach_group("AFC")},
        {"id": "coach_nfc", "role": "coach", "title": "Most wins, NFC coaches", "unit": "record", "note": "This season.", "players": coach_group("NFC")},
    ]
    if any(not g["players"] for g in groups):
        raise RuntimeError("a leader group came back empty")
    return {"season": season, "through_week": week, "updated": now.strftime("%Y-%m-%d %H:%M UTC"), "groups": groups}


def _refresh_leaders_forever():
    while True:
        try:
            LEADERS["data"], LEADERS["live"] = build_leaders(), True
        except Exception as e:                           # keep whatever we had; try again next cycle
            print("leaders refresh failed:", repr(e))
        time.sleep(LEADER_REFRESH_SECONDS if LEADERS["live"] else 600)


_snap = ROOT / "models" / "leaders_snapshot.json"
if _snap.exists():
    LEADERS["data"] = json.loads(_snap.read_text())
threading.Thread(target=_refresh_leaders_forever, daemon=True).start()


@app.get("/api/leaders")
def leaders(page: str = "hub"):
    """Leader groups to draw on one page ('hub' or a model slug). Every group is assigned to exactly one page."""
    data = LEADERS["data"]
    if not data:
        return {"groups": [], "live": False}
    home = lambda g: LEADER_PAGES.get(g["id"]) if LEADER_PAGES.get(g["id"]) in REGISTRY else "hub"
    return {"season": data["season"], "through_week": data["through_week"], "updated": data["updated"], "live": LEADERS["live"],
            "groups": [g for g in data["groups"] if home(g) == page]}


# ------------------------------------------------------------------------- pages
@app.get("/", response_class=HTMLResponse)
def hub():
    return ui.HUB


@app.get("/m/{slug}", response_class=HTMLResponse)
def model_page(slug: str):
    if not re.fullmatch(r"[a-z0-9-]+", slug) or slug not in REGISTRY:
        raise HTTPException(404, "Unknown model")
    return ui.MODEL.replace("__SLUG__", slug).replace("__NAME__", REGISTRY[slug]["meta"]["name"])


# ---------------------------------------------- demo: NCR text classifier (unchanged)
NCR_DATA = {
    "Dimensional": ["bore diameter out of tolerance on finished part", "length exceeds drawing spec by 0.02 inches",
                    "flange thickness below minimum dimension", "hole position off from datum by 0.015",
                    "outer diameter oversize after final grind", "wall thickness under tolerance at section B"],
    "Surface Finish": ["scratches visible on sealing surface", "surface roughness exceeds Ra requirement",
                       "machining chatter marks on housing face", "pitting and corrosion spots on exterior",
                       "burrs left on edge after deburr operation", "tool marks on bearing journal"],
    "Material": ["hardness test below specified range", "wrong alloy certificate received from supplier",
                 "inclusions found in forging cross section", "material lot missing traceability documentation",
                 "porosity detected in casting during x-ray", "tensile strength failed supplier cert check"],
    "Assembly": ["fastener torque not within specification", "missing washer during final assembly",
                 "o-ring installed twisted in groove", "wrong part number installed at station 4",
                 "connector not fully seated on harness", "gasket misaligned causing leak at joint"],
    "Documentation": ["operator signature missing on traveler", "inspection record incomplete for lot",
                      "revision level mismatch between drawing and work order", "calibration sticker expired on gauge used",
                      "cert of conformance not attached to shipment", "incorrect serial number recorded in log"],
}
NCR_MODEL = make_pipeline(TfidfVectorizer(ngram_range=(1, 2), sublinear_tf=True), LogisticRegression(max_iter=1000, C=10))
NCR_MODEL.fit([t for ts in NCR_DATA.values() for t in ts], [k for k, ts in NCR_DATA.items() for _ in ts])


class ClassifyIn(BaseModel):
    text: str = Field(min_length=3, max_length=2000)


@app.post("/api/classify")
def api_classify(body: ClassifyIn):
    probs = NCR_MODEL.predict_proba([body.text])[0]
    ranked = sorted(zip(NCR_MODEL.classes_, probs), key=lambda p: -p[1])[:3]
    return {"predictions": [{"label": l, "score": round(float(s), 4)} for l, s in ranked]}


@app.get("/apps/ncr", response_class=HTMLResponse)
def ncr_page():
    return ui.NCR
