#!/usr/bin/env python3
"""Visual check of the BetterHud mockup layouts WITHOUT a client: places the pictures BetterHud actually GENERATED (its
build.zip, or pack/ after tools/merge-betterhud.sh) where BetterHud 1.14.1 will draw them, over an in-game GUI-3 shot.

- y comes from the generated font: each picture is a bitmap glyph whose ascent encodes the layout y
  (BetterHud Huds.createAscent: ascent = -(((shaderId + 1024) << 13) + 4095 + y)), so a wrong y in the yml, a trimmed
  top row or a scale mistake shows up here exactly as in game.
- x comes from the layout yml (BetterHud sends it as space characters, not in the pack) + the left trim BetterHud adds
  back (xOffset x the element's scale); the layout must use `offset: left` (checked), so x is the left edge.
- listener pictures (bars) pick frame round(fraction x split) like ImageType.LISTENER; sequence pictures (M2 icons,
  cooldown sweep, badges) pick file round(value / max x files) like ImageType.SEQUENCE; frame 0 = nothing.
- scaled glyphs (the 64 px skill icons at scale 0.25) are drawn at screen resolution, nearest-sampled, like the game.
- texts: the y is decoded from the generated text fonts; glyphs are drawn with the vanilla font (BetterHud's rb_font
  merges the vanilla bitmap font, scale 0.5 = 8 px), centred like TextRenderer (x - width / 2), `outline: true` = a black
  1 px shadow; `conditions` on health_percentage and %arcane_…% placeholders are evaluated against the state.
- underneath: the pack's hotbar sprites, 4 items, and the vanilla EXPERIENCE BAR BACKGROUND (ArcaneSouls empties the bar
  on the pack layout but the empty frame is still drawn), so anything it peeks out from is visible.

Also checks every placed single picture (and the M2 icon / badge spots) against layout.json (the approved M0 spots).

    python3 -I tools/composite_betterhud.py --build <build.zip | pack dir> --out <dir> [--set m1|m2|all]
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
G = 3   # GUI scale of the base shot

spec = importlib.util.spec_from_file_location('cm', os.path.join(HERE, 'composite_mockup_hud.py'))
cm = importlib.util.module_from_spec(spec)
spec.loader.exec_module(cm)

HUDS = [('runeblock_m1', 'rb_m1'), ('runeblock_m2', 'rb_m2')]   # draw order


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
    p = os.path.join(BH, sub, name)
    return yaml.safe_load(open(p)) if os.path.exists(p) else None


def tex_name(file):
    """BetterHud names a picture's texture after its file (folders -> '_')."""
    return 'image_' + file.replace('/', '_')


