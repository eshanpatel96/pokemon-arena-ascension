## V9 Championship — compiled source checkpoint (8 October 2026)

**CURRENT LATEST COMPILED SOURCE:** `d004c4da56784a3f7c3ac6a69ae6f3c4df7c7264`, [successful GitHub Actions run 37846797245](https://github.com/eshanpatel96/pokemon-arena-ascension/actions/runs/37846797245), [ROM artifact 11580282635](https://github.com/eshanpatel96/pokemon-arena-ascension/actions/runs/37846797245/artifacts/11580282635).

The original Emerald Arena 0.13.0 engine, eight expanded towers and V9 central-city native-tile changes are retained. The previous provisional Summit is replaced with four six-member Elite trainer parties (Articuno, Registeel, Raikou, Regice last) plus six-member World Champion (Ho-Oh last). Native individual trainer sprites/photos, five arena backdrops, healing after II and IV, five-first-clear eligible rewards per round (25 unique Championship rewards), loss fee/restart and native lab PC claim path are authored and compiled. Once-only flags are only set after a successful native Pokémon grant; full storage leaves prize eligible.

**CI PASSED:** source bootstrap, V9 static preflight, original engine GBA compile, valid 32 MiB BPEE ROM. Linked ROM 33,496,984 / 33,554,432 bytes (57,448 bytes free), EWRAM 259,989 / 262,144 (2,155 bytes free), IWRAM 30,892 / 32,768 (1,876 free).

**NOT YET ACCEPTED:** live Delta/mGBA 55-encounter playthrough, in-battle faint/send-out, healing, Bag, save/reload, reward claiming, visuals and runtime performance. All eight bespoke trial/boss battlefields and final city architecture/service polish remain major V9 deliverables. No claim of bug-free completion. Additional Championship rounds are V9; Masters, shinies and postgame remain V10.

---

## V9 Championship scope update (approved 2026-10-08)

V9 now includes five real six-Pokémon Championship teams: Articuno, Registeel, Raikou, Regice and Ho-Oh as their respective final opponents. Existing native Summit/Champion maps, healing after Elite II and IV, and losses restarting at Elite I are the implementation targets. The Lab must grant 25 separate permanent one-time Championship rewards in addition to 64 tower rewards and 80 starters: **169 species obtainable in V9**. Existing native PC capacity is ample under ordinary play; retain only a simple full-PC failsafe.

**Release proof pending:** this source milestone still requires a successful GitHub ROM build, actual mGBA and Delta fight/save QA, full 55-round campaign and visually polished city/towers. The Masters/shiny extras move to V10.

# V9 — Live Development Status (8 October 2026)

## Current checkpoint

**Target:** Complete eight-tower V9 with redesigned town, meaningful arena trial/boss fights, preserved Emerald Arena 0.13.0 controls and a stable save/economy/recruiting system. V9 now contains the five-round Championship source; V10 holds Masters Circuit, shiny licenses and final endgame extras. Full V9 was approved; no need to re-ask.

**Latest fully compiled GitHub run:** [#81, 37843254758](https://github.com/eshanpatel96/pokemon-arena-ascension/actions/runs/37843254758) — **SUCCESS**.
- Source: `d2b39491306dca041b3ff84db59f44ad834ba5d8` from `v9-full-build`.
- Development ROM ZIP: [Ascension-V9-DEV-UNTESTED-GBA, artifact 11578861771](https://github.com/eshanpatel96/pokemon-arena-ascension/actions/runs/37843254758/artifacts/11578861771).
- GitHub static preflight and native Emerald/Arena GBA compile passed; valid BPEE header and padded 32 MiB GBA.
- Link usage: ROM 33,495,600 / 33,554,432 bytes (**58,832 bytes free**); EWRAM 259,989 / 262,144 (**2,155 bytes free**); IWRAM 30,892 / 32,768 (**1,876 free**). Near capacity, runtime not profiled.
- **Zero completed documented mGBA/Delta game-playthrough tests.** Compile does not prove boot, controls, AI, switch/KO replacement, Bag, save/reload, geography or boss victory.
- Earlier reported run 37841392509 was canceled by subsequent code updates; its cancellation is not a failure of latest run. No extra compilation should be assumed in progress.

## 1. Built into compiled V9 DEV source (functional confirmation still pending)

- **Original native real-time engine** remains; controls and small Pokémon sprites are intended to be preserved.
- **Longer tower schedule coded:** Bronze **4**, Gale **5**, Verdant **5**, Phantom **6**, Inferno **6**, Tidal **7**, Thunder **8**, Astral **9**; Summit **five provisional** encounters (NOT V10's completed Elite + World Champion).
- **Existing sequential trainer-party system** and larger boss parties, distinct four-mon Bronze semifinals, signature final legendaries, separate native boss-room maps. Correct faint/send-out and floor transition must still be witnessed in game.
- **Source-level economy:** actual native shop stock without Poké Balls; payout formula revised, 10% carried-money loss capped at **1,000**, lost run resets at its first fight and returns to city, checkpoints in early/later towers; no known item-usage runtime QA.
- **Pokémon recruitment source:** 80 initial + 64 tower rewards + 43 V10 reservations (187 original animated species total); per-grant starter progress; boss prize lock until clear; saved normal-floor reward milestones across failed runs. Individual movesets still use shared profiles, not 144 specially tuned/battle-safe loadouts.
- **AI source:** distance/move recency biases and five themed attack-style scoring choices (rushdown, sniper/zoner, defender, bait-and-counter, balanced). Behavior/frequency measurements absent.
- **Native arena stages** differ for trial vs boss. Original native water/flood interaction invoked in Tidal and Thunder leader fights; other environmental set pieces remain partial.
- **City physical source:** Lab facade/graphic lettering, different Supply/Move roof colors, real copied flower-bed metatiles, new visible service signs. Native Name Rater and four-move **restoration** service added (not a free four-move editor). Walkway/warp **static** checks passed.
- **Exteriors:** Verdant green, Phantom purple, Tidal blue, Thunder warmer reactor palette recolors; Bronze, Gale, Inferno, Astral reuse distinct Emerald Frontier building silhouettes. Recolors are not a full bespoke tower redesign.
- Static checks passed for roster allocation, rank floors, scripts, landmark tile changes, terrain collision paths and room/stage mapping.

## 2. Built but MUST BE PLAYTESTED (open release blockers)

- Fresh boot, iPhone Delta controls and original animated combat feel/sprite size.
- First opposing Pokémon faint, correct send-out of second through full team, forced/voluntary player switching, effects/status/PP/Struggle, Bag targeting and pause/resume; no classic turn-based fallback.
- Full Bronze 4-round chain including normal fights, boss-last Regirock, checkpoint, money and permanent rewards.
- Eight towers' correct checkpoint/boss transitions, side-by-side sideline trainer graphics, win/loss, replay/retry and precise return warp. Current code stage/build checks cannot prove user-visible paths.
- Save/cold reload, V8 save compatibility or migration choice, incomplete PC storage grants, zero-money recovery and one loss fee.
- Actual on-screen Lab/roof/courtyard design, all eight entrances/signed routes, metatile collision and wandering NPCs.
- Real frame pacing, worst-case weather, OAM and EWRAM runtime headroom in mGBA and Delta.
- Encounter balance and no repetitive move spam, measured AI frequencies, meaningful team choices.

## 3. STILL NEEDS DEVELOPMENT to qualify as FULL V9

1. **Central-town polish/architecture:** real identifiable campus with proper native façade beyond letters/recolored roofs, landscaping, interior service flow, actual training/nature/EV center and wardrobe. Restore full UI affordances, readable directory and more authentic town identity.
2. **Eight complete tower environments:** each recognizably themed exterior + walkable foyer + genuinely differentiated **actual in-battle** trial and grand boss arena. Genuine counterable hazards for Bronze/Gale/Verdant/Phantom/Inferno/Tidal/Thunder/Astral, rather than stage swaps and existing effects alone.
3. **Team-selection and move customization:** usable unlock catalog, correct rank/lock display, select/modify battle squad and preview type/role/speed, customizable four supported moves with PP/windup/range information. Verify each selectable recruit and prevent evolution bypasses.
4. **Boss and floor tuning:** distinct curated teams/archetypes per floor rather than over-reusing 5 species; trainer/leader match and choreography; AI reliability and varied tactics. Provide non-grindy level progression and meaningful loot/economy balance.
5. **Regression certification:** automatic tests where possible + real mGBA and Delta multi-hour fresh/returning save loops; fix progression blockers, text glitches, collisions, arena menu bugs and performance issues. Do not claim zero bugs without test evidence.

## 4. Recommended next milestones

**Gate A — Bronze playable proof (highest priority):** fresh career/PC; enter Bronze; first enemy faints → next fighter; four complete opposing parties; switch and use Bag; all boss transitions; Regirock last; earn money/recruit; lose, retry, save and cold reload. Attach screenshots/recorded actual results. Failures supersede cosmetic updates.

**Gate B — Genuine environment package:** finish town and one complete Bronze exterior+foyer+trial+boss real-time battlefield as quality baseline; then implement/verify Gale through Astral, rather than recoloring and claiming eight finished.

**Gate C — full V9 acceptance:** the stable-ID checklist at `docs/V9-FEATURE-ACCEPTANCE-CHECKLIST.txt` supplies exact acceptance rows. Full 8/8 tower run, full service and team functions, bug regression, fresh/old save policy, mGBA+Delta. Only then label V9 finished and advance to V10.

## Preservation

- Draft PR [#7](https://github.com/eshanpatel96/pokemon-arena-ascension/pull/7) remains the active implementation workspace, **not merged to main as finished**.
- Read [PROJECT-START-HERE.md](PROJECT-START-HERE.md), [V9-FEATURE-ACCEPTANCE-CHECKLIST.txt](V9-FEATURE-ACCEPTANCE-CHECKLIST.txt) and the user-provided original continuation handoff before further development.
- Do not reset earlier decisions, confuse doc commitments with code, or confuse compiled code with an actual Delta gameplay pass.
