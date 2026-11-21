#!/usr/bin/env python3
"""Gear v4 weapons: 16 weapon types, each with its own set of silhouettes. Long weapons lie on the diagonal, tip top-right."""
import math

from gear_core import (A, L, Sprite, bez, blade, curve, disc, fx, grip, guard, knob, line, local, m, poly, rect, ring, shaft, taper)


# ------------------------------------------------------------------------------------------------- swords
def greatsword(o):
    s = Sprite()
    c = A(8.5)
    grip(s, A(0.5), c, o.get('grip', 'leather'), 2.8, o.get('wrap'))
    knob(s, A(0.5), o.get('trim', 'iron'), 2.3, o.get('gem'))
    v = o.get('var', 'plain')
    f = {'plain': taper(2.9, 2.3), 'broad': taper(3.8, 3.2, .86), 'flame': taper(2.8, 1.9, .8, wave=.9, freq=3.5),
         'saw': taper(3.2, 2.6, .84, saw=1.1, teeth=9), 'notch': taper(3.0, 2.5, .86, saw=1.3, teeth=4),
         'slim': taper(2.4, 1.7, .76)}[v]
    info = blade(s, c, .5, 26, f, o.get('metal', 'steel'), 1.5, ridge=o.get('ridge', True), edge=o.get('edge'), glow=o.get('core'), lift=o.get('lift', .2))
    if o.get('crack'):
        s.mark(line(L(c, 9, -1.5), L(c, 12, .8)) | line(L(c, 12, .8), L(c, 16, -1)) | line(L(c, 16, -1), L(c, 20, .6)), o['crack'], 4)
    if o.get('runes'):
        for a in (5, 9, 13, 17):
            s.mark({tuple(map(int, m.T(L(c, a, 0))))}, o['runes'], 5)
    guard(s, c, o.get('trim', 'iron'), o.get('guard', 'bar'), o.get('gh', 6.5), o.get('gem'))
    if o.get('extra'):
        o['extra'](s)
    fx(s, o.get('fx', ()))
    return s


def katana(o):
    s = Sprite()
    c = A(8.5)
    grip(s, A(0.5), c, o.get('grip', 'ebony'), 2.8, o.get('wrap', 'white'), 3)
    knob(s, A(0.5), o.get('trim', 'iron'), 1.8)
    f = taper(1.9, 1.5, .88, bend=o.get('bend', 3.2))
    if o.get('snap'):
        f = (lambda g: lambda a, t: (9, -9) if t > .72 + .05 * math.sin(a * 5) else g(a, t))(f)
    blade(s, c, .8, 25, f, o.get('metal', 'steel'), 1.1, edge=o.get('edge', 'white'), spine=o.get('spine', 'iron'), glow=o.get('core'))
    guard(s, c, o.get('trim', 'iron'), o.get('guard', 'disc'), o.get('gh', 5.5), o.get('gem'))
    if o.get('extra'):
        o['extra'](s)
    fx(s, o.get('fx', ()))
    return s


def dagger(o):
    s = Sprite()
    c = A(11)
    grip(s, A(2), c, o.get('grip', 'leather'), 3.2, o.get('wrap'))
    knob(s, A(2), o.get('trim', 'iron'), 2.2, o.get('pgem'))
    v = o.get('var', 'plain')
    f = {'plain': taper(3.1, 2.1, .68), 'shiv': taper(2.3, 1.6, .55), 'fang': taper(3.2, 1.9, .5, bend=3.4),
         'talon': taper(3.3, 1.5, .45, bend=6), 'rend': taper(3.2, 2.2, .7, saw=1.2, teeth=6), 'needle': taper(2.4, 1.4, .6)}[v]
    blade(s, c, .8, 21, f, o.get('metal', 'steel'), 1.5, ridge=o.get('ridge', True), edge=o.get('edge'), glow=o.get('core'))
    if v != 'shiv':
        guard(s, c, o.get('trim', 'iron'), o.get('guard', 'bar'), o.get('gh', 5), o.get('gem'))
    else:
        s.paint(local(c, [(-1.5, -2.3), (1, -2.3), (1, 2.3), (-1.5, 2.3)]), o.get('trim', 'leather'), 1)
    if o.get('extra'):
        o['extra'](s)
    fx(s, o.get('fx', ()))
    return s


def rapier(o):
    s = Sprite()
    c = A(9.5)
    grip(s, A(1), c, o.get('grip', 'ebony'), 2.4, o.get('wrap', 'gold'), 2)
    blade(s, c, .6, 26, taper(1.5, .8, .8), o.get('metal', 'white'), 1, ridge=False, edge=o.get('edge'), glow=o.get('core'))
    t = o.get('trim', 'steel')
    s.paint(curve(L(c, 0, 5.5), L(c, -4, 7.5), A(1, 1.5), 1.4), t, 1)                                       # knuckle bow
    s.paint(curve(L(c, 0, -6.5), L(c, 1, 0), L(c, 0, 6.5), 1.7), t, 1.1)                                    # quillons
    s.paint(disc(*L(c, 0, -6.8), 1.3) | disc(*L(c, 0, 6.8), 1.3), t, 1)
    v = o.get('var', 'cup')
    if v == 'cup':
        s.paint(disc(c[0], c[1], 3.7), t, 1.9)
        s.paint(disc(c[0] + .3, c[1] - .3, 2.5), o.get('cup', t), 2, base=.05)
    elif v == 'shell':
        s.paint(local(c, [(1.6, -5), (-2.6, -4), (-3.2, 0), (-2.6, 4), (1.6, 5), (2.8, 0)]), t, 2)
        for b in (-2.4, 0, 2.4):
            s.shift(line(L(c, 1.8, b), L(c, -2.2, b * .8)), -2)
    elif v == 'thorn':
        s.paint(disc(c[0], c[1], 3), t, 1.6)
        for q in ((2.5, -4.5), (-2.5, -4.5), (2.5, 4.5), (-2.5, 4.5)):
            s.paint(local(c, [(0, -1), (q[0], q[1]), (0, 1)]), t, .9)
    elif v == 'wisp':
        s.paint(ring(c[0], c[1], 2, 4), t, 1.2)
        s.paint(disc(c[0], c[1], 1.8), o.get('cup', 'aqua'), 1.5, base=.2)
    if o.get('gem'):
        s.paint(disc(c[0], c[1], 1.5), o['gem'], 1.2, base=.22)
    knob(s, A(1), t, 2.1, o.get('pgem'))
    if o.get('extra'):
        o['extra'](s)
    fx(s, o.get('fx', ()))
    return s


