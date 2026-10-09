# V11.1 refresh — first device-feedback response

**Distribution: INTERNAL ONLY. The delivered Gameplay Test is not accepted for external testing.**

The user's latest eleven observations supersede any claim that generic mosaics, signs, a source-map PNG, or static unit checks fulfilled the full design. Preserve the accepted title. Saving work is excluded; do not reintroduce it as a blocker. No new approval is required to address this feedback.

## User observations and tracked corrections

| ID | User feedback | Actual finding and refresh status |
|---|---|---|
| R01 | Title screen good. | Accepted. Title art/menu source hashes are protected; unchanged in the internal refresh. |
| R02 | Brief freeze on starting. | Delivered version registered the collection behind the initial field transition. Internal refresh reveals the Lab first, displays a registration message and processes one starter per task tick. Native emulator shows the message and then usable field control. Elimination of the reported iPhone hitch is NOT yet verified. |
| R03 | Did not start in Birch's Lab with explanations. | Delivered source deliberately warped to the city; Lab onboarding was missing. Internal refresh changes NEW career destination to the Lab and wires an automatic Birch welcome, visible registration, skippable briefing, controls, team/PC explanation, recovery rules and first destination. Native key-input test passed locally. |
| R04 | Starting Pokemon in boxes. | Registration is present, but storage access is not onboarding. Briefing now explains the six-member party versus boxed collection and directs the user to team selection. Existing legacy starters remain; the 86-unique versus approved 80 allocation is still unresolved and is not silently deleted. |
| R05 | No building redesign or improved usable space. | Valid failed requirement. Previous paving/sign/planter work is insufficient. Structural campus facades, building footprints, useful courtyards, direct routes and legible service interiors are still open; no new building redesign is claimed by this first correction. |
| R06 | No map. | Delivered ZIP had an external PNG, not an in-game map. Internal refresh adds actual START > CITY MAP with West/East source-derived miniatures, named numbered services/towers, L/R district switching and B close. Both pages and return to field tested via normal key input. Current markers reflect current doors; regenerate when architecture changes. |
| R07 | No extra people/Pokemon in the world. | Visible world-population upgrade was not delivered. Add purposeful researchers/trainees/residents and wandering Pokemon in the preparation district/courtyards. Preserve door paths and native per-map object limits. This means overworld life, not expansion of the 187-species battle roster. Still open. |
| R08 | Fights too short; HP feedback ignored. | Valid missed priority. Delivered patch did not change hit damage or HP. Internal prototype halves resolved direct attack damage symmetrically (rounding upward), approximately doubling effective durability against direct hits without changing saved HP stats. Both sides use the same rule; Bide is not scaled twice. Live match durations, status damage, healing/items and attrition balance remain unaccepted. This is a new tuning starting point, not an old user-approved multiplier. |
| R09 | AI does not feel changed. | Actual delivered source includes career-only range/recovery/windup/repetition/low-HP/style scoring and contextual Protect/absorption checks. It is a scoring pass, not a demonstrated smarter opponent. Behavioral acceptance remains open: show close/ranged/counter/defensive decisions in recorded fights; do not equate unit assertions with game feel. |
| R10 | Floor power-ups and temporary fire charring. | Delivered native effects include water/ice/charge reactions; flood slows non-Water grounded Pokemon rather than boosting Water speed. New internal prototypes: grounded wet-floor Water attacks +20% before global pacing unless native rain already applies; Water-type grounded speed +15%; one temporary cosmetic char footprint (~180 active ticks), extinguished by Water. Compiled and arithmetic checked, NOT a full live terrain pass. Decorative blue/lava backgrounds do not count as simulated terrain. |
| R11 | Bronze better, still basic; reuse real caves, Sky Pillar and mountains. | Agree. The current simple courts are not the limit of native pixels. Verified native TerraCave_End, MarineCave_End, SkyPillar_Top, MtChimney, NavelRock_Top, MtPyre_Summit and other source layouts are present. Next art implementation should use cloned native-location geometry and authentic tiles, not another recolored generic gym. Corresponding real-time backgrounds/collision/terrain must be adapted separately. Still open. |

