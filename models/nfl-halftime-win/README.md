# NFL halftime win probability

Logistic regression that gives the home team's chance of winning from what is known at halftime.

## Retrain

    pip install pandas pyarrow numpy scipy scikit-learn statsmodels
    python train.py

This script imports the dataset builder from `../nfl-halftime-total/train.py`, so keep both folders. By default it reuses that model's `data_cache/`. It rewrites `model.json`, `meta.json` and `training_report.json`. Commit those three files and Render redeploys.

Options: `--data-dir DIR`, `--last-season 2026`.

## What the script does

1. Builds one row per game from first-half plays only, plus pregame context. Ties are dropped.
2. Screens out near-duplicate stats (variance inflation above 10).
3. Scores each candidate four ways: L1 logistic regression with season-ordered cross-validation, stability selection over 300 half-samples, recursive feature elimination, and permutation importance on later seasons.
4. Keeps stats with at least three of four votes, then adds weaker ones only if they lower log loss in at least five of six forward-in-time folds.
5. Repeats with advanced stats and uses them only if they clearly win.
6. Fits on seasons before 2025 and reports accuracy, precision, recall, specificity, ROC AUC, Brier score and calibration on 2025 onward, against two simple picks.
7. Refits on every game for the deployed model.