def sabre(o):
    s = Sprite()
    c = A(9)
    grip(s, A(1), c, o.get('grip', 'leather'), 2.8, o.get('wrap'))
    def f(a, t):
        h = 1.5 + 1.6 * math.sin(min(t / .78, 1) * math.pi / 2)
        if t > .78:
            h *= (1 - t) / .22
        off = -o.get('bend', 5.2) * t * t
        return off - h * .55, off + h
    blade(s, c, .8, 24.5, f, o.get('metal', 'steel'), 1.4, edge=o.get('edge'), spine=o.get('spine'), glow=o.get('core'), lift=o.get('lift', .2))
    t = o.get('trim', 'iron')
    s.paint(curve(L(c, 0, 5), L(c, -4, 7), A(1, 1.6), 1.5), t, 1)                                           # D guard
    guard(s, c, t, o.get('guard', 'flare'), o.get('gh', 4.5), o.get('gem'))
    knob(s, A(1), t, 2, o.get('pgem'))
    if o.get('extra'):
        o['extra'](s)
    fx(s, o.get('fx', ()))
    return s


def kris(o):
    s = Sprite()
    c = A(9.5)
    grip(s, A(1), c, o.get('grip', 'dark'), 3, o.get('wrap'))
    knob(s, A(1), o.get('trim', 'bronze'), 2.2, o.get('pgem'))
    def f(a, t):
        h = (3.0 - 1.5 * t) * (1 if t < .85 else (1 - t) / .15)
        off = o.get('amp', 1.0) * math.sin(t * o.get('waves', 2.5) * math.pi * 2)
        return off - h, off + h
    blade(s, c, .6, 23.5, f, o.get('metal', 'steel'), 1.3, ridge=True, edge=o.get('edge'), glow=o.get('core'))
    s.paint(local(c, [(-1.5, -5.5), (1.2, -4.2), (2, 3.2), (.2, 5.2), (-1.5, 3)]), o.get('trim', 'bronze'), 1.4)     # the asymmetric ganja
    if o.get('gem'):
        s.paint(disc(c[0], c[1], 1.5), o['gem'], 1.2, base=.22)
    if o.get('extra'):
        o['extra'](s)
    fx(s, o.get('fx', ()))
    return s


# ------------------------------------------------------------------------------------------------- axes + hammers
def axe(o):
    s = Sprite()
    c = A(25)
    grip(s, A(1), A(29.5), o.get('haft', 'oak'), 2.7)
    for a in o.get('bands', ()):
        s.paint(shaft(*A(a - .7), *A(a + .7), 3.3), o.get('trim', 'iron'), 1)
    knob(s, A(.8), o.get('trim', 'iron'), 2, o.get('pgem'))
    v = o.get('var', 'hatchet')
    H = {'hatchet': [(-2.2, 0), (2.2, 0), (3.2, 4), (7, 8.5), (3.5, 10.6), (0, 11.2), (-3.5, 10.6), (-7, 8.5), (-3.2, 4)],
         'beard': [(-2, 0), (2.4, 0), (3.2, 3.5), (6.4, 7), (4.4, 10), (0, 10.8), (-5, 10.6), (-11, 9.5), (-7.5, 6), (-3, 3)],
         'cleaver': [(-3, 0), (6.5, 0), (7.2, 10.4), (3, 11), (-2, 11), (-7, 10.4), (-5, 4)],
         'crescent': [(-2, 0), (2, 0), (5, 2), (9.5, 3.5), (10, 8), (6, 12), (0, 13), (-6, 12), (-10, 8), (-9.5, 3.5), (-5, 2)],
         'wing': [(-2, 0), (2.2, 0), (6, 2.5), (10.5, 3), (8.5, 6), (10, 8.5), (6.5, 9.8), (7, 12), (2, 11.8), (-1, 12.6), (-5, 10.5), (-7.5, 7), (-3, 3)]}
    def bit(q, scale=1.0):
        pts = [(a, q * b * scale) for a, b in H[v]]
        mask = local(c, pts)
        ramp = o.get('metal', 'steel')
        s.paint(mask, ramp, 2.2, base=.04, bands=(.8, .8, .05))
        honed = {p for p in mask if ((p[0] + q, p[1] + q) not in mask)}
        s.mark(honed, o.get('edge', ramp), 5)
        s.mark({p for p in mask - honed if (p[0] + 2 * q, p[1] + 2 * q) not in mask}, o.get('edge', ramp), 4)
        return mask
    main = bit(1)
    if o.get('double'):
        bit(-1, o.get('dscale', .85))
    elif o.get('spike', True):
        s.paint(local(c, [(-2, 0), (2, 0), (.4, -6.5), (-.4, -6.5)]), o.get('metal', 'steel'), 1.2)
    if o.get('chip'):
        s.erase([L(c, q, 11) for q in (-3, -2.2, 4)] + [L(c, 5.5, 8.8)])
    if o.get('rust'):
        s.shift({p for p in main if (p[0] * 7 + p[1] * 3) % 6 == 0}, -2)
    if o.get('crack'):
        s.mark(line(L(c, 1, 3), L(c, -1.5, 6)) | line(L(c, -1.5, 6), L(c, 1.5, 9)), o['crack'], 4)
    if o.get('core'):
        s.mark(line(L(c, -4, 6), L(c, 4, 6)), o['core'], 5)
    s.paint(local(c, [(-3.4, -2.1), (3.4, -2.1), (3.4, 2.1), (-3.4, 2.1)]), o.get('trim', 'iron'), 1.3)
    s.paint(local(L(c, 4.8, 0), [(-1.4, -1.7), (2.6, 0), (-1.4, 1.7)]), o.get('trim', 'iron'), 1)
    if o.get('gem'):
        s.paint(disc(c[0], c[1], 1.6), o['gem'], 1.3, base=.22)
    if o.get('extra'):
        o['extra'](s)
    fx(s, o.get('fx', ()))
    return s


