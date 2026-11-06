# Data dictionary

Rates are per 200,000 hours worked (100 full-time workers), the OSHA and BLS convention. Blank means unknown, never zero.

## data/final/site_years.parquet

One row per site per year, industrial sectors only (NAICS 11, 21, 22, 23, 31 to 33, 42, 48 to 49). 1,594,425 rows. Built by `02_build_panel.py`. Kept internal: it holds establishment and company names.

| Column | Meaning |
| --- | --- |
| year | Calendar year the injuries occurred (OSHA year_filing_for) |
| establishment_id | OSHA establishment ID (2019 decimals normalised) |
| establishment_name, company_name | As filed. Internal only, never exported |
| state, zip5 | State or territory; first 5 digits of the zip |
| naics6, naics3, sector2, sector | NAICS code at 6, 3 and 2 digits; sector name |
| size_band | <20, 20-249 or 250+ employees (OSHA codes 21 and 22 from 2023 merged back into 20-249) |
| establishment_type | 1 private, 2 state government, 3 local government |
| employees, hours | Annual average employees; total hours worked |
| deaths, dafw_cases, djtr_cases, other_cases | Form 300A fields G, H, I, J |
| dafw_days, djtr_days | Form 300A fields K, L |
| dart_cases, total_cases | H + I; H + I + J |
| dart_rate, tcr_rate, dafw_rate | Rates of DART cases, all recordable cases, days-away cases |
| lost_days_rate | (K + L) per 200,000 hours |
| hours_per_employee | hours / employees |
| submitted_at | Submission timestamp, used to keep the latest record when an ID repeats |
| site_id | Stable project key chaining a site across years (internal number, not an OSHA field) |
| in_cohort | Meets the modelling rules: 20+ employees, 20,000+ hours, 100 to 8,760 hours per employee, valid DART rate |
| threshold, threshold_level | 80th percentile DART rate of the site's 3-digit NAICS group that year (cohort sites); "sector" when the group has under 200 sites and the 2-digit sector is used |
| industry_pctile | Site's percentile rank of DART rate within its year and 3-digit NAICS group |

## data/final/pairs.parquet

One row per cohort site per starting year t (2016 to 2024) with a usable record in t+1. 799,158 rows. Features come from t (and t-1 where linked); the outcome comes from t+1.

| Column | Meaning |
| --- | --- |
| site_id, year | Site and starting year t |
| hours_next, dart_rate_next, dart_cases_next | The t+1 record |
| method | How t was linked to t+1: "id" (same establishment ID) or "key" (backup name, zip and NAICS match) |
| dart_rate_prev, tcr_rate_prev, dart_cases_prev, hours_prev | The t-1 record, when linked |
| has_prev | A t-1 record exists |
| dart_rate_2yr | DART cases over t-1 and t divided by their pooled hours |
| dart_change | dart_rate minus dart_rate_prev (0 when no prior year) |
| top_band_now | dart_rate is above this year's industry threshold |
| years_seen | Number of linked years up to t |
| **target** | 1 if dart_rate_next is above the year-t threshold. Plain words: next year's serious-injury rate crosses the line that marked the worst fifth of the industry this year |
| (other columns) | As in site_years, for year t |

## data/final/scores.parquet

The 2023 and 2024 test pairs with model scores. 215,802 rows. Adds `log_hours`, `any_death` and three scores: `score_rating_class` (M0), `score_scorecard` (M2) and `score_boosting` (M3). Each is a probability of target = 1.

## data/final/pricing_sites.parquet

Private-sector test pairs used in the pricing simulation, central claim cost. 199,150 rows.

| Column | Meaning |
| --- | --- |
| p | Scorecard probability |
| band | Score quintile across both test years: 1 lowest to 5 highest |
| relativity | p divided by the average p of the site's year and 3-digit NAICS group, capped at 0.6 to 2.0 |
| bls_dart, bls_level | BLS DART rate for year t-1, and whether it was matched at 3-digit NAICS or the sector |
| premium_a | Simulated industry-only premium: bls_dart x hours_next / 200,000 x $50,076 |
| premium_b | premium_a x relativity, rebalanced so each year and industry total equals premium A's |
| sim_loss | dart_cases_next x $50,076 (observed next-year cases, simulated cost) |

## outputs/powerbi/workplace_risk_powerbi.xlsx

