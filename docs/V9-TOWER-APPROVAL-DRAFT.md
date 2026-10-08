# Pokémon Arena: Ascension — V9 Tower Approval Blueprint

**STATUS: AWAITING PLAYER APPROVAL. DESIGN ONLY. Do not initiate a V9 build or treat these features as implemented.**
Created following V8.2 iPhone feedback on confusing façades, weak boss scenery, identical battle-trainer sprites, move spam, and the missing item economy.

## Creative direction

V9 should feel like a polished Emerald-era fighting league. Preserve the original **Emerald Arena 0.13.0 native real-time combat**, animated sprite quality, and slightly smaller size-weighted Pokémon. Do not rebuild the engine, reintroduce the discarded V5 arcade system, or extend the city footprint further. Reuse/redesign the two current city districts, exterior tiles, walkable spaces, and selected original GBA art to make one coherent, lively city.

All nine competition venues (eight towers plus Champion Summit) have **one clear front door**, accurate exterior name/rank sign, distinct real-time-compatible themed fight grounds, trainer entry/choreography, a Master briefing, and a separate more dramatic **boss chamber**. No battles triggered by merely talking to an old guy at a counter. The Master exits the battle lane; the challenger comes in from the opposite end, stands on the opposing sideline, fights, delivers a quick exit line, and leaves before the next round. Tower Master congratulates the player, displays first-clear rewards in the Lab, and directs them to the next venue. Opponent world sprite, intro and battle sideline graphic must match.

## Eight towers for approval

| Rank & tower | Exterior & immediate neighborhood | Inside/regular trial battlefield | Distinct Leader chamber + arena | Distinct core skill | First-clear highlight prizes |
|---|---|---|---|---|---|
| **1 Bronze Trials** | Warm sandstone coliseum, training banners, coaches, weight/dodge dummies | Open stone training court, columns, breakable crates, clear sightlines | Monumental bronze-and-stone rotunda, medal banners, Regirock pedestal, heavier rocks | Timing, defense, using cover; accessible difficulty | **Regirock + Aggron** |
| **2 Gale Tower** | Windmill/sky-temple façades, windsocks, Flying Pokémon and aviator trainers | Open high terrace, wind direction indicators, clear railings | Cloud-top sky coliseum, dramatic gusts, Lugia arrival | Lateral dodging, distance control, wind | **Lugia + Dragonite** |
| **3 Verdant Crown** | Greenhouse/woodland lodge, flowers, rangers and grass Pokémon | Sun-dappled gardens, hedges, tall grass and moving leaves | Ancient tree-sanctuary chamber with giant roots and sunlight shafts | Cover, field control, grass pressure | **Suicune + Sceptile** |
| **4 Phantom Spire** | Haunted manor, iron gates, cemetery edge, mysterious townsfolk | Foggy graveyard with tombstones and ghostly wisps | Dark cathedral crypt with luminous spirits and Mewtwo reveal | Visibility, feints, precision, recovery windows | **Mewtwo + Gengar** |
| **5 Inferno Forge** | Smoky foundry/volcanic fortress, smithy NPCs, orange-lit windows | Basalt stone floors and telegraphed lava vents | Grand molten forge, lava rivers, glowing dais, Entei entrance | Committed attacks, heat zones, safe positioning | **Entei + Blaziken** |
| **6 Tidal Bastion** | Coastal fort/canal façade, waterwheel, fishermen and Water Pokémon | Shallow canals, wet stepping-stones, limited safe paths | Flooded sapphire amphitheater with cascading waterfalls | Conductive water, ice, positioning, attrition | **Kyogre + Swampert** |
| **7 Thunder Citadel** | Lightning-rod power tower, neon-blue electric signage, engineer NPCs | Stormy rooftop with telegraphed ground pulses | Electric generator chamber with dark storm sky and Zapdos lightning | Fast windows, conductivity, speed counterplay | **Zapdos + Metagross** |
| **8 Astral Apex** | Observatory, crystal spires and star-gazing NPCs | Crystal halls and changing cover, muted starlight | Celestial observatory arena under animated stars; Rayquaza descends | Multi-pattern AI, timing, changing terrain | **Rayquaza + Salamence** |

**Champion Summit (V10 full campaign):** Regal boulevard and championship palace, five successive Elite Four/Champion chambers, visible banners/spectators; Articuno, Registeel, Raikou, Regice and Ho-Oh as signature last Pokémon of each trainer. Each championship trainer has a themed six-Pokémon team. V9 should establish compatible venue architecture; V10 finishes the full five-round gauntlet, ceremony, and rematch systems.

