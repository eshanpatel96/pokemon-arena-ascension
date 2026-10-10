#!/usr/bin/env python3
from pathlib import Path
import json,re,sys

root=Path(sys.argv[1]) if len(sys.argv)>1 else Path('.')
roster=json.loads((root/'tools/arena/roster.json').read_text())
assert len(roster)==187, len(roster)
names=[x['species'] for x in roster]
assert len(names)==len(set(names))

# Emerald-native evolution endpoints.
evo=(root/'src/data/pokemon/evolution.h').read_text()
pat=re.compile(r'\[SPECIES_([A-Z0-9_]+)\]\s*=\s*\{(.*?)(?=\n\s*\[SPECIES_|\n\};)',re.S)
evolves=set()
for m in pat.finditer(evo):
    targets=[x for x in re.findall(r'SPECIES_([A-Z0-9_]+)',m.group(2)) if x!='NONE']
    if targets:evolves.add(m.group(1))

bosses=['MEWTWO','LUGIA','HO_OH','KYOGRE','RAYQUAZA']
assert all(x in names for x in bosses)
assert 'GROUDON' not in names

gen3_endpoints=[x for x in roster if x['species'] not in evolves]
gen3_play=[x for x in gen3_endpoints if x['species'] not in bosses]
assert len(gen3_endpoints)==114, len(gen3_endpoints)
assert len(gen3_play)==109, len(gen3_play)

# Wildlands means FINAL evolution, not merely an endpoint in Pokemon Emerald.
# These animated Gen I-III forms later received true evolutions.
later_evolutions={
    'PRIMEAPE':'ANNIHILAPE',
    'MAGNETON':'MAGNEZONE',
    'RHYDON':'RHYPERIOR',
    'ELECTABUZZ':'ELECTIVIRE',
    'MAGMAR':'MAGMORTAR',
    'NOSEPASS':'PROBOPASS',
    'DUSCLOPS':'DUSKNOIR',
    'ROSELIA':'ROSERADE',
}
assert set(later_evolutions).issubset({x['species'] for x in gen3_play})
play=[x for x in gen3_play if x['species'] not in later_evolutions]
assert len(play)==101, len(play)

# Every selector entry must have enough legal native Arena actions to build a
# real four-move loadout. ascension_studio_legal.inc is generated from the
# pinned Emerald learnsets intersected with actual Arena move profiles.
studio=(root/'src/ascension_studio_legal.inc').read_text()
legal_counts={sp:int(count) for sp,start,count in
              re.findall(r'\{SPECIES_([A-Z0-9_]+),(\d+),(\d+)\}',studio)}
missing=[x['species'] for x in play if legal_counts.get(x['species'],0)<4]
assert not missing, missing
minimum=min(legal_counts[x['species']] for x in play)

play_legends=['ARTICUNO','ZAPDOS','RAIKOU','ENTEI','SUICUNE','REGIROCK','REGICE','REGISTEEL']
assert all(x in [y['species'] for y in play] for x in play_legends)

# Current one-on-one Arena compatibility still needs Wildlands implementations
# for four signature abilities before these four should be exposed in V4.
ability_work={
    'SLAKING':'TRUANT',
    'NINJASK':'SPEED_BOOST',
    'EXPLOUD':'SOUNDPROOF',
    'SHARPEDO':'ROUGH_SKIN',
}

out={
 'arena_animated_species':len(roster),
 'emerald_final_or_single_stage':len(gen3_endpoints),
 'emerald_selectable_after_bosses':len(gen3_play),
 'excluded_because_later_evolution':later_evolutions,
 'strict_final_evolution_selectable_count':len(play),
 'boss_only':bosses,
 'selectable_legendaries':play_legends,
 'minimum_legal_arena_moves_per_selectable_species':minimum,
 'wildlands_ability_work_before_v4_full_selector':ability_work,
 'groudon_arena_sprite':False,
}
print(json.dumps(out,indent=2))
