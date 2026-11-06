"""
Audit the OSHA ITA Form 300A summary files before any modelling.

Reads every year found in data/raw (a CSV, or a ZIP holding one CSV), standardises column names, and writes:
  outputs/audit/schema_by_year.csv       columns present in each year
  outputs/audit/missing_by_year.csv      share blank per column and year
  outputs/audit/checks_by_year.csv       row counts, duplicates, invalid values, consistency checks
  outputs/audit/sector_feasibility.csv   sites and positive DART sites by NAICS sector, latest year
  docs/data-audit.md                     the same results in plain English

Nothing is dropped here. Every check only counts. Exclusion rules live in 02_build_panel.py.

Usage: .venv/bin/python scripts/01_audit.py
"""
import sys
from pathlib import Path

import numpy as np
import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from src.osha import SECTORS, link_key, num, raw_files, read_year, year_of  # noqa: E402

OUT = Path("outputs/audit")
DOC = Path("docs/data-audit.md")
COUNTS = ["total_deaths", "total_dafw_cases", "total_djtr_cases", "total_other_cases", "total_dafw_days",
          "total_djtr_days", "total_injuries", "total_skin_disorders", "total_respiratory_conditions",
          "total_poisonings", "total_hearing_loss", "total_other_illnesses"]
SIZE = {1: "<20", 2: "20-249", 21: "20-99", 22: "100-249", 3: "250+"}


def linkage(frames):
    """Year t to t+1: share of sites whose ID reappears, and links the backup key adds."""
    rows = []
    years = sorted(frames)
    for t in years[:-1]:
        a, b = frames[t], frames[t + 1]
        ida, idb = set(a["establishment_id"].dropna()), set(b["establishment_id"].dropna())
        both = ida & idb
        ka = a.loc[~a["key"].duplicated(keep=False)].set_index("key")["establishment_id"]
        kb = b.loc[~b["key"].duplicated(keep=False)].set_index("key")["establishment_id"]
        common = ka.index.intersection(kb.index)
        pairs = pd.DataFrame({"id_t": ka[common].values, "id_n": kb[common].values})
        unlinked = pairs[~pairs["id_t"].isin(both) & ~pairs["id_n"].isin(both)]
        rows.append({"from": t, "to": t + 1, "sites_t": len(ida), "id_links": len(both), "id_link_rate": len(both) / len(ida),
                     "key_links": len(pairs), "key_agrees_with_id": (pairs["id_t"] == pairs["id_n"]).mean(),
                     "key_adds": len(unlinked), "total_link_rate": (len(both) + len(unlinked)) / len(ida)})
    return pd.DataFrame(rows)


