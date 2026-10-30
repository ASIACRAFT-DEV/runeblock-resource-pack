"""Dread sets armour built from scratch (ArcaneSouls 0.37.0, kuwusaki 2026-10-30 "Dark Fantasy" concept art).

Unlike the class armour (a recoloured Reforged base), every Dread set has its own geometry and its own painted texture,
both made here: cubes per bone + a material per cube (plate, ribs, scale, stone, moss, robe cloth, bone, glow ...),
each face painted into its own rect of a 512x512 atlas (2 px per model unit). The result is a normal Blockbench
file (`blockbench/dread_armour/<set>_armor.bbmodel`, editable; `--from-blockbench` bakes your edits) that
bake_reforged_armour.py turns into the vanilla layers the same way as before: 3D helmet, flat chest/legs/boots.

Pack ids: equipment `runeblock:dread_<set>`, items `runeblock:dread_<set>_<helmet|chestplate|leggings|boots>`.

Usage: python3 -I tools/dread_models.py [--out pack] [--bb blockbench/dread_armour] [--from-blockbench] [--preview x.png]
"""
import argparse, base64, io, json, math, os, random, sys, uuid, zlib
from PIL import Image, ImageDraw

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import bake_reforged_armour as B

PPU = 2                 # atlas pixels per model unit
ATLAS = 512             # atlas size in pixels (uv space = ATLAS / PPU)
ITEM_OFF = (8, -16, 8)  # helmet: Blockbench space -> item-model space (head x -4..4, y 24..32 -> item 4..12, 8..16)
PIECES = ['helmet', 'chestplate', 'leggings', 'boots']


def hexrgb(h): h = h.lstrip('#'); return tuple(int(h[i:i + 2], 16) for i in (0, 2, 4))


# set -> ramps (dark -> light): main (plate/robe), acc (the glow), det (trim / cloth / bone / bark)
PALETTES = {
    'bloodrune':       {'main': ['#0b0a0c', '#1d1a1e', '#332d33', '#5a4f57'], 'acc': ['#3a0206', '#9a0a14', '#ff2530', '#ffb0a8'],
                        'det': ['#1e0306', '#46070d', '#7c0f18', '#b02430']},
    'necrotic':        {'main': ['#07060b', '#151022', '#271c3c', '#41305e'], 'acc': ['#2a0848', '#6c1cc0', '#b45cff', '#f0d0ff'],
                        'det': ['#4a4436', '#8a8068', '#cdc3a6', '#f4eedc']},
    'dragonforged':    {'main': ['#0a0807', '#1b1512', '#2f2520', '#4c3d33'], 'acc': ['#4a1802', '#c0500a', '#ff9a1a', '#ffe28a'],
                        'det': ['#3a2404', '#8a5e10', '#d9a62a', '#ffe590']},
    'shadow_assassin': {'main': ['#050509', '#0e0e17', '#1b1b2c', '#2e2e48'], 'acc': ['#2a0848', '#6a20b0', '#a855f0', '#e4c4ff'],
                        'det': ['#16161c', '#2c2c38', '#4c4c5e', '#7e7e96']},
    'earthwarden':     {'main': ['#2b2c29', '#4a4c46', '#6d7067', '#989b90'], 'acc': ['#0e2a0a', '#2e7a1e', '#62d23c', '#c4ff9e'],
                        'det': ['#2a1a0c', '#4e3218', '#76502a', '#a87c48']},
}
SET_NAMES = {'bloodrune': 'Bloodrune', 'necrotic': 'Necrotic', 'dragonforged': 'Dragonforged',
             'shadow_assassin': 'Shadow Assassin', 'earthwarden': 'Earthwarden'}   # kept in sync with arcane-souls gear.yml


# ---- painting ------------------------------------------------------------------------------------------------
def shade(c, k): return tuple(max(0, min(255, int(v * k))) for v in c[:3]) + (255,)
def jitter(c, rnd, a): d = rnd.randint(-a, a); return tuple(max(0, min(255, v + d)) for v in c[:3]) + (255,)


