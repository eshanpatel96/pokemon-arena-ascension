# V9 Boss Presentation — Verified Source Audit (release blockers)

**Recorded:** 2026-10-08. **Audit basis:** actual assembled Championship V9 source (ROM build `d004c4da56784a3f7c3ac6a69ae6f3c4df7c7264`, compiled `37846797245`) plus the original Emerald map.bin/layout/metatile/palette assets, pinned pret/pokeemerald `5eff78649e7170a877b961ef0b3da13b81a16038`.

**Status: FAIL against user's V9 boss-presentation acceptance.** This is a static source inspection, not a proven Delta runtime bug or gameplay screenshot. Do **not** call the present Championship DEV ROM polished or ask the user to do a full eight-tower acceptance test before these blockers are repaired.

## What the ordinary tower scripts actually do

In each `AscensionTower1..8/scripts.inc`, the Master stands at (5,5). On player A interaction, confirmation is required. The Master `walk_left` once, is removed, and the player `walk_up` once. A challenger is created at (5,1), then `walk_down` twice to (5,3), opposite the player at about (5,5). Script begins `dowildbattle`, but the original battle setup switches it to a dynamic trainer-party battle when `gAscensionTrainerPartyActive` is set. After the whole opposing party is defeated, challenger `walk_up` twice, is removed, and the next enters. Player trainer appears on real-time Arena sideline at approximately (8,118) and opponent at (232,50), with inward facing set by `CreateSidelineTrainers` (two sprites when BATTLE_TYPE_TRAINER).

This is **implemented source**, but not shown/validated in Delta. The Master does not physically return between fighters: recovery checkpoints are script dialogue/heal specials while Master is absent.

## All eight boss maps: current source-level defects

All eight have `MAP_SCRIPT_ON_FRAME_TABLE` + automatic `dowildbattle` after introductory dialogue. No deliberate player-controlled approach, A-button leader interaction, leader choreography, or boss battlefield walk-up occurs. `AscensionBronzeBoss` and `AscensionLeader2..8` reuse native Emerald map layouts and stage numbers; these are not custom V9 showcase arenas.

| Tier | Original overworld room | Entry tile from tower warp | Boss NPC | Exact native metatile collision / route |
|---|---|---|---|---|
| Bronze | Rustboro Gym 11×20 | (11,9) | (5,2) | **OUT OF BOUNDS**: valid x only 0..10 |
| Gale | Fortree Gym 20×25 | (15,7) | (15,2) | Entry valid, but entry component **cannot reach the boss** through remaining native puzzle barriers |
| Verdant | Battle Palace Battle Room 15×10 | (5,7) | (13,2) | Entry valid, leader reachable (preliminary base64 scan wrongly flagged the entry) |
| Phantom | Mt Pyre 2F 13×13 | (6,8) | (6,4) | Entry valid and boss-adjacent floor reachable; **boss NPC is placed on a collision-blocked tile** |
| Inferno | Lavaridge Gym 17×19 | (13,12) | (13,9) | Entry and boss reachable, but **original southern exit warp lies in a different connectivity region** |
| Tidal | Sootopolis Gym 17×26 | (8,7) | (8,2) | Entry and boss reachable through native tiles |
| Thunder | Mauville Gym 10×21 | (5,7) | (5,2) | **ENTRY BLOCKED** (collision 1) |
| Astral | Mossdeep Gym 26×36 | (22,11) | (23,7) | **ENTRY BLOCKED** and **boss NPC tile blocked** |

Collision means the GBA metatile collision bits derived from the exact pinned upstream `map.bin`. Native scripted puzzle tiles/warps may have additional behavior, so the source checks must still be verified in emulator.

### What the player sees in the real-time battle

The boss map's **overworld** visuals and the real-time Arena backgrounds are distinct. Native `arena_biomes.inc` boss stages are: Bronze 8 (stone Gym), Gale 13 (Fortree Gym), Verdant 5 (grass), Phantom 14 (psychic), Inferno 16 (volcanic), Tidal 15 (water Gym), Thunder 10 (electric Gym), Astral 14 (psychic). These are existing native Emerald Arena backgrounds selected in source, **not eight independently redesigned interactive boss stages**, and on-phone screenshots have not yet been captured.

## Mandatory before the user's full V9 test

1. Remove the boss on-frame auto-fight triggers; a boss should be visible while the player moves under normal control. Initiate via walking up and pressing A or a clear **opt-in physical start line**, with a real confirmation/cancel path.
2. Correct and validate the boss-room player entry coordinates for all eight, based on original map.bin bounds, passable collision and actual adjacency. Place leaders on accessible floor tiles. Do not allow a one-way trap on decline or after save/reload.
3. Rework room navigation where the original Gym's puzzle tiles isolate the player from the Master (at minimum Gale; evaluate Thunder and Astral). Use existing native floor metatiles/chambers and theme assets rather than assuming a music/name swap is enough.
4. Present Master and boss differently from ordinary challenger: separate boss preparation/recovery stage, approach, opposing leader intro, original real-time battle, correct win/outro, next-rank unlock and exit. Ensure source variation/rematch data doesn't accidentally replace the final signature legendary.
5. Show **real screenshots/video from mGBA and Delta**, not only static rasterization, of eight overworld boss approach maps and eight real-time battlefield backgrounds. Capture arrival, movement, A interaction, leader facing, battle start, final KO, win/loss, save/reload.
6. Preserve the regular tower ceremony and improve visible Master re-entry for advertised heal breaks; validate both side trainer sprites appear and match the actual challenger native trainer photos.

**Release decision:** current compiled V9 Championship DEV ROM is useful as a source baseline but fails the user's explicit near-perfect eight-boss acceptance. Do not re-label it V9 FINAL or direct an end-to-end acceptance test before fixes.

## Evidence / preview provenance

The Project conversation contains the generated audit contact sheet `V9-eight-current-boss-rooms-source-render.png` and eight individual room PNGs (8bpp-style reconstruction of original tilesets/metatiles/palettes, with labeled scripted entry and NPC positions). These are **source-art previews, not actual game captures**. GitHub short workflow `v9-boss-map-previews.yml` produces `V9-BOSS-NATIVE-MAP-ASSETS`, the exact original art/layout backing the previews. Some background transparency/layering and overworld sprites may not match a live emulator rendering.

### Next milestone gate

An accepted V9 boss pass is recorded **separately for all eight**: spawn walkable, approach reachable, one free-movement segment, consent prompt, Master stages/faces correctly, side trainers visible in native 1v1 real-time Arena, no immediate auto trigger, signature boss last, heal/rewards, deliberate exit, fail/retry and cold reload. Only then invite the player to certify the first eight-tower run.
