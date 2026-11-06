"""
Page backgrounds for the Site Risk Lens Power BI report (design system: docs/dashboard-design.md).

The images carry only static text: the sidebar, each page's kicker, headline and deck, panel titles and subtitles,
fixed explanatory notes and the footer. Every number in a headline or subtitle is read from the analysis outputs
below, so the wording always matches the data. Every number inside a visual comes from Power BI.

Writes outputs/powerbi/bg_page1.png to bg_page4.png at 1920 x 1080 (the Power BI canvas). Layout units are
1280 x 720; VISUALS lists where each Power BI visual goes and the script prints those positions in canvas pixels.

Usage: .venv/bin/python scripts/07_powerbi_backgrounds.py
"""
import tempfile
from pathlib import Path
from textwrap import wrap

import matplotlib
matplotlib.use("Agg")
matplotlib.rcParams["text.parse_math"] = False
import matplotlib.pyplot as plt
import pandas as pd
from fontTools.ttLib import TTCollection
from matplotlib.font_manager import FontProperties
from matplotlib.patches import Rectangle

OUT = Path("outputs/powerbi")
W, H = 1280, 720
CANVAS, SIDE_BG = "#F7F7F5", "#EEEDE8"
INK, TEXT, MUTED, RULE = "#1C2127", "#3A424B", "#6B747E", "#DCDAD4"
ACCENT, HIGH = "#0B5CAD", "#C2410C"
SIDEBAR, X0, X1 = 150, 180, 1250
MID = 715  # gutter between the left and right panels

VISUALS = {
    "all pages": {"page navigator, vertical": (14, 104, 122, 120)},
    "page1": {
        "card: Sites": (180, 146, 170, 40), "card: Base rate": (360, 146, 170, 40),
        "card: Top band capture": (540, 146, 170, 40), "card: Top band lift": (720, 146, 170, 40),
        "card: Misallocated share A (PricingBands, 2023 central)": (900, 146, 170, 40),
        "card: Misallocated share B (PricingBands, 2023 central)": (1080, 146, 170, 40),
        "bar: AUC by Model (Models, test year 2023)": (180, 262, 520, 390),
        "column: Base rate by Risk band (Sites)": (730, 262, 520, 390),
    },
    "page2": {
        "slicer: Score year": (180, 140, 250, 26), "slicer: Sector": (450, 140, 250, 26),
        "slicer: State": (730, 140, 250, 26), "slicer: Size band": (1000, 140, 250, 26),
        "bar: Average site DART rate by Sector": (180, 230, 520, 190),
        "100% bar: Sites by Sector and Risk band": (180, 486, 520, 176),
        "bar: Share of sites in top band by State": (730, 230, 520, 432),
    },
    "page3": {
        "table: Models (Model, Test year, AUC, AUC low, AUC high, Gini, Capture, Precision)": (180, 166, 1070, 140),
        "line: Calibration, Scorecard 2023": (180, 372, 520, 290),
        "bar: Drivers, top 8": (730, 372, 520, 168),
    },
    "page4": {
        "slicer: Score year": (180, 140, 160, 26), "slicer: Claim-cost scenario": (360, 140, 160, 26),
        "card: Misallocated share A": (560, 140, 160, 40), "card: Misallocated share B": (730, 140, 160, 40),
        "card: Band spread A": (920, 140, 160, 40), "card: Band spread B": (1090, 140, 160, 40),
        "column: Premium A and B by Risk band": (180, 272, 520, 390),
        "line: Loss ratio A and B by Risk band, constant line 1": (730, 272, 520, 250),
    },
}


def faces():
    ttc = TTCollection("/System/Library/Fonts/HelveticaNeue.ttc")
    folder = Path(tempfile.gettempdir()) / "srl_fonts"
    folder.mkdir(exist_ok=True)
    out = {}
    for key, index in (("regular", 0), ("medium", 10)):
        path = folder / f"HelveticaNeue-{key}.ttf"
        if not path.exists():
            ttc.fonts[index].save(path)
        out[key] = FontProperties(fname=path)
    return out


FONT = faces()


