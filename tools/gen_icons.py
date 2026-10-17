#!/usr/bin/env python3
"""Skill and status-effect icons for RuneBlock (kuwusaki 2026-10-17: "generate skill icons on all skills and status effects").

  python3 -I tools/gen_icons.py <classes.yml> <out-dir> [<sheet-dir>]
  (this repo: python3 -I tools/gen_icons.py ../arcane-souls/src/main/resources/classes.yml pack/assets/runeblock/textures/gui ../docs/screenshots/icons-<date>)

Writes 64x64 PNGs: <out-dir>/skill/<skill_id>.png (every class skill + the Adventurer kit) and
<out-dir>/effect/<effect_id>.png (buffs, debuffs, statuses), plus labelled preview sheets in <sheet-dir>.

How an icon is made (painted at 256 px, downsampled once, so edges stay clean at 64 px):
  background  radial gradient in the class palette (vfx-palette in classes.yml), darker at the rim
  motif       white-hot shapes from the MOTIFS library, lit in the class accent, with a soft glow behind
  frame       by tier: Basic stone, Intermediate silver, Advanced steel blue, Saint violet, King gold,
              Emperor crimson + gold, God white-gold with corner gems and light rays
Effects use one frame per kind (buff green-gold, debuff red, status blue) and a fixed palette per effect.
"""
import math, re, sys, os
from PIL import Image, ImageDraw, ImageFilter, ImageFont, ImageChops

S = 256          # paint size
OUT = 64         # icon size
CJK = '/System/Library/Fonts/Hiragino Sans GB.ttc'
LABEL = '/System/Library/Fonts/Supplemental/Trebuchet MS Bold.ttf'


def rgb(h):
    h = h.strip('"').lstrip('#')
    return tuple(int(h[i:i + 2], 16) for i in (0, 2, 4))


def mix(a, b, k):
    return tuple(round(x + (y - x) * k) for x, y in zip(a, b))


WHITE, BLACK = (255, 255, 255), (0, 0, 0)


# ───────────────────────── palettes from classes.yml ─────────────────────────

def palettes(classes_yml):
    """{class_id: {primary, secondary, accent, dark}} and [(class_id, tier, skill_id, name)] from classes.yml."""
    pal, skills = {}, []
    cls = None
    tier = None
    section = None
    for line in open(classes_yml, encoding='utf-8'):
        top = re.match(r'^([a-z_-]+):', line)
        if top:
            section = top.group(1)
            cls = 'adventurer' if section == 'adventurer' else None
        m = re.match(r'^  ([a-z_]+):\s*$', line)
        if m and section == 'classes':
            cls = m.group(1)
        m = re.search(r'vfx-palette: \{(.*)\}', line)
        if m and cls:
            d = dict(re.findall(r'(\w+): ("?[#\w]+"?)', m.group(1)))
            pal[cls] = {k: rgb(d[k]) for k in ('primary', 'secondary', 'accent', 'dark') if k in d and d[k].strip('"').startswith('#')}
        m = re.match(r'^      (BASIC|INTERMEDIATE|ADVANCED|SAINT|KING|EMPEROR|GOD):', line)
        if m:
            tier = m.group(1)
        m = re.match(r'^    ([a-z_]+):\s*$', line)
        if m and cls == 'adventurer':
            tier = 'ADVENTURER'
            skills.append([cls, tier, m.group(1), None])   # Adventurer skills are keyed by id (no id: line)
            continue
        m = re.match(r'^\s+id: ([a-z_]+)', line)
        if m and cls and tier:
            skills.append([cls, tier, m.group(1), None])
        m = re.match(r'^\s+name: "(.*)"', line)
        if m and skills and skills[-1][3] is None:
            skills[-1][3] = m.group(1)
    seen, out = set(), []
    for c, t, i, n in skills:
        if i in seen:
            continue
        seen.add(i)
        out.append((c, t, i, n or i))
    return pal, out


# ───────────────────────── drawing helpers ─────────────────────────

class Pen:
    """Draws on an RGBA layer in 0..256 coordinates; rot() turns local shapes around a centre."""

    def __init__(self):
        self.im = Image.new('RGBA', (S, S), (0, 0, 0, 0))
        self.d = ImageDraw.Draw(self.im)

    @staticmethod
    def rot(pts, ang, cx=128, cy=128):
        a = math.radians(ang)
        ca, sa = math.cos(a), math.sin(a)
        return [(cx + (x - cx) * ca - (y - cy) * sa, cy + (x - cx) * sa + (y - cy) * ca) for x, y in pts]

    def poly(self, pts, fill, ang=0, cx=128, cy=128, outline=None, width=0):
        p = self.rot(pts, ang, cx, cy) if ang else pts
        self.d.polygon(p, fill=fill, outline=outline, width=width)

    def ell(self, x0, y0, x1, y1, fill=None, outline=None, width=0):
        self.d.ellipse((x0, y0, x1, y1), fill=fill, outline=outline, width=width)

    def circ(self, cx, cy, r, **kw):
        self.ell(cx - r, cy - r, cx + r, cy + r, **kw)

    def line(self, pts, fill, width, ang=0, cx=128, cy=128):
        p = self.rot(pts, ang, cx, cy) if ang else pts
        self.d.line(p, fill=fill, width=width, joint='curve')
        r = width / 2
        for x, y in (p[0], p[-1]):
            self.d.ellipse((x - r, y - r, x + r, y + r), fill=fill)

    def arc(self, cx, cy, r, a0, a1, fill, width):
        self.d.arc((cx - r, cy - r, cx + r, cy + r), a0, a1, fill=fill, width=width)

    def crescent(self, cx, cy, r, a0, a1, thick, fill, steps=40):
        """A filled crescent band: outer arc r, inner arc r-thick tapering to points at both ends."""
        outer, inner = [], []
        for i in range(steps + 1):
            t = i / steps
            a = math.radians(a0 + (a1 - a0) * t)
            w = thick * math.sin(math.pi * t)
            outer.append((cx + r * math.cos(a), cy + r * math.sin(a)))
            inner.append((cx + (r - w) * math.cos(a), cy + (r - w) * math.sin(a)))
        self.d.polygon(outer + inner[::-1], fill=fill)

    def text(self, s, cx, cy, size, fill, font=CJK):
        f = ImageFont.truetype(font, size)
        b = self.d.textbbox((0, 0), s, font=f)
        self.d.text((cx - (b[0] + b[2]) / 2, cy - (b[1] + b[3]) / 2), s, font=f, fill=fill)


def star_pts(cx, cy, r1, r2, n, rot=-90):
    pts = []
    for i in range(n * 2):
        r = r1 if i % 2 == 0 else r2
        a = math.radians(rot + i * 180 / n)
        pts.append((cx + r * math.cos(a), cy + r * math.sin(a)))
    return pts


# ───────────────────────── motifs ─────────────────────────
# Every motif: f(pen, C) where C = {'hi': highlight, 'mid': main fill, 'lo': shade, 'ac': accent}.

def m_sword(p, C, ang=-45, scale=1.0, cx=128, cy=128):
    L = 92 * scale
    blade = [(cx - 9 * scale, cy + 20 * scale), (cx - 9 * scale, cy - L + 18), (cx, cy - L), (cx + 9 * scale, cy - L + 18), (cx + 9 * scale, cy + 20 * scale)]
    p.poly(blade, C['mid'], ang, cx, cy)
    p.poly([(cx - 2, cy + 18 * scale), (cx - 2, cy - L + 14), (cx, cy - L + 4), (cx + 2, cy - L + 14), (cx + 2, cy + 18 * scale)], C['hi'], ang, cx, cy)
    p.poly([(cx - 30 * scale, cy + 20 * scale), (cx + 30 * scale, cy + 20 * scale), (cx + 30 * scale, cy + 30 * scale), (cx - 30 * scale, cy + 30 * scale)], C['ac'], ang, cx, cy)
    p.poly([(cx - 6 * scale, cy + 30 * scale), (cx + 6 * scale, cy + 30 * scale), (cx + 6 * scale, cy + 62 * scale), (cx - 6 * scale, cy + 62 * scale)], C['lo'], ang, cx, cy)
    px, py = Pen.rot([(cx, cy + 68 * scale)], ang, cx, cy)[0]
    p.circ(px, py, 9 * scale, fill=C['ac'])


