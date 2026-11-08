#!/usr/bin/env python3
"""Accessory art for ArcaneSouls 0.52.0 (Ett, dev-chat 2026-11-08 01:24 UTC).

Writes into pack/ (or --out DIR):
  assets/runeblock/textures/item/accessory/<id>.png   4 test accessories (32 px) + 3 empty-slot icons (16 px)
  assets/runeblock/models/item/accessory/<id>.json     item/generated
  assets/runeblock/items/accessory/<id>.json           item_model definitions (runeblock:accessory/<id>)
  assets/runeblock/textures/gui/sprites/tooltip/runeblock_{background,frame}.png (+ .mcmeta)  tooltip_style runeblock:runeblock
  assets/minecraft/textures/gui/container/inventory.png   the player inventory in the RuneBlock panel look, slots 9-12 framed
Usage: python3 tools/accessory_art.py --vanilla <dir with vanilla assets/minecraft/textures/gui> [--out pack] [--preview png]
Palette = asc-mmo-gui UiTheme (soot, bronze FRAME, tarnished GOLD, EMBER, SOUL, bone TEXT).
"""
import argparse, json, math, os
from PIL import Image, ImageDraw

SOOT = (20, 12, 14, 255)
SOOT2 = (28, 18, 20, 255)
INSET = (12, 7, 8, 255)
FRAME = (74, 53, 40, 255)
FRAME_HI = (110, 82, 58, 255)
ORN = (138, 106, 58, 255)
GOLD = (212, 166, 74, 255)
GOLD_HI = (240, 206, 120, 255)
GOLD_LO = (150, 104, 40, 255)
OUT = (34, 20, 14, 255)          # outline: dark umber
ASH = (140, 127, 114, 255)
ASH_LO = (92, 82, 74, 255)


def outline(im, col=OUT):
    """A 1 px outline (4-neighbour) around every opaque pixel, on transparent pixels only."""
    w, h = im.size
    src = im.copy(); s = src.load(); d = im.load()
    for y in range(h):
        for x in range(w):
            if s[x, y][3]: continue
            for dx, dy in ((1, 0), (-1, 0), (0, 1), (0, -1)):
                nx, ny = x + dx, y + dy
                if 0 <= nx < w and 0 <= ny < h and s[nx, ny][3] and s[nx, ny] != col:
                    d[x, y] = col; break
    return im


def ramp(lo, mid, hi, t):
    a, b, u = (hi, mid, t * 2) if t < 0.5 else (mid, lo, (t - 0.5) * 2)
    return tuple(int(a[i] + (b[i] - a[i]) * u) for i in range(3)) + (255,)


def band(im, cx, cy, rx, ry, thick, lo, mid, hi, front_only=False, back_dim=0.65):
    """An elliptical band (a ring seen from above-front): lit at the top-left, darker at the back."""
    px = im.load()
    for y in range(im.size[1]):
        for x in range(im.size[0]):
            dx, dy = (x + 0.5 - cx) / rx, (y + 0.5 - cy) / ry
            r = math.hypot(dx, dy)
            inner = 1 - thick / max(rx, ry)
            if inner <= r <= 1.0:
                back = dy < 0
                if front_only and back: continue
                t = min(1, max(0, (dy + 1) / 2 * 0.7 + (dx + 1) / 2 * 0.3))
                c = ramp(lo, mid, hi, t)
                if back: c = tuple(int(v * back_dim) for v in c[:3]) + (255,)
                px[x, y] = c


def gem(im, cx, cy, r, lo, mid, hi):
    """A cut gem: diamond shape, light facet top-left, a 1 px white glint."""
    px = im.load()
    for y in range(im.size[1]):
        for x in range(im.size[0]):
            dx, dy = x + 0.5 - cx, y + 0.5 - cy
            if abs(dx) + abs(dy) <= r:
                if dx <= 0 and dy <= 0: c = hi
                elif dx > 0 and dy > 0: c = lo
                else: c = mid
                px[x, y] = c
    gx, gy = int(cx - r / 2), int(cy - r / 2)
    if 0 <= gx < im.size[0] and 0 <= gy < im.size[1]: px[gx, gy] = (255, 250, 235, 255)


# ───────────────────────── accessories (32 px) ─────────────────────────

