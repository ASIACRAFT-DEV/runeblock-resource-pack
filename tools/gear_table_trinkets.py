#!/usr/bin/env python3
"""The 50 accessories still to draw (Heart of the World, approved in pass 2, lives in mythic_art.py).
Necklaces hang from a chain, bracelets are seen from above the wrist, rings stand with the setting on top."""
import math

from gear_core import Sprite, curve, disc, line, m, poly, rect, ring, shaft
from gear_armour import oval
from gear_weapons import flame, star4, starn

TRINKETS = {}


def heart(cx, cy, size):
    k = size / 16
    pts = []
    for i in range(40):
        t = i / 40 * math.tau
        pts.append((cx + k * 16 * math.sin(t) ** 3, cy - k * (13 * math.cos(t) - 5 * math.cos(2 * t) - 2 * math.cos(3 * t) - math.cos(4 * t))))
    return poly(pts)


def drop(cx, cy, w, h):
    """A teardrop, point up. (cx, cy) = the centre of the round part."""
    return poly([(cx, cy - h)] + [(cx + w * math.cos(math.radians(a)), cy + w * math.sin(math.radians(a))) for a in range(-40, 221, 20)])


def gem(s, x, y, r, ramp, base=.16):
    """A cut stone: a dark rim, a bright table and one hard glint at the top left."""
    s.paint(disc(x, y, r), ramp, r, base=base)
    if r >= 2:
        s.mark([(x - r * .42, y - r * .42)], 'white', 5)
        s.mark([(x + r * .4, y + r * .45)], ramp, 4)


def bolt(x, y, k=1.0):
    return line((x + 2 * k, y - 5 * k), (x - 1.5 * k, y)) | line((x - 1.5 * k, y), (x + 1.5 * k, y)) | line((x + 1.5 * k, y), (x - 2 * k, y + 5 * k))


# ------------------------------------------------------------------------------------------------- necklaces
def chain(s, kind, ramp, alt=None):
    if kind == 'cord':
        for q in (-1, 1):
            s.paint(curve((15.5 + q * 12.5, 1.5), (15.5 + q * 10, 8), (15.5 + q * 2.6, 11.5), 1.8), ramp, 1, shadow=False)
        return
    for q in (-1, 1):
        for i in range(8):
            x, y = 15.5 + q * (12 - i * 1.25), 1.5 + i * 1.3
            if kind == 'link':
                s.paint(disc(x, y, 1.05 if i % 2 else .8), ramp, 1, shadow=False)
            elif kind == 'heavy':
                s.paint(disc(x, y, 1.45 if i % 2 else 1.0), ramp, 1.2, shadow=False)
            elif kind == 'bead':
                s.paint(disc(x, y, 1.25), alt if i % 2 and alt else ramp, 1.1, base=.1, shadow=False)
            else:
                s.paint(disc(x, y, .7), ramp, 1, base=.1, shadow=False)


def nk(name, kind='link', ramp='gold', alt=None, bail=True):
    def deco(f):
        def fn(o):
            s = Sprite()
            chain(s, kind, ramp, alt)
            if bail:
                s.paint(poly([(13.5, 10), (17.5, 10), (17, 14), (14, 14)]), alt if kind == 'cord' and alt else ramp, 1.3)
            f(s)
            return s
        TRINKETS[name] = (fn, {})
        return f
    return deco


@nk('Copper Pendant', 'link', 'copper')
def _(s):
    s.paint(disc(15.5, 21, 7.6), 'copper', 3, bands=(.8, .8, .07))
    s.shift(ring(15.5, 21, 5.2, 6), -2)
    s.paint(disc(15.5, 21, 3.2), 'copper', 2.2, base=.2)
    s.shift(line((15.5, 18.6), (15.5, 23.4)) | line((13.1, 21), (17.9, 21)), -2)


@nk('Wooden Charm', 'cord', 'leather', 'copper')
def _(s):
    s.paint(poly([(11, 14), (20, 14), (23, 18), (23, 25), (20, 29), (11, 29), (8, 25), (8, 18)]), 'oak', 3)
    for y in (17, 22, 26):
        s.shift(line((10, y), (21, y + 1)), -1)
    s.paint(poly([(15.5, 16.5), (19.5, 21.5), (15.5, 27), (11.5, 21.5)]), 'moss', 1.6, base=.12)
    s.shift(line((15.5, 18), (15.5, 26)), -2)


@nk("Traveler's Pendant", 'cord', 'hide', 'bronze')
def _(s):
    s.paint(disc(15.5, 21, 8), 'bronze', 2, bands=(.8, .8, .07))
    s.paint(disc(15.5, 21, 5.8), 'page', 3)
    for a in range(0, 360, 90):
        s.mark([(15.5 + 4.9 * math.cos(math.radians(a)), 21 + 4.9 * math.sin(math.radians(a)))], 'dark', 2)
    s.paint(poly([(15.5, 15.8), (17, 21), (14, 21)]), 'ruby', 1, base=.2)
    s.paint(poly([(15.5, 26.2), (17, 21), (14, 21)]), 'steel', 1)
    s.paint(disc(15.5, 21, 1), 'gold', 1, base=.2)


