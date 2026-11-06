"""
Builds the Workplace Risk Intelligence report as a Power BI enhanced report definition (PBIR, the format the Power BI
service stores the report in) from the approved design: page backgrounds from powerbi/backgrounds/, the theme from
powerbi/theme/wri-theme.json, and the native visuals defined below (positions follow the mockups in powerbi/mockups/).

Writes powerbi/report/ (definition/ and StaticResources/RegisteredResources/) and powerbi/build/report-bundle.json,
the same parts base64-encoded for the Fabric "update report definition" call. The connection to the semantic model
(definition.pbir) and the service's base theme are kept from the published report when the bundle is applied.

Usage: .venv/bin/python powerbi/tools/build_report.py
"""
import base64
import json
import shutil
from pathlib import Path

PBI = Path(__file__).resolve().parents[1]
OUT = PBI / "report"
BUNDLE = PBI / "build" / "report-bundle.json"

SCHEMA = "https://developer.microsoft.com/json-schemas/fabric/item/report/definition"
BASE_THEME = "Fluent2-CY26SU11"
VERSIONS = {"visual": "2.15.0", "report": "3.4.0", "page": "2.3.1"}
THEME_FILE = "wri-theme.json"

# design system colours (docs/design-system.md)
NEST, CARD, CARD_LINE, AXIS = "#EFECDF", "#F7F5EC", "#E3DECF", "#CFCBBD"
ONYX, INK, MUTED, SHELL = "#000000", "#303A39", "#66655F", "#FFFFFF"
EMBER, COBALT, SCREEN_INK, WARM_GREY = "#E24337", "#1936E8", "#274A48", "#B3AFA1"
BANDS = ["#C9D6BD", "#D1A76A", "#C98369", "#A96247", "#944126"]
BAND_LABELS = ["Band 1, lowest fifth", "Band 2", "Band 3", "Band 4", "Band 5, highest fifth"]

SEGOE = "'Segoe UI', wf_segoe-ui_normal, helvetica, arial, sans-serif"
SEGOE_SEMIBOLD = "'Segoe UI Semibold', wf_segoe-ui_semibold, helvetica, arial, sans-serif"

PAGES = [
    ("executive", "Executive Intelligence", "page1-executive-intelligence"),
    ("landscape", "Risk Landscape", "page2-risk-landscape"),
    ("trust", "Model Trust", "page3-model-trust"),
    ("pricing", "Pricing Lab", "page4-pricing-lab"),
]
NAV = [(186, 705), (145, 891), (120, 1036), (115, 1156)]


# ---------- PBIR expression helpers ----------

def value(v):
    if isinstance(v, bool):
        return "true" if v else "false"
    if isinstance(v, int):
        return f"{v}L"
    if isinstance(v, float):
        return (f"{int(v)}" if v.is_integer() else repr(v)) + "D"
    return "'" + str(v).replace("'", "''") + "'"


def lit(v):
    """A literal property value; whole-number formatting values are doubles, so pass them as floats."""
    return {"expr": {"Literal": {"Value": value(v)}}}


def colour(hex_colour):
    return {"solid": {"color": lit(hex_colour)}}


def obj(selector=None, **properties):
    o = {"properties": properties}
    if selector is not None:
        o["selector"] = selector
    return o


def default(**properties):
    return obj({"id": "default"}, **properties)


def measure(table, name):
    return {"Measure": {"Expression": {"SourceRef": {"Entity": table}}, "Property": name}}


def column(table, name):
    return {"Column": {"Expression": {"SourceRef": {"Entity": table}}, "Property": name}}


def ref(field):
    kind = next(iter(field))
    return field[kind]["Expression"]["SourceRef"]["Entity"], field[kind]["Property"]


def projection(field, display=None, fmt=None, active=False):
    table, name = ref(field)
    p = {"field": field, "queryRef": f"{table}.{name}", "nativeQueryRef": name}
    if display is not None:
        p["displayName"] = display
    if fmt:
        p["format"] = fmt
    if active:
        p["active"] = True
    return p


def query(roles, sort=None):
    q = {"queryState": {role: {"projections": items} for role, items in roles.items()}}
    q["sortDefinition"] = {"sort": [{"field": f, "direction": d} for f, d in sort], "isDefaultSort": False} if sort \
        else {"isDefaultSort": True}
    return q


def when(field, v):
    """Selector for one category value, used to colour a single bar."""
    return {"data": [{"scopeId": {"Comparison": {"ComparisonKind": 0, "Left": field,
                                                 "Right": {"Literal": {"Value": value(v)}}}}}]}


def series(field):
    table, name = ref(field)
    return {"metadata": f"{table}.{name}"}


def keep(name, field, values):
    """Visual-level filter that keeps the listed values of a column."""
    table, prop = ref(field)
    alias = table[0].lower()
    return {"name": name, "field": field, "type": "Categorical",
            "filter": {"Version": 2, "From": [{"Name": alias, "Entity": table, "Type": 0}],
                       "Where": [{"Condition": {"In": {
                           "Expressions": [{"Column": {"Expression": {"SourceRef": {"Source": alias}}, "Property": prop}}],
                           "Values": [[{"Literal": {"Value": value(v)}}] for v in values]}}}]},
            "isHiddenInViewMode": True}


def frame(**extra):
    """Container formatting shared by every visual: no title, background, border or shadow; titles are baked."""
    o = {"title": [obj(show=lit(False))], "background": [obj(show=lit(False))], "border": [obj(show=lit(False))],
         "dropShadow": [obj(show=lit(False))], "padding": [obj(top=lit(0.0), bottom=lit(0.0), left=lit(0.0), right=lit(0.0))]}
    o.update(extra)
    return o


# ---------- visual builders ----------

def card(field, size, ink=ONYX, bold=True, align="left", fmt=None, wrap=False):
    value_props = dict(fontSize=lit(float(size)), fontColor=colour(ink), horizontalAlignment=lit(align),
                       fontFamily=lit(SEGOE_SEMIBOLD if bold else SEGOE))
    if wrap:
        value_props["wordWrap"] = lit(True)
    return {"visualType": "cardVisual",
            "query": query({"Data": [projection(field, fmt=fmt)]}),
            "objects": {
                "value": [default(**value_props)],
                "label": [default(show=lit(False))],
                "outline": [default(show=lit(False))],
                "divider": [default(show=lit(False))],
                "fillCustom": [obj(show=lit(False))],
            },
            "visualContainerObjects": frame(visualHeader=[obj(show=lit(False))]),
            "drillFilterOtherVisuals": True}


