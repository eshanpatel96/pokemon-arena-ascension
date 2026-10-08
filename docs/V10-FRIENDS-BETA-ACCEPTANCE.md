# Pokémon Arena: Ascension — V10 Friends Beta Acceptance

**Scope decision, 8 October 2026:** The user wants a **near-ready V10 game to share with friends**. Include **Masters Circuit**, the completed eight towers and five-round Championship, corrected manual boss approaches and visible Tower Masters, clean/tidy central town and gameplay reliability. Final polish/shinies/extra modalities may follow, but must be tracked rather than silently dropped.

## Status and labels

**Source development branch:** `v10-friends-beta` and [draft PR #8](https://github.com/eshanpatel96/pokemon-arena-ascension/pull/8). **Never merge or label fully playable solely on code or CI.** Current V9 source built in [CI 37846797245](https://github.com/eshanpatel96/pokemon-arena-ascension/actions/runs/37846797245); V10 acceptance requires a separate successful source SHA / GBA ROM hash and emulator tests.

### Implemented V10 source candidates — runtime acceptance still open

- `bootstrap/v10-boss-approach.py`: nine physical rooms (eight tower leaders and Champion), walkable native metatile entry and boss locations, reachable gatekeeper NPCs; leader battles start **only after A interaction and Yes**, with No and attendant exit; no automatic on-frame boss fight; native 1-active-per-side Emerald Arena retained.
- Regular tower flow: Tower Master steps left and **remains visible sideline**; directly offers checkpoint healing from outside the fighting lane; opposing challenger walks into a cleared lane, is defeated, walks out; Master returns to central position at reset.
- `bootstrap/v10-masters-circuit.py`: eight post-Champion native trainer-party battles with six opposing Pokémon, tougher variation, one full-heal checkpoint after round IV, defeat resets tournament and deducts only one native fee; permanent best-cleared round tracks **18 original animated Masters species** through one-time flags claimed at Lab. Current Masters uses the original Summit chamber; later distinct arenas/flow depth may be needed before friends beta.
- `bootstrap/check-v10-friends.py`: all nine player entrance/leader positions and route connectivity validated against the exact 16-bit original layout collision bits, reachable exit NPCs, preserved actual warps, one manual fight trigger, 187 total original animated species, image tile/4bpp/palette-range checks, and clean original native city-tile rendering for West + East districts.
- The original V9 compilation currently includes eight career towers (4/5/5/6/6/7/8/9 = **50 fights**) and Championship five rounds, **169 one-time obtainable species**. Masters adds eight fights and 18 species for **63 total staged fights/187 species**; **none** of the Masters implementation has been gameplay-validated yet.

### Hard acceptance gates before inviting friends

[ ] GBA source static checks + ROM link + verified 32 MiB BPEE header + SHA; measure ROM and EWRAM/IWRAM.
[ ] Fresh save/Delta + mGBA boot, movement, L/R selected attack, A, B+dodge, START Bag, party switch, zero PP, faint/replacement; no accidental turn-based fallback.
[ ] Play a complete Bronze 4-round run, watch Master step aside, remain at sideline, intervene at heal stage; challenger spawn/exit and trainer pictures match.
[ ] Eight boss rooms: fresh arrival on walkable tile; physically approach leader; cancel safely; press A and Yes only when ready; boss six-member/five-member team appears one at a time; signature legend last; defeat + fee + recovery; clear + reward; exit and save.
[ ] Championship Elite I Articuno, II Registeel, III Raikou, IV Regice, World Champion Ho-Oh with six real foes each, healing after II/IV, return after loss starts from I, claim 25 unique earned licenses.
[ ] Post-Champion Masters unlock; complete eight six-Pokémon rounds, checkpoint once after IV, loss/restart/replay, claim **18 once-only** species; no conflict with other 169.
[ ] Free basic Lab recovery, shop items and native in-battle Bag; money and loss fee persisted, no accidental duplication from rematch.
[ ] Original 80/64/25/18 species allocation uniqueness, every offered Pokémon has supported battle animations/moves. Verify team composition and tactical move mix, not just compiled moves.
[ ] Town West and East on-device visual review: normal roof/metatile/palette seams, signs, LAB, shop, room doors, landscape, water, NPC walkers, entrance collision and warp returns. Preview overlays (red square, yellow numbers) are **not actual game tiles**.
[ ] Long-session 63-fight walkthrough, save/cold reload and repeated bonus fights; performance on target iPhone Delta, no crashes or serious frame drops.
[ ] Prior-save policy documented; fresh save recommended until compatibility proven. Actual user/friend feedback logged and blockers fixed before friends-distribution label.

### Known limitations as of starting V10 source pass

- None of these source fixes automatically guarantees on-device visual polish. The original Emerald Gym/Frontier room tiles are reused for the nine leader overworld arenas, and some backgrounds differ only via existing stage choices.
- The central city has a themed native Lab/shop/studio/flower court and other towers, but it's not a wholly original finished 8-theme sprite/art pack. ROM at V9 nearly full (~57 KiB left); heavy asset expansion is risky without reclaiming space.
- A physical walk-up route on native map collision bits isn't gameplay proof; each room must be walked and its NPC interaction tested in an emulator.
- Masters currently uses Summit tournament space, not eight standalone custom rooms.
- Recheck every user-requested V9/V10 acceptance item in `docs/V9-FEATURE-ACCEPTANCE-CHECKLIST.txt`, including advanced move editor/training/wardrobe and real unique arena hazards. Do not silently call missing features completed.

**Testing and distribution rule:** A build can be labeled `V10-DEV-UNTESTED` after passing CI; `V10-FRIENDS-BETA` only after the tested acceptance gates above have evidence. Friend feedback means testing the actual game, not discovering known blocked boss maps or broken save logic.
