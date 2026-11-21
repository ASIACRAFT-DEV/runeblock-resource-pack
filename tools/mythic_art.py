#!/usr/bin/env python3
"""Gear v4 Mythic icons, pass 2 (Ett's brief, dev-chat Nov 18, docs/spec/Gear_icon_redraw_ettlel_2026-11-18.md).

32x32 pixel art at the density of the pack's other weapons: long weapons lie on the diagonal, pommel bottom-left, tip
top-right; light from the top-left. Every part is shaded as a volume (a height field from its own outline, lit, then snapped to
a 6-step ramp, so gradients are clean pixel clusters, never airbrushed), casts a one-pixel contact shadow on what lies under it,
and the finished sprite gets a one-pixel outline in the darkest step of the part next to it. Centred in the 32x32 canvas.

  python3 -I tools/mythic_art.py <out dir>      writes <id>.png for every sprite in SPRITES
"""
import math
import os
import sys
from collections import deque

from PIL import Image

N = 32


def rgb(h): return tuple(int(h[i:i + 2], 16) for i in (1, 3, 5))


# outline, deep shadow, shadow, mid, light, highlight
R = {k: [rgb(c) for c in v] for k, v in {
    'gold':    ['#351f04', '#74460a', '#b27812', '#e4aa22', '#fbdb5a', '#fffcdc'],
    'steel':   ['#12141c', '#2b2f3e', '#4a5064', '#747c92', '#a8b1c6', '#eaf0fa'],
    'iron':    ['#0b0a10', '#1b1923', '#2f2c3b', '#474455', '#656173', '#928ea2'],
    'ebony':   ['#07050a', '#150f1a', '#251c2e', '#382c44', '#4f415f', '#726284'],
    'white':   ['#1c2034', '#565d7a', '#9098b4', '#c5cce0', '#e8edf7', '#ffffff'],
    'void':    ['#0b041e', '#220d50', '#421f98', '#6a3ad4', '#a072f4', '#eee0ff'],
    'ruby':    ['#220309', '#580a15', '#98131f', '#d22b2f', '#f46558', '#ffd6c8'],
    'teal':    ['#052829', '#0a5856', '#138e86', '#2ac2b0', '#7af0dc', '#eafff9'],
    'blue':    ['#091536', '#152e78', '#234eb2', '#3b7ade', '#86b2f6', '#e6f0ff'],
    'green':   ['#06220d', '#114e1e', '#1e7a2d', '#3bac3d', '#88dc52', '#eaffba'],
    'bone':    ['#231b11', '#584a34', '#8d7e62', '#bcae8c', '#e0d5b4', '#fdf7e2'],
    'page':    ['#322818', '#7d6d4e', '#b2a47e', '#d8ccaa', '#f2e9cf', '#fffdf3'],
    'leather': ['#190d07', '#361f0e', '#533118', '#714726', '#90613a', '#b28157'],
}.items()}
LIGHT = (-0.52, -0.62, 0.59)
K = 1.0      # per-sprite fit: the drawing is scaled about the canvas centre so every icon keeps at least 1 px of padding


def T(p): return ((p[0] - 15.5) * K + 15.5, (p[1] - 15.5) * K + 15.5)


def fit(pts):
    """Hand-placed points go through the fit; a set came from a shape builder and is already on the final grid."""
    return pts if isinstance(pts, (set, frozenset)) else [T(q) for q in pts]


