#!/usr/bin/env python3
"""Tooltip layout mockups (weapon / armour / accessory) in the RuneBlock tooltip frame, drawn with the vanilla font.
For confirming a tooltip layout before it is built (Ett, dev-chat 2026-11-08). Not an in-game screenshot.
Usage: python3 tools/tooltip_mock.py --ascii <vanilla font/ascii.png> --sprites <dir with runeblock_background.png + _frame.png>
       --inventory <inventory.png> --out sheet.png
"""
import argparse
from PIL import Image

C = {'white': (255, 255, 255), 'gray': (170, 170, 170), 'dgray': (85, 85, 85), 'green': (85, 255, 85), 'red': (255, 85, 85),
     'gold': (255, 170, 0), 'yellow': (255, 255, 85), 'aqua': (85, 255, 255), 'daqua': (0, 170, 170), 'bone': (232, 220, 196)}

CHECK = ["......#", ".....##", "#...##.", "##.##..", ".###...", "..#...."]
CROSS = ["#....#", ".#..#.", "..##..", "..##..", ".#..#.", "#....#"]
HEART = [".##.##.", "#######", "#######", ".#####.", "..###..", "...#..."]
SHIELD = ["#######", "#######", "#######", ".#####.", "..###..", "...#..."]
SWORD = ["......#", ".....#.", "#...#..", ".#.#...", "..#....", ".#.#...", "#......"]
ICONS = {'check': CHECK, 'cross': CROSS, 'heart': HEART, 'shield': SHIELD, 'sword': SWORD}


