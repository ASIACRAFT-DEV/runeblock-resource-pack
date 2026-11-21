#!/usr/bin/env python3
"""32 px Armour Casket icons v3 (Ett 13:38 UTC 2026-11-19, docs/spec/Caskets_ettlel_2026-11-19.md): a redesign of the
v2 set (tools/casket_art.py), not six recolours. One chest family (same width, same light from the top-left, same
one-pixel dark outline), but each rarity gets its own lid shape, material, corners, lock and gem:

  Common     worn plank wood, rusty iron corner caps, a plain hasp with a keyhole, a chipped lid corner
  Uncommon   clean oak, iron L-brackets with green enamel, a riveted plate with a round emerald
  Rare       blue-stained dark wood, two steel straps over lid + body, bevelled caps, a shield lock with a sapphire
  Unique     (optional, Ett 13:39: aqua, between Rare and Epic) pale ash wood, teal enamel side panels, silver trim,
             a drop-shaped aquamarine
  Epic       violet wood, a domed lid, silver-violet curled corners, two faint rune marks, a hexagon amethyst in an arch
  Legendary  black lacquer framed in gold, a gold crest on the lid, gold studs, an oval amber gem in prongs
  Mythic     obsidian body with two red veins, crimson lid, horned corners, a big ruby in a spiked black setting

The gem stays the brightest thing on each icon (Ett v2 rule). Files keep the v2 names (armour_<rarity>.png), so no
code or config change is needed; Unique is written only with --unique (there is no Unique rarity in the game yet).

Usage: python3 -I tools/casket_art_v3.py [--out pack] [--unique] [--preview sheet.png] [--compare old_sheet.png]
"""
import argparse, os
from PIL import Image, ImageDraw, ImageFont

N = 32
RARITIES = ['common', 'uncommon', 'rare', 'unique', 'epic', 'legendary', 'mythic']
LABEL = {'common': ('Common', (220, 220, 220)), 'uncommon': ('Uncommon', (85, 255, 85)), 'rare': ('Rare', (85, 170, 255)),
         'unique': ('Unique', (85, 255, 255)), 'epic': ('Epic', (255, 85, 255)),
         'legendary': ('Legendary', (255, 170, 0)), 'mythic': ('Mythic', (255, 85, 85))}


def ramp(*h): return [tuple(int(x[i:i + 2], 16) for i in (1, 3, 5)) for x in h]


# 5-step ramps, dark -> light
WOOD_WORN = ramp('#3b2a1c', '#5a4130', '#77583d', '#93714f', '#ab8962')
WOOD_OAK = ramp('#3a2210', '#5e3818', '#7f4d22', '#a0652e', '#bf8040')
WOOD_BLUE = ramp('#0f1726', '#1b2a42', '#283d5c', '#36527a', '#476a96')
WOOD_ASH = ramp('#5a4a36', '#86704f', '#ab9370', '#c9b38e', '#e0cfa9')
WOOD_VIOLET = ramp('#1c0b30', '#2f1450', '#431f70', '#592c90', '#7040ae')
LACQUER = ramp('#060506', '#0f0d0e', '#191618', '#242023', '#302a2d')
OBSIDIAN = ramp('#050407', '#0c0a10', '#15121a', '#1f1a26', '#2a2433')
CRIMSON = ramp('#3d0407', '#66080d', '#930f15', '#bd1c1e', '#de3a32')

IRON_RUST = ramp('#2a2522', '#4a403a', '#6b5d52', '#8c7b6b', '#a69481')
IRON = ramp('#232326', '#3e3f44', '#5d5f66', '#82858d', '#a9acb3')
STEEL = ramp('#1b2028', '#3a4350', '#5f6b7a', '#8995a4', '#b6c1cd')
SILVER = ramp('#4a4f55', '#757c84', '#a3aab1', '#c8cfd5', '#e6ebef')
SILVER_V = ramp('#3a3346', '#625a73', '#8f86a3', '#b9b1cc', '#ddd6ec')
GOLD = ramp('#5e3f06', '#9a6b0c', '#cf9a1c', '#efc240', '#fbe08a')
BLACKMETAL = ramp('#0e0d10', '#1e1c22', '#302d36', '#45414c', '#5c5766')