class Sprite:
    def __init__(self):
        self.px = {}      # (x, y) -> (ramp, step)
        self.free = {}    # (x, y) -> (ramp, step): loose motes, no outline around them

    def paint(self, mask, ramp, r=2.0, base=0.0, shape=None, bands=None, shadow=True):
        """Shades `mask` as a rounded volume of radius r. shape: the outline the volume comes from (default the mask).
        bands: (fx, fy, amp) adds metal reflections that run across the part."""
        mask = {p for p in mask if 0 <= p[0] < N and 0 <= p[1] < N}
        shape = shape or mask
        dist = {}
        q = deque()
        for p in shape:
            if any((p[0] + dx, p[1] + dy) not in shape for dx in (-1, 0, 1) for dy in (-1, 0, 1)):
                dist[p] = 1
                q.append(p)
        while q:
            p = q.popleft()
            for dx in (-1, 0, 1):
                for dy in (-1, 0, 1):
                    n = (p[0] + dx, p[1] + dy)
                    if n in shape and n not in dist:
                        dist[n] = dist[p] + 1
                        q.append(n)

        def h(p):
            if p not in dist:
                return 0.0
            t = min(dist[p] - 0.5, r) / r
            return r * math.sqrt(max(0, 1 - (1 - t) ** 2))

        out = {}
        for (x, y) in mask:
            dx, dy = (h((x + 1, y)) - h((x - 1, y))) / 2, (h((x, y + 1)) - h((x, y - 1))) / 2
            ln = math.sqrt(dx * dx + dy * dy + 1)
            v = ((-dx * LIGHT[0] - dy * LIGHT[1] + LIGHT[2]) / ln - 0.1) / 0.9 + base
            if bands:
                v += bands[2] * math.sin(x * bands[0] + y * bands[1])
            out[(x, y)] = 1 if v < 0.30 else 2 if v < 0.50 else 3 if v < 0.72 else 4 if v < 0.92 else 5
        for p, s in list(out.items()):      # no orphan pixels: a lone step joins its neighbours (highlights may stay single)
            near = [out[n] for n in ((p[0] + 1, p[1]), (p[0] - 1, p[1]), (p[0], p[1] + 1), (p[0], p[1] - 1)) if n in out]
            if near and s not in near and s != 5:
                out[p] = max(set(near), key=near.count)
        if shadow:
            for (x, y) in mask:
                for n in ((x + 1, y), (x, y + 1), (x + 1, y + 1)):
                    if n not in mask and n in self.px:
                        a, s = self.px[n]
                        self.px[n] = (a, max(1, s - 1))
        for p, s in out.items():
            self.px[p] = (ramp, s)
            self.free.pop(p, None)

    def mark(self, pts, ramp, step):
        for p in fit(pts):
            p = (int(p[0]), int(p[1]))
            if 0 <= p[0] < N and 0 <= p[1] < N:
                self.px[p] = (ramp, step)

    def shift(self, pts, by):
        """Lightens / darkens what is already painted at pts by whole steps (engraving)."""
        for p in fit(pts):
            p = (int(p[0]), int(p[1]))
            if p in self.px:
                a, s = self.px[p]
                self.px[p] = (a, max(1, min(5, s + by)))

    def mote(self, pts, ramp, step):
        for p in fit(pts):
            p = (int(p[0]), int(p[1]))
            if p not in self.px:
                self.free[p] = (ramp, step)

    def spark(self, x, y, ramp='gold'):
        x, y = (int(round(v)) for v in T((x, y)))
        self.mote({(x, y)}, ramp, 5)
        self.mote({(x - 1, y), (x + 1, y), (x, y - 1), (x, y + 1)}, ramp, 4)

    def erase(self, pts):
        for p in fit(pts):
            self.px.pop((int(p[0]), int(p[1])), None)

    def image(self):
        solid = {}
        for (x, y), (a, s) in self.px.items():
            solid[(x, y)] = R[a][s]
        edge = {}
        for x in range(-1, N + 1):
            for y in range(-1, N + 1):
                if (x, y) in self.px:
                    continue
                for n in ((x - 1, y), (x + 1, y), (x, y - 1), (x, y + 1)):
                    if n in self.px:
                        edge[(x, y)] = R[self.px[n][0]][0]
                        break
        loose = {p: R[a][s] for p, (a, s) in self.free.items() if p not in edge and p not in solid}
        every = {**loose, **edge, **solid}
        x0, x1 = min(p[0] for p in every), max(p[0] for p in every)
        y0, y1 = min(p[1] for p in every), max(p[1] for p in every)
        ox, oy = (N - 1 - x1 - x0) // 2, (N - 1 - y1 - y0) // 2       # centred
        im = Image.new('RGBA', (N, N), (0, 0, 0, 0))
        for (x, y), c in every.items():
            if 0 <= x + ox < N and 0 <= y + oy < N:
                im.putpixel((x + ox, y + oy), (*c, 255))
        return im


# ---------------------------------------------------------------------------------------------- shapes
def shaft(x0, y0, x1, y1, w, w1=None):
    w1 = w if w1 is None else w1
    (x0, y0), (x1, y1), w, w1 = T((x0, y0)), T((x1, y1)), w * K, w1 * K
    dx, dy = x1 - x0, y1 - y0
    ln2 = dx * dx + dy * dy
    out = set()
    for x in range(N):
        for y in range(N):
            t = max(0, min(1, ((x - x0) * dx + (y - y0) * dy) / ln2))
            if math.hypot(x - (x0 + t * dx), y - (y0 + t * dy)) <= (w + (w1 - w) * t) / 2:
                out.add((x, y))
    return out


def poly(pts):
    pts = [T(q) for q in pts]
    out = set()
    for x in range(N):
        for y in range(N):
            inside = False
            px, py = x + 0.5, y + 0.5
            for i in range(len(pts)):
                (ax, ay), (bx, by) = pts[i], pts[(i + 1) % len(pts)]
                if (ay > py) != (by > py) and px < (bx - ax) * (py - ay) / (by - ay) + ax:
                    inside = not inside
            if inside:
                out.add((x, y))
    return out


