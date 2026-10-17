"""Class armour: one 4-piece set per ArcaneSouls class, built on the Reforged armour models (Hydra team).

For each class this tool:
  1. takes a Reforged base model (.bbmodel), recolours its texture with a gradient map (luminance -> the class palette;
     pixels whose hue stands apart from the main colour get the accent palette),
  2. adds the class ornaments (helmet crest, mask, halo, antlers ... and a chest emblem) as plain cubes,
  3. writes the result as a Blockbench file, `blockbench/class_armour/<class>_armor.bbmodel` (open it in Blockbench to
     edit; re-run with `--from-blockbench` to bake your edits instead of regenerating them),
  4. bakes it exactly like the Reforged sets (bake_reforged_armour.py): 3D helmet, flat chest/legs/boots.

Pack ids: equipment `runeblock:class_<class>`, items `runeblock:class_<class>_<helmet|chestplate|leggings|boots>`.
Ornament cubes are drawn from flat swatches painted into an empty corner of the texture.
The .bbmodel files are derived from a bought asset: they stay out of git (blockbench/ is ignored).

Usage: python3 -I tools/make_class_armour.py <dir with mythicarmors/ + nexo/ from the zip> [--out pack]
       [--bb blockbench/class_armour] [--from-blockbench] [--preview x.png]
"""
import argparse, base64, colorsys, copy, io, json, os, sys, uuid, zipfile
from PIL import Image

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import bake_reforged_armour as B

# class -> base Reforged metal, main ramp (dark -> light), accent ramp, ornaments, emblem colour key
CLASSES = {
    'guardian':     ('iron',      ['#1c2433', '#3d4f6b', '#7f93b0', '#c9d6e8'], ['#4a2c08', '#9c6a14', '#e0b23a', '#fff0a8']),
    'samurai':      ('netherite', ['#140808', '#4a0f12', '#8f1d22', '#d9534f'], ['#2a1a05', '#8a6212', '#d9ab2e', '#fbe39a']),
    'monk':         ('leather',   ['#3a1a06', '#8a3f0c', '#d97a1c', '#ffc46b'], ['#3a0a0a', '#7a1414', '#c42a2a', '#ff7a6a']),
    'assassin':     ('leather', ['#0b0910', '#1d1826', '#3a3150', '#6e6290'], ['#2a0610', '#6e0f26', '#b3203f', '#ff5c7a']),
    'swashbuckler': ('copper',    ['#0c1530', '#1d2f66', '#3a5aa6', '#8fb0ec'], ['#3a2606', '#8a6212', '#d9ab2e', '#fbe39a']),
    'bard':         ('iron',   ['#0e2414', '#1f5230', '#3f8f52', '#9be0a0'], ['#3a2606', '#8a6212', '#d9ab2e', '#fbe39a']),
    'cleric':       ('diamond',   ['#5a5650', '#a8a296', '#e6e0d2', '#ffffff'], ['#4a3006', '#a07418', '#e8c04a', '#fff3b0']),
    'druid':        ('leather', ['#141f0c', '#2e4a18', '#5e8a2c', '#b2d66a'], ['#2a1808', '#5e3a16', '#94652e', '#d1a26a']),
    'kannagi':      ('golden',    ['#6a6260', '#b8b0aa', '#ece6e0', '#ffffff'], ['#3a0606', '#8a1010', '#d42a1e', '#ff7a5a']),
    'sorcerer':     ('diamond',   ['#120a24', '#2e1a5a', '#5c38a8', '#a78bf0'], ['#06303a', '#0e7a8a', '#2ad4e0', '#b8fbff']),
    'summoner':     ('netherite', ['#0a1414', '#1c3436', '#3d6e6a', '#9fd6c8'], ['#2c2a24', '#6e685a', '#bdb6a0', '#f2eedc']),
    'enchanter':    ('copper',    ['#2a0820', '#6a1450', '#b8308a', '#f58ad0'], ['#3a2606', '#8a6212', '#d9ab2e', '#fbe39a']),
}
SET_NAMES = {   # (set name, helmet, chest, legs, boots) - kept in sync with arcane-souls gear.yml
    'guardian': 'Bastion', 'samurai': 'Ronin', 'monk': 'Iron Lotus', 'assassin': 'Nightshroud',
    'swashbuckler': 'Corsair', 'bard': 'Troubadour', 'cleric': 'Sanctified', 'druid': 'Grovewarden',
    'kannagi': 'Shrine', 'sorcerer': 'Archmage', 'summoner': 'Soulbinder', 'enchanter': 'Runeweaver',
}
PIECES = ['helmet', 'chestplate', 'leggings', 'boots']
ITEM_OFF = (8, -16, 8)            # helmet item-model space = Blockbench space + this (checked on all 7 Reforged helmets)

