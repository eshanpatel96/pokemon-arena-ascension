# V11 Championship presentation and regression contract

**Project:** Pokémon Ascension Arena, V11 (working branch `v11-tower-redesign`).
**Status:** approved direction and implementation plan; this document is not a compiled ROM, mockups are not game screenshots, and no Delta gameplay pass is claimed.
**Scope priority:** later user direction > existing V10.2 gameplay acceptance > visual proposal. **No scope cuts.**

## Preserve the working V10.2 base

- Pin the known V10.2 baseline at `v10-2-full-test` commit `5e6d5517cab706753debd1cce01a0d625a542b6e`; the packaged, successfully compiled ROM source in the checkpoint is `c879a1c90d37bff86f8733d4ad06c19eaf9e5059`. Retain its artifact/hash and an independent tested save backup. Do not merge V11 into `main` during experimental development.
- Preserve Emerald Arena 0.13.0 native real-time engine, small size/weight-aware sprites, L/R selected attacks+A, B/direction dodge, native Bag and switch/faint rules, persistent 187-species career, money/rewards and existing save fields.
- The 50 tower encounters + five six-Pokémon Championship rounds + eight Masters encounters (63) must remain reachable. The 8 tower boss rooms + Champion native-tile ninth are designed/staged, not yet all committed/compiled.
- **Known unclosed V10.2 requirements remain V11 release blockers, not abandoned features:** all 8,776 legal species-move pairs vs only 3,051 supported real-time pairings; Box selection; EV/nature respec; native Wardrobe persistence/in-battle appearance; eight real boss hazards; save and full Delta campaign certification.

## The actual existing Championship contract (do not accidentally change)

Native existing source: `bootstrap/v9-championship.py`, `AscensionSummit`, `AscensionLeader9` and original Arena stage routing.

1. **Elite I — Arctic Tempest (Articuno last):** Walrein, Dewgong, Lapras, Glalie, Cloyster, Articuno.
2. **Elite II — Iron Architect (Registeel last):** Magneton, Skarmory, Metagross, Scizor, Armaldo, Registeel.
3. **Elite III — Lightning Sovereign (Raikou last):** Ninjask, Sandslash, Electabuzz, Crobat, Manectric, Raikou.
4. **Elite IV — Crystal Oracle (Regice last):** Claydol, Slowbro, Gardevoir, Alakazam, Jynx, Regice.
5. **World Champion — Ascension Throne (Ho-Oh last):** Machamp, Absol, Gyarados, Slaking, Rayquaza, Ho-Oh.

All five six-member enemy teams fight with one active Pokémon on each side, replacing the fainted opponent correctly. Champion has Rayquaza as the penultimate member and Ho-Oh as final ace. Elite II and Elite IV offer **full team recovery after victory** (the latter before the Champion). No other automatic full heal; native battle item use remains available. Losing resets the next Championship attempt to Elite I and deducts the intended once-only capped defeat fee; earned recruitment licenses persist. Preserve the 25 distinct Championship reward licenses and once-only storage-safe claim path.

## V11 native-room look targets (visual design, not implemented fact)

These four Elite chambers join the existing *ninth* Ho-Oh Champion concept; together with the eight tower leaders there are **13 distinct end-of-rank boss/championship chamber identities**. Avoid a misleading assertion that there are only nine boss fights in the whole career.

| Stage | Overworld room | In-battle real-time look/mechanic target | Reuse-first art recipe |
|---|---|---|---|
| Elite I: Frozen Sky Sanctuary | Pale blue crystalline floor, symmetric ice pillars, Arctic gateway, elevated legendary dais | Drifting snow, telegraphed gust/ice patches with safe lanes; Articuno finale | Sootopolis/ice and existing sky/wind Arena effects; minimal recoloring |
| Elite II: Hall of the Iron Titan | Slate/metal floor, mechanical paired pylons, steel central aisle, Registeel plinth | Timed guards/cover columns and heavy strike warning arcs | Mauville/metal native metatiles + existing arena solid cover |
| Elite III: Stormheart Arena | Dark-blue storm stone, bright yellow conductor strips, paired ground pylons, Raikou platform | Announced shock lanes, dodge windows, grounded safety zones | Mauville electric gym tiles and existing shock/weather behavior where supported |
| Elite IV: Prismatic Crystal Sanctum | Indigo crystal gallery, reflective mosaic floor and symmetrical crystal obelisks | Psychic-type directional cover and changing clear sightlines; no unavoidable flash | Mossdeep/palace-native tiles and existing psychic prop effects |
| Champion: Celestial Crown Coliseum | White-gold royal stone, crimson/amber banners, long processional walk, high Ho-Oh dais | Distinct ceremonial firelit finale with existing fire stage/effects, staged legendary entry | The ninth V11 native Champion layout concept, original championship/palace tiles; no new bitmap pack by default |

