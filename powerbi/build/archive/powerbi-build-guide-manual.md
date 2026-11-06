# Power BI build guide: Workplace Risk Intelligence

This is the build sheet for the four-page Workplace Risk Intelligence report (Executive Intelligence, Risk Landscape, Model Trust, Pricing Lab) at 1920 x 1080, built click by click in the Power BI web editor. It replaces the Site Risk Lens guide. Work through sections a to g in order. Every number a page shows comes from the Python scripts; Power BI only adds them up, so if a figure disagrees with section g, a measure, relationship or interaction is wrong, not the data.

| File | What it is |
|---|---|
| `outputs/powerbi/workplace_risk_powerbi.xlsx` | The data: 17 Excel tables, one per sheet (scripts/06_export_powerbi.py) |
| `outputs/powerbi/define-measures.dax` | One DAX query that defines all 155 measures; paste it into the DAX query view |
| `outputs/powerbi/measures.dax` | The same measures, documented: home table, format string, pages that use it, expected value |
| `outputs/powerbi/expected_values.csv`, `docs/verified-metrics.md` | The values section g checks against |
| `powerbi/theme/wri-theme.json` | The report theme |
| `powerbi/backgrounds/<page>.png` | The baked page backgrounds, 3840 x 2160 |
| `powerbi/mockups/<page>.html` and `.png` | The approved designs (1920 x 1080); the PNGs double as an alignment aid |
| `powerbi/build/<page>.boxes.json` | The measured position of every live visual on each mockup |
| `powerbi/build/inventory.json` | Everything in section f in machine-readable form |

Do not use `outputs/powerbi/bg_page1.png` to `bg_page4.png` or `outputs/powerbi/site-risk-lens-theme.json`: they belong to the old Site Risk Lens design.

## Before you start

1. **Model editing in the service.** Measures, relationships, sort-by-column and the DAX query view all need the tenant setting that lets users edit data models in the Power BI service. Prove it first: add one measure and one relationship, then delete them. If the Open data model button is greyed out, ask the admin before going further.
2. **Freeze the workbook.** Use the workbook exactly as exported (1 Nov 2026, 19:41). Do not re-run `scripts/06_export_powerbi.py` or open and re-save the file in Excel during the build: the semantic model refreshes from it, and a changed column breaks measures.
3. **Current assets.** Each background in `powerbi/backgrounds/` must be newer than its mockup HTML, and each box file in `powerbi/build/` too. Check with `ls -l powerbi/mockups/page*.html powerbi/backgrounds powerbi/build`. If a mockup changed after its background, re-export it with `.venv/bin/python -I powerbi/tools/render_backgrounds.py powerbi/mockups/<page>.html` and refresh its boxes with `.venv/bin/python -I powerbi/tools/visual_boxes.py powerbi/mockups/<page>.html`. If a box changed, re-check the values in section f against it.
4. **One measure source.** The visuals below use the measure names in `outputs/powerbi/define-measures.dax`. `powerbi/model/measures.tmdl` (from `powerbi/tools/measures.py`, for the scripted build in `powerbi/tools/build_report.py`) is a different set that reuses some of the same names with other expressions and home tables. Apply one or the other to a semantic model, never both.
5. **Static captions are baked.** Every caption that never changes (the key-figure captions, column and axis labels that do not move, scales, notes and tags) is in the background image. Never rebuild one as a text box. Section f lists, page by page, what is baked so you can check the background shows it.

## a. Create the semantic model from the workbook

1. Put `outputs/powerbi/workplace_risk_powerbi.xlsx` in OneDrive for work or school, or a SharePoint document library, under the account that will own the report. Keep the file name.
2. In app.powerbi.com open the target workspace, choose Upload > OneDrive for Business (or SharePoint), pick the workbook and import its data as a semantic model. Do not choose to open it as an Excel workbook item. A semantic model connected to the OneDrive file refreshes from it automatically, so later fixes to the workbook flow in; a file uploaded from disk does not, and re-uploading it can replace the model and the measures with it.
3. Rename the semantic model Workplace Risk Intelligence, open it and select Open data model.
4. Check that all 17 tables are there with these row counts (Model view shows each table; the counts come from the workbook):

