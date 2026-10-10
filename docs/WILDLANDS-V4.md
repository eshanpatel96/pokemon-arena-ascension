# Pokemon Wildlands V4 — Lab Hub + 2v2 Practice Vertical Slice

## Product direction

Wildlands now uses the native realtime Arena as the gameplay engine. The Emerald overworld experiment is retired for combat.

Arena XL proved that the native Arena controller can operate in a 16384x12288 scrolling coordinate space. That size is a stress ceiling, not the intended 30-team match size.

Recommended first Battle Royale world target: 4096x3072 pixels.
- ~17 GBA screens wide x 19 screens tall.
- ~328 screen-equivalents of area.
- 30 teams averages ~11 screen-equivalents per team before the closing field.
- Enough room for 18+ tile spawn separation without making first contact take forever.

Do not ship the 16384x12288 stress size for 30 teams; it would be far too sparse.

## V4 flow

### 1. Wildlands title
Replace Ascension branding on startup with a dedicated Pokemon Wildlands title presentation.
No Ascension town/career screen should be visible during normal V4 flow.

### 2. Wildlands Research Lab hub
NEW GAME begins in a compact Pokemon laboratory using native Emerald lab/interior assets.

Hub services:
- TEAM TERMINAL: select the two Pokemon used in the next run.
- MOVE TERMINAL: choose four Arena-supported moves for each Pokemon.
- PROFESSOR: career statistics and records.
- QUEUE TERMINAL / transport pad: launch PRACTICE.
- Future mode slots can show Battle Royale as coming soon.

Career stats planned:
- Practice wins
- Battle Royale wins
- Eliminations / KOs
- Matches played
- Highest placement
- Legendary defeats / recruits
- Damage dealt
- Longest win streak

V4 must persist at least matches, wins and eliminations.

### 3. Team selection
V4 test roster uses a curated 16-species final-evolution catalog:
Charizard, Blastoise, Venusaur, Gengar, Alakazam, Machamp, Snorlax, Dragonite,
Tyranitar, Sceptile, Blaziken, Swampert, Gardevoir, Metagross, Salamence, Milotic.

Selection is explicit for:
- player Pokemon
- AI partner
- four moves for player
- four moves for partner

Final Wildlands target remains roughly 80 selectable final evolutions with type/archetype coverage.

### 4. V4 practice match
Practice is a true local 2v2 Arena-world fight:
- selected player Pokemon
- selected highlighted AI partner
- two AI enemies
- all four use the same Arena body/controller/animation/combat model
- no classic battle transition
- no Emerald overworld player controller
- return to the lab when the practice match ends

This is the first required multi-body proof before 30-team scaling.

### 5. Sprite scale test
V4 uses a modest visual reduction target of about 87.5%-90% of current Arena presentation.
Goals:
- preserve species readability
- make the world feel larger
- improve 2v2/2v2v2 combat readability
- do not use tiny Emerald overworld sprites

Use a shared affine scale where possible so the GBA does not need one matrix per Pokemon.
Gameplay collision and attack range should be tuned to the displayed scale rather than leaving obviously oversized hitboxes.

## Real map architecture

Arena XL's repeating court is only a stress floor. The actual world uses chunked Arena terrain.

First Battle Royale map target: 4096x3072 pixels, expandable to 5120x3840 if spawn and POI density require it.

Biome plan:
- central grassland / training grounds
- dense forest with concealment grass
- river / lake / wetlands
- coast / beach
- desert / badlands
- rocky mountain / highland
- volcanic region
- ruins / abandoned structures
- small settlement / roofless buildings
- cave network
- five legendary lairs in the eventual full game

Terrain tags:
- LAND
- WATER
- GRASS / CONCEALMENT
- BURROWABLE
- CLIFF
- BUILDING
- CAVE
- HAZARD

Only terrain near the camera is rendered and fully simulated.

Caves remain part of the same match state. They may stream into a separate Arena chunk/sector through a short doorway/fade, but never enter traditional Pokemon battle mode.

## Spawn rules retained
Every squad spawn must:
- be on certified connected terrain
- have a non-traversal escape path
- have room for both teammates
- meet minimum separation from every other squad
- avoid legendary-lair and premium-loot exclusion zones
- never rely on Surf/Fly/Dig to escape
- reject the whole map layout if 30 valid squad zones cannot coexist

## V4 acceptance
V4 is accepted only when:
1. Pokemon Wildlands branding appears on startup.
2. NEW GAME goes to the Wildlands Lab, not Ascension City.
3. Team Terminal changes the next player + partner Pokemon.
4. Move Terminal changes all four moves for both Pokemon.
5. Professor reports persistent practice stats.
6. Queue launches a native Arena-world practice match.
7. Player and highlighted partner appear from the selected loadout.
8. Two enemy Arena bodies are active and damageable.
9. 2v2 ends correctly when one squad loses both Pokemon.
10. Match returns to the lab and updates stats.
11. The repeating Arena court pop-in is gone in practice.
12. Movement/attacks/dodge remain native Arena-feeling.
13. ~90% sprite-scale experiment is visually readable.