def button(text, target=None, active=False, ink=INK, size=10.5, align="center", hover_fill=True):
    text_default = default(text=lit(text), fontColor=colour(ONYX if active else ink),
                           fontSize=lit(size), fontFamily=lit(SEGOE), horizontalAlignment=lit(align),
                           verticalAlignment=lit("middle"))
    fill = [obj(show=lit(True)), default(fillColor=colour(EMBER if active else CARD_LINE), transparency=lit(0.0 if active else 100.0))]
    if hover_fill and not active:
        fill.append(obj({"id": "hover"}, fillColor=colour(CARD_LINE), transparency=lit(0.0)))
    v = {"visualType": "actionButton",
         "objects": {"icon": [default(shapeType=lit("blank"))],
                     "outline": [default(show=lit(False))],
                     "text": [obj(show=lit(True)), text_default, obj({"id": "hover"}, fontColor=colour(ONYX if hover_fill else ink))],
                     "fill": fill},
         "visualContainerObjects": frame(visualHeader=[obj(show=lit(False))]),
         "drillFilterOtherVisuals": True}
    if target:
        v["visualContainerObjects"]["visualLink"] = [obj(show=lit(True), type=lit("PageNavigation"),
                                                         navigationSection=lit(target))]
    return v


def link(text, target, align="left"):
    return button(text, target, ink=COBALT, align=align, hover_fill=False)


def labels(size=15.0, ink=ONYX, bold=True, position="OutsideEnd", decimals=1):
    return [obj(show=lit(True), color=colour(ink), fontSize=lit(size), fontFamily=lit(SEGOE_SEMIBOLD if bold else SEGOE),
                labelPosition=lit(position), labelDisplayUnits=lit(1.0), labelPrecision=lit(decimals))]


def label_text(field):
    """Data labels that show a text measure instead of the bar's value ("about 8 in 10")."""
    return obj({"data": [{"dataViewWildcard": {"matchingOption": 1}}], "highlightMatching": 1},
               dynamicLabelValue={"expr": field})


def constant_line(field_or_value, ink, style="solid", width=None, label=None):
    v = {"expr": field_or_value} if isinstance(field_or_value, dict) else lit(float(field_or_value))
    props = dict(show=lit(True), value=v, lineColor=colour(ink), style=lit(style), position=lit("front"),
                 transparency=lit(0.0), dataLabelShow=lit(label is not None))
    if width:
        props["width"] = lit(float(width))
    if label:
        props.update(displayName=lit(label), dataLabelColor=colour(INK), dataLabelText=lit("ValueAndName"),
                     dataLabelHorizontalPosition=lit("left"), dataLabelVerticalPosition=lit("above"),
                     dataLabelDecimalPoints=lit(1.0), dataLabelDisplayUnits=lit(1.0))
    return [obj({"id": "1"}, **props)]


def axes(category=False, value_axis=False, start=None, end=None, inner=None, cat_size=10.5, cat_ink=ONYX):
    cat = dict(show=lit(category), fontSize=lit(cat_size), fontFamily=lit(SEGOE), labelColor=colour(cat_ink),
               showAxisTitle=lit(False))
    if inner is not None:
        cat["innerPadding"] = lit(int(inner))
    val = dict(show=lit(value_axis), showAxisTitle=lit(False), gridlineShow=lit(False))
    if start is not None:
        val["start"] = lit(float(start))
    if end is not None:
        val["end"] = lit(float(end))
    return {"categoryAxis": [obj(**cat)], "valueAxis": [obj(**val)], "legend": [obj(show=lit(False))]}


def chart(kind, roles, objects, sort=None):
    return {"visualType": kind, "query": query(roles, sort), "objects": objects,
            "visualContainerObjects": frame(), "drillFilterOtherVisuals": True}


def table(columns, objects, sort=None):
    return {"visualType": "tableEx", "query": query({"Values": columns}, sort), "objects": objects,
            "visualContainerObjects": frame(), "drillFilterOtherVisuals": True}


def table_style(size=10.5, header_wrap=False, padding=4.0):
    return {"columnHeaders": [obj(fontColor=colour(MUTED), fontSize=lit(size), fontFamily=lit(SEGOE), outline=lit("None"),
                                  backColor=colour(CARD), alignment=lit("Right"), wordWrap=lit(header_wrap))],
            "values": [obj(fontColorPrimary=colour(ONYX), fontColorSecondary=colour(ONYX), backColorPrimary=colour(CARD),
                           backColorSecondary=colour(CARD), fontSize=lit(size), fontFamily=lit(SEGOE), outline=lit("None"),
                           wordWrap=lit(False))],
            "grid": [obj(gridHorizontal=lit(False), gridVertical=lit(False), rowPadding=lit(padding), outlineWeight=lit(0.0))],
            "total": [obj(totals=lit(False))]}


def widths(*pairs):
    return [obj({"metadata": m}, value=lit(float(w))) for m, w in pairs]


def aligned(*pairs):
    return [obj({"metadata": m}, alignment=lit(a)) for m, a in pairs]


def by_measure(metadata, prop, field):
    """Conditional formatting by field value: a measure that returns a hex colour."""
    return obj({"data": [{"dataViewWildcard": {"matchingOption": 1}}], "metadata": metadata},
               **{prop: {"solid": {"color": {"expr": field}}}})


def by_column(metadata, prop, field):
    """Conditional formatting by field value from a text column (first value)."""
    return obj({"data": [{"dataViewWildcard": {"matchingOption": 1}}], "metadata": metadata},
               **{prop: {"solid": {"color": {"expr": {"Aggregation": {"Expression": field, "Function": 3}}}}}})


def selection(field, values):
    """The saved selection of a slicer."""
    table_name, prop = ref(field)
    alias = table_name[0].lower()
    return {"filter": {"Version": 2, "From": [{"Name": alias, "Entity": table_name, "Type": 0}],
                       "Where": [{"Condition": {"In": {
                           "Expressions": [{"Column": {"Expression": {"SourceRef": {"Source": alias}}, "Property": prop}}],
                           "Values": [[{"Literal": {"Value": value(v)}}] for v in values]}}}]}}


