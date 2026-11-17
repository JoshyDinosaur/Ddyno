"""
Train the halftime game-type clustering (k-means) for ddyno.

Unsupervised: the model is never told how a game ended. It only groups halftime box scores that look alike.
Afterwards we look up how the games in each group finished, which is what makes the groups useful.
Offline only. Writes model.json, meta.json and training_report.json next to itself.
Needs ../nfl-halftime-total/train.py (dataset builder) and ../../tools/ou_common.py.

    python train.py --data-dir DIR [--last-season 2026]

How the number of groups (k) is chosen
  For every k from 2 to 10, fit k-means 25 times from different random starts and keep the best, then measure:
    inertia            total squared distance to the nearest centre (always falls as k grows; look for the elbow)
    silhouette         how much closer a game is to its own group than to the next one (higher is better, max 1)
    Calinski-Harabasz  spread between groups over spread within groups (higher is better)
    Davies-Bouldin     how much neighbouring groups overlap (lower is better)
    stability          refit on random halves of the games and check the two fits agree (adjusted Rand index, max 1)
    hold-out silhouette  silhouette on the 2025+ seasons using centres learned from earlier seasons
  The page ships every k from 2 to 8 so you can switch between them; DEFAULT_K is the one shown first.
"""
import argparse
import json
import os
import sys
import warnings
from datetime import date

import numpy as np
import pandas as pd
from sklearn.cluster import KMeans
from sklearn.metrics import adjusted_rand_score, calinski_harabasz_score, davies_bouldin_score, silhouette_score
from sklearn.preprocessing import StandardScaler

warnings.filterwarnings("ignore")
HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(HERE, "..", "..", "tools"))
import ou_common as C  # noqa: E402

SLUG, NAME = "nfl-halftime-game-types", "Halftime Game Types (K-Means)"
SEED = 7
FEATS = ["home_h1_pts", "away_h1_pts", "home_h1_yards", "away_h1_yards"]
K_RANGE, K_SHIPPED = range(2, 11), range(2, 9)


def km(k, seed=SEED, n_init=25):
    return KMeans(n_clusters=k, n_init=n_init, random_state=seed)


def name_clusters(cent):
    """Plain-English names from the centres (in real units): who leads, and how much scoring there has been."""
    avg_total = cent.home_h1_pts.mean() + cent.away_h1_pts.mean()
    names = []
    for c in cent.itertuples():
        total, margin = c.home_h1_pts + c.away_h1_pts, c.home_h1_pts - c.away_h1_pts
        if abs(margin) >= 4:
            who = "Home" if margin > 0 else "Away"
            names.append(f"{who} {'running away' if abs(margin) >= 16 else 'in control'}")
        else:
            names.append("Shootout" if total >= avg_total + 6 else "Defensive struggle" if total <= avg_total - 6 else "Even game")
    # Same name twice: tell them apart by how much scoring there has been.
    for n in set(names):
        idx = [i for i, x in enumerate(names) if x == n]
        if len(idx) > 1:
            order = sorted(idx, key=lambda i: cent.home_h1_pts[i] + cent.away_h1_pts[i])
            tags = ["low scoring", "high scoring"] if len(idx) == 2 else ["low scoring", "middling"] + ["high scoring"] * (len(idx) - 2)
            for i, t in zip(order, tags):
                names[i] = f"{n}, {t}"
    seen = {}
    for i, n in enumerate(names):          # last resort so names are always unique
        seen[n] = seen.get(n, 0) + 1
        if seen[n] > 1:
            names[i] = f"{n} ({seen[n]})"
    return names


