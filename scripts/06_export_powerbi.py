"""
Power BI extract. No new analysis happens here: every value is renamed or rounded from the tables written by
02_build_panel.py, 03_model.py, 04_pricing.py, 08_curves.py and 09_landscape.py, so the report can only show numbers
the scripts produced.

Writes outputs/powerbi/workplace_risk_powerbi.xlsx, one Excel table per sheet (the Power BI service only imports
Excel data formatted as a table):
  Sites           priced test-year sites (private sector, BLS rate matched), central claim-cost scenario, aggregated
                  to one row per score year, sector, state, size band and risk band (no site-level rows)
  Models          test-year metrics for the four models, including the top-20% confusion counts
  Calibration     predicted against observed share by score decile, per model and test year
  Drivers         permutation importance for the gradient boosting model
  ROC             ROC curve points per model and test year
  PrecisionRecall precision-recall curve points per model and test year
  PricingBands    premium and simulated loss by risk band, every claim-cost scenario
  PricingSummary  the band-alignment measures per year and scenario
  Robustness      the robustness and subgroup AUCs shown on Model Trust, at their published precision
  ModelPicker, TestYearPicker, ScoreYears, ClaimCostScenarios, TestYears, Bands, StateGrid
                  small lookup tables behind the report's slicers, band colours and the state tile map
  About           source, cohort rules and the labels every page footer must carry

Also writes outputs/powerbi/expected_values.csv: the figures each DAX measure should return, for checking.
"""
from pathlib import Path

import pandas as pd
from openpyxl.worksheet.table import Table, TableStyleInfo

FINAL, MODEL, PRICING, LANDSCAPE = Path("data/final"), Path("outputs/model"), Path("outputs/pricing"), Path("outputs/landscape")
OUT = Path("outputs/powerbi")
WORKBOOK = OUT / "workplace_risk_powerbi.xlsx"

SITE_COLUMNS = {
    "site_key": "Site key",
    "year": "Score year",
    "outcome_year": "Outcome year",
    "sector": "Sector",
    "naics3": "NAICS 3-digit",
    "state": "State",
    "size_band": "Size band",
    "dart_rate": "DART rate this year",
    "dart_rate_next": "DART rate next year",
    "industry_line": "Industry line",
    "target": "Crossed line next year",
    "p": "Risk score",
    "band": "Risk band",
    "decile": "Risk decile",
    "relativity": "Relativity",
    "hours_next": "Hours worked next year",
    "premium_a": "Premium A industry only",
    "premium_b": "Premium B with score",
    "sim_loss": "Simulated loss",
}
MODEL_NAMES = {"M0 rating class": "Rating class only", "M1 last year only": "Last year's rate",
               "M2 scorecard": "Scorecard", "M3 gradient boosting": "Gradient boosting"}
MODEL_ORDER = {name: i for i, name in enumerate(MODEL_NAMES.values(), start=1)}
MODEL_INPUTS = {"Rating class only": "Sector, size band, state and ownership",
                "Last year's rate": "This year's DART rank in its industry",
                "Scorecard": "Banded injury history plus the rating-class fields",
                "Gradient boosting": "The same information in decision trees"}
BAND_ORDER = {"1 lowest": 1, "2": 2, "3": 3, "4": 4, "5 highest": 5}
BAND_LABEL = {1: "Band 1, lowest", 2: "Band 2", 3: "Band 3", 4: "Band 4", 5: "Band 5, highest"}
BAND_COLOUR = {1: "#C9D6BD", 2: "#D1A76A", 3: "#C98369", 4: "#A96247", 5: "#944126"}  # docs/design-system.md
SECTOR_ORDER = ["Manufacturing", "Construction", "Transport and warehousing", "Wholesale", "Utilities", "Agriculture",
                "Mining, oil and gas"]  # by portfolio site-years
SIZE_LABEL = {"20-249": ("20 to 249 employees", 1), "250+": ("250+ employees", 2)}
DRIVER_NAMES = {"industry_pctile": "DART rank in industry", "log_hours": "Hours worked", "tcr_rate": "Total case rate",
                "dart_change": "Change on last year", "top_band_now": "Above the line now",
                "dart_rate_2yr": "Two-year DART rate", "dart_rate": "DART rate", "sector": "Sector", "state": "State",
                "has_prev": "Has a prior year", "lost_days_rate": "Lost-days rate", "dafw_rate": "Days-away rate",
                "size_band": "Size band", "any_death": "Any death", "establishment_type": "Ownership"}
