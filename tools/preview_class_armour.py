"""Headless showcase of the class armour (no game client): each set worn by the vanilla Steve skin, front and back,
the way vanilla draws it (3D helmet from the Blockbench file, baked layers on the vanilla armour boxes), with the
4 inventory icons from the pack. One PNG per row of classes.

Usage: python3 -I tools/preview_class_armour.py <minecraft-client.jar> <out dir> [--per 4] [--size 220]
"""
import argparse, io, json, math, os, sys, zipfile
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


# ---- held weapon: vanilla third-person right hand, mapped into Blockbench space (px, y up, facing -z) ---------
def rx(a): a = math.radians(a); c, s = math.cos(a), math.sin(a); return [[1, 0, 0], [0, c, -s], [0, s, c]]
def ry(a): a = math.radians(a); c, s = math.cos(a), math.sin(a); return [[c, 0, s], [0, 1, 0], [-s, 0, c]]
def rz(a): a = math.radians(a); c, s = math.cos(a), math.sin(a); return [[c, -s, 0], [s, c, 0], [0, 0, 1]]
def sc(v): return [[v[0], 0, 0], [0, v[1], 0], [0, 0, v[2]]]
def inv3(m):
    a, b, c = m[0]; d, e, f = m[1]; g, h, i = m[2]
    A, Bc, C = e * i - f * h, -(d * i - f * g), d * h - e * g
    det = a * A + b * Bc + c * C
    return [[A / det, -(b * i - c * h) / det, (b * f - c * e) / det],
            [Bc / det, (a * i - c * g) / det, -(a * f - c * d) / det],
            [C / det, -(a * h - b * g) / det, (a * e - b * d) / det]]


def hand_affine(disp):
    """item-model px -> Blockbench px. Vanilla: arm pivot (-5,2,0)/16, arm raised 18 deg (holding pose), Rx(-90) Ry(180),
    translate (1/16, 2/16, -10/16), the model's thirdperson_righthand display (T, R xyz, S), translate (-.5,-.5,-.5).
    Entity model space -> Blockbench: (x, y, z) -> 16 * (-x, 1.501 - y, z)."""
    t = [v / 16 for v in disp.get('translation', [0, 0, 0])]
    r = disp.get('rotation', [0, 0, 0]); s = disp.get('scale', [1, 1, 1])
    Rd = B.mul(rx(r[0]), B.mul(ry(r[1]), rz(r[2])))
    L = B.mul(rx(-18), B.mul(rx(-90), ry(180)))                    # arm, then the hand turn
    M = B.mul(L, B.mul(Rd, sc([v / 16 for v in s])))               # applied to (p - 8 px)
    off = B.add([-5 / 16, 2 / 16, 0], B.mv(L, B.add([1 / 16, 2 / 16, -10 / 16], t)))
    F = [[-16, 0, 0], [0, -16, 0], [0, 0, 16]]
    Lw = B.mul(F, M)
    tw = B.add(B.mv(F, B.sub(off, B.mv(M, [8, 8, 8]))), [0, 1.501 * 16, 0])
    return Lw, tw


class HeldElem(B.Elem):
    def __init__(self, e, tex, Lw, tw):
        r = e.get('rotation')
        if r:
            e = dict(e); rot = [0, 0, 0]; rot['xyz'.index(r['axis'])] = r['angle']
            e['rotation'], e['origin'] = rot, r['origin']
        super().__init__(e, [], tex)
        self.Lw, self.tw, self.Li = Lw, tw, inv3(Lw)

    def hit(self, p, d):
        return super().hit(B.mv(self.Li, B.sub(p, self.tw)), B.mv(self.Li, d))

    def normal_world(self, n):
        n = super().normal_world(n)
        w = [sum(self.Li[k][i] * n[k] for k in range(3)) for i in range(3)]        # inverse transpose
        l = math.sqrt(sum(v * v for v in w)) or 1
        return [v / l for v in w]


def weapon_elems(cls, stand=False):
    m = json.load(open(os.path.join(A, 'models', 'item', 'class_weapon', f'{cls}.json')))
    tex = {}
    for k, ref in m['textures'].items():
        img = Image.open(os.path.join(A, 'textures', ref.split(':', 1)[1] + '.png')).convert('RGBA')
        if img.height > img.width: img = img.crop((0, 0, img.width, img.width))     # animated strip: frame 0
        img.uvw = img.uvh = 16
        tex['#' + k] = img
    if stand:   # upright on its own: the model's z axis (its length) up, centred on 0
        lo = [min(e['from'][i] for e in m['elements']) for i in range(3)]
        hi = [max(e['to'][i] for e in m['elements']) for i in range(3)]
        Lw = rx(-90) if hi[2] - lo[2] > hi[1] - lo[1] else rx(0)          # longest of y / z goes up
        tw = [-v for v in B.mv(Lw, [(lo[i] + hi[i]) / 2 for i in range(3)])]
    else:
        Lw, tw = hand_affine(m.get('display', {}).get('thirdperson_righthand', {}))
    return [HeldElem(e, tex, Lw, tw) for e in m['elements']]


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
    els += weapon_elems(cls)
    return [B.render(els, yaw, 8, size, [0, 19, 0], 40) for yaw in (-40, 140)]


