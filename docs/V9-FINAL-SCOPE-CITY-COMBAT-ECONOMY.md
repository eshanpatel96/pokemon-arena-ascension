# Pokémon Arena: Ascension — V9 LOCKED SCOPE: City, Arenas, Combat & Economy

**Design version:** 2026-10-08. **Status:** planning only; no V9 ROM created by this document. Supersedes outdated 60-Pokémon cap and conflicting older healing plans. The full roster allocation is in [ALL-187-CAREER-ROSTER.md](ALL-187-CAREER-ROSTER.md).

## Definition of V9 done

On an iPhone running Delta, a new player can enter an attractive, fully functional two-district Ascension City; navigate using correct signs and START > Arena Guide; choose from a validated 187-species roster (80 open on arrival; the remainder locked appropriately); use the Lab and battle-only supply shop; and complete all eight towers through native, varied trainer-party fights, with genuine boss rooms, themed native real-time battlefield effects, post-fight rewards, in-battle Bag items, save/load, and an economy that charges for defeat. V9 is a **substantial complete eight-tower experience**, not a compiler-only demonstration; Elite Four/World Champion and the full Masters circuit are V10.

**Preserve the original Emerald Arena 0.13.0 real-time engine**, existing 187 animated sprites, handheld movement/dodge, attack and sprite scaling. No separate arcade game or fallback offered as an intentional gameplay mode. Source currently pins upstream commit `e1502f9`, already the 0.13.0 release (October 4).

## V8.2 bugs and regressions — V9 P0 blockers

1. **Trainer identities:** The V8 Bronze trainer battle uses a fixed Brawly opponent ID despite rotating overworld challenger sprites. In `realtime_arena.c`, `OpponentGraphics()` chooses sideline sprite from `gTrainers[gTrainerBattleOpponent_A].trainerPic`. Fix synchronization (overworld arrival sprite, trainer name/intro, battle ID/appearance, right sideline). Player stands on **left** opposite trainer on **right** during battle. Never show the same unrelated trainer in every arena.
2. **Choreography:** Master briefs, steps entirely off the fighting lane and disappears while competitors fight. A different challenger enters from far side and says an archetype-specific intro. Full trainer team enters sequentially; victory happens only after the **last enemy Pokémon** is defeated. Losing trainer speaks and walks out; new challenger enters; Master or medic returns at clearly indicated checkpoints. Final room has a visible door/gate to a **separate genuinely majestic boss arena**, with unique boss trainer art/intro and congrats/failure outro. Win text names unlocked Pokémon, credits and next tower.
3. **Opponent AI:** Source `AiChooseMove()` maximizes raw power × type effectiveness plus limited RNG; players observe high-power orb/ball spam. Add move-repetition penalty, distance/utility/cooldown/status weighting and 4–5 archetypes (rushdown, ranged zoner, balanced counterpunch, tactical stall, boss specialist). Log combat telemetry by species and selected move. Protect native damage/PP/aim/windup correctness; do not invent free universal cancellation.
4. **Enemy teams:** Fights are trainer parties (1 active enemy each side, 2–6 opponents per floor; 4–6 for bosses), **not** sequential wild encounters pretending to be a trainer. Preserve 4 real-time-compatible moves per member, actual roster swapping, faint transitions, held items, HP and status. Unsupported moves must not force classic battle UIs in curated V9 ranks.
5. **World integrity:** Every door and return warp has an unambiguous destination, no accidental old Frontier interiors, no redundant/hidden door search, signs can be read, no NPC/Pokémon spawn inside furniture or block the only exit. Cold-save/load must retain floor, rank, money and unlocks.

## 1. City footprint and central plaza

**Do not expand geography again.** Keep the V7/V8 connected West and East district footprint. The user considers the inherited Battle Frontier cluster of generic houses, Pokémon Center and Mart visually wrong. Redesign their **external façades and landscape**, not merely their dialogue and interior script.

