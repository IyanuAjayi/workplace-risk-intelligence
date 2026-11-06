# QA note

Checks run on 31 Oct 2026 against the committed scripts and the data in `data/raw/` (`docs/extract-log.md`).

## Automated tests (`tests/test_panel.py`, 7 of 7 pass)

- DART rate equals (DAFW + DJTR cases) x 200,000 / hours.
- One row per site per year in both site_years and pairs.
- Pairs cover starting years 2016 to 2024.
- The target uses the threshold from the starting year, not the outcome year, and equals dart_rate_next > threshold.
- No prior-year features exist for 2016.
- Yearly prevalence sits between 15% and 25%.
- Cohort rules hold on both sides of every pair (20+ employees, 20,000+ hours).

## Built-in assertions

- `04_pricing.py`: next-year days-away plus restricted cases equal the DART count for every priced site, and premium A and premium B sum to the same total in every year and scenario.
- `03_model.py`: test years 2023 and 2024 are scored once, after settings were chosen on 2022 and models refit on 2016 to 2022.

## Manual checks

- **Row counts:** audit row counts match the raw files (2016: 214,978 to 2025: 400,288). Panel funnel by year in `docs/panel-note.md`.
- **Linking:** the backup match agrees with the OSHA ID 84% to 95% of the time where both exist. A model trained on ID links only gives the same test AUC (`docs/robustness.md`).
- **ZIP formats:** the raw files store `zip_code` differently by year. 2021, 2022 and 2024 lost their leading zeros: 22,813, 25,016 and 29,876 ZIPs have 3 or 4 digits, 99.4% or more of them in New England, New Jersey and Puerto Rico, and no five-digit ZIP in those files starts with 0 (2021 and 2022 also hold 519 and 578 eight-digit ZIP+4 codes). 2023 stores its ZIP+4 codes in scientific notation rounded to three significant digits (14,418 records such as `123E6`, only 1,133 distinct values), and the lost digits cannot be recovered from the file. `link_key` takes the first five characters as stored, so the backup key cannot match a site whose ZIP starts with 0 across 2020 to 2021, 2022 to 2023, 2023 to 2024 or 2024 to 2025 (2021 to 2022 still matches, as both files lost the zeros), and it matches no 2023 scientific-notation record. ID links don't use the ZIP and are unaffected: they still join the 76,758 linked sites (all sectors) whose ZIP differs between the two years only in format. No verified figure changes, because they come from the panel as built, which an in-memory rerun reproduces exactly. Not fixed in the current build. Zero-padding 1 to 4 digit ZIPs in `link_key` would add 7,330 backup links (162,552 to 169,882, none lost) and 2,940 usable pairs (799,158 to 802,098). Test pairs would go from 107,673 and 108,129 to 108,232 and 109,237, the priced portfolio from 199,150 to 200,217, and 2023 prevalence from 18.4% to 18.5%, so the two test years would no longer share 18.4%. Every model and pricing figure would then need rerunning (not done). Checked on 2 Nov against the raw files (read with `read_year`), with `load()` and `link()` from `02_build_panel.py` rerun in memory with and without the padding.
- **Test-year coincidence:** both test years show 18.4% prevalence and 0.729 AUC for "last year only". Checked: the years differ in size (107,673 vs 108,129), mean rates and membership (about 24,000 sites differ), so it is a coincidence, not a duplicated set.
- **BLS duplicates:** Table 1 repeats NAICS codes in its state and local government sections. Only the private-industry rows (first occurrence) are used, and pricing is private-sector only.
- **Privacy:** the Power BI workbook and the GitHub repository (private) hold no establishment names, EINs or street addresses. site_years.parquet, which holds names, isn't committed. The Sites table behind the report is grouped by score year, sector, state, size band and risk band, but 4,716 of its 5,240 groups hold fewer than 100 site-years (88,030 site-years) and 698 hold a single site-year (0.35% of site-years). For a single-site group, the group's DART rate, band, crossing, simulated premium and simulated loss are that site's, and for anyone who rebuilds the cohort from the public file, the counts and sums of small groups can pin down the band of many sites. No page shows a rate, share or premium for a group under 100 site-years (band table cells under 100 read Too few sites, map states under 500 get no tile, and the smallest sector and size group a filter can show is 113). Since 2 Nov the map hover reads Under 500 site-years for smaller states instead of an exact count, the Sector and Size dropdowns take one pick at a time (two multi-sector views could be compared to reveal small groups), and the report's data export is off (`exportDataMode` None in `build_report.py`). Comparing single-pick map views can still reveal band counts for some groups of 10 to 99 site-years, but no longer for a single site. The model, the workbook and the repository stay internal, with report viewers on read access only and no build permission, and the code is handed over as a clean copy without its history (David's decision, 2 Nov). Also since 2 Nov, `outputs/landscape/states.csv` and `sector_bands.csv` leave the rates blank for states under 500 site-years and cells under 100, as the report does; earlier commits still hold the filled-in values. The data for a site-level page (Site Explorer, one row per priced site-year under the internal site_id) was drafted on 1 and 2 Nov and dropped for privacy on 2 Nov: 119,230 of its 199,150 rows (59.9%) were unique on score year, state, 3-digit NAICS, size band and this year's DART rate (to four decimals), and 145,480 (73.1%) with next year's DART rate added. All of these can be recomputed from the public ITA file, which names each establishment, so an internal key would not have kept sites anonymous. The draft sheet was taken out of the workbook, the Power BI model and the current OneDrive file, but on 2 Nov the file's OneDrive version history still held the draft version, for David to delete. The repository's history also holds an earlier site-level workbook: in commits 1f0bea0 (30 Oct) and 1dc73b9 (31 Oct), both pushed to GitHub, its Sites sheet has one row per priced site-year under a numeric site key, and 118,100 of those 199,150 rows (59.3%) are unique on score year, state, 3-digit NAICS, size band and this year's DART rate (to three decimals, as stored), so the same risk applies to anyone given access to the repository.

## Reconciliation of headline figures

These figures appear in more than one output. They differ only where the model or population differs, so every output must say which one it uses.

| Figure | Value | Model and population | Where |
| --- | --- | --- | --- |
| Best model AUC | 0.80 (2023 and 2024) | Gradient boosting, all test pairs | brief, meeting pack, README, Power BI |
| Scorecard AUC | 0.78 (2023), 0.79 (2024) | Scorecard, all test pairs | meeting pack, README |
| Rating-class AUC | 0.59 | M0, all test pairs | brief, meeting pack, README, Power BI |
| Share of next year's crossing sites caught in the top 20% | 51.7% (2023), 51.8% (2024) | Gradient boosting, all test pairs | brief ("52%") |
| Same, scorecard | 50.8%, 51.1% | Scorecard, all test pairs | `outputs/model/metrics.csv` |
| Same, pricing population | 51.4% | Scorecard bands, private-sector pairs, both years pooled | Power BI "Top band capture" |
| Share of flagged top 20% that crossed | 47% | Scorecard, all test pairs (46.97% in the pricing population) | meeting pack, Power BI "Top band hit rate" |
| Premium in the wrong band | 27.5% to 10.0% (2023), 26.7% to 9.3% (2024) | Scorecard, private, central cost | brief ("27% to 10%"), meeting pack ("28% to 10%", 2023 rounded), Power BI |
| Overall simulated loss / premium | 0.92 (2023), 0.96 (2024), same under A and B | Private, central cost | meeting pack, pricing results |

**Action for Power BI and the brief:** cards and sentences quoting "caught in the top 20%" must name the model, because 52% is gradient boosting while the dashboard's 51.4% is the scorecard on the pricing population. The meeting pack rounds 2023's 27.5% to 28% while the brief says 27%. Use "about 27%" everywhere from here on.

## Populations and denominators (checked 31 Oct for the Executive Intelligence design)

Two populations appear in the outputs. Neither figure is wrong; each must be labelled with its own base.

| Step | 2023 | 2024 | Both |
| --- | --- | --- | --- |
| All test pairs (model metrics: AUC, top-20% capture and precision) | 107,673 | 108,129 | 215,802 |
| less pairs with no next-year case split (next year's NAICS left the industrial sectors) | 188 | 149 | 337 |
| less sites not marked private: state government 13,900, local government 2,078, no valid ownership code (OSHA type 0) 337 | 8,300 | 8,015 | 16,315 |
| less sites with no BLS rate | 0 | 0 | 0 |
| **Priced portfolio** (band figures, sectors, states, sizes, pricing) | **99,185** | **99,965** | **199,150** |

Earlier notes and the `04_pricing.py` log called all 16,315 "government sites". 337 of them carry OSHA establishment type 0 (no valid ownership code), so "not marked private" is the accurate label. The counts are unchanged.

**51.4% and 47.0% use the same population (priced portfolio, both test years pooled) and the same numerator, 18,709 band 5 sites that crossed the line, over different denominators:**

- **51.4%, capture:** 18,709 of the 36,389 sites that crossed the line were in band 5. Reads "half of next year's line-crossers were already in the top band".
- **47.0%, hit rate:** 18,709 of the 39,830 band 5 sites crossed. Reads "nearly half of top-band sites crossed". By year: 46.5% (9,380 of 20,191) in 2023 and 47.5% (9,329 of 19,639) in 2024.
- **2.57x lift** is 47.0% over the 18.3% base rate (36,389 of 199,150).
- Band 5 is exactly one fifth of the pooled portfolio (39,830 of 199,150) because the bands are fifths across both years. Within a year it is 20.4% (2023) and 19.6% (2024).
- These are not the model table's figures: scorecard top-20% capture is 50.8% and 51.1%, and precision 46.7% and 46.9%, on all test pairs with the top 20% taken within each year.

## Rounding corrections (1 Nov)

A re-check of every figure in `docs/verified-metrics.md` against its source file, rounding once from the full value, found two figures that had been rounded twice. Both are corrected wherever they appeared; no other figure changed.

| Figure | Was | Correct | Source value |
| --- | --- | --- | --- |
| Last year's rate, 2024, share of crossing sites caught in the top 20% | 49.9% | 49.8% | 9,899 of 19,858 = 0.4985 (`outputs/model/metrics.csv`) |
| Simulated loss / premium, Scenario A, band 4, 2023 central | 1.20 | 1.19 | 1.1950 (`outputs/pricing/bands.csv`) |
| Crossing rate next year, Manufacturing (Risk Landscape) | 18.4% | 18.3% | 14,481 of 78,918 = 0.18349 |
| Crossing rate next year, Agriculture, band 3 | 13.5% | 13.4% | 0.134461 |
| Share of site-years in band 5, Georgia | 14.4% | 14.5% | 0.144543 |
| Share of site-years in band 5, Kentucky | 14.1% | 14.0% | 0.140497 |
| Share of site-years in band 5, Utah | 14.1% | 14.0% | 0.140474 |

The five Risk Landscape corrections (found on 1 Nov when the Power BI measures, which round once from the full value, disagreed with the document) came from `scripts/09_landscape.py` writing shares to four decimals before the document rounded them again. The script now writes six decimals, and every Risk Landscape figure in `docs/verified-metrics.md` was re-derived from those, rounding once. Kentucky and Utah also swap places in the state ranking.

## Power BI report validation (1 Nov)

The live report was checked against `outputs/powerbi/expected_values.csv` and `docs/verified-metrics.md` with DAX queries on the semantic model: every expected value matched to full precision, and every page figure in its default state matched the verified figure (table in `docs/powerbi-build-guide.md`, section 4). Every slicer, page link and Reset filters button was clicked through, including the edge states: Last year's rate on Model Trust (no calibration, note shown), the single-year tiles on Risk Landscape (Mining band 5 shows "Too few sites" in 2023, under 100 site-years) and the low scenario in 2024 on Pricing Lab. The additions deployed later on 1 Nov (sector drill-through, band table data bars and "All bands" row, A to B connectors, map hover) were checked live, and on 2 Nov a sector drill-through filter was found to stay on Risk Landscape until Reset to default in the toolbar (`docs/powerbi-implementation-notes.md`).

**Map interaction.** On Risk Landscape, clicking a state filters nothing else. Since the hover layer was added later on 1 Nov, the click lands on that invisible layer, so the tile no longer highlights either. The page statement ("Every sector's band 5 crossed the line at about twice its rate or more") holds for every sector cell with 100+ band 5 site-years in every test year and size band filter (lowest 1.95x), but not within single states: 68 of 419 state-by-sector cells fall under 1.9x (lowest Washington agriculture, 1.35x on 143 site-years). A state filter would have put a false statement on screen.

## Known issues and limits

- 337 test pairs (0.2%) whose next-year NAICS left the industrial sectors are excluded from pricing, because their case split isn't in site_years. They remain in the model metrics.
- The relativity cap (0.6 to 2.0) is a design choice. The lowest band stays overcharged under B because of the floor.
- Scenario B's relativity uses the crossing probability, not an expected rate. A rate-based relativity is a natural next step.
- BLS tables before 2021 are XLSX only and weren't needed. The pricing uses BLS 2022 and 2023.
- `03_model.py` is slow when the machine is busy (about 50 minutes on 30 Oct with Chrome saturating the CPU, about 15 minutes otherwise).
