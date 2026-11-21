#!/usr/bin/env python3
"""Gear v4 armour, front view: helms, chests, legs and boots, each with several constructions per material."""
import math

from gear_core import N, Sprite, curve, disc, fx, line, m, mir, poly, rect, ring, shaft  # noqa: F401
from gear_weapons import flame, star4, starn


def sym(mask): return mask | mir(mask)


def dots(pts): return [(x, y) for x, y in pts] + [(N - 1 - x, y) for x, y in pts]


def grow(mask):
    return {(x + a, y + b) for x, y in mask for a in (-1, 0, 1) for b in (-1, 0, 1)} - mask


def oval(cx, cy, rx, ry):
    (cx, cy), rx, ry = m.T((cx, cy)), rx * m.K, ry * m.K
    return {(x, y) for x in range(N) for y in range(N) if ((x - cx) / rx) ** 2 + ((y - cy) / ry) ** 2 <= 1}


def motif(s, kind, ramp, where):
    """A small mark repeated on both legs or both boots, so each line of armour keeps its own theme."""
    x, y0 = (10.5, 21) if where == 'leg' else (9, 11)
    if kind == 'flame':
        s.paint(sym(flame((x, y0 + 2), 4, 2.8)), 'ember', 1.8, base=.14)
        s.paint(sym(flame((x, y0 + 3), 2, 1.4)), 'amber', 1, base=.3)
    elif kind == 'ribs':
        for d in (-4, -1, 2):
            s.paint(sym(rect(x - 2.5, y0 + d, x + 2.5, y0 + d)), 'bone', .7, base=.2)
    elif kind == 'bolt':
        s.mark(sym(line((x + 1.5, y0 - 4), (x - 1, y0)) | line((x - 1, y0), (x + 1, y0)) | line((x + 1, y0), (x - 1.5, y0 + 4))), ramp, 5)
    elif kind == 'stars':
        s.mark(sym({(int(x - 2), y0 - 3), (int(x + 1), y0), (int(x - 1), y0 + 3)}), ramp, 5)
    elif kind == 'vine':
        s.mark(sym(line((x + 2, y0 - 5), (x - 2, y0 + 4))), 'lime', 3)
        s.mark(sym({(int(x + 2), y0 - 2), (int(x - 2), y0 + 1)}), 'lime', 5)
    elif kind == 'cracks':
        s.mark(sym(line((x - 2, y0 - 4), (x + 1, y0)) | line((x + 1, y0), (x - 1, y0 + 4))), 'ember', 5)


def seam(s, kind, ramp):
    """Item details laid over the finished piece."""
    if kind == 'cracks':
        s.mark(line((11, 12), (14, 16)) | line((14, 16), (12, 20)) | line((20, 11), (18, 15)) | line((18, 15), (21, 19)), ramp, 5)
    elif kind == 'bolt':
        s.mark(line((17, 10), (14, 16)) | line((14, 16), (17, 16)) | line((17, 16), (14, 22)), ramp, 5)
    elif kind == 'stars':
        s.mark([(11, 12), (20, 15), (13, 20), (19, 22), (16, 9)], ramp, 5)
    elif kind == 'runes':
        s.mark([(12, 13), (19, 13), (12, 17), (19, 17), (15, 11), (16, 21)], ramp, 5)
    elif kind == 'ribs':
        for y in (13, 16, 19, 22):
            s.shift(sym(line((9, y - 1), (14, y + 1))), -3)