class Hud:
    def __init__(self, src, hud, lay_name, problems):
        self.name, self.problems = hud, problems
        self.lay = load_yaml('layouts', hud + '.yml')[lay_name]
        self.imgs = load_yaml('images', hud + '.yml')
        h = load_yaml('huds', hud + '.yml')[hud]['layouts'][1]
        assert h['gui'] == {'x': 50, 'y': 100}, 'composite assumes the bottom-centre anchor'
        self.hx, self.hy = h['pixel']['x'], h['pixel']['y']
        if str(self.lay.get('offset', 'center')).lower() != 'left':
            problems.append('%s: layout offset is not left: every piece shifts left by half the widest picture' % hud)
        font_img = json.loads(src.read('assets/betterhud/font/hud_%s_image.json' % hud))
        self.glyph = {}   # texture file -> (y, height)
        for p in font_img['providers']:
            if p.get('type') == 'bitmap':
                self.glyph[p['file'].split(':', 1)[1]] = (decode_y(p['ascent']), p['height'])
        self.text_y = set()
        for rel in src.names('assets/betterhud/font/'):
            if os.path.basename(rel).startswith('hud_%s_text_' % hud):
                ft = json.loads(src.read(rel))
                self.text_y |= {decode_y(p['ascent']) for p in ft['providers'] if p.get('type') == 'bitmap' and p.get('height') == 8}
        want = {t['y'] for t in self.lay.get('texts', {}).values()}
        if want != self.text_y:
            problems.append('%s: text rows in the generated fonts %s != layout %s' % (hud, sorted(self.text_y), sorted(want)))
        self.src = src

    def texture(self, fname):
        return Image.open(io.BytesIO(self.src.read('assets/betterhud/textures/' + fname))).convert('RGBA')

    def place(self, state):
        """[(name, PIL texture, x, y, w, h)] in GUI px from the bottom centre (w/h = drawn size), in draw order."""
        out = []
        for k in sorted(self.lay['images'], key=int):
            el = self.lay['images'][k]
            name = el['name']
            d = self.imgs[name]
            scale = float(el.get('scale', 1.0))
            x = self.hx + el['x']
            if d['type'] == 'single':
                orig = Image.open(os.path.join(BH, 'assets', d['file'])).convert('RGBA')
                fname = tex_name(d['file'])
                bb = orig.getbbox()
                x += round(bb[0] * scale)
            elif d['type'] == 'listener':
                orig = Image.open(os.path.join(BH, 'assets', d['file'])).convert('RGBA')
                bb = orig.getbbox()
                split, side = d['split'], d['split-type']
                n = round(state[name] * split)
                if n <= 0:
                    continue
                fname = 'image_image_%s_%s_%d_%d.png' % (name, side, split, n)
                im = self.texture(fname)
                x += bb[0] + (orig.width - bb[0] - im.width if side == 'right' else 0)
            else:   # sequence: value / max x files
                files = d['files']
                v = state.get(name, 0)
                n = round(v * len(files))
                if n <= 0:
                    continue
                file = files[min(n, len(files)) - 1]
                orig = Image.open(os.path.join(BH, 'assets', file)).convert('RGBA')
                cols = [c for c in range(orig.width) if any(orig.getpixel((c, r))[3] for r in range(orig.height))]
                x += round(cols[0] * scale)
                fname = tex_name(file)
            im = self.texture(fname)
            gy, gh = self.glyph[fname]
            if gh != round(im.height * scale):
                self.problems.append('%s: glyph height %d != texture %d x %.2f' % (fname, gh, im.height, scale))
            out.append((name, im, x, self.hy + gy, round(im.width * scale), gh))
        return out

    def texts(self, state):
        out = []
        for k in sorted(self.lay.get('texts', {}), key=int):
            t = self.lay['texts'][k]
            if not conditions_ok(t.get('conditions'), state):
                continue
            s = t['pattern'].replace('//', '/')
            for ph, v in state['ph'].items():
                s = s.replace('[%s]' % ph, str(v))
            col = tuple(int(t['color'][i:i + 2], 16) for i in (1, 3, 5))
            out.append((s, self.hx + t['x'], self.hy + t['y'], col, bool(t.get('outline'))))
        return out


def value(token, state):
    token = token.strip()
    if token.startswith("'") and token.endswith("'"):
        return token[1:-1]
    try:
        return float(token)
    except ValueError:
        pass
    v = state['ph'][token.replace('(number)', '')]
    return v


def conditions_ok(conds, state):
    if not conds:
        return True
    for c in conds.values():
        a, b = value(c['first'], state), value(c['second'], state)
        if isinstance(b, float):
            a = float(a)
        else:
            a, b = str(a), str(b)
        ok = {'==': a == b, '!=': a != b, '>': a > b, '<': a < b, '>=': a >= b, '<=': a <= b}[c['operation']]
        if not ok:
            return False
    return True


