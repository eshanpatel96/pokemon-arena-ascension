# V11.1 implementation checkpoint

The user approved the full V11.1 Beta build, explicitly including town redesign and AI Pokemon moves. The approved final build list remains the acceptance contract. This first code slice is NOT the complete Beta and does not defer or close remaining requirements.

Baseline: branch v11-tower-redesign at c4aa718c2b816956530ff0370beb0cd7b3a8b1e3; compiled game 54ebd5c1ea335474ebd7ffb826d6349f00a39e3d, ROM SHA-256 9dd86e04c4503b4969cd4000175631c09a205621db6a027bea83e075c77a4e58. Preserve this ROM and previous saves separately.

First implemented changes:
- Career-only tactical move scorer accounts for range, move windup/recovery, repetition, low HP and five existing styles. Bait/counter bonuses require line of sight and unobscured observed commitment. Native move effects, PP, cooldowns and player controls are not changed.
- Score water/electric/fire absorption as ineffective; prevent style bonuses from promoting rejected actions. Protect can be useful against a visible committed opponent, rather than always treated as an unsupported setup.
- West campus first geometry pass: 90 native paving tiles, central directory and real Style House sign. Same map size, all eight existing door/warp definitions, 16 NPCs and existing art. This is the FIRST campus pass, not complete town architecture or interiors.
- Check protected title/menu, career/team/reward and save-layout files by hash. No species, move profile or saved field added in this slice.

Local evidence: patch on the exact assembled V11 source passed static doorstep reachability for all eight west doors and checks preserving actor/warp definitions. The pure C scoring helper passed 58 assertions. These are static/unit tests, NOT in-game battle or Delta acceptance. Native source renders were inspected; they are not emulator captures.

Still open: remaining town architecture/services, 13-room boss framing/clipping and thematic combat mechanics, original-80 preload/rewards-only Birch, full legal move behavior and Box selection, nature/EV respec, save/cold-Continue/restart tests, campaign progression/rewards/Bag/switching, measured AI battle choices and performance, and all Delta acceptance. The original save-export test failure is not silently waived. Do not relabel a compilation checkpoint as final V11.1 Beta.
