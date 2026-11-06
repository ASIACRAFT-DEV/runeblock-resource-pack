#!/usr/bin/env python3
"""Mockup HUD art set (M0 "art check" of docs/spec/HUD_mockup_build_plan_2026-11-05.md, indigo133's rainy mockup).

Draws every element of the mockup HUD as a separate sprite at native GUI size (1 GUI px = 1 texture px, the size the
HUD is drawn at GUI scale 1), into art/mockup-hud/. NOT wired into the pack: M1-M4 move the pieces they use into
pack/ (hotbar sprites) and betterhud/assets/ (everything BetterHud draws).

Also writes art/mockup-hud/layout.json: where each piece sits, in GUI px from its anchor
(bottom = bottom centre of the screen, top = top centre, top_right, bottom_left, bottom_right; y grows downwards,
so bottom pieces have negative y). tools/composite_mockup_hud.py reads it to place the pieces over a screenshot;
the BetterHud huds/layouts yml for M1-M4 should take the same numbers.

Text that changes (HP / mana numbers, level, EXP, tracker lines, distance, cooldown seconds) is NOT in the sprites:
BetterHud draws it with the vanilla font. Fixed letters (compass points, combo + key badges) are drawn here with our
own small pixel fonts.

    python3 -I tools/gen_mockup_hud.py            # rewrites art/mockup-hud/
"""
import json
import math
import os
from PIL import Image, ImageDraw

ROOT = os.path.normpath(os.path.join(os.path.dirname(os.path.abspath(__file__)), '..'))
OUT = os.path.join(ROOT, 'art', 'mockup-hud')
SKILL_ICONS = os.path.join(ROOT, 'pack', 'assets', 'runeblock', 'textures', 'gui', 'skill')


def rgb(v, a=255):
    return ((v >> 16) & 255, (v >> 8) & 255, v & 255, a)


CLEAR = (0, 0, 0, 0)
# ── palette, sampled from the mockup (bronze/wood frames, warm gold, dark plum-brown insides) ──
OUTLINE = rgb(0x1A1210)
BRONZE_HI, BRONZE, BRONZE_MID, BRONZE_DK = rgb(0xD0A070), rgb(0xA57954), rgb(0x895E40), rgb(0x5D413C)
WOOD_DK = rgb(0x3E2C26)
INSIDE, INSIDE_DK = rgb(0x2A2224, 235), rgb(0x18141A, 245)
CELL, CELL_DK, CELL_HI = rgb(0x2A201A), rgb(0x1A1311), rgb(0x3A2C24)
GOLD_HI, GOLD, GOLD_MID, GOLD_DK, GOLD_SH = rgb(0xFFF0A8), rgb(0xFACC44), rgb(0xE0A830), rgb(0xB07A20), rgb(0x6E4512)
CREAM = rgb(0xFFE9B0)
HP = [rgb(0xFB9B6B), rgb(0xEE6A4E), rgb(0xD64A3D), rgb(0xBC3934), rgb(0xA32B2E)]
MP = [rgb(0x8FE3FF), rgb(0x59C2E6), rgb(0x1E8FDA), rgb(0x117BD1), rgb(0x115AAC)]
XP = [rgb(0xB8F070), rgb(0x86D044), rgb(0x5FA830), rgb(0x3F8020), rgb(0x2C5E16), rgb(0x2C5E16), rgb(0x214A10)]
LEAF_HI, LEAF, LEAF_DK, STEM = rgb(0xB4D466), rgb(0x7FA83C), rgb(0x4C7224), rgb(0x5A4A26)
FLAME = [rgb(0xFFF4B0), rgb(0xFFD84A), rgb(0xFFA82A), rgb(0xF0701A), rgb(0xB8400E)]

LAYOUT = {}   # sprite name -> {anchor, x, y, w, h, note}


def new(w, h, fill=CLEAR):
    return Image.new('RGBA', (w, h), fill)


def save(im, name, anchor=None, x=None, y=None, note=None, sub=None):
    folder = os.path.join(OUT, sub) if sub else OUT
    os.makedirs(folder, exist_ok=True)
    im.save(os.path.join(folder, name + '.png'))
    if anchor is not None:
        LAYOUT[name] = {'anchor': anchor, 'x': x, 'y': y, 'w': im.width, 'h': im.height, **({'note': note} if note else {})}
    return im


def px(im, x, y, c):
    if 0 <= x < im.width and 0 <= y < im.height:
        im.putpixel((x, y), c)


def hline(im, x0, x1, y, c):
    for x in range(x0, x1 + 1):
        px(im, x, y, c)


def vline(im, x, y0, y1, c):
    for y in range(y0, y1 + 1):
        px(im, x, y, c)


def rect(im, x0, y0, x1, y1, c):
    for y in range(y0, y1 + 1):
        hline(im, x0, x1, y, c)


def box(im, x0, y0, x1, y1, c):
    hline(im, x0, x1, y0, c); hline(im, x0, x1, y1, c)
    vline(im, x0, y0, y1, c); vline(im, x1, y0, y1, c)


def mirror(im):
    return im.transpose(Image.FLIP_LEFT_RIGHT)


