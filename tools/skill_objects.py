"""3D objects that fly in skills (pack v0.6.9, kuwusaki 2026-10-24: "actual drawn objects flying, not just particles").
ArcaneSouls 0.35.0 spawns them as item displays (`fx: object` in classes.yml, `rbobject{...}` in MythicMobs).

Every model is centred on (8, 8, 8) with its FRONT (tip / leading edge) toward NORTH (-z): the item display renderer turns
items 180 deg about y (1.21.11 `ItemDisplayEntityRenderer.render`), so north in the model is +z in the display's frame, and
ArcaneSouls rotates +z onto the flight direction. Display context NONE = no display transform, so 16 px = 1 block at scale 1.

Usage: python3 -I tools/skill_objects.py [--preview <out.png>]
Writes pack/assets/runeblock/{items/skill_object/,models/item/skill_object/,textures/item/skill_object/}.
"""
import argparse, json, math, os, random, sys
from PIL import Image, ImageDraw, ImageFont

HERE = os.path.dirname(os.path.abspath(__file__))
RB = os.path.join(HERE, '..', 'pack', 'assets', 'runeblock')
SUB = 'skill_object'


# ───────────────────────── textures ─────────────────────────
def _clamp(v): return max(0, min(255, int(v)))

def _noise_tile(seed, base, dark, light, alpha=255, streak=None, size=16):
    """Shaded 16 px tile: base colour, value noise, darker edges; `streak` = (colour, every) horizontal bands."""
    r = random.Random(seed)
    im = Image.new('RGBA', (size, size))
    for y in range(size):
        for x in range(size):
            n = r.random()
            c = base if n < 0.6 else (light if n < 0.8 else dark)
            if x in (0, size - 1) or y in (0, size - 1): c = tuple((a + b) // 2 for a, b in zip(c, dark))
            if streak and (y + x // 3) % streak[1] == 0: c = streak[0]
            im.putpixel((x, y), tuple(c) + (alpha,))
    return im

def tex_fire_core():
    im = Image.new('RGBA', (16, 16)); r = random.Random(11)
    for y in range(16):
        for x in range(16):
            k = abs(x - 7.5) / 7.5
            c = (255, _clamp(250 - 90 * k - r.random() * 30), _clamp(170 - 160 * k))
            im.putpixel((x, y), c + (255,))
    return im

def tex_fire_outer():
    im = Image.new('RGBA', (16, 16)); r = random.Random(12)
    for y in range(16):
        for x in range(16):
            w = math.sin((x + y * 0.6) * 0.9 + r.random()) * 0.5 + 0.5
            c = (_clamp(230 + 25 * w), _clamp(70 + 110 * w), _clamp(10 + 30 * w))
            im.putpixel((x, y), c + (255,))
    return im

def tex_magma():
    im = _noise_tile(21, (58, 40, 36), (30, 22, 22), (84, 60, 50))
    d = ImageDraw.Draw(im); r = random.Random(22)
    for _ in range(4):                                   # glowing cracks
        x, y = r.randrange(16), r.randrange(16)
        for _ in range(7):
            im.putpixel((x % 16, y % 16), (255, _clamp(120 + r.random() * 90), 30, 255))
            x += r.choice((-1, 0, 1)); y += r.choice((0, 1))
    return im

def tex_rock(): return _noise_tile(31, (118, 112, 104), (74, 70, 66), (150, 144, 134))

def tex_ice():
    im = Image.new('RGBA', (16, 16)); r = random.Random(41)
    for y in range(16):
        for x in range(16):
            h = (x + y) % 9 == 0
            c = (235, 250, 255) if h else (_clamp(150 + r.random() * 40), _clamp(215 + r.random() * 25), 255)
            im.putpixel((x, y), c + (255 if h else 205,))
    return im

def tex_water_frames(n=8):
    """Animated: blue body with foam bands that roll down the face (frame strip, frametime 2)."""
    strip = Image.new('RGBA', (16, 16 * n)); r = random.Random(51)
    spots = [(r.randrange(16), r.randrange(16)) for _ in range(10)]
    for f in range(n):
        for y in range(16):
            for x in range(16):
                yy = (y + f * 2) % 16
                w = math.sin((x * 0.7 + yy * 1.1)) * 0.5 + 0.5
                c = (_clamp(30 + 40 * w), _clamp(110 + 60 * w), _clamp(200 + 40 * w))
                a = 215
                if (yy % 8) in (0, 1) and (x + yy) % 3: c, a = (200, 235, 255), 235
                strip.putpixel((x, f * 16 + y), c + (a,))
        for sx, sy in spots:
            strip.putpixel((sx, f * 16 + (sy + f * 2) % 16), (240, 250, 255, 245))
    return strip

def tex_foam(): return _noise_tile(61, (232, 244, 252), (190, 214, 236), (255, 255, 255))

def tex_spectral():
    im = Image.new('RGBA', (16, 16)); r = random.Random(71)
    for y in range(16):
        for x in range(16):
            edge = x in (0, 15) or y in (0, 15)
            c = (230, 255, 255) if edge else (_clamp(130 + r.random() * 50), _clamp(225 + r.random() * 30), 255)
            im.putpixel((x, y), c + (240 if edge else 170,))
    return im

def tex_void():
    im = Image.new('RGBA', (16, 16)); r = random.Random(81)
    for y in range(16):
        for x in range(16):
            s = (x * 2 + y) % 7 == 0
            c = (215, 120, 255) if s else (_clamp(40 + r.random() * 30), 16, _clamp(70 + r.random() * 40))
            im.putpixel((x, y), c + (255,))
    return im

def tex_spirit():
    im = Image.new('RGBA', (16, 16)); r = random.Random(91)
    for y in range(16):
        for x in range(16):
            k = abs(y - 7.5) / 7.5
            c = (_clamp(120 + 100 * (1 - k)), 255, _clamp(170 + 70 * (1 - k)))
            im.putpixel((x, y), c + (_clamp(255 - 70 * k * r.random()),))
    return im

def tex_wood(): return _noise_tile(101, (150, 112, 70), (104, 76, 46), (176, 138, 92), streak=((120, 88, 54), 4))
def tex_steel(): return _noise_tile(111, (196, 204, 214), (130, 138, 150), (236, 242, 250))

TEXTURES = {
    'fire_core': tex_fire_core, 'fire_outer': tex_fire_outer, 'magma': tex_magma, 'rock': tex_rock, 'ice': tex_ice,
    'water': tex_water_frames, 'foam': tex_foam, 'spectral': tex_spectral, 'void': tex_void, 'spirit': tex_spirit,
    'wood': tex_wood, 'steel': tex_steel,
}
ANIMATED = {'water': 2}


# ───────────────────────── geometry ─────────────────────────
class Model:
    def __init__(self): self.els, self.used = [], set()

    def box(self, lo, hi, t, axis=None, angle=0, origin=None, glow=0):
        lo, hi = [float(v) for v in lo], [float(v) for v in hi]
        for i in range(3):
            if lo[i] > hi[i]: lo[i], hi[i] = hi[i], lo[i]
            assert -16 <= lo[i] and hi[i] <= 32, (lo, hi)
        w, h, d = hi[0] - lo[0], hi[1] - lo[1], hi[2] - lo[2]
        def uv(a, b): return [0, 0, max(0.5, min(16, a)), max(0.5, min(16, b))]
        faces = {'north': uv(w, h), 'south': uv(w, h), 'east': uv(d, h), 'west': uv(d, h), 'up': uv(w, d), 'down': uv(w, d)}
        e = {'from': lo, 'to': hi, 'faces': {k: {'uv': v, 'texture': '#' + t} for k, v in faces.items()}}
        if axis and angle:
            e['rotation'] = {'origin': origin or [(lo[i] + hi[i]) / 2 for i in range(3)], 'axis': axis, 'angle': angle}
        if glow: e['light_emission'] = glow
        self.els.append(e); self.used.add(t)
        return self

    def cbox(self, c, s, t, **kw):
        """Box by centre + size."""
        return self.box([c[i] - s[i] / 2 for i in range(3)], [c[i] + s[i] / 2 for i in range(3)], t, **kw)

    def taper(self, z0, z1, s0, s1, t, steps=4, diamond=True, glow=0, cx=8, cy=8):
        """A point along -z: square sections from size s0 at z0 down to s1 at z1 (z1 < z0), plus a 45 deg copy."""
        for i in range(steps):
            za, zb = z0 + (z1 - z0) * i / steps, z0 + (z1 - z0) * (i + 1) / steps
            s = s0 + (s1 - s0) * (i + 0.5) / steps
            self.box([cx - s / 2, cy - s / 2, zb], [cx + s / 2, cy + s / 2, za], t, glow=glow)
            if diamond and s > 0.6:
                self.box([cx - s / 2, cy - s / 2, zb], [cx + s / 2, cy + s / 2, za], t, axis='z', angle=45, origin=[cx, cy, 8], glow=glow)
        return self

    def json(self):
        return {'textures': {t: f'runeblock:item/{SUB}/{t}' for t in sorted(self.used)} | {'particle': f'runeblock:item/{SUB}/{sorted(self.used)[0]}'},
                'elements': self.els}


def searing_lance():
    m = Model()
    m.box([7, 7, 4], [9, 9, 30], 'fire_outer', glow=12)                      # shaft
    m.box([7.4, 7.4, 2], [8.6, 8.6, 31], 'fire_core', glow=15)                # core showing at both ends
    m.box([6, 6, 5], [10, 10, 7], 'fire_core', glow=15)                       # collar
    m.taper(5, -14, 6, 0.6, 'fire_core', steps=6, glow=15)                    # spearhead
    for a in (-30, 30, 90):                                                   # flame fins at the back
        m.box([7.75, 4, 22], [8.25, 12, 31], 'fire_outer', axis='z', angle=a if a != 90 else 0, origin=[8, 8, 26], glow=13) \
            if a != 90 else m.box([4, 7.75, 22], [12, 8.25, 31], 'fire_outer', glow=13)
    m.box([7.75, 4, 22], [8.25, 12, 31], 'fire_outer', glow=13)
    return m

def infernal_meteor():
    m = Model()
    m.cbox([8, 8, 6], [12, 12, 12], 'magma', glow=6)
    for (c, s, ax, ang) in (([8, 8, 6], [10, 13, 10], 'x', 30), ([8, 8, 6], [13, 10, 10], 'y', 40),
                            ([8, 8, 6], [10, 10, 13], 'z', 25), ([4, 10, 3], [5, 5, 5], 'y', 20), ([12, 5, 8], [5, 4, 5], 'x', -25)):
        m.cbox(c, s, 'magma', axis=ax, angle=ang, glow=6)
    m.cbox([8, 8, 14], [9, 9, 6], 'fire_core', glow=15)                       # tail, widening backwards
    m.cbox([8, 8, 20], [11, 11, 8], 'fire_outer', glow=14)
    for a in (-35, 0, 35):
        m.cbox([8, 8, 24], [1, 12, 14], 'fire_outer', axis='z', angle=a, glow=13)
    m.cbox([8, 8, 27], [5, 5, 6], 'fire_core', glow=15)
    return m

def tidal_wave():
    """Cross-section in the y-z plane, extruded along x (48 px wide). The wave rolls toward -z (its front); the barrel
    opens to the front and the lip curls over it. Curl segments sit on a circle, each turned along the tangent."""
    m = Model()
    m.box([-16, -4, 8], [32, 0, 31], 'water')                                 # swell behind the face
    m.box([-16, -4, -6], [32, -1.5, 8], 'foam')                               # foam skirt in front
    cy, cz, R = 10.0, 8.0, 11.0
    steps = list(range(-90, 211, 15))
    for i, phi in enumerate(steps):
        a = math.radians(phi)
        y, z = cy + R * math.sin(a), cz + R * math.cos(a)
        th = 6.0 - 3.5 * i / (len(steps) - 1)                                 # thick at the base, thin at the lip
        ln = 2 * math.pi * R * 15 / 360 + 1.2                                 # segment length along the tangent
        ang = -(phi + 90)
        ang = (ang + 90) % 180 - 90                                           # same box every 180 deg
        sy, sz = th, ln
        if ang > 45: ang -= 90; sy, sz = ln, th                               # a 90 deg turn = swapped sides
        elif ang < -45: ang += 90; sy, sz = ln, th
        t = 'foam' if phi >= 165 or phi <= -75 else 'water'
        m.box([-16, y - sy / 2, z - sz / 2], [32, y + sy / 2, z + sz / 2], t, axis='x', angle=ang, origin=[8, y, z])
    m.box([-16, 5, 13], [32, 19, 17], 'water')                                # back wall filling the curl
    return m

def ice_spear():
    m = Model()
    m.box([7.2, 7.2, 6], [8.8, 8.8, 30], 'ice', glow=8)
    m.box([7.2, 7.2, 6], [8.8, 8.8, 30], 'ice', axis='z', angle=45, origin=[8, 8, 8], glow=8)
    m.taper(6, -14, 5, 0.6, 'ice', steps=5, glow=10)
    for z in (12, 20):                                                        # frost rings
        m.box([6.5, 6.5, z], [9.5, 9.5, z + 1.2], 'foam', glow=10)
    m.taper(30, 31.5, 2.4, 1, 'ice', steps=1, glow=8)
    return m

def spectral_blade():
    m = Model()
    m.box([7.5, 5, -10], [8.5, 11, 22], 'spectral', glow=15)                   # blade (flat, edge up/down)
    m.box([7.75, 7, -10], [8.25, 9, 22], 'steel', glow=15)                     # fuller
    m.taper(-10, -15.5, 6, 0.8, 'spectral', steps=3, diamond=False, glow=15)  # point
    m.box([6, 2, 22], [10, 14, 24], 'spectral', glow=15)                       # guard
    m.box([7, 7, 24], [9, 9, 30], 'steel', glow=12)                            # grip
    m.cbox([8, 8, 31], [3, 3, 2], 'spectral', glow=15)                         # pommel
    return m

def boulder():
    """A rough rock: a small core inside turned slabs, so no face reads as a cube."""
    m = Model()
    m.cbox([8, 8, 8], [11, 11, 11], 'rock')
    for (c, s, ax, ang) in (([8, 8, 8], [15, 9, 12], 'y', 30), ([8, 8, 8], [9, 15, 12], 'x', 35),
                            ([8, 8, 8], [12, 10, 15], 'z', 40), ([8, 9, 8], [13, 8, 10], 'y', -25),
                            ([8, 7, 8], [10, 12, 9], 'z', -30), ([3, 11, 6], [5, 5, 6], 'y', 20),
                            ([13, 5, 11], [5, 4, 6], 'x', -25), ([9, 13, 3], [6, 4, 5], 'z', 15)):
        m.cbox(c, s, 'rock', axis=ax, angle=ang)
    return m

def veil_lance():
    m = Model()
    m.box([7, 7, 2], [9, 9, 31], 'void', glow=10)
    m.taper(2, -15, 7, 0.6, 'void', steps=6, glow=12)
    m.taper(1, -12, 3, 0.4, 'spectral', steps=3, diamond=False, glow=15)
    for i, a in enumerate((0, 45, 90, 135)):                                   # spiral fins along the shaft
        z = 8 + i * 5
        m.box([4, 7.7, z], [12, 8.3, z + 4], 'void', axis='z', angle=[0, 45, -45, 22.5][i], origin=[8, 8, z + 2], glow=12)
    m.cbox([8, 8, 30], [4, 4, 2], 'spectral', glow=15)
    return m

def spirit_arrow():
    m = Model()
    m.box([7.5, 7.5, -4], [8.5, 8.5, 26], 'spirit', glow=15)
    m.taper(-4, -13, 4, 0.5, 'spirit', steps=4, glow=15)
    for a in (0, 90):
        if a == 0: m.box([7.8, 4.5, 20], [8.2, 11.5, 28], 'spirit', glow=13)
        else: m.box([4.5, 7.8, 20], [11.5, 8.2, 28], 'spirit', glow=13)
    m.box([7, 7, 26], [9, 9, 28], 'wood')
    return m

MODELS = {'searing_lance': searing_lance, 'infernal_meteor': infernal_meteor, 'tidal_wave': tidal_wave,
          'ice_spear': ice_spear, 'spectral_blade': spectral_blade, 'boulder': boulder, 'veil_lance': veil_lance,
          'spirit_arrow': spirit_arrow}


# ───────────────────────── write ─────────────────────────
def _save_json(path, obj):
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, 'w') as f: json.dump(obj, f, indent=2); f.write('\n')

def write():
    tdir = os.path.join(RB, 'textures', 'item', SUB); os.makedirs(tdir, exist_ok=True)
    for name, fn in TEXTURES.items():
        fn().save(os.path.join(tdir, name + '.png'))
        if name in ANIMATED: _save_json(os.path.join(tdir, name + '.png.mcmeta'), {'animation': {'frametime': ANIMATED[name]}})
    models = {}
    for name, fn in MODELS.items():
        m = fn(); models[name] = m
        _save_json(os.path.join(RB, 'models', 'item', SUB, name + '.json'), m.json())
        _save_json(os.path.join(RB, 'items', SUB, name + '.json'),
                   {'model': {'type': 'minecraft:model', 'model': f'runeblock:item/{SUB}/{name}'}})
    return models


# ───────────────────────── preview (headless ray cast, no client) ─────────────────────────
def preview(models, out):
    import bake_reforged_armour as B
    tex = {}
    for name in TEXTURES:
        img = Image.open(os.path.join(RB, 'textures', 'item', SUB, name + '.png')).convert('RGBA')
        if img.height > img.width: img = img.crop((0, 0, img.width, img.width))
        img.uvw = img.uvh = 16
        tex['#' + name] = img

    class E(B.Elem):
        def __init__(self, e):
            r = e.get('rotation')
            e = dict(e)
            if r:
                rot = [0, 0, 0]; rot['xyz'.index(r['axis'])] = r['angle']
                e['rotation'], e['origin'] = rot, r['origin']
            e['from'] = [v - 8 for v in e['from']]; e['to'] = [v - 8 for v in e['to']]
            if r: e['origin'] = [v - 8 for v in e['origin']]
            super().__init__(e, [], tex)

    W = 220
    try: ft = ImageFont.truetype('/System/Library/Fonts/Supplemental/Arial.ttf', 15)
    except OSError: ft = ImageFont.load_default()
    tiles = []
    for name, m in models.items():
        els = [E(e) for e in m.els]
        span = 64 if name == 'tidal_wave' else 50
        a = B.render(els, -55, 20, W, [0, 4, 0], span)                       # 3/4 view, front toward the viewer's left
        b = B.render(els, -90, 2, W, [0, 4, 0], span)                        # side view
        tiles.append((name, a, b))
    sheet = Image.new('RGBA', (4 * W * 2 // 2 * 1, 0))
    cols = 4
    th = tiles[0][1].height
    sheet = Image.new('RGBA', (cols * W, (len(tiles) + cols - 1) // cols * (th * 2 + 28)), (44, 46, 54, 255))
    d = ImageDraw.Draw(sheet)
    for i, (name, a, b) in enumerate(tiles):
        x, y = (i % cols) * W, (i // cols) * (th * 2 + 28)
        d.text((x + 8, y + 6), name.replace('_', ' ').title(), fill=(236, 236, 240), font=ft)
        sheet.alpha_composite(a, (x, y + 24 - th // 5)); sheet.alpha_composite(b, (x, y + 24 + th - th // 4))
    sheet.save(out)
    print('preview ->', out)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--preview')
    a = ap.parse_args()
    models = write()
    print('wrote', len(models), 'models,', len(TEXTURES), 'textures under', os.path.normpath(os.path.join(RB, '*', SUB)))
    if a.preview:
        sys.path.insert(0, HERE)
        preview(models, a.preview)

if __name__ == '__main__':
    main()
