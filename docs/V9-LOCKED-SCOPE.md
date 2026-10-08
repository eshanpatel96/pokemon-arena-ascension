# Ascension V9 — Consolidated Release Contract (2026-10-08)

**Status:** Agreed design, implementation not yet finished. V9 must preserve the original Emerald Arena 0.13.0 real-time battle engine. No fake arcade renderer and no unsupported promises of all features being live until Delta/mGBA tests pass.

## V9 definition of done

A player starts a fresh career in an attractive, coherent, functional central city; chooses from a broad collection of native animated Pokémon and customizes battle loadouts; locates the correct tower from obvious exterior signs / START Arena Guide; walks through a single clearly themed entrance; sees the Master move away and distinct challengers enter; fights real multi-Pokémon trainer teams in distinct normal and boss battle environments with smart varied moves, item use and correct healing/forfeit rules; earns currency and persistent Pokémon licenses; can shop and manage team; save/load is reliable. **All eight towers have this loop.** Full Elite Four / Champion plus second Masters circuit remain V10.

## Hard original-engine constraints

- V7 link used about **99.81% of 32 MiB ROM** and **99.18% of EWRAM**. V9 must budget ROM/RAM before new graphics. Reuse/recolor native tiles and battle stages/effects where possible; prune unused story assets and profile overhead before introducing unique asset sets.
- The pinned upstream Emerald Arena release is **v0.13.0, e1502f9**, with **187 original animated species** and **89 native real-time move profiles**. This is an animation roster, **not** proof that all 187 already have compatible movesets or will always stay in real-time after fainting. Produce a species-by-species compatibility matrix, and gate new selectable entries on four genuinely useful supported moves, correct ability/effects, PP, party switching and opponent replacement.
- Don't import Groudon or Tyranitar as "existing" assets: these are NOT in the original 187 animated species. Bronze reward pair is **Regirock + Aggron**, Inferno **Entei + Blaziken**.
- Never silently replace original Pokémon graphics, small size reduction, movement/dodge or native battle renderer. New build must remain a 32MB valid .gba playable on Delta.

## Phase A: Central Trainer's Plaza — redesign in current footprint

Replace generic, visually inconsistent center buildings with **purpose-specific Pokémon-native architecture**:
1. Main **Ascension Pokémon Lab**: prominent distinct research exterior, reception, walkable terminals, accessible Pokémon PC/Boxes, 187-species unlock catalogue, battle team/order/loadouts, reward collection; not a Pokémon Center interior with a new label.
2. **Battle Supply Shop**: obvious sign; sells only in-battle healing, status cure, revive, PP-restoring, and strategic held/battle items. **NO Poké Balls**, capture items or story-only goods. Item list and prices must match what actually functions in native real-time Bag.
3. **Move Studio**: choose compatible four moves per Pokémon with role/range/power/cooldown preview. No unsupported moves advertised as viable.
4. **Training Center**: optional EV/nature adjustment, move and type practice, time trials; level normalization means no mandatory XP grind.
5. **Name Rater** and **Style Studio**: Pokémon renaming and trainer sprite/palette/wardrobe choices using existing GBA visuals; only promise selectable options once interfaces are functional.
6. Real **residences, gardens and paths** around these landmarks so the center feels like a small town, not an unlabeled shopping mall. Add NPCs and occasional roaming Pokémon on collision-checked tiles only; no characters standing inside counters, trees or building roofs.
7. A readable **sign at every functional doorway** (Lab, Supply, Studio, Training, Name, Style, each tower). Update **START → ARENA GUIDE** with current rank/floor, next tower, named location, unlocks, and right directions. Sign coordinates must be verified against interactable native sign metatiles.

**Keep city total footprint approximately unchanged.** Give each tower vicinity themed landscaping, matching entrance architecture and exterior NPCs.

## Phase B: Eight consistent but visually distinct towers

Towers always have a **single unmistakable street entrance** → themed foyer → Master briefing → one visible arena threshold → opposing trainer enters and walks to the **opposite side** from the player → original Emerald Arena fight with actual trainer identity → loss/victory text and challenger exit → next challenger or checkpoint Master → a separate dramatic boss chamber → signature legendary final ace → master congratulates player, announces specific Pokémon licenses available at Lab and guides toward the next tower. **Master must leave battle lane** and not stand inside a desk. No duplicated decorative "fake doors", inaccessible gates, or battle triggered by a clerk instead of entering the arena.

