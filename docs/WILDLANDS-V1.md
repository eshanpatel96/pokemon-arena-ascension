# Pokemon Wildlands V1 — Vertical Slice

Wildlands is a separate game branch built from the Pokemon Ascension Arena / Emerald Arena combat foundation. V1 is intentionally a field-combat proof, not the final 30-team Battle Royale.

## Locked game rules

- One continuous match. No random encounters and no transition into a battle scene.
- Standard target: 30 teams / 60 Pokemon. Remote-team simulation is deferred until local field combat proves fun and stable.
- Every squad is exactly two Pokemon: the player and one AI teammate.
- Final evolutions form the eventual selectable roster; five legendary Pokemon are world bosses and cannot be selected at spawn.
- Defeating a legendary in the world makes it recruitable. Recruiting it replaces the AI partner rather than creating a third squad member.
- Tall/long grass is concealment, not an encounter trigger.
- Water, flight and burrow are traversal traits, independent of the four combat-move slots. V1 proves partner Surf and a Dig shortcut first.
- No human trainers, ordinary NPCs or ambient wild grass encounters.

## V1 playable slice

V1 reuses Route 119 because it already supplies a long Emerald landscape with river, bridges, tall grass, verticality and multiple tactical lanes. Story/NPC/warp events are removed on this branch while the native terrain remains.

Test squad: Charizard + AI Blastoise. Two enemy duos are spawned into the southern field. Rayquaza is an overworld boss in the northern section. Four item-ball pickups test HP, Attack, Defense and move upgrades.

Controls in the slice:

- D-pad: native Emerald world movement.
- A: use the selected combat move in the facing direction.
- L/R: cycle the four combat moves.
- B + direction: native running plus a short Wildlands dodge/invulnerability window.
- Select: contextual action — pick up nearby loot, recruit a defeated Rayquaza, use partner Surf when facing water, or use the first Dig shortcut on eligible terrain.

The field-combat controller reuses Arena move profiles for ranges, windups, recovery, move kind, projectile speed and cones. Damage and multi-actor AI are Wildlands-specific because the inherited realtime arena is fundamentally a two-body battle renderer.

## Acceptance gate before scale-up

V1 is successful only if the ROM compiles and the player can traverse Route 119 as a Pokemon, fight multiple Pokemon without a battle transition, see the AI partner participate, use grass tactically, cross water with the partner, collect loot, defeat Rayquaza and replace the partner. Only then should the project add the 30-team remote simulator, closing field, full island sectors, selection UI and the remaining four legendary lairs.
