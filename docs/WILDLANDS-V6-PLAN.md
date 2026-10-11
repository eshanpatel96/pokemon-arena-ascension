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
A9. Enemy AI: no backing into walls to stand and shoot (firing spots need an exit; strafe while firing). Partner AI: tighter follow, smarter target choice, out of the storm, never stuck.

## B. Duo control and information
B1. R swaps you into your partner (short cooldown); the AI takes the other.
B2. Bigger partner HP panel (name, HP).
B3. TEAM page in pause: both members, moves and PP, buffs vs cap, legendary partner, kills and pickups, foe buffs.
B4. LOG page in pause: last ~12 events with match time.
B5. Storm on the map: danger zone shaded, phase and timer, arrow to the safe edge, lair status.

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
