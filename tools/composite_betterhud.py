#!/usr/bin/env python3
"""Visual check of a BetterHud layout WITHOUT a client: places the pictures BetterHud actually GENERATED (its build.zip,
or pack/ after tools/merge-betterhud.sh) where BetterHud 1.14.1 will draw them, over an in-game GUI-3 screenshot.

- y comes from the generated font: each picture is a bitmap glyph whose ascent encodes the layout y
  (BetterHud Huds.createAscent: ascent = -(((shaderId + 1024) << 13) + 4095 + y)), so a wrong y in the yml, a trimmed
  top row or a scale mistake shows up here exactly as in game.
- x comes from the layout yml (BetterHud sends it as space characters, not in the pack) + the left trim BetterHud adds
  back (xOffset); the layout must use `offset: left` (checked), so x is the left edge.
- listener pictures (bars) pick frame round(fraction x split) like ImageType.LISTENER; frame 0 = nothing.
- texts: the y is decoded from the generated text fonts as well; glyphs are drawn with the vanilla font
  (BetterHud's rb_font merges the vanilla bitmap font, scale 0.5 = 8 px), centred like TextRenderer (x - width / 2),
  `outline: true` = a black 1 px shadow.
- underneath: the pack's hotbar sprites, 4 items, and the vanilla EXPERIENCE BAR BACKGROUND (ArcaneSouls 0.44.0 empties
  the bar on the pack layout but the empty frame is still drawn), so anything it peeks out from is visible.

Also checks every placed picture against layout.json (the approved M0 spots) and prints mismatches.

    python3 -I tools/composite_betterhud.py --build <build.zip | pack dir> --out <dir> [--layout rb_m1]
"""
import argparse
import importlib.util
import io
import json
import os
import zipfile
import yaml
from PIL import Image

HERE = os.path.dirname(os.path.abspath(__file__))
PACK = os.path.normpath(os.path.join(HERE, '..'))
BH = os.path.join(PACK, 'betterhud')
ART = os.path.join(PACK, 'art', 'mockup-hud')

spec = importlib.util.spec_from_file_location('cm', os.path.join(HERE, 'composite_mockup_hud.py'))
cm = importlib.util.module_from_spec(spec)
spec.loader.exec_module(cm)


class Source:
    """build.zip (assets/… + overlay betterhud_1_21_6/assets/…) or a merged pack dir."""
    def __init__(self, path):
        self.zip = zipfile.ZipFile(path) if path.endswith('.zip') else None
        self.dir = None if self.zip else path

    def names(self, prefix):
        if self.zip:
            return sorted({n.split('/', 1)[1] if n.startswith('betterhud_1_21_6/') else n for n in self.zip.namelist()
                           if n.startswith(prefix) or n.startswith('betterhud_1_21_6/' + prefix)})
        return sorted(prefix + f for f in os.listdir(os.path.join(self.dir, prefix)))

    def read(self, rel):
        if self.zip:
            for pre in ('betterhud_1_21_6/', ''):
                try:
                    return self.zip.read(pre + rel)
                except KeyError:
                    pass
            raise KeyError(rel)
        return open(os.path.join(self.dir, rel), 'rb').read()


def decode_y(ascent):
    v = -ascent - 4095
    return ((v + 4096) % 8192) - 4096