def slicer(field, header, tiles=True, default_value=None):
    general = dict(outlineColor=colour(AXIS), outlineWeight=lit(1.0))
    if tiles:
        general["orientation"] = lit(1.0)
    if default_value is not None:
        general["filter"] = selection(field, [default_value])
    return {"visualType": "slicer",
            "query": query({"Values": [projection(field, display=header, active=True)]}),
            "objects": {"data": [obj(mode=lit("Basic" if tiles else "Dropdown"))],
                        # single pick everywhere: comparing two multi-sector views could expose small groups
                        "selection": [obj(singleSelect=lit(True), selectAllCheckboxEnabled=lit(False), strictSingleSelect=lit(False))],
                        "header": [obj(show=lit(True), fontColor=colour(MUTED), textSize=lit(10.5), fontFamily=lit(SEGOE), outline=lit("None"))],
                        "items": [obj(fontColor=colour(INK), background=colour(CARD), textSize=lit(10.5), fontFamily=lit(SEGOE),
                                      outline=lit("Frame"), outlineColor=colour(AXIS))],
                        "general": [obj(**general)]},
            "visualContainerObjects": frame(visualHeader=[obj(show=lit(False))]),
            "drillFilterOtherVisuals": True}


def reset_button():
    v = button("↺ Reset filters", ink=COBALT, align="right", hover_fill=False)
    v["visualContainerObjects"]["visualLink"] = [obj(show=lit(True), type=lit("ClearAllSlicers"))]
    return v


def data_bars():
    """Fixed 0 to 100% data bars in Screen ink; "too few sites" cells are negative and draw nothing."""
    return {"minValue": lit(0.0), "maxValue": lit(1.0), "positiveColor": colour(SCREEN_INK), "negativeColor": colour(CARD),
            "axisColor": colour(CARD), "reverseDirection": lit(False), "hideText": lit(False), "totalMatchingOption": lit(1)}


def connectors(anchor, low, high):
    """Error bars from the lower to the higher of two series, drawn on one of them: the A to B connector."""
    return [obj(series(anchor), enabled=lit(True)),
            obj({"data": [{"dataViewWildcard": {"matchingOption": 0}}], "metadata": series(anchor)["metadata"], "highlightMatching": 1},
                errorRange={"kind": "ErrorRange", "explicit": {"isRelative": lit(False), "lowerBound": {"expr": low},
                                                               "upperBound": {"expr": high}}})]


def series_style(field, ink, width=2.0, dashed=False, marker=False, shade=False):
    return obj(series(field), strokeWidth=lit(float(width)), lineStyle=lit("dashed" if dashed else "solid"),
               showMarker=lit(marker), markerShape=lit("circle"), markerSize=lit(5.0), shadeArea=lit(shade))


def top_n(name, field, by, n):
    table_name, prop = ref(field)
    a = table_name[0].lower()
    by_table, by_prop = ref(by)
    return {"name": name, "field": field, "type": "TopN",
            "filter": {"Version": 2, "From": [
                {"Name": "subquery", "Expression": {"Subquery": {"Query": {
                    "Version": 2, "From": [{"Name": a, "Entity": table_name, "Type": 0}],
                    "Select": [{"Column": {"Expression": {"SourceRef": {"Source": a}}, "Property": prop}, "Name": "field"}],
                    "OrderBy": [{"Direction": 2, "Expression": {"Measure": {"Expression": {"SourceRef": {"Source": a}}, "Property": by_prop}}}],
                    "Top": n}}}, "Type": 2},
                {"Name": a, "Entity": table_name, "Type": 0}],
                "Where": [{"Condition": {"In": {"Expressions": [{"Column": {"Expression": {"SourceRef": {"Source": a}}, "Property": prop}}],
                                                "Table": {"SourceRef": {"Source": "subquery"}}}}}]},
            "isHiddenInViewMode": True}


# ---------- pages ----------

SITES = "Sites"


def nav(page):
    out = []
    for (name, title, _), (w, x) in zip(PAGES, NAV):
        out.append((f"nav_{name}", (x, 37, w, 38), button(title, None if name == page else name, active=name == page)))
    return out


