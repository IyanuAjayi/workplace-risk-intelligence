"""
Build the linked site panel and the year-pair modelling table.

Steps, each counted in outputs/panel/funnel.csv:
  1. Read and standardise every year (src/osha.py). EIN and street address are not carried forward.
  2. Within a year, keep one record per establishment_ID: the most recent submission (OSHA's own rule).
  3. Link year t to t+1: same establishment_ID first; otherwise the backup key (name, zip, NAICS) where it is
     unique in both years and neither record is already linked. Chain links into a stable site_id.
  4. Flag the modelling cohort (rules fixed before any model was run, see docs/panel-note.md).
  5. Build pairs: features from year t (and t-1 where linked), outcome from t+1.
     Target: the t+1 DART rate is above the 80th percentile of the site's industry in year t.

Outputs:
  data/final/site_years.parquet   one row per site per year, industrial sectors, with cohort flag and site_id
  data/final/pairs.parquet        one row per site per year t with a usable t+1 outcome
  outputs/panel/*.csv             funnel, link counts, thresholds, prevalence
  docs/panel-note.md              plain-English summary

Usage: .venv/bin/python scripts/02_build_panel.py
"""
import sys
from pathlib import Path

import numpy as np
import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from src.osha import raw_files, read_year, standardise, year_of  # noqa: E402

FINAL = Path("data/final")
OUT = Path("outputs/panel")
DOC = Path("docs/panel-note.md")

INDUSTRIAL = {"11", "21", "22", "23", "31", "32", "33", "42", "48", "49"}
MIN_HOURS = 20_000          # about 10 full-time workers; limits how far one injury can move the rate
HPE_RANGE = (100, 8_760)    # hours per average employee; outside this the hours or headcount are wrong
TOP_SHARE = 0.20            # top 20% of the industry
MIN_GROUP = 200             # sites needed in a 3-digit NAICS group for its own threshold


def load():
    frames, funnel = [], []
    for p in raw_files():
        y = year_of(p)
        df = standardise(read_year(p), y)
        n0 = len(df)
        df = df.sort_values("submitted_at", na_position="first").drop_duplicates("establishment_id", keep="last")
        funnel.append({"year": y, "rows": n0, "duplicate_ids_removed": n0 - len(df)})
        frames.append(df)
        print(f"{y}: {n0:,} rows, {n0 - len(df):,} duplicate IDs removed")
    sy = pd.concat(frames, ignore_index=True)
    return sy, pd.DataFrame(funnel)


def link(sy):
    """Return a frame of (row_t, row_n, method) links for consecutive years."""
    links = []
    for t in sorted(sy["year"].unique())[:-1]:
        a = sy.loc[sy["year"] == t, ["establishment_id", "link_key"]].reset_index()
        b = sy.loc[sy["year"] == t + 1, ["establishment_id", "link_key"]].reset_index()
        by_id = a.merge(b, on="establishment_id", suffixes=("_t", "_n"))[["index_t", "index_n"]].assign(method="id")
        ra = a[~a["index"].isin(by_id["index_t"])]
        rb = b[~b["index"].isin(by_id["index_n"])]
        ua = ra[~ra["link_key"].duplicated(keep=False)]
        ub = rb[~rb["link_key"].duplicated(keep=False)]
        by_key = ua.merge(ub, on="link_key", suffixes=("_t", "_n"))[["index_t", "index_n"]].assign(method="key")
        links.append(pd.concat([by_id, by_key]).assign(year_t=t))
    return pd.concat(links, ignore_index=True)


def site_ids(sy, links):
    """Chain year-to-year links into one site_id; a record with no link from the year before starts a new site."""
    sid = np.zeros(len(sy), dtype=np.int64)
    year = sy["year"].to_numpy()
    counter = 0
    for y in sorted(sy["year"].unique()):
        rows = np.where((year == y) & (sid == 0))[0]
        sid[rows] = np.arange(counter + 1, counter + 1 + len(rows))
        counter += len(rows)
        step = links[links["year_t"] == y]
        sid[step["index_n"].to_numpy()] = sid[step["index_t"].to_numpy()]
    return sid