# swatch keys -> (ramp, index); a swatch is a 4x4 flat tile in an empty corner of the 128x128 texture
SWATCH_KEYS = [('main', 0), ('main', 1), ('main', 2), ('main', 3), ('acc', 0), ('acc', 1), ('acc', 2), ('acc', 3)]


def box(f, t, sw, name, rot=None, origin=None):
    """An ornament cube in Blockbench space. `sw` = swatch key like 'acc2'."""
    return {'from': f, 'to': t, 'sw': sw, 'name': name, 'rot': rot, 'origin': origin}


# Head = x -4..4, y 24..32, z -4..4 (facing -z). Helmets reach about +-4.75 and y 32.75.
ORNAMENTS = {
    'guardian': [   # tall crest (red-gold plume) + shield emblem
        box([-0.5, 32.5, -3.5], [0.5, 35.5, 4.0], 'acc2', 'crest'),
        box([-0.5, 35.5, -1.5], [0.5, 36.5, 4.5], 'acc3', 'crest_top'),
        box([-2, 17, -3.6], [2, 21.5, -3.1], 'acc2', 'emblem_shield'),
        box([-0.5, 17.5, -3.9], [0.5, 21, -3.6], 'main3', 'emblem_boss'),
    ],
    'samurai': [    # maedate crescent on the brow + gold mon on the chest
        box([-0.5, 31, -5.6], [0.5, 33, -4.9], 'acc2', 'maedate_stem'),
        box([-3.5, 33, -5.6], [-0.5, 34, -4.9], 'acc2', 'maedate_l', [0, 0, 22.5], [-0.5, 33, -5.25]),
        box([0.5, 33, -5.6], [3.5, 34, -4.9], 'acc2', 'maedate_r', [0, 0, -22.5], [0.5, 33, -5.25]),
        box([-1.5, 18.5, -3.6], [1.5, 21.5, -3.1], 'acc2', 'emblem_mon'),
    ],
    'monk': [       # red headband with knot tails at the back + prayer-bead sash
        box([-4.8, 28.5, -4.8], [4.8, 29.5, 4.8], 'acc2', 'headband'),
        box([-1, 26, 4.8], [-0.2, 29, 5.4], 'acc2', 'band_tail_l', [15, 0, 0], [-0.6, 29, 5]),
        box([0.2, 25.5, 4.8], [1, 29, 5.4], 'acc1', 'band_tail_r', [22.5, 0, 0], [0.6, 29, 5]),
        box([-3, 19, -3.6], [-1.8, 20.2, -3.1], 'acc3', 'bead1'),
        box([-1.2, 17.2, -3.6], [0, 18.4, -3.1], 'acc3', 'bead2'),
        box([0.6, 15.4, -3.6], [1.8, 16.6, -3.1], 'acc3', 'bead3'),
    ],
    'assassin': [   # cloth face mask + hood peak + crimson sash
        box([-4.9, 24, -5.0], [4.9, 27.6, -4.5], 'main1', 'mask'),
        box([-1, 32.5, -4.5], [1, 33.5, 1], 'main1', 'hood_peak'),
        box([-3.5, 19, -3.6], [3.5, 20, -3.1], 'acc2', 'sash', [0, 0, -22.5], [0, 19.5, -3.35]),
    ],
    'swashbuckler': [   # wide brim + gold feather + gold buttons
        box([-6, 31.5, -6], [6, 32.2, 6], 'main1', 'brim'),
        box([2.5, 32, -1], [3.3, 37, 0], 'acc3', 'feather', [0, 0, -22.5], [2.9, 32, -0.5]),
        box([-0.5, 21, -3.6], [0.5, 22, -3.1], 'acc2', 'button1'),
        box([-0.5, 18.5, -3.6], [0.5, 19.5, -3.1], 'acc2', 'button2'),
        box([-0.5, 16, -3.6], [0.5, 17, -3.1], 'acc2', 'button3'),
    ],
    'bard': [       # feathered cap: plume sweeping back + lute-string sash
        box([-4.9, 31, -4.9], [4.9, 32.4, 4.9], 'main2', 'cap_band'),
        box([3.5, 31.5, 0], [4.3, 36.5, 1], 'acc2', 'plume', [-22.5, 0, 0], [3.9, 31.5, 0.5]),
        box([3.6, 33, 1.5], [4.2, 36, 2.3], 'acc3', 'plume2', [-45, 0, 0], [3.9, 33, 1.9]),
        box([-3.5, 21, -3.6], [3.5, 21.7, -3.1], 'acc2', 'sash', [0, 0, 22.5], [0, 21.35, -3.35]),
    ],
    'cleric': [     # floating halo + gold sun on the chest
        box([-3.5, 35, -3.5], [3.5, 35.6, -2.7], 'acc3', 'halo_n'),
        box([-3.5, 35, 2.7], [3.5, 35.6, 3.5], 'acc3', 'halo_s'),
        box([-3.5, 35, -2.7], [-2.7, 35.6, 2.7], 'acc3', 'halo_w'),
        box([2.7, 35, -2.7], [3.5, 35.6, 2.7], 'acc3', 'halo_e'),
        box([-0.6, 16.5, -3.6], [0.6, 22, -3.1], 'acc2', 'emblem_v'),
        box([-2.2, 19.6, -3.6], [2.2, 20.8, -3.1], 'acc2', 'emblem_h'),
    ],
    'druid': [      # antlers + leaf emblem
        box([-3.5, 32, -0.5], [-2.7, 36, 0.5], 'acc2', 'antler_l', [0, 0, 22.5], [-3.1, 32, 0]),
        box([-5.5, 34, -0.4], [-4.0, 34.8, 0.4], 'acc2', 'tine_l'),
        box([2.7, 32, -0.5], [3.5, 36, 0.5], 'acc2', 'antler_r', [0, 0, -22.5], [3.1, 32, 0]),
        box([4.0, 34, -0.4], [5.5, 34.8, 0.4], 'acc2', 'tine_r'),
        box([-1.5, 18, -3.6], [1.5, 21, -3.1], 'main3', 'emblem_leaf', [0, 0, 45], [0, 19.5, -3.35]),
    ],
    'kannagi': [    # red kanzashi tassels on both sides + red cord knot
        box([-5.2, 25, -0.5], [-4.6, 30, 0.5], 'acc2', 'tassel_l'),
        box([4.6, 25, -0.5], [5.2, 30, 0.5], 'acc2', 'tassel_r'),
        box([-5.3, 24, -0.6], [-4.5, 25, 0.6], 'acc3', 'bell_l'),
        box([4.5, 24, -0.6], [5.3, 25, 0.6], 'acc3', 'bell_r'),
        box([-4, 17.5, -3.6], [4, 18.5, -3.1], 'acc2', 'cord'),
        box([-1, 16, -3.6], [1, 18.5, -3.1], 'acc2', 'knot'),
    ],
    'sorcerer': [   # floating arcane crystal over a tall point + rune
        box([-1.2, 32.5, -1.2], [1.2, 34.5, 1.2], 'main2', 'point'),
        box([-0.8, 36, -0.8], [0.8, 38.5, 0.8], 'acc2', 'crystal', [0, 45, 0], [0, 37, 0]),
        box([-1.5, 18, -3.6], [1.5, 21, -3.1], 'acc2', 'rune', [0, 0, 45], [0, 19.5, -3.35]),
    ],
    'summoner': [   # soul gems on the brow + bone collar
        box([-2.6, 29.5, -5.3], [-1.4, 30.7, -4.8], 'acc3', 'soul_l'),
        box([1.4, 29.5, -5.3], [2.6, 30.7, -4.8], 'acc3', 'soul_r'),
        box([-0.6, 30.5, -5.4], [0.6, 31.7, -4.8], 'acc2', 'soul_c'),
        box([-3.5, 22, -3.6], [3.5, 23, -3.1], 'acc2', 'collar'),
        box([-1, 18, -3.6], [1, 21, -3.1], 'acc3', 'emblem_soul'),
    ],
    'enchanter': [  # gold circlet with a floating gem + gem brooch
        box([-4.9, 29.5, -4.9], [4.9, 30.3, 4.9], 'acc2', 'circlet'),
        box([-0.8, 31.2, -5.6], [0.8, 32.8, -4.9], 'main3', 'gem', [0, 0, 45], [0, 32, -5.25]),
        box([-1.2, 18.5, -3.6], [1.2, 20.9, -3.1], 'main3', 'brooch', [0, 0, 45], [0, 19.7, -3.35]),
    ],
}
BONE_OF = lambda name: 'helmet' if not name.startswith(('emblem', 'bead', 'sash', 'button', 'rune', 'cord', 'knot',
                                                         'collar', 'brooch')) else 'torso'


