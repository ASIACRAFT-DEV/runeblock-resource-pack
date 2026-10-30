"""Dread sets armour (ArcaneSouls 0.37.0, kuwusaki 2026-10-30 "Dark Fantasy" concept art): Bloodrune, Necrotic,
Dragonforged, Shadow Assassin, Earthwarden. Same pipeline as the class armour (make_class_armour.py): a Reforged base
model recoloured with a gradient map, ornament cubes added, baked to a 3D helmet + flat chest/legs/boots.

Pack ids: equipment `runeblock:dread_<set>`, items `runeblock:dread_<set>_<helmet|chestplate|leggings|boots>`.
The .bbmodel files are derived from a bought asset: they stay out of git (blockbench/ is ignored).

Usage: python3 -I tools/make_dread_sets.py <dir with mythicarmors/ + nexo/ from the zip> [--out pack]
       [--bb blockbench/dread_armour] [--from-blockbench] [--preview x.png]
"""
import argparse, json, os, sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import bake_reforged_armour as B
import make_class_armour as M
from make_class_armour import box, belt, cape, shoulder, cuff, knee, boot_band

# set -> base Reforged metal, main ramp (dark -> light), accent ramp (the glow), detail ramp
SETS = {
    'bloodrune':       ('netherite', ['#0c0a0c', '#26201f', '#4a3e3c', '#7a6a66'], ['#160406', '#3a080c', '#a01420', '#ff4a40'],
                        ['#0e0606', '#241010', '#4a1418', '#8a2028']),     # black plate, blood-red glow, dark red cloth
    'necrotic':        ('leather',   ['#0a0810', '#1c1428', '#352650', '#5a4880'], ['#2a0a4a', '#6a1aa8', '#b050ff', '#e8b8ff'],
                        ['#3a362c', '#7a7260', '#c8c0a8', '#f2ecdc']),     # black-violet robe, violet soul glow, bone
    'dragonforged':    ('netherite', ['#0c0a08', '#221c16', '#3e342a', '#665848'], ['#1a0c04', '#4a2208', '#d07a14', '#ffc040'],
                        ['#140806', '#2e140a', '#6a2c10', '#d0581a']),     # black scale, molten gold, ember orange
    'shadow_assassin': ('leather',   ['#06060c', '#12121e', '#22223a', '#3a3a5e'], ['#2a0a40', '#5a1890', '#9a40e0', '#d8a0ff'],
                        ['#202228', '#4a4e58', '#8a909c', '#d0d6e0']),     # night leather, violet glow, blade steel
    'earthwarden':     ('iron',      ['#2a2c28', '#54584e', '#80867a', '#b0b6a8'], ['#0a1606', '#1c3412', '#3a7424', '#86d45a'],
                        ['#2a1808', '#5e3a16', '#94652e', '#d1a26a']),     # mountain stone, moss-green glow, bark
}
SET_NAMES = {'bloodrune': 'Bloodrune', 'necrotic': 'Necrotic', 'dragonforged': 'Dragonforged',
             'shadow_assassin': 'Shadow Assassin', 'earthwarden': 'Earthwarden'}   # kept in sync with arcane-souls gear.yml
