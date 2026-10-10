#!/usr/bin/env python3
from pathlib import Path
import json,re,sys
root=Path(sys.argv[1]) if len(sys.argv)>1 else Path('.')
roster=json.loads((root/'tools/arena/roster.json').read_text())
assert len(roster)==187, len(roster)
names=[x['species'] for x in roster]
assert len(names)==len(set(names))
evo=(root/'src/data/pokemon/evolution.h').read_text()
pat=re.compile(r'\[SPECIES_([A-Z0-9_]+)\]\s*=\s*\{(.*?)(?=\n\s*\[SPECIES_|\n\};)',re.S)
evolves=set()
for m in pat.finditer(evo):
    targets=[x for x in re.findall(r'SPECIES_([A-Z0-9_]+)',m.group(2)) if x!='NONE']
    if targets:evolves.add(m.group(1))
final=[x for x in roster if x['species'] not in evolves]
bosses=['MEWTWO','LUGIA','HO_OH','KYOGRE','RAYQUAZA']
assert all(x in names for x in bosses)
assert 'GROUDON' not in names
play=[x for x in final if x['species'] not in bosses]
assert len(final)==114, len(final)
assert len(play)==109, len(play)
play_legends=['ARTICUNO','ZAPDOS','RAIKOU','ENTEI','SUICUNE','REGIROCK','REGICE','REGISTEEL']
assert all(x in [y['species'] for y in play] for x in play_legends)
out={
 'arena_animated_species':len(roster),
 'final_or_single_stage_gen3_rules':len(final),
 'boss_only':bosses,
 'boss_count':len(bosses),
 'selectable_count':len(play),
 'selectable_legendaries':play_legends,
 'groudon_arena_sprite':False,
}
print(json.dumps(out,indent=2))