| Tower | Streets and foyer | Native-themed trial arena | Distinct boss chamber | Master pair |
|---|---|---|---|---|
| 1 Bronze | Stone academy, practice flags | Rock cover and heavy attack windows | Regal stone arena, special Regirock entrance | Regirock + Aggron |
| 2 Gale | Windmills, cloud banners | Open terraces and gust timing | Skyborne ring, Lugia final ace | Lugia + Dragonite |
| 3 Verdant | Greenhouse, vines, sunlight | Grass, cover and sun | Giant-tree sanctuary with Suicune | Suicune + Sceptile |
| 4 Phantom | Haunted manor, candles, gravestones | Mist, obstacles and feints | Haunted crypt with Mewtwo | Mewtwo + Gengar |
| 5 Inferno | Forge, lava light, black rock | Heat, timed vents, Flamethrower clash | Molten leader chamber with Entei | Entei + Blaziken |
| 6 Tidal | Water channels, waterfalls | Shallows, ice and electric conduction | Flooded amphitheater with Kyogre | Kyogre + Swampert |
| 7 Thunder | Lightning spires, machinery | Conductive surfaces and telegraphed bolts | Grand lightning arena with Zapdos | Zapdos + Metagross |
| 8 Astral | Observatory, crystals, stars | Moving cover, advanced AI | Celestial ring with Rayquaza | Rayquaza + Salamence |

**Both real environments (trial and boss)** must be visually and mechanically different, not just the text or trainer name. Reuse tiles/palettes/FX intelligently to fit native ROM budget. Boss room requires genuinely better scene design than the current placeholder Battle Dome clone.

## Phase C: Real trainer teams, matched sprites, distinctive move AI

- One active Pokémon each side, but **2–6 Pokémon per trainer team** depending on floor and tier; victory triggers ONLY after last opposing Pokémon faints. Fully preserve in-arena player party changes, faint transitions, HP/status/PP and supported native battle flow.
- Overworld trainer appearance must match **in-battle sidelines**, trainer introduction and opponent trainer ID. Different trainers across floors; leader is separately dressed and positioned. No fixed Brawly trainer pic on every screen.
- Enemy move choice must NOT spam a single high-score damaging "ball" move. Score based on move range, current positions, type and role, utility/status opportunities, opponent attack windup, time since move last used, PP, terrain and cooldown. Support rushdown/ranged/control/defensive/leader AI archetypes. Test selected-move distribution on real fights.
- Use existing upstream mechanics: attack interrupts/cancel on supported hits, Flamethrower clashes, Hyper Beam–Protect, rain/flood, electric conduction, ice, walls/cover, Psychic rocks, Dig/Fly/Teleport/Seismic Toss/Double Team/Rollout, stat/status/ability behavior, native move costs/PP.
- Build a **full compatibility matrix for the 187 species** and supported four-move loadouts; starter/reward pools exactly match `ALL-187-CAREER-ROSTER.md` (80 starter, 64 tower, 25 Championship, 18 Masters). Some lower evolutions exist as optional low-power playstyles. The roster is not instantly unlocked wholesale; 107 earnable licenses remain permanent. No duplicate legendaries awarded by normal rematches.
- Level progression is normalized to promotion brackets, not grinding. More skillful AI, compositions and environment create the difficulty.
- Towers 1–4: checkpoint(s) with full/partial healing as balanced. **Towers 5–8: full-team healing checkpoints** at explicit well-placed stages, not between every floor. HP/status carry otherwise; PP refresh between floors. Between each trainer's multiple Pokémon, nothing auto-heals.

## Phase D: Credits, loss deductions, items and shop economy

