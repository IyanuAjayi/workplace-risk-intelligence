"""
Train and validate the risk models on the year-pair table, forward in time.

Split (by starting year t; the outcome is year t+1):
  train     2016 to 2021
  validate  2022          used once to pick model settings
  test      2023 and 2024 untouched until the final run; models are refit on 2016 to 2022 first

Models:
  M0 rating class      logistic regression on sector, size band, state and establishment type (what is known without
                       any injury history)
  M1 last year only    the site's current-year percentile within its industry
  M2 scorecard         logistic regression on binned injury history plus the rating-class fields
  M3 gradient boosting HistGradientBoostingClassifier on the same information

Outputs: outputs/model/*.csv, data/final/scores.parquet (test-year scores), models/*.joblib, docs/model-results.md

Usage: .venv/bin/python scripts/03_model.py
"""
import json
from pathlib import Path

import joblib
import numpy as np
import pandas as pd
from sklearn.compose import ColumnTransformer
from sklearn.ensemble import HistGradientBoostingClassifier
from sklearn.inspection import permutation_importance
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import average_precision_score, brier_score_loss, roc_auc_score
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import KBinsDiscretizer, OneHotEncoder, OrdinalEncoder

SEED = 42
FINAL, OUT, MODELS = Path("data/final"), Path("outputs/model"), Path("models")
DOC = Path("docs/model-results.md")
TRAIN, VALID, TESTS = range(2016, 2022), [2022], [2023, 2024]

CLASS = ["sector", "size_band", "state", "establishment_type"]
HISTORY = ["industry_pctile", "dart_rate", "dart_rate_2yr", "tcr_rate", "dafw_rate", "lost_days_rate", "dart_change",
           "log_hours"]
FLAGS = ["has_prev", "any_death", "top_band_now"]


def prepare(df):
    df = df.copy()
    df["log_hours"] = np.log10(df["hours"])
    df["any_death"] = (df["deaths"] > 0).astype(int)
    df["has_prev"] = df["has_prev"].astype(int)
    df["top_band_now"] = df["top_band_now"].astype(int)
    df["dart_change"] = df["dart_change"].fillna(0)
    df["establishment_type"] = df["establishment_type"].fillna(0).astype(int).astype(str)
    return df


def rating_class_model(C=1.0):
    pre = ColumnTransformer([("cat", OneHotEncoder(handle_unknown="ignore", min_frequency=50), CLASS)])
    return Pipeline([("pre", pre), ("lr", LogisticRegression(C=C, max_iter=2000))])


def scorecard(C=1.0, bins=10):
    pre = ColumnTransformer([
        ("bins", Pipeline([("kb", KBinsDiscretizer(n_bins=bins, encode="onehot", strategy="quantile", subsample=200_000,
                                                   random_state=SEED))]), HISTORY),
        ("cat", OneHotEncoder(handle_unknown="ignore", min_frequency=50), CLASS),
        ("flags", "passthrough", FLAGS)])
    return Pipeline([("pre", pre), ("lr", LogisticRegression(C=C, max_iter=3000))])


def boosting(lr=0.1, leaves=31):
    pre = ColumnTransformer([
        ("num", "passthrough", HISTORY + FLAGS),
        ("cat", OrdinalEncoder(handle_unknown="use_encoded_value", unknown_value=-1, encoded_missing_value=-1), CLASS)])
    n_num = len(HISTORY + FLAGS)
    cat_mask = [False] * n_num + [True] * len(CLASS)
    gb = HistGradientBoostingClassifier(learning_rate=lr, max_leaf_nodes=leaves, max_iter=400, early_stopping=True,
                                        validation_fraction=0.1, n_iter_no_change=20, categorical_features=cat_mask,
                                        random_state=SEED)
    return Pipeline([("pre", pre), ("gb", gb)])


def evaluate(y, p, name, split, top_share=0.20, n_boot=200):
    rng = np.random.default_rng(SEED)
    auc = roc_auc_score(y, p)
    boots = []
    idx = np.arange(len(y))
    for _ in range(n_boot):
        s = rng.choice(idx, len(idx))
        boots.append(roc_auc_score(y[s], p[s]))
    cut = np.quantile(p, 1 - top_share)
    flag = p >= cut
    tp, fp = int((flag & (y == 1)).sum()), int((flag & (y == 0)).sum())
    fn, tn = int((~flag & (y == 1)).sum()), int((~flag & (y == 0)).sum())
    prev = y.mean()
    top10 = p >= np.quantile(p, 0.9)
    return {"model": name, "split": split, "n": len(y), "prevalence": prev, "auc": auc,
            "auc_lo": np.quantile(boots, 0.025), "auc_hi": np.quantile(boots, 0.975), "gini": 2 * auc - 1,
            "avg_precision": average_precision_score(y, p), "brier": brier_score_loss(y, p),
            "precision_top20": tp / (tp + fp), "recall_top20": tp / (tp + fn), "lift_top20": (tp / (tp + fp)) / prev,
            "lift_top10": y[top10].mean() / prev, "tp": tp, "fp": fp, "fn": fn, "tn": tn}


def calibration(y, p, name, split):
    d = pd.DataFrame({"y": y, "p": p})
    d["decile"] = pd.qcut(d["p"].rank(method="first"), 10, labels=range(1, 11)).astype(int)
    g = d.groupby("decile").agg(n=("y", "size"), predicted=("p", "mean"), observed=("y", "mean")).reset_index()
    return g.assign(model=name, split=split)


