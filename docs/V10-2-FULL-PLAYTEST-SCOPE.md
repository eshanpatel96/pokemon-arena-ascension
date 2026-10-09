# Pokémon Arena Ascension — V10.2 Full-Length Test Candidate Scope

**Design request:** 8 Oct 2026. **Status: PLANNED, NOT IMPLEMENTED OR COMPILED.** User wants V10.2 to be the *near-complete longer playtest*, followed by friends-beta hardening, not a small 10.1-style patch. Preserve all compiled V10.1 career content: eight towers (50 fights), five Championship bouts, eight Masters bouts, 187 animated species and original real-time Emerald Arena 0.13.0 controls.

**Sources inspected:** compiled V10.1 source at `6840ea411b3a9a4e799b25206f39e4193dc376fa`, [successful CI](https://github.com/eshanpatel96/pokemon-arena-ascension/actions/runs/37855729085); pinned `GBurgardt/pokemon-emerald-arena` source `e1502f9f7ed46d969880d73adbf5ab23ef7b2a56`; pinned `pret/pokeemerald` source `5eff78649e7170a877b961ef0b3da13b81a16038`; user-recorded Bronze clear/reward and tower choreography feedback; V10.1 + V9 acceptance files. No V10.2 ROM exists at this time.

## V10.2 must-ship A: real Pokémon Move Studio, not preset drills

**User target:** select a Pokémon, choose ANY move that specific Pokémon can legitimately learn, and replace ANY one of its four slots. This is a **hard requested scope** and must not be silently reduced to Protect/Double Team/Swift, shared starter profiles, or global unlicensed skills.

- Build native 4-slot move-selection UI: Party/Box Pokémon picker, inspect learned moves, browse relevant legal moves, indicate level-up/TM-HM/tutor/egg acquisition source, search/paginate by type/source, preview power/type/PP/range/arc/windup/recovery/status/native collision/environment effects; choose exactly slot 1/2/3/4, confirm/cancel, save, reload, revert to prior valid loadout. L/R navigation must work on Delta.
- Determine legality from *pinned Gen III Emerald source tables*: `src/data/pokemon/level_up_learnsets.h`, `tmhm_learnsets.h`, `tutor_learnsets.h`, `egg_moves.h`; account for stage, evolution and license rules; preserve party/box, nickname, EV/IV, held item, PP; no magical unsupported cross-species skills.
- **Critical engine blocker:** pinned original `game/overlay/src/arena_moves.c` provides **89 unique move profiles** (includes fallback Struggle and low-utility status moves). Audit across 187 animated roster found **~8,536 species–move combinations** via all-level-up, TM/HM and tutor eligibility; **~3,015 pairs** have existing real-time profiles and **~5,521 pairs** do not (egg moves not yet included). Not all Pokémon legitimately have four distinct moves (e.g. cocoons); do not invent illegal abilities. A move cannot be made selectable just by adding it to a menu—its real-time attack/status behavior, animation, PP/effects and interrupt rules must truly work.
- **Acceptance standard:** every legally eligible move appearing in final V10.2 Studio has a functioning native Arena profile, and all Gen III legally learnable moves for each of 187 entries must be handled. If completing all missing profiles exceeds GBA/engineering limits, report exact missing moves/types and obtain explicit scope revision; do not represent a supported subset as the user's requested full editor.
- Test 20+ representative species across body sizes/types, special move interactions, PP depletion, evolutions, rare/legendary and very limited learnset Pokémon, all four replaced slots, cancellation, repeated edits and save/cold reload. Ensure no broken classic-mode fallback.

## V10.2 must-ship B: final choreographed tournament and arena gates

- **Normal towers:** player walks to center of the native 10×9 court (suggest target (5,4)), opponent right (7,3), Master lower (suggest (4,7)), not overlapping party intro or the approach. Master returns for advertised checkpoints and retreats; challenger arrives/exits one by one; trainer sideline graphic/actual photo/party name matches; no desk obstructing lanes or auto battle trigger.
- **Bronze boss:** currently scripted entry (5,8). Candidate lower native tile (5,12) has been checked walkable with routes to leader and exit assistant in original Rustboro Gym 11×20 map. Test in Delta. Retain A/Yes manual leader challenge and a safe visible exit; other eight bosses require individually verified physical staging.
- Completion/failure state: real-time full enemy-party replacement (not one-KO clear), recovery only at promised points, one capped 10% penalty, proper rank unlock, named gifts, clean return door, optional safe withdraw and persistent records. Preserve Regirock last and original Emerald Arena engine.

## V10.2 must-ship C: eight actual standout tower/boss experiences

**Overworld and battle arena are distinct renderers**: a new Gym map/foyer does *not* change the actual combat backdrop/props automatically. Every one of eight needs distinct facade+foyer+approach, boss banner/dialogue, actual native Arena stage, one readable interactive environment mechanic, and a real reward ceremony. No fake labels or palette swaps counted complete.

Suggested native art/logic reuse, pending actual gameplay/VRAM/OAM verification:

| Tower | Visual identity | Real-time counterable battle feature (design target, not yet implemented) |
|---|---|---|
| Bronze | stone quarry -> Regirock amphitheater | destructible pillars/rock cover, telegraphed heavy slam |
| Gale | high terraces -> Lugia cloud-ring | predictable lateral gust lanes, dodging across safe gaps |
| Verdant | canopy -> ancient tree sanctuary | regrowing vine/wood cover with sunlight/heal tradeoff |
| Phantom | graveyard -> crypt | visibility fog/smoke and decoy tells, never blind unavoidable damage |
| Inferno | foundry -> volcanic furnace | warning-lit heat vents, safe lanes; flame/water reaction |
| Tidal | shallows -> Kyogre flood stage | existing rain/flood and freeze/electric conduction with visible tells |
| Thunder | rooftop -> Zapdos reactor | timed shock pulses/pylons with groundable safe zones |
| Astral | crystals -> Rayquaza observatory | destructible/moving psychic crystal cover with anticipation |

Most stage backgrounds and elemental mechanics already exist upstream, but eight **finished** interactive packages do not. Prefer recombination of 17 native stage backgrounds, seven original physics props and existing effects/sprite sheets over eight new huge art packs. Distinct battle visuals must be actually shown in mGBA/Delta with side-by-side screenshot tests. Reduce reuse of same psychic boss scene for Phantom/Astral. Prioritize reliable telegraphs and counterplay over sheer particle count.

## V10.2 must-ship D: character, team and town

- Functional in-world **Wardrobe** with real, selectable and persistent native character graphic/palette presets; preview, choose, cancel, revert, maintain overworld and battle-facing consistency where supported. Do not substitute a Name Rater or menu-only dialogue. Avoid claiming full new trainer art without checking asset and RAM costs.
- Improve Lab: player can view owned/locked roster (80 starters+64 towers+25 Championship+18 Masters), first-clear progress, type/team roles; party sorting, quick 4–6-mon saved squad presets if save layout permits, transparent restrictions and safe PC path.
- Preserve the user-approved native-clean West/East city. Verify actual roofs, windows, signs, water/planting/doors on iPhone; no floating tiles, fake NPCs, save traps or new big palettes. Add subtle native touches (banners, doors, lamps, NPC dialogue), not random new bitmap replacements.
- Good small add-ons: a free nature/EV **respec** option (with actual stat update), career log/clear record/medal counters, boss preparation readout (floors left, healing, next leader/legend, reward) and a clear loss fee display.

## Engineering feasibility gate (before labeling V10.2 near perfect)

- Last V10.1 link: **55,422 bytes ROM free**, **2,155 bytes EWRAM free**, **1,876 bytes IWRAM free**. These are link figures, not peak-runtime guarantee. Reclaim ROM/RAM space *before* new UI data or rich arena effects. Compress/pool legal move tables, use native scratch buffers and existing tilesets, avoid bloating EWRAM/OAM. Do NOT simply attempt to exceed a 32MiB GBA ROM.
- Action plan: (1) source legality/profile coverage matrix for 187 species; (2) implement real four-slot Studio and learnable/profile system; (3) movement and physical boss entry corrections; (4) one fully polished Bronze boss package and reusable themed environmental logic; (5) replicate and test all seven other towers plus Championship/Masters; (6) trainer customizer/town/quality of life; (7) memory headroom and full regression.
- Hard stop: no friends-beta or `V10.2-FULL-TEST-CANDIDATE` label until compile and smoke test of all core areas; record unresolved moves/towers and explicit user decision if deadlines require a partial version.

## Longer playtest release acceptance

- Each of the **63 career encounters** may be played end-to-end; 1v1 active at a time, party replacement and actual full boss party, signature legendary last where designed, rest checkpoints and returns. Verify on Delta and at least a representative mGBA smoke.
- All 187 species grants/unlocks exactly once, correct move legality and slot changes retained through save/reload; full-PC cases cannot corrupt a save.
- Screenshot/video **eight actual overworld boss chambers and eight actual combat arenas**, not source-generated stills; verify A/Yes and Master/intro staging, no random out-of-place helper.
- Loss at zero/normal/high wallet, Bag items, no heal/paywall, player switching, L/R+A+B, abilities, PP, status, cooldown/interrupt mechanics, original sprite scale, stable framerate.
- Verify town and Wardrobe artwork at correct GBA sprite scale; accept original pixel-art look rather than introducing blocky mismatch.
- **Status of this file:** roadmap specification only, not proof any listed new V10.2 feature was committed or compiled.
