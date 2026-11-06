# Verified metrics (the only numbers any design or report may use)

Every figure below was produced by the committed scripts and checked (see `docs/qa-note.md`). If a design needs a number that isn't here, label it **"Pending validation"**. Never estimate or invent one.

Brand hierarchy: **Parakeet Risk** (parent, official logo) > **Workplace Risk Intelligence** (product) > *Predictive insights for industrial insurance underwriting* (proposition).

## Data and freshness

- Source: OSHA Injury Tracking Application (ITA), Form 300A summary data, calendar years 2016 to 2025. The 2025 file covers submissions received to 31 Aug 2026. Downloaded 27 and 29 Oct 2026.
- 3.2 million establishment records in total (2016: 214,978 rising to 2025: 400,288).
- Industrial sectors only (NAICS 11, 21, 22, 23, 31 to 33, 42, 48 to 49): 1,594,425 site-years.
- Modelling cohort rules: 20+ employees, 20,000+ hours worked, 100 to 8,760 hours per employee. The 2025 cohort is 149,200 sites.
- Linked year pairs (a site's year t record with its t+1 outcome): 799,158, starting years 2016 to 2024.
- Test years: starting years 2023 and 2024 (outcomes 2024 and 2025). Rating class, scorecard and gradient boosting first fitted on 2016 to 2021, the last two tuned on 2022, then all three refit on 2016 to 2022: **583,356** pairs (799,158 less the 215,802 test pairs; `docs/model-results.md`). Last year's rate is a rank and needs no training.
- External: BLS SOII industry DART rates 2022 to 2024 (relative standard errors about 2% to 7% for large industrial groups). Claim cost: NCCI average lost-time claim, accidents 2023 to 2024, **$50,076** (via NSC Injury Facts, valued 15 Oct 2026). Falls or slips average **$57,314** (high scenario).

## Target

Next year's DART rate (cases with days away, restriction or transfer per 200,000 hours) is above the line marking the worst 20% of the site's 3-digit NAICS industry this year. Prevalence by starting year: 2016 19.7%, 2017 20.2%, 2018 18.9%, 2019 18.5%, 2020 21.5%, 2021 20.3%, 2022 18.0%, 2023 18.4%, 2024 18.4%.

## Model performance (all test pairs: 2023 n = 107,673; 2024 n = 108,129)

| Model | AUC 2023 (95% CI) | AUC 2024 (95% CI) | Gini 2023 / 2024 | Capture top 20% 2023 / 2024 | Precision top 20% 2023 / 2024 | Lift top 10% 2023 / 2024 |
| --- | --- | --- | --- | --- | --- | --- |
| Rating class only (sector, size, state, ownership) | 0.592 (0.587 to 0.596) | 0.589 (0.585 to 0.593) | 0.183 / 0.177 | 28.0% / 27.2% | 25.6% / 24.8% | 1.41x / 1.37x |
| Last year's rate only | 0.729 (0.725 to 0.734) | 0.729 (0.725 to 0.734) | 0.459 / 0.458 | 49.8% / 49.8% | 45.9% / 45.8% | 2.98x / 2.99x |
| Scorecard (explainable, used for pricing) | 0.783 (0.780 to 0.787) | 0.785 (0.782 to 0.789) | 0.567 / 0.571 | 50.8% / 51.1% | 46.7% / 46.9% | 3.01x / 3.04x |
| Gradient boosting | 0.800 (0.797 to 0.803) | 0.801 (0.798 to 0.804) | 0.600 / 0.601 | 51.7% / 51.8% | 47.6% / 47.6% | 3.21x / 3.19x |

- Scorecard gain over last year's rate: +0.054 AUC in 2023 (95% CI 0.051 to 0.057) and +0.056 in 2024 (0.053 to 0.059).
- Prevalence in both test years: 18.4%.
- **Calibration, scorecard 2023, by score decile (predicted vs observed):** 1: 4.0% vs 2.1%; 2: 6.2% vs 4.0%; 3: 7.5% vs 6.4%; 4: 8.9% vs 8.9%; 5: 10.8% vs 11.8%; 6: 13.9% vs 14.1%; 7: 18.7% vs 18.1%; 8: 26.3% vs 25.2%; 9: 38.8% vs 38.0%; 10: 57.8% vs 55.5%.
- **Drivers** (gradient boosting, AUC drop when an input is shuffled, 2023 sample): industry percentile this year 0.125; hours worked (log) 0.037; total case rate 0.018; change from last year 0.011; above the line this year 0.011; two-year DART rate 0.010; DART rate 0.007; sector 0.005; state 0.005. These are associations, not causes.
- **ROC and precision-recall curves:** every model, both test years, in `outputs/model/roc_curve.csv` (columns Model, Test year, False positive rate, True positive rate) and `outputs/model/pr_curve.csv` (Model, Test year, Recall, Precision). Thinned to about 200 points per curve by `scripts/08_curves.py`; the AUC from each thinned ROC curve is within 0.002 of the full figure. Curves may be drawn to scale from these files.
- **Robustness:** without 2020, same AUC to three decimals (0.783 / 0.785). Stable-ID links only (model rebuilt on pairs linked by OSHA ID alone), AUC 0.782 / 0.790, which is 0.78 / 0.79 at two decimals. Alternative target (next year's own top 20%): agrees with the main target on 98.7% (2023) and 98.6% (2024) of sites, scorecard AUC 0.781 / 0.784. Source: `outputs/model/robustness_*.csv` from `scripts/05_robustness.py`.
- **By sector, scorecard 2023 AUC:** construction 0.808, mining 0.800 (only 428 test pairs, so read with care; `outputs/model/robustness_subgroups.csv`), manufacturing 0.787, utilities 0.779, wholesale 0.779, transport and warehousing 0.765, agriculture 0.761. **By size:** 250+ employees 0.915; 20 to 249 employees 0.762.

## Portfolio (private-sector test sites with a BLS rate: 199,150 site-years; 2023: 99,185; 2024: 99,965)

- How the portfolio is reached from all 215,802 test pairs: less 337 pairs with no next-year case split, less 16,315 sites not marked private (13,900 state government, 2,078 local government, 337 with no valid ownership code). The model figures above use all test pairs; every figure in this section uses the 199,150 portfolio.
- Crossed the line next year: 36,389 (18.3%). Average site DART rate this year: 2.57 per 100 full-time workers.
- **Risk bands** (scorecard fifths across both test years). Observed crossing rate by band, 2023 / 2024:
  - 1 lowest: 2.9% / 3.0%
  - 2: 7.1% / 7.6%
  - 3: 12.3% / 12.8%
  - 4: 21.0% / 22.0%
  - 5 highest: 46.5% / 47.5%
- Top band (both test years pooled): 39,830 sites, 18,709 of which crossed the line. Capture 51.4% (18,709 of all 36,389 line-crossers were in band 5). Hit rate 47.0% (18,709 of the 39,830 band 5 sites crossed). Lift 2.57x (47.0% over the 18.3% base rate). Band 5 is exactly one fifth of the pooled portfolio, 20.4% of 2023 and 19.6% of 2024.
- **By sector** (site-years; share in top band; average DART rate):
  - Manufacturing 78,918; 20.3%; 2.17
  - Construction 43,110; 18.4%; 1.85
  - Transport and warehousing 36,087; 21.0%; 4.29
  - Wholesale 27,123; 21.2%; 2.83
  - Utilities 6,729; 15.8%; 1.38
  - Agriculture 6,335; 20.4%; 3.04
  - Mining, oil and gas 848; 19.8%; 0.77
- **By state** (states with 500+ site-years, share in top band). Highest: Maine 42.6%, Washington 37.5%, Oregon 33.2%, Connecticut 32.7%, California 32.5%, Montana 32.5%, Rhode Island 31.9%, Nevada 31.5%. Lowest: Louisiana 2.8%, Arkansas 6.8%, Mississippi 7.5%, North Carolina 10.6%, Alabama 10.8%. State gaps may partly reflect reporting practice and state rules, not only safety.
- **By size:** 20 to 249 employees: 172,239 site-years, 21.2% in the top band. 250+: 26,911, 12.0%.

## Pricing simulation (simulated, not actual premiums, claims or loss ratios)

- Scenario A: BLS industry DART rate (year t-1) x hours x claim cost. Scenario B: the same total re-spread within each industry by score (relativity capped 0.6 to 2.0).
- **Central scenario, 2023 by band (1 lowest to 5 highest):**

| Band | Premium change A to B | Simulated loss / premium, A | Simulated loss / premium, B |
| --- | --- | --- | --- |
| 1 lowest | -33.6% | 0.35 | 0.52 |
| 2 | -33.6% | 0.58 | 0.87 |
| 3 | -28.3% | 0.82 | 1.14 |
| 4 | +19.5% | 1.19 | 1.00 |
| 5 highest | +99.4% | 2.10 | 1.05 |

- **2024 central:**

| Band | Premium change A to B | Simulated loss / premium, A | Simulated loss / premium, B |
| --- | --- | --- | --- |
| 1 lowest | -33.3% | 0.38 | 0.57 |
| 2 | -32.8% | 0.62 | 0.92 |
| 3 | -27.4% | 0.87 | 1.20 |
| 4 | +22.4% | 1.26 | 1.03 |
| 5 highest | +102.5% | 2.21 | 1.09 |

- **Premium in the wrong band:** 27.5% to 10.0% (2023), 26.7% to 9.3% (2024). Low scenario: 26.4% to 9.5% (2023), 26.2% to 9.1% (2024).
- **Gap between highest and lowest band ratio:** 6.1x to 2.2x (2023), 5.8x to 2.1x (2024).
- **Overall simulated loss / premium,** identical under A and B by construction: 0.92 (2023), 0.96 (2024). Low scenario: 0.81 and 0.88.
- **Simulated totals, central:** 2023 premium $17.84bn, loss $16.43bn. 2024 premium $16.48bn, loss $15.80bn.

## Not yet computed (label "Pending validation" if shown)

DART rate trend by year for the cohort; any geographic exposure rate, such as injuries per worker or per hour by state (no exposure denominators reconciled). State shares of site-years in the top band are computed above; anything about 2025 outcomes beyond the 2024 starting-year test.

## Risk Landscape tables (`scripts/09_landscape.py`, `outputs/landscape/`; priced portfolio, both test years pooled)

- **States** with 500+ site-years, share of site-years in the top band (site-years in brackets). States below 500 site-years are shown as "too few sites", not ranked: ME 42.6% (768), WA 37.5% (4,314), OR 33.2% (3,065), CT 32.7% (1,952), CA 32.5% (18,521), MT 32.5% (567), RI 31.9% (586), NV 31.5% (1,659), NH 30.7% (1,096), ID 29.5% (1,312), CO 28.6% (3,390), HI 28.0% (610), IA 27.9% (3,439), MN 25.9% (4,887), SD 25.8% (863), MA 25.2% (3,589), PA 23.4% (10,080), NE 22.7% (1,637), NY 22.1% (7,296), NJ 21.2% (3,772), NM 20.9% (680), MD 20.5% (2,419), WI 20.3% (7,073), IL 20.2% (9,040), MO 20.1% (4,261), MI 19.1% (8,143), AZ 19.1% (3,412), FL 18.9% (9,354), ND 16.6% (790), VA 15.7% (3,799), KS 15.0% (2,499), OK 14.7% (2,172), IN 14.6% (5,954), GA 14.5% (6,780), WV 14.4% (840), KY 14.0% (3,267), UT 14.0% (1,858), TN 13.0% (4,729), TX 12.5% (16,580), SC 12.4% (2,889), OH 11.0% (10,773), AL 10.8% (3,453), NC 10.6% (6,545), MS 7.5% (1,741), AR 6.8% (1,832), LA 2.8% (2,751).
- Below 500 site-years (not ranked): DE (448), AK (416), PR (404), VT (326), WY (321), DC (119), GU (45), VI (16), MP (11), AS (3), MH (2), AP (1), AE (1).
- **Crossing rate next year by sector and band** (band 1 to band 5; cells under 100 site-years are too small to read): Agriculture: 4.3%, 8.4%, 13.4%, 22.5%, 45.0%; Construction: 2.5%, 6.8%, 13.6%, 23.3%, 49.5%; Manufacturing: 2.9%, 8.0%, 12.8%, 22.0%, 46.4%; Mining, oil and gas: too few sites (5), too few sites (30), 8.8%, 20.4%, 46.4%; Transport and warehousing: 3.7%, 7.2%, 10.4%, 18.1%, 46.4%; Utilities: 2.5%, 7.0%, 13.7%, 24.5%, 43.6%; Wholesale: 2.4%, 6.8%, 12.7%, 21.7%, 47.0%.
- **Crossing rate next year by sector:** Manufacturing 18.3%, Construction 18.1%, Transport and warehousing 17.7%, Wholesale 19.2%, Utilities 16.8%, Agriculture 18.8%, Mining, oil and gas 19.9%. **By size:** 20-249 employees 19.2%, 250+ employees 12.6%.

## Pricing scenarios, all three claim costs (`outputs/pricing/summary.csv`; simulated)

| Year | Scenario | Premium in the wrong band, A to B | Band spread, A to B | Overall simulated loss / premium |
| --- | --- | --- | --- | --- |
| 2023 | low | 26.4% to 9.5% | 5.9x to 2.2x | 0.81 |
| 2023 | central | 27.5% to 10.0% | 6.1x to 2.2x | 0.92 |
| 2023 | high | 27.5% to 10.0% | 6.1x to 2.2x | 0.92 |
| 2024 | low | 26.2% to 9.1% | 5.6x to 2.1x | 0.88 |
| 2024 | central | 26.7% to 9.3% | 5.8x to 2.1x | 0.96 |
| 2024 | high | 26.7% to 9.3% | 5.8x to 2.1x | 0.96 |

- The high scenario multiplies every premium and every simulated loss by the same factor ($57,314 / $50,076), so all its ratios equal the central scenario. Only the low scenario (days-away cases only) changes the shape.
- Scenario totals (premium, simulated loss): 2023 central $17.84bn, $16.43bn; 2023 high $20.42bn, $18.80bn; 2023 low $10.02bn, $8.11bn; 2024 central $16.48bn, $15.80bn; 2024 high $18.86bn, $18.09bn; 2024 low $9.03bn, $7.95bn.
- Band-level premium change and loss / premium for every year and scenario: `outputs/pricing/bands.csv` (the PricingBands table in Power BI).

## Calibration for every model and test year

- Predicted against observed share by score decile for each model and test year: `outputs/model/calibration.csv` (the Calibration table in Power BI). The scorecard 2023 deciles are listed above.
