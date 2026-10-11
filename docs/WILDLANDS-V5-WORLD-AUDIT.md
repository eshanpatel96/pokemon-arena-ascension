# Wildlands V5 World Validation — Engineering Audit

Status labels: **IMPLEMENTED**, **PARTIAL**, **MISSING**, **VALIDATION TARGET**.

## Native Arena systems retained

**IMPLEMENTED — player body/controller.** `src/realtime_arena.c` defines `struct ArenaBody` with Q8 `s32 x,y` coordinates. `MoveDelta`, `Move`, and `TickPlayer` own movement. V5 adds terrain legality to these functions; it does not replace them with Emerald's `PlayerStep` / overworld controller.

**IMPLEMENTED — dodge.** `TickPlayer` retains the existing dash buffer, 10-frame dash, 75-frame dash cooldown, attack cancellation and `DashLanding` path.

**IMPLEMENTED — real-time attacks/cooldowns/hit resolution.** `BeginShot`, `Fire`, `TickActions`, `TickShots`, `ApplyMoveHit`, `ApplyResolvedHit` remain the combat path. V5 adds static map-cover clipping to projectiles/beams.

**IMPLEMENTED — PMD/Arena animation system.** `ArenaSprites_Get`, `ArenaSprites_Decode`, `ArenaRender_Copy` remain the actor renderer.

**IMPLEMENTED — two-body enemy AI.** `TickEnemy`, `AiChooseGoal`, `AiRoute`, `AiTryEvade` remain native. V5 routes those decisions through world terrain when Wildlands world mode is active.

**MISSING — true 2v2.** `struct ArenaState` still contains `struct ArenaBody bodies[2]`. The V4/V5 partner actor is a highlighted follower with PMD animation and terrain routing. It is not a damageable/attacking `ArenaBody`. A real 2v2 requires expansion of target selection, shots, hit resolution, cooldown ownership, status effects and AI from side-indexed 2-body assumptions to a local actor pool. The validation build must not claim 2v2.

**MISSING — 30-duo simulation.** No 60-Pokemon match simulation exists. This is separate from local rendering/combat and will need a lightweight distant-squad simulation plus a bounded local full-fidelity actor pool.

## Native Emerald world data

**IMPLEMENTED — real metatile source, not a floor bitmap.** `bootstrap/wildlands-v5/generate_world.py` builds the validation world from `data/layouts/Route120/map.bin` and `data/layouts/FortreeCity/map.bin`. It writes ROM-resident 16x16 metatile entries to `data/wildlands_world/slice.bin`.

**IMPLEMENTED — reusable General + Fortree tilesets.** `src/wildlands_world.c` uses `gTileset_General` and `gTileset_Fortree` tiles, palettes, metatiles and metatile attributes directly.

**IMPLEMENTED — separate render layers.** The world decomposes each Emerald metatile according to its native `METATILE_LAYER_TYPE_NORMAL`, `COVERED` or `SPLIT` attribute into:
- BG3 priority 3: bottom / floor layer
- BG1 priority 2: middle layer
- BG2 priority 0: foreground layer
- BG0 priority 0: existing Arena HUD

Arena actors remain OBJ priority 1, so native split-layer tree canopies/roof tops can draw in front of Pokemon while floor/middle art remains behind them.

**PARTIAL — structures.** The first Fortree-derived structure is explicitly **cover/scenery only**. It is not enterable in the validation slice. Doors/interiors will be added only with explicit enterable semantics; decorative buildings will never silently act like doors.

## Collision and gameplay terrain

**IMPLEMENTED — solid world cover.** Layout collision bits plus directional/jump-block behaviors feed `WildlandsWorld_LineClear`. Trees, rocks, walls, cliffs and the validation structure therefore block bodies, static line of sight and projectiles.

**IMPLEMENTED — bridge behavior.** Native bridge behaviors are recognized before water behavior. Bridges are walkable crossings and do not inherit deep-water traversal restrictions.

**IMPLEMENTED — deep water traversal rule.** Deep surfable water is tagged `WL_TERRAIN_DEEP_WATER`. Ordinary land actors cannot enter it. Water-type, Flying-type and Levitate Arena bodies may cross it. The V5 partner uses its species typing for the same rule. This is a field trait and does not consume a move slot.

**IMPLEMENTED — wet terrain tag.** Deep water, puddles and shallow flowing water expose `WL_TERRAIN_WET`. The static tag is available to combat/environment logic.