ENAMEL_GREEN = ramp('#123d1c', '#1f6230', '#2f8a44', '#46ad5c', '#6fcf80')
ENAMEL_TEAL = ramp('#0b3b40', '#11616a', '#1a8c96', '#2fb5bd', '#66d9dc')

GEM_EMERALD = ramp('#0a4318', '#127a2b', '#22b748', '#62ec84', '#d2ffdc')
GEM_SAPPHIRE = ramp('#0a2a6e', '#1448b0', '#2f74ec', '#7fb0ff', '#e2eeff')
GEM_AQUA = ramp('#06555c', '#0b8f99', '#1fd0d6', '#86f4f2', '#e6fffe')
GEM_AMETHYST = ramp('#3a0b6e', '#661cb8', '#9748ff', '#c798ff', '#f2e6ff')
GEM_AMBER = ramp('#7a3400', '#c06204', '#f39612', '#ffc85a', '#fff2c6')
GEM_RUBY = ramp('#520406', '#990b0e', '#de1b1b', '#ff6a4a', '#ffd6c2')
VEIN = ramp('#5a0808', '#b0140f', '#ff4a1e')
RUNE_V = ramp('#7d4cc0', '#b98cf0')

L, R = 3, 28                     # chest left / right columns (26 wide, same on every rarity)
LID_TOP, LID_FRONT, SEAM, BODY, BOTTOM = 6, 10, 15, 16, 28


class Canvas:
    def __init__(self):
        self.px = {}

    def put(self, x, y, c):
        if 0 <= x < N and 0 <= y < N and c is not None:
            self.px[(x, y)] = c

    def get(self, x, y): return self.px.get((x, y))

    def box(self, x0, y0, x1, y1, rp, top=4, mid=2, bottom=1, left=3, right=1):
        """A bevelled block: lighter top + left edge, darker bottom + right edge."""
        for y in range(y0, y1 + 1):
            for x in range(x0, x1 + 1):
                t = top if y == y0 else bottom if y == y1 else left if x == x0 else right if x == x1 else mid
                self.put(x, y, rp[t])

    def image(self, outline=0.32):
        shape = set(self.px)
        out = dict(self.px)
        for (x, y) in shape:
            for dx, dy in ((1, 0), (-1, 0), (0, 1), (0, -1)):
                q = (x + dx, y + dy)
                if q not in shape and 0 <= q[0] < N and 0 <= q[1] < N:
                    c = self.px[(x, y)]
                    cand = tuple(max(0, int(v * outline)) for v in c)
                    old = out.get(q)
                    if old is None or sum(cand) < sum(old):
                        out[q] = cand
        im = Image.new('RGBA', (N, N), (0, 0, 0, 0))
        for (x, y), c in out.items():
            im.putpixel((x, y), c + (255,))
        return im


# ───────────────────────────── shared pieces ─────────────────────────────

def lid_inset(profile, y):
    """How far the lid top's row y is pulled in from each side (gives flat / rounded / domed lids)."""
    rows = {'flat': {6: 1, 7: 0}, 'round': {6: 2, 7: 1}, 'dome': {5: 4, 6: 2, 7: 1}, 'tall': {4: 6, 5: 3, 6: 1}}[profile]
    return rows.get(y)


def lid_top_rows(profile):
    return [y for y in range(4, LID_FRONT) if lid_inset(profile, y) is not None or y > max(
        k for k in range(4, LID_FRONT) if lid_inset(profile, k) is not None)]


def draw_lid(c, wood, profile, planks=True, vertical_planks=6):
    first = min(y for y in range(4, LID_FRONT) if lid_inset(profile, y) is not None)
    for y in range(first, LID_FRONT):
        ins = lid_inset(profile, y) or 0
        for x in range(L + ins, R - ins + 1):
            t = 4 if y == first else 3 if y < first + 2 else 2
            if x == L + ins: t = min(t + 0, 3)
            if x == R - ins: t = 1
            c.put(x, y, wood[t])
    if planks:   # plank seams across the lid top
        for x in range(L + vertical_planks, R - 1, vertical_planks):
            for y in range(first + 1, LID_FRONT):
                c.put(x, y, wood[1])
    # lid front: bevelled band
    c.box(L, LID_FRONT, R, SEAM - 1, wood, top=3, mid=2, bottom=1, left=3, right=1)
    return first


