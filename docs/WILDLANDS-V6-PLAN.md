# Pokémon Wildlands V6: build list (from the V5 playtests, 2026-10-11)

Base: wildlands-v5 (V5 ROM run 38181288381; fixes after it ship in V6).
Every item is verified in the mGBA harness (PASS / NOT RUN reported per item); Delta playtest is the owner's.

## A. Playtest fixes (gameplay)
A1. Out of PP never drops a match into the classic turn-based battle (Struggle instead); a won match heals the party in the Lab. [done in 26357c2]
A2. Sprite size from the art: small PMD frames (Zapdos) scale up toward a Pokédex-height target. [done in b1f7e99]
A3. Legendaries never retreat or leave their lair; they press harder at low HP.
A4. Lair entrances: replace the Lugia treetop huts with one obvious open-ground entrance and a map marker; audit every lair entrance and door for large Pokémon snagging.
A5. Water: Flying types (and Levitate) fly over water; Water types swim; swimmers are slower in deep water so water is not a free escape; more crossings.
A6. Loot never dead at the cap: cap raised to +3, a capped pickup turns into a team heal; plus a PP-restore pickup.
A7. Rest regen: a duo that stands still and does not attack for 3s heals slowly (not in the storm).
A8. Random player spawn per match on legal ground away from lairs and other duos.
A8b. Dynamic storm: the first circle is offset to a random side each match (on top of V5's random later circles, lair hot zones and the 2:30 opening).
A10. Roster movesets: every roster Pokémon starts with Arena-supported moves only (same loadout rule as the AI duos); the coach and move editor offer only supported moves (playtest: Zapdos had moves it could not use).
A9. Enemy AI (playtest: backs into a wall and stands there shooting; runs sometimes, camps other times): no backing into walls to stand and shoot (firing spots need an exit; strafe while firing). Partner AI: tighter follow, smarter target choice, out of the storm, never stuck.

## B. Duo control and information
B1. SELECT swaps you into your partner (short cooldown); the AI takes the other. L/R keep cycling moves and L+R keeps the ball throw; SELECT's old party/bag shortcut goes away with the Lab coach (C2).
B2. Bigger partner HP panel (name, HP).
B3. TEAM page in pause: both members, moves and PP, buffs vs cap, legendary partner, kills and pickups, foe buffs.
B4. LOG page in pause: last ~12 events with match time.
B5. Storm on the map: everything outside the current circle shaded red, the next (closer) circle outlined, phase and timer, arrow to the safe edge, lair status.

## C. Systems
C1. Status effects in real time for all four battlers (burn and poison tick, paralysis slows and stalls, sleep and freeze timed with fire thaw, confusion aim drift), status icons, status-cure pickup.
C2. Lab coach NPC: pick your duo, set moves (Arena-legal only), controls card, start; no START menu or bag needed in the Lab.
C3. Shiny Pokémon (rate to decide; default 1/64 for the BR so they are seen).
C4. End-of-match summary (placement, kills, damage, legendaries, time); spectate the nearest duo after elimination.

## D. Performance and world
D1. 60 fps while exploring (off-screen sprites out of sort and animate, off-screen work at half rate, hot collision in IWRAM); even 30 in heavy fights.
D2. Map polish toward overworld immersion: cleaner edges and transitions, fewer blocky single-tile rocks, natural decor, fewer stray islets, landmark review.

## Open
- Floor items reported as "little shiny things": no screenshot yet; recheck in V6 captures.

## Progress (WildLands Beta V6.1, 2026-10-12)
Shipped in V6.1 (all smoke-verified, island 148/148, slice 46/46):
- A1-A10, B1-B5, C2 Lab COACH, C3 shinies, C4 summary card, D2 first pass (rounded masses, tall grass).
- Status: HUD tags, supplies cure, burn/poison KOs routed through the squad. Partners are status-immune.
- Breakable cover: arena prop sets incl. ruins (columns in colonnades, obelisks, urns), 7 streamed slots, Psychic throws rocks/columns.
- Roaming legendaries: one dog, bird and Regi per match, staggered spawns in the circle, join when beaten; removed from the PC.
- Biome weather: desert sandstorm (Rock/Ground/Steel +20%), volcano ashfall (Fire +20%), storm rain outside the circle (Water +20%, Fire -20%).
- Bosses: Mewtwo moved to Terra Cave; all five bosses on screen at lair entry (audited, <= 180 px).
- Post-win heal fixed; loss heals via whiteout.
Open: C4 spectate, D1 60 fps exploring, partner status, cliff/biome-belt straightness, EWRAM headroom (~20 bytes left).

## V6.2 (2026-10-12)
- Status (all four battlers): PAR 3s stun, SLP 4s (hit wakes), FRZ 5s (fire thaws), PSN 30s, TOX 60s, BRN 40s; DoT every 5s; no rest regen while PSN/BRN; one status, 5s immunity, legends half duration; HUD tag + countdown; supplies cure.
- AI: enemy duos strafe around targets, back off when outnumbered; partner steps out of the player's line of fire once in range, tighter leash when the player is hurt; bosses telegraph a slam every 7s (5s enraged; roamers 9s) with knockback, enrage once at half HP.
- Map: rounded coastline, oval oases, rounded tall grass, denser stone/sand features; full-island render in evidence (world-half.png).
- 60 fps: measured walking updates at ~1.3 vblanks; adaptive 60 overran repeatedly, parked behind WL_FAST_PACE=0. Needs a ~30% per-frame cut (top costs: AI type values, circle fills, sprite sort, frame decode).
- Memory: debris pool 32 -> 20 (EWRAM 99.90%).
Open: 60 fps optimisation, biome-belt straight borders, spectate, partner-shot coverage in the slice.

## V6.3 (2026-10-12)
- No EXP popup in the Lab; bosses and roamers never rest-heal; breakable props removed (FPS); partner flat-sprite fix (shared OAM matrix); boss slam uses fixed Strength/Stomp.

## V6.4 (2026-10-12): 60 fps
- WL_FAST_PACE=1: the world renders at 60 fps exploring and fighting. Sim stays vblank-timed, so game speed is unchanged.
- Fallback: leaky bucket (overrun +4, fit -1, >=16 drops to 30 for 4s). Only a sustained >20% overrun rate falls back.
- Cuts: one-pass world OAM build (27 -> 8 scanlines), lean sprite animation, coarse collision bitmap, route memo, periodic AI/route/loot/target work staggered across frames (was all on frame 0 mod 8), per-frame type-chart memo, direct move-profile index, aim LOS every 4th render, wing palettes blend only while flashing, corner-assist cache.
- Smoke (run 38251237090): biome tour 1546 updates at 60 / 63 overruns; forced-60 fight 291/300 (9 overruns); heavy late-match walk 252/300 at 60 (auto pacing 256/42). Island 175/175, slice 45/45.
Open: spectate, biome-belt straight borders, heavy late-match walk still ~16% overruns (SolidCircle, frame decode, CB2 inline).

## V6.5 / V6.6 (2026-10-12)
- V6.5: hit flash, Rollout squash, damage numbers and sparks advance at a steady 30/s (they ran double speed at 60 fps).
- V6.6 bosses: legendaries hunt the nearest player Pokemon (no retreat, loot or wandering), press closer when hurt, never pick Teleport, healing or draining moves.
- V6.6 loss: a lost match ends the battle directly (outcome LOST, like a capture), so no classic battle screen can appear before the Lab.
- V6.6 wings: move choice by power x type value x range (cached, re-scored on target/range change and every 16 frames); sidestep incoming shots (odds by level); partner covers a hurt player (<40%); hurt wings fight from the edge of their range.
- V6.6 map: sea islets removed, 1-6 cell specks on open desert/highland ground removed (35% of lone rocks kept), noise-driven bays and capes on long straight coasts.
Open: spectate, boss/AI feel from playtests, "enemy team stuck" repro (no capture yet).

## V6.7 Beta (2026-10-12): ready for testing
- Backend cleanup only, no gameplay change: CI now fails on any failed smoke check (ROM/evidence still upload); dead breakable-prop pipeline removed (props_apply, arena_props, render_props, prop-site table); OAM wrapper simplified; stray .pyc untracked.
- Build: run 38259663834, commit b42e7ad, island ROM sha256 261aefb7...d37e. Island 175/175, slice 45/45.