**IMPLEMENTED — tall/long grass concealment.** Native tall/long-grass behaviors expose `WL_TERRAIN_CONCEAL`. Beyond 48 pixels, AI stops refreshing a concealed player's position and uses last-known position; player auto-lock likewise does not acquire a concealed enemy at that distance. Explicit directional aiming still works. Grass is therefore concealment, not invulnerability.

**PARTIAL — environmental reactions.** Existing battle-local water/ice/electric surfaces in `arena_elements.inc` remain. Static world water is now tagged wet/deep-water, but freezing an entire river or propagating electricity across a large static water body is not implemented in the first world validation.

**PARTIAL — destructibility.** Existing seven Arena props are disabled in world mode so they do not duplicate native tile scenery. Native world trees/cliffs/buildings are static cover in V5; they are not destructible yet.

## Streaming / GBA limits

### Coordinate space
4096x3072 pixels = 256x192 Emerald metatiles. Arena Q8 `s32` body coordinates handle this scale comfortably. Earlier Arena XL/XXL tests already exercised much larger coordinates; coordinate width is not the constraint.

### ROM
A raw full 256x192 u16 metatile map is 98,304 bytes. The validation slice is only 40x48 = 3,840 bytes. V4 used 97.92% of a 32 MB ROM, so map data itself is plausible, but the final multi-biome art/bank plan must still be budgeted.

### EWRAM
V4 used 260,142 of 262,144 bytes (99.24%). Therefore V5 deliberately does **not** allocate a full world tilemap in EWRAM. World layout stays ROM-resident; only camera/chunk state and a small VBlank tile-write queue use EWRAM. The V5 build report is the acceptance source for actual post-link memory usage.

### BG VRAM
Validation uses one native Emerald tileset pair:
- General: up to 512 4bpp tiles = 16 KB
- Fortree secondary: up to 512 4bpp tiles = 16 KB
- combined world atlas: up to 32 KB beginning at BG charbase 1
- streamed tilemaps: three 32x32 screenblocks (BG3/BG2/BG1) = 6 KB
- HUD: existing BG0 tile/map allocation

Only a 32x32 hardware tile ring is visible/updated, regardless of total world dimensions.

**REAL CONSTRAINT — final multi-biome island tilesets.** General+Fortree fits. Simultaneously loading every biome's secondary tileset will not. The full island therefore needs region-local secondary tileset bank streaming at safe transition boundaries. That is not yet validated by the forest-river-ruin slice.

### Palette
BG palette bank 0 remains Arena HUD. The 13 Emerald outdoor palette banks are shifted to BG banks 1..13. OBJ palettes are separate. This leaves BG banks 14..15 spare in the validation bank.

### OAM
World terrain/canopies/roofs are BG tiles and consume **zero OAM entries**. Pokemon, projectiles and FX keep native Arena OAM usage. This avoids spending sprites on trees/buildings. True 2v2 and larger local actor counts still need separate OAM/profile testing.

### Frame time
Normal camera motion queues only newly exposed 8px tile rows/columns and commits them in `VBlank_Arena`; map size does not scale per-frame work. Telemetry records VBlank tile count, streamer scanlines, Arena phase scanlines, missed VBlanks and upload/OAM pressure. Feasibility is not accepted until the mGBA runtime run is green and those values are inspected.

## Validation slice

The first implementation slice is intentionally not the full island:
- 40x48 metatiles / 640x768 px
- located inside the final 4096x3072 coordinate space
- exact Route 120 river/pond/forest/tall-grass/bridge terrain
- Fortree-derived cover/scenery outpost
- spans multiple 256px streaming chunks
- player/enemy start on opposite sides of the native bridge
- bounded world nav points generated from legal dry/walkable terrain

Acceptance requires actual runtime movement, scrolling, foreground layering, terrain collision, AI routing, projectile clipping and chunk streaming. Passing this gate allows expansion to the full island; it does not reduce final scope.

## Explicitly not proven by this slice

- true 2v2
- 30-duo/60-Pokemon match simulation
- full five-legendary boss system
- multi-secondary-tileset bank streaming
- enterable buildings
- world-cover destruction
- full-island spawn certification/travel-time balance
- iPhone Delta behavior

Those items remain separate gates and must not be inferred from a successful V5 world-slice build.
