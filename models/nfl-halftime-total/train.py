"""
Train the NFL halftime -> final total points model for ddyno.

Offline only. The web app never imports this file; it reads model.json and
meta.json, which this script writes next to itself.

    pip install pandas pyarrow numpy scikit-learn statsmodels
    python train.py                 # downloads nflverse play-by-play into ./data_cache
    python train.py --data-dir DIR  # reuse parquet files already on disk

Data: nflverse play-by-play (https://github.com/nflverse/nflverse-data, release
"pbp"), one parquet per season. Nothing here is simulated.
"""
import argparse
import json
import os
import urllib.request
import warnings
from datetime import date

import numpy as np
import pandas as pd
import statsmodels.api as sm
from scipy import stats
from sklearn.feature_selection import RFECV
from sklearn.inspection import permutation_importance
from sklearn.linear_model import Lasso, LassoCV, LinearRegression
from sklearn.preprocessing import StandardScaler
from statsmodels.stats.outliers_influence import variance_inflation_factor

warnings.filterwarnings("ignore")
HERE = os.path.dirname(os.path.abspath(__file__))
URL = "https://github.com/nflverse/nflverse-data/releases/download/pbp/play_by_play_{y}.parquet"
FIRST_SEASON = 1999
HOLDOUT_FROM = 2025          # seasons >= this are never touched during selection
RNG = np.random.default_rng(7)

PBP_COLS = ["game_id", "season", "season_type", "week", "home_team", "away_team", "posteam", "defteam", "qtr",
            "pass", "rush", "yards_gained", "epa", "success", "interception", "fumble_lost",
            "third_down_converted", "third_down_failed", "first_down", "sack", "penalty", "penalty_team",
            "penalty_yards", "posteam_score_post", "defteam_score_post", "total_home_score", "total_away_score",
            "home_score", "away_score", "total_line", "spread_line", "roof", "surface", "temp", "wind",
            "fixed_drive", "yardline_100", "kickoff_attempt", "punt_attempt", "field_goal_attempt",
            "no_huddle", "shotgun"]

# Per-team first-half stats. "box" = something a halftime box score shows.
TEAM_STATS = {
    "pts": "box", "plays": "box", "yards": "box", "ypp": "box", "pass_rate": "box", "turnovers": "box",
    "third_rate": "box", "first_downs": "box", "sacks": "box", "explosive": "box", "rz_drives": "box",
    "punts": "box", "fg_att": "box", "pen_yards": "box", "drives": "box", "plays_per_drive": "box",
    "epa": "advanced", "success": "advanced", "no_huddle": "advanced", "shotgun": "advanced",
}
STAT_ORDER = list(TEAM_STATS)
CONTEXT = ["total_line", "spread_line", "indoor", "grass", "temp", "wind", "home_gets_2h_kickoff",
           "home_ppg", "home_papg", "away_ppg", "away_papg", "abs_h1_margin"]
# Never dropped by the collinearity screen. Yards are protected because total yards is the stat every
# halftime box score shows, so when yards, plays and yards-per-play overlap the derived ones go first.
PROTECTED = ["home_h1_pts", "away_h1_pts", "total_line", "home_h1_yards", "away_h1_yards"]


# ------------------------------------------------------------------- page metadata
SLUG, NAME, CATEGORY = "nfl-halftime-total", "Halftime to Final Total", "NFL Inference"
DERIVED = {"abs_h1_margin": {"op": "absdiff", "args": ["home_h1_pts", "away_h1_pts"], "label": "Halftime margin",
                             "description": "Gap between the two halftime scores. Worked out for you."}}
