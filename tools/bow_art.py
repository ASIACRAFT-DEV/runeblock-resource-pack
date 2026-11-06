#!/usr/bin/env python3
"""32 px bow sprites (kuwusaki 2026-11-06: "can we design more bows"): ten crafted metal bows, each with its own
silhouette (not one shape recoloured), the Dread Shadow bow, a redrawn Pathfinder Longbow (Ranger class weapon) and
five named boss bows.

Same pixel style as weapon_art.py (shaded parts, light from the top-left, one-pixel outline in the darkest step of the
neighbouring material) and the same diagonal coordinates:
  s = x - y        along the bow, bottom-left tip (-) .. top-right tip (+)
  t = x + y - 31   across it, negative = up-left = the side the arrow flies to
Laid out like vanilla's bow.png: the limbs arc from the top-right corner to the bottom-left one, bulging up-left, the
string runs straight along the diagonal behind them. Models use parent minecraft:item/bow, so they're held like a bow.

Usage: python3 -I tools/bow_art.py [--out pack] [--preview sheet.png] [--only id,id]
"""
import argparse, math, os, sys
from PIL import Image, ImageDraw

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import weapon_art as W
from weapon_art import Art, S, T, at, rgb, gem_ramp, lerp

N = 32
NO_OUTLINE = {'string', 'gstring'}      # bow strings stay one clean pixel line, like vanilla's


def ramp5(*hexes): return [rgb(h) for h in hexes]


