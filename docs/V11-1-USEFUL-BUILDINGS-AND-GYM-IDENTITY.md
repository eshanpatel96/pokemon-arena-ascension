# V11.1 refresh — useful interiors and gym identity

**Required design clarification from the user, 9 October 2026. Not an implementation or release-completion report.**

This supplements `V11-1-REFRESH-DEVICE-FEEDBACK.md`, specifically R05/R07/R11. The user reiterates that ALL enterable houses must contain something useful, and that legendary locations, haunted houses or graveyards must be adapted into a gym-like experience rather than imported as raw destinations. These clarify existing core requirements; they are not optional expansion ideas.

The current gameplay test remains internal/not accepted for external testing. The accepted title stays unchanged. Saving work remains excluded. This documentation commit adds no game code and makes no new ROM/build claim.

## H01 — Every enterable building has a real purpose

Audit both city districts and their connected residential/service interiors, not just the initial eight west-district doors. Every enterable building must have a named primary player benefit, matching exterior identity/sign, a functioning interior interaction, accurate City Map/Guide information and a working return exit. An empty room, generic greeting or sign advertising an absent service does not pass.

Use the already-approved service set first. These are functional assignment targets, not a claim that all services are implemented:

| Building/interior role | Useful content required |
|---|---|
| Birch Lab / team preparation | Onboarding, party/PC team management, roster/unlock explanation and earned recruitment rewards. |
| Battle Supply Shop | Functional purchases of supported combat items with clear prices and correct inventory effects. |
| Move Studio | Real move-slot editing and relevant move information; full legal moves and direct Box/collection selection remain required. |
| Training specialist's house | EV training/reset and nature changes with confirmation and actual stat recalculation. Nature changes remain unimplemented in the current checkpoint. |
| Style House / Wardrobe | Functional native trainer appearance selection/cancel/revert. |
| Name Rater's house | Functional Pokemon nickname changes/cancellation. |
| Recovery and practice facilities | Actual free recovery and/or the already-approved repeatable controls, switching and terrain practice; place logically rather than forcing extra travel. |
| Other retained houses / tower-adjacent homes | A specific useful role drawn from the approved guide, preparation or practice systems, with relevant themed inhabitants. Name the interaction before retaining the enterable building. Do not satisfy every spare house with the same generic advice. |

Final one-to-one building assignments depend on the door/interior inventory and usable-space redesign. This list does not authorize adding endless new buildings or inventing quests, crafting, currencies or other expansion systems merely to fill existing empty houses. Nor does it authorize deleting useful existing access. Redesign/reassign genuinely redundant interiors; any scenery-only facade must be unmistakably non-enterable, not a fake door or a way to evade the useful-house requirement.

Homes can still LOOK like homes and contain residents/Pokemon; a useful specialist service does not require turning every residence into a shop counter. Tower-adjacent houses/NPCs should fit that tower's theme. Keep residents and wandering Pokemon away from doors, sole corridors and interaction tiles.

### Building inventory and acceptance evidence

Maintain a row for each retained enterable building: district, map ID, doorway/warp, sign/name, interior ID, primary useful action, provider/event, implemented status, ordinary-input test result and exit destination. Acceptance is entering every building through its real door and using the advertised action. Source inspection or a screenshot of the exterior is insufficient. Update the actual in-game City Map and guide when doors or services move. More useful space means accessible preparation/practice/courtyard space and shorter sensible routes, not simply a larger map.

## G01 — Recognizable environments designed as Ascension gyms

**The environment supplies the identity; the gym supplies the layout and encounter structure.**

Do not choose between a plain rectangular gym and an untouched cave/dungeon. Adapt native environmental art and selected architectural motifs into purpose-built competitive venues. Retain the eight tower identities, full encounter counts, trainer parties, checkpoint rules and legendary-last opponents; Elite Four/Champion follow the same principle.

Shared gym features:

- An identifiable entrance/foyer and Master or attendant explaining challenge, floor and recovery rules.
- A clear procession through the existing trainer sequence, with a deliberate gate/door or threshold into the boss chamber. No confusing extra entrances or accidental challenge just by entering.
- A readable compact battle footprint fitted into the setting. Use stone inlays, a ritual seal, a raised platform, lamps or themed boundary markers rather than imposing the same bright rectangle on every environment.
- Player and opposing trainer staged on opposite sides of the inner combat space, facing each other across a clear lane; Master outside that lane. Architecture cannot obscure actors or force unreadable camera framing.
- Boss introduction, full opposing-party fight, named victory/reward and clear return/next-round flow. Keep safe cancellation and intended recovery boundaries.
- Adapt the actual real-time battlefield, cover/collision and simulated terrain separately to match the walkable gym. Water/lava/ghost scenery alone does not implement a mechanic.

### Location-to-gym design targets

| Venue | Environmental identity | Gym adaptation |
|---|---|---|
| Bronze / Regirock | Desert ruins, quarry, carved stone. | Ancient stone gym with formal entrance, weathered pillars, inset combat boundary and boss dais; retain improved close staging. |
| Gale / Lugia | Mountain/cliff sanctuary and exposed sky. | Summit gym with a defined stone platform, wind markers, a legible entrance and safe edges. |
| Verdant / Suicune | Forest shrine, roots, pools and canopy. | Grove gym with a deliberate path, natural trial clearings, and a bounded shrine court rather than maze-like woodland. |
| Phantom / Mewtwo | Haunted manor/crypt with graveyard elements. | Haunted gym: manor-style entrance/foyer, controlled haunted trial halls or graveyard paths, then a ritual hall or graveyard courtyard serving as the boss court. Grave markers, ironwork, candlelight and mist establish identity without blocking the fight. This is an art direction, not a claim that a complete native haunted-manor asset set exists. Keep Mewtwo; no boss/roster change follows from the ghost theme. |
| Inferno / Entei | Groudon-inspired Terra Cave/Mt. Chimney volcanic rock and magma. | Volcanic gym built into the cavern: controlled approach over stone, formal dry central fighting platform, magma around/along telegraphed boundaries, leader at the far side. No story Groudon capture event. |
| Tidal / Kyogre | Marine Cave-like ocean den and surrounding water. | Ocean-shrine gym with a clear approach, bridges/stepping platforms where appropriate, a marked central shelf and controlled wet/dry combat areas. No mandatory Surf or unrelated dungeon travel. |
| Thunder / Zapdos | Power station machinery and storm atmosphere. | Reactor gym with entrance briefing, conductor-marked court, side generators and readable grounded positions. |
| Astral / Rayquaza | Sky Pillar-style summit and ancient broken masonry. | Summit gym: intentional approach and elevated marked combat platform; broken architecture and open sky outside a safe playable footprint, not the original bike/fall puzzle. |

For Phantom, haunted manor and graveyard elements may be combined as exterior/approach and interior/finale. The gym identity must remain unmistakable whichever room arrangement fits the native assets best. Do not describe a speculative complete haunted-house tileset as verified existing art.

Use Ascension-owned maps/scripts. Reuse native art/geometry where appropriate; do not bring over original story flags, HMs, capture triggers, maze/puzzle dependencies or exits to the Emerald adventure. All existing tower/Elite/Champion teams and final aces remain unchanged.

## Completion criteria

A functional house must do what its identity advertises. A themed boss venue must look and play like a gym deliberately constructed within its environment. Another paving-only town pass, generic tiled rectangle, raw dungeon copy, or pretty approach followed by an unrelated real-time combat floor does not satisfy these requirements.

These criteria remain alongside longer meaningful fights, observable tactical AI, actual terrain interactions, visible world population, the remaining services/moves and normal campaign verification. They do not replace or silently defer any of that work.