# ------------------------------------------------------------------------------------------------- helms
def helm(o):
    s = Sprite()
    v, c, t, a, g = o['v'], o['m'], o.get('t', 'iron'), o.get('a', o.get('t', 'iron')), o.get('g')
    dk = o.get('dk', 'ebony')
    if v == 'cap':
        s.paint(poly([(7, 19), (7, 12), (10, 7), (15.5, 4.5), (21, 7), (24, 12), (24, 19)]), c, 6, bands=(.5, 0, .05))
        s.shift(line((15, 6), (15, 17)), 2)
        s.paint(poly([(3, 18), (28, 18), (29, 21), (25, 23), (6, 23), (2, 21)]), t, 1.6)
        s.shift([(x, 20) for x in range(5, 28, 4)], 2)
        s.paint(poly([(14, 22), (17, 22), (16.5, 28), (14.5, 28)]), c, 1.2)
    elif v == 'mask':
        s.paint(poly([(9, 5), (22, 5), (25, 10), (25, 19), (23, 24), (8, 24), (6, 19), (6, 10)]), c, 5)
        s.paint(rect(7, 12, 24, 15), dk, 1)
        s.mark([(10, 13), (11, 13), (20, 13), (21, 13)], o.get('eye', 'sand'), 5)
        s.paint(poly([(6, 18), (25, 18), (27, 27), (23, 29), (8, 29), (4, 27)]), t, 3)
        for y in (21, 24, 27):
            s.shift(line((6, y), (25, y - 1)), -2)
        s.paint(rect(6, 8, 25, 9), a, 1)
    elif v in ('hood', 'cowl'):
        hs = o.get('hs')
        shell = poly({'tall': [(15.5, .5), (19, 5), (24, 14), (26, 23), (23, 28), (8, 28), (5, 23), (7, 14), (12, 5)],
                      'flare': [(15.5, 3), (21, 5), (29, 12), (26, 17), (27, 24), (23, 28), (8, 28), (4, 24), (5, 17), (2, 12), (10, 5)],
                      'mantle': [(15.5, 3), (20, 6), (24, 13), (25, 20), (29, 26), (26, 29), (5, 29), (2, 26), (6, 20), (7, 13), (11, 6)]}.get(
            hs, [(15.5, 2.5), (20, 6), (25, 14), (26.5, 23), (23, 28), (8, 28), (4.5, 23), (6, 14), (11, 6)]))
        if hs == 'scarf':
            s.paint(poly([(22, 22), (31, 19), (30, 25), (26, 24), (28, 30), (22, 28)]), o.get('sc', t), 1.7)
        if hs == 'leaf':
            for x, y, r_ in ((5, 12, -1), (26, 12, 1), (10, 4, -1), (21, 4, 1), (15.5, 1, 0)):
                s.paint(poly([(x, y + 3), (x + r_ * 3 - 2, y), (x + r_ * 2, y - 3), (x + r_ * 3 + 2, y + 1)]), o.get('lf', 'green'), 1.2, base=.08)
        if v == 'cowl':
            for q in (poly([(7, 11), (5, 1), (13, 6)]),):
                s.paint(sym(q), c, 1.8)
                s.paint(sym(poly([(7.5, 8), (6.5, 4), (10.5, 6.5)])), o.get('ear', 'hide'), 1)
        s.paint(shell, c, 5, base=-.03)
        s.shift(sym(line((9, 12), (7, 24)) | line((12, 7), (10, 11))), -1)
        hole = poly([(15.5, 10), (20.5, 15), (21.5, 21), (18.5, 26), (12.5, 26), (9.5, 21), (10.5, 15)])
        s.paint(grow(hole) & shell, t, 1)
        s.paint(hole, dk, 1, base=-.3)
        s.mark(dots([(12, 19), (13, 19)]), o.get('eye', 'sand'), 5)
        s.paint(poly([(7, 27), (24, 27), (27, 30), (4, 30)]), c, 1.6)
        if v == 'cowl':
            for x in (6, 10, 14, 18, 22):
                s.paint(poly([(x, 29), (x + 3, 29), (x + 1.5, 31)]), c, 1)
        if g:
            s.paint(poly([(15.5, 26), (18, 28.5), (15.5, 31), (13, 28.5)]), t, 1.2)
            s.paint(disc(15.5, 28.5, 1.2), g, 1, base=.25)
        if o.get('tip'):
            s.paint(star4((15.5, 7.5), 3, .9), o['tip'], 1, base=.2)
        if o.get('brow') == 'eye':
            s.paint(poly([(11, 8), (15.5, 5), (20, 8), (15.5, 11)]), 'page', 1)
            s.paint(disc(15.5, 8, 1.7), o.get('eye', 'void'), 1.2, base=.2)
        elif o.get('brow') == 'bolt':
            s.mark(line((17, 3), (14, 7)) | line((14, 7), (17, 7)) | line((17, 7), (14, 11)), 'gold', 5)
    elif v == 'coif':
        s.paint(poly([(15.5, 3), (22, 5), (26, 11), (27, 21), (29, 28), (24, 30), (7, 30), (2, 28), (4, 21), (5, 11), (9, 5)]), c, 6)
        s.shift({(x, y) for x in range(N) for y in range(N) if (x + y * 2) % 4 == 0}, -1)
        face = poly([(10, 12), (21, 12), (21, 20), (18, 24), (13, 24), (10, 20)])
        s.paint(face, o.get('skin', 'sand'), 3.4)
        s.paint(grow(face), t, 1)
        s.paint(face, o.get('skin', 'sand'), 3.4, shadow=False)
        s.paint(rect(9, 13, 22, 15), dk, 1)
        s.mark(dots([(12, 14), (13, 14)]), o.get('eye', 'sky'), 5)
        s.paint(rect(5, 8, 26, 10), t, 1.2)
        s.paint(poly([(15.5, 5), (18, 9), (15.5, 13), (13, 9)]), g or t, 1.4, base=.12)
    elif v == 'visor':
        if o.get('crest'):
            s.paint(poly([(7, 9), (9, 2), (15.5, .5), (22, 2), (24, 9), (20, 6), (15.5, 5), (11, 6)]), o['crest'], 1.7)
        s.paint(poly([(8, 8), (11, 4), (20, 4), (23, 8), (25, 14), (25, 22), (22, 27), (18, 29), (13, 29), (9, 27), (6, 22), (6, 14)]), c, 7, bands=(.5, 0, .05))
        s.paint(rect(6, 11, 25, 12), t, 1)
        s.paint(rect(8, 14, 23, 16) | rect(14, 16, 17, 24), dk, 1, base=-.3)
        s.paint(rect(13, 13, 13, 25) | rect(18, 13, 18, 25), t, .8)
        for x in (9, 11, 20, 22):
            s.shift([(x, y) for y in (19, 21, 23)], -3)
        s.paint(poly([(9, 27), (22, 27), (20, 30), (11, 30)]), t, 1.2)
        if g:
            s.mark(dots([(10, 15), (11, 15)]), g, 5)
    elif v == 'crown' and o.get('cs') == 'flame':
        s.paint(poly([(7, 15), (24, 15), (26, 19), (5, 19)]), dk, 1)
        for x, h, w in ((5.5, 6, 3), (25.5, 6, 3), (10.5, 9, 3.4), (20.5, 9, 3.4), (15.5, 12, 4)):
            s.paint(flame((x, 22 - h), h, w), 'ember', 2, base=.1)
            s.paint(flame((x, 23 - h * .6), h * .55, w * .55), 'amber', 1.2, base=.3)
        s.paint(rect(4, 21, 27, 27), t, 1.6)
        for x in (8, 15.5, 23):
            s.paint(poly([(x, 22), (x + 2.2, 24), (x, 26.5), (x - 2.2, 24)]), c, 1.3)
    elif v == 'crown' and o.get('cs') == 'ash':
        s.paint(poly([(7, 15), (24, 15), (26, 19), (5, 19)]), dk, 1)
        s.paint(poly([(4, 26), (27, 26), (28, 15), (25, 18), (23.5, 10), (20.5, 16), (18, 7), (15, 14), (12.5, 9), (10, 15), (7.5, 12), (6, 18), (3, 14)]), c, 3.2)
        s.shift({(x, y) for x in range(N) for y in range(N) if (x * 5 + y * 3) % 7 == 0}, -1)
        s.mark(line((9, 24), (12, 18)) | line((12, 18), (11, 15)) | line((22, 24), (19, 18)) | line((19, 18), (20, 13)) | line((15, 25), (16, 19)), 'ember', 5)
        s.paint(rect(4, 23, 27, 27), t, 1.5)
        s.paint(poly([(15.5, 19), (18.5, 23), (15.5, 28), (12.5, 23)]), g or 'ember', 2, base=.14)
        s.mote([(6, 7), (11, 4), (21, 3), (26, 8)], 'ember', 4)
    elif v == 'crown' and o.get('cs') == 'tiara':
        s.paint(sym(curve((15.5, 25), (7, 25), (4, 16), 2.6, 1.2)), t, 1.2)
        s.paint(sym(poly([(9, 22), (10.5, 12), (12.5, 22)])), c, 1.5, base=.14)
        s.paint(sym(poly([(4.5, 18), (5, 10), (7.5, 19)])), c, 1.2, base=.14)
        s.paint(poly([(12.5, 25), (15.5, 3), (18.5, 25)]), c, 2, base=.16)
        s.paint(poly([(15.5, 14), (19, 20), (15.5, 27), (12, 20)]), t, 1.5)
        s.paint(poly([(15.5, 16), (17.6, 20), (15.5, 25), (13.4, 20)]), g or a, 1.6, base=.16)
        s.paint(sym(disc(10.5, 11, 1.3)) | sym(disc(5, 9, 1.1)), a, 1, base=.25)
        s.mote([(15, 1), (9, 5), (22, 5)], a, 5)
    elif v == 'crown' and o.get('cs') == 'rays':
        for d in range(-60, 61, 20):
            r = math.radians(d - 90)
            ln = 20 if d % 40 == 0 else 14
            x, y = 15.5 + ln * math.cos(r), 26 + ln * math.sin(r)
            s.paint(shaft(15.5 + 6 * math.cos(r), 26 + 6 * math.sin(r), x, y, 2.4, .9), c, 1, base=.16)
            if d % 40 == 0:
                s.paint(star4((x, y), 2.4, .7), a, 1, base=.25)
        s.paint(oval(15.5, 25, 12, 5), t, 2.4)
        s.paint(oval(15.5, 23.5, 8.5, 2.6), dk, 1)
        s.paint(poly([(15.5, 22), (19, 25.5), (15.5, 30), (12, 25.5)]), g or a, 2, base=.14)
    elif v == 'crown':
        s.paint(poly([(7, 13), (24, 13), (26, 18), (5, 18)]), dk, 1)
        s.paint(poly([(5, 25), (26, 25), (27.5, 12), (23, 18), (21.5, 6), (18, 15), (15.5, 3), (13, 15), (9.5, 6), (8, 18), (3.5, 12)]), c, 3.4, bands=(.7, 0, .06))
        if o.get('broken'):
            s.erase({(x, y) for x in range(19, 26) for y in range(2, 13)})
            s.mark(line((20, 13), (22, 16)) | line((22, 16), (20, 20)), dk, 1)
            s.mote([(23, 7), (25, 4), (21, 3)], c, 4)
        s.paint(rect(4, 22, 27, 27), t, 1.6)
        for x in (8, 23):
            s.paint(disc(x, 24.5, 1.5), a, 1.1, base=.2)
        s.paint(poly([(15.5, 10), (19, 16), (15.5, 22), (12, 16)]), g or a, 2.2, base=.08)
        for x, y in ((3.5, 12), (9.5, 6), (15.5, 3), (21.5, 6), (27.5, 12)):
            if not (o.get('broken') and x == 21.5):
                s.paint(disc(x, y, 1.5), a, 1, base=.25)
        if o.get('glowc'):
            s.mark(line((10, 20), (13, 18)) | line((21, 20), (18, 18)), o['glowc'], 5)
    elif v == 'visage':
        face = o.get('face', 'skull')
        s.paint(poly([(9, 3), (22, 3), (26, 8), (27, 16), (24, 24), (20, 29), (11, 29), (7, 24), (4, 16), (5, 8)]), c, 7, base=o.get('lift', 0), bands=(.45, 0, .05))
        if face == 'skull':
            s.paint(sym(poly([(8, 12), (14, 13), (13.5, 18), (9.5, 18)])), dk, 1, base=-.3)
            s.mark(dots([(11, 15), (12, 15)]), g or 'ruby', 5)
            s.paint(poly([(15.5, 18), (17.5, 22), (13.5, 22)]), dk, 1)
            for x in (11, 13, 15, 17, 19):
                s.paint(rect(x, 24, x, 28), dk, 1)
            s.paint(sym(poly([(5, 6), (1.5, 1), (10, 3.5)])), t, 1.4)
        elif face == 'titan':
            s.paint(rect(7, 10, 24, 11), t, 1)
            s.paint(sym(poly([(8, 13), (14, 13), (13, 16), (9, 16)])), dk, 1, base=-.3)
            s.mark(dots([(11, 14)]), g or 'gold', 5)
            s.paint(rect(14, 11, 17, 21), t, 1.1)
            s.paint(poly([(10, 22), (21, 22), (19, 28), (12, 28)]), dk, 1)
            s.paint(rect(10, 22, 21, 22), t, .8)
            for x in (12, 15, 18):
                s.paint(rect(x, 23, x, 27), t, .7)
            s.paint(poly([(15.5, 2), (18.5, 6), (15.5, 9.5), (12.5, 6)]), g or t, 1.4, base=.1)
        elif face == 'dragon':
            s.paint(sym(curve((8, 8), (2, 6), (3, 0), 3.4, 1)), t, 1.2)
            s.paint(sym(poly([(8, 13), (14, 15), (13, 18), (9, 17)])), dk, 1)
            s.mark(dots([(11, 16), (12, 16)]), g or 'amber', 5)
            s.paint(poly([(11, 19), (20, 19), (22, 25), (19, 30), (12, 30), (9, 25)]), t, 3)
            s.mark(dots([(13, 24), (13, 25)]), dk, 1)
            s.mark(line((10, 28), (21, 28)), dk, 2)
            for x in (11, 14, 17, 20):
                s.paint(poly([(x - 1, 29), (x + 1, 29), (x, 31)]), 'bone', .8)
            s.paint(poly([(15.5, 4), (17.5, 10), (15.5, 14), (13.5, 10)]), t, 1.3)
        elif face == 'serene':
            s.paint(sym(line((9, 14), (13, 13))), dk, 1)
            s.mark(dots([(11, 14)]), g or 'sky', 5)
            s.paint(line((15.5, 12), (15.5, 20)), t, .8, base=.2)
            s.paint(line((13, 24), (18, 24)), dk, 1)
            s.paint(poly([(15.5, 3), (19, 7), (15.5, 11), (12, 7)]), t, 1.5)
            s.paint(disc(15.5, 7, 1.3), g or 'sky', 1, base=.25)
            s.paint(sym(poly([(5, 8), (8, 9), (7, 22), (4.5, 16)])), t, 1.4)
        elif face == 'raven':
            s.paint(sym(poly([(8, 11), (14, 12), (13, 16), (9, 15)])), dk, 1, base=-.3)
            s.mark(dots([(11, 13), (12, 13)]), g or 'amber', 5)
            s.paint(poly([(11, 15), (20, 15), (18.5, 23), (15.5, 31), (12.5, 23)]), t, 2.6, base=.05)
            s.shift(line((15.5, 16), (15.5, 29)), 1)
            for x, y in ((5, 2), (9, 0), (22, 0), (26, 2)):
                s.paint(poly([(x - 1.6, 8), (x + 1.6, 8), (x, y)]), c, 1)
        elif face == 'stitch':
            s.paint(sym(disc(11, 14, 2.6)), dk, 1, base=-.3)
            s.mark(dots([(11, 14)]), g or 'lime', 5)
            s.mark(line((15.5, 4), (15.5, 27)), dk, 2)
            s.mark([(14, y) for y in range(6, 27, 4)] + [(17, y) for y in range(6, 27, 4)], dk, 2)
            s.paint(rect(11, 23, 20, 25), dk, 1)
            for x in range(12, 20, 2):
                s.paint(rect(x, 22, x, 26), t, .7)
        elif face == 'veil':
            s.paint(poly([(4, 15), (27, 15), (25, 26), (20, 30), (11, 30), (6, 26)]), t, 3)
            s.paint(sym(poly([(8, 9), (14, 11), (13, 13), (9, 13)])), dk, 1, base=-.3)
            s.mark(dots([(11, 11), (12, 12)]), g or 'violet', 5)
            for x in (9, 13, 18, 22):
                s.shift(line((x, 17), (x, 28)), -2)
    elif v == 'horned':
        for q, w in ((curve((9, 9), (0, 9), (2, 0), 4.2, 1), c),):
            s.paint(sym(q), w, 1.7)
            s.shift(sym(line((5, 7), (4, 3))), -2)
        s.paint(poly([(9, 6), (22, 6), (25, 13), (25, 22), (21, 28), (10, 28), (6, 22), (6, 13)]), c, 7)
        s.paint(sym(poly([(8, 12), (14, 13), (13, 18), (9, 17)])), dk, 1, base=-.3)
        s.mark(dots([(11, 15)]), g or 'ember', 5)
        s.paint(rect(14, 7, 17, 22), t, 1.2)
        for x in (10, 13, 16, 19):
            s.paint(poly([(x, 25), (x + 3, 25), (x + 1.5, 31)]), c, 1)
        for y in (9, 12):
            s.shift(line((13, y), (18, y)), -2)
    elif v == 'hat':
        s.paint(poly([(10, 14), (11, 6), (15.5, 3), (20, 6), (21, 14)]), c, 4)
        s.paint(poly([(1.5, 18), (8, 13), (23, 13), (29.5, 18), (24, 22), (7, 22)]), c, 3.5, base=.04)
        s.paint(poly([(9, 13), (22, 13), (22, 16), (9, 16)]), t, 1.3)
        if o.get('feather'):
            s.paint(curve((21, 13), (27, 9), (26, 1), 3.4, 1), o['feather'], 1.3)
            s.shift(line((22, 12), (26, 4)), 1)
        if o.get('goggles'):
            s.paint(sym(ring(11.5, 13.5, 1.7, 3.2)), o['goggles'], 1)
            s.paint(sym(disc(11.5, 13.5, 1.7)), g or 'aqua', 1.4, base=.2)
            s.paint(rect(14, 12, 17, 14), o['goggles'], .8)
    elif v == 'halo':
        s.paint(oval(15.5, 3.5, 10, 3) - oval(15.5, 3.5, 7, 1.4), o.get('halo', 'gold'), 1, base=.2)
        s.paint(poly([(9, 9), (22, 9), (25, 14), (25, 22), (21, 29), (10, 29), (6, 22), (6, 14)]), c, 7, base=o.get('lift', .08))
        s.paint(sym(poly([(9, 15), (13.5, 14.5), (13, 17), (9.5, 17)])), dk, 1)
        s.mark(dots([(11, 15), (12, 15)]), g or 'sky', 5)
        s.paint(rect(15, 12, 16, 21), t, .8)
        s.paint(line((13, 24), (18, 24)), dk, 1)
        s.paint(sym(poly([(6, 13), (10, 9), (13, 9), (8, 18), (6, 22)])), t, 1.6)
        s.paint(poly([(15.5, 9), (18, 12), (15.5, 15), (13, 12)]), g or t, 1.3, base=.15)
        if o.get('wings'):
            for y, ln in ((10, 7), (15, 6.5), (20, 5)):
                s.paint(sym(poly([(6, y - 2), (6 - ln, y - 1), (6, y + 2)])), o['wings'], 1.1, base=.15)
    if o.get('fxs'):
        fx(s, o['fxs'])
    return s


