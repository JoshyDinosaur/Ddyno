"""
Train the halftime over/under random forest for ddyno.

Question: given the halftime numbers, will the game finish OVER a total you choose?
The total to beat is an input. Every training game is paired with several different totals, so one forest
learns the chance of clearing any number. Offline only. Writes model.json, meta.json, training_report.json.
Needs ../nfl-halftime-total/train.py (dataset builder) and ../../tools/ou_common.py.

    python train.py --data-dir DIR [--last-season 2026]

How the settings are chosen
  1. Seasons before 2025 are the training pool. 2025 onward is locked away as the final test.
  2. Grid search: every combination of the settings in GRID, for each set of inputs, is scored with
     forward-chaining cross-validation (train on earlier seasons, validate on later ones, six folds). Log loss decides.
  3. The best combination is scored once on the locked seasons, then refit on every game for shipping.
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
from sklearn.ensemble import RandomForestClassifier
from sklearn.metrics import log_loss
from sklearn.model_selection import GridSearchCV

warnings.filterwarnings("ignore")
HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(HERE, "..", "..", "tools"))
import ou_common as C  # noqa: E402

SLUG, NAME = "nfl-halftime-ou-forest", "Halftime Over/Under (Random Forest)"
SEED, N_LINES, N_TREES = 7, 4, 300
FEATURE_SETS = {
    "points needed, worked out": ["need_vs_pace", "need", "total_line", "abs_h1_margin", "h1_first_downs", "h1_explosive", "wind"],
    "raw inputs only": ["line", "home_h1_pts", "away_h1_pts", "total_line", "home_h1_first_downs", "away_h1_first_downs",
                        "home_h1_explosive", "away_h1_explosive", "wind"],
}
GRID = {"max_depth": [5, 8, 12, None], "min_samples_leaf": [25, 50, 100, 200], "max_features": [2, 3, None]}


def forest(n=N_TREES, **kw):
    return RandomForestClassifier(n_estimators=n, n_jobs=2, random_state=SEED, **kw)


def export_trees(rf):
    """Flat arrays numpy can walk: per tree the split feature (-1 = leaf), threshold, children and leaf over-rate."""
    trees = []
    for est in rf.estimators_:
        t = est.tree_
        val = t.value[:, 0, :]
        trees.append({"f": t.feature.clip(min=-1).tolist(), "t": [round(float(v), 3) for v in t.threshold],
                      "l": t.children_left.tolist(), "r": t.children_right.tolist(),
                      "v": [round(float(v), 3) for v in val[:, 1] / val.sum(axis=1)]})
    return trees


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--data-dir", default=os.path.join(HERE, "..", "nfl-halftime-total", "data_cache"))
    ap.add_argument("--last-season", type=int, default=date.today().year if date.today().month >= 9 else date.today().year - 1)
    ap.add_argument("--cache", default=None)
    ap.add_argument("--quick", action="store_true", help="tiny grid, for smoke tests")
    args = ap.parse_args()

    df = C.load(args.data_dir, args.last_season, args.cache).reset_index(drop=True)
    train, hold = df[df.season < C.HOLDOUT_FROM].reset_index(drop=True), df[df.season >= C.HOLDOUT_FROM].reset_index(drop=True)
    folds = C.B.season_folds(train.season.values)
    S = C.stack_train(train, N_LINES, SEED)                      # each game with N_LINES random totals
    sfolds = C.B.season_folds(S.season.values)                   # a game's rows always stay in the same fold
    print(f"games {len(df)}  train {len(train)}  holdout {len(hold)}  stacked training rows {len(S)}")

    grid = {k: v[:2] for k, v in GRID.items()} if args.quick else GRID
    searches, t0 = [], time.time()
    for label, feats in FEATURE_SETS.items():
        g = GridSearchCV(forest(40 if args.quick else 100), grid, cv=sfolds, scoring={"ll": "neg_log_loss", "acc": "accuracy"}, refit=False, n_jobs=1).fit(S[feats], S.y)
        r = pd.DataFrame(g.cv_results_)
        searches.append(pd.DataFrame({"feature_set": label, **{k: r[f"param_{k}"] for k in grid}, "cv_log_loss": -r.mean_test_ll,
                                      "cv_se": r.std_test_ll / np.sqrt(len(sfolds)), "cv_accuracy": r.mean_test_acc}))
        print(f"{label}: best CV log loss {searches[-1].cv_log_loss.min():.4f}  ({time.time() - t0:.0f}s)")
    allres = pd.concat(searches, ignore_index=True).sort_values("cv_log_loss").reset_index(drop=True)
    best = allres.iloc[0]
    feats = FEATURE_SETS[best.feature_set]
    clean = lambda v: None if pd.isna(v) else int(v)
    params = {k: clean(best[k]) for k in grid}
    print(allres.head(10).to_string(), "\nbest:", best.feature_set, params)

    sizes = [1, 10, 40] if args.quick else [1, 2, 5, 10, 20, 50, 100, 200, 300]
    tree_curve = []
    for n in sizes:
        ll = [log_loss(S.y.iloc[va], np.clip(forest(n, **params).fit(S[feats].iloc[tr], S.y.iloc[tr]).predict_proba(S[feats].iloc[va])[:, 1], 1e-6, 1 - 1e-6)) for tr, va in sfolds]
        tree_curve.append({"trees": n, "cv_log_loss": round(float(np.mean(ll)), 4)})
    n_final = sizes[-1]

    def make_fit(St):
        m = forest(n_final, **params).fit(St[feats], St.y)
        return lambda d: m.predict_proba(d[feats])[:, 1]
    ev = C.full_eval(make_fit, train, hold, folds, N_LINES, SEED)
    print(pd.DataFrame(ev["rows"]).T.to_string())
    imp = C.perm_importance(ev["predict"], ev["E2"], feats, SEED)
    print(pd.DataFrame(imp).to_string())

    S_all = C.stack_train(df, N_LINES, SEED)
    final = forest(n_final, **params).fit(S_all[feats], S_all.y)
    raw = C.raw_inputs(feats)
    sch = C.schema(raw, df)
    model = {"type": "random_forest_classifier", "target": "over", "feature_order": feats, "trees": export_trees(final),
             "typical": {d["name"]: d["default"] for d in sch}, "percentiles": C.percentiles(df, [r for r in raw if r != "line"]),
             "params": params, "n_train": int(len(df)), "seasons": [int(df.season.min()), int(df.season.max())], "trained_on": date.today().isoformat()}
    json.dump(model, open(os.path.join(HERE, "model.json"), "w"), separators=(",", ":"))

    names = {d["name"]: d["label"] for d in C.derived_meta(feats)} | {"total_line": "the pregame over/under", "wind": "wind", "line": "your total"}
    show = lambda v: "no limit" if v is None else str(v)
    by_set = allres.groupby("feature_set").cv_log_loss.min()
    good = allres[allres.cv_log_loss <= best.cv_log_loss + best.cv_se]
    real = [names.get(i["feature"], i["feature"]).lower() for i in imp if i["gain"] > 2 * i["sd"] and i["gain"] > 0.002]
    findings = [
        "The forest now takes the total you want to test as an input. It was trained on every game paired with four different totals, so the same 300 trees "
        "can answer for 38.5, 47.5 or any other number.",
        f"What it leans on: {', '.join(real[:3]) if real else 'points still needed'}. In plain terms, how many more points the game needs, compared with what a normal second half produces. "
        "Each of the other inputs adds only a sliver on top of that.",
        f"The grid search tried {len(allres)} combinations of settings and inputs. The winner: trees up to depth {show(params['max_depth'])}, "
        f"at least {params['min_samples_leaf']} rows in every leaf, {'every input' if params['max_features'] is None else str(params['max_features']) + ' inputs'} considered per split. "
        f"{len(good) - 1} other combinations scored within the noise of the winner, so the exact settings matter little.",
        f"How the inputs are handed over matters more. Given only raw scores and totals, the best forest scored {by_set['raw inputs only']:.3f} in cross-validation. "
        f"Given 'points still needed' worked out in advance, it scored {by_set.min():.3f}. Trees split on one input at a time, so they struggle to discover a subtraction on their own.",
        C.scorecard(ev, "the forest"),
    ]
    sections = [{
        "title": "How the settings were chosen",
        "paragraphs": [
            "A random forest has settings you pick before training, called hyperparameters. Trying every combination and keeping the one that scores best on held-back games is called a grid search.",
            f"This one scored {len(allres)} combinations with six rounds of cross-validation. Each round trains on earlier seasons and is graded on later ones, "
            f"so the forest is never graded on games it has already seen. Best log loss was {best.cv_log_loss:.4f}; the worst combination scored {allres.cv_log_loss.max():.4f}."],
        "table": {"head": ["Inputs", "Max depth", "Min leaf", "Inputs per split", "CV log loss", "CV accuracy"],
                  "rows": [[r.feature_set, show(clean(r.max_depth)), str(int(r.min_samples_leaf)), show(clean(r.max_features)), f"{r.cv_log_loss:.4f}", f"{100 * r.cv_accuracy:.1f}%"]
                           for r in allres.head(8).itertuples()]},
        "note": "Top 8 combinations. The first row is the model on this page. Max depth is the deepest a tree may grow. Min leaf is the fewest training rows allowed in a leaf. "
                "Inputs per split is how many inputs each split may look at. These scores use random totals, so they are not comparable with the test table above."}]
    meta = C.classifier_meta(
        SLUG, NAME, "random_forest_classifier",
        "Set the halftime numbers and any total you like, and 300 decision trees vote on whether the game finishes over it.",
        feats, df, hold, ev, f"Random forest ({n_final} trees)", len({f for fs in FEATURE_SETS.values() for f in fs}), sections, findings,
        C.COMMON_LIMITS + ["A forest gives the same answer for every game that lands in the same leaves, so the percentage moves in steps, not smoothly, "
                           "and it can wobble slightly the wrong way when you nudge the total."],
        controls=[{"name": "n_trees", "label": "Trees that vote", "min": 1, "max": n_final, "step": 1, "default": n_final,
                   "description": f"A random forest averages many decision trees. Slide down to see how jumpy a few trees are; all {n_final} is the tuned model."}])
    json.dump(meta, open(os.path.join(HERE, "meta.json"), "w"), indent=1)
    json.dump({"best": {"feature_set": best.feature_set, **params}, "holdout": ev["rows"], "importance": imp, "tree_curve": tree_curve,
               "grid": json.loads(allres.to_json(orient="records")), "feature_sets": FEATURE_SETS,
               "cv_pooled": {k: ev[k] for k in ("cv_ll", "cv_ll_linear", "cv_acc", "cv_acc_linear")}}, open(os.path.join(HERE, "training_report.json"), "w"), indent=1)
    np.savez(os.path.join(HERE, "_plotdata.npz"), y_hold=ev["y_hold"], p_hold=ev["p_hold"])
    print("\nwrote model.json", os.path.getsize(os.path.join(HERE, "model.json")) // 1024, "KB"); [print("-", f) for f in findings]


if __name__ == "__main__":
    main()
