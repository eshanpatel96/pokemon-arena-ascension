# Pokémon Arena: Ascension — V9 Design Sign-off (DRAFT)

**Status: DESIGN FOR USER APPROVAL — NOT IMPLEMENTED.** Created after the V8.2 playtest and continuing the V9/V10 scope discussion. Once the tower architecture is approved, implementation can be batched into playable GitHub GBA/Delta builds. Preserve upstream Emerald Arena **v0.13.0**, pinned commit `e1502f9`; **do not resurrect the V5 replacement battle renderer**.

## Release goal
**V9 = complete competitive Arena City, all eight playable and strongly differentiated towers, meaningful native Trainer-vs-Trainer battles, full 187-sprite Pokémon recruitment/selection plan, varied moves/AI, a working recovery-and-money economy.** V10 = the five-trainer Elite Four + World Champion gauntlet, Masters Circuit, Shiny Licenses, endgame balance and full-campaign QA. V9's code, art, ROM headroom and on-device tests must be evaluated incrementally; source design does not equal shipped gameplay.

### Non-negotiable test failures from V8/V8.2
1. There are **too many doors**, old people behind desks/furniture, confusing entrances; a player sometimes cannot reach an arena battle.
2. Opposing **battle trainer sprite stays the same** even when overworld challenger gfx changes. Original native code resolves in-arena opponent gfx from `gTrainers[gTrainerBattleOpponent_A].trainerPic`; currently Bronze assigns Brawly.
3. Strong projectiles / “ball move” get repeatedly selected because original `AiChooseMove` prioritizes power × type effectiveness; strategic AI and four genuinely distinct usable moves needed.
4. Bronze boss room may be a different overworld room but still **looks bad or generic in actual fight**. Need genuine battlefield change and cinematic introduction, not just different dialog or a map palette.
5. Central generic Frontier houses do not look like a specialized lab and services are partially broken; NPCs sometimes overlap structures.
6. V8.2 trainer switches, defeat returns, save/reload, arena eligibility and tutorial must be revalidated on actual Delta. Compiler pass alone is insufficient.

## City plan — same two districts, substantially better use of their footprint
- **No further geographical expansion** by default. Preserve connected West/East Frontier map architecture and quality but **redesign the middle**.
- West-center: **Ascension Pokémon Lab** as visually recognizable research-facility building (not a reskinned generic house), practical selection/storage terminals, team roster and reward claims; **Arena Supplies shop** (separate visible shop façade, not a PokéMart clone); **Move Studio**; **Training and Nature/EV specialist**; **Name Rater**; **Wardrobe**. Consolidate services into a hub with clear signs rather than lots of anonymous doors.
- Use authentic Emerald tiles and animation sprites, reuse tilesets/palettes/shared native assets to stay under 32 MiB; update the *actual building exterior tiles*, not just the interior or sign event.
- Other residences contain themed trainers / townspeople with meaningful hints, short sparring or quests. No duplicate fake tower warps.
- Keep **four towers West, four East, Summit east/north**. Disperse them aesthetically among neighborhoods with tower-relevant statues, vegetation/weather colors/NPC outfits and local Pokémon wanderers; paths connect visibly. Keep the single obvious front entrance per venue and exact exit return.
- START **ARENA GUIDE** lists ordered towers 1–8 + Summit, name, district, locked/unlocked/cleared, next objective and route hints; every door has a **functional adjacent sign**, matching real warp; tower clearance can be rechecked.
- NPC collisions: verify placement on walkable, unoccupied native metatiles in maps, visually inspect all exterior/interior tiles in an emulator, prevent doorway/warp overlap. Don't label decorative non-interactable floor tiles as working signs.

## Eight tower identities (TWO actual battle environments each)