@nk('Emberglass Pendant', 'link', 'bronze')
def _(s):
    s.paint(drop(15.5, 22.5, 6.6, 10), 'ember', 4, base=.08)
    s.paint(flame((15.5, 24), 4.4, 3), 'amber', 2, base=.22)
    s.paint(disc(15.5, 25.5, 1.4), 'white', 1, base=.4)
    s.paint(poly([(13, 12.5), (18, 12.5), (17.5, 15.5), (13.5, 15.5)]), 'bronze', 1.2)
    s.mote([(6, 19), (25, 24), (24, 15)], 'ember', 5)


@nk("Wolf's Tooth", 'cord', 'hide', 'fur')
def _(s):
    s.paint(curve((17.5, 14), (20.5, 22), (12.5, 29.5), 6.4, .9), 'bone', 2.6)
    s.shift(curve((16.5, 16), (18.5, 22), (13.5, 28), 1), -1)
    s.paint(rect(14, 12.5, 20.5, 15), 'hide', 1.2)
    for x in (9.5, 21.5):
        s.paint(disc(x, 12, 1.7), 'fur', 1.3, base=.1)


@nk('Moonstone Amulet', 'fine', 'moon')
def _(s):
    s.paint(disc(15.5, 21, 8.6) - disc(18, 19, 7.2), 'moon', 2, base=.1)
    gem(s, 17.2, 20.5, 4.8, 'white', 0)
    s.paint(oval(17.2, 20.5, 2.4, 3), 'sky', 1.8, base=.3, shadow=False)
    s.mark([(16, 19)], 'white', 5)
    s.spark(26, 26, 'moon')


@nk('Stormheart Pendant', 'link', 'steel')
def _(s):
    s.paint(poly([(15.5, 12.5), (24.5, 21.5), (15.5, 30.5), (6.5, 21.5)]), 'steel', 2, bands=(.8, .8, .07))
    s.paint(heart(15.5, 21.5, 7), 'blue', 3, base=.1)
    s.mark(bolt(15.5, 21.5, .9), 'gold', 5)
    s.mote([(5, 15), (26, 16), (27, 27)], 'sky', 5)


@nk("Raven's Amulet", 'bead', 'ebony', 'bone')
def _(s):
    for q in (-1, 1):
        s.paint(poly([(15.5 + q * 2, 15), (15.5 + q * 11, 14), (15.5 + q * 10, 18), (15.5 + q * 12, 19), (15.5 + q * 8, 22), (15.5 + q * 8.5, 25), (15.5 + q * 3, 23)]), 'shadow', 2)
        s.shift(line((15.5 + q * 4, 17), (15.5 + q * 10, 16)) | line((15.5 + q * 4, 20), (15.5 + q * 9, 20)), 1)
    s.paint(poly([(12, 14), (19, 14), (20, 19), (17.5, 23), (16.5, 30), (15.5, 31), (14.5, 30), (13.5, 23), (11, 19)]), 'bone', 2.2)
    for x in (13.5, 17.5):
        s.paint(disc(x, 18, 1.7), 'ebony', 1)
    s.mark([(13, 18), (17, 18)], 'amber', 5)
    s.shift(line((15.5, 23), (15.5, 29)), -2)


@nk('Frostbound Necklace', 'link', 'ice')
def _(s):
    for a in range(0, 180, 60):
        c, d = 10 * math.cos(math.radians(a)), 10 * math.sin(math.radians(a))
        s.paint(shaft(15.5 - c, 21 - d, 15.5 + c, 21 + d, 2.8), 'ice', 1.2, base=.1)
        for q in (-1, 1):
            x, y = 15.5 + q * c * .62, 21 + q * d * .62
            s.mark(line((x, y), (x + 2.6 * math.cos(math.radians(a + 50)) * q, y + 2.6 * math.sin(math.radians(a + 50)) * q)), 'white', 5)
            s.mark(line((x, y), (x + 2.6 * math.cos(math.radians(a - 50)) * q, y + 2.6 * math.sin(math.radians(a - 50)) * q)), 'white', 5)
    gem(s, 15.5, 21, 3.2, 'sky')


@nk('Heart of the Eclipse', 'link', 'gold')
def _(s):
    for a in range(0, 360, 30):
        r = math.radians(a)
        s.paint(shaft(15.5 + 7 * math.cos(r), 21.5 + 7 * math.sin(r), 15.5 + 10.2 * math.cos(r), 21.5 + 10.2 * math.sin(r), 1.8, .8), 'amber', 1, base=.2)
    s.paint(ring(15.5, 21.5, 7, 8.2), 'gold', 1.2, base=.2)
    s.paint(heart(15.5, 21.5, 7.4), 'ebony', 3, base=-.05)
    s.mark([(12, 18), (13, 17)], 'gold', 4)