# claim-cost scenarios as in scripts/04_pricing.py and docs/benchmarks.md
SCENARIOS = [("low", "Low", "Days-away cases", 50_076, "NCCI average lost-time claim, accidents 2023 to 2024"),
             ("central", "Central", "DART cases", 50_076, "NCCI average lost-time claim, accidents 2023 to 2024"),
             ("high", "High", "DART cases", 57_314, "NCCI average for falls or slips, accidents 2023 to 2024")]


def sites():
    p = pd.read_parquet(FINAL / "pricing_sites.parquet")
    s = pd.read_parquet(FINAL / "scores.parquet", columns=["site_id", "year", "dart_rate", "dart_rate_next", "threshold"])
    d = p.merge(s, on=["site_id", "year"], how="left", validate="one_to_one")
    assert d["dart_rate"].notna().all(), "every priced site should have a score row"
    # An anonymous key instead of OSHA's establishment ID: no site can be looked up from the report
    d["site_key"] = pd.factorize(d["site_id"])[0] + 1
    d["outcome_year"] = d["year"] + 1
    d["industry_line"] = d["threshold"]
    d["band"] = d["band"].astype(str)
    d["decile"] = pd.qcut(d["p"].rank(method="first"), 10, labels=range(1, 11)).astype(int)
    out = d[list(SITE_COLUMNS)].rename(columns=SITE_COLUMNS)
    out["Band order"] = out["Risk band"].map(BAND_ORDER)
    for c in ("DART rate this year", "DART rate next year", "Industry line"):
        out[c] = out[c].round(3)
    for c in ("Risk score", "Relativity"):
        out[c] = out[c].round(5)
    for c in ("Hours worked next year", "Premium A industry only", "Premium B with score", "Simulated loss"):
        out[c] = out[c].round(0)
    return out


def site_groups(site):
    """One row per score year, sector, state, size band and risk band. Every report measure is a sum or a ratio of sums,
    so the totals are unchanged, the file stays small, and no individual site appears in the report data."""
    keys = ["Score year", "Outcome year", "Sector", "State", "Size band", "Risk band", "Band order"]
    g = site.groupby(keys, observed=True).agg(**{
        "Site count": ("Site key", "size"),
        "Crossing sites": ("Crossed line next year", "sum"),
        "DART rate sum": ("DART rate this year", "sum"),
        "Premium A industry only": ("Premium A industry only", "sum"),
        "Premium B with score": ("Premium B with score", "sum"),
        "Simulated loss": ("Simulated loss", "sum")}).reset_index()
    g["DART rate sum"] = g["DART rate sum"].round(3)
    g["Sector order"] = g["Sector"].map({s: i for i, s in enumerate(SECTOR_ORDER, 1)})
    g["Size band label"] = g["Size band"].map(lambda b: SIZE_LABEL[b][0])
    g["Size order"] = g["Size band"].map(lambda b: SIZE_LABEL[b][1])
    assert g[["Sector order", "Size order"]].notna().all().all(), "unexpected sector or size band"
    return g


def models():
    m = pd.read_csv(MODEL / "metrics.csv")
    m["model"] = m["model"].map(MODEL_NAMES)
    m["Model order"] = m["model"].map(MODEL_ORDER)
    return m.rename(columns={
        "model": "Model", "split": "Test year", "n": "Sites", "prevalence": "Base rate", "auc": "AUC",
        "auc_lo": "AUC low", "auc_hi": "AUC high", "gini": "Gini", "avg_precision": "Average precision",
        "brier": "Brier score", "precision_top20": "Precision top 20%", "recall_top20": "Capture top 20%",
        "lift_top20": "Lift top 20%", "lift_top10": "Lift top 10%", "tp": "Flagged and crossed",
        "fp": "Flagged, did not cross", "fn": "Missed", "tn": "Not flagged, did not cross"})


def calibration():
    c = pd.read_csv(MODEL / "calibration.csv")
    c["model"] = c["model"].map(MODEL_NAMES)
    c["Model order"] = c["model"].map(MODEL_ORDER)
    return c.rename(columns={"decile": "Score decile", "n": "Sites", "predicted": "Predicted share",
                             "observed": "Observed share", "model": "Model", "split": "Test year"})


