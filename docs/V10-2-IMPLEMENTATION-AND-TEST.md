# V10.2 — Implementation checkpoint and expanded-test plan

**User scope (8 October 2026):** V10.2 should become the larger near-complete test campaign with genuine Pokémon-specific four-slot move teaching, meaningfully distinct boss experiences, finalized Master/player movement, native character customization and a stable town. V11 is post-Masters expansion and should not silently inherit broken V10.2 systems.

## Build evidence

- Last stable V10.1: source `6840ea411b3a9a4e799b25206f39e4193dc376fa`, [success CI 37855729085](https://github.com/eshanpatel96/pokemon-arena-ascension/actions/runs/37855729085).
- V10.2 branch `v10-2-full-test`, [draft PR #10](https://github.com/eshanpatel96/pokemon-arena-ascension/pull/10).
- **Never call V10.2 a tested/finished ROM without an exact successful build source SHA, raw GBA checksum and recorded Delta/mGBA gameplay.**

## Changes currently connected to build

**Move Studio:** `bootstrap/v10-2-real-move-studio.py` uses native Emerald `TeachMoveRelearnerMove` scrolling move chooser/preview and four-slot replacement/cancel screen. A compile-time species-specific legality catalog is generated from native Emerald level-up, TM/HM, tutor and direct egg sources, intersected with actual original realtime Arena profiles. Taught moves really occupy the chosen move slot; old fake Protect/Double Team/Swift-only menu removed. Native caller selects one **party Pokémon**, not arbitrary Box Pokémon yet; PC storage and party transfer remain functional separately. **Important missing scope:** cannot legally teach unsupported moves without implementing their actual realtime move actions. Coverage artifact `V10-2-EMERALD-ARENA-MOVE-COVERAGE` records the full exceptions. Pinned native source presently has 89 profiles (88 excluding Struggle), and source audit counted 3,051 usable vs 8,776 legal species/move entries (5,725 still missing, direct egg moves included). The complete 'any legal move' user requirement is NOT finished.

**Arena positioning:** `bootstrap/v10-2-stage-and-boss.py` stages player (5,4) at center, Master (4,7) lower, challenger (7,3) opposite in original native 10×9 tower chamber; physical recovery step and return preserved. Bronze boss arrival lowered from (5,8) to original Rustboro Gym (5,12), collision-passable with walk-up to leader. Astral no longer shares Phantom's psychic backdrop (uses distinct original Arena stage 12). Boss-specific introductions added to all nine leader rooms.

**Original compiled V10.1 preserved:** 50 encounters across eight towers, five six-Pokémon Championship rounds ending Ho-Oh, eight post-Champion Masters rounds; 187 animated Pokémon, one-time earned licenses, money penalties/shops, native in-battle combat/dodge/Bag, Lab/Move Studio/EV selection and physically valid nine boss approaches.

## Candidate follow-on source once first source build passes

A compact native trainer wardrobe is prepared (5 existing Emerald overworld visuals, saved choice and Name Rater retained); eight physically different boss prop/cover setups are also prepared from the existing realtime Arena obstacle engine with no new graphics sheets. **Do not count these as shipped until integrated/compiled and demonstrated in Delta.** Full skin/hair design, bespoke architecture and entirely new gfx still require memory reclamation and explicit art QA.

## V10.2 gating tests — evidence needed

1. **Bronze court**: Master low, player center, challenger opposite; each trainer walk-in, fight, exit/replacement and Master healing check; no two NPCs on same tile. Videorecord entry/after 1st win/checkpoint.
2. **Bronze boss**: arrival farther down, walkable toward leader and exit attendant, A then Yes initiates, No cancels, Regirock final, money/rewards and return safe.
3. **Native four-slot Studio**: choose Pikachu/Charizard/Sceptile and one unusual species, inspect legal move list, replace EACH of four move slots over four transactions, use resulting moves with L/R+A, verify PP/cancel/save and no unsupported move reaches classic turn mode. Include one species with limited moves.
4. **Training/wardrobe** (if integrated): six EV focuses with real stats, original/alt outfit reverts, persistence across city->tower->boss->reload; no broken NPC sprite/palette.
5. **Nine boss environments**: screenshots of actual overworld chamber and actual realtime Arena stage for eight leaders + Champion; physical hazards should have recognizable, counterable effects; no random helper or missing exit.
6. **Full campaign**: eight towers' correct species/reward/switching and no trapped map warps, Championship Articuno/Registeel/Raikou/Regice/Ho-Oh, Masters 8, 187 species claims unique, healing after Elite II/IV and Masters IV, zero/mid/high money loss, native Bag, performance and cold reload.

## Honest release line

- `V10.2-DEV-UNTESTED`: compiler + static checks pass; available for private exploratory test only.
- `V10.2-LONG-TEST-CANDIDATE`: critical complete functionality demonstrably works in emulator on representative rounds; major unimplemented move legality gaps are explicitly disclosed/approved.
- `V10.2-FRIENDS-BETA`: no known progression blockers, full squad/award/save/Delta test, complete acceptance items or explicit negotiated scope.

Latest V11 roadmap remains `docs/V11-ASCENSION-LEGENDS-ROADMAP.md`: prestige Legends Circuit, shiny cosmetics, medals, Boss Rush and additional challenge modes, not a substitute for V10.2 core acceptance.
