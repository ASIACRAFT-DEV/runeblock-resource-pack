#!/usr/bin/env python3
"""The 112 weapons still to draw (the 8 Mythic weapons approved in pass 2 live in mythic_art.py). Names = Ett's list + the 11:54 renames."""
import math

from gear_core import A, L, disc, line, local, poly, ring, shaft
from gear_weapons import starn, axe, bow, crossbow, dagger, greatsword, grimoire, halberd, hammer, katana, kris, rapier, sabre, sceptre, sickle, staff, wand


def endbringer(s):
    c = A(25)
    for q in (-1, 1):
        s.mark(line(L(c, 3, q * 4), L(c, 0, q * 6)) | line(L(c, 0, q * 6), L(c, 2.5, q * 8)) | line(L(c, -4, q * 5), L(c, -2.5, q * 8)), 'void', 5)


def dying_star(s):
    g = (9.5, 9.5)
    s.paint(starn(g, 8, 7, 3.4), 'ember', 1.8, base=.1)
    s.paint(disc(g[0], g[1], 3.4), 'amber', 2.6, base=.2)
    s.paint(disc(g[0] - .3, g[1] - .3, 1.5), 'white', 1.2, base=.5)
    s.erase([(4, 5), (5, 3)])


def beyond_reality(s):
    c = A(23)
    for dx, dy, r, col in ((-8, -2, 2, 'pink'), (2, -9, 1.6, 'void'), (8, 4, 1.8, 'pink'), (-5, 7, 1.3, 'void')):
        x, y = c[0] + dx, c[1] + dy
        s.paint(poly([(x, y - r), (x + r, y), (x, y + r), (x - r, y)]), col, 1, base=.15)


def first_light_rays(s):
    s.mote([(3, 18), (5, 22), (19, 28), (23, 30)], 'amber', 5)


def absolute(s):
    c = A(23)
    k = L(c, 8, 0)
    s.paint(ring(k[0], k[1], 3.4, 4.6), 'gold', 1, shadow=False)
    s.paint(local(c, [(3.5, -2), (12, 0), (3.5, 2)]), 'white', 1.4, base=.3)


def unspoken(s):
    c = A(11)
    for a in (3.5, 6.5):
        s.paint(local(L(c, a, 0), [(-.7, -3.4), (.7, -3.4), (.7, 3.4), (-.7, 3.4)]), 'gold', .8)
    s.mark(line(L(c, 10, -1), L(c, 10, 1)) | line(L(c, 13, -1), L(c, 13, 1)), 'void', 5)


def deathless(s):
    p = A(1)
    s.paint(disc(p[0], p[1], 2.7), 'bone', 2)
    s.mark([(p[0] - 1, p[1] - 1), (p[0] + 1, p[1] - 1)], 'ebony', 1)
    s.mark([(p[0], p[1] + 1)], 'lime', 5)


