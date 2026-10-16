"""Reforged armour (Hydra team / McModels, bought 2026-10) -> RuneBlock pack assets, without MythicArmors or shaders.

The source .bbmodel files are full 3D armour. Their own pack draws chest, legs and boots with an objmc-style entity
shader fed by textures the MythicArmors plugin generates; that path needs GL subgroup extensions macOS lacks and the
plugin itself, so this tool keeps only what vanilla can draw (kuwusaki 2026-10-16: "3D helmet + flat body"):

  helmet      their 3D item model, worn through `equippable` HEAD with no asset id (the head layer draws the item)
  chest/boots baked onto the vanilla `humanoid` layer          (body + right arm, right leg; inflate 1.0)
  leggings    baked onto the vanilla `humanoid_leggings` layer (body + right leg; inflate 0.5)

Baking = an orthographic ray per texel, cast at each face of the vanilla armour box from outside, against the
elements of the matching bone only; the first opaque texel hit wins, lightly shaded by how far the hit face turns
away from the ray. Parts that stick out past the vanilla box (pauldrons, horns) are lost except where they cover a
face. Vanilla mirrors the right limbs onto the left, so only the right-side bones are baked.

Usage: python3 -I tools/bake_reforged_armour.py <dir with mythicarmors/ + nexo/ from the zip> [--out pack] [--preview x.png]
  --preview renders every set on a plain figure the way vanilla draws it (baked layers on the vanilla armour boxes, the
  helmet from the source model), front and back, without a game client.
"""
import argparse, base64, io, json, math, os, shutil, sys, zipfile
from PIL import Image

METALS = ['leather', 'chainmail', 'copper', 'iron', 'golden', 'diamond', 'netherite']
SCALE = 2                       # 128x64 layers: 2 rays per model pixel, so angled plates keep their shape
BOX = {                         # vanilla armour boxes in Blockbench space (facing -z, player's right = +x)
    'body': ((-4, 12, -2), (4, 24, 2), (16, 16)),
    'arm':  ((4, 12, -2), (8, 24, 2), (40, 16)),
    'leg':  ((0, 0, -2), (4, 12, 2), (0, 16)),
}
LAYERS = {                      # layer -> [(box, bone, inflate)]
    'humanoid':          [('body', 'torso', 1.0), ('arm', 'right_arm', 1.0), ('leg', 'right_boot', 1.0)],
    'humanoid_leggings': [('body', 'hips', 0.5), ('leg', 'right_leg', 0.5)],
}
ICONS = {'chestplate': ['torso', 'right_arm', 'left_arm'], 'leggings': ['hips', 'right_leg', 'left_leg'],
         'boots': ['right_boot', 'left_boot']}


# ---- maths -----------------------------------------------------------------------------------------------------
def rot_matrix(r):
    """Blockbench Euler degrees, order ZYX (X applied first)."""
    ax, ay, az = (math.radians(a) for a in r)
    cx, sx, cy, sy, cz, sz = math.cos(ax), math.sin(ax), math.cos(ay), math.sin(ay), math.cos(az), math.sin(az)
    rx = [[1, 0, 0], [0, cx, -sx], [0, sx, cx]]
    ry = [[cy, 0, sy], [0, 1, 0], [-sy, 0, cy]]
    rz = [[cz, -sz, 0], [sz, cz, 0], [0, 0, 1]]
    return mul(rz, mul(ry, rx))

def mul(a, b): return [[sum(a[i][k] * b[k][j] for k in range(3)) for j in range(3)] for i in range(3)]
def mv(m, v): return [sum(m[i][k] * v[k] for k in range(3)) for i in range(3)]
def tr(m): return [[m[j][i] for j in range(3)] for i in range(3)]
def sub(a, b): return [a[i] - b[i] for i in range(3)]
def add(a, b): return [a[i] + b[i] for i in range(3)]


