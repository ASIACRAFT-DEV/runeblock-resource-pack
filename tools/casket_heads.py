#!/usr/bin/env python3
"""Player-head-shaped Armour Caskets (Ett 07:21 UTC 2026-11-21: "Convert the custom casket icon into a player head item
and show an example of it before pushing"). Same six rarities, materials, locks and gems as the flat v3 icons
(tools/casket_art_v3.py, palette imported from there), drawn on the six faces of a cube the size of a player head.

Route (see the report in the session that made this): a plain block model, NOT a real player_head item.
  - geometry  = the vanilla skull: cube [4,0,4]-[12,8,12] (8 px) + a hat-style shell [3.75,-0.25,3.75]-[12.25,8.25,12.25]
                for the metal trim, lock and gem (transparent where empty)
  - display   = vanilla 1.21.11 models/item/template_skull.json (gui / fixed / ground / thirdperson_righthand), copied
                verbatim, plus "head" from item/generated.json (unused: caskets are PAPER, not equippable)
  - texture   = one 64x64 atlas per rarity, 16x16 per face (twice the 8x8 of a player skin): row 0 = base south (front),
                east, north (back), west; row 1 = base up, down; rows 2-3 = the shell, same order
  - front     = south face, like the face of a skull and the front of a generated item

Pack files (with --out pack): textures/item/casket/head_<r>.png, models/item/casket/head_<r>.json,
items/casket_head_<r>.json → item model id runeblock:casket_head_<r>. Nothing is overwritten: the flat
casket_armour_<r> icons stay in the pack, so going back is a gear.yml change only.

Usage:
  python3 -I tools/casket_heads.py                       # writes everything to ./casket-heads-preview/
  python3 -I tools/casket_heads.py --out DIR             # textures + models + items under DIR/assets/runeblock/...
  python3 -I tools/casket_heads.py --out pack            # the pack itself (do not run until Ett approves)
  python3 -I tools/casket_heads.py --renders DIR [--mc-jar client.jar]   # example renders (inventory, 3D, ground, hotbar)
"""
import argparse, json, math, os, sys, zipfile, io
import numpy as np
from PIL import Image, ImageDraw, ImageFont

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import casket_art_v3 as v3          # noqa: E402  (palette + gem shapes, one source of truth)
from casket_art_v3 import (WOOD_WORN, WOOD_OAK, WOOD_BLUE, WOOD_VIOLET, LACQUER, OBSIDIAN, CRIMSON, IRON_RUST, IRON,  # noqa: E402
                           STEEL, SILVER_V, GOLD, BLACKMETAL, ENAMEL_GREEN, GEM_EMERALD, GEM_SAPPHIRE,
                           GEM_AMETHYST, GEM_AMBER, GEM_RUBY, VEIN, RUNE_V, LABEL)

F = 16                                   # pixels per face
RARITIES = ['common', 'uncommon', 'rare', 'epic', 'legendary', 'mythic']
SIDES = ['south', 'east', 'north', 'west']          # atlas row order (south = front)
LID_END, SEAM = 5, 6                     # lid rows 0..5, seam row 6, body rows 7..15 on every side face
KEYHOLE = (20, 14, 16)


# ───────────────────────────── canvas ─────────────────────────────

class Face:
    """A 16x16 face, drawn as seen from outside the cube with its top edge up (top face: north edge up)."""
    def __init__(self, fill=None):
        self.px = {}
        if fill is not None:
            for y in range(F):
                for x in range(F): self.px[(x, y)] = fill

    def put(self, x, y, c):
        if 0 <= x < F and 0 <= y < F and c is not None: self.px[(x, y)] = tuple(c[:3])

    def get(self, x, y): return self.px.get((x, y))

    def box(self, x0, y0, x1, y1, rp, top=4, mid=2, bottom=1, left=3, right=1):
        for y in range(y0, y1 + 1):
            for x in range(x0, x1 + 1):
                t = top if y == y0 else bottom if y == y1 else left if x == x0 else right if x == x1 else mid
                self.put(x, y, rp[t])

    def mirror(self):
        m = Face()
        m.px = {(F - 1 - x, y): c for (x, y), c in self.px.items()}
        return m

    def image(self):
        im = Image.new('RGBA', (F, F), (0, 0, 0, 0))
        for (x, y), c in self.px.items(): im.putpixel((x, y), c + (255,))
        return im


def rng(seed):
    return np.random.default_rng(seed)


# ───────────────────────────── base layer (wood, seam) ─────────────────────────────

def side_base(lid, body, seed, plank='h', seam_c=None, edge=True):
    """A chest side: lid rows 0-5, seam row 6, body 7-15. Light from the top-left, like v3."""
    r = rng(seed)
    f = Face()
    for y in range(F):
        for x in range(F):
            if y <= LID_END:
                t = 4 if y == 0 else 1 if y == LID_END else 3
                rp = lid
            elif y == SEAM:
                f.put(x, y, seam_c or body[0]); continue
            else:
                t = 1 if y == SEAM + 1 else 0 if y == F - 1 else 2
                rp = body
            if t in (2, 3) and r.random() < 0.16: t += 1 if r.random() < 0.5 else -1
            f.put(x, y, rp[t])
    if plank == 'h':
        for y in (10, 13):
            for x in range(F): f.put(x, y, body[1])
            for x in range(F):
                if r.random() < 0.5: f.put(x, y + 1, body[3])
    elif plank == 'v':
        for x in (4, 8, 12):
            for y in range(SEAM + 2, F - 1): f.put(x, y, body[1])
    if plank != 'none':   # one plank line across the lid
        for x in (5, 11):
            for y in range(1, LID_END): f.put(x, y, lid[2])
    if edge:              # cube edges a step darker so the corners read
        for y in range(F):
            for x in (0, F - 1):
                c = f.get(x, y)
                f.put(x, y, tuple(int(v * 0.78) for v in c))
    return f