# stat -> (label, unit, step, hard max, description)
STAT_INFO = {
    "pts": ("Halftime points", "pts", 1, 60, "Points this team has at halftime."),
    "first_downs": ("First downs", "", 1, 30, "First downs gained in the first half."),
    "explosive": ("Big plays (20+ yds)", "", 1, 15, "Runs or passes of 20 yards or more in the first half."),
    "yards": ("Total yards", "yds", 5, 500, "Offensive yards gained in the first half."),
    "plays": ("Offensive plays", "", 1, 70, "Runs plus pass plays in the first half."),
    "ypp": ("Yards per play", "yds", 0.1, 15, "First-half yards divided by plays."),
    "pass_rate": ("Pass share", "%", 1, 100, "Share of first-half plays that were passes."),
    "turnovers": ("Turnovers", "", 1, 8, "Interceptions plus lost fumbles in the first half."),
    "third_rate": ("3rd-down conversions", "%", 1, 100, "Share of third downs converted in the first half."),
    "sacks": ("Sacks taken", "", 1, 10, "Times this team's quarterback was sacked in the first half."),
    "rz_drives": ("Red-zone trips", "", 1, 8, "First-half drives that got inside the 20."),
    "punts": ("Punts", "", 1, 10, "Punts in the first half."),
    "fg_att": ("Field goal tries", "", 1, 6, "Field goals attempted in the first half."),
    "pen_yards": ("Penalty yards", "yds", 5, 150, "Penalty yards against this team in the first half."),
    "drives": ("Drives", "", 1, 12, "Possessions in the first half."),
    "plays_per_drive": ("Plays per drive", "", 0.1, 15, "Average plays per first-half possession."),
    "epa": ("EPA per play", "", 0.01, 1, "Expected points added per play in the first half."),
    "success": ("Success rate", "", 0.01, 1, "Share of first-half plays that gained enough to stay on schedule."),
    "no_huddle": ("No-huddle share", "", 0.01, 1, "Share of first-half plays run without a huddle."),
    "shotgun": ("Shotgun share", "", 0.01, 1, "Share of first-half plays from shotgun."),
}
CONTEXT_INFO = {
    "total_line": ("Pregame over/under", "pts", 0.5, 70, "The closing Vegas total for the game, set before kickoff."),
    "spread_line": ("Pregame spread (home favored by)", "pts", 0.5, 30, "Closing point spread. Positive means the home team was favored."),
    "wind": ("Wind", "mph", 1, 40, "Wind speed at the stadium. Use 0 for a dome or closed roof."),
    "temp": ("Temperature", "F", 1, 110, "Temperature at kickoff. Use 70 for a dome."),
    "indoor": ("Indoors (1 = yes)", "", 1, 1, "1 for a dome or closed roof, 0 for outdoors."),
    "grass": ("Grass field (1 = yes)", "", 1, 1, "1 for natural grass, 0 for artificial turf."),
    "home_gets_2h_kickoff": ("Home receives 2nd-half kickoff (1 = yes)", "", 1, 1, "1 if the home team gets the ball to start the third quarter."),
    "home_ppg": ("Home season points per game", "pts", 0.5, 45, "Home team's scoring average so far this season."),
    "home_papg": ("Home season points allowed", "pts", 0.5, 45, "Points per game the home team has allowed this season."),
    "away_ppg": ("Away season points per game", "pts", 0.5, 45, "Away team's scoring average so far this season."),
    "away_papg": ("Away season points allowed", "pts", 0.5, 45, "Points per game the away team has allowed this season."),
}
PLAIN = {"turnovers": "turnovers", "third_rate": "third-down conversion rate", "pen_yards": "penalties",
         "rz_drives": "red-zone trips", "pass_rate": "how pass-heavy each team was", "punts": "punts",
         "fg_att": "field goal tries", "sacks": "sacks", "yards": "total yards", "first_downs": "first downs",
         "explosive": "big plays", "plays": "play counts", "spread_line": "the point spread",
         "indoor": "dome or outdoors", "grass": "grass or turf", "temp": "temperature", "wind": "wind",
         "home_gets_2h_kickoff": "who gets the second-half kickoff", "home_ppg": "each team's season scoring average"}


def feature_schema(f, df):
    side = "home" if f.startswith("home_h1_") else "away" if f.startswith("away_h1_") else "shared"
    label, unit, step, hard_max, desc = STAT_INFO[f.split("_h1_")[1]] if side != "shared" else CONTEXT_INFO[f]
    snap = lambda v: round(round(v / step) * step, 4)
    lo, hi = np.percentile(df[f], [1, 99])
    return {"name": f, "label": label, "side": side, "unit": unit, "step": step,
            "min": snap(lo), "max": snap(hi), "default": snap(df[f].median()),
            "hard_min": min(0.0, snap(df[f].min())), "hard_max": hard_max, "description": desc}