def disc(cx, cy, r):
    (cx, cy), r = T((cx, cy)), r * K
    return {(x, y) for x in range(N) for y in range(N) if math.hypot(x - cx, y - cy) <= r}


def ring(cx, cy, r0, r1): return disc(cx, cy, r1) - disc(cx, cy, r0)


def rect(x0, y0, x1, y1):
    (a, b), (c, d) = T((x0, y0)), T((x1, y1))
    return {(x, y) for x in range(int(round(a)), int(round(c)) + 1) for y in range(int(round(b)), int(round(d)) + 1)}


def bez(p0, c, p1, t):
    return ((1 - t) ** 2 * p0[0] + 2 * (1 - t) * t * c[0] + t * t * p1[0], (1 - t) ** 2 * p0[1] + 2 * (1 - t) * t * c[1] + t * t * p1[1])


def curve(p0, c, p1, w0, w1=None, wm=None, steps=80):
    """A stroke along a quadratic Bezier: width w0 at the start, w1 at the end, wm in the middle."""
    w1 = w0 if w1 is None else w1
    out = set()
    for i in range(steps + 1):
        t = i / steps
        w = w0 + (w1 - w0) * t
        if wm is not None:
            w += (wm - (w0 + w1) / 2) * math.sin(t * math.pi)
        x, y = bez(p0, c, p1, t)
        out |= disc(x, y, max(0.45, w / 2))
    return out


def line(a, b):
    a, b = T(a), T(b)
    n = int(max(abs(b[0] - a[0]), abs(b[1] - a[1]))) or 1
    return {(int(round(a[0] + (b[0] - a[0]) * i / n)), int(round(a[1] + (b[1] - a[1]) * i / n))) for i in range(n + 1)}


U, V = (math.sqrt(.5), -math.sqrt(.5)), (math.sqrt(.5), math.sqrt(.5))   # along the weapon (to the tip), across it


def L(c, a, b): return (c[0] + a * U[0] + b * V[0], c[1] + a * U[1] + b * V[1])


def local(c, pts): return poly([L(c, a, b) for a, b in pts])


# ---------------------------------------------------------------------------------------------- weapons
def throne_of_ruin():
    """Hammer: a huge black-iron head built like a throne, high back and arms, royal gold on it, one arm broken away."""
    s = Sprite()
    c = (20.0, 12.0)
    handle = shaft(3.5, 28.5, 16, 16, 3)
    s.paint(handle, 'leather', 1.5)
    s.shift({p for p in handle if (p[0] - p[1]) % 4 == 0}, -2)                       # leather wrap
    for k in (-20, -12):
        s.paint({p for p in shaft(3, 29, 17, 15, 3.6) if k <= p[0] - p[1] <= k + 1}, 'gold', 1.2)
    s.paint(local((4, 28), [(-3.6, 0), (-1, -2.2), (1.4, -1.6), (1.4, 1.6), (-1, 2.2)]), 'gold', 1.6)      # spiked pommel
    s.paint(local(c, [(-10.5, -2.2), (-6, -4), (-6, 4), (-10.5, 2.2)]), 'gold', 1.6)                        # collar
    s.paint(local(c, [(-6.5, -11), (4.5, -12), (4.5, 12), (-6.5, 11)]), 'iron', 3.2, bands=(0.7, 0.7, 0.05))  # the block
    s.paint(local(c, [(-7.5, -13.5), (5.5, -13.5), (5.5, -9.5), (-7.5, -9.5)]), 'steel', 1.8)               # left striking face
    broken = [(-7.5, 9.5), (5.5, 9.5), (5.5, 11), (3, 12.2), (2, 13.8), (-1, 12.6), (-3, 14), (-5.5, 12.8), (-7.5, 13.5)]
    s.paint(local(c, broken), 'steel', 1.8)                                                                 # right face, broken
    s.paint(local(c, [(4.5, -3.8), (9, -3.8), (11, 0), (9, 3.8), (4.5, 3.8)]), 'iron', 2.4)                 # the throne's high back
    s.paint(local(c, [(8.2, -2.6), (9.2, -2.6), (11, 0), (9.2, 2.6), (8.2, 2.6)]), 'gold', 1.4)
    for b in (-7.5, 7.5):                                                                                   # its posts
        s.paint(local(c, [(4.5, b - 2), (7.5, b - 1.6), (9.2, b), (7.5, b + 1.6), (4.5, b + 2)]), 'iron', 1.7)
        s.paint(local(c, [(7, b - 1.2), (7.8, b - 1.2), (9.2, b), (7.8, b + 1.2), (7, b + 1.2)]), 'gold', 1)
    s.paint(local(c, [(3.2, -9.5), (4.6, -9.5), (4.6, 9.5), (3.2, 9.5)]), 'gold', 1)                        # gilded bands
    s.paint(local(c, [(-5.8, -9.5), (-4.5, -9.5), (-4.5, 9.5), (-5.8, 9.5)]), 'gold', 1)
    s.paint(disc(*L(c, -0.8, 0), 4), 'gold', 2)                                                             # the royal seal
    s.paint(local(L(c, -0.8, 0), [(2.8, 0), (0, -2.6), (-2.8, 0), (0, 2.6)]), 'ruby', 2.2)
    s.shift(line(L(c, 2.5, 8.5), L(c, -1, 5.2)) | line(L(c, -1, 5.2), L(c, -4, 7)), -3)                     # the crack
    s.shift([L(c, 1.5, -6.5), L(c, -2.5, -7.5), L(c, 0.5, -8.5), L(c, -3, -4.5)], 2)                        # rivets
    return s


