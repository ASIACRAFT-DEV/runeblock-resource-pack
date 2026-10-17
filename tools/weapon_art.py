"""32 px weapon sprites built from shaded parts (blade, guard, grip, gem, ...), three looks per category by gear tier.

Imported by gen_metal_weapons.py. `sprite(category, metal) -> PIL.Image` (32x32 RGBA).

Coordinates: pixel (x, y), y down. Long weapons lie on the diagonal from bottom-left (pommel) to top-right (tip):
  s = x - y        along the weapon, -31 (bottom-left corner) .. 31 (top-right corner); one diagonal pixel = 2
  t = x + y - 31   across it, negative = the upper-left (lit) side; one diagonal pixel = 2
A pixel exists for every s, t of opposite parity; keep |s| + |t| <= 29 so the outline still fits.
Light comes from the top-left: every part gets a light edge up-left and a dark edge down-right, then the whole
sprite gets a one-pixel outline in the darkest step of the material next to it.
"""
import math
from PIL import Image

N = 32
def rgb(h): return tuple(int(h[i:i + 2], 16) for i in (1, 3, 5))

# 5-step ramps: outline, dark, mid, light, highlight
METALS = {  # in progression order
    'wooden':    ['#24170a', '#4e3517', '#76552a', '#9c7640', '#c29a5e'],
    'stone':     ['#202020', '#3f3f3f', '#666666', '#8f8f8f', '#bdbdbd'],
    'copper':    ['#3a170c', '#7a3820', '#b9603c', '#e38d63', '#ffc6a2'],
    'iron':      ['#1c1d21', '#4a4c52', '#8b8e95', '#c9ccd2', '#ffffff'],
    'golden':    ['#4a3205', '#9c6e0e', '#e0ad26', '#fbdc56', '#fff8c4'],
    'diamond':   ['#0b3530', '#16766a', '#2fc4b2', '#86f0e2', '#ffffff'],
    'netherite': ['#0d0c0e', '#272428', '#433d44', '#655c64', '#948893'],
    'mithril':   ['#14303c', '#3a7a8a', '#78c8d2', '#c4f2f0', '#ffffff'],
    'bloodiron': ['#220708', '#5e1214', '#a3241f', '#de5246', '#ffc2b0'],
    'voidsteel': ['#0e0820', '#2a1850', '#52309a', '#8f64ea', '#e4d2ff'],
}
TIER = {'wooden': 0, 'stone': 0, 'copper': 0, 'iron': 0, 'golden': 1, 'diamond': 1, 'netherite': 1,
        'mithril': 2, 'bloodiron': 2, 'voidsteel': 2}
GEM = {  # accent: gems, glowing edges, wrap stripes
    'wooden': '#5f9e3a', 'stone': '#c8822a', 'copper': '#3fb89a', 'iron': '#c2342e', 'golden': '#d42a4a',
    'diamond': '#3a7fe0', 'netherite': '#ff8a1e', 'mithril': '#5ac8ff', 'bloodiron': '#ff3b30', 'voidsteel': '#d05aff'}
TRIM = {'golden': 'iron', 'mithril': 'iron'}   # everyone else trims in gold
FIXED = {
    'wood':    ['#22150a', '#3f2814', '#5e3d1f', '#7d552d', '#9a6e40'],
    'ebony':   ['#0c080c', '#1e161e', '#342834', '#4c3c4a', '#665462'],
    'leather': ['#1e0f08', '#3f2112', '#60351c', '#7f4b2a', '#9e663e'],
    'cloth':   ['#14101a', '#2a2234', '#3e344c', '#564a66', '#706282'],
    'gold':    ['#3a2604', '#8a5e0c', '#d29e1e', '#f6d24a', '#fff4b0'],
    'iron':    METALS['iron'],
    'paper':   ['#3e3420', '#8e7c54', '#c4b282', '#e6d9ae', '#fbf3d6'],
    'string':  ['#3a3a3a', '#9a9a9a', '#cfcfcf', '#ececec', '#ffffff'],
}
def gem_ramp(h):   # a 5-step ramp around one accent colour
    r, g, b = rgb(h)
    def mix(c, k, to): return tuple(round(v + (to - v) * k) for v in c)
    dk = lambda k: mix((r, g, b), k, 0); lt = lambda k: mix((r, g, b), k, 255)
    return [dk(0.75), dk(0.45), (r, g, b), lt(0.35), lt(0.75)]

def S(x, y): return x - y
def T(x, y): return x + y - 31
def at(s, t): return ((s + t + 31) / 2, (t - s + 31) / 2)   # pixel centre of a diagonal coordinate (may be .5)
def lerp(a, b, k): return a + (b - a) * k
BLADE = [4, 3, 3, 2, 2, 1]     # lit edge .. shadow edge
ROD = [3, 2, 1]
ROUND = [4, 3, 2, 2, 1]

