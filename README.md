# RuneBlock resource pack

Resource pack for the RuneBlock MMO server (Minecraft **1.21.11**, resource pack format **75**).

- `pack/` is the pack root (`pack.mcmeta` + `assets/`). Custom content goes under `assets/runeblock/`.
- The server sends the pack **after** a player joins, never during login (a pack in the login phase caused
  mass join timeouts on another server of ours).

## Releasing
1. Commit the changes, then tag and push: `git tag v0.1.0 && git push origin v0.1.0`
2. The `release` workflow zips `pack/` and publishes a GitHub release whose notes give the **URL** and **SHA-1**.
3. Point the server at that URL + SHA-1, then confirm in game that the pack downloads.

Releases are immutable: never replace a released zip in place. Players' clients cache by SHA-1, so ship a new tag instead.

## Boss models
For now the two story bosses use vanilla mob bodies (wither, warden), so they need nothing from this pack.
Blockbench models for them go here later (they are built by the server's model plugin into its own zip, then merged in).

## Bottom HUD (BetterHud, v0.3.2)
HP (red) and mana (blue) bars over a reskinned hotbar, drawn by the **BetterHud** plugin (1.14.1 on the box; 2.x needs Java 25).
The vanilla hearts, drumsticks and armour are blanked here; crosshair, XP bar, air and mount hearts stay.
- `tools/gen_hud.py` draws the pictures: hotbar sprites into `pack/`, bar pictures into `betterhud/assets/`
- `betterhud/` mirrors the box's `plugins/BetterHud/` (images, layouts, huds, texts, shader.yml). Upload it, run
  `hud reload` in the **panel console** (RCON can't run it), fetch `plugins/BetterHud/build.zip`, then
  `tools/merge-betterhud.sh build.zip`. The merged files must match the box's config exactly, so always re-merge after a change
- BetterHud gotchas (1.14.1, seen in game): text glyphs are built at 16 px, so layout text `scale: 0.5` = vanilla size; `/` in a `pattern` escapes the next char (write `//`); each layout draws shifted left by ~half its width, so `huds/` pixel x = wanted left edge + half the bar width
- `shader.yml` `bar-color: pink`: BetterHud blanks that boss bar colour for its own carrier bar. Never yellow (ArcaneSouls cast bar, tracker, escort HP)