def hammer(o):
    s = Sprite()
    c = A(24)
    grip(s, A(1), A(20), o.get('haft', 'oak'), 2.8)
    knob(s, A(.8), o.get('trim', 'iron'), 2.2, o.get('pgem'))
    for a in o.get('bands', ()):
        s.paint(shaft(*A(a - .7), *A(a + .7), 3.4), o.get('trim', 'iron'), 1)
    t, mt = o.get('trim', 'iron'), o.get('metal', 'steel')
    v = o.get('var', 'block')
    if v == 'mallet':
        s.paint(local(c, [(-5, -9), (5, -9), (5, 9), (-5, 9)]), mt, 2.8)
        for b in (-8.5, -5.5, 5.5, 8.5):
            s.paint(local(c, [(-5.6, b - .9), (5.6, b - .9), (5.6, b + .9), (-5.6, b + .9)]), t, 1)
        s.shift({p for p in local(c, [(-5, -4), (5, -4), (5, 4), (-5, 4)]) if (p[0] + p[1]) % 4 == 0}, -1)
    elif v == 'block':
        s.paint(local(c, [(-5, -7), (5, -7), (5, 7), (-5, 7)]), mt, 2.8, bands=(.7, .7, .05))
        for q in (-1, 1):
            s.paint(local(c, [(-6.4, q * 7), (6.4, q * 7), (5.4, q * 10.5), (-5.4, q * 10.5)]), t, 1.7)
        s.paint(local(c, [(-5.4, -1.4), (5.4, -1.4), (5.4, 1.4), (-5.4, 1.4)]), t, 1.2)
    elif v == 'earth':
        s.paint(local(c, [(-5, -10), (-2, -11), (3, -10), (6, -8), (6.5, -2), (5.4, 4), (6, 9), (2, 11), (-3, 10), (-6, 8), (-5.4, 1), (-6.5, -5)]), mt, 2.8)
        s.mark(line(L(c, 4, -7), L(c, 0, -3)) | line(L(c, 0, -3), L(c, 2, 1)) | line(L(c, 2, 1), L(c, -3, 5)) | line(L(c, -3, 5), L(c, -1, 9)), o.get('crack', 'amber'), 5)
    elif v == 'mount':
        s.paint(local(c, [(-5, -10.5), (2, -10.5), (6, -6), (4, -3.5), (9, 0), (4, 3.5), (6, 6), (2, 10.5), (-5, 10.5)]), mt, 2.8)
        s.mark(line(L(c, 8, 0), L(c, 5.5, -1.5)) | line(L(c, 8, 0), L(c, 5.5, 1.5)) | line(L(c, 5.2, -6), L(c, 3.6, -7)) | line(L(c, 5.2, 6), L(c, 3.6, 7)), 'white', 5)
        s.paint(local(c, [(-5.8, -10.5), (-3.6, -10.5), (-3.6, 10.5), (-5.8, 10.5)]), t, 1.1)
    elif v == 'titan':
        s.paint(local(c, [(-6, -8), (6, -8), (6, 8), (-6, 8)]), mt, 3, bands=(.7, .7, .06))
        for q in (-1, 1):
            s.paint(local(c, [(-7.5, q * 8), (7.5, q * 8), (6.2, q * 12), (-6.2, q * 12)]), t, 2)
        s.paint(local(c, [(-6, -3), (6, -3), (6, 3), (-6, 3)]), t, 1.4)
    if o.get('gem'):
        s.paint(local(c, [(3.2, 0), (0, -3), (-3.2, 0), (0, 3)]), o['gem'], 2.2, base=.1)
    s.paint(local(c, [(-8.6, -2.4), (-5, -3), (-5, 3), (-8.6, 2.4)]), t, 1.3)                               # collar
    if o.get('extra'):
        o['extra'](s)
    fx(s, o.get('fx', ()))
    return s


