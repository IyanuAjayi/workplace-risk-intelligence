"""
Builds the two-page project summary, Finding next year's riskiest workplaces, as a PDF and a Word file from one
source, docs/templates/riskiest-workplaces.html, so the two can't drift apart.

  1. Draws the three charts in docs/templates/riskiest-workplaces-charts.html into outputs/riskiest-workplaces/.
  2. Prints docs/Finding-Next-Years-Riskiest-Workplaces.pdf with headless Chrome, checks that each page's content
     stops above its footer (the page box hides overflow), and stamps the title and author.
  3. Writes docs/Finding-Next-Years-Riskiest-Workplaces.docx as Office Open XML: the same text, charts and report
     screens in editable Word styles, set in Arial so it looks the same on any computer, with the cream masthead
     cut from page 1 as a picture in the first-page header.

Usage, from the repository root: .venv/bin/python scripts/11_riskiest_workplaces.py
"""
import io
import re
import subprocess
import tempfile
import zipfile
from datetime import datetime, timezone
from html import escape
from html.parser import HTMLParser
from pathlib import Path
from xml.dom import minidom

from PIL import Image, ImageChops
from pypdf import PdfReader, PdfWriter

CHROME = "/Applications/Google Chrome.app/Contents/MacOS/Google Chrome"
SOURCE = Path("docs/templates/riskiest-workplaces.html")
CHARTS = Path("docs/templates/riskiest-workplaces-charts.html")
ASSETS = Path("outputs/riskiest-workplaces")
PDF = Path("docs/Finding-Next-Years-Riskiest-Workplaces.pdf")
DOCX = Path("docs/Finding-Next-Years-Riskiest-Workplaces.docx")
TITLE = "Finding next year’s riskiest workplaces"
AUTHOR = "David Ajayi"
SUBJECT = "Project summary, Parakeet Risk, November 2026"

TW = 1440 / 25.4  # twips per mm
EMU = 36000  # EMUs per mm
COL, GAP = 83.5, 7  # the two-column grid, mm (174 mm between 18 mm margins)
ONYX, INK, MUTED, CARD, RULE, MOLT = "000000", "303A39", "66655F", "F7F5EC", "DCD8CA", "B5C7E4"

FIT_PROBE = """<script>document.fonts.ready.then(() => {
  const room = [...document.querySelectorAll('.page')].map(page => {
    const top = page.getBoundingClientRect().top;
    const footer = page.querySelector('.footer').getBoundingClientRect().top - top;
    let bottom = 0;
    page.querySelectorAll('*').forEach(el => { if (!el.closest('.footer')) bottom = Math.max(bottom, el.getBoundingClientRect().bottom - top); });
    return ((footer - bottom) * 25.4 / 96).toFixed(1);
  });
  document.body.insertAdjacentHTML('beforeend', '<pre id="room">' + room.join(' ') + '</pre>');
});</script>"""


def chrome(*args):
    with tempfile.TemporaryDirectory() as profile:
        return subprocess.run([CHROME, "--headless=new", "--disable-gpu", "--hide-scrollbars", f"--user-data-dir={profile}",
                               "--virtual-time-budget=8000", *args], check=True, capture_output=True, text=True).stdout


def tw(mm):
    return round(mm * TW)


def draw_charts():
    """Each chart is drawn at its printed width (316 px is one 83.5 mm column) at 4x, then trimmed below."""
    for name in ("bands", "auc", "pricing"):
        out = ASSETS / f"{name}-chart.png"
        chrome("--window-size=316,400", "--force-device-scale-factor=4", f"--screenshot={out.resolve()}",
               f"{CHARTS.resolve().as_uri()}#{name}")
        img = Image.open(out).convert("RGB")
        bottom = ImageChops.difference(img, Image.new("RGB", img.size, "white")).getbbox()[3]
        img.crop((0, 0, img.width, bottom + 8)).save(out)


def check_fit():
    probe = SOURCE.with_name(".fit-probe.html")
    probe.write_text(SOURCE.read_text(encoding="utf-8").replace("</body>", FIT_PROBE + "</body>"), encoding="utf-8")
    try:
        dom = chrome("--window-size=794,2246", "--dump-dom", probe.resolve().as_uri())
    finally:
        probe.unlink()
    room = [float(x) for x in re.search(r'<pre id="room">(-?[\d.]+ -?[\d.]+)</pre>', dom).group(1).split()]
    assert len(room) == 2 and min(room) >= 3, f"content runs too close to the footer: {room} mm"
    return room