def weapon_view(cls, w, h, yaw=-60):
    els = weapon_elems(cls, stand=True)
    img = B.render(els, yaw, 6, w, [0, 0, 0], 26)
    return img


def font(sz):
    for p in ('/System/Library/Fonts/Supplemental/Arial Bold.ttf', '/System/Library/Fonts/Helvetica.ttc'):
        try: return ImageFont.truetype(p, sz)
        except OSError: pass
    return ImageFont.load_default()


WEAPON_NAMES = {'guardian': 'Bastion Warhammer', 'samurai': 'Ronin Odachi', 'monk': 'Iron Lotus Bo Staff',
                'assassin': 'Nightshroud Shortblade', 'swashbuckler': 'Corsair Sabre', 'bard': 'Troubadour Harp',
                'cleric': 'Sanctified Holy Mace', 'druid': 'Grovewarden Wildstaff', 'kannagi': 'Shrine Naginata',
                'sorcerer': 'Archmage Spellstaff', 'summoner': 'Soulbinder Soulscythe', 'enchanter': 'Runeweaver Sceptre'}


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('jar'); ap.add_argument('out'); ap.add_argument('--per', type=int, default=3)
    ap.add_argument('--size', type=int, default=220)
    a = ap.parse_args()
    skin = Image.open(io.BytesIO(zipfile.ZipFile(a.jar).read('assets/minecraft/textures/entity/player/wide/steve.png'))).convert('RGBA')
    os.makedirs(a.out, exist_ok=True)
    S, W = a.size, int(a.size * 0.62)
    tw, th = 2 * S + W + 40, int(S * 1.6) + 150
    f1, f2, f3 = font(22), font(15), font(13)
    classes = list(M.CLASSES)
    for row in range(0, len(classes), a.per):
        group = classes[row:row + a.per]
        sheet = Image.new('RGBA', (tw * len(group), th), (0, 0, 0, 255))
        g = ImageDraw.Draw(sheet)
        for y in range(th):                                   # dusk-sky gradient
            k = y / th
            g.line([(0, y), (sheet.width, y)], fill=(int(46 + 30 * k), int(56 + 34 * k), int(84 + 18 * k), 255))
        g.rectangle([0, th - 130, sheet.width, th - 122], fill=(78, 120, 52, 255))
        for i, cls in enumerate(group):
            x = i * tw
            if i: g.line([(x, 0), (x, th)], fill=(30, 34, 46, 255), width=2)
            front, back = figure(cls, skin, S)
            wv = weapon_view(cls, W, 0)
            sheet.alpha_composite(front, (x + 8, 34)); sheet.alpha_composite(back, (x + 14 + S, 34))
            sheet.alpha_composite(wv, (x + 24 + 2 * S, 30 + (int(S * 1.6) - wv.height) // 2))
            g.text((x + 14, 8), SETS[cls], font=f1, fill=(255, 236, 170, 255))
            g.text((x + 26 + 2 * S, 12), WEAPON_NAMES[cls], font=f3, fill=(255, 236, 170, 255))
            g.text((x + 14, th - 112), f'{cls.capitalize()} · {ARCH[cls]}', font=f2, fill=(230, 232, 240, 255))
            for j, piece in enumerate(['helmet', 'chestplate', 'leggings', 'boots', 'weapon']):
                if piece == 'helmet':   # the helmet's inventory look is its 3D model: show it from the front
                    ic = B.icon(B.load(os.path.join(BB, f'{cls}_armor.bbmodel')), ['helmet'])
                elif piece == 'weapon':
                    ic = weapon_view(cls, 64, 0, -35).crop((0, 0, 64, 64)) if False else None
                    big = weapon_view(cls, 96, 0, -35)
                    bb = big.getbbox() or (0, 0, 96, 96)
                    ic = big.crop(bb); k = 64 / max(ic.width, ic.height)
                    ic = ic.resize((max(1, int(ic.width * k)), max(1, int(ic.height * k))), Image.LANCZOS)
                else:
                    ic = Image.open(os.path.join(A, 'textures', 'item', 'class_armour', f'{cls}_{piece}.png')).convert('RGBA')
                if piece != 'weapon': ic = ic.resize((64, 64), Image.NEAREST)
                bx = x + 14 + j * 76
                g.rectangle([bx - 3, th - 86, bx + 67, th - 16], fill=(139, 139, 139, 255), outline=(55, 55, 55, 255), width=3)
                sheet.alpha_composite(ic, (bx + (64 - ic.width) // 2, th - 83 + (64 - ic.height) // 2))
        p = os.path.join(a.out, f'class_armour_{row // a.per + 1}.png')
        sheet.convert('RGB').save(p); print(p)


if __name__ == '__main__':
    main()
