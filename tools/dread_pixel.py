"""Dread sets armour as hand-style pixel art (ArcaneSouls 0.37.0; kuwusaki 2026-10-30: "reference solforge and arctis").

Like the SolForge / Arctis armour on the Cobblemon server (asc-forge textures/models/armor/*_layer_*.png), every piece
is a flat 128x64 vanilla armour texture: dark plates with 1-px outlines, a few clean panel lines, and bright glow
channels and emblems in one accent colour. No 3D, no noise. The helmet is drawn on the layer too (worn like SolForge).

Each face is painted in vanilla box-UV at 2x (head 16x16, body front 16x24, arm / leg faces 8x24). A shared skeleton
(panels, lames, belts, pauldrons, bracers, knees, sabatons) takes each set's palette; set motifs (visor, emblem, cape,
hood, skull, scales, stone, moss) make the sets different.

Pack ids: equipment `runeblock:dread_<set>` (humanoid = helmet, chest, boots; humanoid_leggings = leggings),
items `runeblock:dread_<set>_<helmet|chestplate|leggings|boots>` with 32x32 icons drawn from the same faces.

Usage: python3 -I tools/dread_pixel.py [--out pack] [--preview x.png]
"""
import argparse, json, os, sys
from PIL import Image, ImageDraw

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import bake_reforged_armour as B

B.BOX['head'] = ((-4, 24, -4), (4, 32, 4), (0, 0))


def hx(h): h = h.lstrip('#'); return tuple(int(h[i:i + 2], 16) for i in (0, 2, 4)) + (255,)


# base = plate (dark -> light), glow = accent channels, trim = metal / bone / bark, cloth = robe / cape, line = outline
PAL = {
    'bloodrune':       dict(base=['#141117', '#221d26', '#332b38', '#4a3f52'], glow=['#4a040c', '#a80c1a', '#ff2e3c', '#ffc0b4'],
                            trim=['#2e282e', '#4c444c', '#7a6e78', '#a89aa6'], cloth=['#2a0408', '#4e0a10', '#76121a', '#9a1c24'], line='#08060a'),
    'necrotic':        dict(base=['#100c1a', '#1c152e', '#2a2144', '#3c315e'], glow=['#360c64', '#7428cc', '#b468ff', '#efd8ff'],
                            trim=['#5e5848', '#9a9078', '#d0c6aa', '#f4eedc'], cloth=['#0c0914', '#16101f', '#21182e', '#2e2240'], line='#060409'),
    'dragonforged':    dict(base=['#15100d', '#241b16', '#362820', '#4c3a2c'], glow=['#661c04', '#cc540c', '#ffa022', '#ffe68e'],
                            trim=['#5c3e0a', '#a07418', '#e0b440', '#fff0a2'], cloth=['#2a1206', '#4a200a', '#6a3010', '#8a4418'], line='#090605'),
    'shadow_assassin': dict(base=['#0b0b13', '#151526', '#212138', '#2f2f52'], glow=['#36105a', '#7430c4', '#ac6cff', '#e6d0ff'],
                            trim=['#34343f', '#555566', '#8a8aa0', '#bcbcd2'], cloth=['#08080e', '#101019', '#191926', '#242436'], line='#040407'),
    'earthwarden':     dict(base=['#34362f', '#4f5248', '#6b6f62', '#8c9082'], glow=['#123a0a', '#2a9218', '#64dc3c', '#c6ffa6'],
                            trim=['#362410', '#5e4020', '#86602e', '#b08446'], cloth=['#1c3a10', '#2e5a1a', '#44802a', '#64a63c'], line='#16170f'),
}
SET_NAMES = {'bloodrune': 'Bloodrune', 'necrotic': 'Necrotic', 'dragonforged': 'Dragonforged',
             'shadow_assassin': 'Shadow Assassin', 'earthwarden': 'Earthwarden'}   # kept in sync with arcane-souls gear.yml