@nk('Voidborn Pendant', 'bead', 'shadow', 'void')
def _(s):
    s.paint(ring(15.5, 21.5, 7.4, 9.2) - poly([(15.5, 21.5), (29, 29), (20, 34)]), 'shadow', 1.4, base=.1)
    s.paint(poly([(15.5, 13.5), (20, 19), (18.5, 22), (21, 25), (15.5, 30), (11, 25), (13, 22), (10.5, 18)]), 'void', 3, base=.14)
    s.mark(line((15.5, 16), (14, 21)) | line((14, 21), (17, 23)) | line((17, 23), (15, 27)), 'white', 5)
    s.mote([(24, 28), (27, 25), (21, 30)], 'violet', 5)


@nk("Dragon's Heart", 'heavy', 'gold')
def _(s):
    s.paint(heart(15.5, 21, 8.8), 'ruby', 4, base=.1)
    s.paint(flame((15.5, 22), 4, 3), 'ember', 1.8, base=.25)
    s.mark([(11, 17), (12, 16)], 'white', 5)
    for x, top in ((8.5, 15), (15.5, 13), (22.5, 15)):
        s.paint(curve((x, top), (x + (15.5 - x) * .15, top + 5), (x + (15.5 - x) * .5, top + 10), 3, .8), 'gold', 1.3, base=.1)
    s.paint(rect(8, 12.5, 23, 15), 'gold', 1.2, base=.1)


@nk("Titan's Pendant", 'heavy', 'gold')
def _(s):
    s.paint(poly([(8, 13.5), (23, 13.5), (25, 17), (23, 29), (8, 29), (6, 17)]), 'stone', 3)
    s.paint(poly([(8, 13.5), (23, 13.5), (25, 17), (23, 29), (8, 29), (6, 17)]) - poly([(9.5, 15.5), (21.5, 15.5), (23, 17.5), (21.5, 27.5), (9.5, 27.5), (8, 17.5)]), 'gold', 1.2, base=.1)
    s.paint(rect(11, 18, 20, 20), 'gold', 1, base=.1)
    for x in (12.5, 18.5):
        s.mark([(x, 19), (x + 1, 19)], 'ruby', 5)
    s.paint(poly([(14.5, 20), (16.5, 20), (17, 24), (14, 24)]), 'stone', 1, base=.2)
    s.shift(rect(12, 25, 19, 25), -2)


@nk("The King's Promise", 'link', 'gold')
def _(s):
    s.paint(heart(15.5, 23.5, 7), 'blue', 3, base=.12)
    s.mark([(12, 20), (13, 19)], 'white', 5)
    s.paint(poly([(9, 18), (8, 11), (12, 14.5), (15.5, 10), (19, 14.5), (23, 11), (22, 18)]), 'gold', 1.6, base=.08)
    for x, y in ((8, 11), (15.5, 10), (23, 11)):
        s.paint(disc(x, y, 1.3), 'ruby', 1, base=.25)
    s.paint(rect(9, 16.5, 22, 18.5), 'gold', 1, base=.14)


@nk('Heart of Eternity', 'link', 'gold')
def _(s):
    for q in (-1, 1):
        s.paint(ring(15.5 + q * 6.4, 21, 3.8, 6.2), 'gold', 1.6, base=.08)
    s.paint(heart(15.5, 21, 5.8), 'aqua', 2.6, base=.2)
    s.mark([(13, 18), (14, 18)], 'white', 5)
    s.spark(4, 14, 'aqua')
    s.spark(27, 28, 'aqua')


@nk('The First Memory', 'link', 'white')
def _(s):
    s.paint(disc(9.5, 21.5, 7), 'gold', 2.4, bands=(.8, .8, .07))
    s.paint(disc(9.5, 21.5, 4.8), 'page', 3)
    s.paint(disc(9.5, 20, 1.9) | poly([(6, 26), (7, 23), (12, 23), (13, 26)]), 'hide', 1, base=.05, shadow=False)
    s.paint(disc(22, 21.5, 7), 'gold', 2.4, bands=(.8, .8, .07))
    s.paint(disc(22, 21.5, 4.8), 'aqua', 3, base=.2)
    s.paint(star4((22, 21.5), 4.4, 1.1), 'white', 1, base=.5)
    s.paint(rect(14.5, 18, 17, 25), 'gold', 1.2, base=.15)
    s.spark(27, 13, 'aqua')
    s.spark(4, 13, 'gold')
    s.mote([(16, 29), (24, 30), (9, 30)], 'aqua', 5)