# ------------------------------------------------------------------------------------------------- chests
def shoulders(s, kind, c, t, a):
    if kind == 'round':
        s.paint(sym(poly([(10, 6), (5, 5), (1.5, 9), (1.5, 15), (5, 17), (8, 14)])), c, 3.4)
        s.paint(sym(rect(2, 14, 7, 15)), t, .9)
    elif kind == 'spike':
        s.paint(sym(poly([(10, 6), (5, 5), (1.5, 9), (1.5, 15), (5, 17), (8, 14)])), c, 3.4)
        s.paint(sym(poly([(2, 7), (.5, .5), (7, 5)])), t, 1.2)
        s.paint(sym(rect(2, 14, 7, 15)), t, .9)
    elif kind == 'fur':
        for x, y in ((3, 8), (6, 6), (2, 12), (5, 11), (9, 7)):
            s.paint(sym(disc(x, y, 3.2)), c, 2.2)
        s.shift(sym({(2, 7), (6, 5), (4, 11), (9, 6)}), 1)
    elif kind == 'bone':
        s.paint(sym(poly([(10, 6), (5, 5), (1.5, 9), (2, 15), (6, 16), (8, 13)])), c, 3)
        for x, y in ((2, 8), (4.5, 5), (8, 4)):
            s.paint(sym(poly([(x - 1.5, y + 2), (x + 1.5, y + 2), (x - 1, y - 5)])), a, 1)
    elif kind == 'wing':
        for y, ln in ((6, 9), (10, 8), (14, 6)):
            s.paint(sym(poly([(8, y - 2), (8 - ln, y - 3), (8 - ln * .55, y + 1), (8, y + 2.5)])), a, 1.3, base=.14)
        s.paint(sym(disc(7, 8, 3.2)), c, 2.4)
    elif kind == 'feather':
        for x, y in ((2, 7), (4, 10), (2.5, 13), (6, 6), (5.5, 13)):
            s.paint(sym(poly([(x + 3, y - 2), (x - 2, y), (x + 3, y + 2)])), c, 1.2)
            s.shift(sym(line((x + 3, y), (x - 1, y))), 1)
    elif kind == 'ember':
        s.paint(sym(poly([(10, 6), (5, 5), (1.5, 9), (1.5, 15), (5, 17), (8, 14)])), c, 3.4)
        s.paint(sym(flame((4, 8), 5, 3)), a, 1.8, base=.14)
    elif kind == 'cape':
        s.paint(sym(poly([(9, 5), (3, 8), (1, 14), (2, 27), (6, 29), (8, 16)])), a, 3)
        s.paint(sym(poly([(10, 6), (5, 5), (2.5, 8), (2.5, 13), (6, 14), (9, 11)])), c, 2.6)