### West central plaza — ordered around ONE dominant research Lab
- **North/center: Ascension Pokémon Lab / Academy**. Large unmistakable science/research building using authentic native Emerald professor/Devon-style metatiles/palettes, bright entry sign, statues or Poké Ball mosaic, laboratory greenhouse and walkway. One obvious front entrance; Professor/scientists/terminals inside on verified walkable coordinates; PC storage and team management must actually function.
- **Southwest: Battle Supply Shop.** Custom storefront distinct from a conventional PokéMart or Pokémon Center, with a **BATTLE ITEMS / HEALING** sign, a working merchant/menu backed by save-money and bag inventory. NO Poké Balls, Great Balls, Ultra Balls or catching consumables for sale.
- **East of Lab: Move Studio.** Native supported four-move loadout changes and explanation of range, windup, recovery and status. The 89 existing Arena profiles are reused, not masqueraded as 89 new attacks.
- **West/near plaza: Training and Nature Studio.** EV/nature tuning at clearly stated limits and costs; no mandatory experience grinding. Different functional staff rather than NPCs with 'coming soon' text.
- **Southern side: Wardrobe + Name Changer**, modest cosmetic house/residence with distinct exterior and functioning naming/palette options after save-safety validation.
- **Perimeter houses** (not doors secretly leading to towers): believable neighbors, trainer tips, optional quests, records, atmospheric NPCs; do not fill the main square with empty decorative buildings.
- A central **ranking statue and tower-directory sign** with cardinal directions/number/name, matching START > ARENA GUIDE. Distinct paved ring, planting beds, benches, decorative lamps, well-marked shop paths, no blocked routes.
- Outdoor life: roaming trainers, civilians, Pokémon sprites using **existing original Emerald objects**, low counts that fit OAM and performance; varied dialogue, idle movement range that cannot occupy doors, no sprites embedded in scenery. Recheck original tiles/map collision bitfield at each spawn AND path destination.
- City heal is ALWAYS free, including when player has 0 credits. No money-softlock.

### City UX
- Each tower approach has a **numbered sign**, clear name, thematic visual cues, a large visible entrance, plus sign indicating floor count/heal rule and which rank is next/locked.
- START → ARENA GUIDE: rank, current tower, all ordered towers, location/directions, completed status, available next opponent, owned credits and recent unlocks.
- No invisible hotspots or multiple confusing 'doors' in a single wall. Visual signs are original 16×16 Emerald metatiles/sprite billboards grounded to map events, not floating UI pasted onto screenshots.

## 2. Themed tower visual package — ALL eight in V9

Every tower has **four distinguishable experiences**: neighborhood exterior, inside briefing/prep room, active trial battlefield, and a much more dramatic leader chamber/boss battlefield. This is a genuine change to environment and gameplay, not a textbox label or palette-only selection.

| Rank | Exterior and neighboring NPCs | Interior briefing and trial arena | Boss reveal and battle stage | Mechanical identity |
|---|---|---|---|---|
| 1 Bronze Trials | Stone academy/arena facade, masonry flags, Rock/Steel statues and trainees | Stone training hall, sparring rings, impact markings, authentic boulders | Elevated bronze colosseum with banners and detailed Regirock temple masonry | Dodge timing, destructible stone, slow telegraphed punish |
| 2 Gale Tower | Wind spires, banners, open green/windy plaza, Bird Keeper NPCs | Open-air balconies, flags and railings | Cloud-level sky arena with dramatic gust effects, Lugia finale | Gust direction, mobility, safe ledge/cover |
| 3 Verdant Crown | Vines/greenhouses, trees, grass gardeners and garden Poké NPCs | Sunlit conservatory, tall grass, movable cover | Giant ancient-tree sanctuary, Suicune guardian finale | Sunny cover, roots, drain, repositioning |
| 4 Phantom Spire | Gothic exterior, gravestones, dusk palette, Hex Maniacs, ghost visitors | Haunted corridors with wisps/tombstones | Fog-heavy haunted crypt, Mewtwo aura finale | Visibility/misdirection, shadow, protected openings |
| 5 Inferno Forge | Basalt/forge facade, smoking vents, blacksmith/fire trainers | Heated stone hallway, lava channels and safe paths | Large erupting volcanic arena using native magma/stage art, Entei finale | Readable periodic lava vents, flame clash, fire/cooldowns |
| 6 Tidal Bastion | Harbor/pier, aquatic motifs, water trainers, Wingull | Aqueduct/tidal hall, streams | Flooded amphitheater and storm stage, Kyogre finale | Flooding, ice, charged water, ranged spacing |
| 7 Thunder Citadel | Electric coils, dark storm clouds, conductive iron facade | Steel machinery hall, insulated routes | Lightning-charged rooftop, Zapdos finale | Telegraph shocks, electrical conduction, fast pursuit |
| 8 Astral Apex | Observatory towers, star signs, crystals and Psychic trainers | Stargazing/crystal hallway | Changing stellar observatory with Rayquaza finale | Shifting cover, advanced predictive AI and positioning |

