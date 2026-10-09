# V11.1 world refresh candidate — actual delivery, 9 October 2026

This document records a NEW locally compiled candidate, not the prior internal refresh renamed. It is not full original-scope Beta acceptance or external-release certification. Saving work remains excluded. The accepted title is preserved.

## Exact deliverables attached to the active project conversation

- `Pokemon-Ascension-Arena-V11.1-Refresh-Candidate.gba` — 33,554,432 bytes; SHA-256 `660c5ecc40fa06aebbf2c4b76b8cc025af619843c2844987c9e17f21bd94ca37`.
- `Pokemon-Ascension-Arena-V11.1-Refresh-Candidate.zip` — 11,697,294 bytes; SHA-256 `04a8eaa81058e0d0266aa6fa427a1044169e9c4ca2781b2a5d9bbc4168729f8b`. Same ROM, readme, limitations, manifest, keyed building/venue records, per-species move compatibility, test logs and actual native screenshots.
- `Pokemon-Ascension-Arena-V11.1-Refresh-Candidate-Source-and-Build-Kit.zip` — 707,287 bytes; SHA-256 `09090b616d266a4f36383a7a5d5eb4cca40ad74063d54ebbe933cd21c7d9ef88`.

The source kit preserves **all 194 changed files**, baseline/final hashes, an exact overlay installer, an independently verified unified-diff/native-asset generation recipe, build script and C test probes. It reuses the existing project baseline rather than duplicating unchanged resources. Retrieve this named conversation/Library file before continuing development; do not assume only this repository document exists or that local unpreserved edits are the source of truth.

## Important repository distinction

**This commit is documentation only. The new candidate game code is preserved in the attached source kit, not yet pushed as a new complete GitHub code tree.** There is no new GitHub Actions run being claimed for this candidate. The two successful builds were performed locally from separate source reconstruction paths and produce identical ROM bytes. Do not relabel the earlier green internal workflow as this new build.

Pinned source baseline: game commit `76fb0b14ed384966820e6a14f2f97e7448233853`, workflow run `37976567048`, artifact `11639542027` (`V11-1-INTERNAL-REFRESH-SOURCE`); archive inside artifact `v11-1-internal-refresh-source.tar.gz`. Conversation baseline filename `V11-1-refresh-baseline-source.zip`. Unchanged source fields, title/menu and native saving files were verified by hash. Main and previous ROM remain untouched.

## Implemented in this candidate

- Structural West/East town map rebuild, native facade composition, connected preparation courts, moved and rewired doors/returns, 17 assigned gym/service interiors. West has15 objects and East12 including native overworld Pokemon and themed people, within native limits. Updated START City Map labels all17 doors.
-13 native-location boss venues: Desert Ruins; Navel Rock cliff/summit; forest clearing; Mt Pyre crypt; Terra/Marine Cave; New Mauville; Sky Pillar summit; Shoal ice; Ancient Tomb; Mt Pyre summit; Island Cave; Navel Rock Champion summit. Each remains an Ascension gym with deliberate challenge and opposite-side staging. Actual native realtime battle scenery was separately replaced/adapted to match.
-New useful Training, Name Rater, Recovery/Practice and East Field Station interiors. Native game map IDs moved into a new group34 rather than overflowing signed map-number127. All17 real doors reached the correct interior in emulator fixtures.
-Birch onboarding retained. New careers now contain exactly80 unique allocated starter species:6 party/74PC. Starting six Charizard, Blastoise, Eevee, Scyther, Hariyama, Lapras; future recruits no longer injected by legacy presets. Existing player collections are not bulk-deleted.
-Native25-nature picker with confirmation and stat recalculation. Correctly reshuffles/decrypts/encrypts Pokemon substructures while preserving identity fields, IVs, moves, held item, EVs and gender/shiny state in tests. Native EV training/reset retained.
-Direct Box/occupant selection in Move Studio, using a temporary converted mon rather than borrowing a party slot. Native Summary/replacement flow commits only move/PP fields after identity checks. Box cancellation and whole-party preservation tested.
-115 additional realtime move profiles/adapters;203 total plus Struggle. Additional physical/elemental attacks, Earthquake pulse, primary conditions, confusion, buffs, recovery, weather and native variable-power adapters. Native type/accuracy/ability/stat paths reused. Constant ROM move index avoids linear per-tick scans.
-Expanded legal catalog includes inherited pre-evolution moves. **6030 supported of9422 audited legal species/move pairs;3392 still unsupported/hidden. Full legal moves are NOT complete.** Event/transfer exclusives are not added; not every new profile has exhaustive edge-case tests.
-Additional AI status/healing choices and hazard avoidance with reaction to visible warnings, retaining range/recovery/repetition/style scoring. No claim of perfect or fully balanced strategic behavior.
-Symmetric half-direct-damage fight pacing retained; residual pacing adjusted too. Wet-floor attack/speed bonuses retained. Fire beam now creates the temporary cosmetic scorch in actual simulation. Water extinguishing, paused timers, shared warnings and stage rules integrated.
-Stage mechanics: bounded telegraphed gusts/vents/shock lanes, regrowing cover, native mist, flood/ice areas, alternating crystal cover. Warnings precede effects; absent warning sprites disable the hazard rather than creating invisible damage.

## Reproducibility and final-ROM evidence

Original edited-source build and independently restored baseline + packaged recipe both produced the exact SHA above.
Link usage: ROM32867735/33554432 (686697 free), EWRAM260076/262144 (2068 free), IWRAM30892/32768 (1876 free). Static totals are not worst-case runtime guarantees.

Final-ROM mGBA0.10.3 checks:31 world-entry/boss-entry assertions;507 controlled native nature/collection/sample move/hazard assertions;8 actual nature/Box UI assertions;8 live attack/PP/scorch/pause/dodge assertions;5 normal onboarding/map assertions. All559 passed with their documented scope.

Normal onboarding uses ordinary buttons. World/UI checks use debugger-selected starting maps/ranks then native interaction. Deep checks call compiled native functions and use high-HP isolated terrain fixtures. These are **not 63 campaign wins**. The live Inferno control check used no HP/stat cheats and observed actual Flamethrower/PP/scorch, paused HP/timers, resume and dodge. Sample514updates recorded10missed VBlanks/max gap3 and22AI decisions; this is not complete performance certification.

## Remaining acceptance / truthful delivery label

Full move coverage still incomplete. Exhaustive new-move/ability/item compatibility, all63 ordinary campaign transitions/wins/rewards, broader retry/rematch economics and full forced-switch/item coverage remain unverified. Physical iPhone Delta testing is unperformed. Native adaptations are substantial changes but not pixel-perfect bespoke lighthouse/conservatory/manor/dam realizations; art, HP, hazard and AI balance still require user feedback. This is a playable refreshed candidate, not a completed original-scope external Beta.

No saving work or saving acceptance gate is reintroduced.
