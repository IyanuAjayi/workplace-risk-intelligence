# Workplace Risk Intelligence: design system

Version 1.1, 1 Nov 2026. For everyone designing or building the four Power BI pages: Executive Intelligence, Risk Landscape, Model Trust and Pricing Lab.

The four approved, built pages are the reference. Executive Intelligence set the pattern and the other three follow it; this document writes the pattern down. Where a mockup simplifies what Power BI draws (table data bars, default tooltips), this document describes the Power BI behaviour, and that is what to build.

| File | What it is |
| --- | --- |
| `powerbi/mockups/wri-system.css` | Tokens and components. Every mockup page links it |
| `powerbi/mockups/page1-executive-intelligence.html` to `page4-pricing-lab.html`, each with its `.png` | The four approved pages, built on the stylesheet. Executive Intelligence is the reference for structure |
| `powerbi/mockups/design-system.html` and `.png` | The board: palette, type, grid, states and components on one 1920 x 1080 sheet |
| `powerbi/theme/wri-theme.json` | The Power BI report theme |

Three principles carry through every decision below.

1. **Lead with the finding.** Each page opens with one statement in the rail and proves it with evidence on the right.
2. **Every number shows its base.** A rate always has its count and period on the page or in its tooltip.
3. **Colour carries one meaning each.** Ember is the active page, Cobalt is a link, band colours are risk bands, and nothing else borrows them. The one stated overlap is the top class of the Risk Landscape map, which shares Band 3's hex (section 1).

## 1. Colour

### Palette and roles

| Name | Hex | Role |
| --- | --- | --- |
| Nest | `#EFECDF` | Page canvas. The insight rail sits directly on it. The cream background always stays |
| Card | `#F7F5EC` | Evidence cards, the navigation strip, slicer fields, dropdown lists, table and matrix backgrounds |
| Card line | `#E3DECF` | The 1 px card hairline, the rule under a table header, bar tracks, hover fill, the Too few sites tag |
| Rule | `#DCD8CA` | Rail rules between ledger rows and above the caveat |
| Axis | `#CFCBBD` | Axis lines and ticks, the logo lockup divider, slicer borders, tooltip keys, the dashed outline of a Too few sites map tile |
| Onyx | `#000000` | Primary text and values. As a surface, only the signature stamp and tooltips |
| Ink | `#303A39` | Secondary text: tab labels, captions, reference labels, comparison values. As a surface, selected slicer tiles and checked boxes |
| Muted | `#66655F` | Tertiary text: base and count lines, table and slicer headers, axis titles, the proposition, the source line, the code on a Too few sites map tile |
| Shell | `#FFFFFF` | Text on Onyx, Ink, Screen ink and band 5 |
| Ember | `#E24337` | The active page tab and one dot per page. Nothing else: never a data colour, never a warning |
| Cobalt | `#1936E8` | Links: drill links, the caveat link, Reset filters. Never a data colour |
| Molt | `#B5C7E4` | The Simulated tag |
| Screen ink | `#274A48` | The primary model series (the scorecard, scenario B) and default data bars |
| Warm grey | `#B3AFA1` | Comparison: the series the primary one is read against, for example Rating class only, Last year's rate and scenario A. Marks only; a comparison's text is Ink |

### Risk bands

The five risk bands are scorecard fifths. Their colours are used for risk bands and nothing else, apart from the map's top class, which shares Band 3's hex (Map classes, below).

| Band | Hex | Lightness (L*) | Contrast on Card | Text on a band fill |
| --- | --- | --- | --- | --- |
| Band 1, lowest fifth | `#C9D6BD` | 84.1 | 1.39 : 1 | Onyx, 13.8 : 1 |
| Band 2 | `#D1A76A` | 71.0 | 2.04 : 1 | Onyx, 9.5 : 1 |
| Band 3 | `#C98369` | 61.4 | 2.77 : 1 | Onyx, 6.9 : 1 |
| Band 4 | `#A96247` | 49.0 | 4.25 : 1 | Onyx, 4.5 : 1 |
| Band 5, highest fifth | `#944126` | 38.2 | 6.32 : 1 | Shell, 6.9 : 1 |

`powerbi/tools/check_palette.py --bg "#F7F5EC"` passes the scale: lightness is ordered, and the smallest neighbour difference is 10.5 in normal vision, 10.5 under protanopia, 8.2 under deuteranopia and 9.5 under tritanopia. Bands 1 to 3 sit under 3 : 1 against the card, so a band colour never carries meaning alone: every band mark also carries its band name or its value.

### Map classes

The tile map on Risk Landscape shows each state's share of site-years in band 5 in three classes. They are the map's own ramp and are used nowhere else.