def print_pdf():
    chrome("--no-pdf-header-footer", f"--print-to-pdf={PDF.resolve()}", SOURCE.resolve().as_uri())
    reader = PdfReader(io.BytesIO(PDF.read_bytes()))
    assert len(reader.pages) == 2, f"the PDF has {len(reader.pages)} pages"
    writer = PdfWriter(clone_from=reader)
    writer.add_metadata({"/Title": TITLE, "/Author": AUTHOR, "/Subject": SUBJECT})
    with open(PDF, "wb") as f:
        writer.write(f)


def cut_masthead():
    shot = ASSETS / "word-masthead.png"
    chrome("--window-size=794,1123", "--force-device-scale-factor=3", f"--screenshot={shot.resolve()}", SOURCE.resolve().as_uri())
    img = Image.open(shot)
    img.crop((0, 0, img.width, round(15 / 25.4 * 96 * 3))).save(shot)
    return shot


class Node:
    def __init__(self, tag, attrs, parent):
        self.tag, self.attrs, self.parent, self.children = tag, dict(attrs), parent, []
        self.classes = set((self.attrs.get("class") or "").split())

    def elements(self):
        return [c for c in self.children if isinstance(c, Node)]

    def walk(self):
        for c in self.elements():
            yield c
            yield from c.walk()


class Tree(HTMLParser):
    VOID = {"br", "img", "meta", "link", "hr", "input", "source", "wbr"}

    def __init__(self, html):
        super().__init__(convert_charrefs=True)
        self.root = self.node = Node("root", {}, None)
        self.feed(html)

    def handle_starttag(self, tag, attrs):
        child = Node(tag, attrs, self.node)
        self.node.children.append(child)
        if tag not in self.VOID:
            self.node = child

    def handle_endtag(self, tag):
        node = self.node
        while node.parent and node.tag != tag:
            node = node.parent
        if node.parent:
            self.node = node.parent

    def handle_data(self, data):
        self.node.children.append(data)


def collect(node, bold=False):
    raw = []
    for c in node.children:
        if isinstance(c, str):
            raw.append(["text", c, bold])
        elif c.tag == "br":
            raw.append(["br", "", bold])
        elif c.tag == "span" and "tag" in c.classes:
            raw.append(["tag", "".join(inline_text(c)), False])
        else:
            raw += collect(c, bold or c.tag == "strong")
    return raw


def inline(node):
    """A paragraph's runs as [kind, text, bold], whitespace collapsed the way a browser does it."""
    runs, space = [], True
    for kind, text, b in collect(node):
        if kind == "text":
            text = re.sub(r"[ \t\n\r\f\v]+", " ", text)
            text = text.lstrip(" ") if space else text
            if not text:
                continue
            space = text.endswith(" ")
        else:
            space = kind == "br"
        runs.append([kind, text, b])
    for i, run in enumerate(runs):
        if run[0] == "text" and (i + 1 == len(runs) or runs[i + 1][0] == "br"):
            run[1] = run[1].rstrip(" ")
    return runs


def inline_text(node):
    return [c if isinstance(c, str) else "".join(inline_text(c)) for c in node.children]


def run(text, bold=False, color=None, size=None, shade=None):
    props = ("<w:b/><w:bCs/>" if bold else "") + (f'<w:color w:val="{ONYX if bold else color}"/>' if bold or color else "")
    props += f'<w:sz w:val="{size}"/><w:szCs w:val="{size}"/>' if size else ""
    props += f'<w:shd w:val="clear" w:color="auto" w:fill="{shade}"/>' if shade else ""
    return f'<w:r>{f"<w:rPr>{props}</w:rPr>" if props else ""}<w:t xml:space="preserve">{escape(text, quote=False)}</w:t></w:r>'


def runs_xml(runs):
    out = []
    for i, (kind, text, bold) in enumerate(runs):
        if kind == "br":
            out.append("<w:r><w:br/></w:r>")
        elif kind == "tag":
            out.append(run(f" {text} ", size=14, shade=MOLT))
            if i + 1 < len(runs) and not runs[i + 1][1].startswith(" "):
                out.append(run(" "))
        else:
            out.append(run(text, bold=bold))
    return "".join(out)


