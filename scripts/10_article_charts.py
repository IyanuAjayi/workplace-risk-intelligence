"""
Charts for the trade article (docs/article-draft.md). Reads the result tables, checks every figure it draws against
docs/verified-metrics.md, then writes three PNGs at 3x (about 300 ppi at full text width) to outputs/article/:

  crossing_by_band.png     observed: share of sites that crossed the line next year, by risk band (priced portfolio)
  auc_by_model.png         model accuracy (AUC) of the four models on the unseen test years (all test pairs)
  premium_wrong_band.png   simulated: share of premium in the wrong band, scenario A against B, central claim cost

Colours and type follow docs/design-system.md, on a white background for print. The charts use Inter if its static
Regular and SemiBold files are installed and Arial otherwise (the design system's fallback); the font used is printed.

With --docx it then builds docs/article-draft.docx with pandoc and docs/templates/wri-reference.docx, and gives the
method box's paragraph style a hairline border and card fill, because pandoc has no box style for a fenced div.

Usage: .venv/bin/python scripts/10_article_charts.py [--docx]
"""
import re
import shutil
import subprocess
import sys
import zipfile
from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
import pandas as pd
from matplotlib import font_manager

MODEL, PRICING, OUT = Path("outputs/model"), Path("outputs/pricing"), Path("outputs/article")
METRICS = Path("docs/verified-metrics.md")
ARTICLE, REFERENCE = Path("docs/article-draft.md"), Path("docs/templates/wri-reference.docx")

W, SCALE = 720, 3  # chart width in pixels at 1x (1 pt = 1 px), saved at 3x
ONYX, INK, MUTED = "#000000", "#303A39", "#66655F"
SCREEN_INK, WARM_GREY, AXIS, CARD_LINE, MOLT = "#274A48", "#B3AFA1", "#CFCBBD", "#E3DECF", "#B5C7E4"
BANDS = ["1 lowest", "2", "3", "4", "5 highest"]
BAND_COLOURS = ["#C9D6BD", "#D1A76A", "#C98369", "#A96247", "#944126"]
MODELS = [("M0 rating class", "Rating class only", "Rating class only", "sector, size, state and ownership"),
          ("M1 last year only", "Last year's rate only", "Last year's rate", "the rate alone, as a rank in its industry"),
          ("M2 scorecard", "Scorecard", "Scorecard", "injury history plus rating class, explainable"),
          ("M3 gradient boosting", "Gradient boosting", "Gradient boosting", "the same inputs, a more flexible model")]
YEARS = [2023, 2024]
SOURCE = "Source: OSHA ITA Form 300A, 2016 to 2025; test years 2023 and 2024 (outcomes in 2024 and 2025)."


def pct(x):
    return f"{x * 100:.1f}%"


def find(pattern, text, what):
    m = re.search(pattern, text, re.M)
    assert m, f"{what} not found in {METRICS}"
    return m.groups()