def executive():
    v = nav("executive")
    band = column("Bands", "Band label long")
    v += [
        # signature stamp: share of next year's line-crossers already in band 5
        ("kpi_capture_value", (94, 506, 320, 112), card(measure(SITES, "Top band capture"), 72, ink=SHELL, fmt="0.0%")),
        ("kpi_capture_count", (424, 579, 262, 26), card(measure(SITES, "Capture base line"), 10.5, ink=MUTED, bold=False)),
        ("chart_capture_vs_random", (64, 634, 336, 34), chart(
            "barChart", {"Category": [projection(column("TestYears", "Tile label"), display="Test years", active=True)],
                         "Y": [projection(measure(SITES, "Top band capture"), display="Line-crossers in band 5"),
                               projection(measure(SITES, "Capture remainder"), display="In bands 1 to 4")]},
            {**axes(start=0, end=1, inner=0),
             "dataPoint": [obj(series(measure(SITES, "Top band capture")), fill=colour(BANDS[4])),
                           obj(series(measure(SITES, "Capture remainder")), fill=colour(CARD_LINE))],
             "labels": [obj(show=lit(False))],
             "general": [obj(responsive=lit(False))],
             "y1AxisReferenceLine": constant_line(measure(SITES, "Random fifth"), INK)})),
        # underwriting ledger
        ("kpi_hit_rate_value", (424, 751, 220, 46), card(measure(SITES, "Top band hit rate"), 22.5, fmt="0.0%")),
        ("kpi_hit_rate_count", (424, 814, 262, 26), card(measure(SITES, "Hit rate base line"), 10.5, ink=MUTED, bold=False)),
        ("kpi_wrong_band_value", (424, 855, 236, 46), card(measure("PricingSummary", "Wrong band A to B 2023 central"), 22.5)),
        ("link_method_caveats", (58, 993, 280, 26), link("Method and caveats: Model Trust →", "trust")),
        # crossed the line next year, by risk band (2023 columns, 2024 row beneath)
        ("chart_crossing_by_band", (801, 252, 1024, 304), chart(
            "clusteredColumnChart",
            {"Category": [projection(band, display="Risk band", active=True)],
             "Y": [projection(measure(SITES, "Crossing rate 2023"), display="Crossed the line next year, 2023", fmt="0.0%")]},
            {**axes(category=True, start=0, inner=41),
             "dataPoint": [obj(when(band, label), fill=colour(c)) for label, c in zip(BAND_LABELS, BANDS)],
             "labels": labels(),
             "y1AxisReferenceLine": constant_line(measure(SITES, "All sites rate"), MUTED, style="dashed",
                                                  label="All sites, 2023 + 2024")},
            sort=[(band, "Ascending")])),
        ("link_risk_landscape", (1064, 698, 176, 28), link("Risk Landscape →", "landscape", align="right")),
        ("link_model_trust", (1672, 698, 160, 28), link("Model Trust →", "trust", align="right")),
        # every sector has band 5 sites
        ("table_sector_dart", (736, 744, 278, 244), table(
            [projection(column(SITES, "Sector"), display=" "),
             projection(measure(SITES, "Average site DART rate"), display="Avg DART rate", fmt="0.00")],
            {"columnHeaders": [obj(fontColor=colour(MUTED), fontSize=lit(10.0), fontFamily=lit(SEGOE), outline=lit("None"),
                                   alignment=lit("Right"), wordWrap=lit(False))],
             "values": [obj(fontColorPrimary=colour(ONYX), fontColorSecondary=colour(ONYX), fontSize=lit(10.0),
                            fontFamily=lit(SEGOE), outline=lit("None"), wordWrap=lit(False))],
             "grid": [obj(gridHorizontal=lit(False), gridVertical=lit(False), rowPadding=lit(4.0), outlineWeight=lit(0.0))],
             "total": [obj(totals=lit(False))],
             "columnWidth": [obj({"metadata": "Sites.Sector"}, value=lit(176.0)),
                             obj({"metadata": "Sites.Average site DART rate"}, value=lit(98.0))],
             "columnFormatting": [obj({"metadata": "Sites.Average site DART rate"}, alignment=lit("Right"),
                                      fontColor=colour(INK)),
                                  obj({"metadata": "Sites.Sector"}, alignment=lit("Left"))]},
            sort=[(measure(SITES, "Average site DART rate"), "Descending")])),
        ("chart_sector_band5", (1016, 772, 218, 196), chart(
            "clusteredBarChart",
            {"Category": [projection(column(SITES, "Sector"), active=True)],
             "Y": [projection(measure(SITES, "Share of sites in top band"), display="Sites in band 5, 2023 + 2024", fmt="0.0%")],
             "Tooltips": [projection(measure(SITES, "Average site DART rate"), display="Avg site DART rate", fmt="0.00")]},
            {**axes(start=0, end=0.3, inner=57),
             "dataPoint": [obj(fill=colour(BANDS[4]))],
             "labels": labels(size=10.5, ink=SHELL, bold=False, position="InsideBase"),
             "y1AxisReferenceLine": constant_line(measure(SITES, "Random fifth"), INK)},
            sort=[(measure(SITES, "Average site DART rate"), "Descending")])),
        # ranking accuracy on unseen years
        ("chart_auc_2023", (1472, 786, 240, 168), chart(
            "clusteredBarChart",
            {"Category": [projection(column("Models", "Model"), active=True)],
             "Y": [projection(measure("Models", "AUC 2023"), display="AUC, 2023 test", fmt="0.00")]},
            {**axes(start=0.5, end=1, inner=71),
             "dataPoint": [obj(fill=colour(WARM_GREY)), obj(when(column("Models", "Model"), "Scorecard"), fill=colour(SCREEN_INK))],
             "labels": labels(size=10.5, ink=MUTED, bold=False, decimals=2) + [label_text(measure("Models", "AUC 2023 words"))]},
            sort=[(column("Models", "Model"), "Descending")])),
    ]
    for k, (label, c) in enumerate(zip(BAND_LABELS, BANDS)):
        x = round(801 + 204.8 * k, 1)
        vis = card(measure(SITES, "Crossing rate 2024"), 10.5, ink=INK, bold=False, align="center", fmt="0.0%")
        v.append((f"card_crossing_2024_b{k + 1}", (x, 574, 204.8, 28), vis, [keep("band", column("Bands", "Band order"), [k + 1])]))
    for r, model in enumerate(["Scorecard", "Last year's rate", "Rating class only"]):
        ink = ONYX if model == "Scorecard" else INK
        for c, year in enumerate([2023, 2024]):
            vis = card(measure("Models", f"AUC {year}"), 10.5, ink=ink, bold=False, align="right", fmt="0.00")
            v.append((f"card_auc_{year}_m{r + 1}", (1696 + 56 * c, 802 + 56 * r, 72, 26), vis,
                      [keep("model", column("Models", "Model"), [model])]))
    return v, {"chart_auc_2023": [keep("models", column("Models", "Model"), ["Scorecard", "Last year's rate", "Rating class only"])],
               "chart_capture_vs_random": [keep("pooled", column("TestYears", "Tile label"), ["2023 + 2024"])]}


def rail(page, kpis, slicers, link_text, link_target):
    """The left rail shared by the three analysis pages: two KPI figures with base lines, the filters and the caveat link."""
    (v1, b1, w1), (v2, b2, w2) = kpis
    out = [("kpi_1_value", (64, 371, w1, 46), card(v1, 22.5)),
           ("kpi_1_base", b1[1], card(b1[0], 10.5, ink=MUTED, bold=False)),
           ("kpi_2_value", (424, 371, w2, 46), card(v2, 22.5)),
           ("kpi_2_base", b2[1], card(b2[0], 10.5, ink=MUTED, bold=False)),
           ("btn_reset", (500, 606, 144, 30), reset_button()),
           ("link_caveats", (58, 993, 320, 26), link(link_text, link_target))]
    for name, box, visual in slicers:
        out.append((name, box, visual))
    return nav(page) + out