def checks(df, year):
    n = len(df)
    hours, emp = num(df["total_hours_worked"]), num(df["annual_average_employees"])
    dafw, djtr, other = num(df["total_dafw_cases"]), num(df["total_djtr_cases"]), num(df["total_other_cases"])
    ill = sum(num(df[c]).fillna(0) for c in ["total_injuries", "total_skin_disorders", "total_respiratory_conditions",
                                              "total_poisonings", "total_hearing_loss", "total_other_illnesses"])
    cases = dafw.fillna(0) + djtr.fillna(0) + other.fillna(0)
    naics = df["naics_code"].fillna("").str.strip()
    hpe = hours / emp.where(emp > 0)
    dart = (dafw + djtr) * 200_000 / hours.where(hours > 0)
    filing = num(df.get("year_filing_for", pd.Series(dtype=str)))
    row = {
        "year": year, "rows": n, "columns": df.shape[1],
        "id_unique": df["id"].nunique() == n if "id" in df else np.nan,
        "establishment_id_blank": df["establishment_id"].isna().sum(),
        "establishment_id_duplicated_rows": df["establishment_id"].duplicated(keep=False).sum(),
        "exact_duplicate_rows": df.drop(columns=[c for c in ["id"] if c in df]).duplicated().sum(),
        "year_filing_for_mismatch": (filing.notna() & (filing != year)).sum(),
        "hours_blank": hours.isna().sum(), "hours_zero": (hours == 0).sum(), "hours_negative": (hours < 0).sum(),
        "employees_blank_or_zero": (emp.isna() | (emp == 0)).sum(),
        "hours_per_employee_over_8760": (hpe > 8760).sum(),
        "hours_per_employee_under_100": (hpe < 100).sum(),
        "hours_under_2000": ((hours > 0) & (hours < 2000)).sum(),
        "dafw_blank": dafw.isna().sum(), "djtr_blank": djtr.isna().sum(),
        "negative_counts": sum((num(df[c]) < 0).sum() for c in COUNTS if c in df),
        "cases_vs_types_mismatch": ((cases - ill).abs() > 0).sum(),
        "flag_none_but_cases": ((num(df["no_injuries_illnesses"]) == 2) & (cases > 0)).sum(),
        "naics_blank": (naics == "").sum(), "naics_not_6_digits": ((naics != "") & ~naics.str.fullmatch(r"\d{6}")).sum(),
        "ein_blank": df["ein"].isna().sum() if "ein" in df else np.nan,
        "dart_rate_valid": dart.notna().sum(), "dart_rate_zero": (dart == 0).sum(),
        "dart_rate_median": dart.median(), "dart_rate_p90": dart.quantile(0.9), "dart_rate_p99": dart.quantile(0.99),
        "dart_rate_over_100": (dart > 100).sum(),
        "size_counts": "; ".join(f"{SIZE.get(int(k), k)}: {v}" for k, v in num(df["size"]).value_counts().sort_index().items()),
        "establishment_type_counts": "; ".join(f"{int(k)}: {v}" for k, v in num(df["establishment_type"]).value_counts().sort_index().items()),
        "states": df["state"].nunique(),
    }
    return row


def feasibility(df):
    hours = num(df["total_hours_worked"])
    dart = (num(df["total_dafw_cases"]) + num(df["total_djtr_cases"])) * 200_000 / hours.where(hours > 0)
    sector = df["naics_code"].fillna("").str[:2].map(SECTORS).fillna("Unknown")
    t = pd.DataFrame({"sector": sector, "naics3": df["naics_code"].fillna("").str[:3], "valid": dart.notna(),
                      "positive": dart > 0, "size": num(df["size"])})
    out = t.groupby("sector").agg(sites=("valid", "size"), valid_rate=("valid", "sum"), any_dart_case=("positive", "sum"),
                                  naics3_groups=("naics3", "nunique"),
                                  size_under_20=("size", lambda s: (s == 1).sum())).reset_index()
    out["share_with_dart_case"] = out["any_dart_case"] / out["valid_rate"]
    g3 = t[t.valid].groupby("naics3").size()
    return out.sort_values("sites", ascending=False), int((g3 >= 100).sum()), int(len(g3)), float(g3[g3 >= 100].sum() / g3.sum())


def main():
    OUT.mkdir(parents=True, exist_ok=True)
    files = raw_files()
    schema, missing, rows, frames = {}, {}, [], {}
    latest = None
    for p in files:
        y = year_of(p)
        df = read_year(p)
        print(f"{y}: {p.name} -> {df.shape}")
        schema[y] = pd.Series(True, index=df.columns)
        missing[y] = df.isna().mean()
        rows.append(checks(df, y))
        frames[y] = pd.DataFrame({"establishment_id": df["establishment_id"], "key": link_key(df)})
        latest = (y, df)
    schema = pd.DataFrame(schema).fillna(False).astype(bool)
    links = linkage(frames)
    links.to_csv(OUT / "linkage_by_year.csv", index=False)
    missing = pd.DataFrame(missing)
    checks_df = pd.DataFrame(rows)
    schema.to_csv(OUT / "schema_by_year.csv")
    missing.to_csv(OUT / "missing_by_year.csv")
    checks_df.to_csv(OUT / "checks_by_year.csv", index=False)
    feas, g3_ok, g3_all, g3_share = feasibility(latest[1])
    feas.to_csv(OUT / "sector_feasibility.csv", index=False)
    write_doc(files, schema, missing, checks_df, feas, latest[0], g3_ok, g3_all, g3_share, links)


