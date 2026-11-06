# Power BI implementation notes

Built 1 Nov 2026 from the approved mockups (pages 1 to 4 in `powerbi/mockups/`), with additions deployed later the same day: a sector drill-through, a hover tooltip on the map, data bars and an "All bands" total in the band table, and A to B connectors on Pricing Lab. Screenshots of the live report are in `powerbi/live/`. How to rebuild: `docs/powerbi-build-guide.md`.

## How a page is put together

Each page is a 1920 x 1080 background image plus native Power BI visuals on top of it.

- **Baked into the background** (rendered from the mockup by `render_backgrounds.py`): the logo lockup, page titles, the rail statement, captions, card frames, headers that never change, legends, the source line. Nothing that depends on data or a filter is baked, with one kind of exception: fixed reference labels whose position is set by a fixed axis, such as "All sites 20%" (the random fifth) and the "0.50 coin toss, 0.75, 1.00" scales.
- **Live** (drawn by Power BI from the model): every figure, bar, line, table, map tile, slicer and button. 93 visuals across the four pages, all bound to the 100 measures in `powerbi/model/measures.tmdl`.

Fonts: Inter in the baked layer, Segoe UI in live visuals, as the design system specifies. The theme is `powerbi/theme/wri-theme.json`.

## What a user can do

| Page | Interactions |
| --- | --- |
| All | Page tabs at the top; text links to the related page ("Risk Landscape →", "Model Trust →", "Method and caveats: Model Trust →", "Scores in pricing: Pricing Lab →", "← Executive Intelligence"); hover tooltips on charts, styled by the theme |
| Executive Intelligence | A fixed summary of both test years. Selecting a bar highlights it but filters nothing else, so every figure on the page stays the pooled figure the statement describes. Right-click a sector (for example a bar in "Every sector has band 5 sites") and choose Drill through, Risk Landscape: that page opens filtered to the sector |
| Risk Landscape | Test year tiles (2023 + 2024, 2023, 2024), single-pick Sector and Size band dropdowns, Reset filters. Clicking a band row in the band table re-colours the map for that band ("Band 3 share by state"). Hovering a state shows its name, band share and site-years (from 500 site-years; smaller states read Under 500 site-years and Too few sites). Clicking a state changes nothing on the page: the click lands on the invisible hover layer, which filters nothing. Opened by drill-through, the page shows the chosen sector only, and keeps that filter until Reset to default (below) |
| Model Trust | Model tiles and test year tiles drive the key figures, the highlighted table row, the ROC curve and the calibration chart. Reset filters |
| Pricing Lab | Claim-cost scenario tiles and test year tiles drive every figure, both charts and the highlighted scenario row. Reset filters |

Reset filters is Power BI's "Clear all slicers" button. After a reset the tiles show no selection and the page shows its defaults: 2023 + 2024; Scorecard, 2023; Central, 2023. The measures fall back to these defaults whenever nothing is picked. Reset filters does not clear a drill-through filter.

## Where the build differs from the mockups

| Page | Mockup | Built | Why |
| --- | --- | --- | --- |
| All | Tile slicer with the default tile always selected | Single-select tiles that can be cleared; measures default when none is picked | A forced selection would make Reset jump to the first tile (for example "Rating class only") instead of the default |
| All | Visual header icons | Off report-wide | They appeared on hover over baked titles |
| Executive | 2024 row as a one-row matrix | Five small cards, one per band, under the columns | A matrix cannot hide its headers or match the column positions |
| Executive | AUC 2023 and 2024 values as a table | Six small cards | Same reason; the bars and "about 8 in 10" labels stay live |
| Executive | Sector shares right-aligned after the bars | Inside the bars, in white | Labels outside the bars collide with the 20% line |
| Executive | Band chart line label "All sites 18.3%, 2023 + 2024" | "All sites, 2023 + 2024: 18.3%" | Power BI's constant-line label puts the name before the value |
| Risk Landscape | Tile map as a scatter chart | A matrix laid out on the tile grid: transparent cells, so the baked ghost tile shows for states under 500 site-years | A scatter cannot centre the state codes on the tiles |
| Risk Landscape | Report-page tooltip for each state (name, band 5 share, site-years) | Power BI's default tooltip, from an invisible scatter chart over the tiles with one point per state at its tile centre (measures `Map hover x` and `Map hover y`, with a blank number format): state name, band share and site-years | Power BI would not use a report-page tooltip on the matrix or the scatter here |
| Risk Landscape | Map click filters the page | Map click changes nothing on the page: it lands on the invisible hover layer, and the tiles and the hover layer are set to No filter on the other visuals | With a single state selected, some sector cells fall below "about twice" (for example Washington agriculture 1.35x on 143 site-years), and the baked statement would be wrong |
| Risk Landscape | Sector and Size band dropdowns multi-select with Select all | One pick at a time (2 Nov) | Comparing two multi-sector map views could reveal small groups; see the privacy note in `docs/qa-note.md` |
| Model Trust | Robustness labels and scale | Row labels and the 0.50 to 1.00 scale baked; bars and values live | The rows are fixed, and live labels would not line up with the baked scale |
| Model Trust | Calibration note appears only for Last year's rate | Same, as a card that is blank for the other models | |
| Pricing Lab | Data bars on simulated premium and loss | Values only | They are text measures (next row), and a data bar needs a number |
| Pricing Lab | Totals in $bn | Text measures (`$17.84bn`) | The service ignored the billions scaling format |

