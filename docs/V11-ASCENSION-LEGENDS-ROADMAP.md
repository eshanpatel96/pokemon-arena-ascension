# Pokémon Arena Ascension — V11 Roadmap: Ascension Legends & Long-Term Play

**Created:** 8 Oct 2026. **Status: PROPOSED ROADMAP ONLY; NO V11 SOURCE OR ROM HAS BEEN BUILT.**

## Release boundary

**V10.2 = near-complete base game and extended Delta testing**: all eight towers, five Championship rounds ending with Ho-Oh, eight Masters battles, all 187 original animated Pokémon, true *legal* four-slot move studio, meaningful themed fights, player/tower choreography and character customization. The user explicitly asked to put that foundation into V10.2; do **not** silently postpone broken V10.2 features to V11.

**V11 = make the already-working game last for dozens more hours**, with prestige challenge ladders, records, cosmetics, replay choices and optional modifiers. V11 must not become a dumping ground for untested save corruption, broken routing, or legally learnable moves unless user explicitly changes scope after a feasibility audit.

## Proposed V11 headline — LEGENDS CIRCUIT

1. **Post-Masters prestige rank:** after complete Championship and Masters, open a separate Legends gauntlet using the original 187 animations. Unpredictable curated team synergies and multiple playstyle archetypes, not merely higher enemy level. Tier II rematches tailored to cover weaknesses; signature legendary remains a dramatic final entry.
2. **Boss Rush / Endless Arena:** optional multi-tower marathon with clearly announced recovery and no pay-to-progress loop. Alternating themed stage mechanics, checkpoint choices and cumulative high scores. No mandatory grind.
3. **Medals and records:** speed clears, no-item fights, low-HP comebacks, flawless-defense rounds, type-mono teams, boss perfect-dodge awards; in-town records hall and persistent personal bests. These should be checked against reliable in-game telemetry, not fake reward dialogue.
4. **Shiny license cosmetics:** use only legitimately supported palettes/animated species (original engine), cosmetic first-clear or difficult challenge unlock; select normal/shiny variant of Pokémon already licensed. Respect save persistence, identity and no free stat advantage. New trainer outfits/poses/insignias as earned cosmetic rewards.
5. **Optional battle modifiers / challenge contracts:** player selects a theme such as weather chaos, cover-heavy, no healing, 3-Pokémon team cap, one-element squad, timed gauntlet. Preview the rules and reward, verify support with real-time combat physics and original GBA performance.
6. **Expanded Arena environment set:** new layouts, stage props, lighting/crowds/entrance ceremony upgrades, more hazard combinations and boss pattern telegraphing, but profile memory/VRAM/OAM first. Ideally make the existing bosses feel remastered instead of replacing the reliable Emerald renderer.
7. **Stronger tactical AI:** learn from distance/windup/cover/cooldown/elemental interaction; bounded non-cheating telegraphs, multiple trainer combat philosophies, anti-spam/anti-kiting that can be countered. Collect run-specific in-game move mix/success telemetry.
8. **Team-build depth:** saved multi-team preset library (if save safe), status/held-item support after targeted testing, better role/type/coverage recommendations, reversible nature+EV training, practice dummies, attack-window tutorial and elemental interaction museum.
9. **Lightweight hub life:** small resident stories/quests, research logs, tower histories, cosmetic home base and animated atmospheric touches using existing native assets, not giant custom town bitmaps.
10. **Polished final credits/ceremony:** world champion sequence, post-Masters Hall of Fame, earned crown/insignia, credits and completion screen, record of entire Ascension career.

## Optional R&D / NOT promised shipped V11

- **Mega Evolution or Ascension Burst:** only if all required 187-compatible art, mechanics and memory can be supported. Existing-sprite temporary Burst is not an equivalent implementation of true Megas. Requires explicit design and feasibility approval.
- **Co-op/PvP and online leaderboards:** Delta GBA internet matchmaking is **not provided by the current source**. Treat as a separate technical feasibility study; do not promise live cross-phone multiplayer.
- **New Pokémon species beyond the existing 187:** would require new animation/assets and RAM/ROM headroom. Do not squeeze in fake static sprites or another renderer.
- **Expanded canonical moves if V10.2 engine audit determines a blocker:** remains a **V10.2 acceptance deviation requiring explicit user approval**; it is NOT automatically deferred to V11.

## Engineering prerequisites

- Reclaim GBA ROM headroom, audit peak EWRAM/IWRAM and sprite OAM; V10.1 linked with ~55.4KiB ROM free and ~2.1KiB EWRAM free. Avoid large graphics packs and excessive simultaneous props.
- Preserve existing PC/reward save IDs and fields; introduce V11 save migration/versioning policy and backup flow.
- Ship a developer-accessible regression route to reach any leader/chamber/Champion/Masters without long manual replay, while keeping cheats/debug room access hidden from friends' normal build.
- Every Legends mechanic needs a repeatable native Arena test with emulated timing + sampled iPhone Delta frame rate and safe decline/exit.

## Milestone outline

- **11.0 — Legends launch:** prestige rematches, Boss Rush, medals/records, durable replay and first earned cosmetics after V10.2 acceptance.
- **11.1 — Arena expansion:** more fully working arena hazard patterns, boss AI differences and controlled rule modifiers.
- **11.2 — Living Ascension:** additional cosmetics/town narrative, Hall of Fame and long-term completion polish.
- **R&D beyond V11:** true Megas/Ascension Burst, optional new species, link or online functionality, only after explicit separate feasibility decision.

## Release condition

No `V11 BETA` until the V10.2 core gameplay is stable, all 187 roster entries can be equipped with legal real-time-compatible moves per approved scope, entire 63-encounter base career completes and reloads safely, and the environment/cosmetic additions respect Delta GBA performance.
