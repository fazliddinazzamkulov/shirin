"""Shirin Nueva: Miama Nueva (Linus Romer, SIL OFL 1.1) asosida.
Ўзгаришлар: ұ ва ғ даги чизиқча аниқ ва каттароқ қилиб қайта чизилди (у/г билан адашмаслиги учун),
шрифт OFL талабига кўра қайта номланди (Reserved Font Name "Miama Nueva").

Ишлатиш: python3 -I build_nueva.py <MiamaNueva.otf> <chiqish.otf>
Керак:   pip install fonttools brotli skia-pathops
"""
import sys, pathops
from fontTools.ttLib import TTFont
from fontTools.pens.t2CharStringPen import T2CharStringPen

src, out = sys.argv[1], sys.argv[2]
f = TTFont(src)
cm = f.getBestCmap(); gs = f.getGlyphSet()
cff = f["CFF "].cff; top = cff.topDictIndex[0]; cs = top.CharStrings

def path_of(gn):
    p = pathops.Path(); gs[gn].draw(p.getPen(glyphSet=gs)); return p

import math

def scan(path, y):
    """y баландликдаги горизонтал кесимда контур ичидаги x оралиқлари."""
    x0, _, x1, _ = path.bounds; out = []; inside = False; a = None; x = x0 - 2
    while x <= x1 + 2:
        c = path.contains((x, y))
        if c and not inside: a, inside = x, True
        elif not c and inside: out.append((a, x)); inside = False
        x += 1
    return out

def lens_bar(cx, cy, w, thick, tilt, n=40):
    """Каллиграфик чизиқча: учлари ингичка, ўртаси қалин, бироз қия."""
    top, bot = [], []
    for i in range(n + 1):
        t = i / n; x = cx - w / 2 + w * t; y = cy - tilt / 2 + tilt * t
        h = (6 + (thick - 6) * math.sin(math.pi * t)) / 2
        top.append((x, y + h)); bot.append((x, y - h))
    p = pathops.Path(); pts = top + bot[::-1]
    p.moveTo(*pts[0]); [p.lineTo(*q) for q in pts[1:]]; p.close(); return p

def add_bar(target, base, y, w, thick, tilt, dx=0):
    """target = base (чизиқчасиз) + янги аниқ чизиқча; y баландликдаги энг қалин штрих марказида."""
    gt, gb = cm[ord(target)], cm[ord(base)]
    pb = path_of(gb)
    a, b = max(scan(pb, y), key=lambda i: i[1] - i[0])
    cx = (a + b) / 2 + dx
    new = pathops.op(pb, lens_bar(cx, y, w, thick, tilt), pathops.PathOp.UNION, fix_winding=True)
    pen = T2CharStringPen(f["hmtx"][gt][0], gs); new.draw(pen)
    old = cs[gt]; cs[gt] = pen.getCharString(private=old.private, globalSubrs=old.globalSubrs)
    return round(cx), y

info = {"ұ": add_bar("ұ", "ү", y=-75, w=440, thick=58, tilt=18),
        "ғ": add_bar("ғ", "г", y=150, w=230, thick=36, tilt=12)}

# --- номлар (OFL: Reserved Font Name "Miama Nueva" ишлатилмайди) ---
fam, ps = "Shirin Nueva", "ShirinNueva-Regular"
copy = ("Copyright (c) 2014, Linus Romer, with Reserved Font Name Miama Nueva. "
        "Copyright 2026 Shirin (shirin.day): modified version (stronger bars in U+04B1 and U+0493), renamed Shirin Nueva.")
name = f["name"]
for nid in (1, 3, 4, 6, 16, 17, 21, 22):
    name.removeNames(nameID=nid)
for nid, val in {0: copy, 1: fam, 2: "Regular", 3: f"{fam} Regular 1.000", 4: f"{fam} Regular", 6: ps,
                 13: "This Font Software is licensed under the SIL Open Font License, Version 1.1. This license is available with a FAQ at: https://openfontlicense.org",
                 14: "https://openfontlicense.org"}.items():
    name.setName(val, nid, 3, 1, 0x409); name.setName(val, nid, 1, 0, 0)
cff.fontNames = [ps]
top.FamilyName, top.FullName, top.Notice = fam, f"{fam} Regular", copy[:250]
if hasattr(top, "Copyright"): top.Copyright = copy[:250]
f.save(out)
print("bars at (x, y):", info, "->", out)
