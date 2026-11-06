#!/usr/bin/env python3
"""Mockup HUD milestone M4 (docs/spec/HUD_mockup_build_plan_2026-11-05.md): the compass top centre with the quest
marker and the distance, from the approved art in art/mockup-hud/ (compass_strip.png, compass/*.png, the M0 composite's
placement in tools/composite_mockup_hud.py) and layout.json `compass`.

Not BetterHud's own `circle` compass: that one is a perspective chain shown to every player (no conditions), and has
no distance text. Here every moving part is a `sequence` image whose frame an ArcaneSouls 0.47.0 placeholder picks
(PackCompass), gated on %arcane_packhud% like M1-M3:
  %arcane_compass_heading%  1..360 = facing in whole degrees + 1 (N = 1): the dial frame (letters + ticks scrolled)
  %arcane_compass_marker%   0 none · 1..177 = diamond at frame - 89 px from the centre · 178 / 179 = off left / right
  %arcane_compass_dist%     "142m", "142m ▲", "Here", "" (text under the strip, centred)
  %arcane_compass_dist_w%   width of that text in px: picks the small diamond's spot just left of it

Placement (BetterHud 1.14.1 rules, see gen_hud_m1.py / gen_hud_m2.py): hud anchored top centre (gui 50/0), layout
`offset: left` (x = left edge from the centre, y = top edge). Sequences trim empty columns and shift by the trim; to be
sure every frame of one sequence lands on the same pixels, each frame gets one alpha-1 pixel in its first and last
column (pin_columns, as M2). Frames are drawn exactly like the M0 composite: 1 px per degree, ±88 px, letters /
ticks / marker fade over the last 18 px.

Writes:
  betterhud/assets/rb_m4/...           strip, dial/ (360), marker/ (179), dist/ (80)
  betterhud/images/runeblock_m4.yml    image definitions
  betterhud/layouts/runeblock_m4.yml   layout rb_m4, gated on %arcane_packhud%
  betterhud/huds/runeblock_m4.yml      hud runeblock_m4 (top centre); listed in betterhud/config.yml default-hud

    python3 -I tools/gen_hud_m4.py
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
OUT = os.path.join(BH, 'assets', 'rb_m4')
P = 'rb_m4_'

FADE = 18          # px over which letters / ticks / marker fade at the strip's ends (M0 composite)
DIST_W_MAX = 80    # widest distance text the diamond sequence covers ("12,345m ▲" = 57 px)
DIST_TEXT = '#F4EEDC'
DIST_Y = 20        # text top; the 5x5 diamond sits at y 21 (M0 composite)
NAMES = {0: 'n', 45: 'ne', 90: 'e', 135: 'se', 180: 's', 225: 'sw', 270: 'w', 315: 'nw'}


def _load(name):
    spec = importlib.util.spec_from_file_location(name, os.path.join(HERE, name + '.py'))
    m = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(m)
    return m


m1 = _load('gen_hud_m1')       # yaml writer, cond(), GATE
m2 = _load('gen_hud_m2')       # pin_columns
gm = _load('gen_mockup_hud')   # small_diamond(), palette helpers


def art(name):
    return Image.open(os.path.join(ART, name + '.png')).convert('RGBA')


def fade(im, x, half):
    a = max(0.0, min(1.0, (half - abs(x)) / FADE))
    if a < 1:
        im = im.copy()
        im.putalpha(im.getchannel('A').point(lambda v: int(v * a)))
    return im


def main():
    L = json.load(open(os.path.join(ART, 'layout.json')))
    cp = L['compass']
    half, ppd = cp['half_span'], cp['px_per_degree']
    if os.path.isdir(OUT):
        shutil.rmtree(OUT)
    for sub in ('dial', 'marker', 'dist'):
        os.makedirs(os.path.join(OUT, sub))
    shutil.copyfile(os.path.join(ART, 'compass_strip.png'), os.path.join(OUT, 'strip.png'))

    letters = {d: art('compass/compass_' + n) for d, n in NAMES.items()}
    tick_major, tick = art('compass/compass_tick_major'), art('compass/compass_tick')
    point = art('compass/compass_point')

    # dial: letters (top y 3) + ticks (major y 11, minor y 12) for heading h = frame - 1
    widest = max(im.width for im in letters.values())
    dx0 = -half - (widest + 1) // 2                  # canvas left edge (GUI px from the centre)
    dial_w, dial_y = 2 * -dx0 + 1, 3
    dial_h = max(11 + tick_major.height, 12 + tick.height) - dial_y
    for h in range(360):
        im = Image.new('RGBA', (dial_w, dial_h), (0, 0, 0, 0))

        def put(src, x, y):
            im.alpha_composite(src, (x - dx0, y - dial_y))
        for k in range(16):                         # every 22.5 deg: letter + major tick, minor tick between
            deg = k * 22.5
            x = ((deg - h + 540) % 360 - 180) * ppd
            if abs(x) > half:
                continue
            if k % 2 == 0:
                lt = letters[int(deg)]
                put(fade(lt, x, half), round(x) - lt.width // 2, 3)
                put(fade(tick_major, x, half), round(x), 11)
            else:
                put(fade(tick, x, half), round(x), 12)
        m2.pin_columns(im).save(os.path.join(OUT, 'dial', 'h%03d.png' % h), optimize=True)

    # marker: 9x9 diamond (top y 9) at off px from the centre; 2 edge frames
    mx0 = -half - point.width // 2 - 4              # room for the edge chevrons
    mw, my = 2 * -mx0 + 1, 9
    frames = []
    for off in range(-half, half + 1):
        im = Image.new('RGBA', (mw, point.height), (0, 0, 0, 0))
        im.alpha_composite(fade(point, off, half), (off - point.width // 2 - mx0, 0))
        frames.append(im)
    gold, dark = gm.GOLD, gm.OUTLINE
    for side in (-1, 1):                            # target behind you: dimmed diamond at the end + an outward chevron
        im = Image.new('RGBA', (mw, point.height), (0, 0, 0, 0))
        dim = point.copy()
        dim.putalpha(dim.getchannel('A').point(lambda v: int(v * 0.55)))
        im.alpha_composite(dim, (side * half - point.width // 2 - mx0, 0))
        tip = side * (half + point.width // 2 + 3) - mx0
        for k in range(4):                          # chevron 4 px deep, 7 tall, pointing outwards
            for y in (4 - k, 4 + k):
                x = tip - side * k
                im.putpixel((x, y), gold)
                if 0 <= x - side < mw:
                    im.putpixel((x - side, y), dark)
        frames.append(im)
    for i, im in enumerate(frames, 1):
        m2.pin_columns(im).save(os.path.join(OUT, 'marker', 'm%03d.png' % i), optimize=True)

    # distance diamond: text centred on x 0 => its left edge -w//2; the 5x5 diamond 2 px further left
    dia = gm.small_diamond()
    sx0 = -(DIST_W_MAX // 2) - 2 - dia.width
    sw = -sx0 - 2
    for w in range(1, DIST_W_MAX + 1):
        im = Image.new('RGBA', (sw, dia.height), (0, 0, 0, 0))
        im.alpha_composite(dia, (-(w // 2) - 2 - dia.width - sx0, 0))
        m2.pin_columns(im).save(os.path.join(OUT, 'dist', 'w%02d.png' % w), optimize=True)

    def seq(files, ph, mx):
        return {'type': 'sequence', 'files': files,
                'setting': {'listener': {'class': 'placeholder', 'value': '(number)papi:arcane_' + ph, 'max': str(mx)}}}
    images = {
        P + 'strip': {'type': 'single', 'file': 'rb_m4/strip.png'},
        P + 'dial': seq(['rb_m4/dial/h%03d.png' % h for h in range(360)], 'compass_heading', 360),
        P + 'marker': seq(['rb_m4/marker/m%03d.png' % i for i in range(1, len(frames) + 1)], 'compass_marker', len(frames)),
        P + 'dist': seq(['rb_m4/dist/w%02d.png' % w for w in range(1, DIST_W_MAX + 1)], 'compass_dist_w', DIST_W_MAX),
    }
    strip = L['compass_strip']
    els = [(P + 'strip', strip['x'], strip['y'] + art('compass_strip').getbbox()[1]),
           (P + 'dial', dx0, dial_y),
           (P + 'marker', mx0, my),
           (P + 'dist', sx0, DIST_Y + 1)]
    el_images = {str(i): {'name': n, 'x': x, 'y': y} for i, (n, x, y) in enumerate(els, 1)}
    el_texts = {'1': {'name': 'rb_font', 'pattern': '[papi:arcane_compass_dist]', 'color': DIST_TEXT, 'align': 'center',
                      'scale': 0.5, 'x': 0, 'y': DIST_Y, 'conditions': m1.cond('papi:arcane_compass_dist_w', '!=', "'0'"),
                      'outline': True}}
    lay = {'rb_m4': {'offset': 'left', 'conditions': m1.GATE, 'images': el_images, 'texts': el_texts}}
    hud = {'runeblock_m4': {'layouts': {'1': {'name': 'rb_m4', 'gui': {'x': 50, 'y': 0}, 'pixel': {'x': 0, 'y': 0}}}}}

    head = '# GENERATED by tools/gen_hud_m4.py from art/mockup-hud (layout.json): edit the script, not this file.\n'
    for sub, obj, note in (
            ('images', images, '# M4 compass pictures. dial / marker / dist = sequences, frame picked by a listener (see the script).\n'),
            ('layouts', lay, '# M4 compass, drawn only when %arcane_packhud% is true (same gate as rb_m1).\n'
                             '# offset: left = x is the left edge from the screen centre; y = top edge.\n'),
            ('huds', hud, '# Anchored at the top centre (gui 50/0); every position is in the layout.\n')):
        with open(os.path.join(BH, sub, 'runeblock_m4.yml'), 'w') as f:
            f.write(head + note + '\n'.join(m1.dump(obj)) + '\n')
    size = sum(os.path.getsize(os.path.join(d, f)) for d, _, fs in os.walk(OUT) for f in fs)
    print('wrote betterhud/{images,layouts,huds}/runeblock_m4.yml + %d pictures, %.0f KB; dial x %d w %d, marker x %d w %d'
          % (sum(len(fs) for _, _, fs in os.walk(OUT)), size / 1024, dx0, dial_w, mx0, mw))


if __name__ == '__main__':
    main()