def draw_body(c, wood, plank='h', grain=None):
    c.box(L, BODY, R, BOTTOM, wood, top=3, mid=2, bottom=0, left=2, right=1)
    if plank == 'h':
        for y in (20, 24):
            for x in range(L + 1, R): c.put(x, y, wood[1])
    elif plank == 'v':
        for x in range(L + 5, R - 1, 5):
            for y in range(BODY + 1, BOTTOM): c.put(x, y, wood[1])
    for (x, y, t) in (grain or []):
        c.put(x, y, wood[t])


def seam(c, rp, t=0):
    for x in range(L, R + 1): c.put(x, SEAM, rp[t])


def rivet(c, x, y, rp):
    c.put(x, y, rp[4]); c.put(x + 1, y + 1, rp[1]) if c.get(x + 1, y + 1) else None


GEM_SHAPES = {   # rows (dy, x0, x1) relative to the gem's top-centre (cx is the left of the two centre columns)
    'round':   [(0, 0, 1), (1, -1, 2), (2, -1, 2), (3, -1, 2), (4, 0, 1)],
    'diamond': [(0, 0, 1), (1, -1, 2), (2, -2, 3), (3, -2, 3), (4, -1, 2), (5, 0, 1)],
    'bigdiamond': [(0, 0, 1), (1, -1, 2), (2, -2, 3), (3, -3, 4), (4, -3, 4), (5, -2, 3), (6, -1, 2), (7, 0, 1)],
    'hexagon': [(0, -1, 2), (1, -2, 3), (2, -2, 3), (3, -2, 3), (4, -1, 2)],
    'drop':    [(0, 0, 1), (1, 0, 1), (2, -1, 2), (3, -1, 2), (4, -1, 2), (5, 0, 1)],
    'oval':    [(0, -1, 2), (1, -2, 3), (2, -2, 3), (3, -2, 3), (4, -2, 3), (5, -1, 2)],
}


def gem(c, shape, cx, y0, rp, sparkle=True):
    rows = GEM_SHAPES[shape]
    h = len(rows) - 1
    for (dy, a, b) in rows:
        for x in range(cx + a, cx + b + 1):
            d = (x - (cx + a)) / max(1, b - a) + dy / max(1, h)
            t = 4 if d < 0.4 else 3 if d < 0.85 else 2 if d < 1.3 else 1 if d < 1.7 else 0
            c.put(x, y0 + dy, rp[t])
    if sparkle:
        dy, a, b = rows[1]
        c.put(cx + a + (1 if b - a > 2 else 0), y0 + dy, (255, 255, 255))
    return [(cx + a, cx + b, y0 + dy) for (dy, a, b) in rows]


def gem_frame(c, shape, cx, y0, rp):
    """A one-pixel metal setting round the gem (drawn before the gem)."""
    rows = GEM_SHAPES[shape]
    cells = set()
    for (dy, a, b) in rows:
        for x in range(cx + a, cx + b + 1): cells.add((x, y0 + dy))
    for (x, y) in list(cells):
        for dx, dy in ((1, 0), (-1, 0), (0, 1), (0, -1), (1, 1), (-1, -1), (1, -1), (-1, 1)):
            q = (x + dx, y + dy)
            if q not in cells:
                t = 4 if dy < 0 or dx < 0 else 1
                c.put(q[0], q[1], rp[t if (dx, dy) != (0, 0) else 2])


CX = (L + R) // 2      # 15: the gem's left centre column


# ───────────────────────────── rarities ─────────────────────────────

