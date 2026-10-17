"""Tools for the three metals vanilla does not have (ArcaneSouls 0.22.0 Smithy): pickaxe, shovel, hoe in Mithril,
Bloodiron and Voidsteel, recoloured from the vanilla iron tool sprites in the jar (the grey head pixels mapped by
brightness onto the metal's ramp; the wooden handle kept). Same ramps as weapon_art.METALS. The seven vanilla metals
use their vanilla tool look, so they need nothing here.

Usage: gen_smithy_tools.py <minecraft client jar (1.21.11)> pack/assets
"""
import colorsys, io, json, os, sys, zipfile
from PIL import Image
import weapon_art

NEW_METALS = ['mithril', 'bloodiron', 'voidsteel']
TOOLS = ['pickaxe', 'shovel', 'hoe']
jar, pack = zipfile.ZipFile(sys.argv[1]), sys.argv[2]
rb = os.path.join(pack, 'runeblock')
rgb = weapon_art.rgb

def recolour(metal, sprite):
    stops = [rgb(h) for h in weapon_art.METALS[metal]]
    im = Image.open(io.BytesIO(jar.read(f'assets/minecraft/textures/item/{sprite}.png'))).convert('RGBA'); out = []
    for p in im.getdata():
        if p[3] > 0 and colorsys.rgb_to_hsv(p[0] / 255, p[1] / 255, p[2] / 255)[1] < 0.08:
            t = min(1.0, max(0.0, (p[0] / 255 - 0.09) / 0.91)) * 4; i = min(int(t), 3); f = t - i
            p = tuple(round(stops[i][k] + (stops[i + 1][k] - stops[i][k]) * f) for k in range(3)) + (p[3],)
        out.append(p)
    im.putdata(out); return im

n = 0
for metal in NEW_METALS:
    for tool in TOOLS:
        name = f'{metal}_{tool}'
        for sub in ('textures/item/gear/metal', 'models/item/gear', 'items'):
            os.makedirs(os.path.join(rb, sub), exist_ok=True)
        recolour(metal, f'iron_{tool}').save(os.path.join(rb, 'textures/item/gear/metal', name + '.png'), optimize=True)
        with open(os.path.join(rb, 'models/item/gear', name + '.json'), 'w') as f:
            json.dump({'parent': 'minecraft:item/handheld', 'textures': {'layer0': f'runeblock:item/gear/metal/{name}'}}, f, indent=2); f.write('\n')
        with open(os.path.join(rb, 'items', name + '.json'), 'w') as f:
            json.dump({'model': {'type': 'minecraft:model', 'model': f'runeblock:item/gear/{name}'}}, f, indent=2); f.write('\n')
        n += 1
print(n, 'tools')