def profile(g):
    np_ = g[~g.push]
    return {"games": int(len(g)), "final_total": round(float(g.final_total.mean()), 1), "second_half": round(float((g.final_total - g.h1_total).mean()), 1),
            "home_win": round(float((g.home_final > g.away_final).mean()), 3), "over": round(float(np_.over.mean()), 3),
            "total_line": round(float(g.total_line.mean()), 1)}


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--data-dir", default=os.path.join(HERE, "..", "nfl-halftime-total", "data_cache"))
    ap.add_argument("--last-season", type=int, default=date.today().year if date.today().month >= 9 else date.today().year - 1)
    ap.add_argument("--cache", default=None)
    ap.add_argument("--default-k", type=int, default=None)
    args = ap.parse_args()

    df = C.load(args.data_dir, args.last_season, args.cache).reset_index(drop=True)
    train, hold = df[df.season < C.HOLDOUT_FROM], df[df.season >= C.HOLDOUT_FROM]
    sc_tr = StandardScaler().fit(train[FEATS])
    Zt, Zh = sc_tr.transform(train[FEATS]), sc_tr.transform(hold[FEATS])
    rng = np.random.default_rng(SEED)

    rows = []
    for k in K_RANGE:
        m = km(k).fit(Zt)
        ari = []
        for b in range(12):
            i1, i2 = rng.choice(len(Zt), len(Zt) // 2, replace=False), rng.choice(len(Zt), len(Zt) // 2, replace=False)
            ari.append(adjusted_rand_score(km(k, b, 5).fit(Zt[i1]).predict(Zt), km(k, 100 + b, 5).fit(Zt[i2]).predict(Zt)))
        # Do the groups mean anything for results the model never saw? Share of final-total variance between groups.
        lab_h = m.predict(Zh)
        ft = hold.final_total.values
        eta = sum((lab_h == j).sum() * (ft[lab_h == j].mean() - ft.mean()) ** 2 for j in range(k) if (lab_h == j).any()) / ((ft - ft.mean()) ** 2).sum()
        rows.append({"k": k, "inertia": round(float(m.inertia_)), "silhouette": round(float(silhouette_score(Zt, m.labels_)), 3),
                     "calinski_harabasz": round(float(calinski_harabasz_score(Zt, m.labels_))),
                     "davies_bouldin": round(float(davies_bouldin_score(Zt, m.labels_)), 3),
                     "stability": round(float(np.mean(ari)), 3), "holdout_silhouette": round(float(silhouette_score(Zh, lab_h)), 3),
                     "holdout_total_explained": round(float(eta), 3), "smallest_group": round(float(np.bincount(m.labels_).min() / len(Zt)), 3)})
        print(rows[-1])
    table = pd.DataFrame(rows)
    # Default k: the largest k that is still stable (>= 0.85) among those whose silhouette is within 0.05 of the best.
    ok = table[(table.stability >= 0.85) & (table.silhouette >= table.silhouette.max() - 0.05) & table.k.isin(list(K_SHIPPED))]
    default_k = args.default_k or int(ok.k.max())
    print("\n", table.to_string(), "\ndefault k:", default_k)

    # Shipped: centres fit on every game, one solution per k.
    sc = StandardScaler().fit(df[FEATS])
    Z = sc.transform(df[FEATS])
    solutions = {}
    for k in K_SHIPPED:
        m = km(k).fit(Z)
        cent = pd.DataFrame(sc.inverse_transform(m.cluster_centers_), columns=FEATS)
        order = np.argsort(-np.bincount(m.labels_))                      # biggest group first
        names = name_clusters(cent.iloc[order].reset_index(drop=True))
        clusters = []
        for new, old in enumerate(order):
            g = df[m.labels_ == old]
            clusters.append({"id": new, "name": names[new], "share": round(float(len(g) / len(df)), 3),
                             "centroid_z": [round(float(v), 4) for v in m.cluster_centers_[old]],
                             "centroid": {f: round(float(cent[f][old]), 1) for f in FEATS}, "profile": profile(g)})
        d = np.sqrt(((Z[:, None, :] - m.cluster_centers_[order][None]) ** 2).sum(-1)).min(1)
        solutions[str(k)] = {"clusters": clusters, "distance_p50": round(float(np.median(d)), 3), "distance_p95": round(float(np.percentile(d, 95)), 3)}
        print(f"\nk={k}")
        for c in clusters:
            print(f"  {c['name']:<34} {c['share']:.0%}  centre {c['centroid']}  -> {c['profile']}")

    sch = C.schema(FEATS, df)
    typical = {d["name"]: d["default"] for d in sch}
    overall = profile(df)
    model = {"type": "kmeans", "feature_order": FEATS, "mean": sc.mean_.tolist(), "scale": sc.scale_.tolist(),
             "solutions": solutions, "default_k": default_k, "typical": typical, "overall": overall,
             "percentiles": C.percentiles(df, FEATS), "n_train": int(len(df)),
             "seasons": [int(df.season.min()), int(df.season.max())], "trained_on": date.today().isoformat()}
    json.dump(model, open(os.path.join(HERE, "model.json"), "w"), indent=1)

    best_sil = table.loc[table.silhouette.idxmax()]
    row = table[table.k == default_k].iloc[0]
    cl = solutions[str(default_k)]["clusters"]
    hi, lo = max(cl, key=lambda c: c["profile"]["final_total"]), min(cl, key=lambda c: c["profile"]["final_total"])
    hw, lw = max(cl, key=lambda c: c["profile"]["home_win"]), min(cl, key=lambda c: c["profile"]["home_win"])
    ho, lo_o = max(cl, key=lambda c: c['profile']['over']), min(cl, key=lambda c: c['profile']['over'])
    findings = [
        f"K-means was given only four numbers per game (each team's halftime points and yards) and never saw a final score. "
        f"Asked for {default_k} groups, it found: " + "; ".join(f"{c['name']} ({c['share']:.0%} of games)" for c in cl) + ".",
        f"The groups mean something for how games end, even though endings were hidden from the model. '{hi['name']}' games finish with "
        f"{hi['profile']['final_total']:.0f} points on average and '{lo['name']}' games with {lo['profile']['final_total']:.0f}. "
        f"The home team wins {100 * hw['profile']['home_win']:.0f}% of '{hw['name']}' games and {100 * lw['profile']['home_win']:.0f}% of '{lw['name']}' games.",
        f"Game type also says a lot about the over/under. '{ho['name']}' games went over the pregame total {100 * ho['profile']['over']:.0f}% of the time and "
        f"'{lo_o['name']}' games only {100 * lo_o['profile']['over']:.0f}%. That is not magic: the type mostly reflects how many points are already on the board, "
        "which is the same signal the over/under models on this site use.",
        f"Honest caveat: halftime box scores do not fall into natural clumps. The silhouette score is {row.silhouette:.2f} at k = {default_k} "
        f"(best is {best_sil.silhouette:.2f} at k = {int(best_sil.k)}; clearly separated groups score above 0.5). "
        "The games form one cloud, and k-means is slicing it into regions. The regions are stable and readable, but the borders between them are soft.",
    ]
    meta = {
        "slug": SLUG, "name": NAME, "category": C.CATEGORY, "type": "kmeans",
        "summary": "Set each team's halftime points and yards and see which kind of game this is, and how games of that kind usually finish.",
        "target": {"label": "Game type"},
        "features": sch, "derived": [],
        "controls": [{"name": "k", "label": "Number of game types (k)", "min": min(K_SHIPPED), "max": max(K_SHIPPED), "step": 1, "default": default_k,
                      "description": f"K-means needs to be told how many groups to make. {default_k} is the default chosen by the checks on the About tab; change it to see the games carved up differently."}],
        "card": {
            "trained_on": date.today().isoformat(), "n_games": int(len(df)), "seasons": [int(df.season.min()), int(df.season.max())],
            "candidates_tested": len(FEATS), "model_kind": f"K-means clustering (k = {default_k} by default)",
            "default_k": default_k, "overall": overall,
            "clusters": [{"name": c["name"], "share": c["share"], **c["profile"]} for c in cl],
            "sections": [
                {"title": f"The {default_k} game types",
                 "paragraphs": ["Each row is one group. The first four columns are the centre of the group, which is the halftime box score of its average game. "
                                "The rest shows how those games finished. The model never saw those columns."],
                 "table": {"head": ["Type", "Share", "Home pts", "Away pts", "Home yds", "Away yds", "Avg final total", "2nd-half pts", "Home wins", "Went over"],
                           "rows": [[c["name"], f"{c['share']:.0%}", f"{c['centroid']['home_h1_pts']:.0f}", f"{c['centroid']['away_h1_pts']:.0f}",
                                     f"{c['centroid']['home_h1_yards']:.0f}", f"{c['centroid']['away_h1_yards']:.0f}", f"{c['profile']['final_total']:.1f}",
                                     f"{c['profile']['second_half']:.1f}", f"{100 * c['profile']['home_win']:.0f}%", f"{100 * c['profile']['over']:.0f}%"] for c in cl]
                                   + [["All games", "100%", "", "", "", "", f"{overall['final_total']:.1f}", f"{overall['second_half']:.1f}",
                                       f"{100 * overall['home_win']:.0f}%", f"{100 * overall['over']:.0f}%"]]}},
                {"title": "How the number of groups was chosen",
                 "paragraphs": [
                     "Clustering has no right answer to grade against, so there is no accuracy score. Instead, each choice of k is judged on whether the groups are "
                     "tight, separate and repeatable. For every k the model was fit 25 times from different random starts and the best fit kept.",
                     "Inertia always falls as k grows, so you look for the bend where it stops falling fast. Silhouette (higher is better) asks whether a game is closer to its "
                     "own group than the next one. Davies-Bouldin (lower is better) measures overlap between neighbouring groups. Stability refits on random halves of the "
                     "games and checks the two answers agree (1.00 is identical). Test silhouette uses centres learned before 2025 on the 2025+ games.",
                     f"Rule used: among the k values whose silhouette is within 0.05 of the best and whose stability is at least 0.85, take the largest. That gave k = {default_k}.",
                 ],
                 "table": {"head": ["k", "Inertia", "Silhouette", "Calinski-Harabasz", "Davies-Bouldin", "Stability", "Test silhouette", "Smallest group"],
                           "rows": [[str(r.k) + (" (default)" if r.k == default_k else ""), f"{r.inertia:,}", f"{r.silhouette:.3f}", f"{r.calinski_harabasz:,}",
                                     f"{r.davies_bouldin:.2f}", f"{r.stability:.2f}", f"{r.holdout_silhouette:.3f}", f"{100 * r.smallest_group:.0f}%"] for r in table.itertuples()]}},
            ],
            "findings": findings,
            "limitations": [
                "The groups are regions of one continuous cloud of games, not separate species. A game near a border could reasonably be either type.",
                "K-means only makes round, similar-sized groups around a centre. It cannot find long, thin or nested patterns.",
                "It uses four inputs. Turnovers, weather and who gets the ball next are not part of the grouping.",
                "The names are written by a simple rule from each group's centre. They are labels for convenience, not something the model knows.",
                "How games of a type finished is an average over many games. It is context, not a prediction for this game.",
            ],
            "disclaimer": "For information and learning only. Not betting advice.",
        },
    }
    json.dump(meta, open(os.path.join(HERE, "meta.json"), "w"), indent=1)
    json.dump({"k_table": rows, "default_k": default_k, "features": FEATS}, open(os.path.join(HERE, "training_report.json"), "w"), indent=1)
    print("\nwrote model.json, meta.json, training_report.json")


if __name__ == "__main__":
    main()
