"""Shirin Script: Great Vibes + ўзбек ва қозоқ ҳарфлари.

Манба: Great Vibes (SIL OFL 1.1), Google Fonts'дан тўлиқ TTF:
  curl -sA curl/8 "https://fonts.googleapis.com/css2?family=Great+Vibes" | grep -o "https://[^)]*ttf" | xargs curl -so GreatVibes-Regular.ttf
Керак: pip install fonttools brotli skia-pathops
Ишлатиш:  python3 -I build.py   → ShirinScript-Regular.ttf ва preview_glyphs.html (текшириш учун)
Сайт учун: python3 -m fontTools.subset ShirinScript-Regular.ttf \
  --unicodes="U+0020-007E,U+00A0-00FF,U+0400-04FF,U+2010-2027,U+2030-203A" \
  --layout-features='*' --no-hinting --flavor=woff2 --output-file=../../assets/fonts/ShirinScript-Regular.woff2
"""
import math
import pathops
from fontTools.ttLib import TTFont
from fontTools.ttLib.removeOverlaps import skPathFromGlyph, ttfGlyphFromSkPath
from fontTools.pens.svgPathPen import SVGPathPen

SRC, OUT = "GreatVibes-Regular.ttf", "ShirinScript-Regular.ttf"
f = TTFont(SRC)
cmap = f.getBestCmap()
gs = f.getGlyphSet()
SLANT = 0.27  # шрифтнинг қиялиги: пастга 1 бирлик — чапга ~0.27

def gname(ch):
    return cmap[ord(ch)]

def base_path(ch):
    return skPathFromGlyph(gname(ch), gs)

def bounds(path):
    return path.bounds  # (xMin, yMin, xMax, yMax)

def points_of(path):
    pts = []
    for verb, p in path:
        pts.extend(p)
    return pts

def lowest_point(path, xmin, xmax):
    """Берилган x оралиғидаги энг пастки нуқта (контур нуқталари бўйича)."""
    cand = [(x, y) for x, y in points_of(path) if xmin <= x <= xmax]
    return min(cand, key=lambda p: p[1])

def scan(path, y, step=1):
    """y баландликдаги горизонтал кесим: контур ичидаги x оралиқлари."""
    xs = []
    b = bounds(path)
    inside = False; start = None
    x = b[0] - 2
    while x <= b[2] + 2:
        c = path.contains((x, y))
        if c and not inside:
            start = x; inside = True
        elif not c and inside:
            xs.append((start, x)); inside = False
        x += step
    return xs

def stroke(center, w0, w1, n=48, curve=1.0):
    """Марказий чизиқ (кубик Безье, 4 нуқта) бўйича ингичкалашиб борувчи штрих контури."""
    P0, P1, P2, P3 = center
    def bez(t):
        u = 1 - t
        return (u**3*P0[0] + 3*u*u*t*P1[0] + 3*u*t*t*P2[0] + t**3*P3[0],
                u**3*P0[1] + 3*u*u*t*P1[1] + 3*u*t*t*P2[1] + t**3*P3[1])
    left, right = [], []
    for i in range(n + 1):
        t = i / n
        x, y = bez(t)
        x2, y2 = bez(min(1, t + 1e-3)); x1, y1 = bez(max(0, t - 1e-3))
        dx, dy = x2 - x1, y2 - y1; L = math.hypot(dx, dy) or 1
        nx, ny = -dy / L, dx / L
        w = (w1 + (w0 - w1) * (1 - t) ** curve) / 2
        left.append((x + nx * w, y + ny * w)); right.append((x - nx * w, y - ny * w))
    # учи юмалоқ бўлиши учун охирида кичик ярим доира
    xe, ye = bez(1); tip = []
    for k in range(1, 8):
        a = math.pi * k / 8
        dx, dy = right[-1][0] - xe, right[-1][1] - ye
        tip.append((xe + dx * math.cos(a) - dy * math.sin(a), ye + dx * math.sin(a) + dy * math.cos(a)))
    poly = left + list(reversed(tip)) + list(reversed(right))
    p = pathops.Path()
    p.moveTo(*poly[0])
    for q in poly[1:]:
        p.lineTo(*q)
    p.close()
    return p

