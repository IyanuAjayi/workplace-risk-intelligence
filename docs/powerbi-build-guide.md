# Power BI build guide: Workplace Risk Intelligence

How the report was built on 1 Nov 2026 and how to rebuild it. The report is defined in code: the measures in `powerbi/tools/measures.py` and the four pages in `powerbi/tools/build_report.py`. Nothing on the pages was placed by hand, so a rebuild gives the same report.

What exists in the Parakeet Risk Power BI service (My workspace; IDs and link not published here):

| Item | Name |
| --- | --- |
| Report | Workplace Risk Intelligence |
| Semantic model | Workplace Risk Intelligence |
| Source | `workplace_risk_intelligence.xlsx` in OneDrive, a copy of `outputs/powerbi/workplace_risk_powerbi.xlsx` |

How the pages differ from the mockups, and why, is in `docs/powerbi-implementation-notes.md`. An earlier click-by-click build sheet, written before the scripted build and never applied, is kept in `powerbi/build/archive/`.

## 1. Semantic model

1. Rebuild the workbook: `.venv/bin/python scripts/06_export_powerbi.py` (after 02 to 05, 08 and 09; see the README).
2. Copy `outputs/powerbi/workplace_risk_powerbi.xlsx` to OneDrive. In Power BI: New item, Semantic model, Get data, Excel workbook from OneDrive. Select all 17 sheets: Sites, Models, Calibration, Drivers, ROC, PrecisionRecall, PricingBands, PricingSummary, Robustness, ModelPicker, TestYearPicker, ScoreYears, ClaimCostScenarios, TestYears, Bands, StateGrid, About. In Power Query, About needs "Use first row as headers"; the others promote their headers on their own. Create a semantic model only (no auto report).

   A site-level sheet (SiteExplorer) for a fifth page was drafted on 1 and 2 Nov and dropped for privacy on 2 Nov (`docs/qa-note.md`). The workbook and the model hold only these 17 sheets.
3. Relationships (all single direction, filtering from the lookup table to the fact table):

| From (many) | To (one) | Notes |
| --- | --- | --- |
| Sites[State] | StateGrid[State] | the tile map |
| Sites[Risk band] | Bands[Risk band] | band rows and colours |
| Sites[Score year] | TestYears[Score year] | many to many: the "2023 + 2024" tile maps to both years |
| ROC[Model], Calibration[Model] | ModelPicker[Model] | model tiles |
| ROC[Test year], Calibration[Test year] | TestYearPicker[Test year] | test year tiles |
| PricingBands[Score year], PricingSummary[Score year] | ScoreYears[Score year] | Pricing Lab year tiles |

   Models, Drivers, Robustness, PrecisionRecall, ClaimCostScenarios and About stay unrelated; measures read the picked model, year and scenario with SELECTEDVALUE.
4. Sort-by columns (21): Sector by Sector order, Risk band by Band order and Size band label by Size order (Sites); Model by Model order (Models, Calibration, ROC, PrecisionRecall, ModelPicker); Risk band, Band label and Band short by Band order (PricingBands); Risk band, Band label and Band label long by Band order (Bands); Scenario by Scenario order (PricingSummary, ClaimCostScenarios); Label by Row order (Robustness); Tile label by Test year (TestYearPicker) and by Score year (ScoreYears); Test year and Tile label by Sort order (TestYears).
5. **Refresh the model after adding relationships.** Until it is refreshed, visuals that cross a new relationship fail with "the relationship ... needs to be recalculated".

## 2. Measures

1. `.venv/bin/python powerbi/tools/measures.py` writes `powerbi/model/measures.tmdl` (100 measures, in display folders by page) and `outputs/powerbi/measures.dax` (the same measures as a readable listing).
2. Open the semantic model, TMDL view, paste `measures.tmdl` and select Apply. It is a `createOrReplace` script: it adds or replaces these measures and leaves tables and data alone.
3. Check with DAX query view or the validation in section 4.

Two service quirks met on 1 Nov:
- In a TMDL script, an expression property such as `formatStringDefinition` must come after the plain properties, or the parser reports an indentation error.
- Re-applying a measure that has a dynamic format string failed with "Stack empty". The "Too few sites" cells therefore use a static format string with a negative section (`0.0%;"Too few sites"`; the measure returns -1 below 100 site-years), and no measure uses a dynamic format string now.

## 3. Report

1. Render the backgrounds and positions from the mockups (only after a mockup changes):

        .venv/bin/python powerbi/tools/render_backgrounds.py powerbi/mockups/page*.html
        .venv/bin/python powerbi/tools/visual_boxes.py powerbi/mockups/page*.html

2. Generate the report definition:

        .venv/bin/python powerbi/tools/build_report.py

   It writes `powerbi/report/` in the Power BI enhanced report format (PBIR): `definition/report.json`, `pages/<page>/page.json` and one `visual.json` per visual (93 visuals), with the theme and the four backgrounds under `StaticResources/RegisteredResources/`. It also writes `powerbi/build/report-bundle.json`, the same files base64-encoded for the API (not committed).
