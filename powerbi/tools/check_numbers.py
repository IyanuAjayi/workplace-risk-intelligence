"""
Lists every number shown on an HTML page or board that does not appear in docs/verified-metrics.md, so a person can
check each one. Reads visible text only (body text and SVG labels, not CSS or scripts).

A number passes if it appears in the metrics file, either exactly or rounded to fewer decimals, or if it is
structural (a year, a band or section number, a common axis tick). Everything else is printed with its context.
Derived figures such as "16x" will be listed: confirm each one by hand.

Usage: python3 powerbi/tools/check_numbers.py powerbi/mockups/concept-a-*.html [--metrics docs/verified-metrics.md]
       python3 powerbi/tools/check_numbers.py refined.html --reference original.html   (figures changed or added)
"""
import argparse
import re
from decimal import ROUND_HALF_EVEN, ROUND_HALF_UP, Decimal
from html.parser import HTMLParser
from pathlib import Path

NUMBER = re.compile(r"(?<![\w.])[-+]?\$?\d[\d,]*(?:\.\d+)?(?:bn|m|k)?%?x?(?![\w])", re.I)
STRUCTURAL = {str(y) for y in range(2010, 2027)} | {str(i) for i in range(0, 11)} | {f"0{i}" for i in range(0, 10)} | {
    "0.0", "0.25", "0.5", "0.50", "0.75", "1.0", "1.00", "1.5", "2.0", "2.5", "3.0", "100", "200,000", "20", "10", "50"}


class Text(HTMLParser):
    def __init__(self):
        super().__init__()
        self.skip, self.parts = 0, []

    def handle_starttag(self, tag, attrs):
        if tag in ("style", "script", "head"):
            self.skip += 1

    def handle_endtag(self, tag):
        if tag in ("style", "script", "head") and self.skip:
            self.skip -= 1

    def handle_data(self, data):
        if not self.skip and data.strip():
            self.parts.append(" ".join(data.split()))


def core(token):
    t = token.lower().lstrip("+-$").rstrip("x%")
    for unit in ("bn", "m", "k"):
        if t.endswith(unit):
            t = t[: -len(unit)]
    return t.replace(",", "")


def allowed(metrics_text):
    """Exact figures, plus roundings that keep at least one decimal place (0.783 -> 0.78, 2.57 -> 2.6). Whole-number
    roundings are not added, so "51%" for 51.4% is listed for a person to confirm rather than passed silently."""
    ok = set(STRUCTURAL)
    for token in NUMBER.findall(metrics_text):
        c = core(token)
        ok.add(c)
        if "." in c:
            for places in range(1, len(c.split(".")[1])):
                q = Decimal(1).scaleb(-places)
                ok.update(str(Decimal(c).quantize(q, rounding=r)) for r in (ROUND_HALF_UP, ROUND_HALF_EVEN))
    return ok


def visible(page):
    parser = Text()
    parser.feed(Path(page).read_text())
    return " | ".join(parser.parts)


def main():
    p = argparse.ArgumentParser()
    p.add_argument("pages", nargs="+")
    p.add_argument("--metrics", default=str(Path(__file__).resolve().parents[2] / "docs" / "verified-metrics.md"))
    p.add_argument("--reference", help="an earlier HTML page: list numbers that are not on it (changed or added figures)")
    args = p.parse_args()
    ok = allowed(visible(args.reference) if args.reference else Path(args.metrics).read_text())
    total = 0
    for page in args.pages:
        text = visible(page)
        flagged = []
        for m in NUMBER.finditer(text):
            if core(m.group()) not in ok:
                flagged.append((m.group(), text[max(0, m.start() - 60): m.end() + 40]))
        total += len(flagged)
        print(f"\n{page}: {len(flagged)} numbers to confirm by hand")
        for token, context in flagged:
            print(f"  {token:>10}  ...{context}...")
    print(f"\n{total} in total")


if __name__ == "__main__":
    main()