**Resource rule:** source currently uses ~99.8% ROM and ~99.2% EWRAM at link time. **Recover memory headroom first**, reuse built-in stage assets, tiles/palettes and environmental effects; generate small bespoke façade tiles or banners only after ROM/RAM budget and Delta frame pacing prove safe. Cannot promise 18 full new high-resolution backgrounds. Native effects include flame clashes, water/ice/charged surfaces, Psychic/rock interactions, shields, smoke, and environmental props. Native art is the baseline, not mockup sprites. Graphically distinct boss-room entrance, stage composition, lighting and props are required for each tower.

### Boss fight story
Arrival → themed Master guide briefs the team and floor objectives → Master steps aside → individual challenger enters from opposite door and speaks → trainer on right in battle and player on left → full roster sequential fight → challenger says defeat/victory line and leaves → repeated through floor → if checkpoint, real medic appears → gate physically transitions to DIFFERENT boss chamber → leader enters/introduction, unique arena art/music, legendary as **last of a multi-Pokémon boss roster** → winner reward ceremony (two marquee species, floor extras, credits, onward directions) → return via correct exit. Defeat reset retains earlier permanent career unlocks; rematch roster rotates while boss ace stays fixed.

## 3. 187 roster and unlocks

Use exactly the 187 entries already shipped in upstream `game/overlay/tools/arena/roster.json`. **No new Pokémon art required**, and do not promise absent Groudon/Tyranitar. The fixed [complete roster allocation](ALL-187-CAREER-ROSTER.md) assigns:
- **80** available from arrival (including some fully evolved Pokémon so teams can win).
- **64** tower unlocks = 8 per tower; boss headline species and legendary granted on first win; other six earned by progression/optional feats/medals.
- **25** Elite Four/Champion recruit licenses (design reserved for V10).
- **18** Masters recruit licenses (reserved for V10).
- Exactly **187**, no duplicate recruit slots. Evolution cannot bypass a locked species; don't force XP grinding or require leveling up low forms to win.
- Native badge/medal/save flags, species selection and role-consistent four-move presets are V9 requirements. A species is not marked battle-ready until sprite, ability, four moves, PP, switches, item effects, save/reload and faint flow pass. Auto-generate 187×4 move-compatibility report and allow curated overrides. Reuse canonical species IDs.
- Comp tiers level-normalized, from 60 upward after promotions; bosses use balanced 4–6 member teams with a guaranteed last legendary. Legendaries initially capped at 1 in 4-mon squads, 2 in 6-mon squads pending testing.

## 4. Credits, DEFEAT PENALTY and inventory

**All amounts below are starting balance targets, not game mechanics already shipped.**

- START WALLET: 1,500 Arena Credits. Free entry into all normal towers, zero-cost basic city healing and practice; no account debt and no ability to buy necessary career unlocks.
- WIN PAYOUT: ~200–650 credits per floor depending on rank and opponent; Tower Leader first-clear bonus ~1,500–3,500; repeat win pays less (~50–60%) but still worthwhile; Championship and Masters payouts higher, balanced with costs.
- **LOSS:** Deduct `min(1000, floor(wallet / 10))` once per failed tower attempt, even if multiple Pokémon faint. Money floors at **zero**; no debt. Consumed bag items remain consumed. In Masters, consider `min(2000, floor(wallet*0.15))` after normal mode testing. No deduction per individual Pokémon KO. Reset to start of the affected tower; earned species/reward flags remain permanent. Champion loss resets to Elite I, retains earned rewards, and incurs one loss fee.
- **Shop inventory, no Poké Balls:** Potion ~150, Super Potion ~350, Full Restore ~800, Revive ~700, status remedy ~250, X Attack / X Defense ~300; optionally PP restorative item where meaningful. Held items can also be sold after native effect compatibility checks. Inventory and receipt persist in save. Replenishing city credits through repeatable no-entry-fee practice is always possible (low payout so avoiding fights is not optimal).
- **REAL in-battle BAG:** START → Bag already exists in native engine; make shop-bought Potions, Revives, cures and battle boosters genuinely usable, with animation and effects on the correct target. Put a limited consumable/action budget per opponent trainer battle, e.g. up to **2 manually used consumables**, adjustable through testing, to prevent pause-menu unlimited heal spam. Pause/Bag should not let enemies attack unfairly while the player is selecting a target. Held item effects validated rather than assumed.
- End-of-floor PP refresh as previously agreed; HP/status/faints carry unless the player heals. Full checkpoint in towers 5–8 (one or two based on floors) and one strategically placed normal Bronze boss heal. **Elite Four gets a full heal after Elite II and after Elite IV**, not after every Elite trainer by default; player can also use purchased items during fights and between trainers. Reassess only if actual six-mon Elite teams prove excessively punishing.
- Shiny License first normal Championship clear and first Masters clears, additional harder Masters Champion repeat prizes. Permanent, non-stat cosmetic.

