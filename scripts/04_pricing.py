"""
Pricing experiment on the test years (simulated, not real premiums or losses).

Two layers, kept apart:
  injury risk   the model's probability that a site's next-year DART rate crosses the industry line
  claim cost    a stated assumption (docs/benchmarks.md) that turns DART cases into dollars afterwards

Private-sector sites only: BLS rates are private-industry rates, and public bodies are often self-insured.

Scenario A, industry only: every site in a 3-digit NAICS group pays the same rate per hour worked, set from the
  BLS DART rate for year t-1 (what an underwriter would have had), times the claim-cost assumption.
Scenario B, industry plus score: the same premium, re-spread within each industry by the site's risk relativity
  (its score divided by its industry's average score, capped), then rebalanced so every industry's total is unchanged.

Because both scenarios charge the same total and losses don't change, the overall loss ratio is identical by
construction. What changes is how well premium lines up with simulated losses band by band.

Usage: .venv/bin/python scripts/04_pricing.py [score_column]
"""
import sys
from pathlib import Path

import numpy as np
import pandas as pd

FINAL, OUT, BLS = Path("data/final"), Path("outputs/pricing"), Path("data/raw/bls")
DOC = Path("docs/pricing-results.md")
SECTOR_CODE = {"31": "31-33", "32": "31-33", "33": "31-33", "48": "48-49", "49": "48-49"}
AVG_CLAIM, FALLS_CLAIM = 50_076, 57_314
SCENARIOS = {"low": ("dafw", AVG_CLAIM), "central": ("dart", AVG_CLAIM), "high": ("dart", FALLS_CLAIM)}
CAP = (0.6, 2.0)
BANDS = ["1 lowest", "2", "3", "4", "5 highest"]


def bls_rates(year):
    b = pd.read_csv(BLS / f"table1_{year}.tsv", sep="\t", dtype=str)
    for c in ("dart", "dafw"):
        b[c] = pd.to_numeric(b[c], errors="coerce")
    # Table 1 lists private industry first, then state and then local government; keep the private-industry rows
    return b.drop_duplicates("naics", keep="first").set_index("naics")[["dart", "dafw"]]


def attach_bls(df):
    parts = []
    for year, grp in df.groupby("year"):
        r = bls_rates(year - 1)
        g = grp.copy()
        sector = g["sector2"].map(lambda s: SECTOR_CODE.get(s, s))
        for c in ("dart", "dafw"):
            own = g["naics3"].map(r[c])
            g[f"bls_{c}"] = own.fillna(sector.map(r[c]))
        g["bls_level"] = np.where(g["naics3"].map(r["dart"]).notna(), "naics3", "sector")
        parts.append(g)
    return pd.concat(parts)