def cohort_flag(sy):
    return (sy["sector2"].isin(INDUSTRIAL) & sy["size_band"].isin(["20-249", "250+"]) & (sy["hours"] >= MIN_HOURS)
            & sy["hours_per_employee"].between(*HPE_RANGE) & sy["dart_rate"].notna())


def thresholds(sy):
    """80th percentile DART rate per year and 3-digit NAICS, pooled to the 2-digit sector when a group is small."""
    c = sy[sy["in_cohort"]]
    g3 = c.groupby(["year", "naics3"])["dart_rate"].agg(n="size", p=lambda s: s.quantile(1 - TOP_SHARE)).reset_index()
    g2 = c.groupby(["year", "sector2"])["dart_rate"].agg(n2="size", p2=lambda s: s.quantile(1 - TOP_SHARE)).reset_index()
    return g3, g2


def build_pairs(sy, links):
    cols = ["site_id", "year", "naics3", "naics6", "sector2", "sector", "state", "size_band", "establishment_type",
            "employees", "hours", "deaths", "dart_cases", "total_cases", "dart_rate", "tcr_rate", "dafw_rate",
            "lost_days_rate", "industry_pctile", "threshold", "threshold_level", "in_cohort"]
    t = sy.loc[links["index_t"], cols].reset_index(drop=True)
    n = sy.loc[links["index_n"], ["hours", "hours_per_employee", "dart_rate", "dart_cases", "dart_rate"]].reset_index(drop=True)
    n.columns = ["hours_next", "hpe_next", "dart_rate_next", "dart_cases_next", "_dup"]
    pairs = pd.concat([t, n.drop(columns="_dup"), links[["method"]].reset_index(drop=True)], axis=1)

    prev = sy.loc[links["index_t"], ["dart_rate", "tcr_rate", "dart_cases", "hours"]].reset_index(drop=True)
    prev.columns = ["dart_rate_prev", "tcr_rate_prev", "dart_cases_prev", "hours_prev"]
    prev["link_to"] = links["index_n"].values
    prev = prev.set_index("link_to")
    here = links["index_t"].values
    p = prev.reindex(here)
    for c in prev.columns:
        pairs[c] = p[c].values
    pairs["has_prev"] = pairs["dart_rate_prev"].notna()
    pooled_hours = pairs["hours"] + pairs["hours_prev"].fillna(0)
    pairs["dart_rate_2yr"] = (pairs["dart_cases"] + pairs["dart_cases_prev"].fillna(0)) * 200_000 / pooled_hours
    pairs["dart_change"] = pairs["dart_rate"] - pairs["dart_rate_prev"]
    pairs["top_band_now"] = pairs["dart_rate"] > pairs["threshold"]
    pairs["years_seen"] = pairs.groupby("site_id")["year"].rank(method="first").astype(int)
    pairs["target"] = (pairs["dart_rate_next"] > pairs["threshold"]).astype(int)
    return pairs