class Page:
    def __init__(self, active):
        self.fig = plt.figure(figsize=(W / 100, H / 100), dpi=150)
        ax = self.fig.add_axes([0, 0, 1, 1])
        ax.set_xlim(0, W)
        ax.set_ylim(H, 0)
        ax.axis("off")
        ax.add_patch(Rectangle((0, 0), W, H, color=CANVAS, zorder=0))
        ax.add_patch(Rectangle((0, 0), SIDEBAR, H, color=SIDE_BG, zorder=1))
        self.ax, self.texts = ax, []
        self.sidebar()

    def t(self, x, y, s, size, color=TEXT, face="regular", right=None, **kw):
        item = self.ax.text(x, y, s, fontsize=size, color=color, fontproperties=FONT[face], ha="left", va="top",
                            zorder=3, **kw)
        item.set_fontsize(size)
        self.texts.append((item, right if right is not None else (SIDEBAR - 10 if x < SIDEBAR else X1)))

    def para(self, x, y, s, size, width, color=TEXT, right=None, gap=1.45):
        lines = wrap(s, width)
        self.t(x, y, "\n".join(lines), size, color, right=right, linespacing=gap)
        return y + len(lines) * size * gap * 1.39

    def hline(self, x0, x1, y, color=RULE, lw=0.6):
        self.ax.plot([x0, x1], [y, y], color=color, lw=lw, zorder=2, solid_capstyle="butt")

    def vline(self, x, y0, y1):
        self.ax.plot([x, x], [y0, y1], color=RULE, lw=0.6, zorder=2)

    def sidebar(self):
        self.vline(SIDEBAR, 0, H)
        self.t(16, 26, "Site Risk Lens", 13, INK, "medium")
        self.t(16, 48, "Workplace injury risk\nfor workers' comp pricing", 7.5, MUTED, linespacing=1.4)
        self.t(16, 88, "PAGES", 6.5, MUTED, "medium")
        self.t(16, 600, "Data: OSHA Injury\nTracking Application,\n2016 to 2025.\n\nPricing figures are\nsimulated.", 6.8, MUTED,
               linespacing=1.45)
        self.t(16, 690, "David Ajayi  ·  Parakeet Risk", 6.5, MUTED)

    def masthead(self, kicker, headline, deck):
        self.t(X0, 22, kicker, 8, ACCENT, "medium")
        self.t(X0, 36, headline, 18, INK, "medium")
        self.para(X0, 70, deck, 9.2, 178)
        self.hline(X0, X1, 112, INK, 0.6)

    def panel(self, x, y, title, sub, right=None, width=95):
        self.t(x, y, title, 11, INK, "medium", right=right)
        return self.para(x, y + 18, sub, 8, width, MUTED, right=right)

    def label(self, x, y, s, right=None):
        self.t(x, y, s, 7.8, MUTED, right=right)

    def footer(self):
        self.hline(X0, X1, 676)
        self.para(X0, 682, "Source: OSHA ITA Form 300A summary data 2016 to 2025; BLS SOII industry rates; NCCI claim costs via NSC "
                  "Injury Facts. Test years 2023 and 2024, industrial sectors. Pricing is simulated, not actual premiums, claims or loss "
                  "ratios. Prediction is not evidence of cause.", 6.6, 200, MUTED, gap=1.35)

    def save(self, name):
        self.footer()
        self.fig.canvas.draw()
        renderer = self.fig.canvas.get_renderer()
        inv = self.ax.transData.inverted()
        for item, right in self.texts:
            box = item.get_window_extent(renderer)
            (x0, _), (x1, y1) = inv.transform([(box.x0, box.y1), (box.x1, box.y0)])
            if x1 > right + 0.5 or y1 > H:
                raise ValueError(f"{name}: text runs past its column ({x1:.0f} > {right}): {item.get_text()[:50]!r}")
        self.fig.savefig(OUT / name, facecolor=CANVAS)
        plt.close(self.fig)