def load_yaml(sub, name):
    return yaml.safe_load(open(os.path.join(BH, sub, name)))


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--build', required=True)
    ap.add_argument('--out', required=True)
    ap.add_argument('--layout', default='rb_m1')
    ap.add_argument('--hud', default='runeblock_m1')
    ap.add_argument('--shot', default=cm.DEF_SHOT)
    ap.add_argument('--client-jar', default=cm.DEF_JAR)
    a = ap.parse_args()
    os.makedirs(a.out, exist_ok=True)
    src = Source(a.build)
    lay = load_yaml('layouts', 'runeblock_m1.yml')[a.layout]
    imgs = load_yaml('images', 'runeblock_m1.yml')
    hud = load_yaml('huds', 'runeblock_m1.yml')[a.hud]['layouts'][1]
    assert hud['gui'] == {'x': 50, 'y': 100}, 'composite assumes the bottom-centre anchor'
    hx, hy = hud['pixel']['x'], hud['pixel']['y']
    problems = []
    if str(lay.get('offset', 'center')).lower() != 'left':
        problems.append('layout offset is not left: every piece shifts left by half the widest picture')
    ref = json.load(open(os.path.join(ART, 'layout.json')))

    font_img = json.loads(src.read('assets/betterhud/font/hud_%s_image.json' % a.hud))
    glyph = {}   # texture file -> (y, height)
    for p in font_img['providers']:
        if p.get('type') == 'bitmap':
            glyph[p['file'].split(':', 1)[1]] = (decode_y(p['ascent']), p['height'])
    text_y = set()
    for rel in src.names('assets/betterhud/font/'):
        if os.path.basename(rel).startswith('hud_%s_text_' % a.hud):
            ft = json.loads(src.read(rel))
            text_y |= {decode_y(p['ascent']) for p in ft['providers'] if p.get('type') == 'bitmap' and p.get('height') == 8}

    def texture(fname):
        return Image.open(io.BytesIO(src.read('assets/betterhud/textures/' + fname))).convert('RGBA')

    def place_list(state):
        """[(PIL image, x, y)] in GUI px from the bottom centre, in draw order."""
        out = []
        for k in sorted(lay['images'], key=int):
            el = lay['images'][k]
            name = el['name']
            d = imgs[name]
            orig = Image.open(os.path.join(BH, 'assets', d['file'])).convert('RGBA')
            bb = orig.getbbox()
            x = hx + el['x']
            if d['type'] == 'single':
                fname = 'image_%s.png' % name
                im = texture(fname)
                x += bb[0]
            else:
                split, side = d['split'], d['split-type']
                frac = state[name]
                n = round(frac * split)
                if n <= 0:
                    continue
                fname = 'image_image_%s_%s_%d_%d.png' % (name, side, split, n)
                im = texture(fname)
                x += bb[0] + (orig.width - bb[0] - im.width if side == 'right' else 0)
            gy, gh = glyph[fname]
            if gh != im.height:
                problems.append('%s: glyph height %d != texture %d (scale?)' % (fname, gh, im.height))
            y = hy + gy
            out.append((name, im, x, y))
            if d['type'] == 'single':
                r = ref.get(name.replace('rb_m1_', ''))
                if r and (r['x'] + bb[0], r['y'] + bb[1]) != (x, y):
                    problems.append('%s at (%d,%d), layout.json wants (%d,%d)' % (name, x, y, r['x'] + bb[0], r['y'] + bb[1]))
        return out

    font = cm.Font(a.client_jar)
    with zipfile.ZipFile(a.client_jar) as z:
        xp_bg = Image.open(io.BytesIO(z.read('assets/minecraft/textures/gui/sprites/hud/experience_bar_background.png'))).convert('RGBA')
    hotbar = Image.open(os.path.join(PACK, 'pack/assets/minecraft/textures/gui/sprites/hud/hotbar.png')).convert('RGBA')
    sel = Image.open(os.path.join(PACK, 'pack/assets/minecraft/textures/gui/sprites/hud/hotbar_selection.png')).convert('RGBA')
    want_text = {t['y'] for t in lay['texts'].values()}
    if want_text != text_y:
        problems.append('text rows in the generated fonts %s != layout %s' % (sorted(text_y), sorted(want_text)))

    def canvas(state, gw, gh, vanilla_xp=True, texts=True):
        c = Image.new('RGBA', (gw, gh), (0, 0, 0, 0))
        bx, by = gw // 2, gh
        if vanilla_xp:
            c.alpha_composite(xp_bg, (bx - 91, by - 29))   # vanilla: bar at height - 32 + 3
        c.alpha_composite(hotbar, (bx - 91, by - 22))
        c.alpha_composite(sel, (bx - 92 + 20 * state['slot'], by - 23))
        for i, item in enumerate(('iron_sword', 'iron_shovel', 'iron_pickaxe', 'iron_axe')):
            c.alpha_composite(font.items[item], (bx - 91 + 3 + 20 * i, by - 19))
        for _, im, x, y in place_list(state):
            c.alpha_composite(im, (bx + x, by + y))
        if texts:
            for k in sorted(lay['texts'], key=int):
                t = lay['texts'][k]
                s = (t['pattern'].replace('//', '/')
                     .replace('[papi:arcane_xp]', str(state['xp'])).replace('[papi:arcane_xp_next]', str(state['xpn']))
                     .replace('[health]', str(state['hp'])).replace('[max_health]', str(state['hpm']))
                     .replace('[papi:arcane_mana]', str(state['mp'])).replace('[papi:arcane_mana_max]', str(state['mpm']))
                     .replace('[papi:arcane_level]', str(state['lv'])))
                col = tuple(int(t['color'][i:i + 2], 16) for i in (1, 3, 5))
                x = bx + hx + t['x'] - font.width(s) // 2
                y = by + hy + t['y']
                if t.get('outline'):
                    font.draw(c, x + 1, y + 1, s, (0, 0, 0), shadow=False)
                font.draw(c, x, y, s, col, shadow=False)
        return c

    states = {
        'full': dict(hp=20, hpm=20, mp=100, mpm=100, lv=1, xp=0, xpn=30, slot=4),
        'fight': dict(hp=3, hpm=20, mp=12, mpm=100, lv=14, xp=12, xpn=30, slot=0),
        'nearly': dict(hp=19, hpm=20, mp=97, mpm=100, lv=27, xp=4410, xpn=8460, slot=8),
    }
    for s in states.values():
        s['rb_m1_hp_fill'] = s['hp'] / s['hpm']
        s['rb_m1_mp_fill'] = s['mp'] / s['mpm']
        s['rb_m1_exp_fill'] = s['xp'] / s['xpn']

    shot = Image.open(a.shot).convert('RGBA')
    g = 3
    base = cm.clean_v032(shot, g)
    W, H = base.size
    gw, gh = W // g, H // g
    for tag, st in states.items():
        c = canvas(st, gw, gh)
        up = c.resize((gw * g, gh * g), Image.NEAREST)
        out = base.copy()
        out.alpha_composite(up, (0, H - gh * g))
        out.convert('RGB').save(os.path.join(a.out, 'm1_gui3_%s.png' % tag))
        crop = out.crop((W // 2 - 130 * g, H - 75 * g, W // 2 + 130 * g, H))
        crop.convert('RGB').save(os.path.join(a.out, 'm1_gui3_%s_bottom.png' % tag))
    # side by side: M0 art composite (layout.json) vs what the build places, images only, 4x GUI px
    st = states['fight']
    built = canvas(st, 260, 75, vanilla_xp=False, texts=False)
    refc = Image.new('RGBA', (260, 75), (0, 0, 0, 0))
    refc.alpha_composite(hotbar, (130 - 91, 75 - 22))
    refc.alpha_composite(sel, (130 - 92, 75 - 23))
    for i, item in enumerate(('iron_sword', 'iron_shovel', 'iron_pickaxe', 'iron_axe')):
        refc.alpha_composite(font.items[item], (130 - 91 + 3 + 20 * i, 75 - 19))
    for name, im, x, y in place_list(st):
        n = name.replace('rb_m1_', '')
        r = ref[n]
        src_im = Image.open(os.path.join(ART, n + '.png')).convert('RGBA')
        if n.endswith('_fill'):
            w = round(src_im.width * st[name])
            src_im = src_im.crop((0, 0, w, src_im.height)) if n != 'mp_fill' else src_im.crop((src_im.width - w, 0, src_im.width, src_im.height))
            refc.alpha_composite(src_im, (130 + r['x'] + (0 if n != 'mp_fill' else r['w'] - w), 75 + r['y']))
        else:
            refc.alpha_composite(src_im, (130 + r['x'], 75 + r['y']))
    diff = sum(1 for p, q in zip(built.getdata(), refc.getdata()) if p != q)
    sbs = Image.new('RGBA', (260 * 4, 75 * 4 * 2 + 8), (40, 40, 40, 255))
    sbs.alpha_composite(refc.resize((1040, 300), Image.NEAREST), (0, 0))
    sbs.alpha_composite(built.resize((1040, 300), Image.NEAREST), (0, 308))
    sbs.convert('RGB').save(os.path.join(a.out, 'm1_ref_vs_build_x4.png'))
    print('pixels differing (layout.json art vs generated build, images only, 260x75 GUI px, "fight" state): %d' % diff)
    print('note: bar fills step in 1/split (3 px) in the build vs any px in the art reference')
    for p in problems:
        print('PROBLEM', p)
    print('wrote', ', '.join(sorted(os.listdir(a.out))))


if __name__ == '__main__':
    main()
