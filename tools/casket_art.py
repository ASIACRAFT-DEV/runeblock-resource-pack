#!/usr/bin/env python3
"""32 px Armour Casket icons, one per rarity (Ett 2026-11-09, reference docs/spec/ett-armour-caskets-reference-2026-11-09.png:
Common wood + iron, Uncommon wood + green trim + emerald, Rare dark wood + steel-blue trim + cyan crystal, Epic purple +
gold trim + violet runes, Legendary black + gold + amber runes, Mythic blackstone + molten red cracks).

A chest seen slightly from above: lid top (lighter), lid front, a seam, the body front, corner caps, a front plate with
the rarity's gem, light from the top-left, a one-pixel outline in the darkest step of the neighbouring material.

v2 (Ett 05:35 UTC 2026-11-09): the gem is the brightest pixel (trim highlights capped below it, no glints); fine detail
dropped (Uncommon vines, Epic/Legendary rune dots, Mythic cracks); Rare body steel-blue; Mythic = a clear split, crimson
lid over a black body; Epic trim silver-violet so gold only means Legendary; gem shapes vary: Uncommon round, Rare
diamond, Epic hexagon, Legendary round, Mythic diamond (Common keeps the iron keyhole).

Usage: python3 -I tools/casket_art.py [--out pack] [--preview sheet.png]
  --out pack     writes pack/assets/runeblock/textures/item/casket/armour_<rarity>.png (+ models/items json)
  --preview      writes a labelled sheet (8x) with inventory-size copies
"""
import argparse, os
from PIL import Image, ImageDraw, ImageFont

N = 32
RARITIES = ['common', 'uncommon', 'rare', 'epic', 'legendary', 'mythic']
LABEL = {'common': ('Common', (220, 220, 220)), 'uncommon': ('Uncommon', (85, 255, 85)), 'rare': ('Rare', (85, 255, 255)),
         'epic': ('Epic', (255, 85, 255)), 'legendary': ('Legendary', (255, 170, 0)), 'mythic': ('Mythic', (255, 85, 85))}


def hexes(*h): return [tuple(int(x[i:i + 2], 16) for i in (1, 3, 5)) for x in h]


# 5-step ramps, dark -> light
PAL = {
    'common': dict(body=hexes('#3a2210', '#5c3519', '#7a4a26', '#9a6132', '#b97b44'),
                   trim=hexes('#2c2c2c', '#555555', '#858585', '#b4b4b4', '#dedede'),
                   gem=hexes('#1e1e1e', '#3a3a3a', '#555555', '#3a3a3a', '#1e1e1e'), rune=None, crack=None),
    'uncommon': dict(body=hexes('#33200f', '#563318', '#744624', '#93602f', '#b07a3d'),
                     trim=hexes('#163d1f', '#24602f', '#348a42', '#4fb35b', '#86da86'),
                     gem=hexes('#0c4a1c', '#13802e', '#25c04a', '#6cf08a', '#d4ffdc'), rune=None, crack=None, vine=True),
    'rare': dict(body=hexes('#16202c', '#24364a', '#355068', '#486c88', '#5e87a6'),
                 trim=hexes('#1a1f26', '#3a424d', '#5e6874', '#8a95a1', '#b9c3cc'),
                 gem=hexes('#0b4d78', '#1683c4', '#2fb6f0', '#86e2ff', '#e4fbff'), rune=None, crack=None),
    'epic': dict(body=hexes('#1d0d33', '#311656', '#45207a', '#5b2d9c', '#7440bd'),
                 trim=hexes('#3a3346', '#625a73', '#8f86a3', '#b9b1cc', '#ddd6ec'),
                 gem=hexes('#3d0d73', '#6a1fbf', '#9a4cff', '#c99bff', '#f2e4ff'),
                 rune=hexes('#b07cff', '#e0c8ff'), crack=None, glint=(190, 120, 255)),
    'legendary': dict(body=hexes('#0d0c0b', '#191714', '#25221e', '#322e28', '#403a32'),
                      trim=hexes('#6b4a08', '#a3760f', '#d8a522', '#f5cb46', '#fff2a8'),
                      gem=hexes('#7a3a00', '#c06a06', '#f29a14', '#ffc95a', '#fff1c2'),
                      rune=hexes('#ffb020', '#ffe680'), crack=None, glint=(255, 210, 80)),
    'mythic': dict(body=hexes('#08080a', '#111114', '#1a1a1e', '#242429', '#2e2e34'),
                   lid=hexes('#4a0608', '#78090d', '#a51014', '#cc1e1e', '#e8403a'),
                   trim=hexes('#1c1c1f', '#333338', '#4c4c53', '#68686f', '#8c8c94'),
                   gem=hexes('#5a0606', '#a00d0d', '#e01e1e', '#ff6a4a', '#ffd0b8'),
                   rune=None, crack=hexes('#a01010', '#ff3a1e', '#ffa060'), glint=(255, 70, 40)),
}


