"""3D models used while a weapon is HELD (pack v0.4.3, kuwusaki 2026-10-14). In the inventory, on the ground and in an
item frame the flat sprite from weapon_art.py stays; in a hand the item definition switches (`minecraft:display_context`):
  gauntlet -> a plated glove around the fist and forearm (ArcaneSouls 0.20.0 puts a twin in the off-hand: both arms)
  grimoire -> an open book whose pages flip (an animated texture: a page turn, then a rune pulsing in the metal's colour)
Called by gen_metal_weapons.py: `write(rb_dir)`. Display transforms are first guesses: check them in a client.
"""
import json, os
from PIL import Image
import weapon_art as W

def _save_json(path, obj):
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, 'w') as f: json.dump(obj, f, indent=2); f.write('\n')

def _ramp(a, mat): return a.ramps[mat]
def _px(c): return tuple(c) + (255,)

# ───────────────────────── gauntlet ─────────────────────────
def gauntlet_texture(metal):
    """32x32 atlas, four 16x16 tiles (uv units 8x8 each): plate | trim / gem | under-layer."""
    a = W.Art(metal); t = a.tier
    im = Image.new('RGBA', (32, 32))
    def tile(ox, oy, ramp, rivets=False, scales=False):
        for y in range(16):
            for x in range(16):
                tone = 2
                if y == 0 or x == 0: tone = 3
                if y == 15 or x == 15: tone = 1
                if scales and y % 4 == 0 and 0 < x < 15: tone = 1          # overlapping plates
                if scales and y % 4 == 1 and 0 < x < 15: tone = 3
                im.putpixel((ox + x, oy + y), _px(ramp[tone]))
        if rivets:
            for x, y in ((3, 3), (12, 3), (3, 12), (12, 12)):
                im.putpixel((ox + x, oy + y), _px(ramp[4])); im.putpixel((ox + x + 1, oy + y + 1), _px(ramp[0]))
    plate = _ramp(a, 'metal')
    tile(0, 0, plate, rivets=True, scales=True)
    tile(16, 0, _ramp(a, 'gold' if t else 'metal'), rivets=False)
    gem = _ramp(a, 'gem')
    for y in range(16):
        for x in range(16):
            d = ((x - 7.5) ** 2 + (y - 7.5) ** 2) ** 0.5
            tone = 4 if d < 2.5 and x < 8 and y < 8 else 3 if d < 5 else 2 if d < 7 else 1
            im.putpixel((x, 16 + y), _px(gem[tone]))
    tile(16, 16, _ramp(a, 'leather' if t == 0 else 'cloth'))
    return im

def _box(frm, to, tex_uv, rot=None):
    faces = {d: {'uv': tex_uv, 'texture': '#t'} for d in ('north', 'south', 'east', 'west', 'up', 'down')}
    e = {'from': frm, 'to': to, 'faces': faces}
    if rot: e['rotation'] = rot
    return e