# ------------------------------------------------------------------------------------------------- bracelets
class Cuff:
    """A band round a wrist, seen from a little above: open at the top, its front face towards us."""

    def __init__(self, s, ramp, rim=None, h=7, t=2.6, rx=13, ry=7.5, top=10, inner=None):
        self.s, self.rx, self.ry, self.top, self.h = s, rx, ry, top, h
        outer = set()
        for y in range(h + 1):
            outer |= oval(15.5, top + y, rx, ry)
        lip = oval(15.5, top, rx, ry)
        hole = oval(15.5, top, rx - t, ry - t * .8)
        through = hole & oval(15.5, top + h, rx - t, ry - t * .8)
        self.face = outer - lip
        s.paint(hole - through, inner or ramp, 1.4, base=-.34, shadow=False)
        s.paint(self.face, ramp, 3.4, bands=(.9, 0, .06))
        s.paint(lip - hole, rim or ramp, 1.3, base=.16, shadow=False)

    def at(self, a, d=0.0):
        r = math.radians(a)
        return 15.5 + self.rx * math.sin(r), self.top + self.ry * math.cos(r) + d

    def patch(self, a0, a1, d0, d1):
        steps = [a0 + (a1 - a0) * i / 10 for i in range(11)]
        return poly([self.at(a, d0) for a in steps] + [self.at(a, d1) for a in reversed(steps)])

    def lower_rim(self, ramp):
        self.s.paint(self.patch(-88, 88, self.h - 1.2, self.h + .4), ramp, 1, base=.1)

    def studs(self, angles, d, ramp, r=1.0):
        for a in angles:
            x, y = self.at(a, d)
            self.s.paint(disc(x, y, r), ramp, 1, base=.2)


def br(name, ramp, rim=None, **kw):
    def deco(f):
        def fn(o):
            s = Sprite()
            f(s, Cuff(s, ramp, rim, **kw))
            return s
        TRINKETS[name] = (fn, {})
        return f
    return deco


@br('Copper Bracelet', 'copper', h=3, t=2.2)
def _(s, c):
    for a in range(-80, 81, 16):
        x, y = c.at(a, 1.5)
        s.shift(line((x - 1, y + 1.5), (x + 1, y - 1.5)), -2)


@br('Leather Band', 'leather', 'hide', h=6)
def _(s, c):
    for a in range(-76, 77, 10):
        s.mark([c.at(a, 1.2), c.at(a, 4.8)], 'page', 3)
    x, y = c.at(0, 3)
    s.paint(rect(x - 3.5, y - 3.5, x + 3.5, y + 3.5) - rect(x - 1.5, y - 1.5, x + 1.5, y + 1.5), 'bronze', 1.2, base=.1)
    s.paint(rect(x - .5, y - 3, x + .5, y + 3), 'steel', 1, base=.2)


@br('Iron Cuff', 'iron', 'steel', h=7)
def _(s, c):
    c.lower_rim('steel')
    c.studs(range(-72, 73, 24), 1.6, 'steel')
    c.studs(range(-60, 61, 24), 4.6, 'steel')


@br("Hunter's Band", 'hide', 'fur', h=6)
def _(s, c):
    c.lower_rim('fur')
    for a in (-36, 0, 36):
        x, y = c.at(a, 1)
        s.paint(poly([(x - 1.8, y), (x + 1.8, y), (x, y + 7.5)]), 'bone', 1.2, base=.08)


@br('Briarwoven Bracelet', 'moss', 'pine', h=5)
def _(s, c):
    for a in range(-80, 81, 20):
        x, y = c.at(a, 0)
        s.shift(line((x - 2, y), (x + 2, y + 5)), -2)
        s.shift(line((x + 2, y), (x - 2, y + 5)), 1)
    for a in (-66, -22, 22, 66):
        x, y = c.at(a, 5)
        s.paint(poly([(x - 1.3, y - .5), (x + 1.3, y - .5), (x, y + 3.2)]), 'oak', 1, base=.1)
    for a in (-44, 44):
        x, y = c.at(a, 2)
        s.paint(poly([(x - 3, y), (x, y - 2.4), (x + 3, y), (x, y + 2.4)]), 'lime', 1.2, base=.12)


@br('Steel Wristguard', 'steel', 'moon', h=11, top=8)
def _(s, c):
    c.lower_rim('moon')
    s.paint(c.patch(-20, 20, .5, 10.5), 'moon', 1.6, base=.1)
    s.shift(line(c.at(0, 1), c.at(0, 10)), 2)
    for d in (2.5, 8):
        s.paint(c.patch(-78, -26, d, d + 1.4), 'leather', 1)
        s.paint(c.patch(26, 78, d, d + 1.4), 'leather', 1)


