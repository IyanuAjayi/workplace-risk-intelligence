"""
Risk Landscape tables for the report: where the top risk band concentrates by state, sector and size, and how
the crossing rate varies by band within each sector. Descriptive only, on the priced portfolio of private-sector
test sites (data/final/pricing_sites.parquet), both test years pooled. No model is refit.

Writes outputs/landscape/states.csv, sectors.csv, sizes.csv and sector_bands.csv, checks the state, sector and size
figures already quoted in docs/verified-metrics.md, and writes state_grid.csv (the tile-grid map layout).

Usage: .venv/bin/python scripts/09_landscape.py
"""
from pathlib import Path

import pandas as pd

FINAL, OUT = Path("data/final"), Path("outputs/landscape")
MIN_STATE = 500  # states with fewer site-years are listed but flagged, not ranked
MIN_CELL = 100  # sector-band cells with fewer site-years are flagged as too small to read
# tile-grid map: state, name, grid column (0 to 10), grid row (0 at the top); territories under 500 site-years have no tile
STATE_GRID = [
    ("AK", "Alaska", 0, 0),
    ("ME", "Maine", 10, 0),
    ("WI", "Wisconsin", 5, 1),
    ("VT", "Vermont", 9, 1),
    ("NH", "New Hampshire", 10, 1),
    ("WA", "Washington", 0, 2),
    ("ID", "Idaho", 1, 2),
    ("MT", "Montana", 2, 2),
    ("ND", "North Dakota", 3, 2),
    ("MN", "Minnesota", 4, 2),
    ("IL", "Illinois", 5, 2),
    ("MI", "Michigan", 6, 2),
    ("NY", "New York", 8, 2),
    ("MA", "Massachusetts", 9, 2),
    ("OR", "Oregon", 0, 3),
    ("NV", "Nevada", 1, 3),
    ("WY", "Wyoming", 2, 3),
    ("SD", "South Dakota", 3, 3),
    ("IA", "Iowa", 4, 3),
    ("IN", "Indiana", 5, 3),
    ("OH", "Ohio", 6, 3),
    ("PA", "Pennsylvania", 7, 3),
    ("NJ", "New Jersey", 8, 3),
    ("CT", "Connecticut", 9, 3),
    ("RI", "Rhode Island", 10, 3),
    ("CA", "California", 0, 4),
    ("UT", "Utah", 1, 4),
    ("CO", "Colorado", 2, 4),
    ("NE", "Nebraska", 3, 4),
    ("MO", "Missouri", 4, 4),
    ("KY", "Kentucky", 5, 4),
    ("WV", "West Virginia", 6, 4),
    ("VA", "Virginia", 7, 4),
    ("MD", "Maryland", 8, 4),
    ("DE", "Delaware", 9, 4),
    ("AZ", "Arizona", 1, 5),
    ("NM", "New Mexico", 2, 5),
    ("KS", "Kansas", 3, 5),
    ("AR", "Arkansas", 4, 5),
    ("TN", "Tennessee", 5, 5),
    ("NC", "North Carolina", 6, 5),
    ("SC", "South Carolina", 7, 5),
    ("DC", "District of Columbia", 8, 5),
    ("OK", "Oklahoma", 3, 6),
    ("LA", "Louisiana", 4, 6),
    ("MS", "Mississippi", 5, 6),
    ("AL", "Alabama", 6, 6),
    ("GA", "Georgia", 7, 6),
    ("HI", "Hawaii", 0, 7),
    ("TX", "Texas", 3, 7),
    ("FL", "Florida", 8, 7),
    ("PR", "Puerto Rico", 10, 7),
]


def portfolio():
    p = pd.read_parquet(FINAL / "pricing_sites.parquet")
    s = pd.read_parquet(FINAL / "scores.parquet", columns=["site_id", "year", "dart_rate"])
    d = p.merge(s, on=["site_id", "year"], how="left", validate="one_to_one")
    assert d["dart_rate"].notna().all(), "every priced site should have a score row"
    d["top"] = d["band"].astype(str) == "5 highest"
    return d


def summarise(d, by):
    g = d.groupby(by, observed=True).agg(site_years=("site_id", "size"), share_top_band=("top", "mean"),
                                         crossing_rate=("target", "mean"), avg_dart_rate=("dart_rate", "mean"))
    return g.reset_index().round({"share_top_band": 6, "crossing_rate": 6, "avg_dart_rate": 4})  # docs round once from these


def main():
    OUT.mkdir(parents=True, exist_ok=True)
    d = portfolio()
    states = summarise(d, "state")
    states["ranked"] = states["site_years"] >= MIN_STATE
    states = states.sort_values("share_top_band", ascending=False)
    sectors = summarise(d, "sector").sort_values("site_years", ascending=False)
    sizes = summarise(d, "size_band")
    sector_bands = summarise(d, ["sector", "band"])
    sector_bands["readable"] = sector_bands["site_years"] >= MIN_CELL

    # the figures already in docs/verified-metrics.md must come out the same
    st = states.set_index("state")["share_top_band"]
    for code, share in {"ME": 0.426, "WA": 0.375, "LA": 0.028, "AR": 0.068, "MS": 0.075}.items():
        assert round(st[code], 3) == share, f"{code} top-band share changed"
    sec = sectors.set_index("sector")
    assert sec.loc["Manufacturing", "site_years"] == 78918 and round(sec.loc["Manufacturing", "share_top_band"], 3) == 0.203
    assert round(sizes.set_index("size_band").loc["250+", "share_top_band"], 3) == 0.120

    # rates for groups too small to publish are left blank, as in the report
    rates = ["share_top_band", "crossing_rate", "avg_dart_rate"]
    states.loc[~states["ranked"], rates] = None
    sector_bands.loc[~sector_bands["readable"], rates] = None
    states.to_csv(OUT / "states.csv", index=False)
    sectors.to_csv(OUT / "sectors.csv", index=False)
    sizes.to_csv(OUT / "sizes.csv", index=False)
    sector_bands.to_csv(OUT / "sector_bands.csv", index=False)
    pd.DataFrame(STATE_GRID, columns=["State", "State name", "Grid column", "Grid row"]).to_csv(OUT / "state_grid.csv", index=False)
    print(f"{len(states)} states and territories ({states['ranked'].sum()} with {MIN_STATE}+ site-years), "
          f"{len(sectors)} sectors, {len(sector_bands)} sector-band cells")


if __name__ == "__main__":
    main()
