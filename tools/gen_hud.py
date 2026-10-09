#!/usr/bin/env python3
"""Generate the MMO bottom HUD (indigo's HUD proposal, #brainstorming 2026-10-08; kuwusaki: keep the crosshair).

Writes two sets of pictures, in the asc-mmo-gui dark-fantasy palette:
  pack/assets/minecraft/textures/gui/sprites/hud/   vanilla sprite overrides in this pack:
      hotbar.png (182x22) + hotbar_selection.png (24x23): reskinned hotbar, same geometry, so the 9 slots, the
      selection and the 1-9 keys work exactly as vanilla
      heart/*, food_*, armor_*: blanked (9x9 transparent). Vehicle hearts, air bubbles, XP bar and crosshair stay
  betterhud/assets/   BetterHud images (upload to the box's plugins/BetterHud/assets/):
      rb_hp_frame / rb_hp_fill (red) + rb_mana_frame / rb_mana_fill (blue): 90x9 bars over the hotbar, where the
      hearts and drumsticks were

  python3 tools/gen_hud.py      # rewrites the PNGs; commit them with the change
"""
import os
from PIL import Image, ImageDraw

ROOT = os.path.join(os.path.dirname(__file__), '..')
SPRITES = os.path.join(ROOT, 'pack', 'assets', 'minecraft', 'textures', 'gui', 'sprites', 'hud')
BH = os.path.join(ROOT, 'betterhud', 'assets')


def rgb(v, a=255):  # 0xRRGGBB -> tuple
    return ((v >> 16) & 255, (v >> 8) & 255, v & 255, a)


# asc-mmo-gui UiTheme
FRAME, ORNAMENT, GOLD, EMBER = rgb(0x4A3528), rgb(0x8A6A3A), rgb(0xD4A64A), rgb(0xE8823A)
CELL, CELL_DARK, CELL_LIGHT = rgb(0x0E0809), rgb(0x050203), rgb(0x2A1C1A)
SOOT = rgb(0x140C0E, 235)
HP_HI, HP_MID, HP_LO = rgb(0xF06A5A), rgb(0xC23A3A), rgb(0x7A1A1E)
MP_HI, MP_MID, MP_LO = rgb(0x8FC4FF), rgb(0x3F7FE0), rgb(0x1C3A82)
CLEAR = (0, 0, 0, 0)


def save(im, *path):
    p = os.path.join(*path)
    os.makedirs(os.path.dirname(p), exist_ok=True)
    im.save(p)


# ───────────────────────────── hotbar ─────────────────────────────

def hotbar():
    """182x22: 1px frame, 9 cells of 20px (vanilla item slot = x 3+20i, y 3, 16x16)."""
    im = Image.new('RGBA', (182, 22), SOOT)
    d = ImageDraw.Draw(im)
    d.rectangle([0, 0, 181, 21], outline=FRAME)
    d.line([(1, 1), (180, 1)], fill=ORNAMENT)          # top highlight
    for i in range(9):
        x = 1 + 20 * i
        d.rectangle([x + 1, 2, x + 18, 19], fill=CELL, outline=CELL_DARK)
        d.line([(x + 1, 19), (x + 18, 19)], fill=CELL_LIGHT)   # bevel
        d.line([(x + 18, 2), (x + 18, 19)], fill=CELL_LIGHT)
        if i:
            d.line([(x, 2), (x, 20)], fill=FRAME)        # divider
            d.point((x, 1), fill=GOLD)                    # rivet
            d.point((x, 20), fill=GOLD)
    for x, y in ((0, 0), (181, 0), (0, 21), (181, 21)):
        d.point((x, y), fill=GOLD)
    return im


def selection():
    """24x23, drawn at (slot x - 1, -1): gold frame with ember corners, clear inside."""
    im = Image.new('RGBA', (24, 23), CLEAR)
    d = ImageDraw.Draw(im)
    d.rectangle([0, 0, 23, 22], outline=GOLD)
    d.rectangle([1, 1, 22, 21], outline=rgb(0x8A6A3A, 200))
    for x, y in ((0, 0), (23, 0), (0, 22), (23, 22)):
        d.point((x, y), fill=EMBER)
    for x, y in ((1, 0), (0, 1), (22, 0), (23, 1), (1, 22), (0, 21), (22, 22), (23, 21)):
        d.point((x, y), fill=EMBER)
    return im


# ───────────────────────────── bars ─────────────────────────────

BAR_W, BAR_H = 90, 9
FILL_W, FILL_H = 86, 5      # placed at (2, 2) inside the frame


def frame(mirror):
    im = Image.new('RGBA', (BAR_W, BAR_H), CLEAR)
    d = ImageDraw.Draw(im)
    d.rectangle([0, 0, BAR_W - 1, BAR_H - 1], fill=CELL_DARK, outline=FRAME)
    d.line([(1, 1), (BAR_W - 2, 1)], fill=CELL)
    d.rectangle([1, 1, BAR_W - 2, BAR_H - 2], outline=CELL)
    # gold cap on the outer end (left for HP, right for mana)
    cap = BAR_W - 1 if mirror else 0
    d.line([(cap, 1), (cap, BAR_H - 2)], fill=GOLD)
    d.point((cap, 0), fill=ORNAMENT)
    d.point((cap, BAR_H - 1), fill=ORNAMENT)
    return im


def fill(hi, mid, lo):
    im = Image.new('RGBA', (FILL_W, FILL_H), CLEAR)
    d = ImageDraw.Draw(im)
    rows = [hi, mid, mid, lo, lo]
    for y, c in enumerate(rows):
        d.line([(0, y), (FILL_W - 1, y)], fill=c)
    for x in range(0, FILL_W, 6):          # faint segment ticks
        d.point((x, 1), fill=rgb(0xFFFFFF, 70))
    return im


def main():
    save(hotbar(), SPRITES, 'hotbar.png')
    save(selection(), SPRITES, 'hotbar_selection.png')
    blank = Image.new('RGBA', (9, 9), CLEAR)
    vanilla_hearts = ['container', 'full', 'half', 'hardcore_full', 'hardcore_half']
    kinds = ['', 'poisoned_', 'withered_', 'frozen_', 'absorbing_']
    for k in kinds:
        for h in (['full', 'half', 'hardcore_full', 'hardcore_half'] if k else vanilla_hearts):
            for blink in ('', '_blinking'):
                save(blank, SPRITES, 'heart', k + h + blink + '.png')
    for n in ('container_hardcore',):
        for blink in ('', '_blinking'):
            save(blank, SPRITES, 'heart', n + blink + '.png')
    for n in ('food_empty', 'food_empty_hunger', 'food_full', 'food_full_hunger', 'food_half', 'food_half_hunger',
              'armor_empty', 'armor_full', 'armor_half'):
        save(blank, SPRITES, n + '.png')
    save(frame(False), BH, 'rb_hp_frame.png')
    save(frame(True), BH, 'rb_mana_frame.png')
    save(fill(HP_HI, HP_MID, HP_LO), BH, 'rb_hp_fill.png')
    save(fill(MP_HI, MP_MID, MP_LO), BH, 'rb_mana_fill.png')


if __name__ == '__main__':
    main()