def para(content="", style=None, before=None, after=None, line=None, rule="exact", ind=None, size=None, section=""):
    props = f'<w:pStyle w:val="{style}"/>' if style else ""
    props += f'<w:tabs><w:tab w:val="left" w:pos="{ind}"/></w:tabs>' if ind else ""
    spacing = "".join(f' w:{k}="{v}"' for k, v in (("before", before), ("after", after)) if v is not None)
    if line is not None:
        spacing += f' w:line="{line}" w:lineRule="{rule}"'
    props += f"<w:spacing{spacing}/>" if spacing else ""
    props += f'<w:ind w:left="{ind}" w:hanging="{ind}"/>' if ind else ""
    props += f'<w:rPr><w:sz w:val="{size}"/><w:szCs w:val="{size}"/></w:rPr>' if size else ""
    props += section
    return f"<w:p>{f'<w:pPr>{props}</w:pPr>' if props else ''}{content}</w:p>"


def spacer(mm):
    """A blank line of an exact height: the gap between blocks, and the paragraph Word needs between two tables."""
    return para(before=0, after=0, line=max(tw(mm), 20), size=2)


def table(widths, cells):
    """A one-row layout table with no borders or cell padding. cells holds (content, extra tcPr) per column."""
    grid = "".join(f'<w:gridCol w:w="{w}"/>' for w in widths)
    tcs = "".join(f'<w:tc><w:tcPr><w:tcW w:w="{w}" w:type="dxa"/>{extra}</w:tcPr>{content or spacer(0)}</w:tc>'
                  for w, (content, extra) in zip(widths, cells))
    margins = "".join(f'<w:{side} w:w="0" w:type="dxa"/>' for side in ("top", "left", "bottom", "right"))
    return (f'<w:tbl><w:tblPr><w:tblW w:w="{sum(widths)}" w:type="dxa"/><w:tblLayout w:type="fixed"/>'
            f'<w:tblCellMar>{margins}</w:tblCellMar><w:tblLook w:val="0000"/></w:tblPr><w:tblGrid>{grid}</w:tblGrid>'
            f"<w:tr><w:trPr><w:cantSplit/></w:trPr>{tcs}</w:tr></w:tbl>")


def spread(total_mm, gap_mm, weights):
    """Column and gutter widths in twips for a row of cells sharing total_mm by weight."""
    unit = (total_mm - gap_mm * (len(weights) - 1)) / sum(weights)
    widths = []
    for i, weight in enumerate(weights):
        widths += [tw(unit * weight)] + ([tw(gap_mm)] if i + 1 < len(weights) else [])
    widths[-1] += tw(total_mm) - sum(widths)
    return widths


class Pictures:
    def __init__(self):
        self.files, self.count = [], 0

    def add(self, path, width_mm, alt, outline=None):
        self.count += 1
        rid, pid = f"rIdImage{self.count}", self.count
        self.files.append((rid, Path(path)))
        img = Image.open(path)
        cx, cy = round(width_mm * EMU), round(width_mm * img.height / img.width * EMU)
        line = f'<a:ln w="9525"><a:solidFill><a:srgbClr val="{outline}"/></a:solidFill></a:ln>' if outline else ""
        edge = 4763 if outline else 0
        alt = escape(alt)
        return (f'<w:r><w:drawing><wp:inline distT="0" distB="0" distL="0" distR="0"><wp:extent cx="{cx}" cy="{cy}"/>'
                f'<wp:effectExtent l="{edge}" t="{edge}" r="{edge}" b="{edge}"/><wp:docPr id="{pid}" name="Picture {pid}" descr="{alt}"/>'
                '<wp:cNvGraphicFramePr><a:graphicFrameLocks noChangeAspect="1"/></wp:cNvGraphicFramePr>'
                '<a:graphic><a:graphicData uri="http://schemas.openxmlformats.org/drawingml/2006/picture"><pic:pic>'
                f'<pic:nvPicPr><pic:cNvPr id="{pid}" name="Picture {pid}" descr="{alt}"/><pic:cNvPicPr/></pic:nvPicPr>'
                f'<pic:blipFill><a:blip r:embed="{rid}"/><a:stretch><a:fillRect/></a:stretch></pic:blipFill>'
                f'<pic:spPr><a:xfrm><a:off x="0" y="0"/><a:ext cx="{cx}" cy="{cy}"/></a:xfrm>'
                f'<a:prstGeom prst="rect"><a:avLst/></a:prstGeom>{line}</pic:spPr></pic:pic></a:graphicData></a:graphic>'
                "</wp:inline></w:drawing></w:r>")