def union(*paths):
    out = paths[0]
    for q in paths[1:]:
        out = pathops.op(out, q, pathops.PathOp.UNION, fix_winding=True)
    return out

def shifted(path, dx, dy):
    q = pathops.Path()
    pen = q.getPen()
    class T:
        def moveTo(s, p): pen.moveTo((p[0]+dx, p[1]+dy))
        def lineTo(s, p): pen.lineTo((p[0]+dx, p[1]+dy))
        def qCurveTo(s, *ps): pen.qCurveTo(*[(a+dx, b+dy) for a, b in ps])
        def curveTo(s, *ps): pen.curveTo(*[(a+dx, b+dy) for a, b in ps])
        def closePath(s): pen.closePath()
        def endPath(s): pen.endPath()
    path.draw(T())
    return q

# ---------- элементлар ----------
def hook(anchor, size, w0):
    """Қ, Ң, Ҳ учун ингичка каллиграфик илмоқ: пастга тушиб, чапга буралади."""
    x, y = anchor
    s = size
    return stroke([(x, y + 0.12*s), (x + 0.02*s, y - 0.45*s), (x - 0.10*s, y - 0.92*s), (x - 0.48*s, y - 0.98*s)], w0, 4, curve=1.3)

def stem(anchor, length, w0):
    """Ү, ү учун тўғри, қия, ингичкалашиб борувчи оёқча."""
    x, y = anchor
    return stroke([(x, y + 25), (x - SLANT*length*0.33, y - length*0.33), (x - SLANT*length*0.66, y - length*0.66), (x - SLANT*length, y - length)], w0, 5, curve=1.1)

BAR = skPathFromGlyph("uni0335", gs)
bb = bounds(BAR); BAR_C = ((bb[0]+bb[2])/2, (bb[1]+bb[3])/2); BAR_W = bb[2]-bb[0]

def bar_at(cx, cy, scale_note=None):
    return shifted(BAR, cx - BAR_C[0], cy - BAR_C[1])

def stem_center(path, y):
    """y баландликда энг ўнгдаги эмас, энг қалин вертикал штрихнинг ўртаси."""
    iv = scan(path, y)
    iv = [i for i in iv if i[1]-i[0] >= 8]
    a, b = max(iv, key=lambda i: i[1]-i[0])
    return (a + b) / 2

# ---------- янги ҳарфлар ----------
new = {}   # unicode -> (path, advance)
adv = lambda ch: f["hmtx"][gname(ch)][0]

# Қ қ Ң ң Ҳ ҳ — илмоқ ўнг оёқнинг энг пастки нуқтасидан
spec = {  # ch: (base, x-оралиқ ўнг оёқ учун, илмоқ ўлчами, қалинлик)
    "Қ": ("К", (1000, 1250), 210, 34),
    "қ": ("к", (230, 400), 175, 26),
    "Ң": ("Н", (1150, 1350), 210, 34),
    "ң": ("н", (150, 300), 175, 26),
    "Ҳ": ("Х", (560, 760), 210, 34),
    "ҳ": ("х", (150, 300), 175, 26),
}
anchors = {}
for cp, (base, xr, size, w) in spec.items():
    p = base_path(base)
    ax, ay = lowest_point(p, *xr)
    anchors[cp] = (ax, ay)
    new[cp] = (union(p, hook((ax, ay), size, w)), adv(base))

# Ғ ғ — Г/г устига чизиқча
for cp, base, yfrac in [("Ғ", "Г", 0.42), ("ғ", "г", 0.48)]:
    p = base_path(base); b = bounds(p)
    y = b[1] + (b[3] - b[1]) * yfrac
    x = stem_center(p, y)
    new[cp] = (union(p, bar_at(x, y)), adv(base))
    anchors[cp] = (x, y)

