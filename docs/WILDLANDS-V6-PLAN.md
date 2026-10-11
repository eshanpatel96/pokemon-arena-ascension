# Pokémon Wildlands V6: build list (draft from V5 playtests, 2026-10-11)

Base: wildlands-v5 at c00d296, run 38181288381 (island 107/0, slice 46/0).

## Performance
1. 60 fps while exploring: cull off-screen sprites from sort/animate, run off-screen work (30 duos, loot, storm upkeep) at half rate, move hot collision code to IWRAM. Fall back to an even 30 only in heavy fights.

## Movement and water
2. Flying types (and Levitate) fly over water; Water types keep swimming; everyone else uses fords and bridges.
3. Rebalance swimmers so water is not a free escape (slower swim speed or no firing while submerged), and add more crossings.

## Duo control and info
4. R swaps you into your partner (short cooldown); the AI takes the other.
5. Bigger partner HP panel (name and HP, matching the main bars).
6. TEAM page in pause: both members, moves and PP, buffs vs cap, legendary partner status, kills and pickups, foe buffs.
7. Match LOG page in pause: last ~12 events with match time (eliminations, legendary attacked or taken, pickups, storm phases, your KOs).
8. Storm on the map: shade the danger zone, phase and timer, arrow to the safe edge, lair status (alive, attacked, taken).

## Loot and healing
9. No dead pickups at the cap: raise the cap and turn a capped pickup into something useful (heal or PP), plus new loot types (PP restore, shield, speed burst).
10. Rest regen: a duo standing still and not attacking for ~3s heals slowly (not in the storm).

## AI
11. Enemy AI: stop backing into walls and standing still while shooting; pick retreat and firing spots with an exit and strafe while firing.
12. Partner AI: tighter follow, better target choice, stays out of the storm, never stuck on scenery.

## Map
13. Polish toward overworld immersion: cleaner edges and transitions, fewer blocky single-tile rocks, natural decor, fewer stray islets, landmark placement review.

## Features
14. Shiny Pokémon (rarity to decide).
15. End-of-match summary; spectate after elimination.

## Open from V5 testing
- Floor items reported as "little shiny things": waiting on a screenshot.
- Legendary encounter: owner playtest pending.
