#!/usr/bin/env python3
"""Builds the flat (2D, 32 px) metal weapons: every weapon category in every metal, plus ingots and ores.

Usage: gen_metal_weapons.py <minecraft client jar (1.21.11)> pack/assets
Writes pack/assets/runeblock/{items,models/item/gear,textures/item/gear/metal} as `<metal>_<category>`.
The weapon sprites are our own, drawn by weapon_art.py: plain at Novice, trimmed at Artisan, gems and a glowing
edge at Mythic. The three metals vanilla does not have also get a sword and an axe. Their ingots and ores are
recoloured from the vanilla sprites in the jar (read, never copied unchanged).
"""
import colorsys, io, json, os, sys, zipfile
from PIL import Image
import weapon_art   # the weapon sprites (32 px, drawn from parts, three looks per category by tier)
import held_models  # 3D models while held: gauntlet around the forearm, grimoire open with flipping pages

jar, pack = zipfile.ZipFile(sys.argv[1]), sys.argv[2]
rb = os.path.join(pack, 'runeblock')
METALS = {  # in progression order; ramp = darkest .. highlight
    'wooden':    ['#281e0b', '#493615', '#684e1e', '#896727', '#a8823a'],
    'stone':     ['#2b2b2b', '#494949', '#6f6f6f', '#9a9a9a', '#c2c2c2'],
    'copper':    ['#4a1f12', '#8a3f24', '#c46a45', '#e7936b', '#ffc9a8'],
    'iron':      ['#181818', '#444444', '#969696', '#d8d8d8', '#ffffff'],
    'golden':    ['#50400a', '#b88a1c', '#eac93a', '#fdf55f', '#ffffc0'],
    'diamond':   ['#0e3f36', '#1e8a7b', '#33d6c4', '#8ef5e8', '#ffffff'],
    'netherite': ['#111012', '#2c2a2d', '#4a454a', '#6e676d', '#9a8f96'],
    'mithril':   ['#1b3440', '#3f7f8c', '#7fd0d6', '#c9f5f2', '#ffffff'],
    'bloodiron': ['#2a0a0c', '#6e1518', '#b3282a', '#e8605a', '#ffd0c0'],
    'voidsteel': ['#120a22', '#2e1a52', '#5a34a0', '#9a6ef0', '#e6d4ff'],
}
NEW_METALS = ['mithril', 'bloodiron', 'voidsteel']
def rgb(h): return tuple(int(h[i:i + 2], 16) for i in (1, 3, 5))

def scaled(k, tp, fp):   # the vanilla item/handheld display values with a larger scale: long weapons from a 16 px sprite
    return {'display': {
        'thirdperson_righthand': {'rotation': [0, -90, 55], 'translation': [0, tp, 0.5], 'scale': [k, k, 0.85]},
        'thirdperson_lefthand':  {'rotation': [0, 90, -55], 'translation': [0, tp, 0.5], 'scale': [k, k, 0.85]},
        'firstperson_righthand': {'rotation': [0, -90, 25], 'translation': [1.13, fp, 1.13], 'scale': [k * 0.8, k * 0.8, 0.68]},
        'firstperson_lefthand':  {'rotation': [0, 90, -25], 'translation': [1.13, fp, 1.13], 'scale': [k * 0.8, k * 0.8, 0.68]}}}
HOLD = {'handheld': ('minecraft:item/handheld', None), 'flat': ('minecraft:item/generated', None),
        'big': ('minecraft:item/handheld', scaled(1.3, 7.5, 5.0))}

def recolour(metal, sprite):   # the grey (iron) pixels of a vanilla sprite, mapped by brightness onto the metal's ramp
    stops = [rgb(h) for h in METALS[metal]]
    im = Image.open(io.BytesIO(jar.read(f'assets/minecraft/textures/item/{sprite}.png'))).convert('RGBA'); out = []
    for p in im.getdata():
        if p[3] > 0 and colorsys.rgb_to_hsv(p[0] / 255, p[1] / 255, p[2] / 255)[1] < 0.08:
            t = min(1.0, max(0.0, (p[0] / 255 - 0.09) / 0.91)) * 4; i = min(int(t), 3); f = t - i
            p = tuple(round(stops[i][k] + (stops[i + 1][k] - stops[i][k]) * f) for k in range(3)) + (p[3],)
        out.append(p)
    im.putdata(out); return im
def emit(name, im, hold):
    parent, extra = HOLD[hold]
    for sub, ext in (('textures/item/gear/metal', '.png'), ('models/item/gear', '.json'), ('items', '.json')):
        os.makedirs(os.path.join(rb, sub), exist_ok=True)
    im.save(os.path.join(rb, 'textures/item/gear/metal', name + '.png'), optimize=True)
    j = {'parent': parent, 'textures': {'layer0': f'runeblock:item/gear/metal/{name}'}}; j.update(extra or {})
    with open(os.path.join(rb, 'models/item/gear', name + '.json'), 'w') as f: json.dump(j, f, indent=2); f.write('\n')
    with open(os.path.join(rb, 'items', name + '.json'), 'w') as f:
        json.dump({'model': {'type': 'minecraft:model', 'model': f'runeblock:item/gear/{name}'}}, f, indent=2); f.write('\n')