def common():
    c = Canvas()
    draw_lid(c, WOOD_WORN, 'flat')
    seam(c, IRON_RUST, 0)
    draw_body(c, WOOD_WORN, 'h', grain=[(7, 18, 1), (8, 18, 1), (21, 22, 1), (22, 22, 1), (12, 26, 1), (24, 17, 3),
                                         (6, 26, 3), (19, 18, 3)])
    # worn: a chipped lid corner (top-right) and a knot
    for (x, y) in ((R, 6), (R - 1, 6), (R, 7)): c.px.pop((x, y), None)
    c.put(10, 22, WOOD_WORN[0]); c.put(11, 22, WOOD_WORN[1])
    # small rusty corner caps (3x3), bottom only + lid top-left
    for (x0, y0) in ((L, BOTTOM - 2), (R - 2, BOTTOM - 2), (L, 6)):
        c.box(x0, y0, x0 + 2, y0 + 2, IRON_RUST, top=3, mid=2, bottom=1, left=3, right=1)
    # plain hasp: a strap from the lid front down to a lock block with a keyhole
    c.box(CX - 1, LID_FRONT + 1, CX + 2, SEAM, IRON_RUST, top=3, mid=2, bottom=1, left=3, right=1)
    c.box(CX - 3, SEAM + 1, CX + 4, SEAM + 7, IRON_RUST, top=4, mid=3, bottom=1, left=4, right=1)
    for (x, y) in ((CX, SEAM + 3), (CX + 1, SEAM + 3), (CX, SEAM + 4), (CX + 1, SEAM + 4), (CX, SEAM + 5)):
        c.put(x, y, IRON[0])
    # one rusty band across the body
    for x in range(L + 1, R):
        if c.get(x, 25) and not (CX - 3 <= x <= CX + 4): c.put(x, 25, IRON_RUST[2])
    return c


def uncommon():
    c = Canvas()
    draw_lid(c, WOOD_OAK, 'round')
    seam(c, IRON, 0)
    draw_body(c, WOOD_OAK, 'v')
    # green band along the lid front
    for x in range(L + 1, R):
        c.put(x, SEAM - 2, ENAMEL_GREEN[2]); c.put(x, SEAM - 1, ENAMEL_GREEN[1])
    # L-brackets: iron with a green enamel inner edge
    for side in (0, 1):
        x0 = L if side == 0 else R - 4
        # bottom bracket
        c.box(x0, BOTTOM - 4, x0 + 4, BOTTOM, IRON, top=3, mid=2, bottom=1, left=3, right=1)
        for x in range(x0 + 1, x0 + 4):
            for y in range(BOTTOM - 3, BOTTOM):
                if (side == 0 and x > x0 + 1 and y < BOTTOM - 1) or (side == 1 and x < x0 + 3 and y < BOTTOM - 1):
                    c.put(x, y, WOOD_OAK[2])
        c.put(x0 + (1 if side == 0 else 3), BOTTOM - 3, ENAMEL_GREEN[3])
        # top bracket on the lid
        c.box(x0, 7, x0 + 4, 11, IRON, top=4, mid=2, bottom=1, left=3, right=1)
        for x in range(x0 + 1, x0 + 4):
            for y in range(8, 11):
                if (side == 0 and x > x0 + 1 and y > 8) or (side == 1 and x < x0 + 3 and y > 8):
                    c.put(x, y, WOOD_OAK[3])
        c.put(x0 + (1 if side == 0 else 3), 8, ENAMEL_GREEN[3])
    # riveted plate + round emerald
    c.box(CX - 3, 12, CX + 4, 21, IRON, top=4, mid=2, bottom=1, left=3, right=1)
    for (x, y) in ((CX - 2, 13), (CX + 3, 13), (CX - 2, 20), (CX + 3, 20)): c.put(x, y, IRON[4])
    gem(c, 'round', CX, 14, GEM_EMERALD)
    return c