def m_katana(p, C, ang=-40, cx=128, cy=128):
    pts = []
    for i in range(21):
        t = i / 20
        y = cy + 40 - 140 * t
        x = cx + 10 * math.sin(t * math.pi * 0.9)
        pts.append((x - 6 + 2 * t * 6, y))
    back = [(x + 11 - 9 * (i / 20), y) for i, (x, y) in enumerate(pts)]
    p.poly(pts + back[::-1], C['mid'], ang, cx, cy)
    p.line([(x + 3, y) for x, y in pts[:-2]], C['hi'], 3, ang, cx, cy)
    p.poly([(cx - 16, cy + 40), (cx + 22, cy + 40), (cx + 22, cy + 48), (cx - 16, cy + 48)], C['ac'], ang, cx, cy)
    p.poly([(cx - 3, cy + 48), (cx + 9, cy + 48), (cx + 9, cy + 92), (cx - 3, cy + 92)], C['lo'], ang, cx, cy)


def m_dagger(p, C, ang=-45, cx=128, cy=128, scale=1.0):
    m_sword(p, C, ang, scale, cx, cy)


def m_slash(p, C, n=1, start=200, span=150):
    for i in range(n):
        p.crescent(128, 128, 96 - i * 22, start + i * 18, start + span + i * 18, 26 - i * 4, C['hi'] if i == 0 else C['mid'])


def m_shield(p, C, cx=128, cy=128, s=1.0, boss=True):
    pts = [(cx - 70 * s, cy - 78 * s), (cx + 70 * s, cy - 78 * s), (cx + 70 * s, cy - 10 * s), (cx + 44 * s, cy + 50 * s), (cx, cy + 86 * s), (cx - 44 * s, cy + 50 * s), (cx - 70 * s, cy - 10 * s)]
    p.poly(pts, C['lo'])
    inner = [(x + (cx - x) * 0.16, y + (cy - y) * 0.16) for x, y in pts]
    p.poly(inner, C['mid'])
    p.poly([(cx - 8 * s, cy - 66 * s), (cx + 8 * s, cy - 66 * s), (cx + 8 * s, cy + 70 * s), (cx - 8 * s, cy + 70 * s)], C['hi'])
    if boss:
        p.circ(cx, cy - 6 * s, 20 * s, fill=C['ac'])


def m_dome(p, C):
    p.d.pieslice((22, 40, 234, 252), 180, 360, fill=C['lo'])
    p.d.pieslice((40, 58, 216, 234), 180, 360, fill=C['mid'])
    p.arc(128, 146, 106, 180, 360, C['hi'], 8)
    p.poly([(14, 146), (242, 146), (242, 160), (14, 160)], C['ac'])
    for x in (70, 128, 186):
        p.line([(x, 146), (x, 100 if x != 128 else 70)], C['hi'], 4)


def m_wall(p, C, n=4):
    w = 180 / n
    for i in range(n):
        x0 = 38 + i * w
        h = 120 + (20 if i % 2 else 0)
        p.poly([(x0 + 4, 210 - h), (x0 + w - 4, 210 - h), (x0 + w - 4, 210), (x0 + 4, 210)], C['mid'])
        p.poly([(x0 + 4, 210 - h), (x0 + w - 4, 210 - h), (x0 + w - 4, 210 - h + 14), (x0 + 4, 210 - h + 14)], C['hi'])
        p.poly([(x0 + w - 14, 210 - h + 14), (x0 + w - 4, 210 - h + 14), (x0 + w - 4, 210), (x0 + w - 14, 210)], C['lo'])
    p.poly([(26, 210), (230, 210), (230, 224), (26, 224)], C['ac'])


def m_tower(p, C):
    p.poly([(86, 214), (92, 70), (164, 70), (170, 214)], C['mid'])
    p.poly([(150, 70), (164, 70), (170, 214), (152, 214)], C['lo'])
    for i in range(4):
        x = 82 + i * 26
        p.poly([(x, 46), (x + 18, 46), (x + 18, 74), (x, 74)], C['hi'])
    p.poly([(112, 214), (112, 170), (128, 154), (144, 170), (144, 214)], C['lo'])
    p.poly([(120, 108), (136, 108), (136, 132), (120, 132)], C['ac'])


def m_fist(p, C, cx=128, cy=132, s=1.0):
    p.d.rounded_rectangle((cx - 58 * s, cy - 52 * s, cx + 54 * s, cy + 44 * s), radius=26 * s, fill=C['mid'])
    for i in range(4):
        x = cx - 50 * s + i * 26 * s
        p.d.rounded_rectangle((x, cy - 66 * s, x + 24 * s, cy - 18 * s), radius=11 * s, fill=C['hi'])
        p.line([(x + 4 * s, cy - 18 * s), (x + 20 * s, cy - 18 * s)], C['lo'], max(2, int(4 * s)))
    p.d.rounded_rectangle((cx - 74 * s, cy - 18 * s, cx - 24 * s, cy + 14 * s), radius=14 * s, fill=C['hi'])
    p.d.rounded_rectangle((cx - 40 * s, cy + 40 * s, cx + 40 * s, cy + 86 * s), radius=8 * s, fill=C['lo'])


def m_palm(p, C):
    p.d.rounded_rectangle((78, 118, 178, 214), radius=26, fill=C['mid'])
    for i, (h, x) in enumerate([(84, 80), (100, 104), (104, 128), (90, 152)]):
        p.d.rounded_rectangle((x, 118 - h, x + 22, 140), radius=11, fill=C['hi'])
    p.d.rounded_rectangle((170, 128, 212, 154), radius=13, fill=C['hi'], )
    p.circ(128, 166, 18, fill=C['ac'])


def m_burst(p, C, n=8, r1=104, r2=44, cx=128, cy=128):
    p.poly(star_pts(cx, cy, r1, r2, n), C['mid'])
    p.poly(star_pts(cx, cy, r1 * 0.66, r2 * 0.66, n, -90 + 180 / n), C['hi'])
    p.circ(cx, cy, r2 * 0.6, fill=WHITE)


def m_flame(p, C, cx=128, cy=140, s=1.0):
    def fl(r, col, dy=0.0, lean=0.0):
        pts = []
        for i in range(61):
            t = i / 60 * 2 * math.pi
            x = r * 0.78 * math.sin(t) * abs(math.sin(t / 2)) ** 1.1
            y = -r * 1.25 * math.cos(t)
            y += 0 if math.cos(t) < 0 else 0
            wob = 0.08 * r * math.sin(5 * t) * max(0, math.cos(t))
            pts.append((cx + x + wob + lean * (r * 1.25 + y) * -0.25, cy + 22 * s + y * 0.82 + dy))
        p.poly(pts, col)
    fl(104 * s, C['lo'], 0, 0.15)
    fl(80 * s, C['mid'], 12 * s, -0.1)
    fl(50 * s, C['hi'], 28 * s, 0.05)
    p.circ(cx, cy + 52 * s, 16 * s, fill=WHITE)


def m_bolt(p, C, cx=128, cy=128, s=1.0, ang=0):
    pts = [(cx + 22 * s, cy - 104 * s), (cx - 46 * s, cy + 6 * s), (cx - 4 * s, cy + 6 * s), (cx - 28 * s, cy + 104 * s), (cx + 50 * s, cy - 16 * s), (cx + 8 * s, cy - 16 * s)]
    p.poly(pts, C['mid'], ang, cx, cy)
    inner = [(x + (cx - x) * 0.35, y + (cy - y) * 0.35) for x, y in pts]
    p.poly(inner, C['hi'], ang, cx, cy)


def m_snow(p, C, cx=128, cy=128, r=96):
    for i in range(6):
        a = math.radians(i * 60 - 90)
        ex, ey = cx + r * math.cos(a), cy + r * math.sin(a)
        p.line([(cx, cy), (ex, ey)], C['hi'], 12)
        for k in (0.5, 0.75):
            bx, by = cx + r * k * math.cos(a), cy + r * k * math.sin(a)
            for d in (-40, 40):
                b = a + math.radians(d)
                p.line([(bx, by), (bx + 26 * math.cos(b) * (1.2 - k), by + 26 * math.sin(b) * (1.2 - k))], C['mid'], 9)
    p.poly(star_pts(cx, cy, 30, 14, 6), C['ac'])