def top_base(lid, seed, plank=True):
    """Lid top: planks running east-west, lighter toward the north-west (the light)."""
    r = rng(seed)
    f = Face()
    for y in range(F):
        for x in range(F):
            t = 4 if (x + y) < 9 else 3
            if r.random() < 0.15: t -= 1
            f.put(x, y, lid[t])
    if plank:
        for y in (5, 10):
            for x in range(F): f.put(x, y, lid[2])
    for i in range(F):                      # rim
        f.put(i, 0, lid[4]); f.put(0, i, lid[4]); f.put(i, F - 1, lid[1]); f.put(F - 1, i, lid[1])
    return f


def bottom_base(body):
    f = Face(body[1])
    for y in (5, 10):
        for x in range(F): f.put(x, y, body[0])
    return f


# ───────────────────────────── shell layer helpers ─────────────────────────────

def gem(f, shape, cx, y0, rp, frame=None):
    """v3's gem (and optional one-pixel setting) on a 16 px face; cx = left of the two centre columns."""
    if frame: v3.gem_frame(f, shape, cx, y0, frame)
    v3.gem(f, shape, cx, y0, rp)


def corner_caps(f, rp, size=2, which=('tl', 'tr', 'bl', 'br')):
    s = size - 1
    spots = {'tl': (0, 0), 'tr': (F - 1 - s, 0), 'bl': (0, F - 1 - s), 'br': (F - 1 - s, F - 1 - s)}
    for k in which:
        x0, y0 = spots[k]
        f.box(x0, y0, x0 + s, y0 + s, rp, top=4, mid=2, bottom=1, left=3, right=1)


def l_brackets(f, rp, inner, n=4, rows=(0, F - 1)):
    """Iron L-brackets on the four corners with an enamel pixel inside each bend."""
    for (cx, dx) in ((0, 1), (F - 1, -1)):
        for (cy, dy) in ((rows[0], 1), (rows[1], -1)):
            for i in range(n):
                f.put(cx + i * dx, cy, rp[3 if dy == 1 else 1])
                f.put(cx, cy + i * dy, rp[3 if dx == 1 else 1])
            f.put(cx, cy, rp[4])
            f.put(cx + dx, cy + dy, inner)


def rivets(f, pts, rp):
    for (x, y) in pts: f.put(x, y, rp[4])


def keyhole(f, x, y):
    f.put(x, y, KEYHOLE); f.put(x + 1, y, KEYHOLE); f.put(x, y + 1, KEYHOLE)


# ───────────────────────────── rarities ─────────────────────────────
# each returns {'base': {side: Face}, 'shell': {side: Face}} for side in south east north west up down

def empty_shell(): return {s: Face() for s in SIDES + ['up', 'down']}


def common():
    base = {s: side_base(WOOD_WORN, WOOD_WORN, 11 + i, 'h', IRON_RUST[0]) for i, s in enumerate(SIDES)}
    base['up'] = top_base(WOOD_WORN, 17); base['down'] = bottom_base(WOOD_WORN)
    # worn: chipped lid corner on the front + a knot + a crack on the lid
    for (x, y) in ((F - 1, 0), (F - 2, 0), (F - 1, 1)): base['south'].put(x, y, WOOD_WORN[0])
    base['south'].put(3, 12, WOOD_WORN[0]); base['south'].put(4, 12, WOOD_WORN[1])
    for (x, y) in ((9, 3), (10, 4), (10, 5), (11, 6)): base['up'].put(x, y, WOOD_WORN[1])
    sh = empty_shell()
    for s in SIDES: corner_caps(sh[s], IRON_RUST, 2, ('bl', 'br'))
    corner_caps(sh['south'], IRON_RUST, 2, ('tl',))           # one cap left on the lid, the other fell off
    corner_caps(sh['up'], IRON_RUST, 2, ('bl',))
    # plain hasp: tongue from the lid over the seam into a lock block with a keyhole
    f = sh['south']
    f.box(7, 2, 8, 6, IRON_RUST, top=3, mid=2, bottom=1, left=3, right=1)
    f.box(5, 7, 10, 11, IRON_RUST, top=4, mid=3, bottom=1, left=4, right=1)
    keyhole(f, 7, 8)
    # one rusty band round the body
    for s in SIDES:
        for x in range(2, F - 2):
            if sh[s].get(x, 12) is None: sh[s].put(x, 12, IRON_RUST[2])
    rivets(sh['north'], [(4, 2), (11, 2)], IRON_RUST)          # hinge nails
    return {'base': base, 'shell': sh}


def uncommon():
    base = {s: side_base(WOOD_OAK, WOOD_OAK, 21 + i, 'v', IRON[0]) for i, s in enumerate(SIDES)}
    base['up'] = top_base(WOOD_OAK, 27); base['down'] = bottom_base(WOOD_OAK)
    sh = empty_shell()
    for s in SIDES:
        l_brackets(sh[s], IRON, ENAMEL_GREEN[3])
        for x in range(4, F - 4):                     # green enamel band along the lid lip
            sh[s].put(x, LID_END - 1, ENAMEL_GREEN[2]); sh[s].put(x, LID_END, ENAMEL_GREEN[1])
    l_brackets(sh['up'], IRON, ENAMEL_GREEN[3])
    f = sh['south']                                    # riveted plate + round emerald
    f.box(5, 4, 10, 11, IRON, top=4, mid=2, bottom=1, left=3, right=1)
    rivets(f, [(6, 5), (9, 5), (6, 10), (9, 10)], IRON)
    gem(f, 'round', 7, 5, GEM_EMERALD)
    rivets(sh['north'], [(4, 1), (11, 1)], IRON)
    return {'base': base, 'shell': sh}


