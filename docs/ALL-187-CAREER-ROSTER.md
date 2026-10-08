# Ascension — Complete 187 Animated Pokémon Career Roster (HYPOTHETICAL)

**Design discussion: October 8, 2026. Not implemented. Do not trigger a GBA build for this planning-only document.**

**Single upstream source of truth:** [Emerald Arena 0.13.0 animated roster](https://github.com/GBurgardt/pokemon-emerald-arena/blob/e1502f9f7ed46d969880d73adbf5ab23ef7b2a56/game/overlay/tools/arena/roster.json). Exactly **187 unique animated Pokémon** already exist. The GBA build also carries [89 native Arena move profiles](https://github.com/GBurgardt/pokemon-emerald-arena/blob/e1502f9f7ed46d969880d73adbf5ab23ef7b2a56/game/overlay/src/arena_moves.c). Sprite presence is NOT proof of native battle, move, status, switch or UI compatibility for an individual species.

## Allocation — EVERY NAME APPEARS EXACTLY ONCE

| Where recruit license is obtained | Unique Pokémon |
|---|---:|
| Available immediately at Arena Lab | **80** |
| First run, eight towers × eight species | **64** |
| Elite Four + World Champion, five × five | **25** |
| Masters Circuit exclusive species | **18** |
| **Total** | **187** |

No Groudon or Tyranitar in this 187: adding either would break the no-new-animation decision. Inferno returns to **Entei + Blaziken**; Bronze uses **Regirock + Aggron**.

## All 80 starter-available species

Immediately selectable via the Lab, with genuine four-move validated loadouts after V9 development. Lower evolutions are included as playable alternatives for challenge formats, not required as leveling grinds. Strong fully evolved Pokémon available on day one allow healthy type-counterplay.

**Kanto (43):** Bulbasaur, Ivysaur, Venusaur, Charmander, Charmeleon, Charizard, Squirtle, Wartortle, Blastoise, Butterfree, Beedrill, Arbok, Sandshrew, Clefable, Ninetales, Zubat, Golbat, Venomoth, Dugtrio, Persian, Golduck, Primeape, Arcanine, Poliwrath, Abra, Kadabra, Machop, Machoke, Victreebel, Tentacool, Tentacruel, Rapidash, Magnemite, Marowak, Koffing, Goldeen, Seaking, Staryu, Scyther, Magikarp, Lapras, Eevee, Flareon.

**Johto (4):** Bellossom, Marill, Azumarill, Slugma.

**Hoenn (33):** Poochyena, Mightyena, Zigzagoon, Linoone, Wurmple, Silcoon, Beautifly, Cascoon, Dustox, Lotad, Lombre, Ludicolo, Seedot, Nuzleaf, Shiftry, Shroomish, Breloom, Slakoth, Vigoroth, Whismur, Loudred, Exploud, Makuhita, Hariyama, Nosepass, Skitty, Delcatty, Meditite, Medicham, Gulpin, Swalot, Barboach, Whiscash.

## All eight towers — exactly 64 unlockable species

**Each first-clear Tower Master grants the signature legendary and partner;** the other six are earned across the tower's floor medals, practice mastery, an optional theme challenge, and the first victory. This avoids dumping eight unlocks in a single text box. A battle trainer's roster should be **70–80% made up of species locked until that tower clears**, with the rest consisting of Pokémon already available or lower evolutionary forms. Show some locked species early to create anticipation.

| Tower | Tower Master prize pair | Six other themed species | Count |
|---|---|---|---:|
| Bronze Trials | **Regirock + Aggron** | Aron, Lairon, Golem, Graveler, Geodude, Rhydon | 8 |
| Gale Tower | **Lugia + Dragonite** | Pidgeot, Taillow, Swellow, Wingull, Pelipper, Altaria | 8 |
| Verdant Crown | **Suicune + Sceptile** | Treecko, Grovyle, Roselia, Vileplume, Oddish, Gloom | 8 |
| Phantom Spire | **Mewtwo + Gengar** | Gastly, Haunter, Shuppet, Banette, Duskull, Dusclops | 8 |
| Inferno Forge | **Entei + Blaziken** | Torchic, Combusken, Torkoal, Numel, Camerupt, Magmar | 8 |
| Tidal Bastion | **Kyogre + Swampert** | Mudkip, Marshtomp, Kingdra, Milotic, Sealeo, Walrein | 8 |
| Thunder Citadel | **Zapdos + Metagross** | Pikachu, Raichu, Electrike, Manectric, Plusle, Minun | 8 |
| Astral Apex | **Rayquaza + Salamence** | Shelgon, Flygon, Trapinch, Gardevoir, Kirlia, Ralts | 8 |

**Tower floor example (Bronze):** Floor 1 might field Geodude → Aron, Floor 2 Graveler → Lairon → Rhydon, Floor 3 Golem/Aggron/varied earlier opponents, and the leader runs a stronger coordinated trainer team with **Regirock last**. Rematches substitute different Rock/Steel opponents and behavior archetypes; leader's signature legendary stays fixed. Player can bring Water/Fighting/Grass counters available from the beginning. No same-shot spam or unexplained HP spikes.

## Elite Four + Champion — 25 unlocks

| Battle | First-clear signature legendary | Four other roster unlocks | Count |
|---|---|---|---:|
| Elite I — Arctic Tempest | **Articuno** | Glalie, Spheal, Dewgong, Cloyster | 5 |
| Elite II — Iron Architect | **Registeel** | Skarmory, Scizor, Magneton, Armaldo | 5 |
| Elite III — Lightning Sovereign | **Raikou** | Electabuzz, Ninjask, Sandslash, Crobat | 5 |
| Elite IV — Crystal Oracle | **Regice** | Alakazam, Jynx, Slowbro, Claydol | 5 |
| World Champion | **Ho-Oh** | Slaking, Absol, Gyarados, Machamp | 5 |

Each Elite Four battle has a **six-Pokémon opposing trainer team** of stronger AI, while the five recruit licenses are rewards spread over Elite victories/challenges; remaining opponent-team slots can reuse owned or previously encountered Pokémon. Only **one mandatory legendary unlock per Elite** is awarded automatically on the first victory; earning the other four involves optional feats, rematches and medals. The final Champion awards Ho-Oh and the first shiny token. Ho-Oh stays the Champion's last Pokémon.

## Masters Circuit — all 18 remaining species

Shedinja, Nincada, Wailord, Wailmer, Sharpedo, Carvanha, Cacturne, Cradily, Solrock, Crawdaunt, Corphish, Nidoking, Nidoqueen, Exeggutor, Kecleon, Sableye, Kingler, Starmie.

Masters license examples: rare dual-form Shedinja/Nincada trial, Sharpedo/Wailord water gauntlets, Nidoqueen/Nidoking no-heal challenge, Exeggutor/Victreebel coverage gauntlet (Victreebel is already selectable at start), Sableye ghost duel, and Kingler/Starmie speed endurance. **Each Masters first-clear tower also awards one Shiny License**, usable on any species already recruited. Champion rematches can award additional shiny licenses under increasingly difficult modifiers, not by farming one easy opponent.

## Gameplay and power curve

- **Normal Circuit**: arena test starts Lv. 60; level brackets rise with promotion. No mandatory XP grinding; tower bosses field 4–6 real-time-validated Pokémon and show different attack/evasion/cover AI patterns. One active Pokémon per side. Legendary sits last on boss team.
- **Masters Circuit**: opponent rosters remix species across towers, restricted healing and advanced AI increase difficulty; boss legendary stays its signature but may use new compatible move sets and timing patterns. A second circuit is not 55 identical fights with inflated levels.
- **Trainer identity**: overworld sprite, intro and sideline arena sprite must match and correspond to a true native trainer ID; distinct neutral and leader battle poses on opposite ends. Defeated trainer exits, next arrives; Master steps out of the lane.
- **Movesets**: automatically generate a compatibility report for each of 187 species. Need four real-time-supported move profiles per Pokémon, reasonably varied power/range/recovery/status, a native AI selection policy balancing range, preferred attack archetype, recency and target conditions. Don't choose the same strongest 'ball' projectile indefinitely. Expose tests for PP depletion, status, switching, faint and battle fallback.
- **Evolution lock rules**: an unlocked base species must NOT evolve past a *locked recruitment reward* without first obtaining its license; otherwise the reward system is bypassed. Competitive levels normalized; allow deliberate 'little cup' variants for lower forms without grinding.
- **Rewards**: unlock species license, not auto-insert into a full party. All reward unlocks permanent, claimable in Lab; one legendary per early squad and two later, subject to playtesting. One Shiny License changes one Pokémon's palette cosmetically, not its stats.
- **Performance**: source GBA link is near 32MB ROM and 256KB EWRAM limits. Since these 187 sprites already exist in source, no new sprite assets are implied by this plan; **activating all of them still requires memory, sprite-buffer, save-schema and UI profiling**, plus four-move validation. Don't claim 187 playable simply because compiled.

## Changes from prior 60-species plan

This document is a **provisional successor** to `TOWER-ACES-AND-REWARDS.md` and the 60-species partition. **187 exactly**, no additional Pokémon or recreations. Groudon/Tyranitar are excluded from this version; Entei and Aggron are valid native replacements. 13 existing animated legendary species (Regirock, Lugia, Suicune, Mewtwo, Entei, Kyogre, Zapdos, Rayquaza, Articuno, Registeel, Raikou, Regice, Ho-Oh) are all used as unique boss reward aces. All 13 are reserved from the initial 80.

**Acceptance gate before implementing V9:** obtain user approval for the allocation, verify all 187 are valid in original real-time engine with a compatibility matrix, and preserve existing V8 stable functionality. A source commit or successful GitHub compile is not a substitute for Delta testing.
