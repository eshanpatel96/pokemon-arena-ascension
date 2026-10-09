# V11.1 gameplay pass

This pass follows the user's instruction to leave the accepted intro/start flow and native saving alone and work on the rest of the game. Expanded save-compatibility/corruption tests are no longer a personal-playtest delivery gate. This document does not claim a finished full-scope Beta.

## Implemented source

- All 13 boss/Elite/Champion chambers retain their surrounding native architecture but use a 7x5-tile inner court. Player and rival stage at (7,10) and (11,10), 64 pixels apart, instead of (5,10)/(13,10). Every walking step, leader approach and exit was statically validated. Small native mosaic seals replace the blank center. Runtime camera/layering still requires inspection.
- Added 149 further native campus paving tiles and an intact flower-bed placement. Existing eight west-district service/tower doorstep routes and NPC/warp definitions are preserved. This advances campus presentation; it is not completion of all desired exterior architecture.
- A new career prepares the existing 80-species starter catalog in batches of two per frame before giving field control. Existing party and box species are recognized rather than duplicated. The legacy six-member starting team and its original extra box species are retained; this does not silently remove the player's familiar starter choices or claim exactly 80 total occupants.
- Birch no longer offers the old bulk starter grant. He retains earned rewards and PC access. The Lab assistant offers an opt-in catalog synchronization for an incomplete older career, using the existing progress index and full-storage retry behavior.
- Native starter/enemy loadouts retain supported legal preferred moves and fill invalid slots using the existing species-specific legal Arena catalog, favoring attacks and type diversity. All four enemy construction paths are covered. Species, party sizes, trainer identities and final aces are preserved. Champion Rayquaza is kept fifth and Ho-Oh last. No new move behavior was added; full legal move coverage remains unfinished.
- Confirmed EV reset clears the six native EV values and recalculates stats; existing +16 focus training remains available. Nature selection is still open.
- Startup/title/menu, native save/load/new-game structures, flags/vars layout, and all eight ordinary tower scripts are protected by source hashes.
- Asset deduplication checks all 17 dry stage images against the corresponding existing flood asset bytes, then uses direct ROM aliases. No art pixels or palettes are removed, no runtime decompressor or RAM buffer is added. Final linked headroom must be measured, not inferred from the 652,800 raw bytes removed.

## Evidence boundaries

The native career C module compiled locally with the original agbcc compiler. Static path/doorstep checks passed. The original tactical-scoring helper's 58 checks remain separate from a live fight. The new CI builds the real ROM and captures native mGBA frames using debugger-selected rooms for fast inspection. That is not a full 63-encounter progression test.

## Still open

Full legal move profiles and Box chooser; nature selection; complete interactive boss environment mechanics; remaining town/tower architecture; broader service and campaign/reward/item/switch validation; actual iPhone Delta testing. No remaining core feature is marked complete solely because the user waived further saving work.
