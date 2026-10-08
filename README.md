# Pokémon Arena: Ascension

A private GBA development project built **on the original Emerald Arena real-time combat engine**, not V5's replacement arcade engine.

## Current V6.1 milestone

The full upstream Emerald/Pokémon Arena source is reconstructed at build time; the **Ascension-specific changes are now committed here**, in a hash-verified compact overlay. This avoids committing copyrighted ROM binaries or thousands of untouched upstream files.

V6.1 source additions:
- Genuine Emerald overworld **Ascension City** and shared tower hall, reusing authentic Battle Frontier artwork
- First-visit city orientation and optional tutorial practice fight
- Career/demo start warp beside the plaza guide, rather than the moving truck
- Eight three-floor tower ranks plus a three-fight Champion Summit, with save variables
- Original Emerald Arena sprites, scenery and physics retained, modest experimental visual/movement tuning

**Not yet a playable release:** Full GBA compilation, emulator testing, first-arrival scripting, save/load, faint/switch/PP fallback, and all tower transitions still require verification.

## Build and CI

The workflow [Ascension V6.1 native GBA build](.github/workflows/ascension-v6.yml) retrieves the pinned Emerald and original Arena source, applies `bootstrap/overlay.part*.b64` using `bootstrap/apply-ascension.sh`, installs agbcc and ARM build tools, generates map files, imports original sprite assets and attempts to compile a ROM.

The overlay bytes are reconstructed with SHA-256 verification. Both the source revision and overlay are pinned. A successful GitHub Action creates a **private untested GBA artifact**, not an advertised finished product.

Open the repository's [Actions tab](https://github.com/eshanpatel96/pokemon-arena-ascension/actions) to review workflow results and errors. Logs are uploaded on failure when available.

The separate [engine bootstrap](.github/workflows/engine-bootstrap.yml) builds the *original* Arena baseline for compiler diagnostics, not the new Ascension game.

## Rules

- Preserve Emerald Arena's detailed Pokémon, animations and terrain.
- Build native Emerald overworld maps and real tower progression, not a replacement game.
- No V4 custom boot gimmick or V5 arcade title screen.
- No committed `.gba` files or proprietary ROM dumps; never mistake a source test for Delta gameplay validation.
- Remain a noncommercial fan-made project.

## Upstream

- [pret/pokeemerald](https://github.com/pret/pokeemerald) – Emerald GBA decompilation
- [GBurgardt/pokemon-emerald-arena](https://github.com/GBurgardt/pokemon-emerald-arena) – original real-time Emerald Arena engine