# face rects at 2x (x, y, w, h) in the 128x64 vanilla armour layout
HEAD = {'up': (16, 0, 16, 16), 'east': (0, 16, 16, 16), 'north': (16, 16, 16, 16), 'west': (32, 16, 16, 16), 'south': (48, 16, 16, 16)}
BODY = {'up': (40, 32, 16, 8), 'east': (32, 40, 8, 24), 'north': (40, 40, 16, 24), 'west': (56, 40, 8, 24), 'south': (64, 40, 16, 24)}
ARM = {'up': (88, 32, 8, 8), 'east': (80, 40, 8, 24), 'north': (88, 40, 8, 24), 'west': (96, 40, 8, 24), 'south': (104, 40, 8, 24)}
LEG = {'up': (8, 32, 8, 8), 'east': (0, 40, 8, 24), 'north': (8, 40, 8, 24), 'west': (16, 40, 8, 24), 'south': (24, 40, 8, 24)}


class Face:
    """Drawing inside one face rect; x/y are face-local. `sym` mirrors every pixel across the vertical centre."""
    def __init__(self, img, rect, P):
        self.img, (self.x0, self.y0, self.w, self.h), self.P = img, rect, P
        self.px = img.load()

    def put(self, x, y, c, sym=False):
        if c is None: return
        for xx in ((x, self.w - 1 - x) if sym else (x,)):
            if 0 <= xx < self.w and 0 <= y < self.h: self.px[self.x0 + xx, self.y0 + y] = c

    def rect(self, x0, y0, x1, y1, c, sym=False):          # inclusive
        for y in range(y0, y1 + 1):
            for x in range(x0, x1 + 1): self.put(x, y, c, sym)

    def clear(self, y0=0, y1=None):
        for y in range(y0, (self.h - 1 if y1 is None else y1) + 1):
            for x in range(self.w): self.px[self.x0 + x, self.y0 + y] = (0, 0, 0, 0)

    def panel(self, x0, y0, x1, y1, ramp='base', lit=True):
        """A plate: mid fill, outline, lit top-left inner edge, shadow bottom-right inner edge."""
        R, L = self.P[ramp], hx(self.P['line'])
        self.rect(x0, y0, x1, y1, R[1])
        if lit:
            self.rect(x0 + 1, y0 + 1, x1 - 1, y0 + 1, R[2]); self.rect(x0 + 1, y0 + 1, x0 + 1, y1 - 1, R[2])
            self.rect(x0 + 1, y1 - 1, x1 - 1, y1 - 1, R[0]); self.rect(x1 - 1, y0 + 2, x1 - 1, y1 - 1, R[0])
        for x in range(x0, x1 + 1): self.put(x, y0, L); self.put(x, y1, L)
        for y in range(y0, y1 + 1): self.put(x0, y, L); self.put(x1, y, L)


def ramps(P):
    return {k: [hx(c) for c in v] if isinstance(v, list) else v for k, v in P.items()}


# ---- shared skeleton -------------------------------------------------------------------------------------------
def plate_face(f, lames_from=None, step=3):
    f.panel(0, 0, f.w - 1, f.h - 1)
    if lames_from is not None:   # overlapping bands: outline row, lit row under it
        for y in range(lames_from, f.h - 1, step):
            f.rect(1, y, f.w - 2, y, hx(f.P['line'])); f.rect(1, y + 1, f.w - 2, y + 1, f.P['base'][2])


def belt(f, y, buckle=True):
    T, G, L = f.P['trim'], f.P['glow'], hx(f.P['line'])
    f.rect(0, y, f.w - 1, y + 2, T[1]); f.rect(0, y, f.w - 1, y, T[2]); f.rect(0, y + 3, f.w - 1, y + 3, L)
    if buckle and f.w >= 12:
        c = f.w // 2
        f.rect(c - 2, y - 1, c + 1, y + 3, L); f.rect(c - 1, y, c, y + 2, G[2]); f.put(c - 1, y, G[3])


def pauldron(f, outer=False, rows=8):
    T, G, L = f.P['trim'], f.P['glow'], hx(f.P['line'])
    f.panel(0, 0, f.w - 1, rows)
    f.rect(1, rows - 1, f.w - 2, rows - 1, T[2]); f.rect(1, rows - 2, f.w - 2, rows - 2, T[1])
    f.rect(1, 3, f.w - 2, 3, L); f.rect(1, 4, f.w - 2, 4, f.P['base'][2])
    if outer: f.rect(2, 5, f.w - 3, 5, G[2])