PLATE, TRIM, GEM, UNDER = [0, 0, 8, 8], [8, 0, 16, 8], [0, 8, 8, 16], [8, 8, 16, 16]
def gauntlet_model(metal):
    """Model frame while held in third person: +Z runs up the arm to the shoulder, the fist ends near z = 8,
    the arm's axis is about x = 8, y = 6 (a 4x4 arm). The glove is 7 wide so it covers either arm."""
    t = W.TIER[metal]
    els = [
        _box([5, 3, 11], [11, 9, 16.5], PLATE),                            # forearm cuff (6 x 6 round a 4 x 4 arm)
        _box([4.6, 2.6, 15.6], [11.4, 9.4, 17], TRIM if t else UNDER),     # cuff rim
        _box([4.8, 2.8, 10], [11.2, 9.2, 11.2], TRIM if t else UNDER),     # wrist band
        _box([5.2, 3.2, 6.6], [10.8, 8.8, 10.2], PLATE),                   # back of the hand
        _box([5.6, 3.6, 6], [10.4, 8.4, 6.8], UNDER),                      # curled fingers
    ]
    for x0 in (5.6, 6.9, 8.2, 9.5):                                        # knuckle plates
        els.append(_box([x0, 8.6, 6.4], [x0 + 1, 9.4, 8], TRIM if t else PLATE))
    if t:
        els.append(_box([10.7, 5, 7.4], [11.2, 7, 9.2], GEM))              # a gem on each side of the hand
        els.append(_box([4.8, 5, 7.4], [5.3, 7, 9.2], GEM))
    if t == 2:
        for y0 in (3.6, 7.4):                                              # cuff fins
            els.append(_box([11, y0, 12], [12.2, y0 + 1, 15.5], TRIM))
            els.append(_box([3.8, y0, 12], [5, y0 + 1, 15.5], TRIM))
        els.append(_box([4.8, 2.8, 13.2], [11.2, 9.2, 13.8], GEM))          # glowing band around the cuff
    disp = {   # tuned in a client 2026-10-14: one model unit in the hand is about 1.45 arm pixels
        'thirdperson_righthand': {'rotation': [0, 0, 0], 'translation': [0, 0, 0], 'scale': [0.62, 0.62, 0.62]},
        'thirdperson_lefthand':  {'rotation': [0, 0, 0], 'translation': [0, 0, 0], 'scale': [0.62, 0.62, 0.62]},
        # first person: seen from behind the forearm, the fist out in front
        'firstperson_righthand': {'rotation': [10, 180, 0], 'translation': [4, 0.5, -3], 'scale': [0.5, 0.5, 0.5]},
        'firstperson_lefthand':  {'rotation': [10, 180, 0], 'translation': [4, 0.5, -3], 'scale': [0.5, 0.5, 0.5]},
    }
    return {'textures': {'t': f'runeblock:item/gear/metal/{metal}_gauntlet_3d', 'particle': f'runeblock:item/gear/metal/{metal}_gauntlet'},
            'elements': els, 'display': disp}

# ───────────────────────── grimoire ─────────────────────────
TURN, IDLE = 8, 16     # frames: a page turn, then the rune pulse; frametime 2 -> 48 ticks a cycle

