## Verified compiled V10.2 development milestone — 9 Oct 2026 UTC

**Source SHA:** `c879a1c90d37bff86f8733d4ad06c19eaf9e5059`  
**Successful Actions CI:** https://github.com/eshanpatel96/pokemon-arena-ascension/actions/runs/37868101102  
**Original ROM artifact (name inherited from V9 pipeline):** https://github.com/eshanpatel96/pokemon-arena-ascension/actions/runs/37868101102/artifacts/11588668631  
**Extracted ROM:** 33,554,432 bytes, BPEE, SHA-256 `cd03bd4c5dce2651e69c7d813c741d572d1c28180a4dd1c58d8e5c511c4cd705`.  
**Linked capacities:** ROM 33,506,952 bytes / 33,554,432 (**47,480 free**); EWRAM 259,990/262,144 (**2,154 free**); IWRAM 30,892/32,768 (**1,876 free**).

**New source features compiled:** real native four-slot Move Relearner UI filtered by Pokémon-specific legal moves and real-time support; player center/Master lower; Bronze boss entry lower; Astral distinct actual Arena backdrop; original boss physical cover differences; nine themed boss introductions; native saved five-choice Wardrobe and still-working-in-source Name Rater. These are **not gameplay certified** until Delta/mGBA tests.

**Hard gap:** 88 native selectable Arena move profiles support **3,051/8,776** audited species-move combinations; **5,725** pairs are missing realtime move behaviors. Native four-slot UI is coded, not full any-legally-learnable-move availability. No direct Box browsing from Studio, only party selection. Eight physical boss stages reuse existing native art; full custom art/hazards and trainer sprite variants need actual Delta visual review. Friends beta remains unapproved. Original long-test ZIP in ChatGPT contains ROM, complete move coverage audit, and test notes.

---

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

## Wardrobe and boss-cover implementation

The five native avatar sprite choices and eight original Arena boss-cover configurations have now **compiled successfully** in build `c879a1c`; **in-game appearance, persistence, physics and device performance remain unverified**. Full skin/hair customization, bespoke boss-room architecture and original artwork still require further development and memory headroom.

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
