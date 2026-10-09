# V11.1 gameplay-test delivery — 9 October 2026

This is a new compiled gameplay test, NOT completion of the full approved V11.1 Beta. The user explicitly waived expanded saving work as a personal-playtest blocker. The accepted title/menu and native save code were left intact; no cross-ROM Delta-state compatibility is promised.

## Exact build

- Build source: `7eb86415e918e3176b828632322e712f29300d5b` on `v11-1-beta`.
- Successful compile/native capture job: https://github.com/eshanpatel96/pokemon-arena-ascension/actions/runs/37970683816
- ROM artifact `11635657567`, V11-1-GAMEPLAY-TEST-ROM.
- Evidence artifact `11635822083`, V11-1-GAMEPLAY-EVIDENCE.
- Rebuildable packed source artifact `11635467843`, V11-1-PACKED-GAMEPLAY-SOURCE.
- ROM SHA256: `e67d248f1e148924b9eadd6e3229e0d38c1555f01870adda3aa75b416be3d138`, padded 33,554,432 bytes, BPEE.
- Local compiled ROM and independently downloaded CI ROM match byte-for-byte.
- Link totals: ROM 32,855,760 / 33,554,432 (698,672 free); EWRAM 260,034 / 262,144 (2,110 free); IWRAM 30,892 / 32,768 (1,876 free). These are not peak-runtime guarantees.

## New game code, committed and compiled

The previous gameplay-pass document describes the native 13 compact courts, 64-pixel actor separation, geometric floor mosaics, additional campus paving/planter, original starter-catalog batches, Birch rewards/PC flow, legal supported enemy move slots, and confirmed EV reset. A 52-byte temporary ownership index now avoids repeatedly decrypting the entire PC during starter registration. It is not a new save field.

The actual fresh-game test contains six preserved party Pokemon and 80 PC Pokemon, 86 unique species in total. All 80 allocated starter-catalog species are present exactly once; six additional legacy preset species were retained instead of silently removing the familiar starting team. This is not a claim of exactly 80 total Pokemon or final license-gate balancing.

All 17 dry stage images were independently rebuilt from existing PNGs and compared byte-for-byte to the existing flood asset's dry halves before aliasing. 652,800 duplicate raw bytes were removed, with no new runtime decoder or altered stage pixels/palettes. Three embedded native multiboot programs omitted by an earlier archive filter were restored byte-for-byte from the checksum-pinned baseline; hashes are retained in build evidence.

## Tests actually performed

- 58 pure tactical-AI helper assertions passed in CI.
- Static connectivity, doorstep and intermediate actor movement checks passed for all 13 modified rooms and eight west-district doors.
- Actual 240x160 mGBA frames captured from all 13 native rooms. Host fixtures now wait for the real native warp and assert the actual target map, preventing a city screenshot from being mislabeled as a room.
- Actual Bronze walk-up, A/Yes dialogue, both actors at the compact court and transition into native real-time battle were observed. Later historical capture filenames 23-native-attacks and 24-native-movement show the party menu; those are NOT claimed as successful attack/movement tests.
- An additional local headless mGBA 0.10.3 fixture exercised real game functions for starter creation, all 63 team constructors and EV operations. 149 assertions passed: checksum validity, all 80 starter species present, no fresh duplicate species, legal supported new-starter/enemy moves, intended party sizes/final aces, Rayquaza fifth/Ho-Oh last, and training/reset identity preservation. These are debugger-controlled function tests, NOT 63 battles won, normal campaign progression or Delta certification.
- No expanded saving, older-save or corruption suite was added to this release gate. Earlier baseline smoke evidence does not automatically certify this changed ROM.

## Package

Standalone `Pokemon-Ascension-Arena-V11.1-Gameplay-Test.gba` and matching ZIP are prepared. ZIP contains the same ROM, manifest, checksum, readme, actual room/title/Bronze captures, keyed native map-data city reconstruction, and bounded test evidence. The map marks the existing Wardrobe/Style House entrance at (44,5) in the west district. No personal saves/states, font files or credentials are included.

ZIP SHA256: `248bc07d3edb0cd5aab9593621cc1b95561aef1d7a2f80d9b20198c29cf99f3c`.

## Still open — not silently deferred or completed

Full legal move profiles (coverage remains 3,051 / 8,776 audited pairs), direct Box editor, nature service, complete interactive environments, remaining bespoke city/tower architecture and concept fidelity, wider reward/loadout/service/item/switch testing, all normal 63-encounter transitions and actual iPhone Delta testing. This pass legalizes enemy/new-starter slots, not every historical reward preset. The geometric mosaics are early native presentation, not finished literal legendary emblems. Retain all other approved requirements.