SHAPE = {'uncommon': 'round', 'rare': 'diamond', 'epic': 'hexagon', 'legendary': 'round', 'mythic': 'diamond'}
ROWS = {  # (y, x0 offset from cx, x1 offset from cx) per row
    'round':   [(14, 0, 1), (15, -1, 2), (16, -1, 2), (17, -1, 2), (18, 0, 1)],
    'diamond': [(13, 0, 1), (14, -1, 2), (15, -2, 3), (16, -2, 3), (17, -1, 2), (18, 0, 1)],
    'hexagon': [(14, -1, 2), (15, -2, 3), (16, -2, 3), (17, -2, 3), (18, -1, 2)],
}


def gem_cells(shape, cx):
    """Gem pixels with a ramp index: light from the top-left, darkest bottom-right."""
    rows = ROWS[shape]
    y0, y1 = rows[0][0], rows[-1][0]
    out = {}
    for (y, a, b) in rows:
        for x in range(cx + a, cx + b + 1):
            d = (x - (cx + a)) / max(1, b - a) + (y - y0) / max(1, y1 - y0)   # 0 (top-left) .. 2 (bottom-right)
            out[(x, y)] = 4 if d < 0.45 else 3 if d < 0.9 else 2 if d < 1.35 else 1 if d < 1.75 else 0
    return out


def gem_highlight(shape, cx):
    rows = ROWS[shape]
    y, a, b = rows[1]
    return cx + a + (1 if b - a > 2 else 0), y


def draw(rarity):
    p = PAL[rarity]
    im = Image.new('RGBA', (N, N), (0, 0, 0, 0))
    px = {}

    def put(x, y, c):
        if 0 <= x < N and 0 <= y < N: px[(x, y)] = c

    def rect(x0, y0, x1, y1, ramp, light_from_top=True):
        for y in range(y0, y1 + 1):
            for x in range(x0, x1 + 1):
                t = 3 if light_from_top else 2
                if y == y0: t = 4
                elif y >= y1 - 1: t = 1
                elif x == x0: t = min(t, 3)
                elif x == x1: t = 1
                put(x, y, ramp[t])

    B, T, G = p['body'], list(p['trim']), p['gem']
    LID = p.get('lid', B)
    T[4] = T[3]            # v2: trim never outshines the gem
    # geometry: lid top y 6..9 (shifted 1 px right = seen from above), lid front y 10..14, seam y 15, body y 16..27
    L, R = 4, 27
    # lid top: lighter strip, rounded ends
    for y in range(6, 10):
        inset = 2 if y == 6 else 1 if y == 7 else 0
        for x in range(L + 1 + inset, R + 1 - inset):
            put(x, y, LID[4] if y < 8 else LID[3])
    # planks on the lid top
    for x in range(L + 6, R, 6):
        for y in range(7, 10): put(x, y, LID[2])
    rect(L, 10, R, 14, LID)
    for y in range(15, 16):
        for x in range(L, R + 1): put(x, y, T[0])
    rect(L, 16, R, 27, B, light_from_top=False)
    # vertical planks on the body
    for x in range(L + 5, R, 5):
        for y in range(17, 27): put(x, y, B[1])
    # trim: corner caps only (top corners of the lid, bottom corners of the body), plus side straps on the lid front
    caps = [(L, 6, L + 3, 11), (R - 3, 6, R, 11), (L, 23, L + 3, 27), (R - 3, 23, R, 27)]
    for (x0, y0, x1, y1) in caps:
        for y in range(y0, y1 + 1):
            for x in range(x0, x1 + 1):
                if y < 10 and ((x0 == L and x < L + 1 + (2 if y == 6 else 1 if y == 7 else 0)) or
                               (x0 != L and x > R - (2 if y == 6 else 1 if y == 7 else 0))):
                    continue
                t = 4 if y == y0 else 1 if y == y1 else 3 if x == x0 else 1 if x == x1 else 2
                put(x, y, T[t])
    for x in (L, R):   # thin edge strip between the caps
        for y in list(range(12, 15)) + list(range(16, 23)): put(x, y, T[2] if x == L else T[1])
    for x in range(L + 4, R - 3):
        put(x, 14, T[2]); put(x, 16, T[3])
    # front plate + gem / keyhole
    cx = (L + R) // 2
    for y in range(12, 22):
        for x in range(cx - 3, cx + 5):
            t = 4 if y == 12 else 1 if y == 21 else 3 if x == cx - 3 else 1 if x == cx + 4 else 2
            put(x, y, T[t])
    if rarity == 'common':
        for (x, y) in ((cx, 15), (cx + 1, 15), (cx, 16), (cx + 1, 16), (cx, 17), (cx + 1, 17), (cx, 18), (cx + 1, 18)):
            put(x, y, G[1])
        put(cx, 15, G[0]); put(cx + 1, 18, G[0])
    else:
        for (x, y), t in gem_cells(SHAPE[rarity], cx).items(): put(x, y, G[t])
        hx, hy = gem_highlight(SHAPE[rarity], cx)
        put(hx, hy, (255, 255, 255))     # v2: the single brightest pixel of the icon
    # outline: darkest step of the neighbouring material, on transparent cells next to the shape
    shape = set(px)
    for (x, y) in list(shape):
        for dx, dy in ((1, 0), (-1, 0), (0, 1), (0, -1)):
            q = (x + dx, y + dy)
            if q not in shape and 0 <= q[0] < N and 0 <= q[1] < N:
                c = px[(x, y)]
                px[q] = tuple(max(0, int(v * 0.35)) for v in c)
    for (x, y), c in px.items(): im.putpixel((x, y), c + (255,))
    return im