def rare():
    base = {s: side_base(WOOD_BLUE, WOOD_BLUE, 31 + i, 'h', STEEL[0]) for i, s in enumerate(SIDES)}
    base['up'] = top_base(WOOD_BLUE, 37); base['down'] = bottom_base(WOOD_BLUE)
    sh = empty_shell()
    # two steel straps: down the front, over the lid, down the back (front/back/top columns 2-3 and 12-13)
    for s in ('south', 'north', 'up'):
        for sx in (2, 12):
            for y in range(F):
                sh[s].put(sx, y, STEEL[3]); sh[s].put(sx + 1, y, STEEL[1])
            for y in (1, 8, 14): sh[s].put(sx, y, STEEL[4])
    for s in ('east', 'west'):                         # bevelled caps + a handle on the ends
        corner_caps(sh[s], STEEL, 3)
        sh[s].box(5, 8, 10, 10, STEEL, top=4, mid=0, bottom=1, left=3, right=1)
        for x in range(6, 10): sh[s].px.pop((x, 9), None)          # hollow ring handle
    f = sh['south']                                    # shield lock with a sapphire
    for dy, (a, b) in enumerate([(5, 10), (5, 10), (5, 10), (5, 10), (5, 10), (6, 9), (6, 9), (7, 8)]):
        for x in range(a, b + 1):
            t = 4 if dy == 0 else 3 if x == a else 1 if x == b else 2
            f.put(x, 3 + dy, STEEL[t])
    gem(f, 'diamond', 7, 3, GEM_SAPPHIRE)
    f.put(7, 11, KEYHOLE); f.put(8, 11, KEYHOLE)
    return {'base': base, 'shell': sh}


RUNES = [[(1, 0), (0, 1), (1, 1), (2, 2), (1, 3), (0, 4)],          # v3 rune
         [(0, 0), (2, 0), (1, 1), (1, 2), (0, 3), (2, 3), (1, 4)],
         [(0, 0), (1, 0), (2, 0), (1, 1), (0, 2), (2, 2), (1, 3), (1, 4)]]


def epic():
    base = {s: side_base(WOOD_VIOLET, WOOD_VIOLET, 41 + i, 'v', SILVER_V[0]) for i, s in enumerate(SIDES)}
    base['up'] = top_base(WOOD_VIOLET, 47, plank=False); base['down'] = bottom_base(WOOD_VIOLET)
    sh = empty_shell()
    curl = [(0, 0), (1, 0), (2, 0), (3, 0), (0, 1), (0, 2), (0, 3), (2, 1), (1, 2), (2, 2)]
    for s in SIDES + ['up']:
        for (x0, y0, fx, fy) in ((0, 0, 1, 1), (F - 1, 0, -1, 1), (0, F - 1, 1, -1), (F - 1, F - 1, -1, -1)):
            for (dx, dy) in curl:
                t = 4 if (dx, dy) in ((0, 0), (1, 0), (0, 1)) else 1 if (dx, dy) == (2, 2) else 3
                sh[s].put(x0 + dx * fx, y0 + dy * fy, SILVER_V[t])
    for s in SIDES:                                    # silver-violet ridge on the lid lip ("dome" edge)
        for x in range(4, F - 4): sh[s].put(x, LID_END, SILVER_V[3])
    for s, (ra, rb) in (('east', (0, 1)), ('west', (2, 0)), ('north', (1, 2))):   # faint runes on the other sides
        for k, rx in ((ra, 3), (rb, 10)):
            for (dx, dy) in RUNES[k]: sh[s].put(rx + dx, 9 + dy, RUNE_V[0])
            sh[s].put(rx + 1, 10, RUNE_V[1])
    t = sh['up']                                       # rune ring on the lid
    for a in range(0, 360, 20):
        x = 7.5 + 4.5 * math.cos(math.radians(a)); y = 7.5 + 4.5 * math.sin(math.radians(a))
        t.put(int(round(x)), int(round(y)), RUNE_V[0])
    for (x, y) in ((7, 7), (8, 7), (7, 8), (8, 8)): t.put(x, y, RUNE_V[1])
    f = sh['south']                                    # pointed arch + hexagon amethyst
    for dy, (a, b) in enumerate([(7, 8), (6, 9), (5, 10), (4, 11), (4, 11), (4, 11), (4, 11), (4, 11), (4, 11), (4, 11)]):
        for x in range(a, b + 1):
            tt = 4 if dy <= 1 or x == a else 1 if x == b or dy == 9 else 2
            f.put(x, 2 + dy, SILVER_V[tt])
    gem(f, 'hexagon', 7, 5, GEM_AMETHYST)
    return {'base': base, 'shell': sh}


def legendary():
    base = {s: side_base(LACQUER, LACQUER, 51 + i, 'none', GOLD[1], edge=False) for i, s in enumerate(SIDES)}
    base['up'] = top_base(LACQUER, 57, plank=False); base['down'] = bottom_base(LACQUER)
    sh = empty_shell()
    for s in SIDES + ['up']:                           # gold frame on every visible face
        f = sh[s]
        for i in range(F):
            f.put(i, 0, GOLD[4]); f.put(0, i, GOLD[3]); f.put(i, F - 1, GOLD[0]); f.put(F - 1, i, GOLD[1])
    for s in SIDES:
        for x in range(1, F - 1): sh[s].put(x, LID_END, GOLD[3])
        for x in range(1, F - 1): sh[s].put(x, SEAM + 1, GOLD[1])
        rivets(sh[s], [(3, 3), (12, 3), (3, 11), (12, 11)], GOLD)          # gold studs
    for s in ('east', 'west', 'north'):                # filigree line on the plain sides
        for x in range(5, 11): sh[s].put(x, 11, GOLD[1])
        sh[s].put(7, 10, GOLD[3]); sh[s].put(8, 10, GOLD[3])
    t = sh['up']                                       # gold crest on the lid
    for (x, y, k) in ((7, 4, 4), (8, 4, 3), (6, 5, 4), (9, 5, 2), (5, 6, 3), (10, 6, 1), (4, 7, 4), (11, 7, 1),
                      (4, 8, 3), (11, 8, 1), (5, 9, 3), (10, 9, 1), (6, 10, 3), (9, 10, 1), (7, 11, 2), (8, 11, 1),
                      (7, 7, 4), (8, 7, 3), (7, 8, 3), (8, 8, 2)):
        t.put(x, y, GOLD[k])
    f = sh['south']                                    # oval amber in a gold setting with prongs
    gem(f, 'oval', 7, 5, GEM_AMBER, frame=GOLD)
    for (x, y) in ((4, 4), (11, 4), (4, 11), (11, 11)): f.put(x, y, GOLD[4])
    return {'base': base, 'shell': sh}