def image_src(img):
    return (SOURCE.parent / img.attrs["src"]).resolve()


def column(node, pictures):
    """The blocks of one column of a .cols row, spaced as the stylesheet spaces them."""
    blocks = node.elements() if node.tag == "div" else [node]
    out = []
    for i, el in enumerate(blocks):
        last = i + 1 == len(blocks)
        if el.tag == "h2":
            out.append(para(runs_xml(inline(el)), "Heading2", before=tw(4.2) if i else 0))
        elif el.tag == "ol":
            items = [li for li in el.elements() if li.tag == "li"]
            first = 4 if "continued" in el.classes else 1
            for n, li in enumerate(items):
                gap = 0 if n + 1 == len(items) and last else tw(1.3)
                out.append(para(run(f"{first + n}", bold=True) + "<w:r><w:tab/></w:r>" + runs_xml(inline(li)),
                                "Step", after=gap, ind=tw(4.6)))
        elif el.tag == "p" and "note" in el.classes:
            note = para(runs_xml(inline(el)), after=0)
            pad = f'<w:shd w:val="clear" w:color="auto" w:fill="{CARD}"/><w:tcMar><w:top w:w="{tw(2.4)}" w:type="dxa"/>' \
                  f'<w:left w:w="{tw(2.8)}" w:type="dxa"/><w:bottom w:w="{tw(2.4)}" w:type="dxa"/><w:right w:w="{tw(2.8)}" w:type="dxa"/></w:tcMar>'
            out.append(spacer(2.8) + table([tw(COL)], [(note, pad)]) + spacer(0))
        elif el.tag == "p":
            out.append(para(runs_xml(inline(el)), after=0 if last else tw(1.6)))
        elif el.tag == "figure":
            img = next(c for c in el.walk() if c.tag == "img")
            caption = next(c for c in el.walk() if c.tag == "figcaption")
            out.append(para(pictures.add(image_src(img), COL, img.attrs.get("alt", "")), before=0, after=0, line=240, rule="auto"))
            out.append(para(runs_xml(inline(caption)), "Caption"))
    return "".join(out)


def kpis(node):
    tiles = [el for el in node.elements() if "kpi" in el.classes]
    widths = spread(COL * 2 + GAP, 6, [1, 1, 1, 1.18])
    border = f'<w:tcBorders><w:top w:val="single" w:sz="6" w:space="0" w:color="{ONYX}"/></w:tcBorders>' \
             f'<w:tcMar><w:top w:w="{tw(2.4)}" w:type="dxa"/></w:tcMar>'
    cells = []
    for i, tile in enumerate(tiles):
        parts = {el.attrs["class"]: el for el in tile.elements()}
        content = (para(runs_xml(inline(parts["kpi-value"])), "KPIValue") + para(runs_xml(inline(parts["kpi-caption"])), "KPICaption")
                   + para(runs_xml(inline(parts["kpi-base"])), "KPIBase"))
        cells.append((content, border))
        if i + 1 < len(tiles):
            cells.append(("", ""))
    return table(widths, cells)


def tiles(node, pictures):
    items = [el for el in node.elements() if "tile" in el.classes]
    widths = spread(COL * 2 + GAP, GAP, [1] * len(items))
    cells = []
    for i, tile in enumerate(items):
        img, h3, p = (next(c for c in tile.walk() if c.tag == t) for t in ("img", "h3", "p"))
        width = widths[2 * i] / TW - 0.3
        content = (para(pictures.add(image_src(img), width, img.attrs.get("alt", ""), outline="E3DECF"), before=0, after=0, line=240, rule="auto")
                   + para(runs_xml(inline(h3)), "TileTitle") + para(runs_xml(inline(p)), "TileText"))
        cells.append((content, ""))
        if i + 1 < len(items):
            cells.append(("", ""))
    return table(widths, cells)