def godless():
    """Katana: a black-backed blade with a white wave-tempered edge and a notch out of it, its guard a broken halo."""
    s = Sprite()
    p0, c, p1 = (11, 21), (21, 15.5), (29.5, 1.5)
    samples = [(i / 120, T(bez(p0, c, p1, i / 120))) for i in range(121)]
    blade = {}
    for x in range(N):
        for y in range(N):
            t, q = min(samples, key=lambda a: (a[1][0] - x) ** 2 + (a[1][1] - y) ** 2)
            tx, ty = T(bez(p0, c, p1, min(1, t + .01))), T(bez(p0, c, p1, max(0, t - .01)))
            nx, ny = -(tx[1] - ty[1]), tx[0] - ty[0]
            ln = math.hypot(nx, ny) or 1
            d = ((x - q[0]) * nx + (y - q[1]) * ny) / ln        # + = the cutting edge (down-right)
            half = 2.5 * K if t < 0.8 else 2.5 * K * max(0, (1 - t) / 0.2)
            if abs(d) <= half and math.hypot(x - q[0], y - q[1]) <= half + 0.5:
                blade[(x, y)] = (t, d)
    s.paint(set(blade), 'white', 1.2)
    for p, (t, d) in blade.items():
        wave = 0.35 * math.sin(t * 34)
        if d < -0.75:
            s.mark([p], 'iron', 3 if d > -1.5 else 2)           # the black spine
        elif d < wave:
            s.mark([p], 'white', 3)                             # the body of the steel
        else:
            s.mark([p], 'white', 5 if int(t * 26) % 3 else 4)   # the bright tempered edge
    s.erase([(25, 12), (26, 12), (26, 11)])                                                                 # a notch out of the edge
    handle = shaft(3, 29, 10, 22, 3.2)
    s.paint(handle, 'ebony', 1.6)
    for k in range(-24, -11, 3):                                                                            # diamond wrap
        for p in handle:
            if p[0] - p[1] == k and p[0] + p[1] == 32:
                s.mark([p], 'ruby', 4)
    s.shift({p for p in handle if (p[0] - p[1]) % 3 == 0 and p[0] + p[1] != 32}, 1)
    s.paint(disc(3, 29, 2), 'gold', 1.5)
    s.mote([(1, 26), (1, 25), (0, 24)], 'ruby', 3)                                                          # the cord
    halo = ring(11, 21, 4.1, 6.6)
    hc = T((11, 21))
    deg = lambda q: math.degrees(math.atan2(q[1] - hc[1], q[0] - hc[0])) % 360
    cut = {q for q in halo if 20 <= deg(q) <= 62 or 200 <= deg(q) <= 232}                                   # broken in two places
    s.paint(halo - cut, 'gold', 1.8, bands=(.8, .8, .07))
    s.mote([(16, 25), (17, 24), (6, 17), (5, 18)], 'gold', 4)                                               # its fallen pieces
    s.paint(shaft(11, 21, 13.5, 18.5, 3.2), 'gold', 1.3)
    s.spark(20, 27, 'gold')
    s.spark(5, 11, 'gold')
    return s