class Elem:
    """One cube, with the chain of (origin, rotation) pivots from itself up to the root group."""
    def __init__(self, e, pivots, tex):
        inf = e.get('inflate', 0) or 0
        self.lo = [e['from'][i] - inf for i in range(3)]
        self.hi = [e['to'][i] + inf for i in range(3)]
        self.faces = e['faces']
        self.tex = tex
        chain = []
        if any(e.get('rotation') or [0, 0, 0]):
            chain.append((e['origin'], rot_matrix(e['rotation'])))
        chain += pivots                          # element first, then parents out to the root
        self.chain = chain

    def to_local(self, p, d):
        for o, m in reversed(self.chain):        # undo the root first
            mt = tr(m)
            p = add(mv(mt, sub(p, o)), o)
            d = mv(mt, d)
        return p, d

    def normal_world(self, n):
        for o, m in self.chain: n = mv(m, n)
        return n

    def hit(self, p, d):
        """Entry hit of a ray: (t, face, local point) or None."""
        p, d = self.to_local(p, d)
        t0, t1, face = -1e9, 1e9, None
        for i, (neg, pos) in enumerate((('west', 'east'), ('down', 'up'), ('north', 'south'))):
            if abs(d[i]) < 1e-12:
                if p[i] < self.lo[i] or p[i] > self.hi[i]: return None
                continue
            a, b = (self.lo[i] - p[i]) / d[i], (self.hi[i] - p[i]) / d[i]
            fa = neg if d[i] > 0 else pos        # the face the ray enters through on this axis
            if a > b: a, b = b, a
            if a > t0: t0, face = a, fa
            t1 = min(t1, b)
        if face is None or t0 > t1 or t0 < 0: return None
        return t0, face, [p[i] + d[i] * t0 for i in range(3)]

    def sample(self, face, q):
        f = self.faces.get(face)
        if not f or f.get('texture') is None or not f.get('uv'): return None
        lo, hi = self.lo, self.hi
        w, h, dz = hi[0] - lo[0] or 1, hi[1] - lo[1] or 1, hi[2] - lo[2] or 1
        x, y, z = (q[0] - lo[0]) / w, (q[1] - lo[1]) / h, (q[2] - lo[2]) / dz
        s, t = {                                  # Java block-model face orientation, seen from outside
            'north': (1 - x, 1 - y), 'south': (x, 1 - y), 'east': (1 - z, 1 - y), 'west': (z, 1 - y),
            'up': (x, z), 'down': (x, 1 - z)}[face]
        if f.get('rotation', 0) == 180: s, t = 1 - s, 1 - t
        u1, v1, u2, v2 = f['uv']
        img = self.tex[f['texture']]
        sx, sy = img.width / img.uvw, img.height / img.uvh
        u = (u1 + (u2 - u1) * min(max(s, 0), 0.9999)) * sx
        v = (v1 + (v2 - v1) * min(max(t, 0), 0.9999)) * sy
        return img.getpixel((min(int(u), img.width - 1), min(int(v), img.height - 1)))


FACE_N = {'north': (0, 0, -1), 'south': (0, 0, 1), 'east': (1, 0, 0), 'west': (-1, 0, 0), 'up': (0, 1, 0),
          'down': (0, -1, 0)}

def cast(elems, p, d):
    hits = []
    for e in elems:
        r = e.hit(p, d)
        if r: hits.append((r[0], e, r[1], r[2]))
    for t, e, face, q in sorted(hits, key=lambda h: h[0]):
        c = e.sample(face, q)
        if c and c[3] >= 128:
            n = e.normal_world(list(FACE_N[face]))
            lam = max(0.0, -sum(n[i] * d[i] for i in range(3)))
            k = 0.62 + 0.38 * lam
            return (int(c[0] * k), int(c[1] * k), int(c[2] * k), 255)
    return None


# ---- model loading ---------------------------------------------------------------------------------------------
def load(path):
    m = json.load(open(path))
    tex = []
    for t in m['textures']:
        img = Image.open(io.BytesIO(base64.b64decode(t['source'].split(',', 1)[1]))).convert('RGBA')
        img.uvw, img.uvh = t.get('uv_width', img.width), t.get('uv_height', img.height)
        tex.append(img)
    els = {e['uuid']: e for e in m['elements'] if e.get('type', 'cube') == 'cube'}
    groups = {g['uuid']: g for g in m.get('groups', [])}
    bones = {}
    def walk(nodes, top, pivots):
        for n in nodes:
            if isinstance(n, str):
                if n in els: bones.setdefault(top, []).append(Elem(els[n], pivots, tex))
                continue
            g = groups.get(n.get('uuid'), n)
            piv = pivots
            if any(g.get('rotation') or [0, 0, 0]):
                piv = [(g['origin'], rot_matrix(g['rotation']))] + pivots
            walk(n.get('children', []), top or g['name'], piv)
    walk(m['outliner'], None, [])
    return bones


