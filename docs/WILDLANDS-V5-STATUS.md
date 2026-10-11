# Pokémon Wildlands V5: status ledger

Branch `wildlands-v5` (integration of `wildlands-v5-world-validation` + the gameplay work).
Each CI run builds two ROMs and runs the mGBA harness on each:

- **slice**: 640x768 Route 120 validation slice (the handoff's first proof).
- **island**: full 4096x3072 island generated from the approved map concept.

Evidence for every run (smoke log, screenshots, build/memory report, patched
source snapshot) is published to branches `wildlands-evidence` (runs/<id>-<world>)
and `wildlands-engine-src`. ROMs are Actions artifacts `WILDLANDS-V5-<world>-ROM`
(never committed: the repo is public).

Labels: **PASS** = automated mGBA check passed on the named ROM. **BUILT** =
implemented and compiled, not runtime-verified. **NOT DONE** = not implemented.
Nothing here is Delta-verified; that is the owner's playtest.

## Gate ledger (latest verified run: see bottom)

| Gate | Status | Evidence |
|---|---|---|
| A Reproducible build | PASS | Clean CI assembly from pinned V11.1 inputs; ROM header/size/SHA in manifest; EWRAM 99.66%, IWRAM 94.27%, ROM 97.95% (slice) / 98.45% (island) |
| B Game-time cadence | PASS | Simulation steps per emulated frame 95-99% idle/4 directions/attacking (slice) and 97-99% idle/travel E/N/W (island, AI active). Render rate ~40% (about 30 fps visuals): see limits |
| B Cross-chunk streaming | PASS | World telemetry: chunk crossings, no rebuild resets during travel; island travel spans many 256px chunks |
| C Interactive terrain | PASS (telemetry + screenshots) | Collision/water/bridge/concealment/projectile-block audit flags; tall-grass concealment beyond 48px for AI, player auto-lock and the map. Video walkthrough not produced |
| D True 2v2 | PASS (first slice) | Partner and enemy wing both fire and land damaging hits; both enemies take damage and KO; zero friendly hits; enemy lead KO promoted its wing in the island run. Player-side promotion not yet observed in a run |
| E Closing zone | PASS | Deterministic circles from encounter seed; explore -> warning (next circle on legal ground) -> shrink; exposure damage to actors outside, including partner; pause stops the clock; deterministic simultaneous-elimination tie-break (code) |
| F Pickups | PASS | Collect-once (0 duplicate attempts), both teams collected, stages applied to both members, cap +2, SPD affects movement only |
| G Live map | PASS | START -> MAP renders terrain from the collision table plus live markers, circles, loot (slice and island) |
| G Move editor | BUILT | Lab MOVE EDITOR sign: native relearner UI listing legal Arena-supported moves, no items. Not exercised by the harness |
| G Shinies | NOT DONE (audited feasible) | One 16-colour palette per Arena species shared by all frames; every actor owns an OBJ palette slot, so normal + shiny of one species can coexist. Needs a build-time shiny palette table; rarity undecided |
| H Title | BUILT | Approved concept at native 240x160, 256 colours, caption removed |
| I Island + landmarks | PASS (prototype) | 256x192 native metatiles from the concept plan; 97.4% of walkable land reachable on real collision; all five lairs reachable with 2-3 approaches; nav graph 2387 nodes |
| I Enterable interiors | PASS | 11 rooms from real Emerald interior layouts, each rendered with its own native tileset pair (swapped under forced blank): Mewtwo = Weather Institute, Rayquaza = Sky Pillar summit, Lugia = Navel Rock depths, Ho-Oh = Navel Rock peak, Kyogre = Marine Cave chamber, 3 Fortree treehouses, 3 wilderness houses. Doors from native warp events plus cliff cave mouths; every door's outside cell is reachable on foot (build audit). Harness entered and exited all 11 doors on the island and the slice house; supplies pickup verified |
| I Room pickups | PASS | Houses: SUPPLIES (both members +40% HP). Lairs: CACHE (+1 ATK/DEF/SPD) and SUPPLIES. Popups "TEAM HEALED" / "TEAM CACHE +1 ALL" |
| AI Enemy duo brain | PASS (slice) / BUILT | FIGHT (focus fire on the weaker / better-matched target), RETREAT in bursts when hurt and behind (cover, tall grass, safe circle), LOOT when nothing visible, RAID lair caches and supplies through doors. Harness verified fight and retreat decisions; raids not yet observed in a run |
| J 30 duos / 60 Pokémon | NOT DONE | Requires owner decision (below) |

## Known limits (honest)

- **Render rate ~30 fps.** Native `BuildOamBuffer` alone is ~67 scanlines with
  ~50 live sprites. Game time is real-time via fixed-timestep catch-up, so
  movement/AI/storm speed is correct; visuals update about every other frame.
- **Lairs have no boss yet.** Each lair is enterable with a cache inside;
  the legendary itself is not spawned. Boss encounters are the next
  proposal (needs owner approval: third team in the Arena, budget below).
- **Off-screen sprites** are hidden from the OAM build (GBA OAM coordinates
  wrap, which made distant enemies flash on screen in the playtest).
- **Island art seams.** Prefab borders and some river/coast edges still read as
  rectangles; generator polish pass pending.
- **Practice balance.** V4 practice rivals are Lv15 versus a Lv60 squad, so
  matches end quickly.
- **Test hooks.** `gWildlandsZoneTestSpeed` and `gWildlandsTestPeace` exist
  only for the harness and are 0 in play.

## Decision needed: 30 duos

Measured constraints: EWRAM 99.66% used (about 880 bytes free); each full
Arena actor costs ~2 KB of frame buffers plus AI and OAM. Sixty full-fidelity
actors cannot fit. The feasible design is a local full-fidelity pool (the
current 4 actors, maybe 6) plus a lightweight off-screen simulation for the
other duos (position, HP, zone damage, abstract fights) with promotion into
the local pool on approach. That is a substantial milestone. Options: build it
as V5.1, or ship V5 as 2v2 and schedule it for V6.

## Proposed V6 (not approved)

Region tileset streaming (true volcano / sea shrine art), legendary boss
encounters at the five lairs, the off-screen squad simulation above, shiny
palettes, seam blending, render-rate work (sprite count / OAM build).

## Latest verified run

- Run: https://github.com/eshanpatel96/pokemon-wildlands/actions/runs/38137170086 (source `20f1b04`)
- Slice ROM: artifact `WILDLANDS-V5-slice-ROM` (11701720722), SHA-256 `da7ba7b5a644ce422f60ab740c503a0d07e045824ba67729f5cfa6e1b98702cf`. Smoke: 30 PASS / 0 FAIL.
- Island ROM: artifact `WILDLANDS-V5-island-ROM` (11702240328), SHA-256 `48d23abe11ec2a41bc396528007de8f6117b73c2cc65125d7accb51d6575eec5`. Smoke: 9 PASS; sim cadence 97-99% idle and travelling E/N with AI; the encounter was won during the W leg (Arena exited to the lab), which the harness records as a cadence miss.
- Evidence: branch `wildlands-evidence`, `runs/38137170086-slice` and `runs/38137170086-island`.

## Build recipe

`.github/workflows/wildlands-v5.yml`: assemble V11.1 (run 37959084673 artifacts),
`arena-xl/apply.py`, `wildlands-v4/apply.py`, `wildlands-v5/generate_world.py`
(slice) or `generate_island.py` (island, uses `bootstrap/wildlands-map` and
`docs/art/wildlands-map-concept-v3.png`), `wildlands-v5/apply.py`,
`squad_apply.py` (2v2, zone, loot, map, catch-up), `move_editor_apply.py`,
`wildlands-v4/generate_ui.py`, `wildlands-v5/title.py`, native asset build,
compile, mGBA smoke (`wl_smoke.c` + `smoke*.commands`).