def main():
    FINAL.mkdir(parents=True, exist_ok=True)
    OUT.mkdir(parents=True, exist_ok=True)
    sy, funnel = load()
    links = link(sy)
    sy["site_id"] = site_ids(sy, links)
    sy["in_cohort"] = cohort_flag(sy)

    g3, g2 = thresholds(sy)
    sy = sy.merge(g3, on=["year", "naics3"], how="left").merge(g2, on=["year", "sector2"], how="left")
    own = sy["n"] >= MIN_GROUP
    sy["threshold"] = np.where(own, sy["p"], sy["p2"])
    sy["threshold_level"] = np.where(own, "naics3", "sector")
    sy.loc[~sy["in_cohort"], ["threshold", "threshold_level"]] = [np.nan, None]
    c = sy["in_cohort"]
    sy.loc[c, "industry_pctile"] = sy[c].groupby(["year", "naics3"])["dart_rate"].rank(pct=True)
    sy = sy.drop(columns=["n", "p", "n2", "p2"])

    # links were built on positional indices before the merge; the merge keeps row order, so they still hold
    pairs_all = build_pairs(sy, links)
    usable = (pairs_all["in_cohort"] & (pairs_all["hours_next"] >= MIN_HOURS)
              & pairs_all["hpe_next"].between(*HPE_RANGE) & pairs_all["dart_rate_next"].notna())
    pairs = pairs_all[usable].drop(columns=["in_cohort", "hpe_next"]).reset_index(drop=True)

    ind = sy[sy["sector2"].isin(INDUSTRIAL)].drop(columns=["link_key"])
    ind.to_parquet(FINAL / "site_years.parquet", index=False)
    pairs.to_parquet(FINAL / "pairs.parquet", index=False)

    linked_t = pairs_all.groupby("year").size()
    in_cohort_t = sy[sy["in_cohort"]].groupby("year").size()
    cohort_linked = pairs_all[pairs_all["in_cohort"]].groupby("year").size()
    funnel = funnel.set_index("year")
    funnel["industrial_rows"] = sy[sy["sector2"].isin(INDUSTRIAL)].groupby("year").size()
    funnel["in_cohort"] = in_cohort_t
    funnel["cohort_linked_to_next_year"] = cohort_linked
    funnel["pairs_with_usable_outcome"] = pairs.groupby("year").size()
    funnel = funnel.reset_index()
    funnel.to_csv(OUT / "funnel.csv", index=False)
    links.groupby(["year_t", "method"]).size().unstack().to_csv(OUT / "links_by_method.csv")
    prev = pairs.groupby("year").agg(pairs=("target", "size"), prevalence=("target", "mean"),
                                     top_band_now=("top_band_now", "mean"), has_prev=("has_prev", "mean"),
                                     key_links=("method", lambda m: (m == "key").mean())).reset_index()
    prev.to_csv(OUT / "prevalence_by_year.csv", index=False)
    lvl = sy[sy["in_cohort"]].groupby(["year", "threshold_level"]).size().unstack(fill_value=0)
    lvl.to_csv(OUT / "threshold_levels.csv")
    write_doc(funnel, prev, links, lvl, len(pairs))
    print(f"pairs: {len(pairs):,}; site_years (industrial): {len(ind):,}")


def write_doc(funnel, prev, links, lvl, n_pairs):
    lines = ["# Panel note", "",
             "Generated by `scripts/02_build_panel.py`.", "",
             "## Rules (fixed before any model was run)", "",
             f"- **Sectors:** industrial NAICS 2-digit codes {', '.join(sorted(INDUSTRIAL))} (agriculture, mining, utilities, construction, manufacturing, wholesale, transport and warehousing).",
             "- **One record per site per year:** where an establishment_ID appears twice in a year, the most recent submission is kept.",
             "- **Linking:** same establishment_ID in consecutive years; otherwise a backup key of normalised name, 5-digit zip and 6-digit NAICS, used only where the key is unique in both years and neither record is already linked.",
             f"- **Cohort:** 20 or more employees, at least {MIN_HOURS:,} hours worked, {HPE_RANGE[0]} to {HPE_RANGE[1]:,} hours per average employee, and a computable DART rate.",
             f"- **Usable outcome:** the linked next-year record meets the same hours rules.",
             f"- **Target:** next year's DART rate is above the {int((1 - TOP_SHARE) * 100)}th percentile of the site's 3-digit NAICS group in the current year (pooled to the 2-digit sector when the group has fewer than {MIN_GROUP} sites). The threshold uses only current-year data.", "",
             "## Funnel by year", "", funnel.to_markdown(index=False), "",
             "## Links by method", "", links.groupby(["year_t", "method"]).size().unstack().to_markdown(), "",
             "## Target prevalence by starting year", "",
             "`prevalence` is the share of pairs whose next-year rate is above the current-year threshold. It moves with year-to-year shifts in injury rates. `top_band_now` is the share above the threshold in the current year.", "",
             prev.to_markdown(index=False, floatfmt=".3f"), "",
             "## Threshold level used (cohort sites)", "", lvl.to_markdown(), "",
             f"Total usable pairs: {n_pairs:,}.", ""]
    DOC.write_text("\n".join(lines))


if __name__ == "__main__":
    main()
