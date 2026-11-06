#!/usr/bin/env python3
"""Mockup HUD milestone M2 (docs/spec/HUD_mockup_build_plan_2026-11-05.md): the skill row above the HP / MP panels,
from the approved art in art/mockup-hud/ (tools/gen_mockup_hud.py) and its layout.json.

Four slots (slot 4 = ultimate: gold frame + flame ring), each with the player's bound skill icon, today's click combo
in a badge under it, a clock-sweep cooldown with whole seconds left, and a "no mana" look (grey icon + blue veil).

How (BetterHud 1.14.1, read in its sources): every changing picture is ONE `sequence` image whose frame is picked by a
listener, so a slot is a handful of elements and no per-skill conditions:
  - ImageType.SEQUENCE.getComponent picks frame round(value x lastIndex), and HudImageParser puts an EMPTY frame first
    whenever the image has a listener: frames = [nothing, file 1, file 2, ...]. With listener value k / max and
    max = number of files, value k (1-based) shows file k and 0 shows nothing.
  - icon: files = the pack's 88 skill icons, then the same 88 as "no mana" copies (grey + veil, baked here);
    value = %arcane_skill_<n>_icon% (0 empty slot, 1..N icon, N+1..2N no mana). The order is betterhud/skill_icons.txt,
    which ArcaneSouls reads too (its jar resource pack-skill-icons.txt is a copy). New icons are APPENDED to that file,
    so an older jar never shows the wrong icon (a sid it doesn't know = empty slot).
  - cooldown sweep: files = cooldown/cd_01..cd_16 (k/16 of the cooldown still to go); value = %arcane_skill_<n>_cdpct%
    (0-100), max 100, so under 1/32 left shows nothing.
  - badge: files = [today's combo, the bow-mirrored combo]; value = %arcane_skill_<n>_badge% (1 or 2).
  - seconds: a text element `[papi:arcane_skill_<n>_cd]`, drawn only while it isn't '0' (string condition).
Glyphs are shared: same texture + same y + same scale = one font character for all four slots.

The skill icons are 64 px: drawn with layout `scale: 0.25` (glyph height 16 GUI px, full detail at GUI 3/4). A
sequence trims only empty COLUMNS (removeEmptyWidth) and shifts by the trim x scale, rounded: to keep every icon on the
same pixel the first and last column get one alpha-1 pixel (invisible) so nothing is trimmed.

Writes:
  betterhud/assets/rb_m2/...            pictures (icons, no-mana icons, cooldown frames, badges, frames, laurels)
  betterhud/skill_icons.txt             icon order (append-only)
  betterhud/images/runeblock_m2.yml     image definitions
  betterhud/layouts/runeblock_m2.yml    layout rb_m2, gated on %arcane_packhud% like M1
  betterhud/huds/runeblock_m2.yml       hud runeblock_m2 (bottom centre); listed in betterhud/config.yml default-hud

    python3 -I tools/gen_hud_m2.py
"""
import importlib.util
import json
import os
import shutil
from PIL import Image

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.normpath(os.path.join(HERE, '..'))
ART = os.path.join(ROOT, 'art', 'mockup-hud')
BH = os.path.join(ROOT, 'betterhud')
OUT = os.path.join(BH, 'assets', 'rb_m2')
SKILL_ICONS = os.path.join(ROOT, 'pack', 'assets', 'runeblock', 'textures', 'gui', 'skill')
ORDER = os.path.join(BH, 'skill_icons.txt')
P = 'rb_m2_'


def _load(name):
    spec = importlib.util.spec_from_file_location(name, os.path.join(HERE, name + '.py'))
    m = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(m)
    return m


gm = _load('gen_mockup_hud')   # art functions (grey_icon, nomana_overlay, combo_badge, COMBOS)
m1 = _load('gen_hud_m1')       # yaml writer + the packhud gate

CD_FRAMES = 16
ICON_SCALE = 0.25              # 64 px texture -> 16 GUI px
CD_TEXT = '#FFF4D0'