def m_meteor(p, C, cx=150, cy=150):
    p.poly([(cx - 30, cy - 20), (32, 40), (cx - 10, cy - 46), (60, 26), (cx + 18, cy - 38)], C['lo'])
    p.poly([(cx - 26, cy - 12), (46, 58), (cx - 16, cy - 32)], C['mid'])
    p.circ(cx, cy, 46, fill=C['mid'])
    p.circ(cx - 10, cy - 10, 30, fill=C['hi'])
    p.circ(cx - 18, cy - 18, 12, fill=WHITE)


def m_cross(p, C, cx=128, cy=128, s=1.0):
    w, l = 30 * s, 92 * s
    p.d.rounded_rectangle((cx - w, cy - l, cx + w, cy + l), radius=10 * s, fill=C['mid'])
    p.d.rounded_rectangle((cx - l, cy - w, cx + l, cy + w), radius=10 * s, fill=C['mid'])
    p.d.rounded_rectangle((cx - w * 0.45, cy - l * 0.85, cx + w * 0.45, cy + l * 0.85), radius=6 * s, fill=C['hi'])
    p.d.rounded_rectangle((cx - l * 0.85, cy - w * 0.45, cx + l * 0.85, cy + w * 0.45), radius=6 * s, fill=C['hi'])


def m_heart(p, C, cx=128, cy=128, s=1.0, col=None):
    pts = []
    for i in range(60):
        t = i / 60 * 2 * math.pi
        x = 16 * math.sin(t) ** 3
        y = 13 * math.cos(t) - 5 * math.cos(2 * t) - 2 * math.cos(3 * t) - math.cos(4 * t)
        pts.append((cx + x * 5.6 * s, cy - y * 5.6 * s - 6 * s))
    p.poly(pts, col or C['mid'])
    p.ell(cx - 54 * s, cy - 62 * s, cx - 20 * s, cy - 34 * s, fill=C['hi'])


def m_leaf(p, C, cx=128, cy=128, ang=-35, s=1.0):
    pts = []
    for i in range(41):
        t = i / 40
        w = 46 * s * math.sin(math.pi * t) ** 0.9
        pts.append((cx + w, cy + 96 * s - 192 * s * t))
    pts += [(cx - (x - cx), y) for x, y in pts[::-1]]
    p.poly(pts, C['mid'], ang, cx, cy)
    p.line([(cx, cy + 96 * s), (cx, cy - 80 * s)], C['hi'], max(3, int(7 * s)), ang, cx, cy)
    for k in range(-2, 3):
        y = cy + k * 30 * s
        p.line([(cx, y), (cx + 30 * s, y - 24 * s)], C['lo'], max(2, int(4 * s)), ang, cx, cy)
        p.line([(cx, y), (cx - 30 * s, y - 24 * s)], C['lo'], max(2, int(4 * s)), ang, cx, cy)


def m_vines(p, C):
    for k, (x0, col) in enumerate([(60, C['mid']), (128, C['hi']), (196, C['mid'])]):
        pts = [(x0 + 22 * math.sin(t / 5 + k), 230 - t * 9) for t in range(22)]
        p.line(pts, col, 14)
        for t in (6, 12, 18):
            x, y = pts[t]
            p.ell(x - 4, y - 16, x + 26, y + 2, fill=C['ac'])


def m_tree(p, C):
    p.poly([(112, 232), (118, 140), (138, 140), (146, 232)], C['lo'])
    p.line([(128, 170), (86, 130)], C['lo'], 12)
    p.line([(130, 160), (178, 122)], C['lo'], 12)
    for cx, cy, r, col in [(84, 112, 46, C['mid']), (172, 108, 46, C['mid']), (128, 82, 60, C['mid']), (128, 76, 40, C['hi']), (96, 104, 20, C['hi'])]:
        p.circ(cx, cy, r, fill=col)
    for x, y in [(70, 92), (180, 90), (140, 50), (110, 130)]:
        p.circ(x, y, 7, fill=C['ac'])


def m_torii(p, C):
    p.poly([(30, 62), (226, 62), (214, 84), (42, 84)], C['mid'])
    p.poly([(20, 50), (236, 50), (230, 62), (26, 62)], C['lo'])
    p.poly([(52, 104), (204, 104), (204, 118), (52, 118)], C['mid'])
    for x in (72, 170):
        p.poly([(x, 84), (x + 16, 84), (x + 20, 226), (x - 4, 226)], C['mid'])
        p.poly([(x + 10, 84), (x + 16, 84), (x + 20, 226), (x + 12, 226)], C['lo'])
    p.poly([(120, 84), (136, 84), (136, 104), (120, 104)], C['hi'])


def m_note(p, C, cx=128, cy=128, s=1.0, double=True):
    def one(x, y):
        p.ell(x - 30 * s, y + 34 * s, x + 10 * s, y + 64 * s, fill=C['mid'])
        p.poly([(x + 2 * s, y - 70 * s), (x + 12 * s, y - 70 * s), (x + 12 * s, y + 50 * s), (x + 2 * s, y + 50 * s)], C['hi'])
    if double:
        one(cx - 30 * s, cy + 6 * s); one(cx + 46 * s, cy - 14 * s)
        p.poly([(cx - 28 * s, cy - 64 * s), (cx + 58 * s, cy - 84 * s), (cx + 58 * s, cy - 62 * s), (cx - 28 * s, cy - 42 * s)], C['ac'])
    else:
        one(cx, cy)
        p.poly([(cx + 12 * s, cy - 70 * s), (cx + 52 * s, cy - 44 * s), (cx + 46 * s, cy - 30 * s), (cx + 12 * s, cy - 48 * s)], C['ac'])


def m_skull(p, C, cx=128, cy=120, s=1.0):
    p.ell(cx - 68 * s, cy - 76 * s, cx + 68 * s, cy + 50 * s, fill=C['hi'])
    p.d.rounded_rectangle((cx - 42 * s, cy + 24 * s, cx + 42 * s, cy + 80 * s), radius=12 * s, fill=C['hi'])
    for dx in (-30, 30):
        p.ell(cx + dx * s - 22 * s, cy - 18 * s, cx + dx * s + 22 * s, cy + 22 * s, fill=C['lo'])
        p.circ(cx + dx * s, cy + 2 * s, 7 * s, fill=C['ac'])
    p.poly([(cx, cy + 22 * s), (cx - 10 * s, cy + 42 * s), (cx + 10 * s, cy + 42 * s)], C['lo'])
    for dx in (-24, -8, 8, 24):
        p.line([(cx + dx * s, cy + 56 * s), (cx + dx * s, cy + 78 * s)], C['lo'], max(2, int(5 * s)))


def m_hourglass(p, C):
    p.poly([(60, 34), (196, 34), (196, 50), (60, 50)], C['ac'])
    p.poly([(60, 206), (196, 206), (196, 222), (60, 222)], C['ac'])
    p.poly([(76, 50), (180, 50), (140, 128), (180, 206), (76, 206), (116, 128)], C['lo'])
    p.poly([(90, 64), (166, 64), (132, 124), (124, 124)], C['hi'])
    p.poly([(124, 150), (132, 150), (164, 196), (92, 196)], C['mid'])


def m_eye(p, C, closed=False):
    if closed:
        p.crescent(128, 60, 110, 30, 150, 34, C['mid'])
        for x in (70, 104, 152, 186):
            p.line([(x, 150), (x - 6 if x < 128 else x + 6, 176)], C['hi'], 7)
        return
    p.d.chord((18, 56, 238, 200), 200, 340, fill=C['mid'])
    p.d.chord((18, 56, 238, 200), 20, 160, fill=C['mid'])
    p.ell(30, 76, 226, 180, fill=C['mid'])
    p.circ(128, 128, 46, fill=C['lo'])
    p.circ(128, 128, 30, fill=C['ac'])
    p.circ(128, 128, 14, fill=BLACK)
    p.circ(112, 112, 8, fill=WHITE)


def m_rune(p, C, cx=128, cy=128, r=100, sides=3):
    p.circ(cx, cy, r, outline=C['mid'], width=10)
    p.circ(cx, cy, r - 22, outline=C['hi'], width=5)
    for i in range(12):
        a = math.radians(i * 30)
        p.line([(cx + (r - 12) * math.cos(a), cy + (r - 12) * math.sin(a)), (cx + (r + 4) * math.cos(a), cy + (r + 4) * math.sin(a))], C['ac'], 5)
    pts = [(cx + (r - 26) * math.cos(math.radians(-90 + i * 360 / sides)), cy + (r - 26) * math.sin(math.radians(-90 + i * 360 / sides))) for i in range(sides)]
    p.d.polygon(pts, outline=C['hi'], width=8)
    p.circ(cx, cy, 14, fill=C['ac'])