The four Elite rooms must visually differ from tower bosses: Articuno is winter/sky rather than Tidal, Registeel is military-iron rather than Thunder, Raikou is storm-gold rather than Thunder's reactor, Regice is crystalline/prismatic rather than Articuno's snow, and Ho-Oh is ceremonial sunset/royalty rather than Inferno's furnace.

## Geometry and memory feasibility

- Stage all four additional Elite layouts as **19×21 native metatile rooms**, 399 tiles × 2 B = 798 raw bytes each / **3,192 bytes raw** total. The eight staged tower map concepts plus Champion ninth total 7,182 raw bytes, so 13 room layouts would total **10,374 raw bytes before headers, events, NPCs, scripts, border tiles and map tables**. Do not interpret raw-map savings as a guaranteed linked result.
- Last recorded V10.2 link had only **47,480 B ROM**, **2,154 B EWRAM**, **1,876 B IWRAM** spare. Run the linker on the exact merged candidate to measure all three again and measure runtime OAM, VRAM, DMA and frame pacing. Do not increase RAM just to store room art; reuse original tilesets and palettes, share scripts/event templates and use map-local geometry.
- Protect the 32 MiB GBA limit and original engine. If headroom falls too far, reclaim duplicated static art/tables and pool scripts before proposing omission of approved features.
- The real-time combat renderer is separate from the walkable overworld chamber. Verify both the map visual and the actual arena background/hazards rather than claiming map edits change combat visuals automatically.

## Fight flow and non-regression contract

- Foyer briefing -> deliberate door -> walkable physical boss-room entry -> leader visible at far end -> clear walk-up path -> A/Yes confirm -> player vs trainer staged on **opposite sides of the inner square**, facing across the center, Master outside the lane -> full six-Pokémon realtime party fight -> no premature floor win -> named result dialogue, license reward, correct exit / next elite transition.
- Keep boss and assistant on walkable/approachable event positions. The trial-room staging fix in V10.2 is not automatically proof of Summit, Elite or Masters correctness.
- Preserve Elite heal boundaries II/IV and no hidden auto-heal. Canceling a challenge must never consume a reward/heal or warp. Defeat is charged only once, restarts at Elite I, and does not erase earned licenses.
- Keep previous saves able to CONTINUE. Avoid changing save layout/flag allocations; any necessary new persistent feature requires a collision scan and migration plan.
- Title/menu is a separate V11 gate: preserve approved Shadow Lugia title concept; A/START to menu, NEW GAME to Arena preset (not Birch), CONTINUE to old save, OPTIONS intact, corrupted/recoverable save warnings and deliberate overwrite confirmation. Do not simply remove the SELECT empty-save safety guard.

## Staged implementation and acceptance

1. Freeze source SHA, ROM digest, previous save files and baseline recorded test script. Work only on `v11-tower-redesign` / a subordinate feature branch; never silently modify main.
2. **Reference Bronze + Elite I vertical slices:** import one staged native boss map at a time, build, inspect static map collision and walk-up, then inspect 240×160 mGBA/Delta screenshots and exact stage behavior. Establish the reusable pattern before spreading.
3. Implement all remaining eight tower/Champion native rooms, then Elite I–IV individual chambers. Wire real source map IDs, local NPC coordinates, directional facing, exits and existing fight scripts; no duplicate progression/reward handler.
4. Reuse native battle stages, add only bounded/interactable hazards whose engine behavior can be tested. Compare each *overworld* and *real-time* arena; preserve six-Pokémon sequencing and sig legendary as final entry.
5. Implement Shadow Lugia title and safe visible New Game route with save-status matrix. Validate zero save, existing save, corrupt/recoverable save and cancel restart separately.
6. Run CI build/static tests and ROM/RAM headroom gates, then emulator and physical iPhone Delta flows. Regression: 50 towers + 5 Champion + 8 Masters, money losses, all 187 license claims, switch/faint/Bag/PP, Move Studio legal move editor, EV/Wardrobe, gates/warps, checkpoints and reload. Record tests by exact SHA and ROM hash.
7. Only label `V11-LONG-TEST-CANDIDATE` after real evidence; `V11-FRIENDS-BETA` needs no known critical blockers and no silently omitted V10.2 requirements. Keep the release ledger showing **proposed / implemented / compiled / mGBA-tested / Delta-tested** separately.

**Visual previews are creative targets, not screenshots of playable V11.**