def bracer(f, glow=True):
    T, G, L = f.P['trim'], f.P['glow'], hx(f.P['line'])
    f.panel(0, 14, f.w - 1, f.h - 1)
    f.rect(0, 14, f.w - 1, 15, T[1]); f.rect(0, 14, f.w - 1, 14, T[2]); f.rect(0, 16, f.w - 1, 16, L)
    if glow: f.rect(1, 19, f.w - 2, 19, G[2]); f.rect(1, 20, f.w - 2, 20, G[1])
    f.rect(0, f.h - 2, f.w - 1, f.h - 1, T[1]); f.rect(0, f.h - 2, f.w - 1, f.h - 2, T[2])


def knee(f, gem=True):
    T, G, L = f.P['trim'], f.P['glow'], hx(f.P['line'])
    f.rect(0, 10, f.w - 1, 13, T[1]); f.rect(0, 10, f.w - 1, 10, T[2]); f.rect(0, 13, f.w - 1, 13, L)
    if gem: f.rect(3, 11, 4, 12, G[2]); f.put(3, 11, G[3])


def sabaton(f, toe=True):
    T, G, L = f.P['trim'], f.P['glow'], hx(f.P['line'])
    f.clear(0, 13)
    f.panel(0, 14, f.w - 1, f.h - 1)
    f.rect(0, 14, f.w - 1, 15, T[1]); f.rect(0, 14, f.w - 1, 14, T[2]); f.rect(0, 16, f.w - 1, 16, L)
    f.rect(1, 19, f.w - 2, 19, L); f.rect(1, 20, f.w - 2, 20, f.P['base'][2])
    f.rect(0, f.h - 2, f.w - 1, f.h - 1, f.P['base'][0]); f.rect(0, f.h - 2, f.w - 1, f.h - 2, L)
    if toe: f.rect(2, 18, f.w - 3, 18, G[2])


# ---- set motifs ------------------------------------------------------------------------------------------------
def visor_t(f):        # Bloodrune: T-slit
    G, L = f.P['glow'], hx(f.P['line'])
    f.rect(2, 7, 13, 9, L); f.rect(3, 8, 12, 8, G[2]); f.rect(6, 8, 9, 8, G[3])
    f.rect(6, 9, 9, 13, L); f.rect(7, 9, 8, 12, G[2])


def rune_emblem(f, top=2, bot=11):
    G, L = f.P['glow'], hx(f.P['line'])
    c = f.w // 2
    f.rect(c - 2, top - 1, c + 1, bot + 1, L)
    f.rect(c - 1, top, c, bot, G[2]); f.rect(c - 1, top, c - 1, bot, G[3])
    for y in range(top + 2, bot - 1, 3):
        for d in range(1, 4): f.put(c - 1 - d, y + d - 1, G[1] if d == 3 else G[2]); f.put(c + d, y + d - 1, G[1] if d == 3 else G[2])