def landscape():
    sector, size = column(SITES, "Sector"), column(SITES, "Size band label")
    v = rail("landscape",
             [(measure(SITES, "Band 5 crossing range"), (measure(SITES, "Band 5 base line"), (64, 432, 340, 26)), 340),
              (measure(SITES, "Portfolio crossing rate"), (measure(SITES, "Portfolio base line"), (424, 432, 240, 26)), 216)],
             [("slicer_test_year", (64, 646, 576, 84), slicer(column("TestYears", "Tile label"), "Test year", default_value="2023 + 2024")),
              ("slicer_sector", (64, 734, 272, 84), slicer(sector, "Sector", tiles=False)),
              ("slicer_size", (368, 734, 272, 84), slicer(size, "Size band", tiles=False))],
             "Method and caveats: Model Trust →", "trust")
    v.append(("link_back", (58, 140, 220, 28), link("← Executive Intelligence", "executive")))
    # band 5 share by state: a matrix laid out as the tile grid; states under 500 site-years leave the baked ghost tile
    tile = measure(SITES, "Map tile label")
    v += [
        ("map_title", (732, 170, 300, 40), card(measure(SITES, "Map title"), 15)),
        # the hidden row and column headers take 55 px on the left and 60 px on top, so the first tile lands on the
        # baked grid at x 737, y 257; columns are 44 px including the 4 px grid line
        ("map_tiles", (682, 197, 545, 418), {
            "visualType": "pivotTable",
            "query": query({"Rows": [projection(column("StateGrid", "Grid row"), display=" ", active=True)],
                            "Columns": [projection(column("StateGrid", "Grid column"), display=" ", active=True)],
                            "Values": [projection(tile, display=" ")]}),
            "objects": {
                "columnHeaders": [obj(fontColor=colour(CARD + "00"), backColor=colour(CARD + "00"), fontSize=lit(8.0), outline=lit("None"))],
                "rowHeaders": [obj(fontColor=colour(CARD + "00"), backColor=colour(CARD + "00"), fontSize=lit(8.0), outline=lit("None"))],
                "values": [obj(fontColorPrimary=colour(ONYX), fontSize=lit(10.5), fontFamily=lit(SEGOE), outline=lit("None"),
                               backColorPrimary=colour(CARD + "00"), backColorSecondary=colour(CARD + "00")),
                           by_measure("Sites.Map tile label", "backColor", measure(SITES, "Map tile colour"))],
                "grid": [obj(gridVertical=lit(True), gridVerticalColor=colour(CARD + "00"), gridVerticalWeight=lit(4.0),
                             gridHorizontal=lit(True), gridHorizontalColor=colour(CARD + "00"), gridHorizontalWeight=lit(4.0),
                             rowPadding=lit(10.0), outlineWeight=lit(0.0))],
                "subTotals": [obj(rowSubtotals=lit(False), columnSubtotals=lit(False))],
                "columnWidth": widths(("Sites.Map tile label", 44)),
                "columnFormatting": aligned(("Sites.Map tile label", "Center"))},
            # matrix cells cannot use a report-page tooltip here and the default one shows grid numbers, so the tiles carry no
            # tooltip: map_hover below supplies it, and both map layers filter nothing
            "visualContainerObjects": frame(visualTooltip=[obj(show=lit(False))], visualHeader=[obj(show=lit(False))]),
            "drillFilterOtherVisuals": True}),
        ("map_legend_title", (792, 250, 280, 26), card(measure(SITES, "Map legend title"), 10.5, ink=MUTED, bold=False)),
        # tile centres sit on whole grid units, so the axes run half a unit past the outer tiles
        ("map_hover", (735, 255, 484, 352), {
            "visualType": "scatterChart",
            # the grid coordinates carry a blank format and blank names, so the tooltip reads as state, share and base
            "query": query({"Category": [projection(column("StateGrid", "State name"), display="State", active=True)],
                            "X": [projection(measure(SITES, "Map hover x"), display=" ")],
                            "Y": [projection(measure(SITES, "Map hover y"), display="  ")],
                            "Tooltips": [projection(measure(SITES, "Map share label"), display="Share"),
                                         projection(measure(SITES, "State site-years"), display="Base")]}),
            "objects": {"categoryAxis": [obj(show=lit(False), start=lit(-0.5), end=lit(10.5))],
                        "valueAxis": [obj(show=lit(False), start=lit(-0.5), end=lit(7.5), gridlineShow=lit(False))],
                        "dataPoint": [obj(fill=colour(CARD + "00"))], "categoryLabels": [obj(show=lit(False))],
                        "legend": [obj(show=lit(False))], "general": [obj(responsive=lit(False))],
                        "bubbles": [obj(bubbleSize=lit(40))]},
            "visualContainerObjects": frame(visualTooltip=[obj(show=lit(True), type=lit("Default"), showTooltipFieldsOnly=lit(False),
                                                               showChartSpecificTooltips=lit(False))],
                                            visualHeader=[obj(show=lit(False))]),
            "drillFilterOtherVisuals": True}),
        # portfolio by sector and size
        ("table_sectors", (1328, 220, 346, 252), table(
            [projection(sector, display=" "), projection(measure(SITES, "Portfolio site-years"), display="Site-years"),
             projection(measure(SITES, "Portfolio DART rate"), display="Avg site DART rate")],
            {**table_style(size=10.0, header_wrap=True), "columnWidth": widths(("Sites.Sector", 180), ("Sites.Portfolio site-years", 80),
                                                                                ("Sites.Portfolio DART rate", 84)),
             "columnFormatting": aligned(("Sites.Sector", "Left"), ("Sites.Portfolio site-years", "Right"),
                                         ("Sites.Portfolio DART rate", "Right"))})),
        ("chart_sectors", (1692, 271, 133, 196), chart(
            "clusteredBarChart", {"Category": [projection(sector, active=True)],
                                  "Y": [projection(measure(SITES, "Band 5 share"), display="Site-years in band 5")]},
            {**axes(start=0, end=0.37, inner=57), "dataPoint": [obj(fill=colour(BANDS[4]))],
             "labels": labels(size=10.5, ink=SHELL, bold=False, position="InsideBase"),
             "y1AxisReferenceLine": constant_line(measure(SITES, "Random fifth"), INK)},
            sort=[(sector, "Ascending")])),
        ("chart_sizes", (1692, 491, 133, 56), chart(
            "clusteredBarChart", {"Category": [projection(size, display="Size band", active=True)],
                                  "Y": [projection(measure(SITES, "Band 5 share"), display="Site-years in band 5")]},
            {**axes(start=0, end=0.37, inner=20), "dataPoint": [obj(fill=colour(BANDS[4]))], "general": [obj(responsive=lit(False))],
             "labels": labels(size=10.5, ink=ONYX, bold=False, position="OutsideEnd"),
             "y1AxisReferenceLine": constant_line(measure(SITES, "Random fifth"), INK)},
            sort=[(size, "Ascending")])),
        ("note_sectors", (1328, 582, 500, 26), card(measure(SITES, "Portfolio note"), 10.5, ink=MUTED, bold=False)),
        # bands split risk inside every sector
        ("table_bands", (736, 734, 1090, 226), table(
            [projection(column("Bands", "Band label"), display="Risk band")] +
            [projection(measure(SITES, f"Crossed {s}"), display=s) for s in SECTOR_NAMES],
            {**table_style(header_wrap=True),
             "total": [obj(totals=lit(True), fontColor=colour(ONYX), backColor=colour(CARD), fontFamily=lit(SEGOE_SEMIBOLD),
                           fontSize=lit(10.5), outline=lit("TopOnly"), label=lit("All bands"))],
             "values": table_style()["values"] + [by_column("Bands.Band label", "backColor", column("Bands", "Band colour")),
                                                  by_column("Bands.Band label", "fontColor", column("Bands", "Band text colour"))],
             "columnWidth": widths(("Bands.Band label", 136), *[(f"Sites.Crossed {s}", 136) for s in SECTOR_NAMES]),
             "columnFormatting": aligned(("Bands.Band label", "Left")) +
                                 [obj({"metadata": f"Sites.Crossed {s}"}, alignment=lit("Right"), dataBars=data_bars())
                                  for s in SECTOR_NAMES]})),
        ("note_bands", (732, 962, 1100, 26), card(measure(SITES, "Band table note"), 10.5, ink=MUTED, bold=False)),
    ]
    for r, label in enumerate(["20 to 249 employees", "250+ employees"]):
        v.append((f"card_size_years_{r + 1}", (1500, 491 + 28 * r, 86, 28),
                  card(measure(SITES, "Site-years label"), 10.5, ink=INK, bold=False, align="right"),
                  [keep("size", size, [label])]))
    return v, {}


