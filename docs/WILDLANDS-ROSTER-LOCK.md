# Pokemon Wildlands — Canonical Roster Lock

This file is derived from the actual Arena animation catalog in `tools/arena/roster.json` and Emerald's Gen III evolution table. Do not hand-edit roster counts without updating the audit.

## Source-of-truth counts

- Arena/PMD animated species: **187**
- Emerald endpoints or single-stage species among those 187: **114**
- Boss-only legends: **5**
- Emerald-era selectable endpoints after bosses: **109**
- Later-evolution forms removed by strict Wildlands rule: **8**
- **Canonical selectable launch pool: 101**
- Minimum legal Arena-adapted moves among the 101: **8**
- Groudon Arena sprite: **absent**

## Removed because they are not true final evolutions

Primeape -> Annihilape; Magneton -> Magnezone; Rhydon -> Rhyperior; Electabuzz -> Electivire; Magmar -> Magmortar; Nosepass -> Probopass; Dusclops -> Dusknoir; Roselia -> Roserade.

## Boss-only legends

These cannot be selected in the Lab. They must be defeated in-world and may replace the AI partner after recruitment:

1. **Rayquaza** — Sky Spire
2. **Kyogre** — Abyssal Basin
3. **Mewtwo** — Abandoned Research Facility
4. **Lugia** — Tempest Shrine
5. **Ho-Oh** — Ember Temple / volcanic summit

## Selectable legendaries at match start

**Articuno, Zapdos, Raikou, Entei, Suicune, Regirock, Regice, Registeel**

## Playable Gen I — 42

Venusaur, Charizard, Blastoise, Butterfree, Beedrill, Pidgeot, Arbok, Raichu, Sandslash, Nidoqueen, Nidoking, Clefable, Ninetales, Vileplume, Venomoth, Dugtrio, Persian, Golduck, Arcanine, Poliwrath, Alakazam, Machamp, Victreebel, Tentacruel, Golem, Rapidash, Slowbro, Dewgong, Cloyster, Gengar, Kingler, Exeggutor, Marowak, Seaking, Starmie, Jynx, Gyarados, Lapras, Flareon, Articuno, Zapdos, Dragonite.

## Playable Gen II — 9

Crobat, Bellossom, Azumarill, Scizor, Skarmory, Kingdra, Raikou, Entei, Suicune.

## Playable Gen III — 50

Sceptile, Blaziken, Swampert, Mightyena, Linoone, Beautifly, Dustox, Ludicolo, Shiftry, Swellow, Pelipper, Gardevoir, Breloom, Slaking, Ninjask, Shedinja, Exploud, Hariyama, Delcatty, Sableye, Aggron, Medicham, Manectric, Plusle, Minun, Swalot, Sharpedo, Wailord, Camerupt, Torkoal, Flygon, Cacturne, Altaria, Solrock, Whiscash, Crawdaunt, Claydol, Cradily, Armaldo, Milotic, Kecleon, Banette, Absol, Glalie, Walrein, Salamence, Metagross, Regirock, Regice, Registeel.

## Single-stage audit

The strict pool has 17 single-stage selectable Pokemon: Lapras, Kecleon, Sableye, Plusle, Minun, Articuno, Zapdos, Raikou, Entei, Suicune, Regirock, Regice, Registeel, Solrock, Torkoal, Absol, and Skarmory.

None is cut merely for being single-stage. Their roles justify inclusion: tanks such as Skarmory/Torkoal, burst such as Absol, control such as Sableye/Kecleon/Solrock, and 2v2 support value for Plusle/Minun.

Low raw-stat finals are kept only with a clear realtime role. Shedinja is a specialist because native Arena already handles Wonder Guard; Delcatty is support/control; Butterfree, Beedrill, Beautifly and Dustox lean on mobility/control rather than raw bulk.

## Current realtime ability work

Four of the 101 need Wildlands realtime ability support before the full V4 selector exposes them: Slaking (Truant), Ninjask (Speed Boost), Exploud (Soundproof), and Sharpedo (Rough Skin).

Tentacruel, Gardevoir, Swalot and Dugtrio already have at least one Arena-supported ability and can use that supported ability until their alternate ability is adapted.

## Legendary presentation and power

Boss legends should render visibly larger than ordinary Pokemon. Target V4/V5 presentation:
- ordinary Pokemon: approximately **90%** of current Arena presentation
- boss legendary encounter: approximately **120–125%**
- recruited boss legendary partner: approximately **110–115%**

The five boss-only legends remain stronger after recruitment, but lose boss-only phase mechanics. Proposed recruited legendary modifier:
- modest higher stat budget, roughly **8–12%** above comparable top-tier selectable Pokemon
- retain one signature passive/identity advantage
- no boss-only extra HP bars, arena-wide hazards, or scripted invulnerability after recruitment

Boss encounter form is significantly stronger than recruited form.

## AI / team-generation rules

Random AI teams are generated from the selectable pool with composition constraints:
- avoid duplicate primary typing where practical
- avoid two Pokemon sharing the same severe type weakness unless coverage compensates
- require usable neutral/coverage damage across the pair
- prefer complementary combat roles (pressure + range, tank + mobility, etc.)
- partner AI evaluates type effectiveness, move range, cooldown/recovery and exposure before choosing a target
- a type-disadvantaged partner should kite, guard or change targets rather than suicide into a hard counter

The purpose is variety between matches without producing obviously noncompetitive AI squads.