def paint(img, x0, y0, w, h, mat, face, pal, rnd):
    """Fill one face rect. `mat` = '<pattern>' or '<pattern>:<ramp>' (ramp main|acc|det, default by pattern)."""
    pat, _, rk = mat.partition(':')
    R = [hexrgb(c) + (255,) for c in pal[rk or {'glow': 'acc', 'eye': 'acc', 'moss': 'acc', 'bone': 'det', 'trim': 'det',
                                               'bark': 'det', 'cloth': 'main'}.get(pat, 'main')]]
    A = [hexrgb(c) + (255,) for c in pal['acc']]
    D = [hexrgb(c) + (255,) for c in pal['det']]
    px = img.load()
    lit = {'up': 1.12, 'down': 0.8}.get(face, 1.0)
    def put(x, y, c):
        if 0 <= x < w and 0 <= y < h: px[x0 + x, y0 + y] = shade(c, lit)
    for y in range(h):
        for x in range(w):
            c = R[1]
            if pat in ('plate', 'ribs', 'runeplate', 'trim'):
                c = jitter(R[1] if pat != 'trim' else R[2], rnd, 5)
                if y == 0 or x == 0: c = R[2] if pat != 'trim' else R[3]
                if y == h - 1 or x == w - 1: c = R[0] if pat != 'trim' else R[1]
                if pat == 'ribs' and y % 5 == 4: c = R[0]
                if pat == 'ribs' and y % 5 == 0 and y: c = R[2]
            elif pat == 'cloth':
                c = jitter(R[1] if x % 3 else R[0], rnd, 4)
                if y >= h - 2: c = D[1]
            elif pat == 'scale':
                row, col = y // 3, (x + (y // 3 % 2) * 2) // 4
                cy, cx = y % 3, (x + (y // 3 % 2) * 2) % 4
                c = R[2] if cy == 0 else R[1]
                if cx == 3: c = R[0]
                if cy == 2: c = A[1] if (row * 3 + col) % 7 == 0 else R[0]   # molten seams between a few scales
                c = jitter(c, rnd, 4)
            elif pat == 'stone':
                c = jitter(R[2] if (x * 7 + y * 3) % 11 else R[1], rnd, 9)
                if rnd.random() < 0.04: c = R[3]
            elif pat == 'moss':
                c = jitter(A[1] if rnd.random() < 0.7 else A[0], rnd, 8)
                if rnd.random() < 0.08: c = A[2]
            elif pat == 'bone':
                c = jitter(R[2], rnd, 6)
                if y == 0: c = R[3]
                if y == h - 1: c = R[1]
            elif pat == 'bark':
                c = jitter(R[1] if x % 4 else R[0], rnd, 6)
            elif pat == 'leather':
                c = jitter(R[1], rnd, 4)
                if (x in (1, w - 2) or y in (1, h - 2)) and (x + y) % 2 == 0 and w > 4 and h > 4: c = D[2]
            elif pat == 'void':
                c = jitter(R[0], rnd, 2)
            elif pat == 'glow':
                c = R[2]
                if w > 2 and h > 2 and 0 < x < w - 1 and 0 < y < h - 1: c = R[3]
            elif pat == 'eye':
                c = R[3] if (w <= 2 or 0 < x < w - 1) else R[2]
            px[x0 + x, y0 + y] = shade(c, lit)
    # pattern overlays
    if pat == 'runeplate' and w >= 6 and h >= 6 and face in ('north', 'south'):
        cx = w // 2
        for y in range(2, h - 2): put(cx, y, A[2]); put(cx - 1, y, A[1] if y % 2 else R[1])
        for k in range(3, h - 3, 5):
            for d in range(1, min(4, cx)): put(cx - d, k + d // 2, A[2]); put(cx + d, k + d // 2, A[2])
    if pat == 'stone' and w >= 6 and h >= 6:
        for _ in range(2):   # cracks
            x, y = rnd.randrange(w), 0
            while y < h:
                put(x, y, R[0]); y += 1; x += rnd.choice((-1, 0, 0, 1))


class Atlas:
    """Shelf-packs face rects into one image."""
    def __init__(self, pal, seed):
        self.img = Image.new('RGBA', (ATLAS, ATLAS), (0, 0, 0, 0))
        self.x = self.y = self.row = 0
        self.pal, self.rnd = pal, random.Random(seed)

    def face(self, w_units, h_units, mat, face):
        w, h = max(2, round(w_units * PPU)), max(2, round(h_units * PPU))
        if self.x + w > ATLAS: self.x, self.y, self.row = 0, self.y + self.row, 0
        if self.y + h > ATLAS: raise SystemExit('atlas full')
        paint(self.img, self.x, self.y, w, h, mat, face, self.pal, self.rnd)
        uv = [self.x / PPU, self.y / PPU, (self.x + w) / PPU, (self.y + h) / PPU]
        self.x += w; self.row = max(self.row, h)
        return uv


# ---- geometry --------------------------------------------------------------------------------------------------
def C(bone, f, t, mat, faces=None, rot=None, origin=None, name=None):
    """A cube on a bone. `mat` = default material; `faces` = {face: material} overrides (e.g. a glowing front)."""
    return {'bone': bone, 'from': f, 'to': t, 'mat': mat, 'faces': faces or {}, 'rot': rot, 'origin': origin, 'name': name}


def mirror(cubes, src='right', dst='left'):
    """Left limbs = right limbs mirrored in x (icons show both)."""
    out = []
    for c in cubes:
        if not c['bone'].startswith(src): continue
        m = dict(c); m['bone'] = c['bone'].replace(src, dst)
        m['from'], m['to'] = [-c['to'][0], c['from'][1], c['from'][2]], [-c['from'][0], c['to'][1], c['to'][2]]
        if c['rot']: m['rot'] = [c['rot'][0], -c['rot'][1], -c['rot'][2]]
        if c['origin']: m['origin'] = [-c['origin'][0], c['origin'][1], c['origin'][2]]
        m['faces'] = {{'east': 'west', 'west': 'east'}.get(k, k): v for k, v in c['faces'].items()}
        out.append(m)
    return out


# Baked surfaces (inflate): torso x -5..5 y 11..25 z -3..3 · right arm x 3..9 y 11..25 · hips (leggings) x -4.5..4.5
# y 11.5..24.5 z -2.5..2.5 · right leg x -0.5..4.5 y -0.5..12.5 z -2.5..2.5 · boot x -1..5 y -1..13 z -3..3.
# Head x -4..4 y 24..32 z -4..4 (facing -z); the helmet is the 3D item model, so it may stick out.
def body_base(torso, arm, hips, leg, boot, boot_top=5.5, hip_low=11.5, hip_top=15.0):
    return [C('torso', [-5, 11, -3], [5, 25, 3], torso), C('right_arm', [3, 11, -3], [9, 25, 3], arm),
            C('hips', [-4.5, hip_low, -2.5], [4.5, hip_top, 2.5], hips), C('right_leg', [-0.5, -0.5, -2.5], [4.5, 12.5, 2.5], leg),
            C('right_boot', [-1, -1, -3], [5, boot_top, 3], boot)]


def bloodrune():
    g = body_base('ribs', 'plate', 'plate:det', 'plate', 'plate')
    g += [  # spiked great helm with a glowing T visor, swept fins and a spine of spikes
        C('helmet', [-4.6, 23.6, -4.8], [4.6, 32.9, 4.6], 'plate', {'north': 'runeplate'}),
        C('helmet', [-3.4, 28.4, -5.2], [3.4, 29.2, -4.8], 'eye'), C('helmet', [-0.4, 25.2, -5.2], [0.4, 28.4, -4.8], 'eye'),
        C('helmet', [-4.0, 23.4, -5.4], [4.0, 25.6, -4.6], 'plate:det'),                                   # jaw guard
        C('helmet', [-0.6, 32.8, -3.0], [0.6, 35.6, -1.8], 'plate', rot=[-22.5, 0, 0], origin=[0, 32.8, -2.4]),
        C('helmet', [-0.6, 32.8, 0.0], [0.6, 36.4, 1.2], 'plate', rot=[-22.5, 0, 0], origin=[0, 32.8, 0.6]),
        C('helmet', [-0.6, 32.8, 3.0], [0.6, 35.0, 4.2], 'plate', rot=[-22.5, 0, 0], origin=[0, 32.8, 3.6]),
        C('helmet', [-6.6, 28.0, -1.0], [-4.6, 29.4, 3.0], 'plate', rot=[0, 0, 22.5], origin=[-4.6, 28.7, 1]),
        C('helmet', [4.6, 28.0, -1.0], [6.6, 29.4, 3.0], 'plate', rot=[0, 0, -22.5], origin=[4.6, 28.7, 1]),
        C('helmet', [-4.7, 30.6, -4.9], [4.7, 31.2, 4.7], 'glow'),                                          # blood rune band
        # torso: rune breastplate, glowing seam, red belt gem, tattered cape on the back
        C('torso', [-3.6, 13.5, -3.4], [3.6, 23.5, -3.0], 'runeplate'),
        C('torso', [-5.2, 11.6, -3.6], [5.2, 13.0, 3.6], 'trim:det'), C('torso', [-1.0, 11.4, -3.9], [1.0, 13.2, -3.6], 'glow'),
        C('torso', [-4.6, 11.0, 3.2], [4.6, 24.6, 3.6], 'cloth:det', {'south': 'cloth:det'}),
        C('torso', [-4.6, 11.0, 3.6], [-2.6, 12.6, 3.7], 'void'), C('torso', [1.0, 11.0, 3.6], [2.4, 13.4, 3.7], 'void'),
        # arm: spiked pauldron, glowing gauntlet line
        C('right_arm', [2.8, 22.0, -3.4], [9.4, 25.4, 3.4], 'plate'), C('right_arm', [4.8, 25.0, -0.6], [6.4, 27.5, 0.6], 'plate:det'),
        C('right_arm', [8.8, 22.4, -2.6], [9.6, 24.8, 2.6], 'glow'),
        C('right_arm', [3.0, 11.0, -3.3], [9.0, 15.0, 3.3], 'plate:det'), C('right_arm', [3.0, 13.2, -3.5], [9.0, 13.8, 3.5], 'glow'),
        # hips: faulds with red trim; legs: knee spike + shin glow; boots: sabatons + red toe
        C('hips', [-4.6, 11.4, -2.7], [4.6, 12.2, 2.7], 'glow'),
        C('right_leg', [0.0, 5.0, -2.9], [4.0, 7.8, -2.5], 'plate:det'), C('right_leg', [1.6, 1.0, -2.8], [2.4, 5.0, -2.5], 'glow'),
        C('right_boot', [-1.1, -1.1, -3.6], [5.1, 1.4, -3.0], 'plate:det'), C('right_boot', [0.0, 0.2, -3.8], [4.0, 0.8, -3.6], 'glow'),
    ]
    return g


def necrotic():
    g = body_base('cloth', 'cloth', 'cloth', 'cloth', 'leather:det', boot_top=4.0, hip_top=16)
    g += [  # deep hood around a bone skull mask with violet eye sockets
        C('helmet', [-5.0, 23.6, -4.4], [5.0, 33.4, 5.0], 'cloth', {'north': 'void'}),
        C('helmet', [-1.4, 33.0, 1.0], [1.4, 34.4, 5.4], 'cloth', rot=[-22.5, 0, 0], origin=[0, 33.2, 3]),
        C('helmet', [-5.0, 31.6, -5.2], [5.0, 33.4, -4.4], 'cloth'),                                        # hood lip
        C('helmet', [-3.6, 24.4, -4.8], [3.6, 31.4, -4.4], 'bone'),                                         # skull
        C('helmet', [-2.8, 27.8, -5.0], [-0.8, 29.8, -4.8], 'eye'), C('helmet', [0.8, 27.8, -5.0], [2.8, 29.8, -4.8], 'eye'),
        C('helmet', [-0.5, 26.4, -5.0], [0.5, 27.4, -4.8], 'void'),
        C('helmet', [-2.6, 24.6, -5.0], [2.6, 25.4, -4.8], 'bone', {'north': 'ribs:det'}),                  # teeth
        C('helmet', [-5.2, 29.0, -4.0], [-4.8, 30.4, 1.0], 'glow'), C('helmet', [4.8, 29.0, -4.0], [5.2, 30.4, 1.0], 'glow'),
        # torso: bone ribcage on the robe, soul gem, violet rune hem, cord belt, hood drape behind
        *[C('torso', [-3.6 + 0.4 * i, 21.6 - 1.8 * i, -3.5], [3.6 - 0.4 * i, 22.6 - 1.8 * i, -3.0], 'bone') for i in range(4)],
        C('torso', [-0.6, 14.4, -3.5], [0.6, 23.4, -3.1], 'bone'),
        C('torso', [-1.2, 17.6, -3.8], [1.2, 20.0, -3.5], 'glow', rot=[0, 0, 45], origin=[0, 18.8, -3.65]),
        C('torso', [-5.2, 12.6, -3.6], [5.2, 13.6, 3.6], 'trim:det'),
        C('torso', [-5.1, 11.0, -3.3], [5.1, 11.8, 3.3], 'glow'),
        C('torso', [-3.6, 19.0, 3.0], [3.6, 25.0, 3.6], 'cloth'),
        # arm: skull pauldron, flared sleeve with violet cuff
        C('right_arm', [3.0, 21.6, -3.4], [9.2, 25.4, 3.4], 'bone'), C('right_arm', [6.0, 23.0, -3.6], [8.0, 24.4, -3.4], 'eye'),
        C('right_arm', [2.8, 11.0, -3.5], [9.2, 14.0, 3.5], 'cloth'), C('right_arm', [2.8, 11.0, -3.6], [9.2, 11.8, 3.6], 'glow'),
        # skirt panels + rune hem; wrapped treads with a bone toe
        C('right_leg', [-0.6, -0.6, -2.7], [4.6, 0.6, 2.7], 'glow'), C('right_leg', [1.6, 2.0, -2.8], [2.4, 11.0, -2.5], 'trim:det'),
        C('right_boot', [-1.1, -1.1, -3.5], [5.1, 1.0, -3.0], 'bone'),
    ]
    return g


def dragonforged():
    g = body_base('scale', 'scale', 'plate', 'scale', 'plate')
    g += [  # dragon-head helm: snout visor, crest of gold spikes, horns swept back, ember eyes
        C('helmet', [-4.6, 23.6, -4.6], [4.6, 32.8, 4.6], 'plate', {'north': 'scale', 'up': 'plate'}),
        C('helmet', [-3.0, 24.0, -6.6], [3.0, 28.0, -4.6], 'plate', {'up': 'scale'}),                      # snout
        C('helmet', [-3.4, 28.2, -5.2], [-0.6, 29.0, -4.6], 'eye'), C('helmet', [0.6, 28.2, -5.2], [3.4, 29.0, -4.6], 'eye'),
        C('helmet', [-2.6, 23.6, -6.8], [2.6, 24.4, -6.4], 'trim'),                                         # fangs line
        *[C('helmet', [-0.6, 32.6, -3.4 + 2.2 * i], [0.6, 35.6 - 0.5 * i, -2.2 + 2.2 * i], 'trim', rot=[-22.5, 0, 0],
            origin=[0, 32.8, -2.8 + 2.2 * i]) for i in range(4)],
        C('helmet', [-6.0, 30.0, 0.0], [-4.4, 31.6, 6.0], 'plate', rot=[22.5, 0, 0], origin=[-4.6, 30.8, 1]),
        C('helmet', [4.4, 30.0, 0.0], [6.0, 31.6, 6.0], 'plate', rot=[22.5, 0, 0], origin=[4.6, 30.8, 1]),
        C('helmet', [-6.4, 31.2, 5.0], [-5.4, 32.2, 7.4], 'trim', rot=[45, 0, 0], origin=[-5.9, 31.7, 5.5]),
        C('helmet', [5.4, 31.2, 5.0], [6.4, 32.2, 7.4], 'trim', rot=[45, 0, 0], origin=[5.9, 31.7, 5.5]),
        # torso: gold-rimmed dragon emblem, gold gorget, molten belt
        C('torso', [-3.0, 15.6, -3.4], [3.0, 21.6, -3.1], 'trim', rot=[0, 0, 45], origin=[0, 18.6, -3.25]),
        C('torso', [-2.0, 16.6, -3.6], [2.0, 20.6, -3.3], 'plate', rot=[0, 0, 45], origin=[0, 18.6, -3.45]),
        C('torso', [-0.8, 17.8, -3.8], [0.8, 19.4, -3.6], 'eye'),
        C('torso', [-5.2, 23.4, -3.4], [5.2, 25.2, 3.4], 'trim'),
        C('torso', [-5.2, 11.2, -3.4], [5.2, 12.6, 3.4], 'glow'),
        # arm: scaled pauldron with gold rim and a claw
        C('right_arm', [2.8, 21.0, -3.5], [9.5, 25.5, 3.5], 'scale'), C('right_arm', [2.8, 20.6, -3.6], [9.5, 21.4, 3.6], 'trim'),
        C('right_arm', [8.8, 23.0, -0.6], [10.4, 24.0, 0.6], 'trim'),
        C('right_arm', [3.0, 11.0, -3.3], [9.0, 14.6, 3.3], 'plate'), C('right_arm', [3.0, 14.2, -3.4], [9.0, 14.8, 3.4], 'trim'),
        # tassets + gold knees, talon boots
        C('hips', [-4.6, 11.4, -2.8], [4.6, 13.0, 2.8], 'trim'),
        C('right_leg', [0.2, 5.0, -2.9], [3.8, 8.0, -2.5], 'trim'),
        C('right_boot', [-1.1, -1.1, -3.7], [5.1, 1.2, -3.0], 'trim'),
        *[C('right_boot', [-0.6 + 1.6 * i, -1.1, -4.2], [0.4 + 1.6 * i, 0.6, -3.7], 'eye') for i in range(3)],
    ]
    return g


def shadow_assassin():
    g = body_base('leather', 'leather', 'leather', 'leather', 'leather:det', boot_top=6.5)
    g += [  # close hood with a pointed tail, shadowed face, two violet eyes, cloth mask over the mouth
        C('helmet', [-4.8, 23.8, -4.4], [4.8, 33.0, 4.8], 'cloth', {'north': 'void'}),
        C('helmet', [-1.2, 30.4, 4.4], [1.2, 32.4, 7.4], 'cloth', rot=[-22.5, 0, 0], origin=[0, 31.4, 4.8]),
        C('helmet', [-4.0, 24.0, -4.8], [4.0, 31.6, -4.4], 'void'),
        C('helmet', [-2.8, 28.2, -5.0], [-1.2, 29.0, -4.8], 'eye'), C('helmet', [1.2, 28.2, -5.0], [2.8, 29.0, -4.8], 'eye'),
        C('helmet', [-4.0, 24.0, -5.0], [4.0, 27.0, -4.6], 'cloth:det'),
        C('helmet', [-4.9, 31.8, -4.6], [4.9, 33.2, -4.2], 'cloth'),
        # torso: crossed straps, crescent-moon clasp, belt with pouch and sheath
        C('torso', [-5.6, 17.6, -3.5], [5.6, 18.6, -3.1], 'trim:det', rot=[0, 0, 38], origin=[0, 18.1, -3.3]),
        C('torso', [-5.6, 17.6, -3.7], [5.6, 18.6, -3.4], 'trim:det', rot=[0, 0, -38], origin=[0, 18.1, -3.55]),
        C('torso', [-1.2, 17.0, -3.9], [1.2, 19.2, -3.6], 'eye'), C('torso', [-0.4, 17.6, -4.0], [1.2, 18.6, -3.9], 'void'),
        C('torso', [-5.2, 12.0, -3.5], [5.2, 13.2, 3.5], 'trim:det'),
        C('torso', [2.0, 11.2, -3.7], [4.0, 13.4, -3.4], 'leather:det'),
        C('torso', [-4.6, 11.0, 3.2], [-0.4, 23.6, 3.6], 'cloth'), C('torso', [0.4, 11.0, 3.2], [4.6, 23.6, 3.6], 'cloth'),
        # arm: bracer with a violet stripe, shoulder wrap
        C('right_arm', [2.9, 11.0, -3.3], [9.1, 16.0, 3.3], 'leather:det'), C('right_arm', [2.9, 14.6, -3.4], [9.1, 15.2, 3.4], 'glow'),
        C('right_arm', [3.0, 22.6, -3.3], [9.0, 25.3, 3.3], 'cloth'),
        # leg straps + knee pad, soft boots with a violet band
        C('right_leg', [-0.6, 8.0, -2.7], [4.6, 8.8, 2.7], 'trim:det'), C('right_leg', [-0.6, 3.0, -2.7], [4.6, 3.8, 2.7], 'trim:det'),
        C('right_leg', [0.4, 5.0, -2.9], [3.6, 7.4, -2.5], 'leather:det'),
        C('right_boot', [-1.1, 4.4, -3.4], [5.1, 5.2, 3.4], 'glow'),
    ]
    return g


def earthwarden():
    g = body_base('stone', 'stone', 'stone', 'stone', 'stone')
    g += [  # blocky stone great helm, wide cheek slabs, moss crown with a sprout, glowing green rune eyes
        C('helmet', [-5.0, 23.4, -4.8], [5.0, 32.6, 4.8], 'stone'),
        C('helmet', [-5.6, 24.0, -3.4], [-4.8, 30.6, 2.4], 'stone'), C('helmet', [4.8, 24.0, -3.4], [5.6, 30.6, 2.4], 'stone'),
        C('helmet', [-5.2, 30.6, -5.4], [5.2, 32.0, -4.6], 'stone'),                                         # brow ridge
        C('helmet', [-3.6, 28.0, -5.0], [-1.2, 29.2, -4.8], 'eye'), C('helmet', [1.2, 28.0, -5.0], [3.6, 29.2, -4.8], 'eye'),
        C('helmet', [-0.6, 25.0, -5.0], [0.6, 27.6, -4.8], 'glow'),
        C('helmet', [-5.2, 32.4, -5.2], [1.0, 33.6, 1.0], 'moss'), C('helmet', [-1.0, 32.4, -1.0], [5.2, 33.2, 5.2], 'moss'),
        C('helmet', [-5.2, 32.4, 1.6], [-1.6, 33.0, 5.2], 'moss'), C('helmet', [-5.1, 28.0, -5.0], [-3.6, 32.4, -4.6], 'moss'),
        C('helmet', [1.6, 33.4, 1.6], [2.2, 35.6, 2.2], 'bark'),                                             # sprout
        C('helmet', [2.0, 35.0, 1.2], [3.6, 35.6, 2.6], 'moss', rot=[0, 0, -22.5], origin=[2.2, 35.3, 1.9]),
        C('helmet', [0.2, 34.4, 1.2], [1.8, 35.0, 2.6], 'moss', rot=[0, 0, 22.5], origin=[1.6, 34.7, 1.9]),
        # torso: stone slab plates, a green rune diamond, moss patches, a bark belt
        C('torso', [-4.2, 13.4, -3.4], [4.2, 23.6, -3.0], 'stone'),
        C('torso', [-1.8, 16.4, -3.7], [1.8, 20.0, -3.4], 'glow', rot=[0, 0, 45], origin=[0, 18.2, -3.55]),
        C('torso', [-1.0, 17.2, -3.9], [1.0, 19.2, -3.7], 'stone', rot=[0, 0, 45], origin=[0, 18.2, -3.8]),
        C('torso', [-5.2, 22.4, -3.6], [-1.6, 25.2, 3.6], 'moss'), C('torso', [2.0, 13.6, -3.6], [4.2, 15.4, -3.4], 'moss'),
        C('torso', [-5.2, 11.6, -3.6], [5.2, 13.0, 3.6], 'bark'),
        # arm: boulder pauldron with moss on top, stone gauntlet
        C('right_arm', [2.6, 20.6, -3.6], [9.6, 25.6, 3.6], 'stone', {'up': 'moss'}),
        C('right_arm', [2.6, 24.4, -3.7], [9.6, 25.6, 1.0], 'moss'),
        C('right_arm', [3.0, 11.0, -3.4], [9.0, 15.2, 3.4], 'stone'), C('right_arm', [3.0, 13.4, -3.5], [9.0, 14.0, 3.5], 'glow'),
        # bark-strapped greaves, mossy stone boots
        C('hips', [-4.6, 11.4, -2.7], [4.6, 12.6, 2.7], 'bark'),
        C('right_leg', [-0.6, 9.6, -2.7], [4.6, 10.4, 2.7], 'bark'), C('right_leg', [-0.6, 2.4, -2.7], [4.6, 3.2, 2.7], 'bark'),
        C('right_leg', [0.4, 5.4, -2.9], [3.6, 8.0, -2.5], 'stone'), C('right_leg', [1.4, 6.0, -3.0], [2.6, 7.4, -2.9], 'glow'),
        C('right_boot', [-1.1, 3.6, -3.4], [5.1, 5.6, 3.4], 'moss'), C('right_boot', [-1.2, -1.1, -3.8], [5.2, 1.6, -3.0], 'stone'),
    ]
    return g


SETS = {'bloodrune': bloodrune, 'necrotic': necrotic, 'dragonforged': dragonforged,
        'shadow_assassin': shadow_assassin, 'earthwarden': earthwarden}
BONES = ['helmet', 'torso', 'right_arm', 'left_arm', 'hips', 'right_leg', 'left_leg', 'right_boot', 'left_boot']


def face_size(f, t, face):
    dx, dy, dz = abs(t[0] - f[0]), abs(t[1] - f[1]), abs(t[2] - f[2])
    return {'north': (dx, dy), 'south': (dx, dy), 'east': (dz, dy), 'west': (dz, dy), 'up': (dx, dz), 'down': (dx, dz)}[face]


def build_bbmodel(s):
    cubes = SETS[s]()
    cubes += mirror(cubes, 'right_arm', 'left_arm') + mirror(cubes, 'right_leg', 'left_leg') + mirror(cubes, 'right_boot', 'left_boot')
    atlas = Atlas(PALETTES[s], zlib.crc32(s.encode()))
    groups = {b: {'name': b, 'origin': [0, 0, 0], 'rotation': [0, 0, 0], 'uuid': str(uuid.uuid4()), 'children': []} for b in BONES}
    elements = []
    for i, c in enumerate(cubes):
        faces = {}
        for fc in ('north', 'east', 'south', 'west', 'up', 'down'):
            w, h = face_size(c['from'], c['to'], fc)
            faces[fc] = {'uv': atlas.face(w, h, c['faces'].get(fc, c['mat']), fc), 'texture': 0}
        e = {'name': c['name'] or f"{c['bone']}_{i}", 'box_uv': False, 'rescale': False, 'from': c['from'], 'to': c['to'],
             'origin': c['origin'] or [(c['from'][k] + c['to'][k]) / 2 for k in range(3)], 'faces': faces, 'type': 'cube',
             'uuid': str(uuid.uuid4())}
        if c['rot']: e['rotation'] = c['rot']
        elements.append(e)
        groups[c['bone']]['children'].append(e['uuid'])
    buf = io.BytesIO(); atlas.img.save(buf, 'PNG')
    tex = {'name': f'dread_{s}_armor', 'id': '0', 'width': ATLAS, 'height': ATLAS, 'uv_width': ATLAS // PPU,
           'uv_height': ATLAS // PPU, 'uuid': str(uuid.uuid4()),
           'source': 'data:image/png;base64,' + base64.b64encode(buf.getvalue()).decode()}
    return {'meta': {'format_version': '4.10', 'model_format': 'free', 'box_uv': False, 'model_identifier': f'dread_{s}_armor'},
            'name': f'dread_{s}_armor', 'resolution': {'width': ATLAS // PPU, 'height': ATLAS // PPU},
            'elements': elements, 'outliner': list(groups.values()), 'textures': [tex]}


def helmet_item_model(bb, s):
    """The helmet cubes as a Java item model worn on the head (uv 0..16 over the whole atlas)."""
    tex = f'runeblock:item/dread_armour/{s}_helmet'
    grp = next(g for g in bb['outliner'] if g['name'] == 'helmet')
    els = {e['uuid']: e for e in bb['elements']}
    sc = 16 / (ATLAS // PPU)
    out = []
    for u in grp['children']:
        e = els[u]
        ie = {'from': [e['from'][i] + ITEM_OFF[i] for i in range(3)], 'to': [e['to'][i] + ITEM_OFF[i] for i in range(3)],
              'faces': {k: {'uv': [v * sc for v in f['uv']], 'texture': '#0'} for k, f in e['faces'].items()}}
        r = e.get('rotation')
        if r and any(r):
            axis = next(i for i in range(3) if r[i])
            ie['rotation'] = {'origin': [e['origin'][i] + ITEM_OFF[i] for i in range(3)], 'axis': 'xyz'[axis], 'angle': r[axis]}
        out.append(ie)
    return {'textures': {'0': tex, 'particle': tex}, 'elements': out,
            'display': {'head': {'translation': [0, -6.4, 0], 'scale': [1.6, 1.6, 1.6]},
                        'gui': {'rotation': [20, 200, 0], 'translation': [0, -1.5, 0], 'scale': [0.6, 0.6, 0.6]},
                        'ground': {'translation': [0, 2, 0], 'scale': [0.4, 0.4, 0.4]},
                        'fixed': {'rotation': [0, 180, 0], 'translation': [0, -2, 0], 'scale': [0.6, 0.6, 0.6]}}}


def preview(bbdir, A, out):
    skin = (196, 160, 130, 255)
    tiles = []
    for s in SETS:
        bones = B.load(os.path.join(bbdir, f'{s}_armor.bbmodel'))
        lay = {l: Image.open(os.path.join(A, 'textures', 'entity', 'equipment', l, f'dread_{s}.png')).convert('RGBA') for l in B.LAYERS}
        head = B.Elem({'from': [-4, 24, -4], 'to': [4, 32, 4], 'faces': {}}, [], [])
        head.sample = lambda f, q: skin
        els = [head] + list(bones.get('helmet', []))
        for bx, mir in (('body', False), ('arm', False), ('arm', True), ('leg', False), ('leg', True)):
            els.append(B.BoxUV(bx, 0, None, mir, skin))
        for bx, mir in (('body', False), ('leg', False), ('leg', True)):
            els.append(B.BoxUV(bx, 0.5, lay['humanoid_leggings'], mir))
        for bx, mir in (('body', False), ('arm', False), ('arm', True), ('leg', False), ('leg', True)):
            els.append(B.BoxUV(bx, 1.0, lay['humanoid'], mir))
        tiles.append([B.render(els, yaw, 8, 200, [0, 19, 0], 36) for yaw in (-25, 155)])
    tw, th = 400, tiles[0][0].height + 26
    sheet = Image.new('RGBA', (len(tiles) * tw, th), (40, 40, 48, 255))
    dr = ImageDraw.Draw(sheet)
    for i, (s, pair) in enumerate(zip(SETS, tiles)):
        sheet.alpha_composite(pair[0], (i * tw, 24)); sheet.alpha_composite(pair[1], (i * tw + 200, 24))
        dr.text((i * tw + 8, 6), SET_NAMES[s], fill=(236, 232, 240, 255))
    sheet.save(out)


def main():
    here = os.path.dirname(os.path.abspath(__file__))
    ap = argparse.ArgumentParser()
    ap.add_argument('--out', default=os.path.join(here, '..', 'pack'))
    ap.add_argument('--bb', default=os.path.join(here, '..', 'blockbench', 'dread_armour'))
    ap.add_argument('--from-blockbench', action='store_true', help='bake the .bbmodel files as they are (your edits)')
    ap.add_argument('--preview')
    a = ap.parse_args()
    A = os.path.join(a.out, 'assets', 'runeblock')
    os.makedirs(a.bb, exist_ok=True)
    for s in SETS:
        bbp = os.path.join(a.bb, f'{s}_armor.bbmodel')
        if a.from_blockbench:
            bb = json.load(open(bbp))
        else:
            bb = build_bbmodel(s)
            with open(bbp, 'w') as f: json.dump(bb, f)
        key = f'dread_{s}'
        bones = B.load(bbp)
        for layer in B.LAYERS:
            p = os.path.join(A, 'textures', 'entity', 'equipment', layer, f'{key}.png')
            os.makedirs(os.path.dirname(p), exist_ok=True)
            B.bake_layer(bones, layer).save(p)
        B.write_json(os.path.join(A, 'equipment', f'{key}.json'), {'layers': {
            'humanoid': [{'texture': f'runeblock:{key}'}], 'humanoid_leggings': [{'texture': f'runeblock:{key}'}]}})
        d = os.path.join(A, 'textures', 'item', 'dread_armour'); os.makedirs(d, exist_ok=True)
        for piece, names in B.ICONS.items():
            B.icon(bones, names).save(os.path.join(d, f'{s}_{piece}.png'))
            B.write_json(os.path.join(A, 'models', 'item', 'dread_armour', f'{s}_{piece}.json'),
                         {'parent': 'minecraft:item/generated', 'textures': {'layer0': f'runeblock:item/dread_armour/{s}_{piece}'}})
            B.write_json(os.path.join(A, 'items', f'{key}_{piece}.json'),
                         {'model': {'type': 'minecraft:model', 'model': f'runeblock:item/dread_armour/{s}_{piece}'}})
        t = bb['textures'][0]
        Image.open(io.BytesIO(base64.b64decode(t['source'].split(',', 1)[1]))).save(os.path.join(d, f'{s}_helmet.png'))
        B.write_json(os.path.join(A, 'models', 'item', 'dread_armour', f'{s}_helmet.json'), helmet_item_model(bb, s))
        B.write_json(os.path.join(A, 'items', f'{key}_helmet.json'),
                     {'model': {'type': 'minecraft:model', 'model': f'runeblock:item/dread_armour/{s}_helmet'}})
        print(s, len(bb['elements']), 'cubes ok')
    if a.preview:
        preview(a.bb, A, a.preview); print('preview', a.preview)


if __name__ == '__main__':
    main()
