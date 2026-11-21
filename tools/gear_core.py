#!/usr/bin/env python3
"""Shared parts for the gear v4 icons (Ett's brief, docs/spec/Gear_icon_redraw_ettlel_2026-11-18.md).
Built on mythic_art.py, the approved 10 Mythic samples: same 6-step ramps, volume shading, outline and top-left light."""
import math
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import mythic_art as m                                                                   # noqa: E402
from mythic_art import N, R, L, U, V, Sprite, bez, curve, disc, line, local, poly, rect, rgb, ring, shaft  # noqa: E402,F401

R.update({k: [rgb(c) for c in v] for k, v in {
    'copper':  ['#2a1208', '#5e2a12', '#8f4620', '#bf6d36', '#e3985c', '#fbd0a4'],
    'bronze':  ['#241606', '#4f3210', '#7c5218', '#a97a2a', '#cfa548', '#f2dc8e'],
    'rust':    ['#1e0e08', '#44200f', '#6e3517', '#945022', '#b5733c', '#cf9a62'],
    'oak':     ['#1d1007', '#3f2510', '#623b1a', '#855428', '#a8733e', '#c99a60'],
    'ash':     ['#26211c', '#544a40', '#7c7062', '#a39787', '#c6bcab', '#e6dfd0'],
    'pine':    ['#10160c', '#263019', '#3d4a25', '#596a33', '#7c8f48', '#a7b868'],
    'dark':    ['#0a0606', '#1c1110', '#2e1d1a', '#452d27', '#5f4136', '#80604f'],
    'crimson': ['#1c0208', '#470712', '#7c0d1c', '#b01a28', '#dc3a3a', '#ff9c88'],
    'ember':   ['#2a0a02', '#6a1c04', '#b03a06', '#ea6a10', '#ffa52e', '#ffe680'],
    'ice':     ['#0c2a3c', '#1d5a78', '#3c92b0', '#74c8dc', '#b4ecf2', '#f2feff'],
    'moon':    ['#161c34', '#343e66', '#5e6c9a', '#94a2c8', '#c8d2ea', '#f6f9ff'],
    'night':   ['#07081a', '#12143a', '#20235c', '#343a84', '#5560b0', '#8a98dc'],
    'shadow':  ['#08050e', '#170f26', '#291b40', '#3f2c5e', '#5a4480', '#8068a8'],
    'violet':  ['#180a34', '#3a1a72', '#5f30a8', '#8a52d6', '#b68af0', '#ecdcff'],
    'pink':    ['#30081e', '#6e1748', '#a82c74', '#dc55a0', '#f490c8', '#ffe2f2'],
    'lime':    ['#10240a', '#2a5212', '#4a861c', '#74ba2c', '#a8e24c', '#eaffa8'],
    'amber':   ['#2c1602', '#6a3a06', '#a8660c', '#e09a18', '#f8c848', '#fff2b0'],
    'stone':   ['#141416', '#2e2e32', '#4a4a50', '#6c6c72', '#92929a', '#bcbcc4'],
    'sand':    ['#2a2010', '#5c4a28', '#8c7444', '#b89c64', '#dcc48c', '#f6e8bc'],
    'wool':    ['#2a2a34', '#62626e', '#9a9aa6', '#c8c8d2', '#e8e8ee', '#ffffff'],
    'navy':    ['#060c20', '#0e1c46', '#183070', '#264a9c', '#4470c8', '#86a8ec'],
    'sky':     ['#0c2a52', '#1c5294', '#2f7cc8', '#58a8e8', '#98d0f6', '#e6f6ff'],
    'aqua':    ['#04282e', '#08565e', '#10888e', '#22bcbc', '#6ae8dc', '#e0fff8'],
    'moss':    ['#0e1a0a', '#1f3a14', '#325a1e', '#4c7e2c', '#70a444', '#a4cc6c'],
    'fur':     ['#17171a', '#35353a', '#55555c', '#7a7a82', '#a2a2aa', '#cdcdd4'],
    'hide':    ['#1c120a', '#3c2816', '#5c4024', '#7c5a36', '#9e7a50', '#c4a47a'],
    'straw':   ['#2c2008', '#5e4814', '#8e7224', '#bc9c3c', '#dcc264', '#f6e8a0'],
    'plum':    ['#14060f', '#2f1026', '#4c1a3e', '#6e2a5c', '#92447e', '#ba6ca4'],
}.items()})


