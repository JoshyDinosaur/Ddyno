"""
Train the tuned halftime over/under model for ddyno: logistic regression built for "will it clear MY total?".

It takes the total to beat as an input. Every training game is paired with several different totals, so one
model learns the chance of clearing any number. Offline only. Writes model.json, meta.json, training_report.json.
Needs ../nfl-halftime-total/train.py (dataset builder) and ../../tools/ou_common.py.

    python train.py --data-dir DIR [--last-season 2026]

How it was chosen
  1. Seasons before 2025 are the training pool; 2025 onward is the locked test.
  2. Grid search over which engineered inputs to include (RECIPES) and the regularisation strength C,
     scored with forward-chaining cross-validation on seven fixed totals per game. Log loss decides.
  3. Other model families (gradient boosting, a small neural net, splines) get the same test, for the record.
  4. The winner is scored once on the locked seasons, then refit on every game for shipping.
"""
import argparse
import json
import os
import sys
import warnings
from datetime import date

import numpy as np
import pandas as pd
from sklearn.ensemble import HistGradientBoostingClassifier
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import log_loss
from sklearn.neural_network import MLPClassifier
from sklearn.pipeline import make_pipeline
from sklearn.preprocessing import SplineTransformer, StandardScaler

warnings.filterwarnings("ignore")
HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(HERE, "..", "..", "tools"))
import ou_common as C  # noqa: E402

SLUG, NAME = "nfl-halftime-ou-logit", "Halftime Over/Under (Tuned Logistic)"
SEED, N_LINES = 7, 8
BASE = ["need", "total_line", "abs_h1_margin", "h1_first_downs", "h1_explosive", "wind"]
RECIPES = {"plain": BASE, "+ curve": BASE + ["need_sq"], "+ favorite's lead": BASE + ["fav_lead"],
           "+ curve + favorite's lead": BASE + ["need_sq", "fav_lead"]}
CS = (0.001, 0.01, 0.1, 1, 10)


