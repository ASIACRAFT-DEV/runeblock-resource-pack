#!/usr/bin/env python3
"""The armour still to draw: 15 standalone lines, 7 Mythic pieces (The Last Crown is in mythic_art.py) and the 12 Unique sets."""
from gear_armour import boots, chest, helm, legs

ARMOUR = {}


def line(names, h, c, l, b, **base):
    for name, fn, o in zip(names, (helm, chest, legs, boots), (h, c, l, b)):
        if name:
            ARMOUR[name] = (fn, {**base, **o})


# ---- Common
line(('Ironbound Cap', 'Ironbound Chestguard', 'Ironbound Legguards', 'Ironbound Boots'), dict(v='cap'), dict(v='plate', sh='round', rivets=1), dict(v='greaves'), dict(v='plated'), m='stone', t='iron', a='steel')
line(("Scout's Mask", 'Padded Coat', 'Padded Leggings', "Scout's Boots"), dict(v='mask', t='sand'), dict(v='coat', quilt=1), dict(v='cloth', t='oak'), dict(v='leather'), m='hide', t='oak', a='sand')
line(('Hedgeweave Hood', 'Hedgeweave Tunic', 'Hedgeweave Trousers', 'Hedgeweave Slippers'), dict(v='hood', eye='lime', hs='leaf'), dict(v='vest'), dict(v='cloth'), dict(v='slipper'), m='moss', t='oak', a='straw', mot='vine')
# ---- Uncommon
line(('Steel Visor', 'Steelguard', 'Steel Legguards', 'Steelwalkers'), dict(v='visor'), dict(v='plate', sh='round', g='sky', set='moon'), dict(v='greaves'), dict(v='plated'), m='steel', t='moon', a='white')
line(('Wolfskin Cowl', 'Wolfhide Vest', 'Wolfhide Leggings', 'Wolfhide Boots'), dict(v='cowl', eye='amber'), dict(v='vest', sh='fur'), dict(v='cloth'), dict(v='leather', cuff='fur'), m='fur', t='hide', a='bone')
line(('Ember Crown', 'Emberplate', 'Ember Greaves', 'Emberstride'), dict(v='crown', cs='flame', m='gold', t='crimson', a='ember', g='ember'), dict(v='plate', sh='ember', g='ember', set='gold', a='ember'), dict(v='greaves', g='ember', knee='gold'), dict(v='plated', a='ember', g='ember'), m='crimson', t='gold', a='ember', mot='flame')
# ---- Rare
line(('Dread Visage', 'Dreadplate', 'Dread Legguards', 'Dreadwalkers'), dict(v='visage', face='skull', t='bone'), dict(v='plate', sh='spike', g='crimson', set='bone', detail=('runes', 'crimson')), dict(v='tasset', g='crimson'), dict(v='plated', g='crimson', cuff='flare'), m='iron', t='bone', a='crimson')
line(('Stormcaller Hood', 'Stormguard', 'Stormwoven Leggings', 'Stormstep Boots'), dict(v='hood', eye='sky', g='sky', hs='flare', brow='bolt'), dict(v='plate', sh='round', detail=('bolt', 'gold')), dict(v='cloth', g='sky'), dict(v='leather', wing='sky', g='sky'), m='navy', t='gold', a='sky', mot='bolt')
line(("Raven's Mask", 'Ravenhide Armor', 'Ravenhide Trousers', 'Ravenhide Boots'), dict(v='visage', face='raven', t='bone', g='amber'), dict(v='vest', sh='feather'), dict(v='cloth'), dict(v='leather', cuff='fur', furc='shadow'), m='shadow', t='iron', a='violet')
# ---- Epic
line(('Crown of Ashes', 'Ashen Bulwark', 'Ashen Legguards', 'Ashen Striders'), dict(v='crown', cs='ash', m='ash', t='iron', a='ember', g='ember'), dict(v='plate', sh='spike', g='ember', detail=('cracks', 'ember')), dict(v='tasset', g='ember'), dict(v='plated', g='ember'), m='ash', t='iron', a='ember', mot='cracks')
line(('Voidwatcher Hood', 'Voidwatcher Robe', 'Voidwatcher Trousers', 'Voidwalkers'), dict(v='hood', eye='void', g='void', hs='tall', brow='eye'), dict(v='robe', sh='round', g='void', detail=('stars', 'violet')), dict(v='cloth', g='void'), dict(v='leather', g='void', wing='violet'), m='shadow', t='violet', a='gold', mot='stars')
line(('Dragonbone Helm', 'Dragonbone Plate', 'Dragonbone Greaves', 'Dragonbone Boots'), dict(v='horned', g='ember'), dict(v='plate', sh='bone', g='ember', detail=('ribs', 'bone')), dict(v='greaves', g='ember'), dict(v='bone', g='ember'), m='bone', t='crimson', a='bone', mot='ribs')
# ---- Legendary
line(("Titan's Visage", "Titan's Aegis", "Titan's Legguards", "Titan's March"), dict(v='visage', face='titan', g='ruby'), dict(v='aegis', sh='spike', g='ruby', detail=('runes', 'white')), dict(v='tasset', g='ruby'), dict(v='plated', cuff='flare', g='ruby'), m='gold', t='bronze', a='amber', fxs=('sparks',))
line(('Crown of Ruin', 'Sovereign Plate', 'Sovereign Legguards', 'Sovereign Boots'), dict(v='crown', t='crimson', a='ruby', g='ruby', broken=1), dict(v='mantle', sh='cape', g='ruby', a='crimson'), dict(v='greaves', g='ruby', knee='gold'), dict(v='plated', g='ruby'), m='gold', t='crimson', a='ruby', fxs=('sparks',))
line(("Heaven's Mask", "Heaven's Mantle", "Heaven's Greaves", "Heaven's Steps"), dict(v='visage', face='serene', g='sky', lift=.14), dict(v='mantle', sh='wing', g='sky', set='gold'), dict(v='greaves', g='sky', knee='gold'), dict(v='plated', wing='white', g='sky'), m='white', t='gold', a='white', fxs=('holy',))
# ---- Mythic
line((None, 'The Unyielding', 'The Unending', 'The Final Step'), {}, dict(v='aegis', sh='wing', g='ruby', set='white', detail=('runes', 'ruby')), dict(v='tasset', g='ruby', knee='white'), dict(v='plated', cuff='flare', wing='gold', g='ruby'), m='gold', t='crimson', a='white', fxs=('sparks', 'embers'))
line(('Face of Eternity', 'Mantle of Eternity', 'Greaves of Eternity', 'Steps Beyond Time'), dict(v='halo', wings='white', halo='aqua', g='aqua'), dict(v='mantle', sh='wing', g='aqua', set='gold', detail=('stars', 'aqua')), dict(v='greaves', g='aqua', knee='gold'), dict(v='plated', wing='aqua', g='aqua', cuff='flare'), m='white', t='gold', a='aqua', fxs=('holy',))
# ---- Unique sets
line(("Pathfinder's Hat", "Pathfinder's Coat", "Pathfinder's Trousers", "Pathfinder's Boots"), dict(v='hat', feather='green', t='moss'), dict(v='coat', sh='fur'), dict(v='cloth'), dict(v='leather', cuff='fur', furc='moss'), m='oak', t='moss', a='green', mot='vine')
line(("Legionnaire's Helm", "Legionnaire's Breastplate", "Legionnaire's Greaves", "Legionnaire's March"), dict(v='visor', crest='crimson', g='crimson'), dict(v='plate', sh='round', g='crimson', set='gold', rivets=1), dict(v='tasset', knee='gold'), dict(v='plated', g='crimson'), m='steel', t='crimson', a='gold')
line(("Windstalker's Hood", "Windstalker's Vest", "Windstalker's Leggings", "Windstalker's Striders"), dict(v='hood', eye='aqua', g='aqua', hs='scarf', sc='wool'), dict(v='vest', sh='feather'), dict(v='cloth', g='aqua'), dict(v='leather', wing='white'), m='green', t='wool', a='aqua', mot='vine')
line(("Apparition's Crown", "Apparition's Robes", "Apparition's Leggings", "Apparition's Steps"), dict(v='crown', cs='tiara', m='wool', t='violet', a='sky', g='sky'), dict(v='robe', sh='round', g='sky', set='violet', detail=('stars', 'sky')), dict(v='cloth', g='sky'), dict(v='slipper', g='sky'), m='wool', t='violet', a='sky', fxs=('stars',), mot='stars')
line(("Tinker's Hat", "Tinker's Vest", "Tinker's Trousers", "Tinker's Boots"), dict(v='hat', goggles='bronze', g='aqua'), dict(v='vest', quilt=1, sh='round'), dict(v='cloth', g='amber'), dict(v='leather'), m='copper', t='bronze', a='amber')
line(("Dawnkeeper's Halo", "Dawnkeeper's Vestment", "Dawnkeeper's Legguards", "Dawnkeeper's Treads"), dict(v='halo', g='amber'), dict(v='robe', sh='round', g='amber', set='gold'), dict(v='greaves', g='amber', knee='gold'), dict(v='plated', g='amber'), m='wool', t='gold', a='amber', fxs=('spark',))
line(("Gravewalker's Mask", "Gravewalker's Shroud", "Gravewalker's Leggings", "Gravewalker's Treads"), dict(v='visage', face='stitch', g='lime', t='bone'), dict(v='shroud', sh='bone', a='lime', g='lime', set='bone'), dict(v='cloth', g='lime'), dict(v='bone', g='lime'), m='ash', t='iron', a='bone', fxs=('souls',), mot='ribs')
line(('Stormbinder Coif', 'Stormbinder Mantle', 'Stormbinder Leggings', 'Stormbinder Sandals'), dict(v='coif', m='moon', eye='sky', g='sky'), dict(v='mantle', sh='cape', a='navy', detail=('bolt', 'gold')), dict(v='cloth', g='gold'), dict(v='sandal', g='sky'), m='sky', t='gold', a='navy', mot='bolt')
line(('Emberwyrm Visage', 'Emberwyrm Plate', 'Emberwyrm Greaves', 'Emberwyrm Striders'), dict(v='visage', face='dragon', g='amber', t='ember'), dict(v='plate', sh='ember', g='ember', set='gold', detail=('cracks', 'amber')), dict(v='tasset', g='ember', knee='gold'), dict(v='bone', a='gold', g='ember'), m='crimson', t='ember', a='gold', fxs=('embers',), mot='flame')
line(('Nightveil Mask', 'Nightveil Garb', 'Nightveil Leggings', 'Nightveil Walkers'), dict(v='visage', face='veil', g='violet', t='violet'), dict(v='shroud', sh='feather', g='violet', set='violet'), dict(v='cloth', g='violet'), dict(v='leather', g='violet', cuff='fur', furc='shadow'), m='night', t='night', a='violet', fxs=('void',), mot='stars')
line(('Celestial Crown', 'Celestial Aegis', 'Celestial Greaves', 'Celestial Striders'), dict(v='crown', cs='rays', m='gold', t='white', a='sky', g='sky'), dict(v='aegis', sh='wing', g='sky', set='gold', detail=('stars', 'gold')), dict(v='greaves', g='sky', knee='gold'), dict(v='plated', wing='white', g='sky'), m='white', t='gold', a='sky', fxs=('stars',), mot='stars')
line(('Aetherborn Hood', 'Aetherborn Mantle', 'Aetherborn Leggings', 'Aetherborn Steps'), dict(v='hood', eye='aqua', tip='gold', g='aqua', hs='mantle'), dict(v='mantle', sh='cape', g='aqua', set='gold', a='navy', detail=('stars', 'aqua')), dict(v='cloth', g='aqua'), dict(v='slipper', g='aqua'), m='sky', t='gold', a='wool', fxs=('souls',), mot='stars')