def hexrgb(h): h = h.lstrip('#'); return tuple(int(h[i:i + 2], 16) for i in (0, 2, 4))


def ramp(cols, t):
    t = min(max(t, 0.0), 1.0) * (len(cols) - 1)
    i = min(int(t), len(cols) - 2); f = t - i
    a, b = hexrgb(cols[i]), hexrgb(cols[i + 1])
    return tuple(int(a[k] + (b[k] - a[k]) * f) for k in range(3))


def recolour(img, main, acc):
    px = [img.getpixel((x, y)) for y in range(img.height) for x in range(img.width)]
    on = [p for p in px if p[3] >= 128]
    lum = lambda p: (0.299 * p[0] + 0.587 * p[1] + 0.114 * p[2]) / 255
    ls = sorted(lum(p) for p in on)
    lo, hi = ls[len(ls) // 50], ls[-len(ls) // 50 - 1]
    # dominant hue among saturated pixels (12 bins); pixels whose hue is far from it are "accent"
    bins = [0] * 12
    hs = {}
    for p in on:
        h, s, v = colorsys.rgb_to_hsv(*(c / 255 for c in p[:3])); hs[p[:3]] = (h, s)
        if s > 0.2: bins[int(h * 12) % 12] += 1
    dom = (bins.index(max(bins)) + 0.5) / 12 if max(bins) > len(on) * 0.2 else None
    out = img.copy()
    for y in range(img.height):
        for x in range(img.width):
            p = img.getpixel((x, y))
            if p[3] == 0: continue
            t = (lum(p) - lo) / max(hi - lo, 1e-6)
            h, s = hs.get(p[:3], (0, 0))
            dh = min(abs(h - dom), 1 - abs(h - dom)) if dom is not None else 0
            is_acc = dom is not None and s > 0.3 and dh > 0.11
            out.putpixel((x, y), ramp(acc if is_acc else main, t) + (p[3],))
    return out


def free_corner(img, w=16, h=8):
    """A fully transparent w x h block (on a 2 px grid) to paint swatches into."""
    for y0 in range(img.height - h, -1, -2):
        for x0 in range(img.width - w, -1, -2):
            if all(img.getpixel((x, y))[3] == 0 for y in range(y0, y0 + h) for x in range(x0, x0 + w)):
                return x0, y0
    raise SystemExit('no free 16x8 block in the texture for swatches')


def paint_swatches(img, main, acc):
    x0, y0 = free_corner(img)
    uv = {}
    for i, (r, k) in enumerate(SWATCH_KEYS):
        sx, sy = x0 + (i % 4) * 4, y0 + (i // 4) * 4
        c = hexrgb((main if r == 'main' else acc)[k])
        for y in range(4):
            for x in range(4):
                edge = x in (0, 3) or y in (0, 3)
                k2 = 0.82 if edge else 1.0      # a soft darker rim so cubes read as separate pieces
                img.putpixel((sx + x, sy + y), tuple(int(v * k2) for v in c) + (255,))
        uv[f'{r}{k}'] = (sx, sy)
    return uv


def enc(img):
    b = io.BytesIO(); img.save(b, 'PNG')
    return 'data:image/png;base64,' + base64.b64encode(b.getvalue()).decode()


def face_uvs(sw_xy, scale):
    """Blockbench face uv in texture px (the bbmodel is 128x128 uv); `scale` = 1 for bbmodel, 16/128 for item models."""
    x, y = sw_xy
    r = [(x + 0.5) * scale, (y + 0.5) * scale, (x + 3.5) * scale, (y + 3.5) * scale]
    return {f: {'uv': r, 'texture': 0} for f in ('north', 'east', 'south', 'west', 'up', 'down')}


def build_bbmodel(src, cls):
    metal, main, acc = CLASSES[cls]
    d = json.load(open(os.path.join(src, 'mythicarmors', 'models', f'reforged_{metal}_armor.bbmodel')))
    t = d['textures'][0]
    img = Image.open(io.BytesIO(base64.b64decode(t['source'].split(',', 1)[1]))).convert('RGBA')
    img = recolour(img, main, acc)
    sw = paint_swatches(img, main, acc)
    t['source'] = enc(img)
    t['name'] = f'class_{cls}_armor'
    for k in ('path', 'relative_path', 'folder'): t.pop(k, None)
    d['name'] = f'class_{cls}_armor'
    d.setdefault('meta', {})['model_identifier'] = f'class_{cls}_armor'
    groups = {g['uuid']: g for g in d.get('groups', [])}
    tops = {groups.get(n['uuid'], n).get('name'): n for n in d['outliner'] if isinstance(n, dict)}
    for o in ORNAMENTS[cls]:
        u = str(uuid.uuid4())
        e = {'name': 'asc_' + o['name'], 'box_uv': False, 'rescale': False, 'locked': False, 'render_order': 'default',
             'allow_mirror_modeling': True, 'from': o['from'], 'to': o['to'], 'autouv': 0, 'color': 1,
             'origin': o['origin'] or [(o['from'][i] + o['to'][i]) / 2 for i in range(3)],
             'faces': face_uvs(sw[o['sw']], 1), 'type': 'cube', 'uuid': u}
        if o['rot']: e['rotation'] = o['rot']
        d['elements'].append(e)
        tops[BONE_OF(o['name'])]['children'].append(u)
    return d, img


def helmet_item_model(src, metal, bb, cls):
    """The base helmet item model (15/33/... elements, verified 1:1 with the bbmodel), plus our ornament cubes."""
    mz = zipfile.ZipFile(os.path.join(src, 'nexo', 'pack', 'external_packs', 'mythicarmor.zip'))
    hm = json.loads(mz.read(f'assets/mythicarmor/models/item/reforged_{metal}_armor_head_piece.json'))
    hm.pop('mcmodels', None)
    tex = f'runeblock:item/class_armour/{cls}_helmet'
    hm['textures'] = {'0': tex, 'particle': tex}
    sc = 16 / 128
    for e in bb['elements']:
        if not e.get('name', '').startswith('asc_') or BONE_OF(e['name'][4:]) != 'helmet': continue
        f = [e['from'][i] + ITEM_OFF[i] for i in range(3)]
        t = [e['to'][i] + ITEM_OFF[i] for i in range(3)]
        faces = {k: {'uv': [v * sc / 1 for v in fc['uv']], 'texture': '#0'} for k, fc in e['faces'].items()}
        ie = {'from': f, 'to': t, 'faces': faces}
        r = e.get('rotation')
        if r and any(r):
            ie['rotation'] = {'origin': [e['origin'][i] + ITEM_OFF[i] for i in range(3)], 'x': r[0], 'y': r[1], 'z': r[2]}
        hm['elements'].append(ie)
    return hm


def helmet_texture(bb):
    t = bb['textures'][0]
    return Image.open(io.BytesIO(base64.b64decode(t['source'].split(',', 1)[1]))).convert('RGBA')


def preview(bbdir, A, out):
    skin = (196, 160, 130, 255)
    tiles = []
    for cls in CLASSES:
        bones = B.load(os.path.join(bbdir, f'{cls}_armor.bbmodel'))
        key = f'class_{cls}'
        lay = {l: Image.open(os.path.join(A, 'textures', 'entity', 'equipment', l, f'{key}.png')).convert('RGBA')
               for l in B.LAYERS}
        head = B.Elem({'from': [-4, 24, -4], 'to': [4, 32, 4], 'faces': {}}, [], [])
        head.sample = lambda f, q: skin
        els = [head] + list(bones.get('helmet', []))
        for bx, mir in (('body', False), ('arm', False), ('arm', True), ('leg', False), ('leg', True)):
            els.append(B.BoxUV(bx, 0, None, mir, skin))
        for bx, mir in (('body', False), ('leg', False), ('leg', True)):
            els.append(B.BoxUV(bx, 0.5, lay['humanoid_leggings'], mir))
        for bx, mir in (('body', False), ('arm', False), ('arm', True), ('leg', False), ('leg', True)):
            els.append(B.BoxUV(bx, 1.0, lay['humanoid'], mir))
        tiles.append([B.render(els, yaw, 8, 120, [0, 19, 0], 34) for yaw in (-25, 155)])
    cols = 6
    tw, th = 240, tiles[0][0].height + 22
    sheet = Image.new('RGBA', (cols * tw, ((len(tiles) + cols - 1) // cols) * th), (52, 54, 62, 255))
    from PIL import ImageDraw
    dr = ImageDraw.Draw(sheet)
    for i, (cls, pair) in enumerate(zip(CLASSES, tiles)):
        x, y = (i % cols) * tw, (i // cols) * th
        sheet.alpha_composite(pair[0], (x, y + 18)); sheet.alpha_composite(pair[1], (x + 120, y + 18))
        dr.text((x + 6, y + 4), f'{cls}  ({SET_NAMES[cls]})', fill=(230, 230, 236, 255))
    sheet.save(out)


def main():
    here = os.path.dirname(os.path.abspath(__file__))
    ap = argparse.ArgumentParser()
    ap.add_argument('src'); ap.add_argument('--out', default=os.path.join(here, '..', 'pack'))
    ap.add_argument('--bb', default=os.path.join(here, '..', 'blockbench', 'class_armour'))
    ap.add_argument('--from-blockbench', action='store_true', help='bake the .bbmodel files as they are (your edits)')
    ap.add_argument('--preview')
    a = ap.parse_args()
    A = os.path.join(a.out, 'assets', 'runeblock')
    os.makedirs(a.bb, exist_ok=True)
    for cls, (metal, main, acc) in CLASSES.items():
        bbp = os.path.join(a.bb, f'{cls}_armor.bbmodel')
        if a.from_blockbench:
            bb = json.load(open(bbp))
        else:
            bb, _ = build_bbmodel(a.src, cls)
            with open(bbp, 'w') as f: json.dump(bb, f)
        key = f'class_{cls}'
        bones = B.load(bbp)
        for layer in B.LAYERS:
            p = os.path.join(A, 'textures', 'entity', 'equipment', layer, f'{key}.png')
            os.makedirs(os.path.dirname(p), exist_ok=True)
            B.bake_layer(bones, layer).save(p)
        B.write_json(os.path.join(A, 'equipment', f'{key}.json'), {'layers': {
            'humanoid': [{'texture': f'runeblock:{key}'}], 'humanoid_leggings': [{'texture': f'runeblock:{key}'}]}})
        for piece, names in B.ICONS.items():
            p = os.path.join(A, 'textures', 'item', 'class_armour', f'{cls}_{piece}.png')
            os.makedirs(os.path.dirname(p), exist_ok=True)
            B.icon(bones, names).save(p)
            B.write_json(os.path.join(A, 'models', 'item', 'class_armour', f'{cls}_{piece}.json'),
                         {'parent': 'minecraft:item/generated', 'textures': {'layer0': f'runeblock:item/class_armour/{cls}_{piece}'}})
            B.write_json(os.path.join(A, 'items', f'{key}_{piece}.json'),
                         {'model': {'type': 'minecraft:model', 'model': f'runeblock:item/class_armour/{cls}_{piece}'}})
        B.write_json(os.path.join(A, 'models', 'item', 'class_armour', f'{cls}_helmet.json'),
                     helmet_item_model(a.src, metal, bb, cls))
        helmet_texture(bb).save(os.path.join(A, 'textures', 'item', 'class_armour', f'{cls}_helmet.png'))
        B.write_json(os.path.join(A, 'items', f'{key}_helmet.json'),
                     {'model': {'type': 'minecraft:model', 'model': f'runeblock:item/class_armour/{cls}_helmet'}})
        print(cls, metal, 'ok')
    if a.preview:
        preview(a.bb, A, a.preview); print('preview', a.preview)


if __name__ == '__main__':
    main()