def rare():
    c = Canvas()
    draw_lid(c, WOOD_BLUE, 'round', vertical_planks=5)
    seam(c, STEEL, 0)
    draw_body(c, WOOD_BLUE, 'h')
    # two steel straps over lid + body
    for sx in (L + 5, R - 6):
        for y in range(6, BOTTOM + 1):
            if c.get(sx, y) is None and c.get(sx + 1, y) is None: continue
            c.put(sx, y, STEEL[3]); c.put(sx + 1, y, STEEL[1])
        for y in (8, 12, 18, 25): c.put(sx, y, STEEL[4])
    # bevelled steel corner caps
    for (x0, y0) in ((L, 7), (R - 2, 7), (L, BOTTOM - 3), (R - 2, BOTTOM - 3)):
        c.box(x0, y0, x0 + 2, y0 + 3, STEEL, top=4, mid=2, bottom=1, left=3, right=0)
    # shield lock
    for dy, (a, b) in enumerate([(-3, 4), (-3, 4), (-3, 4), (-3, 4), (-3, 4), (-2, 3), (-2, 3), (-1, 2), (0, 1)]):
        y = 12 + dy
        for x in range(CX + a, CX + b + 1):
            t = 4 if dy == 0 else 3 if x == CX + a else 1 if x == CX + b else 2
            c.put(x, y, STEEL[t])
    gem(c, 'diamond', CX, 12, GEM_SAPPHIRE)
    c.put(CX, 19, STEEL[0]); c.put(CX + 1, 19, STEEL[0])     # keyhole under the gem
    return c


def unique():
    c = Canvas()
    draw_lid(c, WOOD_ASH, 'dome', vertical_planks=7)
    seam(c, SILVER, 1)
    first = min(y for y in range(4, LID_FRONT) if lid_inset('dome', y) is not None)
    draw_body(c, WOOD_ASH, 'h')
    for x in range(L + 5, R - 4):
        c.put(x, first + 1, ENAMEL_TEAL[3]); c.put(x, first + 2, ENAMEL_TEAL[1])
    # teal enamel side panels framed in silver
    for (x0, x1) in ((L + 2, L + 7), (R - 7, R - 2)):
        c.box(x0, BODY + 2, x1, BOTTOM - 3, SILVER, top=4, mid=2, bottom=1, left=3, right=1)
        c.box(x0 + 1, BODY + 3, x1 - 1, BOTTOM - 4, ENAMEL_TEAL, top=3, mid=2, bottom=1, left=3, right=1)
        c.put(x0 + 2, BODY + 5, ENAMEL_TEAL[4])
    # silver trim on the lid front edge + corners
    for x in range(L, R + 1): c.put(x, LID_FRONT, SILVER[3])
    for (x0, y0) in ((L, 8), (R - 1, 8), (L, BOTTOM - 1), (R - 1, BOTTOM - 1)):
        c.box(x0, y0, x0 + 1, y0 + 1, SILVER, top=4, mid=3, bottom=1, left=4, right=1)
    # drop aquamarine on a silver plate
    c.box(CX - 2, 11, CX + 3, 21, SILVER, top=4, mid=2, bottom=1, left=3, right=1)
    gem(c, 'drop', CX, 13, GEM_AQUA)
    return c


def epic():
    c = Canvas()
    first = draw_lid(c, WOOD_VIOLET, 'dome', vertical_planks=7)
    seam(c, SILVER_V, 0)
    draw_body(c, WOOD_VIOLET, 'v')
    # curled silver-violet corners
    curl_tl = [(0, 0), (1, 0), (2, 0), (0, 1), (0, 2), (2, 1), (1, 2), (3, 0), (0, 3)]
    for (x0, y0, fx, fy) in ((L, 8, 1, 1), (R, 8, -1, 1), (L, BOTTOM, 1, -1), (R, BOTTOM, -1, -1)):
        for (dx, dy) in curl_tl:
            t = 4 if (dx, dy) in ((0, 0), (1, 0), (0, 1)) else 2 if (dx, dy) in ((2, 1), (1, 2)) else 3
            c.put(x0 + dx * fx, y0 + dy * fy, SILVER_V[t])
    # silver ridge on the dome
    for x in range(L + 4, R - 3): c.put(x, first + 1, SILVER_V[3])
    # two faint rune marks on the body sides
    for (rx, ry) in ((L + 3, 19), (R - 5, 19)):
        for (dx, dy) in ((1, 0), (0, 1), (1, 1), (2, 2), (1, 3), (0, 4)):
            c.put(rx + dx, ry + dy, RUNE_V[0])
        c.put(rx + 1, ry + 1, RUNE_V[1])
    # pointed-arch plate + hexagon amethyst
    for dy, (a, b) in enumerate([(0, 1), (-1, 2), (-2, 3), (-3, 4), (-3, 4), (-3, 4), (-3, 4), (-3, 4), (-3, 4), (-3, 4), (-3, 4)]):
        y = 11 + dy
        for x in range(CX + a, CX + b + 1):
            t = 4 if dy <= 1 or x == CX + a else 1 if x == CX + b or dy == 10 else 2
            c.put(x, y, SILVER_V[t])
    gem(c, 'hexagon', CX, 14, GEM_AMETHYST)
    return c