| Table | Rows | Used for |
|---|---|---|
| Sites | 5,240 | Priced portfolio, one row per score year, sector, state, size band and risk band (199,150 site-years) |
| Models | 8 | Four models x two test years: AUC with interval, Gini, top-20% capture and precision |
| Calibration | 60 | Predicted against observed share by decile (no rows for Last year's rate) |
| Drivers | 15 | Gradient boosting permutation importance |
| ROC | 1,459 | ROC curve points, every model and test year |
| PrecisionRecall | 1,300 | Not used on any page; leave it disconnected |
| PricingBands | 30 | Simulated premium and loss by year, band and claim-cost scenario |
| PricingSummary | 6 | Simulated totals and alignment by year and scenario |
| Robustness | 13 | Robustness and subgroup AUCs |
| ModelPicker | 4 | Model slicer on Model Trust |
| TestYearPicker | 2 | Test year slicer on Model Trust |
| ScoreYears | 2 | Test year slicer on Pricing Lab |
| ClaimCostScenarios | 3 | Claim-cost slicer on Pricing Lab (disconnected) |
| TestYears | 4 | Test year slicer on Risk Landscape (2023 + 2024, 2023, 2024) |
| Bands | 5 | Band labels, long labels and colours |
| StateGrid | 52 | Tile-map grid positions |
| About | 12 | Source and caveat text |

5. Data types and summarisation. Set these columns to Whole number, format `0` (no thousands separator), summarisation Don't summarize: every Score year, Outcome year and numeric Test year column, Band order, Sector order, Size order, Model order, Row order, Scenario order, Sort order, Grid column, Grid row and Score decile. TestYears[Test year] is Text. Set ROC[False positive rate] to Don't summarize. Sites[Risk band], Bands[Risk band] and PricingBands[Risk band] are Text ('1 lowest', '2', '3', '4', '5 highest').

## b. Relationships

Open Manage relationships. Delete every relationship Power BI detected by itself, then create exactly these nine. Cross-filter direction is Single on all of them, from the first table to the second.

| # | From (filters) | To (is filtered) | Cardinality | Cross-filter direction | Why |
|---|---|---|---|---|---|
| 1 | TestYears[Score year] | Sites[Score year] | Many to many | Single (TestYears filters Sites) | The Risk Landscape year tile '2023 + 2024' maps to both score years, so one tile selects two years |
| 2 | StateGrid[State] | Sites[State] | One to many | Single | Tile map; Sites also holds GU, VI, MP, AS, MH, AP and AE, which have no tile and fall into the blank row |
| 3 | Bands[Risk band] | Sites[Risk band] | One to many | Single | Band rows of the Risk Landscape band table, and band labels and colours on Executive Intelligence |
| 4 | ModelPicker[Model] | ROC[Model] | One to many | Single | Model slicer drives the ROC curve |
| 5 | ModelPicker[Model] | Calibration[Model] | One to many | Single | Model slicer drives the calibration chart |
| 6 | TestYearPicker[Test year] | ROC[Test year] | One to many | Single | Test year slicer drives the ROC curve |
| 7 | TestYearPicker[Test year] | Calibration[Test year] | One to many | Single | Test year slicer drives the calibration chart |
| 8 | ScoreYears[Score year] | PricingBands[Score year] | One to many | Single | Pricing Lab test year slicer drives the band charts |
| 9 | ScoreYears[Score year] | PricingSummary[Score year] | One to many | Single | Pricing Lab test year slicer drives the rail figures and the sensitivity table |

These tables stay disconnected: Models, Drivers, Robustness, PrecisionRecall, ClaimCostScenarios and About. In particular there must be no relationship from ModelPicker or TestYearPicker to Models (the comparison table would collapse to the picked row and its row fill would stop working), none from ScoreYears to Sites, none from TestYears to the pricing tables, none from Bands to PricingBands, and none at all on ClaimCostScenarios (its Scenario, Scenario order and Rule columns share names with PricingSummary, so autodetect likes to link them; a link would cut the sensitivity table to one row).

## c. Sort by column

Select each column in the data pane, then Column tools (or Properties > Advanced) > Sort by column.

| Column | Sort by |
|---|---|
| Sites[Sector] | Sites[Sector order] |
| Sites[Size band label] | Sites[Size order] |
| Sites[Risk band] | Sites[Band order] |
| Bands[Risk band] | Bands[Band order] |
| Bands[Band label] | Bands[Band order] |
| Bands[Band label long] | Bands[Band order] |
| TestYears[Test year] | TestYears[Sort order] |
| TestYears[Tile label] | TestYears[Sort order] |
| ModelPicker[Model] | ModelPicker[Model order] |
| Models[Model] | Models[Model order] |
| TestYearPicker[Tile label] | TestYearPicker[Test year] |
| ScoreYears[Tile label] | ScoreYears[Score year] |
| ClaimCostScenarios[Scenario] | ClaimCostScenarios[Scenario order] |
| PricingSummary[Scenario] | PricingSummary[Scenario order] |
| PricingBands[Risk band] | PricingBands[Band order] |
| PricingBands[Band label] | PricingBands[Band order] |
| PricingBands[Band short] | PricingBands[Band order] |
| Robustness[Label] | Robustness[Row order] |

The columns the designers proposed as calculated columns (Sites[Sector order], [Size band label], [Size order], PricingBands[Band label], [Band short], PricingSummary[Scenario], [Scenario order], [Rule], Drivers[Driver], Bands[Band label long], TestYears[Tile label], ScoreYears[Tile label]) already come from the workbook. Do not create them again: a calculated column with the same name fails.

## d. Measures

1. In the data model editor open the DAX query view and start a new query.
2. Paste the whole of `outputs/powerbi/define-measures.dax` and select Run. It defines 155 measures and returns one row. Check it reads (column = value, unformatted):

   - Sites = 199150
   - Base rate = 0.1827...
   - Top band capture = 0.5141...
   - Top band hit rate = 0.4697...
   - Capture base line = 18,709 of 36,389 · 2023 + 2024
   - Wrong band A to B 2023 central = 27.5% → 10.0%
   - Band 5 crossing range = 43.6% to 49.5%
   - Portfolio base line = 36,389 of 199,150 · 2023 + 2024
   - Picked AUC = 0.7833...
   - Picked AUC base = Scorecard, 2023 · 95% CI 0.780 to 0.787
   - Picked test pairs = 107,673 test pairs · 2023
   - Priced sites 2023 = 99185
   - Pricing base line 2023 = 2023 central · 99,185 sites

   Priced sites 2023 and Pricing base line 2023 also test relationship 8: if they read 199150 and 2023 central · 199,150 sites, the ScoreYears relationship is missing.

3. Select Update model with changes. Every measure is added to its home table (Sites, Models, PricingBands and so on). Running it again overwrites them, which is safe.
4. Set format strings. Select each measure, then Properties > Format, choose Custom and type the string. Text measures (53 of them) need nothing.

| Format string | Measures |
|---|---|
| `#,0` | Sites[Sites], Sites[Sites crossing next year], Sites[Top band crossing sites], Sites[Top band site-years], Sites[Portfolio site-years], Sites[Portfolio crossing sites], Sites[Band 5 site-years], Sites[Size site-years 20 to 249], Sites[Size site-years 250+], Sites[Cell site-years], ModelPicker[Flagged and crossed], ModelPicker[Flagged, did not cross], ModelPicker[Missed], ModelPicker[Not flagged, did not cross], PricingBands[Priced sites] |
| `0.0%` | Sites[Base rate], Sites[Top band hit rate], Sites[Top band capture], Sites[Share of sites in top band], Sites[Capture remainder], Sites[Crossing rate 2023], Sites[Crossing rate 2024], Sites[Crossing rate 2024 band 1], Sites[Crossing rate 2024 band 2], Sites[Crossing rate 2024 band 3], Sites[Crossing rate 2024 band 4], Sites[Crossing rate 2024 band 5], Sites[All sites rate], Sites[Portfolio crossing rate], Sites[Band 5 share], Sites[Size band 5 share 20 to 249], Sites[Size band 5 share 250+], Sites[Map share], Models[Capture top 20% 2023], Models[Capture top 20% 2024], Models[Precision top 20% 2023], Models[Precision top 20% 2024], Calibration[Calibration share crossed], Calibration[Calibration predicted], ClaimCostScenarios[Misallocated share A], ClaimCostScenarios[Misallocated share B] |
| `0.0"x"` | Sites[Top band lift], Models[Capture gain vs rating class], ClaimCostScenarios[Band spread A], ClaimCostScenarios[Band spread B] |
| `0.00` | Sites[Average site DART rate], Sites[Portfolio DART rate], Models[Model AUC], Models[Model AUC low], Models[Model AUC high], Models[Model Gini], Models[Best model AUC], Models[Rating class AUC], Models[Picked AUC], Models[Picked Gini], Models[AUC 2023 scorecard], Models[AUC 2024 scorecard], Models[AUC 2023 last year], Models[AUC 2024 last year], Models[AUC 2023 rating class], Models[AUC 2024 rating class], PricingBands[Band loss ratio A], PricingBands[Band loss ratio B], PricingBands[Band loss ratio low], PricingBands[Band loss ratio high], PricingSummary[Overall loss ratio A], PricingSummary[Overall loss ratio B], PricingSummary[Scenario loss ratio] |
| `\$#,0.0,,"m"` | Sites[Site premium A], Sites[Site premium B], Sites[Site simulated loss] |
| `+0%;−0%;0%` | Sites[Site premium change] |
| `0%` | Sites[Random fifth], Models[Model capture top 20%], Models[Model precision top 20%], ROC[ROC true positive rate], ROC[Coin toss] |
| `0.0%;"Too few sites";0.0%` | Sites[Cell crossing rate], Sites[Crossed Manufacturing], Sites[Crossed Construction], Sites[Crossed Transport and warehousing], Sites[Crossed Wholesale], Sites[Crossed Utilities], Sites[Crossed Agriculture], Sites[Crossed Mining, oil and gas] |
| `0` | Sites[Map band order], Sites[Map x], Sites[Map y], TestYearPicker[Picked test year] |
| `0.000` | Models[AUC 2023], Models[AUC 2024], Models[Gini 2023], Models[Gini 2024], Robustness[Robustness AUC 2023], Robustness[Robustness AUC 2024], Drivers[Driver AUC drop] |
| `\$#,0.00,,,"bn"` | PricingBands[Band premium A], PricingBands[Band premium B], PricingBands[Band simulated loss], PricingSummary[Scenario premium], PricingSummary[Scenario simulated loss] |
| `+0.0%;−0.0%;0.0%` | PricingBands[Band premium change] |

Notes. `0.0%;"Too few sites";0.0%` shows the -1 that the band-table measures return for cells under 100 site-years as the words Too few sites. The `\$#,0.00,,,"bn"` strings show dollars in billions to two decimals ($17.84bn). The minus sign in `+0.0%;−0.0%;0.0%` is the typographic minus (U+2212), as on the mockups. Eight measures kept from Site Risk Lens moved home table because their old home has a column with the same name; `measures.dax` lists them. A measure's home table changes nothing it calculates.

## e. Theme and page setup

1. From the semantic model select Create report > Start from scratch, then save the report as Workplace Risk Intelligence.
2. View > Themes > Browse for themes, and pick `powerbi/theme/wri-theme.json`.
3. Pages, in this order: Executive Intelligence, Risk Landscape, Model Trust, Pricing Lab, then Tooltip state (built in Risk Landscape's section).
4. For each of the four main pages, select the empty canvas and in Format page set:
   - Canvas settings: Type Custom, Width 1920, Height 1080, Vertical alignment Top.
   - Canvas background: Image, browse to `powerbi/backgrounds/<page>.png`, Image fit Fit, Transparency 0%.
   - Wallpaper: colour #EFECDF, transparency 0%.
5. View: Fit to page, and Snap to grid off, so the typed positions stick.
6. Alignment aid. While placing a page's visuals, set its canvas background to the full mockup instead (`powerbi/mockups/<page>.png`, 1920 x 1080, Fit). Place each visual over its twin, nudge until text and marks sit on the mockup's, then switch the background back to the baked PNG. Power BI pads text inside visuals a little differently from the mockup, so expect nudges of a few pixels.
7. Positions. Type x, y, width and height in Format > General > Properties. The page tables give the values to type; an asterisk marks a value that differs from the box file, and the note under the table says why.
8. Names and alt text. In View > Selection, rename every visual with its id from the tables, so QA can match report and mockup one to one. Give every chart and table alt text in General > Alt text: the mockup's aria-label (in `inventory.json`), or fx with the alt-text measure where the table names one.
9. Navigation. Build the four navigation buttons on Executive Intelligence, then copy and paste them onto each page (positions are kept) and swap which one is active. Paste does not copy Edit interactions settings, so set those page by page.
10. Theme limits. The theme turns visual titles, backgrounds, borders, shadows and header icons off for every visual, and styles the classic card and slicer, tables, matrices, axes, data labels and tooltips. The new Card and the Button slicer take none of its card or slicer styling, so set the first one by hand from its preset, then use Format painter for the rest.

Presets used in the page tables:

| Preset | Settings |
|---|---|
| NAV | Button (Blank). Text on, Segoe UI 11 pt, centred, vertical centre. Default: fill off, text Ink #303A39. On hover and On press: fill #E3DECF at 0% transparency, text Onyx #000000. Border, shadow and glow off. |
| NAV-ACTIVE | As NAV, but fill Ember #E24337 at 0% transparency and text Onyx in Default, On hover and On press. Action off (this is the current page). |
| LINK | Button (Blank). Text on, Segoe UI 11 pt, Cobalt #1936E8 in every state, fill off, border off. Underline on hover if your editor offers it. |
| RESET | Button (Reset icon, from Insert > Buttons > Reset). Text on: 'Reset filters', Segoe UI 11 pt, Cobalt #1936E8, right aligned; icon Cobalt, placed left of the text, about 14 px; fill and border off. |
| HERO | Card (new). Callout value Segoe UI Semibold 72 pt, Shell #FFFFFF, left, vertical top. Display units None (so 172,239 does not become 172K), decimals from the measure. Label off. Card background, border, shadow and accent bar off; padding 0. |
| FIGURE | Card (new). Callout value Segoe UI Semibold 23 pt, Onyx #000000, left, vertical middle, no word wrap. Display units None (so 172,239 does not become 172K), decimals from the measure. Label off. Card background, border, shadow and accent bar off; padding 0. |
| BASE | Card (new). Callout value Segoe UI 11 pt, Muted #66655F, left, vertical middle, no word wrap. Display units None (so 172,239 does not become 172K), decimals from the measure. Label off. Card background, border, shadow and accent bar off; padding 0. |
| TITLE | Card (new). Callout value Segoe UI Semibold 15 pt, Onyx #000000, vertical middle, no word wrap. Display units None (so 172,239 does not become 172K), decimals from the measure. Label off. Card background, border, shadow and accent bar off; padding 0. |
| LABEL-INK | Card (new). Callout value Segoe UI 11 pt, Ink #303A39, vertical middle, no word wrap. Display units None (so 172,239 does not become 172K), decimals from the measure. Label off. Card background, border, shadow and accent bar off; padding 0. |
| TILES | Button slicer. Slicer header on (field renamed as given), Segoe UI 11 pt Muted #66655F. Buttons: one row, spacing 0, text Segoe UI 11 pt centred. Default: fill #F7F5EC, text Ink #303A39. On hover and On press: fill #E3DECF, text Onyx. Selected: fill Ink #303A39, text Shell #FFFFFF. Border 1 px Axis #CFCBBD. Selection: Single select on, Force selection on. |
| DROPDOWN | Slicer (the classic slicer), style Dropdown. Header on (field renamed as given), Segoe UI 11 pt Muted. Values Segoe UI 11 pt Onyx on Card #F7F5EC, 1 px Axis #CFCBBD border (the theme sets these). Selection: Single select off, Multi-select with Ctrl off (clicks tick the check boxes), Show Select all on. Shows All when nothing is picked. |
| TABLE | Table. Style preset None. Grid: horizontal and vertical gridlines off, row padding 4 (28 px rows). Column headers Segoe UI 11 pt Muted on Card, word wrap on. Values Segoe UI 11 pt Onyx on Card for both row colours (no banding). Totals off unless stated. Auto-size column width off, then drag the column widths given. |
| CHART | Title, background, border and shadow off (theme). Legend off, gridlines off, axis titles off unless stated. |

Sizes in Power BI are points: 14 px labels are 11 pt, 20 px data labels and titles 15 pt, 30 px figures 23 pt, the 96 px stamp figure 72 pt. Colours: Onyx #000000, Ink #303A39, Muted #66655F, Shell #FFFFFF, Card #F7F5EC, Card line #E3DECF, Axis #CFCBBD, Ember #E24337, Cobalt #1936E8, Screen ink #274A48, Warm grey #B3AFA1, bands #C9D6BD, #D1A76A, #C98369, #A96247, #944126.

Tooltips are Power BI's default tooltips, styled by the theme (Onyx, Shell values, Axis grey keys). Where a table row below lists Tooltips, add those fields so the hover shows the base. The one report-page tooltip is the Risk Landscape map's, because a scatter chart's default tooltip would show grid coordinates.

## f. Build the pages

### Page 1: Executive Intelligence

Background `powerbi/backgrounds/page1-executive-intelligence.png`. No slicers: every figure is pooled 2023 + 2024 except the column chart (2023), the 2024 row, the AUC card (2023 and 2024) and the pricing ledger (2023 central). Population: the 199,150 priced site-years, except the AUC card, which uses all test pairs and says so in its baked header.

Baked in the background (check it is there; do not build it): kpi-capture-caption; kpi-hit-rate-caption; kpi-wrong-band-caption; legend-crossing-year; 'In band 5' and 'All sites 20%' in the sector card; the AUC card's header, model names, 0.50 coin toss / 0.75 / 1.00 scale, 2023 and 2024 headers and the '2024' row label.

| # | id | Power BI visual | x | y | w | h | Fields by well | Key format settings | Action, slicer, bookmark |
|---|---|---|---|---|---|---|---|---|---|
| 1 | `nav-executive-intelligence` | Button (Blank) | 705 | 37 | 186 | 38 | Text: Executive Intelligence | Preset NAV-ACTIVE. | None (current page) |
| 2 | `nav-risk-landscape` | Button (Blank) | 891 | 37 | 145 | 38 | Text: Risk Landscape | Preset NAV. | Page navigation to Risk Landscape |
| 3 | `nav-model-trust` | Button (Blank) | 1036 | 37 | 120 | 38 | Text: Model Trust | Preset NAV. | Page navigation to Model Trust |
| 4 | `nav-pricing-lab` | Button (Blank) | 1156 | 37 | 115 | 38 | Text: Pricing Lab | Preset NAV. | Page navigation to Pricing Lab |
| 5 | `kpi-capture-value` | Card (new) | 98* | 493* | 302* | 128* | Data: Sites[Top band capture] | Preset HERO. Shows 51.4%. Sits on the baked Onyx stamp (x 64 to 400, y 480 to 632). |  |
| 6 | `kpi-capture-count` | Card (new) | 424 | 582 | 216 | 20 | Data: Sites[Capture base line] | Preset BASE. 18,709 of 36,389 · 2023 + 2024 |  |
| 7 | `chart-capture-vs-random` | Stacked bar chart | 64 | 642 | 336 | 20 | Y-axis: TestYears[Tile label] (visual filter: Tile label is 2023 + 2024); X-axis: Sites[Top band capture], Sites[Capture remainder] | Preset CHART. Bar colours: Top band capture #944126, Capture remainder #E3DECF. X-axis off, range 0 to 1. Y-axis off. Bars > Layout > inner padding 60% (an 8 px bar, y 648 to 656). Data labels off. Tooltips off. Analytics: X-axis constant line, value fx Sites[Random fifth] (0.2), Ink #303A39, 2 px, solid, position In front, data label off. |  |
| 8 | `kpi-hit-rate-value` | Card (new) | 424 | 757 | 216 | 40 | Data: Sites[Top band hit rate] | Preset FIGURE. 47.0% |  |
| 9 | `kpi-hit-rate-count` | Card (new) | 424 | 817 | 216 | 20 | Data: Sites[Hit rate base line] | Preset BASE. 18,709 of 39,830 · 2023 + 2024 |  |
| 10 | `kpi-wrong-band-value` | Card (new) | 424 | 861 | 216 | 40 | Data: PricingSummary[Wrong band A to B 2023 central] | Preset FIGURE. 27.5% → 10.0%. Pinned to 2023 central, as the baked Simulated tag below it says. |  |
| 11 | `link-method-caveats` | Button (Blank) | 64 | 996 | 576 | 20 | Text: Method and caveats: Model Trust → | Preset LINK. Left aligned. The first caveat line is baked. | Page navigation to Model Trust |
| 12 | `chart-crossing-by-band` | Clustered column chart | 801* | 257* | 1024* | 292* | X-axis: Bands[Band label long]; Y-axis: Sites[Crossing rate 2023]; Tooltips: Sites[Crossing base 2023] renamed Base | Preset CHART. Sort: Band label long ascending (follows Band order). Columns: colour fx Field value Bands[Band fill]; inner padding 41% (120 px columns on a 204.8 px pitch). Y-axis off, range 0 to 0.53. X-axis on: Segoe UI 11 pt Onyx, no title. Data labels on: Outside end, Segoe UI Semibold 15 pt Onyx, 0.0%. Analytics, Y-axis constant line 1: name 'All sites 18.3%, 2023 + 2024', value fx Sites[All sites rate], Muted #66655F, 1 px, dashed, position Behind, data label on, text Name only, Segoe UI 11 pt Ink, horizontal Left, vertical Above. Constant line 2: value 0, Ink #303A39, 1 px, solid, Behind, label off (the baseline). Alt text: copy the mockup's aria-label (inventory.json has it). |  |
| 13 | `matrix-crossing-2024` | Card (new), five values | 801* | 574* | 1024* | 28* | Data, in this order: Sites[Crossing rate 2024 band 1], Sites[Crossing rate 2024 band 2], Sites[Crossing rate 2024 band 3], Sites[Crossing rate 2024 band 4], Sites[Crossing rate 2024 band 5] | Preset LABEL-INK. Layout: 5 cards in one row, card spacing 0, padding 0. Callout value centred, Ink. Shows 3.0%, 7.6%, 12.8%, 22.0%, 47.5%. |  |
| 14 | `link-risk-landscape` | Button (Blank) | 1109 | 702 | 123 | 20 | Text: Risk Landscape → | Preset LINK. Right aligned. | Page navigation to Risk Landscape |
| 15 | `table-sector-dart` | Table | 737* | 740* | 496* | 228* | Columns: Sites[Sector] renamed ' ' (one space); Sites[Average site DART rate] renamed Avg DART rate; Sites[Share of sites in top band] renamed '  ' (two spaces: its header 'In band 5' is baked) | Preset TABLE. Sort: Average site DART rate descending. Widths 160, 92, 244. Column header outline None (the rule under the header is baked at y 768). Avg DART rate header and values right aligned, values Ink #303A39 (Specific column font colour). Sector left, Onyx. Third column values right aligned, Onyx. Totals off. Rows from y 768 to 964. Alt text: copy the mockup's aria-label (inventory.json has it). |  |
| 16 | `chart-sector-band5` | Clustered bar chart | 1013* | 768* | 180* | 196* | Y-axis: Sites[Sector]; X-axis: Sites[Share of sites in top band]; Tooltips: Sites[Average site DART rate], Sites[Band 5 share base] renamed Base | Preset CHART. Sort: Average site DART rate descending (same order as the table). Bars #944126; inner padding 57% (12 px bars). X-axis off, range 0 to 0.25. Y-axis off. Data labels off. Analytics: X-axis constant line, value fx Sites[Random fifth] (0.2), Ink #303A39, 1 px, solid, Behind, label off ('All sites 20%' is baked). |  |
| 17 | `link-model-trust` | Button (Blank) | 1726 | 702 | 98 | 20 | Text: Model Trust → | Preset LINK. Right aligned. | Page navigation to Model Trust |
| 18 | `chart-auc-2023` | Clustered bar chart | 1473* | 787* | 240* | 168* | Y-axis: Models[Model] (visual filter: Model is Scorecard, Last year's rate, Rating class only); X-axis: Models[AUC 2023]; Tooltips: Models[Tooltip AUC 2023] renamed AUC, 2023 test; Models[Tooltip AUC 2024] renamed AUC, 2024 test; Models[Tooltip base] renamed Base | Preset CHART. Sort: Model descending (Model order gives Scorecard, Last year's rate, Rating class only). Bar colours (Colors, show all): Scorecard #274A48, the other two #B3AFA1. Inner padding 71% (16 px bars). X-axis off, range 0.5 to 1. Y-axis off (model names are baked). Data labels on: Outside end; Value field Models[AUC 2023 words] (about 8 in 10, blank, about 6 in 10); Segoe UI 11 pt Muted. Alt text: copy the mockup's aria-label (inventory.json has it). |  |
| 19 | `table-auc-by-year` | Card (new), six values | 1713* | 787* | 112* | 168* | Data, in this order: Models[AUC 2023 scorecard], [AUC 2024 scorecard], [AUC 2023 last year], [AUC 2024 last year], [AUC 2023 rating class], [AUC 2024 rating class] | Preset LABEL-INK. Layout: 2 cards per row, 3 rows, card spacing 0, padding 0. Callout value right aligned; first two values Onyx #000000, the other four Ink #303A39. Shows 0.78 0.79 / 0.73 0.73 / 0.59 0.59. The 2023 and 2024 headers are baked. |  |

Why the values marked * differ from the box file:

- `kpi-capture-value` (box file 98, 514, 302, 96). 72 pt Segoe UI needs a 128 px line, so the card starts 21 px higher and the digits keep the mockup's baseline (y 597) inside the stamp.
- `chart-crossing-by-band` (box file 737, 261, 1088, 288). The plot must start at x 801 so the five columns sit on the mockup's centres (903, 1108, 1313, 1518, 1723) and line up with the 2024 row. Power BI draws the reference line across the plot only, so it starts at x 801, not 737.
- `matrix-crossing-2024` (box file 885, 579, 860, 17). The box is the text extent. Five equal 204.8 px cells from x 801 centre each value under its column; the baked '2024' label sits at x 737.
- `table-sector-dart` (box file 737, 741, 252, 221). The table also carries the band 5 shares as a third, right-aligned column, because Power BI bar labels cannot line up at x 1233. It spans the card's 496 px and the bar chart sits over the empty left part of that column.
- `chart-sector-band5` (box file 1013, 773, 220, 194). The plot is the bars only: 0 to 25% over 180 px (7.2 px per point) and seven 28 px rows level with the table rows. The values come from the table.
- `chart-auc-2023` (box file 1473, 806, 234, 129). The box is the drawn bars and labels. The plot must run from the baked 0.50 floor (x 1473) to the baked 1.00 tick (x 1713) and cover three 56 px rows.
- `table-auc-by-year` (box file 1738, 806, 87, 129). Two 56 px columns end on the mockup's right edges (x 1769 and 1825) and three 56 px rows sit level with the bars.

**Edit interactions.**

Every data visual and card is set to None on every other visual, except table-sector-dart to chart-sector-band5, which is Highlight. The page is a fixed summary.

| Source (select it, then Format > Edit interactions) | Filter | Highlight | None |
|---|---|---|---|
| `chart-capture-vs-random` |   |   | every visual |
| `chart-crossing-by-band` |   |   | every visual |
| `table-sector-dart` |   | chart-sector-band5 | every other visual |
| `chart-sector-band5` |   |   | every visual, including table-sector-dart |
| `chart-auc-2023` |   |   | every visual |

### Page 2: Risk Landscape

Background `powerbi/backgrounds/page2-risk-landscape.png`. Population: the 199,150 priced site-years; the Test year slicer pools 2023 + 2024 by default. Risk Landscape is reached by the tabs and the Risk Landscape → link; it has no drill-through filter, so the back link is a plain page navigation.

Baked in the background (check it is there; do not build it): kpi-band5-range-caption; kpi-all-sites-caption; 'In band 5' header and its rule; the size band names; 'All sites 20%' under the size bars; the map's ghost tiles, codes and class legend.

| # | id | Power BI visual | x | y | w | h | Fields by well | Key format settings | Action, slicer, bookmark |
|---|---|---|---|---|---|---|---|---|---|
| 1 | `nav-executive-intelligence` | Button (Blank) | 705 | 37 | 186 | 38 | Text: Executive Intelligence | Preset NAV. | Page navigation to Executive Intelligence |
| 2 | `nav-risk-landscape` | Button (Blank) | 891 | 37 | 145 | 38 | Text: Risk Landscape | Preset NAV-ACTIVE. | None (current page) |
| 3 | `nav-model-trust` | Button (Blank) | 1036 | 37 | 120 | 38 | Text: Model Trust | Preset NAV. | Page navigation to Model Trust |
| 4 | `nav-pricing-lab` | Button (Blank) | 1156 | 37 | 115 | 38 | Text: Pricing Lab | Preset NAV. | Page navigation to Pricing Lab |
| 5 | `link-back-executive` | Button (Blank) | 64 | 144 | 164 | 20 | Text: ← Executive Intelligence | Preset LINK. Left aligned. | Page navigation to Executive Intelligence (not the Back action, which would return to whichever page the reader came from) |
| 6 | `kpi-band5-range-value` | Card (new) | 64* | 376* | 336* | 40* | Data: Sites[Band 5 crossing range] | Preset FIGURE. 43.6% to 49.5% |  |
| 7 | `kpi-band5-range-count` | Card (new) | 64* | 436* | 336* | 20* | Data: Sites[Band 5 base line] | Preset BASE. 39,830 band 5 site-years · 2023 + 2024 |  |
| 8 | `kpi-all-sites-value` | Card (new) | 424* | 376* | 216* | 40* | Data: Sites[Portfolio crossing rate] | Preset FIGURE. 18.3% |  |
| 9 | `kpi-all-sites-count` | Card (new) | 424* | 436* | 216* | 20* | Data: Sites[Portfolio base line] | Preset BASE. 36,389 of 199,150 · 2023 + 2024 |  |
| 10 | `btn-reset-filters` | Button (Reset) | 540 | 612 | 100 | 20 | Text: Reset filters | Preset RESET. | Bookmark: Risk Landscape defaults |
| 11 | `slicer-test-year` | Button slicer | 64 | 652 | 576 | 72 | Field: TestYears[Tile label], renamed Test year | Preset TILES. 3 buttons: 2023 + 2024, 2023, outcome 2024, 2024, outcome 2025 (sorted by Sort order). Default selection 2023 + 2024. | Single select, Force selection, default 2023 + 2024 |
| 12 | `slicer-sector` | Slicer (dropdown) | 64 | 740 | 272 | 72 | Field: Sites[Sector], renamed Sector | Preset DROPDOWN. Sorted by Sector (follows Sector order). | Multi-select, Select all, default All |
| 13 | `slicer-size-band` | Slicer (dropdown) | 368 | 740 | 272 | 72 | Field: Sites[Size band label], renamed Size band | Preset DROPDOWN. Sorted by Size band label (follows Size order). | Multi-select, Select all, default All |
| 14 | `link-method-caveats` | Button (Blank) | 64 | 996 | 576 | 20 | Text: Method and caveats: Model Trust → | Preset LINK. Left aligned. | Page navigation to Model Trust |
| 15 | `map-title` | Card (new) | 736* | 176* | 250* | 28* | Data: Sites[Map title] | Preset TITLE. Left aligned. Band 5 share by state; Band 2 share by state after a band 2 row click. |  |
| 16 | `map-legend-title` | Card (new) | 797* | 256* | 240* | 20* | Data: Sites[Map legend title] | Preset BASE. Share of site-years, 2023 + 2024. The three class swatches under it are baked. |  |
| 17 | `map-tiles` | Scatter chart | 735* | 255* | 484* | 352* | Values (details): StateGrid[State]; X-axis: Sites[Map x]; Y-axis: Sites[Map y] | Preset CHART. Markers: shape square, size tuned until a tile measures 40 px, colour fx Field value Sites[Map tile colour]. Category labels on: Segoe UI 11 pt Onyx. X-axis off, range -0.5 to 10.5. Y-axis off, range -0.5 to 7.5, Invert range on. Legend off. Tooltips: Type Report page, Page Tooltip state. States under 500 site-years return no X and Y, so no marker is drawn and the baked dashed tile shows. Alt text: fx, field Sites[Alt text map]. |  |
| 18 | `tooltip-state` | Report page tooltip (hover preview only) | 941 | 281 | 234 | 92 | Not placed on this page. Built as the hidden page Tooltip state (table below) and set as map-tiles' tooltip. | The box shows where the mockup draws the hover state for Maine. |  |
| 19 | `table-sector-context` | Table | 1329* | 220* | 496* | 248* | Columns: Sites[Sector] renamed ' '; Sites[Portfolio site-years] renamed Site-years; Sites[Portfolio DART rate] renamed Avg site DART rate; Sites[Band 5 share] renamed '  ' (two spaces: 'In band 5' is baked) | Preset TABLE. Sort: Sector ascending (follows Sector order). Widths 184, 72, 84, 156 (the DART header wraps to 'Avg site' over 'DART rate'). Column header outline None (rule baked). Site-years and DART headers and values right aligned, values Ink #303A39. Sector Onyx, left. Band 5 share values Onyx, right aligned at x 1825. Totals off. Alt text: copy the mockup's aria-label (inventory.json has it). |  |
| 20 | `chart-sector-band5` | Clustered bar chart | 1693* | 268* | 90* | 196* | Y-axis: Sites[Sector]; X-axis: Sites[Band 5 share]; Tooltips: Sites[Band 5 share base] renamed Base | Preset CHART. Sort: Sector ascending. Bars #944126, inner padding 57% (12 px). X-axis off, range 0 to 0.25. Y-axis off. Data labels off (the values are the table's last column). Analytics: X-axis constant line, value fx Sites[Random fifth], Ink 1 px solid, Behind, label off. |  |
| 21 | `table-size-context` | Card (new), four values | 1345* | 492* | 480* | 56* | Data, in this order: Sites[Size site-years 20 to 249], Sites[Size band 5 share 20 to 249], Sites[Size site-years 250+], Sites[Size band 5 share 250+] | Preset LABEL-INK. Layout: 2 cards per row, 2 rows, card spacing 0, padding 0. Callout values right aligned; site-years Ink #303A39, shares Onyx #000000. Shows 172,239 21.2% / 26,911 12.0%. |  |
| 22 | `chart-size-band5` | Clustered bar chart | 1693* | 492* | 90* | 56* | Y-axis: Sites[Size band label]; X-axis: Sites[Band 5 share]; Tooltips: Sites[Band 5 share base] renamed Base | Preset CHART. As chart-sector-band5: bars #944126, inner padding 57%, X 0 to 0.25 off, Y off, labels off, constant line fx Sites[Random fifth] Ink 1 px, label off ('All sites 20%' is baked). |  |
| 23 | `text-sector-size-note` | Card (new) | 1329* | 586* | 496* | 20* | Data: Sites[Sector size note] | Preset BASE. 2023 + 2024 · DART: serious-injury rate per 100 full-time workers |  |
| 24 | `table-sector-band` | Table | 737 | 737 | 1088 | 217 | Columns: Bands[Band label] renamed Risk band; then Sites[Crossed Manufacturing], [Crossed Construction], [Crossed Transport and warehousing], [Crossed Wholesale], [Crossed Utilities], [Crossed Agriculture], [Crossed Mining, oil and gas], each renamed to its sector name | Preset TABLE. Sort: Band label ascending (follows Band order). Eight columns of 136 px; headers wrap to two lines (48 px header row). Header outline Bottom only, Card line #E3DECF. Risk band column: Background colour fx Field value Bands[Band fill]; Font colour fx Field value Bands[Band text fill]. Sector columns: right aligned; Data bars on (Apply to values only): Minimum Number 0, Maximum Number 1, positive bar #274A48, negative bar #E3DECF, not bar only; Background colour fx Rules: if value < 0 then #E3DECF; Font colour fx Rules: if value < 0 then Ink #303A39 (apply both rules to values and totals). Totals on, label All bands, Segoe UI Semibold 11 pt, top border 1 px Ink #303A39 (Grid > Borders > Totals section). Values under 100 site-years show Too few sites through the format string. Alt text: copy the mockup's aria-label (inventory.json has it). |  |
| 25 | `text-band-table-note` | Card (new) | 737* | 965* | 1088* | 20* | Data: Sites[Band table note] | Preset BASE. Crossed the line next year, 2023 + 2024 · line: each industry's worst-20% DART rate this year · data bars 0 to 100% · too few sites: under 100 site-years |  |

Why the values marked * differ from the box file:

- `kpi-band5-range-value` (box file 64, 376, 214, 40). The box is only as wide as the default text; the frame takes the figure column's width so longer values in other slicer states fit.
- `kpi-band5-range-count` (box file 64, 436, 268, 20). The box is only as wide as the default text; the frame gives longer values room.
- `kpi-all-sites-value` (box file 424, 376, 80, 40). The box is only as wide as the default text; the frame gives longer values room.
- `kpi-all-sites-count` (box file 424, 436, 217, 20). The text is 1 px wider than the figure column in the mockup font; the frame stays inside the 216 px column.
- `map-title` (box file 736, 176, 202, 28). The box is only as wide as the text; 250 px fits Band 2 share by state and stays clear of the baked legend on the right of the card head.
- `map-legend-title` (box file 797, 257, 227, 17). The box is the glyph box of an SVG text line; the frame is its 20 px line box.
- `map-tiles` (box file 737, 257, 480, 348). The box is the drawn tiles. The plot must be 11 x 8 cells of 44 px so the axis ranges put each tile centre on its baked ghost tile.
- `table-sector-context` (box file 1329, 221, 496, 241). The two-line header (48 px) must end on the baked rule at y 268, with the seven 28 px rows running to y 464.
- `chart-sector-band5` (box file 1693, 273, 76, 194). 0 to 25% at 3.6 px per point is 90 px, and the seven 28 px rows sit level with the table rows.
- `table-size-context` (box file 1527, 497, 298, 45). The box is the text extent. Two equal 240 px columns end on the mockup's right edges (x 1585 for site-years, x 1825 for shares) and two 28 px rows sit under the baked rule; the size names are baked.
- `chart-size-band5` (box file 1693, 489, 77, 56). Same scale as chart-sector-band5, with two 28 px rows level with the size values.
- `text-sector-size-note` (box file 1329, 587, 444, 17). The box is the glyph box of an SVG text line; the frame is its 20 px line box.
- `text-band-table-note` (box file 737, 965, 1015, 20). The box is only as wide as the default text; the frame gives longer values room.

**Edit interactions.**

Set these by hand. They keep the overlaid bars aligned with their tables and stop small state bases reaching the context visuals. Every other pair keeps the default.

| Source (select it, then Format > Edit interactions) | Filter | Highlight | None |
|---|---|---|---|
| `slicer-test-year` | every visual |   |   |
| `slicer-sector` | every other visual |   | table-sector-context, chart-sector-band5 |
| `slicer-size-band` | every other visual |   | table-size-context, chart-size-band5 |
| `map-tiles` | table-sector-band, map-title |   | table-sector-context, chart-sector-band5, table-size-context, chart-size-band5, map-legend-title, the rail cards, both notes |
| `table-sector-context` | map-tiles, map-title, table-size-context, chart-size-band5 | chart-sector-band5 | table-sector-band, map-legend-title, the rail cards, both notes |
| `chart-sector-band5` | map-tiles, map-title, table-size-context, chart-size-band5 |   | table-sector-context, table-sector-band, map-legend-title, the rail cards, both notes |
| `chart-size-band5` | map-tiles, map-title, table-sector-context, chart-sector-band5, table-sector-band |   | table-size-context, map-legend-title, the rail cards, both notes |
| `table-sector-band` | map-tiles, map-title |   | table-sector-context, chart-sector-band5, table-size-context, chart-size-band5, map-legend-title, the rail cards, both notes |

**Bookmark.** Set the page to: Test year 2023 + 2024; Sector and Size band cleared (All); no visual selections. Then View > Bookmarks > Add, name it Risk Landscape defaults, and in its options keep Data on, turn Display off, keep Current page on and apply to All visuals. Point `btn-reset-filters`'s action at it (Action > Type Bookmark > Risk Landscape defaults). Re-capture it whenever a default changes. Do not use the built-in Clear all slicers action: it clears rather than restores, and the measures would then fall back silently.

**Tooltip state page** (hidden). Page information: Allow use as tooltip on. Canvas settings: Type Custom, 240 x 96. Canvas background colour #000000, transparency 0%. Hide the page. It inherits the hovered state and the page's slicers; if it ever ignores the Test year slicer, sync the three slicers to it as hidden slicers (View > Sync slicers).

| # | id | Power BI visual | x | y | w | h | Fields | Format |
|---|---|---|---|---|---|---|---|---|
| T1 | `tt-state-name` | Card (new) | 16 | 12 | 208 | 20 | Data: StateGrid[State name] (First) | Callout Segoe UI Semibold 11 pt, Shell #FFFFFF, left. Label off, no background. |
| T2 | `tt-share-key` | Card (new) | 16 | 36 | 120 | 20 | Data: Sites[Map share label] | Segoe UI 11 pt, Axis grey #CFCBBD, left. Reads In band 5. |
| T3 | `tt-share-value` | Card (new) | 136 | 36 | 88 | 20 | Data: Sites[Map share] | Segoe UI 11 pt, Shell, right aligned. 0.0%. |
| T4 | `tt-base` | Card (new) | 16 | 60 | 208 | 20 | Data: Sites[State base line] | Segoe UI 11 pt, Axis grey #CFCBBD, left. Maine: 768 site-years · 2023 + 2024. |

Then on `map-tiles`: Format > Properties > Tooltips > Type Report page, Page Tooltip state.

### Page 3: Model Trust

Background `powerbi/backgrounds/page3-model-trust.png`. Population: all 215,802 test pairs (107,673 in 2023, 108,129 in 2024), as the header says. The Model and Test year slicers drive the key figures, the ROC curve, the calibration chart and the row fill; the comparison table, robustness and drivers do not move.

Baked in the background (check it is there; do not build it): kpi-auc-caption; kpi-gini-caption; the robustness labels, group rules, '428 pairs' note and 0.50 to 1.00 scale; the ROC and calibration axes, ticks and keys; the table's group labels and spanner rules.

| # | id | Power BI visual | x | y | w | h | Fields by well | Key format settings | Action, slicer, bookmark |
|---|---|---|---|---|---|---|---|---|---|
| 1 | `nav-executive-intelligence` | Button (Blank) | 705 | 37 | 186 | 38 | Text: Executive Intelligence | Preset NAV. | Page navigation to Executive Intelligence |
| 2 | `nav-risk-landscape` | Button (Blank) | 891 | 37 | 145 | 38 | Text: Risk Landscape | Preset NAV. | Page navigation to Risk Landscape |
| 3 | `nav-model-trust` | Button (Blank) | 1036 | 37 | 120 | 38 | Text: Model Trust | Preset NAV-ACTIVE. | None (current page) |
| 4 | `nav-pricing-lab` | Button (Blank) | 1156 | 37 | 115 | 38 | Text: Pricing Lab | Preset NAV. | Page navigation to Pricing Lab |
| 5 | `kpi-auc-value` | Card (new) | 64* | 424* | 336* | 40* | Data: Models[Picked AUC] | Preset FIGURE. 0.78 (format 0.00) |  |
| 6 | `kpi-auc-base` | Card (new) | 64* | 484* | 336* | 20* | Data: Models[Picked AUC base] | Preset BASE. Scorecard, 2023 · 95% CI 0.780 to 0.787 |  |
| 7 | `kpi-gini-value` | Card (new) | 424* | 424* | 216* | 40* | Data: Models[Picked Gini] | Preset FIGURE. 0.57 |  |
| 8 | `kpi-gini-base` | Card (new) | 424* | 484* | 216* | 20* | Data: Models[Picked test pairs] | Preset BASE. 107,673 test pairs · 2023 |  |
| 9 | `btn-reset-filters` | Button (Reset) | 540 | 612 | 100 | 20 | Text: Reset filters | Preset RESET. | Bookmark: Model Trust defaults |
| 10 | `slicer-model` | Button slicer | 64 | 652 | 576 | 72 | Field: ModelPicker[Model], renamed Model | Preset TILES. 4 buttons in Model order: Rating class only, Last year's rate, Scorecard, Gradient boosting. Default Scorecard. | Single select, Force selection, default Scorecard |
| 11 | `slicer-test-year` | Button slicer | 64 | 740 | 576 | 72 | Field: TestYearPicker[Tile label], renamed Test year | Preset TILES. 2 buttons: 2023, outcome 2024 and 2024, outcome 2025. Default 2023, outcome 2024. | Single select, Force selection, default 2023, outcome 2024 |
| 12 | `link-pricing-lab` | Button (Blank) | 64 | 996 | 576 | 20 | Text: Scores in pricing: Pricing Lab → | Preset LINK. Left aligned. | Page navigation to Pricing Lab |
| 13 | `table-model-comparison` | Table | 737 | 305 | 644 | 141 | Columns: Models[Model] renamed ' '; Models[AUC 2023] renamed 2023; [AUC 2024] renamed 2024; [Gini 2023] renamed '2023 '; [Gini 2024] renamed '2024 '; [Capture top 20% 2023] renamed '2023  '; [Capture top 20% 2024] renamed '2024  '; [Precision top 20% 2023] renamed '2023   '; [Precision top 20% 2024] renamed '2024   ' (trailing spaces keep the repeated names distinct) | Preset TABLE. Sort: Model ascending (follows Model order). Widths 140, 56, 56, 56, 56, 70, 70, 70, 70. Header outline Bottom only, Card line. Number headers and values right aligned; 2023 columns Onyx, 2024 columns Ink #303A39 (Specific column). Background colour fx Field value Models[Model row fill] on every column (the picked model's row turns #E3DECF). Totals off. AUC and Gini 0.000, shares 0.0% (from the measures). The group labels and their rules above the header are baked. Alt text: copy the mockup's aria-label (inventory.json has it). |  |
| 14 | `chart-robustness` | Clustered bar chart | 1685* | 217* | 140* | 364* | Y-axis: Robustness[Label]; X-axis: Robustness[Robustness AUC 2023]; Tooltips: Robustness[Robustness note] renamed Note | Preset CHART. Sort: Label ascending (follows Row order). Bars #274A48, inner padding 57%. X-axis off, range 0.5 to 1.148 (0.50 on the baked tick at x 1685, 1.00 on the tick at x 1793). Y-axis off (labels and the '428 pairs' note are baked). Data labels on: Outside end, Segoe UI 11 pt Onyx, 0.000. Alt text: copy the mockup's aria-label (inventory.json has it). |  |
| 15 | `chart-roc` | Line chart | 781* | 765* | 156* | 156* | X-axis: ROC[False positive rate] (Don't summarize); Y-axis: ROC[ROC true positive rate] renamed Crossers caught, ROC[Coin toss] renamed Coin toss; Tooltips: Models[Picked model and year] renamed Model and year | Preset CHART. X-axis type Continuous, range 0 to 1, off. Y-axis range 0 to 1, off. Series Crossers caught: Screen ink #274A48, 2 px, Shade area on, area transparency 88%. Series Coin toss: Muted #66655F, 1 px, dashed, no shade. Markers off. Alt text: fx, field ROC[Alt text ROC]. |  |
| 16 | `label-roc-auc` | Card (new) | 823 | 863 | 112 | 28 | Data: Models[ROC AUC label] | Preset TITLE. Right aligned. AUC 0.78. Sits inside the shaded area, under the diagonal. |  |
| 17 | `label-roc-selection` | Card (new) | 737 | 969 | 200 | 20 | Data: Models[Picked model and year] | Preset LABEL-INK. Right aligned. Scorecard, 2023. |  |
| 18 | `chart-calibration` | Line and clustered column chart | 1073* | 789* | 308* | 172* | X-axis: Calibration[Score decile]; Column y-axis: Calibration[Calibration share crossed] renamed Share that crossed; Line y-axis: Calibration[Calibration predicted] renamed Predicted; Tooltips: Models[Picked model and year] renamed Model and year | Preset CHART. X-axis type Categorical, on, Segoe UI 11 pt Muted, no title. Columns #B3AFA1, inner padding 42% (18 px). Line #274A48, 2 px, markers on, circle, 8 px, #274A48. Y-axis range 0 to 0.6, values off; Secondary y-axis on with the same range 0 to 0.6, values off (so the line and columns share one scale). Data labels off. Alt text: fx, field Calibration[Alt text calibration]. |  |
| 19 | `label-calibration-selection` | Card (new) | 1213 | 761 | 168 | 20 | Data: Models[Picked model and year] | Preset LABEL-INK. Right aligned. Scorecard, 2023. |  |
| 20 | `card-calibration-note` | Card (new) | 1073* | 815* | 308* | 40* | Data: Calibration[Calibration note] | Preset LABEL-INK. Left aligned, word wrap on. Empty by default; shows only when Last year's rate is picked. |  |
| 21 | `chart-drivers` | Clustered bar chart | 1477* | 772* | 348* | 196* | Y-axis: Drivers[Driver]; X-axis: Drivers[Driver AUC drop]; Tooltips: Drivers[Driver note] renamed Note | Preset CHART. Filter: Driver, Top N, top 7 by Driver AUC drop. Sort: Driver AUC drop descending. Bars #274A48, inner padding 57%. Y-axis on: Segoe UI 11 pt Onyx, no title (check the bars start under the baked header at x 1645; move the visual sideways if not). X-axis off, range 0 to 0.174. Data labels on: Outside end, Segoe UI 11 pt Onyx, 0.000. Alt text: copy the mockup's aria-label (inventory.json has it). |  |

Why the values marked * differ from the box file:

- `kpi-auc-value` (box file 64, 424, 57, 40). The box is only as wide as the default text; the frame gives longer values room.
- `kpi-auc-base` (box file 64, 484, 272, 20). The box is only as wide as the default text; the frame gives longer values room.
- `kpi-gini-value` (box file 424, 424, 58, 40). The box is only as wide as the default text; the frame gives longer values room.
- `kpi-gini-base` (box file 424, 484, 163, 20). The box is only as wide as the default text; the frame gives longer values room.
- `chart-robustness` (box file 1685, 222, 136, 353). The box is the bars and labels. The plot starts on the baked 0.50 tick (x 1685) and covers thirteen 28 px rows.
- `chart-roc` (box file 737, 737, 200, 256). The box is the whole SVG, baked axes included; the plot is the 156 px square inside it.
- `chart-calibration` (box file 1033, 737, 348, 256). The box is the whole SVG. The plot must run from the baked 60% tick (y 789) to the baked 0% baseline (y 937) between x 1073 and 1381, with the decile labels below.
- `card-calibration-note` (box file 0, 0, 0, 0). The note is hidden in the mockup's default state, so its box is empty; the frame comes from the HTML (inside the plot, two lines).
- `chart-drivers` (box file 1477, 737, 348, 256). The box is the whole SVG; the plot is seven 28 px rows from y 772.

**Edit interactions.**

The two slicers keep the default (Filter). Every other visual is set to None on every visual: the table, robustness and drivers have no relationship to the slicers, and a click on the ROC or calibration chart must not cut anything.

| Source (select it, then Format > Edit interactions) | Filter | Highlight | None |
|---|---|---|---|
| `slicer-model` | every visual |   |   |
| `slicer-test-year` | every visual |   |   |
| `table-model-comparison` |   |   | every visual |
| `chart-robustness` |   |   | every visual |
| `chart-roc` |   |   | every visual |
| `chart-calibration` |   |   | every visual |
| `chart-drivers` |   |   | every visual |

**Bookmark.** Set the page to: Model Scorecard; Test year 2023, outcome 2024; no visual selections. Then View > Bookmarks > Add, name it Model Trust defaults, and in its options keep Data on, turn Display off, keep Current page on and apply to All visuals. Point `btn-reset-filters`'s action at it (Action > Type Bookmark > Model Trust defaults). Re-capture it whenever a default changes. Do not use the built-in Clear all slicers action: it clears rather than restores, and the measures would then fall back silently.

### Page 4: Pricing Lab

Background `powerbi/backgrounds/page4-pricing-lab.png`. Everything is simulated, on the priced portfolio (99,185 sites in 2023, 99,965 in 2024). Defaults: Central, 2023, outcome 2024. The claim-cost slicer sits on the disconnected ClaimCostScenarios table and acts only through the measures.

Baked in the background (check it is there; do not build it): kpi-wrong-band-caption; kpi-overall-ratio-caption; the Simulated tags; the A and B legend; the Assumptions block and the high-scenario note.

| # | id | Power BI visual | x | y | w | h | Fields by well | Key format settings | Action, slicer, bookmark |
|---|---|---|---|---|---|---|---|---|---|
| 1 | `nav-executive-intelligence` | Button (Blank) | 705 | 37 | 186 | 38 | Text: Executive Intelligence | Preset NAV. | Page navigation to Executive Intelligence |
| 2 | `nav-risk-landscape` | Button (Blank) | 891 | 37 | 145 | 38 | Text: Risk Landscape | Preset NAV. | Page navigation to Risk Landscape |
| 3 | `nav-model-trust` | Button (Blank) | 1036 | 37 | 120 | 38 | Text: Model Trust | Preset NAV. | Page navigation to Model Trust |
| 4 | `nav-pricing-lab` | Button (Blank) | 1156 | 37 | 115 | 38 | Text: Pricing Lab | Preset NAV-ACTIVE. | None (current page) |
| 5 | `kpi-wrong-band-value` | Card (new) | 64* | 376* | 336* | 40* | Data: PricingSummary[Wrong band A to B]; Tooltips: PricingSummary[Wrong band definition] | Preset FIGURE. 27.5% → 10.0% |  |
| 6 | `kpi-wrong-band-base` | Card (new) | 150* | 436* | 250* | 20* | Data: PricingBands[Pricing scenario label] | Preset BASE. 2023 central |  |
| 7 | `kpi-overall-ratio-value` | Card (new) | 424* | 376* | 216* | 40* | Data: PricingSummary[Overall ratio A to B]; Tooltips: PricingSummary[Overall ratio note] | Preset FIGURE. 0.92 → 0.92 |  |
| 8 | `kpi-overall-ratio-base` | Card (new) | 510* | 436* | 130* | 20* | Data: PricingBands[Pricing scenario label] | Preset BASE. 2023 central |  |
| 9 | `btn-reset-filters` | Button (Reset) | 540 | 612 | 100 | 20 | Text: Reset filters | Preset RESET. | Bookmark: Pricing Lab defaults |
| 10 | `slicer-claim-cost` | Button slicer | 64 | 652 | 576 | 72 | Field: ClaimCostScenarios[Scenario], renamed Claim-cost scenario | Preset TILES. 3 buttons: Low, Central, High (Scenario order). Default Central. The table is disconnected, so the slicer filters nothing by itself; the measures read it. | Single select, Force selection, default Central |
| 11 | `slicer-score-year` | Button slicer | 64 | 740 | 576 | 72 | Field: ScoreYears[Tile label], renamed Test year | Preset TILES. 2 buttons: 2023, outcome 2024 and 2024, outcome 2025. Default 2023, outcome 2024. | Single select, Force selection, default 2023, outcome 2024 |
| 12 | `link-method-caveats` | Button (Blank) | 64 | 996 | 576 | 20 | Text: Method and caveats: Model Trust → | Preset LINK. Left aligned. | Page navigation to Model Trust |
| 13 | `chart-loss-premium-by-band` | Line chart | 737* | 217* | 644* | 352* | X-axis: PricingBands[Band label]; Y-axis: PricingBands[Band loss ratio A] renamed A, industry only, PricingBands[Band loss ratio B] renamed B, with the score; Tooltips: PricingBands[Band premium A] renamed Premium A, industry only; [Band premium B] renamed Premium B, with the score; [Band simulated loss] renamed Simulated loss; [Band tooltip base] renamed Base | Preset CHART. Sort: Band label ascending (follows Band order). Lines: transparency 100% on both series (markers only). Markers on, circle, 8 px: A #B3AFA1, B #274A48. Y-axis off, range -0.1 to 2.6. X-axis on, Segoe UI 11 pt Onyx, no title. Data labels on: series A position Left, Segoe UI 11 pt Ink, 0.00; series B position Right, Segoe UI Semibold 15 pt Onyx, 0.00, label background on, Card #F7F5EC, 0% transparency. Analytics: Error bars on series B, upper bound PricingBands[Band loss ratio high], lower bound PricingBands[Band loss ratio low], bar on, #B3AFA1, 2 px, no caps or markers (draws the A to B connector). Y-axis constant line 1: name '1.0: simulated loss equals premium', value 1, Ink 1 px solid, Behind, data label on, Name only, Segoe UI 11 pt Ink, Left, Above. Constant line 2: value 0, Axis #CFCBBD, 1 px solid, label off. Alt text: fx, field PricingBands[Alt text loss premium]. |  |
| 14 | `text-loss-premium-base` | Card (new) | 823* | 589* | 300* | 20* | Data: PricingBands[Pricing base line] | Preset BASE. 2023 central · 99,185 sites |  |
| 15 | `chart-premium-change` | Clustered column chart | 1477* | 217* | 348* | 352* | X-axis: PricingBands[Band short]; Y-axis: PricingBands[Band premium change]; Tooltips: the same four as chart-loss-premium-by-band | Preset CHART. Sort: Band short ascending (follows Band order). Columns: colour fx Field value PricingBands[Band colour]; inner padding 43% (40 px columns on a 69.6 px pitch). Y-axis off, range -0.5 to 1.15. X-axis on, Segoe UI 11 pt Onyx. Data labels on: Outside end, Segoe UI 11 pt Onyx (format from the measure, +0.0%). Analytics: Y-axis constant line, value 0, Ink 1 px solid, label off. Alt text: fx, field PricingBands[Alt text premium change]. |  |
| 16 | `text-premium-change-base` | Card (new) | 1563* | 589* | 262* | 20* | Data: PricingBands[Pricing base line] | Preset BASE. 2023 central · 99,185 sites |  |
| 17 | `table-claim-cost-sensitivity` | Table | 737 | 737 | 1088 | 113 | Columns: PricingSummary[Scenario] renamed Scenario; PricingSummary[Rule] renamed Cases priced × claim cost; [Scenario premium] renamed Simulated premium; [Scenario simulated loss] renamed Simulated loss; [Scenario loss ratio] renamed Loss / premium, A and B; [Scenario wrong band A to B] renamed Wrong band, A → B; [Scenario band spread A to B] renamed Band spread, A → B | Preset TABLE. Sort: Scenario ascending (follows Scenario order). Widths 96, 200, 152, 152, 168, 168, 152. Header outline Bottom only, Card line. Rule column Ink #303A39. Last three columns right aligned (headers and values). Data bars on Simulated premium and Simulated loss (values only): Minimum Number 0, Maximum Number 48000000000, positive bar #274A48, value shown. Background colour fx Field value PricingSummary[Scenario row fill] on every column. Totals off. Alt text: copy the mockup's aria-label (inventory.json has it). |  |
| 18 | `text-sensitivity-base` | Card (new) | 823* | 973* | 200* | 20* | Data: PricingBands[Pricing year base line] | Preset BASE. 2023 · 99,185 sites |  |

Why the values marked * differ from the box file:

- `kpi-wrong-band-value` (box file 64, 376, 199, 40). The box is only as wide as the default text; the frame gives longer values room.
- `kpi-wrong-band-base` (box file 150, 436, 85, 20). The box is only as wide as the default text; the frame starts 8 px after the baked Simulated tag and runs to the column edge.
- `kpi-overall-ratio-value` (box file 424, 376, 156, 40). The box is only as wide as the default text; the frame gives longer values room.
- `kpi-overall-ratio-base` (box file 510, 436, 85, 20). The box is only as wide as the default text; the frame gives longer values room.
- `chart-loss-premium-by-band` (box file 737, 268, 644, 296). The box is the drawn marks. The plot is the card's full plot area (y 217 to 541 for -0.1 to 2.6) with the band labels below.
- `text-loss-premium-base` (box file 823, 589, 175, 20). The box is only as wide as the default text; the frame starts after the baked Simulated tag and gives longer values room.
- `chart-premium-change` (box file 1477, 228, 348, 336). The box is the drawn marks. The plot is the full plot area (y 217 to 541 for -50% to +115%) with the band labels below.
- `text-premium-change-base` (box file 1563, 589, 175, 20). The box is only as wide as the default text; the frame gives longer values room.
- `text-sensitivity-base` (box file 823, 973, 125, 20). The box is only as wide as the default text; the frame gives longer values room.

**Edit interactions.**

Line charts cannot be highlighted, so the column chart is None on the line chart. Nothing filters the base-line cards, so they keep the whole portfolio's site count.

| Source (select it, then Format > Edit interactions) | Filter | Highlight | None |
|---|---|---|---|
| `slicer-claim-cost` | every visual |   |   |
| `slicer-score-year` | every visual |   |   |
| `chart-loss-premium-by-band` |   | chart-premium-change | every card, table-claim-cost-sensitivity |
| `chart-premium-change` |   |   | chart-loss-premium-by-band, every card, table-claim-cost-sensitivity |
| `table-claim-cost-sensitivity` |   |   | every visual |

**Bookmark.** Set the page to: Claim-cost scenario Central; Test year 2023, outcome 2024; no visual selections. Then View > Bookmarks > Add, name it Pricing Lab defaults, and in its options keep Data on, turn Display off, keep Current page on and apply to All visuals. Point `btn-reset-filters`'s action at it (Action > Type Bookmark > Pricing Lab defaults). Re-capture it whenever a default changes. Do not use the built-in Clear all slicers action: it clears rather than restores, and the measures would then fall back silently.

## g. Validation checklist

Open each page in reading view in its default state (select Reset filters where there is one) and tick each line. The values come from `docs/verified-metrics.md` and `outputs/powerbi/expected_values.csv`.

### Executive Intelligence

| Visual | Must show with no filters (defaults) | Source |
|---|---|---|
| `kpi-capture-value` | 51.4% | Top band capture 0.5141 in expected_values.csv |
| `kpi-capture-count` | 18,709 of 36,389 · 2023 + 2024 | verified: 18,709 of all 36,389 line-crossers |
| `chart-capture-vs-random` | Band 5 bar ends at 51.4% of the track (x about 237); Ink marker at 20% (x about 131) | Random fifth 20% |
| `kpi-hit-rate-value` | 47.0% | Top band hit rate 0.4697 |
| `kpi-hit-rate-count` | 18,709 of 39,830 · 2023 + 2024 | verified |
| `kpi-wrong-band-value` | 27.5% → 10.0% | Misallocated share A 0.2754, B 0.0995 (central 2023) |
| `chart-crossing-by-band` | 2.9%, 7.1%, 12.3%, 21.0%, 46.5%; dashed line at 18.3% labelled All sites 18.3%, 2023 + 2024 | verified risk bands, 2023; Base rate 0.1827 |
| `matrix-crossing-2024` | 3.0%, 7.6%, 12.8%, 22.0%, 47.5% | verified risk bands, 2024 |
| `table-sector-dart` | Transport and warehousing 4.29 / 21.0%; Agriculture 3.04 / 20.4%; Wholesale 2.83 / 21.2%; Manufacturing 2.17 / 20.3%; Construction 1.85 / 18.4%; Utilities 1.38 / 15.8%; Mining, oil and gas 0.77 / 19.8%, in that order | verified by sector |
| `chart-sector-band5` | Seven bars level with the table rows, all ending just short of or past the 20% line (Utilities the shortest) |  |
| `chart-auc-2023` | Scorecard bar longest, then Last year's rate, then Rating class only; labels about 8 in 10 and about 6 in 10 | verified AUC 0.783, 0.729, 0.592 |
| `table-auc-by-year` | 0.78 0.79 / 0.73 0.73 / 0.59 0.59 | verified, two decimals |

### Risk Landscape

| Visual | Must show with no filters (defaults) | Source |
|---|---|---|
| `kpi-band5-range-value` | 43.6% to 49.5% | utilities and construction band 5 |
| `kpi-band5-range-count` | 39,830 band 5 site-years · 2023 + 2024 | verified |
| `kpi-all-sites-value` | 18.3% | Base rate |
| `kpi-all-sites-count` | 36,389 of 199,150 · 2023 + 2024 | verified |
| `map-title / map-legend-title` | Band 5 share by state / Share of site-years, 2023 + 2024 |  |
| `map-tiles` | 46 tiles: 16 in #C98369 (25% and over, Maine darkest group), 15 in #D9B9A7, 15 in #EADFD2; no tile for AK, VT, WY, DE, DC, PR | verified state list (KS at 15.0% falls in 15% to 25%) |
| `Tooltip state (hover Maine)` | Maine / In band 5 42.6% / 768 site-years · 2023 + 2024 | verified |
| `table-sector-context` | Manufacturing 78,918 / 2.17 / 20.3%; Construction 43,110 / 1.85 / 18.4%; Transport and warehousing 36,087 / 4.29 / 21.0%; Wholesale 27,123 / 2.83 / 21.2%; Utilities 6,729 / 1.38 / 15.8%; Agriculture 6,335 / 3.04 / 20.4%; Mining, oil and gas 848 / 0.77 / 19.8% | verified by sector |
| `table-size-context` | 20 to 249 employees 172,239 / 21.2%; 250+ employees 26,911 / 12.0% | verified by size |
| `table-sector-band` | Band 5 row 46.4%, 49.5%, 46.4%, 47.0%, 43.6%, 45.0%, 46.4%; Mining bands 1 and 2 Too few sites; Agriculture band 3 13.4%; All bands 18.3%, 18.1%, 17.7%, 19.2%, 16.8%, 18.8%, 19.9% | verified sector by band (13.4% and 18.3% as corrected on 1 Nov) |
| `text-sector-size-note / text-band-table-note` | Both start with 2023 + 2024 (the note reads Crossed the line next year, 2023 + 2024 · ...) |  |

Slicer spot checks (computed from the workbook; not published figures):

- [ ] Test year 2023, outcome 2024: 44.2% to 49.4%; 20,191 band 5 site-years · 2023; 18.2%; 18,005 of 99,185 · 2023; notes start with 2023.
- [ ] Test year 2024, outcome 2025: 42.9% to 49.5%; 19,639 band 5 site-years · 2024; 18.4%; 18,384 of 99,965 · 2024.
- [ ] Click the Band 2 row: the map title reads Band 2 share by state and the tiles recolour; the sector and size tables do not change.
- [ ] Pick Mining, oil and gas in Sector: the sector table and bars keep all seven rows; the band table blanks the other six columns.

### Model Trust

| Visual | Must show with no filters (defaults) | Source |
|---|---|---|
| `kpi-auc-value / kpi-auc-base` | 0.78 / Scorecard, 2023 · 95% CI 0.780 to 0.787 | verified |
| `kpi-gini-value / kpi-gini-base` | 0.57 / 107,673 test pairs · 2023 | verified |
| `table-model-comparison` | AUC 0.592 0.589 / 0.729 0.729 / 0.783 0.785 / 0.800 0.801; Gini 0.183 0.177 / 0.459 0.458 / 0.567 0.571 / 0.600 0.601; caught 28.0% 27.2% / 49.8% 49.8% / 50.8% 51.1% / 51.7% 51.8%; share crossed 25.6% 24.8% / 45.9% 45.8% / 46.7% 46.9% / 47.6% 47.6%; Scorecard row filled #E3DECF | verified model table; Gradient boosting AUC 0.7999 and 0.8007 in expected_values.csv |
| `chart-robustness` | 0.783, 0.783, 0.782, 0.781, 0.808, 0.800, 0.787, 0.779, 0.779, 0.765, 0.761, 0.762, 0.915 | verified robustness and subgroups |
| `chart-roc / label-roc-auc / label-roc-selection` | Curve bowing above the dashed diagonal, shaded underneath / AUC 0.78 / Scorecard, 2023 |  |
| `chart-calibration / label-calibration-selection` | Decile 1: columns 2.1%, line 4.0%; decile 10: columns 55.5%, line 57.8% / Scorecard, 2023 | verified calibration, scorecard 2023 |
| `card-calibration-note` | Empty |  |
| `chart-drivers` | 0.125, 0.037, 0.018, 0.011, 0.011, 0.010, 0.007 (DART rank in industry first) | verified drivers, top seven |

Slicer spot checks (computed from the workbook; not published figures):

- [ ] Gradient boosting, 2024: 0.80; Gradient boosting, 2024 · 95% CI 0.798 to 0.804; 0.60; 108,129 test pairs · 2024; AUC 0.80; Gradient boosting row filled.
- [ ] Last year's rate: the calibration chart is empty and the note reads Last year's rate is a rank, not a probability, so it has no calibration.

### Pricing Lab

| Visual | Must show with no filters (defaults) | Source |
|---|---|---|
| `kpi-wrong-band-value / kpi-wrong-band-base` | 27.5% → 10.0% / 2023 central | verified |
| `kpi-overall-ratio-value / kpi-overall-ratio-base` | 0.92 → 0.92 / 2023 central | verified |
| `chart-loss-premium-by-band` | A 0.35, 0.58, 0.82, 1.19, 2.10; B 0.52, 0.87, 1.14, 1.00, 1.05; line at 1.0 labelled 1.0: simulated loss equals premium | verified 2023 central band table |
| `chart-premium-change` | −33.6%, −33.6%, −28.3%, +19.5%, +99.4% | verified |
| `text-loss-premium-base / text-premium-change-base` | 2023 central · 99,185 sites | verified 2023 portfolio |
| `table-claim-cost-sensitivity` | Low $10.02bn, $8.11bn, 0.81, 26.4% → 9.5%, 5.9x → 2.2x; Central $17.84bn, $16.43bn, 0.92, 27.5% → 10.0%, 6.1x → 2.2x (row filled #E3DECF); High $20.42bn, $18.80bn, 0.92, 27.5% → 10.0%, 6.1x → 2.2x | verified pricing scenarios |
| `text-sensitivity-base` | 2023 · 99,185 sites | verified |

Slicer spot checks (computed from the workbook; not published figures):

- [ ] Central, 2024: 26.7% → 9.3%; 0.96 → 0.96; 2024 central · 99,965 sites; A 0.38, 0.62, 0.87, 1.26, 2.21; B 0.57, 0.92, 1.20, 1.03, 1.09; change −33.3%, −32.8%, −27.4%, +22.4%, +102.5%; table $9.03bn / $16.48bn / $18.86bn premium.
- [ ] Low, 2023: 26.4% → 9.5%; 0.81 → 0.81; 2023 low; the Low row is filled.
- [ ] Click band 5 in the line chart: band 5 stays bright in the column chart, the others dim; the base lines still read 99,185 sites.

Every page:

- [ ] The active tab is Ember with Onyx text; the other three go Card line on hover and navigate.
- [ ] Every Cobalt link goes where its text says.
- [ ] Click every slicer state and Reset filters: nothing reads (Blank), every base line names its year or scenario, and the baked statement still holds.
- [ ] Every pricing figure sits beside a Simulated tag; no title or card says loss ratio without simulated.
- [ ] The footer source line is visible; the mockup corner label is not.

## Risks to watch

- Overlays. Bars sit over table columns (Executive Intelligence sectors, Risk Landscape sectors and sizes) and live charts sit on baked scales (AUC card, robustness, ROC, calibration). Power BI does not expose plot padding or exact bar thickness, so check each one at 100% in reading view after placing it, and keep every axis range fixed as given.
- Bar thickness. The thin bars need inner padding of 57% to 71%. If the editor caps inner padding lower, the bars come out thicker; keep the rows aligned and accept the thickness.
- Tile map. The scatter needs square markers tuned to 40 px and category labels centred on them. If labels drift off the tiles, check the plot is exactly 484 x 352 and the axis ranges are -0.5 to 10.5 and -0.5 to 7.5.
- Interactions and bookmarks are invisible settings that reset when a visual is recreated or pasted. Re-check the Edit interactions tables after any rebuild, and re-capture the defaults bookmarks after changing a default.
- Text cards. A text measure that returns blank shows (Blank). The measures here return text or an empty string instead; if a new one is added, keep that rule.
- Workbook changes. The measures name columns exactly. Re-exporting the workbook with renamed columns, or importing it in a way that types Risk band as a number, breaks them; freeze it for the build.
- Name clashes. Some measures share a name with a column in another table (for example Sites and Models[Sites], AUC 2023 and Robustness[AUC 2023]). Power BI allows this; never rename a column to a measure's name within its home table.
