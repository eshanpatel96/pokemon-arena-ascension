# Pokemon Wildlands V2 — Arena Controller + Loadout

## Why V2 exists

The V1 player test proved that Pokemon can coexist on an Emerald overworld map, but the video test showed the visible movement/animation is not acceptable. V1 still uses Emerald's tile-step player controller under static Arena sprites, which causes sliding/floating, poor direction changes and no native Arena attack pose presentation. V2 replaces that bridge instead of polishing it.

## Locked V2 goals

### 1. Arena-quality field movement
- Player Pokemon owns Q8 pixel coordinates in the world.
- D-pad movement is continuous and eight-directional like the existing realtime Arena.
- Diagonal movement is normalized.
- B + direction uses the same short dodge/dash commitment concept as Arena.
- Movement/collision uses the Emerald map as terrain, but never the normal trainer tile-step controller.
- Camera follows the Pokemon smoothly; the hidden native player object exists only as a field/map anchor.
- AI Pokemon use the same movement/collision model as the player.

### 2. Arena sprite state machine in the overworld
- Idle, walk and move-specific Arena animations are decoded from ArenaSprites.
- Facing direction comes from movement or attack aim.
- Attack windup/release/recovery selects the ArenaMoveProfile animation.
- Frames are uploaded only when frame/direction changes, following realtime_arena.c.
- Player, partner and enemies all use the same presentation path.
- No static/floating Pokemon bodies.
- Player and partner remain visually distinct; partner keeps a persistent ally marker.

### 3. Real pre-match loadout
NEW GAME must enter a Wildlands loadout flow before deployment:
1. Pick the player Pokemon.
2. Pick the AI partner.
3. Pick four moves for the player from its compatible Arena-supported pool.
4. Pick four moves for the partner.
5. Confirm loadout, then deploy.

V2 starter catalog:
- Charizard
- Blastoise
- Venusaur
- Gengar
- Alakazam
- Machamp
- Snorlax
- Dragonite
- Tyranitar
- Sceptile
- Blaziken
- Swampert
- Gardevoir
- Metagross
- Salamence
- Milotic

This is a V2 test catalog, not the final ~80 final-evolution roster.

### 4. Loadout information
The selection screen should show:
- Species name
- Type(s)
- HP / Attack / Defense / Speed summary
- Traversal trait: SWIM, FLY, BURROW, or LAND
- Current four selected moves
- Move names, type and simple role/range information where practical

No trainer/NPC is used for selection.

### 5. Battle Royale deployment
- Preserve the V1 certified-spawn rules.
- Player/partner deploy together.
- Enemy squads spawn in separated certified regions.
- V2 remains a local vertical slice; full 30-team remote simulation follows after movement/loadout acceptance.

## Acceptance tests

V2 is not accepted merely because it compiles.

1. Framebuffer/input test: player Pokemon moves continuously in at least four cardinal and two diagonal directions without tile-step pauses.
2. Walk animation frames change while moving and return to idle while stationary.
3. An attack visibly enters the correct Arena move animation before release and recovery.
4. B+d-pad performs a faster dodge movement with recovery.
5. Human trainer sprite never appears.
6. Partner remains visible near the player and has a persistent ally marker.
7. NEW GAME cannot deploy until player, partner and both four-move loadouts are confirmed.
8. Selected species/moves are the species/moves that appear after deployment.
9. Certified spawn and team-separation audits still pass.
10. Player Delta test confirms movement feels materially like the native Arena rather than Emerald walking.