def slot_state(st, n_icons, order):
    """Expand a state's skill list into the placeholder values + listener fractions BetterHud would see."""
    ph = {'health': st['hp'], 'max_health': st['hpm'], 'health_percentage': st['hp'] / st['hpm'],
          'papi:arcane_mana': st['mp'], 'papi:arcane_mana_max': st['mpm'], 'papi:arcane_level': st['lv'],
          'papi:arcane_xp': st['xp'], 'papi:arcane_xp_next': st['xpn'], 'papi:arcane_packhud': 'true'}
    out = dict(st)
    out['rb_m1_hp_fill'] = st['hp'] / st['hpm']
    out['rb_m1_mp_fill'] = st['mp'] / st['mpm']
    out['rb_m1_exp_fill'] = st['xp'] / st['xpn']
    for i, sk in enumerate(st.get('skills', [None] * 4), 1):
        cd = sk.get('cd') if sk else None                    # (seconds left, seconds total)
        icon = 0
        if sk:
            icon = order.index(sk['sid']) + 1
            if sk.get('nomana') and not cd:
                icon += n_icons
        out['rb_m2_icon_%d' % i] = icon / (2 * n_icons)
        out['rb_m2_cd_%d' % i] = (cd[0] / cd[1]) if cd else 0
        out['rb_m2_badge_%d' % i] = 0.5   # 1 of 2: normal combo
        ph['papi:arcane_skill_%d_cd' % i] = str(cd[0]) if cd else '0'
    out['ph'] = ph
    return out


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--build', required=True)
    ap.add_argument('--out', required=True)
    ap.add_argument('--set', default='all', choices=['m1', 'm2', 'all'])
    ap.add_argument('--shot', default=cm.DEF_SHOT)
    ap.add_argument('--client-jar', default=cm.DEF_JAR)
    a = ap.parse_args()
    os.makedirs(a.out, exist_ok=True)
    src = Source(a.build)
    problems = []
    huds = [Hud(src, h, l, problems) for h, l in HUDS if load_yaml('layouts', h + '.yml')]
    ref = json.load(open(os.path.join(ART, 'layout.json')))
    order = [ln.strip() for ln in open(os.path.join(BH, 'skill_icons.txt')) if ln.strip() and not ln.startswith('#')]

    font = cm.Font(a.client_jar)
    with zipfile.ZipFile(a.client_jar) as z:
        xp_bg = Image.open(io.BytesIO(z.read('assets/minecraft/textures/gui/sprites/hud/experience_bar_background.png'))).convert('RGBA')
    hotbar = Image.open(os.path.join(PACK, 'pack/assets/minecraft/textures/gui/sprites/hud/hotbar.png')).convert('RGBA')
    sel = Image.open(os.path.join(PACK, 'pack/assets/minecraft/textures/gui/sprites/hud/hotbar_selection.png')).convert('RGBA')

    def up(im, w=None, h=None):
        return im.resize(((w or im.width) * G, (h or im.height) * G), Image.NEAREST)

    def canvas(state, gw, gh, vanilla_xp=True, texts=True, only=None):
        """Screen-resolution layer (GUI px x G) of everything the HUD draws."""
        c = Image.new('RGBA', (gw * G, gh * G), (0, 0, 0, 0))
        bx, by = gw // 2, gh

        def put(im, x, y, w=None, h=None):
            c.alpha_composite(up(im, w, h), ((bx + x) * G, (by + y) * G))
        if vanilla_xp:
            put(xp_bg, -91, -29)   # vanilla: bar at height - 32 + 3
        put(hotbar, -91, -22)
        put(sel, -92 + 20 * state['slot'], -23)
        for i, item in enumerate(('iron_sword', 'iron_shovel', 'iron_pickaxe', 'iron_axe')):
            put(font.items[item], -91 + 3 + 20 * i, -19)
        for hud in huds:
            if only and hud.name not in only:
                continue
            for name, im, x, y, w, h in hud.place(state):
                put(im, x, y, w, h)
            if texts:
                for s, x, y, col, outline in hud.texts(state):
                    t = Image.new('RGBA', (font.width(s) + 2, 9), (0, 0, 0, 0))
                    if outline:
                        font.draw(t, 1, 1, s, (0, 0, 0), shadow=False)
                    font.draw(t, 0, 0, s, col, shadow=False)
                    c.alpha_composite(up(t), ((bx + x - font.width(s) // 2) * G, (by + y) * G))
        return c

    # layout.json check: singles (+ trim) and the M2 icon / badge spots
    st0 = slot_state(STATES['ready'], len(order), order)
    for hud in huds:
        for name, im, x, y, w, h in hud.place(st0):
            key = name.replace('rb_m1_', '').replace('rb_m2_', '')
            d = hud.imgs[name]
            if d['type'] == 'single' and key in ref:
                bb = Image.open(os.path.join(BH, 'assets', d['file'])).convert('RGBA').getbbox()
                wants = [(ref[key]['x'] + bb[0], ref[key]['y'] + bb[1])] if not key.startswith('skill_slot') else \
                    [(ref['skill_slot_%d' % i]['x'] + bb[0], ref['skill_slot_%d' % i]['y'] + bb[1]) for i in range(1, 5)
                     if ref['skill_slot_%d' % i]['sprite'] == key]
                if (x, y) not in wants:
                    problems.append('%s at (%d,%d), layout.json wants %s' % (name, x, y, wants))
            elif key.startswith('icon_'):
                ic = ref['skill_slot_%s' % key[5:]]['icon']
                if (x, y, w, h) != (ic['x'], ic['y'], ic['w'], ic['h']):
                    problems.append('%s at (%d,%d) %dx%d, layout.json wants %s' % (name, x, y, w, h, ic))
            elif key.startswith('badge_'):
                b = ref['skill_badge_%s' % key[6:]]
                if (x, y) != (b['x'], b['y']):
                    problems.append('%s at (%d,%d), layout.json wants (%d,%d)' % (name, x, y, b['x'], b['y']))

    shot = Image.open(a.shot).convert('RGBA')
    base = cm.clean_v032(shot, G)
    W, H = base.size
    gw, gh = W // G, H // G
    sets = {'m1': ['full', 'fight', 'nearly'], 'm2': ['ready', 'cooldown', 'nomana', 'empty', 'lowhp']}
    chosen = sets['m1'] + sets['m2'] if a.set == 'all' else sets[a.set]
    for tag in chosen:
        st = slot_state(STATES[tag], len(order), order)
        c = canvas(st, gw, gh)
        out = base.copy()
        out.alpha_composite(c, (0, H - gh * G))
        pre = 'm1' if tag in sets['m1'] else 'm2'
        out.convert('RGB').save(os.path.join(a.out, '%s_gui3_%s.png' % (pre, tag)))
        crop = out.crop((W // 2 - 130 * G, H - 112 * G, W // 2 + 130 * G, H))
        crop.convert('RGB').save(os.path.join(a.out, '%s_gui3_%s_bottom.png' % (pre, tag)))
    for p in problems:
        print('PROBLEM', p)
    print('%d problem(s); wrote %s' % (len(problems), ', '.join(sorted(os.listdir(a.out)))))


ASSASSIN = ['dagger_flick', 'shadow_lurk', 'shadowstep_execution', 'deaths_whisper']   # the M0 art's skills
ADVENTURER = ['rune_strike', 'sidestep', 'second_wind']
STATES = {
    # M1
    'full': dict(hp=20, hpm=20, mp=100, mpm=100, lv=1, xp=0, xpn=30, slot=4),
    'fight': dict(hp=3, hpm=20, mp=12, mpm=100, lv=14, xp=12, xpn=30, slot=0),
    'nearly': dict(hp=19, hpm=20, mp=97, mpm=100, lv=27, xp=4410, xpn=8460, slot=8),
    # M2 (skills: sid, cd = (seconds left, total), nomana)
    'ready': dict(hp=20, hpm=20, mp=100, mpm=100, lv=27, xp=1210, xpn=8460, slot=0,
                  skills=[{'sid': s} for s in ASSASSIN]),
    'cooldown': dict(hp=17, hpm=20, mp=64, mpm=100, lv=27, xp=1210, xpn=8460, slot=0,
                     skills=[{'sid': ASSASSIN[0]}, {'sid': ASSASSIN[1], 'cd': (8, 14)}, {'sid': ASSASSIN[2]}, {'sid': ASSASSIN[3]}]),
    'nomana': dict(hp=17, hpm=20, mp=4, mpm=100, lv=27, xp=1210, xpn=8460, slot=0,
                   skills=[{'sid': ASSASSIN[0], 'nomana': True}, {'sid': ASSASSIN[1], 'cd': (3, 14)},
                           {'sid': ASSASSIN[2], 'nomana': True}, {'sid': ASSASSIN[3], 'nomana': True}]),
    'empty': dict(hp=20, hpm=20, mp=40, mpm=40, lv=6, xp=12, xpn=104, slot=0,
                  skills=[{'sid': s} for s in ADVENTURER] + [None]),
    'lowhp': dict(hp=5, hpm=20, mp=70, mpm=100, lv=27, xp=1210, xpn=8460, slot=0,
                  skills=[{'sid': s} for s in ASSASSIN]),
}


if __name__ == '__main__':
    main()