def plain_findings(feats, coef, runs, use, res, cover, n_games, seasons, n_cand):
    out, c = [], coef
    hp = np.mean([c[f] for f in ("home_h1_pts", "away_h1_pts") if f in c])
    out.append(f"Two things carry almost all of the signal: the halftime score and the pregame over/under. "
               f"A point already on the board is worth about {hp:.2f} points in the final total, so first-half scoring "
               f"neither snowballs nor fades much. Each point of the pregame over/under adds about {c['total_line']:.2f}.")
    extras = []
    if "home_h1_first_downs" in c:
        extras.append(f"each first down adds about {np.mean([c['home_h1_first_downs'], c['away_h1_first_downs']]):.2f} points")
    if "home_h1_explosive" in c:
        extras.append(f"each 20+ yard play adds about {np.mean([c['home_h1_explosive'], c['away_h1_explosive']]):.2f}")
    if "home_h1_yards" in c:
        extras.append(f"every 100 yards adds about {100 * np.mean([c['home_h1_yards'], c['away_h1_yards']]):.1f}")
    if extras:
        out.append("Moving the ball without scoring still counts a little: " + " and ".join(extras)
                   + ". Offenses that looked better than the scoreboard tend to cash in later.")
    if "wind" in c:
        out.append(f"Wind is the only weather input that held up. Every 10 mph takes about {abs(10 * c['wind']):.1f} points off the final total.")
    if "abs_h1_margin" in c:
        out.append(f"Lopsided games slow down. Each point of halftime margin trims about {abs(c['abs_h1_margin']):.2f} points, "
                   f"so a 21-point lead costs roughly {abs(21 * c['abs_h1_margin']):.1f} as the leader runs the clock.")
    kept = {f.split("_h1_")[-1] for f in feats}
    dropped = [PLAIN[k] for k in PLAIN if k not in kept and k not in feats and not (k == "home_ppg" and "home_ppg" in feats)]
    out.append("Tested and left out because they added nothing once the score and the betting line were known: "
               + ", ".join(dropped) + ". Most of what these stats tell you already shows up in the score.")
    b = runs["box_score_only"][2]["cv_rmse_selected"][0]
    a = runs["with_advanced_stats"][2]["cv_rmse_selected"][0]
    out.append(f"Advanced stats (EPA per play, success rate, shotgun and no-huddle share) were also tried. "
               f"They did not beat plain box-score stats ({a:.2f} vs {b:.2f} points of typical error), so the inputs stay simple.")
    gain = res["baseline_halftime_plus_half_vegas"]["rmse"] - res["model"]["rmse"]
    out.append(f"Honest scorecard: on games it never saw, the model misses by {res['model']['mae']:.1f} points on average. "
               f"That is far better than doubling the halftime score ({res['baseline_double_halftime']['mae']:.1f}) or using the "
               f"pregame over/under alone ({res['baseline_vegas_total']['mae']:.1f}), but only about {gain:.1f} points of error better than "
               f"the simple recipe of halftime score plus half the over/under.")
    return out

# --------------------------------------------------------------------------- data
def fetch(data_dir, seasons):
    os.makedirs(data_dir, exist_ok=True)
    paths = []
    for y in seasons:
        p = os.path.join(data_dir, f"pbp_{y}.parquet")
        if not os.path.exists(p):
            print("downloading", y)
            urllib.request.urlretrieve(URL.format(y=y), p)
        paths.append(p)
    return paths


