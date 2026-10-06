#!/usr/bin/env python3
"""Generate the chest-menu panels (pack/assets/runeblock/textures/gui/*.png).

Each panel is a 176x222 picture of a 6-row chest screen (vanilla generic_54 geometry) in the asc-mmo-gui
dark-fantasy palette. The server puts it in the menu TITLE as a glyph of the runeblock:gui font, so it is drawn
1:1 over the vanilla chest background; item slots stay where vanilla puts them, so every cell here must line up
with a slot: top inventory (7 + 18*col, 17 + 18*row), player inventory (7 + 18*col, 139 + 18*row), hotbar y 197.

  python3 tools/gen_gui.py      # rewrites the PNGs; commit them with the change
"""
import os
from PIL import Image, ImageDraw

OUT = os.path.join(os.path.dirname(__file__), '..', 'pack', 'assets', 'runeblock', 'textures', 'gui')
W, H = 176, 222

def rgb(v):  # 0xRRGGBB -> tuple
    return ((v >> 16) & 255, (v >> 8) & 255, v & 255, 255)

# asc-mmo-gui UiTheme
BG_TOP, BG_BOT = rgb(0x140C0E), rgb(0x070405)
BAND_TOP, BAND_BOT = rgb(0x221315), rgb(0x140A0C)
FRAME, ORNAMENT, GOLD, EMBER, MUTED = rgb(0x4A3528), rgb(0x8A6A3A), rgb(0xD4A64A), rgb(0xE8823A), rgb(0x8C7F72)
CELL, CELL_DARK, CELL_LIGHT = rgb(0x0E0809), rgb(0x050203), rgb(0x2A1C1A)


def lerp(a, b, t):
    return tuple(int(a[i] + (b[i] - a[i]) * t) for i in range(4))


def base():
    im = Image.new('RGBA', (W, H))
    d = ImageDraw.Draw(im)
    for y in range(H):
        d.line([(0, y), (W - 1, y)], fill=lerp(BG_TOP, BG_BOT, y / (H - 1)))
    for y in range(1, 15):  # title band
        d.line([(2, y), (W - 3, y)], fill=lerp(BAND_TOP, BAND_BOT, y / 14))
    d.line([(4, 15), (W - 5, 15)], fill=ORNAMENT)
    # outer frame: bronze 2px + ornament inner line
    d.rectangle([0, 0, W - 1, H - 1], outline=FRAME)
    d.rectangle([1, 1, W - 2, H - 2], outline=FRAME)
    d.rectangle([2, 2, W - 3, H - 3], outline=rgb(0x2A1D16))
    # gold corner brackets
    for cx, cy, sx, sy in [(1, 1, 1, 1), (W - 2, 1, -1, 1), (1, H - 2, 1, -1), (W - 2, H - 2, -1, -1)]:
        d.line([(cx, cy), (cx + 7 * sx, cy)], fill=GOLD)
        d.line([(cx, cy), (cx, cy + 7 * sy)], fill=GOLD)
        d.point((cx + sx, cy + sy), fill=GOLD)
    # divider above the player inventory (the vanilla "Inventory" label is blanked by the pack's lang file)
    d.line([(6, 130), (W - 7, 130)], fill=FRAME)
    d.line([(6, 131), (W - 7, 131)], fill=ORNAMENT)
    for x in (W // 2 - 3, W // 2, W // 2 + 3):
        d.point((x, 133), fill=GOLD)
    return im, d


def cell(d, x, y, ring=None, fill=CELL):
    """A recessed 18x18 slot cell at (x, y). ring = colour of the cell's own 1px border (slot rows touch, so a
    frame outside the cell would overlap the next row). Everything is opaque: a translucent pixel in a font glyph
    becomes a hole in the panel."""
    d.rectangle([x, y, x + 17, y + 17], fill=fill)
    if ring:
        d.rectangle([x, y, x + 17, y + 17], outline=ring)
        d.rectangle([x + 1, y + 1, x + 16, y + 16], outline=CELL_DARK)
        return
    d.line([(x, y), (x + 16, y)], fill=CELL_DARK)
    d.line([(x, y), (x, y + 16)], fill=CELL_DARK)
    d.line([(x + 1, y + 17), (x + 17, y + 17)], fill=CELL_LIGHT)
    d.line([(x + 17, y + 1), (x + 17, y + 17)], fill=CELL_LIGHT)


def top(slot):
    return 7 + 18 * (slot % 9), 17 + 18 * (slot // 9)


def player_cells(d):
    for r in range(3):
        for c in range(9):
            cell(d, 7 + 18 * c, 139 + 18 * r)
    for c in range(9):
        cell(d, 7 + 18 * c, 197)


def panel_54():
    im, d = base()
    for s in range(54):
        cell(d, *top(s))
    player_cells(d)
    return im


def codex():
    im, d = base()
    # header: the Codex book, gold border on an ember-tinted cell
    cell(d, *top(4), ring=GOLD, fill=rgb(0x2A140C))
    for s in range(10, 17):                  # character: Character · Classes · Skills · Armory · Quests · Party · Lore
        cell(d, *top(s), ring=GOLD, fill=rgb(0x1E140C))
    for s in (19, 20, 21):                   # world: Regions · Sanctuaries & Travel · Bestiary
        cell(d, *top(s), ring=ORNAMENT, fill=rgb(0x18100C))
    for s in (23, 24, 25):                   # coming soon
        cell(d, *top(s), ring=FRAME)
    player_cells(d)
    return im


if __name__ == '__main__':
    os.makedirs(OUT, exist_ok=True)
    for name, fn in (('panel_54', panel_54), ('codex', codex)):
        im = fn()
        assert im.size == (W, H)
        im.save(os.path.join(OUT, name + '.png'))
        print('wrote', name, im.size)
