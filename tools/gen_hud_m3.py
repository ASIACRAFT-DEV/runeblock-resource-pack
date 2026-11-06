#!/usr/bin/env python3
"""Mockup HUD milestone M3 (docs/spec/HUD_mockup_build_plan_2026-11-05.md): the quest tracker panel top right, from the
approved art in art/mockup-hud/ (tools/gen_mockup_hud.py) and its layout.json (tracker_panel, tracker_star, checkbox,
tracker_text).

Data: ArcaneSouls 0.46.0 placeholders (QuestTrackerService.packTrack):
  %arcane_track%              true when the panel shows (pack HUD on and a line tracked): the layout gate
  %arcane_track_main%         true = Main Scenario (gold title), false = side quest (aqua title)
  %arcane_track_title%        quest name, already cut to the panel on the server
  %arcane_track_lines%        text lines used (0-4): two objective rows, each word-wrapped onto up to two lines
  %arcane_track_line_<1-4>%   one text line (the server wraps and cuts with vanilla font widths)
  %arcane_track_line_<1-4>_style%  0 unused, 1 open row, 2 done row (text colour)
  %arcane_track_line_<1-4>_box%    checkbox on a row's first line: 0 none, 1 open, 2 done

How (BetterHud 1.14.1, same rules as M1/M2, see gen_hud_m1.py / gen_hud_m2.py):
  - the hud is anchored top right (gui 100/0) with `offset: left`, so an element's x is its left edge measured from the
    right edge of the screen (negative) and y its top edge; single pictures get their empty top rows added to y.
  - panel = one sequence image [1 line .. 4 lines] (same art, tools/gen_mockup_hud.tracker_panel(w, h) at each height)
    whose frame a listener picks from track_lines, so the box grows with the text. Sequences are not trimmed in height:
    y = the art's y.
  - checkbox = one sequence image [open, done] per line, frame from line_<n>_box (0 = nothing: continuation line).
  - text: two text elements per line (open colour / done colour) gated on line_<n>_style; title: gold or aqua gated
    on track_main. Texts are rb_font (vanilla bitmap at 16 px) at scale 0.5 = the vanilla 8 px line.

Writes:
  betterhud/assets/rb_m3/...           panel, star, checkbox frames
  betterhud/images/runeblock_m3.yml    image definitions
  betterhud/layouts/runeblock_m3.yml   layout rb_m3, gated on %arcane_track%
  betterhud/huds/runeblock_m3.yml      hud runeblock_m3 (top right); listed in betterhud/config.yml default-hud

    python3 -I tools/gen_hud_m3.py
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
OUT = os.path.join(BH, 'assets', 'rb_m3')
P = 'rb_m3_'

# colours from tools/composite_mockup_hud.py (the approved M0 composite)
TITLE_MAIN, TITLE_SIDE = '#FACC44', '#7FD8E8'
ROW_OPEN, ROW_DONE = '#E8E4DC', '#9A9488'
LINES = 4          # text lines under the title (2 rows x 2 wrapped lines)
LINE_H = 10         # px between lines (layout.json row_y 25, 35)


def _load(name):
    spec = importlib.util.spec_from_file_location(name, os.path.join(HERE, name + '.py'))
    m = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(m)
    return m


m1 = _load('gen_hud_m1')   # yaml writer + cond()

GATE = {'1': {'first': 'papi:arcane_track', 'second': "'true'", 'operation': '=='}}


def top_trim(name):
    im = Image.open(os.path.join(ART, name + '.png')).convert('RGBA')
    bb = im.getbbox()
    return bb[1] if bb else 0


def main():
    L = json.load(open(os.path.join(ART, 'layout.json')))
    if os.path.isdir(OUT):
        shutil.rmtree(OUT)
    os.makedirs(OUT)
    gm = _load('gen_mockup_hud')
    pan = L['tracker_panel']
    tt, cb = L['tracker_text'], L['checkbox']
    row_y = [tt['row_y'][0] + LINE_H * k for k in range(LINES)]
    base_h = pan['h'] - LINE_H * (len(tt['row_y']) - 1)   # panel height with one text line (42 - 10 = 32)
    for n in range(1, LINES + 1):
        im = gm.tracker_panel(pan['w'], base_h + LINE_H * (n - 1))
        if n == len(tt['row_y']):   # the approved 2-line panel must come out identical to the M0 art
            ref = Image.open(os.path.join(ART, 'tracker_panel.png')).convert('RGBA')
            if list(im.getdata()) != list(ref.getdata()):
                raise SystemExit('tracker_panel(%d, %d) differs from art/mockup-hud/tracker_panel.png' % (pan['w'], pan['h']))
        im.save(os.path.join(OUT, 'tracker_panel_%d.png' % n), optimize=True)
    for n in ('tracker_star', 'checkbox', 'checkbox_done'):
        shutil.copyfile(os.path.join(ART, n + '.png'), os.path.join(OUT, n + '.png'))

    images = {
        P + 'panel': {'type': 'sequence', 'files': ['rb_m3/tracker_panel_%d.png' % n for n in range(1, LINES + 1)],
                      'setting': {'listener': {'class': 'placeholder', 'value': '(number)papi:arcane_track_lines',
                                               'max': str(LINES)}}},
        P + 'star': {'type': 'single', 'file': 'rb_m3/tracker_star.png'},
    }
    for r in range(1, LINES + 1):
        images[P + 'box_%d' % r] = {
            'type': 'sequence', 'files': ['rb_m3/checkbox.png', 'rb_m3/checkbox_done.png'],
            'setting': {'listener': {'class': 'placeholder', 'value': '(number)papi:arcane_track_line_%d_box' % r,
                                     'max': '2'}}}

    els = [(P + 'panel', pan['x'], pan['y']),
           (P + 'star', L['tracker_star']['x'], L['tracker_star']['y'] + top_trim('tracker_star'))]
    for r in range(1, LINES + 1):
        els.append((P + 'box_%d' % r, cb['x'], row_y[r - 1]))
    el_images = {str(i): {'name': n, 'x': x, 'y': y} for i, (n, x, y) in enumerate(els, 1)}

    texts = []

    def text(pattern, x, y, color, conditions):
        texts.append({'name': 'rb_font', 'pattern': pattern, 'color': color, 'align': 'left', 'scale': 0.5,
                      'x': x, 'y': y, 'conditions': conditions, 'outline': True})

    text('[papi:arcane_track_title]', tt['title_x'], tt['title_y'], TITLE_MAIN,
         m1.cond('papi:arcane_track_main', '==', "'true'"))
    text('[papi:arcane_track_title]', tt['title_x'], tt['title_y'], TITLE_SIDE,
         m1.cond('papi:arcane_track_main', '!=', "'true'"))
    for r in range(1, LINES + 1):
        style = 'papi:arcane_track_line_%d_style' % r
        text('[papi:arcane_track_line_%d]' % r, tt['row_x'], row_y[r - 1], ROW_OPEN, m1.cond(style, '==', "'1'"))
        text('[papi:arcane_track_line_%d]' % r, tt['row_x'], row_y[r - 1], ROW_DONE, m1.cond(style, '==', "'2'"))
    el_texts = {str(i): t for i, t in enumerate(texts, 1)}
    lay = {'rb_m3': {'offset': 'left', 'conditions': GATE, 'images': el_images, 'texts': el_texts}}
    hud = {'runeblock_m3': {'layouts': {'1': {'name': 'rb_m3', 'gui': {'x': 100, 'y': 0}, 'pixel': {'x': 0, 'y': 0}}}}}

    head = '# GENERATED by tools/gen_hud_m3.py from art/mockup-hud (layout.json): edit the script, not this file.\n'
    for sub, obj, note in (
            ('images', images, '# M3 quest tracker pictures. panel = sequence [1..4 text lines], box_<n> = sequence [open, done];\n'
                                '# frames picked by listeners.\n'),
            ('layouts', lay, '# M3 quest tracker, drawn only when %arcane_track% is true (pack HUD on + a tracked line).\n'
                             '# offset: left = x is the left edge, from the right edge of the screen; y = top edge.\n'),
            ('huds', hud, '# Anchored at the top right (gui 100/0); every position is in the layout.\n')):
        with open(os.path.join(BH, sub, 'runeblock_m3.yml'), 'w') as f:
            f.write(head + note + '\n'.join(m1.dump(obj)) + '\n')
    print('wrote betterhud/{images,layouts,huds}/runeblock_m3.yml + %d pictures' % len(os.listdir(OUT)))


if __name__ == '__main__':
    main()