def mythic():
    base = {}
    for i, s in enumerate(SIDES):
        base[s] = side_base(CRIMSON, OBSIDIAN, 61 + i, 'none', BLACKMETAL[0])
    base['up'] = top_base(CRIMSON, 67); base['down'] = bottom_base(OBSIDIAN)
    veins = [[(1, 8, 0), (2, 8, 1), (2, 9, 1), (3, 9, 2), (3, 10, 1), (4, 10, 2), (4, 11, 1), (5, 12, 1), (5, 13, 0)],
             [(14, 8, 0), (13, 9, 1), (13, 10, 2), (12, 10, 1), (12, 11, 2), (11, 12, 1), (11, 13, 1), (10, 14, 0)]]
    for s in SIDES:                                     # two red veins in the obsidian on every side
        for v in veins:
            for (x, y, k) in v: base[s].put(x, y, VEIN[k])
    sh = empty_shell()
    for s in SIDES:                                    # black-metal lid band + horned corners + spiked feet
        f = sh[s]
        for x in range(F): f.put(x, LID_END, BLACKMETAL[3])
        for (hx, d) in ((0, 1), (F - 1, -1)):
            for (dx, dy, k) in ((0, 0, 4), (1, 0, 3), (0, 1, 3), (1, 1, 2), (2, 1, 1), (0, 2, 2), (1, 2, 1),
                                (0, 3, 2), (0, 4, 1), (2, 0, 4), (3, 0, 3)):
                f.put(hx + dx * d, dy, BLACKMETAL[k])
            f.box(min(hx, hx + 2 * d), F - 3, max(hx, hx + 2 * d), F - 1, BLACKMETAL, top=3, mid=2, bottom=0, left=3, right=1)
            f.put(hx + 3 * d, F - 1, BLACKMETAL[3])
    t = sh['up']                                       # black-metal cross bands + a small ruby on the lid
    for i in range(F):
        t.put(i, 7, BLACKMETAL[3]); t.put(i, 8, BLACKMETAL[1]); t.put(7, i, BLACKMETAL[3]); t.put(8, i, BLACKMETAL[1])
    corner_caps(t, BLACKMETAL, 3)
    gem(t, 'round', 7, 5, GEM_RUBY, frame=BLACKMETAL)
    f = sh['south']                                    # big ruby in a spiked black setting
    gem(f, 'bigdiamond', 7, 4, GEM_RUBY, frame=BLACKMETAL)
    for (x, y, k) in ((7, 2, 4), (8, 2, 3), (2, 7, 4), (13, 7, 3), (2, 8, 2), (13, 8, 1), (7, 13, 2), (8, 13, 1)):
        f.put(x, y, BLACKMETAL[k])
    return {'base': base, 'shell': sh}


DRAW = {'common': common, 'uncommon': uncommon, 'rare': rare, 'epic': epic, 'legendary': legendary, 'mythic': mythic}


# ───────────────────────────── atlas, model, item ─────────────────────────────

CELL = {'south': (0, 0), 'east': (1, 0), 'north': (2, 0), 'west': (3, 0), 'up': (0, 1), 'down': (1, 1)}


def atlas(design):
    im = Image.new('RGBA', (4 * F, 4 * F), (0, 0, 0, 0))
    for layer, row0 in (('base', 0), ('shell', 2)):
        for side, (cx, cy) in CELL.items():
            im.alpha_composite(design[layer][side].image(), (cx * F, (cy + row0) * F))
    return im


def face_uv(side, shell):
    cx, cy = CELL[side]
    cy += 2 if shell else 0
    return [cx * 4, cy * 4, cx * 4 + 4, cy * 4 + 4]     # UV units: 16 across the 64 px atlas, 4 per face


GROUND_SCALE = 1.0
# vanilla 1.21.11 assets/minecraft/models/item/template_skull.json (display only), read from the client jar 2026-11-21
SKULL_DISPLAY = {
    "gui": {"rotation": [30, 45, 0], "translation": [0, 3, 0], "scale": [1, 1, 1]},
    "fixed": {"rotation": [0, 180, 0], "translation": [0, 4, 0], "scale": [1, 1, 1]},
    "on_shelf": {"rotation": [0, 0, 0], "translation": [0, 8, 0], "scale": [2, 2, 2]},
    # Ett 09:53 UTC Nov 21: bigger when dropped -> 1.0 (vanilla skull 0.5), i.e. twice a dropped player head
    "ground": {"rotation": [0, 0, 0], "translation": [0, 3, 0], "scale": [GROUND_SCALE] * 3},
    "thirdperson_righthand": {"rotation": [45, 45, 0], "translation": [0, 3, 0], "scale": [0.5, 0.5, 0.5]},
}
BASE_BOX = ([4, 0, 4], [12, 8, 12])
SHELL_BOX = ([3.75, -0.25, 3.75], [12.25, 8.25, 12.25])     # the skull hat layer is the head grown by 0.25 px


