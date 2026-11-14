"""
Train the NFL halftime win probability model for ddyno (logistic regression).

Offline only. Writes model.json, meta.json and training_report.json next to itself.
Reuses the dataset builder from ../nfl-halftime-total/train.py, so keep both folders.

    pip install pandas pyarrow numpy scipy scikit-learn statsmodels
    python train.py                 # downloads nflverse play-by-play if needed
    python train.py --data-dir DIR  # reuse parquet files already on disk
"""
import argparse
import importlib.util
import json
import os
import warnings
from datetime import date

import numpy as np
import pandas as pd
import statsmodels.api as sm
from sklearn.feature_selection import RFECV
from sklearn.inspection import permutation_importance
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import brier_score_loss, log_loss, roc_auc_score, roc_curve
from sklearn.preprocessing import StandardScaler

warnings.filterwarnings("ignore")
HERE = os.path.dirname(os.path.abspath(__file__))
_spec = importlib.util.spec_from_file_location("base", os.path.join(HERE, "..", "nfl-halftime-total", "train.py"))
B = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(B)

HOLDOUT_FROM = 2025
RNG = np.random.default_rng(11)
SLUG, NAME, CATEGORY = "nfl-halftime-win", "Halftime Win Probability", "NFL Inference"
CONTEXT = ["spread_line", "total_line", "indoor", "grass", "temp", "wind", "home_gets_2h_kickoff",
           "home_ppg", "home_papg", "away_ppg", "away_papg"]
B.PROTECTED = ["home_h1_pts", "away_h1_pts", "spread_line", "home_h1_yards", "away_h1_yards"]
PLAIN = dict(B.PLAIN, total_line="the pregame over/under")
PLAIN.pop("spread_line")


def l1(C):
    return LogisticRegression(penalty="l1", solver="liblinear", C=C, max_iter=2000)


def plain():
    return LogisticRegression(C=1e6, max_iter=5000)


def fold_ll(X, y, folds):
    return np.array([log_loss(y.iloc[va], plain().fit(X.iloc[tr], y.iloc[tr]).predict_proba(X.iloc[va])[:, 1])
                     for tr, va in folds])


def forward_second_tier(X, y, folds, core, pool, need_wins):
    chosen, steps, groups = list(core), [], []
    for c in pool:
        g = sorted({c, B.twin_of(c)} & set(X.columns))
        if g not in groups and not set(g) & set(core):
            groups.append(g)
    while groups:
        base = fold_ll(X[chosen], y, folds)
        g, r = min(((g, fold_ll(X[chosen + g], y, folds)) for g in groups), key=lambda t: t[1].mean())
        wins = int((r < base).sum())
        step = {"group": g, "wins": wins, "logloss_gain": round(float(base.mean() - r.mean()), 5), "kept": wins >= need_wins}
        steps.append(step)
        if not step["kept"]:
            break
        chosen += g
        groups.remove(g)
    return chosen, steps