def necklace():
    im = Image.new('RGBA', (32, 32), (0, 0, 0, 0)); px = im.load()
    # chain: a U from the top corners, alternating gold links
    pts = []
    for i in range(0, 61):
        t = i / 60
        x = 6 + 20 * t
        y = 4 + 15 * math.sin(math.pi * t) ** 0.8
        pts.append((int(round(x)), int(round(y))))
    seen = set()
    for n, (x, y) in enumerate(pts):
        if (x, y) in seen: continue
        seen.add((x, y))
        px[x, y] = GOLD_HI if (x + y) % 3 == 0 else GOLD if (x + y) % 3 == 1 else GOLD_LO
    # bail + pendant: an ember gem in a gold setting
    for y in range(18, 21): px[16, y] = GOLD; px[15, y] = GOLD_LO
    setting = Image.new('RGBA', (32, 32)); band(setting, 16, 25, 5.5, 5.5, 1.6, GOLD_LO[:3], GOLD[:3], GOLD_HI[:3])
    im.alpha_composite(setting)
    gem(im, 16, 25, 3.6, (150, 40, 20, 255), (226, 98, 40, 255), (255, 186, 96, 255))
    return outline(im)


def bracelet():
    im = Image.new('RGBA', (32, 32), (0, 0, 0, 0))
    lo, mid, hi = (96, 58, 30), (176, 112, 58), (232, 176, 110)   # bronze
    band(im, 16, 17, 12, 8.5, 3.2, lo, mid, hi)
    px = im.load()
    for sx, sy in ((7, 21), (12, 24), (20, 24), (25, 21)):      # studs on the front
        px[sx, sy] = GOLD_HI; px[sx + 1, sy] = GOLD; px[sx, sy + 1] = GOLD_LO
    gem(im, 16, 25, 2.2, (40, 70, 90, 255), (90, 150, 180, 255), (170, 220, 236, 255))   # spectral stone
    return outline(im)


def ring(stone):
    im = Image.new('RGBA', (32, 32), (0, 0, 0, 0))
    metal, gemcols = stone
    band(im, 16, 20, 9.5, 7, 2.6, *metal)
    # crown + stone on top of the band
    px = im.load()
    for x in range(12, 21): px[x, 14] = GOLD_LO if metal[1][0] > 150 else (110, 110, 120, 255)
    gem(im, 16, 10, 4.6, *gemcols)
    return outline(im)


VIGOR = (((140, 96, 34), (206, 158, 66), (246, 214, 130)),
         ((30, 90, 40, 255), (90, 170, 80, 255), (170, 230, 140, 255)))          # gold band, moss gem
FOCUS = (((90, 90, 104), (160, 160, 176), (226, 226, 236)),
         ((70, 40, 120, 255), (150, 110, 220, 255), (210, 180, 250, 255)))        # silver band, soul gem


# ───────────────────────── empty-slot icons (16 px, muted ash) ─────────────────────────

def slot_icon(kind):
    im = Image.new('RGBA', (16, 16), (0, 0, 0, 0)); px = im.load()
    c, lo = ASH, ASH_LO
    if kind == 'necklace':
        for i in range(0, 41):
            t = i / 40
            x = int(round(3 + 10 * t)); y = int(round(2 + 7 * math.sin(math.pi * t) ** 0.8))
            px[x, y] = c
        for y in (10, 11): px[8, y] = c
        for dx, dy in ((0, 0), (-1, 1), (1, 1), (0, 1), (-2, 2), (2, 2), (-1, 2), (1, 2), (0, 2), (-1, 3), (1, 3), (0, 3), (0, 4)):
            px[8 + dx, 11 + dy] = lo if dy >= 3 else c
    elif kind == 'bracelet':
        for a in range(0, 360, 4):
            r = math.radians(a)
            x = int(round(8 + 6 * math.cos(r) - 0.5)); y = int(round(8 + 4 * math.sin(r)))
            px[x, y] = c if math.sin(r) > -0.2 else lo
            px[x, min(15, y + 1)] = lo
    else:   # ring
        for a in range(0, 360, 4):
            r = math.radians(a)
            x = int(round(8 + 4.5 * math.cos(r) - 0.5)); y = int(round(10 + 3.5 * math.sin(r)))
            px[x, y] = c if math.sin(r) > -0.2 else lo
        for dx, dy in ((0, 0), (-1, 1), (1, 1), (0, 1), (-2, 2), (2, 2), (-1, 2), (1, 2), (0, 2), (0, 3)):
            px[8 + dx - (1 if dx > 0 else 0) * 0, 2 + dy] = c if dy < 2 else lo
    return im


# ───────────────────────── tooltip frame (tooltip_style runeblock:runeblock) ─────────────────────────