### Tower paths and checkpoint rhythms (normal circuit)

| Tower | Floors | Trainer opponents/floor | Free healing after floor | Leader |
|---|---:|---|---|---|
| Bronze | 4 | 2 / 2 / 3 / 4 Pokémon | Full team restoration just before leader | Regirock last |
| Gale | 5 | 2–3, rising to 4–5 | Full recovery after floor 3 | Lugia last |
| Verdant | 5 | 3–4, boss 5 | Full recovery after floor 3 | Suicune last |
| Phantom | 6 | 3–4, boss 5 | Full recovery after floor 3 | Mewtwo last |
| Inferno | 6 | 3–5, boss 6 | Full recovery after floor 3 | Entei last |
| Tidal | 7 | 3–5, boss 6 | Full recovery after floor 4 | Kyogre last |
| Thunder | 8 | 4–6, boss 6 | Full recovery after floor 4 | Zapdos last |
| Astral | 9 | 4–6, boss 6 | Full recovery after floors 3 and 6 | Rayquaza last |

Floor counts are targets; adjust based on playtesting. One Pokémon active per side. Individual opponents must be trainer **teams**, not one wild Pokémon or six simultaneous enemies. HP/status persist across floor victories; PP refreshes between floors. No free heals after every single opponent. Full checkpoints restore HP, status and fainted Pokémon. Losses send player back to free city health services.

## Tournament economy — cash matters

- Earn Arena Money from each **completed trainer fight**, substantial bonuses for boss clears, medals and rematch streaks; balance income against recovery expenses.
- On battle defeat: **lose 10% of carried Arena Money, capped at ₽2,000, rounded down, never below ₽0**. No debt. Repeated retries have escalating opportunity cost but cannot cause a soft lock; practise and basic city heal/re-entry always free.
- The redesigned central **Battle Supply Shop** stocks **healing items and legal arena battle items only**, e.g. Potions/Super/Hyper, status cures, Revives, ethers and balanced battle-enhancers/held items. **No Poké Balls for sale**.
- Items usable during battles using Emerald Arena's actual START → Bag interface. The battle is paused while selecting; require a **1-item-per-opponent deployment** or similar tested cooldown/usage limiter to prevent heal-spamming, and preserve native party switching. Item effects must correctly persist HP/PP/status.
- Between floors, use the preparation room to change party order and access earned inventory; gauntlets limit restocking.
- No required paid tower-entry fees. Unclaimed unlocked Pokémon, medals, shinies and career progression are permanent after a loss. Cash and consumables are expendable.

## Championship healing and economy (V10, design agreed)

- Heal after **Elite II** and **Elite IV**, not between Elite I→II or Elite III→IV. Each recovery is a **full team heal**, including revives. In-battle items remain legal within balance limits.
- Lose a championship battle → start again from Elite I, **keep permanent earned recruitment licenses**, lose 10% of held currency (same cap), restore team for free back in Arena City. Cannot return to Lab or shop *during* an Elite Four run; buying consumables and configuring party happens before entry.
- Harder Masters Circuit: remixed opponents, harder AI, stricter consumable allowances and themed hazard patterns. One first-clear shiny license per Masters tower; Champion Masters rematches award further licenses under changing modifiers. Shinies are visual only.

## Central city without confusing house façades

**No additional city acreage in V9.** Replace generic middle Battle Frontier buildings with clearly readable, visually unique *real* Emerald-looking civic structures, with one logical doorway and prominent exterior signs:
- **Ascension Pokémon Research Lab** — signature large laboratory façade, interior scientists, PC, unlock list/selection, roster/move management, party ordering, full move compatibility indicators, nickname service.
- **Battle Supply Shop** — shop façade, bag stock, vending/counter, prices, winning money total; heals and battle items, NO Poké Balls.
- **Move Studio / Training Dojo** — move teaching, practice target, utility combo explanations, AI practice, EV and nature adjustments as optional services, not mandatory experience grinding.
- **Clothier / Trainer Style House** — trainer sprite/palette selection, battle poses if viable, non-stat cosmetics and shiny token desk.
- **Small homes** — optional NPC visits, local lore and useful hints, no unexplained doors routing to towers. A central plaza signboard points to tower ranks, and START → ARENA GUIDE still lists the next destination.

Remove NPCs overlapping walls/desks/roofs; inspect actual GBA collision/warp/event coordinates. Add Pokémon and people on real walkable sidewalks—no excessive sprite/object load; meaningful NPC theme and sign text. Scatter tower buildings around the two districts, visually themed; don't lump them in the center.