class Bow(Art):
    def __init__(self, metal='iron', extra=None, gem=None):
        super().__init__(metal)
        self.ramps['string'] = ramp5('#3a3a3a', '#8f8f8f', '#cfcfcf', '#ececec', '#ffffff')
        if gem: self.ramps['gem'] = gem_ramp(gem)
        self.ramps['gstring'] = self.ramps['gem']
        for k, v in (extra or {}).items(): self.ramps[k] = [rgb(h) for h in v] if isinstance(v[0], str) else v

    def image(self):
        im = Image.new('RGBA', (N, N), (0, 0, 0, 0))
        for (x, y), (m, tone) in self.px.items(): im.putpixel((x, y), self.ramps[m][tone] + (255,))
        for x in range(N):
            for y in range(N):
                if (x, y) in self.px: continue
                for nx, ny in ((x, y - 1), (x - 1, y), (x + 1, y), (x, y + 1)):
                    if (nx, ny) in self.px and self.px[(nx, ny)][0] not in NO_OUTLINE:
                        m = self.px[(nx, ny)][0]; im.putpixel((x, y), self.ramps[m][0] + (255,)); break
        return im

    # ---- bow parts -----------------------------------------------------------------------------------------------
    def string(self, L, t, mat='string', tone=3, gap=None):
        """The string: a straight diagonal pixel line at t (its parity picks the line), from tip to tip.
        `gap` = (s0, s1) left out (where the hand / arrow rest sits)."""
        t = int(round(t))
        for x in range(N):
            for y in range(N):
                s = S(x, y)
                if T(x, y) == t and -L <= s <= L and not (gap and gap[0] <= s <= gap[1]):
                    self.px.setdefault((x, y), (mat, tone))

    def limb(self, L, centre, half, mat, tones=(4, 3, 2, 1), s0=None, s1=None):
        """Both limbs as one band: centreline t = centre(s), half width half(s), from s0 to s1 (default -L..L)."""
        s0 = -L if s0 is None else s0; s1 = L if s1 is None else s1
        return self.band(s0, s1, lambda s: -half(s), lambda s: half(s), mat, list(tones), curve=centre)

    def arc(self, L, B, tip=0.0, power=1.0, recurve=0.0, rlen=6, kink=None):
        """Centreline: t = tip at both ends, tip - B at the grip. recurve > 0 bends the last `rlen` toward the target
        (up-left); kink = (s_at, depth) adds an angular bend (a reflex shape) instead of a smooth arc."""
        def c(s):
            u = min(1.0, abs(s) / L)
            v = tip - B * (1 - u ** 2) ** power
            if kink: v = tip - B * (1 - u) - kink[1] * max(0.0, 1 - abs(s) / kink[0])
            if recurve and abs(s) > L - rlen: v -= recurve * ((abs(s) - (L - rlen)) / rlen) ** 2
            return v
        return c

    def riser(self, c, hs, w, mat, wrap=None, period=2, tones=(3, 3, 2, 1, 1)):
        m = mat if wrap is None else (lambda x, y: wrap if (S(x, y) + 64) % period < period // 2 else mat)
        return self.band(-hs, hs, lambda s: -w, lambda s: w, m, list(tones), curve=c)

    def p(self, s, t):   # pixel centre of (s, t), rounded
        x, y = at(s, t); return int(round(x)), int(round(y))


def taper(wm, wt, L, at_grip=0.0):
    return lambda s: lerp(wm, wt, min(1.0, abs(s) / L)) + (at_grip if abs(s) < 4 else 0)


# ---- the ten metal bows (own shape each) -----------------------------------------------------------------------------
def wooden(b):        # Hunter's Bow: a plain D-shaped self bow, one piece of wood, leather grip
    L, c = 26, b.arc(26, 11, tip=0.5)
    b.string(L, 1)
    b.limb(L, c, taper(1.6, 0.8, L), 'wood')
    b.riser(c, 3, 1.6, 'leather', wrap='wood', period=2)


def stone(b):         # Flint Short Bow: short and thick, knapped flint caps on the tips and a stone grip band
    L, c = 20, b.arc(20, 10, tip=0.5, power=0.8)
    b.string(L, 1)
    b.limb(L, c, taper(2.2, 1.2, L), 'wood')
    for sg in (-1, 1):
        b.poly_st([(sg * 14, c(14) - 3.5), (sg * 24, c(21) - 1), (sg * 14, c(14) + 3.0)], 'metal')
    b.riser(c, 3.5, 2.3, 'metal', tones=(4, 3, 2, 1))
    b.riser(c, 1.5, 2.0, 'leather')


def copper(b):        # Copper Recurve: wooden limbs, copper bands, tips that flick toward the target
    L, c = 25, b.arc(25, 9, tip=1, recurve=4.5, rlen=7)
    b.string(L, 2)
    b.limb(L, c, taper(1.8, 1.0, L), 'wood')
    for s in (-19, -11, 11, 19): b.band(s - 1, s + 1, lambda q: -2.2, lambda q: 2.2, 'metal', 'bevel', curve=c)
    b.riser(c, 3.5, 2.2, 'metal', tones=(4, 3, 2, 1))
    b.gem(*at(0, c(0) - 0.5), 1.0)


def iron(b):          # Iron Longbow: the longest and slimmest, iron-shod nocks, iron riser plate
    L, c = 28, b.arc(28, 9.5, tip=0.5, power=1.2)
    b.string(L, 1)
    b.limb(L, c, taper(1.8, 1.0, L), 'metal', tones=(4, 3, 2, 1))
    b.limb(L, c, lambda s: 0.3, 'wood', tones=(2,), s0=-24, s1=24)
    for s in (-24, -16, 16, 24): b.band(s - 0.6, s + 0.6, -2.2, 2.2, 'gold', 'bevel', curve=c)
    b.riser(c, 5, 2.0, 'metal', tones=(4, 3, 2, 1))
    b.riser(c, 2, 1.8, 'leather', wrap='cloth', period=2)


def golden(b):        # Gilded Recurve: gold limbs ending in scroll curls, red gem in an ornate riser
    L, c = 23, b.arc(23, 10, tip=1, recurve=3.5, rlen=6)
    b.string(L + 2, 2)
    b.limb(L, c, taper(2.0, 1.2, L), 'metal')
    for sg in (-1, 1):                                             # scroll curls past the tips
        cx, cy = at(sg * 25, c(L) - 2.5)
        b.disc(cx, cy, 2.4, 'metal', ring=1.3)
        b.setpx(int(round(cx)), int(round(cy)), 'gem', 3)
    for s in (-14, 14): b.band(s - 1, s + 1, -2.6, 2.6, 'metal', 'bevel', curve=c)
    b.riser(c, 4.5, 2.8, 'metal', tones=(4, 3, 2, 1))
    b.gem(*at(0, c(0)), 1.8)


def diamond(b):       # Crystal Bow: limbs of separate diamond shards bound by gold collars
    L, c = 25, b.arc(25, 10.5, tip=0.5)
    b.string(L, 1)
    for a0, a1 in ((5, 12), (13, 19), (20, 26)):
        for sg in (-1, 1):
            lo, hi = sorted((sg * a0, sg * a1))
            mid = (a0 + a1) / 2
            b.band(lo, hi, lambda s, m=mid, h=(a1 - a0) / 2: -3.2 * max(0.35, 1 - abs(abs(s) - m) / (h + 1)),
                   lambda s, m=mid, h=(a1 - a0) / 2: 2.6 * max(0.35, 1 - abs(abs(s) - m) / (h + 1)),
                   'metal', [4, 4, 3, 3, 2, 1], curve=c)
    for s in (-12.5, -19.5, 12.5, 19.5): b.band(s - 0.5, s + 0.5, -1.4, 1.4, 'gold', 'bevel', curve=c)
    b.riser(c, 4.5, 2.2, 'gold', tones=(4, 3, 2, 1))
    b.gem(*at(0, c(0)), 1.6)


def netherite(b):     # Ember Warbow: heavy and angular (a reflex bow), glowing seam along the belly
    L, c = 25, b.arc(25, 7, tip=0, kink=(12, 4))
    b.string(L, 1)
    b.limb(L, c, taper(2.6, 1.4, L), 'metal', tones=(3, 3, 2, 1, 1))
    seam = b.cells(lambda x, y: (x, y) in b.px and b.px[(x, y)][0] == 'metal' and 6 < abs(S(x, y)) < 23
                   and abs((T(x, y) - c(S(x, y))) - 1.6) <= 0.6)
    for q in seam: b.px[q] = ('gem', 3)
    for sg in (-1, 1): b.poly_st([(sg * 22, c(22) - 2), (sg * 28, c(25) - 4.5), (sg * 24, c(24) + 1)], 'metal')
    b.riser(c, 4.5, 3.0, 'metal', tones=(3, 2, 2, 1))
    b.riser(c, 2, 2.4, 'leather', wrap='gem', period=4)


def mithril(b):       # Elven Wingbow: thin double-curved limbs sweeping into feathered blade tips
    L, c = 24, b.arc(24, 11, tip=1, recurve=5, rlen=9, power=1.3)
    b.string(L, 2)
    b.limb(L, c, taper(1.4, 0.9, L), 'metal')
    for sg in (-1, 1):                                             # feather blades along the outer limb
        for k, s in enumerate((7, 12, 17)):
            b.poly_st([(sg * s, c(s) - 0.8), (sg * (s + 3), c(s) - 4.8 + k * 0.5), (sg * (s + 6.5), c(s + 5) - 1.6), (sg * (s + 5), c(s + 5) - 0.6)], 'metal')
    b.riser(c, 3.5, 1.8, 'iron', tones=(4, 3, 2, 1))
    b.gem(*at(0, c(0) - 0.5), 1.2)
    edge = [q for q in b.px if b.px[q][0] == 'metal' and T(*q) - c(S(*q)) <= -3.5]
    for q in edge: b.px[q] = ('gem', 3)


def bloodiron(b):     # Thorn Bow: barbed limbs (spikes on the outer edge), red glow edge, blood gem
    L, c = 25, b.arc(25, 10, tip=0.5, power=0.9)
    b.string(L, 1, mat='gstring', tone=2)
    b.limb(L, c, taper(2.0, 1.0, L), 'metal')
    for sg in (-1, 1):
        for s in (7, 12, 17, 22):
            b.poly_st([(sg * (s - 1.2), c(s) - 1.4), (sg * (s + 1.5), c(s) - 5.2), (sg * (s + 1.2), c(s) - 1.2)], 'metal')
    W.glow_edge(b, -24, 24, 2.0, 0.1, curve=c, side=1)
    for sg in (-1, 1): b.poly_st([(sg * 24, c(24) - 1.5), (sg * 29, c(26)), (sg * 24, c(24) + 1.5)], 'metal')
    b.riser(c, 3.5, 2.4, 'ebony', tones=(3, 2, 1, 1))
    b.gem(*at(0, c(0)), 1.7)


def voidsteel(b):     # Void Crescent: two crescents that float apart from the riser, a void orb, a glowing string
    L, c = 25, b.arc(25, 11.5, tip=1)
    b.string(L, 2, mat='gstring', tone=3)
    for sg in (-1, 1):
        lo, hi = sorted((sg * 7, sg * 26))
        b.band(lo, hi, lambda s: -2.8 * max(0.2, math.sin(math.pi * (abs(s) - 7) / 19)) - 0.4,
               lambda s: 1.6 * max(0.2, math.sin(math.pi * (abs(s) - 7) / 19)) + 0.4, 'metal', [4, 3, 2, 2, 1], curve=c)
    W.glow_edge(b, -25, -8, 1.8, 0.1, curve=c, side=1); W.glow_edge(b, 8, 25, 1.8, 0.1, curve=c, side=1)
    cx, cy = at(0, c(0) + 0.5)
    b.disc(cx, cy, 3.3, 'gold', ring=2.4)
    b.gem(cx, cy, 2.0)
    for s in (-5, 5): b.setpx(*b.p(s, c(s) - 1), 'gem', 4)


METAL_BOWS = {'wooden': wooden, 'stone': stone, 'copper': copper, 'iron': iron, 'golden': golden, 'diamond': diamond,
              'netherite': netherite, 'mithril': mithril, 'bloodiron': bloodiron, 'voidsteel': voidsteel}
METAL_NAMES = {'wooden': "Hunter's Bow", 'stone': 'Flint Short Bow', 'copper': 'Copper Recurve', 'iron': 'Iron Longbow',
               'golden': 'Gilded Recurve', 'diamond': 'Crystal Bow', 'netherite': 'Ember Warbow',
               'mithril': 'Elven Wingbow', 'bloodiron': 'Thorn Bow', 'voidsteel': 'Void Crescent'}


# ---- Dread, Pathfinder and the named boss bows -------------------------------------------------------------------------
def dread_shadow(b):  # Nightfall Bow (Dread Shadow set): blade-edged limbs, wrapped grip, the set's violet glow
    L, c = 25, b.arc(25, 10, tip=0.5, recurve=3, rlen=5)
    b.string(L, 1)
    b.limb(L, c, taper(2.0, 1.0, L), 'base')
    for sg in (-1, 1):
        b.poly_st([(sg * 6, c(6) - 1.2), (sg * 13, c(13) - 9), (sg * 15, c(15) - 6.5), (sg * 21, c(21) - 1.4)], 'trim')   # swept blade fins
        b.poly_st([(sg * 23, c(23) - 1.5), (sg * 29, c(26) - 2.5), (sg * 24, c(24) + 1.2)], 'trim')
    b.limb(L, c, taper(2.0, 1.0, L), 'base')
    W.glow_edge(b, -24, 24, 2.0, 0.1, curve=c, side=1)
    for q in [q for q in b.px if b.px[q][0] == 'metal']: b.px[q] = ('base', b.px[q][1])
    b.riser(c, 4, 2.4, 'cloth', wrap='base', period=3)
    b.gem(*at(0, c(0) - 0.5), 1.3)


def pathfinder(b):    # Pathfinder Longbow (Ranger): living olive wood, leaves sprouting along the limbs, emerald
    L, c = 27, b.arc(27, 10.5, tip=0.5, power=1.1)
    b.string(L, 1)
    b.limb(L, c, taper(1.7, 0.8, L), 'olive')
    for sg, s, side in ((1, 10, -1), (1, 19, -1), (-1, 14, -1), (-1, 22, -1), (1, 15, 1), (-1, 8, 1)):
        base = c(s) + side * 1.2
        b.poly_st([(sg * s, base), (sg * (s + 2), base + side * 3.2), (sg * (s + 4.5), base + side * 0.4)], 'leaf')
    for sg in (-1, 1): b.disc(*at(sg * 27.5, c(27)), 1.1, 'leaf')
    b.riser(c, 4, 2.0, 'leather', wrap='leaf', period=3)
    b.gem(*at(0, c(0) - 0.5), 1.3)


def hollowfang(b):    # Hollowfang (Hollow Stalker): bone limbs with ridges, fang tips, a sickly green eye
    L, c = 25, b.arc(25, 10.5, tip=0.5, power=0.9)
    b.string(L, 1, mat='gstring', tone=1)
    b.limb(L, c, taper(2.0, 1.1, L), 'bone')
    for s in (-20, -15, -10, 10, 15, 20): b.band(s - 0.5, s + 0.5, -2.2, 2.2, 'bone', [1], curve=c)
    for sg in (-1, 1): b.poly_st([(sg * 23, c(23) - 1.4), (sg * 28.5, c(25) + 2.5), (sg * 23, c(23) + 1.6)], 'bone')
    b.riser(c, 4, 2.6, 'rot', tones=(3, 2, 1, 1))
    cx, cy = at(0, c(0) - 0.5)
    b.disc(cx, cy, 2.0, 'bone', ring=1.2); b.gem(cx, cy, 1.0)


def cinderspan(b):    # Cinderspan (Ashen Colossus): charred stone slabs, lava cracks, an ember at the grip
    L, c = 24, b.arc(24, 9, tip=0, kink=(10, 3))
    b.string(L, 1, mat='gstring', tone=2)
    b.limb(L, c, taper(3.0, 1.6, L), 'char', tones=(3, 2, 2, 1, 1))
    crack = b.cells(lambda x, y: (x, y) in b.px and b.px[(x, y)][0] == 'char' and 4 < abs(S(x, y)) < 22
                    and abs((T(x, y) - c(S(x, y))) - 0.7 * math.sin(S(x, y) * 0.9)) <= 0.5)
    for q in crack: b.px[q] = ('gem', 3)
    for sg in (-1, 1): b.poly_st([(sg * 21, c(21) - 3), (sg * 27, c(24) - 2), (sg * 22, c(22) + 2.5)], 'char')
    cx, cy = at(0, c(0))
    b.disc(cx, cy, 3.0, 'char'); b.gem(cx, cy, 1.8)


def wyrmfrost(b):     # Wyrmfrost (Frost Wyrm): wing-bone limbs with an ice membrane, frost spikes at the tips
    L, c = 26, b.arc(26, 12, tip=0.5, recurve=3, rlen=6)
    b.string(L, 1)
    for sg in (-1, 1):                                            # membrane between limb and string, ice blue
        lo, hi = sorted((sg * 5, sg * 22))
        b.band(lo, hi, lambda s: 0.8, lambda s: max(0.8, (-c(s) - 0.5) * 0.5), 'ice', [3, 3, 2], curve=c)
    b.limb(L, c, taper(1.6, 0.9, L), 'bone')
    for s in (-17, -10, 10, 17): b.setpx(*b.p(s, c(s) - 1), 'bone', 4)
    for sg in (-1, 1):
        b.poly_st([(sg * 24, c(24) - 1), (sg * 29, c(25) - 4.5), (sg * 26, c(26) + 1)], 'ice')
        b.poly_st([(sg * 18, c(18) - 1.2), (sg * 21, c(18) - 5), (sg * 20.5, c(20) - 1)], 'ice')
    b.riser(c, 3.5, 2.0, 'iron', wrap='ice', period=3)
    b.gem(*at(0, c(0) - 0.5), 1.2)


def oathbreaker(b):   # Oathless Warbow (Silent Commander): a black-steel military recurve, gold trim, a torn crimson banner
    L, c = 25, b.arc(25, 10, tip=1, recurve=3.5, rlen=6)
    b.string(L, 2)
    b.limb(L, c, taper(2.0, 1.1, L), 'steel')
    for s in (-22, -14, 14, 22): b.band(s - 0.7, s + 0.7, -2.4, 2.4, 'gold', 'bevel', curve=c)
    b.riser(c, 4.5, 2.6, 'steel', tones=(3, 2, 2, 1))
    b.gem(*at(0, c(0)), 1.4)
    # the banner hangs from the lower limb toward the bottom-right corner, torn at the end
    b.poly([(9, 21), (14, 22), (17, 27), (15, 26), (14, 29), (12, 26), (10, 28), (9, 24)], 'banner')
    b.rect(9, 21, 10, 21, 'gold')


def azkharoth(b):     # Azkharoth's Span (Guardian Raid): bat-wing limbs with spread finger-bones, a demon eye
    L, c = 25, b.arc(25, 11, tip=0.5, power=0.85)
    b.string(L, 1, mat='gstring', tone=2)
    for sg in (-1, 1):                                            # membrane scallops on the outer side
        for s0, s1 in ((5, 11), (11, 17), (17, 23)):
            lo, hi = sorted((sg * s0, sg * s1))
            m = (s0 + s1) / 2
            b.band(lo, hi, lambda s, m=m: -1.0 - 5.2 * max(0, 1 - ((abs(s) - m) / 3.4) ** 2), lambda s: -0.6, 'wing',
                   [3, 2, 2, 1], curve=c)
    b.limb(L, c, taper(1.6, 0.8, L), 'horn')
    for sg in (-1, 1):
        for s in (5, 11, 17, 23): b.band(min(sg * s, sg * (s + 0.4)), max(sg * s, sg * (s + 0.4)), lambda q: -6.4, lambda q: -0.5, 'horn', [3, 2], curve=c)
        b.poly_st([(sg * 23, c(23) - 1), (sg * 28.5, c(25) - 3), (sg * 24, c(24) + 1)], 'horn')
    cx, cy = at(0, c(0))
    b.disc(cx, cy, 2.6, 'horn'); b.gem(cx, cy, 1.5)


SPECIAL = {   # id -> (draw, display name, ramps, gem accent)
    'dread_shadow_bow': (dread_shadow, 'Nightfall Bow', 'dread:shadow_assassin', None),
    'class_ranger_weapon': (pathfinder, 'Pathfinder Longbow',
                            {'olive': ['#1c1a0a', '#3f3b17', '#6a6428', '#8f8a3e', '#b4ad5e'],
                             'leaf': ['#0d2410', '#1f5126', '#2f7d38', '#4fae50', '#8fdc7a']}, '#2fd27a'),
    'boss_hollowfang': (hollowfang, 'Hollowfang',
                        {'bone': ['#2a261c', '#6b6450', '#a9a084', '#d6cfb2', '#f4efdc'],
                         'rot': ['#0f140c', '#273220', '#3d4b31', '#566844', '#73875b']}, '#7dff6a'),
    'boss_cinderspan': (cinderspan, 'Cinderspan',
                        {'char': ['#0b0908', '#1f1a17', '#352d28', '#4c413a', '#655850']}, '#ff7a1a'),
    'boss_wyrmfrost': (wyrmfrost, 'Wyrmfrost',
                       {'bone': ['#1f2a33', '#5d7384', '#9db6c6', '#d3e6f0', '#ffffff'],
                        'ice': ['#123048', '#2c6c96', '#5aaedc', '#9fdcf6', '#e8fbff']}, '#7fe6ff'),
    'boss_oathless': (oathbreaker, 'Oathless Warbow',
                      {'steel': ['#08090c', '#1b1d24', '#30333d', '#4a4e5b', '#6c7180'],
                       'banner': ['#2a0608', '#5e0f14', '#97212a', '#c13a40', '#e2686a']}, '#d4a63a'),
    'boss_azkharoth': (azkharoth, "Azkharoth's Span",
                       {'horn': ['#120a0c', '#33191c', '#58302c', '#7e4a3c', '#a86d55'],
                        'wing': ['#14060f', '#3a0f2a', '#621a45', '#8c2c60', '#b5507f']}, '#ff3b5c'),
}


def make(bow_id):
    if bow_id.endswith('_bow') and bow_id[:-4] in METAL_BOWS:
        metal = bow_id[:-4]; b = Bow(metal); METAL_BOWS[metal](b); return b.image(), METAL_NAMES[metal]
    draw, name, ramps, gem = SPECIAL[bow_id]
    if ramps == 'dread:shadow_assassin':
        from dread_pixel import PAL, hx
        P = PAL['shadow_assassin']
        r = {k: [rgb(P['line'])] + [rgb(c) for c in v] for k, v in P.items() if isinstance(v, list)}
        b = Bow('netherite', extra=r); b.ramps['gem'] = b.ramps['glow']
    else:
        b = Bow('iron', extra=ramps, gem=gem)
    draw(b); return b.image(), name


ALL = [f'{m}_bow' for m in METAL_BOWS] + list(SPECIAL)


def sheet(ids, path, scale=6):
    cols = 6; rows = math.ceil(len(ids) / cols)
    cw, ch = N * scale + 24, N * scale + 44
    im = Image.new('RGBA', (cols * cw, rows * ch), (29, 31, 36, 255)); d = ImageDraw.Draw(im)
    for i, bid in enumerate(ids):
        spr, name = make(bid)
        x0, y0 = (i % cols) * cw + 12, (i // cols) * ch + 8
        d.rectangle([x0 - 2, y0 - 2, x0 + N * scale + 1, y0 + N * scale + 1], fill=(40, 43, 50, 255))
        im.alpha_composite(spr.resize((N * scale, N * scale), Image.NEAREST), (x0, y0))
        slot = spr.resize((N, N), Image.NEAREST)           # inventory size (16 px item at GUI 2)
        d.rectangle([x0 + N * scale - 36, y0 + 2, x0 + N * scale - 2, y0 + 36], fill=(139, 139, 139, 255))
        im.alpha_composite(slot, (x0 + N * scale - 35, y0 + 3))
        d.text((x0, y0 + N * scale + 6), name, fill=(235, 235, 235, 255))
        d.text((x0, y0 + N * scale + 20), bid, fill=(140, 146, 160, 255))
    im.save(path)


def write_pack(out, ids):
    for bid in ids:
        spr, _ = make(bid)
        tdir = os.path.join(out, 'assets/runeblock/textures/item/bow'); os.makedirs(tdir, exist_ok=True)
        spr.save(os.path.join(tdir, f'{bid}.png'))
        mdir = os.path.join(out, 'assets/runeblock/models/item/bow'); os.makedirs(mdir, exist_ok=True)
        with open(os.path.join(mdir, f'{bid}.json'), 'w') as f:
            f.write('{\n  "parent": "minecraft:item/bow",\n  "textures": { "layer0": "runeblock:item/bow/%s" }\n}\n' % bid)
        idir = os.path.join(out, 'assets/runeblock/items'); os.makedirs(idir, exist_ok=True)
        with open(os.path.join(idir, f'{bid}.json'), 'w') as f:
            f.write('{\n  "model": { "type": "minecraft:model", "model": "runeblock:item/bow/%s" }\n}\n' % bid)


if __name__ == '__main__':
    ap = argparse.ArgumentParser()
    ap.add_argument('--out'); ap.add_argument('--preview'); ap.add_argument('--only')
    a = ap.parse_args()
    ids = a.only.split(',') if a.only else ALL
    if a.preview: sheet(ids, a.preview); print('preview', a.preview)
    if a.out: write_pack(a.out, ids); print('wrote', len(ids), 'bows to', a.out)