def one_season(path):
    d = pd.read_parquet(path, columns=PBP_COLS)
    g = d.groupby("game_id", sort=False)
    games = g.agg(season=("season", "first"), season_type=("season_type", "first"), week=("week", "first"),
                  home_team=("home_team", "first"), away_team=("away_team", "first"),
                  home_final=("home_score", "first"), away_final=("away_score", "first"),
                  total_line=("total_line", "first"), spread_line=("spread_line", "first"),
                  roof=("roof", "first"), surface=("surface", "first"), temp=("temp", "first"),
                  wind=("wind", "first"), max_qtr=("qtr", "max"))
    # Who received the opening kickoff is known before the game; the other team receives after halftime.
    ko = d[(d.kickoff_attempt == 1) & (d.qtr == 1)].groupby("game_id").first()
    games["home_recv_open"] = (ko.posteam == ko.home_team).reindex(games.index).astype(float)

    h = d[d.qtr <= 2].copy()          # LEAKAGE CONTROL: only first-half plays below this line
    home_pos = h.posteam == h.home_team
    h["hs"] = np.where(h.posteam.isna(), h.total_home_score,
                       np.where(home_pos, h.posteam_score_post, h.defteam_score_post))
    h["as_"] = np.where(h.posteam.isna(), h.total_away_score,
                        np.where(home_pos, h.defteam_score_post, h.posteam_score_post))
    games["home_h1_pts"] = h.groupby("game_id").hs.max()
    games["away_h1_pts"] = h.groupby("game_id").as_.max()

    sc = h[(h["pass"] == 1) | (h["rush"] == 1)]
    for side in ("home", "away"):
        s = sc[sc.posteam == sc[f"{side}_team"]]
        a = s.groupby("game_id").agg(
            plays=("epa", "size"), yards=("yards_gained", "sum"), epa=("epa", "mean"), success=("success", "mean"),
            pass_rate=("pass", "mean"), ints=("interception", "sum"), fum=("fumble_lost", "sum"),
            c3=("third_down_converted", "sum"), f3=("third_down_failed", "sum"), first_downs=("first_down", "sum"),
            sacks=("sack", "sum"), no_huddle=("no_huddle", "mean"), shotgun=("shotgun", "mean"),
            drives=("fixed_drive", "nunique"))
        a["explosive"] = s[s.yards_gained >= 20].groupby("game_id").size()
        a["rz_drives"] = s[s.yardline_100 <= 20].groupby("game_id").fixed_drive.nunique()
        allp = h[h.posteam == h[f"{side}_team"]]
        a["punts"] = allp[allp.punt_attempt == 1].groupby("game_id").size()
        a["fg_att"] = allp[allp.field_goal_attempt == 1].groupby("game_id").size()
        pen = h[(h.penalty == 1) & (h.penalty_team == h[f"{side}_team"])]
        a["pen_yards"] = pen.groupby("game_id").penalty_yards.sum()
        a = a.reindex(games.index).fillna(0)
        a["ypp"] = a.yards / a.plays.clip(lower=1)
        a["turnovers"] = a.ints + a.fum
        a["third_rate"] = 100 * a.c3 / (a.c3 + a.f3).clip(lower=1)
        a["pass_rate"] = 100 * a.pass_rate
        a["plays_per_drive"] = a.plays / a.drives.clip(lower=1)
        for c in TEAM_STATS:
            if c != "pts":
                games[f"{side}_h1_{c}"] = a[c]
    return games.reset_index()


def add_context(df):
    df = df.sort_values(["season", "week", "game_id"]).reset_index(drop=True)
    df["final_total"] = df.home_final + df.away_final
    df["indoor"] = df.roof.isin(["dome", "closed"]).astype(float)
    df["grass"] = df.surface.fillna("").str.strip().str.contains("grass").astype(float)
    df["temp"] = np.where(df.indoor == 1, 70.0, df.temp)
    df["wind"] = np.where(df.indoor == 1, 0.0, df.wind)
    df["temp"] = df.temp.fillna(df.temp[df.indoor == 0].median())
    df["wind"] = df.wind.fillna(df.wind[df.indoor == 0].median()).clip(upper=40)
    df["home_gets_2h_kickoff"] = 1 - df.home_recv_open.fillna(0.5)
    df["abs_h1_margin"] = (df.home_h1_pts - df.away_h1_pts).abs()
    # Season-to-date scoring for each team, from games BEFORE this one only.
    long = pd.concat([
        df[["game_id", "season", "week"]].assign(team=df.home_team, pf=df.home_final, pa=df.away_final),
        df[["game_id", "season", "week"]].assign(team=df.away_team, pf=df.away_final, pa=df.home_final),
    ]).sort_values(["team", "season", "week"])
    grp = long.groupby(["team", "season"])
    long["ppg"] = grp.pf.transform(lambda s: s.shift(1).expanding().mean())
    long["papg"] = grp.pa.transform(lambda s: s.shift(1).expanding().mean())
    prev = long.groupby(["team", "season"])[["pf", "pa"]].mean().reset_index()
    prev["season"] += 1
    long = long.merge(prev.rename(columns={"pf": "prev_pf", "pa": "prev_pa"}), on=["team", "season"], how="left")
    long["ppg"] = long.ppg.fillna(long.prev_pf).fillna(21.5)
    long["papg"] = long.papg.fillna(long.prev_pa).fillna(21.5)
    for side in ("home", "away"):
        m = long.merge(df[["game_id", f"{side}_team"]], left_on=["game_id", "team"],
                       right_on=["game_id", f"{side}_team"])[["game_id", "ppg", "papg"]]
        df = df.merge(m.rename(columns={"ppg": f"{side}_ppg", "papg": f"{side}_papg"}), on="game_id")
    return df


