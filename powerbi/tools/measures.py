"""
Every DAX measure in the Workplace Risk Intelligence semantic model, in one place. The measures are added to the model
built from outputs/powerbi/workplace_risk_powerbi.xlsx (see docs/powerbi-build-guide.md).

Writes powerbi/model/measures.tmdl, a TMDL script to paste into the Power BI TMDL view and apply ("createOrReplace"
leaves tables and data alone and adds or replaces only these measures), and outputs/powerbi/measures.dax, the same
measures as a readable listing.

Usage: .venv/bin/python powerbi/tools/measures.py
"""
from pathlib import Path

OUT = Path(__file__).resolve().parents[1] / "model" / "measures.tmdl"
LISTING = Path(__file__).resolve().parents[2] / "outputs" / "powerbi" / "measures.dax"
TOO_FEW = '0.0%;"Too few sites"'  # cells under 100 site-years return -1, shown by the negative section
SECTORS = ["Manufacturing", "Construction", "Transport and warehousing", "Wholesale", "Utilities", "Agriculture",
           "Mining, oil and gas"]

# (table, display folder, name, expression, format string or None, dynamic format string or None)
MEASURES = [
    # ---- base measures on the priced portfolio (Sites: one row per year, sector, state, size and band) ----
    ("Sites", "Base", "Sites scored", "SUM ( Sites[Site count] )", "#,0", None),
    ("Sites", "Base", "Sites crossing next year", "SUM ( Sites[Crossing sites] )", "#,0", None),
    ("Sites", "Base", "Base rate", "DIVIDE ( [Sites crossing next year], [Sites scored] )", "0.0%", None),
    ("Sites", "Base", "Average site DART rate", "DIVIDE ( SUM ( Sites[DART rate sum] ), [Sites scored] )", "0.00", None),
    ("Sites", "Base", "Test year label", 'SELECTEDVALUE ( TestYears[Test year], "2023 + 2024" )', None, None),

    # ---- Executive Intelligence (both test years pooled, no slicers) ----
    ("Sites", "Executive Intelligence", "Band 5 sites", 'CALCULATE ( [Sites scored], Sites[Risk band] = "5 highest" )', "#,0", None),
    ("Sites", "Executive Intelligence", "Band 5 crossing sites",
     'CALCULATE ( [Sites crossing next year], Sites[Risk band] = "5 highest" )', "#,0", None),
    ("Sites", "Executive Intelligence", "All crossing sites",
     "CALCULATE ( [Sites crossing next year], REMOVEFILTERS ( Sites[Risk band], Sites[Band order] ), REMOVEFILTERS ( Bands ) )",
     "#,0", None),
    ("Sites", "Executive Intelligence", "All sites scored",
     "CALCULATE ( [Sites scored], REMOVEFILTERS ( Sites[Risk band], Sites[Band order] ), REMOVEFILTERS ( Bands ) )", "#,0", None),
    ("Sites", "Executive Intelligence", "Top band capture", "DIVIDE ( [Band 5 crossing sites], [All crossing sites] )", "0.0%", None),
    ("Sites", "Executive Intelligence", "Capture remainder", "1 - [Top band capture]", "0.0%", None),
    ("Sites", "Executive Intelligence", "Top band hit rate", "DIVIDE ( [Band 5 crossing sites], [Band 5 sites] )", "0.0%", None),
    ("Sites", "Executive Intelligence", "Share of sites in top band", "DIVIDE ( [Band 5 sites], [All sites scored] )", "0.0%", None),
    ("Sites", "Executive Intelligence", "All sites rate", "DIVIDE ( [All crossing sites], [All sites scored] )", "0.0%", None),
    ("Sites", "Executive Intelligence", "Random fifth", "0.2", "0%", None),
    ("Sites", "Executive Intelligence", "Capture base line",
     'FORMAT ( [Band 5 crossing sites], "#,0" ) & " of " & FORMAT ( [All crossing sites], "#,0" ) & " · 2023 + 2024"', None, None),
    ("Sites", "Executive Intelligence", "Hit rate base line",
     'FORMAT ( [Band 5 crossing sites], "#,0" ) & " of " & FORMAT ( [Band 5 sites], "#,0" ) & " · 2023 + 2024"', None, None),
    ("Sites", "Executive Intelligence", "Crossing rate 2023", "CALCULATE ( [Base rate], Sites[Score year] = 2023 )", "0.0%", None),
    ("Sites", "Executive Intelligence", "Crossing rate 2024", "CALCULATE ( [Base rate], Sites[Score year] = 2024 )", "0.0%", None),
    ("Models", "Executive Intelligence", "AUC 2023", "CALCULATE ( AVERAGE ( 'Models'[AUC] ), 'Models'[Test year] = 2023 )", "0.000", None),
    ("Models", "Executive Intelligence", "AUC 2024", "CALCULATE ( AVERAGE ( 'Models'[AUC] ), 'Models'[Test year] = 2024 )", "0.000", None),
    ("Models", "Executive Intelligence", "AUC 2023 words",
     "VAR m = SELECTEDVALUE ( 'Models'[Model] )\n"
     "RETURN IF ( m <> \"Last year's rate\", \"about \" & FORMAT ( ROUND ( [AUC 2023] * 10, 0 ), \"0\" ) & \" in 10\" )", None, None),
    ("PricingSummary", "Executive Intelligence", "Wrong band A to B 2023 central",
     'VAR f = FILTER ( ALL ( PricingSummary ), PricingSummary[Score year] = 2023 && PricingSummary[Claim-cost scenario] = "central" )\n'
     'RETURN FORMAT ( MAXX ( f, PricingSummary[Misallocated share A] ), "0.0%" ) & UNICHAR ( 8201 ) & "→" & UNICHAR ( 8201 )\n'
     '    & FORMAT ( MAXX ( f, PricingSummary[Misallocated share B] ), "0.0%" )', None, None),

    # ---- Risk Landscape (slicers: test year tiles, sector, size band; a band row can be picked in the band table) ----
    ("Sites", "Risk Landscape", "Portfolio site-years",
     "CALCULATE ( [Sites scored], REMOVEFILTERS ( Bands ), REMOVEFILTERS ( Sites[Risk band], Sites[Band order] ) )", "#,0", None),
    ("Sites", "Risk Landscape", "Portfolio crossing sites",
     "CALCULATE ( [Sites crossing next year], REMOVEFILTERS ( Bands ), REMOVEFILTERS ( Sites[Risk band], Sites[Band order] ) )",
     "#,0", None),
    ("Sites", "Risk Landscape", "Portfolio crossing rate", "DIVIDE ( [Portfolio crossing sites], [Portfolio site-years] )", "0.0%", None),
    ("Sites", "Risk Landscape", "Portfolio base line",
     'FORMAT ( [Portfolio crossing sites], "#,0" ) & " of " & FORMAT ( [Portfolio site-years], "#,0" ) & " · " & [Test year label]',
     None, None),
    ("Sites", "Risk Landscape", "Portfolio DART rate",
     "CALCULATE ( [Average site DART rate], REMOVEFILTERS ( Bands ), REMOVEFILTERS ( Sites[Risk band], Sites[Band order] ) )",
     "0.00", None),
    ("Sites", "Risk Landscape", "Band 5 site-years",
     'CALCULATE ( [Sites scored], REMOVEFILTERS ( Bands ), REMOVEFILTERS ( Sites[Band order] ), Sites[Risk band] = "5 highest" )',
     "#,0", None),
    ("Sites", "Risk Landscape", "Band 5 share", "DIVIDE ( [Band 5 site-years], [Portfolio site-years] )", "0.0%", None),
    ("Sites", "Risk Landscape", "Band 5 base line",
     'FORMAT ( [Band 5 site-years], "#,0" ) & " band 5 site-years · " & [Test year label]', None, None),
    ("Sites", "Risk Landscape", "Band 5 crossing range",
     "VAR t =\n"
     "    FILTER (\n"
     "        ADDCOLUMNS (\n"
     "            VALUES ( Sites[Sector] ),\n"
     '            "@n", CALCULATE ( [Sites scored], REMOVEFILTERS ( Bands ), REMOVEFILTERS ( Sites[Band order] ), Sites[Risk band] = "5 highest" ),\n'
     '            "@r", CALCULATE ( [Base rate], REMOVEFILTERS ( Bands ), REMOVEFILTERS ( Sites[Band order] ), Sites[Risk band] = "5 highest" )\n'
     "        ),\n"
     "        [@n] >= 100\n"
     "    )\n"
     "VAR lo = MINX ( t, [@r] )\n"
     "VAR hi = MAXX ( t, [@r] )\n"
     "RETURN\n"
     "    IF (\n"
     "        NOT ISEMPTY ( t ),\n"
     '        IF ( ROUND ( lo, 3 ) = ROUND ( hi, 3 ), FORMAT ( lo, "0.0%" ), FORMAT ( lo, "0.0%" ) & " to " & FORMAT ( hi, "0.0%" ) )\n'
     "    )", None, None),
    ("Sites", "Risk Landscape", "Map band order", "COALESCE ( SELECTEDVALUE ( Bands[Band order] ), 5 )", "0", None),
    ("Sites", "Risk Landscape", "Map share",
     "VAR b = [Map band order]\n"
     "RETURN DIVIDE ( CALCULATE ( [Sites scored], REMOVEFILTERS ( Bands ), REMOVEFILTERS ( Sites[Risk band] ), Sites[Band order] = b ), [Portfolio site-years] )",
     "0.0%", None),
    # a space, not blank, keeps every grid row and column in the map matrix; states under 500 site-years get no tile
    ("Sites", "Risk Landscape", "Map tile label", 'IF ( [Portfolio site-years] >= 500, SELECTEDVALUE ( StateGrid[State] ), " " )', None, None),
    ("Sites", "Risk Landscape", "Map tile colour",
     "VAR s = [Map share]\n"
     'RETURN IF ( [Portfolio site-years] >= 500, SWITCH ( TRUE (), s >= 0.25, "#C98369", s >= 0.15, "#D9B9A7", "#EADFD2" ) )',
     None, None),
    ("Sites", "Risk Landscape", "State name label", "SELECTEDVALUE ( StateGrid[State name] )", None, None),
    # an invisible scatter over the map tiles carries the hover tooltip (matrix cells cannot use a tooltip page)
    ("Sites", "Risk Landscape", "Map hover x", "SELECTEDVALUE ( StateGrid[Grid column] )", ";;;", None),
    ("Sites", "Risk Landscape", "Map hover y", "7 - SELECTEDVALUE ( StateGrid[Grid row] )", ";;;", None),
    ("Sites", "Risk Landscape", "Map title", '"Band " & [Map band order] & " share by state"', None, None),
    ("Sites", "Risk Landscape", "Map legend title", '"Share of site-years, " & [Test year label]', None, None),
    ("Sites", "Risk Landscape", "Map share label",
     'IF ( [Portfolio site-years] < 500, "Too few sites", FORMAT ( [Map share], "0.0%" ) & " in band " & [Map band order] )', None, None),
    # the hover gives no exact base under 500, so small groups can't be counted state by state
    ("Sites", "Risk Landscape", "State site-years",
     'IF ( [Portfolio site-years] < 500, "Under 500", FORMAT ( [Portfolio site-years], "#,0" ) ) & " site-years · " & [Test year label]',
     None, None),
    ("Sites", "Risk Landscape", "Site-years label", 'FORMAT ( [Portfolio site-years], "#,0" )', None, None),
    ("Sites", "Risk Landscape", "Portfolio note", '[Test year label] & " · DART: serious-injury rate per 100 full-time workers"', None, None),
    ("Sites", "Risk Landscape", "Cell site-years", "CALCULATE ( [Sites scored], REMOVEFILTERS ( Sites[Risk band], Sites[Band order] ) )", "#,0", None),
    ("Sites", "Risk Landscape", "Cell crossing rate",
     "VAR n = [Cell site-years]\n"
     "RETURN IF ( n > 0, IF ( n < 100, -1, CALCULATE ( [Base rate], REMOVEFILTERS ( Sites[Risk band], Sites[Band order] ) ) ) )",
     TOO_FEW, None),
    ("Sites", "Risk Landscape", "Band table note",
     '"Crossed the line next year, " & [Test year label] & " · line: each industry\'s worst-20% DART rate this year · data bars 0 to 100% · too few sites: under 100 site-years"',
     None, None),
]
for sector in SECTORS:
    keep = f'KEEPFILTERS ( Sites[Sector] = "{sector}" )'
    MEASURES.append(("Sites", "Risk Landscape", f"Crossed {sector}", f"CALCULATE ( [Cell crossing rate], {keep} )", TOO_FEW, None))