def line(a, b):
    """mythic_art.line with half-up rounding: round() alternates on .5 coordinates and leaves gaps in long diagonals."""
    a, b = m.T(a), m.T(b)
    n = int(max(abs(b[0] - a[0]), abs(b[1] - a[1]))) or 1
    return {(math.floor(a[0] + (b[0] - a[0]) * i / n + .5), math.floor(a[1] + (b[1] - a[1]) * i / n + .5)) for i in range(n + 1)}


GLOW = {'ember', 'ice', 'violet', 'teal', 'lime', 'sky', 'aqua', 'amber', 'pink', 'gold', 'white', 'ruby', 'void', 'green', 'moon', 'blue'}


def A(a, b=0.0):
    """A point on the main diagonal: a along it from the bottom-left corner, b across it (+ = down-right)."""
    return L((3.5, 28.5), a, b)


def mir(mask): return {(N - 1 - x, y) for x, y in mask}


def prof(c, a0, a1, f):
    """Every pixel inside a blade profile. f(a, t) gives (lo, hi) across the weapon at distance a from c. -> {pixel: (t, b, lo, hi)}"""
    cx, cy = m.T(c)
    out = {}
    for x in range(N):
        for y in range(N):
            dx, dy = (x - cx) / m.K, (y - cy) / m.K
            a, b = dx * U[0] + dy * U[1], dx * V[0] + dy * V[1]
            if a0 <= a <= a1:
                t = (a - a0) / (a1 - a0)
                lo, hi = f(a, t)
                if lo <= b <= hi:
                    out[(x, y)] = (t, b, lo, hi)
    return out


def blade(s, c, a0, a1, f, ramp, r=1.4, ridge=False, edge=None, spine=None, glow=None, lift=.2):
    """A lit blade: bright upper face, darker lower face, honed edge (+b side), optional ridge, dark spine or glowing core."""
    info = prof(c, a0, a1, f)
    mask = set(info)
    up = {p for p, i in info.items() if i[1] < (i[2] + i[3]) / 2}
    s.paint(up, ramp, r, base=lift, shape=mask)
    s.paint(mask - up, ramp, r, base=-.06, shape=mask, shadow=False)
    for p, (t, b, lo, hi) in info.items():
        mid = (lo + hi) / 2
        if hi - b < .95:
            s.mark({p}, edge or ramp, 5 if edge or (p[0] + p[1]) % 5 else 4)
        elif lo and b - lo < .8 and spine:
            s.mark({p}, spine, 2)
        elif ridge and abs(b - mid) < .5:
            s.mark({p}, ramp, 5)
        elif glow and abs(b - mid) < .7 and t < .9:
            s.mark({p}, glow, 4 if int(t * 22) % 3 else 5)
    return info


def taper(h0, h1, tip=.82, bend=0.0, wave=0.0, freq=0.0, saw=0.0, teeth=0):
    """A blade profile: half-width h0 -> h1, pointed from t=tip, optional curve, wave or saw teeth on the edge."""
    def f(a, t):
        h = h0 + (h1 - h0) * t
        if t > tip:
            h *= max(0, (1 - t) / (1 - tip))
        o = -bend * t * t + wave * math.sin(t * freq * math.pi * 2)
        hi = o + h
        if teeth and t < tip and (t * teeth) % 1 < .45:
            hi -= saw
        return o - h, hi
    return f


def grip(s, a, b, ramp='leather', w=2.6, wrap=None, every=3):
    h = shaft(a[0], a[1], b[0], b[1], w)
    s.paint(h, ramp, 1.3)
    if wrap:
        s.mark({p for p in h if (p[0] - p[1]) % every == 0}, wrap, 3)
    else:
        s.shift({p for p in h if (p[0] - p[1]) % every == 0}, -2)
    return h


def knob(s, p, ramp='gold', r=2.0, gem=None):
    s.paint(disc(p[0], p[1], r), ramp, r * .8)
    if gem:
        s.paint(disc(p[0], p[1], max(.8, r - 1)), gem, 1.1, base=.2)