def page_body(section, pictures):
    out = []
    for el in section.elements():
        if el.tag == "header" or "footer" in el.classes:
            continue
        if el.tag == "h1":
            out.append(spacer(8) + para(runs_xml(inline(el)), "Title"))
        elif el.tag == "p" and "dek" in el.classes:
            out.append(para(runs_xml(inline(el)), "Standfirst"))
        elif el.tag == "p" and "byline" in el.classes:
            out.append(para(runs_xml(inline(el)), "Byline"))
        elif el.tag == "h2":
            out.append(para(runs_xml(inline(el)), "Heading2", before=tw(5.2) if "block" in el.classes else None))
        elif "cols" in el.classes:
            gap = 5.2 if "block" in el.classes else 3.8 if "near" in el.classes else 0
            left, right = el.elements()
            out.append((spacer(gap) if gap else "") + table([tw(COL), tw(GAP), tw(COL)],
                                                            [(column(left, pictures), ""), ("", ""), (column(right, pictures), "")]))
        elif "kpis" in el.classes:
            out.append(kpis(el))
        elif "tiles" in el.classes:
            out.append(spacer(3.4) + tiles(el, pictures))
        elif el.tag == "p" and "sources" in el.classes:
            out.append(para(runs_xml(inline(el)), "Sources"))
        else:
            raise ValueError(f"no Word layout for <{el.tag} class={sorted(el.classes)}>")
    return "".join(out)


def footer_xml(section, page):
    left, right = (el for el in next(el for el in section.elements() if "footer" in el.classes).elements())
    number = f'<w:fldSimple w:instr=" PAGE "><w:r><w:t>{page}</w:t></w:r></w:fldSimple>'
    pages = '<w:fldSimple w:instr=" NUMPAGES "><w:r><w:t>2</w:t></w:r></w:fldSimple>'
    assert "".join(inline_text(right)).strip() == f"Page {page} of 2"
    return (f'<w:ftr {NS}><w:p><w:pPr><w:pStyle w:val="Footer"/></w:pPr>{run("".join(inline_text(left)).strip())}'
            f'<w:r><w:tab/></w:r>{run("Page ")}{number}{run(" of ")}{pages}</w:p></w:ftr>')


NS = ('xmlns:w="http://schemas.openxmlformats.org/wordprocessingml/2006/main" '
      'xmlns:r="http://schemas.openxmlformats.org/officeDocument/2006/relationships" '
      'xmlns:wp="http://schemas.openxmlformats.org/drawingml/2006/wordprocessingDrawing" '
      'xmlns:a="http://schemas.openxmlformats.org/drawingml/2006/main" '
      'xmlns:pic="http://schemas.openxmlformats.org/drawingml/2006/picture"')


def style(sid, name, size, color=INK, bold=False, line=None, before=0, after=0, keep=False, ind=None, extra=""):
    ppr = "<w:keepNext/>" if keep else ""
    ppr += extra
    ppr += f'<w:spacing w:before="{before}" w:after="{after}"' + (f' w:line="{line}" w:lineRule="exact"/>' if line else "/>")
    ppr += f'<w:ind w:left="{ind}" w:hanging="{ind}"/>' if ind else ""
    rpr = '<w:rFonts w:ascii="Arial" w:hAnsi="Arial" w:cs="Arial"/>' + ("<w:b/><w:bCs/>" if bold else "")
    rpr += f'<w:color w:val="{color}"/><w:sz w:val="{size}"/><w:szCs w:val="{size}"/>'
    return (f'<w:style w:type="paragraph" w:customStyle="1" w:styleId="{sid}"><w:name w:val="{name}"/><w:basedOn w:val="Normal"/>'
            f"<w:qFormat/><w:pPr>{ppr}</w:pPr><w:rPr>{rpr}</w:rPr></w:style>")


