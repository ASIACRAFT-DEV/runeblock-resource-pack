#!/usr/bin/env python3
"""Place the mockup HUD art (art/mockup-hud/, from tools/gen_mockup_hud.py) over an in-game screenshot at several
GUI scales, the way Minecraft would draw it: every GUI px becomes a g x g block (nearest neighbour), bottom pieces
anchored to the bottom centre (vanilla hotbar 182x22 flush with the bottom edge), the compass top centre, the tracker
top right with a 5 px margin, chat bottom left, menu keys bottom right. Text (HP, mana, level, EXP, tracker,
distance, cooldown seconds) is drawn with the vanilla bitmap font from a 1.21.11 client jar, as BetterHud would.

M0 art check only: nothing here runs on the server.

    python3 -I tools/composite_mockup_hud.py --out <dir> [--shot <png>] [--shot-gui 3] [--clean v032]
                                             [--client-jar <1.21.11 client jar>] [--mockup <png>]

The default shot is docs/screenshots/hud-2026-10-10-v0.3.2/v032_vanilla_hud_01_idle.png (2304x973, GUI 3,
taken with the old v0.3.2 bars + combo boxes + tracker boss bar): `--clean v032` paints those over with
neighbouring terrain before the new HUD goes on. A shot with no HUD (F1) needs `--clean none`.
"""
import argparse
import io
import json
import math
import os
import zipfile
from PIL import Image

HERE = os.path.dirname(os.path.abspath(__file__))
PACK = os.path.normpath(os.path.join(HERE, '..'))
MMO = os.path.normpath(os.path.join(PACK, '..'))
ART = os.path.join(PACK, 'art', 'mockup-hud')
SKILL_ICONS = os.path.join(PACK, 'pack', 'assets', 'runeblock', 'textures', 'gui', 'skill')
DEF_SHOT = os.path.join(MMO, 'docs', 'screenshots', 'hud-2026-10-10-v0.3.2', 'v032_vanilla_hud_01_idle.png')
DEF_MOCK = os.path.join(MMO, 'docs', 'spec', 'RuneBlock_CBT_GUI_mockup_rainy_indigo133_2026-11-02.png')
DEF_JAR = os.path.expanduser('~/.gradle/caches/fabric-loom/1.21.11/minecraft-client.jar')


def art(name):
    return Image.open(os.path.join(ART, name + '.png')).convert('RGBA')


# ───────────────────────── vanilla font (ascii.png from the client jar) ─────────────────────────