def model_json(r):
    def element(box, shell):
        return {"from": box[0], "to": box[1],
                "faces": {s: {"uv": face_uv(s, shell), "texture": "#casket"} for s in CELL}}
    return {"textures": {"casket": f"runeblock:item/casket/head_{r}", "particle": f"runeblock:item/casket/head_{r}"},
            "elements": [element(BASE_BOX, False), element(SHELL_BOX, True)],
            "display": SKULL_DISPLAY}


def item_json(r):
    return {"model": {"type": "minecraft:model", "model": f"runeblock:item/casket/head_{r}"}}


def write_files(out):
    tex = os.path.join(out, 'assets/runeblock/textures/item/casket')
    mod = os.path.join(out, 'assets/runeblock/models/item/casket')
    itm = os.path.join(out, 'assets/runeblock/items')
    for d in (tex, mod, itm): os.makedirs(d, exist_ok=True)
    designs = {}
    for r in RARITIES:
        designs[r] = DRAW[r]()
        atlas(designs[r]).save(os.path.join(tex, f'head_{r}.png'))
        with open(os.path.join(mod, f'head_{r}.json'), 'w') as f: json.dump(model_json(r), f, indent=2); f.write('\n')
        with open(os.path.join(itm, f'casket_head_{r}.json'), 'w') as f: json.dump(item_json(r), f, indent=2); f.write('\n')
    return designs


# ───────────────────────────── software renderer (orthographic, nearest texel, like the game) ─────────────────────────────
# World axes as in Minecraft: +x east, +y up, +z south. The camera looks along -z; display rotation = X·Y·Z Euler
# (Y applied first, then the X tilt), so gui [30, 45, 0] shows the top, the south (front) face and the east face.
# Which of the two sides lands left vs right in the real client is the one thing this mock can't prove
# (front on the left here, like the face of a vanilla head in the inventory).

SHADE = {'up': 1.0, 'down': 0.5, 'south': 0.8, 'north': 0.8, 'east': 0.6, 'west': 0.6}


def rot(rx, ry):
    a, b = math.radians(ry), math.radians(rx)
    Ry = np.array([[math.cos(a), 0, -math.sin(a)], [0, 1, 0], [math.sin(a), 0, math.cos(a)]])
    Rx = np.array([[1, 0, 0], [0, math.cos(b), -math.sin(b)], [0, math.sin(b), math.cos(b)]])
    return Rx @ Ry


def box_faces(lo, hi):
    """(side, top-left, top-right, bottom-left, normal) of each face, seen from outside, texture top up."""
    x0, y0, z0 = lo; x1, y1, z1 = hi
    P = lambda x, y, z: np.array([x, y, z], float)
    return [
        ('south', P(x0, y1, z1), P(x1, y1, z1), P(x0, y0, z1), (0, 0, 1)),
        ('north', P(x1, y1, z0), P(x0, y1, z0), P(x1, y0, z0), (0, 0, -1)),
        ('east', P(x1, y1, z1), P(x1, y1, z0), P(x1, y0, z1), (1, 0, 0)),
        ('west', P(x0, y1, z0), P(x0, y1, z1), P(x0, y0, z0), (-1, 0, 0)),
        ('up', P(x0, y1, z0), P(x1, y1, z0), P(x0, y1, z1), (0, 1, 0)),
        ('down', P(x0, y0, z1), P(x1, y0, z1), P(x0, y0, z0), (0, -1, 0)),
    ]


def draw_quad(img, zbuf, s0, s1, s3, zs, tex, shade, light=None):
    """Fill the parallelogram s0 + u(s1-s0) + v(s3-s0) with tex (RGBA numpy, nearest), alpha-test like a cutout,
    per-pixel depth from zs = (z at s0, z at s1, z at s3)."""
    H, W = img.shape[:2]
    pts = np.array([s0, s1, s3, s1 + s3 - s0])
    xa, xb = int(max(0, math.floor(pts[:, 0].min()))), int(min(W, math.ceil(pts[:, 0].max()) + 1))
    ya, yb = int(max(0, math.floor(pts[:, 1].min()))), int(min(H, math.ceil(pts[:, 1].max()) + 1))
    if xa >= xb or ya >= yb: return
    M = np.array([[s1[0] - s0[0], s3[0] - s0[0]], [s1[1] - s0[1], s3[1] - s0[1]]])
    if abs(np.linalg.det(M)) < 1e-9: return
    Mi = np.linalg.inv(M)
    xs, ys = np.meshgrid(np.arange(xa, xb) + 0.5, np.arange(ya, yb) + 0.5)
    dx, dy = xs - s0[0], ys - s0[1]
    u = Mi[0, 0] * dx + Mi[0, 1] * dy
    v = Mi[1, 0] * dx + Mi[1, 1] * dy
    depth = zs[0] + u * (zs[1] - zs[0]) + v * (zs[2] - zs[0])
    inside = (u >= 0) & (u < 1) & (v >= 0) & (v < 1) & (depth >= zbuf[ya:yb, xa:xb])
    th, tw = tex.shape[:2]
    tx = np.clip((u * tw).astype(int), 0, tw - 1); ty = np.clip((v * th).astype(int), 0, th - 1)
    texel = tex[ty, tx]
    inside &= texel[..., 3] > 127
    rgb = texel[..., :3].astype(float) * shade
    if light is not None: rgb = rgb * light
    sub = img[ya:yb, xa:xb]
    sub[inside, :3] = np.clip(rgb[inside], 0, 255)
    sub[inside, 3] = 255
    zbuf[ya:yb, xa:xb][inside] = depth[inside]