def guard(s, c, ramp, kind='bar', h=6.0, gem=None):
    if kind == 'bar':
        s.paint(local(c, [(-1.2, -h), (1.2, -h), (1.2, h), (-1.2, h)]), ramp, 1.2)
        for q in (-h, h):
            s.paint(disc(*L(c, 0, q), 1.5), ramp, 1.2)
    elif kind == 'down':
        for q in (-1, 1):
            s.paint(curve(L(c, .6, 0), L(c, 1.4, q * h * .7), L(c, -3.5, q * h), 2.6, 1.1), ramp, 1.2)
    elif kind == 'up':
        for q in (-1, 1):
            s.paint(curve(L(c, -.6, 0), L(c, -1.2, q * h * .7), L(c, 3.5, q * h), 2.6, 1.1), ramp, 1.2)
    elif kind == 'wing':
        for q in (-1, 1):
            s.paint(local(c, [(-1.4, 0), (1.5, 0), (3.5, q * h * .6), (5, q * h * 1.1), (1.5, q * h * .95), (.4, q * h * 1.1), (-.8, q * h * .78), (-2, q * h * .8)]), ramp, 1.3)
            s.shift(line(L(c, 0, q * 2), L(c, 2.6, q * h * .8)), -2)
    elif kind == 'crown':
        s.paint(local(c, [(-1.3, -h), (1, -h), (3.4, -h - .8), (2.2, -h * .55), (4, -h * .3), (2.2, -1.4), (4.6, 0), (2.2, 1.4), (4, h * .3), (2.2, h * .55), (3.4, h + .8), (1, h), (-1.3, h)]), ramp, 1.3)
    elif kind == 'disc':
        s.paint(disc(c[0], c[1], h * .62), ramp, 1.7, bands=(.8, .8, .07))
        s.shift(ring(c[0], c[1], h * .62 - 1.2, h * .62 - .5), -1)
    elif kind == 'flare':
        s.paint(local(c, [(-1.2, -2), (-.4, -h), (2.4, -h - 1), (1, -2), (1, 2), (2.4, h + 1), (-.4, h), (-1.2, 2)]), ramp, 1.2)
    elif kind == 'spike':
        s.paint(local(c, [(-1.2, -2), (0, -h - 2), (1.2, -2), (1.2, 2), (0, h + 2), (-1.2, 2)]), ramp, 1.1)
    s.paint(local(c, [(-1.8, -2.1), (1.5, -2.1), (1.5, 2.1), (-1.8, 2.1)]), ramp, 1.3)
    if gem:
        s.paint(disc(c[0], c[1], 1.5), gem, 1.2, base=.22)


# ------------------------------------------------------------------------------------------------- small effects
def fx(s, kinds):
    for k in kinds:
        if k == 'sparks':
            s.spark(6, 8, 'gold'); s.spark(25, 25, 'gold')
        elif k == 'spark':
            s.spark(25, 25, 'gold')
        elif k == 'wspark':
            s.spark(7, 9, 'white'); s.spark(25, 26, 'white')
        elif k == 'embers':
            s.mote([(24, 24), (27, 21), (25, 28), (7, 8), (4, 12)], 'ember', 4); s.mote([(26, 25), (6, 11)], 'ember', 5)
        elif k == 'frost':
            s.spark(25, 25, 'ice'); s.mote([(7, 8), (5, 11), (28, 21), (22, 28)], 'ice', 5)
        elif k == 'void':
            s.mote([(7, 7), (5, 11), (26, 24), (23, 27), (28, 20)], 'void', 4); s.mote([(9, 5), (26, 27)], 'void', 5)
        elif k == 'souls':
            s.mote([(25, 24), (27, 21), (23, 27), (7, 9), (5, 6)], 'aqua', 4); s.mote([(26, 26)], 'aqua', 5)
        elif k == 'leaves':
            s.paint(poly([(24, 24), (27, 23), (28, 26), (25, 27)]), 'green', 1); s.mote([(6, 9), (8, 6)], 'green', 4)
        elif k == 'bolt':
            s.mark(line((27, 18), (24, 22)) | line((24, 22), (27, 23)) | line((27, 23), (24, 28)), 'sky', 5)
        elif k == 'gbolt':
            s.mark(line((27, 18), (24, 22)) | line((24, 22), (27, 23)) | line((27, 23), (24, 28)), 'gold', 5)
        elif k == 'poison':
            s.mote([(26, 22), (24, 25), (27, 27)], 'lime', 4); s.mote([(25, 28), (28, 24)], 'lime', 5)
        elif k == 'blood':
            s.mote([(27, 21), (25, 25), (27, 28)], 'crimson', 4); s.mote([(24, 28)], 'crimson', 5)
        elif k == 'moon':
            s.mark(ring(7, 8, 1.6, 3.4) - disc(8.6, 7, 2.6), 'moon', 5)
        elif k == 'stars':
            s.spark(7, 8, 'moon'); s.mote([(25, 24), (28, 27), (23, 28), (4, 12)], 'white', 5)
        elif k == 'holy':
            s.spark(7, 8, 'gold'); s.spark(26, 25, 'white'); s.mote([(23, 28), (4, 12), (28, 21)], 'gold', 5)