def diamond(im, cx, cy, r, fill, edge=None, hi=None):
    """Filled diamond of radius r (2r+1 wide), optional outline and top-left highlight."""
    for dy in range(-r, r + 1):
        w = r - abs(dy)
        hline(im, cx - w, cx + w, cy + dy, fill)
    if edge:
        for dy in range(-r, r + 1):
            w = r - abs(dy)
            px(im, cx - w, cy + dy, edge); px(im, cx + w, cy + dy, edge)
    if hi and r >= 2:
        for dy in range(-r + 1, 1):
            w = r - abs(dy) - 1
            px(im, cx - w, cy + dy, hi)


# ── tiny pixel fonts (our own glyphs, so no Mojang art is copied into the sprites) ──
FONT3 = {   # 3x5, for combo / key badges
    'R': ['111', '101', '110', '101', '101'], 'L': ['100', '100', '100', '100', '111'],
    'C': ['011', '100', '100', '100', '011'], 'J': ['001', '001', '001', '101', '010'],
    'K': ['101', '110', '100', '110', '101'], 'H': ['101', '101', '111', '101', '101'],
    'T': ['111', '010', '010', '010', '010'], 'M': ['101', '111', '111', '101', '101'],
    'B': ['110', '101', '110', '101', '110'], 'Q': ['010', '101', '101', '110', '011'],
    'E': ['111', '100', '110', '100', '111'], 'F': ['111', '100', '110', '100', '100'],
    'G': ['011', '100', '101', '101', '011'], 'N': ['101', '111', '111', '111', '101'],
    '-': ['00', '00', '11', '00', '00'],
}
FONT5 = {   # 5x7, compass points
    'N': ['10001', '11001', '11001', '10101', '10011', '10011', '10001'],
    'E': ['11111', '10000', '10000', '11110', '10000', '10000', '11111'],
    'S': ['01111', '10000', '10000', '01110', '00001', '00001', '11110'],
    'W': ['10001', '10001', '10001', '10101', '10101', '11011', '10001'],
}


def text_width(s, font):
    return sum(len(font[ch][0]) for ch in s) + max(0, len(s) - 1)


def draw_text(im, x, y, s, font, c, shadow=None):
    for ch in s:
        g = font[ch]
        for gy, row in enumerate(g):
            for gx, bit in enumerate(row):
                if bit == '1':
                    if shadow:
                        px(im, x + gx + 1, y + gy + 1, shadow)
                    px(im, x + gx, y + gy, c)
        x += len(g[0]) + 1


# ═════════════════════════════ bottom centre ═════════════════════════════
# y = 0 is the bottom edge of the screen. Vanilla hotbar: x -91..+90, y -22..-1 (fixed by the game).

def hotbar():
    """Vanilla sprite override, 182x22, same geometry: 9 cells, item slot at x 3+20i, y 3 (16x16)."""
    im = new(182, 22, CELL_DK)
    rect(im, 0, 0, 181, 21, BRONZE_MID)
    hline(im, 0, 181, 0, BRONZE_HI); hline(im, 0, 181, 21, BRONZE_DK)
    vline(im, 0, 0, 21, BRONZE); vline(im, 181, 0, 21, BRONZE_DK)
    for i in range(9):
        x0 = 20 * i + 2
        rect(im, x0, 2, x0 + 17, 19, CELL)
        hline(im, x0, x0 + 17, 2, CELL_DK); vline(im, x0, 2, 19, CELL_DK)      # inner shadow top-left
        hline(im, x0 + 1, x0 + 17, 19, CELL_HI); vline(im, x0 + 17, 3, 19, CELL_HI)
        if i:  # 2 px divider: bronze with a lit left edge
            vline(im, 20 * i, 1, 20, BRONZE)
            vline(im, 20 * i + 1, 1, 20, BRONZE_DK)
            px(im, 20 * i, 1, BRONZE_HI)
    return im


def hotbar_selection():
    """Vanilla sprite override, 24x23, drawn at (slot x - 1, -1): gold frame over the cell's own border.
    Row 0 and columns 0/23 stay clear so the BetterHud ring above the hotbar can own that line."""
    im = new(24, 23)
    box(im, 1, 1, 22, 22, GOLD_DK)
    box(im, 2, 2, 21, 21, GOLD)
    box(im, 3, 3, 20, 20, GOLD_MID)
    hline(im, 2, 21, 2, GOLD_HI); vline(im, 2, 2, 21, GOLD_HI)
    for (x, y) in ((1, 1), (22, 1), (1, 22), (22, 22)):
        px(im, x, y, CLEAR)
    return im