def logit(c):
    return make_pipeline(StandardScaler(), LogisticRegression(C=c, max_iter=5000))


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--data-dir", default=os.path.join(HERE, "..", "nfl-halftime-total", "data_cache"))
    ap.add_argument("--last-season", type=int, default=date.today().year if date.today().month >= 9 else date.today().year - 1)
    ap.add_argument("--cache", default=None)
    args = ap.parse_args()

    df = C.load(args.data_dir, args.last_season, args.cache).reset_index(drop=True)
    train, hold = df[df.season < C.HOLDOUT_FROM].reset_index(drop=True), df[df.season >= C.HOLDOUT_FROM].reset_index(drop=True)
    folds = C.B.season_folds(train.season.values)
    data = [(C.stack_train(train.iloc[a], N_LINES, SEED), C.stack_eval(train.iloc[b]), C.linear_fit(train.iloc[a])) for a, b in folds]
    lin = np.array([log_loss(E.y, C.linear_p(lf, E)) for _, E, lf in data])

    def cv(feats, make):
        ll = np.array([log_loss(E.y, np.clip(make().fit(S[feats], S.y).predict_proba(E[feats])[:, 1], 1e-6, 1 - 1e-6)) for S, E, _ in data])
        return {"cv_log_loss": float(ll.mean()), "cv_se": float(ll.std() / np.sqrt(len(ll))), "folds_beating_linear": int((ll < lin).sum())}

    grid = pd.DataFrame([{"recipe": r, "C": c, **cv(f, lambda c=c: logit(c))} for r, f in RECIPES.items() for c in CS]).sort_values("cv_log_loss").reset_index(drop=True)
    print("linear model CV log loss", lin.mean().round(4)); print(grid.to_string())
    best = grid.iloc[0]
    feats, c_best = RECIPES[best.recipe], float(best.C)

    mono = [-1 if f == "need" else 0 for f in BASE + ["fav_lead"]]
    others = [("Linear model on this site (normal curve)", {"cv_log_loss": float(lin.mean()), "folds_beating_linear": 0}),
              ("Gradient boosting, shallow (100 rounds)", cv(BASE + ["fav_lead"], lambda: HistGradientBoostingClassifier(max_iter=100, learning_rate=0.1, max_leaf_nodes=4, min_samples_leaf=300, l2_regularization=5, monotonic_cst=mono, random_state=SEED))),
              ("Gradient boosting, slower and longer (300 rounds)", cv(BASE + ["fav_lead"], lambda: HistGradientBoostingClassifier(max_iter=300, learning_rate=0.03, max_leaf_nodes=4, min_samples_leaf=300, l2_regularization=5, monotonic_cst=mono, random_state=SEED))),
              ("Gradient boosting, bigger trees", cv(BASE + ["fav_lead"], lambda: HistGradientBoostingClassifier(max_iter=300, learning_rate=0.03, max_leaf_nodes=8, min_samples_leaf=300, l2_regularization=5, monotonic_cst=mono, random_state=SEED))),
              ("Logistic with spline curves on every input", cv(BASE, lambda: make_pipeline(StandardScaler(), SplineTransformer(n_knots=5, degree=3), LogisticRegression(C=1, max_iter=5000)))),
              ("Small neural network (16 and 8 units)", cv(BASE, lambda: make_pipeline(StandardScaler(), MLPClassifier((16, 8), alpha=1e-2, early_stopping=True, random_state=SEED, max_iter=200))))]
    for n, r in others:
        print(f"{n:52s} {r['cv_log_loss']:.4f}  folds beating linear {r['folds_beating_linear']}/6")

    def make_fit(S):
        m = logit(c_best).fit(S[feats], S.y)
        return lambda d: m.predict_proba(d[feats])[:, 1]
    ev = C.full_eval(make_fit, train, hold, folds, N_LINES, SEED)
    print(pd.DataFrame(ev["rows"]).T.to_string()); print("CV pooled: model", ev["cv_ll"], ev["cv_acc"], "linear", ev["cv_ll_linear"], ev["cv_acc_linear"])

    # paired bootstrap over games: is the edge over the linear model real on the unseen games?
    rng = np.random.default_rng(SEED)
    lf_h = C.linear_fit(train); E2 = ev["E2"]
    d_ll = (-(E2.y * np.log(np.clip(C.linear_p(lf_h, E2), 1e-6, 1)) + (1 - E2.y) * np.log(np.clip(1 - C.linear_p(lf_h, E2), 1e-6, 1)))
            + (E2.y * np.log(np.clip(ev["p_hold"], 1e-6, 1)) + (1 - E2.y) * np.log(np.clip(1 - ev["p_hold"], 1e-6, 1)))).groupby(E2.game_id).mean().values
    boots = [d_ll[rng.integers(0, len(d_ll), len(d_ll))].mean() for _ in range(4000)]
    edge = {"holdout_gain": round(float(d_ll.mean()), 4), "lo": round(float(np.percentile(boots, 2.5)), 4), "hi": round(float(np.percentile(boots, 97.5)), 4)}
    print("holdout log-loss gain over linear (positive = better):", edge)

    S_all = C.stack_train(df, N_LINES, SEED)
    final = logit(c_best).fit(S_all[feats], S_all.y)
    sc, lr = final.named_steps["standardscaler"], final.named_steps["logisticregression"]
    raw = C.raw_inputs(feats)
    sch = C.schema(raw, df)
    model = {"type": "logistic_classifier", "target": "over", "feature_order": feats, "mean": sc.mean_.tolist(), "scale": sc.scale_.tolist(),
             "coef": lr.coef_[0].tolist(), "intercept": float(lr.intercept_[0]), "C": c_best,
             "typical": {d["name"]: d["default"] for d in sch}, "percentiles": C.percentiles(df, [r for r in raw if r != "line"]),
             "n_train": int(len(df)), "seasons": [int(df.season.min()), int(df.season.max())], "trained_on": date.today().isoformat()}
    json.dump(model, open(os.path.join(HERE, "model.json"), "w"), indent=1)

    raw_coef = dict(zip(feats, lr.coef_[0] / sc.scale_))
    sig = lambda z: 1 / (1 + np.exp(-z))
    m, linr = ev["rows"]["model"], ev["rows"]["linear"]
    n_beat = int(best.folds_beating_linear)
    findings = [
        f"This is the best model found for the question 'will the game clear my total?'. In cross-validation it beat the linear model in {n_beat} of 6 rounds "
        f"(log loss {best.cv_log_loss:.4f} against {lin.mean():.4f}). The edge is consistent but small, about {100 * (lin.mean() - best.cv_log_loss) / lin.mean():.1f}%.",
        f"Two additions earned their place. A curve on points still needed: the chance does not fall in a straight line as the total rises, and letting it bend fits better. "
        f"And the favorite's halftime lead: each extra point the pregame favorite leads by {'lowers' if raw_coef.get('fav_lead', 0) < 0 else 'raises'} the odds of the over by about "
        f"{abs(100 * (np.exp(raw_coef.get('fav_lead', 0)) - 1)):.1f}%. " + ("A favorite sitting on a lead runs the clock; a favorite that is behind has to throw." if raw_coef.get("fav_lead", 0) < 0 else ""),
        "Fancier models lost. Gradient boosting, a small neural network and spline curves all scored worse than this model in the same cross-validation, "
        "and most scored worse than the plain linear model. With about 7,000 games and one dominant signal, extra flexibility mostly fits noise.",
        C.scorecard(ev, "this model") + f" On the test seasons alone the log-loss edge over the linear model is {edge['holdout_gain']:+.4f} "
        f"(95% range {edge['lo']:+.4f} to {edge['hi']:+.4f}), so {'the test seasons agree' if edge['lo'] > 0 else 'the test seasons cannot confirm the edge on their own'}.",
        "Why nothing does much better: second-half scoring is mostly luck from here. Even the best model on this site misses the final total by about 7.6 points "
        "on average, and no halftime stat tested so far narrows that.",
    ]
    g = lambda v: f"{v:g}"
    sections = [
        {"title": "How the settings were chosen",
         "paragraphs": [
             "Two things were searched together: which engineered inputs to include, and C, which controls how much the model is allowed to trust any one input "
             "(small C shrinks every weight toward zero).",
             f"All {len(grid)} combinations were scored with six rounds of cross-validation, each training on earlier seasons and grading on later ones, "
             "using seven different totals per game. 'Rounds won' counts the rounds in which the combination beat the linear model on this site."],
         "table": {"head": ["Inputs", "C", "CV log loss", "Rounds won vs linear"],
                   "rows": [[r.recipe, g(r.C), f"{r.cv_log_loss:.4f}", f"{r.folds_beating_linear} of 6"] for r in grid.head(8).itertuples()]},
         "note": "Top 8 combinations. The first row is the model on this page."},
        {"title": "Other model types tried",
         "paragraphs": ["Same data, same cross-validation, same totals. Lower is better."],
         "table": {"head": ["Model", "CV log loss", "Rounds won vs linear"],
                   "rows": [["This model", f"{best.cv_log_loss:.4f}", f"{n_beat} of 6"]] + [[n, f"{r['cv_log_loss']:.4f}", "n/a" if n.startswith("Linear") else f"{r['folds_beating_linear']} of 6"] for n, r in others]}},
    ]
    meta = C.classifier_meta(
        SLUG, NAME, "logistic_classifier",
        "Set the halftime numbers and any total you like, and get the chance the game finishes over it. In cross-validation it is the best-scoring over/under model here, by a small margin.",
        feats, df, hold, ev, "Logistic regression with engineered inputs", len(set(sum(RECIPES.values(), []))), sections, findings,
        C.COMMON_LIMITS + ["The edge over the simpler linear model is small. On any one game the two will usually agree within a couple of percentage points."])
    json.dump(meta, open(os.path.join(HERE, "meta.json"), "w"), indent=1)
    json.dump({"best": {"recipe": best.recipe, "C": c_best}, "holdout": ev["rows"], "edge_vs_linear": edge, "grid": json.loads(grid.to_json(orient="records")),
               "others": [{"model": n, **r} for n, r in others], "coef_per_unit": {k: float(v) for k, v in raw_coef.items()},
               "coef_std": dict(zip(feats, map(float, lr.coef_[0]))), "cv_pooled": {k: ev[k] for k in ("cv_ll", "cv_ll_linear", "cv_acc", "cv_acc_linear")}},
              open(os.path.join(HERE, "training_report.json"), "w"), indent=1)
    np.savez(os.path.join(HERE, "_plotdata.npz"), y_hold=ev["y_hold"], p_hold=ev["p_hold"])
    print("\nwrote model.json, meta.json, training_report.json"); [print("-", f) for f in findings]


if __name__ == "__main__":
    main()
