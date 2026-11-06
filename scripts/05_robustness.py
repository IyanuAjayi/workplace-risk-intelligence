"""
Robustness checks for the scorecard (M2). Each check answers one question a reviewer would ask.

  1. Linked vs unlinked: are sites we can follow into next year different from those we can't?
  2. ID-only links: do results hold if the backup name/zip/NAICS match is dropped?
  3. Alternative target: does the ranking hold if "high risk" means next year's own top 20%?
  4. Without the COVID years: does excluding pairs touching 2020 change the test result?
  5. Subgroups: how does performance vary by sector and size?

Outputs: outputs/model/robustness_*.csv and docs/robustness.md
Usage: .venv/bin/python scripts/05_robustness.py
"""
import importlib.util
from pathlib import Path

import joblib
import numpy as np
import pandas as pd
from sklearn.metrics import roc_auc_score

spec = importlib.util.spec_from_file_location("m", Path(__file__).with_name("03_model.py"))
m = importlib.util.module_from_spec(spec)
spec.loader.exec_module(m)

FINAL, OUT, DOC = Path("data/final"), Path("outputs/model"), Path("docs/robustness.md")
FIT_YEARS = list(m.TRAIN) + m.VALID


def auc(y, p):
    return roc_auc_score(y, p) if len(np.unique(y)) == 2 else np.nan


def main():
    pairs = m.prepare(pd.read_parquet(FINAL / "pairs.parquet"))
    sy = pd.read_parquet(FINAL / "site_years.parquet", columns=["site_id", "year", "in_cohort", "naics3", "sector", "size_band",
                                                                 "hours", "dart_rate", "threshold"])
    C = float(m.json.loads((OUT / "model_choice.json").read_text())["scorecard_C"])
    full = joblib.load("models/M2.joblib")
    test = pairs[pairs["year"].isin(m.TESTS)].copy()
    test["p"] = full.predict_proba(test)[:, 1]

    # 1. Linked vs unlinked, cohort sites in 2016 to 2024
    c = sy[sy["in_cohort"] & (sy["year"] <= 2024)].copy()
    nxt = set(zip(sy["site_id"], sy["year"] - 1))
    c["linked"] = [k in nxt for k in zip(c["site_id"], c["year"])]
    c["top_band_now"] = c["dart_rate"] > c["threshold"]
    link = c.groupby("linked").agg(sites=("site_id", "size"), mean_dart_rate=("dart_rate", "mean"),
                                   share_top_band=("top_band_now", "mean"), share_250_plus=("size_band", lambda s: (s == "250+").mean()),
                                   median_hours=("hours", "median")).reset_index()
    by_sector = c.groupby("sector")["linked"].mean().rename("link_rate").reset_index()
    link.to_csv(OUT / "robustness_linked.csv", index=False)
    by_sector.to_csv(OUT / "robustness_link_by_sector.csv", index=False)

    # 2. ID-only links: refit on ID-linked pairs, compare on ID-linked test pairs
    fit = pairs[pairs["year"].isin(FIT_YEARS)]
    id_fit = fit[fit["method"] == "id"]
    id_model = m.scorecard(C).fit(id_fit, id_fit["target"])
    rows = []
    for year in m.TESTS:
        t = test[test["year"] == year]
        tid = t[t["method"] == "id"]
        tkey = t[t["method"] == "key"]
        rows.append({"year": year, "auc_all_pairs": auc(t["target"], t["p"]),
                     "auc_id_pairs_full_model": auc(tid["target"], tid["p"]),
                     "auc_id_pairs_id_model": auc(tid["target"], id_model.predict_proba(tid)[:, 1]),
                     "auc_key_pairs_full_model": auc(tkey["target"], tkey["p"]),
                     "key_pairs": len(tkey), "key_prevalence": tkey["target"].mean(), "id_prevalence": tid["target"].mean()})
    ids = pd.DataFrame(rows)
    ids.to_csv(OUT / "robustness_id_only.csv", index=False)

    # 3. Alternative target: next year's own 80th percentile within the industry
    thr = (sy[sy["in_cohort"]].groupby(["year", "naics3"])["threshold"].first().rename("threshold_next").reset_index())
    thr["year"] -= 1
    t3 = test.merge(thr, on=["year", "naics3"], how="left")
    t3["target_alt"] = (t3["dart_rate_next"] > t3["threshold_next"]).astype(int)
    alt = []
    for year, g in t3.groupby("year"):
        g = g[g["threshold_next"].notna()]
        alt.append({"year": year, "pairs": len(g), "prevalence_main": g["target"].mean(), "prevalence_alt": g["target_alt"].mean(),
                    "agreement": (g["target"] == g["target_alt"]).mean(),
                    "auc_main": auc(g["target"], g["p"]), "auc_alt": auc(g["target_alt"], g["p"])})
    alt = pd.DataFrame(alt)
    alt.to_csv(OUT / "robustness_alt_target.csv", index=False)

    # 4. Without the COVID years: drop pairs whose features or outcome fall in 2020
    nc_fit = fit[~fit["year"].isin([2019, 2020])]
    nc_model = m.scorecard(C).fit(nc_fit, nc_fit["target"])
    covid = pd.DataFrame([{"year": y, "auc_full": auc(g["target"], g["p"]),
                           "auc_without_2020": auc(g["target"], nc_model.predict_proba(g)[:, 1])}
                          for y, g in test.groupby("year")])
    covid.to_csv(OUT / "robustness_covid.csv", index=False)

    # 5. Subgroups on the first test year
    t1 = test[test["year"] == m.TESTS[0]]
    sub = pd.concat([
        t1.groupby("sector").apply(lambda g: pd.Series({"pairs": len(g), "prevalence": g["target"].mean(), "auc": auc(g["target"], g["p"])})).reset_index().rename(columns={"sector": "group"}).assign(kind="sector"),
        t1.groupby("size_band").apply(lambda g: pd.Series({"pairs": len(g), "prevalence": g["target"].mean(), "auc": auc(g["target"], g["p"])})).reset_index().rename(columns={"size_band": "group"}).assign(kind="size")])
    sub.to_csv(OUT / "robustness_subgroups.csv", index=False)

    lines = ["# Robustness checks (scorecard)", "", "Generated by `scripts/05_robustness.py`.", "",
             "## 1. Sites we can follow into next year vs those we can't (cohort, 2016 to 2024)", "", link.to_markdown(index=False, floatfmt=".3f"), "",
             by_sector.to_markdown(index=False, floatfmt=".3f"), "",
             "## 2. Stable IDs only vs IDs plus the backup match", "", ids.to_markdown(index=False, floatfmt=".3f"), "",
             "## 3. Alternative target: next year's own top 20%", "", alt.to_markdown(index=False, floatfmt=".3f"), "",
             "## 4. Without pairs touching 2020", "", covid.to_markdown(index=False, floatfmt=".3f"), "",
             f"## 5. By sector and size ({m.TESTS[0]})", "", sub.to_markdown(index=False, floatfmt=".3f"), ""]
    DOC.write_text("\n".join(lines))
    print("\n".join(lines))


if __name__ == "__main__":
    main()