class Scene:
    """Collect textured boxes, project them with one display rotation, draw back to front (z-buffer per face)."""
    def __init__(self, W, H, px_per_unit, rx=30, ry=45, origin=(0, 0)):
        self.img = np.zeros((H, W, 4), float)
        self.z = np.full((H, W), -1e9)
        self.k, self.R, self.o = px_per_unit, rot(rx, ry), np.array(origin, float)
        self.zoff = 0.0

    def project(self, p):
        q = self.R @ np.asarray(p, float)
        return np.array([self.o[0] + q[0] * self.k, self.o[1] - q[1] * self.k]), q[2] + self.zoff

    def box(self, lo, hi, textures, shade=True, light=1.0, bias=0.0):
        """textures: side -> RGBA numpy array (missing side = not drawn)."""
        for (side, tl, tr, bl, n) in box_faces(lo, hi):
            if side not in textures: continue
            nz = (self.R @ np.array(n, float))[2]
            if nz <= 1e-6: continue
            s0, z0 = self.project(tl); s1, z1 = self.project(tr); s3, z3 = self.project(bl)
            draw_quad(self.img, self.z, s0, s1, s3, (z0 + bias, z1 + bias, z3 + bias), textures[side],
                      SHADE[side] if shade else 1.0, light)

    def image(self):
        return Image.fromarray(self.img.astype(np.uint8), 'RGBA')


def face_arrays(design):
    to = lambda f: np.array(f.image())
    return ({s: to(design['base'][s]) for s in CELL}, {s: to(design['shell'][s]) for s in CELL})


def skull_boxes(center, scale, base_tex, shell_tex):
    """Model-space boxes of the head (pivot = model centre 8,8,8), scaled + moved like a display transform."""
    c = np.array(center, float)
    tf = lambda p: c + (np.array(p, float) - 8) * scale
    return [(tf(BASE_BOX[0]), tf(BASE_BOX[1]), base_tex, 0.0), (tf(SHELL_BOX[0]), tf(SHELL_BOX[1]), shell_tex, 0.01)]


def render_head(design_or_arrays, size_px, rx=30, ry=45, translation=(0, 3, 0), scale=1.0, fit=16):
    """The head in a fit x fit model-unit square (16 = one inventory slot) at size_px, with a display transform."""
    base, shell = design_or_arrays if isinstance(design_or_arrays, tuple) else face_arrays(design_or_arrays)
    k = size_px / fit
    sc = Scene(size_px, size_px, k, rx, ry, origin=(size_px / 2, size_px / 2))
    sc.o = np.array([size_px / 2, size_px / 2])
    # display: v' = T + R * (S * (v - 8)); we pass T through the projection by shifting the origin
    sc.o = sc.o + np.array([translation[0] * k, -translation[1] * k])
    for (lo, hi, tex, bias) in skull_boxes((0, 0, 0), scale, base, shell):
        sc.box(lo, hi, tex, bias=bias)
    return sc.image()


def steve_arrays(skin):
    """A vanilla player head from a 64x64 skin (head at 0..32 x 0..16, hat at +32) in the same face convention."""
    s = np.array(skin.convert('RGBA'))
    cut = lambda x, y: s[y:y + 8, x:x + 8]
    base = {'south': cut(8, 8), 'east': cut(16, 8), 'north': cut(24, 8), 'west': cut(0, 8), 'up': cut(8, 0), 'down': cut(16, 0)}
    hat = {'south': cut(40, 8), 'east': cut(48, 8), 'north': cut(56, 8), 'west': cut(32, 8), 'up': cut(40, 0), 'down': cut(48, 0)}
    return base, hat


# ───────────────────────────── example renders ─────────────────────────────

def font(sz, bold=True):
    for p in ('/System/Library/Fonts/Supplemental/Arial Bold.ttf' if bold else '/System/Library/Fonts/Supplemental/Arial.ttf',
              '/Library/Fonts/Arial.ttf'):
        try: return ImageFont.truetype(p, sz)
        except OSError: pass
    return ImageFont.load_default()


def mc_assets(jar):
    want = {'slot': 'assets/minecraft/textures/gui/sprites/container/slot.png',
            'hotbar': 'assets/minecraft/textures/gui/sprites/hud/hotbar.png',
            'hotsel': 'assets/minecraft/textures/gui/sprites/hud/hotbar_selection.png',
            'grass_top': 'assets/minecraft/textures/block/grass_block_top.png',
            'grass_side': 'assets/minecraft/textures/block/grass_block_side.png',
            'grass_ov': 'assets/minecraft/textures/block/grass_block_side_overlay.png',
            'dirt': 'assets/minecraft/textures/block/dirt.png',
            'steve': 'assets/minecraft/textures/entity/player/wide/steve.png'}
    out = {}
    if jar and os.path.exists(jar):
        with zipfile.ZipFile(jar) as z:
            for k, p in want.items():
                try: out[k] = Image.open(io.BytesIO(z.read(p))).convert('RGBA')
                except KeyError: pass
    if 'slot' not in out:   # vanilla slot look: dark top-left, white bottom-right, #8B8B8B inside
        im = Image.new('RGBA', (18, 18), (139, 139, 139, 255)); d = ImageDraw.Draw(im)
        d.line((0, 0, 16, 0), fill=(55, 55, 55, 255)); d.line((0, 0, 0, 16), fill=(55, 55, 55, 255))
        d.line((1, 17, 17, 17), fill=(255, 255, 255, 255)); d.line((17, 1, 17, 17), fill=(255, 255, 255, 255))
        out['slot'] = im
    return out


GUI = 3   # GUI scale 3 (what the testers play at)


def flat_icon(pack_dir, r):
    p = os.path.join(pack_dir, 'assets/runeblock/textures/item/casket', f'armour_{r}.png')
    if os.path.exists(p): return Image.open(p).convert('RGBA')
    return v3.icon(r)