def icon_order():
    """Existing order first (append-only), then any new icon in the pack, sorted."""
    have = sorted(f[:-4] for f in os.listdir(SKILL_ICONS) if f.endswith('.png'))
    order = []
    if os.path.exists(ORDER):
        order = [ln.strip() for ln in open(ORDER) if ln.strip() and not ln.startswith('#')]
    gone = [s for s in order if s not in have]
    if gone:
        raise SystemExit('icons listed in skill_icons.txt are missing from the pack (keep the order, re-add them): %s' % gone)
    order += [s for s in have if s not in order]
    return order


def pin_columns(im):
    """One alpha-1 pixel in the first and last column so BetterHud's removeEmptyWidth trims nothing."""
    im = im.copy()
    for x, y in ((0, 0), (im.width - 1, im.height - 1)):
        r, g, b, a = im.getpixel((x, y))
        if a == 0:
            im.putpixel((x, y), (0, 0, 0, 1))
    return im


def nomana_icon(src):
    """Grey copy of the 64 px icon + the 16 px no-mana veil scaled x4 (nearest: same pixels as the M0 art)."""
    g = gm.grey_icon(src)
    veil = gm.nomana_overlay().resize((src.width, src.height), Image.NEAREST)
    g.alpha_composite(veil)
    return g