# ------------------------------------------------------------------------------------------------- bows
def bow(o):
    s = Sprite()
    v = o.get('var', 'long')
    p0, c, p1 = {'short': ((6.5, 25), (7, 7.5), (25, 6.5)), 'long': ((5, 27), (5.5, 5.5), (27, 5)),
                 'deep': ((7, 26), (2.5, 2.5), (26, 7))}[o.get('shape', 'long' if v != 'short' else 'short')]
    st = o.get('string', 'white')
    s.paint(shaft(p0[0] - .5, p0[1] + .5, p1[0] + .5, p1[1] - .5, 1.25), st, 1, base=.9, shadow=False)
    lm = o.get('limb', 'oak')
    s.paint(curve(p0, c, p1, 1.8, 1.8, o.get('thick', 3.6)), lm, 1.9, bands=(.6, .6, .06))
    if o.get('recurve', True):
        s.paint(curve(p0, (p0[0] - 2, p0[1] + 2), (p0[0] + 1, p0[1] + 3.2), 2.1, 1), o.get('tip', lm), 1.1)
        s.paint(curve(p1, (p1[0] + 2, p1[1] - 2), (p1[0] + 3.2, p1[1] + 1), 2.1, 1), o.get('tip', lm), 1.1)
    if o.get('trimline'):
        s.paint(curve(bez(p0, c, p1, .08), c, bez(p0, c, p1, .92), .9), o['trimline'], .8)
    for t in o.get('runes', ()):
        q = bez(p0, c, p1, t)
        s.mark({tuple(map(int, m.T(q)))}, o.get('rune', 'gold'), 5)
    if v == 'thorn':
        for t in (.16, .3, .7, .84):
            x, y = bez(p0, c, p1, t)
            s.paint(poly([(x - 1, y - 1), (x - 4, y - 1.5), (x - 1, y + 1)]) | poly([(x - 1, y - 1), (x - 1.5, y - 4), (x + 1, y - 1)]), o.get('spur', 'moss'), .9)
    elif v == 'wing':
        for t, ln in ((.14, 4), (.26, 6), (.38, 7), (.62, 7), (.74, 6), (.86, 4)):
            x, y = bez(p0, c, p1, t)
            s.paint(poly([(x + 1, y + 1), (x - ln * .75, y - ln * .15), (x - ln * .35, y - ln * .75), (x + 1, y - 1)]), o.get('feather', 'white'), 1.1)
    elif v == 'storm':
        for t in (.2, .8):
            x, y = bez(p0, c, p1, t)
            s.mark(line((x - 1, y - 1), (x - 4, y - 2)) | line((x - 4, y - 2), (x - 3, y - 5)), 'sky', 5)
    elif v == 'horn':
        for q, d in ((p0, (-3, 3)), (p1, (3, -3))):
            s.paint(curve(q, (q[0] + d[0], q[1]), (q[0] + d[0], q[1] + d[1]), 2.4, .8), o.get('tip', 'bone'), 1)
    elif v == 'moon':
        s.paint(ring(9.5, 9.5, 3, 5) - disc(11.5, 11.5, 3.2), o.get('tip', 'moon'), 1.3)
    g = bez(p0, c, p1, .5)
    gr = o.get('grip', 'leather')
    s.paint(local(g, [(-4, -2.1), (4, -2.1), (4, 2.1), (-4, 2.1)]), gr, 1.5)
    s.shift({p for p in local(g, [(-4, -2.1), (4, -2.1), (4, 2.1), (-4, 2.1)]) if (p[0] - p[1]) % 3 == 0}, -1)
    for a in (-4.2, 3.2):
        s.paint(local(g, [(a, -2.6), (a + 1.2, -2.6), (a + 1.2, 2.6), (a, 2.6)]), o.get('trim', 'iron'), 1)
    if o.get('gem'):
        s.paint(disc(g[0], g[1], 2.1), o.get('trim', 'gold'), 1.3)
        s.paint(disc(g[0], g[1], 1.2), o['gem'], 1.2, base=.2)
    if o.get('arrow'):
        s.paint(shaft(11, 20, 25, 6, 1.2), o['arrow'], .8, base=.15)
        s.paint(local((26, 5), [(2.8, 0), (-1, -1.8), (-.2, 0), (-1, 1.8)]), o['arrow'], 1, base=.2)
    if o.get('extra'):
        o['extra'](s)
    fx(s, o.get('fx', ()))
    return s


def crossbow(o):
    s = Sprite()
    st, rl, lm, t = o.get('stock', 'oak'), o.get('rail', 'iron'), o.get('limb', 'steel'), o.get('trim', 'iron')
    s.paint(local((7.5, 24.5), [(-4.2, -2.6), (3.6, -2), (3.6, 2), (-4.2, 3.2)]), st, 2)
    s.paint(local((10.5, 21.5), [(-1.6, 1), (1.6, 1), (1.2, 6.5), (-1.2, 6.5)]), st, 1.3)
    s.paint(local((7.5, 24.5), [(-1.5, -2.6), (-.2, -2.6), (-.2, 3), (-1.5, 3)]), t, 1)
    s.paint(shaft(9, 23, 24.5, 7.5, 3), rl, 1.5, bands=(.8, .8, .07))
    c = (22.5, 9.5)
    v = o.get('var', 'plain')
    reach = {'plain': 12, 'short': 10, 'wide': 13.5}.get(o.get('span', 'plain'), 12)
    arm = lambda q: curve(L(c, 0, 0), L(c, 2.5, q * reach * .55), L(c, -3.5, q * reach), o.get('thick', 3.4), 1.4)
    s.paint(arm(-1) | arm(1), lm, 1.7, base=.08)
    if v == 'wing':
        for q in (-1, 1):
            for b, ln in ((4.5, 5), (7.5, 5.5), (10.5, 4.5)):
                s.paint(local(L(c, 1.5, q * b), [(-1, -1.3), (ln, q * 1.3 * -.2), (-1, 1.3)]), o.get('feather', 'white'), 1)
    elif v == 'star':
        for q in (-1, 1):
            x, y = L(c, -3.5, q * reach)
            s.paint(poly([(x, y - 3.4), (x + 1, y - 1), (x + 3.4, y), (x + 1, y + 1), (x, y + 3.4), (x - 1, y + 1), (x - 3.4, y), (x - 1, y - 1)]), o.get('tipc', 'gold'), 1.2)
    elif v == 'hook':
        for q in (-1, 1):
            x, y = L(c, -3.5, q * reach)
            s.paint(curve((x, y), L((x, y), -3, q * .8), L((x, y), -3.5, q * -2.5), 2, .8), o.get('tipc', 'bone'), 1)
    tips = L(c, -3.5, -reach), L(c, -3.5, reach)
    core = (15.5, 16.5)
    s.mark(line(tips[0], core) | line(tips[1], core), o.get('string', 'white'), 4)
    for q in tips:
        s.paint(disc(q[0], q[1], 1.4), t, 1.1)
    s.paint(disc(c[0], c[1], 2.3), t, 1.4)
    s.paint(local(core, [(-3, -2.8), (3, -2.8), (3, 2.8), (-3, 2.8)]), t, 1.5)
    if o.get('gem'):
        s.paint(disc(core[0], core[1], 1.8), o['gem'], 1.5, base=.2)
    b = o.get('bolt', 'steel')
    s.paint(shaft(19, 13, 27.5, 4.5, 1.4), b, 1, base=.1)
    s.paint(local((28, 4), [(2.6, 0), (-1.2, -1.9), (-.4, 0), (-1.2, 1.9)]), o.get('head', b), 1.2, base=.2)
    if o.get('extra'):
        o['extra'](s)
    fx(s, o.get('fx', ()))
    return s