def render_inventory(designs, A, pack_dir, path, zoom=2):
    """Two rows of vanilla slots at GUI scale 3 (true size, left) and the same slots zoomed x2 (right):
    today's flat v3 icon vs the head, plus a vanilla Steve head with the same transform for size."""
    slot = A['slot'].resize((18 * GUI, 18 * GUI), Image.NEAREST)
    item, step = 16 * GUI, 18 * GUI + 6
    steve = render_head(steve_arrays(A['steve']), item) if 'steve' in A else None
    n = len(RARITIES) + (1 if steve is not None else 0)
    strip_w, strip_h = n * step + 12, 2 * (18 * GUI + 10)
    strip = Image.new('RGBA', (strip_w, strip_h), (198, 198, 198, 255))
    for j in range(2):
        y = j * (18 * GUI + 10)
        for i, r in enumerate(RARITIES):
            x = i * step
            strip.alpha_composite(slot, (x, y))
            icon = flat_icon(pack_dir, r).resize((item, item), Image.NEAREST) if j == 0 else render_head(designs[r], item)
            strip.alpha_composite(icon, (x + GUI, y + GUI))
        if j == 1 and steve is not None:
            x = len(RARITIES) * step + 12
            strip.alpha_composite(slot, (x, y)); strip.alpha_composite(steve, (x + GUI, y + GUI))
    big = strip.resize((strip_w * zoom, strip_h * zoom), Image.NEAREST)
    lab_w, top = 230, 96
    W = lab_w + strip_w + 50 + big.width + 30
    H = top + big.height + 70
    sheet = Image.new('RGBA', (W, H), (198, 198, 198, 255))
    d = ImageDraw.Draw(sheet)
    d.rectangle((0, 0, W - 1, H - 1), outline=(85, 85, 85, 255), width=3)
    d.text((18, 14), 'Armour Caskets in inventory slots', font=font(26), fill=(63, 63, 63, 255))
    d.text((18, 50), 'Left: true size at GUI scale 3.  Right: the same slots zoomed x2.  Last slot: a vanilla player head, same transform.',
           font=font(16, False), fill=(63, 63, 63, 255))
    sheet.alpha_composite(strip, (lab_w, top))
    bx = lab_w + strip_w + 50
    sheet.alpha_composite(big, (bx, top))
    for j, label in enumerate(('Today (flat icon)', 'Player-head casket')):
        d.text((18, top + j * (18 * GUI + 10) + 16), label, font=font(19), fill=(63, 63, 63, 255))
    yl = top + big.height + 10
    for i, r in enumerate(RARITIES):
        name, col = LABEL[r]
        cx = bx + (i * step + 9 * GUI) * zoom
        tw = d.textlength(name, font=font(17))
        d.text((cx - tw / 2, yl), name, font=font(17), fill=tuple(int(c * 0.6) for c in col))
    if steve is not None:
        cx = bx + (len(RARITIES) * step + 12 + 9 * GUI) * zoom
        tw = d.textlength('vanilla head', font=font(15))
        d.text((cx - tw / 2, yl), 'vanilla head', font=font(15), fill=(90, 90, 90, 255))
    sheet.save(path)


def render_big(designs, path, per_file_dir=None):
    """Each rarity large: front three-quarter (inventory angle) and back three-quarter."""
    S = 300
    W, H = len(RARITIES) * (S + 20) + 20, 2 * S + 170
    sheet = Image.new('RGBA', (W, H), (34, 36, 42, 255))
    d = ImageDraw.Draw(sheet)
    d.text((20, 14), 'Player-head Armour Caskets: front (inventory angle) and back', font=font(26), fill=(230, 230, 230, 255))
    for i, r in enumerate(RARITIES):
        x = 20 + i * (S + 20)
        mid = (0, 4 * math.cos(math.radians(30)), 0)          # lift the cube's centre to the middle of the cell
        front = render_head(designs[r], S, 30, 45, mid, 1.0, fit=15)
        back = render_head(designs[r], S, 30, 225, mid, 1.0, fit=15)
        sheet.alpha_composite(front, (x, 60)); sheet.alpha_composite(back, (x, 80 + S))
        name, col = LABEL[r]
        tw = d.textlength(name, font=font(24))
        d.text((x + S / 2 - tw / 2, 2 * S + 100), name, font=font(24), fill=col)
        if per_file_dir:
            one = Image.new('RGBA', (2 * S + 60, S + 80), (34, 36, 42, 255))
            one.alpha_composite(front, (20, 10)); one.alpha_composite(back, (S + 40, 10))
            od = ImageDraw.Draw(one)
            od.text((20, S + 30), f'{name} casket: front / back', font=font(24), fill=col)
            one.save(os.path.join(per_file_dir, f'casket_head_{r}_3d.png'))
    sheet.save(path)


