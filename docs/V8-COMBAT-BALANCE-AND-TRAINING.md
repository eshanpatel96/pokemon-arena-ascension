# V8 Combat Contract — Arena Trainer Teams, Balance & Training

**Status: DESIGN / IMPLEMENTATION SPEC ONLY. No V8 ROM contains these mechanics yet.**

This follows the 2026-10-08 Delta playtest: Bronze Tower cleared in about 30 seconds; current `ascension_career.c` spawns only one scripted wild Pokémon per floor and equips just two explicit moves. It therefore lacks team play, opponent switching and a meaningful stamina challenge.

## Design decision: trainer-versus-trainer, not multiple simultaneous enemies

- Original Emerald Arena has two active combatants in its arena engine, and its eligibility logic allows **trainer battle** flags. The native battle engine must handle switching in a defeated trainer's next team member, retaining the real-time renderer when moves, effects and abilities are supported.
- Do **not** try to insert 2–6 simultaneous enemy sprites. A "3-Pokémon floor" means **sequential 1v1 active bouts against a three-Pokémon trainer roster**, with the player able to switch members of their own roster.
- Replace V7's `CreateScriptedWildMon(...); dowildbattle` for ranking floors with genuine trainer battle setup, or a carefully validated equivalent using native battle party/transition machinery. Don't misrepresent three independent wild battles as one trainer battle.
- Opposing NPC trainer stands in a dedicated battle antechamber. Walking through a visible, labeled **Arena Gate** deliberately starts the encounter. The master introduces rules and advice but does not trigger combat from dialogue.
- Show opponent/team indicator (remaining Pokémon), selected move, health and faint/switch flow using the native arena HUD. Retain familiar battle sprites and existing environments.
- Have **four compatible moves** on every opponent, not two and `MOVE_NONE`. Supported abilities/effects/PP are a hard acceptance gate to avoid classic-battle fallback.

## V8 Bronze vertical slice (4 floors including leader)

| Encounter | Enemy roster | Team size | Relative opponent level | Goal |
|---|---|---:|---|---|
| 1 Entry Test | Scizor + Blaziken | 2 | -2 to 0 | Switch, timing, dodge |
| 2 Tempo Duel | Sceptile + Scizor | 2 | -1 to 0 | Attack windows, matchups |
| 3 Endurance Match | Blastoise + Sceptile + Charizard | 3 | 0 to +1 | Carry HP, team strategy |
| 4 Bronze Master | Scizor + Blastoise + Blaziken + Dragonite | 4 | 0 to +2 | Boss AI, stage transition |

**Not predeclaring unsupported Pokémon moves as playable:** Opponent moves are to be taken from the engine's validated real-time compatibility registry. The species are curated examples, subject to a compatible-move and ability check before shipping.

- Player initially picks **four active Pokémon** at a fixed PvP-style Lv. 60 bracket; remaining unlocked Pokémon live in the Lab.
- HP, conditions and PP carry between rounds; don't automatically heal after each opponent or each floor.
- One *full* recovery checkpoint between Floor 2 and 3 for Bronze, marked clearly. Restarting a failed run is free; basic city healing is free.
- Floor victory counts only after opposing entire team is defeated. Defeat or forfeiture returns to hub without increasing tower floor/rank; previous permanent tower unlocks persist.
- Start bronze floor transition from actual tower gate, end with returning to antechamber/checkpoint or moving deeper through tower; no receptionist-triggered wild battle.
- Target **10–15 minutes Bronze** for a typical new tester (not a guaranteed duration). Tune after trials.

## Difficulty philosophy & normalized levels

**No mandatory XP grind.** It is an arena career, with challenge coming primarily from real-time combat mastery. Use a **promotion-based normalized level bracket** which levels owned Pokémon fairly as a user progresses:

| Tier | Player target | Opponents (ordinary) | Leader |
|---|---:|---|---|
| Bronze / Gale | 60 | 58–61 | 60–62 |
| Grass / Ghost | 60–63 | near equal | up to +2 |
| Fire / Water | 63–65 | near equal | up to +3 |
| Thunder / Astral | 65–70 | near equal | up to +3 |
| Champion | 70 | 69–72 | up to 73 |