def trust():
    models = column("Models", "Model")
    v = rail("trust",
             [(measure("Models", "Picked AUC"), (measure("Models", "Picked AUC base"), (64, 480, 340, 26)), 200),
              (measure("Models", "Picked Gini"), (measure("Models", "Picked test pairs"), (424, 480, 240, 26)), 200)],
             [("slicer_model", (64, 646, 576, 84), slicer(column("ModelPicker", "Model"), "Model", default_value="Scorecard")),
              ("slicer_test_year", (64, 734, 576, 84), slicer(column("TestYearPicker", "Tile label"), "Test year",
                                                              default_value="2023, outcome 2024"))],
             "Scores in pricing: Pricing Lab →", "pricing")
    # the rail KPIs sit lower on this page
    v = [(n, (b[0], b[1] + 48, b[2], b[3]) if n in ("kpi_1_value", "kpi_2_value") else b, *rest) for n, b, *rest in v]
    metrics = [("AUC 2023", "2023", 56), ("AUC 2024", "2024", 56), ("Gini 2023", "2023", 56), ("Gini 2024", "2024", 56),
               ("Capture top 20% 2023", "2023", 70), ("Capture top 20% 2024", "2024", 70),
               ("Precision top 20% 2023", "2023", 70), ("Precision top 20% 2024", "2024", 70)]
    fill = measure("Models", "Model row fill")
    v += [
        ("table_models", (736, 300, 646, 150), table(
            [projection(models, display=" ")] + [projection(measure("Models", m), display=d) for m, d, _ in metrics],
            {**table_style(),
             "values": table_style()["values"] + [by_measure(f"Models.{m}", "backColor", fill) for m, _, _ in metrics] +
                       [by_measure("Models.Model", "backColor", fill)],
             "columnWidth": widths(("Models.Model", 140), *[(f"Models.{m}", w) for m, _, w in metrics]),
             "columnFormatting": aligned(("Models.Model", "Left"), *[(f"Models.{m}", "Right") for m, _, _ in metrics])})),
        ("chart_robustness", (1684, 216, 140, 364), chart(
            "clusteredBarChart",
            {"Category": [projection(column("Robustness", "Label"), display="Check", active=True)],
             "Y": [projection(measure("Robustness", "Robustness AUC 2023"), display="Scorecard AUC, 2023")],
             "Tooltips": [projection(column("Robustness", "Note"), display="Note")]},
            {**axes(start=0.5, end=1.148, inner=57), "dataPoint": [obj(fill=colour(SCREEN_INK))],
             "labels": labels(size=10.5, bold=False, decimals=3)},
            sort=[(column("Robustness", "Label"), "Ascending")])),
        ("chart_roc", (780, 764, 156, 156), chart(
            "lineChart",
            {"Category": [projection(column("ROC", "False positive rate"), display="Non-crossers flagged", active=True)],
             "Y": [projection(measure("ROC", "ROC true positive rate"), display="Crossers caught"),
                   projection(measure("ROC", "Coin toss"), display="Coin toss")]},
            {"categoryAxis": [obj(show=lit(False), axisType=lit("Scalar"), start=lit(0.0), end=lit(1.0))],
             "valueAxis": [obj(show=lit(False), start=lit(0.0), end=lit(1.0), gridlineShow=lit(False))],
             "legend": [obj(show=lit(False))],
             "dataPoint": [obj(series(measure("ROC", "ROC true positive rate")), fill=colour(SCREEN_INK)),
                           obj(series(measure("ROC", "Coin toss")), fill=colour(MUTED))],
             "lineStyles": [series_style(measure("ROC", "ROC true positive rate"), SCREEN_INK, shade=True),
                            series_style(measure("ROC", "Coin toss"), MUTED, width=1.0, dashed=True)]})),
        ("label_roc_auc", (812, 856, 124, 36), card(measure("Models", "ROC AUC label"), 15, align="right")),
        ("label_roc_selection", (736, 964, 202, 26), card(measure("Models", "Picked model and year"), 10.5, ink=INK, bold=False, align="right")),
        ("chart_calibration", (1072, 784, 308, 176), chart(
            "lineClusteredColumnComboChart",
            {"Category": [projection(column("Calibration", "Score decile"), display="Score decile", active=True)],
             "Y": [projection(measure("Calibration", "Share that crossed"))],
             "Y2": [projection(measure("Calibration", "Predicted"))]},
            {"categoryAxis": [obj(show=lit(True), fontSize=lit(10.5), fontFamily=lit(SEGOE), labelColor=colour(MUTED),
                                  showAxisTitle=lit(False), innerPadding=lit(50), axisType=lit("Categorical"))],
             "valueAxis": [obj(show=lit(False), start=lit(0.0), end=lit(0.6), gridlineShow=lit(False),
                               secShow=lit(False), secStart=lit(0.0), secEnd=lit(0.6))],
             "legend": [obj(show=lit(False))],
             "dataPoint": [obj(fill=colour(WARM_GREY)), obj(series(measure("Calibration", "Share that crossed")), fill=colour(WARM_GREY)),
                           obj(series(measure("Calibration", "Predicted")), fill=colour(SCREEN_INK))],
             "lineStyles": [series_style(measure("Calibration", "Predicted"), SCREEN_INK, marker=True)]},
            sort=[(column("Calibration", "Score decile"), "Ascending")])),
        ("label_calibration_selection", (1208, 756, 174, 26), card(measure("Models", "Picked model and year"), 10.5, ink=INK, bold=False, align="right")),
        ("note_calibration", (1072, 840, 300, 64), card(measure("Calibration", "Calibration note"), 10.5, ink=INK, bold=False, wrap=True)),
        ("chart_drivers", (1476, 762, 352, 210), chart(
            "clusteredBarChart",
            {"Category": [projection(column("Drivers", "Driver"), active=True)],
             "Y": [projection(measure("Drivers", "Driver AUC drop"), display="AUC lost if shuffled")]},
            {**axes(category=True, inner=57), "dataPoint": [obj(fill=colour(SCREEN_INK))], "labels": labels(size=10.5, bold=False, decimals=3)},
            sort=[(measure("Drivers", "Driver AUC drop"), "Descending")]),
         [top_n("top7", column("Drivers", "Driver"), measure("Drivers", "Driver AUC drop"), 7)]),
    ]
    return v, {}


