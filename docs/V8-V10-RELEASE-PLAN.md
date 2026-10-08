# Pokémon Arena: Ascension — V8–V10 Release Plan

**Product target:** By V10, a near-complete, original-Emerald-Arena-based GBA game playable in Delta on iPhone. Eight distinct towers, a five-fight Champion Summit, a functional city, roster and trainer customization, lasting progression, and repeatable endgame. **No replacement arcade combat engine.**

**Baseline:** V7 compiled on GitHub Actions (run `37792959292`), but the expanded world requires a full Delta playthrough test. The source creates two connected districts, distinct tower lobbies and return destinations, rank gates, and rotating dojo trainers. **It does not yet contain themed trial/boss battlefields or the full career.**

## Non-negotiable design principles

1. Preserve Emerald Arena's original real-time battle engine, original animated Pokémon and high-quality Emerald art.
2. Real city streets, interiors and gates—not "talk to a woman" to teleport directly to every identical fight.
3. Every tower offers an Arena Master briefing, a dedicated approach/interior, a themed trial battlefield and a more spectacular boss battlefield.
4. Damage persists between floors; healing cadence is part of the challenge. No mandatory real-money spending and no way to run out of credits needed to continue playing.
5. New Pokémon are playable only if sprites, moves, switching, PP and AI are validated in original real-time combat.
6. Phone-safe controls: D-pad movement, L/R move selection, A attack, B dodge, in-arena switching; no forced regression into Emerald's old turn-based battle menu.
7. Save/load, dialogue, return warps, boss defeats and game-over flow are release blockers, not polish items.

## Hard engineering constraint (verified in V7 link map)

- ROM: **33,491,580 / 33,554,432 bytes** used (**99.81%**) on the 32 MB GBA cartridge image.
- EWRAM: **259,988 / 262,144 bytes** used (**99.18%**).
- IWRAM: **30,892 / 32,768 bytes** used (**94.27%**).
- The current numbers are **link-time region use**, not a comprehensive peak-runtime memory profile. We must profile runtime memory and worst-case battle performance separately.

**V8 blocker:** inventory ROM and RAM; reclaim capacity from unused Emerald story assets, redundant generated graphics and/or compressed/shared tile and palette assets *without breaking the original battle engine*. Record memory totals for every CI build, and gate content growth on headroom and Delta tests. Reuse authentic art and palette/weather/hazard variations; do not promise 18 huge independent animated arena sets when 32 MB is almost full. Prefer a practical target of approximately 2 MB ROM and 8 KB EWRAM reserve before investing heavily in bespoke graphics, then revisit based on actual asset budgets.

## V8 — WORLD & VERTICAL SLICE (native Emerald city + one complete tower)

**Release goal:** V8 feels like a new game *around* the proven original combat.

### Core features
- Verify V7 two-district walkability, collision, location/map transitions and tower exits on real Delta. Fix unreachable doors and wrong warp return coordinates.
- Make Arena City's essential buildings functional with existing Emerald interfaces: Pokémon Lab (party management), Move Studio (limited arena-supported skill teaching), healing and practice dojo, equipment/items desk, trainer customization preview.
- Create distinct façades/entrances/interiors, one Arena Master with tower-specific guidance, and an actual door/gate inside the tower leading to its arena.
- Complete **Bronze Trials** as the production template: four unique floor encounters, a boss, differentiated trial/boss battlefield atmosphere using original art, victory/failure/exit/retry screens, and one clearly signposted recovery checkpoint.
- No NPC-triggered fight until player deliberately enters the arena gate or selects a clear start prompt.
- Implement reliable **persistent** tower, unlock and checkpoint save variables; ensure a saved party and progress are not corrupted on cold restart.
- Basic credits earned through fights and replayable dojo; free essential healing and re-entry so no softlock.
- Dojo fights rotate among at least six curated fully real-time-compatible opponents, with repeat attempts not always the same Pokémon.
- Address confirmed fallback causes (unsupported move effects, fainting, PP exhaustion) and test in-arena party switching without damaging original combat.

### V8 acceptance gate
Fresh Delta career → free roam western/eastern city → access Pokémon Lab → prepare team → enter Bronze building → speak to master → cross physical battle gate → clear four encounters with a recovery checkpoint → defeat boss → earn credit/unlock → exit to correct street → save → cold reload → progress persists. No corruption, gibberish text, surprise classic battle screen or stuck tile. V8 is not accepted by compilation alone.

## V9 — COMBAT DEPTH, ROSTER & THEMED TOWERS

**Release goal:** Variety, meaningful team-building and reasons to train rather than a repetitive opponent ladder.

### Core features
- Extend Bronze's working flow to **all eight towers**, each with a real unique approach/interior, leader personality, unlocks, reward and opponent archetypes.
- Implement **two visually distinct arena phases per tower** using shared graphics and theme overlays/effects: trial phase and leader/boss phase. These should be genuinely different in gameplay, not just a text label.
- Theme mechanics: Gale gusts; Verdant cover/sun; Phantom fog/tombstones; Inferno timed lava vents; Tidal shallows/water conductivity; Thunder telegraphed pulses; Astral shifting cover; Bronze dodge fundamentals. Every environmental hazard must be clearly telegraphed and counterable.
- Build reusable native floor/challenge templates (aggressive pursuit, ranged pressure, endurance, environmental control, boss patterns), escalating AI without unfair stat inflation or unimplemented 2v1.
- Replace the fixed six-Pokémon demo experience with **roster selection and unlocks**. Planning target **40–60 curated playable Pokémon** from the existing animated roster, released in batches and confirmed with four supported attacks each; not a promise to implement all 386/1000+.
- Squad grows from **4 Pokémon in early towers to 6 later**, balanced by tower difficulty, with sensible no-heal checkpoints.
- Pokémon Lab: team slots, party ordering, type, movement speed/weight, move loadouts, status, item effects, and supported move compatibility warnings.
- Original-engine L/R → A four-move selection plus **independent per-move cooldowns**; design around handheld button count and clearly visible small HUD.
- Add challenge-grade healing cadence (full/partial/none at designed checkpoints), battle credits, meaningful items, skill trainers, and opponent-team variation.
- Preliminary trainer sprite/palette variants and shiny reward pipeline only after memory profiling.

