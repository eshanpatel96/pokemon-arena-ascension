# Ascension healing, battle items and central supply shop — locked design

**Approved October 8, 2026 — not yet implemented in a verified ROM.** This supersedes earlier partial-heal, one-time Champion heal, and “no items during battle” planning assumptions.

## Healing rules
- Within a multi-Pokémon trainer encounter: no free automatic healing between enemy send-outs. HP, status and PP persist between active Pokémon. Player may pause and access **Bag** to use battle items/healing items; consume stock normally. No infinite item spam or turn-free exploit; implement a measurable recovery/opening cost after a combat item and test that it never lets players bypass recovery windows.
- Between rounds: no free automatic heal except specified checkpoints. Party may review loadouts, spend purchased items and change lead, with native PP restoration between trainer floors as proposed; test for compatibility with original engine.
- **Towers 1–4:** keep forgiving full-heal checkpoints at defined points (Bronze before leader, remaining to be tuned).
- **Towers 5–8:** full-team healing at the clearly labeled recovery room/checkpoint before the leader. Earlier floors still force thoughtful HP/item use; no forced partial-only restoration. Exactly how many earlier checkpoints is a balancing variable, not an implicit second full heal.
- **Elite Four + Champion:** **automatic full recovery of all party Pokémon, PP and status after every successful Elite Four battle**, including immediately before the World Champion. Each of the five opponents fields a six-Pokémon elite team; difficulty comes from each individual well-designed encounter. Roster and items may be managed between battles, but swap restrictions should be explicit; no mid-run Lab or outside refill.
- Lose Elite II, III, IV or Champion: return to city, fully heal, **restart next attempt from Elite I**. All earned first-clear recruitment licenses remain. Never farm duplicates from repeats.
- **Masters Circuit:** harder opponents, hazards, team compositions and optional no-heal medals; if healing reductions are introduced, they must be explicitly announced and tested, not silently applied to normal Elite Four.

## Arena Supply Shop
- Main central-city building is a distinct **Arena Supply Shop**, not a generic capture PokéMart. **No Poké Balls and no wild captures in tower trainer fights.**
- Prize currency: original **Pokédollars** are preferable to inventing a second “Arena Credits” balance; earn money by beating trainers/floors/tower leaders, display payouts on victory and preserve across save/load. Cap any bonus farming to prevent trivial infinite potion stocking.
- Stock (candidate): Potions / Super Potions / Hyper Potions; Full Heals and status remedies (Antidote, Paralyze Heal, Awakening, Burn Heal); Revives; battle consumables such as X Attack, X Defense, X Speed, Guard Spec and Dire Hit **only after** compatibility tests in the real-time combat engine. Full Restore/Max Revive should be appropriately scarce or Masters rewards.
- Prevent buying/selling Poké Balls inside Arena Supply Shop. Use a curated Emerald-native item list, but do not assume existing PokéMart stock matches the custom list.
- Economy: early victories afford basic healing, later victories afford strategy items. Essential city healing is always free and entry is never paywalled. Players can recover from zero money by visiting the free Lab healer and earning from practice battles.
- **In-combat item UX:** START → BAG → pick item → pick target → consume once → return to paused/recovery state, maintaining original battle sprite/AI/weather and avoiding default turn-based fallback. Items with unsupported real-time mechanics must be clearly disabled rather than silently doing nothing.
- Held items and consumables need separate validation; unsupported effects must not force a surprising permanent switch to classic mode.

## QA
1. Purchase a Potion and an X item, see money deduction and Bag count, save/reload.
2. Use Potion during arena fight: confirm HP changes once, item decreases once, native fight resumes with cooldown and weather preserved.
3. Use status remedy and Revive where compatible; verify fainted targeting and no wrong party index.
4. Test battle boost items explicitly for correct effect and duration before selling them.
5. Full heal after every Normal Elite win, plus before Champion; current run remains locked; loss resets to Elite I while reward inventory persists.
6. Tower 5–8 checkpoint full recoveries include fainted Pokémon, not just HP of surviving members.
7. Shop stocks no Poké Balls, Bag doesn't let player capture a trainer's Pokémon.
