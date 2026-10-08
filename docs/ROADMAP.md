# Pokémon Arena: Ascension — Career & World Development Plan
**Status:** V7 is source-integrated; its native GBA/Delta build and live playthrough still require verification.

## Non-negotiables
- Preserve **Emerald Arena 0.13** real-time battle engine, detailed animated sprites, movement/dodge/terrain, and original Emerald art quality.
- No replacement arcade battle mode; never force the classic turn-based battle screen.
- Start a career at the city plaza; optional tutorial; dojo chooses varied compatible opponents.
- Native Emerald maps with exact entrance/exit warps. Distinct tower interiors, no single shared lobby.
- No custom low-resolution replacement title screen.

## City: two adjacent districts
**Western District:** city arrival, Bronze through Astral tower buildings, tutorial, practice dojo, healing services.
**Eastern District:** future Move Studio, Pokémon Lab, trainer cosmetics and item shop, Championship Summit, and training events.
V7 enlarges the explorable overworld using the original connected West+East Frontier map architecture. Many eastern buildings will require dedicated usable interiors and art in later releases.

## Tower concept — each tier has TWO distinct arena environments
1. **Bronze Trials:** stone practice court → ceremonial training ring; positioning, pacing, first boss
2. **Gale Tower:** open windy terraces → suspended high-altitude ring; movement and gust direction
3. **Verdant Crown:** sunlit grass gardens → giant-tree sanctuary; cover, sunlight, area denial
4. **Phantom Spire:** misty graveyard/tombstones → haunted crypt; fog, telegraphed apparitions
5. **Inferno Forge:** volcanic paths → molten forge; lava vents, safe-zone control
6. **Tidal Bastion:** coastal shallows → flooded amphitheater; water hazards, freeze/electric conductivity
7. **Thunder Citadel:** storm-battered rooftop → conductive lightning chamber; telegraphed electrical pulses
8. **Astral Apex:** crystalline observatory → psychic/stellar arena; moving terrain and advanced AI
9. **Champion Summit:** regal gallery → ornate gold championship ring; multi-phase championship.

Each tower has an **Arena Master** who previews its floor count, recommended Pokémon roles, hazard mechanics, boss tactics, and healing schedule. Then the player enters a real arena through a door/gate, instead of receiving a battle immediately from a receptionist. V7 adds unique maps and guides; the dramatic trial/boss battlefields will be a later engine/art release.

## Tower run structure, difficulty & long-term play
- Target floor counts: 4 / 5 / 5 / 6 / 6 / 7 / 8 / 9 + 5 Summit battles (55 total).
- Every early floor has a rotating opponent team/objective; last floor is a scripted Tower Master boss with an elite environment.
- Healing **not after every battle**. Between-floor HP carries forward. Clearly marked healing checkpoints at mid-run, varying by tower; allow explicit early exit to heal in town and replay a run.
- Actual challenge comes from improved enemy movement AI, arena geometry, readable hazard timings, move combos, attack cooldown strategy, and opponent team selection — *not* unbounded level inflation.
- No forced 2v1 until the real-time engine supports two enemies safely.
- Unlock challenge modifiers and a repeatable postgame gauntlet after Summit; medals for clean clears, no-heal clears, and timed runs.

## Expanded Pokémon, abilities and moves
- Existing animation pipeline includes **187 animated Pokémon sprites**, but not all have complete supported real-time move behavior.
- Validate moves/AI individually before making Pokémon selectable; never unlock a Pokémon without at least four compatible usable moves.
- Expand roster in unlockable batches by tower tiers, keeping balanced fast/slow/specialist options.
- Four move slots; L/R cycles selection, A attacks; independent per-move cooldowns require native combat-engine development and tests.
- Repeated dojo attempts should rotate opponents with a non-repeating pool; eventually vary AI archetype and environment.
- Shiny variants as cosmetic rewards, not stat advantages.
- Mega Evolution later: charge through activity/damage, normally one Mega activation per team per round, carefully balanced.

## Trainer/roster customization
Pokémon Lab: unlocked Pokémon selection, four-move loadouts, HP/attack information, party order, styles; keep a team of 4 during introductory towers then expand to 6.
Cosmetic trainer sprites/palettes, outfits, and battle insignia should use GBA-native visuals.

## Arena Credits economy
*If 'credits' refers to in-game currency:* Make it impossible to soft-lock yourself for lack of credits. Entry and basic healing are always free; all practice battles free. Award repeatable credits for battles/clears; use credits only for optional consumables, cosmetics, move-teaching or convenience. Expensive items must never be the only way to progress. No real-money system.

## Development expense
*If 'credits' refers to tooling/usage:* Avoid expensive parallel CI runs. Keep source changes batched into a meaningful milestone, cancel superseded GitHub Actions builds, and cache agbcc/build tooling when reliable. Do not claim access to the user's plan balance or quota.

## Acceptance tests for a phone-ready milestone
1. Fresh SELECT career → city plaza, no dialogue lock or corrupt glyphs.
2. Walk seamlessly to the eastern district and back.
3. Each of eight western tower doors reaches a **different map** and exiting returns to the specific originating door.
4. Summit entrance and return use eastern district.
5. Master and tips in every tower display valid English Pokémon font.
6. Wrong tower cannot advance rank. Correct tower launches **original** real-time Emerald Arena fight.
7. Switching/fainting does not strand you in old battle mode; challenge can resume.
8. Dojo presents mixed Pokémon across attempts; save/load does not corrupt progress.
9. GBA header checks, valid save data, no map corruption; emulator test in mGBA/Delta.

**Current V7 implementation scope:** two native districts, separate tower lobbies, distinct master tips/music, precise exits, rank gating, rotating dojo opponent pool. The full theme-specific *battle arenas* and 55-floor campaign are planned and **not** implemented by this V7 source step.