def write_pack(out):
    tex = os.path.join(out, 'assets/runeblock/textures/item/casket')
    mod = os.path.join(out, 'assets/runeblock/models/item/casket')
    itm = os.path.join(out, 'assets/runeblock/items')
    for d in (tex, mod, itm): os.makedirs(d, exist_ok=True)
    for r in RARITIES:
        draw(r).save(os.path.join(tex, f'armour_{r}.png'))
        with open(os.path.join(mod, f'armour_{r}.json'), 'w') as f:
            f.write('{\n  "parent": "minecraft:item/generated",\n  "textures": {\n    "layer0": "runeblock:item/casket/armour_%s"\n  }\n}\n' % r)
        with open(os.path.join(itm, f'casket_armour_{r}.json'), 'w') as f:
            f.write('{\n  "model": {\n    "type": "minecraft:model",\n    "model": "runeblock:item/casket/armour_%s"\n  }\n}\n' % r)


def preview(path):
    S, pad = 8, 24
    W = len(RARITIES) * (N * S + pad) + pad
    H = N * S + 120
    sheet = Image.new('RGBA', (W, H), (34, 36, 42, 255))
    d = ImageDraw.Draw(sheet)
    try:
        f = ImageFont.truetype('/System/Library/Fonts/Supplemental/Arial Bold.ttf', 22)
    except OSError:
        f = ImageFont.load_default()
    for i, r in enumerate(RARITIES):
        x = pad + i * (N * S + pad)
        sheet.alpha_composite(draw(r).resize((N * S, N * S), Image.NEAREST), (x, pad))
        name, col = LABEL[r]
        d.text((x, pad + N * S + 10), name, font=f, fill=col)
        # inventory-size copies: 16 px (GUI 1) and 32 px (GUI 2) on a slot-grey square
        for j, sz in enumerate((16, 32)):
            bx, by = x + N * S - 80 + j * 40, pad + N * S + 44
            d.rectangle((bx - 2, by - 2, bx + sz + 1, by + sz + 1), fill=(139, 139, 139, 255))
            sheet.alpha_composite(draw(r).resize((sz, sz), Image.NEAREST), (bx, by))
    sheet.save(path)


if __name__ == '__main__':
    ap = argparse.ArgumentParser()
    ap.add_argument('--out'); ap.add_argument('--preview')
    a = ap.parse_args()
    if a.out: write_pack(a.out)
    if a.preview: preview(a.preview)