MEASURES += [
    # ---- Model Trust (slicers: model tiles, test year tiles; picker tables are not related to Models) ----
    ("Models", "Model Trust", "Picked model", 'SELECTEDVALUE ( ModelPicker[Model], "Scorecard" )', None, None),
    ("Models", "Model Trust", "Picked test year", "SELECTEDVALUE ( TestYearPicker[Test year], 2023 )", "0", None),
    ("Models", "Model Trust", "Picked AUC",
     "VAR m = [Picked model]\nVAR y = [Picked test year]\n"
     "RETURN CALCULATE ( AVERAGE ( 'Models'[AUC] ), REMOVEFILTERS ( 'Models' ), 'Models'[Model] = m, 'Models'[Test year] = y )",
     "0.00", None),
    ("Models", "Model Trust", "Picked AUC base",
     "VAR m = [Picked model]\nVAR y = [Picked test year]\n"
     "VAR lo = CALCULATE ( AVERAGE ( 'Models'[AUC low] ), REMOVEFILTERS ( 'Models' ), 'Models'[Model] = m, 'Models'[Test year] = y )\n"
     "VAR hi = CALCULATE ( AVERAGE ( 'Models'[AUC high] ), REMOVEFILTERS ( 'Models' ), 'Models'[Model] = m, 'Models'[Test year] = y )\n"
     'RETURN m & ", " & y & " · 95% CI " & FORMAT ( lo, "0.000" ) & " to " & FORMAT ( hi, "0.000" )', None, None),
    ("Models", "Model Trust", "Picked Gini",
     "VAR m = [Picked model]\nVAR y = [Picked test year]\n"
     "RETURN CALCULATE ( AVERAGE ( 'Models'[Gini] ), REMOVEFILTERS ( 'Models' ), 'Models'[Model] = m, 'Models'[Test year] = y )",
     "0.00", None),
    ("Models", "Model Trust", "Picked test pairs",
     "VAR y = [Picked test year]\n"
     "RETURN FORMAT ( CALCULATE ( MAX ( 'Models'[Sites] ), REMOVEFILTERS ( 'Models' ), 'Models'[Test year] = y ), \"#,0\" ) & \" test pairs · \" & y",
     None, None),
    ("Models", "Model Trust", "Picked model and year", '[Picked model] & ", " & [Picked test year]', None, None),
    ("Models", "Model Trust", "ROC AUC label", '"AUC " & FORMAT ( [Picked AUC], "0.00" )', None, None),
    ("Models", "Model Trust", "Gini 2023", "CALCULATE ( AVERAGE ( 'Models'[Gini] ), 'Models'[Test year] = 2023 )", "0.000", None),
    ("Models", "Model Trust", "Gini 2024", "CALCULATE ( AVERAGE ( 'Models'[Gini] ), 'Models'[Test year] = 2024 )", "0.000", None),
    ("Models", "Model Trust", "Capture top 20% 2023", "CALCULATE ( AVERAGE ( 'Models'[Capture top 20%] ), 'Models'[Test year] = 2023 )", "0.0%", None),
    ("Models", "Model Trust", "Capture top 20% 2024", "CALCULATE ( AVERAGE ( 'Models'[Capture top 20%] ), 'Models'[Test year] = 2024 )", "0.0%", None),
    ("Models", "Model Trust", "Precision top 20% 2023", "CALCULATE ( AVERAGE ( 'Models'[Precision top 20%] ), 'Models'[Test year] = 2023 )", "0.0%", None),
    ("Models", "Model Trust", "Precision top 20% 2024", "CALCULATE ( AVERAGE ( 'Models'[Precision top 20%] ), 'Models'[Test year] = 2024 )", "0.0%", None),
    ("Models", "Model Trust", "Model row fill", 'IF ( SELECTEDVALUE ( \'Models\'[Model] ) = [Picked model], "#E3DECF", "#F7F5EC" )', None, None),
    ("ROC", "Model Trust", "ROC true positive rate",
     "VAR m = [Picked model]\nVAR y = [Picked test year]\nRETURN CALCULATE ( MAX ( ROC[True positive rate] ), ROC[Model] = m, ROC[Test year] = y )",
     "0%", None),
    ("ROC", "Model Trust", "Coin toss",
     "VAR m = [Picked model]\nVAR y = [Picked test year]\nRETURN CALCULATE ( MAX ( ROC[False positive rate] ), ROC[Model] = m, ROC[Test year] = y )",
     "0%", None),
    ("Calibration", "Model Trust", "Share that crossed",
     "VAR m = [Picked model]\nVAR y = [Picked test year]\n"
     "RETURN CALCULATE ( AVERAGE ( Calibration[Observed share] ), Calibration[Model] = m, Calibration[Test year] = y )", "0.0%", None),
    ("Calibration", "Model Trust", "Predicted",
     "VAR m = [Picked model]\nVAR y = [Picked test year]\n"
     "RETURN CALCULATE ( AVERAGE ( Calibration[Predicted share] ), Calibration[Model] = m, Calibration[Test year] = y )", "0.0%", None),
    ("Calibration", "Model Trust", "Calibration note",
     'IF ( [Picked model] = "Last year\'s rate", "Last year\'s rate is a rank, not a probability, so it has no calibration.", " " )', None, None),
    ("Robustness", "Model Trust", "Robustness AUC 2023", "SUM ( Robustness[AUC 2023] )", "0.000", None),
    ("Drivers", "Model Trust", "Driver AUC drop", "SUM ( Drivers[AUC drop] )", "0.000", None),

    # ---- Pricing Lab (slicers: claim-cost scenario tiles, score year tiles). Every figure is simulated ----
    ("PricingSummary", "Pricing Lab", "Selected scenario", 'SELECTEDVALUE ( ClaimCostScenarios[Scenario key], "central" )', None, None),
    ("PricingSummary", "Pricing Lab", "Selected score year", "SELECTEDVALUE ( ScoreYears[Score year], 2023 )", "0", None),
    ("PricingSummary", "Pricing Lab", "Pricing scenario label", 'FORMAT ( [Selected score year], "0" ) & " " & [Selected scenario]', None, None),
    ("PricingSummary", "Pricing Lab", "Priced sites",
     "VAR y = [Selected score year]\n"
     'RETURN CALCULATE ( SUM ( PricingBands[Sites] ), REMOVEFILTERS ( PricingBands ), PricingBands[Claim-cost scenario] = "central", PricingBands[Score year] = y )',
     "#,0", None),
    ("PricingSummary", "Pricing Lab", "Pricing base line", '[Pricing scenario label] & " · " & FORMAT ( [Priced sites], "#,0" ) & " sites"', None, None),
    ("PricingSummary", "Pricing Lab", "Pricing year base line",
     'FORMAT ( [Selected score year], "0" ) & " · " & FORMAT ( [Priced sites], "#,0" ) & " sites"', None, None),
    ("PricingSummary", "Pricing Lab", "Wrong band share A",
     "VAR s = [Selected scenario]\nVAR y = [Selected score year]\nRETURN CALCULATE ( AVERAGE ( PricingSummary[Misallocated share A] ), PricingSummary[Claim-cost scenario] = s, PricingSummary[Score year] = y )",
     "0.0%", None),
    ("PricingSummary", "Pricing Lab", "Wrong band share B",
     "VAR s = [Selected scenario]\nVAR y = [Selected score year]\nRETURN CALCULATE ( AVERAGE ( PricingSummary[Misallocated share B] ), PricingSummary[Claim-cost scenario] = s, PricingSummary[Score year] = y )",
     "0.0%", None),
    ("PricingSummary", "Pricing Lab", "Wrong band A to B",
     'FORMAT ( [Wrong band share A], "0.0%" ) & UNICHAR ( 8201 ) & "→" & UNICHAR ( 8201 ) & FORMAT ( [Wrong band share B], "0.0%" )', None, None),
    ("PricingSummary", "Pricing Lab", "Overall loss ratio A",
     "VAR s = [Selected scenario]\nVAR y = [Selected score year]\nRETURN CALCULATE ( AVERAGE ( PricingSummary[Overall ratio A] ), PricingSummary[Claim-cost scenario] = s, PricingSummary[Score year] = y )",
     "0.00", None),
    ("PricingSummary", "Pricing Lab", "Overall loss ratio B",
     "VAR s = [Selected scenario]\nVAR y = [Selected score year]\nRETURN CALCULATE ( AVERAGE ( PricingSummary[Overall ratio B] ), PricingSummary[Claim-cost scenario] = s, PricingSummary[Score year] = y )",
     "0.00", None),
    ("PricingSummary", "Pricing Lab", "Overall ratio A to B",
     'FORMAT ( [Overall loss ratio A], "0.00" ) & UNICHAR ( 8201 ) & "→" & UNICHAR ( 8201 ) & FORMAT ( [Overall loss ratio B], "0.00" )', None, None),
    ("PricingSummary", "Pricing Lab", "Scenario premium",
     "VAR y = [Selected score year]\n"
     'RETURN FORMAT ( CALCULATE ( SUM ( PricingSummary[Total premium] ), PricingSummary[Score year] = y ) / 1E9, "$#,0.00" ) & "bn"',
     None, None),
    ("PricingSummary", "Pricing Lab", "Scenario simulated loss",
     "VAR y = [Selected score year]\n"
     'RETURN FORMAT ( CALCULATE ( SUM ( PricingSummary[Simulated loss] ), PricingSummary[Score year] = y ) / 1E9, "$#,0.00" ) & "bn"',
     None, None),
    ("PricingSummary", "Pricing Lab", "Scenario loss ratio", "VAR y = [Selected score year]\nRETURN CALCULATE ( AVERAGE ( PricingSummary[Overall ratio A] ), PricingSummary[Score year] = y )", "0.00", None),
    ("PricingSummary", "Pricing Lab", "Scenario wrong band A to B",
     'VAR y = [Selected score year]\n'
     'RETURN FORMAT ( CALCULATE ( AVERAGE ( PricingSummary[Misallocated share A] ), PricingSummary[Score year] = y ), "0.0%" ) & " → "\n'
     '    & FORMAT ( CALCULATE ( AVERAGE ( PricingSummary[Misallocated share B] ), PricingSummary[Score year] = y ), "0.0%" )',
     None, None),
    ("PricingSummary", "Pricing Lab", "Scenario band spread A to B",
     'VAR y = [Selected score year]\n'
     'RETURN FORMAT ( CALCULATE ( AVERAGE ( PricingSummary[Band spread A] ), PricingSummary[Score year] = y ), "0.0" ) & "x → "\n'
     '    & FORMAT ( CALCULATE ( AVERAGE ( PricingSummary[Band spread B] ), PricingSummary[Score year] = y ), "0.0" ) & "x"',
     None, None),
    ("PricingSummary", "Pricing Lab", "Scenario row fill",
     'IF ( SELECTEDVALUE ( PricingSummary[Claim-cost scenario] ) = [Selected scenario], "#E3DECF", "#F7F5EC" )', None, None),
    ("PricingBands", "Pricing Lab", "Band loss ratio A",
     "VAR s = [Selected scenario]\nVAR y = [Selected score year]\nRETURN CALCULATE ( AVERAGE ( PricingBands[Loss ratio A] ), PricingBands[Claim-cost scenario] = s, PricingBands[Score year] = y )",
     "0.00", None),
    ("PricingBands", "Pricing Lab", "Band loss ratio B",
     "VAR s = [Selected scenario]\nVAR y = [Selected score year]\nRETURN CALCULATE ( AVERAGE ( PricingBands[Loss ratio B] ), PricingBands[Claim-cost scenario] = s, PricingBands[Score year] = y )",
     "0.00", None),
    ("PricingBands", "Pricing Lab", "Band loss ratio low", "MIN ( [Band loss ratio A], [Band loss ratio B] )", "0.00", None),
    ("PricingBands", "Pricing Lab", "Band loss ratio high", "MAX ( [Band loss ratio A], [Band loss ratio B] )", "0.00", None),
    ("PricingBands", "Pricing Lab", "Band premium change",
     "VAR s = [Selected scenario]\nVAR y = [Selected score year]\nRETURN CALCULATE ( AVERAGE ( PricingBands[Premium change] ), PricingBands[Claim-cost scenario] = s, PricingBands[Score year] = y )",
     "+0.0%;−0.0%;0.0%", None),
]