def figures():
    """Every value the charts draw, computed from the result tables and checked against docs/verified-metrics.md."""
    doc = METRICS.read_text()
    bands = pd.read_csv(PRICING / "bands.csv").query("scenario == 'central'")
    bands["crossed"] = (bands["sites"] * bands["observed_crossing"]).round().astype(int)
    rates = {y: dict(zip(g["band"], g["observed_crossing"])) for y, g in bands.groupby("year")}
    sites = bands.groupby("year")["sites"].sum()
    base = bands["crossed"].sum() / bands["sites"].sum()

    assert find(r"Portfolio \(private-sector test sites with a BLS rate: ([\d,]+) site-years; 2023: ([\d,]+); 2024: ([\d,]+)\)",
                doc, "priced portfolio") == (f"{sites.sum():,}", f"{sites[2023]:,}", f"{sites[2024]:,}")
    assert find(r"Crossed the line next year: ([\d,]+) \(([\d.]+%)\)", doc, "base rate") == (f"{bands['crossed'].sum():,}", pct(base))
    section = doc[doc.index("**Risk bands**"):doc.index("- Top band")]
    for band in BANDS:
        assert find(rf"^\s*- {re.escape(band)}: ([\d.]+%) / ([\d.]+%)\s*$", section, f"band {band}") == \
            (pct(rates[2023][band]), pct(rates[2024][band])), f"band {band} crossing rate"
    for y in YEARS:  # the chart title says "about 16 times"
        assert round(rates[y]["5 highest"] / rates[y]["1 lowest"]) == 16, f"top to bottom band ratio, {y}"

    m = pd.read_csv(MODEL / "metrics.csv").set_index(["model", "split"])
    auc = {}
    for code, row, name, _ in MODELS:
        got = find(rf"^\| {re.escape(row)}[^|]*\| ([\d.]+) \([\d.]+ to [\d.]+\) \| ([\d.]+) \(", doc, f"AUC for {row}")
        assert got == tuple(f"{m.loc[(code, y), 'auc']:.3f}" for y in YEARS), f"AUC for {name}"
        auc[name] = {y: m.loc[(code, y), "auc"] for y in YEARS}
    pairs = {y: int(m.loc[("M2 scorecard", y), "n"]) for y in YEARS}
    assert find(r"all test pairs: 2023 n = ([\d,]+); 2024 n = ([\d,]+)", doc, "test pairs") == tuple(f"{pairs[y]:,}" for y in YEARS)

    s = pd.read_csv(PRICING / "summary.csv").query("scenario == 'central'").set_index("year")
    wrong = {y: (s.loc[y, "misallocated_share_a"], s.loc[y, "misallocated_share_b"]) for y in YEARS}
    assert find(r"\*\*Premium in the wrong band:\*\* ([\d.]+%) to ([\d.]+%) \(2023\), ([\d.]+%) to ([\d.]+%) \(2024\)", doc,
                "premium in the wrong band") == tuple(pct(v) for y in YEARS for v in wrong[y])
    assert "$50,076" in doc and "capped 0.6 to 2.0" in doc, "claim cost or relativity cap changed"
    return rates, base, sites, auc, pairs, wrong


def font():
    # matplotlib's font cache misses fonts installed after it was built, so register any Inter files first
    dirs = [*font_manager.X11FontDirectories, *font_manager.OSXFontDirectories]
    for path in map(Path, font_manager.findSystemFonts(dirs)):
        if path.name.startswith("Inter") and path.suffix.lower() in (".ttf", ".otf"):
            font_manager.fontManager.addfont(str(path))
    for family in ("Inter", "Arial"):
        try:
            font_manager.findfont(font_manager.FontProperties(family=family), fallback_to_default=False)
            return family
        except ValueError:
            continue
    return "DejaVu Sans"


def wrap(text, size, width=W - 48, weight="normal"):
    """Break text into lines no wider than width pixels, measured in the chart font."""
    fig = plt.figure(figsize=(W / 72, 1), dpi=72)
    renderer = fig.canvas.get_renderer()
    lines, line = [], ""
    for word in text.split():
        trial = f"{line} {word}".strip()
        t = fig.text(0, 0, trial, fontsize=size, fontweight=weight)
        if line and t.get_window_extent(renderer).width > width:
            lines.append(line)
            line = word
        else:
            line = trial
        t.remove()
    plt.close(fig)
    return lines + [line]


