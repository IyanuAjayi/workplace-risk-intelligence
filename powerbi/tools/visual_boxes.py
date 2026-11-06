"""
Lists the position and size of every native Power BI visual drawn on a design mockup, read from the rendered page:
each element marked data-pbi="visual" with its id, data-pbi-type and box in page pixels (the Power BI page is
1920 x 1080, so these are the values to type into Format > General > Properties).

Writes powerbi/build/<page>.boxes.json and prints a table.

Usage: .venv/bin/python powerbi/tools/visual_boxes.py powerbi/mockups/page1-executive-intelligence.html [...]
"""
import json
import re
import subprocess
import sys
import tempfile
from html import unescape
from pathlib import Path

CHROME = "/Applications/Google Chrome.app/Contents/MacOS/Google Chrome"
OUT = Path(__file__).resolve().parents[1] / "build"
PROBE = """<script>window.addEventListener('load',()=>setTimeout(()=>{const b=[...document.querySelectorAll('[data-pbi="visual"]')].map(e=>{const r=e.getBoundingClientRect();return{id:e.id,type:e.dataset.pbiType||'',x:Math.round(r.left),y:Math.round(r.top),w:Math.round(r.width),h:Math.round(r.height)}});const p=document.createElement('pre');p.id='pbi-boxes';p.textContent=JSON.stringify(b);document.body.appendChild(p)},500))</script>"""


def boxes(page):
    page = Path(page).resolve()
    with tempfile.NamedTemporaryFile("w", suffix=".html", dir=page.parent, delete=False) as tmp:
        tmp.write(page.read_text().replace("</body>", PROBE + "</body>", 1))
    try:
        with tempfile.TemporaryDirectory() as profile:
            dom = subprocess.run([CHROME, "--headless=new", "--disable-gpu", f"--user-data-dir={profile}",
                                  "--window-size=1920,1080", "--virtual-time-budget=8000", "--dump-dom",
                                  f"file://{tmp.name}"], check=True, capture_output=True, text=True).stdout
    finally:
        Path(tmp.name).unlink()
    found = re.search(r'<pre id="pbi-boxes">(.*?)</pre>', dom, re.S)
    assert found, f"no boxes reported for {page.name}"
    return json.loads(unescape(found.group(1)))


def main():
    OUT.mkdir(exist_ok=True)
    for page in sys.argv[1:]:
        found = boxes(page)
        (OUT / f"{Path(page).stem}.boxes.json").write_text(json.dumps(found, indent=1))
        print(f"\n{Path(page).name}: {len(found)} visuals")
        for b in found:
            print(f"  {b['id']:<34} {b['type']:<26} x {b['x']:>4}  y {b['y']:>4}  w {b['w']:>4}  h {b['h']:>4}")


if __name__ == "__main__":
    main()
