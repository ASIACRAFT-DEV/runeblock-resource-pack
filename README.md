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