class Font:
    def __init__(self, path):
        self.img = Image.open(path).convert('RGBA')
        self.w = {}
        px = self.img.load()
        for code in range(256):
            gx, gy = (code % 16) * 8, (code // 16) * 8
            right = -1
            for x in range(8):
                if any(px[gx + x, gy + y][3] for y in range(8)): right = x
            self.w[code] = 4 if code == 32 else right + 2

    def width(self, s): return sum(self.w.get(ord(ch), 6) for ch in s if ord(ch) < 256)

    def draw(self, dst, x, y, s, col):
        for shadow in (True, False):
            cx = x
            c = tuple(v // 4 for v in col) if shadow else col
            for ch in s:
                code = ord(ch)
                if code >= 256: continue
                gx, gy = (code % 16) * 8, (code // 16) * 8
                glyph = self.img.crop((gx, gy, gx + 8, gy + 8))
                tint = Image.new('RGBA', (8, 8), c + (255,))
                tint.putalpha(glyph.getchannel('A'))
                dst.alpha_composite(tint, (cx + (1 if shadow else 0), y + (1 if shadow else 0)))
                cx += self.w.get(code, 6)
        return cx


def icon(dst, x, y, name, col):
    for r, row in enumerate(ICONS[name]):
        for c, ch in enumerate(row):
            if ch == '#':
                dst.putpixel((x + c + 1, y + r + 2), tuple(v // 4 for v in col) + (255,))
    for r, row in enumerate(ICONS[name]):
        for c, ch in enumerate(row):
            if ch == '#': dst.putpixel((x + c, y + r + 1), col + (255,))
    return x + len(ICONS[name][0]) + 2


def nine(src, w, h, border):
    out = Image.new('RGBA', (w, h)); sw, sh = src.size
    for (sx0, sx1, dx0, dx1) in ((0, border, 0, border), (border, sw - border, border, w - border), (sw - border, sw, w - border, w)):
        for (sy0, sy1, dy0, dy1) in ((0, border, 0, border), (border, sh - border, border, h - border), (sh - border, sh, h - border, h)):
            if dx1 > dx0 and dy1 > dy0:
                out.alpha_composite(src.crop((sx0, sy0, sx1, sy1)).resize((dx1 - dx0, dy1 - dy0), Image.NEAREST), (dx0, dy0))
    return out


def tooltip(font, bg, fr, lines):
    """lines: list of None (blank) or list of segments (text, colour) / ('@icon', colour). Vanilla spacing: title + 2 px."""
    def seg_w(segs): return sum(len(ICONS[t[1:]][0]) + 2 if t.startswith('@') else font.width(t) for t, _ in segs)
    w = max(seg_w(l) for l in lines if l)
    h = 0
    for i, l in enumerate(lines): h += 10 + (2 if i == 0 else 0)
    h -= 2
    pad = 12   # the sprite draws 3 px outside the text plus its own 9 px margin
    W, H = w + 2 * pad, h + 2 * pad
    out = Image.new('RGBA', (W, H), (0, 0, 0, 0))
    out.alpha_composite(nine(bg, W, H, 9)); out.alpha_composite(nine(fr, W, H, 10))
    y = pad
    for i, l in enumerate(lines):
        if l is None: y += 10; continue
        x = pad
        for t, col in l:
            x = icon(out, x, y, t[1:], C[col]) if t.startswith('@') else font.draw(out, x, y, t, C[col])
        y += 10 + (2 if i == 0 else 0)
    return out


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--ascii', required=True); ap.add_argument('--sprites', required=True)
    ap.add_argument('--inventory'); ap.add_argument('--out', required=True)
    a = ap.parse_args()
    font = Font(a.ascii)
    bg = Image.open(f'{a.sprites}/runeblock_background.png').convert('RGBA')
    fr = Image.open(f'{a.sprites}/runeblock_frame.png').convert('RGBA')
    # real gear.yml items; Uncommon = x1.5 stats + 1 socket (rarities in gear.yml)
    weapon = [[('Iron Katana', 'green')],
              [('Fast Attack Speed', 'gray')],
              None,
              [('@sword', 'gold'), ('Damage: ', 'gold'), ('4.6 per hit', 'white')],
              None,
              [('@check', 'green'), ('Class Req: ', 'gray'), ('Warrior', 'white')],
              None,
              [('+5.4% ', 'green'), ('Damage', 'gray')],
              [('+2.7% ', 'green'), ('Crit Chance', 'gray')],
              None,
              [('[0/1] Gem Sockets', 'daqua')],
              [('Uncommon Weapon', 'green'), (' - Novice', 'dgray')]]
    armour = [[('Bastion Cuirass', 'green')],
              None,
              [('@heart', 'red'), ('Health: ', 'red'), ('+6', 'white')],
              [('@shield', 'gold'), ('Defense: ', 'gold'), ('+7.5%', 'white')],
              None,
              [('@check', 'green'), ('Class Req: ', 'gray'), ('Warrior', 'white')],
              [('@cross', 'red'), ('Level Min: ', 'gray'), ('15', 'white')],
              None,
              [('[0/1] Gem Sockets', 'daqua')],
              [('Uncommon Chestplate', 'green'), (' - Artisan', 'dgray')]]
    accessory = [[('Ember Pendant', 'white')],
                 [('Necklace', 'gray')],
                 None,
                 [('No stats (test item)', 'dgray')],
                 None,
                 [('Common Necklace', 'white'), (' - Novice', 'dgray')],
                 [('Wear it in the Necklace slot.', 'dgray')]]
    tips = [tooltip(font, bg, fr, t) for t in (weapon, armour, accessory)]
    S = 3
    inv = Image.open(a.inventory).convert('RGBA').crop((0, 0, 176, 166)) if a.inventory else None
    gap = 8
    W = sum(t.size[0] for t in tips) + gap * (len(tips) + 1) + (176 + gap if inv else 0)
    H = max([t.size[1] for t in tips] + ([166] if inv else [])) + 2 * gap
    sheet = Image.new('RGBA', (W, H), (34, 30, 30, 255))
    x = gap
    if inv: sheet.alpha_composite(inv, (x, gap)); x += 176 + gap
    for t in tips: sheet.alpha_composite(t, (x, gap)); x += t.size[0] + gap
    sheet.resize((W * S, H * S), Image.NEAREST).save(a.out)


if __name__ == '__main__':
    main()