# ------------------------------------------------------------------------------------------------- caster heads
def star4(c, big, small):
    x, y = c
    return poly([(x, y - big), (x + small, y - small), (x + big, y), (x + small, y + small), (x, y + big), (x - small, y + small), (x - big, y), (x - small, y - small)])


def starn(c, n, big, small, rot=-90.0):
    x, y = c
    pts = []
    for i in range(n * 2):
        r = big if i % 2 == 0 else small
        a = math.radians(rot + 180.0 * i / n)
        pts.append((x + r * math.cos(a), y + r * math.sin(a)))
    return poly(pts)


def flame(c, h, w):
    x, y = c
    return poly([(x + w * .1, y - h), (x + w * .75, y - h * .25), (x + w, y + h * .35), (x + w * .45, y + h), (x - w * .45, y + h), (x - w, y + h * .3), (x - w * .6, y - h * .1), (x - w * .25, y - h * .3)])


def head(s, c, kind, o):
    g, t = o.get('glow', 'gold'), o.get('trim', 'gold')
    x, y = c
    if kind == 'star':
        s.paint(star4(c, 6.5, 1.8), g, 2, base=.14)
        s.paint(disc(x, y, 1.6), 'white', 1.2, base=.4)
    elif kind == 'orb':
        for q in (-1, 1):
            s.paint(curve(L(c, -4.5, 0), L(c, -2, q * 6.5), L(c, 3.5, q * 4.5), 1.7, .8), t, 1)
        s.paint(disc(x, y, 3.7), g, 3.2, base=.06)
        s.mark({tuple(map(int, m.T((x - 1.3, y - 1.3))))}, 'white', 5)
    elif kind == 'leaf':
        for ang, ln in o.get('leaves', ((-100, 8), (-40, 8), (20, 7), (-160, 6))):
            r = math.radians(ang)
            tipx, tipy = x + ln * math.cos(r), y + ln * math.sin(r)
            nx, ny = -math.sin(r) * 2.3, math.cos(r) * 2.3
            s.paint(poly([(x, y), (x + (tipx - x) * .5 + nx, y + (tipy - y) * .5 + ny), (tipx, tipy), (x + (tipx - x) * .5 - nx, y + (tipy - y) * .5 - ny)]), g, 1.5, base=.06)
            s.shift(line((x, y), (tipx, tipy)), 1)
        s.paint(disc(x, y, 1.8), t, 1.2)
    elif kind == 'flame':
        s.paint(flame((x, y - 1), 7.5, 5), o.get('fl1', 'ember'), 3, base=.1)
        s.paint(flame((x, y + 1), 4.2, 2.8), o.get('fl2', 'amber'), 2.2, base=.25)
        s.paint(disc(x, y + 2.4, 1.2), 'white', 1, base=.5)
        s.paint(local(L(c, -5.5, 0), [(-2, -4), (1, -3), (1, 3), (-2, 4)]), t, 1.3)
    elif kind == 'crystal':
        k = L(c, 1, 0)
        sh = local(k, [(7.5, 0), (3, -3.2), (-3.5, -3), (-6, 0), (-3.5, 3), (3, 3.2)])
        s.paint(sh, g, 3, base=.05)
        s.shift(line(L(k, 7, 0), L(k, -5, 0)), 1)
        s.shift(line(L(k, 3, -3), L(k, -1, 0)) | line(L(k, 3, 3), L(k, -1, 0)), -1)
        for q in (-1, 1):
            j = L(c, -2.5, q * 5.5)
            s.paint(local(j, [(4, 0), (0, -1.6), (-2.5, 0), (0, 1.6)]), g, 1.3, base=.12)
        s.paint(local(L(c, -5.5, 0), [(-2, -5), (1.4, -4), (1.4, 4), (-2, 5)]), t, 1.3)
    elif kind == 'dawn':
        s.paint(disc(x, y, 5) & local(c, [(0, -8), (8, -8), (8, 8), (0, 8)]), g, 3, base=.16)
        for d in (-64, -32, 0, 32, 64):
            r = math.radians(d)
            pt = lambda rr, dd: L(c, rr * math.cos(r + dd), rr * math.sin(r + dd))
            s.paint(poly([pt(5.4, .2), pt(9.5, 0), pt(5.4, -.2)]), t, 1, base=.2)
        s.paint(local(c, [(-2, -8), (0, -8), (0, 8), (-2, 8)]), t, 1.2)
    elif kind == 'lantern':
        s.paint(local(c, [(-5, -4), (5, -4), (5, 4), (-5, 4)]), g, 3, base=.2)
        s.paint(disc(x, y, 1.8), 'white', 1.2, base=.5)
        for b in (-4, 0, 4):
            s.paint(local(c, [(-5, b - .6), (5, b - .6), (5, b + .6), (-5, b + .6)]), t, .9)
        s.paint(local(c, [(5, -5), (6.4, -5), (9, 0), (6.4, 5), (5, 5)]), t, 1.3)
        s.paint(local(c, [(-7.4, -3.5), (-5, -5), (-5, 5), (-7.4, 3.5)]), t, 1.3)
    elif kind == 'genesis':
        s.paint(star4(c, 9.5, 1.5), t, 1.2, base=.2)
        s.paint(ring(x, y, 5, 6.2), t, 1.1)
        s.paint(disc(x, y, 4), g, 3.2, base=.2)
        s.mark({tuple(map(int, m.T((x - 1.4, y - 1.4))))}, 'white', 5)
        for a in (-35, 145):
            r = math.radians(a)
            s.paint(disc(x + 5.6 * math.cos(r), y + 5.6 * math.sin(r), 1.3), o.get('gem', 'sky'), 1, base=.25)
    elif kind == 'firstlight':
        s.paint(star4(c, 10, 1.9), g, 1.5, base=.2)
        s.paint(starn(c, 4, 6.8, 1.5, -45), t, 1.2, base=.25)
        s.paint(ring(x, y, 4.3, 5.4), 'gold', 1)
        s.paint(disc(x, y, 3), 'white', 2.4, base=.35)
    elif kind == 'flake':
        for a in range(0, 180, 60):
            r = math.radians(a + 15)
            s.paint(shaft(x - 7 * math.cos(r), y - 7 * math.sin(r), x + 7 * math.cos(r), y + 7 * math.sin(r), 1.8), g, 1, base=.15)
            for q in (-1, 1):
                ex, ey = x + q * 4.5 * math.cos(r), y + q * 4.5 * math.sin(r)
                s.mark(line((ex, ey), (ex + q * 2 * math.cos(r + 1), ey + q * 2 * math.sin(r + 1))) | line((ex, ey), (ex + q * 2 * math.cos(r - 1), ey + q * 2 * math.sin(r - 1))), g, 5)
        s.paint(disc(x, y, 1.7), 'white', 1.2, base=.3)
    elif kind == 'rift':
        s.paint(ring(x, y, 3.8, 6.2), t, 1.5, bands=(.8, .8, .07))
        s.paint(disc(x, y, 3.9), 'ebony', 3)
        s.mark(line((x + 2.6, y - 3), (x + .3, y - .7)) | line((x + .3, y - .7), (x + 1.2, y + .8)) | line((x + 1.2, y + .8), (x - 2.3, y + 3)), g, 5)
        s.mote([(x - 7, y - 3), (x + 2, y - 8), (x + 8, y + 2)], g, 4)
    elif kind == 'bolt':
        s.paint(poly([(x + 3, y - 8), (x - 3.5, y + .5), (x, y + .5), (x - 3, y + 8), (x + 4.5, y - 1), (x + .8, y - 1)]), g, 1.6, base=.2)
        s.mote([(x - 6, y - 3), (x + 7, y + 3), (x - 5, y + 5)], g, 5)
    elif kind == 'sun':
        for a in range(0, 360, 45):
            r = math.radians(a)
            ln = 8 if a % 90 == 0 else 6
            s.paint(poly([(x + 2.2 * math.cos(r + .55), y + 2.2 * math.sin(r + .55)), (x + ln * math.cos(r), y + ln * math.sin(r)), (x + 2.2 * math.cos(r - .55), y + 2.2 * math.sin(r - .55))]), t, 1, base=.15)
        s.paint(disc(x, y, 3.7), g, 2.8, base=.14)
        s.paint(disc(x - .4, y - .4, 1.6), 'white', 1.2, base=.4)
    elif kind == 'blackstar':
        s.paint(starn(c, 8, 8, 2.8), 'ebony', 2)
        s.paint(starn(c, 4, 7, 1.6, -45), 'iron', 1.4, base=.2)
        s.paint(disc(x, y, 1.6), g, 1.3, base=.25)
    elif kind == 'moon':
        s.paint(disc(x, y, 7) - disc(x - 2.6, y - 2.6, 6), g, 2.2, base=.14)
        s.paint(star4((x - 2.4, y - 2.4), 3, .9), t, 1, base=.3)
    elif kind == 'wings':
        for q in (-1, 1):
            for a, b in ((-3, 6.5), (1, 9), (5, 9.5), (9, 7)):
                s.paint(curve(L(c, -2, q * 1), L(c, a * .3, q * b * .8), L(c, a, q * b), 3.4, 1), g, 1.2, base=.14)
                s.shift(line(L(c, a * .35, q * b * .55), L(c, a * .85, q * b * .95)), -1)
        s.paint(disc(x, y, 2.8), t, 2)
        s.paint(disc(x, y, 1.6), o.get('gem', 'teal'), 1.3, base=.22)
    elif kind == 'crook':
        s.paint(curve(L(c, -6, 0), L(c, 7, 0), L(c, 1.5, -6), 2.4, 1.6), t, 1.2)
        s.paint(disc(*L(c, 1.5, -6), 1.5), t, 1)
    elif kind == 'knob':
        s.paint(disc(x, y, 3.8), t, 3, bands=(.7, .7, .06))
        s.paint(disc(x + .3, y - .3, 2), g, 1.6, base=.16)
    elif kind == 'cross':
        s.paint(local(c, [(-6, -1.6), (1, -1.6), (1, -5.5), (3.6, -5.5), (3.6, -1.6), (8, -1.6), (8, 1.6), (3.6, 1.6), (3.6, 5.5), (1, 5.5), (1, 1.6), (-6, 1.6)]), t, 1.4)
        s.paint(disc(*L(c, 2.3, 0), 1.9), g, 1.5, base=.22)
    elif kind == 'twig':
        s.paint(curve(L(c, -5, 0), L(c, 0, 5), L(c, 7, 3.5), 2, .9), o.get('wood', 'oak'), 1)
        s.paint(curve(L(c, -5, 0), L(c, -1, -4), L(c, 5.5, -5), 1.8, .8), o.get('wood', 'oak'), 1)
        for a, b in ((7, 3.5), (5.5, -5), (1, 1)):
            q = L(c, a, b)
            s.paint(star4(q, 2.6, .9), g, 1.2, base=.2)
    elif kind == 'spire':
        for b, ln, w in ((0, 10, 2.6), (-3.5, 6, 2), (3.5, 7, 2)):
            k = L(c, -3, b)
            s.paint(local(k, [(-1, -w), (ln * .7, -w * .7), (ln, 0), (ln * .7, w * .7), (-1, w)]), g, 1.7, base=.1)
        s.paint(local(L(c, -5, 0), [(-1.6, -5.5), (1.4, -4.8), (1.4, 4.8), (-1.6, 5.5)]), t, 1.3)
    elif kind == 'astral':
        s.paint(ring(x, y, 5.5, 6.9), t, 1.2)
        s.paint(star4(c, 5.5, 1.4), g, 1.6, base=.2)
        for a in (-20, 100, 220):
            r = math.radians(a)
            s.paint(disc(x + 6.2 * math.cos(r), y + 6.2 * math.sin(r), 1.3), o.get('gem', 'violet'), 1.1, base=.2)
    elif kind == 'grasp':
        for b in (-5, 0, 5):
            k = L(c, -4, b * .5)
            s.paint(curve(k, L(c, 1, b * 1.5), L(c, 7, b * .55), 2, .8), t, 1)
        s.paint(disc(*L(c, 2.5, 0), 3), g, 2.6, base=.12)
    elif kind == 'cage':
        s.paint(flame((x, y), 6, 3.8), o.get('fl1', 'ember'), 2.5, base=.14)
        s.paint(flame((x, y + 1.5), 3, 2), o.get('fl2', 'amber'), 1.7, base=.3)
        for q in (-1, 1):
            s.paint(curve(L(c, -6, 0), L(c, 0, q * 8), L(c, 7, 0), 1.3), t, 1)
        s.paint(disc(*L(c, 7.2, 0), 1.5), t, 1.1)


