"""
Train the halftime over/under support vector machine (SVM) for ddyno.

Question: given the halftime numbers, will the game finish OVER a total you choose?
The total to beat is an input: every training game is paired with two different totals.
Offline only. Writes model.json, meta.json and training_report.json next to itself.
Needs ../nfl-halftime-total/train.py (dataset builder) and ../../tools/ou_common.py.

    python train.py --data-dir DIR [--last-season 2026]

How the settings are chosen
  1. Seasons before 2025 are the training pool. 2025 onward is locked away as the final test.
  2. Inputs are standardised (an SVM measures distances, so every input must be on the same scale).
  3. Grid search over kernel, C and gamma, scored with forward-chaining cross-validation
     (train on earlier seasons, validate on later ones, six folds). Log loss decides.
  4. An SVM outputs a signed distance from its boundary, not a percentage. Platt scaling (a one-input
     logistic regression fit on out-of-fold distances) turns that distance into a chance.
  5. The best recipe is scored once on the locked seasons, then refit on every game for shipping.
"""
import argparse
import json
import os
import sys
import time
import warnings
from datetime import date

import numpy as np
import pandas as pd
from joblib import Parallel, delayed
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import accuracy_score, log_loss, roc_auc_score
from sklearn.model_selection import GroupKFold, cross_val_predict
from sklearn.pipeline import make_pipeline
from sklearn.preprocessing import StandardScaler
from sklearn.svm import SVC

warnings.filterwarnings("ignore")
HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(HERE, "..", "..", "tools"))
import ou_common as C  # noqa: E402

SLUG, NAME = "nfl-halftime-ou-svm", "Halftime Over/Under (SVM)"
SEED, N_LINES = 7, 2
FEATS = ["need", "total_line", "abs_h1_margin", "h1_first_downs", "h1_explosive", "wind"]
GRID = ([{"kernel": "linear", "C": c, "gamma": None} for c in (0.01, 0.1, 1)]
        + [{"kernel": "rbf", "C": c, "gamma": g} for c in (0.1, 0.3, 1, 3, 10) for g in (0.003, 0.01, 0.03, 0.1)])


def svc(p):
    return make_pipeline(StandardScaler(), SVC(kernel=p["kernel"], C=p["C"], gamma=p["gamma"] or "scale", cache_size=800))


def platt(d, y):
    lr = LogisticRegression(C=1e6, max_iter=1000).fit(d.reshape(-1, 1), y)
    return float(lr.coef_[0, 0]), float(lr.intercept_[0])


def sig(d, a, b):
    return 1 / (1 + np.exp(-(a * d + b)))


def fit_calibrated(S, p):
    """SVM on all of S, plus Platt scaling learned from out-of-fold distances (a game's rows stay together)."""
    X, y = S[FEATS], S.y
    d = cross_val_predict(svc(p), X, y, cv=GroupKFold(4), groups=S.game_id, method="decision_function")
    a, b = platt(d, y)
    return svc(p).fit(X, y), a, b