| Class | Hex | Lightness (L*) | Contrast on Card | State code on the tile |
| --- | --- | --- | --- | --- |
| Under 15% | `#EADFD2` | 89.4 | 1.20 : 1 | Onyx, 16.0 : 1 |
| 15% to 25% | `#D9B9A7` | 77.4 | 1.68 : 1 | Onyx, 11.5 : 1 |
| 25% and over | `#C98369` | 61.4 | 2.77 : 1 | Onyx, 6.9 : 1 |

A state under 500 site-years has too few sites to class: its tile is unfilled, with a dashed 1 px Axis grey outline and its code in Muted. `powerbi/tools/check_palette.py --bg "#F7F5EC" "#EADFD2" "#D9B9A7" "#C98369"` passes the ramp: lightness is ordered, and the smallest neighbour difference is 11.5 in normal vision, 9.2 under protanopia, 8.7 under deuteranopia and 12.1 under tritanopia. All three classes sit under 3 : 1 against the card, so every tile carries its state code and the card carries the class legend. The top class shares Band 3's hex, so the legend is always on show beside the map.

### Dark surfaces

The cream background stays. Dark surfaces are used in three places only, so each stays meaningful.

| Surface | Where | Why |
| --- | --- | --- |
| Onyx | The signature stamp on Executive Intelligence | The product's one signature figure, echoing Parakeet's black colour block with one large rounded corner |
| Onyx | Tooltips | Detail on demand reads as a separate layer above the cream page |
| Ink | Selected slicer tiles and checked boxes | A selected state that is clear without spending Ember or Onyx |

### Contrast of the text pairs we use

| Pair | Ratio | Pair | Ratio |
| --- | --- | --- | --- |
| Onyx on Card | 19.2 : 1 | Onyx on Ember (active tab) | 5.1 : 1 |
| Ink on Card | 10.7 : 1 | Shell on Ink (selected tile) | 11.7 : 1 |
| Muted on Nest | 4.9 : 1 | Axis grey on Onyx (tooltip keys) | 12.9 : 1 |
| Muted on Card | 5.4 : 1 | Ink on Molt (Simulated tag) | 6.9 : 1 |
| Cobalt on Card | 7.0 : 1 | Ink on Card line (Too few sites tag, hover) | 8.7 : 1 |

Muted text is never placed on Card line (4.35 : 1), Ember is never used for text (3.5 : 1 on Nest), and an Onyx value is never drawn over a Screen ink or Band 5 data bar (2.2 : 1 and 3.0 : 1).

## 2. Typography

### Three faces, two layers

| Face | Layer | Used for |
| --- | --- | --- |
| Inter | Baked into the page background image | Statements, titles, subtitles, explanatory copy |
| Segoe UI | Live, rendered by Power BI | Everything Power BI draws: figures, labels, axes, tables, slicers, buttons, tooltips. Inter stands in for it in mockups |
| IBM Plex Mono | Baked | Technical labels only: the source line, the test period, units. Always 13 px and sentence case |

Inter at weight 600 maps to Segoe UI Semibold; Inter at 400 and 500 maps to Segoe UI. Mabry and Yumex, Parakeet's website faces, are not licensed for reports and are not used.

### Type scale

| Style | Face | Size / line height | Weight | Tracking | Layer | Use |
| --- | --- | --- | --- | --- | --- | --- |
| Statement | Inter | 52 / 58 px | 500 | -2.2% | Baked | The rail finding. Two to four lines, ends with a full stop |
| Hero | Segoe UI Semibold | 96 / 96 px | 600 | -2% | Live | The signature stamp figure only, Shell on Onyx |
| Figure | Segoe UI Semibold | 30 / 40 px | 600 | -1.5% | Live | Ledger figures and analysis key figures |
| Data label | Segoe UI Semibold | 20 px | 600 | -0.5% | Live | Values on columns and bars |
| Title | Inter | 20 / 28 px | 600 | -0.5% | Baked | Product name, card titles, rail section heads |
| Body | Inter | 18 / 28 px | 400 | 0 | Baked | Ledger actions, the stamp caption, card subtitles, what it means |
| Label | Inter baked, Segoe UI live | 14 / 20 px | 500 | 0 | Both | Captions, base lines, tabs, axis labels, table text, slicers, tags, the caveat, drill links |
| Technical | IBM Plex Mono | 13 / 20 px | 500 | 0 | Baked | Source line, test period and population, units |

Rules that apply to every style:

- Sentence case everywhere, including tabs, buttons, headers and tags. No all-caps labels.
- No italic. Weights 400, 500 and 600 only.
- Nothing a reader needs is set below 14 px, except the 13 px technical labels.
- Figures in charts, tables and tooltips use tabular digits so columns of numbers line up (Inter's `tnum` in mockups; Segoe UI's digits are tabular by default).

### Sizes in Power BI

The report page is 1920 x 1080, so mockup pixels are Power BI pixels. Power BI sizes text in points: points are pixels x 0.75, rounded up to a whole point so live text never falls under its pixel size.