def tooltip(vanilla_dir):
    bg = Image.open(os.path.join(vanilla_dir, 'sprites/tooltip/background.png')).convert('RGBA')
    fr = Image.open(os.path.join(vanilla_dir, 'sprites/tooltip/frame.png')).convert('RGBA')
    b = bg.load()
    for y in range(bg.size[1]):
        for x in range(bg.size[0]):
            if b[x, y][3]: b[x, y] = (20, 12, 14, 242)
    out = Image.new('RGBA', fr.size, (0, 0, 0, 0)); o = out.load(); f = fr.load()
    h = fr.size[1]
    for y in range(h):
        for x in range(fr.size[0]):
            if f[x, y][3]:
                t = y / (h - 1)
                c = tuple(int(GOLD[i] + (FRAME_HI[i] - GOLD[i]) * t) for i in range(3))
                o[x, y] = c + (255,)
    # gold corner ornaments (inside the 10 px nine-slice border, so they never stretch)
    for cx, cy, sx, sy in ((9, 9, 1, 1), (90, 9, -1, 1), (9, 90, 1, -1), (90, 90, -1, -1)):
        for i in range(4):
            o[cx + sx * i, cy] = GOLD_HI; o[cx, cy + sy * i] = GOLD_HI
        o[cx + sx, cy + sy] = GOLD
        o[cx + sx * 2, cy + sy * 2] = GOLD_LO
    return bg, out


# ───────────────────────── the inventory screen ─────────────────────────

SLOT_ACC = [(7 + 18 * c, 83) for c in range(4)]   # inventory 9-12: the first main-inventory row, left 4


def slot_box(d, x, y, accent=False):
    """A slot: 18x18 at (x, y) with the 16x16 inner at +1."""
    d.rectangle((x, y, x + 17, y + 17), fill=FRAME)
    d.line((x, y, x + 16, y), fill=OUT); d.line((x, y, x, y + 16), fill=OUT)            # inset: dark top-left
    d.line((x + 1, y + 17, x + 17, y + 17), fill=FRAME_HI); d.line((x + 17, y + 1, x + 17, y + 17), fill=FRAME_HI)
    d.rectangle((x + 1, y + 1, x + 16, y + 16), fill=INSET)
    if accent:
        d.rectangle((x, y, x + 17, y + 17), outline=GOLD)
        for cx, cy in ((x, y), (x + 17, y), (x, y + 17), (x + 17, y + 17)): d.point((cx, cy), fill=GOLD_HI)