### Example loss math
Balance 5,000 → lose 500 → 4,500. Balance 20,000 → lose max 1,000 → 19,000. Balance 0 → lose 0 and can still heal and enter practice/towers. This is a flat once-per-failed-run penalty, **not** a floor-by-floor subscription or battle-entry tax.

## 5. V9 milestones / gates (do not call unfinished product complete)

**Gate A — Fix the foundation (highest priority):** Broken maps, collision, NPC blocking, working Bag and money/shop, trainer sprite mismatch, boss battle transitions, correctly inherited real-time trainer multi-foe sendouts, battle record/save status. Produce separate phone-test ROM and regression notes.

**Gate B — Final city landscape:** Same two-district size but original, purposeful Lab & supporting shop houses/central square. Doors/signs connected properly; every facility demonstrably functional; on-map NPC/Pokémon idle paths and door/collision checks. User visually approves real Delta screenshots, not assistant concept art.

**Gate C — Four-layer tower package ×8:** All towers visually distinct outside and inside, with real trial AND elevated leader battle stages, staging/leader after-fight dialogue, normal checkpoint flow and themed opponent AI. No duplicate-room aliases.

**Gate D — Complete 187:** Lab roster unlocked/locked UI, four supported unique role-appropriate moves per recruit, accurate save flags, all Pokémon move PP/status/switch/animations and enemy AI validation. 80 available initially, 64 tower rewards. V10's 43 championship/Masters-locked Pokémon appear as locked entries but aren't obtained yet.

**Gate E — Balance + Delta acceptance:** Full eight tower run on actual iPhone/Delta, repeated losses/defeat money penalty & item use, rematches changing lineups, legendary last, checkpoint cadence, clear/cold-reload consistency. Failures block calling V9 complete even if CI GBA build passes.

### Test automation checklist
- Check 32 MB ROM, EWRAM/IWRAM linker margins and worst-case GBA frame timings.
- Sign event matching and readable name/rank; all door coordinates, return warp anchors, tile collisions and indoor object placements before build.
- Test trainer identity in overworld and arena, score actual first 2–3 attacking moves and their usage diversity at all ranks, and distinct move effects vs 'same ball spam'.
- Shop stock excludes all Poké Ball varieties; buy/consume/persist currency, capped defeat fee cannot go negative; free city heal at zero.
- Opposing trainer team not cleared after first KO; player switch/Revive/bag/status, PP exhaustion and native trainer sendout do not fall back to classic inadvertently.
- Boss separate room AND different active arena stage, correct legendary, after-fight two-species Lab recruitment and credits; save/load; previous unlocks survive lost run.

## V10 (intentionally separate)

Complete five elite Championship battles (Arctic Articuno, Iron Registeel, Lightning Raikou, Crystal Regice, Champion Ho-Oh), full six-Pokémon squads, heals after battles II and IV, loss sends player back to Elite I but keeps earned unlocks. Finish 25 Elite recruitment rewards and 18 Masters exclusives; full Masters circuit remixed AI, reduced recovery and Shiny Licenses; ending, medals, records, outfits and long-tail balance polish. V9 must leave V10 hooks and save schema but should NOT pretend Championship and Masters are complete.

## What the uploaded recording illustrates

The user's screen recording shows social posts demonstrating upstream Emerald Arena gameplay (battlefield fire/volcano footage, trainer/menu examples). Those are **inspirations and existing source possibilities**, not an independent Delta playtest of the current Ascension ROM, nor direct evidence the V8.2 custom maps are visually finished.

**Approval rule:** This is a design document in private GitHub. No new V9 build is automatically triggered by it. Commit gameplay, compile, inspect and ship test ROM only after agreed scope and corrected bugs are actually implemented.