def pricing():
    band = column("PricingBands", "Band label")
    short = column("PricingBands", "Band short")
    label = measure("PricingSummary", "Pricing scenario label")
    v = rail("pricing",
             [(measure("PricingSummary", "Wrong band A to B"), (label, (146, 432, 160, 26)), 330),
              (measure("PricingSummary", "Overall ratio A to B"), (label, (506, 432, 160, 26)), 216)],
             [("slicer_claim_cost", (64, 646, 576, 84), slicer(column("ClaimCostScenarios", "Scenario"), "Claim-cost scenario",
                                                               default_value="Central")),
              ("slicer_score_year", (64, 734, 576, 84), slicer(column("ScoreYears", "Tile label"), "Test year",
                                                               default_value="2023, outcome 2024"))],
             "Method and caveats: Model Trust →", "trust")
    a, b = measure("PricingBands", "Band loss ratio A"), measure("PricingBands", "Band loss ratio B")
    fill = measure("PricingSummary", "Scenario row fill")
    cols = [("Scenario", "Scenario", 90, "Left"), ("Rule", "Cases priced × claim cost", 196, "Left")]
    meas = [("Scenario premium", "Simulated premium", 150), ("Scenario simulated loss", "Simulated loss", 150),
            ("Scenario loss ratio", "Loss / premium, A and B", 180), ("Scenario wrong band A to B", "Wrong band, A → B", 170),
            ("Scenario band spread A to B", "Band spread, A → B", 154)]
    v += [
        ("chart_loss_premium", (736, 236, 646, 336), chart(
            "lineChart", {"Category": [projection(band, display="Risk band", active=True)],
                          "Y": [projection(a, display="Simulated loss / premium, A industry only"),
                                projection(b, display="Simulated loss / premium, B with the score")]},
            {**axes(category=True, start=0), "legend": [obj(show=lit(False))],
             "dataPoint": [obj(series(a), fill=colour(WARM_GREY)), obj(series(b), fill=colour(SCREEN_INK))],
             "lineStyles": [series_style(a, WARM_GREY, width=0.0, marker=True), series_style(b, SCREEN_INK, width=0.0, marker=True)],
             "error": connectors(a, measure("PricingBands", "Band loss ratio low"), measure("PricingBands", "Band loss ratio high")),
             "labels": [obj(show=lit(True), color=colour(INK), fontSize=lit(10.5), fontFamily=lit(SEGOE), labelDisplayUnits=lit(1.0),
                            labelPrecision=lit(2)),
                        obj(series(b), color=colour(ONYX), fontSize=lit(15.0), fontFamily=lit(SEGOE_SEMIBOLD))],
             "y1AxisReferenceLine": [obj({"id": "1"}, show=lit(True), value=lit(1.0), lineColor=colour(MUTED), style=lit("solid"),
                                         position=lit("front"), transparency=lit(0.0), dataLabelShow=lit(True),
                                         displayName=lit("1.0: simulated loss equals premium"), dataLabelColor=colour(INK),
                                         dataLabelText=lit("Name"), dataLabelHorizontalPosition=lit("left"),
                                         dataLabelVerticalPosition=lit("above"))]},
            sort=[(band, "Ascending")])),
        ("note_loss_premium", (818, 584, 300, 26), card(measure("PricingSummary", "Pricing base line"), 10.5, ink=MUTED, bold=False)),
        ("chart_premium_change", (1476, 220, 350, 350), chart(
            "clusteredColumnChart", {"Category": [projection(short, display="Risk band", active=True)],
                                     "Y": [projection(measure("PricingBands", "Band premium change"), display="Simulated premium change, A to B")]},
            {**axes(category=True, inner=30), "dataPoint": [obj(when(short, f"Band {k + 1}"), fill=colour(c)) for k, c in enumerate(BANDS)],
             "labels": labels(size=10.5, bold=False)},
            sort=[(short, "Ascending")])),
        ("note_premium_change", (1558, 584, 300, 26), card(measure("PricingSummary", "Pricing base line"), 10.5, ink=MUTED, bold=False)),
        ("table_sensitivity", (736, 732, 1092, 124), table(
            [projection(column("PricingSummary", c), display=d) for c, d, _, _ in cols] +
            [projection(measure("PricingSummary", m), display=d) for m, d, _ in meas],
            {**table_style(),
             "values": table_style()["values"] +
                       [by_measure(f"PricingSummary.{c}", "backColor", fill) for c, _, _, _ in cols] +
                       [by_measure(f"PricingSummary.{m}", "backColor", fill) for m, _, _ in meas],
             "columnWidth": widths(*[(f"PricingSummary.{c}", w) for c, _, w, _ in cols], *[(f"PricingSummary.{m}", w) for m, _, w in meas]),
             "columnFormatting": aligned(*[(f"PricingSummary.{c}", al) for c, _, _, al in cols],
                                         *[(f"PricingSummary.{m}", "Right") for m, _, _ in meas])})),
        ("note_sensitivity", (818, 968, 260, 26), card(measure("PricingSummary", "Pricing year base line"), 10.5, ink=MUTED, bold=False)),
    ]
    return v, {}


SECTOR_NAMES = ["Manufacturing", "Construction", "Transport and warehousing", "Wholesale", "Utilities", "Agriculture",
                "Mining, oil and gas"]
DRILL = {"landscape": column(SITES, "Sector")}
BUILDERS = {"executive": executive, "landscape": landscape, "trust": trust, "pricing": pricing}
TOOLTIPS = []


# ---------- assembly ----------

