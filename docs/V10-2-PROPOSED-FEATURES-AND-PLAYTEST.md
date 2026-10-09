# Pokémon Arena Ascension — V10.2 feature queue and real-player test ledger

Date: 8 Oct 2026. V10.1 latest successful compiled source: `6840ea411b3a9a4e799b25206f39e4193dc376fa`, [Actions 37855729085](https://github.com/eshanpatel96/pokemon-arena-ascension/actions/runs/37855729085). Working source branch: `v10-1-polish`. This document is a plan and playtest log; **writing it does not change the ROM**.

## User-observed facts (NOT source speculation)

- V10: Bronze leader battle completed successfully; user confirmed the walk-up boss approach improved, although room is not unique enough.
- V10: ordinary tower choreography looked wrong; user wanted Tower Master LOWER and player CENTERED. V10.1 source attempted opposing-side choreography, **not yet confirmed corrected** by user.
- V10: first boss-room Gentleman looked out of place. V10.1 source replaced with Hiker. **Not yet gameplay confirmed**.
- V10.1: user reports town looks good in on-device screenshot, and says **the gym worked perfectly** and **rewards were received**. Mark only that tested gym (Bronze) and reported reward flow; this is not a pass for every tower, 64 tower recruits, Champion or Masters.
- User will perform a **longer V10.1 test session** and provide new findings.
- Prior request: move the Bronze boss room's arrival warp **lower**, so entering doesn't place player so far up the chamber.

## V10.2 first priority: positioning and core battle flow

**Regular tower court (all 8)**: current native Battle Tower room is 10x9, Master initial (5,5), player from near (5,6), challenger enters from (5,1). Current V10.1 staging in source: player left (3,4); challenger right (7,3); Master sideline (4,6) plus he approaches for heal. User wants player **middle** and Master **lower**. Proposed safe geometric target: player **(5,4)** facing opponent right; challenger **(7,3)**; Master **(4,7)** (outside play). Recovery Master walks (4,7)->(5,5) to address player, then back; reset returns player (5,4)->(5,6) and Master (4,7)->(5,5). Before coding, verify all scripted movement sources, object blocking, sequences, and raw native 10x9 room walkable tiles. Preserve opponent walkout and one active Pokémon per side.

**Bronze boss entrance**: V10.1 current entry (5,8) vs Rustboro Gym native map 11x20 and leader (5,2), themed exit helper around (6,8). Lower desired arrival candidate **(5,12)**. Original pinned Emerald map.bin pathfinding inspection found (5,12) walkable, boss and exit helper approachable, 123 traversable cells even when occupied boss and helper are excluded. **This is a static candidate, not a delivered change**. Preserve A/Yes deliberate leader start and safe exit.

**Player-recorded acceptance:** actual Delta clips show Player center, Master lower, challenger right, checkpoint Master approaches/returns without collision, Bronze lower boss arrival, boss cannot auto-trigger, rewards survive cold reload.

## V10.2 second priority: finished character customization

Not currently present: real outfit, palette, overworld trainer appearance selection and persistence; the Name Rater is not a character wardrobe. Build from **existing native Emerald trainer/overworld palettes or graphics** to avoid new big sprite assets. Offer a visible Wardrobe attendant and several genuine choices (perhaps classic Emerald boy/girl/hoodie-style palette variants if backed by native sprites), with preview/cancel/revert, matching overworld/battle representation when technically supported and save/reload. No fake menu that only changes dialogue. This user specifically called out missing "small customizer like custom character designs".

## V10.2 third priority: deeper team and move customization

V10.1 has selectable six-stat +16 EV training and three move drills (Protect, Double Team, Swift), but not a full four-move editor. Next: 187-entry unlock catalog; eligible move choices tailored per Pokémon; inspect what native move profiles can actually perform with range/PP/windup/cooldown; prevent unsupported choices, persist and allow cancel/revert. Nature/respec and proper legal evolution/rank rules remain open. Be explicit which features fit within ROM/RAM headroom; do not invent assets.

## V10.3 / friends beta completion

- Finish native-themed eight tower exterior, foyer, trial and boss combat-stage differentiation and **working** hazards/counterplay. Existing stage swaps/palette recolors are not enough to claim complete unique environments.
- Improve AI archetypes, source team pools and fight diversity by round; ensure legend last and source trainer overworld/battle identity agreement; polish boss reward dialogue and next-tower guides.
- Real playtest all eight towers, five Championship rounds, eight Masters rounds, all 187 assigned species unlocked exactly once, save/cold reload, START Bag, L/R/A/B/dodge, currency loss, zero money heal, performance; no known softlocks, unintended classic mode or blocked doors.
- Optional longer-horizon content tracked: shiny cosmetics/licenses, medals/records, ending ceremony, seasonal variants, optional Ascension Burst/Mega mechanic **proposal contingent on engine/assets**, more rematches/training dummies/quests.

## Test notes for current long V10.1 run

At minimum record: current tower/floor, player/attendant/opponent positions, when the Master speaks, whether opponent steps out between trainers, faint/sendout, reward received and if duplicate on re-visit, money before/after a loss, save/quit/reopen state; training stat chooser and effective move, and shop/battle Bag usability. Attempt first clear for Gale if accessible; *do not* conclude all bosses work based on Bronze. Send 10–20 seconds of ordinary tower staging/heal for exact fixes.

## Release gate

V10.1 is a compiled private DEV ROM, **not certified friends-ready**. User-confirmed Bronze and rewards are passes for those specific situations only. V10.2 future coordinate changes and customization are **planned, not yet compiled**. Wait for longer test feedback before replacing their currently running ROM unless there is a reproducible blocker.