| Style | px | Power BI |
| --- | --- | --- |
| Hero | 96 | Segoe UI Semibold 72 pt, Shell |
| Figure | 30 | Segoe UI Semibold 23 pt (theme callout) |
| Data label, visual title | 20 | Segoe UI Semibold 15 pt |
| Body (live text boxes) | 18 | Segoe UI 14 pt |
| Label | 14 | Segoe UI 11 pt |

## 3. Spacing and grid

### Spacing

The base unit is 8 px. Margins, columns, gutters, rows and card sizes are all multiples of 8. Text is placed by its baseline, so a few text positions fall between grid lines (the statement at y 172, the base line at y 582). Inside components, 4 and 12 are allowed as half steps.

| Step | Typical use |
| --- | --- |
| 4 | Gap between a dropdown field and its open list, the space under a report-page tooltip's first line |
| 8 | Legend gaps, the gap between a tag and the text after it |
| 12 | Top padding of a ledger row, the gap between a slicer header and its field, report-page tooltip top and bottom padding, text inset in a dropdown |
| 16 | Report-page tooltip side padding, the chevron's inset in a dropdown |
| 24 | From the stamp to the figure column (x 400 to 424), the clear space at the bottom of a card |
| 32 | Gutters between columns, between cards and between canvas rows; card padding |
| 48 | The header band (y 32 to 80); from a rail section head to the first ledger row (y 696 to 744) |
| 64 | Page margins, the channel between rail and canvas, the gap from the header to the first row (y 80 to 144) |

### Page and columns

The page is 1920 x 1080 with 64 px margins left and right. It has 12 columns: 4 in the rail and 8 in the canvas, with 32 px gutters, and a 64 px channel between the two blocks. The canvas is exactly twice the rail.

| Block | x | Width | Columns |
| --- | --- | --- | --- |
| Rail | 64 to 640 | 576 | 4 columns of 120 at x 64, 216, 368, 520 |
| Channel | 640 to 704 | 64 | |
| Canvas | 704 to 1856 | 1152 | 8 columns of 116 at x 704, 852, 1000, 1148, 1296, 1444, 1592, 1740 |

Inside the rail, findings and figures use the **ledger split**: a statement column from x 64 to 424 (360 wide, of which the stamp takes 336) and a figure column from x 424 to 640 (216 wide). Every caption, base line and evidence figure starts at x 424, so related counts line up one above the other. Slicers use the rail's four columns instead.

### Rows

| Row | y | Height |
| --- | --- | --- |
| Header band | 32 to 80 | 48 |
| Canvas row 1 | 144 to 632 | 488 |
| Canvas row 2 | 664 to 1016 | 352 |
| Full-height card (instead of rows 1 and 2) | 144 to 1016 | 872 |
| Footer line | 1040 to 1060 | 20 |

### Card slots

| Slot | x | Width |
| --- | --- | --- |
| Full | 704 | 1152 |
| Halves | 704 and 1296 | 560 each |
| Quarters | 704, 1000, 1296, 1592 | 264 each |
| Three eighths and five eighths | 704 and 1148 | 412 and 708 |
| Five eighths and three eighths | 704 and 1444 | 708 and 412 |
| Three quarters and a quarter | 704 and 1592 | 856 and 264 |
| A quarter and two three eighths | 704, 1000 and 1444 | 264, 412 and 412 |

Card padding is 32 px. Inside a card the title line sits at +32 (28 tall), the optional subtitle at +64, the plot starts at +72 under a title or +112 under a title and subtitle, and nothing sits closer than 24 px to the card's bottom edge. The plot is the card width less 64.

## 4. Navigation and page structure

Every page has the same four parts in the same places: header, insight rail, evidence canvas, footer line.

### Header (identical on all four pages)

| Element | Position | Notes |
| --- | --- | --- |
| Logo | x 64, y 40, 28 tall (163.8 wide) | The official `powerbi/brand/parakeet-logo.svg`, unmodified, never recoloured |
| Lockup divider | x 252, y 38, 1 x 32 | Axis grey |
| Product name | x 276, y 32 | Title style: Workplace Risk Intelligence |
| Proposition | x 276, y 60 | Label, Muted: Predictive insights for industrial insurance underwriting |
| Navigation frame | x 704, y 36, 568 x 40 | Card fill, 1 px Card line border. Baked |
| Navigation buttons | y 37, 38 tall | Executive Intelligence x 705 w 186; Risk Landscape x 891 w 145; Model Trust x 1036 w 120; Pricing Lab x 1156 w 115. Label 14 px, 20 px side padding |
| Test period | right-aligned to x 1856, y 36 | Two technical lines: the period ("Test years 2023 + 2024"), then the page's population in Muted: "199,150 private-sector site-years" on every page except Model Trust, which reads "215,802 test pairs, public sites included" (section 10) |

Navigation states:

| State | Fill | Text |
| --- | --- | --- |
| Default | Card (the frame shows through) | Ink |
| Hover and press | Card line `#E3DECF` | Onyx |
| Active page | Ember `#E24337` | Onyx |
| Keyboard focus (mockups) | 2 px Cobalt outline inside the tab | |

Power BI's page navigator makes every button the same width, which cannot hold the approved tab widths, so the navigation is four page-navigation buttons. Each page carries its own copy with its own tab in the active state.

### Insight rail (x 64 to 640, on Nest)

The rail holds the page's finding as one statement, its key figure or figures, what it means, filters on analysis pages, and one caveat line.

**Executive Intelligence (as built):**

| Element | Position |
| --- | --- |
| Statement | x 64, y 172, 576 wide, four lines (to y 404) |
| Signature stamp | x 64, y 480, 336 x 152 (bottom aligns with canvas row 1 at 632) |
| Stamp caption | x 424, y 480, 216 wide, three lines |
| Base line | x 424, y 582 |
| Signature bar and its key | bar x 64, y 642, 336 x 20; key x 424, y 642 |
| Section head with the dot | x 64, y 696 (aligns with the titles of the row 2 cards) |
| Ledger rows | x 64, y 744 and y 848, 576 x 104 each |
| Close rule | x 64, y 952, 576 x 1 |
| Caveat | x 64, y 976, two lines to 1016 |

**Analysis pages (Risk Landscape, Model Trust, Pricing Lab):**

| Element | Position |
| --- | --- |
| Page tag (optional) | x 64, y 144, 20 tall: the back link on a drill-through page ("← Executive Intelligence" on Risk Landscape) or the Simulated banner on Pricing Lab |
| Statement | x 64, y 172, 576 wide, at most three lines (to y 346) |
| Key figures | y 376. First at x 64 (336 wide), optional second at x 424 (216 wide). Each: figure 40 tall, caption 20 (Ink), base line 20 (Muted) |
| What it means | Section head with the page's one dot at x 64, y 488; one sentence in Body at x 64, y 524, at most two lines |
| Filters head | x 64 to 640, y 608: Filters (Title) on the left, Reset filters on the right |
| Slicer row 1 | y 652: tile slicer, x 64, 576 x 72 |
| Slicer row 2 | y 740: a second tile slicer, x 64, 576 x 72 (Model Trust, Pricing Lab), or dropdown slicers at x 64 and x 368, 272 x 72 each (Risk Landscape) |
| Slicer row 3 | y 828: dropdown slicers at x 64 and x 368, only on a page with no notes block |
| Notes block (optional) | Rule at y 836, Title at y 848, up to three lines of Label from y 884, ending above the close rule: Limits of the data on Model Trust, Assumptions on Pricing Lab |
| Close rule | x 64, y 952 |
| Caveat | x 64, y 976, two lines to 1016 |

The signature stamp appears once in the product, on Executive Intelligence. Analysis pages state their key figures as ledger figures, which keeps Onyx rare and the stamp meaningful. The statement's line box starts at y 172 so the tops of its capitals (y 181) line up with those of the first card title (y 182).

### Evidence canvas and footer

The canvas holds cards in the rows and slots of section 3, built as section 8 describes. The footer line carries the source at x 64, y 1040 in the technical style, Muted, on one line. Mockups add a corner label right-aligned to x 1856, y 1040 (for example "Executive Intelligence. Design mockup, not a live Power BI report"); it never appears in Power BI.

## 5. KPI treatments

| Treatment | Specification | Example |
| --- | --- | --- |
| Signature stamp | Onyx block 336 x 152, top-right corner radius 72 (the only curve in the product), Hero figure in Shell inset 34 px. Caption beside it at x 424 in Body, reading on from the figure | 51.4% of next year's line-crossers were in band 5 |
| Signature bar | 336 x 20 under the stamp: the figure as an 8 px Band 5 bar on a Card line track, its comparison as a 2 px Ink marker | Band 5's 51.4% against a 20% marker |
| Secondary figure | A comparison value in Label, Ink, after its name, never larger than 14 px and never coloured | Random fifth 20% |
| Ledger figure | Figure style at x 424 inside a ledger row (104 tall, Rule above, 12 px top padding). Action on the left in Body, 360 wide, baseline-aligned with the figure. Caption below in Label, Ink | 47.0% of band 5 sites crossed |
| Base and count line | Label, Muted, one line, tabular figures: numerator of denominator, a middle dot, the period | 18,709 of 39,830 · 2023 + 2024 |
| Change figure | From-value, a thin space, an arrow, a thin space, to-value, in the Figure style | 27.5% → 10.0% |

Every percentage on a page has a base line beside it or in its tooltip. Every pricing figure is simulated and carries the Simulated tag at the start of its base line ("Simulated 2023 central"), on whichever page it appears.

## 6. Charts

### Mark types