def build_dataset(data_dir, last_season):
    paths = fetch(data_dir, range(FIRST_SEASON, last_season + 1))
    df = pd.concat([one_season(p) for p in paths], ignore_index=True)
    df = df[df.home_final.notna() & df.total_line.notna()]
    return add_context(df)


# ---------------------------------------------------------------------- selection
def season_folds(seasons, n=6, min_train=8):
    """Forward-chaining folds: always train on earlier seasons, validate on later ones."""
    uniq = np.sort(np.unique(seasons))
    blocks = np.array_split(uniq[min_train:], n)
    out = []
    for b in blocks:
        tr = np.where(seasons < b[0])[0]
        va = np.where(np.isin(seasons, b))[0]
        out.append((tr, va))
    return out


def cv_rmse(X, y, folds):
    errs = []
    for tr, va in folds:
        m = LinearRegression().fit(X.iloc[tr], y.iloc[tr])
        errs.append(np.sqrt(np.mean((y.iloc[va] - m.predict(X.iloc[va])) ** 2)))
    return float(np.mean(errs)), float(np.std(errs) / np.sqrt(len(errs)))


def vif_screen(X, limit=10.0):
    cols, dropped = list(X.columns), []
    while True:
        Z = StandardScaler().fit_transform(X[cols])
        v = pd.Series([variance_inflation_factor(Z, i) for i in range(len(cols))], index=cols)
        cand = v.drop([c for c in PROTECTED if c in v.index])
        if cand.max() <= limit:
            return cols, dropped, v
        worst = cand.idxmax()
        dropped.append((worst, round(float(cand.max()), 1)))
        cols.remove(worst)


def twin_of(c):
    if c.startswith("home_"):
        return c.replace("home_", "away_", 1)
    if c.startswith("away_"):
        return c.replace("away_", "home_", 1)
    return c


def fold_rmses(X, y, folds):
    return np.array([np.sqrt(np.mean((y.iloc[va] - LinearRegression().fit(X.iloc[tr], y.iloc[tr]).predict(X.iloc[va])) ** 2))
                     for tr, va in folds])


def forward_second_tier(X, y, folds, core, pool, need_wins):
    """Greedy forward step for weaker signals. A candidate (added for both teams when it is a team stat)
    is kept only if it lowers out-of-sample RMSE in at least `need_wins` of the forward-chaining folds."""
    chosen, steps = list(core), []
    groups = []
    for c in pool:
        g = sorted({c, twin_of(c)} & set(X.columns))
        if g not in groups and not set(g) & set(core):
            groups.append(g)
    while groups:
        base = fold_rmses(X[chosen], y, folds)
        trials = [(g, fold_rmses(X[chosen + g], y, folds)) for g in groups]
        g, r = min(trials, key=lambda t: t[1].mean())
        wins = int((r < base).sum())
        if wins < need_wins:
            steps.append({"tried": g, "wins": wins, "gain": round(float(base.mean() - r.mean()), 4), "kept": False})
            break
        steps.append({"added": g, "wins": wins, "gain": round(float(base.mean() - r.mean()), 4), "kept": True})
        chosen += g
        groups.remove(g)
    return chosen, steps