| # | Tower | Exterior and entry room | Trial arena | Leader/boss arena | Native combat identity | First-clear signature |
|---|---|---|---|---|---|---|
| 1 | **Bronze Trials** | Carved-rock guild, banners, stone challenge foyer | Compact quarry ring with pillars and breakable stone props | Monumental **Regirock coliseum** with carved ancient seals, statues and a large ceremonial battlefield | Spacing, dodge timing, heavy strikes, stone cover | **Regirock + Aggron** |
| 2 | **Gale Tower** | Windmill/high-tower façade, flying banners, feather and bird NPCs | Open sky terraces with gust telegraphs and small obstacles | Stormlit open-air sky ring with striking cloud/parallax background | Fast aerial pressure and lateral evasion, ranged gusts | **Lugia + Dragonite** |
| 3 | **Verdant Crown** | Vines, overgrown architecture, gardeners and roaming forest Pokémon | Grass/canopy ring with sunlight patches and movable cover | Ancient-tree sanctuary with roots, beams of light and petal effects | Grass cover, healing, positioning, terrain control | **Suicune + Sceptile** |
| 4 | **Phantom Spire** | Gothic chapel/manor, graveyard fence, tombstones and ghost NPCs | Graveyard with fog, graves and directional visibility breaks | Spectral crypt with ghost wisps, deeper fog and active illusion/prop effects | Feints, defensive spacing, Shadow/Psychic mind-games | **Mewtwo + Gengar** |
| 5 | **Inferno Forge** | Blackstone volcano/forge, embers and fire workers | Heated foundry ring, timed lava vents, safe floor routes | Imposing molten furnace with lava channels and active fire/Flamethrower clashes | Commitment windows, heat hazards, fire pressure | **Entei + Blaziken** |
| 6 | **Tidal Bastion** | Seaside citadel, bridges, docks and water NPCs | Shallow pool arena and cover islands | Flooded amphitheater with rain, waterfalls and changing water levels | Water/ice/electric conduction, stamina | **Kyogre + Swampert** |
| 7 | **Thunder Citadel** | Metal coil tower, generators, thunder signs, engineers | Electrical rooftop, conductive rails and charge zones | Lightning reactor with timed strikes and dramatic charge pulses | Speed, guard timing, move interruption and electric conduction | **Zapdos + Metagross** |
| 8 | **Astral Apex** | Observatory, star domes, crystal gardens, psychic NPCs | Crystal-platform arena, shifting cover and psychic props | Celestial observatory with floating rocks, space sky and complex timing | Predictive AI, Psychic prop interactions and precision | **Rayquaza + Salamence** |

**No claim these venues' new art is already in V8.** Reuse/composite native Emerald graphics with shared GBA tilesets and the original Arena stage/biome pipeline; add unique lightweight tile overlays, palettes, particles and actual collision/hazard behaviors. Performance and ROM/RAM budgeting are release gates. Different boss rooms must be recognizable *during real-time combat*, not only in the overworld.

## Mandatory tournament choreography for EVERY tower
**Street → one entrance → compact themed foyer → Arena Master explains round, remaining enemies, healing and hazards → Master steps off field/disappears → player automatically walks into arena → opponent TRAINER enters at far end and stands opposite player → real-time trainer-party battle, 2–6 Pokémon one active at a time → defeated trainer speaks and walks away → next trainer enters or Master reappears with advertised recovery checkpoint → boss warning and separate theme-rich Leader arena → full boss trainer team (legendary as final send-out) → Leader congratulates and explains Lab Pokémon unlocks, prize money and next tower → exit to correct town entrance.**

- Do not trigger fights from an unreachable hidden doorway.
- **In-battle** trainer sprite, intro identity and overworld sprite must correspond; do not pin everyone to Brawly.
- Avoid accidentally resetting career variables, skipping the next trainer, or healing after every KO. HP/status carry across trainer fights. PP may refresh between trainer floors as explicit design.
- V8 Bronze pre-boss paths must be repaired before extending all towers.
- Each tower has varied species/moves/AI among attempts; on loss rematch lineup changes while final legendary stays fixed.
- Tower enemy teams **2–6 Pokémon**. Make the boss harder by AI, terrain and complementary team composition rather than vast level gaps.

## Full Pokémon availability — original 187 ONLY
Adopt `docs/ALL-187-CAREER-ROSTER.md` as the authoritative **provisional distribution: 80 available initially + 64 tower unlocks (8/tower) + 25 Elite/Champion + 18 Masters exclusives**. Every species appears exactly once and is in original `tools/arena/roster.json`. Do NOT create Tyranitar, Groudon, etc., unless a separately approved later expansion; existing licensed ace/companion pairs are in table above. The first normal clear grants legendary + elite directly to Lab as permanent selectable licenses; the other six tower-pool species come from floors/medals/small optional challenges. Evolution must not bypass locked species. V9 milestone must test four supported, role-diverse real-time moves and all switching/PP/faint paths for each claimed playable species; **187 sprite animations ≠ 187 currently battle-safe selectable monsters**.

## Native combat upgrades (preserve Emerald Arena 0.13.0)
- Audit the original **89** supported move profiles for range, damage, windup, hit shape, cooldown, status/effect, particles and compatibility. Build an automatic species × four-move × ability/PP compatibility report.
- **Anti-spam AI:** move recency penalties, type/range/line-of-sight consideration, status setup opportunities, dodge/interruption windows, safe cover and style-specific weighting. Five archetypes: rushdown, sniper/zoner, defender, bait-and-counter, balanced. Distinct early-tier readable patterns, better leader behavior.
- Trainer sides should be at **opposite edges** of the existing battle field. Animation should match named trainer; no cloned trainers at side.
- Use already-implemented native mechanics: interrupt before windup release, Protect vs Hyper Beam, colliding Flamethrowers, rain/flood/conductivity, frozen water, Psychic rocks, Dig/Fly/Teleport/Rollout/Seismic Toss/Double Team. Arena effects must be visible/telegraphed and truly affect strategy.
- Only make **four native move slots** selectable using L/R, A attack, B+d-pad dodge, START in-battle menu; preserve existing effects/PP and no exploit from item/menu pause. Full independent per-slot cooldowns are proposed but must be engine-tested, not casually claimed implemented.

