# V11.0 Boss Room Redesign — Native Map Mockups / Approval Gate

**User decision:** Existing regular tower/trial rooms may remain structurally familiar with small thematic variations; all **eight boss rooms** must be genuinely rebuilt, with the Champion as ninth signature finale. Keep working native Emerald Arena combat, saves/rewards and A-to-challenge event flow unchanged.

**Current deliverable (9 October 2026):** Nine visual prototypes and editable native-layout sources were generated from the *actual pinned original Emerald metatiles*.

### What has actually been created

- Nine 19×21-tile top-down native tile layouts, each `798 B` raw 16-bit map data; **7,182 bytes combined raw**. No new tile/palette PNG imported, original tileset ids only. Existing GBA resolution 16×16 metatiles.
- Eight of them are packaged with staged `data/layouts/<AscensionBoss>/map.bin`, copied native `border.bin`, amended `map.json` with new unique layout id + boss and exit attendant coordinates, existing tower `scripts.inc` warp targets to safe arrival `(9,18)`, and appended entries in `data/layouts/layouts.json`. The underlying original gyms are NEVER overwritten; Ascension map IDs and existing boss fight scripts are retained.
- Champion room ninth is an **editable binary/map-art concept only**, not yet connected to source because compiled V10.2 source export omitted `AscensionLeader9/map.json` and `AscensionSummit/scripts.inc`. Wire it using full real source before a ROM build.
- Player marker `(9,18)`, boss marker `(9,4)`, exit guide `(12,18)`; cyan/pink/gold circles are **mockup-only diagnostics**, not in-game graphics. Flood/hazard/particle effects are not simulated by these static illustrations.
- Each prototype passes a **static graph traversal** respecting authored metatile collisions while treating both boss and attendant tiles as occupied: boss and exit approachable; at least 295 tile locations reachable per map. This is not a Delta runtime test.

### Native style concepts

| Room | Boss | Native floor/style | Battle feature target (not shown as implemented by static mock) |
|---|---|---|---|
| Bronze: Quarry of the Ancients | Regirock | Rustboro stone paving, paired standing columns | Breakable stone pillars and heavyweight tells |
| Gale: Temple Above the Clouds | Lugia | Fortree pale-green sky terraces, cloud pylons | Predictable gust lanes |
| Verdant: Ancient Grove | Suicune | Battle Palace stone and reflecting blue pools | Natural/regrowing cover |
| Phantom: Hall of the Forgotten | Mewtwo | Mt. Pyre crypt slabs and cemetery columns | Decoys/visibility |
| Inferno: Eternal Furnace | Entei | Lavaridge lava-lit brick and thermal columns | Telegraph heat hazards |
| Tidal: Abyssal Tide Throne | Kyogre | Sootopolis ice/glass with flooded channels | Water/rain and conduction |
| Thunder: Lightning Reactor | Zapdos | Mauville electric floor + grounding pylons | Chain-reaction reactor props |
| Astral: Celestial Observatory | Rayquaza | Mossdeep cosmic tile mosaic + orbit obelisks | Destructible crystal cover |
| World Champion: Ascension Summit | Ho-Oh | Regal native Emerald ceremonial paving | Firelight arena reveal / final ceremony |

### ROM-space reality

- Last confirmed V10.2 linker: ROM 33,506,952/33,554,432 B (**47,480 B headroom**), EWRAM ~2.15 KB headroom, IWRAM ~1.88 KB headroom.
- **7,182 raw layout bytes is a promising prototype, not a guarantee of just 7,182 linked bytes.** Layout table entries, event scripts, map collision and constants add ROM overhead; new 8 maps plus Champion requires a fresh GBA link. No new EWRAM data or large asset packs are planned.
- Editing native `map.bin` geometry only is generally memory-efficient; custom new graphics/palettes are not required for this first pass.

### Required next steps before merging to V11

1. Show and accept the nine native-tile previews. Adjust the central dais, floor patterns and prop arrangements based on user feedback (particularly Bronze, Gale, Verdant and Astral).
2. Import eight staged native source patches and hook the Champion ninth layout to its real map/source. Make all room entries and NPCs correct with authentic `elevation=3`, no overlapping hero and gatekeeper. Confirm warps and in-game story progression.
3. Compile real `V11-BOSS-REDESIGN-DEV` ROM in GitHub; do not merge preview binaries as finished. Confirm <32 MiB, acceptable EWRAM/IWRAM, valid header and no linker issues.
4. Delta test actual walk-up to boss, A/Yes challenge, signature legendary last, victory, reward, cancel, loss and exit for **all 9**. Verify actual in-battle Arena stage and physical hazard interaction separately. Run old-save/backward-compatibility tests.
5. Capture actual boss-room screenshots/short video from Delta, because palette transparency, layering and NPC sprites may differ from source-based mock render.

**Status: REVIEW-READY STATIC SOURCE MOCKUPS. NOT YET A PLAYABLE V11 ROM.**