def main(score_col="score_scorecard"):
    OUT.mkdir(parents=True, exist_ok=True)
    s = pd.read_parquet(FINAL / "scores.parquet")
    sy = pd.read_parquet(FINAL / "site_years.parquet", columns=["site_id", "year", "dafw_cases", "djtr_cases"])
    nxt = sy.assign(year=sy["year"] - 1).rename(columns={"dafw_cases": "dafw_next", "djtr_cases": "djtr_next"})
    s = s.merge(nxt, on=["site_id", "year"], how="left", validate="one_to_one")
    # Sites whose next-year NAICS left the industrial sectors aren't in site_years, so their case split is unknown
    split_missing = int(s["dafw_next"].isna().sum())
    s = s[s["dafw_next"].notna()].copy()
    gov = int((s["establishment_type"] != "1").sum())
    s = s[s["establishment_type"] == "1"].copy()
    assert np.allclose(s["dafw_next"] + s["djtr_next"], s["dart_cases_next"]), "next-year case split doesn't add up"
    s = attach_bls(s)
    no_bls = int(s["bls_dart"].isna().sum())
    s = s[s["bls_dart"].notna()].copy()
    print(f"excluded: {split_missing} pairs with no next-year case split, {gov} sites not marked private (government or no valid ownership code), {no_bls} with no BLS rate")

    s["p"] = s[score_col]
    s["band"] = pd.qcut(s["p"].rank(method="first"), 5, labels=BANDS)
    ind_mean = s.groupby(["year", "naics3"])["p"].transform("mean")
    s["relativity"] = (s["p"] / ind_mean).clip(*CAP)

    rows, sites = [], []
    for name, (kind, cost) in SCENARIOS.items():
        d = s.copy()
        rate = d[f"bls_{kind}"]
        d["premium_a"] = rate * d["hours_next"] / 200_000 * cost
        raw_b = d["premium_a"] * d["relativity"]
        d["premium_b"] = raw_b * d.groupby(["year", "naics3"])["premium_a"].transform("sum") / raw_b.groupby([d["year"], d["naics3"]]).transform("sum")
        cases = d["dafw_next"] if kind == "dafw" else d["dart_cases_next"]
        d["sim_loss"] = cases * cost
        assert np.isclose(d["premium_a"].sum(), d["premium_b"].sum())
        g = d.groupby(["year", "band"], observed=True).agg(
            sites=("p", "size"), predicted_risk=("p", "mean"), observed_crossing=("target", "mean"),
            premium_a=("premium_a", "sum"), premium_b=("premium_b", "sum"), sim_loss=("sim_loss", "sum")).reset_index()
        g["scenario"] = name
        g["ratio_a"] = g["sim_loss"] / g["premium_a"]
        g["ratio_b"] = g["sim_loss"] / g["premium_b"]
        g["premium_change"] = g["premium_b"] / g["premium_a"] - 1
        rows.append(g)
        if name == "central":
            sites = d
    bands = pd.concat(rows, ignore_index=True)
    bands.to_csv(OUT / "bands.csv", index=False)

    summ = []
    for (year, scen), g in bands.groupby(["year", "scenario"]):
        tot_a, tot_b, loss = g["premium_a"].sum(), g["premium_b"].sum(), g["sim_loss"].sum()
        share = lambda x: x / x.sum()
        summ.append({"year": year, "scenario": scen, "total_premium": tot_a, "total_premium_b": tot_b, "sim_loss": loss,
                     "overall_ratio_a": loss / tot_a, "overall_ratio_b": loss / tot_b,
                     "band_ratio_spread_a": g["ratio_a"].max() / g["ratio_a"].min(),
                     "band_ratio_spread_b": g["ratio_b"].max() / g["ratio_b"].min(),
                     "misallocated_share_a": (share(g["sim_loss"]) - share(g["premium_a"])).abs().sum() / 2,
                     "misallocated_share_b": (share(g["sim_loss"]) - share(g["premium_b"])).abs().sum() / 2})
    summ = pd.DataFrame(summ)
    summ.to_csv(OUT / "summary.csv", index=False)
    sites[["site_id", "year", "naics3", "sector", "state", "size_band", "hours_next", "p", "band", "relativity", "bls_dart",
           "bls_level", "premium_a", "premium_b", "sim_loss", "target"]].to_parquet(FINAL / "pricing_sites.parquet", index=False)
    write_doc(bands, summ, s, score_col)
    print(summ.round(3).to_string(index=False))


def write_doc(bands, summ, s, score_col):
    c = bands[bands["scenario"] == "central"][["year", "band", "sites", "predicted_risk", "observed_crossing", "premium_a",
                                                "premium_b", "premium_change", "sim_loss", "ratio_a", "ratio_b"]]
    lines = ["# Pricing results (simulated)", "",
             f"Generated by `scripts/04_pricing.py` using `{score_col}`. Test years only. Premiums and losses are simulations built from BLS industry rates, OSHA injury counts and the claim-cost scenarios in `docs/benchmarks.md`. They are not real premiums, claims or loss ratios.", "",
             f"BLS rate matched at 3-digit NAICS for {(s['bls_level'] == 'naics3').mean():.1%} of sites; the rest use their 2-digit sector. Relativity cap: {CAP[0]} to {CAP[1]}.", "",
             "## Summary", "",
             "The overall ratio of simulated loss to premium is the same under A and B by construction. The test is whether B lines premium up with losses better across bands: a smaller spread between bands, and a smaller share of premium sitting in the wrong band.", "",
             summ.to_markdown(index=False, floatfmt=".3f"), "",
             "## Central scenario by risk band", "",
             c.to_markdown(index=False, floatfmt=".3f"), ""]
    DOC.write_text("\n".join(lines))


if __name__ == "__main__":
    main(*sys.argv[1:])