W = {
    # ---- Warrior
    'Roughsplitter': (axe, dict(var='hatchet', metal='iron', haft='oak', chip=1, spike=False)),
    'Old Warhammer': (hammer, dict(var='mallet', metal='oak', trim='rust', haft='hide')),
    'Worn Battleaxe': (axe, dict(var='hatchet', double=1, metal='stone', trim='rust', chip=1, rust=1)),
    'Steel Edge': (katana, dict(metal='steel', grip='leather', wrap='sand', guard='disc')),
    'Rusted Greatsword': (greatsword, dict(var='notch', metal='rust', trim='rust', ridge=False)),
    'Steelbreaker': (hammer, dict(var='block', metal='steel', trim='iron', bands=(9,))),
    'Warborn Axe': (axe, dict(var='beard', metal='steel', trim='crimson', bands=(9, 16))),
    'Battleforged Blade': (katana, dict(metal='steel', trim='bronze', wrap='crimson', guard='flare', gh=4.5)),
    'Redsteel Greatsword': (greatsword, dict(metal='crimson', lift=.02, ridge=False, trim='iron', guard='down', core='ember', fx=('spark',))),
    'Dreadcleaver': (axe, dict(var='cleaver', metal='iron', edge='moon', haft='ebony', trim='bone', gem='crimson', fx=('blood',))),
    'Earthshatter': (hammer, dict(var='earth', metal='stone', trim='bronze', crack='amber', haft='dark', fx=('embers',))),
    'Oathbreaker': (katana, dict(metal='iron', edge='moon', trim='gold', snap=1, wrap='crimson', guard='flare', gh=4.5, fx=('blood',))),
    'Kingslayer': (greatsword, dict(var='broad', metal='moon', trim='gold', guard='crown', gh=6, gem='ruby', wrap='crimson', fx=('sparks',))),
    'Warpath': (axe, dict(var='crescent', double=1, dscale=.72, metal='crimson', edge='ruby', trim='iron', haft='ebony', bands=(9, 15), fx=('blood',))),
    "Mountain's Wrath": (hammer, dict(var='mount', metal='stone', trim='iron', haft='dark', gem='sky', bands=(8, 14), fx=('wspark',))),
    "Tyrant's Edge": (greatsword, dict(var='saw', metal='iron', edge='crimson', trim='crimson', guard='wing', gem='ember', grip='ebony', fx=('embers',))),
    'Ruinbringer': (katana, dict(metal='shadow', edge='ember', spine='ebony', trim='gold', guard='crown', gh=4.5, gem='ember', wrap='ember', fx=('embers',))),
    "Titan's Wrath": (hammer, dict(var='titan', metal='gold', trim='bronze', haft='ebony', gem='ruby', bands=(7, 13), fx=('gbolt', 'sparks'))),
    'Ashen Sovereign': (greatsword, dict(var='broad', metal='ash', crack='ember', trim='gold', guard='crown', gem='ember', grip='ebony', wrap='gold', fx=('embers',))),
    'Ruin of Kings': (katana, dict(metal='moon', edge='white', spine='iron', trim='gold', guard='crown', gh=5, gem='ruby', wrap='gold', bend=4, fx=('sparks',))),
    'Heavenbreaker': (axe, dict(var='wing', double=1, metal='white', edge='gold', trim='gold', haft='bone', gem='sky', bands=(8, 14), fx=('holy',))),
    'The Endbringer': (axe, dict(var='crescent', double=1, metal='ebony', edge='void', trim='gold', haft='ebony', gem='void', bands=(7, 12, 17), extra=endbringer, fx=('void', 'sparks'))),
    # ---- Archer
    'Shortbow': (bow, dict(var='short', limb='oak', recurve=False)),
    'Roughstring': (bow, dict(var='short', shape='deep', limb='hide', grip='dark', string='straw', recurve=False)),
    'Ashwood Bow': (bow, dict(limb='ash', grip='leather', trim='oak')),
    "Hunter's Curve": (bow, dict(shape='deep', limb='oak', grip='moss', trim='bronze', arrow='steel')),
    'Pine Longbow': (bow, dict(limb='pine', grip='leather', trim='iron', trimline='moss')),
    'Thornwood Bow': (bow, dict(var='thorn', limb='dark', spur='moss', grip='moss', trim='bronze', fx=('leaves',))),
    "Falcon's Reach": (crossbow, dict(var='wing', stock='oak', limb='steel', feather='sand', trim='bronze')),
    'Windpiercer': (bow, dict(var='wing', limb='aqua', feather='white', grip='wool', trim='moon', fx=('wspark',))),
    'Duskhunter': (crossbow, dict(stock='shadow', rail='iron', limb='violet', trim='moon', bolt='violet', gem='violet', fx=('void',))),
    'Stormstring': (bow, dict(var='storm', limb='navy', string='sky', trim='gold', trimline='gold', grip='ebony', gem='sky', fx=('bolt',))),
    'Phantom Shot': (crossbow, dict(var='hook', stock='ebony', limb='aqua', rail='shadow', tipc='aqua', bolt='aqua', gem='aqua', fx=('souls',))),
    'Skyshatter': (bow, dict(var='wing', limb='sky', feather='wool', trim='gold', grip='navy', gem='gold', runes=(.2, .8), fx=('wspark',))),
    'Moonpiercer': (bow, dict(var='moon', limb='moon', tip='moon', grip='night', trim='moon', gem='moon', arrow='moon', fx=('stars',))),
    "Eagle's Verdict": (bow, dict(var='wing', limb='gold', feather='sand', trim='gold', grip='crimson', gem='ruby', fx=('sparks',))),
    'Dreadwood Crossbow': (crossbow, dict(var='hook', stock='dark', limb='dark', rail='iron', tipc='bone', trim='bone', bolt='crimson', gem='crimson', span='wide', fx=('blood',))),
    'Starfall': (crossbow, dict(var='star', stock='navy', limb='moon', rail='moon', trim='gold', bolt='gold', gem='sky', tipc='gold', fx=('stars',))),
    'Eclipse Longbow': (bow, dict(var='moon', limb='ebony', tip='gold', trimline='gold', grip='shadow', trim='gold', gem='ember', string='amber', fx=('sparks',))),
    'Judgement of the Sky': (bow, dict(var='wing', limb='white', feather='gold', trim='gold', grip='sky', gem='sky', string='amber', arrow='gold', fx=('holy',))),
    'The Unerring': (crossbow, dict(var='star', span='wide', stock='ebony', rail='steel', limb='gold', trim='gold', bolt='white', gem='ruby', tipc='ruby', fx=('sparks',))),
    'The Last Horizon': (bow, dict(var='horn', shape='deep', limb='ember', tip='gold', trimline='gold', grip='ebony', trim='gold', gem='amber', string='amber', fx=('embers', 'sparks'))),
    'Worldender': (crossbow, dict(var='hook', span='wide', thick=4.2, stock='ebony', rail='crimson', limb='ember', trim='gold', tipc='gold', bolt='ember', gem='ember', fx=('embers', 'sparks'))),
    'The Dying Star': (bow, dict(var='horn', shape='deep', limb='night', tip='amber', trimline='amber', grip='ebony', trim='gold', gem='amber', string='ember', arrow='amber', runes=(.14, .28, .72, .86), extra=dying_star, fx=('embers', 'stars'))),
    # ---- Mage
    'Spark Wand': (wand, dict(head='star', glow='gold', wood='oak', hcol='leather')),
    'Oak Wand': (wand, dict(head='knob', glow='green', wood='oak', trim='oak', hcol='hide')),
    'Willow Wand': (wand, dict(head='leaf', glow='green', wood='pine', trim='moss', hcol='moss', leaves=((-120, 7), (-60, 8), (0, 7)))),
    "Novice's Focus": (grimoire, dict(cover='sky', trim='sand', spine='sand', band='oak', emblem='rune', glow='wool', corners=False)),
    'Enchanted Twig': (staff, dict(head='twig', glow='aqua', wood='oak', crooked=1, trim='moss', fx=('souls',))),
    'Ember Wand': (wand, dict(head='flame', trim='bronze', wood='dark', hcol='crimson', fx=('embers',))),
    'Frostwood Staff': (staff, dict(head='flake', glow='ice', wood='moon', trim='ice', bands=(14,), fx=('frost',))),
    'Stormspark': (wand, dict(head='bolt', glow='sky', wood='navy', trim='gold', hcol='navy', fx=('bolt',))),
    'Moonlit Focus': (grimoire, dict(cover='night', trim='moon', spine='moon', band='sky', emblem='moon', glow='moon', fx=('stars',))),
    'Riftcaller': (wand, dict(head='rift', glow='violet', trim='moon', wood='shadow', hcol='violet', fx=('void',))),
    'Frostwhisper': (staff, dict(head='crystal', glow='ice', wood='night', trim='moon', bands=(10, 16), fx=('frost',))),
    'Soulflare': (wand, dict(head='flame', fl1='aqua', fl2='ice', trim='moon', wood='shadow', hcol='aqua', fx=('souls',))),
    'Tempest Focus': (grimoire, dict(cover='navy', trim='gold', band='sky', emblem='bolt', glow='gold', fx=('gbolt', 'wspark'))),
    'Voidspire': (staff, dict(head='spire', glow='void', trim='iron', wood='ebony', bands=(9, 15), fx=('void',))),
    'Spellstorm': (wand, dict(head='orb', glow='sky', trim='gold', wood='navy', hcol='gold', pgem='sky', fx=('bolt', 'wspark'))),
    'Riftweaver': (grimoire, dict(cover='shadow', trim='violet', spine='violet', band='gold', emblem='rift', glow='violet', fx=('void',))),
    'Blackstar Wand': (wand, dict(head='blackstar', glow='ruby', trim='gold', wood='ebony', hcol='ruby', pgem='ruby', fx=('void', 'sparks'))),
    'Astral Dominion': (staff, dict(head='astral', glow='white', trim='gold', gem='sky', wood='night', bands=(8, 14), pgem='sky', fx=('stars',))),
    'The First Flame': (wand, dict(head='cage', trim='gold', wood='ebony', hcol='gold', pgem='ember', fx=('embers', 'sparks'))),
    "Reality's End": (grimoire, dict(cover='ebony', trim='gold', band='void', emblem='end', glow='ruby', fx=('void', 'sparks'))),
    "Eternity's Grasp": (staff, dict(head='grasp', glow='aqua', trim='gold', wood='ebony', bands=(9, 15), pgem='aqua', fx=('souls', 'sparks'))),
    'Beyond Reality': (wand, dict(head='rift', glow='pink', trim='gold', wood='void', hcol='void', pgem='pink', bands=(10,), extra=beyond_reality, fx=('void', 'stars'))),
    # ---- Priest
    "Pilgrim's Staff": (staff, dict(head='crook', trim='oak', wood='oak', bands=(14,), neck=3)),
    "Novice's Rod": (sceptre, dict(head='knob', glow='amber', trim='bronze', rod='oak', bands=(14,))),
    'Oak Staff': (staff, dict(head='knob', glow='moss', trim='oak', wood='oak', bands=())),
    "Shepherd's Rod": (sceptre, dict(head='crook', trim='sand', rod='sand', bands=(8,), neck=3)),
    'Willow Staff': (staff, dict(head='leaf', glow='lime', trim='moss', wood='pine', crooked=1, fx=('leaves',))),
    'Dawnlight Staff': (staff, dict(head='dawn', glow='amber', trim='gold', wood='sand', bands=(12,), fx=('spark',))),
    'Blessed Sickle': (sickle, dict(metal='oak', edge='lime', grain=1, haft='oak', trim='moss', gem='lime', sprout='green', fx=('leaves',))),
    'Moonprayer': (sceptre, dict(head='moon', glow='moon', trim='moon', rod='night', fx=('stars',))),
    'Lightkeeper': (halberd, dict(metal='steel', edge='white', trim='gold', haft='sand', gem='amber', tassel='amber', fx=('spark',))),
    'Dawnkeeper': (staff, dict(head='lantern', glow='amber', trim='gold', wood='wool', bands=(8, 14), pgem='amber', fx=('sparks',))),
    'Lifebinder': (sickle, dict(metal='gold', edge='lime', haft='dark', trim='moss', gem='green', sprout='green', notes=(30, 60), fx=('leaves',))),
    'Spiritwarden': (sceptre, dict(head='cage', fl1='aqua', fl2='wool', trim='moon', rod='moon', fx=('souls',))),
    'Sunspire': (halberd, dict(var='sun', metal='gold', edge='white', trim='gold', haft='wool', gem='ember', tassel='ruby', fx=('sparks',))),
    "Seraphim's Grace": (staff, dict(head='wings', glow='white', trim='gold', gem='sky', wood='wool', bands=(8, 14), fx=('holy',))),
    'Soul Sanctuary': (sickle, dict(metal='aqua', edge='white', haft='moon', trim='moon', gem='aqua', notes=(25, 50, 75), fx=('souls',))),
    'Sacred Oath': (sceptre, dict(head='cross', glow='ruby', trim='gold', rod='wool', fx=('holy',))),
    'Divine Retribution': (halberd, dict(var='wing', metal='white', edge='gold', trim='gold', haft='crimson', gem='ruby', tassel='crimson', bands=(7, 13, 18), fx=('gbolt', 'sparks'))),
    'Light of Creation': (staff, dict(head='genesis', glow='amber', trim='gold', wood='gold', bands=(7, 13, 18), pgem='amber', fx=('holy',))),
    'Eternal Testament': (sickle, dict(metal='gold', edge='white', haft='wool', trim='gold', gem='sky', notes=(20, 45, 70), fx=('holy',))),
    "Heaven's Verdict": (halberd, dict(var='moon', metal='moon', edge='white', trim='gold', haft='navy', gem='sky', tassel='sky', fx=('holy',))),
    "The Seraph's Promise": (sceptre, dict(head='wings', glow='gold', trim='gold', gem='ruby', rod='gold', pgem='ruby', fx=('holy',))),
    'The First Light': (staff, dict(head='firstlight', glow='amber', trim='white', wood='gold', bands=(6, 11, 16), pgem='white', extra=first_light_rays, fx=('holy', 'sparks'))),
    'The Divine Absolute': (halberd, dict(var='sun', metal='white', edge='amber', trim='gold', haft='gold', gem='aqua', tassel='sky', bands=(6, 11, 16), pgem='aqua', extra=absolute, fx=('holy', 'gbolt'))),
    # ---- Rogue
    'Rusted Dagger': (dagger, dict(metal='rust', trim='rust', ridge=False)),
    'Copper Shiv': (dagger, dict(var='shiv', metal='copper', grip='hide', trim='hide')),
    'Iron Rapier': (rapier, dict(metal='steel', trim='steel', var='cup', grip='leather', wrap='iron')),
    'Roughblade': (sabre, dict(metal='stone', trim='rust', bend=3.8)),
    'Old Kris': (kris, dict(metal='stone', trim='rust', grip='oak')),
    'Nightfang': (dagger, dict(var='fang', metal='night', edge='moon', trim='shadow', grip='ebony', fx=('stars',))),
    'Quickthorn': (rapier, dict(var='thorn', metal='moss', edge='lime', trim='moss', grip='dark', wrap='moss', fx=('leaves',))),
    'Silent Edge': (sabre, dict(metal='iron', edge='moon', trim='shadow', grip='ebony', spine='ebony', guard='bar', gh=3.5)),
    'Venomtip': (kris, dict(metal='moss', edge='lime', core='lime', trim='iron', grip='ebony', gem='lime', fx=('poison',))),
    'Phantom Talon': (dagger, dict(var='talon', metal='aqua', edge='white', trim='shadow', grip='shadow', gem='aqua', fx=('souls',))),
    'Wraithblade': (rapier, dict(var='wisp', metal='aqua', trim='moon', cup='aqua', grip='shadow', wrap='aqua', fx=('souls',))),
    "Viper's Kiss": (sabre, dict(metal='moss', edge='lime', core='lime', trim='gold', grip='moss', gem='lime', pgem='lime', fx=('poison',))),
    'Grimfang': (kris, dict(metal='iron', edge='bone', trim='bone', grip='ebony', gem='crimson', pgem='crimson', waves=3, fx=('blood',))),
    'Soulrender': (dagger, dict(var='rend', metal='violet', edge='ice', core='ice', trim='shadow', grip='ebony', gem='aqua', fx=('souls',))),
    'Silent Requiem': (rapier, dict(var='shell', metal='moon', trim='moon', grip='ebony', wrap='moon', gem='violet', fx=('stars',))),
    'Crimson Lament': (sabre, dict(metal='crimson', lift=.02, edge='ruby', trim='gold', grip='ebony', gem='ruby', spine='dark', fx=('blood',))),
    'Eclipse Fang': (kris, dict(metal='ebony', edge='amber', core='amber', trim='gold', grip='shadow', gem='ember', pgem='amber', fx=('embers', 'sparks'))),
    "Death's Testament": (dagger, dict(var='needle', metal='bone', edge='white', trim='gold', grip='ebony', guard='crown', gem='crimson', pgem='crimson', fx=('blood', 'sparks'))),
    'The Unseen Hand': (rapier, dict(var='wisp', metal='white', edge='aqua', trim='gold', cup='violet', grip='shadow', wrap='violet', pgem='violet', fx=('void', 'sparks'))),
    'Crimson Judgement': (sabre, dict(metal='ruby', lift=.02, edge='white', trim='gold', grip='crimson', gem='amber', pgem='ruby', guard='crown', gh=4, bend=6, fx=('blood', 'sparks'))),
    'Fatebreaker': (kris, dict(metal='sky', edge='white', core='gold', trim='gold', grip='navy', gem='gold', pgem='sky', waves=3, amp=1.3, fx=('sparks', 'bolt'))),
    'The Unspoken': (dagger, dict(var='needle', metal='ebony', edge='violet', core='violet', trim='gold', grip='shadow', guard='wing', gh=4.5, gem='void', pgem='void', extra=unspoken, fx=('void', 'sparks'))),
    'Deathless Silence': (sabre, dict(metal='white', edge='lime', core='lime', spine='iron', trim='gold', grip='ebony', guard='wing', gh=4, gem='lime', bend=6, extra=deathless, fx=('poison', 'sparks'))),
}