def write_doc(files, schema, missing, c, feas, ly, g3_ok, g3_all, g3_share, links):
    pct = lambda a, b: f"{a / b:.1%}" if b else "n/a"
    lines = ["# Data audit: OSHA ITA Form 300A summary data", "",
             f"Generated by `scripts/01_audit.py`. Years found in `data/raw`: {', '.join(str(year_of(p)) for p in files)}.",
             "Nothing is removed at this stage; every figure below is a count.", ""]
    for _, r in c.iterrows():
        n = r["rows"]
        lines += [f"## {int(r['year'])}", "",
                  f"- {n:,} rows, {r['columns']} columns, {r['states']} states or territories. Record ID unique: {r['id_unique']}.",
                  f"- establishment_ID: {r['establishment_id_blank']:,} blank, {r['establishment_id_duplicated_rows']:,} rows share an ID with another row. Exact duplicate rows (ignoring record ID): {r['exact_duplicate_rows']:,}.",
                  f"- year_filing_for different from the file year: {r['year_filing_for_mismatch']:,}.",
                  f"- Hours worked: {r['hours_blank']:,} blank, {r['hours_zero']:,} zero, {r['hours_negative']:,} negative, {r['hours_under_2000']:,} above zero but under 2,000 hours (about one full-time worker).",
                  f"- Hours per average employee over 8,760 (more hours than a year has): {r['hours_per_employee_over_8760']:,}. Under 100: {r['hours_per_employee_under_100']:,}. Employees blank or zero: {r['employees_blank_or_zero']:,}.",
                  f"- Case totals that don't equal the injury and illness type totals: {r['cases_vs_types_mismatch']:,}. 'No injuries' flag set but cases reported: {r['flag_none_but_cases']:,}. Negative counts: {r['negative_counts']:,}.",
                  f"- NAICS: {r['naics_blank']:,} blank, {r['naics_not_6_digits']:,} not a 6-digit code. EIN blank: {r['ein_blank']:,}.",
                  f"- DART rate computable for {r['dart_rate_valid']:,} sites ({pct(r['dart_rate_valid'], n)}). Zero DART cases: {r['dart_rate_zero']:,} ({pct(r['dart_rate_zero'], r['dart_rate_valid'])} of those). Median {r['dart_rate_median']:.2f}, 90th percentile {r['dart_rate_p90']:.2f}, 99th percentile {r['dart_rate_p99']:.2f} per 100 full-time workers. Above 100: {r['dart_rate_over_100']:,}.",
                  f"- Size bands: {r['size_counts']}.", f"- Establishment type (1 private, 2 state, 3 local government): {r['establishment_type_counts']}.", ""]
    lines += ["## Missing values by column (share blank)", "", missing.map(lambda v: f"{v:.1%}").to_markdown(), "",
              f"## Sector feasibility, {ly}", "",
              "Sites with a computable DART rate and how many had at least one DART case. A within-industry top-20% target needs enough sites and enough cases per group.", "",
              feas.to_markdown(index=False, floatfmt=".3f"), "",
              f"{g3_ok} of {g3_all} three-digit NAICS groups have at least 100 sites with a valid rate, covering {g3_share:.1%} of those sites.", ""]
    if len(links):
        lines += ["## Linking sites from one year to the next", "",
                  "OSHA warns that establishment_ID may change if a site re-registers. The backup key is the normalised establishment name, 5-digit zip and 6-digit NAICS, used only where it is unique in both years. 'Key agrees with ID' is the share of backup-key matches whose IDs are also equal, a check on the key's accuracy where both exist.", "",
                  links.to_markdown(index=False, floatfmt=".3f"), ""]
    if schema.shape[1] > 1:
        diff = schema[~schema.all(axis=1)]
        lines += ["## Schema changes across years", "", diff.to_markdown() if len(diff) else "None.", ""]
    DOC.write_text("\n".join(lines))
    print("wrote", DOC)


if __name__ == "__main__":
    main()
