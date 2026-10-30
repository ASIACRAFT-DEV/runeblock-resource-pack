"""Dread set weapons as 32x32 handheld sprites (ArcaneSouls 0.37.0), in the same flat pixel style and palettes as the
Dread armour (dread_pixel.py, after the SolForge / Arctis armour).

Every weapon lies on the 45-degree diagonal like a vanilla sword (handle bottom-left, tip top-right) and is drawn in
diagonal coordinates: u = x - y runs along the weapon, v = x + y - 31 across it, so every edge is a clean pixel
staircase. A weapon is a function (u, v) -> colour or None; a dark outline goes around the result.

Pack ids: items `runeblock:dread_bloodrune_sword`, `dread_necrotic_staff`, `dread_dragonforged_sword`,
`dread_shadow_dagger`, `dread_earthwarden_hammer` (parent minecraft:item/handheld).

Usage: python3 -I tools/dread_weapons.py [--out pack] [--preview x.png]
"""
import argparse, os, sys
from PIL import Image, ImageDraw

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import bake_reforged_armour as B
from dread_pixel import PAL, hx

N = 32


def ramp(s):
    P = PAL[s]
    return {k: [hx(c) for c in v] for k, v in P.items() if isinstance(v, list)}, hx(P['line'])


def blade(u, v, rows, tip_from, tip_to, serrate=0):
    """A straight blade. `rows` = the colours across it, upper-left edge first (one diagonal pixel row each);
    the tip narrows from both edges between tip_from and tip_to."""
    half = len(rows) // 2
    if u > tip_to: return None
    w = half if u < tip_from else half - (u - tip_from + 1) * (half + 1) // (tip_to - tip_from + 2)
    if abs(v) > max(w, 0): return None
    if serrate and v == half and u % serrate == 0: return None   # fangs on the lower edge
    return rows[v + half]


def guard(u, v, at, span, tips, cols, gem=None):
    """A crossguard across the blade at u = at-1..at+1, `span` wide, tips bent toward the blade (`tips` long)."""
    if at - 1 <= u <= at + 1 and abs(v) <= span - (1 if u != at else 0):
        if gem and u == at and v == 0: return gem
        return cols[0] if v < 0 else cols[1]
    if at + 2 <= u <= at + 1 + tips and span - 1 <= abs(v) <= span: return cols[0] if v < 0 else cols[1]
    return None


def bloodfang(u, v):
    C, L = ramp('bloodrune'); T, G, Cl, Bs = C['trim'], C['glow'], C['cloth'], C['base']
    if -27 <= u <= -25 and abs(v) <= 1: return T[3] if v < 0 else T[1]                        # pommel
    if u == -28 and v == 0: return G[2]
    if -24 <= u <= -16 and abs(v) <= 1: return (Cl[3] if u % 2 else Cl[2]) if v <= 0 else Cl[0]   # red wrapped grip
    g = guard(u, v, -14, 7, 3, (T[2], T[1]), G[3])                                               # spiked guard
    if g: return g
    if u < -12: return None
    return blade(u, v, [T[3], Bs[3], Bs[3], G[2], Bs[2], Bs[1], Bs[0]], 21, 28, serrate=4)


def dragon_slayer(u, v):
    C, L = ramp('dragonforged'); T, G, Bs = C['trim'], C['glow'], C['base']
    if -28 <= u <= -26 and abs(v) <= 1: return T[3] if v < 0 else T[1]
    if -25 <= u <= -17 and abs(v) <= 1: return (T[2] if u % 3 == 0 else Bs[3]) if v <= 0 else Bs[2]
    g = guard(u, v, -15, 8, 4, (T[3], T[1]), G[3])                                               # gold wing guard
    if g: return g
    if u < -13: return None
    return blade(u, v, [G[2], Bs[3], Bs[2], Bs[1], Bs[1], Bs[0], G[1]], 22, 28)


def shadow_dagger(u, v):
    C, L = ramp('shadow_assassin'); T, G, Cl, Bs = C['trim'], C['glow'], C['cloth'], C['base']
    if u == -21 and abs(v) <= 1: return T[2]                                                   # ring pommel
    if u == -20 and abs(v) == 1: return T[1]
    if -19 <= u <= -11 and abs(v) <= 1: return (Cl[3] if u % 2 else Cl[2]) if v <= 0 else Cl[0]
    g = guard(u, v, -9, 5, 2, (G[2], T[1]), G[3])                                                # crescent guard
    if g: return g
    if u < -7: return None
    return blade(u, v, [G[3], Bs[3], G[1], Bs[1], Bs[0]], 6, 13)