class Chart:
    """A white chart canvas laid out in pixels from the top-left corner, at 1 pt = 1 px. The body is the space above
    the source note, which is wrapped to the chart width and sets the final height."""

    def __init__(self, body, title, subtitle, source, title_width=W - 48):
        assert len(wrap(title, 18, title_width, 600)) == 1, f"title too long for one line: {title}"
        lines = wrap(subtitle, 13)
        assert len(lines) <= 2, f"subtitle runs to {len(lines)} lines: {subtitle}"
        notes = wrap(source, 11)
        self.h = body + 16 * len(notes) + 12
        self.fig = plt.figure(figsize=(W / 72, self.h / 72), dpi=72, facecolor="white")
        self.text(24, 34, title, size=18, weight=600)
        for i, line in enumerate(lines):
            self.text(24, 58 + 18 * i, line, size=13, color=MUTED)
        for i, line in enumerate(notes):
            self.text(24, body + 12 + 16 * i, line, size=11, color=MUTED)

    def text(self, x, y, s, size=13, color=ONYX, weight="normal", ha="left", **kw):
        return self.fig.text(x / W, 1 - y / self.h, s, fontsize=size, color=color, fontweight=weight, ha=ha,
                             va="baseline", **kw)

    def axes(self, left, top, right, bottom):
        ax = self.fig.add_axes([left / W, 1 - bottom / self.h, (right - left) / W, (bottom - top) / self.h])
        ax.set_facecolor("none")
        for side in ("top", "right", "left", "bottom"):
            ax.spines[side].set_visible(False)
        ax.tick_params(colors=AXIS, labelcolor=MUTED, labelsize=12, length=6, width=1)
        return ax

    def save(self, name):
        self.fig.savefig(OUT / name, dpi=72 * SCALE, facecolor="white")
        plt.close(self.fig)


def chart_bands(rates, base, sites):
    c = Chart(456, "Band 5 sites crossed the line about 16 times as often as band 1 sites",
              "Share of sites whose serious-injury (DART) rate the following year was above their industry's line. "
              "Columns show the 2023 test year; the row beneath shows 2024.",
              f"{SOURCE} Observed crossing rates for the priced portfolio, {sites.sum():,} private-sector site-years "
              f"({sites[2023]:,} in 2023, {sites[2024]:,} in 2024). Bands are scorecard fifths of both test years pooled. "
              "The line is the DART rate that marked the worst 20% of qualifying sites in the site's 3-digit NAICS industry "
              "this year; DART cases are those with "
              "days away from work, job restriction or transfer.")
    left, right, lo, hi = 64, 696, -0.6, 4.6
    ax = c.axes(left, 116, right, 360)
    ax.bar(range(5), [rates[2023][b] for b in BANDS], width=0.56, color=BAND_COLOURS, zorder=3)
    for i, b in enumerate(BANDS):
        ax.annotate(pct(rates[2023][b]), (i, rates[2023][b]), xytext=(0, 6), textcoords="offset points", ha="center",
                    va="bottom", fontsize=14, fontweight=600, color=ONYX)
    ax.axhline(base, color=MUTED, lw=1, dashes=(4, 4), zorder=2)
    ax.annotate(f"All sites {pct(base)}, 2023 + 2024", (lo + 0.12, base), xytext=(0, 5), textcoords="offset points",
                fontsize=12, color=INK, va="bottom")
    ax.set_xlim(lo, hi)
    ax.set_ylim(0, 0.52)
    ax.set_xticks([])
    ax.set_yticks([0, 0.1, 0.2, 0.3, 0.4, 0.5])
    ax.set_yticklabels([f"{t:.0%}" for t in ax.get_yticks()])
    ax.spines["bottom"].set_visible(True)
    ax.spines["bottom"].set_color(INK)
    c.text(24, 98, "Crossed the line next year", size=12, color=MUTED)

    x = [left + (i - lo) / (hi - lo) * (right - left) for i in range(5)]
    for i, note in enumerate(["lowest fifth", "", "", "", "highest fifth"]):
        c.text(x[i], 382, f"Band {i + 1}", size=13, ha="center")
        c.text(x[i], 398, note, size=12, color=MUTED, ha="center")
    c.fig.add_artist(plt.Line2D([24 / W, 696 / W], [1 - 414 / c.h] * 2, color=CARD_LINE, lw=1))
    c.text(24, 436, "2024", size=13, color=INK, weight=600)
    for i, b in enumerate(BANDS):
        c.text(x[i], 436, pct(rates[2024][b]), size=13, color=INK, ha="center")
    c.save("crossing_by_band.png")