def visual_json(name, box, z, visual, filters=None):
    x, y, w, h = box
    d = {"$schema": f"{SCHEMA}/visualContainer/2.14.0/schema.json", "name": name,
         "position": {"x": x, "y": y, "z": z, "height": h, "width": w, "tabOrder": z}, "visual": visual}
    if filters:
        d["filterConfig"] = {"filters": filters}
    return d


def page_json(name, title, background, interactions, drill=None):
    image = {"image": {"name": lit(background), "scaling": lit("Fit"),
                       "url": {"expr": {"ResourcePackageItem": {"PackageName": "RegisteredResources", "PackageType": 1,
                                                                 "ItemName": background}}}}}
    d = {"$schema": f"{SCHEMA}/page/2.1.0/schema.json", "name": name, "displayName": title,
         "displayOption": "FitToPage", "height": 1080, "width": 1920,
         "objects": {"background": [obj(image=image, transparency=lit(0.0))],
                     "outspace": [obj(color=colour(NEST), transparency=lit(0.0))]}}
    if interactions:
        d["visualInteractions"] = interactions
    if drill:
        d["filterConfig"] = {"filters": [{"name": f"{name}_drill", "field": drill, "type": "Categorical", "howCreated": "Drillthrough"}]}
        d["pageBinding"] = {"name": f"{name}_binding", "type": "Drillthrough",
                            "parameters": [{"name": f"{name}_drill_param", "boundFilter": f"{name}_drill", "asAggregation": False,
                                            "qnaSingleSelectRequired": False, "fieldExpr": drill}]}
    return d


def tooltip_page_json(name, title, width, height):
    return {"$schema": f"{SCHEMA}/page/2.1.0/schema.json", "name": name, "displayName": title,
            "displayOption": "FitToPage", "height": height, "width": width, "type": "Tooltip",
            "visibility": "HiddenInViewMode", "pageBinding": {"name": f"{name}_binding", "type": "Tooltip"},
            "objects": {"background": [obj(color=colour(ONYX), transparency=lit(0.0))],
                        "outspace": [obj(color=colour(ONYX), transparency=lit(0.0))]}}


def report_json(images):
    return {"$schema": f"{SCHEMA}/report/3.4.0/schema.json",
            "themeCollection": {
                "baseTheme": {"name": BASE_THEME, "reportVersionAtImport": VERSIONS, "type": "SharedResources"},
                "customTheme": {"name": THEME_FILE, "reportVersionAtImport": VERSIONS, "type": "RegisteredResources"}},
            "objects": {"section": [obj(verticalAlignment=lit("Top"))],
                        "outspacePane": [obj(expanded=lit(False), visible=lit(True))]},
            "resourcePackages": [
                {"name": "SharedResources", "type": "SharedResources",
                 "items": [{"name": BASE_THEME, "path": f"BaseThemes/{BASE_THEME}.json", "type": "BaseTheme"}]},
                {"name": "RegisteredResources", "type": "RegisteredResources",
                 "items": [{"name": THEME_FILE, "path": THEME_FILE, "type": "CustomTheme"}] +
                          [{"name": i, "path": i, "type": "Image"} for i in images]}],
            "settings": {"useStylableVisualContainerHeader": True, "exportDataMode": "None",
                         "defaultDrillFilterOtherVisuals": True, "allowChangeFilterTypes": True,
                         "useEnhancedTooltips": True, "useDefaultAggregateDisplayName": True}}


def build():
    files = {}
    images = []
    for name, title, stem in PAGES:
        background = f"{stem}.png"
        images.append(background)
        files[f"StaticResources/RegisteredResources/{background}"] = (PBI / "backgrounds" / background).read_bytes()
        visuals, filters = BUILDERS[name]()
        names = []
        for z, item in enumerate(visuals):
            vname, box, visual = item[:3]
            vfilters = item[3] if len(item) > 3 else filters.get(vname)
            vname = f"{name}_{vname}"
            names.append(vname)
            files[f"definition/pages/{name}/visuals/{vname}/visual.json"] = visual_json(vname, box, 1000 + z, visual, vfilters)
        # the Executive page is a fixed summary: selecting a mark filters nothing else on the page. On Risk Landscape
        # the map does not filter either: the baked statement is about whole sectors, and a single state's cells can
        # fall below it (see docs/qa-note.md)
        data = [n for n in names if "_nav_" not in n and "_link_" not in n]
        sources = [n for n in data if "_chart_" in n or "_table_" in n] if name == "executive" else \
            [f"{name}_map_tiles", f"{name}_map_hover"] if name == "landscape" else []
        interactions = [{"source": s, "target": t, "type": "NoFilter"} for s in sources for t in data if s != t]
        files[f"definition/pages/{name}/page.json"] = page_json(name, title, background, interactions,
                                                              DRILL.get(name))
    for name, title, width, height, builder in TOOLTIPS:
        visuals, _ = builder()
        for z, (vname, box, visual) in enumerate(visuals):
            vname = f"{name}_{vname}"
            files[f"definition/pages/{name}/visuals/{vname}/visual.json"] = visual_json(vname, box, 1000 + z, visual)
        files[f"definition/pages/{name}/page.json"] = tooltip_page_json(name, title, width, height)
    files["definition/pages/pages.json"] = {"$schema": f"{SCHEMA}/pagesMetadata/1.1.0/schema.json",
                                            "pageOrder": [p[0] for p in PAGES] + [t[0] for t in TOOLTIPS],
                                            "activePageName": PAGES[0][0]}
    files["definition/version.json"] = {"$schema": f"{SCHEMA}/versionMetadata/1.0.0/schema.json", "version": "2.0.0"}
    files["definition/report.json"] = report_json(images)
    files[f"StaticResources/RegisteredResources/{THEME_FILE}"] = (PBI / "theme" / THEME_FILE).read_bytes()
    return files


def main():
    files = build()
    if OUT.exists():
        shutil.rmtree(OUT)
    parts = []
    for path, content in sorted(files.items()):
        data = content if isinstance(content, bytes) else (json.dumps(content, indent=2, ensure_ascii=False) + "\n").encode()
        target = OUT / path
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_bytes(data)
        parts.append({"path": path, "payload": base64.b64encode(data).decode(), "payloadType": "InlineBase64"})
    BUNDLE.write_text(json.dumps({"parts": parts}))
    visuals = sum(1 for p in files if p.endswith("visual.json"))
    print(f"{len(files)} parts, {visuals} visuals, bundle {BUNDLE.stat().st_size / 1e6:.1f} MB -> {BUNDLE}")


if __name__ == "__main__":
    main()