| Chart | Use for | Specification |
| --- | --- | --- |
| Columns | Ordered categories: risk bands 1 to 5, score deciles | One fill per band, 120 px wide on a full card and 56 px on a half card; on a three-eighths card 40 px for five bands and 18 px for ten deciles. Data label above each column, category labels beneath, 1 px Ink baseline, no value axis, no gridlines |
| Bars | Ranked categories: sectors, states, models, robustness checks | Bar chart visuals; data bars inside a table follow section 7. 12 px thick on a 28 px row pitch beside table text, or 16 px on a 56 px pitch for a short model comparison; values aligned in a column at the right, or as outside-end data labels where the chart stands alone (the robustness and drivers charts on Model Trust); sorted by value or by the stated order |
| Lines | Curves and time: ROC, calibration, any trend | 2 px. Primary series Screen ink, comparisons Warm grey, the chance diagonal dashed Muted. Label line ends directly instead of using a legend. Markers only under 12 points |
| Dots and intervals | Estimates with ranges, paired scenarios: AUC with its 95% interval, simulated loss / premium by band under A and B | 8 px dots, Screen ink for the model or scenario B, Warm grey for the comparison or scenario A, intervals as 2 px lines in the series colour. Where an interval is narrower than the dot (the AUC intervals are about 0.004 either side), say so in the tooltip instead of drawing it |
| Tile map | One measure by state: the band 5 share on Risk Landscape | 40 px square tiles on a 44 px pitch: a native scatter chart with square markers over a baked grid that holds a dashed, unfilled tile and a Muted code for every state. A state with a value gets a live tile filled in its map class (section 1), its code in Label, Onyx; a state under 500 site-years gets no live tile, so it stays dashed and unfilled. The class legend sits in the card; its title names the selected years, so it is live |

### Lines, labels and axes