def chart_auc(auc, pairs):
    c = Chart(380, "Within its industry, a site's record ranks risk far better than its rating class",
              "AUC on test pairs the models never saw: the chance that a site which crossed the line was scored above "
              "one that didn't. Bars show the 2023 test year; 0.50 is a coin toss.",
              f"{SOURCE} Rating class, scorecard and gradient boosting trained on 2016 to 2022, the last two tuned on "
              "2022; last year's rate is a rank and needs no training. All test pairs, including public-sector sites: "
              f"{pairs[2023]:,} in 2023 and {pairs[2024]:,} in 2024.")
    top, bottom, left, right, lo, hi = 116, 324, 272, 572, 0.5, 0.85
    for _, _, name, about in MODELS:
        assert len(wrap(name, 13, left - 32, 600)) == 1 and len(wrap(about, 11.5, left - 32)) == 1, \
            f"model label runs into the bars: {name}, {about}"
    ax = c.axes(left, top, right, bottom)
    names = [name for _, _, name, _ in MODELS]
    ax.barh(range(4), [auc[n][2023] - lo for n in names], left=lo, height=0.42,
            color=[SCREEN_INK if n == "Scorecard" else WARM_GREY for n in names], zorder=3)
    ax.set_ylim(3.5, -0.5)
    ax.set_xlim(lo, hi)
    ax.set_yticks([])
    ax.set_xticks([0.5, 0.6, 0.7, 0.8])
    ax.set_xticklabels([f"{t:.2f}" for t in ax.get_xticks()])
    ax.spines["left"].set_visible(True)
    ax.spines["left"].set_color(INK)
    ax.spines["bottom"].set_visible(True)
    ax.spines["bottom"].set_color(AXIS)
    c.text(left, bottom + 40, "AUC, 2023 test year (the axis starts at 0.50, a coin toss)", size=12, color=MUTED)

    pitch = (bottom - top) / 4
    c.text(636, top - 10, "2023", size=12, color=MUTED, ha="right")
    c.text(696, top - 10, "2024", size=12, color=MUTED, ha="right")
    for i, (_, _, name, about) in enumerate(MODELS):
        y = top + pitch * (i + 0.5)
        main = name == "Scorecard"
        c.text(24, y - 1, name, size=13, color=ONYX if main else INK, weight=600 if main else "normal")
        c.text(24, y + 15, about, size=11.5, color=MUTED)
        c.text(636, y + 5, f"{auc[name][2023]:.3f}", size=14, color=ONYX if main else INK, weight=600 if main else "normal",
               ha="right")
        c.text(696, y + 5, f"{auc[name][2024]:.3f}", size=14, color=INK, ha="right")
    c.save("auc_by_model.png")