@br('Stormcaller Cuff', 'navy', 'moon', h=8)
def _(s, c):
    c.lower_rim('moon')
    x, y = c.at(0, 4)
    s.paint(poly([(x, y - 5), (x + 5.5, y), (x, y + 5), (x - 5.5, y)]), 'moon', 1.4, base=.1)
    s.paint(poly([(x + 1.5, y - 4), (x - 2, y + .6), (x, y + .6), (x - 1.5, y + 4), (x + 2.2, y - .8), (x + .2, y - .8)]), 'gold', 1, base=.35)
    s.mark(bolt(*c.at(-52, 4), .55) | bolt(*c.at(52, 4), .55), 'sky', 5)
    s.mote([(4, 26), (27, 27), (28, 6)], 'sky', 5)


@br('Soulbinder Band', 'shadow', 'aqua', h=6)
def _(s, c):
    for a in range(-68, 69, 34):
        x, y = c.at(a, 3)
        s.mark(line((x, y - 2), (x, y + 2)) | line((x - 1.5, y - 1), (x + 1.5, y + 1)), 'aqua', 5)
    s.mote([(5, 4), (9, 2), (22, 2), (27, 5), (15, 3)], 'aqua', 5)
    s.mote([(7, 6), (25, 3)], 'aqua', 4)


@br('Dreadstone Bangle', 'stone', 'iron', h=6, t=3.2)
def _(s, c):
    for a in range(-70, 71, 28):
        x, y = c.at(a, 6)
        s.paint(poly([(x - 2.2, y - 1), (x + 2.2, y - 1), (x, y + 4)]), 'stone', 1.2)
    s.mark(line(c.at(-50, 1), c.at(-34, 3.5)) | line(c.at(-34, 3.5), c.at(-20, 2)) | line(c.at(-20, 2), c.at(8, 4.5)) | line(c.at(8, 4.5), c.at(30, 1.5)) | line(c.at(30, 1.5), c.at(54, 4)), 'crimson', 4)


@br('Eclipse Cuff', 'ebony', 'gold', h=8)
def _(s, c):
    c.lower_rim('gold')
    x, y = c.at(0, 4)
    for a in range(0, 360, 45):
        r = math.radians(a)
        s.paint(shaft(x + 4 * math.cos(r), y + 4 * math.sin(r), x + 7 * math.cos(r), y + 7 * math.sin(r), 1.6, .7), 'amber', 1, base=.25)
    s.paint(disc(x, y, 4.6), 'gold', 1.2, base=.25)
    s.paint(disc(x, y, 3.4), 'ebony', 2, base=-.1)


@br('Dragonbone Bangle', 'bone', 'bone', h=6, t=3)
def _(s, c):
    for a in range(-78, 79, 26):
        x, y = c.at(a, 3)
        s.shift(line((x + 3, y - 4), (x + 3, y + 4)), -3)
        s.paint(poly([(x - 1.6, y + 3), (x + 1.6, y + 3), (x, y + 8)]), 'bone', 1, base=.08)
    gem(s, *c.at(0, 3), 3, 'ember')


@br('Astral Wristguard', 'night', 'gold', h=11, top=8)
def _(s, c):
    c.lower_rim('gold')
    x, y = c.at(0, 5.5)
    s.paint(disc(x, y, 5), 'gold', 1.2, base=.15)
    s.paint(disc(x, y, 3.8) - disc(x + 1.6, y - 1, 3), 'moon', 1.4, base=.25)
    for a, d in ((-62, 3), (-46, 8), (-34, 2.5), (38, 8), (50, 3), (66, 7)):
        s.mark([c.at(a, d)], 'white', 5)
    s.spark(*c.at(-50, 5), 'moon')
    s.spark(*c.at(50, 5.5), 'moon')


@br("King's Dominion", 'gold', 'ruby', h=11, top=8)
def _(s, c):
    c.lower_rim('ruby')
    x, y = c.at(0, 5.5)
    s.paint(poly([(x - 7, y + 4), (x - 8, y - 4), (x - 3.6, y - .6), (x, y - 6), (x + 3.6, y - .6), (x + 8, y - 4), (x + 7, y + 4)]), 'white', 1.4, base=.1)
    s.paint(rect(x - 7, y + 2, x + 7, y + 4), 'ruby', 1, base=.1)
    for q in (x - 8, x, x + 8):
        s.paint(disc(q, y - 5 if q == x else y - 4, 1.2), 'ruby', 1, base=.25)
    c.studs((-70, 70), 5.5, 'white', 1.4)


@br("Titan's Grasp", 'stone', 'gold', h=9, top=9, t=3)
def _(s, c):
    c.lower_rim('gold')
    for a in (-48, -16, 16, 48):
        x0, y0 = c.at(a, -3)
        x1, y1 = c.at(a * .86, 8)
        s.paint(shaft(x0, y0, x1, y1, 5, 3.6), 'gold', 2, base=.06)
        s.shift(line((x0 - 2, (y0 + y1) / 2), (x0 + 2, (y0 + y1) / 2)), -2)
        s.paint(disc(x1, y1, 1.7), 'ruby', 1, base=.2)