- **Reference line**: dashed 1 px Muted (4 on, 4 off) for an average or base rate, drawn behind the marks, labelled in Label Ink above its left end with its period: "All sites 18.3%, 2023 + 2024".
- **Constant line**: solid 1 px Ink for a fixed comparison (the 20% random fifth, 1.00 simulated loss / premium), labelled beneath or beside it.
- **Data labels**: label every mark when there are seven or fewer, in Data label style, Onyx, and drop the value axis. Percentages to one decimal (46.5%), AUC and Gini by the decimal rule below, lift to one with an x (2.6x), money in billions to two decimals ($17.84bn), counts with thousands separators.
- **AUC decimals**: a headline AUC takes two decimals, because the reader needs its level: a key figure, the AUC label on the ROC curve, the model card on Executive Intelligence (0.78). AUCs read against each other take three: the model comparison table and the robustness bars on Model Trust, where two decimals would hide real differences (the scorecard's 0.783 in 2023 and 0.785 in 2024 would both read 0.78, and so would every check from 0.781 to 0.783). Gini follows the same rule (0.57 as a key figure, 0.567 in the table). The drivers chart's AUC lost and a 95% interval in a base line also take three (0.125; 0.780 to 0.787). Every AUC in one visual uses the same precision.
- **Axis labels**: category names in Label, Onyx for the series to read first and Ink for comparisons. Axis titles, column headers, ticks and notes in Muted. Ticks 6 px in Axis grey.
- **Scales**: bars and columns start at zero, unless a floor is meaningful and labelled ("0.50 coin toss" for AUC).
- **Legends**: avoid them by labelling directly. When one is needed, it sits at the right of the card head in Label, Ink, with a 12 px swatch or the five-step band ramp.
- **Sorting**: natural orders stay natural (band 1 to 5, size bands ascending, deciles 1 to 10). Rankings sort by value, highest first.

### Colour in charts

Band colours only for risk bands; Screen ink for the primary model series; Warm grey for comparisons. The map classes (section 1) appear on the Risk Landscape map only. Ember, Cobalt and Onyx never appear in data. If two series need telling apart and neither is a band, use Screen ink and Warm grey, never two hues.

### When to show 2024

The model was tested on two unseen years, 2023 and 2024. Draw 2023 and show 2024 as a compact row or column of values beneath or beside it, in Ink, labelled "2024", whenever the point is that the result held in both years (the risk-band chart and the model card on Executive Intelligence). Draw both years as series only where the difference between test years is the subject, on Model Trust with its test-year slicer. Pooled figures say "2023 + 2024". Never average the two years without saying so.

## 7. Tables and filters

### Tables (table and matrix visuals)

- Card background, no banding, no vertical or horizontal gridlines.
- One 1 px Card line rule under the header row. Totals in Semibold with a 1 px Ink rule above.
- Header text Label, Muted. Values Label, Onyx; secondary values Ink.
- Row height 28 (Power BI row padding 4).
- Numbers right-aligned with tabular figures, text left-aligned.
- **Data bars** follow Power BI's own drawing, not the 12 px bar the mockups show. The bar fills the height of its row (28 px at 11 pt text and row padding 4, so the row sets its thickness), starts at the left edge of the cell and has no track. The value is drawn over the bar in the same cell, at the column's alignment: numbers are right-aligned, so the value sits at the cell's right edge and the bar runs under it only if it is long enough to reach it. Fix the axis rather than leaving it on Lowest and Highest value, so bars compare across cells and filter states, and fix it high enough that the longest bar ends clear of its value (section 1). Crossing rates use 0 to 100% (Minimum Number 0, Maximum Number 1), as in the "Bands split risk inside every sector" table on Risk Landscape, whose note says "data bars 0 to 100%". Pricing Lab's simulated premium and loss use 0 to $48bn. Band 5 for a share of sites in band 5, Screen ink for any other measure.
- **Conditional colour** comes only from the risk band field: the cell takes its band colour, with Onyx text on bands 1 to 4 and Shell on band 5 (Power BI: background colour by field value, from a band colour column). Never colour values on a gradient. The theme's default gradient is a neutral grey ramp so an accidental gradient cannot borrow band meaning.
- **Too few sites**: a row or cell under its minimum base shows the Too few sites tag instead of a value, and is listed but not ranked (states under 500 site-years, sector and band cells under 100 site-years). On the map a too-few-sites state is a dashed, unfilled tile instead (section 6).

### Filters

- Slicers live in the rail, under the Filters head, and nowhere else. Executive Intelligence has none.
- **Tile slicer** for two to four alternatives that matter (claim-cost scenario, test year, model): the full rail width, 576 x 72, equal tiles in one frame. Single select.
- **Test year** follows one convention on every page. The slicer is headed Test year and its single-year tiles read "2023, outcome 2024" and "2024, outcome 2025". A pooled "2023 + 2024" tile comes first only where pooling makes sense: Risk Landscape's descriptive figures pool, while Model Trust's model metrics and Pricing Lab's simulation are reported per test year. Single select with Force selection on, so a year, or the pooled pair, is always picked. Defaults: "2023 + 2024" on Risk Landscape, "2023, outcome 2024" on Model Trust and Pricing Lab.
- **Dropdown slicer** for long lists (sector, state, size band): 272 x 72, two per row at x 64 and x 368. Multi-select with Select all.
- Each slicer is a 20 px header in Label, Muted, a 12 px gap and a 40 px field.

| State | Tile | Dropdown |
| --- | --- | --- |
| Default | Ink text on Card, 1 px Axis frame, Card line dividers | Value in Onyx on Card, 1 px Axis border, Ink chevron |
| Hover | Card line fill, Onyx text | List row takes a Card line fill |
| Selected or open | Ink fill, Shell text | Border turns Ink, list opens 4 px below, 32 px rows, 14 px check boxes with Ink borders; checked boxes fill Ink with a Shell tick |

- **Reset filters** sits at the right of the Filters head in Cobalt Label with a 14 px reset icon. In Power BI it is a button that applies a Defaults bookmark (data only) restoring every slicer to its stated default. Do not use the built-in Clear all slicers action: it clears selections rather than restoring the defaults, and with nothing selected the pricing measures fall back to the central scenario and average the two test years without the page saying so.
- The baked rail statement stays true in every slicer state (section 10). Live key figures open in the default state, follow the slicers, and name the model, year or scenario they show in their base line ("Scorecard, 2023 · 95% CI 0.780 to 0.787").

## 8. Cards and analytical surfaces

- A card is Card fill with a 1 px Card line border, no radius and no shadow, and 32 px padding.
- One question per card. The title states the finding or names the measure in plain words ("Every sector has band 5 sites"), never a field name.
- The head row holds the title on the left and at most one element on the right: a drill link or a legend.
- An optional subtitle in Body, Muted, defines the measure ("Line: each industry's worst-20% serious-injury (DART) rate this year.").
- Card frames, titles and subtitles are baked into the background. The visuals placed on them have transparent backgrounds, no borders, no shadows, and no visual titles or card category labels (the theme sets all of this). A title or caption that must change with a slicer, to name the year, model or population picked, is a card or text box of its own (the map title and legend title on Risk Landscape).
- Surfaces have fixed jobs: Nest holds context (the rail), Card holds evidence, Onyx is for the stamp and tooltips, Ink is for selection. No other fills sit behind charts.
- A figure that is not yet computed gets a card with its title, the Pending validation tag and one sentence saying what is missing. No chart and no placeholder numbers.

## 9. Interaction and hover states

### Tooltips

Tooltips are Power BI's default tooltips, styled by the theme: Onyx background, values in Shell, keys muted to Axis grey `#CFCBBD`, Segoe UI 11 pt. Power BI sets their padding and position. A page uses a report-page tooltip only where its spec names one; today that is the state map on Risk Landscape (state, share in band 5, site-years and period). A report-page tooltip is an Onyx page in the same colours: the first line in Shell Semibold, keys and the base line in Axis grey, values in Shell, 12 x 16 px padding.

Content rules, for both kinds:

1. The first line names the mark: "Band 5, highest fifth".
2. Then up to three measure rows, key on the left and value on the right, with the period in the key: "Crossed the line, 2023 · 46.5%".
3. The last line is the base, with its unit: "18,709 of 39,830 site-years".
4. Every rate in a tooltip has its denominator. Simulated values end with the word Simulated and the scenario.
5. No more than five lines.

In a default tooltip each row is a field's name and its value, so rename fields for the visual to give these keys, and add the base as a text measure in the Tooltips well.

### Selection, drill and links

- **Selection**: clicking a mark cross-highlights the other visuals; the selected mark keeps its colour and the others dim, which mockups show at 40% opacity. A selected table row takes a Card line fill.
- **Drill cues**: a drill link in a card head reads "Page name →" in Cobalt Label and goes to the page that explains the card. The caveat link goes to the method on Model Trust; on Model Trust itself it goes on to Pricing Lab ("Scores in pricing: Pricing Lab →"). A drill-through page adds a back link, "← Page name", in the same style at the top of its rail (x 64, y 144).
- **Link style**: Cobalt, Label size, sentence case, no underline at rest, underlined on hover, colour unchanged. The arrow means navigation.
- **Navigation tabs**: see section 4. **Slicers**: see section 7.

## 10. Writing rules

- Sentence case everywhere. No italic, no exclamation marks, no em dashes: use a comma, a colon or "to" ("2016 to 2025").
- **Statement**: one sentence stating a finding with its comparison, 8 to 16 words, two to four lines at about 24 characters a line, ending with a full stop ("Top-band sites crossed the line about 16 times as often as bottom-band sites."). Never a question, never a topic label. It is baked into the background and cannot follow a slicer, so it must stay true in every filter state the page offers: every year, model, scenario, sector and size band it can show. If it is true of one model or population only, it names that model or population.
- **Name what the page can change**: when a page can change the model, year, scenario or population a figure describes, the figure names it in a live label ("Scorecard, 2023" beside the ROC curve and the calibration chart on Model Trust). A figure never relies on the slicer to say what it shows.
- **Card titles**: 3 to 7 words. Define DART and AUC where they first appear on a page.
- **Denominators**: every rate shows "x of y" and its period on the page or in its tooltip. Pooled years read "2023 + 2024". Units are written out: "rate per 100 full-time workers".
- **Populations** have fixed labels. Model metrics (AUC, Gini, top-20% capture and precision, ROC, calibration and the robustness checks) use all 215,802 test pairs, public sites included (107,673 in 2023, 108,129 in 2024), and say "all test pairs". Everything else (bands, sectors, states, sizes and every pricing figure) uses the priced portfolio, 199,150 private-sector site-years (99,185 in 2023, 99,965 in 2024). The header's second line names the page's population; a figure from the other population names its own ("AUC, 2023 test, all test pairs" on Executive Intelligence).
- **Model names** are the same on every page, in this order: Rating class only, Last year's rate, Scorecard, Gradient boosting. Never "rating class alone", "baseline" or a code such as M0.
- **Observed, predicted and simulated are different things** and are never mixed in one figure:
  - Observed is what OSHA records show: "crossed the line", "reported", "DART rate".
  - Predicted is model output: "score", "risk band", "predicted share".
  - Simulated is the pricing scenarios: "simulated premium", "simulated loss / premium". Every pricing figure is labelled Simulated, on every page it appears (the Executive Intelligence ledger included), and names its scenario (central, low or high claim cost; A or B). Never write "loss ratio" without "simulated".
- **Fixed caveats**: "Associations, not causes." "Reported injuries, not claims." Say "site-years" when years are pooled.
- **Tags** use exactly these words: Simulated, Too few sites, Pending validation. Tags are 20 px tall, Label, Ink text: Simulated on Molt, Too few sites on Card line, Pending validation in a 1 px dashed Ink outline.
- A number not in `docs/verified-metrics.md` is not shown. Label it Pending validation instead.

## 11. Power BI implementation

**As built (1 Nov 2026).** The report is generated from code, not set up by hand: `powerbi/tools/build_report.py` writes every page and visual, and `powerbi/tools/measures.py` every measure (`docs/powerbi-build-guide.md`). It follows this section, with these differences, explained in `docs/powerbi-implementation-notes.md`: the tile slicers are Power BI's classic slicer in tile mode, single select without forced selection, so Reset filters returns each page to its default (except a drill-through filter, which only Reset to default in the toolbar clears); the Risk Landscape map is a matrix laid out on the tile grid, not a scatter chart, and its hover tooltip is Power BI's default tooltip (state, band share, site-years) from an invisible scatter chart laid over the tiles, not a report-page tooltip; visual header icons are off report-wide; for privacy, the Sector and Size band dropdowns take one pick at a time and data export is off (2 Nov); the five 2024 band values and the six AUC values on Executive Intelligence are small cards; the Risk Landscape band table has data bars (fixed 0 to 100%, Screen ink) but Pricing Lab's table has none, because its simulated premium and loss are text measures; Risk Landscape is the one drill-through page, by sector from Executive Intelligence, and its "← Executive Intelligence" link is page navigation.

### Page setup

- Page size: Custom, 1920 x 1080. Mockup coordinates then equal Power BI coordinates.
- Canvas background: the exported PNG, Image fit Fit, transparency 0%. Wallpaper: Nest.
- Import the theme: View, Themes, Browse for themes, `powerbi/theme/wri-theme.json`.

### Baked or live

| Baked into the background image | Live Power BI visuals |
| --- | --- |
| Logo lockup, product name, proposition, test period | Navigation buttons, drill links, the caveat link, Reset filters |
| Navigation frame | Cards and text boxes holding figures, captions and base lines |
| Rail statement, section heads and the dot, ledger actions, rules, the stamp block, the caveat text | Charts, tables, matrices, slicers |
| Card frames, titles, subtitles, chart header rules, unit notes | Titles, legend titles and legends that change with a filter, as cards or text boxes |
| Footer source line | Tooltips |

In every mockup, each live element carries `data-pbi="visual"`, a unique `id` and `data-pbi-type` (the Power BI visual type, such as `card`, `textbox`, `actionButton`, `clusteredColumnChart`, `tableEx`, `pivotTable`). Name each visual in Power BI's Selection pane with that id, so QA can match mockup and report one to one. Copy each chart's `aria-label` into the visual's alt text.

### Exporting the background image

Opening any mockup as `page.html#baked` hides every live visual and the corner label, leaving exactly the background. Export it at 1x and 2x:

```sh
P=powerbi/mockups/page1-executive-intelligence
T=$(mktemp -d); "/Applications/Google Chrome.app/Contents/MacOS/Google Chrome" --headless=new --disable-gpu --hide-scrollbars --user-data-dir="$T" --window-size=1920,1080 --virtual-time-budget=8000 --screenshot="$PWD/$P-bg.png" "file://$PWD/$P.html#baked" 2>/dev/null; rm -rf "$T"
T=$(mktemp -d); "/Applications/Google Chrome.app/Contents/MacOS/Google Chrome" --headless=new --disable-gpu --hide-scrollbars --user-data-dir="$T" --window-size=1920,1080 --force-device-scale-factor=2 --virtual-time-budget=8000 --screenshot="$PWD/$P-bg@2x.png" "file://$PWD/$P.html#baked" 2>/dev/null; rm -rf "$T"
```

The 1x file is 1920 x 1080 and the 2x file is 3840 x 2160. Use the 2x file in Power BI: it is scaled to the page and keeps the baked text sharp on high-density screens.

### What the theme sets, and what is set by hand

The theme sets the data colours (the five bands, then Screen ink, Warm grey and Cobalt), text classes in Segoe UI, transparent visual backgrounds with no border or shadow, visual titles and card category labels switched off by default (titles and captions are baked into the backgrounds; a title switched on by hand takes Segoe UI Semibold 15 pt), default tooltips in Onyx with Shell values and Axis grey keys, axes without gridlines, card values without display units, slicer, table and matrix styling, and the Nest page and wallpaper.

Set these by hand:

- **Navigation buttons**: per state. Default: no fill, Ink text. Hover and press: fill `#E3DECF`, Onyx text. On each page, its own button: fill Ember, Onyx text, in every state.
- **The stamp figure**: card visual, 72 pt Segoe UI Semibold, Shell (its category label is already off in the theme).
- **Tile slicers**: the button slicer with Selected state Ink fill and Shell text, Hover state Card line fill. The test year slicer also has Single select and Force selection on (section 7).
- **Constant and reference lines**: in the Analytics pane, position Behind, styles from section 6.
- **Data bars and band colours**: conditional formatting as in section 7, with each data bar's Minimum and Maximum set to fixed numbers.
- **Map tiles**: on Risk Landscape's scatter chart, square markers coloured by conditional formatting with the three class hexes (section 1). A state under 500 site-years gets no marker, so its baked dashed tile shows.
- **Number formats**: in the measures (`outputs/powerbi/measures.dax`).
- **Tooltips**: leave each visual on the default tooltip. If the modern tooltip ignores the theme's colours, set Tooltips, Background to Onyx and the text colours by hand. The one report-page tooltip, for Risk Landscape's map, is a page with Allow use as tooltip on and an Onyx canvas, set as the map's tooltip page.

### Before sharing

- Every figure matches `outputs/powerbi/expected_values.csv` and `docs/verified-metrics.md`; run `powerbi/tools/check_numbers.py` on each mockup.
- Click every slicer state and the Reset filters button: nothing goes blank, the baked statement still holds in every state, and every live figure names the model, year or population it shows.
- Every pricing figure carries the Simulated tag, on every page.
- The footer source line is on every page.