def styles_xml():
    """Arial at sizes close to the PDF's Inter (Arial sets a little wider, so body text is 8.5 pt), with the PDF's line spacing."""
    step_tabs = f'<w:tabs><w:tab w:val="left" w:pos="{tw(4.6)}"/></w:tabs>'
    rule = f'<w:pBdr><w:top w:val="single" w:sz="6" w:space="6" w:color="{RULE}"/></w:pBdr>'
    footer_tabs = f'<w:tabs><w:tab w:val="right" w:pos="{tw(COL * 2 + GAP)}"/></w:tabs>'
    return (f'<?xml version="1.0" encoding="UTF-8" standalone="yes"?><w:styles {NS}>'
            '<w:docDefaults><w:rPrDefault><w:rPr><w:rFonts w:ascii="Arial" w:hAnsi="Arial" w:eastAsia="Arial" w:cs="Arial"/>'
            f'<w:color w:val="{INK}"/><w:sz w:val="17"/><w:szCs w:val="17"/><w:lang w:val="en-US"/></w:rPr></w:rPrDefault>'
            '<w:pPrDefault><w:pPr><w:spacing w:after="0" w:line="240" w:lineRule="auto"/></w:pPr></w:pPrDefault></w:docDefaults>'
            '<w:style w:type="paragraph" w:default="1" w:styleId="Normal"><w:name w:val="Normal"/><w:qFormat/>'
            f'<w:pPr><w:spacing w:after="0" w:line="{round(8.6 * 1.48 * 20)}" w:lineRule="exact"/></w:pPr>'
            f'<w:rPr><w:rFonts w:ascii="Arial" w:hAnsi="Arial" w:cs="Arial"/><w:color w:val="{INK}"/><w:sz w:val="17"/><w:szCs w:val="17"/></w:rPr></w:style>'
            '<w:style w:type="table" w:default="1" w:styleId="TableNormal"><w:name w:val="Normal Table"/><w:uiPriority w:val="99"/>'
            '<w:semiHidden/><w:unhideWhenUsed/><w:tblPr><w:tblInd w:w="0" w:type="dxa"/><w:tblCellMar><w:top w:w="0" w:type="dxa"/>'
            '<w:left w:w="0" w:type="dxa"/><w:bottom w:w="0" w:type="dxa"/><w:right w:w="0" w:type="dxa"/></w:tblCellMar></w:tblPr></w:style>'
            + style("Title", "Title", 44, ONYX, bold=True, line=round(22 * 1.15 * 20))
            + style("Standfirst", "Standfirst", 21, line=round(10.2 * 1.45 * 20), before=tw(2.4))
            + style("Byline", "Byline", 16, MUTED, line=round(7.8 * 1.48 * 20), before=tw(2.4))
            + style("Heading2", "Section heading", 21, ONYX, bold=True, line=round(10.5 * 1.3 * 20), after=tw(1.4), keep=True)
            + style("Step", "Numbered step", 17, line=round(8.6 * 1.48 * 20), ind=tw(4.6), extra=step_tabs)
            + style("KPIValue", "Key figure", 34, ONYX, bold=True, line=round(19 * 1.1 * 20))
            + style("KPICaption", "Key figure caption", 16, line=round(7.8 * 1.38 * 20), before=tw(1.3))
            + style("KPIBase", "Key figure base", 15, MUTED, line=round(7 * 1.35 * 20), before=tw(1.1))
            + style("Caption", "Chart caption", 15, MUTED, line=round(7 * 1.4 * 20), before=tw(1.5))
            + style("TileTitle", "Report page name", 17, ONYX, bold=True, line=round(8 * 1.3 * 20), before=tw(1.9))
            + style("TileText", "Report page text", 15, line=round(7.4 * 1.42 * 20), before=tw(0.6))
            + style("Sources", "Sources", 14, MUTED, line=round(6.8 * 1.45 * 20), before=tw(5), extra=rule)
            + style("Footer", "Footer", 15, MUTED, line=round(7 * 1.48 * 20), extra=footer_tabs)
            + "</w:styles>")