### V9 acceptance gate
All eight distinct tower flows enter original real-time combat, vary themes, maintain HP/recovery rules, allow a curated multi-Pokémon team with move customization, and save/restore progress. All supported roster Pokémon pass sprite, switching, PP, faint and move test matrices.

## V10 — NEAR-COMPLETE CAREER & POSTGAME

**Release goal:** A credible complete playable campaign, not an early prototype. Target **approximately 90% of the intended core experience**, with subsequent V10.x reserved for remaining art, balance, rare fixes and ambitious extras.

### The full career
| Tier | Floors | Theme | Recovery guidance |
|---|---:|---|---|
| 1 Bronze Trials | 4 | Stone practice → ceremonial ring | Full recovery around floor 2 |
| 2 Gale Tower | 5 | Windy terrace → sky arena | Checkpoint after floor 3 |
| 3 Verdant Crown | 5 | Sunlit garden → giant-tree sanctuary | Partial recovery after floor 3 |
| 4 Phantom Spire | 6 | Misty tombstones → haunted crypt | One limited checkpoint |
| 5 Inferno Forge | 6 | Volcanic track → molten forge | One partial-heal checkpoint |
| 6 Tidal Bastion | 7 | Coastal shallows → flooded amphitheater | One checkpoint after floor 4 |
| 7 Thunder Citadel | 8 | Storm rooftop → lightning chamber | One checkpoint after floor 4 |
| 8 Astral Apex | 9 | Crystal observatory → stellar ring | Two small partial checkpoints |
| Champion Summit | 5 | Regal hall → gold championship arena | One limited recovery before final |

**Total 55 floors/fights**, plus city practice, trials, optional rematches and endgame. Floor counts and recovery are *design targets*, to revise during playtesting. Every tower boss should be memorable mechanically and visually. No 2v1 unless original engine support and collision/AI tests are proven.

### Completeness features
- Finishing story, formal Champion rank, satisfying ending/ceremony, victory/records screen.
- Persistent completion medals, tower leader rematches, ranking challenges, no-heal/timed modifiers, replayable post-Champion gauntlet, dojo rotation.
- Functional Pokémon Lab, Move Studio, item shop, practice dojo, and trainer customization **using GBA-native sprite/palette options**.
- Expanded unlock progression, optional shiny palette variants with no competitive stat advantage.
- **Mega Evolution** is a high-priority stretch system but contingent on memory/graphics/time: ideally a limited number of supported Mega forms and a one-per-team combat-earned meter; if this threatens V10 stability, ship an in-engine "Ascension Burst" temporary powered state with existing sprites and graduate full Mega art/forms to V10.x. Do not mislabel Burst as implemented Mega.
- Multiple team styles and viable attack/move options; boss difficulty arises from AI/terrain/composition rather than endless levels.
- Accessible help screens; no unavoidable cutscenes, dialogue corruption, surprise fallbacks or softlocked saves.

### V10 acceptance gate
On Delta: brand-new career → optional tutorial → build a team → enter every tower and progress 55-floor career with correct difficulty, healing and bosses → win Champion Summit → save/reload → return to city and access rematches/endgame. Test *all* exits and defeated-team transitions, including Blastoise, PP depletion and status effects. Re-run all build/ROM header, map, battle navigation and move-compatibility checks plus performance and save regression tests.

## Three-release scope discipline
| Category | V8 | V9 | V10 |
|---|---|---|---|
| City | Core facilities, real gate | Fully populated facilities | Final NPCs, polish and events |
| Towers | Bronze full template; other unique lobbies | 8 themed flows and two arena phases | All 55 floor encounters + Champion |
| Pokémon | Stabilize team and compatibility | 40–60 curated playable | Balance, unlocks, shinies and rewards |
| Combat | Fix fallback and persist HP | Four native cooldowns, expanded AI/hazards | Boss phases, final balance, optional Mega |
| Progression | Save and checkpoint | Rank, rewards, economy | Ending, medals, postgame |
| QA | Full Bronze Delta playthrough | All 8 tower regression | Full career + reload + postgame |

## Build/resource management
- Keep everything in private GitHub with reproducible pinned builds.
- **Cache compiler/build dependencies** and cancel superseded CI runs; batch changes rather than burning GitHub Actions minutes on every tiny edit.
- Save an artifact and crash logs for each numbered release. Distinguish "source changed" vs "CI compiled" vs "emulator tested."
- Do not upload copyrighted original Emerald ROMs to the repository. Never promote a build based only on GBA header validation.
- After each release, prioritize reported Delta regressions before starting the next feature wave.

## Explicit exclusions before V10
- 1,000+ Pokédex support; fully voiced cutscenes; online multiplayer; arbitrary 2v1; building an entirely new real-time combat renderer; photorealistic/art-off-style city; guaranteed full Mega Dex.

**Definition of 'near complete':** A new player can enjoy a rich offline campaign from the Ascension City arrival through every tower and champion to a repeatable endgame, without encountering unfinished placeholders in critical flow. Extra generations and artistic flourishes can continue after V10.
