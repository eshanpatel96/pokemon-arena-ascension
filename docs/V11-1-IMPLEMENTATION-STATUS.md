# V11.1 implementation checkpoint

The user approved the full V11.1 Beta build, explicitly including town redesign and AI Pokemon moves. The approved final build list remains the acceptance contract. This development checkpoint is NOT the complete Beta and does not defer or close remaining requirements. Final delivery is a matching standalone .gba and shareable .zip once the approved release gates are supported.

## Verified save/Continue milestone — 9 October 2026

Independent Ubuntu mGBA CI verification succeeded:
https://github.com/eshanpatel96/pokemon-arena-ascension/actions/runs/37961032296

- Tested ROM is the unchanged first-slice build from source c9166a82bf701f44fd17e4f500afab8a1dac868c, produced by run 37959084673.
- ROM SHA-256: 93e6a36e7f3b85dc6c6328b4f479bb264ef9ecfbb8ab08b053ca786531a36770; padded size 33,554,432 bytes.
- Corrected test runner source: a61a291d68b8b3a09916b3d07ba5cc3b0a64711f. Independent validation workflow source: da153aec48acd93428e7bc9bca015c766f543154.
- Passed normal key-input tests: Shadow Lugia title, visible no-SELECT New Game, fresh city/six-member party, native SAVE counter, no damaged sectors reported, full 128 KiB save export, native valid-save recognition, Continue to same city, decrypted money and all six party structs preserved.
- Restart test waits until the native confirmation task accepts input, then B cancels. Continue works afterwards; party and complete Flash bytes remain unchanged.
- A SECOND emulator host process loads the actual exported .sav file and uses native Continue. Map and party count match, and exported Flash bytes remain identical. All 14 native save section IDs occur in a complete slot.
- Local pinned headless mGBA 0.10.3 also passed the same 14 auto assertions, 3 separate-process assertions and file comparisons before CI.
- The run's V11-1-SAVE-CONTINUE-PROOF-NOT-RELEASE artifact contains actual 240x160 framebuffer captures, both logs, generated test save files, exact runner and result.json. These are fresh test fixtures, not the user's main save.

### Root cause and test correction

The host runner omitted mgba/flags.h before mgba/core/core.h. The distribution library enables USE_DEBUGGERS, changing struct mCore's function table. savedataClone was at offset 5408 with the correct Ubuntu headers/flags, versus 5352 without them. Including the correct flags fixed the false export failure. Merely attaching an erased Flash file was not sufficient. No ROM save-code change was needed for this result.

The old fixed-delay B input also arrived before the restart warning finished printing, so it was ignored. The corrected test observes the native task's input-ready state before pressing B and verifies Continue and full-party preservation after cancel. No RAM writes, bypasses or waived failures are used.

**Scope limit:** this closes only the demonstrated fresh-city save/Continue/cancel smoke. It does NOT certify arbitrary V10/V11 saves, interrupted/corrupt/backup recovery, all career/reward/service states, the complete 63 encounters, full legal moves or iPhone Delta. Keep the original versions and saves backed up.

## Preserved baseline

Branch v11-tower-redesign at c4aa718c2b816956530ff0370beb0cd7b3a8b1e3; compiled V11 game 54ebd5c1ea335474ebd7ffb826d6349f00a39e3d, ROM SHA-256 9dd86e04c4503b4969cd4000175631c09a205621db6a027bea83e075c77a4e58. Preserve that ROM and previous saves separately. Work remains on v11-1-beta, not main.

## First implemented game changes

- Career-only tactical move scorer accounts for range, move windup/recovery, repetition, low HP and five existing styles. Bait/counter bonuses require line of sight and unobscured observed commitment. Native move effects, PP, cooldowns and player controls are not changed.
- Score water/electric/fire absorption as ineffective; prevent style bonuses from promoting rejected actions. Protect can be useful against a visible committed opponent, rather than always treated as an unsupported setup.
- West campus first geometry pass: 90 native paving tiles, central directory and real Style House sign. Same map size, all eight existing door/warp definitions, 16 NPCs and existing art. This is the FIRST campus pass, not complete town architecture or interiors.
- Protected title/menu, career/team/reward and save-layout files checked by hash. No species, move profile or saved field added in this slice.

Static/unit evidence: patch on the exact assembled V11 source passed doorstep reachability for all eight west doors and checks preserving actor/warp definitions. The pure C scoring helper passed 58 assertions. These are NOT in-game battle or Delta acceptance. Native source city renders were inspected; they are not emulator captures.

## Still required before full approved V11.1 Beta

Remaining town architecture/services; 13-room boss framing/clipping and thematic combat mechanics; original-80 preload/rewards-only Birch; full legal move behavior and Box selection; nature/EV respec; older-save and corrupt/backup/recovery coverage; full campaign progression/rewards/Bag/switching; measured AI battle choices and performance; actual iPhone Delta acceptance. The tested title/start and ordinary battle positioning must be preserved while repairing separate boss visibility defects.

Do not relabel this first-slice compilation or the new green save test as the final V11.1 Beta. Reconcile each approved feature against implementation and evidence before packaging the .gba/.zip; no silent omissions or V12 deferrals.
