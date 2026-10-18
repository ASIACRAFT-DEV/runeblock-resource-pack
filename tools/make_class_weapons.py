"""Class set weapons: the class's Rimeforged weapon model (tools/import_gear_models.py) recoloured with the palette of
its class armour set (tools/make_class_armour.py), so armour and weapon match.

Body pixels (dark / grey) -> the set's main ramp by luminance; glow pixels (saturated) -> the set's accent (or detail)
ramp. Animated glow strips are recoloured frame by frame (same .mcmeta).

Pack ids: item `runeblock:class_<class>_weapon` -> model `runeblock:item/class_weapon/<class>`,
textures `runeblock:item/class_weapon/<class>/<name>`.
Usage: python3 -I tools/make_class_weapons.py [--pack pack]
"""
import argparse, colorsys, json, os, shutil, sys
from PIL import Image

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import make_class_armour as M

# class -> Rimeforged model it is built on (same as the class's Rimeforged weapon in gear.yml), glow ramp.
# Monk (gauntlets) and Sorcerer (grimoire) are made by tools/make_held_variants.py since ArcaneSouls 0.28.1.
WEAPONS = {
    'guardian': ('hammer', 'acc'), 'samurai': ('greatsword', 'acc'),
    'assassin': ('sword', 'acc'), 'swashbuckler': ('sword', 'acc'), 'bard': ('harp', 'acc'),
    'cleric': ('mace', 'acc'), 'druid': ('staff', 'det'), 'kannagi': ('spear', 'acc'),
    'summoner': ('scythe', 'det'), 'enchanter': ('trident', 'det'),
}


def recolour(img, body, glow):
    lum = lambda p: (0.299 * p[0] + 0.587 * p[1] + 0.114 * p[2]) / 255
    px = [img.getpixel((x, y)) for y in range(img.height) for x in range(img.width)]
    def is_glow(p):
        h, s, v = colorsys.rgb_to_hsv(*(c / 255 for c in p[:3]))
        return s >= 0.25 and v >= 0.3
    bl = sorted(lum(p) for p in px if p[3] and not is_glow(p)) or [0, 1]
    lo, hi = bl[len(bl) // 50], bl[-len(bl) // 50 - 1]
    out = img.copy()
    for y in range(img.height):
        for x in range(img.width):
            p = img.getpixel((x, y))
            if not p[3]: continue
            if is_glow(p):
                c = M.ramp(glow, 0.35 + 0.65 * lum(p))           # glow stays bright
            else:
                c = M.ramp(body, (lum(p) - lo) / max(hi - lo, 1e-6))
            out.putpixel((x, y), c + (p[3],))
    return out


def main():
    here = os.path.dirname(os.path.abspath(__file__))
    ap = argparse.ArgumentParser(); ap.add_argument('--pack', default=os.path.join(here, '..', 'pack'))
    a = ap.parse_args()
    A = os.path.join(a.pack, 'assets', 'runeblock')
    for cls, (kind, glow_key) in WEAPONS.items():
        metal, main, acc = M.CLASSES[cls]
        glow = {'acc': acc, 'det': M.DETAIL[cls], 'main': main}[glow_key]
        model = json.load(open(os.path.join(A, 'models', 'item', 'gear', f'rimeforged_{kind}.json')))
        tex = {}
        for k, ref in model['textures'].items():
            ns, path = ref.split(':', 1)
            name = os.path.basename(path)
            src = os.path.join(a.pack, 'assets', ns, 'textures', path + '.png')
            dst_rel = f'item/class_weapon/{cls}/{name}'
            dst = os.path.join(A, 'textures', dst_rel + '.png')
            os.makedirs(os.path.dirname(dst), exist_ok=True)
            recolour(Image.open(src).convert('RGBA'), main, glow).save(dst)
            if os.path.exists(src + '.mcmeta'): shutil.copy(src + '.mcmeta', dst + '.mcmeta')
            tex[k] = f'runeblock:{dst_rel}'
        model['textures'] = tex
        M.B.write_json(os.path.join(A, 'models', 'item', 'class_weapon', f'{cls}.json'), model)
        M.B.write_json(os.path.join(A, 'items', f'class_{cls}_weapon.json'),
                       {'model': {'type': 'minecraft:model', 'model': f'runeblock:item/class_weapon/{cls}'}})
        print(cls, kind, 'ok')


if __name__ == '__main__':
    main()