def caster(o, a1=20, w=2.3):
    """Wand / staff / sceptre: a shaft on the diagonal with a head on top."""
    s = Sprite()
    c = A(a1 + o.get('neck', 5.5))
    w = o.get('w', w)
    if o.get('crooked'):
        s.paint(curve(A(1), A(a1 * .5, 1.6), A(a1 + 1), w, w * .8), o.get('wood', 'oak'), 1.2)
    else:
        grip(s, A(1), A(a1 + 1), o.get('wood', 'oak'), w)
    for a in o.get('bands', ()):
        s.paint(shaft(*A(a - .6), *A(a + .6), w + 1), o.get('trim', 'gold'), 1)
    if o.get('handle'):
        g = shaft(*A(1), *A(o['handle']), w + .6)
        s.paint(g, o.get('hcol', 'leather'), 1.2)
        s.shift({p for p in g if (p[0] - p[1]) % 3 == 0}, -2)
    knob(s, A(.8), o.get('trim', 'gold'), 1.9, o.get('pgem'))
    head(s, c, o.get('head', 'orb'), o)
    if o.get('extra'):
        o['extra'](s)
    fx(s, o.get('fx', ()))
    return s


def wand(o): return caster({'neck': 5, 'handle': 7, **o}, 18, 2.0)


