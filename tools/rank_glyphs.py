#!/usr/bin/env python3
"""Rank icons as chat/TAB font characters (v0.7.0).

Copies the 16 px icons from MMO/rank-icons/16/ into textures/font/rank/ and writes
assets/minecraft/font/default.json, one bitmap glyph per rank, 8 units high (one chat line) from U+E100 up.
The order follows MMO/rank-icons/manifest.json; LuckPerms prefixes use the same codepoints.

  python3 -I tools/rank_glyphs.py <MMO/rank-icons> pack/assets
"""
import json, os, shutil, sys

FIRST = 0xE100

def main():
    src, assets = sys.argv[1], sys.argv[2]
    manifest = json.load(open(os.path.join(src, 'manifest.json')))
    tex = os.path.join(assets, 'runeblock', 'textures', 'font', 'rank')
    os.makedirs(tex, exist_ok=True)
    providers = []
    for i, r in enumerate(manifest):
        shutil.copyfile(os.path.join(src, '16', r['file']), os.path.join(tex, r['file']))
        cp = FIRST + i
        providers.append({'type': 'bitmap', 'file': 'runeblock:font/rank/' + r['file'],
                          'ascent': 7, 'height': 8, 'chars': [chr(cp)]})
        print('U+%04X %s' % (cp, r['rank']))
    os.makedirs(os.path.join(assets, 'minecraft', 'font'), exist_ok=True)
    with open(os.path.join(assets, 'minecraft', 'font', 'default.json'), 'w') as f:
        json.dump({'providers': providers}, f, indent=2, ensure_ascii=True)
        f.write('\n')

if __name__ == '__main__':
    main()