def soul_reaper(u, v):
    C, L = ramp('necrotic'); T, G, Cl = C['trim'], C['glow'], C['cloth']
    d2 = ((u - 19) ** 2 + v ** 2) / 2                                                           # orb at u = 19
    if d2 <= 4.5: return G[3] if d2 <= 1 else G[2] if d2 <= 2.5 else G[1]
    if 4.5 < d2 <= 9 and (u - 19 > 1 or abs(v) >= 3): return T[2] if v < 0 else T[1]          # bone cage
    if 25 <= u <= 27 and v == 0: return T[3]                                                    # cage tip
    if 11 <= u <= 14 and abs(v) <= 2: return T[2] if (u + v) % 3 else L                        # skull collar
    if -28 <= u <= 10 and -1 <= v <= 0:                                                         # shaft
        if u % 7 == 0: return G[2]                                                              # violet bands
        return Cl[3] if v < 0 else Cl[1]
    if u == -29 and v == 0: return T[2]
    return None


def earthshaker(u, v):
    C, L = ramp('earthwarden'); T, G, M, Bs = C['trim'], C['glow'], C['cloth'], C['base']
    if 9 <= u <= 19 and abs(v) <= 7:                                                            # stone head
        if (u in (9, 19)) and abs(v) == 7: return None
        if u == 14 and abs(v) <= 5: return G[3] if v == 0 else G[2]                             # rune band
        if v <= -5 and u >= 12: return M[2] if (u + v) % 2 else M[1]                            # moss on top
        lu, lv = (u - 9) % 3, (v + 7) % 4
        if lu == 2 or lv == 3: return Bs[0]
        return Bs[3] if (lu == 0 and lv == 0) else Bs[2] if v < 0 else Bs[1]
    if 20 <= u <= 21 and abs(v) <= 2: return Bs[2] if v < 0 else Bs[1]                         # top cap
    if -28 <= u <= 8 and abs(v) <= 1:                                                           # bark handle
        if u % 6 == 0: return G[1] if u > -10 else T[3]
        return T[2] if v < 0 else T[1] if v == 0 else T[0]
    return None


WEAPONS = {'dread_bloodrune_sword': bloodfang, 'dread_necrotic_staff': soul_reaper, 'dread_dragonforged_sword': dragon_slayer,
           'dread_shadow_dagger': shadow_dagger, 'dread_earthwarden_hammer': earthshaker}
NAMES = {'dread_bloodrune_sword': 'Bloodfang Sword', 'dread_necrotic_staff': 'Soul Reaper Staff',
         'dread_dragonforged_sword': 'Dragon Slayer Sword', 'dread_shadow_dagger': 'Shadow Dagger',
         'dread_earthwarden_hammer': 'Earthshaker Hammer'}   # kept in sync with arcane-souls gear.yml
LINE = {'dread_bloodrune_sword': 'bloodrune', 'dread_necrotic_staff': 'necrotic', 'dread_dragonforged_sword': 'dragonforged',
        'dread_shadow_dagger': 'shadow_assassin', 'dread_earthwarden_hammer': 'earthwarden'}


def draw(fn, line):
    img = Image.new('RGBA', (N, N), (0, 0, 0, 0))
    for y in range(N):
        for x in range(N):
            c = fn(x - y, x + y - (N - 1))
            if c: img.putpixel((x, y), c)
    out = img.copy()
    for y in range(N):
        for x in range(N):
            if img.getpixel((x, y))[3]: continue
            if any(0 <= x + dx < N and 0 <= y + dy < N and img.getpixel((x + dx, y + dy))[3]
                   for dx, dy in ((1, 0), (-1, 0), (0, 1), (0, -1))):
                out.putpixel((x, y), line)
    return out


def main():
    here = os.path.dirname(os.path.abspath(__file__))
    ap = argparse.ArgumentParser()
    ap.add_argument('--out', default=os.path.join(here, '..', 'pack'))
    ap.add_argument('--preview')
    a = ap.parse_args()
    A = os.path.join(a.out, 'assets', 'runeblock')
    d = os.path.join(A, 'textures', 'item', 'dread_weapon'); os.makedirs(d, exist_ok=True)
    sprites = {}
    for key, fn in WEAPONS.items():
        img = draw(fn, hx(PAL[LINE[key]]['line']))
        sprites[key] = img
        name = key[len('dread_'):]
        img.save(os.path.join(d, f'{name}.png'))
        B.write_json(os.path.join(A, 'models', 'item', 'dread_weapon', f'{name}.json'),
                     {'parent': 'minecraft:item/handheld', 'textures': {'layer0': f'runeblock:item/dread_weapon/{name}'}})
        B.write_json(os.path.join(A, 'items', f'{key}.json'),
                     {'model': {'type': 'minecraft:model', 'model': f'runeblock:item/dread_weapon/{name}'}})
        print(key, 'ok')
    if a.preview:
        S = 8
        sheet = Image.new('RGBA', (len(sprites) * (N * S + 24) + 24, N * S + 56), (40, 40, 48, 255))
        dr = ImageDraw.Draw(sheet)
        for i, (k, img) in enumerate(sprites.items()):
            x = 24 + i * (N * S + 24)
            sheet.alpha_composite(img.resize((N * S, N * S), Image.NEAREST), (x, 40))
            dr.text((x, 14), NAMES[k], fill=(236, 232, 240, 255))
        sheet.save(a.preview); print('preview', a.preview)


if __name__ == '__main__':
    main()