Drill-through is by sector only. Risk Landscape is a drill-through page bound to Sites[Sector] (`powerbi/tools/build_report.py`: `DRILL` and `page_json`): right-click a sector on Executive Intelligence, choose Drill through, Risk Landscape, and the page opens filtered to that sector. The filter stays on Risk Landscape after you leave it, also when the page is reopened from its tab, and the Sector dropdown still reads All while it is on. The page's Reset filters (Clear all slicers) does not clear it, because a drill-through filter is not a slicer; Reset to default in the toolbar does (checked live on 2 Nov). Its "← Executive Intelligence" link is page navigation, like the other links between pages, and otherwise filtering is by slicer and cross-highlight. There is no drill-through by band, because it would cut the band table to one row.

The first build's gaps in the band table, and its missing A to B connectors on Pricing Lab, are closed. Every sector column in the band table has a data bar on a fixed 0 to 100% scale in Screen ink, with the value still printed, and Too few sites cells draw no bar. The table's total row reads "All bands". On Pricing Lab's "Simulated loss / premium by band", a vertical connector joins each band's A and B points, drawn as error bars on series A from the lower to the higher of the two values (measures `Band loss ratio low` and `Band loss ratio high`). The bars and connectors come from `data_bars` and `connectors` in `powerbi/tools/build_report.py`.

## Corrections found during the build

The Power BI measures round once from full values. They disagreed with `docs/verified-metrics.md` in five Risk Landscape figures that had been rounded twice (Manufacturing crossing rate 18.4% to 18.3%, Agriculture band 3 13.5% to 13.4%, Georgia 14.4% to 14.5%, Kentucky and Utah 14.1% to 14.0%). The document, the mockup and `scripts/09_landscape.py` (now six decimals in its CSVs) are corrected; details in `docs/qa-note.md`. No headline figure changed.

## Known limits of the build

- The report is deployed from the definition in `powerbi/report/`. Edits made by hand in the Power BI editor are overwritten by the next deploy.
- Power BI keeps each viewer's last filter state. After testing, use Reset to default in the toolbar.
- A sector drill-through filter stays on Risk Landscape until Reset to default in the toolbar; the page's Reset filters leaves it on. After showing a drill-through, reset before passing the report on.
- The semantic model reads the workbook from OneDrive. A rebuilt workbook must be copied there and the model refreshed.
- Two test years only, reported injuries not claims, and simulated pricing: the same limits as the analysis, shown on every page.

## Checks

Late on 1 Nov, after the additions were deployed, the live report and model were compared with the repository. The live report definition (Fabric getDefinition) equals `powerbi/report/` file by file, compared as canonical JSON; the service adds only its own `.platform`, `definition.pbir` and base theme. The live model's 100 measures equal `powerbi/model/measures.tmdl` in expression, format string and table. Rerunning `powerbi/tools/measures.py` and `powerbi/tools/build_report.py` changes nothing. The report shows "You're viewing the author's default view", so no saved viewer state needs resetting. On 2 Nov two interactions were checked live: clicking a state changes nothing on the page, and a sector drill-through filter stays on Risk Landscape, also after leaving it and reopening it from its tab, until Reset to default. The report was then reset to the author's default view. The figure and interaction checks are in `docs/powerbi-build-guide.md`, section 4.