@br("Heaven's Wrath", 'white', 'gold', h=8)
def _(s, c):
    c.lower_rim('gold')
    x, y = c.at(0, 4)
    for q in (-1, 1):
        s.paint(poly([(x + q * 3, y - 3), (x + q * 13, y - 7), (x + q * 11, y - 3), (x + q * 13, y - 1), (x + q * 10, y + 1), (x + q * 10.5, y + 4), (x + q * 3, y + 3)]), 'white', 1.5, base=.1)
        s.shift(line((x + q * 5, y - 1), (x + q * 10, y - 3)) | line((x + q * 5, y + 1), (x + q * 9, y + 1)), -2)
    gem(s, x, y, 3.6, 'sky')
    s.mark(bolt(x, y, .6), 'gold', 5)


@br('Hands of Creation', 'white', 'gold', h=5, top=16, ry=6, rx=12)
def _(s, c):
    c.lower_rim('gold')
    orb = (15.5, 8.5)
    for q in (-1, 1):
        s.paint(poly([(15.5 + q * 2.5, 27), (15.5 + q * 11, 25), (15.5 + q * 12, 18), (15.5 + q * 8, 15), (15.5 + q * 3.5, 18)]), 'gold', 2.4, base=.06)
        for x0, cx, cy, x1, y1 in ((10.5, 14.5, 11, 8.5, 3.5), (8, 11.5, 11.5, 6, 3), (5.5, 8, 13, 3.6, 5)):
            s.paint(curve((15.5 + q * x0, 18), (15.5 + q * cx, cy), (15.5 + q * x1, y1), 2.6, 1.3), 'gold', 1.2, base=.1)
        s.paint(curve((15.5 + q * 4, 21), (15.5 + q * 1.5, 17), (15.5 + q * 1.5, 14), 2.6, 1.4), 'gold', 1.2, base=.02)
    s.paint(disc(orb[0], orb[1], 4.6), 'aqua', 3.4, base=.2)
    s.paint(star4(orb, 4.6, 1), 'white', 1, base=.5)
    s.spark(3, 13, 'aqua')
    s.spark(28, 14, 'gold')


@br('The Unbroken Oath', 'white', 'gold', h=6)
def _(s, c):
    for i, a in enumerate(range(-80, 81, 16)):
        x, y = c.at(a, 3)
        s.paint(ring(x, y, 1.3, 3), 'gold' if i % 2 else 'white', 1, base=.08)
    x, y = c.at(0, 3)
    s.paint(starn((x, y), 9, 7, 5.6), 'crimson', 2, base=.1)
    s.paint(disc(x, y, 4.4), 'ruby', 2, base=.08)
    s.shift(ring(x, y, 3, 3.7), -2)
    s.paint(star4((x, y), 3, .8), 'gold', 1, base=.35)
    s.spark(5, 3, 'gold')
    s.spark(27, 27, 'gold')


# ------------------------------------------------------------------------------------------------- rings
def band(s, metal, r0=6.2, r1=9.6, cy=20.5, inner=None):
    s.paint(oval(17, cy + .8, r1, r1 + .5) - oval(15.5, cy, r0, r0 + .6) - oval(17.6, cy + 1, r0 - .4, r0 + .1), inner or metal, 1.4, base=-.34)
    s.paint(oval(15.5, cy, r1, r1 + .5) - oval(15.5, cy, r0, r0 + .6), metal, 1.9, bands=(.9, .5, .07))


def seat(s, metal, r=5.0, y=8.0):
    """The shoulders that rise from the band and the collet that holds the stone."""
    for q in (-1, 1):
        s.paint(poly([(15.5 + q * 2, y + 3), (15.5 + q * (r + 2.4), y + 2), (15.5 + q * 8.6, y + 7), (15.5 + q * 4, y + 5)]), metal, 1.3, base=.06)
    s.paint(disc(15.5, y, r + 1.3), metal, 1.6, base=.1)


def prongs(s, metal, r=5.0, y=8.0):
    for a in (45, 135, 225, 315):
        s.paint(disc(15.5 + r * .86 * math.cos(math.radians(a)), y + r * .86 * math.sin(math.radians(a)), 1.1), metal, 1, base=.25)


def rg(name, metal, **kw):
    def deco(f):
        def fn(o):
            s = Sprite()
            band(s, metal, **kw)
            f(s)
            return s
        TRINKETS[name] = (fn, {})
        return f
    return deco


@rg('Copper Ring', 'copper')
def _(s):
    s.paint(oval(15.5, 11, 4.6, 3), 'copper', 2, base=.14)
    s.shift(ring(15.5, 11, 1.6, 2.3), -2)


@rg('Iron Band', 'iron', r0=5.4, r1=10)
def _(s):
    s.shift(ring(15.5, 20.5, 7.2, 7.9), 2)
    for a in range(0, 360, 45):
        r = math.radians(a + 22)
        s.paint(disc(15.5 + 8.8 * math.cos(r), 20.5 + 8.8 * math.sin(r), .9), 'steel', 1, base=.25)