# ---- baking ----------------------------------------------------------------------------------------------------
def bake_layer(bones, layer):
    img = Image.new('RGBA', (64 * SCALE, 32 * SCALE), (0, 0, 0, 0))
    for box, bone, inf in LAYERS[layer]:
        (x0, y0, z0), (x1, y1, z1), (u0, v0) = BOX[box]
        x0, y0, z0, x1, y1, z1 = x0 - inf, y0 - inf, z0 - inf, x1 + inf, y1 + inf, z1 + inf
        w, h, d = BOX[box][1][0] - BOX[box][0][0], BOX[box][1][1] - BOX[box][0][1], BOX[box][1][2] - BOX[box][0][2]
        W, H, D = x1 - x0, y1 - y0, z1 - z0
        # face -> (uv rect origin, size in vanilla px, (s, t) -> point on the face)
        faces = {
            'up':    ((u0 + d, v0), (w, d), lambda s, t: (x1 - s * W, y1, z1 - t * D)),
            'down':  ((u0 + d + w, v0), (w, d), lambda s, t: (x1 - s * W, y0, z0 + t * D)),
            'east':  ((u0, v0 + d), (d, h), lambda s, t: (x1, y1 - t * H, z1 - s * D)),
            'north': ((u0 + d, v0 + d), (w, h), lambda s, t: (x1 - s * W, y1 - t * H, z0)),
            'west':  ((u0 + d + w, v0 + d), (d, h), lambda s, t: (x0, y1 - t * H, z0 + s * D)),
            'south': ((u0 + 2 * d + w, v0 + d), (w, h), lambda s, t: (x0 + s * W, y1 - t * H, z1)),
        }
        elems = bones.get(bone, [])
        for face, ((fu, fv), (fw, fh), at) in faces.items():
            n = FACE_N[face]
            for j in range(fh * SCALE):
                for i in range(fw * SCALE):
                    p = at((i + 0.5) / (fw * SCALE), (j + 0.5) / (fh * SCALE))
                    c = cast(elems, [p[k] + n[k] * 30 for k in range(3)], [-n[0], -n[1], -n[2]])
                    if c: img.putpixel((fu * SCALE + i, fv * SCALE + j), c)
    return img