def drivers():
    d = pd.read_csv(MODEL / "importance_boosting.csv")
    d["Driver"] = d["feature"].map(DRIVER_NAMES)
    assert d["Driver"].notna().all(), "every model input needs a plain name"
    return d.rename(columns={"feature": "Feature", "auc_drop": "AUC drop", "sd": "Spread"})


def robustness():
    """Scorecard AUCs from 05_robustness.py, stored at three decimals as docs/verified-metrics.md publishes them, so
    no report format can round them across a boundary."""
    covid = pd.read_csv(MODEL / "robustness_covid.csv").set_index("year")
    ids = pd.read_csv(MODEL / "robustness_id_only.csv").set_index("year")
    alt = pd.read_csv(MODEL / "robustness_alt_target.csv").set_index("year")
    sub = pd.read_csv(MODEL / "robustness_subgroups.csv")
    agree = alt["agreement"]
    rows = [("Check", "All test pairs", covid["auc_full"], "Scorecard on all test pairs"),
            ("Check", "Without 2020", covid["auc_without_2020"], "Trained without the 2020 starting year"),
            ("Check", "Stable-ID links only", ids["auc_id_pairs_id_model"], "Model rebuilt on pairs linked by OSHA ID alone"),
            ("Check", "Next year's own top 20%", alt["auc_alt"],
             f"Alternative target; agrees with the main target on {agree[2023]:.1%} (2023) and {agree[2024]:.1%} (2024) of sites")]
    out = [{"Group": g, "Label": label, "AUC 2023": round(s[2023], 3), "AUC 2024": round(s[2024], 3), "Note": note}
           for g, label, s, note in rows]
    sizes = {"20-249": "20 to 249 employees", "250+": "250+ employees"}
    # sectors by AUC, then sizes smallest first
    by_sector = sub[sub["kind"] == "sector"].sort_values("auc", ascending=False)
    by_size = sub[sub["kind"] != "sector"].sort_values("group", key=lambda g: g.map({"20-249": 1, "250+": 2}))
    for r in pd.concat([by_sector, by_size]).itertuples():
        out.append({"Group": "Sector" if r.kind == "sector" else "Size", "Label": sizes.get(r.group, r.group),
                    "AUC 2023": round(r.auc, 3), "AUC 2024": None, "Note": f"Scorecard, 2023 test, {int(r.pairs):,} pairs"})
    t = pd.DataFrame(out)
    t["Group order"] = t["Group"].map({"Check": 1, "Sector": 2, "Size": 3})
    t = t.sort_values(["Group order"], kind="stable").reset_index(drop=True)
    t.insert(0, "Row order", range(1, len(t) + 1))
    return t.drop(columns="Group order")


def lookups(mod):
    """Small tables behind the slicers. Pickers are related to the curve and pricing tables in Power BI, never to
    Models, so comparison tables keep every row."""
    picker = pd.DataFrame({"Model": list(MODEL_ORDER), "Model order": list(MODEL_ORDER.values())})
    picker["Has calibration"] = picker["Model"] != "Last year's rate"
    picker["Inputs"] = picker["Model"].map(MODEL_INPUTS)
    years = mod.groupby("Test year", as_index=False)["Sites"].max().rename(columns={"Sites": "Test pairs"})
    years["Outcome year"] = years["Test year"] + 1
    years["Tile label"] = years["Test year"].astype(str) + ", outcome " + years["Outcome year"].astype(str)
    score_years = years[["Test year", "Outcome year", "Tile label"]].rename(columns={"Test year": "Score year"})
    scen = pd.DataFrame(SCENARIOS, columns=["Scenario key", "Scenario", "Cases priced", "Claim cost per case", "Claim-cost source"])
    scen["Scenario order"] = range(1, len(scen) + 1)
    scen["Rule"] = scen["Cases priced"] + " × $" + scen["Claim cost per case"].map("{:,}".format)
    # "2023 + 2024" maps to both score years (many-to-many with Sites), so one tile slicer offers pooled or single years
    test_years = pd.DataFrame({"Test year": ["2023 + 2024", "2023 + 2024", "2023", "2024"], "Score year": [2023, 2024, 2023, 2024],
                               "Sort order": [1, 1, 2, 3]})
    test_years["Tile label"] = test_years["Test year"].map(
        {"2023 + 2024": "2023 + 2024", "2023": "2023, outcome 2024", "2024": "2024, outcome 2025"})
    bands = pd.DataFrame({"Risk band": list(BAND_ORDER), "Band order": list(BAND_ORDER.values())})
    bands["Band label"] = bands["Band order"].map(BAND_LABEL)
    bands["Band label long"] = bands["Band label"].str.replace("lowest", "lowest fifth").str.replace("highest", "highest fifth")
    bands["Band colour"] = bands["Band order"].map(BAND_COLOUR)
    bands["Band text colour"] = bands["Band order"].map(lambda b: "#FFFFFF" if b == 5 else "#000000")
    grid = pd.read_csv(LANDSCAPE / "state_grid.csv")
    return (picker, years[["Test year", "Outcome year", "Tile label", "Test pairs"]], score_years, scen, test_years, bands,
            grid)


