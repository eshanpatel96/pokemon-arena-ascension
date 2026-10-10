# Pokemon Wildlands V4 — Field Dex Team Picker

## Roster shown by the picker

The selector uses the strict **101-species** Wildlands launch pool:
- animated in the actual Arena/PMD catalog
- final evolution in the broader franchise, not merely an Emerald endpoint
- not one of the five boss-only legends
- at least four legal Arena-adapted moves (current minimum is eight)

Boss-only legends remain visible in the Field Dex as locked silhouettes:
**Mewtwo, Lugia, Ho-Oh, Kyogre, Rayquaza**.

## Screen concept

Use a dedicated menu callback/VRAM state. Never draw this over the live Arena or Emerald field.

### Browse view

- Header: `WILDLANDS FIELD DEX   023/101`
- Left pane: five visible entries, each with a 32x32 Pokemon icon and species name
- Right pane: large animated Arena idle sprite using the actual PMD/Arena art
- Type icons
- Role: BRAWLER / RANGED / TANK / CONTROL / SUPPORT / HYBRID
- four short bars: POWER / BULK / SPEED / RANGE
- traversal tag: LAND / SWIM / FLY / BURROW where applicable
- special tag for specialist designs such as SHEDINJA
- L/R filters by TYPE, ROLE and TRAVERSAL
- A chooses; B backs out; START confirms a completed squad

Do not shrink the large preview to an overworld icon. The point of the terminal is to make the Pokemon feel like Arena combatants before deployment.

### Partner selection

After the lead is chosen, pin its portrait in the header.

The second selection panel adds a live `TEAM FIT` summary:
- shared severe weakness warning
- useful resistance/coverage
- melee/ranged complement
- mobility/traversal complement
- recommended AI role

Examples:
- `GREAT FIT — Water coverage / ranged partner / no major shared weakness`
- `RISKY — both weak to Rock`

This is advisory, never a hard lock.

### Locked legendary page

The five boss-only legends appear as silhouettes with:
`FIELD LEGEND — DEFEAT IN WILDLANDS`

After a player has encountered one in a run, its Dex silhouette can reveal for career-history purposes, but it remains unavailable at match start.

## Power communication

Do not hide roster hierarchy.

Use four stat bars plus a compact class badge:
- STANDARD
- APEX
- LEGENDARY

Low-BST but mechanically distinctive Pokemon are not automatically removed. Instead the UI makes their role obvious:
- Shedinja: SPECIALIST / Wonder Guard
- Plusle / Minun: SUPPORT / pair synergy
- Sableye: CONTROL
- Butterfree / Dustox: CONTROL / ranged status
- Delcatty: SUPPORT

Selectable legends are stronger by design. Boss legends are stronger still after recruitment, while their boss encounter form additionally owns boss-only mechanics.

## Move selection

After each Pokemon selection, open a matching Field Dex loadout page:
- animated Pokemon preview remains on screen
- four equipped move slots
- scrollable legal Arena move list
- each move shows type, power class, range, cooldown and action type
- invalid/unsupported moves never appear

The same UI is reused at the Lab MOVE TERMINAL.

## Technical notes

- Use Emerald's existing small Pokemon icon assets for list rows.
- Use the imported Arena sprite decoder for the large animated preview.
- Reuse one affine matrix for ordinary preview scaling where possible.
- Dedicated menu BG/OAM setup prevents the V2 garbage/VRAM overlap bug.
- Keep selector data table-driven from the audited roster rather than manually duplicating 101 names.