class Art:
    def __init__(self, metal):
        self.metal, self.tier = metal, TIER[metal]
        self.ramps = dict(FIXED); self.ramps['metal'] = [rgb(h) for h in METALS[metal]]
        self.ramps['gold'] = [rgb(h) for h in FIXED['gold']] if TRIM.get(metal) is None else [rgb(h) for h in FIXED[TRIM[metal]]]
        self.ramps['gem'] = gem_ramp(GEM[metal])
        for k in ('wood', 'ebony', 'leather', 'cloth', 'paper', 'string', 'iron'):
            if isinstance(self.ramps[k][0], str): self.ramps[k] = [rgb(h) for h in self.ramps[k]]
        self.trim = 'gold'
        self.handle = 'wood' if self.tier == 0 else ('leather' if self.tier == 1 else 'ebony')
        self.px = {}   # (x, y) -> (material, tone)

    # ---- filling -----------------------------------------------------------------------------------------------
    def _put(self, cells, mat, shade):
        """cells: set of (x, y). mat: name or f(x, y) -> name. shade: 'bevel', a tone list sampled by `key`, or an int."""
        for (x, y) in cells:
            m = mat(x, y) if callable(mat) else mat
            if m is None: continue
            if isinstance(shade, int): tone = shade
            elif callable(shade): tone = shade(x, y)
            else:
                up, lf, dn, rt = (x, y - 1) in cells, (x - 1, y) in cells, (x, y + 1) in cells, (x + 1, y) in cells
                lit, dark = (not up) + (not lf), (not dn) + (not rt)
                tone = 4 if lit == 2 and not dark else 3 if lit and lit >= dark else 1 if dark else 2
            self.px[(x, y)] = (m, tone)
        return cells

    def cells(self, pred):
        return {(x, y) for x in range(N) for y in range(N) if pred(x, y)}

    def band(self, s0, s1, lo, hi, mat, tones=BLADE, curve=None):
        """A run along the diagonal: s0 <= s <= s1, lo(s) <= t - curve(s) <= hi(s). Tones sampled across t."""
        f = lambda v: v if callable(v) else (lambda s: v)
        lo, hi, cv = f(lo), f(hi), f(curve or 0)
        def inside(x, y):
            s, t = S(x, y), T(x, y) - cv(S(x, y))
            return s0 <= s <= s1 and lo(s) - 1e-9 <= t <= hi(s) + 1e-9
        c = self.cells(inside)
        if tones == 'bevel': return self._put(c, mat, 'bevel')
        def tone(x, y):
            s = S(x, y); t = T(x, y) - cv(s); a, b = lo(s), hi(s)
            u = 0.5 if b - a < 1e-6 else (t - a) / (b - a)
            return tones[min(len(tones) - 1, max(0, int(u * len(tones) - 1e-9)))]
        return self._put(c, mat, tone)

    def blade(self, s0, s1, w, tip, mat='metal', tones=BLADE, curve=None, w0=None, off=0):
        """Straight or curved blade of half width w (t), tapering to a point over the last `tip` units of s."""
        def half(s):
            k = 1 if s <= s1 - tip else max(0.0, (s1 - s) / tip)
            base = w if w0 is None else lerp(w0, w, min(1, (s - s0) / max(1, (s1 - tip - s0))))
            return base * (k ** 0.8)
        return self.band(s0, s1, lambda s: -half(s) + off, lambda s: half(s) + off, mat, tones, curve)

    def poly_st(self, pts, mat, shade='bevel'):     # polygon in (s, t) space
        xy = [at(s, t) for s, t in pts]; return self.poly(xy, mat, shade)

    def poly(self, pts, mat, shade='bevel'):        # polygon in pixel space (pixel centres = x + .5? no: x, y)
        def inside(x, y):
            px, py, c = x, y, False
            for (ax, ay), (bx, by) in zip(pts, pts[1:] + pts[:1]):
                if (ay > py) != (by > py) and px < ax + (py - ay) * (bx - ax) / (by - ay): c = not c
            return c
        return self._put(self.cells(inside), mat, shade)

    def disc(self, cx, cy, r, mat, shade='bevel', ring=None):
        def inside(x, y):
            d = math.hypot(x - cx, y - cy)
            return d <= r + 0.25 and (ring is None or d >= ring - 0.25)
        return self._put(self.cells(inside), mat, shade)

    def gem(self, cx, cy, r, mat='gem'):   # a cut stone: dark rim, bright upper-left, one sparkle pixel
        c = self.disc(cx, cy, r, mat)
        if c:
            top = min(c, key=lambda p: (p[0] + p[1], p[1]))
            for p in c:
                if (p[0] - cx) + (p[1] - cy) > r * 0.6: self.px[p] = (mat, 1)
            sp = (int(round(cx - r * 0.35)), int(round(cy - r * 0.35)))
            if sp in c: self.px[sp] = (mat, 4)
        return c

    def rect(self, x0, y0, x1, y1, mat, shade='bevel'):
        return self._put(self.cells(lambda x, y: x0 <= x <= x1 and y0 <= y <= y1), mat, shade)

    def setpx(self, x, y, mat, tone):
        if 0 <= x < N and 0 <= y < N: self.px[(x, y)] = (mat, tone)

    def grip(self, s0, s1, w=1, mat=None, wrap=None, period=4):
        """Handle on the diagonal. `wrap` = a second material in bands across the handle."""
        mat = mat or self.handle
        m = mat if wrap is None else (lambda x, y: wrap if (S(x, y) - s0) % period < period // 2 else mat)
        return self.band(s0, s1, -w, w, m, ROD if w <= 1 else [3, 3, 2, 1, 1])

    def guard(self, s, hs, t0, t1, mat='gold', tips=False):   # a bar across the weapon
        c = self.band(s - hs, s + hs, t0, t1, mat, 'bevel')
        if tips:   # flared ends: one pixel further toward the blade
            for t in (t0, t1):
                x, y = at(s + hs + 1, t + (1 if t < 0 else -1))
                self.setpx(int(x), int(y), mat, 3)
        return c

    # ---- output ------------------------------------------------------------------------------------------------
    def image(self):
        im = Image.new('RGBA', (N, N), (0, 0, 0, 0))
        for (x, y), (m, tone) in self.px.items(): im.putpixel((x, y), self.ramps[m][tone] + (255,))
        for x in range(N):        # outline: the darkest step of the neighbouring material
            for y in range(N):
                if (x, y) in self.px: continue
                for nx, ny in ((x, y - 1), (x - 1, y), (x + 1, y), (x, y + 1)):
                    if (nx, ny) in self.px:
                        m = self.px[(nx, ny)][0]; im.putpixel((x, y), self.ramps[m][0] + (255,)); break
        return im

# ---- the categories ------------------------------------------------------------------------------------------------
# Each takes an Art and draws into it. a.tier: 0 novice (plain), 1 artisan (trim, wrapped grips), 2 mythic (gems,
# flares, glowing edge in the metal's accent colour).

def glow_edge(a, s0, s1, w, tip, curve=None, side=1):
    """Mythic: the shadow-side cutting edge in the accent colour."""
    def half(s): return w * (1 if s <= s1 - tip else max(0.0, (s1 - s) / tip)) ** 0.8
    f = curve if callable(curve) else (lambda s: 0)
    c = a.cells(lambda x, y: s0 <= S(x, y) <= s1 and abs((T(x, y) - f(S(x, y))) - side * half(S(x, y))) <= 0.6
                and half(S(x, y)) > 0.4)
    for p in c: a.px[p] = ('gem', 3)

def sword(a):        # (new metals only) a classic arming sword
    t = a.tier
    a.grip(-25, -12, 1, wrap='gold' if t == 2 else None if t == 0 else 'cloth')
    a.blade(-9, 28, 3, 8)
    a.band(-9, 18, 0, 0, 'metal', [1]) if t else None          # fuller
    if t == 2: glow_edge(a, -6, 26, 3, 8)
    a.guard(-10, 1, -7, 7, 'gold' if t else 'metal', tips=t > 0)
    if t == 2: a.gem(*at(-10, 0), 1.6)
    a.disc(*at(-26, 0), 1.6 if t else 1.2, 'gold' if t else 'metal')

def axe(a):          # (new metals only)
    t = a.tier
    a.grip(-27, 22, 1, mat=a.handle, wrap='cloth' if t else None, period=6) if False else a.band(-27, 22, -1, 1, a.handle, ROD)
    if t: a.band(-26, -16, -1, 1, lambda x, y: 'leather' if S(x, y) % 4 < 2 else 'cloth', ROD)
    head = [(10, -2), (6, -6), (4, -13), (10, -18), (18, -17), (24, -13), (22, -7), (18, -2)]
    a.poly_st(head, 'metal')
    a.band(8, 20, -2, 2, 'metal', ROD)
    if t == 2:
        a.poly_st([(12, 2), (16, 6), (18, 2)], 'metal'); a.gem(*at(15, 0), 1.4)
        for s in range(5, 24): pass
    edge = a.cells(lambda x, y: (x, y) in a.px and a.px[(x, y)][0] == 'metal' and T(x, y) <= -15 + 0 * S(x, y))
    for p in edge: a.px[p] = ('gem' if t == 2 else 'metal', 4 if t < 2 else 3)
    a.band(23, 24, -1, 1, 'gold' if t else 'metal', 'bevel')

def katana(a):
    t = a.tier
    curve = lambda s: max(0, s + 4) ** 2 / 260.0      # bends toward the shadow side
    w = 2.6 if t < 2 else 3
    a.blade(-4, 28, w, 6, curve=curve)
    if t: a.band(-4, 22, -w, -w + 0.6, 'metal', [4], curve=curve)   # bright back edge
    if t == 2: glow_edge(a, -2, 26, w, 6, curve=curve)
    a.band(-6, -4, -2, 2, 'gold' if t else 'metal', 'bevel')       # habaki
    # tsuba: round guard
    cx, cy = at(-8, 0)
    a.disc(cx, cy, 2.8 if t == 0 else 3.2, 'ebony' if t == 0 else 'gold')
    if t == 2: a.gem(cx, cy, 1.3)
    else: a.setpx(int(cx), int(cy), 'cloth', 1)
    a.grip(-26, -10, 1, mat='cloth' if t else 'wood', wrap='gem' if t == 2 else 'leather' if t == 0 else 'iron', period=4)
    a.disc(*at(-27, 0), 1.2, 'gold' if t else 'metal')
    if t == 2:   # tassel
        for i, (x, y) in enumerate([(3, 27), (2, 28), (2, 29), (1, 30)]): a.setpx(x, y, 'gem', 2 if i % 2 else 3)

def dagger(a):
    t = a.tier
    w = 3.4 if t < 2 else 3.8
    a.blade(-1, 20, w, 8)
    a.band(0, 13, -0.5, 0.5, 'metal', [1]) if t else None
    if t == 2:
        glow_edge(a, 1, 19, w, 8)
        a.poly_st([(-1, -4), (8, -6), (12, -4), (-1, -2)], 'metal', 'bevel')   # serrated back spur
    if t == 0: a.guard(-2, 1, -5, 5, 'metal')
    else:
        a.guard(-2, 1, -7, 7, 'gold', tips=True)
        for s, tt in ((-1, -8), (-1, 8)): pass
    if t == 2: a.gem(*at(-2, 0), 1.7)
    a.grip(-16, -4, 1.4 if t else 1, wrap='gold' if t == 2 else 'cloth' if t == 1 else None, period=4)
    if t == 0: a.disc(*at(-17, 0), 1.3, 'metal')
    else:
        a.poly_st([(-17, 0), (-20, -3), (-24, 0), (-20, 3)], 'gold')
        if t == 2: a.gem(*at(-20, 0), 1.0)

def rapier(a):
    t = a.tier
    a.blade(-6, 29, 1.2, 10, tones=[4, 3, 2, 1])
    if t == 2: glow_edge(a, -4, 26, 1.2, 10)
    # swept hilt: a ring guard on the shadow side, a quillon across
    cx, cy = at(-10, 3.5)
    a.disc(cx, cy, 4.6 if t else 4.0, 'gold' if t else 'metal', ring=3.6 if t else 3.0)
    a.guard(-8, 1, -7 if t else -5, 6 if t else 4, 'gold' if t else 'metal', tips=t > 0)
    if t: a.disc(*at(-8, 0), 1.8, 'gold')
    if t == 2: a.gem(*at(-8, 0), 1.3)
    a.grip(-20, -10, 1, wrap='gold' if t else None, mat='leather' if t else 'wood', period=3)
    a.disc(*at(-22, 0), 2.0 if t else 1.4, 'gold' if t else 'metal')
    if t == 2: a.setpx(*map(int, at(-22, 0)), 'gem', 4)

def greatsword(a):
    t = a.tier
    w = 4 if t == 0 else 4.6
    a.blade(-6, 29, w, 9)
    a.band(-6, 18, -0.6, 0.6, 'metal', [1 if t else 2])         # fuller
    if t == 2:
        glow_edge(a, -3, 27, w, 9, side=1); glow_edge(a, -3, 27, w, 9, side=-1)
        for s in (2, 10): a.gem(*at(s, 0), 1.0)
    if t == 0: a.guard(-8, 1.5, -8, 8, 'metal')
    else:
        a.guard(-8, 1.5, -10, 10, 'gold', tips=True)
        a.poly_st([(-6, -3), (-2, 0), (-6, 3)], 'gold')
        if t == 2:
            a.poly_st([(-9, -10), (-5, -14), (-7, -9)], 'gold'); a.poly_st([(-9, 10), (-5, 14), (-7, 9)], 'gold')
            a.gem(*at(-8, 0), 1.6)
    a.grip(-25, -10, 1.4, mat='leather' if t else 'wood', wrap='cloth' if t else None, period=4)
    a.disc(*at(-26, 0), 2.0, 'gold' if t else 'metal')

def spear(a):
    t = a.tier
    a.band(-28, 12, -1, 1, a.handle, ROD)
    if t: a.band(-14, -6, -1.2, 1.2, lambda x, y: 'leather' if S(x, y) % 4 < 2 else a.trim, ROD)
    head = {0: [(10, 0), (16, -3.5), (28, 0), (16, 3.5)],
            1: [(9, 0), (15, -4.5), (29, 0), (15, 4.5)],
            2: [(8, 0), (14, -5), (29, 0), (14, 5)]}[t]
    a.poly_st(head, 'metal')
    a.band(12, 26, 0, 0, 'metal', [4])
    if t == 2:
        glow_edge(a, 12, 29, 5, 15, curve=lambda s: 0)
        a.poly_st([(8, -2), (6, -8), (11, -3)], 'metal'); a.poly_st([(8, 2), (6, 8), (11, 3)], 'metal')   # wings
    a.band(7, 10, -1.6, 1.6, 'gold' if t else 'metal', 'bevel')    # socket
    if t == 2: a.gem(*at(8.5, 0), 1.2)
    a.band(-29, -27, -1.4, 1.4, 'gold' if t else 'metal', 'bevel')  # butt cap

def halberd(a):
    t = a.tier
    a.band(-28, 18, -1, 1, a.handle, ROD)
    if t: a.band(-12, -5, -1.2, 1.2, lambda x, y: 'leather' if S(x, y) % 4 < 2 else a.trim, ROD)
    a.poly_st([(16, 0), (20, -2.4), (29, 0), (20, 2.4)], 'metal')                       # top spike
    axe = {0: [(6, -1), (4, -7), (8, -11), (14, -9), (16, -1)],
           1: [(5, -1), (2, -7), (6, -13), (13, -12), (17, -1)],
           2: [(5, -1), (1, -8), (4, -14), (12, -15), (15, -9), (18, -1)]}[t]
    a.poly_st(axe, 'metal')
    edge = [p for p in a.px if a.px[p][0] == 'metal' and T(*p) <= {0: -9, 1: -11, 2: -12}[t]]
    for p in edge: a.px[p] = ('gem', 3) if t == 2 else ('metal', 4)
    a.poly_st([(8, 1), (11, 6), (14, 1)] if t else [(9, 1), (11, 4), (13, 1)], 'metal')  # back hook
    a.band(4, 17, -1.4, 1.4, 'gold' if t else 'metal', 'bevel')
    if t == 2: a.gem(*at(11, 0), 1.3)
    a.band(-29, -27, -1.4, 1.4, 'gold' if t else 'metal', 'bevel')

def staff(a):
    t = a.tier
    a.band(-28, 16, -1, 1, a.handle, ROD)
    if t: a.band(-6, 2, -1.2, 1.2, lambda x, y: 'cloth' if S(x, y) % 4 < 2 else a.trim, ROD)
    cx, cy = at(21, 0)
    if t == 0:
        a.disc(cx, cy, 3.4, 'metal')
        a.gem(cx, cy, 1.6)
    else:
        r = 4.2 if t == 1 else 5.0
        a.disc(cx, cy, r + 1.4, 'gold', ring=r + 0.2)                 # cradle ring
        a.gem(cx, cy, r - 0.2)
        if t == 2:  # crescent prongs reaching past the orb
            a.poly_st([(16, -6), (26, -9), (22, -5)], 'gold'); a.poly_st([(16, 6), (26, 9), (22, 5)], 'gold')
            a.setpx(*map(int, at(29, 0)), 'gem', 4)
    a.band(14, 16, -1.6, 1.6, 'gold' if t else 'metal', 'bevel')
    a.band(-29, -27, -1.4, 1.4, 'metal', 'bevel')

def sceptre(a):
    t = a.tier
    a.band(-24, 8, -1, 1, 'metal' if t == 0 else 'gold', ROD)
    if t: a.band(-20, -8, -1.2, 1.2, lambda x, y: 'gem' if S(x, y) % 6 < 2 else 'gold', ROD)
    cx, cy = at(16, 0)
    if t == 0:
        a.poly_st([(8, 0), (14, -5), (22, 0), (14, 5)], 'metal')
        a.gem(cx, cy, 1.4)
    else:
        a.poly_st([(7, 0), (12, -7), (18, -6), (24, 0), (18, 6), (12, 7)], 'metal')   # flanged head
        a.gem(cx, cy, 2.4 if t == 1 else 2.8)
        if t == 2:
            a.poly_st([(20, -4), (28, -3), (24, 0)], 'gold'); a.poly_st([(20, 4), (28, 3), (24, 0)], 'gold')
            a.setpx(*map(int, at(27, 0)), 'gem', 4)
        a.band(6, 8, -2, 2, 'gold', 'bevel')
    a.disc(*at(-25, 0), 1.8, 'gold' if t else 'metal')

def crescent(a, c1, R, c2, r, keep=lambda x, y: True):
    """A curved blade: inside circle (c1, R), outside circle (c2, r). Thick in the middle, pointed at both ends.
    The inner (cutting) edge is bright; on mythic gear it glows in the accent colour."""
    def inside(x, y): return math.hypot(x - c1[0], y - c1[1]) <= R and math.hypot(x - c2[0], y - c2[1]) > r and keep(x, y)
    c = a.cells(inside); a._put(c, 'metal', 'bevel')
    for p in c:
        if math.hypot(p[0] - c2[0], p[1] - c2[1]) <= r + 1.3: a.px[p] = ('gem', 3) if a.tier == 2 else ('metal', 4)
    return c

def sickle(a):
    t = a.tier
    a.band(-28, -4, -1.2, 1.2, a.handle, ROD)
    if t: a.band(-26, -12, -1.3, 1.3, lambda x, y: 'leather' if S(x, y) % 4 < 2 else 'gold', ROD)
    R = 10.5 if t < 2 else 11.5
    crescent(a, (19.0, 12.0), R - 1.5, (21.5, 14.0), R - 1.9, keep=lambda x, y: not (x > 20 and y > 11) and y <= 18)
    if t == 2: a.poly([(26, 4), (30, 1), (28, 7)], 'gold')
    a.band(-6, -2, -1.8, 1.8, 'gold' if t else 'metal', 'bevel')
    if t == 2: a.gem(*at(-4, 0), 1.3)
    a.disc(*at(-28, 0), 1.6, 'gold' if t else 'metal')

def scythe(a):
    t = a.tier
    a.band(-28, 22, -1, 1, a.handle, ROD)
    if t: a.band(-10, -4, -1.2, 1.2, lambda x, y: 'cloth' if S(x, y) % 4 < 2 else a.trim, ROD)
    # the blade leaves the top of the shaft toward the upper left and hooks down to a point
    R = 13.0 if t < 2 else 14.0
    crescent(a, (19.0, 17.0), R + 1, (18.0, 21.0), R + 1.3, keep=lambda x, y: x <= 26 and y <= 14)
    a.band(18, 24, -1.8, 1.8, 'gold' if t else 'metal', 'bevel')
    if t == 2:
        a.gem(*at(21, 0), 1.3)
        a.poly_st([(23, 1), (29, 4), (25, 0)], 'gold')
    a.band(-29, -27, -1.4, 1.4, 'metal', 'bevel')

def hammer(a):
    t = a.tier
    a.band(-28, 14, -1, 1, a.handle, ROD)
    if t: a.band(-26, -14, -1.2, 1.2, lambda x, y: 'leather' if S(x, y) % 4 < 2 else a.trim, ROD)
    hs, ht = (5, 8) if t == 0 else (6, 9) if t == 1 else (6.5, 10)
    a.band(18 - hs, 18 + hs, -ht, ht, 'metal', 'bevel')                       # the head, across the shaft
    if t:
        for tt in (-ht + 1.5, ht - 1.5): a.band(18 - hs, 18 + hs, tt - 0.6, tt + 0.6, 'gold', 'bevel')   # bands
        a.gem(*at(18, 0), 1.8 if t == 1 else 2.3)
    if t == 2:
        a.poly_st([(18 + hs, -2), (28, 0), (18 + hs, 2)], 'metal')          # top spike
        for tt in (-ht, ht): a.band(16, 20, tt - 0.6 * (1 if tt > 0 else -1), tt + 2.4 * (1 if tt > 0 else -1), 'gem', 'bevel') if False else None
    a.band(-29, -27, -1.6, 1.6, 'gold' if t else 'metal', 'bevel')

def gauntlet(a):
    t = a.tier
    # an armoured fist seen from the back, knuckles up, flared cuff at the bottom
    cuff = 'metal' if t else 'leather'
    a.poly([(8, 21), (24, 21), (27, 30), (5, 30)], cuff)                  # cuff
    a.poly([(9, 8), (24, 8), (24, 18), (22, 21), (10, 21), (9, 18)], 'metal')   # back of the hand
    for x0 in (9.5, 13.5, 17.5, 21.5):                                    # four curled fingers
        a.disc(x0 + 1.2, 6.5, 2.1, 'metal')
        a.setpx(int(x0 + 1), 9, 'metal', 1)
    a.poly([(5, 12), (9.5, 10), (9.5, 18), (6, 17)], 'metal')             # thumb
    a.rect(10, 10, 23, 10, 'metal', 1)                                    # knuckle line
    a.rect(8, 20, 24, 21, 'gold' if t else 'metal')                       # wrist band
    if t: a.gem(16.5, 15, 2.2 if t == 1 else 2.7)
    else: a.disc(16.5, 15, 1.6, 'metal', ring=0.9)
    if t == 2:
        for x0 in (10.7, 14.7, 18.7, 22.7): a.poly([(x0 - 1, 4), (x0, 0.3), (x0 + 1, 4)], 'gold')   # knuckle spikes
        a.rect(7, 26, 25, 26, 'gem', 3)
    elif t == 1: a.rect(7, 26, 25, 26, 'gold', 3)
    else:
        for x in (8, 12, 16, 20, 24): a.setpx(x, 26, 'metal', 3)          # stitches

def grimoire(a):
    t = a.tier
    a.rect(5, 4, 25, 27, 'paper')                                      # page block
    a.rect(4, 3, 24, 26, 'metal' if t == 0 else 'leather')             # cover
    a.rect(4, 3, 6, 26, 'cloth' if t else 'metal')                     # spine
    for y in range(28 - 1, 28): pass
    a.rect(6, 27, 26, 28, 'paper', 2)
    if t == 0:
        a.disc(15, 14, 4.2, 'metal', ring=3.0)
    else:
        for (x, y) in ((8, 6), (21, 6), (8, 23), (21, 23)): a.rect(x - 1, y - 1, x + 1, y + 1, 'gold')   # corners
        a.disc(15, 14.5, 5.6, 'gold', ring=4.6)
        a.gem(15, 14.5, 2.6 if t == 1 else 3.2)
    if t == 2:
        a.rect(25, 12, 27, 17, 'gold')                                 # clasp
        for y in (5, 24): a.rect(10, y, 20, y, 'gem', 3)
        a.rect(12, 28, 13, 30, 'gem', 2)                               # ribbon

def harp(a):
    t = a.tier
    # pillar on the left, curved neck on top, sound box down the right
    a.rect(6, 5, 8, 27, 'metal' if t == 0 else 'gold')
    a.poly([(6, 3), (13, 1), (20, 4), (26, 3), (27, 6), (20, 8), (13, 5), (8, 7)], 'metal')
    a.poly([(20, 6), (26, 5), (26, 10), (14, 27), (8, 27), (8, 25)], 'metal')
    for i, x in enumerate(range(10, 21, 2)):                           # strings, pillar to sound box
        y1 = int(25 - (x - 8) * 1.45)
        for y in range(7 if x > 13 else 6, max(8, y1)): a.setpx(x, y, 'string', 3)
    a.rect(5, 27, 15, 29, 'metal' if t == 0 else 'gold')
    if t:
        a.gem(7, 4, 1.6 if t == 1 else 2.0)
        a.gem(22.5, 13, 1.4)
    if t == 2:
        a.poly([(26, 3), (30, 0), (28, 6)], 'gold')
        for y in range(9, 26, 4): a.setpx(7, y, 'gem', 3)

# ---- ArcaneSouls 0.27.0 swords (kuwusaki 2026-10-17: more weapons, our own drawings, each with its own stats) -----------------------

def longsword(a):    # hand-and-a-half: long grip, long straight guard, wheel pommel
    t = a.tier
    a.grip(-27, -11, 1, mat='leather' if t else 'wood', wrap='gold' if t == 2 else 'cloth' if t else None, period=4)
    a.blade(-8, 29, 2.6, 7, w0=3.4)
    a.band(-8, 20, -0.5, 0.5, 'metal', [1])                       # fuller
    if t == 2: glow_edge(a, -5, 27, 2.6, 7)
    a.guard(-9, 1, -10, 10, 'gold' if t else 'metal', tips=t > 0)
    cx, cy = at(-28, 0)
    a.disc(cx, cy, 2.2, 'gold' if t else 'metal', ring=1.0 if t else None)
    if t == 2: a.gem(cx, cy, 1.0)

def flamberge(a):    # two-hander with a wavy blade, a blunt ricasso and parrying lugs
    t = a.tier
    wave = lambda s: 0 if s < -1 else 1.3 * math.sin((s + 1) * math.pi / 5)
    a.blade(-1, 29, 3.0, 7, curve=wave)
    a.band(-7, -1, -1.6, 1.6, 'metal', 'bevel')                     # ricasso
    for tt in (-1, 1): a.poly_st([(-2, 2.6 * tt), (1, 4.6 * tt), (0, 2 * tt)], 'gold' if t else 'metal')   # lugs
    if t == 2: glow_edge(a, 1, 27, 3.0, 7, curve=wave)
    a.guard(-8, 1.2, -11, 11, 'gold' if t else 'metal', tips=t > 0)
    if t == 2: a.gem(*at(-8, 0), 1.5)
    a.grip(-27, -10, 1.2, mat='leather' if t else 'wood', wrap='cloth' if t else None, period=5)
    a.disc(*at(-28, 0), 1.8, 'gold' if t else 'metal')

def sabre(a):        # light curved blade, D-shaped knuckle bow on the shadow side
    t = a.tier
    curve = lambda s: max(0, s + 6) ** 2 / 420.0
    a.blade(-6, 29, 2.2, 6, curve=curve)
    if t: a.band(-6, 22, -2.2, -1.7, 'metal', [4], curve=curve)
    if t == 2: glow_edge(a, -4, 27, 2.2, 6, curve=curve)
    g = 'gold' if t else 'metal'
    a.band(-9, -7, -4, 5, g, 'bevel')                               # cross guard
    a.band(-24, -8, 4.0, 5.2, g, 'bevel')                           # knuckle bow
    a.band(-25, -23, -1, 5.2, g, 'bevel')                           # bow meets the pommel
    a.grip(-22, -10, 1, mat='leather' if t else 'wood', wrap='gold' if t == 2 else None, period=3)
    if t == 2: a.gem(*at(-8, 0), 1.3)

def scimitar(a):     # strong curve, the blade widens toward the tip
    t = a.tier
    curve = lambda s: max(0, s + 4) ** 2 / 170.0
    a.blade(-4, 25, 3.6, 6, curve=curve, w0=1.8)
    if t: a.band(-4, 18, -1.8, -1.2, 'metal', [4], curve=curve)
    if t == 2: glow_edge(a, -2, 23, 3.6, 6, curve=curve)
    g = 'gold' if t else 'metal'
    a.guard(-6, 1, -6, 6, g)
    for tt in (-1, 1): a.poly_st([(-7, 6 * tt), (-11, 8 * tt), (-7, 4.5 * tt)], g)   # down-swept quillons
    if t == 2: a.gem(*at(-6, 0), 1.3)
    a.grip(-21, -8, 1, mat='cloth' if t else 'wood', wrap='gold' if t else None, period=3)
    a.poly_st([(-21, 0), (-24, -2.5), (-27, 1.5), (-23, 3)], g)                      # hooked pommel

def falchion(a):     # single-edged, straight back, the edge swells toward a clipped point
    t = a.tier
    a.poly_st([(-7, -2.2), (24, -2.2), (29, 0), (26, 3.6), (18, 5.4), (6, 4.2), (-7, 2.4)], 'metal')
    edge = [p for p in a.px if a.px[p][0] == 'metal' and T(*p) >= 1 and
            T(*p) >= (2.4 + (S(*p) + 7) * 0.12 if S(*p) < 18 else 4.0) - 1.6]
    for p in edge: a.px[p] = ('gem', 3) if t == 2 else ('metal', 4)
    a.band(-7, 20, -2.2, -1.6, 'metal', [1])                         # thick spine
    g = 'gold' if t else 'metal'
    a.guard(-8, 1, -6, 6, g, tips=t > 0)
    if t == 2: a.gem(*at(-8, 0), 1.3)
    a.grip(-23, -10, 1, mat='leather' if t else 'wood', wrap='cloth' if t else None, period=4)
    a.disc(*at(-24, 0), 1.8, g)

def cutlass(a):      # short, broad, curved; a shell guard
    t = a.tier
    curve = lambda s: max(0, s + 4) ** 2 / 300.0
    a.blade(-4, 22, 3.4, 6, curve=curve)
    if t: a.band(-4, 16, -3.4, -2.8, 'metal', [4], curve=curve)
    if t == 2: glow_edge(a, -2, 20, 3.4, 6, curve=curve)
    g = 'gold' if t else 'metal'
    a.disc(*at(-7, 2.5), 3.8, g)                                    # shell
    a.band(-20, -7, 4.6, 5.6, g, 'bevel')                           # knuckle bow
    a.band(-21, -19, -1, 5.6, g, 'bevel')
    a.grip(-19, -8, 1, mat='leather' if t else 'wood', wrap='gold' if t == 2 else None, period=3)
    if t == 2: a.gem(*at(-7, 2.5), 1.6)

def gladius(a):      # short leaf blade, round pommel, ridged grip
    t = a.tier
    a.poly_st([(-6, -2.6), (8, -3.6), (18, -2.4), (25, 0), (18, 2.4), (8, 3.6), (-6, 2.6)], 'metal')
    a.band(-4, 18, -0.5, 0.5, 'metal', [1 if t else 2])
    if t == 2: glow_edge(a, -2, 23, 3.4, 8)
    g = 'gold' if t else 'metal'
    a.band(-9, -6, -4.6, 4.6, g if t else 'wood', 'bevel')            # oval guard
    a.grip(-18, -10, 1.4, mat='ebony' if t == 2 else 'wood', wrap=g, period=3)
    cx, cy = at(-21, 0)
    a.disc(cx, cy, 2.6, g if t else 'wood')
    if t == 2: a.gem(cx, cy, 1.2)

def khopesh(a):      # hilt and a straight neck, then an arc bulging up-left that hooks back; the convex edge cuts
    t = a.tier
    a.grip(-26, -10, 1.2, mat='ebony' if t else 'wood', wrap='gold' if t else None, period=4)
    a.band(-9, 0, -1.3, 1.3, 'metal', ROD)                         # neck
    cx, cy, rm = 21.0, 13.5, 7.0                                    # the arc: centre, middle radius
    a0, a1 = 150.0, 340.0                                           # degrees, image coordinates (y down): neck .. tip
    def half(ang):                                                  # half thickness: 1.6 at the neck, 2.4 mid, 0 at the tip
        u = (ang - a0) / (a1 - a0)
        return 1.6 + 1.6 * math.sin(min(1, u / 0.55) * math.pi / 2) if u < 0.55 else 3.2 * ((1 - u) / 0.45) ** 0.7
    def polar(x, y):
        ang = math.degrees(math.atan2(y - cy, x - cx)) % 360
        if ang < 90: ang += 360
        return math.hypot(x - cx, y - cy), ang
    def inside(x, y):
        r, ang = polar(x, y); return a0 <= ang <= a1 and abs(r - rm) <= half(ang) * 0.75 + 0.3
    c = a.cells(inside); a._put(c, 'metal', 'bevel')
    for p in c:
        r, ang = polar(*p)
        if r - rm >= half(ang) * 0.75 - 0.9: a.px[p] = ('gem', 3) if t == 2 else ('metal', 4)
    a.band(-11, -9, -2.4, 2.4, 'gold' if t else 'metal', 'bevel')
    if t == 2: a.gem(*at(-10, 0), 1.2)
    a.disc(*at(-27, 0), 1.6, 'gold' if t else 'metal')

def kris(a):         # a short wavy blade with a wide asymmetric base
    t = a.tier
    wave = lambda s: 1.1 * math.sin(s * math.pi / 4.5)
    a.blade(-2, 21, 2.2, 6, curve=wave)
    a.poly_st([(-4, -2.4), (2, -2.0), (0, 5.4), (-4, 4.6)], 'metal')          # ganja (base)
    if t == 2: glow_edge(a, 0, 19, 2.2, 6, curve=wave)
    g = 'gold' if t else 'metal'
    a.band(-6, -4, -2, 2, g, 'bevel')
    a.grip(-17, -6, 1.2, mat='wood' if t < 2 else 'ebony', wrap=g if t else None, period=3)
    a.poly_st([(-17, -1), (-21, -4), (-22, 0), (-19, 2)], 'wood' if t == 0 else g)   # bent pommel
    if t == 2: a.gem(*at(-19, -1), 1.0)

CATEGORIES = {   # category -> (draw, how it is held)
    'hammer': (hammer, 'big'), 'katana': (katana, 'big'), 'gauntlet': (gauntlet, 'flat'), 'dagger': (dagger, 'small'),
    'rapier': (rapier, 'big'), 'harp': (harp, 'flat'), 'sceptre': (sceptre, 'handheld'), 'sickle': (sickle, 'handheld'),
    'halberd': (halberd, 'big'), 'staff': (staff, 'big'), 'scythe': (scythe, 'big'), 'grimoire': (grimoire, 'flat'),
    'greatsword': (greatsword, 'big'), 'spear': (spear, 'big'), 'sword': (sword, 'handheld'), 'axe': (axe, 'handheld'),
    'longsword': (longsword, 'handheld'), 'flamberge': (flamberge, 'big'), 'sabre': (sabre, 'handheld'),
    'scimitar': (scimitar, 'handheld'), 'falchion': (falchion, 'handheld'), 'cutlass': (cutlass, 'handheld'),
    'gladius': (gladius, 'handheld'), 'khopesh': (khopesh, 'handheld'), 'kris': (kris, 'handheld'),
}
def sprite(category, metal):
    a = Art(metal); CATEGORIES[category][0](a); return a.image()