def icon(bones, names, size=32, ss=4):
    """Near-front view (yaw 22, pitch 10), orthographic, fitted to the icon."""
    elems = [e for n in names for e in bones.get(n, [])]
    yaw, pitch = math.radians(-22), math.radians(10)
    fwd = [math.sin(yaw) * math.cos(pitch), -math.sin(pitch), math.cos(yaw) * math.cos(pitch)]   # toward the model (+z)
    right = [-fwd[2], 0, fwd[0]]                                 # fwd x world-up: the viewer's right
    rl = math.hypot(right[0], right[2]); right = [right[0] / rl, 0, right[2] / rl]
    up = [right[1] * fwd[2] - right[2] * fwd[1], right[2] * fwd[0] - right[0] * fwd[2], right[0] * fwd[1] - right[1] * fwd[0]]
    if up[1] < 0: up = [-u for u in up]
    corners = []
    for e in elems:
        for cx in (e.lo[0], e.hi[0]):
            for cy in (e.lo[1], e.hi[1]):
                for cz in (e.lo[2], e.hi[2]):
                    q = [cx, cy, cz]
                    for o, m in e.chain: q = add(mv(m, sub(q, o)), o)
                    corners.append(q)
    us = [sum(q[i] * right[i] for i in range(3)) for q in corners]
    vs = [sum(q[i] * up[i] for i in range(3)) for q in corners]
    cu, cv = (min(us) + max(us)) / 2, (min(vs) + max(vs)) / 2
    span = max(max(us) - min(us), max(vs) - min(vs)) * 1.04
    n = size * ss
    big = Image.new('RGBA', (n, n), (0, 0, 0, 0))
    for j in range(n):
        for i in range(n):
            a, b = cu + ((i + 0.5) / n - 0.5) * span, cv - ((j + 0.5) / n - 0.5) * span
            p = [right[k] * a + up[k] * b - fwd[k] * 40 for k in range(3)]
            c = cast(elems, p, fwd)
            if c: big.putpixel((i, j), c)
    out = Image.new('RGBA', (size, size), (0, 0, 0, 0))
    for y in range(size):
        for x in range(size):
            px = [big.getpixel((x * ss + a, y * ss + b)) for a in range(ss) for b in range(ss)]
            on = [p for p in px if p[3]]
            if len(on) * 2 >= len(px):
                out.putpixel((x, y), tuple(sum(p[k] for p in on) // len(on) for k in range(3)) + (255,))
    # one-pixel dark outline, like the weapon sprites
    edge = out.copy()
    for y in range(size):
        for x in range(size):
            if out.getpixel((x, y))[3]: continue
            nb = [out.getpixel((x + dx, y + dy)) for dx, dy in ((1, 0), (-1, 0), (0, 1), (0, -1))
                  if 0 <= x + dx < size and 0 <= y + dy < size]
            if any(p[3] for p in nb): edge.putpixel((x, y), (18, 16, 20, 255))
    return edge


class BoxUV(Elem):
    """A vanilla armour / body box textured with box UV from a 64x32-layout image; mirror=True = a left limb."""
    def __init__(self, box, inf, img, mirror=False, colour=None):
        (x0, y0, z0), (x1, y1, z1), (u0, v0) = BOX[box]
        if mirror: x0, x1 = -x1, -x0
        self.lo, self.hi, self.chain = [x0 - inf, y0 - inf, z0 - inf], [x1 + inf, y1 + inf, z1 + inf], []
        self.box, self.inf, self.img, self.mirror, self.colour = box, inf, img, mirror, colour

    def sample(self, face, q):
        if self.colour: return self.colour
        if self.mirror:
            q = [-q[0], q[1], q[2]]
            face = {'east': 'west', 'west': 'east'}.get(face, face)
        (x0, y0, z0), (x1, y1, z1), (u0, v0) = BOX[self.box]
        i = self.inf
        x0, y0, z0, x1, y1, z1 = x0 - i, y0 - i, z0 - i, x1 + i, y1 + i, z1 + i
        w, h, d = BOX[self.box][1][0] - BOX[self.box][0][0], BOX[self.box][1][1] - BOX[self.box][0][1], BOX[self.box][1][2] - BOX[self.box][0][2]
        x, y, z = q
        (fu, fv), (fw, fh), (s, t) = {
            'up':    ((u0 + d, v0), (w, d), ((x1 - x) / (x1 - x0), (z1 - z) / (z1 - z0))),
            'down':  ((u0 + d + w, v0), (w, d), ((x1 - x) / (x1 - x0), (z - z0) / (z1 - z0))),
            'east':  ((u0, v0 + d), (d, h), ((z1 - z) / (z1 - z0), (y1 - y) / (y1 - y0))),
            'north': ((u0 + d, v0 + d), (w, h), ((x1 - x) / (x1 - x0), (y1 - y) / (y1 - y0))),
            'west':  ((u0 + d + w, v0 + d), (d, h), ((z - z0) / (z1 - z0), (y1 - y) / (y1 - y0))),
            'south': ((u0 + 2 * d + w, v0 + d), (w, h), ((x - x0) / (x1 - x0), (y1 - y) / (y1 - y0))),
        }[face]
        sc = self.img.width // 64
        px = int((fu + min(max(s, 0), 0.9999) * fw) * sc); py = int((fv + min(max(t, 0), 0.9999) * fh) * sc)
        return self.img.getpixel((px, py))


def render(elems, yaw_deg, pitch_deg, size, centre, span):
    yaw, pitch = math.radians(yaw_deg), math.radians(pitch_deg)
    fwd = [math.sin(yaw) * math.cos(pitch), -math.sin(pitch), math.cos(yaw) * math.cos(pitch)]
    right = [-fwd[2], 0, fwd[0]]
    rl = math.hypot(right[0], right[2]); right = [right[0] / rl, 0, right[2] / rl]
    up = [right[1] * fwd[2] - right[2] * fwd[1], right[2] * fwd[0] - right[0] * fwd[2], right[0] * fwd[1] - right[1] * fwd[0]]
    if up[1] < 0: up = [-u for u in up]
    img = Image.new('RGBA', (size, int(size * 1.6)), (0, 0, 0, 0))
    for j in range(img.height):
        for i in range(size):
            a = ((i + 0.5) / size - 0.5) * span
            b = (0.8 - (j + 0.5) / size) * span
            p = [centre[k] + right[k] * a + up[k] * b - fwd[k] * 40 for k in range(3)]
            c = cast(elems, p, fwd)
            if c: img.putpixel((i, j), c)
    return img


def preview(src, out, out_assets):
    skin = (196, 160, 130, 255)
    tiles = []
    for metal in METALS:
        bones = load(os.path.join(src, 'mythicarmors', 'models', f'reforged_{metal}_armor.bbmodel'))
        lay = {l: Image.open(os.path.join(out_assets, 'textures', 'entity', 'equipment', l, f'reforged_{metal}.png')).convert('RGBA')
               for l in LAYERS}
        head = Elem({'from': [-4, 24, -4], 'to': [4, 32, 4], 'faces': {}}, [], [])
        head.sample = lambda f, q: skin
        els = [head] + list(bones.get('helmet', []))
        for box, mir in (('body', False), ('arm', False), ('arm', True), ('leg', False), ('leg', True)):
            els.append(BoxUV(box, 0, None, mir, skin))
        for box, mir in (('body', False), ('leg', False), ('leg', True)):
            els.append(BoxUV(box, 0.5, lay['humanoid_leggings'], mir))
        for box, mir in (('body', False), ('arm', False), ('arm', True), ('leg', False), ('leg', True)):
            els.append(BoxUV(box, 1.0, lay['humanoid'], mir))
        for yaw in (-25, 155):
            tiles.append(render(els, yaw, 8, 120, [0, 17, 0], 30))
    sheet = Image.new('RGBA', (len(tiles) * 120, tiles[0].height + 24), (52, 54, 62, 255))
    for i, t in enumerate(tiles): sheet.alpha_composite(t, (i * 120, 20))
    sheet.save(out)


def write_json(path, obj):
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, 'w') as f: json.dump(obj, f, indent=2); f.write('\n')


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('src'); ap.add_argument('--out', default=os.path.join(os.path.dirname(__file__), '..', 'pack'))
    ap.add_argument('--preview')
    a = ap.parse_args()
    A = os.path.join(a.out, 'assets', 'runeblock')
    if a.preview:
        preview(a.src, a.preview, A); print('preview', a.preview); return
    mz = zipfile.ZipFile(os.path.join(a.src, 'nexo', 'pack', 'external_packs', 'mythicarmor.zip'))
    for metal in METALS:
        key = f'reforged_{metal}'
        bones = load(os.path.join(a.src, 'mythicarmors', 'models', f'reforged_{metal}_armor.bbmodel'))
        for layer in LAYERS:
            p = os.path.join(A, 'textures', 'entity', 'equipment', layer, f'{key}.png')
            os.makedirs(os.path.dirname(p), exist_ok=True)
            bake_layer(bones, layer).save(p)
        write_json(os.path.join(A, 'equipment', f'{key}.json'), {'layers': {
            'humanoid': [{'texture': f'runeblock:{key}'}], 'humanoid_leggings': [{'texture': f'runeblock:{key}'}]}})
        for piece, names in ICONS.items():
            p = os.path.join(A, 'textures', 'item', 'reforged', f'{metal}_{piece}.png')
            os.makedirs(os.path.dirname(p), exist_ok=True)
            icon(bones, names).save(p)
            write_json(os.path.join(A, 'models', 'item', 'reforged', f'{metal}_{piece}.json'),
                       {'parent': 'minecraft:item/generated', 'textures': {'layer0': f'runeblock:item/reforged/{metal}_{piece}'}})
            write_json(os.path.join(A, 'items', f'{key}_{piece}.json'),
                       {'model': {'type': 'minecraft:model', 'model': f'runeblock:item/reforged/{metal}_{piece}'}})
        # helmet: their 3D item model, moved into our namespace
        hm = json.loads(mz.read(f'assets/mythicarmor/models/item/reforged_{metal}_armor_head_piece.json'))
        hm.pop('mcmodels', None)
        hm['textures'] = {k: f'runeblock:item/reforged/{metal}_helmet' for k in hm['textures']}
        write_json(os.path.join(A, 'models', 'item', 'reforged', f'{metal}_helmet.json'), hm)
        p = os.path.join(A, 'textures', 'item', 'reforged', f'{metal}_helmet.png')
        with open(p, 'wb') as f: f.write(mz.read(f'assets/mythicarmor/textures/item/reforged_{metal}_armor_head_0.png'))
        write_json(os.path.join(A, 'items', f'{key}_helmet.json'),
                   {'model': {'type': 'minecraft:model', 'model': f'runeblock:item/reforged/{metal}_helmet'}})
        print(metal, 'ok')


if __name__ == '__main__':
    main()