def m_swirl(p, C, cx=128, cy=128, arms=3, r=104):
    for k in range(arms):
        pts = []
        for i in range(60):
            t = i / 59
            a = math.radians(k * 360 / arms + t * 330)
            rr = r * (0.12 + 0.88 * t)
            pts.append((cx + rr * math.cos(a), cy + rr * math.sin(a)))
        p.line(pts, C['mid'] if k else C['hi'], 14)
    p.circ(cx, cy, 18, fill=C['ac'])


def m_wind(p, C):
    for k, (y, ln) in enumerate([(78, 160), (128, 190), (178, 140)]):
        pts = [(34 + t * ln / 30, y + 10 * math.sin(t / 4)) for t in range(31)]
        x, yy = pts[-1]
        for i in range(14):
            a = math.radians(-90 + i * 22)
            pts.append((x + 20 * math.cos(a) - 0, yy - 20 + 20 * math.sin(a) + 20))
        p.line(pts, C['hi'] if k == 1 else C['mid'], 13)


def m_crown(p, C, cx=128, cy=140, s=1.0):
    pts = [(cx - 90 * s, cy + 40 * s), (cx - 90 * s, cy - 50 * s), (cx - 46 * s, cy - 6 * s), (cx, cy - 70 * s), (cx + 46 * s, cy - 6 * s), (cx + 90 * s, cy - 50 * s), (cx + 90 * s, cy + 40 * s)]
    p.poly(pts, C['mid'])
    p.poly([(cx - 90 * s, cy + 22 * s), (cx + 90 * s, cy + 22 * s), (cx + 90 * s, cy + 40 * s), (cx - 90 * s, cy + 40 * s)], C['lo'])
    for x, y in [(cx - 90 * s, cy - 50 * s), (cx, cy - 70 * s), (cx + 90 * s, cy - 50 * s)]:
        p.circ(x, y, 12 * s, fill=C['ac'])
    p.circ(cx, cy + 4 * s, 14 * s, fill=C['ac'])


def m_wings(p, C, cx=128, cy=132):
    for sgn in (-1, 1):
        for k in range(4):
            pts = [(cx + sgn * 10, cy - 10 + k * 14), (cx + sgn * (110 - k * 14), cy - 70 + k * 30), (cx + sgn * (96 - k * 18), cy - 52 + k * 34), (cx + sgn * 10, cy + 10 + k * 16)]
            p.poly(pts, C['hi'] if k == 0 else C['mid'] if k < 3 else C['lo'])
    p.circ(cx, cy, 18, fill=C['ac'])


def m_chain(p, C):
    for i, (cx, cy) in enumerate([(70, 186), (128, 128), (186, 70)]):
        a = -45
        pts = Pen.rot([(cx - 46, cy - 26), (cx + 46, cy + 26)], 0)
        p.d.rounded_rectangle((cx - 50, cy - 26, cx + 50, cy + 26), radius=26, outline=C['hi'] if i == 1 else C['mid'], width=14)


def m_mirror(p, C):
    p.ell(56, 26, 200, 196, fill=C['ac'])
    p.ell(70, 40, 186, 182, fill=C['lo'])
    p.poly([(96, 60), (126, 60), (86, 150), (72, 130)], C['hi'])
    p.poly([(140, 56), (152, 56), (104, 166), (96, 158)], C['mid'])
    p.poly([(116, 196), (140, 196), (148, 238), (108, 238)], C['ac'])


def m_moon(p, C, cx=128, cy=128):
    p.circ(cx, cy, 96, fill=C['hi'])
    p.circ(cx + 44, cy - 30, 86, fill=(0, 0, 0, 0))


def m_sun(p, C, cx=128, cy=128):
    for i in range(12):
        a = math.radians(i * 30)
        p.poly([(cx + 60 * math.cos(a - 0.16), cy + 60 * math.sin(a - 0.16)), (cx + 112 * math.cos(a), cy + 112 * math.sin(a)), (cx + 60 * math.cos(a + 0.16), cy + 60 * math.sin(a + 0.16))], C['mid'])
    p.circ(cx, cy, 62, fill=C['hi'])
    p.circ(cx, cy, 38, fill=WHITE)


def m_arrow(p, C, ang=-45, cx=128, cy=128, s=1.0):
    p.poly([(cx - 6 * s, cy + 92 * s), (cx + 6 * s, cy + 92 * s), (cx + 6 * s, cy - 50 * s), (cx - 6 * s, cy - 50 * s)], C['mid'], ang, cx, cy)
    p.poly([(cx - 30 * s, cy - 44 * s), (cx, cy - 104 * s), (cx + 30 * s, cy - 44 * s)], C['hi'], ang, cx, cy)
    for k in (0, 1):
        p.poly([(cx - 6 * s, cy + (60 + k * 18) * s), (cx - 28 * s, cy + (78 + k * 18) * s), (cx - 6 * s, cy + (74 + k * 18) * s)], C['ac'], ang, cx, cy)
        p.poly([(cx + 6 * s, cy + (60 + k * 18) * s), (cx + 28 * s, cy + (78 + k * 18) * s), (cx + 6 * s, cy + (74 + k * 18) * s)], C['ac'], ang, cx, cy)


def m_drop(p, C, cx=128, cy=136, s=1.0, col=None):
    pts = []
    for i in range(41):
        t = i / 40 * 2 * math.pi
        r = 70 * s
        x = cx + r * math.sin(t) * (0.5 + 0.5 * math.sin(t / 2) ** 0.6 if t < math.pi else 0.5 + 0.5 * math.sin(t / 2) ** 0.6)
        y = cy + 20 * s - r * math.cos(t) * 1.2
        pts.append((x, y))
    pts = [(cx, cy - 104 * s)] + [(cx + 70 * s * math.sin(a), cy + 20 * s + 70 * s * math.cos(a)) for a in [math.radians(d) for d in range(120, -121, -10)]]
    p.poly(pts, col or C['mid'])
    p.ell(cx - 40 * s, cy + 2 * s, cx - 14 * s, cy + 46 * s, fill=C['hi'])


def m_ghost(p, C, cx=128, cy=124, s=1.0):
    p.d.pieslice((cx - 64 * s, cy - 84 * s, cx + 64 * s, cy + 44 * s), 180, 360, fill=C['hi'])
    pts = [(cx - 64 * s, cy - 20 * s), (cx + 64 * s, cy - 20 * s), (cx + 64 * s, cy + 74 * s)]
    for i in range(6):
        x = cx + 64 * s - (i + 1) * 128 * s / 6
        pts.append((x + 64 * s / 6 * 1.0, cy + (52 if i % 2 == 0 else 80) * s))
    pts += [(cx - 64 * s, cy + 74 * s)]
    p.poly(pts, C['hi'])
    for dx in (-24, 24):
        p.ell(cx + dx * s - 12 * s, cy - 34 * s, cx + dx * s + 12 * s, cy - 6 * s, fill=C['lo'])


def m_claw(p, C):
    for k in range(3):
        x = 60 + k * 50
        p.crescent(x - 140, 128 + k * 6, 210, -42, 22, 26, C['hi'] if k == 1 else C['mid'], 30)


def m_golem(p, C):
    p.poly([(88, 30), (168, 30), (168, 92), (88, 92)], C['mid'])
    p.poly([(104, 54), (120, 54), (120, 66), (104, 66)], C['ac'])
    p.poly([(136, 54), (152, 54), (152, 66), (136, 66)], C['ac'])
    p.poly([(60, 96), (196, 96), (186, 176), (70, 176)], C['mid'])
    p.poly([(26, 100), (60, 100), (56, 206), (24, 206)], C['lo'])
    p.poly([(196, 100), (230, 100), (232, 206), (200, 206)], C['lo'])
    p.poly([(82, 176), (122, 176), (122, 236), (82, 236)], C['lo'])
    p.poly([(134, 176), (174, 176), (174, 236), (134, 236)], C['lo'])
    p.line([(96, 120), (160, 150)], C['ac'], 6)


def m_hammer(p, C, ang=-35):
    p.poly([(120, 230), (136, 230), (136, 90), (120, 90)], C['lo'], ang)
    p.d.rounded_rectangle((0, 0, 0, 0))
    p.poly([(60, 40), (196, 40), (196, 100), (60, 100)], C['mid'], ang)
    p.poly([(60, 40), (196, 40), (196, 56), (60, 56)], C['hi'], ang)
    p.poly([(116, 100), (140, 100), (140, 112), (116, 112)], C['ac'], ang)


