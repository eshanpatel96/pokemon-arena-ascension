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
| B Game-time cadence | PASS | Simulation 99-100% of real time in every biome and on long travel. World render locked at 30 fps (every frame advances exactly two 60 Hz steps); walking window: 98% of frames on time, 2% one VBlank late |
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
| I Enterable interiors | PASS | Rooms from real Emerald interior layouts, each rendered with its own native tileset pair: Mewtwo = Weather Institute (154 floor cells), Rayquaza = Altering Cave (263), Lugia = Faraway Island grove (180), Ho-Oh = Birth Island summit (169), Kyogre = Seafloor Cavern chamber (233), 3 Fortree treehouses, 3 wilderness houses. Doors from native warp events plus cliff cave mouths; every door's outside cell is reachable on foot (build audit). Harness entered and exited all 11 doors on the island and the slice house; supplies pickup verified |
| I Room pickups | PASS | Houses: SUPPLIES (both members +40% HP). Lairs: CACHE (+1 ATK/DEF/SPD) and SUPPLIES. Popups "TEAM HEALED" / "TEAM CACHE +1 ALL" |
| I Biomes + clearings | PASS (island) | Five biomes on native secondaries streamed per region (woodland/Fortree, desert/Mauville, mountain/Fallarbor, volcano/Lavaridge, beach/Slateport) with primary-only belts; 16 named clearings with native landmark prefabs, cover props and >=2 exits; walked and cadence-checked in every biome (95-100%) |
| I Cover | PASS (build audit) | Solid tiles (trees, rocks, cliffs, buildings, props) block movement and shots; water blocks land movement only; tall grass conceals; canopy layer draws behind actors and pickups. Invisible walls (ground art with collision) cleared and audited to 0 in CI |
| AI boss runs | PASS (island) | Utility score per lair (storm coverage now and next circle, type matchup, HP, distance, crowding, late-game caution, comeback bonus); off-screen duos travel the nav graph to the door, fight a simulated round (win: the legendary joins them with heal and +2 levels; loss: chip damage stays on the legendary, duo escapes hurt or is out); the on-screen duo walks to the door and hands over. Harness: 2 attempts, 1 legendary taken by AI, 1 escape |
| Storm rain | PASS (island) | Rain streaks drawn only over the part of the screen the storm covers (no free BG layer for fog), plus the violet tint and edge markers; 16 streaks visible outside the circle, none indoors |
| AI Enemy duo brain | PASS (slice) / BUILT | FIGHT (focus fire on the weaker / better-matched target), RETREAT in bursts when hurt and behind (cover, tall grass, safe circle), LOOT when nothing visible, RAID lair caches and supplies through doors. Harness verified fight and retreat decisions; raids not yet observed in a run |
| J 30 duos / 60 Pokémon | PASS (island) | Duo director: player + 29 AI duos (lobby level = player level minus 0-8). One duo fights at full fidelity; the rest run an off-screen sim (travel, storm, sim-vs-sim fights, lair raids). Nearest duo takes over on elimination; far/near swap. Island run: 29 -> 19 left, 11 swaps, 10 sim eliminations; LEFT counter and kill feed |
| Legendary bosses | PASS (island) | Mewtwo/Lugia/Ho-Oh/Kyogre/Rayquaza wait in their lairs (level +5, double HP, +1 DEF/SPDEF). Beaten: joins as partner (old partner restored after the match), team full heal +1 ATK/DEF/SPD. Harness: Mewtwo active in lair, KO, joined as battler 2 |

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

## 30 duos (resolved)

Measured constraints: EWRAM 99.81% used (about 500 bytes free); each full
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

- Run: https://github.com/eshanpatel96/pokemon-wildlands/actions/runs/38160721744 (source `178ab61`)
- Island ROM: artifact `WILDLANDS-V5-island-ROM` (11710691134), SHA-256 `90df4542157e58a6d7054c73c1e0c6480ad556c7052245f2bc77dab0789c160a`. Smoke 37 PASS / 0 FAIL; cadence 96-99% with the 30-duo director running.
- Slice ROM: artifact `WILDLANDS-V5-slice-ROM` (11710880319), SHA-256 `2803eebee876b4e7f0a34bac2e180330ee529502150f75c455e2f9301194985b`. Smoke 45 PASS / 0 FAIL.
- Flicker fix verified: BG1/BG2/BG3 scroll buffers identical on 8 consecutive frames while moving (previously BG1 snapped to 0,0 every other frame).
- Evidence: branch `wildlands-evidence`, `runs/38160721744-*`.

## Build recipe

`.github/workflows/wildlands-v5.yml`: assemble V11.1 (run 37959084673 artifacts),
`arena-xl/apply.py`, `wildlands-v4/apply.py`, `wildlands-v5/generate_world.py`
(slice) or `generate_island.py` (island, uses `bootstrap/wildlands-map` and
`docs/art/wildlands-map-concept-v3.png`), `wildlands-v5/apply.py`,
`squad_apply.py` (2v2, zone, loot, map, catch-up), `move_editor_apply.py`,
`wildlands-v4/generate_ui.py`, `wildlands-v5/title.py`, native asset build,
compile, mGBA smoke (`wl_smoke.c` + `smoke*.commands`).

## Run 38172551959 (source a0fe30f): biome round 2

- Island 66 PASS / 0 FAIL, ROM SHA-256 7cbd3fb23ba075bea5fe14256a0d6faa5e23640efeee157dccb2316552aebdd8 (artifact 11714796435)
- Slice 45 PASS / 0 FAIL, ROM SHA-256 46ed572fa2950301491ed4304b35fa6deb9c0d81118a6e19162060252abf2930
- Fixed: travel cadence 49-63% (nav fallback scanned all anchors), 18-frame hitch on enemy duo swap (CreateMon learnset replay), lavender puddle-fill ponds, 827 invisible-wall cells, cramped Lugia/Ho-Oh/Rayquaza lairs; mountain and beach biomes doubled
- Asset audit: no palm-tree tiles exist in Emerald outdoor tilesets (Slateport, Dewford, Pacifidlog, Battle Frontier checked); beach uses Slateport umbrellas/chairs/Seashore House and native sea rocks
- Still open: render rate ~28-34% of VBlanks (simulation stays real-time); small square grass patches with a stone centre in the highlands; AI lair raid not yet observed in a run; shinies not done; no Delta playtest

## Run 38179606785 (source 092ae12): boss AI, storm rain, frame pacing

- Island 104 PASS / 0 FAIL, ROM SHA-256 b569a6258ebc08fe2abff57e43a02b0177a828cbf286310d0a93842354373b39 (artifact 11716224775)
- Slice 46 PASS / 0 FAIL, ROM SHA-256 91f34d2ebd8cac89cf71b9930dc12899cd87bcfe3c0a2cbbffc08fbecf7153c6 (artifact 11717088819)
- Frame pacing: locked 30 fps world render; cost cuts (no idle 240-colour palette reblend, memoised move profiles, cheaper pickup scans, HP-only HUD repaint, HUD work split over two frames, bounded A*, no arena-corner scan on the island, director mons built at level 1)
- Boss runs and rain verified in the harness; invisible walls 0; no Delta playtest yet