def chest(o):
    s = Sprite()
    v, c, t, a, g = o['v'], o['m'], o.get('t', 'iron'), o.get('a', o.get('t', 'iron')), o.get('g')
    dk = o.get('dk', 'ebony')
    sh = o.get('sh')
    if sh == 'cape':
        shoulders(s, sh, c, t, a)
    long_ = v in ('robe', 'coat', 'shroud')
    if long_:
        s.paint(sym(poly([(8, 10), (3.5, 12), (1.5, 24), (5, 26), (8, 18)])), c, 2.4, base=-.04)
        s.paint(sym(rect(2, 23, 5, 25)), t, .9)
    torso = [(9, 6), (22, 6), (25, 11), (24, 20), (22, 26), (22, 30), (9, 30), (9, 26), (7, 20), (6, 11)]
    if v == 'robe':
        torso = [(9, 6), (22, 6), (25, 11), (24, 20), (27, 30), (4, 30), (7, 20), (6, 11)]
    elif v == 'shroud':
        torso = [(9, 6), (22, 6), (25, 11), (24, 20), (27, 27), (25, 31), (22, 27), (20, 31), (17, 27), (14, 31), (11, 27), (9, 31), (6, 27), (4, 31), (4, 27), (7, 20), (6, 11)]
    elif v == 'coat':
        torso = [(9, 6), (22, 6), (25, 11), (24, 20), (25.5, 30), (5.5, 30), (7, 20), (6, 11)]
    s.paint(poly(torso), c, 6.5, base=-.02, bands=(.5, 0, .04) if v in ('plate', 'aegis', 'mantle') else None)
    if v in ('plate', 'aegis', 'mantle'):
        s.shift(line((15.5, 10), (15.5, 26)), 2)
        s.shift(sym(line((9, 13), (14, 16))), -1)
        for y in (21, 24):
            s.shift(line((10, y), (21, y)), -2)
        s.paint(rect(9, 26, 22, 28), t, 1.2)
        s.paint(rect(14, 26, 17, 28), a, 1, base=.15)
        if o.get('rivets'):
            s.shift(dots([(10, 10), (11, 18), (10, 23)]), 2)
    elif v == 'vest':
        s.paint(poly([(13, 6), (18, 6), (17, 28), (14, 28)]), t, 1.2)
        for y in range(10, 27, 4):
            s.mark(line((13, y), (18, y + 2)) | line((18, y), (13, y + 2)), a, 4)
        s.paint(rect(9, 22, 22, 24), t, 1.1)
        s.paint(rect(14, 22, 17, 24), a, .9, base=.15)
        s.shift(sym(line((10, 11), (10, 20))), -1)
        if o.get('quilt'):
            s.shift({(x, y) for x in range(8, 24) for y in range(8, 30) if (x + y) % 5 == 0 or (x - y) % 5 == 0}, -1)
    elif v == 'coat':
        s.paint(rect(15, 7, 16, 30), dk, 1)
        s.paint(rect(8, 19, 23, 21), t, 1.2)
        s.paint(rect(13, 18, 18, 22), a, 1.1, base=.1)
        s.shift(dots([(13, 10), (13, 14), (13, 25), (13, 28)]), 2)
        s.paint(rect(6, 28, 25, 30), t, 1)
        if o.get('quilt'):
            s.shift({(x, y) for x in range(7, 25) for y in range(8, 19) if (x + y) % 4 == 0}, -1)
    elif v == 'robe':
        s.paint(poly([(13.5, 7), (17.5, 7), (19, 30), (12, 30)]), t, 1.6)
        s.paint(rect(8, 17, 23, 19), a, 1.2)
        s.paint(rect(5, 28, 26, 30), t, 1.1)
    elif v == 'shroud':
        s.paint(poly([(10, 6), (21, 6), (19, 14), (15.5, 17), (12, 14)]), t, 2)
        for x in (9, 13, 18, 22):
            s.shift(line((x, 16), (x - 1, 26)), -2)
        s.paint(rect(8, 19, 23, 20), a, 1)
    if sh and sh != 'cape':
        shoulders(s, sh, c if sh not in ('wing',) else t, t, a)
    s.paint(poly([(11, 3.5), (20, 3.5), (21, 7), (18, 11), (15.5, 12.5), (13, 11), (10, 7)]), t, 1.7)      # the collar
    s.paint(poly([(13, 4), (18, 4), (17, 8), (15.5, 9.5), (14, 8)]), dk, 1, base=-.2)
    if g:
        s.paint(poly([(15.5, 11), (19.5, 15.5), (15.5, 20), (11.5, 15.5)]), o.get('set', t), 1.5)
        s.paint(poly([(15.5, 12.8), (18, 15.5), (15.5, 18.2), (13, 15.5)]), g, 1.8, base=.12)
    if o.get('detail'):
        seam(s, *o['detail'])
    if o.get('fxs'):
        fx(s, o['fxs'])
    return s