def facts():
    m = pd.read_csv("outputs/model/metrics.csv")
    auc = m.pivot(index="model", columns="split", values="auc")
    gains = pd.read_csv("outputs/model/scorecard_vs_last_year.csv")
    summ = pd.read_csv("outputs/pricing/summary.csv")
    central = summ[summ["scenario"] == "central"]
    bands = pd.read_csv("outputs/pricing/bands.csv")
    bc = bands[bands["scenario"] == "central"]
    sites = pd.read_excel(OUT / "workplace_risk_powerbi.xlsx", sheet_name="Sites")
    top = sites["Risk band"] == "5 highest"
    capture = sites.loc[top, "Crossed line next year"].sum() / sites["Crossed line next year"].sum()
    sector_top = sites.assign(top=top).groupby("Sector")["top"].mean()
    st = sites.assign(top=top).groupby("State").agg(n=("top", "size"), share=("top", "mean"))
    st = st[st["n"] >= 500]
    names = {"ME": "Maine", "LA": "Louisiana", "WA": "Washington", "AR": "Arkansas"}
    return {
        "auc_rc": auc.loc["M0 rating class"].mean(), "auc_last": auc.loc["M1 last year only"].mean(),
        "auc_sc_lo": auc.loc["M2 scorecard"].min(), "auc_sc_hi": auc.loc["M2 scorecard"].max(),
        "auc_gb": auc.loc["M3 gradient boosting"].mean(),
        "gain_lo": gains["lo"].min(), "gain_hi": gains["hi"].max(),
        "mis_a": central["misallocated_share_a"].mean(), "mis_b": central["misallocated_share_b"].mean(),
        "capture": capture, "n_sites": len(sites),
        "sector_lo": sector_top.min(), "sector_hi": sector_top.max(),
        "state_hi": (names.get(st["share"].idxmax(), st["share"].idxmax()), st["share"].max()),
        "state_lo": (names.get(st["share"].idxmin(), st["share"].idxmin()), st["share"].min()),
        "top_ratio_a": (bc.loc[bc["band"] == "5 highest", "ratio_a"].min(), bc.loc[bc["band"] == "5 highest", "ratio_a"].max()),
        "low_ratio_a": (bc.loc[bc["band"] == "1 lowest", "ratio_a"].min(), bc.loc[bc["band"] == "1 lowest", "ratio_a"].max()),
    }


def pct(x):
    return f"{x:.0%}"


def page1(f):
    p = Page(1)
    p.masthead("Executive summary  ·  OSHA injury records, US industrial sites  ·  tested on 2023 and 2024",
               f"Half of next year's serious-injury sites were already in the top fifth of the score",
               f"Industry, size and state alone rank sites barely better than chance (AUC {f['auc_rc']:.2f}). Adding the site's own "
               f"injury record lifts that to {f['auc_sc_lo']:.2f} to {f['auc_gb']:.2f} on years the model never saw. Priced with the "
               f"score, the share of simulated premium in the wrong risk band falls from about {pct(f['mis_a'])} to about {pct(f['mis_b'])}.")
    labels = ["Sites scored", "Crossed the line next year", "Caught in the top fifth", "Top fifth vs average",
              "Wrong band, industry only", "Wrong band, with score"]
    for i, lab in enumerate(labels):
        x = X0 + i * 180
        p.t(x, 128, "\n".join(wrap(lab, 30)), 7.6, MUTED, right=x + 170, linespacing=1.3)
    p.hline(X0, X1, 200)
    p.panel(X0, 214, "How well each model ranks sites",
            "AUC on the 2023 test year. 0.5 is a coin flip, 1.0 is perfect ranking.", right=MID - 15, width=80)
    p.panel(MID + 15, 214, "Share of sites that crossed the line next year, by risk band",
            "Scorecard bands, 2023 and 2024 test years, private-sector sites. Each band is a fifth of sites.", right=X1, width=80)
    p.vline(MID, 214, 660)
    p.save("bg_page1.png")


def page2(f):
    p = Page(2)
    (hs, hv), (ls, lv) = f["state_hi"], f["state_lo"]
    p.masthead("Risk landscape  ·  private-sector industrial sites  ·  2023 and 2024 test years",
               "High-risk sites are in every industry. Where they cluster is by state",
               f"Each sector has {pct(f['sector_lo'])} to {pct(f['sector_hi'])} of its sites in the top risk band, because the target is "
               f"set within each industry. States differ far more: {pct(hv)} of scored sites in {hs} sit in the top band, against "
               f"{pct(lv)} in {ls}.")
    for x, lab in zip((180, 450, 730, 1000), ("Score year", "Sector", "State", "Size band")):
        p.label(x, 124, lab)
    p.panel(X0, 184, "Average DART rate by sector",
            "Cases with days away, restriction or transfer per 100 full-time workers, this year.", right=MID - 15, width=80)
    p.panel(X0, 440, "Risk-band mix by sector",
            "Share of each sector's sites in each band. Orange is the top band, green the lowest.", right=MID - 15, width=80)
    p.panel(MID + 15, 184, "Share of sites in the top risk band, by state",
            "Gaps between states may partly reflect reporting practice and state rules, not only safety.", right=X1, width=80)
    p.vline(MID, 184, 660)
    p.save("bg_page2.png")