def main():
    layout = json.load(open(os.path.join(ART, 'layout.json')))
    order = icon_order()
    n_icons = len(order)
    if os.path.isdir(OUT):
        shutil.rmtree(OUT)
    for sub in ('skill', 'skill_nm', 'cd', 'badge'):
        os.makedirs(os.path.join(OUT, sub))
    with open(ORDER, 'w') as f:
        f.write('# GENERATED by tools/gen_hud_m2.py: skill icon order for the BetterHud skill row (1-based line = frame).\n'
                '# APPEND-ONLY: ArcaneSouls (resource pack-skill-icons.txt) maps a skill id to its line number.\n')
        f.write('\n'.join(order) + '\n')

    for sid in order:
        src = Image.open(os.path.join(SKILL_ICONS, sid + '.png')).convert('RGBA')
        if src.size != (64, 64):
            raise SystemExit('%s is %s, the skill row expects 64x64' % (sid, src.size))
        pin_columns(src).save(os.path.join(OUT, 'skill', sid + '.png'), optimize=True)
        pin_columns(nomana_icon(src)).save(os.path.join(OUT, 'skill_nm', sid + '.png'), optimize=True)
    for k in range(1, CD_FRAMES + 1):
        shutil.copyfile(os.path.join(ART, 'cooldown', 'cd_%02d.png' % k), os.path.join(OUT, 'cd', 'cd_%02d.png' % k))
    for i, combo in enumerate(gm.COMBOS):
        gold = i == 3
        mir = ''.join('L' if ch == 'R' else 'R' for ch in combo)
        gm.combo_badge(combo, gold).save(os.path.join(OUT, 'badge', 'badge_%d_normal.png' % (i + 1)))
        gm.combo_badge(mir, gold).save(os.path.join(OUT, 'badge', 'badge_%d_mirrored.png' % (i + 1)))
    for n in ('skill_slot', 'skill_slot_ult', 'skill_ult_flames', 'laurel_skill_l', 'laurel_skill_r'):
        shutil.copyfile(os.path.join(ART, n + '.png'), os.path.join(OUT, n + '.png'))

    def ph(name):
        return '(number)papi:arcane_' + name

    images = {}
    for n in ('skill_slot', 'skill_slot_ult', 'skill_ult_flames', 'laurel_skill_l', 'laurel_skill_r'):
        images[P + n] = {'type': 'single', 'file': 'rb_m2/%s.png' % n}
    for s in range(1, 5):
        images[P + 'icon_%d' % s] = {
            'type': 'sequence',
            'files': ['rb_m2/skill/%s.png' % sid for sid in order] + ['rb_m2/skill_nm/%s.png' % sid for sid in order],
            'setting': {'listener': {'class': 'placeholder', 'value': ph('skill_%d_icon' % s), 'max': str(2 * n_icons)}}}
        images[P + 'cd_%d' % s] = {
            'type': 'sequence',
            'files': ['rb_m2/cd/cd_%02d.png' % k for k in range(1, CD_FRAMES + 1)],
            'setting': {'listener': {'class': 'placeholder', 'value': ph('skill_%d_cdpct' % s), 'max': '100'}}}
        images[P + 'badge_%d' % s] = {
            'type': 'sequence',
            'files': ['rb_m2/badge/badge_%d_normal.png' % s, 'rb_m2/badge/badge_%d_mirrored.png' % s],
            'setting': {'listener': {'class': 'placeholder', 'value': ph('skill_%d_badge' % s), 'max': '2'}}}

    def top_trim(rel):
        im = Image.open(os.path.join(BH, 'assets', rel)).convert('RGBA')
        bb = im.getbbox()
        return bb[1] if bb else 0

    els = []   # (image name, x, y, scale) in draw order
    L = layout
    els.append((P + 'skill_ult_flames', L['skill_ult_flames']['x'],
                L['skill_ult_flames']['y'] + top_trim('rb_m2/skill_ult_flames.png'), None))
    for s in range(1, 5):
        sl = L['skill_slot_%d' % s]
        name = 'skill_slot_ult' if s == 4 else 'skill_slot'
        els.append((P + name, sl['x'], sl['y'] + top_trim('rb_m2/%s.png' % name), None))
    for s in range(1, 5):   # sequences keep their full height: y = the art's y
        ic = L['skill_slot_%d' % s]['icon']
        els.append((P + 'icon_%d' % s, ic['x'], ic['y'], ICON_SCALE))
    for s in range(1, 5):
        ic = L['skill_slot_%d' % s]['icon']
        els.append((P + 'cd_%d' % s, ic['x'], ic['y'], None))
    for n in ('laurel_skill_l', 'laurel_skill_r'):
        els.append((P + n, L[n]['x'], L[n]['y'] + top_trim('rb_m2/%s.png' % n), None))
    for s in range(1, 5):
        b = L['skill_badge_%d' % s]
        els.append((P + 'badge_%d' % s, b['x'], b['y'], None))

    el_images = {}
    for i, (name, x, y, scale) in enumerate(els, 1):
        e = {'name': name, 'x': x, 'y': y}
        if scale:
            e['scale'] = scale
        el_images[str(i)] = e
    el_texts = {}
    for s in range(1, 5):
        ic = L['skill_slot_%d' % s]['icon']
        el_texts[str(s)] = {'name': 'rb_font', 'pattern': '[papi:arcane_skill_%d_cd]' % s, 'color': CD_TEXT,
                            'align': 'center', 'scale': 0.5, 'x': ic['x'] + ic['w'] // 2, 'y': ic['y'] + 4,
                            'conditions': m1.cond('papi:arcane_skill_%d_cd' % s, '!=', "'0'"), 'outline': True}
    lay = {'rb_m2': {'offset': 'left', 'conditions': m1.GATE, 'images': el_images, 'texts': el_texts}}
    hud = {'runeblock_m2': {'layouts': {'1': {'name': 'rb_m2', 'gui': {'x': 50, 'y': 100}, 'pixel': {'x': 0, 'y': 0}}}}}

    head = '# GENERATED by tools/gen_hud_m2.py from art/mockup-hud (layout.json): edit the script, not this file.\n'
    for sub, obj, note in (
            ('images', images, '# M2 skill row pictures. icon/cd/badge = sequence images, frame picked by a listener (see the script).\n'),
            ('layouts', lay, '# M2 skill row, drawn only when %arcane_packhud% is true (same gate as rb_m1).\n'
                             '# offset: left = x is the left edge; y = top edge; icons are 64 px textures at scale 0.25.\n'),
            ('huds', hud, '# Anchored at the bottom centre (gui 50/100); every position is in the layout.\n')):
        with open(os.path.join(BH, sub, 'runeblock_m2.yml'), 'w') as f:
            f.write(head + note + '\n'.join(m1.dump(obj)) + '\n')
    size = sum(os.path.getsize(os.path.join(d, f)) for d, _, fs in os.walk(OUT) for f in fs)
    print('wrote betterhud/{images,layouts,huds}/runeblock_m2.yml, skill_icons.txt (%d icons), %d pictures, %.0f KB'
          % (n_icons, sum(len(fs) for _, _, fs in os.walk(OUT)), size / 1024))


if __name__ == '__main__':
    main()