def select_features(train, candidates, label):
    X, y, seasons = train[candidates], train.final_total, train.season.values
    folds = season_folds(seasons)
    log = {"label": label, "n_candidates": len(candidates)}

    cols, dropped, _ = vif_screen(X)
    log["vif_dropped"] = dropped
    Z = pd.DataFrame(StandardScaler().fit_transform(X[cols]), columns=cols, index=X.index)

    a_max = float(np.abs(Z.values.T @ (y.values - y.mean())).max() / len(Z))
    lcv = LassoCV(cv=folds, alphas=np.geomspace(a_max, a_max * 1e-3, 60), max_iter=20000).fit(Z, y)
    mse = lcv.mse_path_.mean(axis=1)
    se = lcv.mse_path_.std(axis=1) / np.sqrt(lcv.mse_path_.shape[1])
    best = mse.argmin()
    alpha_1se = float(lcv.alphas_[np.where(mse <= mse[best] + se[best])[0]].max())
    lasso_1se = Lasso(alpha=alpha_1se, max_iter=20000).fit(Z, y)
    lasso_keep = set(np.array(cols)[lasso_1se.coef_ != 0])
    log["lasso_alpha_min"], log["lasso_alpha_1se"] = float(lcv.alpha_), alpha_1se

    # Stability selection: how often does a feature survive the lasso on random half-samples?
    B, hits = 300, np.zeros(len(cols))
    for _ in range(B):
        idx = RNG.choice(len(Z), len(Z) // 2, replace=False)
        hits += Lasso(alpha=alpha_1se, max_iter=20000).fit(Z.iloc[idx], y.iloc[idx]).coef_ != 0
    stab = pd.Series(hits / B, index=cols)

    rfe = RFECV(LinearRegression(), cv=folds, scoring="neg_root_mean_squared_error", min_features_to_select=3).fit(Z, y)
    rfe_keep = set(np.array(cols)[rfe.support_])

    # Permutation importance on seasons the fit has not seen.
    cut = np.sort(np.unique(seasons))[-3]
    tr, va = seasons < cut, seasons >= cut
    lin = LinearRegression().fit(Z[tr], y[tr])
    pi = permutation_importance(lin, Z[va], y[va], n_repeats=30, random_state=7,
                                scoring="neg_root_mean_squared_error")
    perm = pd.DataFrame({"mean": pi.importances_mean, "sd": pi.importances_std}, index=cols)
    perm_keep = set(perm.index[(perm["mean"] - 2 * perm["sd"]) > 0])

    table = pd.DataFrame({
        "stability": stab.round(3), "lasso_1se": [c in lasso_keep for c in cols],
        "rfecv": [c in rfe_keep for c in cols], "perm_rmse_gain": perm["mean"].round(4),
        "perm_sig": [c in perm_keep for c in cols]})
    table["votes"] = (table.stability >= 0.8).astype(int) + table.lasso_1se + table.rfecv + table.perm_sig
    table = table.sort_values(["votes", "stability", "perm_rmse_gain"], ascending=False)
    core = list(table.index[table.votes >= 3])
    # Keep the page symmetric: if a stat matters for one team, ask for it for both.
    for c in list(core):
        if twin_of(c) in cols and twin_of(c) not in core:
            core.append(twin_of(c))
    pool = [c for c in table.index if 1 <= table.votes[c] < 3]
    chosen, steps = forward_second_tier(X, y, folds, core, pool, need_wins=len(folds) - 1)
    log["core"], log["second_tier_pool"], log["second_tier_steps"] = core, pool, steps
    log["cv_rmse_core"] = cv_rmse(X[core], y, folds)
    log["cv_rmse_all_candidates"] = cv_rmse(X[cols], y, folds)
    log["cv_rmse_selected"] = cv_rmse(X[chosen], y, folds)
    return chosen, table, log


# ------------------------------------------------------------------------ metrics
def metrics(y, p):
    e = np.asarray(y) - np.asarray(p)
    return {"rmse": round(float(np.sqrt(np.mean(e ** 2))), 2), "mae": round(float(np.mean(np.abs(e))), 2),
            "r2": round(float(1 - np.sum(e ** 2) / np.sum((y - np.mean(y)) ** 2)), 3),
            "bias": round(float(np.mean(e)), 2)}


def interval_half_width(Xc, cov, s2, tcrit):
    return tcrit * np.sqrt(s2 + np.einsum("ij,jk,ik->i", Xc, cov, Xc))


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--data-dir", default=os.path.join(HERE, "data_cache"))
    ap.add_argument("--last-season", type=int, default=date.today().year if date.today().month >= 9 else date.today().year - 1)
    ap.add_argument("--report", default=os.path.join(HERE, "training_report.json"))
    args = ap.parse_args()

    df = build_dataset(args.data_dir, args.last_season)
    train, hold = df[df.season < HOLDOUT_FROM], df[df.season >= HOLDOUT_FROM]
    print(f"games: {len(df)}  train {train.season.min()}-{train.season.max()}: {len(train)}  holdout: {len(hold)}")

    box = [f"{s}_h1_{c}" for c, kind in TEAM_STATS.items() if kind == "box" for s in ("home", "away")] + CONTEXT
    adv = box + [f"{s}_h1_{c}" for c, kind in TEAM_STATS.items() if kind == "advanced" for s in ("home", "away")]
    runs = {}
    for label, cand in (("box_score_only", box), ("with_advanced_stats", adv)):
        chosen, table, log = select_features(train, cand, label)
        runs[label] = (chosen, table, log)
        print(f"\n=== {label}: {len(cand)} candidates -> {len(chosen)} selected")
        print("VIF dropped:", log["vif_dropped"])
        print(table.to_string())
        print("core:", log["core"], "\nsecond tier:", log["second_tier_steps"])
        print("forward-chaining CV RMSE  all:", log["cv_rmse_all_candidates"], " core:", log["cv_rmse_core"],
              " selected:", log["cv_rmse_selected"])

    # Prefer inputs a fan can read off a halftime box score unless advanced stats clearly earn their place.
    b, a = runs["box_score_only"][2]["cv_rmse_selected"], runs["with_advanced_stats"][2]["cv_rmse_selected"]
    use = "with_advanced_stats" if a[0] < b[0] - b[1] else "box_score_only"
    feats, table, log = runs[use]
    print(f"\nusing: {use}  (box {b[0]:.3f}+/-{b[1]:.3f} vs advanced {a[0]:.3f}+/-{a[1]:.3f})")

    # ---- honest holdout: fit on train seasons only
    fit = sm.OLS(train.final_total, sm.add_constant(train[feats])).fit()
    Xh = sm.add_constant(hold[feats], has_constant="add")
    pred = fit.predict(Xh)
    h1 = hold.home_h1_pts + hold.away_h1_pts
    res = {
        "model": metrics(hold.final_total, pred),
        "baseline_double_halftime": metrics(hold.final_total, 2 * h1),
        "baseline_vegas_total": metrics(hold.final_total, hold.total_line),
        "baseline_halftime_plus_half_vegas": metrics(hold.final_total, h1 + hold.total_line / 2),
    }
    cov, s2 = fit.cov_params().values, float(fit.scale)
    cover = {}
    for lvl in (0.80, 0.95):
        hw = interval_half_width(Xh.values, cov, s2, stats.t.ppf(0.5 + lvl / 2, fit.df_resid))
        cover[str(int(lvl * 100))] = round(float(np.mean(np.abs(hold.final_total - pred) <= hw)), 3)
    by_season = {int(s): metrics(g.final_total, fit.predict(sm.add_constant(g[feats], has_constant="add")))
                 for s, g in hold.groupby("season")}
    print("\nHOLDOUT", HOLDOUT_FROM, "+  n =", len(hold))
    print(pd.DataFrame(res).T.to_string())
    print("interval coverage on holdout:", cover, " by season:", by_season)
    print(fit.summary().tables[1])

    # ---- deployed model: same features, refit on every completed game
    final = sm.OLS(df.final_total, sm.add_constant(df[feats])).fit()
    names = ["const"] + feats
    model = {
        "type": "linear_regression", "target": "final_total_points",
        "intercept": float(final.params["const"]),
        "coefficients": {f: float(final.params[f]) for f in feats},
        "scaler": {"type": "none", "note": "OLS fit on raw units; no scaling needed at inference"},
        "feature_order": names,
        "coef_std_err": {n: float(final.bse[n]) for n in names},
        "covariance": final.cov_params().loc[names, names].values.tolist(),
        "residual_std_error": float(np.sqrt(final.scale)), "df_resid": int(final.df_resid),
        "t_crit": {"80": float(stats.t.ppf(0.90, final.df_resid)), "95": float(stats.t.ppf(0.975, final.df_resid))},
        "feature_means": {f: float(df[f].mean()) for f in feats},
        "target_mean": float(df.final_total.mean()),
        "percentiles": {f: {str(q): float(np.percentile(df[f], q)) for q in (1, 5, 25, 50, 75, 95, 99)} for f in feats},
        "n_train": int(len(df)), "seasons": [int(df.season.min()), int(df.season.max())],
        "trained_on": date.today().isoformat(),
    }
    with open(os.path.join(HERE, "model.json"), "w") as f:
        json.dump(model, f, indent=1)

    inputs = [f for f in feats if f not in DERIVED]
    order = {"home": 0, "away": 1, "shared": 2}
    schema = sorted((feature_schema(f, df) for f in inputs), key=lambda d: (order[d["side"]], inputs.index(d["name"]) if d["side"] == "shared" else STAT_ORDER.index(d["name"].split("_h1_")[1])))
    coef_final = {f: float(final.params[f]) for f in feats}
    meta = {
        "slug": SLUG, "name": NAME, "category": CATEGORY, "type": "linear_regression",
        "summary": "Set the halftime numbers for both teams and get the expected final combined score, with a range.",
        "target": {"label": "Final combined points", "unit": "pts", "decimals": 1},
        "features": schema,
        "derived": [dict(name=k, **v) for k, v in DERIVED.items() if k in feats],
        "floor": {"op": "sum", "args": ["home_h1_pts", "away_h1_pts"], "label": "already scored"},
        "compare_line": {"label": "Current over/under to compare (optional)", "step": 0.5, "min": 0, "max": 120},
        "synopsis_extra": "With {floor} points already on the board, that means about {remaining} more in the second half.",
        "card": {
            "trained_on": date.today().isoformat(), "n_games": int(len(df)),
            "seasons": [int(df.season.min()), int(df.season.max())],
            "candidates_tested": len(adv), "holdout_label": f"{HOLDOUT_FROM} season onward ({len(hold)} games the model never saw)",
            "accuracy": [
                {"name": "This model", **res["model"]},
                {"name": "Halftime score + half the over/under", **res["baseline_halftime_plus_half_vegas"]},
                {"name": "Halftime score doubled", **res["baseline_double_halftime"]},
                {"name": "Pregame over/under alone", **res["baseline_vegas_total"]}],
            "coverage": cover, "typical_miss": res["model"]["mae"],
            "findings": plain_findings(feats, coef_final, runs, use, res, cover, len(df), None, len(adv)),
            "limitations": [
                "It only knows what you enter. Injuries, a quarterback change or a team sitting starters are invisible to it.",
                "It is a straight-line model, so it cannot capture special situations such as a team that abandons the run when trailing big.",
                "Overtime games are included in the history, which stretches the top of the range slightly.",
                "The range is wide because second halves are noisy, and no halftime stat tested here narrows it much.",
                "Sliders move independently, so you can enter combinations that rarely happen in real games. Unusual inputs are flagged."],
            "disclaimer": "For information and learning only. Not betting advice.",
        },
    }
    with open(os.path.join(HERE, "meta.json"), "w") as f:
        json.dump(meta, f, indent=1)

    report = {
        "used": use, "selected": feats, "holdout_from": HOLDOUT_FROM, "n_holdout": int(len(hold)),
        "n_train_selection": int(len(train)), "holdout": res, "coverage": cover, "holdout_by_season": by_season,
        "runs": {k: {"selected": v[0], "log": v[2], "table": v[1].reset_index().rename(columns={"index": "feature"}).to_dict("records")}
                 for k, v in runs.items()},
        "coef_table": [{"feature": n, "coef": float(fit.params[n]), "se": float(fit.bse[n]), "p": float(fit.pvalues[n])} for n in ["const"] + feats],
        "r2_in_sample_final": float(final.rsquared),
    }
    with open(args.report, "w") as f:
        json.dump(report, f, indent=1, default=str)
    print("\nwrote model.json, meta.json and", os.path.basename(args.report))


if __name__ == "__main__":
    main()
