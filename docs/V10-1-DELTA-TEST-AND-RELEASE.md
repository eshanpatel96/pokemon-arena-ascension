# V10.1 Compiled Development / User-Tested Fixes

**Gameplay scope:** keep 50 tower encounters, five Championship rounds and eight Masters rounds, all from original Emerald Arena 0.13.0. The user reported one **successful Bronze boss fight** in V10; this does **not certify** the other seven tower bosses, five Championship rounds or Masters Circuit.

## Verified build, October 8, 2026

- Source commit (exact compiled code): `6840ea411b3a9a4e799b25206f39e4193dc376fa` on `v10-1-polish`.
- GitHub CI: https://github.com/eshanpatel96/pokemon-arena-ascension/actions/runs/37855729085 — **SUCCESS**.
- GBA ROM artifact: https://github.com/eshanpatel96/pokemon-arena-ascension/actions/runs/37855729085/artifacts/11583649025 (inherited naming `Ascension-V9-DEV-UNTESTED-GBA`, **actually V10.1 source**).
- Verified output: **32 MiB** Emerald `BPEE` ROM, raw SHA-256 `7cb9cd91cd9faea923ddd905a729e893a55296ae83b8ed3380445d27eb541b86`.
- ROM linker `33,499,010 / 33,554,432 B` (**55,422 free**); EWRAM `259,989/262,144` (**2,155 free**); IWRAM `30,892/32,768` (**1,876 free**).
- Source static checks, all 9 boss map routing checks, 187-species allocation, map art checks, 4bpp PNG palette checks, native map generation and GBA linker passed. **No mGBA/Delta runtime regression recorded for V10.1.**
- Private ZIP in conversation: `Pokemon-Arena-Ascension-V10.1-Delta-DEV.zip`, includes correct `.gba`, focused test notes, checksum and clean city previews. Keep older ROM/save separately.

## Implemented fixes relative to compiled V10

1. **Ordinary tower ceremony — structural source fix** (`bootstrap/v10-1-court-choreography.py`):
   native 10×9 Tower battle chamber, Master at (5,5) walks left/down to (4,6) and remains visible; player stages left at (3,4), challenger walks from (5,1) to right court (7,3); challenger returns/vanishes after whole-team victory; Master walks to (3,5) directly below player to offer advertised heal/checkpoint then returns to side. Stage is reset by scripts. No new renderer.
2. **Selectable stat training** (`bootstrap/v10-1-training-services.py`): the city training NPC offers choose-party Pokémon and then choice of HP, Attack, Defense, Speed, Special Attack, Special Defense. Each free session applies +16 native EVs, capped at 252 per stat and 510 total, then recalculates stats. Generic practice remains accessible.
3. **More functional Move Studio**: choose a party Pokémon then restore the original supported baseline or specifically select a native Arena drill: slot 4 Protect (guard), slot 3 Double Team (evasion), slot 2 Swift (ranged). These three are engine-supported original moves, not full individualized 187-species canonical learnset editing.
4. **Pixel-art correction** (`bootstrap/v9-city-architecture.py` + `bootstrap/v10-1-native-town-polish.py`): remove earlier single-shade partial-palette roof recolors for two service houses; preserve full Emerald-native roof shading and borders, retain functional Lab signage, storefronts and native landscaping. The **first attempted palette-reversion render had roof defects** and was rejected **before shipping**. The final source-rendered Western town shows corrected intact original roofs; East is unchanged. GBA native 16-pixel metatiles remain pixel art, not high-res assets.
5. **Bronze boss attendant**: source swaps the out-of-place generic Gentleman exit helper for a native Hiker suited to the stone tower. Other eight helpers use themed native NPCs. All keep an exit/decline option. Their presence is intentional to avoid one-way trapped boss rooms.

## Specific quick test to run before accepting V10.1

- **Fresh save, West City:** walk near Lab, Supply Shop, Move Studio; confirm no broken roof strips, cut-off signs or blocked paths.
- **Town training specialist:** select your Pokémon, select **Speed**, verify success, try another focus, try maxed focus and cancel. Check save/quit/reload keeps improvement.
- **Move Studio:** choose Pokémon and Protect/Double Team/Swift drill; verify selected move slot, use move in Arena battle, cold reload.
- **Bronze ordinary tournament:** Master steps to side; player walks to LEFT of court, opposing challenger to RIGHT. Verify no NPC collision. After defeating entire opposing party, rival walks out and new one enters. Master visibly steps in for recovery and steps back out.
- **Bronze leader:** press A to accept (not entry auto-trigger); Regirock last; new Hiker should provide safe exit; win, claim once, save/reload.
- **Loss:** charge 10% max 1,000 once and return safely; check no duplicate prize.
- **Other bosses and later tiers:** do not infer from Bronze victory; individually verify Gale/Verdant/Phantom/Inferno/Tidal/Thunder/Astral, five Elite + Ho-Oh, and all eight Masters including recovery/18 prizes.
- **Native controls:** L/R selecting moves, A attack, B dodge, START Bag, party switch, HP/faint/PP/status and no turn-based fallback.

**Release status:** V10.1 DEVELOPMENT, **not friends-ready yet**. Fix any runtime positioning or text defects, pass representative end-to-end Delta/mGBA testing and ensure saves/performance before friend distribution. ROM and RAM are almost full. Full custom move picker, nature respec, wardrobes, and unique interactive native boss hazards still need development; do not silently claim they shipped. Original V10 friends-beta acceptance checklist remains controlling.