def render_ground(designs, A, path):
    """Three caskets dropped on grass, seen from a player's eye angle (ground transform: scale GROUND_SCALE, up 3 px)."""
    if 'grass_top' not in A: return False
    tint = np.array([145, 189, 89]) / 255.0      # plains grass colour 0x91BD59
    top = np.array(A['grass_top']).astype(float); top[..., :3] *= tint
    ov = np.array(A['grass_ov']).astype(float); ov[..., :3] *= tint
    side = np.array(A['grass_side']).astype(float)
    a = ov[..., 3:4] / 255.0
    side[..., :3] = side[..., :3] * (1 - a) + ov[..., :3] * a
    dirt = np.array(A['dirt']).astype(float)
    gtex = {'up': top.astype(np.uint8), 'south': side.astype(np.uint8), 'east': side.astype(np.uint8),
            'west': side.astype(np.uint8), 'north': side.astype(np.uint8), 'down': dirt.astype(np.uint8)}
    W, H, k = 1400, 760, 26.0
    sc = Scene(W, H, k, 32, 35, origin=(W / 2, H / 2 + 60))
    blocks = [(bx, bz) for bz in range(-2, 2) for bx in range(-2, 2)]
    for (bx, bz) in sorted(blocks, key=lambda b: (b[1], b[0])):
        sc.box((bx * 16, -16, bz * 16), (bx * 16 + 16, 0, bz * 16 + 16), gtex)
    picks = [('common', -16, -6, 20), ('rare', 0, 6, -25), ('mythic', 16, -4, 40)]
    for (r, cx, cz, spin) in picks:
        base, shell = face_arrays(designs[r])
        anchor = np.array([cx, 0, cz], float)
        # shadow (round, soft) on the grass
        sp, _ = sc.project(anchor + np.array([0, 0.05, 0]))
        sh = Image.new('L', (W, H), 0); ImageDraw.Draw(sh).ellipse((sp[0] - 2.4 * k, sp[1] - 1.0 * k, sp[0] + 2.4 * k, sp[1] + 1.0 * k), fill=110)
        shm = np.array(sh).astype(float) / 255.0
        sc.img[..., :3] *= (1 - shm[..., None] * 0.55)
        # item entity: lifted 0.1 block (bob) + 0.25 x ground scale, then the ground transform (+3 px, scale 0.5)
        sub = Scene(W, H, k, 32, 35 + spin)
        sub.o, sub.zoff = sc.project(anchor)
        sub.z, sub.img = sc.z, sc.img
        for (lo, hi, tex, bias) in skull_boxes((0, 1.6 + 4.0 * GROUND_SCALE + 3.0, 0), GROUND_SCALE, base, shell):
            sub.box(lo, hi, tex, bias=bias)
    img = sc.image()
    bg = Image.new('RGBA', (W, H), (122, 168, 255, 255))
    bg.alpha_composite(img)
    d = ImageDraw.Draw(bg)
    d.text((24, 18), 'Dropped on the ground: Common, Rare, Mythic (twice the size of a dropped player head)', font=font(24),
           fill=(20, 24, 40, 255))
    bg.save(path)
    return True


def render_hotbar(designs, A, pack_dir, path):
    if 'hotbar' not in A: return False
    G = 3
    hb = A['hotbar'].resize((182 * G, 22 * G), Image.NEAREST)
    sel = A['hotsel'].resize((24 * G, 23 * G), Image.NEAREST)
    W, H = 182 * G * 2 + 120, 22 * G + 110
    sheet = Image.new('RGBA', (W, H), (60, 92, 60, 255))
    d = ImageDraw.Draw(sheet)
    for j, (label, make) in enumerate((('Today', lambda r: flat_icon(pack_dir, r).resize((16 * G, 16 * G), Image.NEAREST)),
                                       ('Player-head', lambda r: render_head(designs[r], 16 * G)))):
        x0 = 30 + j * (182 * G + 60)
        d.text((x0, 16), label, font=font(22), fill=(235, 235, 235, 255))
        sheet.alpha_composite(hb, (x0, 60))
        for i, r in enumerate(RARITIES):
            sheet.alpha_composite(make(r), (x0 + (3 + i * 20) * G, 60 + 3 * G))
        sheet.alpha_composite(sel, (x0 - G + 4 * 20 * G, 60 - G))
    sheet.save(path)
    return True


def render_textures(designs, path):
    """The six atlases (what goes in the pack), enlarged, with the face names."""
    Z = 6
    W, H = 3 * (64 * Z + 30) + 30, 2 * (64 * Z + 70) + 40
    H += 40
    sheet = Image.new('RGBA', (W, H), (34, 36, 42, 255))
    d = ImageDraw.Draw(sheet)
    d.text((30, H - 50), 'Each 64x64: top half = the cube (front, right, back, left / top, bottom), bottom half = the trim layer '
           '(transparent where empty), 16x16 per face.', font=font(16, False), fill=(200, 200, 200, 255))
    for i, r in enumerate(RARITIES):
        x, y = 30 + (i % 3) * (64 * Z + 30), 30 + (i // 3) * (64 * Z + 70)
        chk = Image.new('RGBA', (64 * Z, 64 * Z), (60, 62, 70, 255))
        cd = ImageDraw.Draw(chk)
        for cy in range(0, 64 * Z, 2 * Z):
            for cx in range((cy // (2 * Z)) % 2 * 2 * Z, 64 * Z, 4 * Z): cd.rectangle((cx, cy, cx + 2 * Z - 1, cy + 2 * Z - 1), fill=(72, 74, 84, 255))
        chk.alpha_composite(atlas(designs[r]).resize((64 * Z, 64 * Z), Image.NEAREST))
        sheet.alpha_composite(chk, (x, y))
        name, col = LABEL[r]
        d.text((x, y + 64 * Z + 8), f'{name}  head_{r}.png', font=font(18), fill=col)
    sheet.save(path)


DEFAULT_JAR = os.path.expanduser('~/.gradle/caches/fabric-loom/1.21.11/minecraft-client.jar')

if __name__ == '__main__':
    ap = argparse.ArgumentParser()
    ap.add_argument('--out', default='casket-heads-preview', help="'pack' writes into ../pack (only after approval)")
    ap.add_argument('--renders', help='folder for the example renders')
    ap.add_argument('--mc-jar', default=DEFAULT_JAR, help='1.21.11 client jar for vanilla slot / hotbar / grass art')
    a = ap.parse_args()
    pack_dir = os.path.join(HERE, '..', 'pack')
    out = pack_dir if a.out == 'pack' else a.out
    designs = write_files(out)
    print('wrote', len(designs), 'textures + models + item definitions under', os.path.abspath(out))
    if a.renders:
        os.makedirs(a.renders, exist_ok=True)
        A = mc_assets(a.mc_jar)
        render_inventory(designs, A, pack_dir, os.path.join(a.renders, '1_inventory_slots.png'))
        render_big(designs, os.path.join(a.renders, '2_all_rarities_3d.png'), a.renders)
        render_hotbar(designs, A, pack_dir, os.path.join(a.renders, '3_hotbar.png'))
        render_ground(designs, A, os.path.join(a.renders, '4_dropped_on_grass.png'))
        render_textures(designs, os.path.join(a.renders, '5_textures.png'))
        print('renders in', os.path.abspath(a.renders))
