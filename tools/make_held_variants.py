"""Gauntlets and grimoires outside the metal line (ArcaneSouls 0.28.1, kuwusaki 2026-10-18: "monk uses gauntlets,
sorcerer uses the book"). Drawn by the metal-weapon code (weapon_art.py sprite in the inventory, held_models.py 3D
glove / open book in the hand) with an extra palette registered as a "metal" (mythic detail: gems, glow, trims):

  class_monk_weapon     -> palette `class_monk`     (Iron Lotus set: main ramp, red accent)
  class_sorcerer_weapon -> palette `class_sorcerer` (Archmage set: violet ramp, cyan accent, gold trim)
  rimeforged_gauntlet / _grimoire -> `rimeforged` (dark steel, ice-cyan glow, as the Rimeforged staff)
  sunforged_gauntlet / _grimoire  -> `sunforged`  (charcoal, amber-gold glow, as the Sunforged staff)

Files land next to the metal ones (textures/item/gear/metal/<palette>_*, models/item/gear/<palette>_*).
Usage: python3 -I tools/make_held_variants.py [--pack pack]
"""
import argparse, json, os, sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import weapon_art as W
import held_models as H
import make_class_armour as M

PALETTES = {   # name -> (5-step body ramp: outline .. highlight, accent, trim ramp key in W.FIXED or None = gold)
    'class_monk': (['#1e0c03'] + M.CLASSES['monk'][1], M.CLASSES['monk'][2][2], None),
    'class_sorcerer': (['#07040f'] + M.CLASSES['sorcerer'][1], M.CLASSES['sorcerer'][2][2], None),
    'rimeforged': (['#05060e', '#141a2e', '#2a3c5c', '#5f8fb8', '#d6f4ff'], '#3ad6e8', 'iron'),
    'sunforged': (['#070707', '#1e1c1e', '#3a3436', '#5e5456', '#8e8284'], '#ffb41e', None),
}
ITEMS = [   # item id (gear.yml `model: runeblock:<id>`), palette, kind
    ('class_monk_weapon', 'class_monk', 'gauntlet'), ('class_sorcerer_weapon', 'class_sorcerer', 'grimoire'),
    ('rimeforged_gauntlet', 'rimeforged', 'gauntlet'), ('rimeforged_grimoire', 'rimeforged', 'grimoire'),
    ('sunforged_gauntlet', 'sunforged', 'gauntlet'), ('sunforged_grimoire', 'sunforged', 'grimoire'),
]


def register(name):
    ramp, gem, trim = PALETTES[name]
    W.METALS[name], W.TIER[name], W.GEM[name] = ramp, 2, gem
    if trim: W.TRIM[name] = trim


_art_init = W.Art.__init__
def _init(self, metal):   # these palettes also colour what is leather on a metal weapon (the grimoire cover)
    _art_init(self, metal)
    if metal in PALETTES: self.ramps['leather'] = self.ramps['metal']
W.Art.__init__ = _init


def main():
    here = os.path.dirname(os.path.abspath(__file__))
    ap = argparse.ArgumentParser(); ap.add_argument('--pack', default=os.path.join(here, '..', 'pack'))
    rb = os.path.join(ap.parse_args().pack, 'assets', 'runeblock')
    tex = os.path.join(rb, 'textures/item/gear/metal')
    for name in PALETTES: register(name)
    for item, pal, kind in ITEMS:
        flat = f'{pal}_{kind}'
        W.sprite(kind, pal).save(os.path.join(tex, flat + '.png'), optimize=True)
        H._save_json(os.path.join(rb, 'models/item/gear', flat + '.json'),
                     {'parent': 'minecraft:item/generated', 'textures': {'layer0': f'runeblock:item/gear/metal/{flat}'}})
        if kind == 'gauntlet':
            H.gauntlet_texture(pal).save(os.path.join(tex, f'{pal}_gauntlet_3d.png'), optimize=True)
            held = f'{pal}_gauntlet_worn'
            H._save_json(os.path.join(rb, 'models/item/gear', held + '.json'), H.gauntlet_model(pal))
        else:
            trim, gem = H.small_textures(pal)
            trim.save(os.path.join(tex, f'{pal}_trim.png'), optimize=True); gem.save(os.path.join(tex, f'{pal}_gem.png'), optimize=True)
            H.page_frames(pal).save(os.path.join(tex, f'{pal}_grimoire_pages.png'), optimize=True)
            H._save_json(os.path.join(tex, f'{pal}_grimoire_pages.png.mcmeta'), {'animation': {'frametime': 2}})
            held = f'{pal}_grimoire_open'
            H._save_json(os.path.join(rb, 'models/item/gear', held + '.json'), H.grimoire_model(pal))
        H._save_json(os.path.join(rb, 'items', item + '.json'),
                     H.select(f'runeblock:item/gear/{flat}', f'runeblock:item/gear/{held}'))
        print(item, pal, kind, 'ok')


if __name__ == '__main__':
    main()