@rg("Traveler's Ring", 'bronze')
def _(s):
    seat(s, 'bronze', 4, 9)
    s.paint(disc(15.5, 9, 4), 'page', 2)
    s.paint(star4((15.5, 9), 3.8, .9), 'navy', 1, base=.1)
    s.mark([(15.5, 6), (15.5, 7)], 'ruby', 5)


@rg('Ring of Embers', 'bronze')
def _(s):
    seat(s, 'bronze', 4.4, 10)
    gem(s, 15.5, 10, 4.4, 'ember')
    s.paint(flame((15.5, 6.5), 5, 3.4), 'ember', 1.6, base=.2)
    s.paint(flame((15.5, 7.5), 3, 2), 'amber', 1, base=.3)
    s.mote([(8, 5), (24, 6), (22, 2), (10, 2)], 'ember', 5)


@rg('Lucky Signet', 'gold')
def _(s):
    seat(s, 'gold', 5.4)
    for x, y in ((13.4, 5.9), (17.6, 5.9), (13.4, 10.1), (17.6, 10.1)):
        s.paint(disc(x, y, 2.3), 'green', 1.5, base=.14)
    s.mark(line((15.5, 8), (18, 13)), 'moss', 2)
    s.mark([(15.5, 8)], 'gold', 5)


@rg('Wolfheart Ring', 'steel')
def _(s):
    s.paint(poly([(9, 3), (12.5, 6), (18.5, 6), (22, 3), (22.5, 10), (19, 13), (17.5, 16), (13.5, 16), (12, 13), (8.5, 10)]), 'fur', 2.2, base=.08)
    s.paint(poly([(13, 11), (18, 11), (17, 15), (14, 15)]), 'wool', 1.2)
    s.mark([(15, 15), (16, 15)], 'ebony', 2)
    for x in (12, 19):
        s.mark([(x, 9)], 'ruby', 5)
    for x in (10, 21):
        s.mark([(x, 5)], 'plum', 3)


@rg('Ring of the Tempest', 'steel')
def _(s):
    seat(s, 'steel', 5)
    s.paint(disc(15.5, 8, 5), 'blue', 3, base=.1)
    for k in range(3):
        a0 = math.radians(k * 120)
        pts = {(15.5 + (1 + i * .55) * math.cos(a0 + i * .55), 8 + (1 + i * .55) * math.sin(a0 + i * .55)) for i in range(7)}
        s.mark(list(pts), 'sky', 5)
    s.mark(bolt(25, 6, .6), 'gold', 5)
    s.mote([(5, 4), (7, 11)], 'sky', 5)


@rg("Raven's Eye", 'ebony')
def _(s):
    for q in (-1, 1):
        s.paint(poly([(15.5 + q * 3, 5), (15.5 + q * 13, 2), (15.5 + q * 12, 6), (15.5 + q * 14, 8), (15.5 + q * 10, 10), (15.5 + q * 10, 13), (15.5 + q * 3, 12)]), 'shadow', 1.8)
        s.shift(line((15.5 + q * 5, 7), (15.5 + q * 12, 5)) | line((15.5 + q * 5, 10), (15.5 + q * 10, 9)), 1)
    s.paint(disc(15.5, 8.5, 5), 'ebony', 1.4)
    gem(s, 15.5, 8.5, 3.8, 'amber')
    s.paint(oval(15.5, 8.5, 1, 2.6), 'ebony', 1, shadow=False)


@rg('Soulbound Signet', 'shadow')
def _(s):
    seat(s, 'shadow', 5.4)
    s.paint(ring(15.5, 8, 4.3, 5.4), 'aqua', 1, base=.1)
    s.paint(flame((15.5, 8), 4, 2.8), 'aqua', 1.6, base=.2)
    s.paint(flame((15.5, 9), 2, 1.3), 'white', 1, base=.4)
    s.mote([(6, 3), (25, 2), (27, 9)], 'aqua', 5)


@rg('Ring of Oblivion', 'ebony')
def _(s):
    s.paint(oval(15.5, 8.5, 12.5, 3), 'void', 1.2, base=.15)
    s.paint(disc(15.5, 8.5, 6), 'ebony', 3, base=-.2)
    s.paint(oval(15.5, 8.5, 12.5, 3) - disc(15.5, 6, 6) - oval(15.5, 7.5, 9.5, 1.6), 'violet', 1, base=.25, shadow=False)
    s.mark([(13, 6)], 'violet', 4)
    s.mote([(4, 3), (27, 3), (24, 14)], 'void', 5)