def hotbar_ring():
    """BetterHud image around the hotbar (outside its 182x22): 3 px bronze band on top and sides + diamond studs.
    Covers x -102..+101, y -27..-1; the hotbar area itself stays clear (BetterHud draws over the vanilla hotbar)."""
    im = new(204, 27)
    ox, oy = 102, 27          # image x = gui x + ox, image y = gui y + oy
    # top band y -26..-24, inner dark line y -23; side bands x -95..-93 / +92..+94, dark line x -92 / +91
    for gx0, gx1 in ((-95, 94),):
        rect(im, gx0 + ox, -26 + oy, gx1 + ox, -24 + oy, BRONZE_MID)
        hline(im, gx0 + ox, gx1 + ox, -26 + oy, BRONZE_HI)
        hline(im, gx0 + ox, gx1 + ox, -27 + oy, OUTLINE)
        hline(im, -92 + ox, 91 + ox, -23 + oy, BRONZE_DK)
    for side in (-1, 1):
        xs = range(-95, -92) if side < 0 else range(92, 95)
        for gx in xs:
            vline(im, gx + ox, -26 + oy, -1 + oy, BRONZE_MID)
        outer = -96 if side < 0 else 95
        vline(im, outer + ox, -27 + oy, -1 + oy, OUTLINE)
        vline(im, (-95 if side < 0 else 92) + ox, -26 + oy, -1 + oy, BRONZE_HI if side < 0 else BRONZE)
        vline(im, (-92 if side < 0 else 91) + ox, -23 + oy, -1 + oy, BRONZE_DK)
        # rivets
        for gy in (-20, -12, -4):
            px(im, (-94 if side < 0 else 93) + ox, gy + oy, GOLD_MID)
        # diamond stud on the outside, mid height
        cx = (-99 if side < 0 else 98) + ox
        diamond(im, cx, -13 + oy, 4, GOLD_MID, OUTLINE, GOLD_HI)
        px(im, cx, -13 + oy, GOLD_SH)
    for i in range(1, 9):
        px(im, -91 + 20 * i + ox, -25 + oy, GOLD_MID)
    return im


def exp_bar():
    """EXP frame 200x11 at x -100..+99, y -38..-28; inner track x -91..+90 (182), fill 180x7 at x -90, y -36."""
    im = new(200, 11)
    rect(im, 8, 0, 191, 10, OUTLINE)
    rect(im, 9, 1, 190, 9, INSIDE_DK)
    hline(im, 9, 190, 1, rgb(0x0E0A0C, 250))
    hline(im, 8, 191, 0, BRONZE_DK); hline(im, 8, 191, 10, BRONZE_DK)
    hline(im, 9, 190, 0, BRONZE)
    # end connectors + diamond caps (the mockup's "◆—" ends)
    # M2 (Nov 6): the progress ticks sit in the rim (every 18 px of the fill), not on the fill, so the centred
    # "EXP n / m" text never crosses a tick (the M1 shots had ticks through the letters)
    for k in range(1, 10):
        x = 10 + 18 * k
        px(im, x, 0, GOLD_MID); px(im, x, 1, GOLD_DK); px(im, x, 10, GOLD_DK)
    for side in (0, 1):
        cx = 3 if side == 0 else 196
        diamond(im, cx, 5, 3, GOLD_MID, OUTLINE, GOLD_HI)
        x0, x1 = (7, 7) if side == 0 else (192, 192)
        vline(im, x0, 3, 7, BRONZE)
        px(im, x0, 5, GOLD)
    return im


def exp_fill():
    im = new(180, 7)
    for y, c in enumerate(XP):
        hline(im, 0, 179, y, c)
    return im   # M2: no ticks on the fill (they moved into the frame rim, see exp_bar)