TRIM = {
    'bloodrune': [('plackart', 'main'), ('shoulderpad', 'main'), ('tasset', 'det')] + M.TRIM_DEFAULT,
    'dragonforged': [('plackart', 'main'), ('tasset', 'det'), ('shoulderpad', 'main')] + M.TRIM_DEFAULT,
    'earthwarden': [('plackart', 'main'), ('shoulderpad', 'main'), ('tasset', 'det')] + M.TRIM_DEFAULT,
}
# Head = x -4..4, y 24..32, z -4..4 (facing -z). Helmets reach about +-4.75 and y 32.75.
ORNAMENTS = {
    'bloodrune': shoulder('det2') + cape('det1', 'acc2') + cuff('acc1') + knee('acc2') + boot_band('acc1', 6) + [
        box([-3.2, 28.6, -5.2], [-0.8, 29.4, -4.8], 'acc3', 'visor_eye_l'),          # glowing red eye slits
        box([0.8, 28.6, -5.2], [3.2, 29.4, -4.8], 'acc3', 'visor_eye_r'),
        box([-0.5, 30.2, -5.3], [0.5, 33.5, -4.8], 'acc2', 'brow_rune'),
        box([-5.6, 31.5, -0.6], [-4.4, 34.5, 0.6], 'main1', 'horn_l', [0, 0, 25], [-5, 31.5, 0]),
        box([4.4, 31.5, -0.6], [5.6, 34.5, 0.6], 'main1', 'horn_r', [0, 0, -25], [5, 31.5, 0]),
        box([-2.5, 16.5, -3.6], [2.5, 21.5, -3.1], 'acc2', 'emblem_rune', [0, 0, 45], [0, 19, -3.35]),
        box([-0.6, 17.6, -3.9], [0.6, 20.4, -3.6], 'acc3', 'emblem_core')],
    'necrotic': belt('det1', 'acc2') + cape('main1', 'acc2') + shoulder('det2') + cuff('acc1') + boot_band('acc1', 3) + [
        box([-3.6, 25.0, -5.2], [3.6, 30.6, -4.8], 'det2', 'skull_face'),           # bone skull mask
        box([-2.8, 28.0, -5.5], [-1.0, 29.6, -5.2], 'acc3', 'skull_eye_l'),
        box([1.0, 28.0, -5.5], [2.8, 29.6, -5.2], 'acc3', 'skull_eye_r'),
        box([-0.5, 26.6, -5.5], [0.5, 27.6, -5.2], 'main0', 'skull_nose'),
        box([-2.6, 25.2, -5.5], [2.6, 25.9, -5.2], 'det3', 'skull_teeth'),
        box([-5.0, 30.8, -5.0], [5.0, 33.6, 5.0], 'main1', 'hood'),
        box([-1.2, 33.6, 1.0], [1.2, 34.6, 5.2], 'main1', 'hood_peak'),
        box([-3.4, 14, -3.6], [3.4, 16.4, -3.1], 'det2', 'ribcage', bone='torso'),
        box([-1.0, 17.5, -3.9], [1.0, 21.5, -3.6], 'acc2', 'soul_gem', bone='torso')],
    'dragonforged': shoulder('acc2') + cuff('acc2') + knee('det2') + boot_band('acc2', 5) + [
        box([-4.0, 32.4, -4.6], [-3.0, 35.4, -3.6], 'acc2', 'crown_spike_1', [0, 0, 12], [-3.5, 32.4, -4.1]),   # gold horn crown
        box([-1.8, 32.4, -4.8], [-0.8, 36.2, -3.8], 'acc3', 'crown_spike_2'),
        box([0.8, 32.4, -4.8], [1.8, 36.2, -3.8], 'acc3', 'crown_spike_3'),
        box([3.0, 32.4, -4.6], [4.0, 35.4, -3.6], 'acc2', 'crown_spike_4', [0, 0, -12], [3.5, 32.4, -4.1]),
        box([-5.6, 31.0, 1.0], [-4.4, 35.0, 2.2], 'acc1', 'horn_l', [-25, 0, 15], [-5, 31, 1.6]),
        box([4.4, 31.0, 1.0], [5.6, 35.0, 2.2], 'acc1', 'horn_r', [-25, 0, -15], [5, 31, 1.6]),
        box([-3.0, 28.4, -5.2], [3.0, 29.2, -4.8], 'det3', 'visor_glow'),
        box([-3.0, 16.0, -3.6], [3.0, 22.0, -3.1], 'acc2', 'emblem_dragon', [0, 0, 45], [0, 19, -3.35], bone='torso'),
        box([-1.0, 17.8, -3.9], [1.0, 20.2, -3.6], 'det3', 'emblem_eye', bone='torso'),
        box([-4.6, 11.2, -3.7], [4.6, 12.8, -3.1], 'acc1', 'hem', bone='torso')],
    'shadow_assassin': belt('det1', 'acc2', 12.6, 1.0) + cape('main0', 'acc1') + cuff('acc1') + boot_band('main2', 7) + [
        box([-5.0, 25.0, -5.0], [5.0, 33.4, 5.0], 'main0', 'hood'),                  # deep hood, face in shadow
        box([-1.0, 33.4, -1.0], [1.0, 34.4, 5.2], 'main0', 'hood_peak'),
        box([-4.2, 25.0, -5.3], [4.2, 31.0, -5.0], 'main0', 'face_shadow'),
        box([-2.8, 28.2, -5.6], [-1.2, 29.0, -5.3], 'acc3', 'eye_l'),
        box([1.2, 28.2, -5.6], [2.8, 29.0, -5.3], 'acc3', 'eye_r'),
        box([-5.6, 18, -3.6], [5.6, 19, -3.1], 'det2', 'baldric', [0, 0, -35], [0, 18.5, -3.35], bone='torso'),
        box([-1.0, 18.0, -3.9], [1.0, 20.0, -3.6], 'acc2', 'moon_clasp', [0, 0, 45], [0, 19, -3.75], bone='torso')],
    'earthwarden': shoulder('acc1') + cuff('det2') + knee('acc1') + boot_band('det1', 4) + belt('det1', 'acc2') + [
        box([-4.9, 32.2, -4.9], [-1.5, 33.4, -1.5], 'acc1', 'moss_1'),            # moss on the helm
        box([0.8, 32.2, -2.0], [4.9, 33.2, 2.6], 'acc2', 'moss_2'),
        box([-3.5, 32.2, 1.5], [0.5, 33.0, 4.9], 'acc1', 'moss_3'),
        box([-3.0, 28.4, -5.2], [3.0, 29.2, -4.8], 'acc3', 'visor_glow'),
        box([-5.4, 26.0, -1.4], [-4.6, 31.0, 1.4], 'main2', 'cheek_l'),
        box([4.6, 26.0, -1.4], [5.4, 31.0, 1.4], 'main2', 'cheek_r'),
        box([-2.5, 16.5, -3.6], [2.5, 21.5, -3.1], 'main3', 'emblem_stone', bone='torso'),
        box([-1.0, 17.2, -3.9], [1.0, 20.8, -3.6], 'acc3', 'emblem_rune', [0, 0, 45], [0, 19, -3.75], bone='torso'),
        box([-4.6, 22.6, -3.7], [-2.2, 24.6, -3.1], 'acc1', 'moss_shoulder', bone='torso')],
}


