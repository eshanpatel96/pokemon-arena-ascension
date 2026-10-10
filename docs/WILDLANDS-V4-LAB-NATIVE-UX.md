# Pokemon Wildlands V4 — Lab Native UX Lock

## Principle
Use existing Pokemon interfaces wherever possible. The Lab is the immersive front end; do not build a separate fighter-select menu unless the native UI cannot support a requirement.

## Team selection — PC
- The PC contains the entire curated 105-species Wildlands roster.
- Party capacity is exactly two.
- Selecting a third Pokemon prompts the player to replace Slot 1 or Slot 2.
- PC grid uses native Pokemon menu icons.
- Highlighting an entry may show a larger animated Arena sprite plus type/role/traversal summary.
- Boss-only legends appear as locked silhouettes/records and cannot be withdrawn.

## Moves — TM Case + Move Tutor
- Every Arena-supported Technical Move that is legal for a species is reusable without consumption.
- No HMs are required.
- Surf/Fly/Dig traversal traits are separate from move slots.
- Arena-supported legal non-TM moves use the Lab Move Tutor / move-reminder flow rather than a custom selector.
- Normal move-forgetting UX is retained.

## Battle items — Bag
- Use the native Bag/Battle Items pocket.
- Lab stock can be unlimited, but deployment carry capacity is limited.
- V4 target: two starting battle-item slots for the squad.
- Field loot can refill or replace carried items.
- No infinite in-match healing simply because the Lab stock is unlimited.

## Stats / EVs
- No EV grinding.
- Every Pokemon deploys at the same match level.
- Wildlands automatically applies a role-appropriate competitive stat profile.
- Natural species differences remain meaningful.
- Selectable legends sit above ordinary Pokemon; recruited boss legends remain stronger still.
- Player decisions focus on species, partner, moves and battle-item loadout.

## Professor
Professor reports persistent career data:
- matches
- practice wins
- Battle Royale wins
- eliminations
- best placement
- boss legends defeated/recruited
- damage dealt
- win streak

## Map
A Lab wall map / terminal and an in-match Map screen use the same Wildlands region map.
- 16 x 12 streamed chunks
- each chunk 256 x 256 px
- total world target 4096 x 3072 px
- grid coordinates A-P / 1-12
- player sector always visible
- five legendary lairs visible from match start
- named POIs and discovered caves visible
- current and next closing boundary visible
- enemy teams are never shown

## Queue
Transport pad / exit:
- PRACTICE
- BATTLE ROYALE (when enabled)

Normal boot flow:
Pokemon Wildlands title -> Lab -> PC/TM/Bag/Professor/Map -> Queue -> Arena-world match -> Lab.
