"""
ROC and precision-recall curve points for the four models on the test years, from the saved scores
(data/final/scores.parquet). No model is refit, so nothing here can leak information from the test years.

Writes outputs/model/roc_curve.csv and outputs/model/pr_curve.csv, each thinned to about 200 points per model and
year so Power BI can draw them as lines. Checks that the AUC from the thinned curve matches the full-resolution AUC.

Usage: .venv/bin/python scripts/08_curves.py
"""
from pathlib import Path

import numpy as np
import pandas as pd
from sklearn.metrics import auc, precision_recall_curve, roc_auc_score, roc_curve

FINAL, OUT = Path("data/final"), Path("outputs/model")
MODELS = {"Rating class only": "score_rating_class", "Last year's rate": "industry_pctile",
          "Scorecard": "score_scorecard", "Gradient boosting": "score_boosting"}
POINTS = 200


def thin(x, y, n=POINTS):
    """Keep points evenly spaced along the curve's length so the shape survives at any zoom."""
    d = np.r_[0, np.cumsum(np.hypot(np.diff(x), np.diff(y)))]
    keep = np.unique(np.searchsorted(d, np.linspace(0, d[-1], n)).clip(0, len(x) - 1))
    return x[keep], y[keep]


def main():
    s = pd.read_parquet(FINAL / "scores.parquet")
    roc_rows, pr_rows = [], []
    for year, g in s.groupby("year"):
        y = g["target"].to_numpy()
        for name, col in MODELS.items():
            p = g[col].to_numpy()
            fpr, tpr, _ = roc_curve(y, p)
            full = roc_auc_score(y, p)
            fx, ty = thin(fpr, tpr)
            assert abs(auc(fx, ty) - full) < 0.002, f"thinned ROC drifts from full AUC for {name} {year}"
            roc_rows += [{"Model": name, "Test year": year, "False positive rate": a, "True positive rate": b} for a, b in zip(fx, ty)]
            prec, rec, _ = precision_recall_curve(y, p)
            order = np.argsort(rec)
            rx, py = thin(rec[order], prec[order])
            pr_rows += [{"Model": name, "Test year": year, "Recall": a, "Precision": b} for a, b in zip(rx, py)]
            print(f"{year} {name}: AUC {full:.4f}, thinned {auc(fx, ty):.4f}, {len(fx)} ROC points")
    pd.DataFrame(roc_rows).round(5).to_csv(OUT / "roc_curve.csv", index=False)
    pd.DataFrame(pr_rows).round(5).to_csv(OUT / "pr_curve.csv", index=False)


if __name__ == "__main__":
    main()