def unwritten_fate():
    """Bow: an ancient gold recurve around a dark carved grip, a blank page bound to it, the string drawn bright."""
    s = Sprite()
    p0, c, p1 = (5.5, 26), (7, 7), (26, 5.5)
    s.paint(line((5, 27), (27, 5)), 'white', 1, base=0.6, shadow=False)                                      # the string
    s.paint(curve(p0, c, p1, 1.8, 1.8, 3.8), 'gold', 2, bands=(0.6, 0.6, 0.08))
    s.paint(curve((5.5, 26), (3.5, 28), (6.5, 29.5), 2.2, 1), 'gold', 1.2)                                   # recurved tips
    s.paint(curve((26, 5.5), (28, 3.5), (29.5, 6.5), 2.2, 1), 'gold', 1.2)
    for t in (.12, .22, .32, .68, .78, .88):                                                                 # engraved runes
        x, y = bez(p0, c, p1, t)
        s.shift([(x, y), (x + 1, y)], -2)
    g = (11.5, 11.5)
    s.paint(local(g, [(-5.5, -2.2), (5.5, -2.2), (5.5, 2.2), (-5.5, 2.2)]), 'ebony', 1.8)                    # the grip
    for a in (-5.5, 4.2):
        s.paint(local(g, [(a, -2.9), (a + 1.4, -2.9), (a + 1.4, 2.9), (a, 2.9)]), 'gold', 1.1)
    s.paint(disc(g[0], g[1], 2.2), 'gold', 1.4)
    s.paint(disc(g[0], g[1], 1.3), 'teal', 1.3, base=.15)
    page = poly([(13, 16), (18, 14), (20, 20), (18.5, 21), (19, 24), (15, 25), (14.5, 21), (12.5, 20)])
    s.paint(page, 'page', 1.5)                                                                               # the blank page
    s.shift(line((15, 18), (18, 17)) | line((15, 20), (18, 19)) | line((16, 23), (18, 22)), -1)
    s.paint(shaft(13, 15.5, 17.5, 13.5, 1.4), 'ruby', 1)
    s.spark(26, 17, 'gold')
    s.spark(23, 26, 'white')
    return s