n = 0
for metal in METALS:
    for cat, (_, hold) in weapon_art.CATEGORIES.items():
        if cat in ('sword', 'axe') and metal not in NEW_METALS: continue
        emit(f'{metal}_{cat}', weapon_art.sprite(cat, metal), hold); n += 1
print(held_models.write(rb), 'held models')
for metal in NEW_METALS:
    # the metal itself: a crafting material (ArcaneSouls gear.yml `ingots:`), flat like a vanilla ingot
    ing = f'{metal}_ingot'
    recolour(metal, 'iron_ingot').save(os.path.join(rb, 'textures/item/gear/metal', ing + '.png'), optimize=True)
    with open(os.path.join(rb, 'models/item/gear', ing + '.json'), 'w') as f:
        json.dump({'parent': 'minecraft:item/generated', 'textures': {'layer0': f'runeblock:item/gear/metal/{ing}'}}, f, indent=2); f.write('\n')
    with open(os.path.join(rb, 'items', ing + '.json'), 'w') as f:
        json.dump({'model': {'type': 'minecraft:model', 'model': f'runeblock:item/gear/{ing}'}}, f, indent=2); f.write('\n')
# the ores (kuwusaki 2026-10-14): vanilla ore block textures with the mineral specks in the new metal; the stone stays
for metal, src in (('mithril', 'diamond_ore'), ('bloodiron', 'iron_ore'), ('voidsteel', 'emerald_ore')):
    im = Image.open(io.BytesIO(jar.read(f'assets/minecraft/textures/block/{src}.png'))).convert('RGBA')
    px = list(im.getdata()); stops = [rgb(h) for h in METALS[metal]]
    speck = [p[3] > 0 and colorsys.rgb_to_hsv(p[0] / 255, p[1] / 255, p[2] / 255)[1] > 0.12 for p in px]
    lum = [(0.299 * p[0] + 0.587 * p[1] + 0.114 * p[2]) / 255 for p in px]
    lo, hi = min(l for l, k in zip(lum, speck) if k), max(l for l, k in zip(lum, speck) if k)
    out = []
    for p, k, l in zip(px, speck, lum):
        if k:
            t = (0.25 + 0.75 * (l - lo) / max(1e-6, hi - lo)) * 4; i = min(int(t), 3); f = t - i   # skip the darkest stop: specks stay readable
            p = tuple(round(stops[i][c] + (stops[i + 1][c] - stops[i][c]) * f) for c in range(3)) + (p[3],)
        out.append(p)
    im.putdata(out); name = f'{metal}_ore'
    os.makedirs(os.path.join(rb, 'textures/block/gear'), exist_ok=True)
    im.save(os.path.join(rb, 'textures/block/gear', name + '.png'), optimize=True)
    os.makedirs(os.path.join(rb, 'models/block/gear'), exist_ok=True)
    with open(os.path.join(rb, 'models/block/gear', name + '.json'), 'w') as f:
        json.dump({'parent': 'minecraft:block/cube_all', 'textures': {'all': f'runeblock:block/gear/{name}'}}, f, indent=2); f.write('\n')
    with open(os.path.join(rb, 'models/item/gear', name + '.json'), 'w') as f:
        json.dump({'parent': f'runeblock:block/gear/{name}'}, f, indent=2); f.write('\n')
    with open(os.path.join(rb, 'items', name + '.json'), 'w') as f:
        json.dump({'model': {'type': 'minecraft:model', 'model': f'runeblock:item/gear/{name}'}}, f, indent=2); f.write('\n')
# The ore BLOCKS in the world are note block states nothing else uses (ArcaneSouls gear.yml `spawn.block`):
# instrument=custom_head, note 1 / 2 / 3. Every other note block state keeps the vanilla model.
INSTRUMENTS = ['harp', 'basedrum', 'snare', 'hat', 'bass', 'flute', 'bell', 'guitar', 'chime', 'xylophone', 'iron_xylophone', 'cow_bell',
               'didgeridoo', 'bit', 'banjo', 'pling', 'zombie', 'skeleton', 'creeper', 'dragon', 'wither_skeleton', 'piglin']   # 1.21.11, + custom_head
ORE_NOTES = {1: 'mithril', 2: 'bloodiron', 3: 'voidsteel'}
variants = {f'instrument={i}': {'model': 'minecraft:block/note_block'} for i in INSTRUMENTS}
for note in range(25):
    variants[f'instrument=custom_head,note={note}'] = {'model': f'runeblock:block/gear/{ORE_NOTES[note]}_ore' if note in ORE_NOTES else 'minecraft:block/note_block'}
os.makedirs(os.path.join(pack, 'minecraft/blockstates'), exist_ok=True)
with open(os.path.join(pack, 'minecraft/blockstates/note_block.json'), 'w') as f: json.dump({'variants': variants}, f, indent=2); f.write('\n')
print(n, 'weapons')