def page_frames(metal):
    """32 x 32*frames. Left page = x 0..15, right page = x 16..31 (uv u 0..8 / 8..16), lines across, top = far edge."""
    a = W.Art(metal); paper = _ramp(a, 'paper'); ink = _ramp(a, 'cloth'); gem = _ramp(a, 'gem')
    frames = []
    def base(seed):
        im = Image.new('RGBA', (32, 32), _px(paper[3]))
        for x in range(32):
            for y in range(32):
                if x in (0, 31) or y in (0, 31): im.putpixel((x, y), _px(paper[2]))
                if x in (15, 16): im.putpixel((x, y), _px(paper[1]))           # gutter
                if x in (14, 17): im.putpixel((x, y), _px(paper[2]))
        for page, x0 in ((0, 2), (1, 19)):
            for row in range(3, 29, 3):
                if page == 1 and 9 <= row <= 21: continue                       # the rune sits here
                n = 8 + (row * 7 + seed * 5 + page * 3) % 4
                for x in range(x0, x0 + n):
                    if (x + row + seed) % 6 != 0: im.putpixel((x, row), _px(ink[2]))
        return im
    def rune(im, glow):
        cx, cy = 23.5, 15.5
        for x in range(17, 31):
            for y in range(8, 24):
                d = ((x - cx) ** 2 + (y - cy) ** 2) ** 0.5
                if 4.2 <= d <= 5.4 or (d < 4.2 and (abs(x - cx) < 0.6 or abs(y - cy) < 0.6)):
                    im.putpixel((x, y), _px(gem[[1, 1, 2, 3, 3][glow]]))
                elif 5.4 < d <= 6.4 and glow >= 3:
                    im.putpixel((x, y), _px(paper[4]))
    for f in range(TURN):          # a page lifts off the right page and lands on the left
        im = base(0 if f < TURN // 2 else 1)
        k = (f + 0.5) / TURN
        if k < 0.5:                # the turning page over the right page, narrowing toward the gutter
            x1 = int(16 + (1 - k * 2) * 15)
            for x in range(17, x1 + 1):
                for y in range(1, 31): im.putpixel((x, y), _px(paper[4] if x > x1 - 2 else paper[3]))
            for y in range(1, 31): im.putpixel((min(31, x1 + 1), y), _px(paper[1]))
        else:                      # ... and widening over the left page
            x0 = int(15 - (k - 0.5) * 2 * 15)
            for x in range(x0, 15):
                for y in range(1, 31): im.putpixel((x, y), _px(paper[4] if x < x0 + 2 else paper[3]))
            for y in range(1, 31): im.putpixel((max(0, x0 - 1), y), _px(paper[1]))
        if f >= TURN // 2: rune(im, 1)
        frames.append(im)
    for f in range(IDLE):
        im = base(1)
        glow = [1, 2, 3, 3, 4, 3, 3, 2][f % 8] if a.tier else [1, 1, 2, 2, 3, 2, 2, 1][f % 8]
        rune(im, glow)
        frames.append(im)
    sheet = Image.new('RGBA', (32, 32 * len(frames)))
    for i, im in enumerate(frames): sheet.paste(im, (0, 32 * i))
    return sheet

def grimoire_model(metal):
    """Model frame: the open book lies in the XZ plane with its pages facing +Y, spine along Z at x = 8."""
    t = W.TIER[metal]
    cover = 'leather' if t else 'metal'
    def el(frm, to, faces, rot=None):
        e = {'from': frm, 'to': to, 'faces': faces}
        if rot: e['rotation'] = rot
        return e
    C_IN = {'uv': [6, 10, 6.5, 10.5], 'texture': '#cover'}            # a pixel of the closed sprite's cover
    C_OUT = {'uv': [2, 1.5, 12.5, 13], 'texture': '#cover'}            # the closed sprite itself = the outside
    EDGE = {'uv': [0, 0, 16, 2], 'texture': '#edge'}
    els = []
    for side, ang in ((-1, -22.5), (1, 22.5)):
        x0, x1 = (1, 8) if side < 0 else (8, 15)
        rot = {'origin': [8, 7, 8], 'axis': 'z', 'angle': ang}
        els.append(el([x0, 6.5, 2], [x1, 7.2, 14],
                      {'up': C_IN, 'down': C_OUT, 'north': C_IN, 'south': C_IN, 'east': C_IN, 'west': C_IN}, rot))
        p0, p1 = (1.6, 8) if side < 0 else (8, 14.4)
        uv = [0, 0, 8, 16] if side < 0 else [8, 0, 16, 16]
        els.append(el([p0, 7.2, 2.6], [p1, 8.6, 13.4],
                      {'up': {'uv': uv, 'texture': '#pages'}, 'north': EDGE, 'south': EDGE, 'east': EDGE, 'west': EDGE,
                       'down': EDGE}, rot))
    els.append(el([7.2, 6.2, 2], [8.8, 7.2, 14], {d: C_IN for d in ('north', 'south', 'east', 'west', 'up', 'down')}))  # spine
    if t:   # metal corners on the covers
        TR = {'uv': [0, 0, 16, 16], 'texture': '#trim'}
        for side, ang in ((-1, -22.5), (1, 22.5)):
            rot = {'origin': [8, 7, 8], 'axis': 'z', 'angle': ang}
            xa = (0.6, 2.6) if side < 0 else (13.4, 15.4)
            for z0 in (1.6, 12.4):
                els.append(el([xa[0], 6.3, z0], [xa[1], 7.4, z0 + 2], {d: TR for d in ('north', 'south', 'east', 'west', 'up', 'down')}, rot))
    if t == 2:   # a ribbon bookmark and a glowing gem on the spine
        G = {'uv': [0, 0, 16, 16], 'texture': '#gem'}
        els.append(el([7.6, 8.6, 13.4], [8.4, 8.8, 16], {d: G for d in ('north', 'south', 'east', 'west', 'up', 'down')}))
        els.append(el([7.4, 5.6, 7], [8.6, 6.4, 9], {d: G for d in ('north', 'south', 'east', 'west', 'up', 'down')}))
    tex = {'cover': f'runeblock:item/gear/metal/{metal}_grimoire', 'pages': f'runeblock:item/gear/metal/{metal}_grimoire_pages',
           'edge': 'runeblock:item/gear/metal/grimoire_edge', 'trim': f'runeblock:item/gear/metal/{metal}_trim',
           'gem': f'runeblock:item/gear/metal/{metal}_gem', 'particle': f'runeblock:item/gear/metal/{metal}_grimoire'}
    disp = {
        # third person: +Y (the pages) turned up, held open in front of the hand
        'thirdperson_righthand': {'rotation': [90, 0, 0], 'translation': [0, 3, 1], 'scale': [0.7, 0.7, 0.7]},
        'thirdperson_lefthand':  {'rotation': [90, 0, 0], 'translation': [0, 3, 1], 'scale': [0.7, 0.7, 0.7]},
        # first person: pages tilted toward the camera, spine running up the screen
        'firstperson_righthand': {'rotation': [55, 0, 0], 'translation': [-4, 4.5, -3], 'scale': [0.5, 0.5, 0.5]},
        'firstperson_lefthand':  {'rotation': [55, 0, 0], 'translation': [-4, 4.5, -3], 'scale': [0.5, 0.5, 0.5]},
    }
    return {'textures': tex, 'elements': els, 'display': disp}

def small_textures(metal):
    a = W.Art(metal)
    trim = Image.new('RGBA', (16, 16)); gem = Image.new('RGBA', (16, 16))
    tr, gm = _ramp(a, 'gold'), _ramp(a, 'gem')
    for y in range(16):
        for x in range(16):
            trim.putpixel((x, y), _px(tr[3 if x + y < 10 else 2 if x + y < 22 else 1]))
            gem.putpixel((x, y), _px(gm[4 if x + y < 6 else 3 if x + y < 14 else 2 if x + y < 24 else 1]))
    return trim, gem

def edge_texture():
    paper = [W.rgb(h) for h in W.FIXED['paper']]
    im = Image.new('RGBA', (16, 16))
    for y in range(16):
        for x in range(16): im.putpixel((x, y), _px(paper[3 if y % 2 == 0 else 2]))
    return im

def select(flat, held):
    return {'model': {'type': 'minecraft:select', 'property': 'minecraft:display_context',
                      'cases': [{'when': ['gui', 'ground', 'fixed'], 'model': {'type': 'minecraft:model', 'model': flat}}],
                      'fallback': {'type': 'minecraft:model', 'model': held}}}

def write(rb):
    tex = os.path.join(rb, 'textures/item/gear/metal')
    edge_texture().save(os.path.join(tex, 'grimoire_edge.png'), optimize=True)
    for metal in W.METALS:
        gauntlet_texture(metal).save(os.path.join(tex, f'{metal}_gauntlet_3d.png'), optimize=True)
        trim, gem = small_textures(metal)
        trim.save(os.path.join(tex, f'{metal}_trim.png'), optimize=True); gem.save(os.path.join(tex, f'{metal}_gem.png'), optimize=True)
        page_frames(metal).save(os.path.join(tex, f'{metal}_grimoire_pages.png'), optimize=True)
        _save_json(os.path.join(tex, f'{metal}_grimoire_pages.png.mcmeta'), {'animation': {'frametime': 2}})
        _save_json(os.path.join(rb, f'models/item/gear/{metal}_gauntlet_worn.json'), gauntlet_model(metal))
        _save_json(os.path.join(rb, f'models/item/gear/{metal}_grimoire_open.json'), grimoire_model(metal))
        _save_json(os.path.join(rb, f'items/{metal}_gauntlet.json'),
                   select(f'runeblock:item/gear/{metal}_gauntlet', f'runeblock:item/gear/{metal}_gauntlet_worn'))
        _save_json(os.path.join(rb, f'items/{metal}_grimoire.json'),
                   select(f'runeblock:item/gear/{metal}_grimoire', f'runeblock:item/gear/{metal}_grimoire_open'))
    return 2 * len(W.METALS)
