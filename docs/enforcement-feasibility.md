# OSHA enforcement data layer: feasibility assessment (task 18)

Prepared 1 Nov 2026 for task 18 on the project task list (P2, parked, "only if matching is defensible"). Corrected on 2 Nov 2026 after two independent fact-checks, one of the external sources and one of the [C] figures; each correction was rechecked against the source or the data before it went in. This is research only: no data file was downloaded. File sizes come from each file's HTTP headers, and file names and counts from each zip file's own index (its central directory), read with small range requests; no data rows were read.

How to read the figures. **[V]** is in `docs/verified-metrics.md`. **[A]** is in `docs/data-audit.md` (written by `scripts/01_audit.py`). **[C]** was computed for this note from the repo's data, and Appendix A gives each computation. Every other figure is quoted from the source cited next to it ([S1] to [S20], listed in section 8). Those are not project results and must not go into the report or brief unless they are first added to `docs/verified-metrics.md`. Effort hours are planning estimates, not data.

Terms. A **risk band** is predicted (scorecard fifths). **Crossing the line** is an observed outcome built from reported injuries (DART cases), not claims. **Inspections and citations** are observed OSHA enforcement records. Any link between them is an association, not a cause.

## Summary

- **Recommendation: leave the layer out of the 6 Nov hand-in.** Keep this note as the output of task 18 and the plan below as next-phase work. If Jowanza wants enforcement context after the 2 Nov meeting, only a small descriptive version fits: fixed-site sectors, the two test years, results by risk band only, about 17 hours, and only if a hand-checked sample shows at least 190 of 200 accepted matches are right.
- **The data exist and are easy to get.** The Department of Labor publishes eleven OSHA enforcement tables on its Open Data Portal, listed as updated daily, as zip files of CSVs that need no key, plus an API that does need one. The three tables a first version needs (inspections, violations, emphasis codes) total 3.87 GB.
- **There is no shared identifier.** Inspections carry the inspected establishment's name, site address, ZIP, NAICS code and headcount, but no EIN and no ITA establishment ID. Matching has to be by name and address inside ZIP blocks. That is defensible for fixed sites (manufacturing, wholesale, warehousing) once a hand check passes, and not defensible for construction, where the ITA record is normally the office or base [S13] (a long project can count as its own establishment [S20]) and inspections are likely to be at jobsites.
- **The value is modest and hard to read.** OSHA's Site-Specific Targeting programme picks inspections using the same ITA DART rates the score uses, though it produces only a small share of inspections (section 5); unprogrammed inspections follow complaints, injuries or fatalities, and referrals; inspections themselves change later injuries; and inspections are rare. As a model feature it would partly echo injury history, and adding it would change every verified model figure days before hand-in.

## 1. What data exist

### 1.1 The tables

All eleven are OSHA tables in the Enforcement category of the DOL Open Data Portal, each listed with update frequency "Daily" [S2]. The old catalog page at enforcedata.dol.gov now redirects to data.dol.gov [S1]. Sizes are as served on 1 Nov 2026 [S4]. Each zip holds CSV files named by build date (for example `2026-11-01_chunk_1.csv`), stored without compression, so the download is about the size of the CSVs. The zip indexes of all eleven files were read again on 2 Nov 2026, while the 1 Nov build was still being served, and confirm the names, the file counts below and the lack of compression [S4].