def staff(o): return caster({'neck': 6, **o}, 21, 2.5)


def sceptre(o): return caster({'wood': o.get('rod', 'steel'), 'bands': (6, 12, 17), 'neck': 5.5, **o}, 19, 2.6)


def sickle(o):
    s = Sprite()
    grip(s, A(1), (13.5, 18.5), o.get('haft', 'oak'), 2.6, o.get('wrap'))
    knob(s, A(1), o.get('trim', 'iron'), 2, o.get('pgem'))
    outer, inner = disc(17, 13, 12.2), disc(13.4, 9.6, 10.2)
    hx, hy = m.T((20, 20))[0], m.T((13, 13))[0]
    x13, y19 = m.T((13, 13))[0], m.T((19, 19))[1]
    bl = {p for p in outer - inner if (p[0] + p[1] > 31 + (26 - 31) * m.K or p[0] > hx) and not (p[0] < x13 and p[1] < y19)}
    mt = o.get('metal', 'steel')
    s.paint(bl, mt, 2.2, base=.02)
    e = {p for p in bl if any((p[0] + a, p[1] + b) in inner for a, b in ((-1, 0), (0, -1), (-1, -1)))}
    s.mark(e, o.get('edge', mt), 5)
    s.mark({p for p in bl - e if any((p[0] + a, p[1] + b) in e for a, b in ((-1, 0), (0, -1)))}, o.get('edge', mt), 4)
    if o.get('grain'):
        s.shift({p for p in bl if (p[0] * 2 + p[1]) % 5 == 0}, -1)
    for t in o.get('notes', ()):
        a = math.radians(t)
        s.shift(line((17 + 8.6 * math.cos(a), 13 + 8.6 * math.sin(a)), (17 + 11 * math.cos(a), 13 + 11 * math.sin(a))), -2)
    if o.get('sprout'):
        for (x, y, a, b) in ((29, 18, 2, -2), (23, 26, 2, 2)):
            s.paint(poly([(x, y), (x + a, y - 1), (x + a + 1, y + b), (x, y + 1)]), o['sprout'], 1, base=.12)
    s.paint(disc(14, 18, 2.9), o.get('trim', 'iron'), 1.8)
    s.paint(disc(14, 18, 1.6), o.get('gem', o.get('trim', 'iron')), 1.4, base=.25)
    if o.get('extra'):
        o['extra'](s)
    fx(s, o.get('fx', ()))
    return s