def bar_panel(hp):
    """HP panel 91x22 (outer end on the left, chamfered; inner end tucks under the level shield).
    The MP panel is this mirrored. Track x 4..86, y 12..18; fill 82x5 at (5, 13)."""
    w, h = 91, 22
    im = new(w, h)
    ch = 4   # chamfer on the outer end
    for y in range(h):
        d = max(0, ch - y, y - (h - 1 - ch))
        hline(im, d, w - 1, y, BRONZE_MID)
    # outline + bevel
    for y in range(h):
        d = max(0, ch - y, y - (h - 1 - ch))
        px(im, d, y, OUTLINE)
        px(im, d + 1, y, BRONZE_HI if y < h // 2 else BRONZE)
    hline(im, ch, w - 1, 0, OUTLINE); hline(im, ch, w - 1, h - 1, OUTLINE)
    hline(im, ch, w - 1, 1, BRONZE_HI); hline(im, ch, w - 1, h - 2, BRONZE_DK)
    vline(im, w - 1, 0, h - 1, OUTLINE)
    # inside (text row + track)
    for y in range(2, h - 2):
        d = max(0, ch - y, y - (h - 1 - ch))
        hline(im, d + 3, w - 3, y, INSIDE)
    hline(im, ch + 2, w - 3, 2, rgb(0x110C0E, 240))
    # track
    rect(im, 4, 12, 86, 18, OUTLINE)
    rect(im, 5, 13, 85, 17, rgb(0x120C0D, 255))
    hline(im, 4, 86, 19, BRONZE_DK)
    # rivets on the band
    for x in (14, 44, 74):
        px(im, x, 1, GOLD_MID)
        px(im, x, h - 2, GOLD_DK)
    return im


def bar_fill(cols, w=81):
    im = new(w, 5)
    for y, c in enumerate(cols):
        hline(im, 0, w - 1, y, c)
    hline(im, 0, w - 1, 0, cols[0])
    for x in range(0, w, 8):
        px(im, x, 1, rgb(0xFFFFFF, 60))
    return im


def heart_icon():
    rows = ['.##.##.', '#######', '#######', '.#####.', '..###..', '...#...']
    im = new(9, 8)
    for y, r in enumerate(rows):
        for x, ch in enumerate(r):
            if ch == '#':
                px(im, x + 1, y + 1, HP[2])
    # outline
    base = im.copy()
    for y in range(8):
        for x in range(9):
            if base.getpixel((x, y))[3] == 0 and any(
                    0 <= x + dx < 9 and 0 <= y + dy < 8 and base.getpixel((x + dx, y + dy))[3]
                    for dx, dy in ((1, 0), (-1, 0), (0, 1), (0, -1))):
                px(im, x, y, OUTLINE)
    px(im, 2, 2, HP[0]); px(im, 3, 2, HP[0]); px(im, 2, 3, HP[1])
    px(im, 6, 4, HP[4]); px(im, 5, 5, HP[4])
    return im


def drop_icon():
    rows = ['...#...', '..###..', '..###..', '.#####.', '#######', '#######', '.#####.', '..###..']
    im = new(9, 10)
    for y, r in enumerate(rows):
        for x, ch in enumerate(r):
            if ch == '#':
                px(im, x + 1, y + 1, MP[2])
    base = im.copy()
    for y in range(10):
        for x in range(9):
            if base.getpixel((x, y))[3] == 0 and any(
                    0 <= x + dx < 9 and 0 <= y + dy < 10 and base.getpixel((x + dx, y + dy))[3]
                    for dx, dy in ((1, 0), (-1, 0), (0, 1), (0, -1))):
                px(im, x, y, OUTLINE)
    px(im, 3, 5, MP[0]); px(im, 3, 6, MP[0]); px(im, 4, 4, MP[1])
    px(im, 6, 7, MP[4]); px(im, 5, 8, MP[4])
    return im


def level_shield():
    """24x28 heater shield, gold, dark outline; the level number is BetterHud text on top (vanilla font)."""
    w, h = 24, 28
    half = []
    for y in range(h):
        if y < 2:
            half.append(9 + y)           # notched top corners
        elif y < 15:
            half.append(11)
        else:
            t = (y - 15) / (h - 1 - 15)
            half.append(max(0, round(11 * math.cos(t * math.pi / 2) ** 0.8)))
    im = new(w, h)
    cx = 11.5
    for y, hw in enumerate(half):
        x0, x1 = math.ceil(cx - hw - 0.5), math.floor(cx + hw + 0.5)
        hline(im, x0, x1, y, OUTLINE)
        if x1 - x0 >= 2:
            hline(im, x0 + 1, x1 - 1, y, GOLD_DK)
        if x1 - x0 >= 4:
            hline(im, x0 + 2, x1 - 2, y, GOLD)
            hline(im, round(cx), x1 - 2, y, GOLD_MID)     # right half shaded
        if x1 - x0 >= 8:
            px(im, x0 + 2, y, GOLD_HI)
    hline(im, 3, 20, 1, GOLD_HI)
    hline(im, 3, 20, 2, GOLD)
    # inner rim line
    for y in range(4, h - 6):
        hw = half[y] - 3
        x0, x1 = math.ceil(cx - hw - 0.5), math.floor(cx + hw + 0.5)
        if x1 > x0:
            px(im, x0, y, GOLD_DK); px(im, x1, y, GOLD_DK)
    hline(im, 4, 19, 4, GOLD_DK)
    return im


def laurel(w=12, h=20, leaves=5):
    """Laurel sprig for the LEFT end (stem curving up and out, leaves in pairs); the right one is mirrored."""
    im = new(w, h)
    n = h * 4
    pts = []
    for i in range(n):
        t = i / (n - 1)
        pts.append(((w - 2.5) - (w - 6) * math.sin(t * math.pi / 2) ** 1.3, (h - 1.5) - (h - 4) * t))
    for x, y in pts:
        px(im, round(x), round(y), STEM)

    def leaf(cx, cy, ux, uy, length):
        nx, ny = -uy, ux
        for yy in range(h):
            for xx in range(w):
                dx, dy = xx + 0.5 - cx, yy + 0.5 - cy
                s_ = dx * ux + dy * uy
                if 0 <= s_ <= length:
                    half = 1.25 * math.sin(math.pi * s_ / length) + 0.15
                    o = dx * nx + dy * ny
                    if abs(o) <= half:
                        c = LEAF_HI if (o * (1 if ux > 0 else -1)) < -0.3 and s_ < length * 0.7 else (LEAF_DK if o > 0.55 else LEAF)
                        px(im, xx, yy, c)

    for k in range(leaves):
        t = 0.12 + 0.8 * k / max(1, leaves - 1)
        i = int(t * (n - 1))
        x, y = pts[i]
        x2, y2 = pts[min(n - 1, i + 2)]
        tx, ty = x2 - x, y2 - y
        ln = math.hypot(tx, ty) or 1
        tx, ty = tx / ln, ty / ln
        for side in (-1, 1):
            a = math.radians(48) * side
            ux, uy = tx * math.cos(a) - ty * math.sin(a), tx * math.sin(a) + ty * math.cos(a)
            leaf(x + 0.5, y + 0.5, ux, uy, 4.6 if k < leaves - 1 else 3.6)
    tx, ty = pts[-1]
    leaf(tx + 0.5, ty + 0.5, -0.5, -0.86, 3.5)   # tip leaf
    return im


def skill_slot(gold=False):
    """22x22 slot frame, icon area 16x16 at (3, 3) left clear (the icon is drawn under/over it by BetterHud)."""
    im = new(22, 22)
    hi, mid, dk = (GOLD_HI, GOLD_MID, GOLD_SH) if gold else (BRONZE_HI, BRONZE, BRONZE_DK)
    rect(im, 0, 0, 21, 21, OUTLINE)
    rect(im, 1, 1, 20, 20, mid)
    hline(im, 1, 20, 1, hi); vline(im, 1, 1, 20, hi)
    hline(im, 2, 20, 20, dk); vline(im, 20, 2, 20, dk)
    rect(im, 2, 2, 19, 19, OUTLINE)
    rect(im, 3, 3, 18, 18, INSIDE_DK)
    for (x, y) in ((0, 0), (21, 0), (0, 21), (21, 21)):
        px(im, x, y, CLEAR)
    for (x, y) in ((1, 1), (20, 1), (1, 20), (20, 20)):
        px(im, x, y, OUTLINE)
    if gold:
        for (x, y) in ((10, 0), (11, 0), (10, 21), (11, 21), (0, 10), (0, 11), (21, 10), (21, 11)):
            px(im, x, y, GOLD_HI)
    return im


def ult_flames():
    """30x34 flame ring around the ultimate slot (the slot sits at (4, 9) under it); flames lick upward, tallest
    over the top centre like the mockup. The slot sprite (gold) is drawn on top."""
    w, h = 30, 34
    im = new(w, h)
    sx, sy, sw = 4, 9, 22
    x0, x1, y0, y1 = sx, sx + sw - 1, sy, sy + sw - 1
    cx = (x0 + x1) / 2
    for y in range(h):
        for x in range(w):
            if x0 <= x <= x1 and y0 <= y <= y1:
                continue
            if y < y0 and x0 - 2 <= x <= x1 + 2:                     # above the slot: rising tongues
                d = y0 - y
                bump = 1 - min(1, abs(x - cx) / 14)
                spike = 0.55 + 0.45 * abs(math.sin((x - cx) * 0.95 + 0.4))
                H = (2.5 + 7.5 * bump ** 1.3) * spike + 0.6
            elif x < x0 or x > x1:                                   # sides: shorter tongues leaning up
                d = (x0 - x) if x < x0 else (x - x1)
                if y > y1 + 1:
                    d += (y - y1 - 1) * 1.6
                if y < y0:
                    d += (y0 - y) * 0.9
                ph = (y - y0) * 0.9 + (0 if x < x0 else 1.7)
                H = 2.2 + 1.6 * abs(math.sin(ph)) + (y1 - y) / sw * 1.2
            else:                                                    # under the slot: a thin glow
                d = y - y1
                H = 1.6
            if d <= H:
                f = d / H
                c = FLAME[1] if f < 0.3 else FLAME[2] if f < 0.58 else FLAME[3] if f < 0.85 else FLAME[4]
                px(im, x, y, c)
    for (x, y) in ((1, 5), (27, 3), (8, 0), (21, 1), (15, 0), (0, 19), (29, 23), (3, 12)):
        px(im, x, y, FLAME[0])
    return im


def combo_badge(combo, gold=False):
    """Key badge under a skill slot: today's click combo ("R-L-R") in the 3x5 font, 21x9 pill."""
    s = '-'.join(combo)
    tw = text_width(s, FONT3)
    w, h = tw + 4, 9
    im = new(w, h)
    rim = GOLD_MID if gold else BRONZE
    rect(im, 1, 0, w - 2, h - 1, OUTLINE)
    rect(im, 0, 1, w - 1, h - 2, OUTLINE)
    rect(im, 1, 1, w - 2, h - 2, rim)
    rect(im, 2, 2, w - 3, h - 3, rgb(0x2E2724))
    hline(im, 2, w - 3, 1, GOLD_HI if gold else BRONZE_HI)
    draw_text(im, 2, 2, s, FONT3, CREAM if not gold else GOLD_HI)
    return im


def key_badge(k):
    im = new(7, 9)
    rect(im, 1, 0, 5, 8, OUTLINE); rect(im, 0, 1, 6, 7, OUTLINE)
    rect(im, 1, 1, 5, 7, BRONZE)
    rect(im, 1, 2, 5, 7, rgb(0x2E2724))
    hline(im, 1, 5, 1, BRONZE_HI)
    draw_text(im, 2, 2, k, FONT3, CREAM)
    return im


def cooldown_frames(n=16, size=16):
    """Clock sweep over a skill icon: frame k = k/n of the cooldown still to go, dark from 12 o'clock clockwise."""
    frames = []
    c = (size - 1) / 2
    for k in range(n + 1):
        im = new(size, size)
        left = k / n
        for y in range(size):
            for x in range(size):
                a = (math.degrees(math.atan2(x - c, -(y - c))) + 360) % 360   # 0 at 12 o'clock, clockwise
                if a < left * 360 - 1e-6:
                    px(im, x, y, rgb(0x0A0608, 165))
        if 0 < k < n:   # bright edge on the sweep line
            ang = math.radians(left * 360)
            for r in range(0, size // 2 + 1):
                px(im, round(c + r * math.sin(ang)), round(c - r * math.cos(ang)), rgb(0xFFE9B0, 120))
        frames.append(im)
    return frames


def nomana_overlay():
    """16x16: blue-black veil + crossed drop in the corner. Used over the GREY copy of the icon (see grey_icon)."""
    im = new(16, 16, rgb(0x0A1430, 110))
    d = drop_icon().resize((9, 10), Image.NEAREST)
    im.alpha_composite(d, (8, 7))
    for i in range(7):
        px(im, 9 + i, 8 + i, rgb(0xF04040)); px(im, 10 + i, 8 + i, rgb(0x701010))
    return im


def grey_icon(src):
    im = src.convert('RGBA')
    out = new(im.width, im.height)
    for y in range(im.height):
        for x in range(im.width):
            r, g, b, a = im.getpixel((x, y))
            l = int((0.3 * r + 0.59 * g + 0.11 * b) * 0.62)
            out.putpixel((x, y), (l, l, int(l * 1.08), a))
    return out


# ═════════════════════════════ top centre: compass ═════════════════════════════

def compass_strip():
    """190x11 static strip (BetterHud image under the compass): 1 px gold line + ornate end caps.
    The moving letters / ticks / marker are the BetterHud compass's own images (compass_*)."""
    w, h = 190, 11
    im = new(w, h)
    cy = 5
    hline(im, 6, w - 7, cy - 1, rgb(0x000000, 70))
    hline(im, 6, w - 7, cy, GOLD_MID)
    hline(im, 6, w - 7, cy + 1, GOLD_SH)
    for side in (0, 1):
        cx = 3 if side == 0 else w - 4
        diamond(im, cx, cy, 3, GOLD_MID, OUTLINE, GOLD_HI)
        sx = 7 if side == 0 else w - 8
        px(im, sx, cy - 1, GOLD); px(im, sx, cy + 1, GOLD)
        px(im, sx + (1 if side == 0 else -1), cy - 2, GOLD_DK); px(im, sx + (1 if side == 0 else -1), cy + 2, GOLD_DK)
    return im


def compass_letter(s, gold=False):
    tw = text_width(s, FONT5)
    im = new(tw + 1, 8)
    draw_text(im, 0, 0, s, FONT5, GOLD if gold else rgb(0xF4F0E8), shadow=rgb(0x2A2024, 200))
    return im


def compass_tick(major=False):
    im = new(1, 5 if major else 3)
    vline(im, 0, 0, im.height - 1, GOLD if major else GOLD_MID)
    return im


def compass_marker():
    im = new(9, 9)
    diamond(im, 4, 4, 4, GOLD, OUTLINE, GOLD_HI)
    px(im, 5, 5, GOLD_MID); px(im, 4, 6, GOLD_MID); px(im, 6, 4, GOLD_MID)
    return im


def small_diamond():
    """5x5 inline image for the distance text ("<image:rb_dist> 142m") and the tracker."""
    im = new(5, 5)
    diamond(im, 2, 2, 2, GOLD, None, GOLD_HI)
    return im


# ═════════════════════════════ top right: quest tracker ═════════════════════════════

def tracker_panel(w, h):
    """Dark translucent box, thin gold frame with corner flourishes and a notch for the star badge."""
    im = new(w, h)
    rect(im, 2, 2, w - 3, h - 3, rgb(0x221C22, 205))
    box(im, 1, 1, w - 2, h - 2, OUTLINE)
    box(im, 2, 2, w - 3, h - 3, GOLD_DK)
    hline(im, 3, w - 4, 2, GOLD_MID)
    # title separator
    hline(im, 6, w - 7, 15, GOLD_DK); hline(im, 6, w - 7, 16, rgb(0x000000, 90))
    # corner flourishes
    for (cx, cy, fx, fy) in ((2, 2, 1, 1), (w - 3, 2, -1, 1), (2, h - 3, 1, -1), (w - 3, h - 3, -1, -1)):
        for k in range(4):
            px(im, cx + fx * k, cy, GOLD); px(im, cx, cy + fy * k, GOLD)
        px(im, cx + fx, cy + fy, GOLD_HI)
        px(im, cx + 2 * fx, cy + 2 * fy, GOLD_DK)
    # right end diamond on the title band (mockup)
    diamond(im, w - 3, 8, 3, GOLD_MID, OUTLINE, GOLD_HI)
    return im


def tracker_star():
    """11x11 four-point gold star (title badge)."""
    im = new(13, 13)
    c = 6
    for k in range(7):
        w = max(0, 2 - k // 2)
        for d in range(-w, w + 1):
            for (x, y) in ((c + d, c - k), (c + d, c + k), (c - k, c + d), (c + k, c + d)):
                px(im, x, y, GOLD)
    diamond(im, c, c, 2, GOLD_HI)
    for k in range(1, 7):
        px(im, c + 1, c + k, GOLD_DK); px(im, c + k, c + 1, GOLD_DK)
    base = im.copy()
    for y in range(13):
        for x in range(13):
            if base.getpixel((x, y))[3] == 0 and any(
                    0 <= x + dx < 13 and 0 <= y + dy < 13 and base.getpixel((x + dx, y + dy))[3]
                    for dx, dy in ((1, 0), (-1, 0), (0, 1), (0, -1))):
                px(im, x, y, rgb(0x2A1A08, 220))
    return im


def checkbox(done):
    im = new(7, 7)
    box(im, 0, 0, 6, 6, rgb(0xE8E4DC))
    rect(im, 1, 1, 5, 5, rgb(0x141014, 200))
    if done:
        for (x, y) in ((1, 3), (2, 4), (3, 5), (4, 4), (5, 3), (5, 2), (6, 1)):
            px(im, x, y, GOLD)
        for (x, y) in ((2, 3), (3, 4), (4, 3), (5, 1)):
            px(im, x, y, GOLD_HI)
    return im


# ═════════════════════════════ corners: chat + menu keys ═════════════════════════════

def button():
    im = new(18, 16)
    rect(im, 1, 0, 16, 15, OUTLINE); rect(im, 0, 1, 17, 14, OUTLINE)
    rect(im, 1, 1, 16, 14, BRONZE_MID)
    hline(im, 1, 16, 1, BRONZE_HI); vline(im, 1, 1, 14, BRONZE)
    hline(im, 2, 16, 14, BRONZE_DK)
    rect(im, 3, 3, 14, 12, rgb(0x2E2220, 240))
    hline(im, 3, 14, 3, rgb(0x1A1210))
    return im


def pix_icon(rows, cmap):
    h, w = len(rows), max(len(r) for r in rows)
    im = new(w, h)
    for y, r in enumerate(rows):
        for x, ch in enumerate(r):
            if ch in cmap:
                px(im, x, y, cmap[ch])
    return im


ICON_MAP = {'#': GOLD, 'h': GOLD_HI, 'd': GOLD_DK, 'o': OUTLINE, 'w': rgb(0xF4F0E8), 'g': rgb(0x8A8A90)}
ICONS = {
    'bag': ['...dd....',
            '..d..d...',
            '.h####d..',
            'h######d.',
            'h#dddd#d.',
            'h#d##d#d.',
            'h######d.',
            'h######d.',
            '.dddddd..'],
    'book': ['.hh...hh.',
             'h##h.h##h',
             'h###d###h',
             'h###d###h',
             'h###d###h',
             'h###d###h',
             'hddddddd#',
             '.d.....d.'],
    'anvil': ['hhhhhhh..',
              '#######dd',
              '.######d.',
              '...###...',
              '...###...',
              '..#####..',
              '.#######.',
              '.ddddddd.'],
    'gear': ['...h#...',
             '.h.##.#.',
             '.######.',
             'h##..##d',
             '###..###',
             '.######.',
             '.#.##.d.',
             '...#d...'],
}


def chat_icon():
    rows = ['.hhhhhhhh.',
            'h########d',
            '##########',
            '##w#w#w###',
            '#########d',
            '.d#######.',
            '..##d.....',
            '..#d......']
    return pix_icon(rows, ICON_MAP)


# ═════════════════════════════ build ═════════════════════════════

SKILLS = ['dagger_flick', 'shadow_lurk', 'shadowstep_execution', 'deaths_whisper']   # Assassin, slot 4 = ultimate
COMBOS = ['RLR', 'RRR', 'RLL', 'RRL']          # SkillService.COMBOS, slot order
MENU_KEYS = [('bag', 'C', 'character'), ('book', 'J', 'journal'), ('anvil', 'K', 'skills'), ('gear', 'H', 'help')]

SLOT_W, SLOT_PITCH = 22, 28
SLOT_Y = -96          # top of the slot row; slots y -96..-75
BADGE_Y = -78         # badges y -78..-70 (overlap the slot's bottom 3 rows)


def main():
    os.makedirs(OUT, exist_ok=True)
    # hotbar (vanilla sprite overrides, fixed position; listed for the composite)
    save(hotbar(), 'hotbar', 'bottom', -91, -22, 'vanilla sprite gui/sprites/hud/hotbar.png')
    save(hotbar_selection(), 'hotbar_selection', 'bottom', -92, -23, 'vanilla sprite; x = -92 + 20*slot')
    save(hotbar_ring(), 'hotbar_ring', 'bottom', -102, -27, 'BetterHud image; studs overlap the off-hand slot (x -120..-92)')
    save(exp_bar(), 'exp_frame', 'bottom', -100, -38)
    save(exp_fill(), 'exp_fill', 'bottom', -90, -36, 'listener image, split left; EXP text vanilla font centred, top y -36')
    hp = bar_panel(True)
    save(hp, 'hp_panel', 'bottom', -101, -63)
    save(mirror(hp), 'mp_panel', 'bottom', 10, -63)
    save(bar_fill(HP), 'hp_fill', 'bottom', -96, -50, 'split left; HP text centred x -54, top y -60')
    save(bar_fill(MP), 'mp_fill', 'bottom', 15, -50, 'split right; MP text centred x +54, top y -60')
    save(heart_icon(), 'icon_heart', 'bottom', -97, -61)
    save(drop_icon(), 'icon_mana', 'bottom', 88, -62)
    save(level_shield(), 'level_shield', 'bottom', -12, -67, 'level = vanilla font text centred x 0, top y -57')
    lau = laurel()
    save(lau, 'laurel_bar_l', 'bottom', -113, -65)
    save(mirror(lau), 'laurel_bar_r', 'bottom', 101, -65)
    lau2 = laurel(12, 16, 4)
    save(lau2, 'laurel_skill_l', 'bottom', -64, -84)
    save(mirror(lau2), 'laurel_skill_r', 'bottom', 52, -84)
    x0 = -(4 * SLOT_W + 3 * (SLOT_PITCH - SLOT_W)) // 2       # -53
    for i in range(4):
        gx = x0 + SLOT_PITCH * i
        ult = i == 3
        if ult:
            save(ult_flames(), 'skill_ult_flames', 'bottom', gx - 4, SLOT_Y - 9)
        save(skill_slot(ult), 'skill_slot' + ('_ult' if ult else ''), 'bottom', gx, SLOT_Y) if i in (0, 3) else None
        LAYOUT['skill_slot_%d' % (i + 1)] = {'anchor': 'bottom', 'x': gx, 'y': SLOT_Y, 'w': 22, 'h': 22,
                                             'sprite': 'skill_slot_ult' if ult else 'skill_slot',
                                             'icon': {'x': gx + 3, 'y': SLOT_Y + 3, 'w': 16, 'h': 16}}
        b = combo_badge(COMBOS[i], ult)
        save(b, 'badge_' + COMBOS[i])
        LAYOUT['skill_badge_%d' % (i + 1)] = {'anchor': 'bottom', 'x': gx + 11 - b.width // 2, 'y': BADGE_Y,
                                              'w': b.width, 'h': b.height, 'sprite': 'badge_' + COMBOS[i]}
    for c in COMBOS:   # bow-mirrored combos (Archer with a bow: CastService shows L/R swapped)
        m = ''.join('L' if ch == 'R' else 'R' for ch in c)
        save(combo_badge(m), 'badge_' + m, sub='mirrored')
    for i, f in enumerate(cooldown_frames()):
        save(f, 'cd_%02d' % i, sub='cooldown')
    save(nomana_overlay(), 'skill_nomana')
    os.makedirs(os.path.join(OUT, 'skill_grey'), exist_ok=True)
    for sid in SKILLS:
        p = os.path.join(SKILL_ICONS, sid + '.png')
        if os.path.exists(p):
            save(grey_icon(Image.open(p)), sid, sub='skill_grey')
    LAYOUT['_skills'] = SKILLS
    LAYOUT['_combos'] = COMBOS

    # compass (top centre)
    save(compass_strip(), 'compass_strip', 'top', -95, 8)
    for s in ('N', 'E', 'S', 'W', 'NE', 'NW', 'SE', 'SW'):
        save(compass_letter(s, s == 'N'), 'compass_' + s.lower(), sub='compass')
    save(compass_tick(True), 'compass_tick_major', sub='compass')
    save(compass_tick(False), 'compass_tick', sub='compass')
    save(compass_marker(), 'compass_point', sub='compass')
    LAYOUT['compass'] = {'anchor': 'top', 'line_y': 13, 'letters_y': 3, 'px_per_degree': 1.0, 'half_span': 88,
                         'note': 'BetterHud circle compass; letters bottom at y 10, ticks cross the line'}
    save(small_diamond(), 'icon_diamond_small', 'top', -24, 21, 'inline image before the distance text, top y 20')

    # tracker (top right)
    tw, th = 152, 42
    save(tracker_panel(tw, th), 'tracker_panel', 'top_right', -5 - tw, 6)
    save(tracker_star(), 'tracker_star', 'top_right', -5 - tw - 4, 3)
    save(checkbox(False), 'checkbox', 'top_right', -5 - tw + 8, 25, 'rows at y 25 and 35 (box), text x +20, y 25 / 35')
    save(checkbox(True), 'checkbox_done')
    LAYOUT['tracker_text'] = {'anchor': 'top_right', 'title_x': -5 - tw + 15, 'title_y': 10, 'row_x': -5 - tw + 20,
                              'row_y': [25, 35], 'max_text_w': tw - 26,
                              'note': 'server truncates a row to max_text_w px of vanilla font (~22 chars)'}

    # corners
    btn = button()
    save(btn, 'button')
    save(chat_icon(), 'icon_chat')
    LAYOUT['chat_button'] = {'anchor': 'bottom_left', 'x': 4, 'y': -24, 'w': 18, 'h': 16, 'icon': 'icon_chat', 'key': 'T'}
    for name, key, page in MENU_KEYS:
        save(pix_icon(ICONS[name], ICON_MAP), 'icon_' + name)
    for k in sorted({'T'} | {k for _, k, _ in MENU_KEYS}):
        save(key_badge(k), 'key_' + k, sub='keys')
    LAYOUT['menu_buttons'] = {'anchor': 'bottom_right', 'x0': -4 - (4 * 18 + 3 * 3), 'y': -24, 'pitch': 21,
                              'buttons': [{'icon': 'icon_' + n, 'key': k, 'page': p} for n, k, p in MENU_KEYS],
                              'note': 'shown only with the client mod (its default keys, HudKeybinds.java)'}
    with open(os.path.join(OUT, 'layout.json'), 'w') as f:
        json.dump(LAYOUT, f, indent=1)
    print('wrote', sum(len(fs) for _, _, fs in os.walk(OUT)), 'files to', OUT)


if __name__ == '__main__':
    main()