def inventory(vanilla_dir):
    van = Image.open(os.path.join(vanilla_dir, 'container/inventory.png')).convert('RGBA')
    im = van.copy()
    d = ImageDraw.Draw(im)
    W, H = 176, 166
    d.rectangle((0, 0, W - 1, H - 1), fill=(0, 0, 0, 0))
    # panel: soot body, bronze rim, gold corner filigree (the chest-menu panel look)
    d.rounded_rectangle((0, 0, W - 1, H - 1), radius=3, fill=FRAME)
    d.rounded_rectangle((1, 1, W - 2, H - 2), radius=2, fill=OUT)
    d.rectangle((3, 3, W - 4, H - 4), fill=SOOT)
    for y in range(3, H - 3):   # faint vertical gradient
        t = (y - 3) / (H - 7)
        c = tuple(int(SOOT2[i] + (SOOT[i] - SOOT2[i]) * t) for i in range(3)) + (255,)
        d.line((3, y, W - 4, y), fill=c)
    d.rectangle((2, 2, W - 3, H - 3), outline=FRAME)
    for cx, cy, sx, sy in ((2, 2, 1, 1), (W - 3, 2, -1, 1), (2, H - 3, 1, -1), (W - 3, H - 3, -1, -1)):
        for i in range(6): d.point((cx + sx * i, cy), fill=GOLD); d.point((cx, cy + sy * i), fill=GOLD)
        d.point((cx + sx, cy + sy), fill=GOLD_HI); d.point((cx + sx * 2, cy + sy * 2), fill=ORN)
    # player picture well
    d.rectangle((25, 7, 77, 77), fill=FRAME)
    d.rectangle((26, 8, 76, 76), fill=(6, 3, 4, 255))
    # armour 4 + off-hand
    for r in range(4): slot_box(d, 7, 7 + 18 * r)
    slot_box(d, 76, 61)
    # 2x2 crafting + arrow + result (kept: the screen draws items there)
    for r in range(2):
        for c in range(2): slot_box(d, 97 + 18 * c, 17 + 18 * r)
    for i in range(8):   # arrow in bronze
        d.line((135 + i, 36, 135 + i, 36), fill=ORN)
    d.polygon([(135, 34), (143, 34), (143, 31), (148, 36), (143, 41), (143, 38), (135, 38)], fill=ORN)
    slot_box(d, 153, 27)
    # divider line between the top part and the bag
    d.line((7, 80, W - 8, 80), fill=FRAME)
    for x in (W // 2 - 3, W // 2, W // 2 + 3): d.point((x, 80), fill=GOLD)
    # bag 3x9 + hotbar
    for r in range(3):
        for c in range(9): slot_box(d, 7 + 18 * c, 83 + 18 * r, accent=(r == 0 and c < 4))
    d.line((7, 138, W - 8, 138), fill=FRAME)
    for c in range(9): slot_box(d, 7 + 18 * c, 141)
    return im


def write(out, rel, img=None, text=None):
    p = os.path.join(out, rel)
    os.makedirs(os.path.dirname(p), exist_ok=True)
    if img is not None: img.save(p)
    else:
        with open(p, 'w') as f: f.write(text)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--vanilla', required=True, help='dir holding vanilla container/inventory.png + sprites/tooltip/*')
    ap.add_argument('--out', default='pack')
    ap.add_argument('--preview')
    a = ap.parse_args()
    arts = {'test_necklace': necklace(), 'test_bracelet': bracelet(), 'test_ring_vigor': ring(VIGOR), 'test_ring_focus': ring(FOCUS),
            'slot_necklace': slot_icon('necklace'), 'slot_bracelet': slot_icon('bracelet'), 'slot_ring': slot_icon('ring')}
    for k, img in arts.items():
        write(a.out, f'assets/runeblock/textures/item/accessory/{k}.png', img)
        write(a.out, f'assets/runeblock/models/item/accessory/{k}.json', text=json.dumps(
            {"parent": "minecraft:item/generated", "textures": {"layer0": f"runeblock:item/accessory/{k}"}}, indent=2) + '\n')
        write(a.out, f'assets/runeblock/items/accessory/{k}.json', text=json.dumps(
            {"model": {"type": "minecraft:model", "model": f"runeblock:item/accessory/{k}"}}, indent=2) + '\n')
    bg, fr = tooltip(a.vanilla)
    write(a.out, 'assets/runeblock/textures/gui/sprites/tooltip/runeblock_background.png', bg)
    write(a.out, 'assets/runeblock/textures/gui/sprites/tooltip/runeblock_frame.png', fr)
    write(a.out, 'assets/runeblock/textures/gui/sprites/tooltip/runeblock_background.png.mcmeta', text=json.dumps(
        {"gui": {"scaling": {"type": "nine_slice", "width": 100, "height": 100, "border": 9}}}, indent=2) + '\n')
    write(a.out, 'assets/runeblock/textures/gui/sprites/tooltip/runeblock_frame.png.mcmeta', text=json.dumps(
        {"gui": {"scaling": {"type": "nine_slice", "width": 100, "height": 100, "border": 10, "stretch_inner": True}}}, indent=2) + '\n')
    inv = inventory(a.vanilla)
    write(a.out, 'assets/minecraft/textures/gui/container/inventory.png', inv)
    if a.preview: preview(arts, inv, bg, fr, a.preview)


def preview(arts, inv, bg, fr, path):
    """Inventory at 3x with the slot icons/accessories drawn in, plus the sprites at 8x."""
    S = 3
    shot = inv.crop((0, 0, 176, 166)).resize((176 * S, 166 * S), Image.NEAREST)
    worn = ['test_necklace', 'slot_bracelet', 'test_ring_vigor', 'slot_ring']
    for (x, y), k in zip(SLOT_ACC, worn):
        icon = arts[k].resize((16 * S, 16 * S), Image.NEAREST)
        shot.alpha_composite(icon, ((x + 1) * S, (y + 1) * S))
    sheet = Image.new('RGBA', (176 * S + 20 + 4 * 8 * 32, 166 * S + 240), (40, 40, 44, 255))
    sheet.alpha_composite(shot, (0, 0))
    for i, k in enumerate(arts):
        big = arts[k].resize((256, 256) if arts[k].size[0] == 32 else (128, 128), Image.NEAREST)
        sheet.alpha_composite(big, (176 * S + 20 + (i % 4) * 256, 0) if i < 4 else (176 * S + 20 + (i - 4) * 160 + 64, 300))
    # a tooltip mock: background + frame stretched to 160x90
    tip = Image.new('RGBA', (160, 70), (0, 0, 0, 0))
    def nine(src, w, h, border):
        out = Image.new('RGBA', (w, h)); sw, sh = src.size
        for (sx0, sx1, dx0, dx1) in ((0, border, 0, border), (border, sw - border, border, w - border), (sw - border, sw, w - border, w)):
            for (sy0, sy1, dy0, dy1) in ((0, border, 0, border), (border, sh - border, border, h - border), (sh - border, sh, h - border, h)):
                piece = src.crop((sx0, sy0, sx1, sy1)).resize((dx1 - dx0, dy1 - dy0), Image.NEAREST)
                out.alpha_composite(piece, (dx0, dy0))
        return out
    tip.alpha_composite(nine(bg, 160, 70, 9)); tip.alpha_composite(nine(fr, 160, 70, 10))
    sheet.alpha_composite(tip.resize((480, 210), Image.NEAREST), (20, 166 * S + 15))
    sheet.save(path)


if __name__ == '__main__':
    main()