def legendary():
    c = Canvas()
    first = draw_lid(c, LACQUER, 'dome', planks=False)
    seam(c, GOLD, 1)
    draw_body(c, LACQUER, 'none')
    # gold frame: lid outline, lid front edges, body border
    for y in range(first, LID_FRONT):
        ins = lid_inset('dome', y) or 0
        c.put(L + ins, y, GOLD[3]); c.put(R - ins, y, GOLD[1])
    for x in range(L + 4, R - 3): c.put(x, first, GOLD[4])
    for x in range(L, R + 1): c.put(x, LID_FRONT, GOLD[3]); c.put(x, SEAM - 1, GOLD[1])
    for y in range(LID_FRONT, SEAM): c.put(L, y, GOLD[3]); c.put(R, y, GOLD[1])
    for x in range(L, R + 1): c.put(x, BODY, GOLD[3]); c.put(x, BOTTOM, GOLD[0])
    for y in range(BODY, BOTTOM + 1): c.put(L, y, GOLD[3]); c.put(R, y, GOLD[1])
    # gold crest on top of the lid (raises the silhouette 2 px)
    for (x, y, t) in ((CX - 1, first - 1, 3), (CX, first - 1, 4), (CX + 1, first - 1, 4), (CX + 2, first - 1, 2),
                      (CX, first - 2, 4), (CX + 1, first - 2, 3)):
        c.put(x, y, GOLD[t])
    # gold studs + filigree lines
    for (x, y) in ((L + 3, 12), (R - 3, 12), (L + 3, 19), (R - 3, 19), (L + 3, 25), (R - 3, 25), (L + 7, 8), (R - 7, 8)):
        c.put(x, y, GOLD[4])
    for x in range(L + 5, CX - 3): c.put(x, 23, GOLD[1])
    for x in range(CX + 5, R - 4): c.put(x, 23, GOLD[1])
    # oval amber gem in a gold setting with prongs
    gem_frame(c, 'oval', CX, 14, GOLD)
    for (x, y) in ((CX - 3, 13), (CX + 4, 13), (CX - 3, 20), (CX + 4, 20)): c.put(x, y, GOLD[4])
    gem(c, 'oval', CX, 14, GEM_AMBER)
    return c


