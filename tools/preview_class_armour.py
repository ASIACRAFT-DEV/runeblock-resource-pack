"""Headless showcase of the class armour (no game client): each set worn by the vanilla Steve skin, front and back,
the way vanilla draws it (3D helmet from the Blockbench file, baked layers on the vanilla armour boxes), with the
4 inventory icons from the pack. One PNG per row of classes.

Usage: python3 -I tools/preview_class_armour.py <minecraft-client.jar> <out dir> [--per 4] [--size 220]
"""
import argparse, io, os, sys, zipfile
from PIL import Image, ImageDraw, ImageFont

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import bake_reforged_armour as B
import make_class_armour as M

HERE = os.path.dirname(os.path.abspath(__file__))
A = os.path.join(HERE, '..', 'pack', 'assets', 'runeblock')
BB = os.path.join(HERE, '..', 'blockbench', 'class_armour')
B.BOX['head'] = ((-4, 24, -4), (4, 32, 4), (0, 0))
ARCH = {'guardian': 'Warrior', 'samurai': 'Warrior', 'monk': 'Warrior', 'assassin': 'Weapon', 'swashbuckler': 'Weapon',
        'bard': 'Weapon', 'cleric': 'Recovery', 'druid': 'Recovery', 'kannagi': 'Recovery', 'sorcerer': 'Magic',
        'summoner': 'Magic', 'enchanter': 'Magic'}
SETS = {'guardian': 'Bastion Plate', 'samurai': 'Ronin Lacquer', 'monk': 'Iron Lotus Garb', 'assassin': 'Nightshroud',
        'swashbuckler': 'Corsair Finery', 'bard': 'Troubadour Attire', 'cleric': 'Sanctified Raiment',
        'druid': 'Grovewarden Hide', 'kannagi': 'Shrine Vestments', 'sorcerer': 'Archmage Regalia',
        'summoner': 'Soulbinder Shroud', 'enchanter': 'Runeweaver Silks'}


def figure(cls, skin, size):
    bones = B.load(os.path.join(BB, f'{cls}_armor.bbmodel'))
    lay = {l: Image.open(os.path.join(A, 'textures', 'entity', 'equipment', l, f'class_{cls}.png')).convert('RGBA')
           for l in B.LAYERS}
    els = [B.BoxUV('head', 0, skin)] + list(bones.get('helmet', []))
    for bx, mir in (('body', False), ('arm', False), ('arm', True), ('leg', False), ('leg', True)):
        els.append(B.BoxUV(bx, 0, skin, mir))
    for bx, mir in (('body', False), ('leg', False), ('leg', True)):
        els.append(B.BoxUV(bx, 0.5, lay['humanoid_leggings'], mir))
    for bx, mir in (('body', False), ('arm', False), ('arm', True), ('leg', False), ('leg', True)):
        els.append(B.BoxUV(bx, 1.0, lay['humanoid'], mir))
    return [B.render(els, yaw, 8, size, [0, 19, 0], 36) for yaw in (-28, 152)]


def font(sz):
    for p in ('/System/Library/Fonts/Supplemental/Arial Bold.ttf', '/System/Library/Fonts/Helvetica.ttc'):
        try: return ImageFont.truetype(p, sz)
        except OSError: pass
    return ImageFont.load_default()


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('jar'); ap.add_argument('out'); ap.add_argument('--per', type=int, default=4)
    ap.add_argument('--size', type=int, default=220)
    a = ap.parse_args()
    skin = Image.open(io.BytesIO(zipfile.ZipFile(a.jar).read('assets/minecraft/textures/entity/player/wide/steve.png'))).convert('RGBA')
    os.makedirs(a.out, exist_ok=True)
    S = a.size
    tw, th = 2 * S + 30, int(S * 1.6) + 140
    f1, f2 = font(22), font(15)
    classes = list(M.CLASSES)
    for row in range(0, len(classes), a.per):
        group = classes[row:row + a.per]
        sheet = Image.new('RGBA', (tw * len(group), th), (0, 0, 0, 255))
        g = ImageDraw.Draw(sheet)
        for y in range(th):                                   # dusk-sky gradient
            k = y / th
            g.line([(0, y), (sheet.width, y)], fill=(int(46 + 30 * k), int(56 + 34 * k), int(84 + 18 * k), 255))
        g.rectangle([0, th - 120, sheet.width, th - 112], fill=(78, 120, 52, 255))
        for i, cls in enumerate(group):
            x = i * tw
            front, back = figure(cls, skin, S)
            sheet.alpha_composite(front, (x + 10, 34)); sheet.alpha_composite(back, (x + 20 + S, 34))
            g.text((x + 14, 8), SETS[cls], font=f1, fill=(255, 236, 170, 255))
            g.text((x + 14, th - 100), f'{cls.capitalize()} · {ARCH[cls]}', font=f2, fill=(230, 232, 240, 255))
            for j, piece in enumerate(['helmet', 'chestplate', 'leggings', 'boots']):
                if piece == 'helmet':   # the helmet's inventory look is its 3D model: show it from the front
                    bones = B.load(os.path.join(BB, f'{cls}_armor.bbmodel'))
                    ic = B.icon(bones, ['helmet'])
                else:
                    ic = Image.open(os.path.join(A, 'textures', 'item', 'class_armour', f'{cls}_{piece}.png')).convert('RGBA')
                ic = ic.resize((64, 64), Image.NEAREST)
                bx = x + 14 + j * 76
                g.rectangle([bx - 3, th - 76, bx + 67, th - 6], fill=(139, 139, 139, 255), outline=(55, 55, 55, 255), width=3)
                sheet.alpha_composite(ic, (bx, th - 73))
        p = os.path.join(a.out, f'class_armour_{row // a.per + 1}.png')
        sheet.convert('RGB').save(p); print(p)


if __name__ == '__main__':
    main()