def curves():
    roc, pr = pd.read_csv(MODEL / "roc_curve.csv"), pd.read_csv(MODEL / "pr_curve.csv")
    for c in (roc, pr):
        c["Model order"] = c["Model"].map(MODEL_ORDER)
        assert c["Model order"].notna().all(), "curve model names should match the Models sheet"
    return roc, pr


def pricing():
    b = pd.read_csv(PRICING / "bands.csv")
    b["Band order"] = b["band"].map(BAND_ORDER)
    b = b.rename(columns={
        "year": "Score year", "band": "Risk band", "sites": "Sites", "predicted_risk": "Predicted risk",
        "observed_crossing": "Observed crossing", "premium_a": "Premium A industry only",
        "premium_b": "Premium B with score", "sim_loss": "Simulated loss", "scenario": "Claim-cost scenario",
        "ratio_a": "Loss ratio A", "ratio_b": "Loss ratio B", "premium_change": "Premium change"})
    s = pd.read_csv(PRICING / "summary.csv").rename(columns={
        "year": "Score year", "scenario": "Claim-cost scenario", "total_premium": "Total premium",
        "total_premium_b": "Total premium B", "sim_loss": "Simulated loss", "overall_ratio_a": "Overall ratio A",
        "overall_ratio_b": "Overall ratio B", "band_ratio_spread_a": "Band spread A",
        "band_ratio_spread_b": "Band spread B", "misallocated_share_a": "Misallocated share A",
        "misallocated_share_b": "Misallocated share B"})
    # Repeat the band-alignment measures on every band row, so one pair of slicers (year, scenario) drives the whole page
    keep = ["Score year", "Claim-cost scenario", "Band spread A", "Band spread B", "Misallocated share A", "Misallocated share B"]
    b = b.merge(s[keep], on=["Score year", "Claim-cost scenario"], how="left", validate="many_to_one")
    b["Band label"] = b["Band order"].map(BAND_LABEL)
    b["Band short"] = "Band " + b["Band order"].astype(str)
    scen = {key: (name, order, f"{cases} × ${cost:,}") for order, (key, name, cases, cost, _) in enumerate(SCENARIOS, 1)}
    s["Scenario"] = s["Claim-cost scenario"].map(lambda k: scen[k][0])
    s["Scenario order"] = s["Claim-cost scenario"].map(lambda k: scen[k][1])
    s["Rule"] = s["Claim-cost scenario"].map(lambda k: scen[k][2])
    return b, s


def about(n_sites, n_test):
    return pd.DataFrame({
        "Item": ["Source", "Population", "Sites table", "Model tables", "Target", "Risk score", "Risk band",
                 "Pricing", "Claim cost", "Not", "Footer", "Rebuilt by"],
        "Value": [
            "OSHA Injury Tracking Application (ITA) Form 300A summary data, 2016 to 2025 (osha.gov/itadata)",
            "Industrial establishments that report to ITA; small sites below the reporting thresholds are not in the data",
            f"{n_sites:,} private-sector sites in the 2023 and 2024 test years with a matched BLS industry rate",
            f"{n_test:,} test-year sites (2023 and 2024), including public-sector sites",
            "Next year's DART rate crosses the site's industry line (top band for its industry)",
            "Scorecard model (M2), trained on 2016 to 2022, never fitted on the test years",
            "Quintiles of the risk score across both test years",
            "Simulated: Scenario A prices by BLS industry rate, Scenario B re-spreads the same total by risk score",
            "Low, central and high scenarios in docs/benchmarks.md",
            "Simulated pricing, not actual premiums, claims or loss ratios",
            "Source: OSHA ITA 300A 2016 to 2025. Test years 2023 and 2024. Simulated pricing, not actual premiums or losses.",
            "scripts/02_build_panel.py, 03_model.py, 04_pricing.py, then 06_export_powerbi.py",
        ],
    })