def mythic():
    c = Canvas()
    first = draw_lid(c, CRIMSON, 'round', vertical_planks=6)
    seam(c, BLACKMETAL, 0)
    draw_body(c, OBSIDIAN, 'none')
    # black metal frame on the lid front
    for x in range(L, R + 1): c.put(x, LID_FRONT, BLACKMETAL[3]); c.put(x, SEAM - 1, BLACKMETAL[1])
    # horned corners: curve up and out from the lid's top corners (raises the silhouette)
    for (hx, d) in ((L, 1), (R, -1)):
        for (dx, dy, t) in ((0, 3, 2), (1, 3, 1), (0, 2, 3), (1, 2, 2), (0, 1, 3), (1, 1, 2), (2, 1, 1),
                            (0, 0, 3), (1, 0, 2), (-1, -1, 4), (0, -1, 3), (-1, -2, 4), (-2, -3, 4), (-2, -4, 3)):
            c.put(hx + dx * d, first + 1 + dy, BLACKMETAL[t])
    # spiked feet
    for (x0, d) in ((L, 1), (R, -1)):
        c.box(min(x0, x0 + 3 * d), BOTTOM - 3, max(x0, x0 + 3 * d), BOTTOM, BLACKMETAL, top=3, mid=2, bottom=0, left=3, right=1)
        c.put(x0 - d, BOTTOM - 4, BLACKMETAL[4]); c.put(x0, BOTTOM - 4, BLACKMETAL[3])
    # two red veins on the obsidian body
    for (x, y, t) in ((6, 17, 0), (7, 17, 0), (7, 18, 1), (8, 18, 1), (8, 19, 2), (9, 19, 1), (9, 20, 2), (10, 20, 1),
                      (10, 21, 1), (10, 22, 0), (11, 23, 0),
                      (25, 18, 0), (24, 18, 1), (24, 19, 1), (23, 19, 2), (23, 20, 2), (22, 20, 1), (22, 21, 1),
                      (21, 22, 1), (21, 23, 0), (22, 24, 0)):
        c.put(x, y, VEIN[t])
    # spiked black setting + big ruby
    for (x, y, t) in ((CX, 10, 4), (CX + 1, 10, 3), (CX - 5, 16, 4), (CX + 6, 16, 3), (CX, 25, 2), (CX + 1, 25, 1)):
        c.put(x, y, BLACKMETAL[t])
    gem_frame(c, 'bigdiamond', CX, 12, BLACKMETAL)
    gem(c, 'bigdiamond', CX, 12, GEM_RUBY)
    return c


DRAW = {'common': common, 'uncommon': uncommon, 'rare': rare, 'unique': unique, 'epic': epic,
        'legendary': legendary, 'mythic': mythic}


def icon(r): return DRAW[r]().image()


def write_pack(out, with_unique):
    tex = os.path.join(out, 'assets/runeblock/textures/item/casket')
    mod = os.path.join(out, 'assets/runeblock/models/item/casket')
    itm = os.path.join(out, 'assets/runeblock/items')
    for d in (tex, mod, itm): os.makedirs(d, exist_ok=True)
    for r in RARITIES:
        if r == 'unique' and not with_unique: continue
        icon(r).save(os.path.join(tex, f'armour_{r}.png'))
        with open(os.path.join(mod, f'armour_{r}.json'), 'w') as f:
            f.write('{\n  "parent": "minecraft:item/generated",\n  "textures": {\n    "layer0": "runeblock:item/casket/armour_%s"\n  }\n}\n' % r)
        with open(os.path.join(itm, f'casket_armour_{r}.json'), 'w') as f:
            f.write('{\n  "model": {\n    "type": "minecraft:model",\n    "model": "runeblock:item/casket/armour_%s"\n  }\n}\n' % r)


def preview(path, compare=None):
    S, pad = 8, 24
    W = len(RARITIES) * (N * S + pad) + pad
    H = N * S + 130
    sheet = Image.new('RGBA', (W, H), (34, 36, 42, 255))
    d = ImageDraw.Draw(sheet)
    try:
        f = ImageFont.truetype('/System/Library/Fonts/Supplemental/Arial Bold.ttf', 22)
    except OSError:
        f = ImageFont.load_default()
    for i, r in enumerate(RARITIES):
        x = pad + i * (N * S + pad)
        im = icon(r)
        sheet.alpha_composite(im.resize((N * S, N * S), Image.NEAREST), (x, pad))
        name, col = LABEL[r]
        d.text((x, pad + N * S + 10), name, font=f, fill=col)
        for j, sz in enumerate((16, 32)):     # inventory sizes on a slot-grey square (GUI scale 1 and 2)
            bx, by = x + N * S - 80 + j * 40, pad + N * S + 44
            d.rectangle((bx - 2, by - 2, bx + sz + 1, by + sz + 1), fill=(139, 139, 139, 255))
            sheet.alpha_composite(im.resize((sz, sz), Image.NEAREST), (bx, by))
    sheet.save(path)


if __name__ == '__main__':
    ap = argparse.ArgumentParser()
    ap.add_argument('--out'); ap.add_argument('--preview'); ap.add_argument('--unique', action='store_true')
    a = ap.parse_args()
    if a.out: write_pack(a.out, a.unique)
    if a.preview: preview(a.preview)
