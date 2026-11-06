# External benchmarks: what they are and how they're used

## 1. BLS industry injury rates (the industry-only baseline)

**Source.** Bureau of Labor Statistics, Survey of Occupational Injuries and Illnesses (SOII), national Table 1, "Incidence rates of nonfatal occupational injuries and illnesses by industry and case types", and Table A-1, "Percent relative standard errors for rates ... by industry". Read from the official HTML pages on bls.gov on 30 Oct 2026 and saved as `data/raw/bls/table1_YYYY.tsv` and `rse_YYYY.tsv` (the XLSX versions couldn't be downloaded through the available browser; the HTML tables hold the same figures). Years held: Table 1 for 2022, 2023 and 2024; Table A-1 for 2023 and 2024.

**Measure used.** The column "Cases with days away from work, job restriction, or transfer: Total", which is the DART rate. BLS footnote 1 defines every rate as (N / EH) x 200,000, where EH is total hours worked by all employees in the calendar year. That is the same formula OSHA's users guide gives for site-level DART rates, so a site's OSHA rate and its industry's BLS rate are on the same scale (cases per 100 full-time-equivalent workers).

**Industry mapping.** BLS publishes rates by NAICS (2017 edition for 2022 to 2024). Each site is matched on its 3-digit NAICS code. Where the 3-digit row is missing or suppressed, the site uses its 2-digit sector row (BLS codes 31-33 for manufacturing and 48-49 for transport and warehousing). On the 2023 and 2024 test years, 94.3% of sites match at 3 digits. The unmatched codes are 220, 232 and 422 (codes that don't exist in the 2017 NAICS, filed by a small number of sites) and 491 (postal service). OSHA sites may report 2012, 2017 or 2022 NAICS codes. At the 3-digit level these editions are almost identical for the industrial sectors used here.

**Reference period.** BLS publishes year t's rates in November of year t+1. To price year t+1 using only what an underwriter would have had, the baseline for a pair starting in year t uses the **BLS rate for year t-1**: 2022 rates for the 2023 test year, and 2023 rates for the 2024 test year.

**Uncertainty.** BLS Table A-1 gives relative standard errors. For the large industrial 3-digit groups, the DART-rate RSE is about 2% to 7% (2024: food manufacturing 1.7%, warehousing 1.8%, transport equipment 1.6%, specialty trades 3.2%, construction of buildings 7.2%). A 95% range is roughly the rate plus or minus two RSEs. That's small next to the spread between sites, so the baseline isn't the weak link. RSEs are carried into the pricing tables.

**Limits.** BLS excludes farms with fewer than 11 employees, and some 3-digit cells are suppressed. Federal agencies are excluded. BLS rates describe all employers in an industry, while OSHA ITA covers a reporting subset, so the two populations differ. That's exactly why BLS is the industry baseline and OSHA supplies only the site-level signal.

## 2. Claim cost per serious injury

**Source.** National Safety Council, Injury Facts, "Workers' Compensation Costs", which publishes data from the National Council on Compensation Insurance (NCCI) Workers Compensation Statistical Plan database. Read on 29 Oct 2026. NCCI is the original source and NSC the publisher. NCCI notes it gives no warranty for third-party use.

**Definition.** "The average cost for all claims combined for accidents that occurred in 2023-2024 was $50,076." The page's charts describe this as the average cost of a **lost-time** claim (indemnity plus medical), valued at the latest report available to NCCI as of 15 Oct 2026. It covers states where NCCI collects data, not every state.

**How it is used.** Only to turn **observed or expected DART cases** into simulated dollars after the model has done its job. The model never sees claim costs, and no figure is presented as an actual claim or premium.

**Scenarios.**

| Scenario | Rule | Why |
| --- | --- | --- |
| Low | Days-away cases x $50,076; restricted-duty-only cases cost nothing | Many restricted-duty cases never become lost-time claims. This is a deliberate floor that uses the data's own split between the two case types |
| Central | All DART cases x $50,076 | Treats every serious case as an average lost-time claim |
| High | All DART cases x $57,314 | NCCI's average for falls or slips, the most common above-average cause for industrial work (same NSC page), as a severity stress test |

The band-level comparison (Scenario A against B) is relative, so the claim-cost level mostly scales results rather than changing them. The low scenario is the exception, because the mix of days-away and restricted-duty cases differs by band, so it is the real sensitivity test.