Don't retroactively rewrite base stats, IVs, move compatibility, or owned mon identities when scaling level. Create an explicit, testable tournament-level normalization procedure, applied on entry and restored after return where appropriate. Trainers should never obtain >+3 levels as a substitute for smarter AI.

**Difficulty weighted toward:**
- 30% encounter/team composition, roles and type counterplay
- 25% AI pursuit, spacing, attack commitment, cooldown exploitation and defensiveness
- 25% arena geometry, cover, hazards and boss patterns (clearly telegraphed)
- 15% sustain management and selective healing
- 5% bounded level advantage

These percentages are a **design heuristic**, not a numeric damage formula.

## Tower pacing

| Tier group | Enemy team per floor | Boss team | Cadence |
|---|---:|---:|---|
| Bronze / Gale | 2–3 | 4 | Full recovery mid-Bronze; fewer in Gale |
| Verdant / Phantom | 3–4 | 5 | Partial recovery at one checkpoint |
| Inferno / Tidal | 3–5 | 5–6 | One checkpoint plus limited items |
| Thunder / Astral | 4–6 | 6 | One or two partial restores, advertised |
| Champion Summit | 6 | 6 | One limited recovery before finale |

Every normal trainer receives a battle archetype (rushdown, zoner, counterpunch, defensive staller or balanced) rather than a random species with identical AI settings.

## Training & customization: optional depth, never leveling gate

- **Pokémon Lab**: choose team, order, moves, held items and species unlocks; start with most of the initial curated pool available and withhold only thematic elite/unlock species until tower clearance.
- **Move Studio**: four validated compatible moves per Pokémon, unlock additional choices through challenge rewards; warn clearly for unsupported arena moves.
- **Training Hall**: free sparring, dummies to practice timing, time trial and boss pattern replay, no mandatory XP grind. EV/nature editor with clear caps and refundable respec fee or free changes between runs.
- **Battle items**: at V8 let each Pokémon equip *one compatible held item*; between floors allow a limited-use recovery pouch. Avoid requiring an additional in-fight Bag menu on iPhone until controller/UX and compatibility testing are done.
- **Run credits**: obtained from fights, spent on optional team upgrades, appearance and training; never gate a mandatory floor behind a paid entry or consumable. No real-money mechanic.
- **Shinies/cosmetics**: cosmetic only; no meaningful PvP-style stat bonus.

## Required native engineering validations

1. Dynamic opponent team battle starts in **original Emerald Arena** (not default turn-based) and shows the opposing trainer.
2. Faint first enemy → next Pokémon deployed → still original real-time combat; repeat through all team members without losing progress.
3. Player forced replacement and SELECT switch both return to real-time arena, with AI never acting in a corrupt background frame.
4. Exhaust all PP in one move, try every supported status effect, and check other compatible move slots; **no involuntary permanent switch to classic battle UI**.
5. HP, PP, faint counts and held-item effects accurately persist within a floor and across tower checkpoints.
6. Defeat all enemy Pokémon → floor completes exactly once; partial KO → no floor clear.
7. Save/reload mid-career and after tower clear; check rank unlocks and city return positions.
8. Real-time frame rate and sprite memory remain stable in longer multi-Pokémon battles on mGBA and Delta.
9. Actual traversal: city street → tower door → Arena Master → themed antechamber → **physical battle gate** → fight → checkpoint/leader → exit.
10. Compare beginner player win rate, first-floor duration, no-heal completion and composition diversity across multiple test teams; adjust only from empirical results.

## Integration order and ship gate

1. First write tests for trainer-party creation and correct next-enemy faint-transition behavior.
2. Implement one **Bronze Floor 1** multi-Pokémon trainer fight with original engine, gate entry and real-time party switching.
3. Test on emulator; repair any classic-mode fallbacks before scaling.
4. Complete Bronze 4-floor loop and one recovery checkpoint.
5. Add functional lab, signs and central customization district; complete visual theme passes only after ROM/RAM budget confirmed.
6. Then scale to other towers in V9.

**Release rule:** a compiler-successful ROM is a test artifact; V8 remains *unverified* until Delta can complete the whole Bronze sequence without return-to-classic battle, map trap or save corruption.