def expected(site, mod, bands, summ):
    """The value each measure in outputs/powerbi/measures.dax should return with no slicers applied."""
    top = site[site["Risk band"] == "5 highest"]
    base = site["Crossed line next year"].mean()
    central = bands[bands["Claim-cost scenario"] == "central"]
    gb = mod[mod["Model"] == "Gradient boosting"]
    rows = [
        ("Sites", len(site)),
        ("Sites crossing next year", int(site["Crossed line next year"].sum())),
        ("Base rate", base),
        ("Top band hit rate", top["Crossed line next year"].mean()),
        ("Top band capture", top["Crossed line next year"].sum() / site["Crossed line next year"].sum()),
        ("Top band lift", top["Crossed line next year"].mean() / base),
        ("Share of sites in top band", len(top) / len(site)),
        ("Average site DART rate", site["DART rate this year"].mean()),
        ("Premium A (Sites, central)", site["Premium A industry only"].sum()),
        ("Premium B (Sites, central)", site["Premium B with score"].sum()),
        ("Simulated loss (Sites, central)", site["Simulated loss"].sum()),
        ("Premium A (PricingBands, central)", central["Premium A industry only"].sum()),
        ("Simulated loss (PricingBands, central)", central["Simulated loss"].sum()),
        ("Top band premium change (central, both years)",
         central.loc[central["Risk band"] == "5 highest", "Premium B with score"].sum()
         / central.loc[central["Risk band"] == "5 highest", "Premium A industry only"].sum() - 1),
        ("Gradient boosting AUC 2023", float(gb.loc[gb["Test year"] == 2023, "AUC"].iloc[0])),
        ("Gradient boosting AUC 2024", float(gb.loc[gb["Test year"] == 2024, "AUC"].iloc[0])),
        ("Misallocated share A (central 2023)",
         float(summ.query("`Score year` == 2023 and `Claim-cost scenario` == 'central'")["Misallocated share A"].iloc[0])),
        ("Misallocated share B (central 2023)",
         float(summ.query("`Score year` == 2023 and `Claim-cost scenario` == 'central'")["Misallocated share B"].iloc[0])),
    ]
    return pd.DataFrame(rows, columns=["Measure", "Expected value"])


def main():
    OUT.mkdir(parents=True, exist_ok=True)
    site = sites()
    mod, cal, drv = models(), calibration(), drivers()
    roc, pr = curves()
    bands, summ = pricing()
    picker, test_years, score_years, scenarios, pooled_years, bands_lookup, grid = lookups(mod)
    n_test = int(mod.loc[mod["Model"] == "Rating class only", "Sites"].sum())
    sheets = {
        "Sites": site_groups(site), "Models": mod, "Calibration": cal, "Drivers": drv, "ROC": roc,
        "PrecisionRecall": pr, "PricingBands": bands, "PricingSummary": summ, "Robustness": robustness(),
        "ModelPicker": picker, "TestYearPicker": test_years, "ScoreYears": score_years,
        "ClaimCostScenarios": scenarios, "TestYears": pooled_years, "Bands": bands_lookup, "StateGrid": grid,
        "About": about(len(site), n_test),
    }
    with pd.ExcelWriter(WORKBOOK, engine="openpyxl") as xl:
        for name, frame in sheets.items():
            frame.to_excel(xl, sheet_name=name, index=False)
            ws = xl.sheets[name]
            ws.add_table(Table(displayName=name, ref=ws.dimensions,
                               tableStyleInfo=TableStyleInfo(name="TableStyleLight1", showRowStripes=True)))
    exp = expected(site, mod, bands, summ)
    exp.to_csv(OUT / "expected_values.csv", index=False)
    print(f"Written {WORKBOOK}: {len(site):,} sites, {len(mod)} model rows, {len(bands)} pricing rows")
    print(exp.to_string(index=False))


if __name__ == "__main__":
    main()