def m_talisman(p, C, glyph='符'):
    p.poly([(80, 22), (176, 22), (176, 234), (80, 234)], (245, 236, 210))
    p.poly([(80, 22), (176, 22), (176, 36), (80, 36)], C['mid'])
    p.text(glyph, 128, 128, 96, C['lo'])
    p.line([(98, 200), (158, 200)], C['mid'], 6)


def m_glyph(p, C, g, size=150, font=CJK, cx=128, cy=132):
    p.text(g, cx, cy, size, C['hi'], font)


def m_figure(p, C, cx=128, cy=128, s=1.0, col=None):
    col = col or C['hi']
    p.circ(cx, cy - 56 * s, 26 * s, fill=col)
    p.d.rounded_rectangle((cx - 36 * s, cy - 26 * s, cx + 36 * s, cy + 70 * s), radius=24 * s, fill=col)


def m_orb(p, C, cx=128, cy=128, r=72):
    p.circ(cx, cy, r, fill=C['mid'])
    p.circ(cx - r * 0.18, cy - r * 0.18, r * 0.7, fill=C['hi'])
    p.circ(cx - r * 0.35, cy - r * 0.35, r * 0.22, fill=WHITE)


def m_drake(p, C):
    p.poly([(40, 150), (120, 70), (190, 60), (232, 96), (200, 110), (226, 140), (176, 132), (128, 176), (92, 210)], C['mid'])
    p.poly([(120, 70), (150, 26), (160, 66)], C['hi'])
    p.poly([(150, 66), (190, 32), (186, 70)], C['hi'])
    p.circ(176, 92, 8, fill=C['ac'])
    for k in range(3):
        p.poly([(190 + k * 10, 110), (196 + k * 10, 130), (202 + k * 10, 110)], WHITE)


def m_behemoth(p, C):
    p.d.pieslice((20, 70, 236, 286), 180, 360, fill=C['mid'])
    p.poly([(60, 120), (20, 40), (92, 100)], C['hi'])
    p.poly([(196, 120), (236, 40), (164, 100)], C['hi'])
    for dx in (-40, 40):
        p.ell(128 + dx - 16, 128, 128 + dx + 16, 152, fill=C['ac'])
    p.poly([(96, 176), (160, 176), (150, 200), (106, 200)], C['lo'])


def m_target(p, C):
    p.circ(128, 128, 96, outline=C['mid'], width=12)
    p.circ(128, 128, 56, outline=C['hi'], width=10)
    p.circ(128, 128, 16, fill=C['ac'])
    for a in (0, 90, 180, 270):
        x, y = math.cos(math.radians(a)), math.sin(math.radians(a))
        p.line([(128 + 70 * x, 128 + 70 * y), (128 + 116 * x, 128 + 116 * y)], C['hi'], 10)


def m_feather(p, C):
    m_leaf(p, {**C, 'mid': C['hi'], 'hi': C['mid']}, ang=35, s=0.95)


def m_stars_ring(p, C):
    p.ell(30, 90, 226, 166, outline=C['mid'], width=8)
    for a in (200, 290, 20):
        x = 128 + 98 * math.cos(math.radians(a)); y = 128 + 38 * math.sin(math.radians(a))
        p.poly(star_pts(x, y, 30, 12, 5), C['hi'])


def m_arrows_up(p, C):
    for x in (76, 128, 180):
        y = 70 if x == 128 else 100
        p.poly([(x - 30, y + 30), (x, y - 20), (x + 30, y + 30), (x + 14, y + 30), (x + 14, y + 110), (x - 14, y + 110), (x - 14, y + 30)], C['hi'] if x == 128 else C['mid'])


def m_arrows_down(p, C):
    for x in (76, 128, 180):
        y = 186 if x == 128 else 156
        p.poly([(x - 30, y - 30), (x, y + 20), (x + 30, y - 30), (x + 14, y - 30), (x + 14, y - 110), (x - 14, y - 110), (x - 14, y - 30)], C['hi'] if x == 128 else C['mid'])


def m_crack(p, C):
    m_shield(p, C, boss=False)
    p.line([(118, 40), (140, 92), (110, 130), (146, 176), (126, 214)], (20, 10, 10), 12)


def m_campfire(p, C):
    m_flame(p, C, cx=128, cy=104, s=0.8)
    p.line([(40, 214), (216, 180)], C['lo'], 22)
    p.line([(40, 180), (216, 214)], C['lo'], 22)


def m_figures(p, C):
    m_figure(p, C, 70, 150, 0.7, C['mid'])
    m_figure(p, C, 186, 150, 0.7, C['mid'])
    m_figure(p, C, 128, 124, 0.95, C['hi'])


def m_crossed_swords(p, C):
    m_sword(p, C, -45, 1.15)
    m_sword(p, C, 45, 1.15)


def no(p, C, over):
    """A red 'not allowed' bar across whatever is drawn."""
    p.circ(128, 128, 104, outline=(230, 40, 40), width=16)
    p.line([(56, 200), (200, 56)], (230, 40, 40), 16)