# ------------------------------------------------------------------------------------------------- legs
def legs(o):
    s = Sprite()
    v, c, t, a, g = o.get('v', 'greaves'), o['m'], o.get('t', 'iron'), o.get('a', o.get('t', 'iron')), o.get('g')
    leg = [(7, 7), (15, 7), (15, 13), (13.5, 28), (8, 28), (6, 15)]
    if v == 'flare':
        leg = [(7, 7), (15, 7), (15, 13), (14, 29), (5.5, 29), (6, 15)]
    s.paint(sym(poly(leg)), c, 4, base=-.02, bands=(.5, 0, .04) if v in ('greaves', 'tasset') else None)
    s.paint(rect(15, 7, 16, 11), c, 1.5)
    if v in ('greaves', 'tasset'):
        s.paint(sym(poly([(8, 19), (13.5, 19), (13, 27), (9, 27)])), t, 2.2)
        s.shift(sym(line((11, 20), (11, 26))), 2)
        s.paint(sym(disc(11, 17, 3.1)), o.get('knee', a), 2, base=.08)
        s.shift(sym({(10, 16)}), 2)
        if g:
            s.paint(sym(disc(11, 17, 1.6)), g, 1.2, base=.25)
        s.shift(sym(line((8, 11), (14, 12))), -2)
    else:
        s.shift(sym(line((12, 8), (11, 26))), -1)
        s.shift(sym(line((9, 13), (13, 15)) | line((9, 21), (13, 22))), -1)
        s.paint(sym(rect(8, 26, 13, 28)), t, 1)
        if a != t:
            s.paint(sym(rect(7, 14, 7, 25)), a, .7)
        if g:
            s.paint(sym(disc(11, 17, 1.5)), g, 1.2, base=.2)
    if v == 'tasset':
        s.paint(sym(poly([(6.5, 7), (14, 7), (13.5, 15), (10, 17), (6.5, 14)])), t, 2.2)
        s.shift(sym(line((10, 8), (10, 15))), -2)
    motif(s, o.get('mot'), a, 'leg')
    s.paint(rect(6, 3, 25, 7), t, 1.6)
    s.paint(rect(13, 2, 18, 8), a, 1.3, base=.1)
    s.paint(disc(15.5, 5, 1.5), g or 'gold', 1, base=.25)
    if o.get('fxs'):
        fx(s, o['fxs'])
    return s