3. Deploy with the Fabric REST API, as a user with write access to the workspace:
   - `POST https://api.fabric.microsoft.com/v1/workspaces/{workspaceId}/reports/{reportId}/getDefinition`, and keep three things from the published report: `definition.pbir` (the connection to the semantic model), `.platform`, and `StaticResources/SharedResources/` (the service's base theme).
   - `POST .../updateDefinition` with `{"definition": {"parts": [bundle parts + the kept parts]}}`. Both calls are long-running: poll the `Location` header until the status is `Succeeded`.
   - On 1 Nov these calls ran from the signed-in Power BI browser session with that session's token. The token was never written down or stored.
4. Open the report and select Reset to default (toolbar), so saved viewer state from testing does not hide the defaults.

To change a page, edit `build_report.py` (or the mockup, then re-render), regenerate and deploy again. Edits made by hand in the Power BI editor are overwritten by the next deploy.

## 4. Validation (run 1 Nov 2026, all passed)

Run as DAX queries against the semantic model (DAX query view, or the executeQueries API). Defaults mean no slicer selected.

| Check | Expected (`expected_values.csv`, `verified-metrics.md`) | Power BI |
| --- | --- | --- |
| Sites scored | 199,150 | 199,150 |
| Sites crossing next year | 36,389 | 36,389 |
| Base rate | 0.182722 | 0.182722 |
| Top band capture | 0.514139 (51.4%) | 0.514139 |
| Top band hit rate | 0.469721 (47.0%) | 0.469721 |
| Lift | 2.5707 | 2.5707 |
| Share of sites in top band | 0.2 | 0.2 |
| Average site DART rate | 2.570455 | 2.570455 |
| Gradient boosting AUC 2023, 2024 | 0.799954, 0.800683 | 0.799954, 0.800683 |
| Misallocated share A, B (2023 central) | 0.275366, 0.099547 | 0.275366, 0.099547 |
| Crossing rate by band, 2023 / 2024 | 2.9/3.0, 7.1/7.6, 12.3/12.8, 21.0/22.0, 46.5/47.5% | same |
| Band 5 crossing range by sector | 43.6% to 49.5% | 43.6% to 49.5% |
| Picked AUC, scorecard 2023, with 95% CI | 0.78, 0.780 to 0.787 | same |
| Wrong band A to B, 2023 / 2024 central | 27.5% to 10.0% / 26.7% to 9.3% | same |
| Overall loss / premium, 2023 / 2024 central | 0.92 / 0.96 | same |
| Band loss / premium A and B, 2023 central | 0.35, 0.58, 0.82, 1.19, 2.10 and 0.52, 0.87, 1.14, 1.00, 1.05 | same |
| Scenario totals, 2023 (premium / loss) | $10.02bn / $8.11bn, $17.84bn / $16.43bn, $20.42bn / $18.80bn | same |
| Sector by band crossing rates, state shares | `verified-metrics.md` Risk Landscape tables | same, after the five rounding corrections in `docs/qa-note.md` |

Interaction checks on the first build, all passed: every navigation tab and link; the tile and dropdown slicers on each page (for example 2024 and Low on Pricing Lab give 26.2% to 9.1% and 0.88); Reset filters; picking Last year's rate (Model Trust shows its ROC and the calibration note); clicking a band row on Risk Landscape (the map re-titles to that band); clicking a state tile (highlights it only, by design).

Checks on the additions deployed later on 1 Nov, all passed in the live report:

- Sector drill-through: drilling through from Manufacturing on Executive Intelligence (right-click, Drill through, Risk Landscape) opened Risk Landscape showing Manufacturing only.
- Map hover: hovering a state on Risk Landscape shows the default tooltip with its name, band share and site-years (Kentucky showed 14.0%, as in `docs/verified-metrics.md`).
- Data bars: every sector column of the band table has a bar on the fixed 0 to 100% scale in Screen ink `#274A48`, with the value still printed; Too few sites cells draw no bar.
- Total row: the band table's total row reads "All bands".
- Connectors: on Pricing Lab, "Simulated loss / premium by band" joins each band's A and B points with a vertical connector.

Privacy changes deployed and checked live on 2 Nov: the map hover reads Under 500 site-years for smaller states (Vermont) and the exact count from 500 (Kentucky 3,267); the Sector and Size dropdowns take one pick at a time; data export is off (`exportDataMode` None). The live definition again matched `powerbi/report/` file by file.

Behaviour checked live on 2 Nov, recorded rather than changed:

- Clicking a state on Risk Landscape changes nothing on the page. Since the hover layer was added, the click lands on it, so the tile no longer highlights.
- A sector drill-through filter stays on Risk Landscape after leaving the page and reopening it from its tab. The page's Reset filters (Clear all slicers) leaves it on and the Sector dropdown reads All; Reset to default in the toolbar clears it. The report was reset to the author's default view afterwards.

Parity checks, run late on 1 Nov, all passed:

- The live report definition (Fabric getDefinition) equals `powerbi/report/` file by file, compared as canonical JSON. The service adds only its own `.platform`, `definition.pbir` and base theme.
- The live model's 100 measures equal `powerbi/model/measures.tmdl` in expression, format string and table.
- Rerunning `powerbi/tools/measures.py` and `powerbi/tools/build_report.py` changes nothing.
- The report shows "You're viewing the author's default view", so no saved viewer state needs resetting.