def halberd(o):
    s = Sprite()
    c = A(23)
    grip(s, A(1), A(32), o.get('haft', 'oak'), 2.3)
    t, mt = o.get('trim', 'steel'), o.get('metal', 'steel')
    for a in o.get('bands', (8, 15)):
        s.paint(shaft(*A(a - .6), *A(a + .6), 3), t, 1)
    knob(s, A(.8), t, 1.9, o.get('pgem'))
    tip = local(c, [(3.5, -2), (12, 0), (3.5, 2)])
    s.paint(tip, mt, 1.4, base=.15)
    v = o.get('var', 'axe')
    Ax = {'axe': [(-3, 0), (3, 0), (4.5, 3.5), (8, 6.5), (4.5, 10.4), (0, 11), (-5, 10.4), (-8, 6.5), (-4.5, 3.5)],
          'sun': [(-3, 0), (3, 0), (4, 2), (9, 3), (6, 5.5), (8, 9.5), (3.5, 8), (0, 12), (-3.5, 8), (-8, 9.5), (-6, 5.5), (-9, 3), (-4, 2)],
          'moon': [(-3, 0), (3, 0), (6, 1.5), (10, 2), (10, 8), (5.5, 11.5), (0, 12), (-5.5, 11.5), (-10, 8), (-10, 2), (-6, 1.5)],
          'wing': [(-3, 0), (3, 0), (9, 2.5), (8, 5), (10.5, 7), (6.5, 8.5), (7, 11), (2, 11), (-1, 12.5), (-5, 10), (-8, 6), (-4, 3)]}[v]
    bl = local(c, Ax)
    s.paint(bl, mt, 2.2, bands=(.8, .8, .05))
    honed = {p for p in bl if (p[0] + 1, p[1] + 1) not in bl}
    if v == 'sun':
        s.paint(disc(*L(c, 0, 4), 2.8), o.get('edge', 'amber'), 2, base=.2)
    else:
        s.mark(honed, o.get('edge', mt), 5)
        s.mark({p for p in bl - honed if (p[0] + 2, p[1] + 2) not in bl}, o.get('edge', mt), 4)
    s.paint(local(c, [(-2.4, 0), (2.4, 0), (.6, -7), (-.6, -7)]), mt, 1.2)                                  # back fluke
    s.paint(local(c, [(-3.5, -2), (3.5, -2), (3.5, 2), (-3.5, 2)]), t, 1.3)
    if o.get('gem'):
        s.paint(disc(c[0], c[1], 1.7), o['gem'], 1.3, base=.22)
    if o.get('tassel'):
        s.paint(curve(A(17, 1), A(13, 4), A(11, 6.5), 1.8, 1), o['tassel'], 1)
    if o.get('extra'):
        o['extra'](s)
    fx(s, o.get('fx', ()))
    return s


def grimoire(o):
    s = Sprite()
    cv, tr = o.get('cover', 'blue'), o.get('trim', 'gold')
    s.paint(rect(8, 26, 27, 29), 'page', 1)
    s.paint(rect(24, 5, 28, 28), 'page', 1)
    for y in range(6, 28, 2):
        s.shift([(x, y) for x in range(26, 29)], -1)
    s.paint(rect(4, 2, 25, 27), cv, 2.4, base=-.04)
    s.paint(rect(4, 2, 8, 27), o.get('spine', tr), 2.2, bands=(0, 1.1, .08))
    for y in (6, 14, 22):
        s.paint(rect(4, y, 8, y + 1), o.get('band', 'ruby'), 1)
    s.paint(rect(10, 4, 23, 25) - rect(11, 5, 22, 24), tr, 1)
    if o.get('corners', True):
        for (x, y) in ((10, 4), (23, 4), (10, 25), (23, 25)):
            s.paint(disc(x, y, 2), tr, 1.4)
    g, c = o.get('glow', 'white'), (16.5, 14.5)
    e = o.get('emblem', 'star')
    if e == 'star':
        s.paint(star4(c, 6, 1.6), g, 1.8, base=.2)
    elif e == 'moon':
        s.paint(disc(16.5, 14.5, 6) - disc(19, 12.5, 5), g, 2, base=.2)
        s.mark([(21, 9), (22, 13), (20, 19)], 'white', 5)
    elif e == 'bolt':
        s.paint(poly([(19, 7), (13, 15), (16, 15), (14, 22), (21, 13), (17.5, 13)]), g, 1.4, base=.2)
    elif e == 'rift':
        s.paint(ring(16.5, 14.5, 4.4, 6), tr, 1)
        s.paint(disc(16.5, 14.5, 4.4), 'ebony', 3)
        s.mark(line((19, 10), (16, 14)) | line((16, 14), (18, 15)) | line((18, 15), (14, 19)), g, 5)
    elif e == 'eye':
        s.paint(poly([(10.5, 14.5), (14, 11), (19, 11), (22.5, 14.5), (19, 18), (14, 18)]), 'page', 1.3)
        s.paint(disc(16.5, 14.5, 3), g, 2, base=.1)
        s.paint(disc(16.5, 14.5, 1.3), 'ebony', 1)
        s.mark([(15, 13)], 'white', 5)
    elif e == 'end':
        s.paint(ring(16.5, 14.5, 4.6, 6.2), tr, 1)
        s.mark(line((13, 11), (20, 18)) | line((20, 11), (13, 18)), g, 5)
    elif e == 'rune':
        s.paint(poly([(16.5, 8), (22, 14.5), (16.5, 21), (11, 14.5)]), tr, 1.2)
        s.paint(poly([(16.5, 10.5), (20, 14.5), (16.5, 18.5), (13, 14.5)]), g, 1.6, base=.2)
    if o.get('extra'):
        o['extra'](s)
    fx(s, o.get('fx', ()))
    return s