# ───────────────────────── which motif for which skill ─────────────────────────
# id -> list of (motif, kwargs). Read from the skill names / descriptions in classes.yml.
SKILLS = {
    # Guardian
    'iron_guard': [('shield', {})],
    'anchor_howl': [('shield', {'s': 0.7, 'cy': 140}), ('ring_waves', {})],
    'phalanx_wall': [('wall', {})],
    'aegis_dome': [('dome', {})],
    'impervious_sovereign': [('shield', {'s': 0.85, 'cy': 150}), ('crown', {'s': 0.55, 'cy': 46})],
    'titans_citadel': [('tower', {}), ('ring_waves', {'r0': 100})],
    'absolute_sanctuary': [('wings', {}), ('shield', {'s': 0.6})],
    # Samurai
    'quick_draw': [('katana', {'ang': -60})],
    'lightning_speed': [('katana', {'ang': -40}), ('bolt', {'s': 0.45, 'cx': 70, 'cy': 70})],
    'iiai_cleave': [('slash', {'n': 1, 'start': 150, 'span': 200})],
    'blade_of_the_tempest': [('wind', {}), ('katana', {'ang': -45})],
    'six_fold_asura_strike': [('slash', {'n': 3, 'start': 190, 'span': 140}), ('glyph', {'g': '六', 'size': 90})],
    'void_severing_edge': [('swirl', {'arms': 2, 'r': 90}), ('katana', {'ang': -45})],
    'world_slash': [('slash', {'n': 3, 'start': 170, 'span': 200}), ('glyph', {'g': '斬', 'size': 100})],
    # Monk
    'iron_palm': [('palm', {})],
    'meteor_strike': [('meteor', {})],
    'chakra_pulse': [('rune', {'sides': 6}), ('ring_waves', {'r0': 60})],
    'asura_shatter': [('fist', {}), ('crack_lines', {})],
    'brahma_pressure': [('arrows_down', {}), ('ring_waves', {'r0': 110})],
    'spatial_fists': [('swirl', {'arms': 3}), ('fist', {'s': 0.7})],
    'nullification_strike': [('fist', {'s': 0.8}), ('glyph', {'g': '空', 'size': 80, 'cy': 64})],
    # Assassin
    'dagger_flick': [('dagger', {'ang': 45})],
    'shadow_lurk': [('eye', {'closed': True})],
    'shadowstep_execution': [('dagger', {'ang': -45}), ('swirl', {'arms': 2, 'r': 60})],
    'nightfall_field': [('moon', {})],
    'phantom_flurry': [('dagger', {'ang': -50, 'scale': 0.8, 'cx': 96}), ('dagger', {'ang': 50, 'scale': 0.8, 'cx': 160}), ('dagger', {'ang': 0, 'scale': 0.9})],
    'deaths_whisper': [('skull', {}), ('target_small', {})],
    'eclipse_extinction': [('eclipse', {})],
    # Swashbuckler
    'parry': [('crossed_swords', {})],
    'dual_flurry': [('dagger', {'ang': -30, 'scale': 0.95}), ('dagger', {'ang': 30, 'scale': 0.95})],
    'blade_dance': [('swirl', {'arms': 3, 'r': 96}), ('sword', {'ang': -45, 'scale': 0.6})],
    'tempest_cascade': [('wind', {})],
    'gale_force_execution': [('wind', {}), ('arrows_up', {})],
    'infinite_blade_horizon': [('blade_ring', {})],
    'eternal_flourish': [('hourglass', {}), ('blade_ring', {'n': 6, 'r': 108})],
    # Bard
    'minuet': [('note', {'double': False})],
    'anthem': [('note', {})],
    'symphony_of_courage': [('note', {'s': 0.8}), ('ring_waves', {'r0': 110})],
    'resonance_of_the_saint': [('note', {'s': 0.7}), ('hourglass_small', {})],
    'aura_of_the_sovereign': [('crown', {'s': 0.8}), ('heart_small', {})],
    'harmonic_requiem': [('note', {}), ('crack_lines', {})],
    'song_of_creation': [('sun', {}), ('note', {'s': 0.6, 'double': False})],
    # Cleric
    'minor_heal': [('cross', {'s': 0.8})],
    'holy_light': [('sun', {})],
    'sanctuary': [('cross', {'s': 0.6}), ('ring_waves', {'r0': 100})],
    'cumulonimbus_blessing': [('cloud', {})],
    'judgment_rain': [('cloud', {'cy': 90}), ('bolt', {'s': 0.5, 'cy': 170})],
    'divine_resurrection_zone': [('rune', {'sides': 4}), ('ankh', {})],
    'miracle_of_rebirth': [('wings', {}), ('cross', {'s': 0.45})],
    # Druid
    'entangle': [('vines', {})],
    'natures_grasp': [('vines', {}), ('palm_small', {})],
    'wild_bloom': [('flower', {})],
    'wrath_of_the_forest': [('leaf', {'ang': -35}), ('leaf', {'ang': 35, 's': 0.8})],
    'verdant_maw': [('maw', {})],
    'gaias_restoration': [('leaf', {'ang': 0, 's': 0.8}), ('ring_waves', {'r0': 112})],
    'genesis_tree': [('tree', {})],
    # Kannagi
    'ward_tag': [('talisman', {'glyph': '符'})],
    'damage_intercept': [('talisman', {'glyph': '守'})],
    'purifying_ward': [('talisman', {'glyph': '浄'})],
    'shrine_maiden_aegis': [('torii', {})],
    'mirror_of_truth': [('mirror', {})],
    'sacred_boundary_realm': [('torii', {}), ('ring_waves', {'r0': 116})],
    'divine_seal': [('torii', {}), ('glyph', {'g': '封', 'size': 80, 'cy': 150})],
    # Sorcerer
    'firebolt': [('flame', {})],
    'searing_lance': [('arrow', {'ang': 45}), ('flame', {'s': 0.45, 'cx': 84, 'cy': 168})],
    'infernal_meteor': [('meteor', {})],
    'thunderstorm': [('cloud', {'cy': 86}), ('bolt', {'s': 0.55, 'cy': 168})],
    'supernova_collapse': [('swirl', {'arms': 4}), ('burst', {'r1': 54, 'r2': 22})],
    'glacial_domain': [('snow', {})],
    'extinction_cataclysm': [('meteor', {'cx': 168, 'cy': 168}), ('bolt', {'s': 0.5, 'cx': 70, 'cy': 90}), ('snow_small', {})],
    # Summoner
    'summon_familiar': [('ghost', {})],
    'call_undead': [('skull', {})],
    'summon_golem_titan': [('golem', {})],
    'legion_of_the_damned': [('skull', {'s': 0.55, 'cx': 70, 'cy': 150}), ('skull', {'s': 0.55, 'cx': 186, 'cy': 150}), ('skull', {'s': 0.7, 'cx': 128, 'cy': 100})],
    'abyssal_drake_awakening': [('drake', {})],
    'army_of_the_dead_sovereign': [('crown', {'s': 0.55, 'cy': 50}), ('skull', {'s': 0.8, 'cy': 150})],
    'mythic_behemoth': [('behemoth', {})],
    # Enchanter
    'mana_dart': [('arrow', {'ang': 45}), ('drop_small', {})],
    'astral_bind': [('chain', {})],
    'mana_siphon': [('drop', {}), ('swirl', {'arms': 2, 'r': 110})],
    'spatial_distortion': [('swirl', {'arms': 4})],
    'absolute_silence': [('note', {'s': 0.8}), ('no', {})],
    'time_stasis_field': [('hourglass', {}), ('ring_waves', {'r0': 116})],
    'world_rewrite': [('rune', {'sides': 5}), ('glyph', {'g': '理', 'size': 76})],
    # Adventurer kit
    'rune_strike': [('sword', {'ang': -45, 'scale': 0.9}), ('rune_small', {})],
    'sidestep': [('wind', {})],
    'second_wind': [('heart', {})],
    'soul_bolt': [('orb', {}), ('arrow_trail', {})],
}

# Effects: (id, label, kind, colour, motif list)
EFFECTS = [
    # buffs
    ('resistance', 'Resistance', 'buff', '#8fb8ff', [('shield', {})]),
    ('regeneration', 'Regeneration', 'buff', '#ff7aa8', [('heart', {}), ('plus_small', {})]),
    ('speed', 'Swiftness', 'buff', '#7fe6ff', [('wings', {})]),
    ('haste', 'Haste', 'buff', '#ffd75a', [('fist', {'s': 0.75}), ('bolt', {'s': 0.4, 'cx': 190, 'cy': 60})]),
    ('absorption', 'Barrier', 'buff', '#ffcf3a', [('heart', {'col': (255, 210, 70)})]),
    ('invulnerable', 'Invulnerable', 'buff', '#fff2a8', [('shield', {}), ('burst_small', {})]),
    ('death_ward', 'Death Ward', 'buff', '#ffe27a', [('ankh', {})]),
    ('damage_store', 'Citadel', 'buff', '#ffb24a', [('tower', {})]),
    ('reflect', 'Reflect', 'buff', '#b8e0ff', [('mirror', {})]),
    ('parry', 'Parry', 'buff', '#e8e8e8', [('crossed_swords', {})]),
    ('empowered', 'Empowered', 'buff', '#ff8a4a', [('sword', {'ang': 0, 'scale': 0.9}), ('arrows_up_small', {})]),
    ('projectile_ward', 'Arrow Ward', 'buff', '#9ad0ff', [('shield', {'s': 0.8}), ('arrow', {'ang': 90, 's': 0.6, 'cy': 128})]),
    ('steadfast', 'Steadfast', 'buff', '#c9c9d6', [('anchor', {})]),
    ('low_gravity', 'Low Gravity', 'buff', '#c8b4ff', [('feather', {})]),
    ('quickened', 'Quickened', 'buff', '#7ff0c8', [('hourglass', {})]),
    ('mana_surge', 'Mana Surge', 'buff', '#5aa8ff', [('drop', {})]),
    ('invisible', 'Unseen', 'buff', '#b0b0c8', [('eye', {'closed': True})]),
    ('linked', 'Shrine Link', 'buff', '#ff8a96', [('chain', {})]),
    # debuffs
    ('silenced', 'Silenced', 'debuff', '#c07bff', [('note', {'s': 0.8}), ('no', {})]),
    ('stunned', 'Stunned', 'debuff', '#ffe066', [('stars_ring', {})]),
    ('sealed', 'Sealed', 'debuff', '#ff5a5a', [('glyph', {'g': '封', 'size': 150})]),
    ('charmed', 'Charmed', 'debuff', '#ff86c8', [('heart', {}), ('swirl_small', {})]),
    ('marked', 'Marked', 'debuff', '#d05aff', [('target', {})]),
    ('armour_broken', 'Armour Broken', 'debuff', '#b0b6c0', [('crack', {})]),
    ('slowed', 'Slowed', 'debuff', '#7aa0c8', [('arrows_down', {})]),
    ('rooted', 'Rooted', 'debuff', '#6ec25a', [('vines', {})]),
    ('weakened', 'Weakened', 'debuff', '#9a8a7a', [('broken_sword', {})]),
    ('darkness', 'Darkness', 'debuff', '#6a5aa8', [('moon', {})]),
    ('burning', 'Burning', 'debuff', '#ff7a2a', [('flame', {})]),
    ('frozen', 'Frozen', 'debuff', '#9fe8ff', [('snow', {})]),
    ('anti_heal', 'Anti-heal', 'debuff', '#ff6a6a', [('heart', {'s': 0.85}), ('no', {})]),
    ('taunted', 'Taunted', 'debuff', '#ff9a3a', [('glyph', {'g': '!', 'size': 190, 'font': LABEL})]),
    ('levitating', 'Levitating', 'debuff', '#e0d0ff', [('arrows_up', {})]),
    ('poisoned', 'Poisoned', 'debuff', '#8ad04a', [('drop', {'col': (120, 200, 70)}), ('skull_small', {})]),
    ('mana_drained', 'Mana Drained', 'debuff', '#4a6aa8', [('drop', {}), ('no', {})]),
    # statuses
    ('in_combat', 'In Combat', 'status', '#ff6a5a', [('crossed_swords', {})]),
    ('resting', 'Resting', 'status', '#ffb45a', [('campfire', {})]),
    ('casting', 'Casting', 'status', '#a07bff', [('rune', {'sides': 5})]),
    ('in_party', 'In Party', 'status', '#6ac8ff', [('figures', {})]),
    ('downed', 'Downed', 'status', '#c0c0c0', [('skull', {})]),
    ('elite', 'Elite', 'status', '#ffb02a', [('skull', {'s': 0.8, 'cy': 140}), ('crown', {'s': 0.45, 'cy': 44})]),
]