# ------------------------------------------------------------------------------------------------- boots
def boots(o):
    s = Sprite()
    v, c, t, a, g = o.get('v', 'leather'), o['m'], o.get('t', 'iron'), o.get('a', o.get('t', 'iron')), o.get('g')
    top = {'slipper': 14, 'sandal': 13}.get(v, 3)
    shaft_ = [(5.5, top), (13, top), (13, 20), (4.5, 20), (5, (top + 20) / 2)]
    foot = [(4.5, 18), (13, 18), (13.5, 26), (13.5, 28), (1, 28), (1, 25), (3.5, 21)]
    if v == 'slipper':
        foot = [(5.5, 17), (13, 17), (13.5, 28), (1.5, 28), (.5, 22), (3, 25), (5.5, 21)]
    if v == 'sandal':
        s.paint(sym(poly(shaft_) | poly(foot)), o.get('skin', 'sand'), 3.5)
        for y in (16, 20, 24):
            s.paint(sym(line((4.5, y + 1), (13, y - 1)) | line((4.5, y - 1), (13, y + 1))), c, .8)
        s.paint(sym(rect(.5, 27, 13.5, 29)), t, 1)
        s.paint(sym(rect(4.5, 12, 13.5, 14)), c, 1)
        if g:
            s.paint(sym(disc(9, 13, 1.5)), g, 1, base=.25)
        if o.get('fxs'):
            fx(s, o['fxs'])
        return s
    s.paint(sym(poly(shaft_)), c, 3.6, base=-.02, bands=(.5, 0, .04) if v == 'plated' else None)
    s.paint(sym(poly(foot)), c, 3.2, base=.03)
    s.paint(sym(rect(1, 27, 13.5, 29)), o.get('sole', 'ebony'), 1)
    if v == 'plated':
        s.paint(sym(poly([(6.5, 7), (11.5, 7), (11, 17), (9, 19), (7, 17)])), t, 1.9)
        s.shift(sym(line((9, 8), (9, 17))), 2)
        s.paint(sym(poly([(1, 25), (3.5, 21), (7.5, 21), (7.5, 28), (1, 28)])), t, 1.8)
        s.paint(sym(rect(3.5, 18, 13, 19)), a, .9)
    elif v in ('leather', 'slipper'):
        if v == 'leather':
            for y in (9, 14):
                s.paint(sym(rect(4.5, y, 13, y + 1)), t, .9)
                s.paint(sym(rect(7.5, y - 1, 9.5, y + 2)), a, .8, base=.2)
            s.shift(sym(line((11.5, 6), (11.5, 18))), -1)
        s.shift(sym(line((3, 24), (9, 24))), -2)
    if v == 'bone':
        for x, y in ((3, 24), (6, 22), (9, 20)):
            s.paint(sym(poly([(x - 1.5, y + 2), (x + 1.5, y + 2), (x - 2.5, y - 4)])), a, 1)
        s.paint(sym(rect(4.5, 9, 13, 10)), t, .9)
    motif(s, o.get('mot'), a, 'boot')
    if v != 'slipper':
        cuff = o.get('cuff', 'band')
        if cuff == 'fur':
            for x in (5.5, 8.5, 11.5):
                s.paint(sym(disc(x, 4, 2.4)), o.get('furc', 'fur'), 1.6)
        elif cuff == 'flare':
            s.paint(sym(poly([(3.5, 1), (14, 1), (13.5, 6), (5, 6)])), t, 1.5)
        else:
            s.paint(sym(rect(4.5, 3, 13.5, 6)), t, 1.2)
    if g:
        s.paint(sym(disc(9, 12 if v != 'slipper' else 21, 1.7)), g, 1.2, base=.22)
    if o.get('wing'):
        for y, ln in ((6, 6), (10, 5), (14, 3.5)):
            s.paint(sym(poly([(4.5, y - 2), (4.5 - ln, y - 3), (4.5 - ln * .5, y + 1), (4.5, y + 2)])), o['wing'], 1.1, base=.16)
    if o.get('fxs'):
        fx(s, o['fxs'])
    return s
