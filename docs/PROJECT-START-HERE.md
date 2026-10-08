# Pokémon Arena: Ascension — Living Project Checkpoint

**Project opened:** 2026-10-08. **The user approved full V9.**
This document is the repository-side durable continuation record for the existing ChatGPT Project context **Pokemon Ascension Arena**. Keep the separately uploaded V9 continuation handoff as well.

## Canonical source and build state

- Repo: https://github.com/eshanpatel96/pokemon-arena-ascension
- Main at project migration: 98263224872021a0b508c442ca291ce75897fd1a (documentation-only commits beyond alpha).
- Most recent **compiled** V9 alpha: 9a295be08f20ed7f54126798c6292e6c52b318e7.
- Alpha CI: https://github.com/eshanpatel96/pokemon-arena-ascension/actions/runs/37828304827
- Raw alpha ROM SHA-256: d77017cfe93136a52874fb604b28a426bc8c88ec156099062ac15a66adb4d29f.
- New implementation branch: **v9-full-build**, source changes underway.
- Alpha has **not** passed a complete mGBA or Delta session; do not call it V9 FINAL.
- Alpha ROM had under 60 KiB free and EWRAM under 3 KiB free. Recheck link results before adding new assets.

## Locked playable target for V9

- Preserve native Emerald Arena 0.13.0 engine, physics, art, smaller Pokémon sprites, D-pad movement, L/R+A move control, B dodge and native START/Bag.
- Two districts: West Bronze/Gale/Verdant/Phantom; East Inferno/Tidal/Thunder/Astral; full Summit V10.
- Actual **visible central research campus**, not just relabeled buildings: Lab with PC/rewards, Arena Supplies, Move Studio, training/nature/EV, Name Rater, Wardrobe, landscaping, clear signage and safe NPC placement.
- Eight themed exteriors and interiors, trial arena and separate grand boss combat stage EACH, with meaningful native environmental mechanics and active gameplay differences.
- Authentic opposing trainer choreography; one active Pokémon per side, full multi-Pokémon teams, legendary last, good entrances/returns.
- 80 starter species; 8×8 permanent tower rewards; remaining 43 reserved for V10. Four safe, varied real-time moves, PP/abilities/status/switch/faint require validation by species.
- Native shop with healing/battle items, currency for wins, 10% loss fine max 1,000, zero floor, free recovery/practice/entry.
- V10: five-stage Championship with Ho-Oh, Elite II/IV healing, Masters and shinies.

## Source evidence vs release evidence

| Area | V9 alpha evidence | Development branch objective | Gameplay acceptance |
|---|---|---|---|
| Middle town facades/landscaping | Native generic Frontier exterior | Actually rebuild native metatiles and service entrances | **INCOMPLETE** |
| Streets, signs, navigation | West/East links and greeters | Check collision, warp, sign and directory | **NOT TESTED** |
| Eight tower exteriors/foyers | Reused Frontier buildings | Eight recognizable themed structures/interiors | **INCOMPLETE** |
| Eight trial arenas | Native Arena stage mapping | Differentiate backgrounds, physics/hazards and staging | **INCOMPLETE** |
| Eight boss arenas | Native Emerald leader layouts | Separate dramatic visible backgrounds, mechanics and intros | **INCOMPLETE** |
| Parties and AI | Prototype trainer rosters, three-floor system | Correct faint/replace, longer progression and tactics | **NOT TESTED** |
| Trainer identities | Some native mapping | Match expert and psychic leader photo to overworld | **NOT TESTED** |
| Starter Lab catalog | 80 bulk grants, partial-storage defect | Saved progress index prevents duplicate retries | **REQUIRES BUILD/QA** |
| Tower recruitment | 64 flagged rewards, early ace claim defect | Gate bosses on full clear, save/retry | **REQUIRES BUILD/QA** |
| Economy/Bag | Native shop, 1,200 loss cap | New cap 1,000 and tuned payouts, item targeting test | **REQUIRES BUILD/QA** |
| Boss rain/flood | Native arena effect requires move | Add original storm/flood at Tidal/Thunder boss starts | **REQUIRES BUILD/QA** |
| Save/Delta/performance | Prior CI header valid | mGBA/Delta boot, fresh/old saves, frame budget | **NOT TESTED** |

## New development branch work

- bootstrap/v9-release-safety.py: save-safe partial registration, reward gating, updated economy, matching leader identities, differentiated native trial/boss stages and two native storm-enabled finals, clear reward/next-venue dialogue.
- bootstrap/v9-city-services.py: native Name Rater in Style House and known-profile four-move restoration in Move Studio; not the planned custom loadout editor, nature/EV service or wardrobe.
- bootstrap/check-v9-invariants.py: static gate for unique 80+64 recruitment, progression safety, contrasting battle stages, local NPC count and exactly one per-battle loss penalty.
- bootstrap/apply-ascension.sh: apply new pass after the alpha scripts.
- Planned CI: static preflight, GBA compile, explicitly labeled V9 DEVELOPMENT ROM, updated memory stats.

**These are initial source improvements, not completion of the visible city or production-quality eight-tower remodel.** Never silently reduce architecture and real mechanics to labels/palette swaps.

## Implementation and acceptance order

1. Compile new branch and fix source/build issues; inspect ROM/RAM usage.
2. Verify Bronze vertical slice: first KO → next Pokémon, switching, leader, reward gate, defeat penalty, cold save/reload.
3. Remodel central town metatiles, signs and doors around Lab/shop/studios; compare actual emulator screenshots with plan.
4. Build each tower exterior+foyer+trial+boss package; test arena visuals and hazard collision/counterplay on screen.
5. Add career floor progression/checkpoints and AI archetypes; inspect all unlockable move compatibility, Bag, PP and status.
6. Full eight-tower fresh/old-save walkthrough in mGBA AND Delta, no turn-based fallback, bad text, blocked doors or severe frame drops.
7. Only after demonstrated acceptance label a ROM near-complete V9.

## ChatGPT Project continuation instructions

Continue Pokémon Arena Ascension V9 from GitHub branch **v9-full-build**, this living checkpoint and the uploaded V9 continuation handoff. Preserve approved V9 direction from the old "Create Delta Compatible Zip" conversation and native Emerald Arena 0.13.0 gameplay. The user already approved the full version. Do not repeatedly ask approval, restart V6/V8, mistake a compiler pass for gameplay acceptance or label the alpha final. Implement the central-town visual redesign, all eight tower exteriors/interiors, truly distinct trial and boss real-time environments, multi-Pokémon fights, rewards, trainer identities, currency and extensive progression. Keep source SHA, CI ROM artifact, raw hash, RAM/ROM, test evidence, known defects and remaining scope updated. Leave the full five-trainer Championship and Masters to V10.

## Moving the conversations

This conversation is already in a workspace identified as **Pokemon Ascension Arena**. Keep using that Project rather than creating a duplicate. Move the older **Create Delta Compatible Zip** chat into it (chat menu → Move to project where supported), and attach the uploaded handoff and updated checkpoint as Project sources. The GitHub repo stays the reproducible editable source. Chats and a ROM alone cannot replace source or build recipes.

Update this document at every meaningful milestone with commit SHA, CI run/artifact, raw ROM SHA, link memory, verified playtest steps and open blockers.