Currency is **Arena Credits** (not real money). Every completed trainer/floor rewards credits; bosses more, no-heal medal optional bonuses. Trainers never require a positive balance to enter. Losing reduces your **carried wallet by 10%, capped by tier**:
- Bronze/Gale: at most **200 credits** per defeat
- Verdant/Phantom: at most **400**
- Inferno/Tidal: at most **700**
- Thunder/Astral: at most **1,000**
- Defeat cannot take the wallet below zero. Credits already spent remain spent; claimed Pokémon and ranks/medals NEVER lost. No required entry fee. **Free basic city healing**, free practice and a repeatable small-credit challenge ensure recovery from zero money.
- The center shop sells potions/full heals/revives/status cures/PP restoration and selective held/battle items, **never Poké Balls**. Stock scales as progression advances. No paywall for species licenses.
- **Item use during real-time fighting is essential.** Preserve START→Bag and Pokémon native controls; using an item pauses time (no free enemy hits while a menu is open), consumes stock on success, applies native effect to chosen target, respects inventory and applies a bounded time/cadence cost or per-battle limit tuned with actual gameplay. Cannot infinitely open/close Bag to reset combat AI or animation. Keep item costs/power balanced rather than disallowing them.
- Between-fight prep chamber allows reviewing party, changing party lead, spending items and choosing to continue/withdraw. Failure ends the tower attempt, preserves permanent rewards, and returns to city for heal, shop and retry.
- **Elite Four rule for V10** (not V9 feature): full restore after Elite II and Elite IV, full teams and limited Bag strategy, loss resets the gauntlet to Elite I while keeping completed trainer's licenses. Masters has stricter healing.

## Phase E: Rewards, save persistence and career UI

- Eight Towers × eight unique recruitable species plus normal 80 starter species. Tower Master first clear grants named legendary and elite companion; floor medals and optional feats award the six additional tower species. Never inject into a full team; claim/view/select in Lab.
- Use valid persistent save flags for rank, tower/floor, completed tower medals, reward licenses and claimed status, money, item inventory, and loss/rematch seed. Cold reload in Delta must restore all.
- Master script victory: acknowledgment + named two-reward announcement + go to Lab + next destination shown on START Arena Guide. Loss: deduct credits once and rotate to an alternative themed team; no money penalty charged twice for one defeat.
- Champion's four Elite and World Champion, plus second Masters campaign/Shiny Licenses, are the **V10 milestones**. V9 should not abandon proper tower finish flow or basic rematch variation.
- Real trainer boss legendary stays the last team member; its use must be validated before granting its license.
  
## V9 acceptance tests (not compile-only)

1. Fresh SELECT career, city loads with English, navigable plaza and functioning correct Lab/Shop/Studios; every building exterior has readable sign, collision-checked NPC/Pokémon.
2. All eight tower entrance/interiors are recognizable and theme-specific; **one entrance**, Master steps aside, trainers enter and stand on opposite sides. Distinct in-battle trainer identity on all floors.
3. All towers have distinct trial arena environments and genuinely special boss arenas. No fallback to default duplicate hall.
4. Party of multiple opponents actually swaps members in real time when a foe faints; trainer battle ends only after entire party is defeated, no repeated projectile as only strategy, correct AI variety even at Bronze.
5. Native Bag pause/party/items/stats and free recovery checkpoints work with no freezes; 5–8 full heal checkpoints match design; currency debit applies once on loss and can never softlock.
6. 187 roster entries are indexed and every selectable entry has verified animation, four supported moves and switching compatibility; report any temporarily unselectable entries, don't silently fake completion.
7. Save/quit/reboot continues with correct wallet, items, rank, unlocks and available towers.
8. 32MB GBA ROM checks, ROM/EWRAM/IWRAM link diagnostics, worst-case visual scene performance, mGBA smoke tests and **hands-on Delta gameplay**.

## Release sequence

A. Audit and budget ROM/RAM; native regression tests + renderer identity/move instrumentation.
B. Finalize city plaza art, interactable shops/Lab and sign positions.
C. Complete Bronze full multi-trainer/boss/receipt loop including loss money and in-battle items.
D. Apply tested pattern to Gale through Astral with authentic theme-specific art and AI, one tower at a time.
E. Enable and validate 187 catalog entries/earned species and menus; package tested .gba in meaningful builds, not a stream of tiny untested revisions.

**Separate V10:** Elite Four + Champion gauntlet, Masters Circuit and Shiny License rewards, championship final ending, content polish and full multi-hour balance suite.

**Source docs:** `ALL-187-CAREER-ROSTER.md`, `V8-COMBAT-BALANCE-AND-TRAINING.md`, `TOWER-ACES-AND-REWARDS.md` (latter contains prior superseded 60-species suggestions), `V8-V10-RELEASE-PLAN.md` (earlier state).
