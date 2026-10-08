# Ascension V8 — iPhone/Delta Test Protocol

**Scope:** source-built experimental V8. The current GitHub build may be compiling; do **not** treat this document as proof of successful compilation, Delta playability or completed trainer-party transitions.

## What's genuinely in V8 source
- Native Emerald START menu item **ARENA GUIDE** (visible in a fresh Ascension career), showing current saved rank/floor, next tower, location, and complete 1–9 tower directory.
- Original Emerald tile-backed signs in both districts with tower name, order and geography.
- Better geographic layout: towers 1–4 west, 5–8 east, Summit east north; central-west buildings become a functional classic Pokémon Center/PC Lab, a functional native PokéMart, and separate Move Studio/Style House rooms (their advanced editing tools are NOT implemented).
- Tower Master gives briefing and does not launch fights on conversation. A physically separate Battle Gate room for each tower initiates battles by walking forward into its trigger.
- Bronze Tier source contains a guarded prototype of native TRAINER battle types with **two, three, and four** sequential opponents over the current **three** Bronze floors, four attacks on each foe, and original Emerald Arena real-time graphics/logic. This requires on-device testing of second/opponent Pokémon switching.
- Remaining tiers still use one scripted opponent per floor while trainer progression is stabilized.

## What is NOT yet playable/verified
- Custom grass/ghost/fire/water/weather and special leader battle arenas. V9 production milestone.
- A fourth Bronze floor, full 55-floor campaign, 40–60 species roster management, independent per-move timers, EV/nature editor, trainer clothing customization, Megas.
- Multi-foe concurrent 2v1, or all existing 187 animated Pokémon as fully playable.

## Phone-first QA steps
1. Back up the known-good V7 save; import the new V8 test .gba as a separate game if possible. Highlight NEW GAME then press SELECT for a **fresh** career.
2. Confirm immediate free roaming and readable tutorial/guide.
3. Open START: **ARENA GUIDE** should show current rank, next tower and optional directory. Check its labels after one victory.
4. Check city signs and walk between West and East. Enter 1–4 in West and 5–8 in East; all exits should return to the corresponding city door. Avoid getting trapped in an NPC dialogue loop.
5. Check **Team Lab** PC access and ordinary PokéMart stock. Studio/Style rooms are navigation-only for now.
6. Enter Bronze Tower from the WEST EAST side, talk to Master; conversation shouldn't start combat. Walk through NORTH gate into dedicated native arena room, step toward the challengers.
7. **Most important:** Fight Bronze Floor 1 until the first enemy faints. Expected opponent sends their second Pokémon while game stays in **real-time arena**. Watch for black screen, default turn-based menu, old sprites, stalled animation or skipped next Pokémon.
8. Continue Floor 2 (3 enemy Pokémon) and Floor 3 boss (4 enemy Pokémon) if safe; check HP carries from one fight to next and city recovery is available.
9. Check defeat/retry, rank updates only after the entire opposing roster is down, save/quit and cold reload. Report exact floor/species with a screenshot or brief video if behavior differs.

## Release blockers before calling V8 complete
- Trainer battle party switching/fainting must work on Delta and mGBA with no classic UI regression.
- Bronze should eventually be **four** floors with one clear, fair healing checkpoint and a distinctive boss room/AI pattern, roughly 10–15 minute total challenge.
- City building sign-to-door correspondence, walkable gate tiles, returns and save data must be verified on device.
- Basic move compatibility, credits/healing economy, NPC functioning and ROM/memory bounds must pass tests.

## Delivery policy
Always distinguish **source committed**, **CI compiled**, and **live Delta verified**. A ROM passing a GBA header checksum is not proof of successful multi-Pokémon transitions or game completion.