# Ү ү — V/v + тўғри оёқча; Ұ ұ — улар + чизиқча
for cp, base, xr, length, w in [("Ү", "V", (300, 800), 300, 50), ("ү", "v", (-50, 200), 290, 38)]:
    p = base_path(base)
    ax, ay = lowest_point(p, *xr)
    leg = stem((ax, ay), length, w)
    pu = union(p, leg)
    new[cp] = (pu, adv(base))
    anchors[cp] = (ax, ay)
    # Ұ / ұ: чизиқча оёқчанинг юқори учдан бирида
    by = ay - length * 0.32
    bx = ax - SLANT * length * 0.32
    new[{"Ү": "Ұ", "ү": "ұ"}[cp]] = (union(pu, bar_at(bx, by)), adv(base))

# ---------- шрифтга қўшиш ----------
new = {ord(k): v for k, v in new.items()}
anchors = {ord(k): v for k, v in anchors.items()}
order = f.getGlyphOrder()
glyf, hmtx = f["glyf"], f["hmtx"]
for cp, (path, a) in new.items():
    name = "uni%04X" % cp
    g = ttfGlyphFromSkPath(path)
    glyf.glyphs[name] = g
    order.append(name)
    hmtx.metrics[name] = (a, g.xMin if hasattr(g, "xMin") else 0)
f.setGlyphOrder(order)
glyf.glyphOrder = order

# Тайёр шакллар: Ә ә = Ə ə, Ө ө = Ɵ ɵ, Һ һ = h
alias = {0x04D8: gname("Ə"), 0x04D9: gname("ə"), 0x04E8: gname("Ɵ"), 0x04E9: gname("ɵ"),
         0x04BA: gname("h"), 0x04BB: gname("h")}
for t in f["cmap"].tables:
    if t.isUnicode():
        for cp in new:
            t.cmap[cp] = "uni%04X" % cp
        for cp, g in alias.items():
            t.cmap[cp] = g

# ---------- номлар ва лицензия ----------
name = f["name"]
copy = ("Copyright 2010 The Great Vibes Pro Project Authors (https://github.com/googlefonts/great-vibes). "
        "Copyright 2026 Shirin (shirin.day): Uzbek and Kazakh Cyrillic letters added.")
for rec in list(name.names):
    if rec.nameID in (1, 3, 4, 6, 16, 17, 21, 22):
        name.removeNames(nameID=rec.nameID)
for nid, val in {0: copy, 1: "Shirin Script", 2: "Regular", 3: "Shirin Script Regular 1.000", 4: "Shirin Script Regular",
                 6: "ShirinScript-Regular",
                 13: "This Font Software is licensed under the SIL Open Font License, Version 1.1. This license is available with a FAQ at: https://openfontlicense.org",
                 14: "https://openfontlicense.org"}.items():
    name.setName(val, nid, 3, 1, 0x409)
    name.setName(val, nid, 1, 0, 0)
f["head"].fontRevision = 1.0
f.save(OUT)

# ---------- текшириш учун SVG ----------
g2 = TTFont(OUT); gs2 = g2.getGlyphSet(); cm2 = g2.getBestCmap()
def svg(ch):
    gn = cm2[ord(ch)]; pen = SVGPathPen(gs2); gs2[gn].draw(pen); a = g2["hmtx"][gn][0]
    x0, x1, y0, y1 = -250, max(a, 600) + 350, -480, 950
    grid = "".join(f'<line x1="{x0}" y1="{y}" x2="{x1}" y2="{y}" stroke="{"#f55" if y == 0 else "#e5e5e5"}" stroke-width="3"/>' for y in range(-400, y1, 100))
    return f'<figure><figcaption>{ch}</figcaption><svg viewBox="{x0} {-y1} {x1-x0} {y1-y0}" width="{(x1-x0)*0.3:.0f}"><g transform="scale(1,-1)">{grid}<path d="{pen.getCommands()}" fill="#2a1450"/></g></svg></figure>'
html = '<meta charset="utf-8"><style>body{margin:10px;font:18px sans-serif;display:flex;flex-wrap:wrap;gap:4px}figure{margin:0;border:1px solid #ddd}</style>'
html += "".join(svg(c) for c in "ҚқҢңҲҳҒғҮүҰұӘәӨөҺһ")
open("preview_glyphs.html", "w").write(html)
print("anchors:", {chr(k): tuple(round(v) for v in a) for k, a in anchors.items()})
print("saved", OUT, "glyphs:", len(g2.getGlyphOrder()))
