#!/usr/bin/env python3
"""Draws the gear v4 icons (32x32, transparent, centred, at least 1 px of padding).
  python3 -I tools/gear_art.py <out dir> [substring filter]"""
import os
import re
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import mythic_art as m                       # noqa: E402
import gear_core                             # noqa: E402,F401
from gear_table_weapons import W             # noqa: E402

TABLES = [W]
for mod, name in (('gear_table_armour', 'ARMOUR'), ('gear_table_trinkets', 'TRINKETS')):
    try:
        TABLES.append(getattr(__import__(mod), name))
    except ModuleNotFoundError:
        pass


def slug(n): return re.sub('[^a-z0-9]+', '_', n.lower()).strip('_')


def fits(s):
    every = set(s.px)
    if any(x in (0, m.N - 1) or y in (0, m.N - 1) for x, y in every):
        return False
    xs, ys = [p[0] for p in every], [p[1] for p in every]
    free = [p for p in s.free]
    xs += [p[0] for p in free]; ys += [p[1] for p in free]
    return max(xs) - min(xs) + 3 <= 30 and max(ys) - min(ys) + 3 <= 30


def draw(fn, o):
    for k in (1.0, .97, .94, .91, .88, .85, .82, .79, .76):
        m.K = k
        s = fn(o)
        if fits(s):
            return s.image(), k
    return s.image(), k


if __name__ == '__main__':
    out, want = sys.argv[1], (sys.argv[2] if len(sys.argv) > 2 else '')
    os.makedirs(out, exist_ok=True)
    n = 0
    for table in TABLES:
        for name, (fn, o) in table.items():
            if want in slug(name):
                draw(fn, o)[0].save(os.path.join(out, slug(name) + '.png'))
                n += 1
    print(n, 'icons ->', out)