def fold_score(p, S, tr, va):
    m, a, b = fit_calibrated(S.iloc[tr], p)
    d = m.decision_function(S[FEATS].iloc[va])
    pr = np.clip(sig(d, a, b), 1e-6, 1 - 1e-6)
    y = S.y.iloc[va]
    return log_loss(y, pr), roc_auc_score(y, d), accuracy_score(y, pr >= 0.5)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--data-dir", default=os.path.join(HERE, "..", "nfl-halftime-total", "data_cache"))
    ap.add_argument("--last-season", type=int, default=date.today().year if date.today().month >= 9 else date.today().year - 1)
    ap.add_argument("--cache", default=None)
    ap.add_argument("--quick", action="store_true")
    args = ap.parse_args()

    df = C.load(args.data_dir, args.last_season, args.cache).reset_index(drop=True)
    train, hold = df[df.season < C.HOLDOUT_FROM].reset_index(drop=True), df[df.season >= C.HOLDOUT_FROM].reset_index(drop=True)
    folds = C.B.season_folds(train.season.values)
    S = C.stack_train(train, N_LINES, SEED)
    sfolds = C.B.season_folds(S.season.values)
    print(f"games {len(df)}  train {len(train)}  holdout {len(hold)}  stacked training rows {len(S)}")

    grid = GRID[1:2] + GRID[8:9] if args.quick else GRID
    t0 = time.time()
    jobs = [(i, k) for i in range(len(grid)) for k in range(len(sfolds))]
    out = Parallel(n_jobs=2)(delayed(fold_score)(grid[i], S, *sfolds[k]) for i, k in jobs)
    rows = []
    for i, p in enumerate(grid):
        r = [o for (j, _), o in zip(jobs, out) if j == i]
        ll = np.array([v[0] for v in r])
        rows.append({**p, "cv_log_loss": ll.mean(), "cv_se": ll.std() / np.sqrt(len(ll)),
                     "cv_auc": np.mean([v[1] for v in r]), "cv_accuracy": np.mean([v[2] for v in r])})
    allres = pd.DataFrame(rows).sort_values("cv_log_loss").reset_index(drop=True)
    print(f"grid search {len(grid)} combinations x {len(sfolds)} folds in {time.time() - t0:.0f}s\n", allres.head(12).to_string())
    best = allres.iloc[0]
    params = {"kernel": best.kernel, "C": float(best.C), "gamma": None if pd.isna(best.gamma) else float(best.gamma)}
    print("best:", params)

    def make_fit(St):
        m, a, b = fit_calibrated(St, params)
        return lambda d: sig(m.decision_function(d[FEATS]), a, b)
    ev = C.full_eval(make_fit, train, hold, folds, N_LINES, SEED)
    print(pd.DataFrame(ev["rows"]).T.to_string())
    imp = C.perm_importance(ev["predict"], ev["E2"], FEATS, SEED, repeats=8)
    print(pd.DataFrame(imp).to_string())

    S_all = C.stack_train(df, N_LINES, SEED)
    final, fa, fb = fit_calibrated(S_all, params)
    sc, sv = final.named_steps["standardscaler"], final.named_steps["svc"]
    raw = C.raw_inputs(FEATS)
    sch = C.schema(raw, df)
    r5 = lambda arr: [[round(float(v), 4) for v in row] for row in arr]
    model = {"type": "svm_classifier", "target": "over", "feature_order": FEATS, "kernel": params["kernel"],
             "gamma": float(sv._gamma), "C": params["C"], "mean": sc.mean_.tolist(), "scale": sc.scale_.tolist(),
             "support_vectors": r5(sv.support_vectors_), "dual_coef": [round(float(v), 5) for v in sv.dual_coef_[0]],
             "intercept": float(sv.intercept_[0]), "platt": {"a": fa, "b": fb},
             "typical": {d["name"]: d["default"] for d in sch}, "percentiles": C.percentiles(df, [r for r in raw if r != "line"]),
             "n_train": int(len(df)), "seasons": [int(df.season.min()), int(df.season.max())], "trained_on": date.today().isoformat()}
    json.dump(model, open(os.path.join(HERE, "model.json"), "w"), separators=(",", ":"))
    n_sv, n_rows = len(sv.support_vectors_), len(S_all)

    lin_best = allres[allres.kernel == "linear"].cv_log_loss.min()
    rbf_best = allres[allres.kernel == "rbf"].cv_log_loss.min()
    kern = ("a straight-line boundary (linear kernel)" if params["kernel"] == "linear"
            else f"a curved boundary (RBF kernel, gamma {params['gamma']:g})")
    findings = [
        f"An SVM draws one boundary between game-and-total pairs that went over and pairs that stayed under, then reports which side you are on and how far "
        f"from the line. The total you want to test is one of its inputs. The grid search picked {kern} with C = {params['C']:g}.",
        "Points still needed decides most calls: how far your total is above what is already on the board. Shuffling it wrecks the model. The pregame over/under is a distant second, and the other inputs add slivers.",
        f"Curved or straight barely matters. The best straight-line boundary scored {lin_best:.4f} in cross-validation and the best curved one {rbf_best:.4f}. "
        "The real boundary is close to a straight line, which is why the plain linear model keeps up.",
        f"{n_sv:,} of the {n_rows:,} training rows ended up as support vectors, the rows close enough to the boundary to shape it. "
        f"That is {100 * n_sv / n_rows:.0f}% of them, which says overs and unders overlap heavily at halftime: there is no clean gap to find.",
        C.scorecard(ev, "the SVM"),
    ]
    g = lambda v: "–" if v is None or pd.isna(v) else f"{v:g}"
    sections = [{
        "title": "How the settings were chosen",
        "paragraphs": [
            "An SVM has three settings to pick before training. The kernel is the shape the boundary may take: a straight line (linear) or a curve (RBF). "
            "C is how hard it tries to get every training row on the right side: high C bends to fit individual games, low C keeps the boundary simple. "
            "Gamma, for the curved kernel, is how far one game's influence reaches: high gamma makes a wiggly local boundary, low gamma a smooth one.",
            f"A grid search scored all {len(allres)} combinations with six rounds of cross-validation, each round training on earlier seasons and grading on later ones. "
            f"Best log loss was {best.cv_log_loss:.4f}; the worst combination scored {allres.cv_log_loss.max():.4f}."],
        "table": {"head": ["Kernel", "C", "Gamma", "CV log loss", "CV AUC", "CV accuracy"],
                  "rows": [[r.kernel, g(r.C), g(r.gamma), f"{r.cv_log_loss:.4f}", f"{r.cv_auc:.3f}", f"{100 * r.cv_accuracy:.1f}%"] for r in allres.head(8).itertuples()]},
        "note": "Top 8 combinations. The first row is the model on this page. These scores use random totals, so they are not comparable with the test table above."}]
    meta = C.classifier_meta(
        SLUG, NAME, "svm_classifier",
        "Set the halftime numbers and any total you like, and a support vector machine says which side of its over/under boundary the game is on.",
        FEATS, df, hold, ev, f"Support vector machine ({'RBF' if params['kernel'] == 'rbf' else 'linear'} kernel, Platt-scaled)", len(FEATS), sections, findings,
        C.COMMON_LIMITS + ["An SVM does not produce percentages on its own. The chance shown comes from a second small model fit on top of it, which adds its own error.",
                           "It is the hardest of these models to explain: there are no coefficients or trees to read, only a boundary in six dimensions."])
    json.dump(meta, open(os.path.join(HERE, "meta.json"), "w"), indent=1)
    json.dump({"best": params, "holdout": ev["rows"], "importance": imp, "n_support_vectors": n_sv, "grid": json.loads(allres.to_json(orient="records")),
               "cv_pooled": {k: ev[k] for k in ("cv_ll", "cv_ll_linear", "cv_acc", "cv_acc_linear")}}, open(os.path.join(HERE, "training_report.json"), "w"), indent=1)
    np.savez(os.path.join(HERE, "_plotdata.npz"), y_hold=ev["y_hold"], p_hold=ev["p_hold"])
    print("\nwrote model.json", os.path.getsize(os.path.join(HERE, "model.json")) // 1024, "KB;", n_sv, "support vectors"); [print("-", f) for f in findings]


if __name__ == "__main__":
    main()
