"""
Checks that an ordered set of risk-state colours stays distinguishable, including for colour-blind readers.

For each colour: CIELAB lightness and WCAG contrast against the page background. For each neighbouring pair:
CIEDE2000 colour difference in normal vision and under simulated protanopia, deuteranopia and tritanopia
(Machado, Oliveira and Fernandes 2009, full severity, applied in linear RGB).

Rule of thumb used for PASS: lightness moves the same way at every step, neighbours differ by at least 10 in normal
vision and at least 6 under every simulation. A colour under 3:1 contrast with the background needs a border or label.

Usage: python3 powerbi/tools/check_palette.py --bg "#EFECDF" "#ABC3A3" "#DFC38B" "#C98369"
"""
import argparse
import math

CVD = {
    "protanopia": ((0.152286, 1.052583, -0.204868), (0.114503, 0.786281, 0.099216), (-0.003882, -0.048116, 1.051998)),
    "deuteranopia": ((0.367322, 0.860646, -0.227968), (0.280085, 0.672501, 0.047413), (-0.011820, 0.042940, 0.968881)),
    "tritanopia": ((1.255528, -0.076749, -0.178779), (-0.078411, 0.930809, 0.147602), (0.004733, 0.691367, 0.303900)),
}


def linear(hex_colour):
    h = hex_colour.lstrip("#")
    rgb = [int(h[i:i + 2], 16) / 255 for i in (0, 2, 4)]
    return [c / 12.92 if c <= 0.04045 else ((c + 0.055) / 1.055) ** 2.4 for c in rgb]


def lab(lin):
    r, g, b = lin
    x = (0.4124564 * r + 0.3575761 * g + 0.1804375 * b) / 0.95047
    y = 0.2126729 * r + 0.7151522 * g + 0.0721750 * b
    z = (0.0193339 * r + 0.1191920 * g + 0.9503041 * b) / 1.08883
    f = [t ** (1 / 3) if t > (6 / 29) ** 3 else t / (3 * (6 / 29) ** 2) + 4 / 29 for t in (x, y, z)]
    return 116 * f[1] - 16, 500 * (f[0] - f[1]), 200 * (f[1] - f[2])


def simulate(lin, matrix):
    return [min(1, max(0, sum(m * c for m, c in zip(row, lin)))) for row in matrix]


def de2000(lab1, lab2):
    l1, a1, b1 = lab1
    l2, a2, b2 = lab2
    cbar = (math.hypot(a1, b1) + math.hypot(a2, b2)) / 2
    g = 0.5 * (1 - math.sqrt(cbar ** 7 / (cbar ** 7 + 25 ** 7)))
    a1p, a2p = (1 + g) * a1, (1 + g) * a2
    c1p, c2p = math.hypot(a1p, b1), math.hypot(a2p, b2)
    h1p = math.degrees(math.atan2(b1, a1p)) % 360 if c1p else 0
    h2p = math.degrees(math.atan2(b2, a2p)) % 360 if c2p else 0
    dlp, dcp = l2 - l1, c2p - c1p
    dh = h2p - h1p
    if c1p * c2p == 0:
        dh = 0
    elif dh > 180:
        dh -= 360
    elif dh < -180:
        dh += 360
    dhp = 2 * math.sqrt(c1p * c2p) * math.sin(math.radians(dh / 2))
    lbar, cbarp = (l1 + l2) / 2, (c1p + c2p) / 2
    if c1p * c2p == 0:
        hbar = h1p + h2p
    elif abs(h1p - h2p) <= 180:
        hbar = (h1p + h2p) / 2
    else:
        hbar = (h1p + h2p + 360) / 2 if h1p + h2p < 360 else (h1p + h2p - 360) / 2
    t = (1 - 0.17 * math.cos(math.radians(hbar - 30)) + 0.24 * math.cos(math.radians(2 * hbar))
         + 0.32 * math.cos(math.radians(3 * hbar + 6)) - 0.20 * math.cos(math.radians(4 * hbar - 63)))
    dtheta = 30 * math.exp(-(((hbar - 275) / 25) ** 2))
    rc = 2 * math.sqrt(cbarp ** 7 / (cbarp ** 7 + 25 ** 7))
    sl = 1 + 0.015 * (lbar - 50) ** 2 / math.sqrt(20 + (lbar - 50) ** 2)
    sc, sh = 1 + 0.045 * cbarp, 1 + 0.015 * cbarp * t
    rt = -math.sin(math.radians(2 * dtheta)) * rc
    return math.sqrt((dlp / sl) ** 2 + (dcp / sc) ** 2 + (dhp / sh) ** 2 + rt * (dcp / sc) * (dhp / sh))


def contrast(hex1, hex2):
    y1, y2 = (0.2126 * r + 0.7152 * g + 0.0722 * b for r, g, b in (linear(hex1), linear(hex2)))
    return (max(y1, y2) + 0.05) / (min(y1, y2) + 0.05)


def main():
    p = argparse.ArgumentParser()
    p.add_argument("colours", nargs="+", help="risk states in order, lowest to highest")
    p.add_argument("--bg", default="#FFFFFF", help="page or card background")
    args = p.parse_args()
    cols = args.colours
    lin = [linear(c) for c in cols]
    print(f"{'colour':<9} {'L*':>5} {'contrast vs ' + args.bg:>20}")
    lightness = []
    for c, li in zip(cols, lin):
        lightness.append(lab(li)[0])
        print(f"{c:<9} {lightness[-1]:5.1f} {contrast(c, args.bg):19.2f}:1")
    steps = [b - a for a, b in zip(lightness, lightness[1:])]
    ordered = all(s > 0 for s in steps) or all(s < 0 for s in steps)
    views = {"normal": None, **CVD}
    worst = {}
    print(f"\n{'pair':<19}" + "".join(f"{v:>14}" for v in views))
    for i in range(len(cols) - 1):
        row = []
        for v, m in views.items():
            a, b = (lin[i], lin[i + 1]) if m is None else (simulate(lin[i], m), simulate(lin[i + 1], m))
            d = de2000(lab(a), lab(b))
            worst[v] = min(worst.get(v, math.inf), d)
            row.append(d)
        print(f"{cols[i] + '>' + cols[i + 1]:<19}" + "".join(f"{d:14.1f}" for d in row))
    ok = ordered and worst["normal"] >= 10 and all(worst[v] >= 6 for v in CVD)
    print(f"\nlightness ordered: {ordered}; smallest neighbour difference: "
          + ", ".join(f"{v} {d:.1f}" for v, d in worst.items()))
    print("PASS" if ok else "WARN: neighbours too close or lightness not ordered")


if __name__ == "__main__":
    main()