Built by `06_export_powerbi.py` for Power BI. Contains no names, EINs or addresses.

| Sheet | Grain | Source |
| --- | --- | --- |
| Sites | One row per score year, sector, state, size band and risk band (5,240 rows covering 199,150 private-sector test-year sites). Columns: Site count, Crossing sites, DART rate sum, Premium A industry only, Premium B with score, Simulated loss | pricing_sites, summed |
| Models | One model per test year | outputs/model/metrics.csv |
| Calibration | Model x test year x score decile | outputs/model/calibration.csv |
| Drivers | One feature | outputs/model/importance_boosting.csv |
| ROC | Model x test year x curve point (about 200 per curve). Columns: False positive rate, True positive rate, Model order | outputs/model/roc_curve.csv, from `08_curves.py` |
| PrecisionRecall | Model x test year x curve point. Columns: Recall, Precision, Model order. A few points share a recall value, so set the line chart's Precision aggregation to Maximum | outputs/model/pr_curve.csv, from `08_curves.py` |
| PricingBands | Year x band x claim-cost scenario. Adds Band label ("Band 1, lowest" to "Band 5, highest") and Band short ("Band 1" to "Band 5") | outputs/pricing/bands.csv |
| PricingSummary | Year x claim-cost scenario. Adds Scenario (Low, Central, High), Scenario order and Rule (for example "DART cases × $50,076") | outputs/pricing/summary.csv |
| Robustness | One row per check or subgroup: Row order, Group (Check, Sector, Size), Label, AUC 2023, AUC 2024 (checks only), Note. Scorecard AUCs at three decimals | outputs/model/robustness_*.csv |
| ModelPicker | One row per model: Model, Model order, Has calibration (false for last year's rate, which is a rank), Inputs | written by the script |
| TestYearPicker | One row per test year: Test year, Outcome year, Tile label ("2023, outcome 2024"), Test pairs | outputs/model/metrics.csv |
| ScoreYears | One row per score year (2023, 2024) with its outcome year, for the Pricing Lab year slicer | written by the script |
| ClaimCostScenarios | One row per claim-cost scenario: Scenario key (low, central, high), Scenario, Cases priced, Claim cost per case, Claim-cost source, Scenario order, Rule | scripts/04_pricing.py, docs/benchmarks.md |
| TestYears | Four rows mapping the Risk Landscape year tiles to score years: Test year ("2023 + 2024" for both, "2023", "2024"), Score year, Sort order and Tile label (the text on the tile: "2023 + 2024", "2023, outcome 2024", "2024, outcome 2025"). Related many-to-many to Sites[Score year] | written by the script |
| Bands | One row per risk band: Risk band, Band order, Band label, Band colour (hex), Band text colour | docs/design-system.md |
| StateGrid | One row per state tile on the Risk Landscape map: State, State name, Grid column (0 to 10), Grid row (0 at the top) | outputs/landscape/state_grid.csv |
| About | Source, period and caveat text | written by the script |

The Sites sheet also carries Sector order (by portfolio site-years), Size band label ("20 to 249 employees", "250+ employees") and Size order, used to sort slicers and tables.

## outputs/landscape/ (scripts/09_landscape.py)

Descriptive tables on the priced portfolio, both test years pooled, with shares and rates to six decimals so that documents round once from them: `states.csv` (site-years, share in the top band, crossing rate, average DART rate, and whether the state has the 500 site-years needed to be ranked), `sectors.csv`, `sizes.csv`, `sector_bands.csv` (crossing rate by sector and band; cells under 100 site-years are flagged as not readable) and `state_grid.csv` (the tile-map layout).

## Metrics

| Metric | Definition |
| --- | --- |
| AUC | Probability a randomly chosen crossing site scores higher than a non-crossing one |
| Gini | 2 x AUC - 1 |
| Precision, recall at top 20% | Among the 20% highest-scored sites: the share that crossed; and the share of all crossing sites caught |
| Lift top 10% | Crossing rate in the top-scored tenth divided by the overall rate |
| Calibration | Mean predicted probability against observed crossing rate in each score decile |
| Simulated loss / premium | Band's sim_loss divided by its premium under A or B. Not a real loss ratio |
| Misallocated share | Half the sum, across bands, of the absolute gap between a band's share of simulated loss and its share of premium |
| Band spread | Highest band loss/premium ratio divided by the lowest |