def page3(f):
    p = Page(3)
    p.masthead("Model trust  ·  trained on 2016 to 2022, tested once on 2023 and 2024",
               "The score was tested on years it never saw, and its probabilities hold up",
               f"Gradient boosting reaches AUC {f['auc_gb']:.2f} and the explainable scorecard {f['auc_sc_lo']:.2f} to {f['auc_sc_hi']:.2f}, "
               f"against {f['auc_last']:.2f} for last year's rate alone. The scorecard's gain is {f['gain_lo']:.2f} to {f['gain_hi']:.2f} "
               f"AUC at 95% confidence. Results are the same without 2020, with stable IDs only, and under the alternative target.")
    p.panel(X0, 124, "Model comparison",
            "Capture: share of next year's crossing sites caught in the model's top 20%. Precision: share of that top 20% that crossed.",
            width=170)
    p.hline(X0, X1, 318)
    p.panel(X0, 330, "Are the probabilities honest?",
            "Scorecard, 2023. Predicted against actual share crossing the line, by tenth of the score.", right=MID - 15, width=80)
    p.panel(MID + 15, 330, "What drives the score",
            "Gradient boosting: drop in AUC when each input is shuffled. Association, not cause.", right=X1, width=80)
    p.vline(MID, 330, 660)
    y = 556
    p.t(MID + 15, y, "Known weaknesses", 9.5, INK, "medium")
    notes = ["Employer-reported data; under-reporting is possible.",
             "Sites below OSHA's reporting thresholds aren't in it.",
             "About 30% of sites can't be followed into the next year; they look the same on risk.",
             "Much stronger for large sites (AUC 0.92) than for sites with 20 to 249 employees (0.76).",
             "Predicting reported injuries is not predicting claim costs, and not proof of cause."]
    y += 16
    for n in notes:
        y = p.para(MID + 15, y, "• " + n, 7.8, 95, TEXT, right=X1, gap=1.35) + 1
    p.save("bg_page3.png")


def page4(f):
    p = Page(4)
    a_hi, a_lo = f["top_ratio_a"], f["low_ratio_a"]
    p.masthead("Pricing lab  ·  simulated  ·  private-sector sites, 2023 and 2024 test years",
               f"With the score, premium follows risk: the share in the wrong band falls from {pct(f['mis_a'])} to {pct(f['mis_b'])}",
               f"Priced by industry alone, the riskiest fifth of sites generate {a_hi[0]:.1f} to {a_hi[1]:.1f} times their premium in "
               f"simulated losses and the safest fifth {a_lo[0]:.2f} to {a_lo[1]:.2f}. Total premium is the same in both scenarios, so "
               "the overall ratio can't change. What changes is how fairly it is split.")
    for x, lab in zip((180, 360), ("Score year", "Claim-cost scenario")):
        p.label(x, 124, lab)
    for x, lab in zip((560, 730, 920, 1090), ("Wrong band: industry only", "Wrong band: with score",
                                             "Gap between bands: industry only", "Gap between bands: with score")):
        p.t(x, 124, lab, 7.4, MUTED, right=x + 165)
    p.hline(X0, X1, 196)
    p.panel(X0, 212, "Premium by risk band",
            "Industry only (A) against with the score (B). Premium moves between sites in the same industry only.",
            right=MID - 15, width=80)
    p.panel(MID + 15, 212, "Simulated loss per $1 of premium, by risk band",
            "1.0 means premium matches losses. The flatter the line, the fairer the split.", right=X1, width=80)
    p.vline(MID, 212, 660)
    y = 540
    p.t(MID + 15, y, "What is simulated", 9.5, INK, "medium")
    notes = ["Premium A: the site's BLS industry DART rate for the prior year x hours worked x claim cost.",
             "Premium B: the same total, re-spread within each industry by the site's score (relativity capped at 0.6 to 2.0).",
             "Loss: the site's next-year OSHA DART cases x claim cost: $50,076 central (NCCI lost-time average); low counts days-away cases only; high uses $57,314.",
             "None of these are real premiums, claims or loss ratios."]
    y += 16
    for n in notes:
        y = p.para(MID + 15, y, "• " + n, 7.8, 95, TEXT, right=X1, gap=1.35) + 1
    p.save("bg_page4.png")


def main():
    f = facts()
    for fn in (page1, page2, page3, page4):
        fn(f)
    print("Visual positions in canvas pixels (x, y, width, height):")
    for page, items in VISUALS.items():
        print(page)
        for name, (x, y, w, h) in items.items():
            print(f"  {name}: {round(x * 1.5)}, {round(y * 1.5)}, {round(w * 1.5)}, {round(h * 1.5)}")


if __name__ == "__main__":
    main()
