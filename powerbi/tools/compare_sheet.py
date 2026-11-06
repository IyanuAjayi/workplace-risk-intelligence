"""
Puts design mockups side by side on one cream sheet so they can be compared at a glance. Each page is scaled to the
same width and labelled underneath. For judging detail, open the full-size PNGs.

Usage: python3 powerbi/tools/compare_sheet.py out.png "Label A=path/a.png" "Label B=path/b.png" "Label C=path/c.png"
"""
import sys

from PIL import Image, ImageDraw, ImageFont

NEST, INK, MUTED = (239, 236, 223), (27, 27, 25), (102, 101, 95)
FONT = "/System/Library/Fonts/HelveticaNeue.ttc"


def main():
    out, items = sys.argv[1], [a.split("=", 1) for a in sys.argv[2:]]
    gap, margin, width = 32, 48, 1200
    pages = [Image.open(p).convert("RGB") for _, p in items]
    thumbs = [im.resize((width, round(im.height * width / im.width)), Image.LANCZOS) for im in pages]
    title, label = ImageFont.truetype(FONT, 30), ImageFont.truetype(FONT, 26)
    h = max(t.height for t in thumbs)
    sheet = Image.new("RGB", (margin * 2 + width * len(thumbs) + gap * (len(thumbs) - 1), margin + 56 + h + 80), NEST)
    draw = ImageDraw.Draw(sheet)
    draw.text((margin, margin - 8), "Executive Intelligence: the three versions side by side", font=title, fill=INK)
    for i, (t, (name, _)) in enumerate(zip(thumbs, items)):
        x = margin + i * (width + gap)
        sheet.paste(t, (x, margin + 56))
        draw.rectangle([x - 1, margin + 55, x + width, margin + 56 + t.height], outline=(214, 209, 194))
        draw.text((x, margin + 56 + h + 24), name, font=label, fill=MUTED)
    sheet.save(out)
    print(out, sheet.size)


if __name__ == "__main__":
    main()
