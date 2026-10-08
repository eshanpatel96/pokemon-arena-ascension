# Ascension V9 — Gameplay/City Release Contract

**Status: work underway; NOT a claim that the complete feature set exists in the compiled ROM.**

This is the consolidated player-approved direction from October 8, 2026. The original Emerald Arena v0.13.0 real-time engine and all 187 existing animated species remain the foundation. Original high-quality Pokémon/Emerald visuals, mobile Delta controls and native effects are preserved. A green GitHub build is NOT a complete in-Delta playthrough.

## 1. Full combat circuit — no fake towers

All eight towers must offer genuine multi-Pokémon **single-active-versus-single-active trainer battles**; the opponent's next Pokémon enters when its current fighter faints. Only defeating the whole opposing party wins a floor. A normal floor uses 2–5 Pokémon; leaders should field 4–6 with their legendary last. Do NOT spawn 2v1 until physically supported. Rank and floor saves remain persistent and accurate.

Round presentation: visible exterior entrance → themed lobby → Master states tower-specific tips/risks → Master exits the battle lane → challenger enters using authentic native overworld trainer graphic → both trainer sideline sprites appear at **opposite sides of the real-time arena** with the same identity → challenger uses several native moves → winning trainer outro → opponent walks out → new challenger walks in. Before leader, a separate prep/checkpoint area with recovery choice, then a **visually distinct, authentic Emerald-style boss chamber** and native arena background. Leader congratulates player after defeat and states recruitment rewards and next tower.

Different trainers, sprites, team members and useful four-move loadouts must vary on repeat losses. Source fix needed for Brawly hardcoded trainer sprite (battle render derives from gTrainerBattleOpponent_A, not overworld local graphics ID). V9 must explicitly test this mapping on Delta. Enemy AI move selections vary by distance, role, cooldown, target and move recency; preserve type effectiveness and prevent the same projectile from being spammed unreasonably. Existing attack interruptions, Flamethrower clash, Protect, water/ice/electric terrain and other native Emerald Arena mechanics must be exploited, **not reimplemented from scratch**.

## 2. One coherent city center; distinct surrounding towers

Two native Battle Frontier-based districts stay connected; never enlarge the city merely to scatter identical buildings. Replace the middle strip of identical Battle Frontier homes with the **visible central research-and-preparation campus**: unique native-style Lab exterior, battle-item supply shop (not a standard Poké Mart), practice/training dojo, Move Studio, style/nickname/nature/EV customization services; limited residential NPC houses and garden landscaping only where appropriate. Wide paths, no invisible doors, NPCs never embedded in counters or blocked tile geometry. Use actual graphics/metatiles or verified tileset reuse, not text labels over unchanged exteriors.

Eight tower exteriors should feel native but themed by local flora, terrain, architecture, roof/banner palette, props and lighting; each tower has **one unambiguous entrance**, clear sign, correct rank number, and an approachable attendant. Keep trainer and Pokémon overworld walkers on verified passable tiles without obstructing doorways. City START → ARENA GUIDE shows tower progress, correct next tower and actual directions. No raw dialogue encoding errors or trapping loops.

Battlefield environment production template: shared authentic Emerald asset palette/prop set for each tower's trial arena, and a distinct dramatic leader arrangement. Bronze stone courtyard vs imposing master coliseum; Gale airy terraces; Verdant sunny forest/giant tree; Phantom misty graveyard/crypt; Inferno volcano/furnace; Tidal water and ice; Thunder storm/electric hazard; Astral star/crystal observatory. Arena-specific mechanics must be real (collision/weather/cover/element effects), visible and telegraphed. A mere pre-existing Battle Dome tileset with a different label is **not** adequate as a complete theme pass.

## 3. Lab, 187 species, unlocks and professor

Target exactly the existing 187 animated Pokémon—NO new Tyranitar/Groudon sprites in V9. Allocation [ALL-187-CAREER-ROSTER.md](ALL-187-CAREER-ROSTER.md): 80 strong starter choices, 64 tower rewards (8×8), 25 Championship rewards and 18 Masters rewards. A Pokémon should not be claimable before its unlock. Every fully selectable species has 4 safe, genuinely differentiated Arena moves and tested native PP, ability, faint/switch, animation and battle-return behavior; unsupported species are explicitly locked until validated. Professor Birch is the central service for opening boxes, arranging team, checking rewards, and preparing for each tower. No reward is silently lost to a full party; save/reload permanent reward flags and box transfers.

Tower first clear grants two headline recruit licenses (legendary plus elite partner), plus additional thematic Pokémon through floor medals and challenges. Bronze Regirock+Aggron, Gale Lugia+Dragonite, Verdant Suicune+Sceptile, Phantom Mewtwo+Gengar, Inferno Entei+Blaziken, Tidal Kyogre+Swampert, Thunder Zapdos+Metagross, Astral Rayquaza+Salamence. The other 25 Elite/Champion and 18 Masters roster positions are V10 campaign features but catalog and save schema should anticipate them.

## 4. Battle item shop and fair loss economy

- Use native Gen III money. Win a trainer floor → payout depending on rank/floor; lose → **10% of current balance capped at ₱1,200**, never below zero. Failure does not deduct earned permanent unlocks. No paywall/debt and free city healing/practice always.
- Shop sells only tactical and healing items: Potion, Super/Hyper/Max Potion, Full Restore, Full Heal, Revive, Max Revive, Ether, Elixir, X Attack/Defend/Speed and Guard Spec. **No Poké Balls**.
- Bag accessible **during active real-time battles** through existing Emerald Arena START pause; items can heal, cure, revive or buff subject to existing native engine eligibility. **Don't assume every consumable item is safe**: test UI return, quantities, PP/effect persistence, switching, damage while paused, and avoid spammable heal abuse.
- Items can also be consumed in between rounds. Full heal/checkpoint cadence: Towers 1–4 guided; Towers 5–8 offer meaningful FULL restore checkpoints. An Elite Four gauntlet heals after its 2nd and 4th battles, not every fight by default; loss restarts Elite I but keeps earned unlocks.
- Battle shop layout/stock must genuinely work, not just a nonfunctional room label.

## 5. V9 acceptance blockers

1. All 8 towers and Summit enter original real-time multi-member trainer fights, opponents cycle, finish/defeat properly, exiting correct door.
2. Identical-looking trainer bug resolved: sideline opponents represent actual challengers and stand opposing each other.
3. 1st and 2nd opponent faint replacement, player switch and PP exhaustion remain in real time and don't corrupt UI.
4. Every tower has readable NPC dialogue before/after, clear wayfinding, Master exit/return and leader boss handoff.
5. Visible central Lab, properly aligned NPCs, working PC, real shop with item inventory and no Poké Balls, money payout and defeat penalty.
6. A functional selection/UI path for every approved starter species, and persistent tower reward flags; distinguish design-only roster counts from actually selectable/tested counts.
7. Ability/move test matrix, type/AI consistency, effects and battle pause/Bag verified.
8. Two districts traversable, walking Pokémon/NPCs visible on passable tiles, door/warp correctness and working signs, on **Delta**.
9. Full asset/ROM/RAM size checks with headroom budget; don't claim a new visual environment based only on reusing one lobby.
10. Saving, cold booting, retrying loss and rematches verified.

**Milestone philosophy:** Prefer one fully validated reference tower and working systems over faking all eight. Publish alpha binaries separately from a fully accepted V9 release, with known limitations clearly stated. V10 delivers the full 55-fight story, Elite Four, champion finale, Masters circuit and shiny rewards.
