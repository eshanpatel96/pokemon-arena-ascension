# Arena Ascension — Tower Aces and Pokémon Unlock Rewards

**Status:** Game design / roster validation, committed October 8, 2026. This file **does not implement reward unlocks**. V8.2 engine prototype focuses on trainer choreography and themed encounters. Recruitment, team editor, save flags and moveset validation belong to V9.

## Core concept

First-clear of each tower awards **TWO permanent recruit licenses** in the Ascension Pokémon Lab:

1. The Tower Master's **signature legendary Pokémon** (boss's final ace).
2. A **signature high-end companion** (a true pseudo-legendary when there is a suitable animated species; otherwise an elite starter or specialized nonlegendary).

Both become **selectable**, not free level-100 Pokémon dropped into the current party. Players can inspect stats, type, size, real-time move compatibility and recommended role before adding one to their team. Level normalization prevents rewards from trivializing subsequent tiers.

Why "companion" rather than "pseudo" for every tower: Gen 1–3 have only four fully evolved pseudo-legendary species: **Dragonite, Tyranitar, Salamence, Metagross**. Forcing a pseudo partner in every one of nine towers would repeat unlocks. Keep rewards type/theme-appropriate instead.

## Planned first-clear reward map

| # / Tower | Legendary Ace / first unlock | Elite partner / second unlock | Theme and implementation notes |
|---|---|---|---|
| **1 Bronze Trials** | **Regirock** | **Tyranitar** *(V9 real-time animation needed)* | Rock/Steel/Ground endurance; Regirock is already animated. **Temporary substitute Aggron** until Tyranitar has a compatible eight-direction spriteset, attacks and switching support |
| **2 Gale Tower** | **Lugia** | **Dragonite** (true pseudo) | Aerial movement, gusts, spacing and reliable Dragon/Flying pressure |
| **3 Verdant Crown** | **Suicune** | **Sceptile** (elite starter) | Forest guardian, sunlit gardens and tactical sustain; Suicune is Water-type, not Grass-type—environment is forest/streams |
| **4 Phantom Spire** | **Mewtwo** | **Gengar** (elite Ghost) | Psychic/ghost mind games, feints, teleport-like dodge patterns, mist |
| **5 Inferno Forge** | **Entei** | **Charizard** (elite starter) | Fire offense, careful timing, lava; matches original user-requested Entei + Charizard pair |
| **6 Tidal Bastion** | **Kyogre** | **Swampert** (elite starter) | Water, partial cover, electric conductivity/water hazards |
| **7 Thunder Citadel** | **Zapdos** | **Metagross** (true pseudo) | Lightning and conductive Steel; **Zapdos replaces Raikou as the first-clear legendary**; Raikou can remain a special rematch challenger |
| **8 Astral Apex** | **Rayquaza** | **Salamence** (true pseudo) | Dragon mastery, shifting star/crystal terrain and final elite preparation |
| **9 Champion Summit** | **Ho-Oh** | **Champion's Shiny Token** for one already-unlocked high-end companion, plus Champion cosmetics | A legendary finale and meaningful personalization instead of duplicating an earlier pseudo reward |

## Asset availability confirmed in Emerald Arena 0.13.0

Inspected `GBurgardt/pokemon-emerald-arena`, pinned commit `e1502f9`:
- Source asset list: `game/overlay/tools/arena/roster.json`; **187 animated species**.
- Existing native move profiles: `game/overlay/src/arena_moves.c` (89 unique move entries).
- **Animated now:** Regirock, Lugia, Suicune, Mewtwo, Entei, Kyogre, Zapdos, Rayquaza, Ho-Oh, Dragonite, Sceptile, Gengar, Charizard, Swampert, Metagross, Salamence, Aggron.
- **Not animated in upstream real-time roster:** Tyranitar. The normal Emerald species/front sprite is not enough for the eight-direction, multi-pose active Arena gameplay.
- New reward Pokémon must be validated individually for **four arena-compatible moves, PP, ability/status support, switching, death replacement and trainer AI** before their recruitment flag can be enabled. Existing sprite presence alone is not sufficient.

## Player fairness and roster progression

- Start with approximately **45–55 usable Pokémon** spanning Fire, Water, Grass, Flying, Electric, Ground, Rock, Steel, Ghost, Psychic, Fighting, Dark/other available types; player should not be forced into a predetermined six-mon team.
- Avoid including boss-specific rare Pokémon in the initial Lab pool. The tutorial/dojos can loan characters like Charizard while their **permanent career recruitment license** remains a later reward.
- Each tower's two rewards unlock on **first clear** and are catalogued in the Lab. Subsequent clears do not award endless legendary duplicates.
- Standardized competitive level bracket: initially Lv. 60, then capped promotion brackets per `V8-COMBAT-BALANCE-AND-TRAINING.md`. A higher raw level isn't the reward.
- Limits to avoid a Legendary-only steamroll: early **4-Pokémon teams can field at most one legendary**, later **6-Pokémon teams may field up to two**. Psuedos and elite starters are separate, but their weight and cooldowns create meaningful tradeoffs.
- **No real-money cost or required spendable credits** to recruit/field earned Pokémon. First-clear rewards are permanent even after a lost subsequent tower.
- Win/loss rematch opponent pools remain thematic; **leader's last Pokémon stays the same legendary** on every variant. Alter the first 2–5 Pokémon with different compatible strategies so a repeat attempt isn't identical.
- Rematch rewards: medals, credits, cosmetic finishes, rare shiny selection tokens, and practice boss records (no additional copies required).
- Shiny versions are cosmetic and should not raise stats.

## Native implementation requirements

1. Save state flags/mask for tower clears and independently awarded legendary and companion licenses.
2. Deterministic and version-safe migration/reset behavior across saved V8/V9 builds.
3. Pokémon Lab UI listing all recruitable species and locked rewards, with reason for lock and supported move loadouts.
4. First-clear dialogue announcing two new recruit licenses; the player visits Lab to assemble squad. Never inject reward into a full party without consent.
5. Boss team template ensures legendary is **last opponent in the full trainer team**, not a single wild legendary encounter.
6. Apply tier-specific level normalization and squad limit when entering a tower; no mandatory grind.
7. Two reward species must have animated combat assets, move/ability/PP compatibility, type balance and AI. The V9 Tyranitar sprite expansion must be verified before enabling its license.
8. Tests for first clear, return warp, save/reload, lost rematch, previous rewards retained, claimed roster, and no classic-battle fallback.
9. Status line in Lab distinguishes locked / unlocked / selected / temporarily loaned.
10. Follow original Emerald Arena engine and visuals; never swap to V5's replacement arcade renderer.

## Tower-boss legend consistency and future implementation

The experimental V8.2 encounter script currently uses **Raikou** for Thunder and **Mewtwo** again for the Summit. These are **NOT yet updated** to this reward plan. Before V9 ships:
- Thunder signature legendary changes to **Zapdos**. Keep Raikou available as a rare optional rematch.
- Champion Summit signature changes to **Ho-Oh** to avoid duplicate Mewtwo trophy.
- Bronze leader's final combatant is **Regirock**. Its companion Tyranitar requires a real-time animation expansion, with Aggron as the interim accessible reward.

**Do not claim any of these recruit licenses or the full legendary/pseudo reward system are implemented until the compiled ROM and actual Delta save/recruitment checks pass.**
