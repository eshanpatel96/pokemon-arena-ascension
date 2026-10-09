# Internal refresh evidence — 9 October 2026

The user's eleven-point device feedback remains tracked in V11-1-REFRESH-DEVICE-FEEDBACK.md. The previous gameplay test is not approved for external testing; this internal build is not a substitute for completing those requirements.

Independent workflow 37976567048 completed successfully from commit 76fb0b14ed384966820e6a14f2f97e7448233853:
https://github.com/eshanpatel96/pokemon-arena-ascension/actions/runs/37976567048

- Exact packed baseline SHA check and no-fuzz code patch succeeded.
- Protected title/menu/native save/load/new-game and flag/var files stayed hash-identical.
- The native GBA compiled. Link totals: EWRAM 260034, IWRAM 30892, ROM 32856024 bytes. Static link totals do not establish runtime performance.
- Normal GBA key input entered the Birch Lab, displayed registration, completed the briefing, opened START > CITY MAP, switched West/East pages and returned to the same Lab. No RAM writes, original-story shortcut or native saving test was used.
- Both map screenshots were checked against the actual RefreshMap_Main callback, and the closed screen against return to the Lab field. Party count stayed six.
- Runtime frame captures and source-based map reconstructions are labeled separately.
- Arithmetic tests passed for symmetric pacing and wet-floor speed/damage policies. This is not a measured full-fight, fire-footprint, terrain-balance or Delta acceptance result.

Artifacts:
- 11639032273: V11-1-INTERNAL-REFRESH-NOT-EXTERNAL-BETA.
- 11639142249: V11-1-INTERNAL-REFRESH-EVIDENCE.
- 11639542027: V11-1-INTERNAL-REFRESH-SOURCE, preserving a rebuildable source snapshot.

Major town architecture, visible world population, authentic boss-location adaptations and corresponding real-time battle scenes remain unfinished. These are the main visual implementation priorities, not optional polish. HP/duration, terrain and AI need live-combat acceptance. Full legal moves, Box editing, nature changes and normal campaign verification remain in the original required scope. Saving work remains excluded.
