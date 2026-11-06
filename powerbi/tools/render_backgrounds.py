"""
Renders the Power BI page backgrounds from the design mockups. Every element marked data-pbi="visual" is something
Power BI draws natively (cards, charts, tables, slicers, the page navigator), so it is hidden along with the mockup
corner label, and the rest (frames, cards, fixed text, logo) becomes the page's background image. Rendered at 2x (3840 x 2160) so text stays sharp when
Power BI scales the image to the 1920 x 1080 page.

Writes powerbi/backgrounds/<page>.png. Use the image with Format page > Canvas background > Image fit: Fit.

Usage: .venv/bin/python powerbi/tools/render_backgrounds.py powerbi/mockups/page1-executive-intelligence.html [...]
"""
import subprocess
import sys
import tempfile
from pathlib import Path

CHROME = "/Applications/Google Chrome.app/Contents/MacOS/Google Chrome"
HIDE = '<style>[data-pbi="visual"],.wri-corner-label{visibility:hidden !important}</style>'
OUT = Path(__file__).resolve().parents[1] / "backgrounds"


def render(page):
    page = Path(page).resolve()
    html = page.read_text()
    assert 'data-pbi="visual"' in html, f"{page.name} marks no live visuals"
    # the copy sits next to the original so relative links (stylesheet, logo) still resolve
    with tempfile.NamedTemporaryFile("w", suffix=".html", dir=page.parent, delete=False) as tmp:
        tmp.write(html.replace("</head>", HIDE + "</head>", 1))
    out = OUT / f"{page.stem}.png"
    try:
        with tempfile.TemporaryDirectory() as profile:
            subprocess.run([CHROME, "--headless=new", "--disable-gpu", "--hide-scrollbars", f"--user-data-dir={profile}",
                            "--window-size=1920,1080", "--force-device-scale-factor=2", "--virtual-time-budget=8000",
                            f"--screenshot={out}", f"file://{tmp.name}"], check=True, capture_output=True)
    finally:
        Path(tmp.name).unlink()
    return out


def main():
    OUT.mkdir(exist_ok=True)
    for page in sys.argv[1:]:
        print(render(page))


if __name__ == "__main__":
    main()
