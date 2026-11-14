"""ddyno: a small host for ML models.

Every folder in models/ that contains meta.json and model.json becomes a model page
at /m/<slug> with sliders built from meta.json. Inference is plain numpy.
To add a model, drop in a folder. No code changes needed for linear models.
"""
import json
import math
import re
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
    for name, d in derived.items():
        x[name] = float(OPS[d["op"]](*[x[a] for a in d["args"]]))
    return feats, derived, x


def unusual_inputs(feats, model, x):
    warnings = []
    for n, f in feats.items():
        p = model["percentiles"][n]
        if not f.get("choices") and (x[n] < p["1"] or x[n] > p["99"]):
            side = f"{tag(f)} " if tag(f) else ""
            where = "higher" if x[n] > p["99"] else "lower"
            warnings.append(f"{side}{f['label'].lower()}".capitalize() + f" of {fmt(x[n])} is {where} than 99% of past games "
                            f"(usual range {fmt(p['1'])} to {fmt(p['99'])}). The model has seen very little like it.")
    return warnings


def predict_linear(entry, inputs, line=None):
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


def predict_logistic(entry, inputs, line=None):
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


ENGINES = {"linear_regression": predict_linear, "logistic_regression": predict_logistic}


class PredictIn(BaseModel):
    inputs: dict[str, float]
    line: float | None = None


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
    return ENGINES[entry["meta"]["type"]](entry, body.inputs, body.line)


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