def chart_wrong_band(wrong, sites):
    c = Chart(306, "Pricing by score cut simulated premium in the wrong band",
              "Share of simulated premium that would have to move between risk bands for each band's share of premium "
              "to match its share of simulated losses. Central claim cost.",
              "Simulated: not actual premiums, claims or loss ratios. A applies the industry's BLS SOII DART rate from two "
              "years before the year priced (2022 rates for 2024 losses and 2023 rates for 2025, the latest published "
              "when each year began) to each site's hours worked in that year; B re-spreads the same total within each "
              "industry by score, with relativities capped at 0.6 to 2.0 before each industry's total is restored. "
              f"Claim cost $50,076 per DART case (NCCI via NSC Injury Facts). {SOURCE} Priced portfolio, "
              f"{sites.sum():,} private-sector site-years.", title_width=W - 48 - 110)
    c.text(690, 34, "Simulated", size=12, color=INK, ha="right",
           bbox=dict(boxstyle="square,pad=0.45", facecolor=MOLT, edgecolor="none"))
    top, bottom, left, right, hi = 108, 254, 264, 640, 0.30
    ax = c.axes(left, top, right, bottom)
    rows = [0, 1, 2.5, 3.5]
    values = [v for y in YEARS for v in wrong[y]]
    ax.barh(rows, values, height=0.62, color=[WARM_GREY, SCREEN_INK] * 2, zorder=3)
    for r, v, main in zip(rows, values, [False, True] * 2):
        ax.annotate(pct(v), (v, r), xytext=(6, 0), textcoords="offset points", va="center", fontsize=14,
                    color=ONYX if main else INK, fontweight=600 if main else "normal")
    ax.set_ylim(4.1, -0.6)
    ax.set_xlim(0, hi)
    ax.set_yticks([])
    ax.set_xticks([0, 0.1, 0.2, 0.3])
    ax.set_xticklabels([f"{t:.0%}" for t in ax.get_xticks()])
    ax.spines["left"].set_visible(True)
    ax.spines["left"].set_color(INK)
    ax.spines["bottom"].set_visible(True)
    ax.spines["bottom"].set_color(AXIS)
    c.text(left, bottom + 40, "Share of simulated premium in the wrong band", size=12, color=MUTED)

    for y, (ra, rb) in zip(YEARS, [(0, 1), (2.5, 3.5)]):
        ya, yb = (top + (r + 0.6) / 4.7 * (bottom - top) for r in (ra, rb))
        c.text(24, (ya + yb) / 2 + 5, f"{y} test year", size=13, weight=600)
        c.text(250, ya + 4.5, "A, industry rate only", size=13, color=INK, ha="right")
        c.text(250, yb + 4.5, "B, with the score", size=13, weight=600, ha="right")
    c.save("premium_wrong_band.png")


def build_docx():
    """Build the Word draft with pandoc, then give pandoc's "Method box" style a border and fill so it reads as a box."""
    pandoc = shutil.which("pandoc") or "/opt/anaconda3/bin/pandoc"
    target = ARTICLE.with_suffix(".docx")
    subprocess.run([pandoc, str(ARTICLE), "-o", str(target), f"--reference-doc={REFERENCE}", "--resource-path=docs"],
                   check=True)
    box = ('<w:pPr><w:keepNext /><w:keepLines /><w:pBdr>'
           + "".join(f'<w:{s} w:val="single" w:sz="4" w:space="6" w:color="CFCBBD" />' for s in ("top", "left", "bottom", "right"))
           + '</w:pBdr><w:shd w:val="clear" w:color="auto" w:fill="F7F5EC" /><w:spacing w:before="0" w:after="80" />'
           '<w:ind w:left="170" w:right="170" /></w:pPr><w:rPr><w:sz w:val="18" /><w:szCs w:val="18" /></w:rPr>')
    tmp = target.with_suffix(".tmp")
    with zipfile.ZipFile(target) as src, zipfile.ZipFile(tmp, "w", zipfile.ZIP_DEFLATED) as dst:
        for item in src.infolist():
            data = src.read(item.filename)
            if item.filename == "word/styles.xml":
                xml, n = re.subn(r'(<w:style [^>]*w:styleId="Methodbox"[^>]*>.*?)(</w:style>)', rf"\g<1>{box}\g<2>",
                                 data.decode("utf-8"), flags=re.S)
                assert n == 1, "Method box style not found in the Word output"
                data = xml.encode("utf-8")
            dst.writestr(item, data)
    tmp.replace(target)
    print(f"wrote {target}")


def main():
    OUT.mkdir(parents=True, exist_ok=True)
    rates, base, sites, auc, pairs, wrong = figures()
    family = font()
    plt.rcParams.update({"font.family": family, "axes.unicode_minus": False})
    print(f"figures match docs/verified-metrics.md; drawing in {family}")
    chart_bands(rates, base, sites)
    chart_auc(auc, pairs)
    chart_wrong_band(wrong, sites)
    print(f"wrote 3 charts to {OUT}/ at {W * SCALE} px wide")
    if "--docx" in sys.argv[1:]:
        build_docx()


if __name__ == "__main__":
    main()