def cape(f, y0=2, split=False):
    C, L, G = f.P['cloth'], hx(f.P['line']), f.P['glow']
    f.rect(1, y0, f.w - 2, f.h - 1, C[1])
    for x in range(2, f.w - 2, 3): f.rect(x, y0 + 1, x, f.h - 2, C[0])
    for x in range(3, f.w - 2, 3): f.rect(x, y0 + 1, x, f.h - 3, C[2])
    f.rect(1, y0, f.w - 2, y0, L)
    for x in range(1, f.w - 1, 2): f.put(x, f.h - 1, (0, 0, 0, 0))   # ragged hem
    if split: f.rect(f.w // 2 - 1, y0 + 6, f.w // 2, f.h - 1, L); f.rect(f.w // 2 - 1, y0 + 6, f.w // 2 - 1, f.h - 1, f.P['base'][1])


def hood_face(f, mask):
    """Hood around the face: cloth frame, shadowed opening, then `mask(f)` draws inside."""
    C, L = f.P['cloth'], hx(f.P['line'])
    f.rect(0, 0, f.w - 1, f.h - 1, C[1])
    for x in range(1, f.w - 1, 3): f.rect(x, 1, x, 3, C[2])
    f.rect(2, 4, 13, 15, L); f.rect(3, 5, 12, 15, C[0])
    f.rect(0, 0, f.w - 1, 0, L)
    mask(f)


def skull(f):
    T, G, L = f.P['trim'], f.P['glow'], hx(f.P['line'])
    f.rect(4, 5, 11, 12, T[2]); f.rect(4, 5, 11, 5, T[3]); f.rect(3, 6, 3, 10, T[1], True)
    f.rect(4, 7, 6, 9, L, True); f.rect(5, 8, 5, 8, G[3], True); f.put(4, 8, G[2], True); f.put(6, 8, G[1], True)
    f.rect(7, 10, 8, 10, L)
    f.rect(5, 12, 10, 14, T[1]); f.rect(5, 13, 10, 13, L)
    for x in range(5, 11, 2): f.put(x, 12, T[3]); f.put(x, 14, T[2])


def ribcage(f):
    T, G, L = f.P['trim'], f.P['glow'], hx(f.P['line'])
    c = f.w // 2
    f.rect(c - 1, 2, c, 14, T[2])
    for i, y in enumerate(range(3, 12, 2)):
        span = 6 - i // 2
        f.rect(c - 1 - span, y, c - 2, y, T[2]); f.rect(c + 1, y, c + span, y, T[2])
        f.rect(c - 1 - span, y + 1, c - 2, y + 1, T[0]); f.rect(c + 1, y + 1, c + span, y + 1, T[0])
    f.rect(c - 2, 14, c + 1, 17, L); f.rect(c - 1, 15, c, 16, G[2]); f.put(c - 1, 15, G[3])


def robe(f, hem=True):
    C, L, G = f.P['cloth'], hx(f.P['line']), f.P['glow']
    f.rect(0, 0, f.w - 1, f.h - 1, C[1])
    for x in range(1, f.w, 3): f.rect(x, 0, x, f.h - 1, C[0])
    for x in range(2, f.w, 3): f.rect(x, 0, x, f.h - 1, C[2] if x % 2 else C[1])
    if hem: f.rect(0, f.h - 3, f.w - 1, f.h - 3, G[2]); f.rect(0, f.h - 2, f.w - 1, f.h - 1, C[0])


def scales(f, x0, y0, x1, y1):
    B_, G, L = f.P['base'], f.P['glow'], hx(f.P['line'])
    for y in range(y0, y1 + 1):
        for x in range(x0, x1 + 1):
            row, off = (y - y0) // 3, ((y - y0) // 3 % 2) * 2
            cx, cy = (x - x0 + off) % 4, (y - y0) % 3
            c = B_[2] if cy == 0 else B_[1]
            if cx == 3 or cy == 2: c = L
            if cy == 2 and (row * 5 + (x - x0 + off) // 4) % 4 == 0: c = G[1]
            if cx == 0 and cy == 0: c = B_[3]
            f.put(x, y, c)


def dragon_emblem(f):
    T, G, L = f.P['trim'], f.P['glow'], hx(f.P['line'])
    c = f.w // 2
    for d in range(0, 6):   # gold diamond
        f.put(c - 1 - d, 6 + d, T[2], True); f.put(c - 1 - d, 16 - d, T[1], True)
    f.rect(c - 2, 9, c + 1, 13, L); f.rect(c - 1, 10, c, 12, G[2]); f.put(c - 1, 10, G[3])
    f.rect(c - 4, 3, c - 3, 5, T[2], True); f.put(c - 4, 2, T[3], True)   # horns over the diamond


def dragon_visor(f):
    T, G, L = f.P['trim'], f.P['glow'], hx(f.P['line'])
    for i in range(4): f.put(2 + i, 6 + i // 2, L, True); f.put(3 + i, 7 + i // 2, G[2], True)
    f.put(4, 7, G[3], True)
    f.panel(3, 10, 12, 15, 'base')
    for x in range(4, 12, 2): f.put(x, 15, T[3]); f.put(x, 14, T[2])          # fangs
    f.rect(6, 11, 9, 11, T[2])


def straps_x(f):
    T, G, L = f.P['trim'], f.P['glow'], hx(f.P['line'])
    for i in range(14):
        y = 2 + i
        f.put(1 + i, y, T[2]); f.put(1 + i, y + 1, T[0])
        f.put(f.w - 2 - i, y, T[2]); f.put(f.w - 2 - i, y + 1, T[0])
    c = f.w // 2
    f.rect(c - 2, 7, c + 1, 10, L); f.rect(c - 1, 8, c, 9, G[2]); f.put(c - 2, 8, G[3]); f.put(c - 2, 9, G[2])   # moon clasp


def shadow_mask(f):
    G, C = f.P['glow'], f.P['cloth']
    f.rect(3, 5, 12, 15, (6, 6, 10, 255))
    f.rect(4, 8, 6, 8, G[2], True); f.put(5, 8, G[3], True); f.put(4, 9, G[0], True)
    f.rect(3, 11, 12, 15, C[1]); f.rect(3, 11, 12, 11, C[2])
    for x in range(4, 12, 3): f.rect(x, 12, x, 15, C[0])


def stone_face(f, x0=0, y0=0, x1=None, y1=None, moss_top=True):
    B_, L, M = f.P['base'], hx(f.P['line']), f.P['cloth']
    x1 = f.w - 1 if x1 is None else x1; y1 = f.h - 1 if y1 is None else y1
    for y in range(y0, y1 + 1):
        for x in range(x0, x1 + 1):
            row = (y - y0) // 4; off = (row % 2) * 3
            lx, ly = (x - x0 + off) % 6, (y - y0) % 4
            c = B_[2] if (row + (x - x0 + off) // 6) % 3 else B_[1]
            if ly == 0 or lx == 0: c = B_[3] if ly == 0 else B_[2]
            if ly == 3 or lx == 5: c = L if (ly == 3 and lx == 5) else B_[0]
            f.put(x, y, c)
    if moss_top:
        for x in range(x0, x1 + 1):
            d = (x * 7) % 5
            for y in range(y0, y0 + 1 + (d > 2) + (d > 3)): f.put(x, y, M[2] if y == y0 else M[1])
            if d == 4: f.put(x, y0 + 3, M[0])


def green_rune(f, cy):
    G, L = f.P['glow'], hx(f.P['line'])
    c = f.w // 2
    for d in range(4):
        f.put(c - 1 - d, cy - 3 + d, G[2], True); f.put(c - 1 - d, cy + 3 - d, G[2], True)
    f.rect(c - 1, cy - 1, c, cy, G[3])


# ---- per set ---------------------------------------------------------------------------------------------------
def paint_set(s):
    P = ramps(PAL[s])
    l1 = Image.new('RGBA', (128, 64), (0, 0, 0, 0))   # humanoid: helmet + chest + boots
    l2 = Image.new('RGBA', (128, 64), (0, 0, 0, 0))   # humanoid_leggings
    F = lambda img, r: Face(img, r, P)
    G, T, L = P['glow'], P['trim'], hx(P['line'])
    stone = s == 'earthwarden'

    # helmet
    for side in ('up', 'east', 'west', 'south', 'north'):
        f = F(l1, HEAD[side])
        if stone: stone_face(f, moss_top=side != 'up')
        else: f.panel(0, 0, f.w - 1, f.h - 1)
        if side == 'up':
            if stone:
                for y in range(f.h):
                    for x in range(f.w):
                        if (x * 3 + y * 5) % 7 < 4: f.put(x, y, P['cloth'][1 + (x + y) % 3 // 2])
            elif s in ('necrotic', 'shadow_assassin'):
                f.rect(0, 0, f.w - 1, f.h - 1, P['cloth'][1]); f.rect(7, 0, 8, f.h - 1, P['cloth'][2])
            else:
                f.rect(7, 0, 8, f.h - 1, L); f.rect(7, 1, 7, f.h - 2, T[2] if s == 'dragonforged' else G[2])
                f.rect(8, 1, 8, f.h - 2, T[1] if s == 'dragonforged' else G[1])
            continue
        if s in ('necrotic', 'shadow_assassin') and side != 'north':
            robe(f, hem=False); f.rect(0, 0, f.w - 1, 0, L)
            if side == 'south': f.rect(6, 0, 9, 3, P['cloth'][2])
            continue
        if side == 'north':
            {'bloodrune': lambda: (f.rect(1, 4, 14, 5, T[1]), f.rect(1, 4, 14, 4, T[2]), f.rect(1, 6, 14, 6, L), visor_t(f),
                                   f.rect(1, 2, 14, 2, G[2])),
             'necrotic': lambda: hood_face(f, skull),
             'dragonforged': lambda: (f.rect(1, 3, 14, 4, T[1]), f.rect(1, 3, 14, 3, T[2]), f.rect(1, 5, 14, 5, L), dragon_visor(f)),
             'shadow_assassin': lambda: hood_face(f, shadow_mask),
             'earthwarden': lambda: (f.rect(1, 5, 14, 6, P['base'][3]), f.rect(1, 7, 14, 7, L),
                                     f.rect(3, 9, 5, 9, G[2], True), f.put(4, 9, G[3], True), f.rect(7, 11, 8, 14, G[1]))}[s]()
        else:
            if not stone:
                f.rect(1, 4, 14, 5, T[1]); f.rect(1, 4, 14, 4, T[2]); f.rect(1, 6, 14, 6, L)
                if side == 'south': f.rect(7, 7, 8, 14, G[1]); f.rect(7, 7, 7, 14, G[2])
                else: f.rect(3, 9, 12, 9, G[1]); f.rect(5, 8, 6, 10, T[2]); f.put(5, 8, T[3])
            elif side != 'south': f.rect(5, 9, 8, 9, G[2])

    # chestplate: body + arm
    f = F(l1, BODY['north'])
    if s == 'necrotic': robe(f); ribcage(f); belt(f, 18)
    elif s == 'shadow_assassin':
        robe(f, hem=False); f.rect(0, 0, f.w - 1, f.h - 1, P['base'][1]); plate_face(f, 13, 4); straps_x(f); belt(f, 18)
    elif stone: stone_face(f); green_rune(f, 8); belt(f, 18)
    else:
        f.panel(0, 0, 7, 11); f.panel(8, 0, 15, 11)
        for y in range(12, 18, 2): f.rect(0, y, 15, y, L); f.rect(0, y + 1, 15, y + 1, P['base'][2] if y % 4 == 0 else P['base'][1])
        if s == 'dragonforged': scales(f, 1, 1, 6, 10); scales(f, 9, 1, 14, 10); dragon_emblem(f)
        else: rune_emblem(f, 2, 11)
        belt(f, 18)
        f.rect(0, 22, 15, 23, P['base'][1]); f.rect(7, 22, 8, 23, L)
    for side in ('east', 'west'):
        f = F(l1, BODY[side])
        if s == 'necrotic': robe(f, hem=False)
        elif stone: stone_face(f)
        else:
            plate_face(f, 12, 2)
            if s == 'dragonforged': scales(f, 1, 1, 6, 10)
        belt(f, 18, False)
    f = F(l1, BODY['south'])
    if stone: stone_face(f); f.rect(7, 2, 8, 16, G[1]); belt(f, 18, False)
    else:
        plate_face(f, 12, 2) if s not in ('necrotic',) else robe(f)
        f.rect(7, 1, 8, 11, G[1]); f.rect(7, 1, 7, 11, G[2])
        belt(f, 18, False)
        if s in ('bloodrune', 'necrotic', 'shadow_assassin'): cape(f, 1, split=s == 'shadow_assassin')
    f = F(l1, BODY['up'])
    if stone: stone_face(f)
    else: f.panel(0, 0, f.w - 1, f.h - 1); f.rect(4, 2, 11, 5, T[1]); f.rect(4, 2, 11, 2, T[2])

    for side in ('east', 'north', 'west', 'south', 'up'):
        f = F(l1, ARM[side])
        if side == 'up':
            if stone: stone_face(f)
            else: f.panel(0, 0, 7, 7); f.rect(1, 1, 6, 2, T[2])
            if s in ('bloodrune', 'dragonforged'): f.rect(3, 3, 4, 4, T[3] if s == 'dragonforged' else T[2])
            continue
        if s == 'necrotic':
            robe(f, hem=False); f.panel(0, 0, 7, 7, 'trim'); f.rect(2, 3, 5, 4, L); f.put(2, 3, G[2]); f.put(5, 3, G[2])
            f.rect(0, 20, 7, 20, G[2]); f.rect(0, 21, 7, 23, P['cloth'][0])
            continue
        if stone:
            stone_face(f); f.rect(0, 8, 7, 8, L); f.rect(1, 18, 6, 18, G[2])
            continue
        f.panel(0, 0, 7, 13)
        if s == 'shadow_assassin':
            robe(f, hem=False)
            for y in range(14, 24, 2): f.rect(0, y, 7, y, T[1]); f.put((y // 2) % 8, y, T[2])
            f.rect(1, 18, 6, 18, G[2])
            continue
        pauldron(f, outer=side == 'east')
        if s == 'dragonforged': scales(f, 1, 9, 6, 13)
        bracer(f)
        if s == 'bloodrune' and side == 'east':
            for i in range(3): f.put(2 + 2 * i, 0, T[3]); f.put(2 + 2 * i, 1, T[2])   # spikes on the pauldron rim

    # boots: layer 1 leg, lower part only
    for side in ('east', 'north', 'west', 'south'):
        f = F(l1, LEG[side])
        if stone:
            f.clear(0, 13); stone_face(f, 0, 14, 7, 23)
            if side == 'north': f.rect(2, 19, 5, 19, G[2])
        elif s == 'necrotic':
            f.clear(0, 13); f.panel(0, 15, 7, 23, 'cloth'); f.rect(0, 15, 7, 16, T[2]); f.rect(1, 22, 6, 23, T[1])
            if side == 'north': f.rect(2, 19, 5, 19, G[2])
        else: sabaton(f, toe=side == 'north')
    f = F(l1, LEG['up']); f.clear()

    # leggings: layer 2 body (faulds) + legs
    f = F(l2, BODY['north'])
    if s == 'necrotic': robe(f); f.clear(0, 13)
    elif stone: stone_face(f, 0, 14, 15, 23, moss_top=False); f.rect(0, 14, 15, 15, P['trim'][1]); f.clear(0, 13)
    else:
        f.panel(0, 14, 7, 23); f.panel(8, 14, 15, 23); f.rect(0, 14, 15, 15, T[1]); f.rect(0, 14, 15, 14, T[2])
        f.rect(3, 19, 4, 19, G[2], True)
    for side in ('east', 'west', 'south'):
        f = F(l2, BODY[side])
        if s == 'necrotic': robe(f)
        elif stone: stone_face(f, 0, 14, f.w - 1, 23, moss_top=False)
        else: f.panel(0, 14, f.w - 1, 23); f.rect(0, 14, f.w - 1, 15, T[1]); f.rect(0, 14, f.w - 1, 14, T[2])
        f.clear(0, 13)
    for side in ('east', 'north', 'west', 'south'):
        f = F(l2, LEG[side])
        if s == 'necrotic':
            robe(f)
            if side == 'north': f.rect(3, 2, 4, 18, T[2]); f.rect(3, 2, 3, 18, T[3])
            continue
        if stone:
            stone_face(f, moss_top=False); knee(f, gem=side == 'north'); f.rect(0, 4, 7, 5, P['trim'][1]); f.rect(0, 17, 7, 18, P['trim'][1])
            continue
        f.panel(0, 0, 7, 9); f.panel(0, 14, 7, 23)
        if s == 'dragonforged': scales(f, 1, 1, 6, 8); scales(f, 1, 15, 6, 22)
        if s == 'shadow_assassin':
            robe(f, hem=False); f.rect(0, 5, 7, 5, T[1]); f.rect(0, 17, 7, 17, T[1]); knee(f, gem=False)
            if side == 'north': f.rect(1, 11, 6, 12, G[1])
            continue
        knee(f, gem=side == 'north')
        if side == 'north': f.rect(3, 15, 4, 22, L); f.rect(3, 16, 3, 21, G[2]); f.rect(4, 16, 4, 21, G[1])
        if side == 'east': f.rect(2, 2, 2, 7, G[1])
    return l1, l2


# ---- icons -----------------------------------------------------------------------------------------------------
def crop(img, r): x, y, w, h = r; return img.crop((x, y, x + w, y + h))


def outline(icon):
    out = icon.copy()
    for y in range(icon.height):
        for x in range(icon.width):
            if icon.getpixel((x, y))[3]: continue
            if any(0 <= x + dx < icon.width and 0 <= y + dy < icon.height and icon.getpixel((x + dx, y + dy))[3]
                   for dx, dy in ((1, 0), (-1, 0), (0, 1), (0, -1))):
                out.putpixel((x, y), (12, 10, 14, 255))
    return out


def icons(l1, l2):
    I = {}
    h = Image.new('RGBA', (32, 32)); h.alpha_composite(crop(l1, HEAD['north']).resize((26, 26), Image.NEAREST), (3, 3)); I['helmet'] = h
    c = Image.new('RGBA', (32, 32))
    c.alpha_composite(crop(l1, ARM['north']).crop((0, 0, 8, 22)), (0, 4)); c.alpha_composite(crop(l1, BODY['north']).crop((0, 0, 16, 24)), (8, 4))
    c.alpha_composite(crop(l1, ARM['north']).crop((0, 0, 8, 22)).transpose(Image.FLIP_LEFT_RIGHT), (24, 4)); I['chestplate'] = c
    g = Image.new('RGBA', (32, 32))
    g.alpha_composite(crop(l2, BODY['north']).crop((0, 14, 16, 22)), (8, 1))
    g.alpha_composite(crop(l2, LEG['north']), (8, 8)); g.alpha_composite(crop(l2, LEG['north']).transpose(Image.FLIP_LEFT_RIGHT), (16, 8))
    I['leggings'] = g
    b = Image.new('RGBA', (32, 32))
    leg = crop(l1, LEG['north']).crop((0, 14, 8, 24)).resize((12, 15), Image.NEAREST)
    b.alpha_composite(leg, (3, 9)); b.alpha_composite(leg.transpose(Image.FLIP_LEFT_RIGHT), (17, 9)); I['boots'] = b
    return {k: outline(v) for k, v in I.items()}


# ---- output ----------------------------------------------------------------------------------------------------
def preview(layers, out):
    skin = (196, 160, 130, 255)
    tiles = []
    for s, (l1, l2) in layers.items():
        els = [B.BoxUV('head', 0, None, False, skin), B.BoxUV('head', 1.0, l1)]
        for bx, mir in (('body', False), ('arm', False), ('arm', True), ('leg', False), ('leg', True)):
            els.append(B.BoxUV(bx, 0, None, mir, skin))
        for bx, mir in (('body', False), ('leg', False), ('leg', True)):
            els.append(B.BoxUV(bx, 0.5, l2, mir))
        for bx, mir in (('body', False), ('arm', False), ('arm', True), ('leg', False), ('leg', True)):
            els.append(B.BoxUV(bx, 1.0, l1, mir))
        tiles.append([B.render(els, yaw, 8, 320, [0, 17, 0], 38) for yaw in (-25, 155)])
    tw, th = 640, tiles[0][0].height + 26
    sheet = Image.new('RGBA', (len(tiles) * tw, th), (40, 40, 48, 255))
    dr = ImageDraw.Draw(sheet)
    for i, (s, pair) in enumerate(zip(layers, tiles)):
        sheet.alpha_composite(pair[0], (i * tw, 24)); sheet.alpha_composite(pair[1], (i * tw + 320, 24))
        dr.text((i * tw + 8, 6), SET_NAMES[s], fill=(236, 232, 240, 255))
    sheet.save(out)


def main():
    here = os.path.dirname(os.path.abspath(__file__))
    ap = argparse.ArgumentParser()
    ap.add_argument('--out', default=os.path.join(here, '..', 'pack'))
    ap.add_argument('--preview')
    a = ap.parse_args()
    A = os.path.join(a.out, 'assets', 'runeblock')
    layers = {}
    for s in PAL:
        l1, l2 = paint_set(s)
        layers[s] = (l1, l2)
        key = f'dread_{s}'
        for layer, img in (('humanoid', l1), ('humanoid_leggings', l2)):
            p = os.path.join(A, 'textures', 'entity', 'equipment', layer, f'{key}.png')
            os.makedirs(os.path.dirname(p), exist_ok=True); img.save(p)
        B.write_json(os.path.join(A, 'equipment', f'{key}.json'), {'layers': {
            'humanoid': [{'texture': f'runeblock:{key}'}], 'humanoid_leggings': [{'texture': f'runeblock:{key}'}]}})
        d = os.path.join(A, 'textures', 'item', 'dread_armour'); os.makedirs(d, exist_ok=True)
        for piece, ic in icons(l1, l2).items():
            ic.save(os.path.join(d, f'{s}_{piece}.png'))
            B.write_json(os.path.join(A, 'models', 'item', 'dread_armour', f'{s}_{piece}.json'),
                         {'parent': 'minecraft:item/generated', 'textures': {'layer0': f'runeblock:item/dread_armour/{s}_{piece}'}})
            B.write_json(os.path.join(A, 'items', f'{key}_{piece}.json'),
                         {'model': {'type': 'minecraft:model', 'model': f'runeblock:item/dread_armour/{s}_{piece}'}})
        print(s, 'ok')
    if a.preview:
        preview(layers, a.preview); print('preview', a.preview)


if __name__ == '__main__':
    main()