def write_docx():
    tree = Tree(SOURCE.read_text(encoding="utf-8")).root
    pages = [el for el in tree.walk() if el.tag == "section" and "page" in el.classes]
    assert len(pages) == 2
    pictures = Pictures()

    def page(n, start, top):
        margins = f'<w:pgMar w:top="{tw(top)}" w:right="{tw(18)}" w:bottom="{tw(16)}" w:left="{tw(18)}" w:header="{tw(4)}" w:footer="{tw(9)}" w:gutter="0"/>'
        return (f'<w:sectPr><w:headerReference w:type="default" r:id="rIdHeader{n}"/><w:footerReference w:type="default" r:id="rIdFooter{n}"/>'
                f'{start}<w:pgSz w:w="11906" w:h="16838"/>{margins}</w:sectPr>')

    # each page is its own section: page 1 carries the masthead header, and the break holds in every Word reader
    body = (page_body(pages[0], pictures) + para(before=0, after=0, line=20, size=2, section=page(1, "", 15))
            + page_body(pages[1], pictures))
    section = page(2, '<w:type w:val="nextPage"/>', 13)
    document = f'<?xml version="1.0" encoding="UTF-8" standalone="yes"?><w:document {NS}><w:body>{body}{section}</w:body></w:document>'

    masthead = cut_masthead()
    band = (f'<w:r><w:drawing><wp:anchor distT="0" distB="0" distL="0" distR="0" simplePos="0" relativeHeight="0" behindDoc="1" '
            'locked="1" layoutInCell="1" allowOverlap="1"><wp:simplePos x="0" y="0"/><wp:positionH relativeFrom="page"><wp:posOffset>0</wp:posOffset>'
            f'</wp:positionH><wp:positionV relativeFrom="page"><wp:posOffset>0</wp:posOffset></wp:positionV><wp:extent cx="{210 * EMU}" cy="{15 * EMU}"/>'
            '<wp:effectExtent l="0" t="0" r="0" b="0"/><wp:wrapNone/><wp:docPr id="900" name="Masthead" descr="Parakeet Risk. Project summary, November 2026"/>'
            '<wp:cNvGraphicFramePr/><a:graphic><a:graphicData uri="http://schemas.openxmlformats.org/drawingml/2006/picture"><pic:pic>'
            '<pic:nvPicPr><pic:cNvPr id="900" name="Masthead"/><pic:cNvPicPr/></pic:nvPicPr><pic:blipFill><a:blip r:embed="rIdMasthead"/>'
            f'<a:stretch><a:fillRect/></a:stretch></pic:blipFill><pic:spPr><a:xfrm><a:off x="0" y="0"/><a:ext cx="{210 * EMU}" cy="{15 * EMU}"/></a:xfrm>'
            '<a:prstGeom prst="rect"><a:avLst/></a:prstGeom></pic:spPr></pic:pic></a:graphicData></a:graphic></wp:anchor></w:drawing></w:r>')
    header_first = f'<w:hdr {NS}>{para(band, before=0, after=0, line=20, size=2)}</w:hdr>'
    header_default = f'<w:hdr {NS}>{para(before=0, after=0, line=20, size=2)}</w:hdr>'

    rel = "http://schemas.openxmlformats.org/officeDocument/2006/relationships"
    doc_rels = [("rIdStyles", "styles", "styles.xml"), ("rIdSettings", "settings", "settings.xml"), ("rIdFonts", "fontTable", "fontTable.xml"),
                ("rIdHeader1", "header", "header1.xml"), ("rIdHeader2", "header", "header2.xml"),
                ("rIdFooter1", "footer", "footer1.xml"), ("rIdFooter2", "footer", "footer2.xml")]
    doc_rels += [(rid, "image", f"media/{path.name}") for rid, path in pictures.files]
    rels_xml = lambda rels: ('<?xml version="1.0" encoding="UTF-8" standalone="yes"?><Relationships xmlns="http://schemas.openxmlformats.org/package/2006/relationships">'
                             + "".join(f'<Relationship Id="{i}" Type="{rel}/{t}" Target="{target}"/>' for i, t, target in rels) + "</Relationships>")
    now = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
    ct = "application/vnd.openxmlformats-officedocument.wordprocessingml"
    parts = {
        "[Content_Types].xml": ('<?xml version="1.0" encoding="UTF-8" standalone="yes"?><Types xmlns="http://schemas.openxmlformats.org/package/2006/content-types">'
                                '<Default Extension="rels" ContentType="application/vnd.openxmlformats-package.relationships+xml"/>'
                                '<Default Extension="xml" ContentType="application/xml"/><Default Extension="png" ContentType="image/png"/>'
                                f'<Override PartName="/word/document.xml" ContentType="{ct}.document.main+xml"/>'
                                f'<Override PartName="/word/styles.xml" ContentType="{ct}.styles+xml"/>'
                                f'<Override PartName="/word/settings.xml" ContentType="{ct}.settings+xml"/>'
                                f'<Override PartName="/word/fontTable.xml" ContentType="{ct}.fontTable+xml"/>'
                                + "".join(f'<Override PartName="/word/{p}{n}.xml" ContentType="{ct}.{p}+xml"/>' for p in ("header", "footer") for n in (1, 2))
                                + '<Override PartName="/docProps/core.xml" ContentType="application/vnd.openxmlformats-package.core-properties+xml"/></Types>'),
        "_rels/.rels": ('<?xml version="1.0" encoding="UTF-8" standalone="yes"?><Relationships xmlns="http://schemas.openxmlformats.org/package/2006/relationships">'
                        f'<Relationship Id="rIdDocument" Type="{rel}/officeDocument" Target="word/document.xml"/>'
                        '<Relationship Id="rIdCore" Type="http://schemas.openxmlformats.org/package/2006/relationships/metadata/core-properties" Target="docProps/core.xml"/>'
                        "</Relationships>"),
        "docProps/core.xml": ('<?xml version="1.0" encoding="UTF-8" standalone="yes"?><cp:coreProperties '
                              'xmlns:cp="http://schemas.openxmlformats.org/package/2006/metadata/core-properties" xmlns:dc="http://purl.org/dc/elements/1.1/" '
                              'xmlns:dcterms="http://purl.org/dc/terms/" xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance">'
                              f"<dc:title>{TITLE}</dc:title><dc:subject>{SUBJECT}</dc:subject><dc:creator>{AUTHOR}</dc:creator>"
                              f'<cp:lastModifiedBy>{AUTHOR}</cp:lastModifiedBy><dcterms:created xsi:type="dcterms:W3CDTF">{now}</dcterms:created>'
                              f'<dcterms:modified xsi:type="dcterms:W3CDTF">{now}</dcterms:modified></cp:coreProperties>'),
        "word/document.xml": document,
        "word/styles.xml": styles_xml(),
        "word/settings.xml": (f'<?xml version="1.0" encoding="UTF-8" standalone="yes"?><w:settings {NS}><w:zoom w:percent="100"/>'
                              '<w:defaultTabStop w:val="720"/><w:characterSpacingControl w:val="doNotCompress"/><w:compat>'
                              '<w:compatSetting w:name="compatibilityMode" w:uri="http://schemas.microsoft.com/office/word" w:val="15"/></w:compat></w:settings>'),
        "word/fontTable.xml": (f'<?xml version="1.0" encoding="UTF-8" standalone="yes"?><w:fonts {NS}><w:font w:name="Arial">'
                               '<w:panose1 w:val="020B0604020202020204"/><w:charset w:val="00"/><w:family w:val="swiss"/><w:pitch w:val="variable"/></w:font></w:fonts>'),
        "word/header1.xml": f'<?xml version="1.0" encoding="UTF-8" standalone="yes"?>{header_first}',
        "word/header2.xml": f'<?xml version="1.0" encoding="UTF-8" standalone="yes"?>{header_default}',
        "word/footer1.xml": f'<?xml version="1.0" encoding="UTF-8" standalone="yes"?>{footer_xml(pages[0], 1)}',
        "word/footer2.xml": f'<?xml version="1.0" encoding="UTF-8" standalone="yes"?>{footer_xml(pages[1], 2)}',
        "word/_rels/document.xml.rels": rels_xml(doc_rels),
        "word/_rels/header1.xml.rels": rels_xml([("rIdMasthead", "image", f"media/{masthead.name}")]),
    }
    for name, xml in parts.items():
        minidom.parseString(xml.encode("utf-8"))
    with zipfile.ZipFile(DOCX, "w", zipfile.ZIP_DEFLATED) as z:
        for name, xml in parts.items():
            z.writestr(name, xml)
        for path in [masthead] + [p for _, p in pictures.files]:
            z.write(path, f"word/media/{path.name}")


def main():
    draw_charts()
    room = check_fit()
    print_pdf()
    write_docx()
    print(f"wrote {PDF} (room above the footers: {room[0]} and {room[1]} mm) and {DOCX}")


if __name__ == "__main__":
    main()