| Table (portal page) | What it holds | Joins on | Bulk file, 1 Nov 2026 | Needed? |
| --- | --- | --- | --- | --- |
| Inspection ([10334](https://data.dol.gov/datasets/10334)) | One row per inspection: establishment name, site address, city, state, ZIP, NAICS and SIC codes, owner type, inspection type and scope, employees in the establishment, open and close dates, mailing address (36 fields) | `activity_nr` (inspection number) | 1,455,983,407 bytes (1.46 GB), 6 CSV files | Yes |
| Violation ([10338](https://data.dol.gov/datasets/10338)) | One row per citation item: standard cited, violation type, gravity, issuance date, initial and current penalty, contest and final order dates, delete flag (29 fields) | `activity_nr` | 2,276,509,790 bytes (2.28 GB), 14 files | Yes, for citation counts |
| Emphasis Codes ([10337](https://data.dol.gov/datasets/10337)) | National, strategic, local and state emphasis programme codes for each inspection | `activity_nr` | 137,903,963 bytes (0.14 GB), 3 files | Yes, to flag Site-Specific Targeting inspections |
| Accident ([10331](https://data.dol.gov/datasets/10331)), Accident Injury ([10333](https://data.dol.gov/datasets/10333)), Accident Lookup2 ([10330](https://data.dol.gov/datasets/10330)) | Incidents OSHA investigated: event date, description, fatality flag; for each injured person the degree of injury, nature, body part and linked inspection number; code lookups | `summary_nr`, `rel_insp_nr` | 36,458,632, 26,293,817 and 55,275 bytes (63 MB together) | Optional |
| Related Activity ([10336](https://data.dol.gov/datasets/10336)) | Complaints, referrals, accidents and other inspections related to each inspection | `activity_nr` | 124,714,988 bytes (0.12 GB) | No |
| Violation Event ([10357](https://data.dol.gov/datasets/10357)) | Described by DOL as the current status of violations (penalty, abatement and settlement); each row carries an event type, event date and penalty | `activity_nr`, `citation_id` | 1,254,081,959 bytes (1.25 GB) | Only to rebuild citation status as it stood on a past date, if its event dates allow that (not yet checked) |
| Violation Gen Duty Std ([10340](https://data.dol.gov/datasets/10340)), Optional Code Info ([10356](https://data.dol.gov/datasets/10356)), Accident Abstract ([10332](https://data.dol.gov/datasets/10332)) | General duty clause citation text, optional inspection codes, incident narratives | `activity_nr`, `summary_nr` | 758,853,232, 85,330,158 and 130,189,689 bytes | No |

Field lists and code descriptions come from the portal's dataset metadata [S3]. The inspection type codes are: A accident, B complaint, C referral, D monitoring, E variance, F follow-up, G unprogrammed related, H planned, I programmed related, J unprogrammed other, K programmed other, L other, M fatality or catastrophe, N unprogrammed emphasis [S3]. The violation type field is described only as "Violation Type", with no code list [S3], so its values must be confirmed in the data before serious, willful or repeat citations are counted.

### 1.2 How to get them

1. **Bulk files, no key:** `https://data.dol.gov/data-catalog/OSHA/<table>/OSHA_<table>.zip` [S4]. The server answered a plain scripted request with HTTP 200 and supports range requests, so a download can resume. Unlike the ITA files on osha.gov, no browser is needed. One trap: a request sent with no User-Agent header also gets HTTP 200, but the server returns the portal's 9,768-byte web page instead of the zip (checked on 2 Nov 2026 [S4]), so check each file's size, type and SHA-256 after download.
2. **API, key needed:** `https://apiprod.dol.gov/v4/get/OSHA/<table>/<json|xml|csv>` with an `X-API-KEY` parameter; without a key the server returns 401. Keys come from a data.dol.gov account (sign-in through login.gov) and a short registration form, which David would have to complete himself. Each request returns at most 10,000 records or 5 MB, whichever comes first (default 10), with offset paging, field selection and filters [S5]. The catalog and field metadata are open without a key, for example `https://apiprod.dol.gov/v4/datasets/10334` [S3]. For millions of rows the bulk files are simpler.
3. **OSHA's own search pages** (by establishment name, NAICS code or inspection number, linked from https://www.osha.gov/data [S7]) run one query at a time and return lists of matching inspections (Establishment Search shows 20 to a page). By default, Establishment Search covers closed cases with a final order, open cases need a separate search, and the date range is five years, ten at most [S8], so the hand check must run the open-case search too. The pages are useful for the hand check, not for bulk work. On 1 Nov 2026, and again on 2 Nov, their hover text said they reflect inspection data through 12/04/2025 [S7].

### 1.3 Coverage and updates

- OSHA describes the inspection database its Establishment Search queries as holding over 3 million inspections conducted since 1972, updated daily from over 120 OSHA Area Offices and State Plan offices [S8]. Ten of the eleven DOL table descriptions point users back to OSHA's data pages, and the inspection table's `reporting_id` identifies the federal or State Plan jurisdiction [S3], so State Plan inspections appear to be included. That stays an inference until the `reporting_id` values are seen in the download.
- Row counts and latest dates are not published on the portal pages. The first step after any download is to record the latest `open_date` and `load_dt`, because OSHA's search pages were labelled "through 12/04/2025" on 1 Nov 2026 while the DOL files were rebuilt that morning [S4, S7]. The test-year windows below need inspections only up to 31 Dec 2024.
- OSHA's own cautions: the data are always subject to change, open cases change daily, citation details may not appear for 5 days (federal) or 30 days (State Plan) after the employer receives them, and establishment names are not unique, with one establishment sometimes spelled several ways [S8].

### 1.4 Terms of use

- DOL material is generally public domain and may be reused without permission, as long as the use does not imply DOL affiliation or endorsement. The page allows material to be credited to the US Department of Labor, but does not ask for a credit [S6].
- The API terms (updated 5 Aug 2020) add that any service using the API should display the notice "This product uses the US Department of Labor API but is not endorsed or certified by the US Department of Labor", and that DOL may limit or block use [S5]. The bulk files need no key, but the no-endorsement rule still applies.

### 1.5 An adjacent source, not recommended here

OSHA's Severe Injury Reports [S19] (amputations, in-patient hospitalisations and eye losses reported by employers since 1 Jan 2015, federal-jurisdiction states only) also carry names, addresses and NAICS codes. They are reported injuries of the kind the target counts, so as features they would leak the outcome, and they would need the same matching.

## 2. Fields that could link an inspection to an ITA site

| Purpose | ITA Form 300A file | Inspection table [S3] | Use in the match |
| --- | --- | --- | --- |
| Name | `establishment_name` (almost never blank: 13 records in the ten files, none from 2023 on [C]) and `company_name` | `estab_name`, the establishment inspected | Scored against both ITA names, keeping the better |
| Street address | `street_address` (blank on 34 records in the ten files [C]) | `site_address`; also `mail_street` | House number and street, scored |
| City and state | `city` (blank on 37 records [C]), `state` (never blank [C]) | `site_city`, `site_state` | State must agree; city is the fallback block when there is no usable ZIP |
| ZIP | `zip_code` (blank on 1 record, in 2019 [C], but with format faults, see 2.2) | `site_zip`, `mail_zip` | Block |
| Industry | `naics_code`, 6 digits on every record [A] | `naics_code` (under SST the inspector verifies it at the opening conference [S9]) and `sic_code` | Block on 2 digits, score on 6, 4 and 3 |
| Size | `annual_average_employees` | `nr_in_estab` | Scored |
| Ownership | `establishment_type` (1 private, 2 state, 3 local government) | `owner_type` (A private, B local, C state, D federal) | Filter to private |
| Identifiers | `establishment_id` (can change when a site re-registers); `ein` (blank on every 2016 record and on all but two 2017 records [A]) | `activity_nr` (the inspection); `host_est_key` ("internal establishment key") | None shared. No public crosswalk was found, though a search cannot prove that none exists. OSHA itself matches newly opened inspections to its list of possible ITA non-filers (establishments that "may have failed to submit") on "nine data elements" and then has Area Offices confirm each match by hand [S16] |

The blank counts are exact counts over the ten raw files (Appendix A, item 9). `docs/data-audit.md` shows them as 0.0% because it rounds.

### 2.1 The project rule on names and addresses

The repo keeps EINs and street addresses out of everything after the first read (README; `standardise` in `src/osha.py` leaves them out), and keeps establishment and company names internal, never exported (`docs/data-dictionary.md`). A matching run would therefore re-read from `data/raw/`, inside the matching script, every field the panel does not keep: the street address, the city (`site_years` keeps only state and ZIP), and the names and addresses of ITA filers outside the industrial sectors, which `site_years` leaves out but which compete for matches (section 3, step 1). It would use names and addresses in memory only and write out flags and counts with no names or addresses (section 3, step 7).

### 2.2 What the ITA side looks like for matching [C]

**ZIP codes need repair before blocking.** The ITA files store ZIPs in different formats by year. Leading zeros were dropped in 2021, 2022 and 2024 (ZIPs starting with 0: New England, New Jersey, Puerto Rico and the Virgin Islands): in those years at least 99.6% of the 3 or 4 digit ZIPs are in those states, and the 2021 and 2022 files also hold 519 and 578 eight-digit values, all but two in those states, which are ZIP+4 codes that lost their leading zero (counted under "Other" below) [C]. In 2016 to 2020 the 3 or 4 digit ZIPs are mostly not lost zeros: only 2 to 7 a year are in those states, and in 2016, 163 of the 302 are in Illinois [C], so padding them would create wrong ZIPs. In 2023, 14,418 records hold scientific notation (three digits, E, one digit, a pattern like `123E6`), which collapses them into 1,133 distinct values, so those ZIPs are unusable. The 2025 file is clean.

| ITA file | Records | Five digits | ZIP+4 | 3 or 4 digits | Scientific notation | Other |
| --- | --- | --- | --- | --- | --- | --- |
| 2016 | 214,978 | 206,376 | 8,128 | 302 | 0 | 172 |
| 2017 | 259,758 | 242,662 | 16,881 | 44 | 0 | 171 |
| 2018 | 289,534 | 272,567 | 16,699 | 42 | 0 | 226 |
| 2019 | 290,475 | 270,884 | 19,394 | 53 | 0 | 144 |
| 2020 | 293,391 | 284,601 | 8,310 | 84 | 0 | 396 |
| 2021 | 317,978 | 277,020 | 17,470 | 22,813 | 0 | 675 |
| 2022 | 346,799 | 310,922 | 10,114 | 25,016 | 0 | 747 |
| 2023 | 394,234 | 379,816 | 0 | 0 | 14,418 | 0 |
| 2024 | 398,620 | 368,738 | 0 | 29,876 | 0 | 6 |
| 2025 | 400,288 | 400,288 | 0 | 0 | 0 | 0 |

In the priced portfolio, this leaves 1,977 of the 99,185 site-years of 2023 without a usable ZIP, and 6,287 of the 99,965 site-years of 2024 with a short ZIP that padding with zeros repairs. All 1,977 have a usable ZIP on the same site's 2024 record [C], which can stand in for the missing one (section 3, step 2).

A side note for `docs/qa-note.md`: the panel's backup link key compares the first five characters of the ZIP exactly, so records whose ZIP format changed between two consecutive files cannot join on that key across that year boundary. The ID link is unaffected and carries most links. No verified figure changes.

**ZIP alone does not separate sites.** Priced portfolio, after ZIP repair, compared against every establishment in the same year's ITA file (all sectors, one record per establishment ID):

| | 2023 | 2024 |
| --- | --- | --- |
| Portfolio site-years [V] | 99,185 | 99,965 |
| With a usable ZIP | 97,208 | 99,965 |
| ITA records in the same ZIP, the site's own included: median | 43 | 46 |
| ITA records in the same ZIP, the site's own included: 90th percentile | 117 | 123 |
| The only ITA record in its ZIP and 2-digit NAICS (31 to 33 as one, as in Pass A) | 12.7% | 12.5% |
| The only ITA record in its ZIP and 6-digit NAICS | 65.5% | 64.8% |
| Site-years sharing a normalised name with another ITA record in the same ZIP | 3,097 | 3,390 |

Without the borrowed 2024 ZIP, the 1,977 site-years of 2023 would fall back to a state and city block, which holds a median of 96 ITA records.

**ITA names come in two versions.** In the 199,150 priced site-years [V], the establishment and company names are the same after normalisation for 67,017 (33.7%), differ for 121,655 (61.1%; in 10 of these the establishment name is the blank one), and the company name is blank for 10,478 (5.3%). An inspection's establishment name may match either, so both are scored.

**Fixed sites are the matchable core.** OSHA's recordkeeping rule says that where employees do not work at one physical location (construction, transportation, utilities and similar), the establishment is the office, terminal or station that supervises or bases the work [S13]. That is the normal case, not the only one: each establishment expected to operate for a year or longer needs its own 300 Log, and OSHA treats a continuous presence at a job site for a year or longer as an establishment [S20], so a long construction project can be its own establishment and, if it files with ITA, its record can carry a jobsite address. Even so, for construction an inspection's site address is likely to be a jobsite that is not an ITA establishment. Splitting the priced portfolio:

| Tier | Sectors | Site-years | Share |
| --- | --- | --- | --- |
| Fixed sites: match | Manufacturing (78,918 [V]), wholesale (27,123 [V]), warehousing, NAICS 493 (10,214 [C]) | 116,255 | 58.4% |
| Mixed: match, report separately | Agriculture (6,335 [V]), utilities (6,729 [V]), mining, oil and gas (848 [V]), transport other than warehousing (25,873 [C]) | 39,785 | 20.0% |
| Construction: do not match | Construction (43,110 [V]) | 43,110 | 21.6% |

## 3. A defensible matching plan

Rules are fixed before anything is compared with risk bands, as the panel rules were (`docs/panel-note.md`). It is a scored match with an accept threshold, a review band and a reject threshold, the approach the BLS and NORC set out for linking ITA records to the BLS injury survey, where there was also no shared identifier [S17].

1. **Scope.** Inspections with owner type A (private), opened 1 Jan 2021 to 31 Dec 2024, excluding records coded "no inspection" (scope D) and construction (NAICS 23). That covers three-year windows for test years 2023 and 2024. Each inspection is matched against the ITA file for the calendar year it opened, using all sectors so that other ITA filers compete for the match. Flags then follow the site to its test-year record through the panel's `site_id`; if the site has no ITA record in the year an inspection opened, its nearest record inside the window is used.
2. **Normalise, in memory only.** Names: upper case, "&" to AND, punctuation removed, the legal suffixes already stripped by `link_key` in `src/osha.py` (INC, LLC, CORP, CORPORATION, CO, COMPANY, LTD, LP, THE) plus LLP and PLLC, a short fixed list of abbreviations (MFG, INTL, SVCS and similar), and "DBA" names split into two candidates. Addresses: house number separated from the street, and a fixed list of street suffix and direction abbreviations. ZIPs: first five digits of ZIP+4; 8-digit values padded to nine digits, then the first five kept (the 2021 and 2022 ZIP+4 codes that lost their leading zero; checked against the same establishment's 2025 ZIP, this gives the same ZIP for 328 of 336 in 2021 and 296 of 305 in 2022 [C]); 3 or 4 digit ZIPs padded with leading zeros in the 2021 to 2024 files, but treated as missing in the 2016 to 2020 files, where they are mostly not lost zeros (section 2.2); scientific notation treated as missing. A site-year still without a usable ZIP takes the repaired ZIP of the same site's record in the next or previous year (through `site_id`; by `establishment_id` for ITA filers outside the panel). All 1,977 portfolio site-years of 2023 without a usable ZIP get one this way from their 2024 record [C]. NAICS: kept at 6, 4, 3 and 2 digits.
3. **Block.** Pass A: same ZIP and same 2-digit NAICS (31 to 33 count as one). Pass B: same ZIP and same house number, which rescues pairs whose NAICS codes disagree (the inspector's code is checked on site [S9], the ITA code is the employer's own). Pass C, for records still without a usable ZIP: same state, same normalised city and same first name word. Pairs from all passes are pooled.
4. **Score each pair, 0 to 100.** Name similarity, using the better of the two ITA names, with rare words counting more than common ones plus a Jaro-Winkler string score as in [S17]: up to 50. Same house number: 15. Street name similarity: up to 10. NAICS agreement at 6, 4, 3 or 2 digits: 10, 7, 5 or 2. Headcounts within a factor of three: 10. Same city: 5. These are starting weights.
5. **Decide.** Accept a pair when its score clears the upper threshold, it is the best candidate for that inspection, and it leads the runner-up by a set margin. Pairs between the two thresholds are checked by hand; pairs below the lower one are rejected. Each inspection links to at most one ITA establishment; a site may have several inspections. Thresholds and the margin are set on a tuning sample of 100 pairs drawn across the score range.
6. **Validate by hand, on fresh samples.**
   - Precision: a simple random sample of 200 accepted pairs, checked side by side on name, address, city, NAICS and headcount, with OSHA's Establishment Search as a second look where needed. **The gate is at least 190 of 200 correct (95.0%; Wilson 95% interval 91.0% to 97.3%).** At 186 of 200 (93.0%) the interval's lower end is 88.6%, which fails: tighten the threshold, draw a new sample and check again. If it fails twice, drop the layer and say so.
   - Boundary: 50 accepted pairs from just above the threshold, to see where errors cluster.
   - Missed matches: 100 unmatched private inspections in fixed-site industries with 20 or more employees, in ZIPs that hold ITA records, searched by hand. This estimates recall. Because some inspected sites are genuinely absent from ITA, the flag is always called "matched inspection", never "not inspected".
   - The mixed tier gets its own 50-pair precision check and is reported separately.
   - Only verdicts are saved (pair number, correct, wrong or unsure). Pair numbers follow a fixed sort order, so a rebuilt pair table lines up with the saved verdicts. Names are seen on screen during the check and never written to the repo.
7. **What is kept: flags and counts only.** One row per portfolio site-year in `data/final/` (internal, never exported): matched inspection in the three years, programmed, Site-Specific Targeting, unprogrammed, fatality or catastrophe, number of serious, willful or repeat citation items, and the match tier. No names, addresses, inspection numbers or penalties. Exports, the report and the brief would get only aggregates by risk band, sector and size, with the project's small-cell rules (cells under 100 site-years shown as too few sites; any state cut only for states with 500 or more site-years, as in the state ranking). The pair table (inspection number and ITA establishment ID for each accepted pair) is needed only while the flags are built and checked, and is deleted once the counts are frozen, because those two numbers identify a named employer through OSHA's inspection search [S7] and the raw ITA file. A rerun rebuilds it from the raw files with the same fixed rules. Keeping it for audits would be an exception to this step that David would have to approve and record.

Acceptance checks before any figure is used: the precision gate passes; the latest `open_date` in the download is on or after 31 Dec 2024; the violation type codes and the Site-Specific Targeting codes (`SSTARG21` and `SSTARG23` in the two most recent directives [S10, S9]; earlier cycles not checked) are confirmed in the data; the `reporting_id` values show which records come from State Plans; the timing assertions in section 4 pass; and, for the full version only, Violation Event's event dates are shown to allow citation status to be rebuilt as of a past date.

## 4. What the layer could add

**As descriptive context (the only version recommended if anything is done).** For the fixed-site tier of the priced portfolio, by risk band: the share of site-years with a matched inspection in the three calendar years up to the test year; the share with serious, willful or repeat citations; the share with a fatality or catastrophe inspection; and programmed against unprogrammed, with Site-Specific Targeting inspections shown separately. That answers a side question, whether OSHA's attention and the score point at the same sites. It would be read as an association between a predicted band and observed enforcement records, not as validation, because of the circularity in section 5.

**As model features (next phase only).** The same flags tested in a separate model next to the scorecard, never replacing it, with the AUC compared with and without them on the same pairs in both test years. Timing rules, written as assertions:

- A year-t feature uses only inspections opened from 1 Jan of year t-2 to 31 Dec of year t. Nothing opened in the outcome year t+1 is used.
- A citation counts only if issued by 31 Dec of year t. Citations can be issued up to six months after a violation [S15], so inspections opened late in year t may show none yet.
- The downloaded citation status is the status today, after settlements and deletions, which is look-ahead for older years: the Violation table holds the current penalty next to the initial one, and DOL describes Violation Event as the current status of violations [S3]. For model use the status would have to be rebuilt as of 31 Dec of year t from Violation Event (another 1.25 GB), if its event dates allow that, which is not yet checked. For descriptive use it is reported as "status at the download date".

Nothing here changes the scorecard, the bands or the pricing simulation (simulated: not actual premiums, claims or loss ratios) unless the feature route is taken.

## 5. Risks

| Risk | Why it matters | What would contain it |
| --- | --- | --- |
| Circularity with Site-Specific Targeting | Site-Specific Targeting (SST), OSHA's main site-specific programmed inspection initiative for non-construction workplaces with 20 or more employees, picks sites from ITA Form 300A data: high DART rates (one cut-off for manufacturing, another for the other non-construction industries), rates at least twice the private-sector average in CY 2022 and rising each year from CY 2021 to 2023, plus random samples of low-rate sites and of non-filers [S9]. That overlaps the project's cohort and uses its main signal, so an inspection flag partly re-measures past injury rates. SST is a small share of inspections, though: 652 from 7 Apr 2023 to 12 Dec 2024 [S9], against 17,170 programmed inspections in FY 2024 alone [S11], which OSHA describes as inspections initiated by emphasis programmes [S11]. The lists lag the data: Form 300A for a year is due by 2 March of the next [S14], and CY 2023 rates drive the directive effective 20 May 2025 [S9]. Last year's rate alone already scores AUC 0.729 [V] | Flag SST inspections from the emphasis codes and show them separately; treat any lift as an echo of injury history until shown otherwise |
| Selection works both ways | Sites with a comprehensive inspection in the past 36 months are deleted from SST lists [S9], so a recent inspection makes a further SST inspection less likely | Describe, do not model, until the selection rules for the whole period are mapped |
| Leakage from the outcome year | Accident and fatality inspections can follow severe injuries that employers must report to OSHA, though not every report leads to an inspection: depending on the case, OSHA may instead ask the employer to investigate [S19]. The same injuries can appear as DART cases in the 300A; an inspection opened in year t+1 can describe the very injuries the target counts | Strict windows ending 31 Dec of year t, asserted in code |
| Look-ahead in citation status | Citation items change through contests and settlements after issue, and the files carry current values: the Violation table has the current penalty next to the initial one, and DOL describes Violation Event as the current status of violations [S3]. OSHA also warns that the data are always subject to change [S8] | Descriptive use labelled "status at download date"; for any model, rebuild as of year t, if Violation Event allows it |
| Inspections change later injuries and recording | Johnson, Levine and Toffel estimate that inspections in the OSHA targeting programme they study led, on average, to 2.4 (9%) fewer serious injuries per inspection over the next five years [S18]. SST inspections also review three years of injury logs [S9], which can change what is recorded | Read every result as an association; never as "inspected sites are riskier" or "safer" |
| Rarity | Federal OSHA conducted 30,273 inspections in FY 2025 (its total, not only the sectors priced here): 13,962 programmed and 16,311 unprogrammed (6,664 complaints, 6,079 referrals, 909 fatality or catastrophe, 2,659 other) [S11]. It conducted 34,625 in FY 2024 [S11]; OSHA's statistics page gives 34,696 for the same year [S12], but 34,625 comes from the same table as the FY 2025 figures, so the two years compare like with like. The 2025 ITA file alone holds 400,288 establishments [V]. SST itself produced 515 inspections from 1 Oct 2019 to 1 Apr 2022 and 652 from 7 Apr 2023 to 12 Dec 2024 [S10, S9]. A three-year flag is expected to be uncommon; its real rate is unknown until the match is run | Report counts beside every share; respect the 100 site-year small-cell rule |
| Bias by sector, state and programme | Unprogrammed inspections follow complaints, referrals and fatalities or catastrophes [S11]; programmed ones follow national and local emphasis programmes (FY 2025 examples include heat, silica, combustible dust and falls [S11]); State Plans run their own targeting, which may copy SST or differ from it [S9]. Inspection rates differ across sectors and states for reasons other than a site's risk | Never read "no matched inspection" as "safe"; compare within sector and state only, showing states only at 500 or more site-years |
| Reporting lags and freshness | Citations up to six months after a violation [S15]; citation details visible 5 or 30 days after the employer receives them [S8]; OSHA's search pages labelled "through 12/04/2025" on 1 Nov 2026 [S7] | Record the download date and latest `open_date` and `load_dt` in `docs/extract-log.md`, as for ITA |
| Matching errors | No shared ID; names are not unique and vary in spelling [S8]; a portfolio site's ZIP holds a median of 43 (2023) or 46 (2024) ITA records [C]; 34.5% (2023) and 35.2% (2024) of portfolio sites with a usable ZIP share their ZIP and 6-digit NAICS with another ITA record [C]; 2023 ZIPs are broken for 1,977 portfolio site-years [C], though all of them can borrow the ZIP on their 2024 record [C]. Even OSHA confirms its own ITA matches by hand [S16] | Scored match, two thresholds, the 190 of 200 precision gate, a recall check |
| Construction and mobile work | Construction, and some transport and utility work, happens away from the establishment that files with ITA, which is usually the office, terminal or base [S13, S20], so inspections there are likely to carry a jobsite address | Construction left out; the mixed tier reported separately |
| Privacy and reputation | The match handles named employers' enforcement histories next to a risk score | Flags and counts only, with the pair table deleted once the counts are frozen; aggregates only in anything shared, in line with decision 2 in `docs/monday-meeting-pack.md` |
| Time and verified figures | Every shown figure must be in `docs/verified-metrics.md`; a model feature would change every model figure; the report build tools are owned by the main session | Not before 6 Nov; if done at all, descriptive tables added to verified metrics first |

## 6. Effort and recommendation

Planning estimates, for one person working in the repo:

| Step | Descriptive version (hours) | Full feature version (hours) |
| --- | --- | --- |
| Download three files (3.87 GB), log size, date and SHA-256 | 1 | 1 |
| Load to Parquet, filter, check dates and code values | 2 | 3 |
| Normalisation, ZIP repair, blocking, scoring, unit tests | 4 | 5 |
| Tuning sample (100 pairs), precision (200 + 50), recall (100), mixed tier (50) | 6 | 9 (more years, more ZIP formats) |
| Flags for portfolio site-years and tables by band, sector and size | 2 | 2 |
| Inspections from 2014 for every starting year 2016 to 2024 | 0 | 3 |
| Model rerun with and without flags, timing assertions, robustness | 0 | 6 |
| QA, verified-metrics entries, write-up | 2 | 3 |
| Brief, meeting pack and report changes | 0 | 4 |
| **Total** | **about 17** | **about 36** |

**Recommendation: leave it out of the 6 Nov hand-in.** Reasons:

1. **Time.** Even the descriptive version is about two working days, against the four days left, which already hold the changes from the 2 Nov review, the article if Jowanza wants it, and hand-in QA. New figures also have to be verified and checked in a report whose build tools the main session owns.
2. **Value.** The layer partly re-measures injury history the model already uses (Site-Specific Targeting selects on ITA DART rates, and accident inspections follow reported injuries), inspections are rare and unevenly spread, and inspections change later injuries. Any result would be an association that is hard to explain to an underwriter, and it would not answer the project's question (does a site's own injury record predict its next year).
3. **Defensibility.** Matching can be made defensible for the fixed-site 58.4% of the priced portfolio after the hand check, not for construction (21.6%), and only with a caveat for the rest.
4. **Privacy.** It brings named enforcement histories into the project for little gain.

**If Jowanza asks for it on 2 Nov:** do the descriptive version only, fixed-site tier, test years 2023 and 2024, aggregates by risk band, behind the 190 of 200 gate, and drop it if the gate fails. **Next phase:** the full plan, with citation status rebuilt as of each year from Violation Event (if its event dates allow that) and the feature tested in a separate model.

## 7. Downloads needed if David approves

Sizes as served on 1 Nov 2026 [S4]. The portal lists the files as updated daily [S2], so record the actual size, date and SHA-256 at download in `docs/extract-log.md`, and check that each file is a zip, not the portal's 9,768-byte web page (section 1.2). Put them in `data/raw/osha_enforcement/` (not committed). No API key is needed.

| File | URL | Size | Why |
| --- | --- | --- | --- |
| OSHA_inspection.zip | https://data.dol.gov/data-catalog/OSHA/inspection/OSHA_inspection.zip | 1,455,983,407 bytes (1.46 GB) | Names, addresses, NAICS, dates and type of every inspection |
| OSHA_violation.zip | https://data.dol.gov/data-catalog/OSHA/violation/OSHA_violation.zip | 2,276,509,790 bytes (2.28 GB) | Serious, willful and repeat citation counts |
| OSHA_emphasis_codes.zip | https://data.dol.gov/data-catalog/OSHA/emphasis_codes/OSHA_emphasis_codes.zip | 137,903,963 bytes (0.14 GB) | Flags Site-Specific Targeting inspections |
| **Core total** | | **3,870,397,160 bytes (3.87 GB)** | |
| OSHA_accident.zip (optional) | https://data.dol.gov/data-catalog/OSHA/accident/OSHA_accident.zip | 36,458,632 bytes | Fatality flag and event dates |
| OSHA_accident_injury.zip (optional) | https://data.dol.gov/data-catalog/OSHA/accident_injury/OSHA_accident_injury.zip | 26,293,817 bytes | Degree of injury, linked inspection number |
| OSHA_accident_lookup2.zip (optional) | https://data.dol.gov/data-catalog/OSHA/accident_lookup2/OSHA_accident_lookup2.zip | 55,275 bytes | Code descriptions for the two accident tables |
| Only for the full version | https://data.dol.gov/data-catalog/OSHA/violation_event/OSHA_violation_event.zip | 1,254,081,959 bytes (1.25 GB) | Citation status as of a past date |

Without citation counts (inspection flags only), the inspection and emphasis code files alone are 1,593,887,370 bytes (1.59 GB). The project disk had 52 GiB free on 1 Nov 2026.

## 8. Sources

All read on 1 Nov 2026. The corrections of 2 Nov 2026 rest on the same sources, reread that day, plus [S20] and the added links in [S11] and [S19].

- [S1] DOL Open Data Portal, https://data.dol.gov/ ; the old catalog https://enforcedata.dol.gov/views/data_catalogs.php returns a permanent redirect to it.
- [S2] DOL API dataset catalog, https://apiprod.dol.gov/v4/datasets?page=2 and https://apiprod.dol.gov/v4/datasets?page=4 (the OSHA entries, category Enforcement, frequency Daily).
- [S3] Dataset pages and metadata (field names, descriptions, inspection type and owner type codes): https://data.dol.gov/datasets/10334 (Inspection), /10338 (Violation), /10337 (Emphasis Codes), /10331 (Accident), /10333 (Accident Injury), /10330 (Accident Lookup2), /10336 (Related Activity), /10357 (Violation Event), /10340 (Violation Gen Duty Std), /10356 (Optional Code Info), /10332 (Accident Abstract); metadata at https://apiprod.dol.gov/v4/datasets/10334 and the same pattern for each ID.
- [S4] Bulk files, https://data.dol.gov/data-catalog/OSHA/<table>/OSHA_<table>.zip : sizes and last-modified dates from HTTP headers; file names and chunk counts from each zip's central directory, read with range requests (no data rows read). Rechecked on 2 Nov 2026 at 00:21 GMT, while the 1 Nov build was still served: same sizes, and the same names, counts and storage without compression in all eleven indexes. That day a request with no User-Agent header returned the portal's 9,768-byte web page (type text/html) instead of the zip.
- [S5] DOL Open Data Portal user guide (API parameters, key, 10,000 records or 5 MB per request), https://data.dol.gov/user-guide ; API terms of service (updated 5 Aug 2020), shown in a pop-up on the API key registration form, https://data.dol.gov/questionnaire , which is submitted from a signed-in account. The sign-in page, https://data.dol.gov/registration , shows a different "Terms of Use" notice. The portal draws its pages in the browser, so both texts were read from the site's script.
- [S6] DOL copyright information, https://www.dol.gov/general/aboutdol/copyright
- [S7] OSHA data page, https://www.osha.gov/data (hover text "Reflects inspection data through 12/04/2025" on the inspection search links).
- [S8] OSHA Establishment Search help, https://www.osha.gov/help/establishment-search
- [S9] OSHA Instruction CPL 02-01-067, Site-Specific Targeting, signed 8 Apr 2025, effective 20 May 2025, https://www.osha.gov/sites/default/files/enforcement/directives/CPL-02-01-067.pdf (listing at https://www.osha.gov/enforcement/directives/cpl-02-01-067).
- [S10] OSHA Instruction CPL 02-01-064, Site-Specific Targeting, effective 7 Feb 2023, https://www.osha.gov/sites/default/files/enforcement/directives/cpl-02-01-064.pdf
- [S11] OSHA enforcement summary, FY 2025, https://www.osha.gov/enforcement/current-enforcement-summary (its table also gives FY 2020 to 2024, including 34,625 inspections and 17,170 programmed in FY 2024); FY 2024 summary, https://www.osha.gov/enforcement/2024-enforcement-summary (also 34,625).
- [S12] OSHA commonly used statistics (FY 2024 total federal inspections 34,696, which differs from the 34,625 in [S11]; about 1,850 federal and state inspectors), https://www.osha.gov/data/commonstats
- [S13] 29 CFR 1904.46, definition of establishment, https://www.osha.gov/laws-regs/regulations/standardnumber/1904/1904.46
- [S14] 29 CFR 1904.41 (Form 300A due by 2 March of the following year), https://www.osha.gov/laws-regs/regulations/standardnumber/1904/1904.41
- [S15] OSH Act section 9(c) (no citation after six months), https://www.osha.gov/laws-regs/oshact/section_9
- [S16] OSHA memorandum, ITA non-responder enforcement program, 23 Mar 2026, https://www.osha.gov/memos/2026-03-23/injury-tracking-application-ita-non-responder-enforcement-program
- [S17] NORC at the University of Chicago for BLS, Matching Survey of Occupational Injuries and Illnesses Data to OSHA ITA Data, 17 Dec 2018, https://www.bls.gov/iif/data-quality-research/norc-fy2019-data-matching-report.pdf
- [S18] Johnson, Levine and Toffel (2023), Improving Regulatory Effectiveness through Better Targeting: Evidence from OSHA, American Economic Journal: Applied Economics 15(4): 30 to 67, https://www.aeaweb.org/doi/10.1257/app.20200659 (abstract read at https://econpapers.repec.org/RePEc:aea:aejapp:v:15:y:2023:i:4:p:30-67).
- [S19] OSHA Severe Injury Reports, https://www.osha.gov/severeinjury ; the dashboard, which lists the establishment's name, address and NAICS code for each report, https://www.osha.gov/severe-injury-reports ; and the 2024 annual report (OSHA either asks the employer to investigate or opens an on-site inspection), https://www.osha.gov/sites/default/files/2024_Annual_Report_of_Fed_OSHA_SIRs.pdf
- [S20] 29 CFR 1904.30(a), a separate 300 Log for each establishment expected to be in operation for one year or longer, https://www.osha.gov/laws-regs/regulations/standardnumber/1904/1904.30 ; OSHA interpretation letter of 28 Feb 2014 (a continuous presence at a site for a year or longer is an establishment), https://www.osha.gov/laws-regs/standardinterpretations/2014-02-28-0

Not verified: the violation type code values; Site-Specific Targeting codes for the 2018 to 2020 cycles; row counts and the latest dates in the bulk files; which records are State Plan records (`reporting_id`); whether Violation Event's event dates allow citation status to be rebuilt as of a past date (all need the download). Not provable: that no public crosswalk between ITA establishment IDs and inspection numbers exists. None was found in the OSHA and DOL documentation or a web search, and OSHA's own non-filer matching [S16] suggests there is none.

## Appendix A: how the [C] figures were computed

All from the repo's data with `.venv/bin/python`, on 1 Nov 2026. An independent fact-check recomputed every [C] figure on 1 and 2 Nov 2026 and found each one exact. The figures added in the corrections (in items 1 to 3 and 5, and items 9 to 11) were computed on 2 Nov 2026. Scripts were run from a scratch folder and not added to the repo. Names, addresses and ZIPs were handled in memory only and printed only as counts.

1. **ZIP formats by year.** Each raw ITA file in `data/raw/` read with `read_year` from `src/osha.py`; `zip_code` stripped and classed by regular expression, in this order: five digits `^\d{5}$`; ZIP+4 `^\d{5}-?\d{4}$`; 3 or 4 digits `^\d{3,4}$`; scientific notation (contains "E"); other is everything else. The 1,133 figure is the number of distinct `zip_code` values among the 14,418 scientific-notation records of 2023, all shaped as three digits, E, one digit. States whose ZIPs start with 0 are taken as CT, MA, ME, NH, NJ, RI, VT, PR, VI and AE (armed forces mail). The 3 or 4 digit ZIPs in those states: 22,759 of 22,813 (2021), 24,948 of 25,016 (2022) and 29,762 of 29,876 (2024), each 99.6% or more; in 2016 to 2020, 4, 3, 7, 4 and 2 records. The 2016 3 or 4 digit ZIPs by state: Illinois 163, Pennsylvania 59, New York 25 of the 302. Eight-digit values (`^\d{8}$`, all within "Other"): 519 in 2021, all in those states, and 578 in 2022, 576 in those states.
2. **Portfolio ZIP repair.** `data/final/pricing_sites.parquet` (199,150 rows) joined to `data/final/site_years.parquet` on `site_id` and `year` to get each site-year's `establishment_id`, then to that year's raw ITA file. Raw files were standardised and de-duplicated as in `scripts/02_build_panel.py` (latest submission kept per `establishment_id`), giving 394,231 records for 2023 and 398,620 for 2024. Repair: five digits or ZIP+4 gives the first five digits; 3 or 4 digits are left-padded with zeros; anything else, and 00000, is missing. 1,977 is the 2023 portfolio count with a missing repaired ZIP; 6,287 is the 2024 portfolio count whose stored five-character ZIP was 3 or 4 digits long. For the 1,977, the same `site_id`'s 2024 record in `site_years.parquet`, joined on `establishment_id` to the de-duplicated 2024 raw file and repaired the same way, has a usable ZIP in all 1,977 cases. Eight-digit check: the 2021 and 2022 raw files de-duplicated the same way hold 514 and 578 eight-digit ZIPs; padded to nine digits, their first five equal the same `establishment_id`'s repaired 2025 ZIP for 328 of the 336 (2021) and 296 of the 305 (2022) that have one.
3. **Block sizes.** For each portfolio site-year, the number of records in that year's de-duplicated ITA file (all sectors) with the same repaired ZIP, the site's own record included; median and 90th percentile over site-years with a usable ZIP (without the site's own record, the medians are 42 and 45). "Only ITA record in its ZIP and 2-digit NAICS" is the share of those site-years where the count of records with the same repaired ZIP and the same 2-digit NAICS code, with 31, 32 and 33 counted as one as in Pass A, is 1: 12,386 of 97,208 (12.7%) in 2023 and 12,482 of 99,965 (12.5%) in 2024. On the plain first two digits the shares would be 16,143 (16.6%) and 16,375 (16.4%). The 6-digit share is the same count on all six digits: 63,672 (65.5%) and 64,801 (64.8%). The shares that do share their ZIP and 6-digit NAICS with another record are 1 minus those: 1 - 0.655 = 0.345 (2023) and 1 - 0.648 = 0.352 (2024). The 96 is the median count of records with the same state and normalised city (letters only, upper case) for the 1,977 site-years without a usable ZIP.
4. **Shared names.** Names normalised with the same rule as `link_key` in `src/osha.py`; a site-year counts when more than one record in that year's de-duplicated ITA file has the same repaired ZIP and normalised establishment name (3,097 in 2023, 3,390 in 2024).
5. **Two name versions.** Over the 199,150 priced site-years: company name blank after normalisation, 10,478; normalised establishment name equal to normalised company name, 67,017; company name present and different, 121,655, of which 10 have a blank normalised establishment name; each divided by 199,150.
6. **Sector tiers.** From `pricing_sites.parquet` columns `sector` and `naics3`: fixed sites are Manufacturing, Wholesale and `naics3` 493 (78,918 + 27,123 + 10,214 = 116,255); construction 43,110; the rest 39,785, of which transport other than 493 is 36,087 minus 10,214 = 25,873. Shares are each count divided by 199,150.
7. **Wilson intervals.** For x correct out of n, with p = x/n and z = 1.96: centre = (p + z^2/(2n)) / (1 + z^2/n) and half-width = z * sqrt(p(1 - p)/n + z^2/(4n^2)) / (1 + z^2/n). 190 of 200 gives 0.910 to 0.973; 186 of 200 gives 0.886 to 0.958.
8. **Download totals.** Sums of the Content-Length values in section 7: 1,455,983,407 + 2,276,509,790 + 137,903,963 = 3,870,397,160 bytes; 1,455,983,407 + 137,903,963 = 1,593,887,370 bytes.
9. **Blank fields.** In each raw file read with `read_year`, values missing or blank after stripping spaces. Establishment name: 13 in all (1, 1, 1, 3, 5, 1 and 1 in 2016 to 2022, none since). Street address: 34 (5, 5, 7, 2, 2, 4, 2, 4, 2 and 1 in 2016 to 2025). City: 37 (4, 4, 5, 16, 2, 2, 1, 1 and 2 in 2016 to 2024, none in 2025). ZIP: 1 (2019). State: none. These agree with the unrounded shares in `outputs/audit/missing_by_year.csv`.
10. **Sectors in the panel.** `site_years.parquet` holds 1,594,425 rows [V] in seven sectors (agriculture; mining, oil and gas; utilities; construction; manufacturing; wholesale; transport and warehousing) and has no city or street address column, which is why section 2.1 re-reads those from `data/raw/`.
11. **Small-cell rules.** `scripts/09_landscape.py` sets `MIN_CELL = 100` for sector and band cells and `MIN_STATE = 500` for states.