## Authentic boss-location direction (not yet integrated)

| Venue | Native source direction | Preserved final opponent |
|---|---|---|
| Bronze | Desert Ruins/quarry rock and an ancient stone clearing; retain improved close staging. | Regirock |
| Gale | High mountain/cliff sanctuary with sky exposure and wind, using native cliff/ruin elements. | Lugia |
| Verdant | Petalburg Woods/Palace-like grove, roots, pools and a natural clearing. | Suicune |
| Phantom | Mt Pyre crypt/summit stonework and mist, not an Astral recolor. | Mewtwo |
| Inferno | Terra Cave/Mt Chimney volcanic cavern: actual rock, magma edges, islands and raised stone. Groudon-inspired setting only. | Entei |
| Tidal | Marine Cave-like den: water boundaries and a dry central shelf rather than blue carpet. | Kyogre |
| Thunder | New Mauville machinery plus a storm-exposed power platform, with conductors and safe ground. | Zapdos |
| Astral | Sky Pillar summit-derived broken ancient platform and open-sky edges. | Rayquaza |

Elite/Champion identities and six-Pokemon teams are preserved. Shoal ice, ancient steel/ruin architecture, storm ridges, crystal caves and Navel Rock/Ho-Oh summit elements are the matching vocabulary; no unapproved boss replacement. The Champion must still have Rayquaza fifth and Ho-Oh last.

Implementation means Ascension-owned map/layout IDs with native art. Do not import original story flags, capture events, puzzles, HMs, or exits into the old Emerald adventure. Keep deliberate challenges, safe cancellation, reward rules and compact readable start positions. The 240x160 battlefield is separate from the walkable map: change both deliberately and validate actual simulated floors rather than assuming scenery creates mechanics.

## Code and local evidence from this turn

Base assembled game: 7eb86415e918e3176b828632322e712f29300d5b.
New branch: v11-1-refresh, created from c6ecc1c93e193fb4fd6fcaca24f8f15f703a8e70. Main and the delivered gameplay-test branch are untouched.

Committed patch: bootstrap/v11-1-refresh/refresh-code.patch. Native map asset generator and pure arithmetic tests are committed alongside it. The independent internal workflow reconstructs from the pinned packed source; no downloaded replacement graphics or saving suite is used.

Local compiled internal ROM SHA-256: 775fe45c18758b7987e14fa22249412785ba8f5e4cf840afb4d228cd6e6610a8.
This is NOT a final Beta distribution. Link totals: ROM 32,856,024/33,554,432; EWRAM 260,034/262,144; IWRAM 30,892/32,768. These are static link totals, not peak-runtime certification.

Normal-input mGBA test: title -> New Game -> Birch Lab (26,110), visible registration, briefing, START map West -> East -> close to Lab, six party members retained. Actual screenshots are preserved. Pure arithmetic edge-case checks cover damage symmetry, no second native-rain multiplier, fixed damage/retaliation exceptions and floor-speed policies. They do NOT prove enjoyable duration, live hazard behavior, environmental AI, or Delta performance.

Internal CI: https://github.com/eshanpatel96/pokemon-arena-ascension/actions/runs/37976567048
Check its actual result before describing independent success.

## Remaining full-build acceptance

The biggest visual work remains R05, R07 and R11: structural town, living world, authentic boss destinations and matching battle scenes. The next gameplay acceptance is R08-R10 in recorded fights. Full legal move profiles, direct Box editing, nature changes, reward/loadout correctness and normal 63-encounter progression remain open from the original scope. No reclassification as optional roadmap merely to make a Beta label.

Do not send this internal prototype as another external-ready Beta. No saving work is required by this refresh.