# extra small motifs used above
def m_ring_waves(p, C, r0=96):
    for k in range(3):
        p.arc(128, 128, r0 - k * 14, 200 + k * 10, 340 - k * 10, C['ac'], 7)
        p.arc(128, 128, r0 - k * 14, 20 + k * 10, 160 - k * 10, C['ac'], 7)


def m_crack_lines(p, C):
    for a in (20, 140, 260):
        x, y = 128, 128
        pts = [(x, y)]
        for k in range(1, 5):
            ang = math.radians(a + (k % 2) * 18 - 9)
            pts.append((x + k * 26 * math.cos(ang), y + k * 26 * math.sin(ang)))
        p.line(pts, C['ac'], 7)


def m_cloud(p, C, cy=110):
    for cx, ccy, r, col in [(80, cy + 10, 44, C['lo']), (176, cy + 14, 40, C['lo']), (128, cy - 14, 58, C['mid']), (88, cy, 40, C['mid']), (168, cy + 4, 38, C['mid']), (120, cy - 26, 32, C['hi'])]:
        p.circ(cx, ccy, r, fill=col)
    p.d.rounded_rectangle((44, cy + 10, 212, cy + 52), radius=21, fill=C['mid'])


def m_ankh(p, C):
    p.ell(92, 22, 164, 112, outline=C['hi'], width=18)
    p.poly([(118, 104), (138, 104), (144, 236), (112, 236)], C['hi'])
    p.poly([(56, 118), (200, 118), (200, 140), (56, 140)], C['hi'])
    p.circ(128, 66, 10, fill=C['ac'])


def m_flower(p, C):
    for i in range(6):
        a = math.radians(i * 60)
        cx, cy = 128 + 56 * math.cos(a), 128 + 56 * math.sin(a)
        p.circ(cx, cy, 42, fill=C['mid'] if i % 2 else C['hi'])
    p.circ(128, 128, 32, fill=C['ac'])


def m_maw(p, C):
    p.d.pieslice((24, 40, 232, 248), 200, 340, fill=C['mid'])
    p.d.pieslice((24, 8, 232, 216), 20, 160, fill=C['mid'])
    for k in range(5):
        x = 52 + k * 38
        p.poly([(x, 96), (x + 18, 136), (x + 36, 96)], WHITE)
        p.poly([(x, 172), (x + 18, 132), (x + 36, 172)], WHITE)


def m_blade_ring(p, C, n=8, r=96):
    for i in range(n):
        a = i * 360 / n
        x, y = 128 + r * 0.62 * math.cos(math.radians(a)), 128 + r * 0.62 * math.sin(math.radians(a))
        m_dagger(p, C, ang=a + 90 + 30, cx=x, cy=y, scale=0.32)
    p.circ(128, 128, 20, fill=C['ac'])


def m_eclipse(p, C):
    p.circ(128, 128, 104, fill=C['ac'])
    p.circ(128, 128, 88, fill=(10, 6, 16))
    p.circ(146, 112, 80, fill=(0, 0, 0, 0))
    for i in range(16):
        a = math.radians(i * 22.5)
        p.line([(128 + 104 * math.cos(a), 128 + 104 * math.sin(a)), (128 + 122 * math.cos(a), 128 + 122 * math.sin(a))], C['hi'], 5)


def m_anchor(p, C):
    p.ell(104, 22, 152, 70, outline=C['hi'], width=12)
    p.poly([(120, 66), (136, 66), (136, 214), (120, 214)], C['hi'])
    p.poly([(74, 96), (182, 96), (182, 112), (74, 112)], C['mid'])
    p.arc(128, 150, 80, 20, 160, C['hi'], 16)
    for x in (48, 208):
        p.poly([(x - 18, 186), (x, 164), (x + 18, 186)], C['hi'])


def m_broken_sword(p, C):
    m_sword(p, C, -45, 1.1)
    p.line([(108, 92), (168, 120)], (16, 10, 14), 16)
    p.poly([(176, 40), (206, 30), (214, 60)], C['hi'])


def small(fn, **kw):
    def f(p, C):
        fn(p, C, **kw)
    return f


EXTRA = {
    'ring_waves': m_ring_waves, 'crack_lines': m_crack_lines, 'cloud': m_cloud, 'ankh': m_ankh, 'flower': m_flower,
    'maw': m_maw, 'blade_ring': m_blade_ring, 'eclipse': m_eclipse, 'anchor': m_anchor, 'broken_sword': m_broken_sword,
    'target_small': lambda p, C: (p.circ(196, 196, 40, outline=C['ac'], width=8), p.circ(196, 196, 12, fill=C['ac'])),
    'hourglass_small': lambda p, C: (p.poly([(170, 160), (222, 160), (202, 196), (222, 232), (170, 232), (190, 196)], C['ac']), p.poly([(166, 154), (226, 154), (226, 162), (166, 162)], C['hi']), p.poly([(166, 230), (226, 230), (226, 238), (166, 238)], C['hi'])),
    'heart_small': lambda p, C: m_heart(p, C, 196, 200, 0.35, C['ac']),
    'palm_small': lambda p, C: p.circ(196, 196, 30, fill=C['ac']),
    'snow_small': lambda p, C: m_snow(p, C, 70, 186, 44),
    'drop_small': lambda p, C: m_drop(p, C, 70, 180, 0.4),
    'rune_small': lambda p, C: (p.circ(186, 186, 46, outline=C['ac'], width=8), p.circ(186, 186, 12, fill=C['ac'])),
    'arrow_trail': lambda p, C: [p.circ(128 - 40 - k * 24, 128 + 40 + k * 24, 16 - k * 4, fill=C['mid']) for k in range(3)],
    'plus_small': lambda p, C: m_cross(p, C, 190, 190, 0.35),
    'burst_small': lambda p, C: p.poly(star_pts(196, 60, 40, 16, 4), WHITE),
    'arrows_up_small': lambda p, C: p.poly([(176, 90), (200, 50), (224, 90), (210, 90), (210, 130), (190, 130), (190, 90)], C['ac']),
    'swirl_small': lambda p, C: m_swirl(p, C, 196, 60, 2, 40),
    'skull_small': lambda p, C: m_skull(p, C, 196, 190, 0.35),
}
MOTIFS = {k[2:]: v for k, v in globals().items() if k.startswith('m_') and callable(v)}
MOTIFS.update(EXTRA)
MOTIFS['no'] = lambda p, C, **kw: no(p, C, None)


# ───────────────────────── composition ─────────────────────────

TIER_FRAME = {
    'BASIC': ((120, 124, 132), (70, 72, 78)),
    'INTERMEDIATE': ((210, 216, 226), (110, 116, 128)),
    'ADVANCED': ((90, 170, 255), (30, 70, 140)),
    'SAINT': ((190, 120, 255), (80, 40, 140)),
    'KING': ((255, 208, 70), (140, 92, 10)),
    'EMPEROR': ((255, 96, 64), (120, 20, 20)),
    'GOD': ((255, 250, 225), (210, 160, 40)),
    'ADVENTURER': ((170, 190, 220), (60, 70, 90)),
}
KIND_FRAME = {'buff': ((120, 230, 140), (30, 90, 40)), 'debuff': ((255, 90, 80), (110, 20, 20)), 'status': ((120, 180, 255), (30, 60, 110))}


