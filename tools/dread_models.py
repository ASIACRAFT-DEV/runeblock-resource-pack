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


def mix(a, b, t): return tuple(int(a[i] + (b[i] - a[i]) * t) for i in range(3)) + (255,)


def ramp4(R, t):
    """Continuous ramp over the 4 swatches, t 0 (dark) .. 1 (light)."""
    t = min(max(t, 0.0), 1.0) * 3
    i = min(int(t), 2)
    return mix(R[i], R[i + 1], t - i)


def paint(img, x0, y0, w, h, mat, face, pal, rnd):
    """Fill one face rect. `mat` = '<pattern>' or '<pattern>:<ramp>' (ramp main|acc|det, default by pattern).
    Every pattern is lit from the top-left: a vertical gradient over the face, bevels on plate edges, and its own
    small-scale relief (rivets, scale cells, stone blocks, cloth folds, moss clumps) so the flat layers read as depth."""
    pat, _, rk = mat.partition(':')
    R = [hexrgb(c) + (255,) for c in pal[rk or {'glow': 'acc', 'eye': 'acc', 'moss': 'acc', 'bone': 'det', 'trim': 'det',
                                               'bark': 'det', 'cloth': 'main'}.get(pat, 'main')]]
    A = [hexrgb(c) + (255,) for c in pal['acc']]
    px = img.load()
    side = face not in ('up', 'down')
    lit = {'up': 1.1, 'down': 0.72}.get(face, 1.0)
    bev = 2 if min(w, h) >= 10 else 1
    stones = {}
    for y in range(h):
        for x in range(w):
            gy = y / max(h - 1, 1)
            grad = (0.62 - 0.32 * gy) if side else 0.5          # top of a face catches more light
            n = rnd.uniform(-0.035, 0.035)
            if pat in ('plate', 'ribs', 'runeplate', 'trim'):
                t = grad + n + (0.12 if pat == 'trim' else 0)
                d = (x + y) - (w + h) * 0.3                       # a soft specular streak across the plate
                if abs(d) < 1.5: t += 0.16
                if pat == 'ribs':                                 # overlapping lames: lit top lip, shadow under
                    k = y % 6
                    t += {0: 0.22, 1: 0.1, 5: -0.25}.get(k, 0)
                if y < bev or x < bev: t += 0.2
                if y >= h - bev or x >= w - bev: t -= 0.22
                c = ramp4(R, t)
            elif pat == 'cloth':
                fold = abs(math.sin((x + 0.5) * math.pi / 5.0))   # vertical folds
                t = grad * 0.7 + 0.25 * fold + n
                c = ramp4(R, t)
                if y >= h - 2: c = ramp4([hexrgb(v) + (255,) for v in pal['det']], 0.45 + (0.15 if y == h - 2 else 0))
            elif pat == 'scale':
                off = (y // 4 % 2) * 3
                cy, cx = y % 4, (x + off) % 6
                col, row = (x + off) // 6, y // 4
                t = 0.62 - cy * 0.13 - abs(cx - 2.5) * 0.04 + n  # each scale domed: light top, dark lower lip
                if cx == 0 and cy == 0: t += 0.25
                c = ramp4(R, t)
                if cy == 3: c = ramp4(A, 0.35) if (row * 3 + col) % 7 == 0 else ramp4(R, 0.02)
                if cx == 5 and cy < 3: c = ramp4(R, 0.08)
            elif pat == 'stone':
                bw, bh = 7, 5
                row = y // bh; off = (row % 2) * 3
                key = ((x + off) // bw, row)
                if key not in stones: stones[key] = rnd.uniform(-0.12, 0.12)
                lx, ly = (x + off) % bw, y % bh
                t = 0.55 + stones[key] + grad * 0.3 - 0.15 + n * 2
                if ly == 0 or lx == 0: t += 0.18                  # block top-left edge in light
                if ly == bh - 1 or lx == bw - 1: t = 0.05          # mortar / shadow
                if rnd.random() < 0.03: t += 0.25
                c = ramp4(R, t)
            elif pat == 'moss':
                blob = math.sin(x * 1.3 + rnd.random()) * math.cos(y * 1.1)
                t = 0.35 + 0.25 * blob + grad * 0.3 + n * 3
                c = ramp4(A, t)
            elif pat == 'bone':
                t = 0.55 + grad * 0.35 + n
                if y < bev: t += 0.2
                if y >= h - bev: t -= 0.3
                c = ramp4(R, t)
            elif pat == 'bark':
                t = 0.35 + 0.25 * abs(math.sin(x * 0.9 + y * 0.15)) + n * 2 + grad * 0.2
                c = ramp4(R, t)
            elif pat == 'leather':
                t = 0.35 + grad * 0.45 + n
                if y < bev: t += 0.15
                if y >= h - bev: t -= 0.2
                c = ramp4(R, t)
                if (x in (1, w - 2) or y in (1, h - 2)) and (x + y) % 2 == 0 and w > 5 and h > 5:
                    c = ramp4([hexrgb(v) + (255,) for v in pal['det']], 0.7)
            elif pat == 'void':
                c = ramp4(R, 0.02 + n * 0.3)
            elif pat == 'glow':
                e = min(x, y, w - 1 - x, h - 1 - y)
                c = ramp4(R, 0.6 + 0.4 * min(e, 2) / 2)
            elif pat == 'eye':
                c = ramp4(R, 1.0 if (w <= 2 or 0 < x < w - 1) else 0.75)
            else:
                c = ramp4(R, grad)
            px[x0 + x, y0 + y] = shade(c, lit) if pat not in ('glow', 'eye') else c
    def put(x, y, c):
        if 0 <= x < w and 0 <= y < h: px[x0 + x, y0 + y] = c
    # relief overlays
    if pat in ('plate', 'trim', 'runeplate') and side and w >= 8 and h >= 8:
        for rx, ry in ((2, 2), (w - 3, 2), (2, h - 3), (w - 3, h - 3)):   # rivets with a shadow
            put(rx, ry, shade(ramp4(R, 0.95), lit)); put(rx + 1, ry + 1, shade(ramp4(R, 0.0), lit))
    if pat == 'runeplate' and w >= 6 and h >= 6 and face in ('north', 'south'):
        cx = w // 2
        for y in range(2, h - 2):
            put(cx, y, ramp4(A, 0.8)); put(cx + 1, y, ramp4(A, 0.35)); put(cx - 1, y, shade(ramp4(R, 0.0), lit))
        for k in range(3, h - 3, 5):
            for d in range(1, min(4, cx)):
                put(cx - d, k + d // 2, ramp4(A, 0.75)); put(cx + d, k + d // 2, ramp4(A, 0.75))
                put(cx - d, k + d // 2 + 1, shade(ramp4(R, 0.0), lit))
    if pat == 'stone' and w >= 6 and h >= 6:
        for _ in range(2):   # cracks
            x, y = rnd.randrange(w), 0
            while y < h:
                put(x, y, shade(ramp4(R, 0.0), lit)); put(x + 1, y, shade(ramp4(R, 0.75), lit))
                y += 1; x += rnd.choice((-1, 0, 0, 1))


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


def lames(bone, x0, x1, ytop, n, step, zf, mat):
    """n overlapping horizontal bands going down from ytop; each band sits a little in front of the one below it."""
    out = []
    for i in range(n):
        y1 = ytop - i * step
        z = zf - 0.18 * (n - i)
        out.append(C(bone, [x0, y1 - step - 0.5, z], [x1, y1, z + 0.45], mat))
    return out


def front_back(cubes):
    """A front-facing piece list plus its copy on the back (z mirrored)."""
    out = list(cubes)
    for c in cubes:
        m = dict(c)
        m['from'], m['to'] = [c['from'][0], c['from'][1], -c['to'][2]], [c['to'][0], c['to'][1], -c['from'][2]]
        if c['origin']: m['origin'] = [c['origin'][0], c['origin'][1], -c['origin'][2]]
        if c['rot']: m['rot'] = [-c['rot'][0], c['rot'][1], c['rot'][2]]
        m['faces'] = {{'north': 'south', 'south': 'north'}.get(k, k): v for k, v in c['faces'].items()}
        out.append(m)
    return out


def depth_layers(s):
    """Raised, overlapping pieces per set: what the depth bake shades into plates, lips and shadows."""
    if s == 'bloodrune':
        return (lames('torso', -4.4, 4.4, 15.8, 3, 1.4, -3.55, 'ribs')                                   # abdomen lames
                + [C('torso', [-4.6, 17.6, -3.9], [-0.4, 23.0, -3.3], 'plate', rot=[0, 0, -8], origin=[-2.5, 20, -3.6]),
                   C('torso', [0.4, 17.6, -3.9], [4.6, 23.0, -3.3], 'plate', rot=[0, 0, 8], origin=[2.5, 20, -3.6]),
                   C('torso', [-3.8, 23.4, -3.8], [3.8, 25.2, 3.8], 'plate:det'),                            # gorget
                   C('right_arm', [2.6, 19.2, -3.9], [9.6, 21.4, 3.9], 'plate'), C('right_arm', [2.6, 17.4, -3.6], [9.4, 19.6, 3.6], 'plate'),
                   C('right_arm', [2.8, 16.8, -3.9], [9.2, 18.2, -3.4], 'plate:det'),                        # elbow cop
                   C('right_leg', [-0.6, 9.6, -2.9], [4.6, 12.6, -2.6], 'ribs'),
                   C('right_leg', [0.6, 7.4, -3.4], [3.4, 8.6, -2.9], 'plate'),
                   C('right_boot', [-1.2, 2.4, -3.6], [5.2, 3.6, -3.1], 'plate'), C('right_boot', [-1.2, 1.2, -3.8], [5.2, 2.6, -3.3], 'plate')]
                + front_back([C('hips', [-4.6, 12.0, -3.1], [-0.3, 15.0, -2.6], 'plate:det'), C('hips', [0.3, 12.0, -3.1], [4.6, 15.0, -2.6], 'plate:det')]))
    if s == 'necrotic':
        return ([C('torso', [-2.6, 11.0, -3.9], [2.6, 23.0, -3.4], 'cloth:det', {'north': 'cloth:acc'}),         # tabard
                 C('torso', [-5.4, 21.0, -3.8], [5.4, 25.4, 3.8], 'cloth'),                                   # mantle
                 C('torso', [-5.6, 22.6, -4.1], [-2.6, 25.4, 4.1], 'bone'), C('torso', [2.6, 22.6, -4.1], [5.6, 25.4, 4.1], 'bone'),
                 C('right_arm', [2.6, 17.0, -3.7], [9.4, 18.6, 3.7], 'cloth'), C('right_arm', [2.6, 14.2, -3.9], [9.4, 16.0, 3.9], 'cloth'),
                 C('right_leg', [-0.6, 5.0, -2.9], [4.6, 12.6, -2.6], 'cloth'), C('right_leg', [-0.6, 0.8, -3.1], [4.6, 5.4, -2.7], 'cloth'),
                 C('right_boot', [-1.2, 1.0, -3.6], [5.2, 2.6, 3.6], 'leather:det')]
                + front_back([C('hips', [-2.4, 11.5, -3.2], [2.4, 16.0, -2.6], 'cloth:det')]))
    if s == 'dragonforged':
        return (lames('torso', -4.4, 4.4, 15.6, 3, 1.4, -3.55, 'plate')
                + [C('torso', [-4.7, 16.6, -3.9], [-0.3, 23.2, -3.3], 'scale', rot=[0, 0, -10], origin=[-2.5, 20, -3.6]),
                   C('torso', [0.3, 16.6, -3.9], [4.7, 23.2, -3.3], 'scale', rot=[0, 0, 10], origin=[2.5, 20, -3.6]),
                   C('right_arm', [2.6, 19.0, -3.9], [9.7, 21.2, 3.9], 'scale'), C('right_arm', [2.6, 17.2, -3.7], [9.5, 19.4, 3.7], 'scale'),
                   C('right_arm', [2.6, 18.8, -4.0], [9.7, 19.3, 4.0], 'trim'),
                   C('right_arm', [3.4, 12.0, -3.8], [8.6, 13.0, -3.3], 'trim'),
                   C('right_leg', [-0.6, 8.6, -2.9], [4.6, 12.6, -2.6], 'scale'), C('right_leg', [-0.6, 0.8, -2.9], [4.6, 4.8, -2.6], 'scale'),
                   C('right_leg', [1.4, 3.0, -3.3], [2.6, 8.4, -2.9], 'trim'),
                   C('right_boot', [-1.2, 2.0, -3.7], [5.2, 3.4, -3.2], 'plate'), C('right_boot', [-1.2, 3.2, -3.5], [5.2, 4.6, -3.1], 'plate')]
                + front_back([C('hips', [-4.6, 12.4, -3.2], [-0.3, 16.0, -2.6], 'scale'), C('hips', [0.3, 12.4, -3.2], [4.6, 16.0, -2.6], 'scale')]))
    if s == 'shadow_assassin':
        return ([C('torso', [-5.1, 13.4, -3.6], [1.0, 22.6, -3.2], 'leather', rot=[0, 0, 6], origin=[-2, 18, -3.4]),   # wrap jerkin
                 C('torso', [-5.4, 22.4, -3.6], [5.4, 25.3, 3.6], 'cloth'),                                   # cowl collar
                 C('torso', [-4.6, 11.0, -3.9], [-2.6, 13.4, -3.5], 'leather:det'), C('torso', [-1.8, 11.0, -3.8], [0.0, 12.8, -3.5], 'leather:det'),
                 C('right_arm', [2.8, 15.8, -3.6], [9.2, 17.2, 3.6], 'trim:det'), C('right_arm', [2.8, 12.4, -3.7], [9.2, 14.0, 3.7], 'trim:det'),
                 C('right_arm', [3.0, 20.6, -3.5], [9.0, 22.8, 3.5], 'leather'),
                 C('right_leg', [0.0, 9.8, -3.0], [4.2, 11.6, -2.6], 'leather:det'),
                 C('right_boot', [-1.2, 0.6, -3.6], [5.2, 2.4, 3.6], 'trim:det'), C('right_boot', [-1.2, 2.8, -3.5], [5.2, 4.0, 3.5], 'trim:det')]
                + front_back([C('hips', [-4.0, 11.5, -3.0], [-1.4, 15.6, -2.6], 'cloth'), C('hips', [1.4, 11.5, -3.0], [4.0, 15.6, -2.6], 'cloth')]))
    if s == 'earthwarden':
        return ([C('torso', [-4.8, 19.4, -3.9], [-0.2, 23.8, -3.3], 'stone', rot=[0, 0, -4], origin=[-2.5, 21.6, -3.6]),
                 C('torso', [0.2, 19.0, -3.9], [4.8, 23.4, -3.3], 'stone', rot=[0, 0, 5], origin=[2.5, 21.2, -3.6]),
                 C('torso', [-4.2, 13.4, -3.7], [-0.6, 17.6, -3.3], 'stone'), C('torso', [0.6, 13.2, -3.7], [4.2, 17.4, -3.3], 'stone'),
                 C('torso', [-5.2, 23.2, -4.0], [5.2, 25.4, 4.0], 'stone', {'up': 'moss'}),
                 C('right_arm', [2.4, 18.4, -4.0], [9.8, 21.0, 4.0], 'stone'), C('right_arm', [2.4, 16.6, -3.8], [9.6, 18.8, 3.8], 'stone'),
                 C('right_arm', [2.6, 20.4, -4.2], [6.4, 21.4, 0.0], 'moss'),
                 C('right_leg', [-0.6, 10.4, -3.0], [4.6, 12.6, -2.6], 'stone'), C('right_leg', [-0.6, 3.4, -3.0], [4.6, 5.4, -2.6], 'stone'),
                 C('right_leg', [0.2, 4.8, -3.6], [3.8, 8.6, -2.9], 'stone', {'north': 'stone'}),
                 C('right_boot', [-1.3, 1.4, -3.9], [5.3, 3.8, -3.2], 'stone'), C('right_boot', [-1.3, 3.6, -3.9], [1.8, 4.4, -3.6], 'moss')]
                + front_back([C('hips', [-4.6, 12.0, -3.1], [4.6, 13.6, -2.6], 'bark'), C('hips', [-3.2, 13.6, -3.0], [3.2, 16.6, -2.6], 'stone')]))
    return []


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


# ---- depth-aware bake --------------------------------------------------------------------------------------------
def cast_depth(elems, p, d):
    """B.cast that also returns the hit distance."""
    hits = []
    for e in elems:
        r = e.hit(p, d)
        if r: hits.append((r[0], e, r[1], r[2]))
    for t, e, face, q in sorted(hits, key=lambda h: h[0]):
        c = e.sample(face, q)
        if c and c[3] >= 128:
            n = e.normal_world(list(B.FACE_N[face]))
            lam = max(0.0, -sum(n[i] * d[i] for i in range(3)))
            k = 0.62 + 0.38 * lam
            return (int(c[0] * k), int(c[1] * k), int(c[2] * k), 255), t
    return None, None


def bake_layer(bones, layer):
    """B.bake_layer plus depth shading: on each face of the vanilla box, a texel whose neighbour up/left sits nearer
    (a raised plate) is in that plate's shadow, a texel nearer than its up/left neighbour is a lit rim, and deeper
    texels are a little darker. Light comes from the top-left like the painted textures."""
    S = B.SCALE
    img = Image.new('RGBA', (64 * S, 32 * S), (0, 0, 0, 0))
    for box, bone, inf in B.LAYERS[layer]:
        (x0, y0, z0), (x1, y1, z1), (u0, v0) = B.BOX[box]
        x0, y0, z0, x1, y1, z1 = x0 - inf, y0 - inf, z0 - inf, x1 + inf, y1 + inf, z1 + inf
        w, h, d = B.BOX[box][1][0] - B.BOX[box][0][0], B.BOX[box][1][1] - B.BOX[box][0][1], B.BOX[box][1][2] - B.BOX[box][0][2]
        W, H, D = x1 - x0, y1 - y0, z1 - z0
        faces = {
            'up':    ((u0 + d, v0), (w, d), lambda s_, t_: (x1 - s_ * W, y1, z1 - t_ * D)),
            'down':  ((u0 + d + w, v0), (w, d), lambda s_, t_: (x1 - s_ * W, y0, z0 + t_ * D)),
            'east':  ((u0, v0 + d), (d, h), lambda s_, t_: (x1, y1 - t_ * H, z1 - s_ * D)),
            'north': ((u0 + d, v0 + d), (w, h), lambda s_, t_: (x1 - s_ * W, y1 - t_ * H, z0)),
            'west':  ((u0 + d + w, v0 + d), (d, h), lambda s_, t_: (x0, y1 - t_ * H, z0 + s_ * D)),
            'south': ((u0 + 2 * d + w, v0 + d), (w, h), lambda s_, t_: (x0 + s_ * W, y1 - t_ * H, z1)),
        }
        elems = bones.get(bone, [])
        for face, ((fu, fv), (fw, fh), at) in faces.items():
            n = B.FACE_N[face]
            FW, FH = fw * S, fh * S
            col, dep = {}, {}
            for j in range(FH):
                for i in range(FW):
                    p = at((i + 0.5) / FW, (j + 0.5) / FH)
                    c, t = cast_depth(elems, [p[k] + n[k] * 30 for k in range(3)], [-n[0], -n[1], -n[2]])
                    if c: col[i, j], dep[i, j] = c, t - 30
            if not dep: continue
            dmin = min(dep.values())
            for (i, j), c in col.items():
                z = dep[i, j]
                k = 1.0 - min(0.22, 0.09 * (z - dmin))            # deeper = darker
                up, lf = dep.get((i, j - 1)), dep.get((i - 1, j))
                dn, rt = dep.get((i, j + 1)), dep.get((i + 1, j))
                for nb, s_shadow in ((up, 0.6), (lf, 0.7), (dep.get((i - 1, j - 1)), 0.75), (dep.get((i, j - 2)), 0.8)):
                    if nb is not None and nb < z - 0.2: k = min(k, s_shadow)   # under a raised neighbour: shadow
                if (up is not None and up > z + 0.2) or (lf is not None and lf > z + 0.2): k *= 1.28   # lit rim
                if (dn is not None and dn > z + 0.2) or (rt is not None and rt > z + 0.2): k *= 0.78   # lower lip
                img.putpixel((fu * S + i, fv * S + j), shade(c, k))
    return img


SETS = {'bloodrune': bloodrune, 'necrotic': necrotic, 'dragonforged': dragonforged,
        'shadow_assassin': shadow_assassin, 'earthwarden': earthwarden}
BONES = ['helmet', 'torso', 'right_arm', 'left_arm', 'hips', 'right_leg', 'left_leg', 'right_boot', 'left_boot']


def face_size(f, t, face):
    dx, dy, dz = abs(t[0] - f[0]), abs(t[1] - f[1]), abs(t[2] - f[2])
    return {'north': (dx, dy), 'south': (dx, dy), 'east': (dz, dy), 'west': (dz, dy), 'up': (dx, dz), 'down': (dx, dz)}[face]


def build_bbmodel(s):
    base = SETS[s]()
    for c in base[5:]:   # the set's own front details (emblems, eyes, straps) sit on top of the raised depth layers
        if c['bone'] != 'helmet' and c['from'][2] < -2.55:
            c['from'] = [c['from'][0], c['from'][1], c['from'][2] - 0.75]
            c['to'] = [c['to'][0], c['to'][1], c['to'][2] - 0.75]
            if c['origin']: c['origin'] = [c['origin'][0], c['origin'][1], c['origin'][2] - 0.75]
    cubes = base + depth_layers(s)
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
        tiles.append([B.render(els, yaw, 8, 320, [0, 19, 0], 36) for yaw in (-25, 155)])
    tw, th = 640, tiles[0][0].height + 26
    sheet = Image.new('RGBA', (len(tiles) * tw, th), (40, 40, 48, 255))
    dr = ImageDraw.Draw(sheet)
    for i, (s, pair) in enumerate(zip(SETS, tiles)):
        sheet.alpha_composite(pair[0], (i * tw, 24)); sheet.alpha_composite(pair[1], (i * tw + 320, 24))
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
            bake_layer(bones, layer).save(p)
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