class Font:
    def __init__(self, jar):
        with zipfile.ZipFile(jar) as z:
            self.sheet = Image.open(io.BytesIO(z.read('assets/minecraft/textures/font/ascii.png'))).convert('RGBA')
            self.items = {n: Image.open(io.BytesIO(z.read('assets/minecraft/textures/item/%s.png' % n))).convert('RGBA')
                          for n in ('iron_sword', 'iron_shovel', 'iron_pickaxe', 'iron_axe')}
        self.glyph, self.adv = {}, {}
        for code in range(32, 127):
            gx, gy = (code % 16) * 8, (code // 16) * 8
            g = self.sheet.crop((gx, gy, gx + 8, gy + 8))
            cols = [x for x in range(8) if any(g.getpixel((x, y))[3] for y in range(8))]
            w = (max(cols) + 1) if cols else 0
            self.glyph[chr(code)] = g
            self.adv[chr(code)] = 4 if code == 32 else w + 1

    def width(self, s):
        return sum(self.adv.get(c, 6) for c in s) - 1

    def draw(self, canvas, x, y, s, color, shadow=True):
        r, g, b = color
        for c in s:
            gl = self.glyph.get(c)
            if gl is None:
                x += 6
                continue
            for (dx, dy, col) in (((1, 1, (r // 4, g // 4, b // 4)),) if shadow else ()) + ((0, 0, (r, g, b)),):
                tint = Image.new('RGBA', gl.size, col + (255,))
                tint.putalpha(gl.getchannel('A'))
                canvas.alpha_composite(tint, (x + dx, y + dy))
            x += self.adv[c]


# ───────────────────────── painting the old HUD out of the v032 shot ─────────────────────────

def clean_v032(shot, g):
    """The v032 shot (GUI 3) still has the v0.3.2 HUD: tracker boss bar top centre, combo boxes, bars, XP bar,
    hotbar bottom centre. Copy terrain from the same rows further left/right over them (block-aligned to g)."""
    im = shot.copy()
    W, H = im.size
    cx = W // 2

    def patch(box, dx):
        x0, y0, x1, y1 = box
        src = shot.crop((x0 + dx, y0, x1 + dx, y1))
        im.paste(src, (x0, y0))
    # bottom centre: GUI x -96..+96, y -82..0. Every 576 px window to the left holds a big trunk, so tile the
    # 288 px of plain grass/dirt just left of the HUD twice (the right side has the held sword)
    half = 96 * g
    patch((cx - half, H - 82 * g, cx, H), -half)
    patch((cx, H - 82 * g, cx + half, H), -2 * half)
    # tracker boss bar: GUI x -96..+96, y 0..19 -> from the left (same sky + leaves)
    patch((cx - 96 * g, 0, cx + 96 * g, 19 * g), -585)
    return im


# ───────────────────────── HUD drawing in GUI px ─────────────────────────

def draw_hud(font, gw, gh, state, layout):
    c = Image.new('RGBA', (gw, gh), (0, 0, 0, 0))
    bx, by = gw // 2, gh            # bottom anchor
    tx = gw // 2                    # top anchor

    def put(name, anchor_xy, x, y, im=None):
        im = im or art(name)
        c.alpha_composite(im, (anchor_xy[0] + x, anchor_xy[1] + y))

    def L(name):
        return layout[name]

    B, T, TR = (bx, by), (tx, 0), (gw, 0)

    # ── hotbar (vanilla sprites) + items
    put('hotbar', B, L('hotbar')['x'], L('hotbar')['y'])
    sel = state['slot']
    put('hotbar_selection', B, -92 + 20 * sel, -23)
    for i, item in enumerate(('iron_sword', 'iron_shovel', 'iron_pickaxe', 'iron_axe')):
        c.alpha_composite(font.items[item], (bx - 91 + 3 + 20 * i, by - 19))
    put('hotbar_ring', B, L('hotbar_ring')['x'], L('hotbar_ring')['y'])

    # ── EXP
    put('exp_frame', B, L('exp_frame')['x'], L('exp_frame')['y'])
    xp, xpn = state['xp']
    fill = art('exp_fill')
    wfill = round(fill.width * xp / xpn)
    if wfill:
        c.alpha_composite(fill.crop((0, 0, wfill, fill.height)), (bx + L('exp_fill')['x'], by + L('exp_fill')['y']))
    s = 'EXP %d / %d' % (xp, xpn)
    font.draw(c, bx - font.width(s) // 2, by - 36, s, (0xF4, 0xEE, 0xDC))

    # ── HP / MP panels, shield, laurels
    for n in ('laurel_bar_l', 'laurel_bar_r', 'hp_panel', 'mp_panel'):
        put(n, B, L(n)['x'], L(n)['y'])
    hp, hpm = state['hp']
    mp, mpm = state['mp']
    hf, mf = art('hp_fill'), art('mp_fill')
    w = round(hf.width * hp / hpm)
    if w:
        c.alpha_composite(hf.crop((0, 0, w, 5)), (bx + L('hp_fill')['x'], by + L('hp_fill')['y']))
    w = round(mf.width * mp / mpm)
    if w:
        c.alpha_composite(mf.crop((mf.width - w, 0, mf.width, 5)), (bx + L('mp_fill')['x'] + mf.width - w, by + L('mp_fill')['y']))
    put('icon_heart', B, L('icon_heart')['x'], L('icon_heart')['y'])
    put('icon_mana', B, L('icon_mana')['x'], L('icon_mana')['y'])
    s = '%d / %d' % (hp, hpm)
    low = hp * 4 <= hpm
    font.draw(c, bx - 54 - font.width(s) // 2, by - 60, s, (0xFF, 0x5A, 0x4A) if low else (0xF8, 0xF0, 0xE6))
    s = '%d / %d' % (mp, mpm)
    font.draw(c, bx + 54 - font.width(s) // 2, by - 60, s, (0xF8, 0xF0, 0xE6))
    put('level_shield', B, L('level_shield')['x'], L('level_shield')['y'])
    s = str(state['level'])
    font.draw(c, bx - font.width(s) // 2, by - 57, s, (0x3A, 0x22, 0x0C), shadow=False)

    # ── skill row
    for n in ('laurel_skill_l', 'laurel_skill_r', 'skill_ult_flames'):
        put(n, B, L(n)['x'], L(n)['y'])
    skills = layout['_skills']
    for i in range(4):
        sl = L('skill_slot_%d' % (i + 1))
        put(sl['sprite'], B, sl['x'], sl['y'])
        ic = sl['icon']
        st = state['skills'][i]
        src = os.path.join(ART, 'skill_grey', skills[i] + '.png') if st.get('nomana') else os.path.join(SKILL_ICONS, skills[i] + '.png')
        icon = Image.open(src).convert('RGBA').resize((ic['w'] * state['g'], ic['h'] * state['g']), Image.NEAREST)
        state.setdefault('_icons', []).append((icon, bx + ic['x'], by + ic['y']))   # drawn at screen res later
        if st.get('cd'):
            left, total = st['cd']
            k = max(1, min(16, round(16 * left / total)))
            state.setdefault('_over', []).append(('cd', art('cooldown/cd_%02d' % k), bx + ic['x'], by + ic['y'], str(left)))
        if st.get('nomana'):
            state.setdefault('_over', []).append(('nm', art('skill_nomana'), bx + ic['x'], by + ic['y'], None))
        b = L('skill_badge_%d' % (i + 1))
        put(b['sprite'], B, b['x'], b['y'])

    # ── compass (top centre)
    cp = layout['compass']
    put('compass_strip', T, L('compass_strip')['x'], L('compass_strip')['y'])
    face = state['facing']
    half = cp['half_span']

    def at(bearing):
        d = (bearing - face + 540) % 360 - 180
        return d * cp['px_per_degree']

    def fade(im, x):
        a = max(0.0, min(1.0, (half - abs(x)) / 18))
        if a < 1:
            im = im.copy()
            im.putalpha(im.getchannel('A').point(lambda v: int(v * a)))
        return im
    names = {0: 'n', 45: 'ne', 90: 'e', 135: 'se', 180: 's', 225: 'sw', 270: 'w', 315: 'nw'}
    for k in range(16):                     # letters + major ticks every 45 deg, a minor tick between
        deg = k * 22.5
        x = at(deg)
        if abs(x) > half:
            continue
        if k % 2 == 0:
            letter = art('compass/compass_' + names[int(deg)])
            put(None, T, round(x) - letter.width // 2, 3, fade(letter, x))
            put(None, T, round(x), 11, fade(art('compass/compass_tick_major'), x))
        else:
            put(None, T, round(x), 12, fade(art('compass/compass_tick'), x))
    if state.get('target') is not None:
        x = at(state['target'])
        if abs(x) <= half:
            put(None, T, round(x) - 4, 9, fade(art('compass/compass_point'), x))
        s = '%dm' % state['dist']
        wd = 5 + 2 + font.width(s)
        put('icon_diamond_small', T, -wd // 2, 21)
        font.draw(c, tx - wd // 2 + 7, 20, s, (0xF4, 0xEE, 0xDC))

    # ── tracker (top right)
    tt = layout['tracker_text']
    put('tracker_panel', TR, L('tracker_panel')['x'], L('tracker_panel')['y'])
    put('tracker_star', TR, L('tracker_star')['x'], L('tracker_star')['y'])
    font.draw(c, gw + tt['title_x'], tt['title_y'], state['quest'][0], (0xFA, 0xCC, 0x44))
    for j, (row, done) in enumerate(state['quest'][1]):
        y = tt['row_y'][j]
        put('checkbox_done' if done else 'checkbox', TR, L('checkbox')['x'], y)
        font.draw(c, gw + tt['row_x'], y, row, (0x9A, 0x94, 0x88) if done else (0xE8, 0xE4, 0xDC))

    # ── chat (bottom left) + menu keys (bottom right, only with the client mod)
    cb = layout['chat_button']
    BL, BR = (0, gh), (gw, gh)
    put('button', BL, cb['x'], cb['y'])
    ic = art('icon_chat')
    put(None, BL, cb['x'] + (18 - ic.width) // 2, cb['y'] + 4, ic)
    put('keys/key_T', BL, cb['x'] + 6, cb['y'] + 13)
    if state.get('mod', True):
        mb = layout['menu_buttons']
        for k, bt in enumerate(mb['buttons']):
            x = mb['x0'] + mb['pitch'] * k
            put('button', BR, x, mb['y'])
            ic = art(bt['icon'])
            put(None, BR, x + (18 - ic.width) // 2, mb['y'] + (16 - ic.height) // 2, ic)
            put('keys/key_' + bt['key'], BR, x + 6, mb['y'] + 13)
    return c


def render(shot, g, font, state, layout):
    W, H = shot.size
    gw, gh = math.ceil(W / g), math.ceil(H / g)       # Minecraft rounds the scaled size up
    state = dict(state, g=g)
    hud = draw_hud(font, gw, gh, state, layout)
    up = hud.resize((gw * g, gh * g), Image.NEAREST)
    # skill icons are 64 px textures drawn 16 GUI px wide: nearest-sampled at the real resolution, under the frame
    out = shot.convert('RGBA').copy()
    layer = Image.new('RGBA', up.size, (0, 0, 0, 0))
    for icon, x, y in state.get('_icons', []):
        layer.alpha_composite(icon, (x * g, y * g))
    for kind, im, x, y, txt in state.get('_over', []):
        layer.alpha_composite(im.resize((im.width * g, im.height * g), Image.NEAREST), (x * g, y * g))
        if txt:
            t = Image.new('RGBA', (16, 16), (0, 0, 0, 0))
            font.draw(t, (16 - font.width(txt)) // 2, 4, txt, (0xFF, 0xF4, 0xD0))
            layer.alpha_composite(t.resize((16 * g, 16 * g), Image.NEAREST), (x * g, y * g))
    base = out.crop((0, 0, up.width, up.height))      # pads with clear when the scaled size rounds up
    base.alpha_composite(up)
    base.alpha_composite(layer)
    return base.crop((0, 0, W, H))


NORMAL = {'slot': 4, 'xp': (0, 30), 'hp': (20, 20), 'mp': (100, 100), 'level': 1, 'facing': 337, 'target': 351,
          'dist': 142, 'quest': ('First Ordeal', [('Reach the Ruins (0/1)', False), ('Defeat 5 Drowned (0/5)', False)]),
          'skills': [{}, {}, {}, {}], 'mod': True}
STATES = dict(NORMAL, hp=(3, 20), mp=(12, 100), xp=(12, 30), level=14,
              quest=('First Ordeal', [('Reach the Ruins (1/1)', True), ('Defeat 5 Drowned (2/5)', False)]),
              skills=[{}, {'cd': (8, 14)}, {'nomana': True}, {'nomana': True}], facing=20, target=60, dist=37)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--out', required=True)
    ap.add_argument('--shot', default=DEF_SHOT)
    ap.add_argument('--shot-gui', type=int, default=3)
    ap.add_argument('--clean', default='v032', choices=['v032', 'none'])
    ap.add_argument('--client-jar', default=DEF_JAR)
    ap.add_argument('--mockup', default=DEF_MOCK)
    a = ap.parse_args()
    os.makedirs(a.out, exist_ok=True)
    layout = json.load(open(os.path.join(ART, 'layout.json')))
    font = Font(a.client_jar)
    shot = Image.open(a.shot).convert('RGBA')
    if a.clean == 'v032':
        shot = clean_v032(shot, a.shot_gui)
    shot.save(os.path.join(a.out, 'base_clean.png'))
    for g in (2, 3, 4):
        im = render(shot, g, font, NORMAL, layout)
        im.convert('RGB').save(os.path.join(a.out, 'mockup_hud_gui%d.png' % g))
        print('gui', g, '->', math.ceil(shot.width / g), 'x', math.ceil(shot.height / g), 'GUI px')
    st = render(shot, 3, font, STATES, layout)
    st.convert('RGB').save(os.path.join(a.out, 'mockup_hud_gui3_states.png'))
    # side by side: indigo's mockup | our GUI 3, same height
    mock = Image.open(a.mockup).convert('RGB')
    ours = Image.open(os.path.join(a.out, 'mockup_hud_gui3.png'))
    h = 941
    ours_s = ours.resize((round(ours.width * h / ours.height), h), Image.LANCZOS)
    sbs = Image.new('RGB', (mock.width + 24 + ours_s.width, h + 40), (20, 16, 18))
    sbs.paste(mock, (0, 40))
    sbs.paste(ours_s, (mock.width + 24, 40))
    lab = Image.new('RGBA', (400, 12), (0, 0, 0, 0))
    font.draw(lab, 0, 2, 'indigo133 mockup', (0xFA, 0xCC, 0x44))
    sbs.paste(lab.resize((1600, 48), Image.NEAREST), (8, -4), lab.resize((1600, 48), Image.NEAREST))
    lab = Image.new('RGBA', (400, 12), (0, 0, 0, 0))
    font.draw(lab, 0, 2, 'art set, GUI 3 (2304x973 shot)', (0xFA, 0xCC, 0x44))
    sbs.paste(lab.resize((1600, 48), Image.NEAREST), (mock.width + 32, -4), lab.resize((1600, 48), Image.NEAREST))
    sbs.save(os.path.join(a.out, 'mockup_vs_artset_gui3.png'))
    print('wrote', a.out)


if __name__ == '__main__':
    main()