def register():
    """Hand the dread sets to make_class_armour's tables, so its build functions work on them unchanged."""
    for s, (metal, main, acc, det) in SETS.items():
        M.CLASSES[s] = (metal, main, acc)
        M.DETAIL[s] = det
        M.ORNAMENTS[s] = ORNAMENTS[s]
        if s in TRIM: M.TRIM[s] = TRIM[s]
        M.SET_NAMES[s] = SET_NAMES[s]


def main():
    here = os.path.dirname(os.path.abspath(__file__))
    ap = argparse.ArgumentParser()
    ap.add_argument('src'); ap.add_argument('--out', default=os.path.join(here, '..', 'pack'))
    ap.add_argument('--bb', default=os.path.join(here, '..', 'blockbench', 'dread_armour'))
    ap.add_argument('--from-blockbench', action='store_true', help='bake the .bbmodel files as they are (your edits)')
    ap.add_argument('--preview')
    a = ap.parse_args()
    register()
    A = os.path.join(a.out, 'assets', 'runeblock')
    os.makedirs(a.bb, exist_ok=True)
    for s, (metal, *_r) in SETS.items():
        bbp = os.path.join(a.bb, f'{s}_armor.bbmodel')
        if a.from_blockbench:
            bb = json.load(open(bbp))
        else:
            bb, _ = M.build_bbmodel(a.src, s)
            with open(bbp, 'w') as f: json.dump(bb, f)
        key = f'dread_{s}'
        bones = B.load(bbp)
        for layer in B.LAYERS:
            p = os.path.join(A, 'textures', 'entity', 'equipment', layer, f'{key}.png')
            os.makedirs(os.path.dirname(p), exist_ok=True)
            B.bake_layer(bones, layer).save(p)
        B.write_json(os.path.join(A, 'equipment', f'{key}.json'), {'layers': {
            'humanoid': [{'texture': f'runeblock:{key}'}], 'humanoid_leggings': [{'texture': f'runeblock:{key}'}]}})
        for piece, names in B.ICONS.items():
            p = os.path.join(A, 'textures', 'item', 'dread_armour', f'{s}_{piece}.png')
            os.makedirs(os.path.dirname(p), exist_ok=True)
            B.icon(bones, names).save(p)
            B.write_json(os.path.join(A, 'models', 'item', 'dread_armour', f'{s}_{piece}.json'),
                         {'parent': 'minecraft:item/generated', 'textures': {'layer0': f'runeblock:item/dread_armour/{s}_{piece}'}})
            B.write_json(os.path.join(A, 'items', f'{key}_{piece}.json'),
                         {'model': {'type': 'minecraft:model', 'model': f'runeblock:item/dread_armour/{s}_{piece}'}})
        hm = M.helmet_item_model(a.src, metal, bb, s)
        tex = f'runeblock:item/dread_armour/{s}_helmet'
        hm['textures'] = {'0': tex, 'particle': tex}
        B.write_json(os.path.join(A, 'models', 'item', 'dread_armour', f'{s}_helmet.json'), hm)
        M.helmet_texture(bb).save(os.path.join(A, 'textures', 'item', 'dread_armour', f'{s}_helmet.png'))
        B.write_json(os.path.join(A, 'items', f'{key}_helmet.json'),
                     {'model': {'type': 'minecraft:model', 'model': f'runeblock:item/dread_armour/{s}_helmet'}})
        print(s, metal, 'ok')
    if a.preview:
        preview(a.bb, A, a.preview); print('preview', a.preview)


def preview(bbdir, A, out):
    """make_class_armour.preview over the dread sets only (its loop reads M.CLASSES and the class_ equipment names)."""
    saved = dict(M.CLASSES)
    M.CLASSES.clear(); M.CLASSES.update({s: saved[s] for s in SETS})
    eq = os.path.join(A, 'textures', 'entity', 'equipment')
    links = []
    for s in SETS:   # preview() looks for class_<set>.png: point those names at the dread textures for the render
        for layer in B.LAYERS:
            src, dst = os.path.join(eq, layer, f'dread_{s}.png'), os.path.join(eq, layer, f'class_{s}.png')
            if not os.path.exists(dst): os.symlink(os.path.abspath(src), dst); links.append(dst)
    try:
        M.preview(bbdir, A, out)
    finally:
        for l in links: os.remove(l)
        M.CLASSES.clear(); M.CLASSES.update(saved)


if __name__ == '__main__':
    main()
