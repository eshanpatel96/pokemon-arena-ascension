# Pokemon Wildlands — Canonical Roster Lock

This file is derived from the actual Arena animation catalog in `tools/arena/roster.json` and Emerald's Gen III evolution table. Do not hand-edit roster counts without updating the audit.

## Source-of-truth counts

- Arena/PMD animated species: **187**
- Gen III final evolutions or single-stage species among those 187: **114**
- Boss-only legends: **5**
- Selectable launch pool: **109**
- Groudon Arena sprite: **absent**

## Boss-only legends

These cannot be selected in the Lab. They must be defeated in-world and may replace the AI partner after recruitment:

1. **Rayquaza** — Sky Spire
2. **Kyogre** — Abyssal Basin
3. **Mewtwo** — Abandoned Research Facility
4. **Lugia** — Tempest Shrine
5. **Ho-Oh** — Ember Temple / volcanic summit

## Selectable legendaries at match start

**Articuno, Zapdos, Raikou, Entei, Suicune, Regirock, Regice, Registeel**

## Playable Gen I — 47

Lapras, Charizard, Blastoise, Dragonite, Vileplume, Alakazam, Tentacruel, Golem, Seaking, Gyarados, Articuno, Raichu, Zapdos, Gengar, Venusaur, Butterfree, Beedrill, Pidgeot, Arbok, Sandslash, Nidoqueen, Nidoking, Clefable, Ninetales, Venomoth, Dugtrio, Persian, Golduck, Primeape, Arcanine, Poliwrath, Machamp, Victreebel, Rapidash, Slowbro, Magneton, Dewgong, Cloyster, Kingler, Exeggutor, Marowak, Rhydon, Starmie, Jynx, Electabuzz, Magmar, Flareon.

## Playable Gen II — 9

Scizor, Crobat, Bellossom, Azumarill, Raikou, Entei, Suicune, Kingdra, Skarmory.

## Playable Gen III — 53

Blaziken, Sceptile, Mightyena, Kecleon, Swellow, Manectric, Breloom, Pelipper, Swampert, Linoone, Beautifly, Dustox, Ludicolo, Shiftry, Gardevoir, Slaking, Ninjask, Shedinja, Exploud, Hariyama, Nosepass, Delcatty, Sableye, Aggron, Plusle, Minun, Swalot, Sharpedo, Wailord, Crawdaunt, Salamence, Metagross, Regirock, Regice, Registeel, Solrock, Torkoal, Cacturne, Absol, Dusclops, Banette, Glalie, Walrein, Altaria, Flygon, Whiscash, Milotic, Camerupt, Claydol, Cradily, Armaldo, Roselia, Medicham.

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