def the_silent_extinction():
    """Crossbow: a steel-railed killing machine: gear-wound core of void, pulleyed glass limbs, a loaded black bolt."""
    s = Sprite()
    s.paint(local((7.5, 24.5), [(-4.2, -2.6), (3.6, -2), (3.6, 2), (-4.2, 3.2)]), 'ebony', 2)                # the stock
    s.paint(local((10.5, 21.5), [(-1.6, 1), (1.6, 1), (1.2, 6.5), (-1.2, 6.5)]), 'ebony', 1.3)               # pistol grip
    s.paint(local((7.5, 24.5), [(-1.5, -2.6), (-0.2, -2.6), (-0.2, 3), (-1.5, 3)]), 'void', 1, base=.25)
    s.paint(shaft(9, 23, 24.5, 7.5, 3), 'steel', 1.5, bands=(.8, .8, .07))                                   # the rail
    c = (22.5, 9.5)
    arm = lambda sgn: curve(L(c, 0, 0), L(c, 2.5, sgn * 7), L(c, -3.5, sgn * 13), 3.6, 1.4)
    s.paint(arm(-1) | arm(1), 'void', 1.7, base=.2)                                                         # glass limbs
    s.paint(curve(L(c, .6, -1), L(c, 3, -6), L(c, 0, -10), 1), 'iron', .8)                                   # steel backing
    s.paint(curve(L(c, .6, 1), L(c, 3, 6), L(c, 0, 10), 1), 'iron', .8)
    tips = L(c, -3.5, -13), L(c, -3.5, 13)
    core = (15.5, 16.5)
    s.mark(line(tips[0], core) | line(tips[1], core), 'white', 4)                                            # the cables
    for t in tips:
        s.paint(disc(t[0], t[1], 1.7), 'gold', 1.2)                                                          # pulleys
    s.paint(disc(c[0], c[1], 2.4), 'iron', 1.4)
    gear = disc(core[0], core[1], 5)
    gc = T(core)
    teeth = {p for p in gear if math.hypot(p[0] - gc[0], p[1] - gc[1]) > 3.9 * K
             and int((math.degrees(math.atan2(p[1] - gc[1], p[0] - gc[0])) + 360) // 45) % 2}
    s.paint(gear - teeth, 'steel', 2)
    s.paint(disc(core[0], core[1], 2.7), 'iron', 1.4)
    s.paint(disc(core[0], core[1], 1.7), 'void', 1.7, base=.3)                                               # the void core
    s.paint(shaft(19, 13, 27.5, 4.5, 1.5), 'iron', 1, base=.1)                                               # the bolt
    s.paint(local((28, 4), [(2.6, 0), (-1.2, -1.9), (-.4, 0), (-1.2, 1.9)]), 'void', 1.2, base=.2)
    s.mote([(29, 9), (24, 1), (30, 1)], 'void', 4)
    return s


def nothing_remains():
    """Staff: claws holding a shard of the void, its own pieces circling away from it, the shaft below already going."""
    s = Sprite()
    shaft_m = shaft(3.5, 28.5, 16.5, 15.5, 2.8)
    s.paint(shaft_m, 'ebony', 1.5)
    s.shift([(8, 23), (11, 20), (13, 18)], 3)
    s.paint(local((16, 16), [(-1.6, -2.6), (1, -2.2), (1, 2.2), (-1.6, 2.6)]), 'gold', 1.3)                  # collar
    s.paint(curve((16, 16), (11.5, 8), (18.5, 3.5), 2.4, .9), 'gold', 1.2)                                   # the claws
    s.paint(curve((16, 16), (24, 20.5), (28.5, 13.5), 2.4, .9), 'gold', 1.2)
    k = (21.5, 10.5)
    shard = local(k, [(7.6, 0), (3, -3), (.5, -4.8), (-5.6, -1), (-5.6, 1), (.5, 4.8), (3, 3)])
    s.paint(shard, 'void', 3.4, base=.05)
    s.shift(line(L(k, 7, 0), L(k, -5, 0)), 1)                                                                # the facet ridge
    s.shift(line(L(k, 3, -3), L(k, -1, 0)) | line(L(k, 3, 3), L(k, -1, 0)), -1)
    s.mark([L(k, 3, -1), L(k, 4, -1), L(k, 2, -1.6)], 'void', 5)
    for ang, size in ((-158, 2.2), (-122, 1.8), (150, 1.5), (118, 1.1)):                                     # pieces leaving in a ring
        x, y = k[0] + 11.2 * math.cos(math.radians(ang)), k[1] + 11.2 * math.sin(math.radians(ang))
        s.paint(poly([(x, y - size), (x + size, y), (x, y + size), (x - size, y)]), 'void', 1.2, base=.1)
    s.mote([(5, 19), (19, 25), (9, 2)], 'void', 4)
    s.erase([(3, 28), (4, 28), (3, 29), (4, 29), (2, 28), (3, 27), (5, 27), (6, 26), (5, 26)])               # the foot of it is gone
    s.mote([(5, 30), (2, 26), (8, 29), (1, 30), (7, 26)], 'ebony', 5)
    return s


def the_final_equation():
    """Grimoire: blue and gold, thick with pages, a proof ringed in sigils that was never finished."""
    s = Sprite()
    s.paint(rect(8, 26, 27, 29), 'page', 1)
    s.paint(rect(24, 5, 28, 28), 'page', 1)
    for y in range(6, 28, 2):
        s.shift([(x, y) for x in range(26, 29)], -1)
    s.shift([(x, 28) for x in range(9, 27, 2)], -1)
    s.paint(rect(4, 2, 25, 27), 'blue', 2.4, base=-.06)                                                      # the cover
    s.paint(rect(4, 2, 8, 27), 'gold', 2.2, bands=(0, 1.1, .1))                                              # the spine
    for y in (6, 14, 22):
        s.paint(rect(4, y, 8, y + 1), 'ruby', 1)
    frame = rect(10, 4, 23, 25) - rect(11, 5, 22, 24)
    s.paint(frame, 'gold', 1)
    for (x, y) in ((10, 4), (23, 4), (10, 25), (23, 25)):                                                     # corner plates
        s.paint(disc(x, y, 2.2), 'gold', 1.5)
    s.mark([(x, 7) for x in range(13, 22, 2)] + [(x, 22) for x in range(13, 22, 2)], 'blue', 5)              # inscriptions
    s.mark([(x, 8) for x in range(14, 21, 3)] + [(x, 23) for x in range(14, 21, 3)], 'gold', 4)
    s.paint(ring(16.5, 14.5, 5.4, 6.6), 'gold', 1)                                                           # the sigil ring
    for a in range(0, 360, 60):
        s.mark([(16.5 + 6 * math.cos(math.radians(a)), 14.5 + 6 * math.sin(math.radians(a)))], 'white', 5)
    sigma = line((14, 11), (19, 11)) | line((14, 11), (17, 14)) | line((17, 14), (14, 17)) | line((14, 17), (19, 17))
    s.mark(sigma, 'white', 5)
    s.mark([(19, 12), (19, 16)], 'white', 4)
    s.paint(rect(24, 12, 27, 16), 'gold', 1.4)                                                               # the clasp
    s.paint(disc(26, 14, 1.3), 'ruby', 1.2, base=.15)
    return s


def grace_beyond_death():
    """Sickle: a spine of bone growing into a living green crescent, shoots breaking out along its back."""
    s = Sprite()
    bones = shaft(3.5, 28.5, 13.5, 18.5, 2.2)
    s.paint(bones, 'bone', 1.1)
    for i in range(4):                                                                                       # vertebrae
        x, y = 5 + i * 2.6, 27 - i * 2.6
        s.paint(local((x, y), [(-.9, -2.2), (.9, -2.2), (.9, 2.2), (-.9, 2.2)]), 'bone', 1)
    s.shift({p for p in shaft(3, 29, 14, 18, 5) if (p[0] - p[1]) % 5 == 2}, -3)
    s.paint(disc(3.5, 28.5, 2), 'bone', 1.4)
    s.shift([(3, 28), (4, 29)], -3)
    outer, inner = disc(17, 13, 12.4), disc(13.2, 9.4, 10.4)
    x20, y19, x13 = T((20, 20))[0], T((19, 19))[1], T((13, 13))[0]
    blade = {p for p in outer - inner if (p[0] + p[1] > 31 + (26 - 31) * K or p[0] > x20) and not (p[0] < x13 and p[1] < y19)}
    s.paint(blade, 'green', 2.2, base=-.02)
    edge = {p for p in blade if any((p[0] + a, p[1] + b) in inner for a, b in ((-1, 0), (0, -1), (-1, -1)))}
    s.mark(edge, 'green', 5)                                                                                 # the honed edge
    glow = {p for p in blade - edge if any((p[0] + a, p[1] + b) in edge for a, b in ((-1, 0), (0, -1)))}
    s.mark(glow, 'green', 4)
    for t in range(4):                                                                                       # sap veins
        a = math.radians(20 + t * 26)
        s.shift(line((17 + 8.6 * math.cos(a), 13 + 8.6 * math.sin(a)), (17 + 11 * math.cos(a), 13 + 11 * math.sin(a))), -2)
    s.paint(disc(14, 18, 3), 'gold', 1.8)
    s.paint(disc(14, 18, 1.7), 'green', 1.6, base=.3)
    for (x, y, a, b) in ((29, 18, 2, -2), (23, 26, 2, 2)):                                                   # new growth
        s.paint(poly([(x, y), (x + a, y - 1), (x + a + 1, y + b), (x, y + 1)]), 'green', 1, base=.12)
    s.mote([(9, 10), (7, 13), (6, 17)], 'green', 4)
    s.mote([(11, 7)], 'green', 5)
    return s


def the_perfect_lie():
    """Rapier: a slender fullered blade, a swept gold and teal hilt, and beside it a second blade that isn't there."""
    s = Sprite()
    ghost = shaft(17, 21, 30.5, 7.5, 1.5, .8)
    s.mote({p for p in ghost if (p[0] + p[1]) % 5 != 0}, 'teal', 4)
    blade = shaft(12, 19, 30, 1, 3, 1.1)
    s.paint(blade, 'white', 1.3, base=.22)
    s.shift(line((15, 16), (25, 6)), -1)                                                                     # the fuller
    c = (11.5, 20.5)
    handle = shaft(3.5, 28.5, 10, 22, 2.4)
    s.paint(handle, 'ebony', 1.2)
    s.shift({p for p in handle if (p[0] - p[1]) % 2 == 0}, 2)                                                # wire wrap
    s.paint(curve(L(c, 0, 6), (11, 29.5), (4.5, 28.5), 1.4), 'gold', 1)                                      # the knuckle bow
    s.paint(curve(L(c, 0, -7), L(c, 1, 0), L(c, 0, 7), 1.8), 'gold', 1.2)                                    # the quillons
    s.paint(disc(*L(c, -2.6, -7.4), 1.3) | disc(*L(c, 2, -7.4), 1.1), 'gold', 1)
    s.paint(disc(c[0], c[1], 3.8), 'gold', 1.8)
    s.paint(disc(c[0] + .3, c[1] - .3, 2.7), 'teal', 2.4, base=.05)                                          # the cup
    s.shift([(c[0] + 1, c[1] - 2), (c[0] + 2, c[1] - 1)], 2)
    s.paint(disc(3.5, 28.5, 2.4), 'gold', 1.6)
    s.paint(disc(3.5, 28.5, 1.4), 'teal', 1.4, base=.15)
    return s


# ---------------------------------------------------------------------------------------------- armour + accessory
def the_last_crown():
    """Helm: a sealed black-steel great helm that wears its crown as part of the armour, one point snapped off."""
    s = Sprite()
    s.paint(poly([(9, 26), (22, 26), (25, 30), (6, 30)]), 'steel', 1.4)                                      # the neck guard
    s.paint(rect(7, 29, 24, 30), 'ruby', 1)
    shell = poly([(8, 9), (23, 9), (26, 14), (26.5, 20), (24, 25), (20, 29), (11, 29), (7, 25), (4.5, 20), (5, 14)])
    s.paint(shell, 'steel', 6, base=-.1, bands=(.55, 0, .05))                                                # the helm
    s.paint(poly([(5, 18), (8, 18), (11, 28), (7, 25), (4.5, 20)]), 'gold', 1.2)                             # cheek guards
    s.paint(poly([(23, 18), (26.5, 18), (26.5, 20), (24, 25), (20, 28)]), 'gold', 1.2)
    s.paint(rect(7, 14, 24, 14), 'gold', 1)                                                                  # the brow plate
    s.mark(rect(7, 15, 24, 16) | rect(15, 17, 16, 22), 'iron', 1)                                            # the T of the visor
    s.mark([(10, 15), (11, 15), (20, 15), (21, 15)], 'ruby', 4)                                              # something still looks out
    s.paint(rect(13, 17, 14, 23) | rect(17, 17, 18, 23), 'gold', 1)                                          # the nasal's edges
    s.paint(poly([(13, 23), (18, 23), (17, 28), (14, 28)]), 'gold', 1.4)
    for x in (9, 11, 20, 22):
        s.mark([(x, y) for y in (20, 22, 24)], 'iron', 1)                                                    # breaths
    crown = poly([(5, 3), (9.5, 8), (11.5, 1), (15.5, 7), (20, 1), (22.5, 8), (24, 11), (6, 11)])
    s.paint(crown, 'gold', 2.2, bands=(.7, 0, .06))
    s.paint(poly([(23, 7), (25, 7), (26, 5), (26.5, 9), (24, 11)]), 'gold', 1.2)                             # the snapped point
    s.paint(rect(5, 9, 26, 12), 'gold', 1.5)
    s.mark([(x, 10) for x in range(7, 26, 3)], 'ruby', 3)
    s.paint(poly([(15.5, 5.5), (18.5, 9), (15.5, 13.5), (12.5, 9)]), 'ruby', 2.4, base=.08)                  # the brow jewel
    for (x, y) in ((5, 3), (11.5, 1), (20, 1)):
        s.paint(disc(x, y + .5, 1.4), 'white', 1.2)
    return s


def heart_of_the_world():
    """Necklace: a whole small world held in a claw-set gold frame, hung from a heavy linked chain."""
    s = Sprite()
    for sx in (-1, 1):
        for i in range(0, 8):
            x, y = 15.5 + sx * (12 - i * 1.25), 1.5 + i * 1.3
            s.paint(disc(x, y, 1.05 if i % 2 else .8), 'gold', 1, shadow=False)
    s.paint(poly([(13, 10), (18, 10), (17.5, 14), (13.5, 14)]), 'gold', 1.5)                                  # the bail
    c = (15.5, 21.5)
    s.paint(ring(c[0], c[1], 6.6, 9.4), 'gold', 2, bands=(.8, .8, .08))                                      # the frame
    hc = T(c)
    notch = {p for p in ring(c[0], c[1], 8.3, 9.4) if int((math.degrees(math.atan2(p[1] - hc[1], p[0] - hc[0])) + 382) // 30) % 2}
    s.shift(notch, -2)
    world = disc(c[0], c[1], 6.6)
    s.paint(world, 'blue', 6.6, base=.05)
    land = {p for p in world if (p[0] - 12.5) ** 2 + (p[1] - 18.5) ** 2 < 8 or (p[0] - 18.5) ** 2 / 2 + (p[1] - 24) ** 2 < 8
            or (p[0] - 11) ** 2 + (p[1] - 25) ** 2 < 2.5}
    s.paint(land, 'green', 6.6, shape=world, base=.05, shadow=False)
    s.mark([(11, 17), (12, 17), (11, 18), (10, 19)], 'white', 5)
    s.mark([(19, 26), (20, 25), (21, 24)], 'teal', 4)                                                        # the far rim's light
    for a in (45, 135, 225, 315):                                                                            # the claws
        x, y = c[0] + 7.4 * math.cos(math.radians(a)), c[1] + 7.4 * math.sin(math.radians(a))
        s.paint(disc(x, y, 1.7), 'gold', 1.2)
    for a in (0, 180):
        s.paint(disc(c[0] + 9.2 * math.cos(math.radians(a)), c[1], 1.6), 'teal', 1.4, base=.12)
    s.spark(27, 12, 'teal')
    s.spark(4, 13, 'teal')
    return s


SPRITES = {   # id: (drawing, fit)
    'throne_of_ruin': (throne_of_ruin, .87), 'godless': (godless, .92), 'unwritten_fate': (unwritten_fate, 1.0),
    'the_silent_extinction': (the_silent_extinction, .97), 'nothing_remains': (nothing_remains, .92),
    'the_final_equation': (the_final_equation, 1.0), 'grace_beyond_death': (grace_beyond_death, .93),
    'the_perfect_lie': (the_perfect_lie, .92), 'the_last_crown': (the_last_crown, .92),
    'heart_of_the_world': (heart_of_the_world, .93),
}

if __name__ == '__main__':
    out = sys.argv[1]
    os.makedirs(out, exist_ok=True)
    for name, (fn, K) in SPRITES.items():
        fn().image().save(os.path.join(out, name + '.png'))
    print(len(SPRITES), 'sprites ->', out)