## Battle feel and latest Emerald Arena features

The pinned upstream v0.13.0 engine already contains attacks with different ranges, windups, cooldowns and art (89 native move profiles), weather/water/ice/electric elements, Protect versus Hyper Beam, Flamethrower clashes, interrupt/cancel on qualifying hits, Psychic props, status/PP, in-fight Bag and party menus and 187 animated species. **Retain that source; V9 must expose, vary, and test these capabilities, not invent a replacement renderer.**

- Build a machine-checked **four-supported-move loadout** for every recruitable species. Roster target **all 187 already animated Pokémon, no extra species or sprites**. Exact [80 + 64 + 25 + 18 complete roster allocation](ALL-187-CAREER-ROSTER.md). For unsupported combos, quarantine loadouts and show unmet QA in dev logs, never fall back silently.
- Fix repetitive projectile spam. Native AI currently heavily weights move power and effectiveness. Give trainers different tactics (rushdown, zoning, counterattack, healing/guard, environmental), incorporate distance, recent attack repetition, opponent behavior, current status and recovery. Track and check AI move selection across many simulated bouts.
- Fix identical combat-side opposing trainers: overworld changing sprite is not enough; native `gTrainerBattleOpponent_A` and resulting actual sideline renderer must change correspondingly. Match trainer names, sprites, entry choreography and battle pose.
- Stage trainers at opposite ends with Master stepping entirely out. When challenger loses, they say a brief themed line, leave, next walks on. Before boss: healing/pouch prep, physical transition to *separate* arena map, camera/palette/props that feel distinctly grander, boss speech and finale, clear first-clear reward announcement and next-tower guidance.
- Combine existing native move interactions with **actual stage geometry/props/palettes**, not just different map labels and text. Stage 1 trial arena and Stage 2 more dramatic boss environment for each tower, while monitoring memory.
- No universal 'cancel any attack' button claim. Native cancellation is conditional on move hit/interrupt; offensive moves still consume PP and cooldown. Avoid stealing player control with too many menus.

## V9 release acceptance gates (not just CI success)

1. Source memory check: existing V7 link used 99.81% of 32MB ROM and 99.18% EWRAM. Inventory unused original Emerald assets; reclaim headroom and measure frame pacing before adding new large graphics/AI allocations.
2. City center looks like a **proper Lab/shop/training complex**, exteriors match signs; no signs in wrong places, doors to towers where shops should be, blocked or trapped NPCs.
3. Each of eight towers has distinct approachable exterior, theme-specific entry hall, trainers staged at opposing ends, physical transition into visibly different trial battlefield and boss chamber.
4. Opponent sprite and identity match before AND during battle; challengers depart after loss and later challengers enter; no permanent "old man" blocking the lane.
5. Tower floors employ true multi-Pokémon trainer parties (at least 2–4 early, up to six late), correct enemy next-Pokémon sendout and player switching, all remaining in original Arena real-time mode.
6. Full native Bag healing and battle items function with stock purchased in central shop, pauses/PP/switch handling, currency income/loss and save persistence.
7. A range of representative 187-species movesets work: projectile, melee, rush, setup, guard, utility, held item/status, team switches, faint. No single high-power ball move dominates all AI.
8. Full heal cadence at designated checkpoints; for towers 5–8 full heal at one or two checkpoints. Leader's last Pokémon is its signature legendary.
9. The Lab actually allows selecting all **validated** starter/earned Pokémon with permanent reward state saved. No promises that animation alone implies all 187 instantly compatible; 187 selectable is acceptance goal.
10. Cold save/reload, loss and retry, map returns, reward claim, and Delta frame pacing regression tests. A compiled ROM alone is a test build, not release-complete.

## Implementation priorities

**Wave A (blockers):** Fix native trainer switch, identical sideline sprite, stable warp/choreography and AI move spam. Write tests/repro cases.
**Wave B (playability):** Real Lab and supplies shop, functioning in-combat Bag, win/loss economy + secure saves, consistent multi-Pokémon tower fights.
**Wave C (quality):** Native exterior/layout tile reuse, signage/streets/interiors, distinctive boss maps/backgrounds, thematic environment hazards and opponent behavior.
**Wave D (completion):** 187-species compatible moveset QA/unlock screens, eight towers end-to-end, performance tuning and on-phone regression.

Do NOT pretend that unverified V8.2 features or this V9 plan are already shipping. Approval of these eight tower identities should precede starting the gameplay implementation.
