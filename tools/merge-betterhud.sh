#!/bin/sh
# Merge the BetterHud plugin's generated pack (box: plugins/BetterHud/build.zip) into pack/.
# BetterHud draws the HUD with font glyphs + a core text shader, so its build must match the box's config exactly:
# re-run this after every change to betterhud/ (upload it, `hud reload` in the panel console, fetch build.zip).
#
#   tools/merge-betterhud.sh /path/to/build.zip
#
# Our pack is format 75 only, so BetterHud's overlays are flattened: base assets, then the overlay whose range
# holds 75 (betterhud_1_21_6, formats 56-99) on top. Our pack.mcmeta and pack.png stay.
set -eu
ZIP=${1:?usage: tools/merge-betterhud.sh build.zip}
cd "$(dirname "$0")/.."
TMP=$(mktemp -d)
trap 'rm -rf "$TMP"' EXIT
unzip -q "$ZIP" -d "$TMP"
grep -q '"betterhud_1_21_6"' "$TMP/pack.mcmeta" || { echo "overlay betterhud_1_21_6 not in pack.mcmeta: check the format ranges" >&2; exit 1; }

# drop the previous merge (everything BetterHud owns)
rm -rf pack/assets/betterhud pack/assets/minecraft/shaders
rm -f pack/assets/minecraft/textures/gui/bars.png pack/assets/minecraft/textures/gui/sprites/boss_bar/*_background.png \
      pack/assets/minecraft/textures/gui/sprites/boss_bar/*_progress.png

cp -R "$TMP/assets/." pack/assets/
cp -R "$TMP/betterhud_1_21_6/assets/." pack/assets/
echo "merged $(find "$TMP/assets" "$TMP/betterhud_1_21_6" -type f | wc -l | tr -d ' ') files from $ZIP"