def main():
    OUT.mkdir(parents=True, exist_ok=True)
    MODELS.mkdir(exist_ok=True)
    pairs = prepare(pd.read_parquet(FINAL / "pairs.parquet"))
    tr, va = pairs[pairs["year"].isin(TRAIN)], pairs[pairs["year"].isin(VALID)]
    ytr, yva = tr["target"].to_numpy(), va["target"].to_numpy()

    # Model selection on the validation year only
    choice = {}
    best = max(([C, roc_auc_score(yva, scorecard(C).fit(tr, ytr).predict_proba(va)[:, 1])] for C in (0.1, 1.0)),
               key=lambda r: r[1])
    choice["scorecard_C"] = best[0]
    best = max(([lr, lv, roc_auc_score(yva, boosting(lr, lv).fit(tr, ytr).predict_proba(va)[:, 1])]
                for lr, lv in ((0.05, 31), (0.1, 31), (0.1, 63))), key=lambda r: r[2])
    choice["boosting_lr"], choice["boosting_leaves"] = best[0], best[1]
    print("selected:", choice)

    # Refit on train + validate, then score the untouched test years once
    fit = pairs[pairs["year"].isin(list(TRAIN) + VALID)]
    yfit = fit["target"].to_numpy()
    models = {"M0 rating class": rating_class_model().fit(fit, yfit),
              "M2 scorecard": scorecard(choice["scorecard_C"]).fit(fit, yfit),
              "M3 gradient boosting": boosting(choice["boosting_lr"], choice["boosting_leaves"]).fit(fit, yfit)}
    for name, m in models.items():
        joblib.dump(m, MODELS / f"{name.split()[0]}.joblib")

    metrics, calib, scored = [], [], []
    for year in TESTS:
        te = pairs[pairs["year"] == year].copy()
        y = te["target"].to_numpy()
        preds = {"M1 last year only": te["industry_pctile"].to_numpy()}
        for name, m in models.items():
            preds[name] = m.predict_proba(te)[:, 1]
        for name, p in preds.items():
            metrics.append(evaluate(y, p, name, str(year)))
            if name != "M1 last year only":
                calib.append(calibration(y, p, name, str(year)))
        te["score_rating_class"] = preds["M0 rating class"]
        te["score_scorecard"] = preds["M2 scorecard"]
        te["score_boosting"] = preds["M3 gradient boosting"]
        scored.append(te)

    metrics = pd.DataFrame(metrics)
    calib = pd.concat(calib, ignore_index=True)
    scored = pd.concat(scored, ignore_index=True)
    metrics.to_csv(OUT / "metrics.csv", index=False)
    calib.to_csv(OUT / "calibration.csv", index=False)
    scored.to_parquet(FINAL / "scores.parquet", index=False)

    # Paired bootstrap: is the scorecard's AUC gain over last-year-only real?
    rng = np.random.default_rng(SEED)
    gains = []
    for year in TESTS:
        te = scored[scored["year"] == year]
        y, a, b = te["target"].to_numpy(), te["score_scorecard"].to_numpy(), te["industry_pctile"].to_numpy()
        diffs = []
        for _ in range(200):
            s = rng.integers(0, len(y), len(y))
            diffs.append(roc_auc_score(y[s], a[s]) - roc_auc_score(y[s], b[s]))
        gains.append({"year": year, "auc_gain": roc_auc_score(y, a) - roc_auc_score(y, b),
                      "lo": np.quantile(diffs, 0.025), "hi": np.quantile(diffs, 0.975)})
    gains = pd.DataFrame(gains)
    gains.to_csv(OUT / "scorecard_vs_last_year.csv", index=False)

    # Drivers: scorecard coefficients by feature group, and permutation importance for boosting on a 2023 sample
    te = scored[scored["year"] == TESTS[0]].sample(20_000, random_state=SEED)
    feats = CLASS + HISTORY + FLAGS
    imp = permutation_importance(models["M3 gradient boosting"], te[feats], te["target"], scoring="roc_auc", n_repeats=5,
                                 random_state=SEED)
    importance = pd.DataFrame({"feature": feats, "auc_drop": imp.importances_mean, "sd": imp.importances_std})
    importance.sort_values("auc_drop", ascending=False).to_csv(OUT / "importance_boosting.csv", index=False)
    (OUT / "model_choice.json").write_text(json.dumps(choice, indent=2))
    write_doc(metrics, gains, importance, choice, pairs)
    print(metrics[["model", "split", "auc", "gini", "precision_top20", "recall_top20", "lift_top10"]].round(3).to_string(index=False))


def write_doc(metrics, gains, importance, choice, pairs):
    m = metrics[["model", "split", "n", "prevalence", "auc", "auc_lo", "auc_hi", "gini", "avg_precision", "brier",
                 "precision_top20", "recall_top20", "lift_top10"]]
    lines = ["# Model results", "", "Generated by `scripts/03_model.py`. No figure here was looked at before the test run.", "",
             f"Training pairs (starting years 2016 to 2022): {pairs['year'].between(2016, 2022).sum():,}. "
             f"Test pairs: {', '.join(f'{y}: {(pairs.year == y).sum():,}' for y in TESTS)}.", "",
             f"Settings chosen on the 2022 validation year: {choice}.", "",
             "## Test-year performance", "",
             "`top20` treats the 20% highest-scored sites as flagged. AUC ranges are 95% bootstrap intervals.", "",
             m.to_markdown(index=False, floatfmt=".3f"), "",
             "## Scorecard against last year's rate alone (paired bootstrap)", "", gains.to_markdown(index=False, floatfmt=".4f"), "",
             "## What drives the gradient boosting model (permutation importance, 2023 sample)", "",
             importance.sort_values("auc_drop", ascending=False).to_markdown(index=False, floatfmt=".4f"), ""]
    DOC.write_text("\n".join(lines))


if __name__ == "__main__":
    main()
