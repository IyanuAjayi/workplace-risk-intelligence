from pathlib import Path

import numpy as np
import pandas as pd
import pytest

FINAL = Path(__file__).resolve().parents[1] / "data" / "final"


@pytest.fixture(scope="module")
def pairs():
    return pd.read_parquet(FINAL / "pairs.parquet")


@pytest.fixture(scope="module")
def site_years():
    return pd.read_parquet(FINAL / "site_years.parquet",
                           columns=["site_id", "year", "naics3", "dart_rate", "dart_cases", "hours", "in_cohort", "threshold"])


def test_dart_rate_formula(site_years):
    s = site_years[site_years["hours"] > 0].head(10_000)
    expected = s["dart_cases"] * 200_000 / s["hours"]
    assert np.allclose(s["dart_rate"], expected, equal_nan=True)


def test_one_row_per_site_per_year(site_years, pairs):
    assert not site_years.duplicated(["site_id", "year"]).any()
    assert not pairs.duplicated(["site_id", "year"]).any()


def test_pairs_cover_2016_to_2024(pairs):
    assert pairs["year"].min() == 2016 and pairs["year"].max() == 2024


def test_target_uses_current_year_threshold(pairs, site_years):
    cohort = site_years[site_years["in_cohort"]]
    sample = pairs.sample(2_000, random_state=0)
    for (year, naics3), grp in sample.groupby(["year", "naics3"]):
        current = cohort[(cohort["year"] == year) & (cohort["naics3"] == naics3)]["threshold"].dropna().unique()
        assert len(current) == 1
        assert np.allclose(grp["threshold"], current[0])
    assert ((pairs["dart_rate_next"] > pairs["threshold"]).astype(int) == pairs["target"]).all()


def test_no_prior_year_before_2017(pairs):
    assert not pairs.loc[pairs["year"] == 2016, "has_prev"].any()


def test_prevalence_near_twenty_percent(pairs):
    prev = pairs.groupby("year")["target"].mean()
    assert prev.between(0.15, 0.25).all()


def test_cohort_rules_hold(pairs):
    assert (pairs["hours"] >= 20_000).all() and (pairs["hours_next"] >= 20_000).all()
    assert pairs["size_band"].isin(["20-249", "250+"]).all()
