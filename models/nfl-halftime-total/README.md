# NFL halftime to final total

Linear regression that predicts final combined points from what is known at halftime.

## Retrain

    pip install pandas pyarrow numpy scipy scikit-learn statsmodels
    python train.py

The script downloads nflverse play-by-play (one parquet per season, about 500 MB in total) into `data_cache/`, rebuilds the dataset, reruns feature selection and rewrites `model.json`, `meta.json` and `training_report.json`. Commit those three files and Render redeploys. Do not commit `data_cache/`.

Options: `--data-dir DIR` to reuse downloaded files, `--last-season 2026` to set the latest season.

It takes about three minutes after the download. Retrain weekly in season if you want the newest games included.

## What the script does

1. Builds one row per game from first-half plays only (quarters 1 and 2), plus pregame context. Nothing from the second half is used as an input.
2. Screens out near-duplicate stats (variance inflation above 10).
3. Scores each candidate four ways: lasso with season-ordered cross-validation, stability selection over 300 half-samples, recursive feature elimination, and permutation importance on later seasons.
4. Keeps stats with at least three of four votes, then adds weaker ones only if they lower error in at least five of six forward-in-time folds. Team stats are always kept for both teams.
5. Repeats with advanced stats (EPA, success rate) and uses them only if they clearly beat box-score stats.
6. Fits ordinary least squares on seasons before 2025 and reports error on 2025 onward against three baselines.
7. Refits on every game for the deployed model.

`training_report.json` holds the full vote table, cross-validation numbers and holdout results from the last run.