def select_features(train, candidates, label):
    X, y, seasons = train[candidates], train.home_win, train.season.values
    folds = B.season_folds(seasons)
    log = {"label": label, "n_candidates": len(candidates)}
    cols, dropped, _ = B.vif_screen(X)
    log["vif_dropped"] = dropped
    Z = pd.DataFrame(StandardScaler().fit_transform(X[cols]), columns=cols, index=X.index)

    # L1-penalised logistic regression, strength chosen by forward-chaining CV log loss (1-SE rule).
    Cs = np.geomspace(0.002, 1, 25)
    ll = np.array([[log_loss(y.iloc[va], l1(C).fit(Z.iloc[tr], y.iloc[tr]).predict_proba(Z.iloc[va])[:, 1])
                    for tr, va in folds] for C in Cs])
    mean, se = ll.mean(axis=1), ll.std(axis=1) / np.sqrt(ll.shape[1])
    best = mean.argmin()
    C_1se = float(Cs[np.where(mean <= mean[best] + se[best])[0]].min())
    lasso_keep = set(np.array(cols)[l1(C_1se).fit(Z, y).coef_[0] != 0])
    log["C_min"], log["C_1se"] = float(Cs[best]), C_1se

    Bn, hits = 300, np.zeros(len(cols))
    for _ in range(Bn):
        idx = RNG.choice(len(Z), len(Z) // 2, replace=False)
        hits += l1(C_1se).fit(Z.iloc[idx], y.iloc[idx]).coef_[0] != 0
    stab = pd.Series(hits / Bn, index=cols)

    rfe = RFECV(plain(), cv=folds, scoring="neg_log_loss", min_features_to_select=3).fit(Z, y)
    rfe_keep = set(np.array(cols)[rfe.support_])

    cut = np.sort(np.unique(seasons))[-3]
    tr, va = seasons < cut, seasons >= cut
    pi = permutation_importance(plain().fit(Z[tr], y[tr]), Z[va], y[va], n_repeats=30, random_state=11, scoring="neg_log_loss")
    perm = pd.DataFrame({"mean": pi.importances_mean, "sd": pi.importances_std}, index=cols)
    perm_keep = set(perm.index[(perm["mean"] - 2 * perm["sd"]) > 0])

    table = pd.DataFrame({"stability": stab.round(3), "lasso_1se": [c in lasso_keep for c in cols],
                          "rfecv": [c in rfe_keep for c in cols], "perm_logloss_gain": perm["mean"].round(5),
                          "perm_sig": [c in perm_keep for c in cols]})
    table["votes"] = (table.stability >= 0.8).astype(int) + table.lasso_1se + table.rfecv + table.perm_sig
    table = table.sort_values(["votes", "stability", "perm_logloss_gain"], ascending=False)
    core = list(table.index[table.votes >= 3])
    for c in list(core):
        if B.twin_of(c) in cols and B.twin_of(c) not in core:
            core.append(B.twin_of(c))
    pool = [c for c in table.index if 1 <= table.votes[c] < 3]
    chosen, steps = forward_second_tier(X, y, folds, core, pool, need_wins=len(folds) - 1)
    f = lambda cs: (float(fold_ll(X[cs], y, folds).mean()), float(fold_ll(X[cs], y, folds).std() / np.sqrt(len(folds))))
    log.update(core=core, second_tier_steps=steps, cv_logloss_all=f(cols), cv_logloss_core=f(core), cv_logloss_selected=f(chosen))
    return chosen, table, log


def scores(y, p, thr=0.5):
    y, p = np.asarray(y), np.asarray(p)
    pred = p >= thr
    tp, tn = int((pred & (y == 1)).sum()), int((~pred & (y == 0)).sum())
    fp, fn = int((pred & (y == 0)).sum()), int((~pred & (y == 1)).sum())
    out = {"accuracy": (tp + tn) / len(y), "precision": tp / max(tp + fp, 1), "recall": tp / max(tp + fn, 1),
           "specificity": tn / max(tn + fp, 1)}
    hard = set(np.unique(p)) <= {0.0, 1.0}
    out["auc"] = float(roc_auc_score(y, p)) if not hard else None
    out["brier"] = float(brier_score_loss(y, p)) if not hard else None
    return {k: (round(v, 3) if v is not None else None) for k, v in out.items()}


def feature_schema(f, df):
    if f == "spread_line":
        d = {"name": f, "label": "Pregame spread (home favored by)", "side": "shared", "unit": "pts", "step": 0.5,
             "description": "Closing point spread. Positive means the home team was favored, negative means the away team was."}
        lo, hi = np.percentile(df[f], [1, 99])
        d.update(min=float(round(lo * 2) / 2), max=float(round(hi * 2) / 2), default=float(round(df[f].median() * 2) / 2), hard_min=-30, hard_max=30)
        return d
    d = B.feature_schema(f, df)
    if f == "home_gets_2h_kickoff":
        d.update(label="Who gets the ball to start the 2nd half", choices={"1": "Home", "0": "Away"}, default=1.0,
                 description="The team that kicked off to start the game receives the second-half kickoff.")
    return d


def findings(feats, c, res, runs, use, base_p):
    sig = lambda z: 1 / (1 + np.exp(-z))
    logit0 = np.log(base_p / (1 - base_p))
    pp = lambda delta: 100 * (sig(logit0 + delta) - base_p)
    out = []
    pts = np.mean([c["home_h1_pts"], -c["away_h1_pts"]])
    out.append(f"The scoreboard does most of the talking. From an even game, each point of halftime lead is worth about "
               f"{pp(pts):.1f} percentage points of win chance, so a 7-point lead moves a coin flip to roughly {100 * sig(7 * pts):.0f}% "
               f"and a 14-point lead to roughly {100 * sig(14 * pts):.0f}%.")
    if "spread_line" in c:
        out.append(f"The pregame spread still matters at halftime. Each point the home team was favored by adds about "
                   f"{pp(c['spread_line']):.1f} percentage points, so a touchdown favorite that is tied at the half is still about "
                   f"{100 * sig(logit0 * 0 + 7 * c['spread_line']):.0f}% to win. The market's read on the better team does not expire after two quarters.")
        out.append(f"Put together, one point of pregame spread is worth about {c['spread_line'] / pts:.2f} points of halftime lead.")
    extra = []
    for stat, text in (("yards", "every 100 yards of first-half offense"), ("first_downs", "each first down"),
                       ("explosive", "each 20+ yard play"), ("turnovers", "each turnover")):
        k = f"home_h1_{stat}"
        if k in c:
            m = np.mean([c[k], -c[f"away_h1_{stat}"]]) * (100 if stat == "yards" else 1)
            extra.append(f"{text} is worth about {pp(m):+.1f} percentage points")
    if extra:
        out.append("Beyond the score: " + "; ".join(extra) + ". A team that moved the ball better than the score shows is a bit more likely to win.")
    if "home_gets_2h_kickoff" in c:
        out.append(f"Getting the ball to start the second half is worth about {pp(c['home_gets_2h_kickoff']):.1f} percentage points.")
    kept = {f.split("_h1_")[-1] for f in feats}
    dropped = [PLAIN[k] for k in PLAIN if k not in kept and k not in feats]
    out.append("Tested and left out because they added nothing once the score and spread were known: " + ", ".join(dropped) + ".")
    m, lead = res["model"], res["baseline_halftime_leader"]
    out.append(f"Honest scorecard: on games it never saw, the model picked the winner {100 * m['accuracy']:.0f}% of the time, "
               f"against {100 * lead['accuracy']:.0f}% for simply taking whoever leads at halftime and "
               f"{100 * res['baseline_pregame_favorite']['accuracy']:.0f}% for taking the pregame favorite. "
               f"Its bigger advantage is that it gives a trustworthy percentage, not just a pick.")
    return out


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--data-dir", default=os.path.join(HERE, "..", "nfl-halftime-total", "data_cache"))
    ap.add_argument("--last-season", type=int, default=date.today().year if date.today().month >= 9 else date.today().year - 1)
    args = ap.parse_args()

    df = B.build_dataset(args.data_dir, args.last_season)
    df = df[df.home_final != df.away_final].copy()            # drop the handful of ties
    df["home_win"] = (df.home_final > df.away_final).astype(int)
    train, hold = df[df.season < HOLDOUT_FROM], df[df.season >= HOLDOUT_FROM]
    print(f"games {len(df)}  train {len(train)}  holdout {len(hold)}  home win rate {df.home_win.mean():.3f}")

    box = [f"{s}_h1_{c}" for c, k in B.TEAM_STATS.items() if k == "box" for s in ("home", "away")] + CONTEXT
    adv = box + [f"{s}_h1_{c}" for c, k in B.TEAM_STATS.items() if k == "advanced" for s in ("home", "away")]
    runs = {}
    for label, cand in (("box_score_only", box), ("with_advanced_stats", adv)):
        chosen, table, log = select_features(train, cand, label)
        runs[label] = (chosen, table, log)
        print(f"\n=== {label}: {len(cand)} candidates -> {len(chosen)} selected\nVIF dropped: {log['vif_dropped']}")
        print(table[table.votes > 0].to_string())
        print("core:", log["core"], "\nsecond tier:", log["second_tier_steps"])
        print("CV log loss  all:", log["cv_logloss_all"], " core:", log["cv_logloss_core"], " selected:", log["cv_logloss_selected"])
    b, a = runs["box_score_only"][2]["cv_logloss_selected"], runs["with_advanced_stats"][2]["cv_logloss_selected"]
    use = "with_advanced_stats" if a[0] < b[0] - b[1] else "box_score_only"
    feats, table, log = runs[use]
    print(f"\nusing {use}: box {b[0]:.4f}+/-{b[1]:.4f}  advanced {a[0]:.4f}+/-{a[1]:.4f}")

    fit = sm.Logit(train.home_win, sm.add_constant(train[feats])).fit(disp=0)
    p = fit.predict(sm.add_constant(hold[feats], has_constant="add"))
    lead = np.where(hold.home_h1_pts != hold.away_h1_pts, hold.home_h1_pts > hold.away_h1_pts, hold.spread_line >= 0).astype(float)
    fav = (hold.spread_line >= 0).astype(float)
    res = {"model": scores(hold.home_win, p), "baseline_halftime_leader": scores(hold.home_win, lead),
           "baseline_pregame_favorite": scores(hold.home_win, fav)}
    res["model"]["log_loss"] = round(float(log_loss(hold.home_win, p)), 3)
    conf = np.maximum(p, 1 - p)
    right = (p >= 0.5) == (hold.home_win == 1)
    confident = {"share": round(float((conf >= 0.8).mean()), 3), "accuracy": round(float(right[conf >= 0.8].mean()), 3),
                 "tossup_share": round(float((conf < 0.6).mean()), 3), "tossup_accuracy": round(float(right[conf < 0.6].mean()), 3)}
    bins = [0, .1, .2, .3, .4, .5, .6, .7, .8, .9, 1.0001]
    calib = [{"range": f"{int(lo * 100)}-{int(min(hi, 1) * 100)}%", "n": int(m.sum()), "predicted": round(float(p[m].mean()), 3),
              "actual": round(float(hold.home_win[m].mean()), 3)}
             for lo, hi in zip(bins[:-1], bins[1:]) for m in [(p >= lo) & (p < hi)] if m.sum() >= 10]
    fpr, tpr, _ = roc_curve(hold.home_win, p)
    grid = np.linspace(0, 1, 41)
    roc = [[round(float(x), 3), round(float(np.interp(x, fpr, tpr)), 3)] for x in grid]
    print("\nHOLDOUT n =", len(hold)); print(pd.DataFrame(res).T.to_string())
    print("confident picks:", confident); print(pd.DataFrame(calib).to_string()); print(fit.summary().tables[1])

    final = sm.Logit(df.home_win, sm.add_constant(df[feats])).fit(disp=0)
    names = ["const"] + feats
    model = {"type": "logistic_regression", "target": "home_win", "intercept": float(final.params["const"]),
             "coefficients": {f: float(final.params[f]) for f in feats},
             "scaler": {"type": "none", "note": "fit on raw units; no scaling needed at inference"},
             "feature_order": names, "coef_std_err": {n: float(final.bse[n]) for n in names},
             "covariance": final.cov_params().loc[names, names].values.tolist(),
             "z_crit": {"80": 1.2815515655, "95": 1.9599639845},
             "feature_means": {f: float(df[f].mean()) for f in feats}, "base_rate": float(df.home_win.mean()),
             "percentiles": {f: {str(q): float(np.percentile(df[f], q)) for q in (1, 5, 25, 50, 75, 95, 99)} for f in feats},
             "n_train": int(len(df)), "seasons": [int(df.season.min()), int(df.season.max())], "trained_on": date.today().isoformat()}
    json.dump(model, open(os.path.join(HERE, "model.json"), "w"), indent=1)

    xb_mean = float(final.params["const"] + sum(final.params[f] * df[f].mean() for f in feats))
    base_p = 1 / (1 + np.exp(-xb_mean))
    order = {"home": 0, "away": 1, "shared": 2}
    stat_order = list(B.TEAM_STATS)
    schema = sorted((feature_schema(f, df) for f in feats),
                    key=lambda d: (order[d["side"]], feats.index(d["name"]) if d["side"] == "shared" else stat_order.index(d["name"].split("_h1_")[1])))
    row = lambda name, r: {"name": name, **r}
    meta = {
        "slug": SLUG, "name": NAME, "category": CATEGORY, "type": "logistic_regression",
        "summary": "Set the halftime numbers for both teams and get each side's chance of winning the game.",
        "target": {"label": "Home win chance", "positive": "Home", "negative": "Away"},
        "features": schema, "derived": [],
        "card": {
            "trained_on": date.today().isoformat(), "n_games": int(len(df)), "seasons": [int(df.season.min()), int(df.season.max())],
            "candidates_tested": len(adv), "holdout_label": f"{HOLDOUT_FROM} season onward ({len(hold)} games the model never saw)",
            "model_kind": "Logistic regression",
            "accuracy_columns": [["accuracy", "Accuracy", "pct"], ["precision", "Precision", "pct"], ["recall", "Recall", "pct"],
                                 ["specificity", "Specificity", "pct"], ["auc", "AUC", "num"]],
            "accuracy": [row("This model", res["model"]), row("Pick the halftime leader", res["baseline_halftime_leader"]),
                         row("Pick the pregame favorite", res["baseline_pregame_favorite"])],
            "metric_note": "A pick counts as 'home wins' when the model says 50% or more. Accuracy is the share of games picked right. "
                           "Precision: when it picked the home team, how often the home team won. Recall: of the games the home team won, how many it picked. "
                           "Specificity: of the games the away team won, how many it picked. ROC AUC measures how well the percentages rank games from "
                           "least to most likely (0.5 is a coin flip, 1.0 is perfect). The simple picks have no AUC because they give no percentage.",
            "brier": res["model"]["brier"], "log_loss": res["model"]["log_loss"],
            "calibration": calib, "roc": roc, "confident": confident,
            "findings": findings(feats, {f: float(final.params[f]) for f in feats}, res, runs, use, 0.5),
            "limitations": [
                "It only knows what you enter. Injuries, a quarterback change or a team resting starters are invisible to it.",
                "It treats every point of lead the same. Real games bend: going from a 3-point to a 10-point lead matters more than going from 24 to 31.",
                "Ties are left out of the history (there are only a handful), so the two sides always add up to 100%.",
                "Sliders move independently, so you can enter combinations that rarely happen in real games. Unusual inputs are flagged.",
                "The uncertainty band shows how sure the model is about its percentage. It does not make an upset any less possible."],
            "disclaimer": "For information and learning only. Not betting advice.",
        },
    }
    json.dump(meta, open(os.path.join(HERE, "meta.json"), "w"), indent=1)
    report = {"used": use, "selected": feats, "holdout": res, "confident": confident, "calibration": calib,
              "runs": {k: {"selected": v[0], "log": v[2], "table": v[1].reset_index().rename(columns={"index": "feature"}).to_dict("records")} for k, v in runs.items()},
              "coef_table": [{"feature": n, "coef": float(fit.params[n]), "se": float(fit.bse[n]), "p": float(fit.pvalues[n])} for n in names]}
    json.dump(report, open(os.path.join(HERE, "training_report.json"), "w"), indent=1, default=str)
    print("\nwrote model.json, meta.json and training_report.json; average-game home win chance", round(base_p, 3))


if __name__ == "__main__":
    main()
