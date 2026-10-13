#!/usr/bin/env python3
"""Builds the gear weapon models (pack/assets/runeblock/{items,models/item/gear,textures/item/gear}).

Source: the `nexusset` (SolForge) and `winterset` (Arctis) models of an extracted asc-ranks-pack release
(v1.18.38), made by PolygonMC. Usage: import_gear_models.py <extracted ranks pack>/assets pack/assets

Lines:
  sunforged  = nexusset as it is (gold glow)
  rimeforged = winterset where it has the weapon (sword, axe, bow, crossbow), else the nexusset model with
               its glow colours swapped for the winterset ice palette
`harp` is the bow model without pull states (a Bard catalyst, not a bow).
"""
import colorsys, json, os, shutil, sys
from PIL import Image

src, pack = sys.argv[1], sys.argv[2]
rb = os.path.join(pack, 'runeblock')
BOW = ['bow', 'bow_0', 'bow_1', 'bow_2']
XBOW = ['crossbow', 'crossbow_0', 'crossbow_1', 'crossbow_2', 'crossbow_charged', 'crossbow_firework']
MELEE = ['greatsword', 'hammer', 'mace', 'scythe', 'spear', 'staff', 'trident']
# line -> [(source namespace, model names, recolour)]
LINES = {'sunforged': [('nexusset', ['sword', 'axe'] + MELEE + BOW + XBOW, None)],
         'rimeforged': [('winterset', ['sword', 'axe', 'bow', 'crossbow'], None), ('nexusset', MELEE + ['harp'], 'ice')]}
ICE = [(0x25, 0x9e, 0xde), (0x1f, 0xdc, 0xcc), (0xa5, 0xfb, 0xdb), (0xfc, 0xfc, 0xfc)]   # orange -> pale yellow

def ice(p):
    r, g, b, a = p
    h, s, v = colorsys.rgb_to_hsv(r / 255, g / 255, b / 255)
    if a == 0 or s < 0.25 or v < 0.3 or h * 360 > 70: return p            # the dark body stays
    t = min(1.0, max(0.0, (h * 360 - 20) / 40)) * (len(ICE) - 1)          # hue 20 (orange) .. 60 (yellow)
    i = min(int(t), len(ICE) - 2); f = t - i
    return tuple(round(ICE[i][k] + (ICE[i + 1][k] - ICE[i][k]) * f) for k in range(3)) + (a,)

copied = set()
def tex(line, ns, ref, recolour):
    assert ref.startswith(ns + ':item/'), ref
    rel = ref[len(ns) + 6:]
    new = f'item/gear/{line}/' + (f'{os.path.dirname(rel)}/n_{os.path.basename(rel)}'.lstrip('/') if recolour else rel)
    s = os.path.join(src, ns, 'textures', 'item', rel + '.png')
    d = os.path.join(rb, 'textures', new + '.png')
    if d not in copied:
        os.makedirs(os.path.dirname(d), exist_ok=True)
        if recolour:
            im = Image.open(s).convert('RGBA'); im.putdata([ice(p) for p in im.getdata()]); im.save(d, optimize=True)
        else: shutil.copyfile(s, d)
        if os.path.exists(s + '.mcmeta'): shutil.copyfile(s + '.mcmeta', d + '.mcmeta')
        copied.add(d)
    return 'runeblock:' + new

def mref(line, name): return f'runeblock:item/gear/{line}_{name}'
def plain(m): return {'type': 'minecraft:model', 'model': m}
def item(name, model):
    d = os.path.join(rb, 'items', name + '.json')
    os.makedirs(os.path.dirname(d), exist_ok=True)
    with open(d, 'w') as f: json.dump({'model': model}, f, indent=2); f.write('\n')

for line, parts in LINES.items():
    have = set()
    for ns, names, recolour in parts:
        for n in names:
            j = json.load(open(os.path.join(src, ns, 'models', ('bow' if n == 'harp' else n) + '.json')))
            assert 'parent' not in j and 'overrides' not in j, n
            j['textures'] = {k: tex(line, ns, v, recolour) for k, v in j['textures'].items()}
            d = os.path.join(rb, 'models', 'item', 'gear', f'{line}_{n}.json')
            os.makedirs(os.path.dirname(d), exist_ok=True)
            with open(d, 'w') as f: json.dump(j, f, separators=(',', ':'))
            have.add(n)
    for n in sorted(have):
        if n in ('bow', 'crossbow') and n + '_0' in have or '_' in n and n.split('_')[0] in ('bow', 'crossbow'): continue
        item(f'{line}_{n}', plain(mref(line, n)))
    if 'bow_0' in have:      # same shape as the vanilla 1.21.11 bow / crossbow item definitions
        item(f'{line}_harp', plain(mref(line, 'bow')))
        item(f'{line}_bow', {'type': 'minecraft:condition', 'property': 'minecraft:using_item',
            'on_false': plain(mref(line, 'bow')),
            'on_true': {'type': 'minecraft:range_dispatch', 'property': 'minecraft:use_duration', 'scale': 0.05,
                        'entries': [{'threshold': 0.65, 'model': plain(mref(line, 'bow_1'))},
                                    {'threshold': 0.9, 'model': plain(mref(line, 'bow_2'))}],
                        'fallback': plain(mref(line, 'bow_0'))}})
    if 'crossbow_0' in have:
        item(f'{line}_crossbow', {'type': 'minecraft:select', 'property': 'minecraft:charge_type',
            'cases': [{'when': 'arrow', 'model': plain(mref(line, 'crossbow_charged'))},
                      {'when': 'rocket', 'model': plain(mref(line, 'crossbow_firework'))}],
            'fallback': {'type': 'minecraft:condition', 'property': 'minecraft:using_item',
                'on_false': plain(mref(line, 'crossbow')),
                'on_true': {'type': 'minecraft:range_dispatch', 'property': 'minecraft:crossbow/pull',
                            'entries': [{'threshold': 0.58, 'model': plain(mref(line, 'crossbow_1'))},
                                        {'threshold': 1.0, 'model': plain(mref(line, 'crossbow_2'))}],
                            'fallback': plain(mref(line, 'crossbow_0'))}}})
print('textures', len(copied))
