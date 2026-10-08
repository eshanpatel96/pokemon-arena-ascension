# Emerald Arena Feature Audit — Ascension V9

**Verified:** 2026-10-08. **Upstream pin in our Actions:** `GBurgardt/pokemon-emerald-arena` @ `e1502f9f7ed46d969880d73adbf5ab23ef7b2a56`, the **latest published release v0.13.0** as checked against the upstream releases and current main commit. V8.2 is built from upstream's **original native Emerald Arena engine** plus our scripts/patches, not a rewritten renderer.

Sources:
- [Official v0.13.0 release](https://github.com/GBurgardt/pokemon-emerald-arena/releases/tag/v0.13.0)
- [Upstream PLAY.md](https://github.com/GBurgardt/pokemon-emerald-arena/blob/e1502f9/PLAY.md)
- [Original real-time C battle engine](https://github.com/GBurgardt/pokemon-emerald-arena/blob/e1502f9/game/overlay/src/realtime_arena.c)
- [All 89 move profiles](https://github.com/GBurgardt/pokemon-emerald-arena/blob/e1502f9/game/overlay/src/arena_moves.c)
- [Opposing Flamethrower clash](https://github.com/GBurgardt/pokemon-emerald-arena/blob/e1502f9/game/overlay/src/arena_flame_clash.inc)
- [Protect/Hyper Beam interaction](https://github.com/GBurgardt/pokemon-emerald-arena/blob/e1502f9/game/overlay/src/arena_guard.inc)
- [Water/ice/electric environment code](https://github.com/GBurgardt/pokemon-emerald-arena/blob/e1502f9/game/overlay/src/arena_elements.inc)

## Already inherited from upstream source

1. **187 animated species** and 89 adapted real-time move profiles. Caveat: this is NOT proof every species is safe with four useful native moves, status effects, replacement or held items.
2. **Native movement, A attack, L/R move-select, B + direction dodge, manual aiming; hit windows and shared action recovery**. Simply switching the selected move does not cancel an already committed attack. V9 can introduce new counterplay, but must prevent free cooldown skips.
3. **Attack interrupts:** Certain secondary effects cancel a pending wind-up and impose recovery (not a refund of a committed hit). No universal free-cancel button exists upstream. **Flamethrower vs Flamethrower** triggers a dedicated clash, and **Protect vs Hyper Beam** absorbs/stops the beam rather than reflecting it.
4. **Distinct move identities and special mechanics:** Dig, Fly, Teleport, Seismic Toss with impact/crater, Rollout with increasing damage and destructible cover, Double Team decoys, Substitute cover, Smokescreen line-of-sight interruption, Reflect/Light Screen, Psychic rock throws, Bide, Struggle, Hyper Beam, Solar Beam, Hydropump, Aeroblast, Sacred Fire, and varied Rush/Melee/Cone/Projectile/Self archetypes.
5. **Breakable objects and environments:** original forest/coast/cave/desert/indoor stages and further community arena stages. Water attacks leave wet cells, ice freezes them and creates slip hazards, electric attacks can conduct through wet connected surfaces, fire melts ice; Rain Dance generates temporary storm/flooding. Ghost types phase through boundaries and solid terrain (some attacks still meet cover).
6. **Trainer battle support and sidelines:** compatible 1v1 trainer fights can retain original real-time renderer, and trainer sprites are rendered at opposite ends. Opponent appearance comes from `gTrainers[gTrainerBattleOpponent_A].trainerPic` by `OpponentGraphics()`, not the overworld sprite alone.
7. **Battle pause/party/Bag:** START menu includes POKÉMON, BAG, MOVES, RESUME; native Bag/party transitions already exist. Native menu integration does NOT prove every in-battle item effect works on our custom career floors without losing AI state or active effects.
8. **Persistence:** HP/PP, some status effects, exp, native save/PC, switching and extra v0.13 fixes. Doubles, link and unsupported move/ability/held item cases still fall back to classic combat.

## Important Ascension gaps, not missing upstream releases

- **Stale trainer appearance:** Our Bronze setup fixes `gTrainerBattleOpponent_A=TRAINER_BRAWLY_1`, so changing the overworld's trainer graphics does NOT change the sideline battle opponent. V9 must synchronize actual native trainer identity and graphics per challenger, with both trainers positioned correctly and unique boss identities.
- **Move spam:** Upstream AI's `AiChooseMove()` picks the highest score, heavily weighting power/type effectiveness, distance and a small random component. Strong ranged attacks can dominate repeatedly even where four moves exist. V9 needs role-driven AI, time-since-last-used penalty, cooldown and setup tactics, player-distance/cover awareness, and per-species loadout validation, while maintaining fair type matchups. Identify the exact "ball attack" via move telemetry before tuning it.
- **Themed arenas:** Upstream supplies community palettes and multiple stages. Ascension V8.2 map-based stage assignments are preliminary art reuse, NOT genuinely unique grass/ghost/fire boss environments with props/hazards/telegraphed mechanics. V9 needs real per-tower stage and environment integration; test actual effects for each floor and final boss, including asset/VRAM costs.
- **Attack-cancel design:** Native interrupt / clash behavior exists, but an unrestricted attack- or dodge-cancel combo mechanic is NOT included. Any added cancel system should have explicit limited windows, commitment cost and equal AI/player fairness. Avoid silently changing original Emerald Arena mechanics.
- **187 species:** sprites already present, not all fielded or recruitable in Ascension yet. V9 needs a real team-selection Lab, compatibility matrix and saved reward unlocks. [187 career roster](ALL-187-CAREER-ROSTER.md) is hypothetical.
- **Items/shop:** an **Arena-only Supply Shop** must filter out Poké Balls, offer useful healing, status, revives and battle items, award prize money from battles, and make Bag use in real-time fights safe and consumptive. Not completed by merely having native PokéMart and Bag menus.
- **Full heals:** approved design now calls for *full* recovery checkpoints in Towers 5–8 and *automatic full party heals after each Elite Four victory*, plus usable healing/battle items **during real-time fights**; supersedes any older partial-heal/one-charge gauntlet proposals.

## V9 acceptance tests

1. Scripted two-Pokémon native trainer fight → second enemy switches in real-time; opponent sideline graphics match entering trainer.
2. Four **different valid moves** per selected Pokémon, appropriate range/power/status and no unsupported-move fallbacks.
3. Same opponent fights under at least three measurable AI archetypes (ranged, pressure, defense); not repeatedly launching only its top-score projectile without reasonable tactical motivation.
4. Protect blocks Hyper Beam; opposing Flamethrowers clash; a confirmed interrupt cancels a wind-up but does not refund already released damage; blocked shot/PP/cooldown consistent.
5. Flying/Dig/Teleport/Rollout/Seismic Toss/Double Team/Substitute/Smokescreen interact correctly with terrain and environment.
6. Water, ice, electric, fire, rain and conductive/flooded surfaces render and resolve one native hit per move; no duplicate damage.
7. START > BAG consumes supported healing and battle items during real-time fights and returns with HP/status/PP, cooldowns, weather, guard and AI state intact. Shop sells **no Poké Balls**.
8. Full heal after each Elite Four victory, trophy preserved after a subsequent loss, but run resets to Elite I.
9. Save/quit/reload; memory budget and performance on Delta; no claims of completion based on CI compile alone.

**No rebuild required just to document features.** 