def background(prim, dark):
    bg = Image.new('RGB', (S, S), dark)
    px = bg.load()
    centre = mix(prim, dark, 0.35)
    for y in range(S):
        for x in range(S):
            d = math.hypot(x - 128, y - 110) / 181
            k = min(1, d ** 1.25)
            c = mix(centre, dark, k)
            # soft diagonal sheen
            s = max(0, 1 - abs((x - y) / 60)) * 0.08
            px[x, y] = mix(c, WHITE, s)
    return bg.convert('RGBA')


def frame(im, outer, inner, tier):
    d = ImageDraw.Draw(im)
    w = 14
    d.rectangle((0, 0, S - 1, S - 1), outline=inner, width=w)
    d.rectangle((3, 3, S - 4, S - 4), outline=outer, width=6)
    d.rectangle((w, w, S - 1 - w, S - 1 - w), outline=mix(outer, BLACK, 0.5), width=3)
    if tier in ('KING', 'EMPEROR', 'GOD'):
        for cx, cy in ((10, 10), (S - 11, 10), (10, S - 11), (S - 11, S - 11)):
            d.polygon([(cx, cy - 14), (cx + 14, cy), (cx, cy + 14), (cx - 14, cy)], fill=outer, outline=inner)
    if tier == 'EMPEROR':
        d.rectangle((9, 9, S - 10, S - 10), outline=(255, 205, 80), width=3)
    if tier == 'GOD':
        d.rectangle((9, 9, S - 10, S - 10), outline=(255, 215, 90), width=4)
        for cx, cy in ((10, 10), (S - 11, 10), (10, S - 11), (S - 11, S - 11)):
            d.ellipse((cx - 6, cy - 6, cx + 6, cy + 6), fill=(120, 220, 255))


def compose(C, motifs, outer, inner, tier, rays=False):
    pal_bg = background(C['prim'], C['dark'])
    if rays:
        r = Image.new('RGBA', (S, S), (0, 0, 0, 0))
        rd = ImageDraw.Draw(r)
        for i in range(16):
            a = math.radians(i * 22.5)
            rd.polygon([(128, 128), (128 + 200 * math.cos(a - 0.07), 128 + 200 * math.sin(a - 0.07)), (128 + 200 * math.cos(a + 0.07), 128 + 200 * math.sin(a + 0.07))], fill=(255, 245, 200, 46))
        pal_bg = Image.alpha_composite(pal_bg, r.filter(ImageFilter.GaussianBlur(3)))
    pen = Pen()
    cols = {'hi': C['hi'], 'mid': C['mid'], 'lo': C['lo'], 'ac': C['ac']}
    for name, kw in motifs:
        fn = MOTIFS[name]
        fn(pen, cols, **kw)
    ink = pen.im
    # glow behind the motif in the accent colour
    a = ink.split()[3]
    glow = Image.new('RGBA', (S, S), C['glow'] + (0,))
    glow.putalpha(a.filter(ImageFilter.GaussianBlur(12)).point(lambda v: min(255, int(v * 1.4))))
    # dark rim around the motif so it reads on any background
    rim = Image.new('RGBA', (S, S), (8, 6, 12, 0))
    rim.putalpha(a.filter(ImageFilter.MaxFilter(9)).filter(ImageFilter.GaussianBlur(2)).point(lambda v: int(v * 0.8)))
    out = Image.alpha_composite(pal_bg, glow)
    out = Image.alpha_composite(out, rim)
    out = Image.alpha_composite(out, ink)
    frame(out, outer, inner, tier)
    small = out.resize((OUT, OUT), Image.LANCZOS)
    return small.filter(ImageFilter.UnsharpMask(radius=1, percent=60, threshold=2))


def colours(prim, sec, acc, dark):
    hi = mix(acc, WHITE, 0.55)
    return {'prim': prim, 'dark': mix(dark, BLACK, 0.55), 'hi': hi, 'mid': mix(prim, WHITE, 0.25), 'lo': mix(prim, dark, 0.55),
            'ac': sec if sum(sec) < 700 else acc, 'glow': acc}


# ───────────────────────── sheets ─────────────────────────

def sheet(items, title, path, cols=7, scale=2):
    cell_w, cell_h = OUT * scale + 80, OUT * scale + 54
    rows = (len(items) + cols - 1) // cols
    W, H = cols * cell_w + 40, rows * cell_h + 90
    sh = Image.new('RGB', (W, H), (20, 18, 28))
    d = ImageDraw.Draw(sh)
    ft = ImageFont.truetype(LABEL, 30)
    fl = ImageFont.truetype(LABEL, 15)
    d.text((24, 22), title, font=ft, fill=(240, 232, 255))
    for i, (img, label, sub) in enumerate(items):
        x = 20 + (i % cols) * cell_w + 40
        y = 80 + (i // cols) * cell_h
        sh.paste(img.resize((OUT * scale, OUT * scale), Image.NEAREST), (x, y), img.resize((OUT * scale, OUT * scale), Image.NEAREST))
        for k, t in enumerate([label, sub]):
            if not t:
                continue
            b = d.textbbox((0, 0), t, font=fl)
            d.text((x + OUT * scale / 2 - (b[2] - b[0]) / 2, y + OUT * scale + 4 + k * 17), t, font=fl, fill=(220, 214, 236) if k == 0 else (150, 144, 170))
    sh.save(path)


def main():
    classes_yml, out_dir = sys.argv[1], sys.argv[2]
    sheet_dir = sys.argv[3] if len(sys.argv) > 3 else None
    pal, skills = palettes(classes_yml)
    os.makedirs(os.path.join(out_dir, 'skill'), exist_ok=True)
    os.makedirs(os.path.join(out_dir, 'effect'), exist_ok=True)
    by_class = {}
    missing = []
    for cls, tier, sid, name in skills:
        P = pal.get(cls) or pal.get('adventurer')
        motifs = SKILLS.get(sid)
        if motifs is None:
            missing.append(sid)
            motifs = [('rune', {})]
        prim = P['secondary'] if sum(P['primary']) > 600 else P['primary']   # near-white palettes (Adventurer) wash out
        C = colours(prim, P['secondary'], P['accent'], P['dark'])
        outer, inner = TIER_FRAME[tier]
        img = compose(C, motifs, outer, inner, tier, rays=tier in ('GOD',))
        img.save(os.path.join(out_dir, 'skill', sid + '.png'))
        by_class.setdefault(cls, []).append((img, re.sub(r'^\w+ God: ', '', name), tier.title()))
    effects = []
    for eid, label, kind, col, motifs in EFFECTS:
        c = rgb(col)
        C = {'prim': mix(c, BLACK, 0.45), 'dark': mix(c, BLACK, 0.88), 'hi': mix(c, WHITE, 0.6), 'mid': mix(c, WHITE, 0.15), 'lo': mix(c, BLACK, 0.45),
             'ac': mix(c, WHITE, 0.85) if kind != 'debuff' else (255, 230, 230), 'glow': c}
        outer, inner = KIND_FRAME[kind]
        img = compose(C, motifs, outer, inner, 'BASIC')
        img.save(os.path.join(out_dir, 'effect', eid + '.png'))
        effects.append((img, label, kind.title()))
    print(f'{len(skills)} skill icons, {len(effects)} effect icons; no motif for: {missing or "none"}')
    if sheet_dir:
        os.makedirs(sheet_dir, exist_ok=True)
        order = ['guardian', 'samurai', 'monk', 'assassin', 'swashbuckler', 'bard', 'cleric', 'druid', 'kannagi', 'sorcerer', 'summoner', 'enchanter']
        groups = [order[i:i + 4] for i in range(0, 12, 4)]
        names = ['Warrior · Weapon', 'Weapon · Recovery', 'Recovery · Magic']
        for gi, grp in enumerate(groups):
            items = []
            for c in grp:
                items += [(img, n, f'{c.title()} · {t}') for img, n, t in by_class[c]]
            sheet(items, f'RuneBlock skill icons ({gi + 1}/3): ' + ', '.join(c.title() for c in grp), os.path.join(sheet_dir, f'skills_{gi + 1}.png'))
        sheet([(img, n, 'Adventurer') for img, n, t in by_class.get('adventurer', [])], 'RuneBlock skill icons: Adventurer kit', os.path.join(sheet_dir, 'skills_adventurer.png'), cols=4)
        sheet(effects, 'RuneBlock status icons: buffs, debuffs, statuses', os.path.join(sheet_dir, 'effects.png'), cols=8)


if __name__ == '__main__':
    main()