@rg("Dragon's Eye", 'gold')
def _(s):
    gem(s, 15.5, 8.5, 6, 'amber')
    s.paint(poly([(14.6, 3), (16.4, 3), (16.8, 8.5), (16.4, 14), (14.6, 14), (14.2, 8.5)]), 'ebony', 1, shadow=False)
    for q in (-1, 1):
        for y, k in ((3.5, 7), (8.5, 8.6), (13.5, 7)):
            s.paint(curve((15.5 + q * (k + 3.4), y + (8.5 - y) * .4), (15.5 + q * (k + 1.6), y - 1), (15.5 + q * (k - 2.6), y), 2.8, .8), 'gold', 1.2, base=.1)


@rg('Astral Signet', 'night')
def _(s):
    seat(s, 'gold', 5.6)
    s.paint(disc(15.5, 8, 5.6), 'night', 3)
    stars = [(12.5, 5.5), (17, 4.5), (19.5, 8), (15.5, 9), (12, 11)]
    for a, b in zip(stars, stars[1:]):
        s.mark(line(a, b), 'navy', 5)
    s.mark(stars, 'white', 5)
    s.spark(26, 12, 'moon')


@rg('Ring of Genesis', 'white')
def _(s):
    seat(s, 'gold', 4, 11)
    gem(s, 15.5, 11, 4, 'green')
    s.paint(curve((15.5, 9), (15, 5), (16, 2), 1.6, .9), 'lime', 1, base=.1)
    for q, y in ((-1, 5), (1, 3.5)):
        s.paint(poly([(15.5, y + 1.4), (15.5 + q * 3, y - 1.2), (15.5 + q * 7, y - .6), (15.5 + q * 4.6, y + 2.2)]), 'lime', 1.4, base=.12)
    s.spark(5, 12, 'lime')
    s.spark(26, 14, 'gold')


@rg("Titan's Signet", 'gold', r0=5.6, r1=10)
def _(s):
    s.paint(poly([(7, 3), (24, 3), (26, 6), (26, 13), (24, 15), (7, 15), (5, 13), (5, 6)]), 'gold', 2, bands=(.9, .5, .07))
    s.paint(rect(8, 5.5, 23, 12.5), 'stone', 2)
    s.paint(poly([(11, 7), (20, 7), (20, 9), (16.8, 9), (16.8, 11.5), (14.2, 11.5), (14.2, 9), (11, 9)]), 'ruby', 1, base=.2)


@rg("Heaven's Ring", 'white')
def _(s):
    for q in (-1, 1):
        s.paint(poly([(15.5 + q * 3, 7), (15.5 + q * 14, 2.5), (15.5 + q * 12.5, 7), (15.5 + q * 14, 9), (15.5 + q * 10.5, 11), (15.5 + q * 10.5, 14), (15.5 + q * 3, 13)]), 'white', 1.7, base=.1)
        s.shift(line((15.5 + q * 5, 9), (15.5 + q * 12, 6)) | line((15.5 + q * 5, 11), (15.5 + q * 10, 10)), -2)
    s.paint(disc(15.5, 10, 5), 'gold', 1.4, base=.12)
    gem(s, 15.5, 10, 3.8, 'sky')
    s.mote([(5, 13), (26, 14)], 'gold', 5)


@rg('The Beginning', 'gold')
def _(s):
    for a in range(-90, 91, 30):
        r = math.radians(a - 90)
        k = 12.5 if a % 60 == 0 else 9.5
        s.paint(shaft(15.5 + 5 * math.cos(r), 11 + 5 * math.sin(r), 15.5 + k * math.cos(r), 11 + k * math.sin(r), 2.2, .8), 'amber', 1, base=.25)
    s.paint(disc(15.5, 11, 6), 'gold', 1.8, base=.14)
    gem(s, 15.5, 11, 4.6, 'white', .1)
    s.paint(star4((15.5, 11), 4, .9), 'amber', 1, base=.4)
    s.spark(5, 16, 'gold')
    s.spark(26, 16, 'white')


@rg('The End', 'ebony', inner='crimson')
def _(s):
    s.erase(list(disc(23.5, 26.5, 2.6)))
    s.mark(line((21, 25), (24, 22)) | line((24, 22), (22, 20)), 'crimson', 5)
    for a in range(0, 360, 30):
        r = math.radians(a)
        k = 10.5 if a % 60 == 0 else 8.2
        s.paint(shaft(15.5 + 5.6 * math.cos(r), 8.5 + 5.6 * math.sin(r), 15.5 + k * math.cos(r), 8.5 + k * math.sin(r), 2, .7), 'crimson', 1, base=.25)
    s.paint(disc(15.5, 8.5, 6.2), 'ruby', 1.2, base=.2)
    s.paint(disc(15.5, 8.5, 5), 'ebony', 3, base=-.2)
    s.mark(line((13, 6), (15.5, 9)) | line((15.5, 9), (14.5, 11)), 'crimson', 4)
    s.mote([(27, 28), (28, 24), (25, 30), (5, 26)], 'crimson', 5)