def tmdl():
    lines = ["createOrReplace", ""]
    for table in dict.fromkeys(m[0] for m in MEASURES):
        lines += [f"\tref table {table}", ""]
        for _, folder, name, expression, fmt, dynamic in (m for m in MEASURES if m[0] == table):
            quoted = "'" + name.replace("'", "''") + "'"
            if "\n" in expression:
                lines.append(f"\t\tmeasure {quoted} = ```")
                lines += ["\t\t\t\t" + line for line in expression.split("\n")]
                lines.append("\t\t\t\t```")
            else:
                lines.append(f"\t\tmeasure {quoted} = {expression}")
            if fmt:
                lines.append(f"\t\t\tformatString: {fmt}")
            lines.append(f"\t\t\tdisplayFolder: {folder}")
            if dynamic:  # expression properties come after plain ones
                lines.append(f"\t\t\tformatStringDefinition = {dynamic}")
            lines.append("")
    return "\n".join(lines)


def dax_listing():
    """The same measures as a readable DAX listing, grouped by page, for review."""
    lines = ["// Workplace Risk Intelligence: every measure in the semantic model, grouped by the page that uses it.",
             "// Generated by powerbi/tools/measures.py from the same list as powerbi/model/measures.tmdl; edit the script, not this file.",
             "// Pricing measures are simulated: never label them as actual premiums, claims or loss ratios.",
             ""]
    for folder in dict.fromkeys(m[1] for m in MEASURES):
        lines += [f"// ---- {folder} ----", ""]
        for table, _, name, expression, fmt, _ in (m for m in MEASURES if m[1] == folder):
            lines.append(f"// format: {fmt}" if fmt else "// format: text or general")
            body = expression.split("\n")
            lines.append(f"{table}[{name}] =" + ("" if len(body) > 1 else f" {body[0]}"))
            if len(body) > 1:
                lines += ["    " + line for line in body]
            lines.append("")
    return "\n".join(lines)


def main():
    OUT.parent.mkdir(exist_ok=True)
    OUT.write_text(tmdl())
    LISTING.write_text(dax_listing())
    print(f"{len(MEASURES)} measures -> {OUT} and {LISTING}")


if __name__ == "__main__":
    main()