## Economy and healing — money matters
- Use a single native money balance (label **Arena Credits** in city UI if possible; avoid parallel unsynced currencies). Defeating floor trainers yields credits, leaders higher bonuses, no mandatory fee.
- **Loss penalty proposed: 10% of CURRENT carried credits, capped at 1,000**, deducted once when the tower/Championship attempt fails. Zero credits cannot go negative or softlock the player; minimum free practice, tower entry and city healing always available. Economy values are starting balance targets, not implemented prices.
- Example early balance: start 2,000; normal floor victory +300–600; boss victory +1,500–3,000 (scaled by tier); later rewards larger. Ensure expected average run winnings can recover from one failure without grinding.
- Central **Arena Supplies** store with unique exterior, no Poké Balls. Buy Potions/Super Potions/Hyper Potions, status healing, Ether/PP restoration, Revives and supported X-items. Inventory and real price/consume behavior must work.
- **Healing and battle items remain usable DURING real-time fights via the native START → BAG menu.** Native Arena should pause correctly while choosing target/item, then resume; Pokémon switching similarly. Limited usage/cooldown for balance is an optional tested adjustment, not a removal of items.
- Tower 1–4: specific recovery checkpoints. Tower 5–8: **full-team recovery checkpoints** between floor groups (vary count by length). Elite Four in V10: full team heal **after Elite II and after Elite IV**, subject to playtest; if objectively too punishing, consider more. Defeat returns to city with free full heal, progress/rewards kept but current run reset.
- Keep higher difficulty from **team composition and AI**, not mandatory XP grinding. Level normalization or bounded tier brackets; fight difficulty grows with rank and player tools.

## How V9 is accepted
1. All eight city exteriors and authentic interior chamber paths visually inspected, signs and directory accurate, NPC/Pokémon wanderers collision-free; central Lab and item shop not fake placeholder houses.
2. **Actual** 2–6 enemy Pokémon native trainer battle; correct team depletion, trainer rotation, proper win/loss transitions; battle sprites vary by trainer; challenger and player remain opposite sides.
3. Two **clearly different real-time battlefield environments** per tower (trial vs leader), with at least one visible genuine interactive hazard in each theme. Champion deferred to V10.
4. Moveset compatibility matrix, AI move-frequency telemetry, and demonstrations of multiple different move types (not recurring orb spam), protect/cancel/clash/element effects working.
5. Lab selection/reward flags save reliably; 187 species validated for selection by tested native movesets; any unsupported one explicitly locked until fixed and reported, not advertised as complete.
6. In-battle Bag/heal/status/revive/battle items + shop's spend/save logic + defeat fine implemented and tested; no Poké Balls on sale.
7. Test saves and fresh starts in mGBA **and Delta**, including returning after a lost tower, repeating, changing squad, no-turn-based fallback and no text corruption. Linker RAM/ROM headroom reviewed.
8. Only then promote experimental V9 artifacts as playable. Compilation alone is not sufficient.

## V10 reserved features
- Entire **Elite Four** (Arctic/Articuno, Iron/Registeel, Lightning/Raikou, Crystal/Regice), plus World Champion **Ho-Oh**. Each six-member roster; themed arena, dialogue, reward/saving and correct reset to Elite I on any loss while earned legendary licenses remain.
- Full healing **after Elite II and Elite IV**; items may be used mid-fight and between rounds; no unlimited free item restocks during gauntlet.
- **Masters Circuit** uses remixed teams/advanced AI/limited healing, preserves first-clear unlocks and awards one selectable shiny palette license per first Masters clear, with progressively harder repeating Summit shiny opportunity.
- Final balancing, ending/credits, save migration, completion records/medals and game QA.

## Approval checklist
- [ ] Eight tower identities, facades, trial + leader battlefields approved.
- [ ] Central city Lab, shop, services, NPC signage and themed districts approved.
- [ ] Economy: 10%-of-carried-money loss fine, max 1,000; free essential healing/entry approved.
- [ ] Two-signature-reward + extended tower pool, original 187 roster approved.
- [ ] V9 then V10 division approved.

**Do not start large content builds until user signs off the tower themes/design.** After approval, implement/build/check in batches and offer Delta ROM only once a real artifact exists.
